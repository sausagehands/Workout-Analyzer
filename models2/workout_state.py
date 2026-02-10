"""
Workout state enums and data classes
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

'''
WorkoutState & FormQuality define allowed states-- (enum defines state models)
'''
class WorkoutState(Enum):
    """Enum for workout state machine"""
    IDLE = "IDLE"
    # READY = "READY"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    # ERROR = "ERROR"


class FormQuality(Enum):
    """Enum for form quality ratings"""
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    POOR = "POOR"
    UNKNOWN = "UNKNOWN"



'''pure data model-- only holds data'''
@dataclass
class WorkoutStats:
    """Data class for workout statistics"""
    total_reps: int = 0
    excellent_reps: int = 0
    good_reps: int = 0
    poor_reps: int = 0
    
    def reset(self):
        """Reset all stats to zero"""
        self.total_reps = 0
        self.excellent_reps = 0
        self.good_reps = 0
        self.poor_reps = 0
    
    def update_from_dict(self, stats_dict: Dict[str, int]):
        """Update stats from dictionary"""
        self.total_reps = stats_dict.get('total_reps', 0)
        self.excellent_reps = stats_dict.get('excellent_reps', 0)
        self.good_reps = stats_dict.get('good_reps', 0)
        self.poor_reps = stats_dict.get('poor_reps', 0)
    
    @property
    def quality_text(self) -> str:
        """Format quality stats as text"""
        return f"Excellent: {self.excellent_reps} | Good: {self.good_reps} | Poor: {self.poor_reps}"