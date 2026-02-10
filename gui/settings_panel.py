"""
Settings panel for user preferences and configuration
Uses grid layout for consistent label/input alignment
"""
import customtkinter as ctk
from config.user_config import UserConfig
from config.app_constants import *
from tkinter import filedialog, messagebox
from gui.config.constants import *

# Use shared grid layout constants from gui.config.constants
LABEL_WIDTH = GRID_LABEL_WIDTH
INPUT_WIDTH = GRID_INPUT_WIDTH
ROW_PADY = GRID_ROW_PADY
COL_PADX = GRID_COL_PADX


class SettingsPanel:
    """Comprehensive settings interface"""

    def __init__(self, parent_frame, user_config: UserConfig, on_save_callback=None):
        """
        Initialize settings panel

        Args:
            parent_frame: Parent CTk frame
            user_config: UserConfig instance
            on_save_callback: Optional callback when settings are saved
        """
        self.parent = parent_frame
        self.user_config = user_config
        self.on_save = on_save_callback

        # Track current row for each tab's grid
        self._tab_rows = {}

        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Build settings
        self._build_settings()

    def _build_settings(self):
        """Build settings interface using grid layout"""
        # Configure parent grid
        self.parent.grid_rowconfigure(1, weight=1)  # Tabview expands
        self.parent.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(
            header_frame,
            text="Settings",
            font=ctk.CTkFont(size=FONT_SIZE_TITLE, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_TEXT_HEADER,
        ).grid(row=0, column=0, sticky="w", padx=10)

        # Tabview for different setting categories
        self.tabview = ctk.CTkTabview(
            self.parent,
            fg_color=COLOR_STAT_CARD_BG,
            text_color=COLOR_BACKGROUND,
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_selected_hover_color=COLOR_TEXT_POP,
            segmented_button_unselected_color=COLOR_TEXT_POP2,
            segmented_button_unselected_hover_color=COLOR_TEXT_POP,
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 0))
        self.tabview._segmented_button.configure(
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight=FONT_WEIGHT_BOLD),
        )
        
        # Create tabs
        self.tabview.add("Profile")
        self.tabview.add("System")
        self.tabview.add("Display")
        self.tabview.add("Workout")
        #self.tabview.add("Thresholds")
        #self.tabview.add("Calibration")
        # self.tabview.add("Advanced")

        # Build each tab
        self._build_profile_tab()
        self._build_system_tab()
        self._build_display_tab()
        self._build_workout_tab()
        #self._build_thresholds_tab()
        #self._build_calibration_tab()
        # self._build_advanced_tab()

        # --- Bottom save buttons ---
        button_bar = ctk.CTkFrame(self.parent, fg_color="transparent")
        button_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(5, 15))
        button_bar.grid_columnconfigure(0, weight=1)

        # Status label (shows confirmations, centered)
        self._save_status_label = ctk.CTkLabel(
            button_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLOR_SUCCESS
        )
        self._save_status_label.grid(row=0, column=0, pady=(0, 5))

        # Button container
        btn_container = ctk.CTkFrame(button_bar, fg_color="transparent")
        btn_container.grid(row=1, column=0)

        ctk.CTkButton(
            btn_container,
            text="Save for Session",
            command=self._save_session,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_TEXT_POP2,
            text_color=COLOR_BACKGROUND,
            font= (BUTTON_FONT,FONT_SIZE_MEDIUM, FONT_WEIGHT_BOLD),
            corner_radius= 8,
            height= 40
        ).grid(row=0, column=0, padx=8)

        ctk.CTkButton(
            btn_container,
            text="Make Default",
            command=self._save_default,
            fg_color=COLOR_TEXT_POP,
            hover_color=COLOR_TEXT_POP2,
            text_color=COLOR_BACKGROUND,
            font= (BUTTON_FONT, FONT_SIZE_MEDIUM, FONT_WEIGHT_BOLD),
            corner_radius= 8,
            height= 40
        ).grid(row=0, column=1, padx=8)
    
    def _init_tab_grid(self, tab):
        """Initialize grid layout for a tab and return current row"""
        tab_name = str(tab)
        if tab_name not in self._tab_rows:
            self._tab_rows[tab_name] = 0
            # Configure column weights for consistent layout
            tab.grid_columnconfigure(0, weight=0, minsize=LABEL_WIDTH)
            tab.grid_columnconfigure(1, weight=1)
        return self._tab_rows[tab_name]

    def _next_row(self, tab):
        """Get next row number for a tab"""
        tab_name = str(tab)
        self._tab_rows[tab_name] = self._tab_rows.get(tab_name, 0) + 1
        return self._tab_rows[tab_name] - 1

    def _build_profile_tab(self):
        """Build profile settings tab"""
        tab = self.tabview.tab("Profile")
        self._init_tab_grid(tab)

        # Name
        self._create_text_setting(
            tab,
            "Name:",
            'profile',
            'name',
            placeholder="What do you like to be called?"
        )

        # Height
        # self._create_number_setting(
        #     tab,
        #     "Height (cm):",
        #     'profile',
        #     'height_cm',
        #     placeholder="177.16"
        # )

    def _build_system_tab(self):
        """Build system settings tab"""
        tab = self.tabview.tab("System")
        self._init_tab_grid(tab)

        # --- Camera Selection Row ---
        row = self._next_row(tab)

        ctk.CTkLabel(
            tab,
            text="Camera:",
            text_color=COLOR_DROPDOWN_LABEL,
            font=ctk.CTkFont(size=FONT_SIZE_MEDIUM, weight=FONT_WEIGHT_BOLD),
            width=LABEL_WIDTH,
            anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=COL_PADX, pady=ROW_PADY)

        # Camera controls container (dropdown + scan button + checkmark)
        camera_controls = ctk.CTkFrame(tab, fg_color="transparent")
        camera_controls.grid(row=row, column=1, sticky="w", padx=COL_PADX, pady=ROW_PADY)

        # Camera dropdown - load cached scan results if available
        current_index = self.user_config.get('system', 'camera_index', 0)
        cached_cameras = self.user_config.get('system', 'cached_cameras', None)

        if cached_cameras and len(cached_cameras) > 0:
            self._camera_options = []
            self._camera_values = []
            selected_display = None
            for cam in cached_cameras:
                display = f"{cam['name']}  ({cam['width']}x{cam['height']})"
                self._camera_options.append(display)
                self._camera_values.append(cam['index'])
                if cam['index'] == current_index:
                    selected_display = display
            initial_value = selected_display or self._camera_options[0]
        else:
            self._camera_options = [f"Camera {current_index}"]
            self._camera_values = [current_index]
            initial_value = self._camera_options[0]

        self._camera_var = ctk.StringVar(value=initial_value)

        self._camera_dropdown = ctk.CTkOptionMenu(
            camera_controls,
            values=self._camera_options,
            variable=self._camera_var,
            command=self._on_camera_selected,
            width=INPUT_WIDTH,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight=FONT_WEIGHT_BOLD),
            dropdown_font=ctk.CTkFont(size=FONT_SIZE_TINY, weight=FONT_WEIGHT_BOLD),
            corner_radius=CORNER_RADIUS_SMALL,
            fg_color=COLOR_DROPDOWN_LABEL,       # main button background
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_STAT_CARD_BG2,
            text_color=COLOR_BACKGROUND,         # main button text
            dropdown_hover_color=COLOR_ACCENT,
            dropdown_text_color=COLOR_BACKGROUND # text color in dropdown items
)
        self._camera_dropdown.grid(row=0, column=0, padx=(0, 5))

        # Scan button next to dropdown
        self._scan_btn = ctk.CTkButton(
            camera_controls,
            text="Scan",
            command=self._scan_for_cameras,
            height=30,
            width=40,
            font= (BUTTON_FONT, FONT_SIZE_SMALL, FONT_WEIGHT_BOLD),
            corner_radius= 8,
            fg_color=COLOR_ACCENT,
            text_color=COLOR_BACKGROUND,
            hover_color=COLOR_TEXT_POP2,
        )
        self._scan_btn.grid(row=0, column=1, padx=(0, 3))

        # Checkmark label (hidden by default, shown after scan completes)
        self._scan_check_label = ctk.CTkLabel(
            camera_controls,
            text="",
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_SUCCESS,
            width=30
        )
        self._scan_check_label.grid(row=0, column=2)

        # --- Video Resolution ---
        self._create_number_setting(
            tab,
            "Video Width:",
            'system',
            'video_width',
            placeholder=FRAME_WIDTH
        )

        self._create_number_setting(
            tab,
            "Video Height:",
            'system',
            'video_height',
            placeholder=FRAME_HEIGHT
        )

        # Model complexity
        self._create_option_setting(
            tab,
            "Model Complexity:",
            'system',
            'model_complexity',
            ["0 (Lite)", "1 (Full)", "2 (Heavy)"],
            values=[0, 1, 2]
        )

    def _scan_for_cameras(self):
        """Scan for all available cameras and populate the dropdown"""
        import threading

        # Disable scan button and show scanning state
        self._scan_btn.configure(text="Scanning...", state="disabled")
        self._scan_check_label.configure(text="")

        def do_scan():
            """Background thread to scan cameras without freezing UI"""
            # Get device names from OS
            from gui.controllers.workout_controller import WorkoutController
            device_names = WorkoutController._get_camera_device_names()

            # OpenCV scan for actual availability
            import cv2
            import time
            found_cameras = []
            for i in range(5):
                cap = None
                try:
                    cap = cv2.VideoCapture(i)
                    if cap.isOpened():
                        # Give camera time to initialize
                        # Continuity Camera (iPhone) needs longer delay
                        time.sleep(1.0)
                        ret, frame = cap.read()
                        if ret:
                            h, w = frame.shape[:2]
                            name = device_names[i] if i < len(device_names) else f"Camera {i}"
                            found_cameras.append({
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

            # Schedule UI update on main thread
            self.parent.after(0, lambda: self._on_scan_complete(found_cameras))

        # Run scan in background thread
        thread = threading.Thread(target=do_scan, daemon=True)
        thread.start()

    def _on_scan_complete(self, found_cameras):
        """Handle scan completion on main thread"""
        # Re-enable scan button
        self._scan_btn.configure(text="Scan", state="normal")

        # Persist scan results to disk so dropdown is populated on next launch
        if found_cameras:
            self.user_config.set('system', 'cached_cameras', found_cameras, save=True)

        if not found_cameras:
            self._camera_options = ["No cameras found"]
            self._camera_values = []
            self._camera_var.set("No cameras found")
            self._camera_dropdown.configure(values=self._camera_options)
            self._scan_check_label.configure(text="")
            return

        # Build dropdown options with device names and resolution
        current_index = self.user_config.get('system', 'camera_index', 0)
        self._camera_options = []
        self._camera_values = []
        selected_display = None

        for cam in found_cameras:
            display = f"{cam['name']}  ({cam['width']}x{cam['height']})"
            self._camera_options.append(display)
            self._camera_values.append(cam['index'])
            if cam['index'] == current_index:
                selected_display = display

        # Update dropdown
        self._camera_dropdown.configure(values=self._camera_options)

        # Set current selection
        if selected_display:
            self._camera_var.set(selected_display)
        else:
            self._camera_var.set(self._camera_options[0])

        # Flash the dropdown green and show checkmark to signal scan complete
        self._scan_check_label.configure(text="Done")
        original_fg = self._camera_dropdown.cget("fg_color")
        self._camera_dropdown.configure(fg_color=COLOR_SUCCESS)
        self._camera_dropdown.after(
            800,
            lambda: self._camera_dropdown.configure(fg_color=original_fg)
        )
        # Fade out checkmark after a couple seconds
        self._scan_check_label.after(
            2500,
            lambda: self._scan_check_label.configure(text="")
        )

    def _on_camera_selected(self, choice):
        """Handle camera selection from dropdown (in-memory only until user saves)"""
        if choice in self._camera_options:
            idx = self._camera_options.index(choice)
            if idx < len(self._camera_values):
                camera_index = self._camera_values[idx]
                self.user_config.set('system', 'camera_index', camera_index, save=False)
    
    def _build_display_tab(self):
        """Build display settings tab"""
        tab = self.tabview.tab("Display")
        self._init_tab_grid(tab)

        # Mirror camera
        self._create_checkbox_setting(
            tab,
            "Mirror Camera (flip horizontally)",
            'display',
            'mirror_video'
        )

        # Show skeleton
        self._create_checkbox_setting(
            tab,
            "Show Skeleton Overlay",
            'display',
            'show_skeleton'
        )

        # Show angle
        self._create_checkbox_setting(
            tab,
            "Show Angle Values",
            'display',
            'show_angle_overlay'
        )

        # Show rep counter
        self._create_checkbox_setting(
            tab,
            "Show Rep Counter",
            'display',
            'show_rep_counter'
        )

        # Show form feedback
        self._create_checkbox_setting(
            tab,
            "Show Form Feedback",
            'display',
            'show_form_feedback'
        )
    
    def _build_workout_tab(self):
        """Build workout settings tab"""
        tab = self.tabview.tab("Workout")
        self._init_tab_grid(tab)

        # Default exercise
        self._create_option_setting(
            tab,
            "Default Exercise:",
            'workout',
            'default_exercise',
            ["Squats", "Push-ups", "Bicep Curls"],
            values=["squat", "pushup", "curl"]
        )


    def _reset_calibrations(self):
        """Reset all calibrations to defaults"""
        from tkinter import messagebox
        
        result = messagebox.askyesno(
            "Reset Calibrations",
            "Are you sure you want to reset all calibrations to default values?\n\n"
            "This will remove your personalized thresholds."
        )
        
        if result:
            # Reset each exercise to defaults
            self.user_config.set_threshold('squat', {
                'standing': 160,
                'squatting': 100,
                'excellent': 90,
                'good': 100,
                'cooldown_frames': 15,
                'calibrated': False,
                'calibration_date': None
            }, mark_calibrated=False)
            
            self.user_config.set_threshold('pushup', {
                'up': 160,
                'down': 100,
                'excellent': 90,
                'good': 110,
                'cooldown_frames': 12,
                'calibrated': False,
                'calibration_date': None
            }, mark_calibrated=False)
            
            self.user_config.set_threshold('curl', {
                'down': 160,
                'curled': 60,
                'excellent': 50,
                'good': 70,
                'cooldown_frames': 10,
                'calibrated': False,
                'calibration_date': None
            }, mark_calibrated=False)
            
            messagebox.showinfo(
                "Reset Complete",
                "All calibrations have been reset to default values."
            )
            
            # Rebuild the tab to show updated status
            self._build_calibration_tab()    
        
    
    # def _build_advanced_tab(self):
    #     """Build advanced settings tab"""
    #     tab = self.tabview.tab("Advanced")
    #     self._init_tab_grid(tab)

    #     # --- Backup & Restore Section ---
    #     row = self._next_row(tab)

    #     # Section header spanning both columns
    #     # ctk.CTkLabel(
    #     #     tab,
    #     #     text="Backup & Restore",
    #     #     font=ctk.CTkFont(size=16, weight="bold"),
    #     #     anchor="w"
    #     # ).grid(row=row, column=0, columnspan=2, sticky="w", padx=COL_PADX, pady=(ROW_PADY, 5))

    #     # # Export button
    #     # row = self._next_row(tab)
    #     # ctk.CTkButton(
    #     #     tab,
    #     #     text="Export Settings",
    #     #     command=self._export_settings,
    #     #     width=INPUT_WIDTH
    #     # ).grid(row=row, column=0, columnspan=2, sticky="w", padx=COL_PADX, pady=5)

    #     # # Import button
    #     # row = self._next_row(tab)
    #     # ctk.CTkButton(
    #     #     tab,
    #     #     text="Import Settings",
    #     #     command=self._import_settings,
    #     #     width=INPUT_WIDTH
    #     # ).grid(row=row, column=0, columnspan=2, sticky="w", padx=COL_PADX, pady=5)

    #     # --- Reset Settings Section ---
    #     row = self._next_row(tab)
    #     ctk.CTkLabel(
    #         tab,
    #         text="Reset Settings",
    #         font=ctk.CTkFont(size=16, weight="bold"),
    #         anchor="w"
    #     ).grid(row=row, column=0, columnspan=2, sticky="w", padx=COL_PADX, pady=(20, 5))

    #     row = self._next_row(tab)
    #     ctk.CTkButton(
    #         tab,
    #         text="Reset to Defaults",
    #         command=self._reset_to_defaults,
    #         fg_color="red",
    #         hover_color="darkred",
    #         width=INPUT_WIDTH
    #     ).grid(row=row, column=0, columnspan=2, sticky="w", padx=COL_PADX, pady=5)
    
    # ========== HELPER METHODS ==========

    def _create_text_setting(self, parent, label, category, key, placeholder="", color=COLOR_DROPDOWN_LABEL):
        """Create text input setting using grid layout"""
        row = self._next_row(parent)

        ctk.CTkLabel(
            parent,
            text=label,
            width=LABEL_WIDTH,
            font=ctk.CTkFont(size=FONT_SIZE_MEDIUM, weight=FONT_WEIGHT_BOLD),
            anchor="w",
            text_color= color
        ).grid(row=row, column=0, sticky="w", padx=COL_PADX, pady=ROW_PADY)

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            width=INPUT_WIDTH,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight=FONT_WEIGHT_BOLD)
        )

        entry.grid(row=row, column=1, sticky="w", padx=COL_PADX, pady=ROW_PADY)

        # Load current value
        current = self.user_config.get(category, key, "")
        if current:
            entry.insert(0, str(current))

        # Store reference for saving
        if not hasattr(self, '_settings_widgets'):
            self._settings_widgets = []
        self._settings_widgets.append((category, key, entry, 'text'))

    def _create_number_setting(self, parent, label, category, key, placeholder="", color=COLOR_DROPDOWN_LABEL):
        """Create number input setting using grid layout"""
        row = self._next_row(parent)

        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=FONT_SIZE_MEDIUM, weight=FONT_WEIGHT_BOLD),
            width=LABEL_WIDTH,
            text_color=color,
            anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=COL_PADX, pady=ROW_PADY)

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=str(placeholder),
            width=INPUT_WIDTH,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight=FONT_WEIGHT_BOLD)  # <-- ADD
        )

        entry.grid(row=row, column=1, sticky="w", padx=COL_PADX, pady=ROW_PADY)

        current = self.user_config.get(category, key)
        if current is not None:
            entry.insert(0, str(current))

        if not hasattr(self, '_settings_widgets'):
            self._settings_widgets = []
        self._settings_widgets.append((category, key, entry, 'number'))

    def _create_checkbox_setting(self, parent, label, category, key):
        """Create a styled checkbox setting using grid layout"""
        row = self._next_row(parent)

        # Track value
        var = ctk.BooleanVar(value=self.user_config.get(category, key, False))

        # Styled checkbox
        checkbox = ctk.CTkCheckBox(
            parent,
            text=label,
            variable=var,
            font=ctk.CTkFont(size=FONT_SIZE_MEDIUM, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_DROPDOWN_LABEL,    # Label color
            fg_color=COLOR_ACCENT,               # Background color when checked
            hover_color=COLOR_STAT_CARD_BG2,       # Hover background
        )
        checkbox.grid(row=row, column=0, columnspan=2, sticky="w", padx=COL_PADX, pady=ROW_PADY)

        # Store for saving
        if not hasattr(self, '_settings_widgets'):
            self._settings_widgets = []
        self._settings_widgets.append((category, key, var, 'bool'))

    def _create_option_setting(self, parent, label, category, key, options, values=None):
        """Create dropdown option setting using grid layout with styled CTkOptionMenu"""
        if values is None:
            values = [opt.lower() for opt in options]

        row = self._next_row(parent)

        # Label for the dropdown
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=FONT_SIZE_MEDIUM, weight=FONT_WEIGHT_BOLD),
            text_color=COLOR_DROPDOWN_LABEL,
            width=LABEL_WIDTH,
            anchor="w"
        ).grid(row=row, column=0, sticky="w", padx=COL_PADX, pady=ROW_PADY)

        # Determine current value
        current = self.user_config.get(category, key)
        display_value = options[0]
        if current in values:
            idx = values.index(current)
            display_value = options[idx]

        var = ctk.StringVar(value=display_value)

        # Styled dropdown
        dropdown = ctk.CTkOptionMenu(
            parent,
            values=options,
            variable=var,
            width=INPUT_WIDTH,
            font=ctk.CTkFont(size=FONT_SIZE_SMALL, weight=FONT_WEIGHT_BOLD),
            dropdown_font=ctk.CTkFont(size=FONT_SIZE_TINY, weight=FONT_WEIGHT_BOLD),
            corner_radius=CORNER_RADIUS_SMALL,
            fg_color=COLOR_DROPDOWN_LABEL,       # background of main button
            button_color=COLOR_ACCENT,
            button_hover_color=COLOR_STAT_CARD_BG2,
            text_color=COLOR_BACKGROUND,         # text color on main button
            dropdown_hover_color=COLOR_ACCENT,
            dropdown_text_color=COLOR_BACKGROUND # text color in dropdown items
        )
        dropdown.grid(row=row, column=1, sticky="w", padx=COL_PADX, pady=ROW_PADY)

        # Store for saving
        if not hasattr(self, '_settings_widgets'):
            self._settings_widgets = []
        self._settings_widgets.append((category, key, var, 'option', options, values))

    
    def _create_threshold_inputs(self, parent, exercise):
        """Create threshold input fields for exercise using grid layout"""
        thresholds = self.user_config.get_threshold(exercise)

        # Initialize grid for this parent if needed
        self._init_tab_grid(parent)

        for threshold_key in ['standing', 'squatting', 'excellent', 'good', 'cooldown_frames']:
            if threshold_key in thresholds:
                self._create_number_setting(
                    parent,
                    f"{threshold_key.replace('_', ' ').title()}:",
                    f'thresholds.{exercise}',
                    threshold_key,
                    placeholder=str(thresholds[threshold_key])
                )
    
    # ========== ACTIONS ==========

    def _apply_widget_values(self):
        """Read all widget values into user_config in-memory (no disk write)"""
        if not hasattr(self, '_settings_widgets'):
            return

        for item in self._settings_widgets:
            category, key, widget, widget_type = item[:4]

            if widget_type == 'text':
                value = widget.get()
                self.user_config.set(category, key, value, save=False)

            elif widget_type == 'number':
                try:
                    value = float(widget.get())
                    if value.is_integer():
                        value = int(value)
                    self.user_config.set(category, key, value, save=False)
                except ValueError:
                    pass

            elif widget_type == 'bool':
                value = widget.get()
                self.user_config.set(category, key, value, save=False)

            elif widget_type == 'option':
                options, values = item[4], item[5]
                display_value = widget.get()
                if display_value in options:
                    idx = options.index(display_value)
                    actual_value = values[idx]
                    self.user_config.set(category, key, actual_value, save=False)

    def _show_save_status(self, text, color=COLOR_SUCCESS):
        """Show a temporary status message above the save buttons"""
        self._save_status_label.configure(text=text, text_color=color)
        self._save_status_label.after(
            3000,
            lambda: self._save_status_label.configure(text="")
        )

    def _save_session(self):
        """Apply settings to current session only (lost on app restart)"""
        self._apply_widget_values()

        if self.on_save:
            self.on_save()

        self._show_save_status("Applied for this session")

    def _save_default(self):
        """Apply settings and write to disk (persists across restarts)"""
        self._apply_widget_values()

        # Write to disk
        self.user_config._save_config()

        if self.on_save:
            self.on_save()

        self._show_save_status("Saved as default")
    
    def _export_settings(self):
        """Export settings to file"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            self.user_config.export_config(filepath)
            messagebox.showinfo("Export Complete", f"Settings exported to:\n{filepath}")
    
    def _import_settings(self):
        """Import settings from file"""
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                self.user_config.import_config(filepath)
                messagebox.showinfo("Import Complete", "Settings imported successfully!")
                # Rebuild settings to show new values
                self._build_settings()
            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import settings:\n{str(e)}")
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        result = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?\nThis cannot be undone."
        )
        
        if result:
            self.user_config.reset_to_defaults()
            messagebox.showinfo("Reset Complete", "All settings have been reset to defaults.")
            self._build_settings()


if __name__ == "__main__":
    print("Testing SettingsPanel...")
    print("SettingsPanel class created (requires GUI context to fully test)")