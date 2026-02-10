from core_cv2.analysis.angle_math import calculate_angle
from config.app_constants import LANDMARKS, VISIBILITY_THRESHOLD


class BackAlignmentTracker:
    """
    Tracks the worst back alignment angle during an exercise rep.

    Back angle is calculated as: shoulder -> hip -> ankle.
    Straight body ~ 180 deg. Lower = sagging/piking/leaning.

    Uses normalized coordinates (0.0-1.0) from MediaPipe directly.
    Angles are scale-invariant so pixel conversion is unnecessary.

    Usage:
        tracker = BackAlignmentTracker()
        tracker.update(landmarks)  # call every frame
        valid = tracker.is_valid(min_angle)
        tracker.reset()  # reset between reps
    """

    def __init__(self):
        self.worst_angle = None

    def reset(self):
        """Reset the tracker for a new rep."""
        self.worst_angle = None

    def update(self, landmarks):
        """
        Update tracker with current frame landmarks.

        Args:
            landmarks: MediaPipe pose landmarks
        """
        angle = self._get_back_angle(landmarks)
        if angle is None:
            return

        if self.worst_angle is None:
            self.worst_angle = angle
        else:
            self.worst_angle = min(self.worst_angle, angle)

    def is_valid(self, min_angle: float) -> bool:
        """
        Check if the worst back angle meets the minimum threshold.

        Args:
            min_angle: minimum acceptable shoulder -> hip -> ankle angle

        Returns:
            True if angle is acceptable or no data available.
        """
        if self.worst_angle is None:
            return True
        return self.worst_angle >= min_angle

    def _get_back_angle(self, landmarks):
        """
        Calculate back alignment angle: shoulder -> hip -> ankle.

        Tries both sides, averages when both visible, falls back to one.

        Returns:
            Angle in degrees (0-180), or None if landmarks not visible.
        """
        left_angle = self._calc_side_back_angle(
            landmarks, 'LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_ANKLE'
        )
        right_angle = self._calc_side_back_angle(
            landmarks, 'RIGHT_SHOULDER', 'RIGHT_HIP', 'RIGHT_ANKLE'
        )

        if left_angle is not None and right_angle is not None:
            return (left_angle + right_angle) / 2
        elif left_angle is not None:
            return left_angle
        elif right_angle is not None:
            return right_angle
        return None

    def _calc_side_back_angle(self, landmarks, shoulder_name, hip_name, ankle_name):
        """
        Calculate shoulder -> hip -> ankle angle for one side.

        Uses normalized coordinates directly (angles are scale-invariant).

        Returns:
            Angle in degrees or None if any landmark is not visible.
        """
        s_idx = LANDMARKS.get(shoulder_name)
        h_idx = LANDMARKS.get(hip_name)
        a_idx = LANDMARKS.get(ankle_name)

        if s_idx is None or h_idx is None or a_idx is None:
            return None

        if (landmarks[s_idx].visibility < VISIBILITY_THRESHOLD or
                landmarks[h_idx].visibility < VISIBILITY_THRESHOLD or
                landmarks[a_idx].visibility < VISIBILITY_THRESHOLD):
            return None

        shoulder = (landmarks[s_idx].x, landmarks[s_idx].y)
        hip = (landmarks[h_idx].x, landmarks[h_idx].y)
        ankle = (landmarks[a_idx].x, landmarks[a_idx].y)

        return calculate_angle(shoulder, hip, ankle)
