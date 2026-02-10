"""
Squat exercise detector
Tracks squat repetitions using knee angle
"""
from enum import Enum
from core_cv2.detection.detector_blueprint import ExerciseDetector
from config.app_constants import SQUAT_THRESHOLDS


class SquatState(Enum):
    """
    states for squat exercise
    """
    STANDING = "standing"
    SQUATTING = "squatting"
    UNKNOWN = "unknown"


class SquatDetector(ExerciseDetector):
    """
    state machine for counting squat reps
    """
    def __init__(self):
        super().__init__(
            name="squat",
            cooldown_frames=SQUAT_THRESHOLDS['COOLDOWN_FRAMES']
        )
        
        self.current_state = SquatState.UNKNOWN
        
        self.STANDING_THRESHOLD = SQUAT_THRESHOLDS['STANDING']
        self.SQUATTING_THRESHOLD = SQUAT_THRESHOLDS['SQUATTING']
    
    
    """
    update state machine with new knee angle
    
    args:
        knee_angle: current knee angle in degrees (or None)
    
    returns:
        bool: True if rep just completed, False otherwise
    """
    def update(self, knee_angle: float) -> bool:
        self._decrement_cooldown()
        
        # determine new state from angle
        if knee_angle is None:
            new_state = SquatState.UNKNOWN
        elif knee_angle > self.STANDING_THRESHOLD:
            new_state = SquatState.STANDING
        elif knee_angle < self.SQUATTING_THRESHOLD:
            new_state = SquatState.SQUATTING
        else:
            # hysteresis - keep current state
            new_state = self.current_state
        
        # check for rep completion (transition from squatting to standing)
        rep_completed = False
        if (
            new_state == SquatState.STANDING and
            self.current_state == SquatState.SQUATTING and
            self.cooldown_frames == 0
            ):
            
            self._increment_rep()
            rep_completed = True
            self._start_cooldown()
        
        # update state
        if new_state != SquatState.UNKNOWN:
            self.current_state = new_state
        
        return rep_completed
    
    """
    get current state as string
    """
    def get_state_name(self) -> str:
        return self.current_state.value
    
    """
    reset rep count and state
    """
    def reset(self):
        super().reset()
        self.current_state = SquatState.UNKNOWN


# Standalone test
if __name__ == "__main__":
    print("Testing SquatDetector...")
    
    detector = SquatDetector()
    
    # Simulate squat movement
    angles = [175, 170, 150, 120, 90, 85, 90, 120, 150, 170, 175]
    
    for angle in angles:
        completed = detector.update(angle)
        if completed:
            print(f"  ✓ Rep {detector.rep_count} completed at angle {angle}°")
    
    print(f"  Total reps: {detector.rep_count}")
    assert detector.rep_count == 1, "Should count exactly 1 rep"
    print("✓ SquatDetector test passed!")