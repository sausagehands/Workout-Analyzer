from core_cv.analysis.landmark_utils import get_avg_landmark_y
from core_cv.analysis.smoothing import MovingAverage
from config.app_constants import CURL_THRESHOLDS
from .rep_history import RepHistoryTracker


class CurlValidator:
    """
    Tracks curl rep and validates form using normalized coordinates.

    Criteria:
        - Wrist must rise at least CURL_THRESHOLDS["MIN_WRIST_RISE"] (fraction of frame)
        - Less strict than pushup/squat; mainly ensures arm movement
    """

    def __init__(self):
        self.baseline_wrist_y = None
        self.peak_wrist_y = None
        self.rep_in_progress = False
        self._wrist_smoother = MovingAverage(3)
        self.history = RepHistoryTracker()

    def reset(self):
        """Reset all tracking state for new exercise/set."""
        self.baseline_wrist_y = None
        self.peak_wrist_y = None
        self.rep_in_progress = False
        self._wrist_smoother.reset()

    def start_rep(self):
        """Call when a rep starts."""
        self.rep_in_progress = True
        self.peak_wrist_y = None

    def update(self, landmarks):
        """
        Update tracker with current frame.

        Args:
            landmarks: MediaPipe pose landmarks
        """
        if landmarks is None:
            return

        wrist_y = get_avg_landmark_y(landmarks, 'LEFT_WRIST', 'RIGHT_WRIST')
        if wrist_y is None:
            return

        wrist_y = self._wrist_smoother.update(wrist_y)

        if self.baseline_wrist_y is None:
            self.baseline_wrist_y = wrist_y
        else:
            self.baseline_wrist_y = max(self.baseline_wrist_y, wrist_y)

        if self.peak_wrist_y is None:
            self.peak_wrist_y = wrist_y
        else:
            self.peak_wrist_y = min(self.peak_wrist_y, wrist_y)

    def validate_rep(self) -> bool:
        """
        Check if curl rep meets threshold.

        Returns:
            True if wrist rose enough, False if not
        """
        if self.baseline_wrist_y is None or self.peak_wrist_y is None:
            return True

        wrist_rise = self.baseline_wrist_y - self.peak_wrist_y
        valid = wrist_rise >= CURL_THRESHOLDS["MIN_WRIST_RISE"]

        self.history.record({
            'wrist_rise': wrist_rise,
        })

        self.peak_wrist_y = None
        self.rep_in_progress = False

        return valid
