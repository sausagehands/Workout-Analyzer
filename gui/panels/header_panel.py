"""
Header panel component
Supports normal mode and workout mode with live stats display
"""
import customtkinter as ctk
import gui.config.constants as config
from gui.widgets.buttons import StyledButton


class HeaderPanel:
    def __init__(self, parent, title_text="Workout Angles", on_settings_click=None, on_back_click=None, on_stop_click=None):
        self.parent = parent
        self.title_text = title_text
        self.title_label = None
        self.on_settings_click = on_settings_click
        self.on_back_click = on_back_click
        self.on_stop_click = on_stop_click

        # Workout mode widgets
        self.is_workout_mode = False
        self.normal_content_frame = None
        self.workout_content_frame = None
        self.home_button = None
        self.settings_button = None
        self.stop_button = None
        self.feedback_label = None
        self.angle_label = None
        self.reps_label = None

        self.create_widgets()

    def create_widgets(self):
        """Create header widgets"""
        self.header_frame = ctk.CTkFrame(
            self.parent,
            fg_color=config.COLOR_FRAME_HEADER,
            height=config.HEADER_HEIGHT,
            corner_radius=config.CORNER_RADIUS_LARGE
        )
        self.header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(config.OUTER_PADDING_X, config.SECTION_SPACING),
            pady=(config.OUTER_PADDING_Y, 0)
        )
        self.header_frame.grid_propagate(False)

        # Create both content frames (normal and workout mode)
        self._create_normal_content()
        self._create_workout_content()

        # Start in normal mode
        self.show_normal_mode()

    def _create_normal_content(self):
        """Create normal mode content (home + title + settings)"""
        self.normal_content_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")

        icon_dir = config.ICON_DIRECTORY

        # Home button on the left (only if callback provided)
        # if self.on_back_click:
        #     self.home_button = StyledButton(
        #         self.normal_content_frame,
        #         round=True,
        #         size=40,
        #         image_path=f"{icon_dir}/home.png",
        #         fg_color="transparent",
        #         hover_color=config.COLOR_ACCENT_HOVER,
        #         border_width=config.BORDER_WIDTH_NORMAL,
        #         border_color=config.COLOR_ACCENT,
        #         hover_border_color=config.COLOR_ACCENT_HOVER,
        #         command=self._on_back_clicked,
        #     )
        #     self.home_button.pack(side="left", pady=config.INNER_PADDING, padx=(10, 15))

        # Title
        self.title_label = ctk.CTkLabel(
            self.normal_content_frame,
            text=self.title_text,
            font=ctk.CTkFont(size=config.FONT_SIZE_TITLE, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_HEADER
        )
        self.title_label.pack(side="left", pady=config.INNER_PADDING, padx=(10, 0))

        # Settings button on the right
        if self.on_settings_click:
            self.settings_button = StyledButton(
                self.normal_content_frame,
                round=True,
                size=40,
                image_path=f"{icon_dir}/settings/normal.png",
                hover_image_path=f"{icon_dir}/settings/hover.png",
                fg_color="transparent",
                hover_color=config.COLOR_SYSTEM_BORDER_HOVER,
                border_width=config.BORDER_WIDTH_NORMAL,
                border_color=config.COLOR_SYSTEM_BORDER,
                hover_border_color=config.COLOR_SYSTEM_BORDER_HOVER,
                command=self._on_settings_clicked,
            )
            self.settings_button.pack(side="right", pady=config.INNER_PADDING, padx=(0, 10))

    def _create_workout_content(self):
        """Create workout mode content (Stop | Feedback | Angle | Reps)"""
        self.workout_content_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")

        # Configure grid for 4 sections
        self.workout_content_frame.grid_columnconfigure(0, weight=0)  # Stop button - fixed
        self.workout_content_frame.grid_columnconfigure(1, weight=2)  # Feedback - larger
        self.workout_content_frame.grid_columnconfigure(2, weight=1)  # Angle
        self.workout_content_frame.grid_columnconfigure(3, weight=1)  # Reps

        icon_dir = config.ICON_DIRECTORY

        # Section 1: Stop button
        self.stop_button = StyledButton(
            self.workout_content_frame,
            round=True,
            size=40,
            image_path=f"{icon_dir}/stop/normal.png",
            hover_image_path=f"{icon_dir}/stop/hover.png",
            fg_color="transparent",
            hover_color=config.COLOR_ERROR_HOVER,
            border_width=config.BORDER_WIDTH_NORMAL,
            border_color=config.COLOR_ERROR_DARK,
            hover_border_color=config.COLOR_ERROR,
            command=self._on_stop_clicked,
        )
        self.stop_button.grid(row=0, column=0, padx=(10, 15), pady=8, sticky="w")

        # Section 2: Feedback display
        feedback_frame = ctk.CTkFrame(self.workout_content_frame, fg_color="transparent")
        feedback_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.feedback_label = ctk.CTkLabel(
            feedback_frame,
            text="Ready for first rep!",
            font=ctk.CTkFont(size=config.FONT_SIZE_LARGE, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP2,
            wraplength=300
        )
        self.feedback_label.pack(expand=True, fill="both", padx=5)

        # Section 3: Angle display
        angle_frame = ctk.CTkFrame(self.workout_content_frame, fg_color="transparent")
        angle_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        angle_inner = ctk.CTkFrame(angle_frame, fg_color="transparent")
        angle_inner.pack(expand=True)

        self.angle_prefix_label = ctk.CTkLabel(
            angle_inner,
            text="ANGLE:",
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT,
            
        )
        self.angle_prefix_label.pack(side="left", padx=(5, 4))

        self.angle_label = ctk.CTkLabel(
            angle_inner,
            text="--°",
            font=ctk.CTkFont(size=config.FONT_SIZE_LARGE, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP,
        )
        self.angle_label.pack(side="left", padx=(0, 5))

        # Section 4: Reps display
        reps_frame = ctk.CTkFrame(self.workout_content_frame, fg_color="transparent")
        reps_frame.grid(row=0, column=3, padx=(5, 10), pady=5, sticky="nsew")

        reps_inner = ctk.CTkFrame(reps_frame, fg_color="transparent")
        reps_inner.pack(expand=True)

        self.reps_prefix_label = ctk.CTkLabel(
            reps_inner,
            text="REPS:",
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT,
        )
        self.reps_prefix_label.pack(side="left", padx=(5, 4))

        self.reps_label = ctk.CTkLabel(
            reps_inner,
            text="0",
            font=ctk.CTkFont(size=config.FONT_SIZE_LARGE, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP,
        )
        self.reps_label.pack(side="left", padx=(0, 5))

    def _on_settings_clicked(self):
        """Handle settings button click"""
        if self.on_settings_click:
            self.on_settings_click()

    def _on_back_clicked(self):
        """Handle back button click"""
        if self.on_back_click:
            self.on_back_click()

    def _on_stop_clicked(self):
        """Handle stop button click in workout mode"""
        if self.on_stop_click:
            self.on_stop_click()

    def set_settings_command(self, command):
        """Set the settings button command"""
        self.on_settings_click = command

    def set_back_command(self, command):
        """Set the back button command"""
        self.on_back_click = command

    def set_stop_command(self, command):
        """Set the stop button command for workout mode"""
        self.on_stop_click = command

    def update_title(self, new_title):
        """Update header title"""
        self.title_text = new_title
        if self.title_label:
            self.title_label.configure(text=new_title)

    # =========================================================================
    # MODE SWITCHING
    # =========================================================================

    def show_normal_mode(self):
        """Switch to normal mode (home + title + settings)"""
        self.is_workout_mode = False
        self.workout_content_frame.pack_forget()
        self.normal_content_frame.pack(fill="both", expand=True)

    def show_workout_mode(self):
        """Switch to workout mode (Stop | Feedback | Angle | Reps)"""
        self.is_workout_mode = True
        self.normal_content_frame.pack_forget()
        self.workout_content_frame.pack(fill="both", expand=True)
        # Reset displays
        self.update_workout_feedback("Ready for first rep!", config.COLOR_TEXT_POP2)
        self.update_workout_angle(None)
        self.update_workout_reps(0)

    # =========================================================================
    # WORKOUT MODE UPDATES
    # =========================================================================

    def update_workout_feedback(self, text, color=None):
        """Update feedback text in workout mode"""
        if self.feedback_label:
            self.feedback_label.configure(text=text)
            if color:
                self.feedback_label.configure(text_color=color)

    def update_workout_angle(self, angle):
        """Update angle display in workout mode"""
        if self.angle_label:
            if angle is not None:
                self.angle_label.configure(text=f"{angle:.1f}°")
            else:
                self.angle_label.configure(text="--°")

    def update_workout_reps(self, count):
        """Update reps display in workout mode"""
        if self.reps_label:
            self.reps_label.configure(text=str(count))

    # =========================================================================
    # HEADER FRAME ACCESS (for spanning columns)
    # =========================================================================

    def set_column_span(self, columnspan):
        """Set the column span for the header (used when panels hide)"""
        current_grid_info = self.header_frame.grid_info()
        self.header_frame.grid(
            row=current_grid_info.get('row', 0),
            column=current_grid_info.get('column', 0),
            columnspan=columnspan,
            sticky="ew",
            padx=(config.OUTER_PADDING_X, config.OUTER_PADDING_X if columnspan > 1 else config.SECTION_SPACING),
            pady=(config.OUTER_PADDING_Y, 0)
        )
