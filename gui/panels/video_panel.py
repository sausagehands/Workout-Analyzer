"""
Video display panel - handles video feed display
"""
import customtkinter as ctk
import gui.config.constants as config
from gui.widgets.video_display import VideoDisplay  # Import from the correct file


class VideoPanel:
    """Panel for displaying video feed"""

    def __init__(self, parent, window):
        """
        Initialize video panel

        Args:
            parent: Parent widget
            window: Main window reference
        """
        self.parent = parent
        self.window = window

        # Create container
        self.container = ctk.CTkFrame(parent, fg_color="transparent")
        self.container.grid(
            row=1, column=0,
            padx=config.OUTER_PADDING_X, pady=config.OUTER_PADDING_Y,
            sticky="nsew"
        )

        # Configure container grid
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Create video label
        self.video_label = ctk.CTkLabel(
            self.container,
            text=config.INITIAL_VIDEO_MESSAGE,
            text_color=config.COLOR_DROPDOWN_LABEL,
            font=ctk.CTkFont(size=config.FONT_SIZE_LARGE),
            fg_color=config.COLOR_STAT_CARD_BG,
            corner_radius=config.CORNER_RADIUS
        )
        self.video_label.grid(row=0, column=0, sticky="nsew")

        # Text overlay (hidden by default, shown on top of video)
        self.overlay_frame = ctk.CTkFrame(
            self.container,
            fg_color=config.COLOR_BACKGROUND,
            corner_radius=config.CORNER_RADIUS,
            border_width=2,
            border_color=config.COLOR_SEPARATOR
        )
        self.overlay_label = ctk.CTkLabel(
            self.overlay_frame,
            text="",
            font=ctk.CTkFont(size=config.FONT_SIZE_XL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP
        )
        self.overlay_label.pack(padx=30, pady=20)

        # Create video display handler - USE THE UPDATED ONE
        self.video_display = VideoDisplay(self.video_label, window)
    
    def update_video_frame(self, frame):
        """Update video frame display"""
        self._hide_overlay()
        return self.video_display.update_frame(frame)
    
    def show_placeholder(self):
        """Show placeholder text"""
        self.video_display.show_placeholder()
    
    def show_camera_ready(self):
        """Show camera ready message"""
        self.video_display.show_camera_ready()
    
    def show_camera_error(self, error_message=""):
        """Show camera error message"""
        self.video_display.show_camera_error(error_message)
        
    def show_text(self, text: str, text_color: str = None):
        """
        Display text overlay on top of the video panel

        Args:
            text: Message to display
            text_color: Optional text color (defaults to secondary text color)
        """
        if text_color is None:
            text_color = config.COLOR_TEXT_SECONDARY
        self.overlay_label.configure(text=text, text_color=text_color)
        self.overlay_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.overlay_frame.lift()

    def _hide_overlay(self):
        """Hide the text overlay"""
        self.overlay_frame.place_forget()
    
    def show_workout_complete(self):
        """Show workout complete message"""
        self.video_display.show_workout_complete()
    
    def clear(self):
        """Clear video display"""
        self.video_display.clear()
    
    def is_showing_video(self):
        """Check if currently showing video"""
        return self.video_display.is_showing_video()
    
    def get_current_frame(self):
        """Get current video frame"""
        return self.video_display.get_current_frame()
    
    def toggle_mirror(self):
        """Toggle mirror mode"""
        if hasattr(self.video_display, 'toggle_mirror'):
            return self.video_display.toggle_mirror()
        return None

    def set_mirror(self, enabled):
        """Set mirror mode"""
        if hasattr(self.video_display, 'set_mirror'):
            self.video_display.set_mirror(enabled)

    def is_mirror_enabled(self):
        """Check if mirror is enabled"""
        if hasattr(self.video_display, 'mirror_enabled'):
            return self.video_display.mirror_enabled
        return False

    def set_column_span(self, columnspan):
        """Set the column span for the video container (used when panels hide)"""
        current_grid_info = self.container.grid_info()
        self.container.grid(
            row=current_grid_info.get('row', 1),
            column=current_grid_info.get('column', 0),
            columnspan=columnspan,
            padx=config.OUTER_PADDING_X,
            pady=config.OUTER_PADDING_Y,
            sticky="nsew"
        )
