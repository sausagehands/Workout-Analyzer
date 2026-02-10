"""
Dashboard with workout calendar, start workout controls, and lifetime stats
Uses grid layout with constants for auto-resizing
"""
import customtkinter as ctk
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Callable
import calendar
import gui.config.constants as config
from gui.widgets.buttons import StyledButton
from gui.widgets.exercise_selector import ExerciseSelector


class Dashboard:
    """Main dashboard with calendar, start controls, and stats"""

    def __init__(self, parent_frame, db, user_config, on_start_workout: Optional[Callable] = None, on_settings_click: Optional[Callable] = None):
        """
        Initialize dashboard

        Args:
            parent_frame: Parent CTk frame
            db: WorkoutDatabase instance
            user_config: UserConfig instance
            on_start_workout: Callback when start button clicked (exercise_name) -> None
            on_settings_click: Callback when settings button clicked
        """
        self.parent = parent_frame
        self.db = db
        self.user_config = user_config
        self.on_start_workout = on_start_workout
        self.on_settings_click = on_settings_click
        
        self.icon_dir = config.ICON_DIRECTORY

        # Current calendar state
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.workout_days = {}  # {date_str: workout_data}

        # UI references
        self.calendar_frame = None
        self.month_label = None
        self.day_buttons = {}
        self.tooltip = None
        self.exercise_selector = None
        self.stats_labels = {}
        self.lifetime_stats_frame = None
        self.sidebar_content = None

        # Clear parent frame
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Build dashboard with grid layout
        self._setup_grid()
        self._build_dashboard()

        # Load data
        self.refresh()

    def _setup_grid(self):
        """Setup grid layout for the dashboard"""
        # Configure parent grid - 2 rows, 2 columns
        # Row 0: Header (fixed height)
        # Row 1: Content (expandable)
        self.parent.grid_rowconfigure(0, weight=config.DASHBOARD_HEADER_WEIGHT)
        self.parent.grid_rowconfigure(1, weight=config.DASHBOARD_CONTENT_WEIGHT)

        # Column 0: Main content (expandable)
        # Column 1: Sidebar (fixed width)
        self.parent.grid_columnconfigure(0, weight=config.DASHBOARD_MAIN_WEIGHT)
        self.parent.grid_columnconfigure(1, weight=config.DASHBOARD_SIDEBAR_WEIGHT,
                                         minsize=config.DASHBOARD_SIDEBAR_WIDTH)

    def _build_dashboard(self):
        """Build the dashboard UI"""
        self._build_header()
        self._build_main_content()
        self._build_sidebar()

    def _build_header(self):
        """Build header row spanning full width"""
        header_frame = ctk.CTkFrame(
            self.parent,
            fg_color=config.COLOR_FRAME_HEADER,
            height=config.DASHBOARD_HEADER_HEIGHT
        )
        header_frame.grid(
            row=0, column=0, columnspan=2,
            sticky="nsew",
            padx=config.OUTER_PADDING_X,
            pady=(config.OUTER_PADDING_Y, 0)
        )
        header_frame.grid_propagate(False)
        
        icon_dir = config.ICON_DIRECTORY

        # Welcome message
        user_name = self.user_config.get('profile', 'name', 'User')
        ctk.CTkLabel(
            header_frame,
            text=f"Welcome back, {user_name}!",
            font=ctk.CTkFont(size=config.FONT_SIZE_TITLE, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_HEADER
        ).pack(side="left", padx=20, pady=20)

        # Settings button
        if self.on_settings_click:
            self.settings_button = StyledButton(
                header_frame,
                round=True,
                size=40,
                image_path=f"{icon_dir}/settings/normal.png",
                hover_image_path=f"{icon_dir}/settings/hover.png",
                fg_color="transparent",
                hover_color=config.COLOR_SYSTEM_BORDER_HOVER,
                border_width=config.BORDER_WIDTH_THICK,
                border_color=config.COLOR_SYSTEM_BORDER,
                hover_border_color=config.COLOR_SYSTEM_BORDER_HOVER,
                command=self._on_settings_click,
            )
            self.settings_button.pack(side="right", padx=20, pady=20)

    def _build_main_content(self):
        """Build main content area with calendar (scrollable)"""
        # Create outer frame for the main content area
        main_outer = ctk.CTkFrame(
            self.parent,
            fg_color=config.COLOR_STAT_CARD_BG,
            corner_radius=config.CORNER_RADIUS_LARGE
        )
        main_outer.grid(
            row=1, column=0,
            sticky="nsew",
            padx=config.OUTER_PADDING_X,
            pady=config.OUTER_PADDING_Y
        )

        # Content frame
        main_frame = ctk.CTkFrame(
            main_outer,
            fg_color="transparent"
        )
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Calendar section
        self._build_calendar(main_frame)

        # Stats cards row
        self._build_stat_cards(main_frame)

    def _build_calendar(self, parent):
        """Build the workout calendar"""
        calendar_container = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        calendar_container.pack(fill="x", padx=20, pady=20)

        # Calendar header with navigation
        header = ctk.CTkFrame(calendar_container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))

        # Previous month button
        StyledButton(
            header,
            round=False,
            size=config.IMAGE_BUTTON_SIZE,
            image_path=f"{self.icon_dir}/previous/normal.png",
            hover_image_path=f"{self.icon_dir}/previous/hover.png",
            width=config.CALENDAR_NAV_BUTTON_SIZE,
            height=config.CALENDAR_NAV_BUTTON_SIZE,
            fg_color=config.COLOR_ACCENT,
            hover_color=config.COLOR_ACCENT_HOVER,
            command=self._prev_month
        ).pack(side="left")

        # Month/Year label
        self.month_label = ctk.CTkLabel(
            header,
            text="",
            font=ctk.CTkFont(size=config.FONT_SIZE_XL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_HEADER
        )
        self.month_label.pack(side="left", expand=True)

        # Next month button
        StyledButton(
            header,
            size=config.IMAGE_BUTTON_SIZE,
            image_path=f"{self.icon_dir}/next/normal.png",
            hover_image_path=f"{self.icon_dir}/next/hover.png",
            width=config.CALENDAR_NAV_BUTTON_SIZE,
            height=config.CALENDAR_NAV_BUTTON_SIZE,
            fg_color=config.COLOR_ACCENT,
            hover_color=config.COLOR_ACCENT_HOVER,
            command=self._next_month
        ).pack(side="right")

        # Calendar grid frame (single grid for headers + day cells)
        self.calendar_frame = ctk.CTkFrame(calendar_container, fg_color="transparent")
        self.calendar_frame.pack(fill="x")

        # Configure 7 equal columns
        for col in range(7):
            self.calendar_frame.grid_columnconfigure(col, weight=1, uniform="cal")

        # Day labels (Mon, Tue, etc.) in row 0
        for col, day_name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            ctk.CTkLabel(
                self.calendar_frame,
                text=day_name,
                font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
                text_color=config.COLOR_TEXT_POP
            ).grid(row=0, column=col, pady=(0, 5), sticky="ew")

        # Initial calendar render
        self._render_calendar()

    def _render_calendar(self):
        """Render the calendar for current month"""
        # Clear existing day cells (keep header row 0)
        for widget in self.calendar_frame.grid_slaves():
            if int(widget.grid_info()['row']) > 0:
                widget.destroy()
        self.day_buttons.clear()

        # Update month label
        month_name = calendar.month_name[self.current_month]
        self.month_label.configure(text=f"{month_name} {self.current_year}")

        # Get calendar data
        cal = calendar.Calendar(firstweekday=0)  # Monday first
        month_days = cal.monthdayscalendar(self.current_year, self.current_month)

        today = date.today()

        for week_idx, week in enumerate(month_days):
            for col, day in enumerate(week):
                if day == 0:
                    # Empty cell
                    ctk.CTkLabel(
                        self.calendar_frame,
                        text="",
                        height=config.CALENDAR_CELL_SIZE
                    ).grid(row=week_idx + 1, column=col, pady=2, sticky="ew")
                else:
                    current_date = date(self.current_year, self.current_month, day)
                    date_str = current_date.strftime("%Y-%m-%d")

                    # Determine styling
                    is_today = current_date == today
                    has_workout = (
                        date_str in self.workout_days
                        and sum(self.workout_days[date_str].get('reps_by_exercise', {}).values()) > 0
                    )

                    if has_workout:
                        bg_color = config.COLOR_CALENDAR_WORKOUT
                        text_color = config.COLOR_BACKGROUND
                    elif is_today:
                        bg_color = config.COLOR_STAT_CARD_BG2
                        text_color = config.COLOR_DROPDOWN_LABEL
                    else:
                        bg_color = "transparent"
                        text_color = config.COLOR_ACCENT

                    # Create day button
                    btn = ctk.CTkButton(
                        self.calendar_frame,
                        text=str(day),
                        width=config.CALENDAR_CELL_SIZE,
                        height=config.CALENDAR_CELL_SIZE,
                        fg_color=bg_color,
                        hover_color=config.COLOR_CALENDAR_HOVER,
                        text_color=text_color,
                        font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
                        corner_radius=config.CORNER_RADIUS_SMALL,
                        command=lambda d=date_str: self._on_day_click(d)
                    )
                    btn.grid(row=week_idx + 1, column=col, pady=2, padx=1)

                    # Add hover tooltip for workout days
                    if has_workout:
                        btn.bind("<Enter>", lambda e, d=date_str: self._show_tooltip(e, d))
                        btn.bind("<Leave>", self._hide_tooltip)

                    self.day_buttons[date_str] = btn

    def _show_tooltip(self, event, date_str):
        """Show tooltip with workout stats"""
        if date_str not in self.workout_days:
            return

        workout = self.workout_days[date_str]

        # Create tooltip
        self.tooltip = ctk.CTkToplevel(self.parent)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_attributes("-topmost", True)

        # Position near cursor
        x = event.widget.winfo_rootx() + 40
        y = event.widget.winfo_rooty() - 10
        self.tooltip.wm_geometry(f"+{x}+{y}")

        # Tooltip frame
        frame = ctk.CTkFrame(
            self.tooltip,
            fg_color=config.COLOR_DROPDOWN_LABEL,
            corner_radius=8,
            border_width=1,
            border_color=config.COLOR_HIGHLIGHT
        )
        frame.pack(padx=2, pady=2)

        # Format workout info
        reps_by_exercise = workout.get('reps_by_exercise', {})
        duration_secs = workout.get('duration_seconds', 0)

        # Format duration human-readably
        if duration_secs >= 60:
            duration_text = f"{duration_secs // 60} min"
        else:
            duration_text = f"{duration_secs} sec"

        # Per-exercise rep counts
        for ex_name, rep_count in reps_by_exercise.items():
            ctk.CTkLabel(
                frame,
                text=f"{ex_name}: {rep_count}",
                font=ctk.CTkFont(size=config.FONT_SIZE_TINY, weight=config.FONT_WEIGHT_BOLD),
                text_color=config.COLOR_BACKGROUND
            ).pack(anchor="w", padx=10, pady=(8, 2))

        ctk.CTkLabel(
            frame,
            text=f"Duration: {duration_text}",
            font=ctk.CTkFont(size=config.FONT_SIZE_TINY),
            text_color=config.COLOR_BACKGROUND
        ).pack(anchor="w", padx=10, pady=(2, 8))

    def _hide_tooltip(self, event=None):
        """Hide the tooltip"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def _on_day_click(self, date_str):
        """Handle day click - could show details or history"""
        if date_str in self.workout_days:
            print(f"Clicked workout day: {date_str}")
            # Could open a detail view here

    def _prev_month(self):
        """Go to previous month"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self._load_workout_days()
        self._render_calendar()

    def _next_month(self):
        """Go to next month"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self._load_workout_days()
        self._render_calendar()

    def _build_stat_cards(self, parent):
        """Build the row of stat cards"""
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Configure grid for even distribution
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1)

        # Get stats
        stats = self.db.get_total_stats()
        streak_data = self.db.get_streak_data()

        # Total Workouts
        self._create_stat_card(
            cards_frame, 0,
            "Total Workouts",
            str(stats.get('total_sessions', 0)),
            "sessions"
        )

        # Current Streak
        self._create_stat_card(
            cards_frame, 1,
            "Current Streak",
            str(streak_data.get('current_streak', 0)),
            "days"
        )

        # Total Reps
        total_reps = sum(stats.get('reps_by_exercise', {}).values())
        self._create_stat_card(
            cards_frame, 2,
            "Total Reps",
            str(total_reps),
            "reps"
        )

        # Best Streak
        self._create_stat_card(
            cards_frame, 3,
            "Best Streak",
            str(streak_data.get('longest_streak', 0)),
            "days"
        )

    def _create_stat_card(self, parent, column, title, value, unit):
        """Create a stat card"""
        card = ctk.CTkFrame(
            parent,
            fg_color=config.COLOR_STAT_CARD_BG2,
            corner_radius=config.CORNER_RADIUS,
            height=config.STAT_CARD_HEIGHT
        )
        card.grid(row=0, column=column, sticky="nsew", padx=5, pady=5)
        card.grid_propagate(False)

        # Value
        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=ctk.CTkFont(size=config.FONT_SIZE_XL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_DROPDOWN_LABEL
        )
        value_label.pack(pady=(20, 0))

        # Unit
        ctk.CTkLabel(
            card,
            text=unit,
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_DROPDOWN_LABEL
        ).pack()

        # Title
        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDLARGE, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_DROPDOWN_LABEL
        ).pack(pady=(5, 15))

        # Store reference for updates
        self.stats_labels[title] = value_label

    def _build_sidebar(self):
        """Build the right sidebar with start controls and lifetime stats (scrollable)"""
        # Outer frame for sidebar
        sidebar_outer = ctk.CTkFrame(
            self.parent,
            fg_color=config.COLOR_STAT_CARD_BG,
            corner_radius=config.CORNER_RADIUS_LARGE,
            border_width=2,
            border_color=config.COLOR_SEPARATOR,
            width=config.DASHBOARD_SIDEBAR_WIDTH
        )
        sidebar_outer.grid(
            row=1, column=1,
            sticky="nsew",
            padx=(0, config.OUTER_PADDING_X),
            pady=config.OUTER_PADDING_Y
        )
        sidebar_outer.grid_propagate(False)

        # Content frame
        self.sidebar_content = ctk.CTkFrame(
            sidebar_outer,
            fg_color="transparent"
        )
        self.sidebar_content.pack(fill="both", expand=True, padx=5, pady=5)

        # Start Workout Section
        self._build_start_section(self.sidebar_content)

        # Separator
        ctk.CTkFrame(self.sidebar_content, height=2, fg_color=config.COLOR_SEPARATOR).pack(
            fill="x", padx=20, pady=20
        )

        # Lifetime Stats Section
        self._build_lifetime_stats(self.sidebar_content)
        
    def _on_exercise_changed(self, exercise_name: str):
        """Handle exercise change from selector"""
        print(f"Selected: {exercise_name}")

    def _build_start_section(self, parent):
        """Build the start workout section"""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=20, pady=(20, 0))

        # Section title
        ctk.CTkLabel(
            section,
            text="START WORKOUT",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP
        ).pack(pady=(0, 15))

        # Exercise selector - read saved preference from user config
        backend_to_display = {"squat": "Squats", "pushup": "Push-ups", "curl": "Curls"}
        saved_exercise = self.user_config.get('workout', 'default_exercise', 'squat')
        initial = backend_to_display.get(saved_exercise, config.DEFAULT_EXERCISE)

        self.exercise_selector = ExerciseSelector(
            section,
            initial_exercise=initial,
            on_change_callback=self._on_exercise_changed  # optional but recommended
        )

        self.exercise_selector.pack(pady=(0, 20))


        # Start button
        start_btn = StyledButton(
            section,
            round=True,
            size=config.IMAGE_BUTTON_SIZE,
            image_path=f"{self.icon_dir}/start/normal.png",
            hover_image_path=f"{self.icon_dir}/start/hover.png",
            fg_color="transparent",
            hover_color=config.COLOR_SUCCESS_HOVER,
            border_width=config.BORDER_WIDTH_THICK,
            border_color=config.COLOR_SUCCESS_DARK,
            hover_border_color=config.COLOR_SUCCESS,
            command=self._on_start_click
        )
        start_btn.pack()

    def _build_lifetime_stats(self, parent):
        """Build the lifetime stats section"""
        # Destroy old section if rebuilding
        if self.lifetime_stats_frame is not None:
            self.lifetime_stats_frame.destroy()

        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.pack(fill="x", padx=20, pady=0)
        self.lifetime_stats_frame = section

        # Section title
        ctk.CTkLabel(
            section,
            text="LIFETIME STATS",
            font=ctk.CTkFont(size=config.FONT_SIZE_MEDIUM, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_TEXT_POP
        ).pack(pady=(0, 15))

        # Get stats
        stats = self.db.get_total_stats()

        # Total time
        total_seconds = stats.get('total_time_seconds', 0)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        if hours > 0:
            time_text = f"{hours}h {minutes}m"
        elif minutes > 0:
            time_text = f"{minutes}m {secs}s"
        else:
            time_text = f"{secs}s"

        self._create_stat_row(section, "Total Time:", time_text)
        self._create_stat_row(section, "Sessions:", str(stats.get('total_sessions', 0)))

        # Separator
        ctk.CTkFrame(section, height=1, fg_color=config.COLOR_SEPARATOR).pack(
            fill="x", pady=10
        )

        # Exercise breakdown
        ctk.CTkLabel(
            section,
            text="REPS BY EXERCISE",
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT
        ).pack(anchor="w", pady=(5, 10))

        for exercise_name, rep_count in stats.get('reps_by_exercise', {}).items():
            display_name = exercise_name.replace('_', ' ').title() + ":"
            self._create_stat_row(section, display_name, str(rep_count))

        # Separator
        ctk.CTkFrame(section, height=1, fg_color=config.COLOR_SEPARATOR).pack(
            fill="x", pady=10
        )

        # Form quality
        total_reps = stats.get('total_all_reps', 0)
        excellent = stats.get('total_excellent_reps', 0)
        good = stats.get('total_good_reps', 0)
        poor = stats.get('total_poor_reps', 0)

        ctk.CTkLabel(
            section,
            text="FORM QUALITY",
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=config.COLOR_ACCENT
        ).pack(anchor="w", pady=(5, 10))

        self._create_stat_row(section, "Excellent:", str(excellent), config.COLOR_SUCCESS)
        self._create_stat_row(section, "Good:", str(good), config.COLOR_WARNING)
        self._create_stat_row(section, "Poor:", str(poor), config.COLOR_ERROR)

    def _create_stat_row(self, parent, label, value, value_color=None):
        """Create a label-value row"""
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=3)

        ctk.CTkLabel(
            row,
            text=label,
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL),
            text_color=config.COLOR_DROPDOWN_LABEL
        ).pack(side="left")

        ctk.CTkLabel(
            row,
            text=value,
            font=ctk.CTkFont(size=config.FONT_SIZE_SMALL, weight=config.FONT_WEIGHT_BOLD),
            text_color=value_color or config.COLOR_DROPDOWN_LABEL
        ).pack(side="right")

    def _on_start_click(self):
        """Handle start button click"""
        exercise = self.exercise_selector.get_exercise()
        if self.on_start_workout:
            self.on_start_workout(exercise)

    def _on_settings_click(self):
        """Handle settings button click"""
        if self.on_settings_click:
            self.on_settings_click()

    def _load_workout_days(self):
        """Load workout data for the current month"""
        self.workout_days.clear()

        # Calculate date range for current month
        first_day = date(self.current_year, self.current_month, 1)
        if self.current_month == 12:
            last_day = date(self.current_year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(self.current_year, self.current_month + 1, 1) - timedelta(days=1)

        # Get sessions for this month
        try:
            sessions = self.db.get_recent_sessions(limit=100)

            for session in sessions:
                if not session.get('start_time'):
                    continue

                # Parse date
                try:
                    start_time = datetime.fromisoformat(str(session['start_time']))
                    session_date = start_time.date()
                except (ValueError, TypeError):
                    continue

                # Check if in current month
                if first_day <= session_date <= last_day:
                    date_str = session_date.strftime("%Y-%m-%d")

                    # Get session summary
                    summary = self.db.get_session_summary(session['session_id'])

                    if date_str not in self.workout_days:
                        self.workout_days[date_str] = {
                            'reps_by_exercise': {},
                            'duration_seconds': 0,
                            'session_count': 0
                        }

                    # Aggregate data for this day
                    day_data = self.workout_days[date_str]
                    day_data['session_count'] += 1

                    # Duration (track in seconds for accuracy with short sessions)
                    duration = session.get('total_duration_seconds', 0) or 0
                    day_data['duration_seconds'] += duration

                    # Per-exercise rep counts from summary
                    if summary:
                        for ex_set in summary.get('exercise_sets', []):
                            ex_name = ex_set.get('exercise_name', '').replace('_', ' ').title()
                            reps = ex_set.get('total_reps', 0)
                            if ex_name and reps > 0:
                                day_data['reps_by_exercise'][ex_name] = (
                                    day_data['reps_by_exercise'].get(ex_name, 0) + reps
                                )

        except Exception as e:
            print(f"Error loading workout days: {e}")

    def refresh(self):
        """Refresh all dashboard data"""
        self._load_workout_days()
        self._render_calendar()

        # Update stat cards
        stats = self.db.get_total_stats()
        streak_data = self.db.get_streak_data()

        if "Total Workouts" in self.stats_labels:
            self.stats_labels["Total Workouts"].configure(
                text=str(stats.get('total_sessions', 0))
            )
        if "Current Streak" in self.stats_labels:
            self.stats_labels["Current Streak"].configure(
                text=str(streak_data.get('current_streak', 0))
            )
        if "Total Reps" in self.stats_labels:
            total_reps = sum(stats.get('reps_by_exercise', {}).values())
            self.stats_labels["Total Reps"].configure(text=str(total_reps))
        if "Best Streak" in self.stats_labels:
            self.stats_labels["Best Streak"].configure(
                text=str(streak_data.get('longest_streak', 0))
            )

        # Rebuild lifetime stats sidebar (dynamic content like exercise list)
        if self.sidebar_content:
            self._build_lifetime_stats(self.sidebar_content)

    def get_selected_exercise(self) -> str:
        """Get the currently selected exercise"""
        return self.exercise_selector.get_exercise() if self.exercise_selector else config.DEFAULT_EXERCISE

if __name__ == "__main__":
    print("Testing Dashboard...")
    print("Dashboard class created (requires GUI context to fully test)")
