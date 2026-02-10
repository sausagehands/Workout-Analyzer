"""
Video display handler for processing and displaying frames
UPDATED: Uses CTkImage to avoid HighDPI warnings
"""
import cv2
from PIL import Image
import customtkinter as ctk
import gui.config.constants as config

class VideoDisplay:
    def __init__(self, video_label, window):
        """
        Initialize video display handler
        
        Args:
            video_label: CTkLabel widget for displaying video
            window: Main window reference for size calculations
        """
        self.video_label = video_label
        self.window = window
        self.current_image = None  # Changed from current_photo
        self.current_ctk_image = None  # Store CTkImage
        self.current_frame = None
        self.is_displaying = False
        self.mirror_enabled = config.MIRROR_CAMERA
    
    def update_frame(self, frame):
        """
        Update video frame display
        
        Args:
            frame: OpenCV frame (BGR format)
        
        Returns:
            bool: True if update successful
        """
        if frame is None:
            return False
        
        try:
            # Store current frame
            self.current_frame = frame.copy()
            self.is_video_active = True
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Apply mirror if enabled
            if self.mirror_enabled:
                frame_rgb = cv2.flip(frame_rgb, 1)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_rgb)
            
            # Get label dimensions
            label_width = self.video_label.winfo_width()
            label_height = self.video_label.winfo_height()
            
            # Only resize if we have valid dimensions
            if label_width > 1 and label_height > 1:
                pil_image = pil_image.resize(
                    (label_width, label_height),
                    Image.Resampling.LANCZOS
                )
            
            # CRITICAL FIX: Always create a NEW CTkImage
            # Don't reuse old image references
            ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=(label_width if label_width > 1 else 640, 
                    label_height if label_height > 1 else 480)
            )
            
            # Update label - clear text first, then set image
            self.video_label.configure(text="")  # Clear any text
            self.video_label.configure(image=ctk_image)
            
            # CRITICAL: Keep a reference to prevent garbage collection
            self.video_label.image = ctk_image
            
            return True
            
        except Exception as e:
            print(f"Video frame update error: {e}")
            return False
        
    def _resize_frame(self, frame_rgb):
        """
        Resize frame to fit display area while maintaining aspect ratio
        
        Args:
            frame_rgb: RGB frame
        
        Returns:
            Resized frame
        """
        try:
            # Get current window dimensions
            window_width = self.window.winfo_width()
            window_height = self.window.winfo_height()
            
            if window_width <= 1 or window_height <= 1:
                # Window not fully initialized, return original
                return frame_rgb
            
            # Calculate target size based on video area
            target_width = window_width * (config.LAYOUT_MAIN_WEIGHT / 
                                          (config.LAYOUT_MAIN_WEIGHT + config.LAYOUT_SIDEBAR_WEIGHT))
            target_height = window_height - config.HEADER_HEIGHT - config.CONTROLS_HEIGHT - 50
            
            # Ensure minimum dimensions
            target_width = max(target_width, 320)
            target_height = max(target_height, 240)
            
            # Get frame dimensions
            frame_height, frame_width = frame_rgb.shape[:2]
            
            # Calculate scaling to fit within target while maintaining aspect ratio
            width_scale = target_width / frame_width
            height_scale = target_height / frame_height
            scale = min(width_scale, height_scale)
            
            new_width = int(frame_width * scale)
            new_height = int(frame_height * scale)
            
            # Ensure minimum size
            new_width = max(new_width, 320)
            new_height = max(new_height, 240)
            
            # Resize frame
            frame_resized = cv2.resize(frame_rgb, (new_width, new_height))
            return frame_resized
            
        except Exception as e:
            print(f"Frame resize error: {e}")
            # Return original frame if resize fails
            return frame_rgb
    
    def show_text(self, text: str, text_color: str = None):
        """
        Display text message

        Args:
            text: Message to display
            text_color: Optional text color
        """
        if text_color is None:
            text_color = config.COLOR_TEXT_SECONDARY

        # Clear video state
        self.current_frame = None
        self.current_ctk_image = None
        self.is_displaying = False

        # Update label to show text
        try:
            self.video_label.configure(
                text=text,
                text_color=text_color
            )
        except Exception:
            pass
    
    def show_placeholder(self):
        """Show default placeholder text"""
        self.show_text(config.INITIAL_VIDEO_MESSAGE, config.COLOR_TEXT_SECONDARY)
    
    def show_camera_ready(self):
        """Show camera ready message"""
        self.show_text(config.CAMERA_READY_MESSAGE, config.COLOR_SUCCESS)
    
    def show_camera_error(self, error_message=""):
        """Show camera error message"""
        if error_message:
            text = f"Camera error: {error_message}"
        else:
            text = "Camera not detected"
        self.show_text(text, config.COLOR_ERROR)
    
    def show_workout_complete(self):
        """Show workout complete message"""
        self.show_text(config.WORKOUT_COMPLETE_MESSAGE, config.COLOR_SUCCESS)
    
    def toggle_mirror(self):
        """Toggle mirror mode on/off"""
        self.mirror_enabled = not self.mirror_enabled
        print(f"Mirror mode: {'ON' if self.mirror_enabled else 'OFF'}")
        return self.mirror_enabled
    
    def set_mirror(self, enabled):
        """Set mirror mode"""
        self.mirror_enabled = enabled
        print(f"Mirror mode: {'ON' if self.mirror_enabled else 'OFF'}")
    
    def clear(self):
        """Clear current image and all references"""
        self.current_ctk_image = None
        self.current_frame = None
        self.is_displaying = False
    
    def is_showing_video(self):
        """Check if currently displaying video frames"""
        return self.is_displaying
    
    def get_current_frame(self):
        """Get the current frame (if available)"""
        return self.current_frame