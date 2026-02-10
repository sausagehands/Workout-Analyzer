import customtkinter as ctk
from typing import Optional, Dict, Any
from config.user_config import UserConfig
from gui.config.constants import (
    COLOR_BACKGROUND, COLOR_STAT_CARD_BG, COLOR_TEXT_HEADER,
    COLOR_ACCENT, COLOR_DROPDOWN_LABEL, COLOR_SECONDARY_BUTTON,
    COLOR_SECONDARY_BUTTON_HOVER, COLOR_TEXT_POP2, COLOR_SUCCESS,
)

import gui.config.constants as config
from gui.widgets.buttons import StyledButton


class SetupWizard:
    """Multi-step setup wizard with validation + hooks"""

    def __init__(self, user_config: UserConfig, on_complete_callback):
        self.user_config = user_config
        self.on_complete = on_complete_callback
        self.icon_dir = config.ICON_DIRECTORY

        # ---------- STEP REGISTRY ----------
        self.steps = [
            {
                "render": self._show_waiver,
                "validate": self._validate_waiver,
                "on_next": self._save_waiver,
            },
            {"render": self._show_welcome},
            {
                "render": self._show_profile_setup,
                "on_next": self._save_profile,
            },
            {
                "render": self._show_preferences,
                "on_next": self._save_preferences,
            },
            {"render": self._show_completion},
        ]

        self.total_steps = len(self.steps)
        self.current_step = 0

        # ---------- WINDOW ----------
        self.window = ctk.CTkToplevel()
        self.window.title("Welcome to AI Workout Analyzer")
        self.window.geometry("720x520")
        self.window.configure(fg_color=COLOR_BACKGROUND)
        self.window.grab_set()

        # Handle window close (X button) - exit program if no waiver on record
        self.window.protocol("WM_DELETE_WINDOW", self._on_wizard_closed)

        self._build_ui()
        self._show_step(0)

    # ==========================================================
    # UI SCAFFOLDING
    # ==========================================================

    def _build_ui(self):
        # Progress
        self.progress_frame = ctk.CTkFrame(self.window, fg_color=COLOR_STAT_CARD_BG, corner_radius=config.CORNER_RADIUS)
        self.progress_frame.pack(fill="x", padx=20, pady=10)

        self.progress_label = ctk.CTkLabel(
            self.progress_frame, text_color=COLOR_DROPDOWN_LABEL
        )
        self.progress_label.pack()

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame, progress_color=COLOR_ACCENT
        )
        self.progress_bar.pack(fill="x", pady=5)

        # Content - outer frame to hold scrollable content
        self.content_outer = ctk.CTkFrame(self.window, fg_color=COLOR_STAT_CARD_BG, corner_radius=config.CORNER_RADIUS)
        self.content_outer.pack(fill="both", expand=True, padx=20, pady=10)

        # Content frame
        self.content_frame = ctk.CTkFrame(
            self.content_outer,
            fg_color="transparent"
        )
        self.content_frame.pack(fill="both", expand=True)

        # Navigation
        self.nav_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        self.nav_frame.pack(fill="x", padx=20, pady=10)

        self.back_button = StyledButton(
            self.nav_frame,
            round=False,
            size=config.IMAGE_BUTTON_SIZE,
            image_path=f"{self.icon_dir}/previous/normal.png",
            hover_image_path=f"{self.icon_dir}/previous/hover.png",
            width=config.CALENDAR_NAV_BUTTON_SIZE,
            height=config.CALENDAR_NAV_BUTTON_SIZE,
            fg_color=config.COLOR_ACCENT,
            hover_color=config.COLOR_TEXT_POP2,
            hide_on_disable=True,
            state="disabled",
            command=self._prev_step,
            
        )
        self.back_button.pack(side="left")

        self.next_button = StyledButton(
            self.nav_frame,
            size=config.IMAGE_BUTTON_SIZE,
            image_path=f"{self.icon_dir}/next/normal.png",
            hover_image_path=f"{self.icon_dir}/next/hover.png",
            width=config.CALENDAR_NAV_BUTTON_SIZE,
            height=config.CALENDAR_NAV_BUTTON_SIZE,
            fg_color=config.COLOR_ACCENT,
            hover=config.COLOR_TEXT_POP2,
            hover_color= config.COLOR_TEXT_POP2,
            text_color= config.COLOR_TEXT_POP,
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            hide_on_disable=True,
            command=self._next_step,
        )
        self.next_button.pack(side="right")

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # ==========================================================
    # STEP NAVIGATION
    # ==========================================================

    def _show_step(self, index: int):
        self.current_step = index
        self._clear_content()

        self.progress_label.configure(
            text=f"Step {index + 1} of {self.total_steps}"
        )
        self.progress_bar.set((index + 1) / self.total_steps)

        self.back_button.configure(
            state="normal" if index > 0 else "disabled"
        )

        self.next_button.configure(
            text="Finish" if index == self.total_steps - 1 else ""
        )

        self.steps[index]["render"]()
        self._update_next_button_state()

    def _next_step(self):
        if not self._validate_current_step():
            return

        self._run_hook("on_next")

        if self.current_step < self.total_steps - 1:
            self._show_step(self.current_step + 1)
        else:
            self._finish_setup()

    def _prev_step(self):
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    # ==========================================================
    # HOOK HELPERS
    # ==========================================================

    def _run_hook(self, hook_name: str):
        step = self.steps[self.current_step]
        if hook_name in step:
            step[hook_name]()

    def _validate_current_step(self) -> bool:
        step = self.steps[self.current_step]
        if "validate" in step:
            return step["validate"]()
        return True

    def _update_next_button_state(self):
        self.next_button.configure(
            state="normal" if self._validate_current_step() else "disabled"
        )

    # ==========================================================
    # STEP 0 — LIABILITY WAIVER
    # ==========================================================

    def _show_waiver(self):
        ctk.CTkLabel(
            self.content_frame,
            text="Liability Waiver",
            font=ctk.CTkFont(size=config.FONT_SIZE_TITLE, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_TEXT_HEADER,
        ).pack(pady=10)

        waiver_text = (
            "By using this application, you acknowledge that physical exercise "
            "involves inherent risks. This software does not provide medical advice.\n\n"
            "You agree that the developers and distributors are not responsible "
            "for injuries, damages, or losses resulting from use of this app."
        )

        textbox = ctk.CTkTextbox(
            self.content_frame, 
            height=220, 
            wrap="word",
            fg_color=COLOR_BACKGROUND, 
            text_color=COLOR_DROPDOWN_LABEL,
            corner_radius=config.CORNER_RADIUS, 
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD)
        )
        textbox.insert("1.0", waiver_text)
        textbox.configure(state="disabled")
        textbox.pack(fill="x", padx=20, pady=10)

        self.waiver_accepted = ctk.BooleanVar(value=False)

        ctk.CTkCheckBox(
            self.content_frame,
            text="I have read and agree to the liability waiver",
            variable=self.waiver_accepted,
            command=lambda: self.window.after(1, self._update_next_button_state),
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_DROPDOWN_LABEL,
            fg_color=COLOR_ACCENT,
            hover_color=config.COLOR_STAT_CARD_BG2,
        ).pack(pady=10)


    def _validate_waiver(self) -> bool:
        return self.waiver_accepted.get()

    def _save_waiver(self):
        self.user_config.set_legal_acceptance(
            accepted=True,
            waiver_version="v1.0",
        )

    # ==========================================================
    # STEP 1 — WELCOME
    # ==========================================================

    def _show_welcome(self):
        ctk.CTkLabel(
            self.content_frame,
            text="Welcome!",
            font=ctk.CTkFont(size=config.FONT_SIZE_TITLE, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_TEXT_HEADER,
        ).pack(pady=30)

        ctk.CTkLabel(
            self.content_frame,
            text="Let's get you set up for your first workout.",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_DROPDOWN_LABEL,
        ).pack(pady=10)

    # ==========================================================
    # STEP 2 — PROFILE (SIMPLIFIED - NO FITNESS_LEVEL OR WEIGHT)
    # ==========================================================

    def _show_profile_setup(self):
        ctk.CTkLabel(
            self.content_frame,
            text="Create Your Profile",
            font=ctk.CTkFont(size=config.FONT_SIZE_TITLE, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_TEXT_HEADER,
        ).pack(pady=20)

        self.name_entry = ctk.CTkEntry(
            self.content_frame, 
            placeholder_text="Name",
            fg_color=COLOR_BACKGROUND, 
            text_color=COLOR_DROPDOWN_LABEL,
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            border_color=COLOR_ACCENT,
        )
        self.name_entry.pack(pady=10)

        # self.height_entry = ctk.CTkEntry(
        #     self.content_frame, placeholder_text="Height (cm, optional)",
        #     fg_color=COLOR_BACKGROUND, text_color=COLOR_DROPDOWN_LABEL,
        #     border_color=COLOR_ACCENT,
        # )
        # self.height_entry.pack(pady=8)

    def _save_profile(self):
        name = self.name_entry.get()

        # try:
        #     height = float(self.height_entry.get()) if self.height_entry.get() else None
        # except ValueError:
        #     height = None

        self.user_config.set_profile(
            name=name or "Hottie",
            # height_cm=height,
        )
        
        # Mark setup as complete here if you're skipping preferences
        self.user_config.mark_setup_complete()

    # ==========================================================
    # STEP 3 — PREFERENCES
    # ==========================================================

    def _show_preferences(self):
        """Show workout preferences setup"""
        ctk.CTkLabel(
            self.content_frame,
            text="Workout Preferences",
            font=ctk.CTkFont(size=config.FONT_SIZE_TITLE, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_TEXT_HEADER,
        ).pack(pady=20)

        # Default Exercise Preference
        ctk.CTkLabel(
            self.content_frame,
            text="Default Exercise Type:",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP,
        ).pack(pady=(10, 5), anchor="w")

        # Exercise selection
        self.exercise_var = ctk.StringVar(value="squat")

        exercise_frame = ctk.CTkFrame(self.content_frame, fg_color=config.COLOR_STAT_CARD_BG, corner_radius=config.CORNER_RADIUS)
        exercise_frame.pack(fill="x", padx=20, pady=5)

        exercises = ["squat", "pushup", "curl"]
        for exercise in exercises:
            ctk.CTkRadioButton(
                exercise_frame,
                text=exercise.title(),
                variable=self.exercise_var,
                value=exercise,
                font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
                text_color=COLOR_DROPDOWN_LABEL,
                fg_color=COLOR_ACCENT,
                hover_color=config.COLOR_STAT_CARD_BG2
            ).pack(anchor="w", pady=2, padx=10)

        # Workout Duration
        # ctk.CTkLabel(
        #     self.content_frame,
        #     text="Typical Workout Duration:",
        #     font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
        #     text_color=config.COLOR_TEXT_POP,
        # ).pack(pady=(20, 5), anchor="w")

        # self.duration_var = ctk.StringVar(value="30")

        # duration_frame = ctk.CTkFrame(self.content_frame, fg_color=COLOR_BACKGROUND, corner_radius=8)
        # duration_frame.pack(fill="x", padx=20, pady=5)

        # durations = ["15", "30", "45", "60"]
        # for duration in durations:
        #     ctk.CTkRadioButton(
        #         duration_frame,
        #         text=f"{duration} minutes",
        #         variable=self.duration_var,
        #         value=duration,
        #         font=ctk.CTkFont(size=12),
        #         text_color=COLOR_DROPDOWN_LABEL,
        #         fg_color=COLOR_ACCENT,
        #     ).pack(anchor="w", pady=2, padx=10)

        # Form Feedback Toggle
        ctk.CTkLabel(
            self.content_frame,
            text="Feedback Settings:",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP,
        ).pack(pady=(20, 5), anchor="w")

        self.feedback_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            self.content_frame,
            text="Enable real-time form feedback",
            variable=self.feedback_var,
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_DROPDOWN_LABEL,
            fg_color=COLOR_ACCENT,
            hover_color=config.COLOR_STAT_CARD_BG2
        ).pack(anchor="w", padx=20, pady=5)

        # Audio Cues
        # self.audio_var = ctk.BooleanVar(value=True)
        # ctk.CTkCheckBox(
        #     self.content_frame,
        #     text="Enable audio feedback cues",
        #     variable=self.audio_var,
        #     font=ctk.CTkFont(size=12),
        #     text_color=COLOR_DROPDOWN_LABEL,
        #     fg_color=COLOR_ACCENT,
        #     hover_color=config.COLOR_STAT_CARD_BG2
        # ).pack(anchor="w", padx=20, pady=5)

    def _save_preferences(self):
        """Save preferences to user config"""
        # Make sure preferences section exists
        if "preferences" not in self.user_config.config:
            self.user_config.config["preferences"] = {}

        # Update preferences
        prefs = self.user_config.config["preferences"]
        prefs["preferred_exercise"] = self.exercise_var.get()
        prefs["enable_feedback"] = self.feedback_var.get()

        # Also save to workout.default_exercise so dashboard picks it up
        self.user_config.set('workout', 'default_exercise', self.exercise_var.get(), save=False)

        # Mark setup as complete using the proper method
        self.user_config.mark_setup_complete()

        # Save to file - call the correct method
        self.user_config._save_config()

    # ==========================================================
    # STEP 4 — COMPLETION
    # ==========================================================

    def _show_completion(self):
        """Show completion screen"""
        ctk.CTkLabel(
            self.content_frame,
            text="Setup Complete!",
            font=ctk.CTkFont(size=config.FONT_SIZE_TITLE, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_TEXT_HEADER,
        ).pack(pady=40)

        ctk.CTkLabel(
            self.content_frame,
            text="You're ready to start your first workout!",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_DROPDOWN_LABEL,
        ).pack(pady=10)

        ctk.CTkLabel(
            self.content_frame,
            text="Click 'Finish' to begin your fitness journey.",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=COLOR_TEXT_POP2,
        ).pack(pady=10)

    def _on_wizard_closed(self):
        """Handle wizard window being closed (X button).
        Exit the whole program since setup is incomplete."""
        if not self.user_config.has_accepted_waiver("v1.0"):
            print("Setup wizard closed without accepting liability waiver. Exiting.")
        else:
            print("Setup wizard closed before completion. Exiting.")
        self.window.destroy()
        # Quit the hidden root mainloop so the program fully exits
        try:
            self.window.master.quit()
            self.window.master.destroy()
        except Exception:
            pass

    def _finish_setup(self):
        """Complete the setup process"""
        # Mark setup as complete (in case it wasn't already)
        self.user_config.mark_setup_complete()

        # Hide the wizard window first, then destroy after a brief delay
        # to let pending CTk internal after callbacks flush before destruction
        self.window.withdraw()
        self.window.after(200, self._cleanup_and_complete)

    def _cleanup_and_complete(self):
        """Destroy wizard window and trigger completion callback"""
        self.window.destroy()
        self.on_complete()