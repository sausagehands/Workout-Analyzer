"""
GUI package - exports main components
"""

# Import the main GUI classes
#from .workout_app import WorkoutGUI
from .app_container import AppContainer

# For backward compatibility - export what main.py expects
__all__ = ['WorkoutGUI', 'AppContainer']