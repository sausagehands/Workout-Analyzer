"""
Pushup exercise detector
Tracks pushup repetitions using elbow angle
"""
from enum import Enum
from core_cv.detection.detector_blueprint import ExerciseDetector
from config.app_constants import PUSHUP_THRESHOLDS

"""
states for pushup exercise
"""
class PushupState(Enum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"

"""
state machine for counting pushup reps
"""
class PushupDetector(ExerciseDetector):
    def __init__(self):
        super().__init__(
            name="pushup",
            cooldown_frames=PUSHUP_THRESHOLDS['COOLDOWN_FRAMES']
        )
        
        self.current_state = PushupState.UNKNOWN
        
        self.UP_THRESHOLD = PUSHUP_THRESHOLDS['UP']
        self.DOWN_THRESHOLD = PUSHUP_THRESHOLDS['DOWN']
        
    """
    Update state and count reps
    
    Args:
        elbow_angle: Current elbow angle in degrees (or None)
    
    Returns:
        bool: True if rep just completed
    """    
    def update(self, elbow_angle: float) -> bool:
        self._decrement_cooldown()
        
        if elbow_angle is None:
            new_state = PushupState.UNKNOWN
        elif elbow_angle > self.UP_THRESHOLD:
            new_state = PushupState.UP
        elif elbow_angle < self.DOWN_THRESHOLD:
            new_state = PushupState.DOWN
        else:
            new_state = self.current_state
        
        rep_completed = False
        if (new_state == PushupState.UP and
            self.current_state == PushupState.DOWN and
            self.cooldown_frames == 0):
            
            self._increment_rep()
            rep_completed = True
            self._start_cooldown()
        
        if new_state != PushupState.UNKNOWN:
            self.current_state = new_state
        
        return rep_completed
    
    """Get current state as string"""
    def get_state_name(self) -> str:
        return self.current_state.value
    
    """Reset rep count and state"""
    def reset(self):
        super().reset()
        self.current_state = PushupState.UNKNOWN


# Standalone test
if __name__ == "__main__":
    print("Testing PushupDetector...")
    
    detector = PushupDetector()
    angles = [170, 165, 140, 110, 85, 80, 85, 110, 140, 165, 170]
    
    for angle in angles:
        completed = detector.update(angle)
        if completed:
            print(f"  ✓ Rep {detector.rep_count} completed at angle {angle}°")
    
    print(f"  Total reps: {detector.rep_count}")
    assert detector.rep_count == 1
    print("✓ PushupDetector test passed!")