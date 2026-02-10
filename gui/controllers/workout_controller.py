"""
Workout controller - handles business logic separated from UI
"""
import threading
import subprocess
import platform
import cv2
from typing import Dict, Any, Optional, List
from models.workout_state import WorkoutState, WorkoutStats
from models.workout_session import WorkoutSession
import gui.config.constants as config


class VideoProcessor:
    """Handles video processing loop"""
    def __init__(self, window, update_callback):
        self.window = window
        self.update_callback = update_callback
        self._is_processing = False
        self._update_id: Optional[str] = None
        self._frame_rate = 30
        self._update_interval = 1000 // self._frame_rate
    
    def start(self):
        """Start video processing loop"""
        if not self._is_processing:
            self._is_processing = True
            self._schedule_next_update()
    
    def stop(self):
        """Stop video processing loop"""
        self._is_processing = False
        if self._update_id:
            try:
                self.window.after_cancel(self._update_id)
            except:
                pass
            self._update_id = None
    
    def _schedule_next_update(self):
        """Schedule next frame update"""
        if self._is_processing:
            self._update_id = self.window.after(
                self._update_interval,
                self._process_frame
            )
    
    def _process_frame(self):
        """Process a single frame"""
        try:
            self.update_callback()
        finally:
            self._schedule_next_update()


class WorkoutController:
    """Controls workout logic, separated from UI"""
    def __init__(self, engine, db, user_config):
        self.engine = engine
        self.db = db
        self.user_config = user_config
        
        self.state = WorkoutState.IDLE
        self.current_exercise = "Squats"
        self.session: Optional[WorkoutSession] = None
        self.video_processor: Optional[VideoProcessor] = None
        
        self.lock = threading.RLock()
    
    def set_video_processor(self, window, update_callback):
        """Set up video processor with window reference"""
        self.video_processor = VideoProcessor(window, update_callback)
    
    def check_camera(self, video_panel) -> dict:
        """Check camera availability using configured index.

        On success, keeps the capture open on the engine so the camera
        isn't released and re-opened when the workout starts (avoids
        iPhone Continuity Camera flickering).

        Runs the actual cv2.VideoCapture in a background thread to avoid
        crashing the GIL on macOS (AVFoundation auth + tkinter conflict).

        Returns:
            dict with keys:
                'success': bool - whether configured camera works
                'camera_index': int - the index that was checked
                'available_cameras': list - other cameras found (only populated on failure)
        """
        import time
        camera_index = self.user_config.get('system', 'camera_index', 0)
        result = {'success': False, 'camera_index': camera_index, 'available_cameras': []}

        # If engine already has an open camera (from pre-tkinter init), reuse it
        if self.engine.cap is not None and self.engine.camera_initialized:
            try:
                ret, _ = self.engine.cap.read()
                if ret:
                    video_panel.show_camera_ready()
                    result['success'] = True
                    return result
            except Exception:
                pass
            # Camera died — fall through
            self.engine.cap.release()
            self.engine.cap = None
            self.engine.camera_initialized = False

        # Open camera in a background thread to avoid GIL crash on macOS.
        # Skip auth in thread — auth was already requested from main thread
        # in _request_camera_permission() before tkinter started.
        cap_result = [None, False]  # [capture, success]

        def _open_camera():
            import os
            os.environ['OPENCV_AVFOUNDATION_SKIP_AUTH'] = '1'
            try:
                cap = cv2.VideoCapture(camera_index)
                if cap.isOpened():
                    time.sleep(2.0)
                    ret, frame = cap.read()
                    if ret:
                        cap_result[0] = cap
                        cap_result[1] = True
                    else:
                        cap.release()
                else:
                    cap.release()
            except Exception as e:
                print(f"Camera check error: {e}")
            finally:
                os.environ.pop('OPENCV_AVFOUNDATION_SKIP_AUTH', None)

        cam_thread = threading.Thread(target=_open_camera, daemon=True)
        cam_thread.start()
        cam_thread.join(timeout=10.0)

        if cap_result[1] and cap_result[0] is not None:
            video_width = self.user_config.get('system', 'video_width', 640)
            video_height = self.user_config.get('system', 'video_height', 480)
            cap_result[0].set(cv2.CAP_PROP_FRAME_WIDTH, video_width)
            cap_result[0].set(cv2.CAP_PROP_FRAME_HEIGHT, video_height)
            self.engine.cap = cap_result[0]
            self.engine.camera_initialized = True
            video_panel.show_camera_ready()
            result['success'] = True
            return result

        # Configured camera failed — use cached scan results instead
        # of re-scanning (which would flicker the iPhone camera again)
        cached = self.user_config.get('system', 'cached_cameras', None)
        if cached:
            result['available_cameras'] = [
                cam for cam in cached if cam['index'] != camera_index
            ]
        else:
            # No cache — must scan
            result['available_cameras'] = self.scan_cameras(exclude=camera_index)

        if not result['available_cameras']:
            video_panel.show_camera_error()
        return result

    def scan_cameras(self, exclude=None, max_index=5) -> list:
        """Scan for available cameras (skips excluded index).

        Runs in a background thread to avoid GIL crash on macOS.

        Args:
            exclude: camera index to skip (already tested)
            max_index: highest index to check

        Returns:
            list of dicts with 'index', 'width', 'height', 'name' for each found camera
        """
        import time
        device_names = self._get_camera_device_names()
        cameras = []

        def _scan():
            import os
            os.environ['OPENCV_AVFOUNDATION_SKIP_AUTH'] = '1'
            try:
                for i in range(max_index):
                    if i == exclude:
                        continue
                    cap = None
                    try:
                        cap = cv2.VideoCapture(i)
                        if cap.isOpened():
                            time.sleep(0.3)
                            ret, frame = cap.read()
                            if ret:
                                h, w = frame.shape[:2]
                                name = device_names[i] if i < len(device_names) else f"Camera {i}"
                                cameras.append({
                                    'index': i,
                                    'width': w,
                                    'height': h,
                                    'name': name
                                })
                    except Exception:
                        pass
                    finally:
                        if cap is not None:
                            cap.release()
            finally:
                os.environ.pop('OPENCV_AVFOUNDATION_SKIP_AUTH', None)

        scan_thread = threading.Thread(target=_scan, daemon=True)
        scan_thread.start()
        scan_thread.join(timeout=15.0)
        return cameras

    def scan_all_cameras(self, max_index=5) -> list:
        """Scan ALL camera indices without exclusions. Used by settings panel.

        Args:
            max_index: highest index to check

        Returns:
            list of dicts with 'index', 'width', 'height', 'name' for each found camera
        """
        return self.scan_cameras(exclude=None, max_index=max_index)

    @staticmethod
    def _get_camera_device_names() -> list:
        """Get camera device names from the OS.

        On macOS, uses system_profiler SPCameraDataType.
        Returns a list of name strings ordered by system index.
        Falls back to generic names on failure or non-macOS.
        """
        names = []
        if platform.system() != 'Darwin':
            return names

        try:
            result = subprocess.run(
                ['system_profiler', 'SPCameraDataType'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                current_name = None
                for line in result.stdout.splitlines():
                    stripped = line.strip()
                    # Camera names appear as top-level entries ending with ':'
                    # that are NOT known section headers
                    if stripped.endswith(':') and not stripped.startswith(('Model ID', 'Unique ID')):
                        # Check if this looks like a camera name (indented one level)
                        indent = len(line) - len(line.lstrip())
                        if indent <= 4 and stripped not in ('Cameras:', 'Camera:'):
                            if current_name is not None:
                                names.append(current_name)
                            current_name = stripped.rstrip(':')
                    # Check for model info to enrich name
                    if current_name and 'Model ID:' in stripped:
                        model = stripped.split('Model ID:')[1].strip()
                        # If model contains iPhone/iPad, add it to the name
                        if any(device in model for device in ['iPhone', 'iPad']):
                            current_name = f"{current_name} ({model})"
                # Don't forget the last camera
                if current_name is not None:
                    names.append(current_name)
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print(f"Could not get camera names: {e}")

        return names
    
    def start_workout(self, exercise: str, backend_type: str) -> bool:
        """Start a workout session"""
        with self.lock:
            if self.state != WorkoutState.IDLE:
                return False
            
            # Initialize camera
            if not self.engine.start_camera():
                return False
            
            # Start session
            self.session = WorkoutSession(self.engine, exercise)
            if not self.session.start():
                self.session = None
                return False
            
            # Switch exercise
            if hasattr(self.engine, 'switch_exercise'):
                self.engine.switch_exercise(backend_type)
            
            self.current_exercise = exercise
            self.state = WorkoutState.RUNNING
            
            # Start video processing
            if self.video_processor:
                self.video_processor.start()
            
            return True
    
    def stop_workout(self) -> Optional[Dict[str, Any]]:
        """Stop workout session"""
        with self.lock:
            if self.state != WorkoutState.RUNNING:
                return None
            
            self.state = WorkoutState.STOPPING
            
            # Stop video
            if self.video_processor:
                self.video_processor.stop()

            # Release camera
            if self.engine and hasattr(self.engine, 'cap') and self.engine.cap is not None:
                self.engine.cap.release()
                self.engine.cap = None
                self.engine.camera_initialized = False

            # End session
            summary = None
            if self.session:
                summary = self.session.end()
                self.session = None
            
            self.state = WorkoutState.IDLE
            return summary
    
    def switch_exercise(self, new_exercise: str, backend_type: str) -> bool:
        """Switch exercise during workout"""
        with self.lock:
            if self.state != WorkoutState.RUNNING or not self.session:
                return False
            
            old_exercise = self.current_exercise
            self.current_exercise = new_exercise
            self.session.exercise_type = new_exercise
            
            try:
                if hasattr(self.engine, 'switch_exercise'):
                    self.engine.switch_exercise(backend_type)
                    self.session.stats.reset()
                    return True
            except Exception as e:
                print(f"Error switching exercise: {e}")
            
            return False
    
    def reset_workout(self, backend_type: str = None):
        """Reset workout counters"""
        with self.lock:
            if self.session:
                self.session.stats.reset()

            # Reset backend if running
            if self.state == WorkoutState.RUNNING and backend_type:
                if hasattr(self.engine, 'switch_exercise'):
                    self.engine.switch_exercise(backend_type)
    
    def process_video_frame(self) -> Optional[Dict[str, Any]]:
        """Process video frame (to be called by UI)"""
        if self.state != WorkoutState.RUNNING:
            return None
        
        try:
            return self.engine.process_frame()
        except Exception as e:
            print(f"Video processing error: {e}")
            return None
    
    def cleanup(self):
        """Cleanup resources — save any in-progress workout data"""
        with self.lock:
            # Stop video
            if self.video_processor:
                self.video_processor.stop()

            # End session if running (any non-IDLE state)
            if self.state != WorkoutState.IDLE and self.session:
                try:
                    self.session.end("Application closed")
                except Exception as e:
                    print(f"Error ending session: {e}")
                self.session = None

            # Also end engine session directly (safety net)
            if hasattr(self.engine, 'session') and self.engine.session.session_id is not None:
                try:
                    self.engine.end_session("Application closed")
                except Exception as e:
                    print(f"Error ending engine session: {e}")

            self.state = WorkoutState.IDLE

            # Cleanup engine
            if hasattr(self.engine, 'cleanup'):
                try:
                    self.engine.cleanup()
                except Exception as e:
                    print(f"Engine cleanup error: {e}")
    
    @property
    def is_running(self) -> bool:
        """Check if workout is running"""
        return self.state == WorkoutState.RUNNING