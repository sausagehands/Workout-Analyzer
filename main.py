"""
Main entry point with setup wizard integration
Checks if initial setup is complete before showing main app
Opens to Dashboard by default
"""
# Must be set before any imports:
# 1. Matplotlib (pulled in by mediapipe) — use non-interactive backend
# 2. OpenCV on macOS — skip its own camera auth request (crashes the GIL
#    when running inside tkinter). The .app bundle's Info.plist handles
#    the permission prompt instead.
import os
import signal
os.environ['MPLBACKEND'] = 'Agg'
# Override PyInstaller's runtime hook that forces MPLCONFIGDIR to a temp dir
# (which gets deleted on exit, causing a 30s font-cache rebuild every launch).
# Use a persistent location instead so the scan only happens once.
_mpl_cache = os.path.join(os.path.expanduser('~'), '.workout_analyzer', 'mpl_cache')
os.makedirs(_mpl_cache, exist_ok=True)
os.environ['MPLCONFIGDIR'] = _mpl_cache
import sys
import traceback
import platform


def _request_camera_permission():
    """
    On macOS, trigger camera permission *before* tkinter starts.
    OpenCV's AVFoundation auth request crashes the GIL when called
    from inside tkinter's mainloop, so we do it here on the main
    thread while nothing else is running.
    """
    if platform.system() != 'Darwin':
        return
    import cv2
    import time
    # Try camera indices 0 and 1 to trigger permission dialog
    for idx in (0, 1):
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            time.sleep(0.5)
            cap.read()  # triggers the macOS permission dialog if needed
            cap.release()
            break
        cap.release()


from database.workout_database import WorkoutDatabase
from core.workout_engine import WorkoutEngine
from gui import AppContainer
from config.user_config import UserConfig
from gui.setup_wizard import SetupWizard
import customtkinter as ctk


def main():
    """Initialize and run the application with setup check"""

    print("="*50)
    print("AI WORKOUT FORM ANALYZER")
    print("="*50)
    print("Initializing...")

    # Request camera permission before tkinter starts (macOS only)
    _request_camera_permission()
    
    
    try:
        # Initialize user configuration
        user_config = UserConfig()
        print("[OK] User configuration loaded")
        
        # Check if setup is complete
        if not user_config.is_setup_complete():
            print("First time setup required...")

            # Create root window for setup wizard
            root = ctk.CTk()
            root.withdraw()  # Hide main window

            setup_completed = False

            def on_setup_complete():
                """Callback when setup is complete"""
                nonlocal setup_completed
                setup_completed = True
                print("[OK] Setup completed!")
                # Use after to ensure clean window destruction
                root.after(100, lambda: launch_main_after_setup(root, user_config))

            # Show setup wizard
            wizard = SetupWizard(user_config, on_setup_complete)
            root.mainloop()

            # If wizard was closed without completing, exit cleanly
            if not setup_completed:
                print("Setup was not completed. Exiting.")
                sys.exit(0)
        else:
            # Setup already complete - launch main app
            launch_main_app(user_config)
            
    except ImportError as e:
        print(f"[FAIL] Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install opencv-python mediapipe customtkinter")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Failed to start application: {e}")
        traceback.print_exc()
        sys.exit(1)


def launch_main_after_setup(root, user_config: UserConfig):
    """Launch main application after setup completion"""
    try:
        root.destroy()
        launch_main_app(user_config)
    except Exception as e:
        print(f"[FAIL] Failed to launch main app: {e}")
        traceback.print_exc()
        sys.exit(1)


def launch_main_app(user_config: UserConfig):
    """Launch main application"""
    
    print("="*50)
    print("Launching main application...")
    
    try:
        # Initialize database
        db = WorkoutDatabase()
        print("[OK] Database initialized")
        
        # Initialize workout engine with user config
        engine = WorkoutEngine(db, user_config)
        print("[OK] Workout engine initialized")
        
        # Create and run GUI (starts with Dashboard)
        print("[OK] Starting GUI (Dashboard)...")
        print("="*50)

        app = AppContainer(engine, db, user_config)

        def _shutdown(signum=None, frame=None):
            """Handle SIGINT/SIGTERM — save session before exit."""
            print(f"\nReceived signal {signum}, saving and exiting...")
            try:
                app.cleanup()
            except Exception:
                pass
            try:
                db.close()
            except Exception:
                pass
            sys.exit(0)

        signal.signal(signal.SIGINT, _shutdown)
        signal.signal(signal.SIGTERM, _shutdown)

        try:
            app.run()
        finally:
            # Cleanup on exit
            print("\n" + "="*50)
            print("Shutting down...")
            try:
                app.cleanup()
            except Exception as e:
                print(f"Warning: GUI cleanup error: {e}")
            try:
                db.close()
            except Exception as e:
                print(f"Warning: Database close error: {e}")
            print("Application closed")
            print("="*50)
            
    except Exception as e:
        print(f"[FAIL] Failed to initialize application: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()