"""
Thin manager for per-exercise form validators.
Selects the appropriate validator and delegates all work to it.
"""
from core_cv2.validation import SquatValidator, PushupValidator, CurlValidator


class FormValidator:
    """
    Manages per-exercise form validators.

    Responsibilities:
        - Select the correct validator based on exercise type
        - Delegate update/validate calls
        - Provide access to rep history and trends
    """

    def __init__(self):
        self._validators = {
            'squat': SquatValidator(),
            'pushup': PushupValidator(),
            'curl': CurlValidator(),
        }
        self.current_exercise = None

    def reset(self):
        """Reset all validators and clear exercise selection."""
        for v in self._validators.values():
            v.reset()
        self.current_exercise = None

    def start_rep(self):
        """Mark the current exercise validator as in-progress."""
        if self.current_exercise:
            self._validators[self.current_exercise].start_rep()

    def update(self, exercise_type: str, landmarks):
        """
        Update the appropriate validator with current frame landmarks.

        Resets state if the exercise type changes.

        Args:
            exercise_type: 'squat', 'pushup', or 'curl'
            landmarks: MediaPipe pose landmarks
        """
        if landmarks is None:
            return

        if exercise_type != self.current_exercise:
            if self.current_exercise:
                self._validators[self.current_exercise].reset()
            self.current_exercise = exercise_type

        self._validators[exercise_type].update(landmarks)

    def validate_rep(self, exercise_type: str) -> bool:
        """
        Validate that the rep was performed correctly.

        Args:
            exercise_type: 'squat', 'pushup', or 'curl'

        Returns:
            True if rep is valid, False if it appears to be cheating
        """
        return self._validators[exercise_type].validate_rep()

    def get_validator(self, exercise_type: str):
        """Get the underlying validator instance for direct access."""
        return self._validators.get(exercise_type)

    def get_trends(self, exercise_type: str, metric_key: str, last_n: int = 5) -> dict:
        """
        Get trend data for a specific metric from the exercise's history.

        Args:
            exercise_type: 'squat', 'pushup', or 'curl'
            metric_key: e.g. 'hip_drop', 'shoulder_drop', 'wrist_rise', 'worst_back_angle'
            last_n: number of recent reps to analyze

        Returns:
            dict with 'avg', 'min', 'max', 'count' keys
        """
        validator = self._validators.get(exercise_type)
        if validator is None:
            return {'avg': None, 'min': None, 'max': None, 'count': 0}
        return validator.history.get_trend(metric_key, last_n)

    def get_validation_info(self) -> dict:
        """Get current validation tracking info (for debugging/display)."""
        if self.current_exercise is None:
            return {'exercise': None, 'validator': None}

        v = self._validators[self.current_exercise]
        return {
            'exercise': self.current_exercise,
            'validator': v,
            'history_count': len(v.history.rep_history),
        }
