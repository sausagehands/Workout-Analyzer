"""
Configuration constants for workout analyzer
★ SINGLE SOURCE OF TRUTH ★

This file contains ALL default values for the entire application.
Other modules (including user_config.py) should reference these values.

DO NOT hardcode these values elsewhere - import from here!
"""
import sys
import os
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a bundled resource.
    Works both in development and when bundled with PyInstaller.

    When running as a PyInstaller bundle, files are extracted to a
    temporary folder stored in sys._MEIPASS. In development, paths
    resolve relative to the project root.
    """
    if getattr(sys, 'frozen', False):
        # Running inside a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in normal development mode
        base_path = str(Path(__file__).parent.parent)
    return os.path.join(base_path, relative_path)


# ---------------------------------------------------------------------------- #
#                               DATABASE SETTINGS                              #
# ---------------------------------------------------------------------------- #


# Database lives in the user's home directory (not inside the bundle),
# so it persists across launches and bundle updates.
DATABASE_PATH = os.path.join(Path.home(), '.workout_analyzer', 'workouts.db')

# ---------------------------------------------------------------------------- #
#                               VIDEO/CAMERA SETTINGS                          #
# ---------------------------------------------------------------------------- #
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
TARGET_FPS = 30

# ---------------------------------------------------------------------------- #
#                               MEDIAPIPE SETTINGS                            #
# ---------------------------------------------------------------------------- #
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.7
MODEL_COMPLEXITY = 1  # 0=Lite, 1=Full, 2=Heavy
VISIBILITY_THRESHOLD = 0.5

# ---------------------------------------------------------------------------- #
#                               EXERCISE THRESHOLDS (degrees and frames)      #
# NOTE: Keys are UPPERCASE to match detector file expectations                 #
# ---------------------------------------------------------------------------- #

SQUAT_THRESHOLDS = {
    'STANDING': 155,        # Knee angle when standing (degrees) - tightened
    'SQUATTING': 110,       # Knee angle when squatting (degrees) - must bend more
    'COOLDOWN_FRAMES': 25,  # Frames to wait before counting next rep (~0.8s at 30fps)
    'EXCELLENT': 90,        # Angle for excellent form
    'GOOD': 105,            # Angle for good form
    'CALIBRATED': False,
    'CALIBRATION_DATE': None,
    # Form validation (anti-cheat) — normalized (fraction of frame height)
    'MIN_HIP_DROP': 0.083,  # Hip must drop at least ~8.3% of frame height
    'MIN_BACK_ANGLE': 135,  # Back angle must stay ≥ 135°
}

PUSHUP_THRESHOLDS = {
    'UP': 155,              # Tightened
    'DOWN': 110,            # Must go lower to count
    'COOLDOWN_FRAMES': 20,  # Increased cooldown (~0.7s at 30fps)
    'EXCELLENT': 90,
    'GOOD': 110,
    'CALIBRATED': False,
    'CALIBRATION_DATE': None,
    # Form validation (anti-cheat) — normalized (fraction of frame height)
    'MIN_SHOULDER_DROP': 0.063,  # Shoulder must drop at least ~6.3% of frame height
    'MIN_BACK_ANGLE': 155,       # Back must stay straight ≥ 155°
}

CURL_THRESHOLDS = {
    'DOWN': 155,            # Tightened
    'CURLED': 70,           # Must curl more to count
    'COOLDOWN_FRAMES': 18,  # Increased cooldown (~0.6s at 30fps)
    'EXCELLENT': 50,
    'GOOD': 70,
    'CALIBRATED': False,
    'CALIBRATION_DATE': None,
    # Form validation (anti-cheat) — normalized (fraction of frame height)
    'MIN_WRIST_RISE': 0.042,  # Wrist must rise at least ~4.2% of frame height
}

# Registry of all exercises with their thresholds
EXERCISE_THRESHOLDS = {
    'squat': SQUAT_THRESHOLDS,
    'pushup': PUSHUP_THRESHOLDS,
    'curl': CURL_THRESHOLDS
}

# ---------------------------------------------------------------------------- #
#                       UI COLORS (BGR FORMAT for OpenCV)                      #
# ---------------------------------------------------------------------------- #
COLORS = {
    'EXCELLENT': (0, 255, 0),      # Green
    'GOOD': (0, 255, 255),          # Yellow
    'POOR': (0, 165, 255),          # Orange
    'NEUTRAL': (255, 255, 255),     # White
    'ERROR': (0, 0, 255)            # Red
}

# # ---------------------------------------------------------------------------- #
# #                               DISPLAY SETTINGS                              #
# # ---------------------------------------------------------------------------- #
# RECENT_SESSIONS_LIMIT = 10
# EXERCISE_HISTORY_LIMIT = 30

# ---------------------------------------------------------------------------- #
#                               MEDIAPIPE LANDMARK INDICES                    #
# ---------------------------------------------------------------------------- #
LANDMARKS = {
    'LEFT_SHOULDER': 11,
    'LEFT_ELBOW': 13,
    'LEFT_WRIST': 15,
    'LEFT_HIP': 23,
    'LEFT_KNEE': 25,
    'LEFT_ANKLE': 27,
    
    'RIGHT_SHOULDER': 12,
    'RIGHT_ELBOW': 14,
    'RIGHT_WRIST': 16,
    'RIGHT_HIP': 24,
    'RIGHT_KNEE': 26,
    'RIGHT_ANKLE': 28
}

# ---------------------------------------------------------------------------- #
#                          DEFAULT USER CONFIG VALUES                          #
# ---------------------------------------------------------------------------- #
'''These are the defaults for user-configurable settings'''

# ----------------------------- Profile Defaults ----------------------------- #
DEFAULT_PROFILE = {
    'name': '',
    'height_cm': None,
    'created_at': None,
    'last_updated': None
}

# ------------------------------ System Defaults ------------------------------ #

DEFAULT_SYSTEM = {
    'camera_index': CAMERA_INDEX,                          # 0
    'video_width': FRAME_WIDTH,                            # 640
    'video_height': FRAME_HEIGHT,                          # 480
    'target_fps': TARGET_FPS,                              # 30
    'model_complexity': MODEL_COMPLEXITY,                  # 1
    'detection_confidence': MIN_DETECTION_CONFIDENCE,      # 0.7
    'tracking_confidence': MIN_TRACKING_CONFIDENCE,        # 0.7
    'preferred_side': 'left',  # 'left' or 'right'
    'cached_cameras': None,  # Populated by camera scan
}

# ----------------------------- Display Defaults ----------------------------- #
DEFAULT_DISPLAY = {
    'show_skeleton': True,
    'show_angle_overlay': True,
    'show_rep_counter': True,
    'show_form_feedback': True,
    'show_fps': False,
    'mirror_video': True,
    'theme': 'dark',  # 'dark' or 'light'
    'font_size': 'medium',  # 'small', 'medium', 'large'
}

# ----------------------------- Workout Defaults ----------------------------- #
DEFAULT_WORKOUT = {
    'default_exercise': 'squat',
}

# ----------------------------- Statistics Defaults ----------------------------- #
DEFAULT_STATISTICS = {
    'show_weekly_summary': True,
    'show_progress_charts': True,
    'track_personal_records': True,
    'weekly_goal_enabled': True,
    'weekly_goal_workouts': 3,
    'monthly_goal_enabled': False,
    'monthly_goal_workouts': 12
}

# ----------------------------- Privacy Defaults ----------------------------- #
DEFAULT_PRIVACY = {
    'save_workout_videos': False,
    'save_screenshots': False,
    'video_retention_days': 30
}

# ------------------------------ Legal Defaults ------------------------------ #

DEFAULT_LEGAL = {
    'liability_waiver': {
        'accepted': False,
        'version': None,
        'accepted_at': None,
    }
}

# ------------------------------ Setup Defaults ------------------------------ #
DEFAULT_SETUP = {
    'completed': False,
    'wizard_version': '1.0',
    'completion_date': None,
}

# ═══════════════════════════════════════════════════════════════════════════
# COMPLETE DEFAULT CONFIG
# This is what user_config.py should use as DEFAULT_CONFIG
# ═══════════════════════════════════════════════════════════════════════════
DEFAULT_USER_CONFIG = {
    'profile': DEFAULT_PROFILE,
    'system': DEFAULT_SYSTEM,
    'display': DEFAULT_DISPLAY,
    'thresholds': {
        exercise_type: thresholds.copy() 
        for exercise_type, thresholds in EXERCISE_THRESHOLDS.items()
    },
    'workout': DEFAULT_WORKOUT,
    # 'statistics': DEFAULT_STATISTICS,
    'privacy': DEFAULT_PRIVACY,
    'legal': DEFAULT_LEGAL,
    'setup': DEFAULT_SETUP
}

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def get_default_thresholds(exercise_type: str) -> dict:
    """
    Get default thresholds for an exercise type
    
    Args:
        exercise_type: 'squat', 'pushup', or 'curl'
    
    Returns:
        dict: Copy of default thresholds
    
    Raises:
        ValueError: If exercise_type is unknown
    """
    if exercise_type in EXERCISE_THRESHOLDS:
        return EXERCISE_THRESHOLDS[exercise_type].copy()
    raise ValueError(f"Unknown exercise type: {exercise_type}")


# def get_all_exercise_types() -> list:
#     """
#     Get list of all available exercise types
    
#     Returns:
#         list: Exercise type names
#     """
#     return list(EXERCISE_THRESHOLDS.keys())


def get_default_config() -> dict:
    """
    Get complete default user configuration
    
    Returns:
        dict: Deep copy of default configuration
    """
    import copy
    return copy.deepcopy(DEFAULT_USER_CONFIG)


# def get_camera_index() -> int:
#     """Get default camera index"""
#     return CAMERA_INDEX


# def get_video_resolution() -> tuple:
#     """
#     Get default video resolution
    
#     Returns:
#         tuple: (width, height)
#     """
#     return (FRAME_WIDTH, FRAME_HEIGHT)


# def get_mediapipe_config() -> dict:
#     """
#     Get MediaPipe configuration
    
#     Returns:
#         dict: MediaPipe settings
#     """
#     return {
#         'model_complexity': MODEL_COMPLEXITY,
#         'min_detection_confidence': MIN_DETECTION_CONFIDENCE,
#         'min_tracking_confidence': MIN_TRACKING_CONFIDENCE
#     }


# # ═══════════════════════════════════════════════════════════════════════════
# # VALIDATION
# # ═══════════════════════════════════════════════════════════════════════════

# def validate_camera_index(index: int) -> bool:
#     """Validate camera index is in valid range"""
#     return isinstance(index, int) and 0 <= index <= 10


# def validate_model_complexity(complexity: int) -> bool:
#     """Validate MediaPipe model complexity"""
#     return complexity in [0, 1, 2]


# def validate_confidence(confidence: float) -> bool:
#     """Validate confidence threshold"""
#     return isinstance(confidence, (int, float)) and 0.0 <= confidence <= 1.0


# def validate_exercise_type(exercise_type: str) -> bool:
#     """Validate exercise type is known"""
#     return exercise_type in EXERCISE_THRESHOLDS