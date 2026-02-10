"""
• abstract base class (ABC) for exercise detectors
    - ABCs give python a way to create 'incomplete parent classes' that force child classes
    to finish them-- a template that can't run on its own -> abstract methods need to be implemented

• provides common functionality for rep counting
"""
from abc import ABC, abstractmethod

class ExerciseDetector(ABC):
    def __init__(self, name: str, cooldown_frames: int = 15):
        '''
        -initialize base detector
        -args:
            -name: name of exercise ('squat', 'pushup', ...)
        '''
        
        self.name = name
        self.rep_count = 0
        self.cooldown_frames = 0
        self.COOLDOWN_PERIOD = cooldown_frames
    
    
    @abstractmethod
    def update(self, angle: float) -> bool:
        """
        • update state machine with new angle measurement
        • must be implemented by subclasses
        
        • args:
            • angle: current joint angle in degrees
        
        • returns:
            • bool: True if rep just completed, False otherwise
        """ 
        pass
    
    
    
    @abstractmethod
    def get_state_name(self) -> str:
        """
        • get current state as string
        • must be implemented by subclasses
        """
        pass
    
    def reset(self):
        """
        • reset rep count and state
        • subclasses should override to also reset their state
        """
        self.rep_count = 0
        self.cooldown_frames = 0
    

    def _decrement_cooldown(self):
        '''
        decrease cooldown counter
        '''
        if self.cooldown_frames > 0:
            self.cooldown_frames -= 1
            
    
    def _start_cooldown(self):
        '''
        start cooldown period
        '''
        self.cooldown_frames = self.COOLDOWN_PERIOD
    
   
    def _increment_rep(self):
         
        '''increment rep counter'''
        self.rep_count += 1

    def update_thresholds(self, **kwargs):
        """
        Update threshold values dynamically (for auto-calibration).

        Args:
            **kwargs: threshold name-value pairs (e.g., STANDING=150, SQUATTING=95)
        """
        for key, value in kwargs.items():
            # Try direct attribute name first
            if hasattr(self, key):
                setattr(self, key, value)
            # Try with _THRESHOLD suffix
            elif hasattr(self, f"{key}_THRESHOLD"):
                setattr(self, f"{key}_THRESHOLD", value)
            # Try COOLDOWN special case
            elif key == 'COOLDOWN_FRAMES' and hasattr(self, 'COOLDOWN_PERIOD'):
                self.COOLDOWN_PERIOD = value
