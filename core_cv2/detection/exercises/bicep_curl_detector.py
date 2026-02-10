"""
Bicep curl exercise detector
Tracks curl repetitions using elbow angle
"""
from enum import Enum
from core_cv2.detection.detector_blueprint import ExerciseDetector
from config.app_constants import CURL_THRESHOLDS


class CurlState(Enum):
    """States for bicep curl exercise"""
    DOWN = "down"
    CURLED = "curled"
    UNKNOWN = "unknown"


class BicepCurlDetector(ExerciseDetector):
    """State machine for counting bicep curl reps"""
    
    def __init__(self):
        """Initialize curl detector"""
        super().__init__(
            name="curl",
            cooldown_frames=CURL_THRESHOLDS['COOLDOWN_FRAMES']
        )
        
        self.current_state = CurlState.UNKNOWN
        
        self.DOWN_THRESHOLD = CURL_THRESHOLDS['DOWN']
        self.CURLED_THRESHOLD = CURL_THRESHOLDS['CURLED']
    
    def update(self, elbow_angle: float) -> bool:
        """
        Update state and count reps
        
        Args:
            elbow_angle: Current elbow angle in degrees (or None)
        
        Returns:
            bool: True if rep just completed
        """
        self._decrement_cooldown()
        
        if elbow_angle is None:
            new_state = CurlState.UNKNOWN
        elif elbow_angle > self.DOWN_THRESHOLD:
            new_state = CurlState.DOWN
        elif elbow_angle < self.CURLED_THRESHOLD:
            new_state = CurlState.CURLED
        else:
            new_state = self.current_state
        
        rep_completed = False
        if (new_state == CurlState.DOWN and
            self.current_state == CurlState.CURLED and
            self.cooldown_frames == 0):
            
            self._increment_rep()
            rep_completed = True
            self._start_cooldown()
        
        if new_state != CurlState.UNKNOWN:
            self.current_state = new_state
        
        return rep_completed
    
    def get_state_name(self) -> str:
        """Get current state as string"""
        return self.current_state.value
    
    def reset(self):
        """Reset rep count and state"""
        super().reset()
        self.current_state = CurlState.UNKNOWN


# Standalone test
if __name__ == "__main__":
    print("Testing CurlDetector...")
    
    detector = BicepCurlDetector()
    angles = [170, 165, 140, 100, 60, 45, 60, 100, 140, 165, 170]
    
    for angle in angles:
        completed = detector.update(angle)
        if completed:
            print(f"  ✓ Rep {detector.rep_count} completed at angle {angle}°")
    
    print(f"  Total reps: {detector.rep_count}")
    assert detector.rep_count == 1
    print("✓ CurlDetector test passed!")