"""
Core workout processing engine
Handles all computer vision and exercise detection
Separated from GUI for modularity
"""
import cv2
import time
import threading
from enum import Enum
from database.workout_database import WorkoutDatabase
from cv.pose_detection import PoseDetector
from core_cv2.detection.exercises import SquatDetector, PushupDetector, BicepCurlDetector
from core_cv2.analysis.form_analysis import analyze_squat_form, analyze_pushup_form, analyze_curl_form
from core_cv2.validation import SquatValidator, PushupValidator, CurlValidator
from config.user_config import UserConfig
from config.app_constants import SQUAT_THRESHOLDS, PUSHUP_THRESHOLDS, CURL_THRESHOLDS


class ExerciseType(Enum):
    SQUAT = 'squat'
    PUSHUP = 'pushup'
    CURL = 'curl'


class WorkoutSession:
    """Manages database tracking for a workout session"""
    
    def __init__(self, db: WorkoutDatabase, user_config: UserConfig):
        self.db = db
        self.user_config = user_config
        self.session_id = None
        self.current_set_id = None
        self.current_exercise = None
        self.set_start_time = None
        self.rep_start_time = None
        
        self.set_stats = {
            'total_reps': 0,
            'excellent_reps': 0,
            'good_reps': 0,
            'poor_reps': 0,
            'angles': []
        }
    
    def start(self):
        """Start new workout session"""
        self.session_id = self.db.start_session()
        return self.session_id
    
    def start_exercise_set(self, exercise_type: str):
        """Start tracking a new exercise"""
        if self.current_set_id is not None:
            self.end_exercise_set()
        
        # Validate exercise type
        valid_exercises = [e.value for e in ExerciseType]
        if exercise_type not in valid_exercises:
            raise ValueError(f"Invalid exercise type: {exercise_type}. Must be one of {valid_exercises}")
        
        self.current_exercise = exercise_type
        self.current_set_id = self.db.create_exercise_set(self.session_id, exercise_type)
        self.set_start_time = time.time()
        self.rep_start_time = time.time()
        
        self.set_stats = {
            'total_reps': 0,
            'excellent_reps': 0,
            'good_reps': 0,
            'poor_reps': 0,
            'angles': []
        }
    
    def log_rep_completed(self, form_quality: str, peak_angle: float):
        """Log a completed repetition"""
        if self.current_set_id is None:
            return

        self.set_stats['total_reps'] += 1
        self.set_stats['angles'].append(peak_angle)

        if form_quality == 'excellent':
            self.set_stats['excellent_reps'] += 1
        elif form_quality == 'good':
            self.set_stats['good_reps'] += 1
        else:
            self.set_stats['poor_reps'] += 1

        rep_duration = time.time() - self.rep_start_time
        self.rep_start_time = time.time()

        self.db.log_rep(
            set_id=self.current_set_id,
            rep_number=self.set_stats['total_reps'],
            form_quality=form_quality,
            peak_angle=peak_angle,
            duration_seconds=rep_duration
        )
    
    def get_current_stats(self):
        """Return current set statistics for UI display"""
        return self.set_stats.copy()
    
    def end_exercise_set(self):
        """End current exercise set and save statistics"""
        if self.current_set_id is None:
            return
        
        angles = self.set_stats['angles']
        if angles:
            duration = int(time.time() - self.set_start_time)
            
            stats = {
                'total_reps': self.set_stats['total_reps'],
                'excellent_reps': self.set_stats['excellent_reps'],
                'good_reps': self.set_stats['good_reps'],
                'poor_reps': self.set_stats['poor_reps'],
                'average_angle': sum(angles) / len(angles),
                'min_angle': min(angles),
                'max_angle': max(angles),
                'duration_seconds': duration
            }
        else:
            stats = {
                'total_reps': 0,
                'excellent_reps': 0,
                'good_reps': 0,
                'poor_reps': 0,
                'average_angle': None,
                'min_angle': None,
                'max_angle': None,
                'duration_seconds': int(time.time() - self.set_start_time)
            }
        
        self.db.update_exercise_set(self.current_set_id, stats)
        self.current_set_id = None
        self.current_exercise = None
    
    def end(self, notes: str = ""):
        """End workout session"""
        if self.current_set_id is not None:
            self.end_exercise_set()
        
        if self.session_id is not None:
            self.db.end_session(self.session_id, notes)
            session_id = self.session_id
            self.session_id = None
            return session_id


class WorkoutEngine:
    """
    Core workout processing engine
    Handles video capture, pose detection, rep counting
    """
    
    def __init__(self, db: WorkoutDatabase, user_config: UserConfig):
        self.db = db
        self.user_config = user_config
        
        # Computer vision
        self.pose_detector = PoseDetector()
        self.cap = None
        self.camera_initialized = False
        
        # Exercise detectors
        self.squat_detector = SquatDetector()
        self.pushup_detector = PushupDetector()
        self.curl_detector = BicepCurlDetector()

        # Session management
        self.session = WorkoutSession(db, user_config)

        # Form validators (anti-cheat) — one per exercise
        self.form_validators = {
            ExerciseType.SQUAT.value: SquatValidator(),
            ExerciseType.PUSHUP.value: PushupValidator(),
            ExerciseType.CURL.value: CurlValidator(),
        }

        # Auto-calibration tracking
        self.calibration_data = {
            'squat': {'angles': [], 'calibrated': False},
            'pushup': {'angles': [], 'calibrated': False},
            'curl': {'angles': [], 'calibrated': False}
        }
        self.CALIBRATION_REP_COUNT = 5  # Calibrate after this many reps

        # Load any previously calibrated thresholds (must come after calibration_data init)
        self._load_calibrated_thresholds()

        # Current state
        self.current_mode = ExerciseType.SQUAT.value
        self.current_detector = self.squat_detector
        self.current_analyzer = analyze_squat_form
        self.current_rep_peak_angle = None

        # Exercise-specific peak tracking logic
        self.peak_tracking_fn = min  # Default: track minimum angle

        # Feedback control - only show feedback during active rep attempt
        self.rep_in_progress = False  # True when user has entered active zone
        self.feedback_given_for_rep = False  # True after feedback shown for current rep
        self.last_feedback = None  # Cache last feedback to avoid duplicates

        # Thread safety
        self.lock = threading.RLock()
        self.is_running = False
        self.is_cleaned_up = False
    
    def start_camera(self, camera_index=None):
        """Initialize webcam using configured or specified camera index.

        If the camera was already opened (e.g. by check_camera), reuses
        the existing capture to avoid re-initializing the hardware
        (prevents iPhone Continuity Camera flickering).
        """
        import time
        with self.lock:
            # If camera is already open and working, reuse it
            if self.cap is not None and self.camera_initialized:
                ret, _ = self.cap.read()
                if ret:
                    return True
                # Camera died — fall through to re-open
                self.cap.release()
                self.cap = None
                self.camera_initialized = False

            if self.cap is not None:
                self.cap.release()

            if camera_index is None:
                camera_index = self.user_config.get('system', 'camera_index', 0)

            video_width = self.user_config.get('system', 'video_width', 640)
            video_height = self.user_config.get('system', 'video_height', 480)

            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False

            # Give camera time to initialize (Continuity Camera/iPhone needs this)
            time.sleep(1.0)

            # Verify camera actually works by reading a test frame
            ret, _ = self.cap.read()
            if not ret:
                self.cap.release()
                self.cap = None
                return False

            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, video_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, video_height)
            self.camera_initialized = True
            return True
    
    def start_session(self):
        """Start new workout session"""
        with self.lock:
            session_id = self.session.start()
            self.session.start_exercise_set(self.current_mode)
            self.is_running = True
            return session_id
    
    def switch_exercise(self, exercise_type: str):
        """Switch to different exercise type"""
        with self.lock:
            # Validate exercise type
            try:
                exercise_enum = ExerciseType(exercise_type)
                self.current_mode = exercise_enum.value
            except ValueError:
                raise ValueError(f"Invalid exercise type: {exercise_type}. Must be one of {[e.value for e in ExerciseType]}")
            
            if exercise_type == ExerciseType.SQUAT.value:
                self.current_detector = self.squat_detector
                self.current_analyzer = analyze_squat_form
                self.peak_tracking_fn = min  # Track minimum angle for squats
            elif exercise_type == ExerciseType.PUSHUP.value:
                self.current_detector = self.pushup_detector
                self.current_analyzer = analyze_pushup_form
                self.peak_tracking_fn = min  # Track minimum angle for pushups
            else:  # curl
                self.current_detector = self.curl_detector
                self.current_analyzer = analyze_curl_form
                self.peak_tracking_fn = min  # Track maximum angle for curls (arm extension)
            
            # Reset detector state if method exists
            if hasattr(self.current_detector, 'reset'):
                self.current_detector.reset()
            else:
                # Reset rep count manually
                self.current_detector.rep_count = 0
                if hasattr(self.current_detector, 'state'):
                    self.current_detector.state = 'start'

            # Reset form validator for the new exercise
            validator = self.form_validators.get(exercise_type)
            if validator:
                validator.reset()

            # Start new set
            self.session.start_exercise_set(exercise_type)
            self.current_rep_peak_angle = None
    
    def process_frame(self):
        """
        Process one video frame
        
        Returns:
            dict with processing results or None
        """
        with self.lock:
            if self.is_cleaned_up or not self.camera_initialized:
                return None
            
            if not self.cap or not self.cap.isOpened():
                return None
            
            ret, frame = self.cap.read()
            if not ret:
                return None

            # Check if skeleton should be drawn
            show_skeleton = self.user_config.get('display', 'show_skeleton', True)

            # Detect pose
            landmarks, annotated_frame = self.pose_detector.process_frame(frame, draw_skeleton=show_skeleton)
            
            result = {
                'frame': annotated_frame,
                'rep_completed': False,
                'current_angle': None,
                'form_feedback': {'quality': 'unknown', 'feedback': ''},
                'rep_count': self.current_detector.rep_count if hasattr(self.current_detector, 'rep_count') else 0,
                'exercise': self.current_mode,
                'stats': self.session.get_current_stats() if hasattr(self.session, 'get_current_stats') else {}
            }
            
            if landmarks:
                height, width = frame.shape[:2]

                # Update form validator with current landmarks (for anti-cheat)
                self.form_validators[self.current_mode].update(landmarks)

                # Get angle based on exercise
                angle = None
                if self.current_mode == ExerciseType.SQUAT.value:
                    angle = self.pose_detector.get_best_knee_angle(landmarks, width, height)
                elif self.current_mode in [ExerciseType.PUSHUP.value, ExerciseType.CURL.value]:
                    angle = self.pose_detector.get_best_elbow_angle(landmarks, width, height)

                result['current_angle'] = angle

                if angle is not None:
                    # Determine if user is in "active zone" (attempting a rep)
                    # For squats: below standing threshold means in active zone
                    # For pushups/curls: similar logic
                    in_active_zone = self._is_in_active_zone(angle)

                    # Track when user enters active zone (starts rep attempt)
                    if in_active_zone and not self.rep_in_progress:
                        self.rep_in_progress = True
                        self.feedback_given_for_rep = False

                    # Track peak angle based on exercise type (only during rep)
                    if self.rep_in_progress:
                        if self.current_rep_peak_angle is None:
                            self.current_rep_peak_angle = angle
                        else:
                            self.current_rep_peak_angle = self.peak_tracking_fn(
                                self.current_rep_peak_angle, angle
                            )

                    # Update state machine
                    rep_completed = self.current_detector.update(angle)
                    result['rep_count'] = self.current_detector.rep_count

                    if rep_completed:
                        # Validate rep with secondary landmarks (anti-cheat)
                        is_valid_rep = self.form_validators[self.current_mode].validate_rep()

                        if is_valid_rep:
                            # Valid rep - analyze form and log
                            result['rep_completed'] = True
                            form_feedback = self.current_analyzer(self.current_rep_peak_angle)
                            result['form_feedback'] = form_feedback

                            # Log to database
                            self.session.log_rep_completed(
                                form_feedback['quality'],
                                self.current_rep_peak_angle
                            )

                            # Check if we should auto-calibrate
                            self._check_calibration(self.current_mode, self.current_rep_peak_angle)
                        else:
                            # Invalid rep (cheat detected) - don't count it
                            result['rep_completed'] = False
                            # Decrement the detector's rep count since it already incremented
                            if hasattr(self.current_detector, 'rep_count'):
                                self.current_detector.rep_count = max(0, self.current_detector.rep_count - 1)
                            result['rep_count'] = self.current_detector.rep_count
                            result['form_feedback'] = {
                                'quality': 'invalid',
                                'feedback': 'Invalid rep detected',
                            }

                        # Reset for next rep
                        self.current_rep_peak_angle = None
                        self.rep_in_progress = False
                        self.feedback_given_for_rep = True
                    else:
                        result['rep_completed'] = False
                        # Only show feedback if in active zone and haven't given feedback yet
                        # This prevents constant feedback spam
                        if self.rep_in_progress and not self.feedback_given_for_rep:
                            current_feedback = self.current_analyzer(angle)
                            # Only update if it's meaningful feedback (not neutral/standing)
                            if current_feedback['quality'] not in ['neutral', 'unknown']:
                                result['form_feedback'] = current_feedback

                    # When user returns to standing, reset rep tracking
                    if not in_active_zone:
                        self.rep_in_progress = False

                    result['stats'] = self.session.get_current_stats()
        
        return result
    
    def end_session(self, notes: str = ""):
        """End workout session"""
        with self.lock:
            self.is_running = False
            return self.session.end(notes)

    def _is_in_active_zone(self, angle: float) -> bool:
        """
        Check if the user is in the active zone (attempting a rep).
        Active zone means they've moved past the starting position threshold.

        Args:
            angle: Current joint angle in degrees

        Returns:
            True if in active zone (attempting rep), False if in resting position
        """
        if self.current_mode == ExerciseType.SQUAT.value:
            # For squats: active when knee angle drops below standing threshold
            return angle < SQUAT_THRESHOLDS['STANDING']
        elif self.current_mode == ExerciseType.PUSHUP.value:
            # For pushups: active when elbow angle drops below up position
            return angle < PUSHUP_THRESHOLDS['UP']
        elif self.current_mode == ExerciseType.CURL.value:
            # For curls: active when elbow angle drops below extended position
            return angle < CURL_THRESHOLDS['DOWN']
        return False

    # ==================== AUTO-CALIBRATION ====================

    def _load_calibrated_thresholds(self):
        """Load any previously calibrated thresholds from user_config"""
        exercises = [
            ('squat', self.squat_detector),
            ('pushup', self.pushup_detector),
            ('curl', self.curl_detector)
        ]

        for exercise_type, detector in exercises:
            if self.user_config.get_threshold(exercise_type, 'CALIBRATED'):
                thresholds = self.user_config.get_threshold(exercise_type)
                if thresholds:
                    self._apply_thresholds_to_detector(detector, exercise_type, thresholds)
                    # Mark as already calibrated so we don't re-calibrate
                    self.calibration_data[exercise_type]['calibrated'] = True
                    print(f"Loaded calibrated thresholds for {exercise_type}")

    def _check_calibration(self, exercise_type: str, peak_angle: float):
        """
        Check if we should auto-calibrate after this rep.
        Called after each valid rep completion.
        """
        cal_data = self.calibration_data.get(exercise_type)
        if cal_data is None:
            return

        # Skip if already calibrated (check persistent flag in user_config)
        if self.user_config.get_threshold(exercise_type, 'CALIBRATED'):
            return

        # Collect the peak angle from this rep
        cal_data['angles'].append(peak_angle)

        # Calibrate after N reps
        if len(cal_data['angles']) >= self.CALIBRATION_REP_COUNT:
            self._perform_calibration(exercise_type, cal_data['angles'])
            cal_data['calibrated'] = True

    def _perform_calibration(self, exercise_type: str, angles: list):
        """
        Calculate and apply calibrated thresholds based on observed angles.

        Args:
            exercise_type: 'squat', 'pushup', or 'curl'
            angles: list of peak angles from first N reps
        """
        if len(angles) < 3:
            return  # Not enough data

        # Check consistency - if angles vary wildly, don't calibrate
        import statistics
        if len(angles) >= 3:
            std_dev = statistics.stdev(angles)
            if std_dev > 25:  # Too inconsistent
                print(f"Auto-calibration skipped for {exercise_type}: inconsistent angles (std={std_dev:.1f})")
                return

        observed_min = min(angles)  # Deepest/most bent position
        observed_max = max(angles)  # Most extended position (during rep peak tracking)

        # Calculate new thresholds based on exercise type
        if exercise_type == 'squat':
            new_thresholds = self._calculate_squat_thresholds(observed_min, observed_max)
            detector = self.squat_detector
        elif exercise_type == 'pushup':
            new_thresholds = self._calculate_pushup_thresholds(observed_min, observed_max)
            detector = self.pushup_detector
        elif exercise_type == 'curl':
            new_thresholds = self._calculate_curl_thresholds(observed_min, observed_max)
            detector = self.curl_detector
        else:
            return

        # Update live detector thresholds
        self._apply_thresholds_to_detector(detector, exercise_type, new_thresholds)
        
        # Persist to user_config (marks as calibrated)
        self.user_config.set_threshold(exercise_type, new_thresholds, mark_calibrated=True)

        print(f"Auto-calibrated {exercise_type}: {new_thresholds}")

    def _calculate_squat_thresholds(self, observed_min: float, observed_max: float) -> dict:
        """Calculate squat thresholds from observed ROM"""
        # observed_min = deepest knee angle user reached
        # For squats, smaller angle = deeper squat

        # State transition thresholds
        standing = max(observed_max - 10, 150)  # Slightly below their standing
        squatting = observed_min + 15  # Slightly above their deepest

        # Form quality thresholds - keep strict but adjust if user can't hit defaults
        default_excellent = SQUAT_THRESHOLDS['EXCELLENT']
        default_good = SQUAT_THRESHOLDS['GOOD']

        if observed_min > default_excellent:
            # User can't hit default excellent depth, adjust relative to their ROM
            excellent = observed_min + 5
            good = observed_min + 15
        else:
            # User can hit standard depths, keep defaults
            excellent = default_excellent
            good = default_good

        return {
            'STANDING': int(standing),
            'SQUATTING': int(squatting),
            'EXCELLENT': int(excellent),
            'GOOD': int(good),
            'COOLDOWN_FRAMES': SQUAT_THRESHOLDS['COOLDOWN_FRAMES']
        }

    def _calculate_pushup_thresholds(self, observed_min: float, observed_max: float) -> dict:
        """Calculate pushup thresholds from observed ROM"""
        # observed_min = deepest elbow angle (arms most bent)

        up = max(observed_max - 10, 150)
        down = observed_min + 15

        default_excellent = PUSHUP_THRESHOLDS['EXCELLENT']
        default_good = PUSHUP_THRESHOLDS['GOOD']

        if observed_min > default_excellent:
            excellent = observed_min + 5
            good = observed_min + 15
        else:
            excellent = default_excellent
            good = default_good

        return {
            'UP': int(up),
            'DOWN': int(down),
            'EXCELLENT': int(excellent),
            'GOOD': int(good),
            'COOLDOWN_FRAMES': PUSHUP_THRESHOLDS['COOLDOWN_FRAMES']
        }

    def _calculate_curl_thresholds(self, observed_min: float, observed_max: float) -> dict:
        """Calculate curl thresholds from observed ROM"""
        # observed_min = tightest curl angle (elbow most bent)

        down = max(observed_max - 10, 150)
        curled = observed_min + 10

        default_excellent = CURL_THRESHOLDS['EXCELLENT']
        default_good = CURL_THRESHOLDS['GOOD']

        if observed_min > default_excellent:
            excellent = observed_min + 5
            good = observed_min + 15
        else:
            excellent = default_excellent
            good = default_good

        return {
            'DOWN': int(down),
            'CURLED': int(curled),
            'EXCELLENT': int(excellent),
            'GOOD': int(good),
            'COOLDOWN_FRAMES': CURL_THRESHOLDS['COOLDOWN_FRAMES']
        }

    def _apply_thresholds_to_detector(self, detector, exercise_type: str, thresholds: dict):
        """Update live detector with new thresholds"""
        if exercise_type == 'squat':
            detector.STANDING_THRESHOLD = thresholds['STANDING']
            detector.SQUATTING_THRESHOLD = thresholds['SQUATTING']
        elif exercise_type == 'pushup':
            detector.UP_THRESHOLD = thresholds['UP']
            detector.DOWN_THRESHOLD = thresholds['DOWN']
        elif exercise_type == 'curl':
            detector.DOWN_THRESHOLD = thresholds['DOWN']
            detector.CURLED_THRESHOLD = thresholds['CURLED']

        # Update cooldown if present
        if hasattr(detector, 'COOLDOWN_PERIOD'):
            detector.COOLDOWN_PERIOD = thresholds.get('COOLDOWN_FRAMES', detector.COOLDOWN_PERIOD)

    def cleanup(self):
        """Release all resources"""
        with self.lock:
            if self.is_cleaned_up:
                return
            
            try:
                if self.cap and self.camera_initialized:
                    self.cap.release()
                    self.camera_initialized = False
            except Exception:
                pass
            
            try:
                if hasattr(self.pose_detector, 'close'):
                    self.pose_detector.close()
            except Exception:
                pass
            
            self.is_cleaned_up = True


if __name__ == "__main__":
    # Quick test (without GUI)
    print("Testing workout engine...")
    
    try:
        db = WorkoutDatabase("test_engine.db")
        user_config = UserConfig()
        engine = WorkoutEngine(db, user_config)
        
        if not engine.start_camera():
            print("✗ Could not open camera")
            exit(1)
        
        print("✓ Camera opened")
        session_id = engine.start_session()
        print(f"✓ Started session {session_id}")
        
        print("Processing frames for 10 seconds... Do some squats!")
        
        start_time = time.time()
        while time.time() - start_time < 10:
            result = engine.process_frame()
            if result and result['rep_completed']:
                print(f"  ✓ Rep {result['rep_count']} - {result['form_feedback']['quality']}")
            time.sleep(0.033)  # ~30 FPS
        
        session_id = engine.end_session("Test session")
        print(f"✓ Ended session {session_id}")
        
        summary = db.get_session_summary(session_id)
        print(f"✓ Summary: {summary}")
        
        engine.cleanup()
        db.close()
        
        import os
        if os.path.exists("test_engine.db"):
            os.remove("test_engine.db")
        
        print("✓ Engine test complete!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()