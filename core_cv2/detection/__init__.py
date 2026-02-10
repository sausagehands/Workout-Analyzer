"""
Exercise detection modules
Each detector implements a state machine for counting reps
"""
from core_cv2.detection.exercises.squat_detector import SquatDetector, SquatState
from core_cv2.detection.exercises.pushup_detector import PushupDetector, PushupState
from core_cv2.detection.exercises.bicep_curl_detector import BicepCurlDetector, CurlState
from core_cv2.detection.detector_blueprint import ExerciseDetector

CurlDetector = BicepCurlDetector

__all__ = [
    'ExerciseDetector',
    'SquatDetector',
    'SquatState',
    'PushupDetector',
    'PushupState',
    'BicepCurlDetector',
    'CurlDetector',
    'CurlState',
]