from core_cv.analysis.landmark_utils import get_avg_landmark_y
from core_cv.analysis.smoothing import MovingAverage
from config.app_constants import SQUAT_THRESHOLDS
from .back_alignment import BackAlignmentTracker
from .rep_history import RepHistoryTracker


class SquatValidator:
    """
    Tracks squat rep and validates form using normalized coordinates.

    Criteria:
        - Hip must drop at least SQUAT_THRESHOLDS["MIN_HIP_DROP"] (fraction of frame)
        - Back must stay within SQUAT_THRESHOLDS["MIN_BACK_ANGLE"]
    """

    def __init__(self):
        self.baseline_hip_y = None
        self.peak_hip_y = None
        self.back_tracker = BackAlignmentTracker()
        self.rep_in_progress = False
        self._hip_smoother = MovingAverage(3)
        self.history = RepHistoryTracker()

    def reset(self):
        """Reset all tracking state for new exercise/set."""
        self.baseline_hip_y = None
        self.peak_hip_y = None
        self.back_tracker.reset()
        self.rep_in_progress = False
        self._hip_smoother.reset()

    def start_rep(self):
        """Call when a rep starts."""
        self.rep_in_progress = True
        self.peak_hip_y = None
        self.back_tracker.reset()

    def update(self, landmarks):
        """
        Update tracker with current frame landmarks.

        Args:
            landmarks: MediaPipe pose landmarks
        """
        if landmarks is None:
            return

        hip_y = get_avg_landmark_y(landmarks, 'LEFT_HIP', 'RIGHT_HIP')
        if hip_y is not None:
            hip_y = self._hip_smoother.update(hip_y)

            if self.baseline_hip_y is None:
                self.baseline_hip_y = hip_y
            else:
                self.baseline_hip_y = min(self.baseline_hip_y, hip_y)

            if self.peak_hip_y is None:
                self.peak_hip_y = hip_y
            else:
                self.peak_hip_y = max(self.peak_hip_y, hip_y)

        self.back_tracker.update(landmarks)

    def validate_rep(self) -> bool:
        """
        Check if squat rep meets thresholds.

        Returns:
            True if valid, False if form looks like cheating
        """
        if self.baseline_hip_y is None or self.peak_hip_y is None:
            return True

        hip_drop = self.peak_hip_y - self.baseline_hip_y
        hip_valid = hip_drop >= SQUAT_THRESHOLDS["MIN_HIP_DROP"]
        back_valid = self.back_tracker.is_valid(SQUAT_THRESHOLDS["MIN_BACK_ANGLE"])

        self.history.record({
            'hip_drop': hip_drop,
            'worst_back_angle': self.back_tracker.worst_angle,
        })

        self.peak_hip_y = None
        self.back_tracker.reset()
        self.rep_in_progress = False

        return hip_valid and back_valid
