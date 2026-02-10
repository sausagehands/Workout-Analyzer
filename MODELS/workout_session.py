"""
Workout session management
"""
import time
from typing import Optional, Dict, Any
from .workout_state import WorkoutStats


'''
represents real workout in system--literally a domain object that changes over time
contains:
    exercise type
    stats
    start time
    end time
    notes
    session id
    duration
'''

class WorkoutSession:
    """Manages workout session state"""
    def __init__(self, engine, exercise_type: str = "Squats"):
        '''refers to engine logic-- makes the car move -> core processing system that runs functionality'''
        self.engine = engine
        self.exercise_type = exercise_type
        self.session_id: Optional[int] = None
        self.stats = WorkoutStats()
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.notes: str = ""
        
    def start(self) -> bool:
        """Start a new workout session"""
        try:
            self.session_id = self.engine.start_session()
            if self.session_id:
                self.start_time = time.time()
                return True
            return False
        except Exception as e:
            print(f"Failed to start session: {e}")
            return False
    
    def end(self, notes: str = "") -> Optional[Dict[str, Any]]:
        """End the current workout session"""
        try:
            if self.session_id:
                if hasattr(self.engine, 'end_session'):
                    self.engine.end_session(notes)
                
                self.end_time = time.time()
                self.notes = notes
                
                # Get session summary
                summary = {}
                if hasattr(self.engine, 'get_session_summary'):
                    summary = self.engine.get_session_summary(self.session_id)
                
                self.session_id = None
                return summary
        except Exception as e:
            print(f"Error ending session: {e}")
        
        return None
    
    @property
    def duration(self) -> float:
        """Get session duration in seconds"""
        if self.start_time:
            end = self.end_time or time.time()
            return end - self.start_time
        return 0.0