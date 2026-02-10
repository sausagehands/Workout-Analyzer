"""
Form quality analysis for each exercise
Returns feedback based on angle measurements
"""
from config.app_constants import SQUAT_THRESHOLDS, PUSHUP_THRESHOLDS, CURL_THRESHOLDS


# ---------------------------------------------------------------------------
# Feedback messages per exercise
# ---------------------------------------------------------------------------
SQUAT_FEEDBACK = {
    'unknown': 'Move into frame',
    'excellent': 'Perfect depth! ✓',
    'good': 'Good! Try deeper',
    'poor': 'Go deeper!',
}

PUSHUP_FEEDBACK = {
    'unknown': 'Move into frame',
    'excellent': 'Perfect form! ✓',
    'good': 'Good! Lower more',
    'poor': 'Go lower!',
}

CURL_FEEDBACK = {
    'unknown': 'Move into frame',
    'excellent': 'Full curl! ✓',
    'good': 'Good! Curl more',
    'poor': 'Curl higher!',
}


# ---------------------------------------------------------------------------
# Core analysis function
# ---------------------------------------------------------------------------
def analyze_form(angle, neutral_threshold, excellent_threshold, good_threshold, feedback):
    """
    Evaluate exercise form quality based on joint angle.

    Args:
        angle: Current joint angle in degrees (or None)
        neutral_threshold: Angle above which the user is in resting position
        excellent_threshold: Angle at or below which form is excellent
        good_threshold: Angle at or below which form is good (above excellent)
        feedback: Dict with keys 'unknown', 'excellent', 'good', 'poor'

    Returns:
        dict with keys:
            - quality: 'excellent', 'good', 'poor', 'neutral', or 'unknown'
            - feedback: string
    """
    if angle is None:
        return {'quality': 'unknown', 'feedback': feedback['unknown']}

    if angle > neutral_threshold:
        return {'quality': 'neutral', 'feedback': ''}

    if angle <= excellent_threshold:
        return {'quality': 'excellent', 'feedback': feedback['excellent']}

    if angle <= good_threshold:
        return {'quality': 'good', 'feedback': feedback['good']}

    return {'quality': 'poor', 'feedback': feedback['poor']}


# ---------------------------------------------------------------------------
# Exercise-specific wrappers (public API)
# ---------------------------------------------------------------------------
def analyze_squat_form(knee_angle):
    """Evaluate squat form quality based on knee angle."""
    return analyze_form(
        knee_angle,
        neutral_threshold=SQUAT_THRESHOLDS['STANDING'],
        excellent_threshold=SQUAT_THRESHOLDS['EXCELLENT'],
        good_threshold=SQUAT_THRESHOLDS['GOOD'],
        feedback=SQUAT_FEEDBACK,
    )


def analyze_pushup_form(elbow_angle):
    """Evaluate pushup form quality based on elbow angle."""
    return analyze_form(
        elbow_angle,
        neutral_threshold=PUSHUP_THRESHOLDS['UP'],
        excellent_threshold=PUSHUP_THRESHOLDS['EXCELLENT'],
        good_threshold=PUSHUP_THRESHOLDS['GOOD'],
        feedback=PUSHUP_FEEDBACK,
    )


def analyze_curl_form(elbow_angle):
    """Evaluate bicep curl form quality based on elbow angle."""
    return analyze_form(
        elbow_angle,
        neutral_threshold=CURL_THRESHOLDS['DOWN'],
        excellent_threshold=CURL_THRESHOLDS['EXCELLENT'],
        good_threshold=CURL_THRESHOLDS['GOOD'],
        feedback=CURL_FEEDBACK,
    )
