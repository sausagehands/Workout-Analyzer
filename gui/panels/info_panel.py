"""
Right sidebar information panel - UPDATED VERSION with exercise stats and history button
Lifetime stats moved to Dashboard
"""
import customtkinter as ctk
import gui.config.constants as config
from gui.widgets.exercise_selector import ExerciseSelector
from gui.widgets.buttons import StyledButton


class InfoPanel:
    def __init__(self, parent, on_exercise_changed=None, on_history_click=None):
        self.parent = parent
        self.on_exercise_changed = on_exercise_changed
        self.on_history_click = on_history_click
        
        self.icon_dir = config.ICON_DIRECTORY

        self.rep_display = None
        self.state_display = None
        self.feedback_display = None
        self.exercise_selector = None
        self.exercise_stats_display = None
        self.history_button = None

        self.create_widgets()

    def create_widgets(self):
        """Create info panel widgets with scrollable content"""
        self.info_frame = ctk.CTkFrame(
            self.parent,
            fg_color=config.COLOR_STAT_CARD_BG,
            corner_radius=config.CORNER_RADIUS_LARGE,
            border_width=2,
            border_color=config.COLOR_SEPARATOR
        )
        self.info_frame.grid(
            row=0,
            column=1,
            rowspan=3,
            sticky="nsew",
            padx=(config.SECTION_SPACING, config.OUTER_PADDING_X),
            pady=config.OUTER_PADDING_Y
        )
        # Alias for backward compatibility
        info_frame = self.info_frame

        # Allow the frame to resize with grid
        info_frame.grid_propagate(True)

        # Content frame
        content_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_rep_counter(content_frame)
        self._create_exercise_selector(content_frame)
        self._create_state_display(content_frame)
        self._create_feedback_display(content_frame)
        self._create_exercise_stats(content_frame)
        self._create_history_button(content_frame)
        # self._create_quick_tips(content_frame)

    def _create_rep_counter(self, parent):
        """Create repetition counter section"""
        rep_label = ctk.CTkLabel(
            parent,
            text="REPS",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT
        )
        rep_label.pack(pady=(0, 10))

        self.rep_display = ctk.CTkLabel(
            parent,
            text="0",
            font=ctk.CTkFont(size=config.FONT_SIZE_REP_DISPLAY, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP
        )
        self.rep_display.pack(pady=(0, 25))

        separator = ctk.CTkFrame(parent, height=2, fg_color=config.COLOR_SEPARATOR)
        separator.pack(fill="x", pady=15)

    def _create_exercise_selector(self, parent):
        """Create exercise selector using ExerciseSelector widget"""
        # Use the ExerciseSelector widget instead of creating manually
        self.exercise_selector = ExerciseSelector(
            parent,
            initial_exercise="Squats",
            on_change_callback=self._handle_exercise_change
        )
        self.exercise_selector.pack(pady=(0, 25))

        separator = ctk.CTkFrame(parent, height=2, fg_color=config.COLOR_SEPARATOR)
        separator.pack(fill="x", pady=15)

    def _handle_exercise_change(self, exercise):
        """Handle exercise change and update stats"""
        if self.on_exercise_changed:
            self.on_exercise_changed(exercise)

    def _create_state_display(self, parent):
        """Create current state display"""
        state_label = ctk.CTkLabel(
            parent,
            text="CURRENT STATE",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT
        )
        state_label.pack(pady=(0, 10))

        self.state_display = ctk.CTkLabel(
            parent,
            text="READY",
            font=ctk.CTkFont(size=config.FONT_SIZE_STATE_DISPLAY, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_DROPDOWN_LABEL
        )
        self.state_display.pack(pady=(0, 25))

        separator = ctk.CTkFrame(parent, height=2, fg_color=config.COLOR_SEPARATOR)
        separator.pack(fill="x", pady=15)

    def _create_feedback_display(self, parent):
        """Create form feedback display"""
        feedback_label = ctk.CTkLabel(
            parent,
            text="FORM FEEDBACK",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT
        )
        feedback_label.pack(pady=(0, 10))

        self.feedback_display = ctk.CTkLabel(
            parent,
            text="Start exercising to see feedback",
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_DROPDOWN_LABEL,
            wraplength=200
        )
        self.feedback_display.pack(pady=(0, 10))

        separator = ctk.CTkFrame(parent, height=2, fg_color=config.COLOR_SEPARATOR)
        separator.pack(fill="x", pady=15)

    def _create_exercise_stats(self, parent):
        """Create exercise-specific stats display"""
        stats_label = ctk.CTkLabel(
            parent,
            text="EXERCISE STATS",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT
        )
        stats_label.pack(pady=(0, 10))

        self.exercise_stats_display = ctk.CTkLabel(
            parent,
            text="Select an exercise to see stats",
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_DROPDOWN_LABEL,
            wraplength=200,
            justify="left"
        )
        self.exercise_stats_display.pack(pady=(0, 10))

        separator = ctk.CTkFrame(parent, height=2, fg_color=config.COLOR_SEPARATOR)
        separator.pack(fill="x", pady=15)

    def _create_history_button(self, parent):
        """Create history button"""
        self.history_button = StyledButton(
            parent,
            round=True,
            size=config.IMAGE_BUTTON_SIZE,
            image_path=f"{self.icon_dir}/history/normal.png",
            hover_image_path=f"{self.icon_dir}/history/hover.png",
            fg_color="transparent",
            hover_color=config.COLOR_SYSTEM_BORDER_HOVER,
            border_width=config.BORDER_WIDTH_THICK,
            border_color=config.COLOR_SYSTEM_BORDER_HOVER,
            hover_border_color=config.COLOR_SYSTEM_BORDER_HOVER,
            command=self._on_history_click
        )
        self.history_button.pack(pady=(0, 15))

        separator = ctk.CTkFrame(parent, height=2, fg_color=config.COLOR_SEPARATOR)
        separator.pack(fill="x", pady=15)

    def _on_history_click(self):
        """Handle history button click"""
        if self.on_history_click:
            self.on_history_click()

    # def _create_quick_tips(self, parent):
    #     """Create quick tips section"""
    #     tips_label = ctk.CTkLabel(
    #         parent,
    #         text="QUICK TIPS",
    #         font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
    #         text_color=config.COLOR_ACCENT
    #     )
    #     tips_label.pack(pady=(0, 10))

    #     tips_text = ctk.CTkLabel(
    #         parent,
    #         text="Stand 6-8 ft from camera\nWear contrasting clothing\nEnsure good lighting\nFace camera directly",
    #         font=ctk.CTkFont(size=config.FONT_SIZE_TINY),
    #         text_color=config.COLOR_TEXT_SECONDARY,
    #         justify="left"
    #     )
    #     tips_text.pack(pady=(0, 10))

    # Updated methods using ExerciseSelector
    def connect_exercise_handler(self, handler):
        """Connect exercise dropdown handler"""
        if self.exercise_selector and handler:
            self.exercise_selector.set_change_callback(handler)

    def set_exercise(self, exercise):
        """Set current exercise"""
        if self.exercise_selector:
            self.exercise_selector.set_exercise(exercise)

    def get_exercise(self):
        """Get current exercise"""
        return self.exercise_selector.get_exercise() if self.exercise_selector else "Squats"

    def get_backend_exercise_type(self, display_name=None):
        """Get backend exercise type"""
        if self.exercise_selector:
            return self.exercise_selector.get_backend_type(display_name)
        return "squat"

    def enable_dropdown(self):
        """Enable exercise dropdown"""
        if self.exercise_selector:
            self.exercise_selector.enable()

    def disable_dropdown(self):
        """Disable exercise dropdown"""
        if self.exercise_selector:
            self.exercise_selector.disable()

    def enable_history_button(self):
        """Enable history button"""
        if self.history_button:
            self.history_button.configure(state="normal")

    def disable_history_button(self):
        """Disable history button"""
        if self.history_button:
            self.history_button.configure(state="disabled")

    def set_history_command(self, command):
        """Set history button command"""
        self.on_history_click = command

    # Existing methods remain the same
    def update_rep_count(self, count):
        """Update rep counter display"""
        if self.rep_display:
            self.rep_display.configure(text=str(count))

    def update_state(self, state, color=None):
        """Update current state display"""
        if self.state_display:
            if color is None:
                color = config.COLOR_WARNING
            self.state_display.configure(text=state, text_color=color)

    def update_feedback(self, feedback, color=None):
        """Update form feedback display"""
        if self.feedback_display:
            if color is None:
                color = config.COLOR_DROPDOWN_LABEL
            # Convert BGR tuple to hex string if needed (for colors from cv/form_analysis)
            if isinstance(color, tuple) and len(color) == 3:
                b, g, r = color
                color = f"#{r:02x}{g:02x}{b:02x}"
            self.feedback_display.configure(text=feedback, text_color=color)

    def update_exercise_stats(self, stats_text):
        """Update exercise-specific statistics"""
        if self.exercise_stats_display:
            self.exercise_stats_display.configure(text=stats_text)

    # Legacy method for backward compatibility
    def update_lifetime_stats(self, stats_text):
        """Legacy method - now updates exercise stats instead"""
        self.update_exercise_stats(stats_text)

    # =========================================================================
    # PANEL VISIBILITY (for workout mode)
    # =========================================================================

    def hide_panel(self):
        """Hide the entire info panel"""
        # The info_frame is created in create_widgets, we need to store a reference
        if hasattr(self, 'info_frame') and self.info_frame:
            self.info_frame.grid_remove()

    def show_panel(self):
        """Show the entire info panel"""
        if hasattr(self, 'info_frame') and self.info_frame:
            self.info_frame.grid()

    def is_visible(self):
        """Check if panel is visible"""
        if hasattr(self, 'info_frame') and self.info_frame:
            return self.info_frame.winfo_ismapped()
        return False
