"""
Exercise detection modules
Each detector implements a state machine for counting reps
"""
from core_cv.detection.exercises.squat_detector import SquatDetector, SquatState
from core_cv.detection.exercises.pushup_detector import PushupDetector, PushupState
from core_cv.detection.exercises.bicep_curl_detector import BicepCurlDetector, CurlState
from core_cv.detection.detector_blueprint import ExerciseDetector

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