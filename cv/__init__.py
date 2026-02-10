"""Computer vision components"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cv.pose_detection import PoseDetector
from core_cv.analysis.angle_math import calculate_angle
from core_cv.analysis.form_analysis import analyze_squat_form, analyze_pushup_form, analyze_curl_form

# Import exercise detectors
try:
    from core_cv.detection.exercises import SquatDetector, PushupDetector, CurlDetector
except ImportError as e:
    print(f"Warning: Could not import exercise detectors: {e}")
    # Create dummy classes
    class SquatDetector:
        def __init__(self): self.rep_count = 0
        def update(self, angle): return False
        def reset(self): self.rep_count = 0
    
    class PushupDetector:
        def __init__(self): self.rep_count = 0
        def update(self, angle): return False
        def reset(self): self.rep_count = 0
    
    class CurlDetector:
        def __init__(self): self.rep_count = 0
        def update(self, angle): return False
        def reset(self): self.rep_count = 0

__all__ = [
    'PoseDetector',
    'calculate_angle',
    'analyze_squat_form',
    'analyze_pushup_form',
    'analyze_curl_form',
    'SquatDetector',
    'PushupDetector',
    'CurlDetector'
]
