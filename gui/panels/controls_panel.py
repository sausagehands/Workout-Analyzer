"""
Controls panel with round icon buttons and feedback display
"""
import customtkinter as ctk
import gui.config.constants as config
from gui.widgets.buttons import StyledButton


class ControlsPanel:
    def __init__(self, parent):
        self.parent = parent
        self.controls_area_frame = None
        self.button_container = None
        self.feedback_container = None
        self.start_button = None
        self.stop_button = None
        self.reset_button = None
        self.dashboard_button = None

        # Feedback widgets
        self.controls_feedback_title = None
        self.controls_feedback_text = None
        self.controls_quality_text = None
        self.controls_angle_text = None
        self.controls_feedback_tip = None
        self.back_to_controls_button = None

        self.create_widgets()

    def create_widgets(self):
        """Create controls panel widgets"""
        self.controls_area_frame = ctk.CTkFrame(
            self.parent,
            fg_color="transparent",
            height=config.CONTROLS_HEIGHT,
        )
        self.controls_area_frame.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=(config.OUTER_PADDING_X, config.SECTION_SPACING),
            pady=(0, config.OUTER_PADDING_Y),
        )
        self.controls_area_frame.grid_propagate(False)

        self._create_button_container()
        self._create_feedback_container()

        # Start with buttons visible
        self.show_buttons()

    # ------------------------------------------------------------------
    # Buttons
    # ------------------------------------------------------------------

    def _create_button_container(self):
        """Create container with round StyledButtons"""
        self.button_container = ctk.CTkFrame(
            self.controls_area_frame, fg_color="transparent"
        )
        self.button_container.pack_forget()

        button_center = ctk.CTkFrame(self.button_container, fg_color="transparent")
        button_center.pack(expand=True)

        icon_dir = config.ICON_DIRECTORY

        # --- START ---
        self.start_button = StyledButton(
            button_center,
            round=True,
            size=config.IMAGE_BUTTON_SIZE,
            image_path=f"{icon_dir}/start/normal.png",
            hover_image_path=f"{icon_dir}/start/hover.png",
            disabled_image_path=f"{icon_dir}/start/disabled.png",
            fg_color="transparent",
            hover_color=config.COLOR_SUCCESS_HOVER,
            border_width=config.BORDER_WIDTH_THICK,
            border_color=config.COLOR_SUCCESS_DARK,
            hover_border_color=config.COLOR_SUCCESS,
            command=self._on_start_clicked,
        )
        self.start_button.pack(side="left", padx=config.SECTION_SPACING)

        # # --- STOP ---
        # self.stop_button = StyledButton(
        #     button_center,
        #     round=True,
        #     size=config.IMAGE_BUTTON_SIZE,
        #     image_path=f"{icon_dir}/stop/normal.png",
        #     hover_image_path=f"{icon_dir}/stop/hover.png",
        #     disabled_image_path=f"{icon_dir}/stop/disabled.png",
        #     fg_color="transparent",
        #     hover_color=config.COLOR_ERROR_HOVER,
        #     border_width=config.BORDER_WIDTH_THICK,
        #     border_color=config.COLOR_ERROR_DARK,
        #     hover_border_color=config.COLOR_ERROR,
        #     hide_on_disable=True,
        #     command=self._on_stop_clicked,
        # )
        # self.stop_button.pack(side="left", padx=config.SECTION_SPACING)
        # self.stop_button.disable()

        # --- RESET ---
        # self.reset_button = StyledButton(
        #     button_center,
        #     round=True,
        #     size=config.IMAGE_BUTTON_SIZE,
        #     image_path=f"{icon_dir}/reset/normal.png",
        #     hover_image_path=f"{icon_dir}/reset/hover.png",
        #     disabled_image_path=f"{icon_dir}/reset/disabled.png",
        #     fg_color="transparent",
        #     hover_color=config.COLOR_TEXT_SECONDARY,
        #     border_width=config.BORDER_WIDTH_THICK,
        #     border_color=config.COLOR_SEPARATOR_DARK,
        #     hover_border_color=config.COLOR_SEPARATOR,
        #     command=self._on_reset_clicked,
        # )
        # self.reset_button.pack(side="left", padx=config.SECTION_SPACING)

        # --- DASHBOARD ---
        self.dashboard_button = StyledButton(
            button_center,
            round=True,
            size=config.IMAGE_BUTTON_SIZE,
            image_path=f"{icon_dir}/dashboard/normal.png",
            hover_image_path=f"{icon_dir}/dashboard/hover.png",
            fg_color="transparent",
            hover_color=config.COLOR_SYSTEM_BORDER_HOVER,
            border_width=config.BORDER_WIDTH_THICK,
            border_color=config.COLOR_SYSTEM_BORDER,
            hover_border_color=config.COLOR_SYSTEM_BORDER_HOVER,
            command=self._go_to_dashboard,
        )
        self.dashboard_button.pack(side="left", padx=config.SECTION_SPACING)

    # ------------------------------------------------------------------
    # Feedback
    # ------------------------------------------------------------------

    def _create_feedback_container(self):
        """Create container for exercise feedback"""
        self.feedback_container = ctk.CTkFrame(
            self.controls_area_frame, fg_color="transparent"
        )
        self.feedback_container.pack_forget()

        feedback_frame = ctk.CTkFrame(
            self.feedback_container,
            fg_color=config.COLOR_FRAME_FEEDBACK,
            corner_radius=config.CORNER_RADIUS_LARGE,
            border_width=config.BORDER_WIDTH_THICK,
            border_color=config.COLOR_SEPARATOR,
        )
        feedback_frame.pack(expand=True, fill="both", padx=20, pady=10)

        self._create_feedback_widgets(feedback_frame)

    def _create_feedback_widgets(self, parent):
        """Create feedback display widgets"""
        self.controls_feedback_title = ctk.CTkLabel(
            parent,
            text="LIVE FORM ANALYSIS",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT,
        )
        self.controls_feedback_title.pack(pady=(10, 5))

        self.controls_feedback_text = ctk.CTkLabel(
            parent,
            text="Camera is active. Begin your exercise to see live feedback!",
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL),
            text_color=config.COLOR_TEXT_PRIMARY,
            wraplength=400,
        )
        self.controls_feedback_text.pack(pady=(0, 10))

        self.controls_quality_text = ctk.CTkLabel(
            parent,
            text="Excellent: 0 | Good: 0 | Poor: 0",
            font=ctk.CTkFont(size=config.FONT_SIZE_TINY),
            text_color=config.COLOR_TEXT_SECONDARY,
        )
        self.controls_quality_text.pack(pady=(0, 5))

        self.controls_angle_text = ctk.CTkLabel(
            parent,
            text="Angle: --",
            font=ctk.CTkFont(size=config.FONT_SIZE_TINY),
            text_color=config.COLOR_TEXT_SECONDARY,
        )
        self.controls_angle_text.pack(pady=(0, 5))

        self.controls_feedback_tip = ctk.CTkLabel(
            parent,
            text="Tip: Make sure you're fully visible in the frame",
            font=ctk.CTkFont(size=config.FONT_SIZE_TINY),
            text_color=config.COLOR_TEXT_SECONDARY,
        )
        self.controls_feedback_tip.pack(pady=(0, 10))

        self.back_to_controls_button = ctk.CTkButton(
            parent,
            text="< Back to Controls",
            command=self.show_buttons,
            width=120,
            height=30,
            corner_radius=config.CORNER_RADIUS_SMALL,
            fg_color=config.COLOR_SEPARATOR,
            hover_color=config.COLOR_TEXT_SECONDARY,
            text_color=config.COLOR_TEXT_PRIMARY,
        )
        self.back_to_controls_button.pack(pady=(0, 10))

    # ------------------------------------------------------------------
    # Button event stubs (overridden by app_container)
    # ------------------------------------------------------------------

    def _on_start_clicked(self):
        print("Start clicked")

    def _on_stop_clicked(self):
        print("Stop clicked")

    def _on_reset_clicked(self):
        print("Reset clicked")

    def _go_to_dashboard(self):
        print("Dashboard clicked")

    # ------------------------------------------------------------------
    # Show / hide views
    # ------------------------------------------------------------------

    def show_buttons(self):
        """Show the control buttons"""
        self.feedback_container.pack_forget()
        self.button_container.pack(fill="both", expand=True)

    def show_feedback(self):
        """Show feedback in the controls area"""
        self.button_container.pack_forget()
        self.feedback_container.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Feedback updates
    # ------------------------------------------------------------------

    def update_feedback_display(self, title=None, main_text=None, quality_text=None,
                                angle_text=None, tip=None, title_color=None, text_color=None):
        """Update feedback display content"""
        if title and self.controls_feedback_title:
            self.controls_feedback_title.configure(text=title)
            if title_color:
                self.controls_feedback_title.configure(text_color=title_color)

        if main_text and self.controls_feedback_text:
            self.controls_feedback_text.configure(text=main_text)
            if text_color:
                self.controls_feedback_text.configure(text_color=text_color)

        if quality_text and self.controls_quality_text:
            self.controls_quality_text.configure(text=quality_text)

        if angle_text and self.controls_angle_text:
            self.controls_angle_text.configure(text=angle_text)

        if tip and self.controls_feedback_tip:
            self.controls_feedback_tip.configure(text=tip)

    # ------------------------------------------------------------------
    # Enable / disable helpers
    # ------------------------------------------------------------------

    def enable_start_button(self):
        if self.start_button:
            self.start_button.enable()

    def disable_start_button(self):
        if self.start_button:
            self.start_button.disable()

    def enable_stop_button(self):
        if self.stop_button:
            self.stop_button.enable()

    def disable_stop_button(self):
        if self.stop_button:
            self.stop_button.disable()

    def enable_reset_button(self):
        if self.reset_button:
            self.reset_button.enable()

    def disable_reset_button(self):
        if self.reset_button:
            self.reset_button.disable()

    def enable_dashboard_button(self):
        if self.dashboard_button:
            self.dashboard_button.enable()

    def disable_dashboard_button(self):
        if self.dashboard_button:
            self.dashboard_button.disable()

    # Legacy aliases
    def enable_history_button(self):
        self.enable_dashboard_button()

    def disable_history_button(self):
        self.disable_dashboard_button()

    # ------------------------------------------------------------------
    # Command setters
    # ------------------------------------------------------------------

    def set_start_command(self, command):
        if self.start_button and command:
            self.start_button.configure(command=command)

    def set_stop_command(self, command):
        if self.stop_button and command:
            self.stop_button.configure(command=command)

    def set_reset_command(self, command):
        if self.reset_button and command:
            self.reset_button.configure(command=command)

    def set_dashboard_command(self, command):
        if self.dashboard_button and command:
            self.dashboard_button.configure(command=command)

    # Legacy alias
    def set_history_command(self, command):
        self.set_dashboard_command(command)

    def set_back_to_controls_command(self, command):
        if self.back_to_controls_button and command:
            self.back_to_controls_button.configure(command=command)

    # ------------------------------------------------------------------
    # Panel visibility
    # ------------------------------------------------------------------

    def hide_panel(self):
        if self.controls_area_frame:
            self.controls_area_frame.grid_remove()

    def show_panel(self):
        if self.controls_area_frame:
            self.controls_area_frame.grid()

    def is_visible(self):
        if self.controls_area_frame:
            return self.controls_area_frame.winfo_ismapped()
        return False
