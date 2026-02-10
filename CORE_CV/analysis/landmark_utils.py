from config.app_constants import LANDMARKS, VISIBILITY_THRESHOLD


def get_landmark_y(landmarks, landmark_name: str) -> float:
    """Get normalized Y position (0.0-1.0) of a landmark, or None if not visible."""
    idx = LANDMARKS.get(landmark_name)
    if idx is None:
        return None

    landmark = landmarks[idx]
    if landmark.visibility < VISIBILITY_THRESHOLD:
        return None

    return landmark.y


def get_avg_landmark_y(landmarks, left_name: str, right_name: str) -> float:
    """Get average normalized Y of left and right landmarks."""
    left_y = get_landmark_y(landmarks, left_name)
    right_y = get_landmark_y(landmarks, right_name)

    if left_y is not None and right_y is not None:
        return (left_y + right_y) / 2
    elif left_y is not None:
        return left_y
    elif right_y is not None:
        return right_y
    return None
