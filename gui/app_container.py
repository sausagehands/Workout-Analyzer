"""
Main application container that manages navigation between Dashboard and Workout views
"""
import customtkinter as ctk
import tkinter as tk
from typing import Optional
from .dashboard import Dashboard
from .controllers.workout_controller import WorkoutController
from .panels.header_panel import HeaderPanel
from .panels.video_panel import VideoPanel
from .panels.controls_panel import ControlsPanel
from .panels.info_panel import InfoPanel
from .dialogs.history_dialog import HistoryDialog
from .dialogs.summary_dialog import SummaryDialog
from .dialogs.error_dialog import ErrorDialog
from .settings_panel import SettingsPanel
import gui.config.constants as config

# --------------------------
# Helper function for PyInstaller-safe close
# --------------------------
def set_close_handler(widget, handler):
    """
    Safely attach a WM_DELETE_WINDOW handler to the window containing this widget.
    Works for CTk() or CTkToplevel(), compatible with PyInstaller builds.
    """
    try:
        window = widget.winfo_toplevel()
        if window is not None:
            window.protocol("WM_DELETE_WINDOW", handler)
    except Exception as e:
        print(f"Failed to attach close handler: {e}")


class AppContainer:
    """
    Main application container that manages:
    - Dashboard view (default/home)
    - Workout view
    - Navigation between views
    """

    def __init__(self, engine, db, user_config):
        self.engine = engine
        self.db = db
        self.user_config = user_config

        # Create controller for workout logic
        self.controller = WorkoutController(engine, db, user_config)

        # Current view tracking
        self.current_view = None  # "dashboard" or "workout"

        # UI references
        self.window = None
        self.content_frame = None
        self.dashboard = None

        # Workout view references
        self.header_panel = None
        self.video_panel = None
        self.controls_panel = None
        self.info_panel = None

        # Initialize window
        self._init_window()

        # Start with dashboard
        self._show_dashboard()

    # --------------------------
    # Window init / cleanup
    # --------------------------
    def _init_window(self):
        """Initialize the main window"""
        self.window = ctk.CTk()
        self.window.title("AI Workout Form Analyzer")
        self.window.attributes("-fullscreen", True)
        self.window.resizable(True, True)
        self.window.configure(fg_color=config.COLOR_BACKGROUND)

        # PyInstaller-safe close handler
        set_close_handler(self.window, self._on_window_close)

        # Content frame fills entire window
        self.content_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True)

    def _on_window_close(self):
        """Handle window close"""
        print("\nClosing application...")
        self.cleanup()
        try:
            self.window.withdraw()
            self.window.quit()
        except (tk.TclError, AttributeError):
            pass

    def cleanup(self):
        """Cleanup resources"""
        self.controller.cleanup()

        if hasattr(self, 'video_panel') and self.video_panel:
            try:
                if self.window.winfo_exists():
                    self.video_panel.clear()
                    print("Video panel cleared")
            except (tk.TclError, RuntimeError, AttributeError):
                pass

        print("GUI cleanup complete")

    def run(self):
        """Start the GUI"""
        self.window.mainloop()

    # --------------------------
    # Content management
    # --------------------------
    def _clear_content(self):
        """Clear all content from the content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

        # Reset references
        self.header_panel = None
        self.video_panel = None
        self.controls_panel = None
        self.info_panel = None
        self.dashboard = None

    # --------------------------
    # Dashboard view
    # --------------------------
    def _show_dashboard(self):
        """Show the dashboard view"""
        self._clear_content()
        self.current_view = "dashboard"

        self.dashboard = Dashboard(
            self.content_frame,
            self.db,
            self.user_config,
            on_start_workout=self._on_start_workout_from_dashboard,
            on_settings_click=self._show_settings_from_dashboard
        )

        if config.DEBUG_MODE:
            print("Switched to Dashboard view")

    def _on_start_workout_from_dashboard(self, exercise: str):
        """Handle start workout button from dashboard"""
        self._show_workout_view(exercise)
        self.window.after(500, lambda: self._auto_start_workout(exercise))

    def _show_settings_from_dashboard(self):
        """Handle settings button click from dashboard"""
        self._show_settings()

    def _auto_start_workout(self, exercise: str):
        """Auto-start workout after view switch"""
        if self.info_panel:
            self.info_panel.set_exercise(exercise)
        self._on_start_clicked()

    # --------------------------
    # Workout view
    # --------------------------
    def _show_workout_view(self, initial_exercise: str = None):
        """Show the workout view"""
        self._clear_content()
        self.current_view = "workout"

        # Setup grid layout
        self.content_frame.grid_rowconfigure(0, weight=config.LAYOUT_HEADER_WEIGHT)
        self.content_frame.grid_rowconfigure(1, weight=config.LAYOUT_VIDEO_WEIGHT)
        self.content_frame.grid_rowconfigure(2, weight=config.LAYOUT_CONTROLS_WEIGHT)
        self.content_frame.grid_columnconfigure(0, weight=config.LAYOUT_MAIN_WEIGHT)
        self.content_frame.grid_columnconfigure(1, weight=config.LAYOUT_SIDEBAR_WEIGHT)

        # Panels
        self._init_workout_panels()
        self._setup_workout_event_handlers()

        if initial_exercise and self.info_panel:
            self.info_panel.set_exercise(initial_exercise)
            self.controller.current_exercise = initial_exercise

        self._load_user_profile()
        self._check_camera_status()
        self._update_exercise_stats()

        if config.DEBUG_MODE:
            print("Switched to Workout view")

    def _init_workout_panels(self):
        """Initialize workout panels"""
        self.header_panel = HeaderPanel(
            self.content_frame,
            on_settings_click=self._show_settings,
            on_back_click=self._on_back_to_dashboard,
            on_stop_click=self._on_stop_clicked
        )
        self.video_panel = VideoPanel(self.content_frame, self.window)
        mirror_enabled = self.user_config.get('display', 'mirror_video', True)
        self.video_panel.set_mirror(mirror_enabled)

        self.controls_panel = ControlsPanel(self.content_frame)
        self.info_panel = InfoPanel(
            self.content_frame,
            on_exercise_changed=self._on_exercise_changed,
            on_history_click=self._show_history
        )

        self.controller.set_video_processor(
            self.window,
            self._process_video_frame
        )

    def _setup_workout_event_handlers(self):
        """Connect panel buttons to commands"""
        self.controls_panel.set_start_command(self._on_start_clicked)
        self.controls_panel.set_stop_command(self._on_stop_clicked)
        self.controls_panel.set_reset_command(self._on_reset_clicked)
        self.controls_panel.set_dashboard_command(self._on_back_to_dashboard)
        self.controls_panel.set_back_to_controls_command(
            lambda: self.controls_panel.show_buttons()
        )
        self.info_panel.set_exercise("Squats")

    def _on_back_to_dashboard(self):
        """Return to dashboard view"""
        if self.controller.is_running:
            self.controller.stop_workout()
        self._show_dashboard()

    # --------------------------
    # User / Camera
    # --------------------------
    def _load_user_profile(self):
        """Load user profile into header panel"""
        user_name = self.user_config.get('profile', 'name', '')
        if user_name and self.header_panel:
            self.header_panel.update_title(f"Welcome, {user_name}!")

    def _check_camera_status(self):
        """Check camera via controller"""
        if not self.video_panel:
            return

        result = self.controller.check_camera(self.video_panel)
        if not result['success'] and result['available_cameras']:
            self._show_camera_selection(result['camera_index'], result['available_cameras'])
        elif not result['success']:
            self.video_panel.show_camera_error("No cameras detected")

    def _show_camera_selection(self, failed_index, available_cameras):
        """Show overlay to pick an alternative camera"""
        overlay = ctk.CTkFrame(self.window, fg_color=("gray90", "gray10"))
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        container = ctk.CTkFrame(
            overlay,
            fg_color=config.COLOR_BACKGROUND,
            corner_radius=15
        )
        container.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.5)

        ctk.CTkLabel(
            container,
            text=f"Camera {failed_index} not available",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=config.COLOR_WARNING
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            container,
            text="Other cameras were found. Select one to use:",
            font=ctk.CTkFont(size=14),
            text_color=config.COLOR_TEXT_SECONDARY
        ).pack(pady=(0, 15))

        for cam in available_cameras:
            cam_name = cam.get('name', f"Camera {cam['index']}")
            label = f"{cam_name}  ({cam['width']}x{cam['height']})"
            ctk.CTkButton(
                container,
                text=label,
                width=320,
                height=40,
                fg_color=config.COLOR_ACCENT,
                hover_color=config.COLOR_ACCENT_HOVER,
                command=lambda idx=cam['index']: self._select_camera(idx, overlay)
            ).pack(pady=5)

        ctk.CTkButton(
            container,
            text="Skip",
            width=120,
            height=35,
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            text_color=config.COLOR_TEXT_SECONDARY,
            border_width=1,
            border_color=config.COLOR_TEXT_SECONDARY,
            command=overlay.destroy
        ).pack(pady=(15, 20))

    def _select_camera(self, camera_index, overlay):
        """Handle camera selection"""
        self.user_config.set('system', 'camera_index', camera_index)
        overlay.destroy()
        result = self.controller.check_camera(self.video_panel)
        if result['success']:
            self.video_panel.show_camera_ready()
        else:
            self.video_panel.show_camera_error(f"Camera {camera_index} failed")

    # --------------------------
    # Exercise handling
    # --------------------------
    def _on_exercise_changed(self, choice: str):
        old_exercise = self.controller.current_exercise
        if self.controller.is_running:
            backend_type = self.info_panel.get_backend_exercise_type(choice)
            if self.controller.switch_exercise(choice, backend_type):
                self.info_panel.update_state("SWITCHING", config.COLOR_WARNING)
                self.info_panel.update_feedback(f"Switched to {choice}", config.COLOR_WARNING)
                self.controls_panel.show_feedback()
                self.controls_panel.update_feedback_display(
                    title=f"SWITCHED TO {choice.upper()}",
                    main_text="Continue your workout with the new exercise",
                    tip="Form tracking has been adjusted",
                    title_color=config.COLOR_WARNING,
                    text_color=config.COLOR_WARNING
                )
        else:
            self.controller.current_exercise = choice

        self.header_panel.update_title(f"{choice}")
        self._update_exercise_stats()

        if config.DEBUG_MODE:
            print(f"Exercise changed from {old_exercise} to {choice}")

    # --------------------------
    # Start / Stop / Reset
    # --------------------------
    def _on_start_clicked(self):
        if not self.info_panel:
            return

        exercise = self.info_panel.get_exercise()
        backend_type = self.info_panel.get_backend_exercise_type()

        if self.controller.start_workout(exercise, backend_type):
            self._update_ui_for_running_state()
            print("Started workout tracking")
        else:
            self._show_error("Failed to start workout. Please check camera.")

    def _on_stop_clicked(self):
        summary = self.controller.stop_workout()
        if summary:
            self._show_session_summary(summary)
        self._update_ui_for_idle_state()
        print("Workout session stopped")

    def _on_reset_clicked(self):
        backend_type = self.info_panel.get_backend_exercise_type()
        self.controller.reset_workout(backend_type)
        self._reset_ui_counters()
        if config.DEBUG_MODE:
            print("Reset counter")

    # --------------------------
    # UI updates
    # --------------------------
    def _update_ui_for_running_state(self):
        self.info_panel.hide_panel()
        self.controls_panel.hide_panel()
        self.video_panel.set_column_span(2)
        self.header_panel.set_column_span(2)
        self.header_panel.show_workout_mode()
        self.controls_panel.disable_start_button()
        self.controls_panel.enable_stop_button()
        self.info_panel.disable_dropdown()
        self.controls_panel.disable_reset_button()
        self.controls_panel.disable_dashboard_button()
        self.info_panel.disable_history_button()
        self.info_panel.update_state("READY", config.COLOR_SUCCESS)
        self.info_panel.update_feedback("Ready for first rep!", config.COLOR_SUCCESS)
        self._reset_display_stats()

    def _update_ui_for_idle_state(self):
        self.header_panel.show_normal_mode()
        self.video_panel.set_column_span(1)
        self.header_panel.set_column_span(1)
        self.video_panel.show_text(config.WORKOUT_COMPLETE_MESSAGE, config.COLOR_SUCCESS)
        self.info_panel.show_panel()
        self.controls_panel.show_panel()
        self.controls_panel.enable_start_button()
        self.controls_panel.disable_stop_button()
        self.info_panel.enable_dropdown()
        self.controls_panel.enable_reset_button()
        self.controls_panel.enable_dashboard_button()
        self.info_panel.enable_history_button()
        self.controls_panel.show_buttons()
        self._update_exercise_stats()

    def _reset_ui_counters(self):
        self.info_panel.update_rep_count(0)
        self.info_panel.update_state("READY", config.COLOR_WARNING)
        self.info_panel.update_feedback("Start exercising to see feedback", config.COLOR_TEXT_SECONDARY)
        self._reset_display_stats()

    def _reset_display_stats(self):
        self.controls_panel.update_feedback_display(
            quality_text="Excellent: 0 | Good: 0 | Poor: 0",
            angle_text="Angle: --°",
            tip=""
        )

    # --------------------------
    # Video processing
    # --------------------------
    def _process_video_frame(self):
        if not self.controller.is_running:
            return

        result = self.controller.process_video_frame()
        if not result:
            return

        frame = result.get('frame')
        if frame is not None:
            self.video_panel.update_video_frame(frame)

        rep_count = result.get('rep_count')
        if rep_count is not None:
            self.info_panel.update_rep_count(rep_count)
            self.header_panel.update_workout_reps(rep_count)

        current_angle = result.get('current_angle')
        if current_angle is not None:
            self.controls_panel.update_feedback_display(angle_text=f"Angle: {current_angle:.1f}°")
            self.header_panel.update_workout_angle(current_angle)

        feedback = result.get('form_feedback', {})
        if feedback.get('feedback'):
            self._update_form_feedback(feedback)
            quality = feedback.get('quality', 'unknown')
            header_color = {
                'excellent': config.COLOR_SUCCESS,
                'good': config.COLOR_WARNING,
                'poor': config.COLOR_ERROR,
                'invalid': config.COLOR_TEXT_SECONDARY,
            }.get(quality, config.COLOR_TEXT_POP2)
            self.header_panel.update_workout_feedback(feedback['feedback'], header_color)

        stats = result.get('stats', {})
        if stats and self.controller.session:
            self.controller.session.stats.update_from_dict(stats)
            self.controls_panel.update_feedback_display(quality_text=self.controller.session.stats.quality_text)

        if result.get('rep_completed'):
            rep_count = result.get('rep_count', 0)
            self.controls_panel.update_feedback_display(tip=f"Rep {rep_count} completed!")

    def _update_form_feedback(self, feedback):
        quality = feedback.get('quality', 'unknown')
        if quality == 'excellent':
            color = config.COLOR_SUCCESS
            state = "EXCELLENT"
        elif quality == 'good':
            color = config.COLOR_WARNING
            state = "GOOD"
        elif quality == 'poor':
            color = config.COLOR_ERROR
            state = "NEEDS WORK"
        else:
            color = config.COLOR_TEXT_SECONDARY
            state = "ANALYZING"

        self.info_panel.update_feedback(feedback['feedback'], color)
        self.info_panel.update_state(state, color)
        self.controls_panel.update_feedback_display(
            title=f"{state} FORM",
            main_text=feedback['feedback'],
            title_color=color,
            text_color=color
        )

    # --------------------------
    # Stats / session / history
    # --------------------------
    def _update_exercise_stats(self):
        if not self.info_panel:
            return

        try:
            exercise = self.info_panel.get_exercise()
            backend_type = self.info_panel.get_backend_exercise_type(exercise)
            stats = self.db.get_total_stats()
            reps_by_exercise = stats.get('reps_by_exercise', {})
            total_reps = reps_by_exercise.get(backend_type, 0)
            exercise_name = backend_type.replace('_', ' ').title() + "s"
            text = f"{exercise_name} Stats:\nTotal Reps: {total_reps}\n"

            excellent = stats.get('total_excellent_reps', 0)
            good = stats.get('total_good_reps', 0)
            poor = stats.get('total_poor_reps', 0)
            if excellent + good + poor > 0:
                text += f"\nForm Quality:\nExcellent: {excellent}\nGood: {good}\nPoor: {poor}"

            self.info_panel.update_exercise_stats(text)
        except Exception as e:
            print(f"Error updating exercise stats: {e}")
            self.info_panel.update_exercise_stats("Error loading stats")

    def _show_session_summary(self, summary_data):
        try:
            if self.controller.session and self.controller.session.session_id:
                session_id = self.controller.session.session_id
                summary_dialog = SummaryDialog(self.window, self.db)
                summary_dialog.show(session_id)
            else:
                print("Warning: No session ID available for summary")
                self._show_error("Could not load workout summary - session data missing")
        except Exception as e:
            print(f"Error showing summary: {e}")
            self._show_error(f"Could not display workout summary: {str(e)}")

    def _show_history(self):
        try:
            history_dialog = HistoryDialog(self.window, self.db)
            history_dialog.show()
        except Exception as e:
            print(f"Error showing history: {e}")
            self._show_error(f"Cannot load history: {str(e)}")

    # --------------------------
    # Settings
    # --------------------------
    def _show_settings(self):
        try:
            was_running = self.controller.is_running if self.controller else False
            if self.engine and self.engine.cap is not None:
                self.engine.cap.release()
                self.engine.cap = None
                self.engine.camera_initialized = False

            settings_window = ctk.CTkToplevel(self.window)
            settings_window.title("Settings")
            settings_window.geometry("700x600")
            settings_window.configure(fg_color=config.COLOR_BACKGROUND)
            settings_window.transient(self.window)
            settings_window.grab_set()

            settings_window.update_idletasks()
            x = (settings_window.winfo_screenwidth() // 2) - (700 // 2)
            y = (settings_window.winfo_screenheight() // 2) - (600 // 2)
            settings_window.geometry(f"700x600+{x}+{y}")

            def on_settings_saved():
                self._load_user_profile()
                if self.video_panel:
                    mirror_enabled = self.user_config.get('display', 'mirror_video', True)
                    self.video_panel.set_mirror(mirror_enabled)
                if self.dashboard and self.dashboard.exercise_selector:
                    backend_to_display = {"squat": "Squats", "pushup": "Push-ups", "curl": "Curls"}
                    saved = self.user_config.get('workout', 'default_exercise', 'squat')
                    display = backend_to_display.get(saved)
                    if display:
                        self.dashboard.exercise_selector.set_exercise(display)

            def on_window_close():
                if self.engine and not was_running:
                    self.engine.start_camera()
                settings_window.destroy()

            set_close_handler(settings_window, on_window_close)
            SettingsPanel(settings_window, self.user_config, on_save_callback=on_settings_saved)

        except Exception as e:
            print(f"Error showing settings: {e}")
            self._show_error(f"Cannot open settings: {str(e)}")

    # --------------------------
    # Error dialog
    # --------------------------
    def _show_error(self, message):
        error_dialog = ErrorDialog(self.window)
        error_dialog.show(message)
