from core_cv2.analysis.landmark_utils import get_avg_landmark_y
from core_cv2.analysis.smoothing import MovingAverage
from config.app_constants import PUSHUP_THRESHOLDS
from .back_alignment import BackAlignmentTracker
from .rep_history import RepHistoryTracker


class PushupValidator:
    """
    Tracks pushup rep and validates form using normalized coordinates.

    Criteria:
        - Shoulder must drop at least PUSHUP_THRESHOLDS["MIN_SHOULDER_DROP"] (fraction of frame)
        - Back must stay straight (BackAlignmentTracker)
    """

    def __init__(self):
        self.baseline_shoulder_y = None
        self.peak_shoulder_y = None
        self.back_tracker = BackAlignmentTracker()
        self.rep_in_progress = False
        self._shoulder_smoother = MovingAverage(3)
        self.history = RepHistoryTracker()

    def reset(self):
        """Reset all tracking state for new exercise/set."""
        self.baseline_shoulder_y = None
        self.peak_shoulder_y = None
        self.back_tracker.reset()
        self.rep_in_progress = False
        self._shoulder_smoother.reset()

    def start_rep(self):
        """Call when a rep starts."""
        self.rep_in_progress = True
        self.peak_shoulder_y = None
        self.back_tracker.reset()

    def update(self, landmarks):
        """
        Update tracker with current frame.

        Args:
            landmarks: MediaPipe pose landmarks
        """
        if landmarks is None:
            return

        shoulder_y = get_avg_landmark_y(landmarks, 'LEFT_SHOULDER', 'RIGHT_SHOULDER')
        if shoulder_y is not None:
            shoulder_y = self._shoulder_smoother.update(shoulder_y)

            if self.baseline_shoulder_y is None:
                self.baseline_shoulder_y = shoulder_y
            else:
                self.baseline_shoulder_y = min(self.baseline_shoulder_y, shoulder_y)

            if self.peak_shoulder_y is None:
                self.peak_shoulder_y = shoulder_y
            else:
                self.peak_shoulder_y = max(self.peak_shoulder_y, shoulder_y)

        self.back_tracker.update(landmarks)

    def validate_rep(self) -> bool:
        """
        Check if pushup rep meets thresholds.

        Returns:
            True if valid, False if form looks like cheating
        """
        if self.baseline_shoulder_y is None or self.peak_shoulder_y is None:
            return True

        shoulder_drop = self.peak_shoulder_y - self.baseline_shoulder_y
        shoulder_valid = shoulder_drop >= PUSHUP_THRESHOLDS["MIN_SHOULDER_DROP"]
        back_valid = self.back_tracker.is_valid(PUSHUP_THRESHOLDS["MIN_BACK_ANGLE"])

        self.history.record({
            'shoulder_drop': shoulder_drop,
            'worst_back_angle': self.back_tracker.worst_angle,
        })

        self.peak_shoulder_y = None
        self.back_tracker.reset()
        self.rep_in_progress = False

        return shoulder_valid and back_valid
