"""Unit tests for FormValidator (thin manager) and individual validators.

Tests anti-cheat validation (normalized movement thresholds) and back alignment
checks (shoulder-hip-ankle angle) for squats, pushups, and curls.

Movement thresholds (normalized, fraction of frame height):
  Squat:  MIN_HIP_DROP       = 0.083
  Pushup: MIN_SHOULDER_DROP  = 0.063
  Curl:   MIN_WRIST_RISE     = 0.042

Back angle thresholds (degrees):
  Pushup: MIN_BACK_ANGLE = 155
  Squat:  MIN_BACK_ANGLE = 135
"""
import pytest

from core_cv.analysis.form_validator import FormValidator
from core_cv.analysis.smoothing import MovingAverage
from core_cv.validation.rep_history import RepHistoryTracker
from config.app_constants import LANDMARKS, VISIBILITY_THRESHOLD


# ---------------------------------------------------------------------------
# Mock landmark helper
# ---------------------------------------------------------------------------
class MockLandmark:
    """Simulates a MediaPipe pose landmark with x, y, visibility."""

    def __init__(self, x, y, visibility=0.9):
        self.x = x
        self.y = y
        self.visibility = visibility


def _make_landmarks(overrides=None):
    """
    Create a list of 33 mock landmarks with default positions.

    Default: all landmarks at (0.5, 0.5) with visibility=0.9.

    Args:
        overrides: dict of {index: (x, y)} or {index: (x, y, visibility)}
    """
    landmarks = [MockLandmark(0.5, 0.5) for _ in range(33)]
    if overrides:
        for idx, values in overrides.items():
            if len(values) == 3:
                landmarks[idx] = MockLandmark(values[0], values[1], values[2])
            else:
                landmarks[idx] = MockLandmark(values[0], values[1])
    return landmarks


# ---------------------------------------------------------------------------
# Constants for test clarity
# ---------------------------------------------------------------------------
# Landmark indices
L_SHOULDER = LANDMARKS['LEFT_SHOULDER']   # 11
R_SHOULDER = LANDMARKS['RIGHT_SHOULDER']  # 12
L_HIP = LANDMARKS['LEFT_HIP']            # 23
R_HIP = LANDMARKS['RIGHT_HIP']           # 24
L_ANKLE = LANDMARKS['LEFT_ANKLE']        # 27
R_ANKLE = LANDMARKS['RIGHT_ANKLE']       # 28
L_WRIST = LANDMARKS['LEFT_WRIST']        # 15
R_WRIST = LANDMARKS['RIGHT_WRIST']       # 16


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def validator():
    """Return a fresh FormValidator (thin manager)."""
    return FormValidator()


# ---------------------------------------------------------------------------
# Helper: build landmarks for back angle tests
# ---------------------------------------------------------------------------
def _straight_back_landmarks():
    """Collinear shoulder-hip-ankle = 180 deg."""
    return _make_landmarks({
        L_SHOULDER: (0.2, 0.4), R_SHOULDER: (0.2, 0.4),
        L_HIP: (0.5, 0.5), R_HIP: (0.5, 0.5),
        L_ANKLE: (0.8, 0.6), R_ANKLE: (0.8, 0.6),
    })


def _sagging_back_landmarks():
    """Hip sags below shoulder-ankle line -> angle ~106 deg."""
    return _make_landmarks({
        L_SHOULDER: (0.2, 0.4), R_SHOULDER: (0.2, 0.4),
        L_HIP: (0.5, 0.7), R_HIP: (0.5, 0.7),
        L_ANKLE: (0.8, 0.4), R_ANKLE: (0.8, 0.4),
    })


def _piking_back_landmarks():
    """Hip rises above shoulder-ankle line -> angle ~106 deg."""
    return _make_landmarks({
        L_SHOULDER: (0.2, 0.6), R_SHOULDER: (0.2, 0.6),
        L_HIP: (0.5, 0.3), R_HIP: (0.5, 0.3),
        L_ANKLE: (0.8, 0.6), R_ANKLE: (0.8, 0.6),
    })


# ===========================================================================
# FormValidator init
# ===========================================================================
class TestInitNominal:
    """Verify FormValidator initializes correctly."""

    def test_current_exercise_none(self, validator):
        assert validator.current_exercise is None

    def test_has_all_validators(self, validator):
        assert 'squat' in validator._validators
        assert 'pushup' in validator._validators
        assert 'curl' in validator._validators

    def test_get_validator_returns_instance(self, validator):
        from core_cv.validation import SquatValidator
        assert isinstance(validator.get_validator('squat'), SquatValidator)


# ===========================================================================
# Back angle (using normalized coords — angles are scale-invariant)
# ===========================================================================
class TestBackAngleNominal:
    """Verify back angle computation with normalized coords."""

    def test_straight_body_returns_180(self, validator):
        """Collinear landmarks -> 180 deg."""
        landmarks = _straight_back_landmarks()
        sv = validator.get_validator('pushup')
        sv.back_tracker.update(landmarks)
        assert sv.back_tracker.worst_angle == pytest.approx(180.0, abs=0.1)

    def test_sagging_returns_low_angle(self, validator):
        """Hip below shoulder-ankle line -> well below 155 deg."""
        sv = validator.get_validator('pushup')
        sv.back_tracker.update(_sagging_back_landmarks())
        assert sv.back_tracker.worst_angle < 120

    def test_piking_returns_low_angle(self, validator):
        sv = validator.get_validator('pushup')
        sv.back_tracker.update(_piking_back_landmarks())
        assert sv.back_tracker.worst_angle < 120

    def test_falls_back_to_left_only(self, validator):
        """Right side invisible -> returns left angle."""
        landmarks = _make_landmarks({
            L_SHOULDER: (0.2, 0.4), R_SHOULDER: (0.2, 0.4, 0.1),
            L_HIP: (0.5, 0.5), R_HIP: (0.5, 0.5, 0.1),
            L_ANKLE: (0.8, 0.6), R_ANKLE: (0.8, 0.6, 0.1),
        })
        sv = validator.get_validator('pushup')
        sv.back_tracker.update(landmarks)
        assert sv.back_tracker.worst_angle == pytest.approx(180.0, abs=0.1)

    def test_returns_none_when_all_invisible(self, validator):
        landmarks = _make_landmarks({
            L_SHOULDER: (0.2, 0.4, 0.1), R_SHOULDER: (0.2, 0.4, 0.1),
            L_HIP: (0.5, 0.5, 0.1), R_HIP: (0.5, 0.5, 0.1),
            L_ANKLE: (0.8, 0.6, 0.1), R_ANKLE: (0.8, 0.6, 0.1),
        })
        sv = validator.get_validator('pushup')
        sv.back_tracker.update(landmarks)
        assert sv.back_tracker.worst_angle is None


# ===========================================================================
# Pushup validation (normalized)
# ===========================================================================
class TestPushupNominal:
    """Pushup: shoulder drop >= 0.063 (normalized) + back angle >= 155 deg."""

    def test_valid_pushup(self, validator):
        """Shoulder drop 0.2 > 0.063 with straight back -> valid."""
        # Up position: shoulders at y=0.3
        up = _make_landmarks({
            L_SHOULDER: (0.2, 0.3), R_SHOULDER: (0.2, 0.3),
            L_HIP: (0.5, 0.4), R_HIP: (0.5, 0.4),
            L_ANKLE: (0.8, 0.5), R_ANKLE: (0.8, 0.5),
        })
        validator.update('pushup', up)

        # Down position: shoulders at y=0.5 (drop = 0.2)
        down = _make_landmarks({
            L_SHOULDER: (0.2, 0.5), R_SHOULDER: (0.2, 0.5),
            L_HIP: (0.5, 0.6), R_HIP: (0.5, 0.6),
            L_ANKLE: (0.8, 0.7), R_ANKLE: (0.8, 0.7),
        })
        validator.update('pushup', down)

        assert validator.validate_rep('pushup') is True

    def test_invalid_no_shoulder_drop(self, validator):
        """Shoulders don't move -> invalid."""
        frame = _straight_back_landmarks()
        validator.update('pushup', frame)
        validator.update('pushup', frame)
        assert validator.validate_rep('pushup') is False

    def test_sagging_back_with_shoulder_drop_invalid(self, validator):
        """Sufficient shoulder drop BUT sagging back -> invalid."""
        up = _make_landmarks({
            L_SHOULDER: (0.2, 0.3), R_SHOULDER: (0.2, 0.3),
            L_HIP: (0.5, 0.4), R_HIP: (0.5, 0.4),
            L_ANKLE: (0.8, 0.5), R_ANKLE: (0.8, 0.5),
        })
        validator.update('pushup', up)

        down = _make_landmarks({
            L_SHOULDER: (0.2, 0.5), R_SHOULDER: (0.2, 0.5),
            L_HIP: (0.5, 0.8), R_HIP: (0.5, 0.8),
            L_ANKLE: (0.8, 0.5), R_ANKLE: (0.8, 0.5),
        })
        validator.update('pushup', down)

        assert validator.validate_rep('pushup') is False

    def test_no_data_passes(self, validator):
        """No update calls -> validate_rep returns True."""
        assert validator.validate_rep('pushup') is True

    def test_no_back_data_passes(self, validator):
        """Back angle landmarks not visible, only shoulder drop check applies."""
        up = _make_landmarks({
            L_SHOULDER: (0.3, 0.3), R_SHOULDER: (0.3, 0.3),
            L_HIP: (0.5, 0.5, 0.1), R_HIP: (0.5, 0.5, 0.1),
            L_ANKLE: (0.8, 0.6, 0.1), R_ANKLE: (0.8, 0.6, 0.1),
        })
        validator.update('pushup', up)

        down = _make_landmarks({
            L_SHOULDER: (0.3, 0.5), R_SHOULDER: (0.3, 0.5),
            L_HIP: (0.5, 0.5, 0.1), R_HIP: (0.5, 0.5, 0.1),
            L_ANKLE: (0.8, 0.6, 0.1), R_ANKLE: (0.8, 0.6, 0.1),
        })
        validator.update('pushup', down)

        assert validator.validate_rep('pushup') is True


# ===========================================================================
# Squat validation (normalized)
# ===========================================================================
class TestSquatNominal:
    """Squat: hip drop >= 0.083 (normalized) + back angle >= 135 deg."""

    def test_valid_squat(self, validator):
        """Hip drop 0.2 > 0.083 with upright back -> valid."""
        standing = _make_landmarks({
            L_HIP: (0.5, 0.3), R_HIP: (0.5, 0.3),
            L_SHOULDER: (0.45, 0.1), R_SHOULDER: (0.45, 0.1),
            L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
        })
        validator.update('squat', standing)

        squatting = _make_landmarks({
            L_HIP: (0.5, 0.6), R_HIP: (0.5, 0.6),
            L_SHOULDER: (0.45, 0.3), R_SHOULDER: (0.45, 0.3),
            L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
        })
        validator.update('squat', squatting)

        # Hip drop = 0.6 - 0.3 = 0.3 (smoothed will be close) > 0.083
        assert validator.validate_rep('squat') is True

    def test_invalid_no_hip_drop(self, validator):
        """Hip stays at same height -> invalid."""
        frame = _make_landmarks({
            L_HIP: (0.5, 0.5), R_HIP: (0.5, 0.5),
            L_SHOULDER: (0.45, 0.3), R_SHOULDER: (0.45, 0.3),
            L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
        })
        validator.update('squat', frame)
        validator.update('squat', frame)

        assert validator.validate_rep('squat') is False

    def test_excessive_forward_lean_invalid(self, validator):
        """Hip drops BUT torso collapses forward -> invalid."""
        standing = _make_landmarks({
            L_SHOULDER: (0.4, 0.2), R_SHOULDER: (0.4, 0.2),
            L_HIP: (0.45, 0.5), R_HIP: (0.45, 0.5),
            L_ANKLE: (0.45, 0.85), R_ANKLE: (0.45, 0.85),
        })
        validator.update('squat', standing)

        # Shoulder far forward of hip -> back angle ~127 deg (< 135 threshold)
        leaning = _make_landmarks({
            L_SHOULDER: (0.1, 0.4), R_SHOULDER: (0.1, 0.4),
            L_HIP: (0.5, 0.7), R_HIP: (0.5, 0.7),
            L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
        })
        validator.update('squat', leaning)

        assert validator.validate_rep('squat') is False

    def test_no_back_data_passes(self, validator):
        """If back angle not available, only hip drop check applies."""
        standing = _make_landmarks({
            L_HIP: (0.5, 0.3), R_HIP: (0.5, 0.3),
            L_SHOULDER: (0.4, 0.2, 0.1), R_SHOULDER: (0.4, 0.2, 0.1),
            L_ANKLE: (0.5, 0.8, 0.1), R_ANKLE: (0.5, 0.8, 0.1),
        })
        validator.update('squat', standing)

        squatting = _make_landmarks({
            L_HIP: (0.5, 0.6), R_HIP: (0.5, 0.6),
            L_SHOULDER: (0.4, 0.3, 0.1), R_SHOULDER: (0.4, 0.3, 0.1),
            L_ANKLE: (0.5, 0.8, 0.1), R_ANKLE: (0.5, 0.8, 0.1),
        })
        validator.update('squat', squatting)

        assert validator.validate_rep('squat') is True


# ===========================================================================
# Curl validation (normalized)
# ===========================================================================
class TestCurlNominal:
    """Curl: wrist rise >= 0.042 (normalized)."""

    def test_valid_wrist_rise(self, validator):
        """Wrist rise 0.2 > 0.042 -> valid."""
        down = _make_landmarks({
            L_WRIST: (0.3, 0.7), R_WRIST: (0.3, 0.7),
        })
        validator.update('curl', down)

        up = _make_landmarks({
            L_WRIST: (0.3, 0.5), R_WRIST: (0.3, 0.5),
        })
        validator.update('curl', up)

        assert validator.validate_rep('curl') is True

    def test_invalid_no_wrist_rise(self, validator):
        """Wrist stays at same height -> invalid."""
        frame = _make_landmarks({
            L_WRIST: (0.3, 0.5), R_WRIST: (0.3, 0.5),
        })
        validator.update('curl', frame)
        validator.update('curl', frame)

        assert validator.validate_rep('curl') is False

    def test_back_angle_does_not_affect_curl(self, validator):
        """Curl has no back angle check; bad back doesn't matter."""
        frame = _sagging_back_landmarks()
        frame[L_WRIST] = MockLandmark(0.5, 0.8)
        frame[R_WRIST] = MockLandmark(0.5, 0.8)
        validator.update('curl', frame)

        frame2 = _sagging_back_landmarks()
        frame2[L_WRIST] = MockLandmark(0.5, 0.6)
        frame2[R_WRIST] = MockLandmark(0.5, 0.6)
        validator.update('curl', frame2)

        # Wrist rise = 0.8 - 0.6 = 0.2 (smoothed) > 0.042
        assert validator.validate_rep('curl') is True


# ===========================================================================
# Cheat detection (fake reps)
# ===========================================================================
class TestCheatDetection:
    """Simulate cheating scenarios that should be rejected."""

    def test_squat_leg_lift_without_hip_drop(self, validator):
        """Lifting leg at squat angle without lowering body -> invalid."""
        # Tiny hip movement (< 0.083 threshold)
        frame1 = _make_landmarks({
            L_HIP: (0.5, 0.5), R_HIP: (0.5, 0.5),
            L_SHOULDER: (0.45, 0.3), R_SHOULDER: (0.45, 0.3),
            L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
        })
        validator.update('squat', frame1)

        frame2 = _make_landmarks({
            L_HIP: (0.5, 0.52), R_HIP: (0.5, 0.52),  # only 0.02 drop
            L_SHOULDER: (0.45, 0.3), R_SHOULDER: (0.45, 0.3),
            L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
        })
        validator.update('squat', frame2)

        assert validator.validate_rep('squat') is False

    def test_pushup_arm_bend_without_lowering(self, validator):
        """Bending arms without actually lowering torso -> invalid."""
        frame = _make_landmarks({
            L_SHOULDER: (0.3, 0.4), R_SHOULDER: (0.3, 0.4),
            L_HIP: (0.5, 0.5), R_HIP: (0.5, 0.5),
            L_ANKLE: (0.8, 0.6), R_ANKLE: (0.8, 0.6),
        })
        validator.update('pushup', frame)

        # Shoulder barely moves (0.01 drop < 0.063 threshold)
        frame2 = _make_landmarks({
            L_SHOULDER: (0.3, 0.41), R_SHOULDER: (0.3, 0.41),
            L_HIP: (0.5, 0.5), R_HIP: (0.5, 0.5),
            L_ANKLE: (0.8, 0.6), R_ANKLE: (0.8, 0.6),
        })
        validator.update('pushup', frame2)

        assert validator.validate_rep('pushup') is False

    def test_curl_minimal_wrist_movement(self, validator):
        """Wrist barely moves (< 0.042) -> invalid."""
        frame = _make_landmarks({
            L_WRIST: (0.3, 0.6), R_WRIST: (0.3, 0.6),
        })
        validator.update('curl', frame)

        frame2 = _make_landmarks({
            L_WRIST: (0.3, 0.58), R_WRIST: (0.3, 0.58),  # only 0.02 rise
        })
        validator.update('curl', frame2)

        assert validator.validate_rep('curl') is False


# ===========================================================================
# Exercise switching
# ===========================================================================
class TestExerciseSwitching:
    """Verify exercise changes reset state."""

    def test_switching_exercise_resets(self, validator):
        validator.update('pushup', _straight_back_landmarks())
        assert validator.current_exercise == 'pushup'

        validator.update('squat', _straight_back_landmarks())
        assert validator.current_exercise == 'squat'

    def test_none_landmarks_does_not_update(self, validator):
        validator.update('pushup', _straight_back_landmarks())
        validator.update('pushup', None)
        # Should not crash; current_exercise unchanged
        assert validator.current_exercise == 'pushup'


# ===========================================================================
# Reset
# ===========================================================================
class TestResetNominal:

    def test_reset_clears_exercise(self, validator):
        validator.update('pushup', _straight_back_landmarks())
        validator.reset()
        assert validator.current_exercise is None

    def test_reset_clears_validator_state(self, validator):
        validator.update('squat', _straight_back_landmarks())
        validator.reset()
        sv = validator.get_validator('squat')
        assert sv.baseline_hip_y is None
        assert sv.peak_hip_y is None


# ===========================================================================
# MovingAverage tests
# ===========================================================================
class TestMovingAverage:

    def test_single_value(self):
        ma = MovingAverage(3)
        assert ma.update(10.0) == 10.0

    def test_averages_over_window(self):
        ma = MovingAverage(3)
        ma.update(1.0)
        ma.update(2.0)
        result = ma.update(3.0)
        assert result == pytest.approx(2.0)

    def test_sliding_window(self):
        ma = MovingAverage(3)
        ma.update(1.0)
        ma.update(2.0)
        ma.update(3.0)
        result = ma.update(6.0)  # window: [2, 3, 6]
        assert result == pytest.approx(3.667, abs=0.01)

    def test_reset_clears(self):
        ma = MovingAverage(3)
        ma.update(100.0)
        ma.update(200.0)
        ma.reset()
        assert ma.update(5.0) == 5.0

    def test_smooths_jitter(self):
        """Jittery input produces stable output."""
        ma = MovingAverage(3)
        # Jittery values around 0.5
        results = []
        for v in [0.48, 0.52, 0.49, 0.51, 0.50]:
            results.append(ma.update(v))
        # Last value should be close to 0.5
        assert results[-1] == pytest.approx(0.5, abs=0.01)


# ===========================================================================
# RepHistoryTracker tests
# ===========================================================================
class TestRepHistoryTracker:

    def test_record_and_get_trend(self):
        h = RepHistoryTracker()
        h.record({'hip_drop': 0.10})
        h.record({'hip_drop': 0.12})
        h.record({'hip_drop': 0.08})

        trend = h.get_trend('hip_drop', last_n=3)
        assert trend['count'] == 3
        assert trend['avg'] == pytest.approx(0.10, abs=0.001)
        assert trend['min'] == pytest.approx(0.08)
        assert trend['max'] == pytest.approx(0.12)

    def test_get_average(self):
        h = RepHistoryTracker()
        h.record({'wrist_rise': 0.05})
        h.record({'wrist_rise': 0.07})
        assert h.get_average('wrist_rise') == pytest.approx(0.06)

    def test_get_average_last_n(self):
        h = RepHistoryTracker()
        h.record({'v': 0.1})
        h.record({'v': 0.2})
        h.record({'v': 0.3})
        assert h.get_average('v', last_n=2) == pytest.approx(0.25)

    def test_is_degrading(self):
        h = RepHistoryTracker()
        h.record({'hip_drop': 0.09})
        h.record({'hip_drop': 0.07})
        h.record({'hip_drop': 0.06})
        # Average of last 3 = 0.073 which is below 0.083
        assert h.is_degrading('hip_drop', threshold=0.083, last_n=3) is True

    def test_is_not_degrading(self):
        h = RepHistoryTracker()
        h.record({'hip_drop': 0.12})
        h.record({'hip_drop': 0.11})
        h.record({'hip_drop': 0.10})
        assert h.is_degrading('hip_drop', threshold=0.083, last_n=3) is False

    def test_max_history_cap(self):
        h = RepHistoryTracker()
        for i in range(60):
            h.record({'v': float(i)})
        assert len(h.rep_history) == 50
        # Oldest entries removed
        assert h.rep_history[0]['v'] == 10.0

    def test_empty_returns_none(self):
        h = RepHistoryTracker()
        assert h.get_average('missing') is None
        trend = h.get_trend('missing')
        assert trend['count'] == 0
        assert trend['avg'] is None

    def test_reset(self):
        h = RepHistoryTracker()
        h.record({'v': 1.0})
        h.reset()
        assert len(h.rep_history) == 0


# ===========================================================================
# Integration: history recorded after validate_rep
# ===========================================================================
class TestHistoryIntegration:

    def test_squat_records_history(self, validator):
        """After a valid squat rep, history should contain hip_drop."""
        standing = _make_landmarks({
            L_HIP: (0.5, 0.3), R_HIP: (0.5, 0.3),
            L_SHOULDER: (0.45, 0.1), R_SHOULDER: (0.45, 0.1),
            L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
        })
        validator.update('squat', standing)

        squatting = _make_landmarks({
            L_HIP: (0.5, 0.6), R_HIP: (0.5, 0.6),
            L_SHOULDER: (0.45, 0.3), R_SHOULDER: (0.45, 0.3),
            L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
        })
        validator.update('squat', squatting)
        validator.validate_rep('squat')

        sv = validator.get_validator('squat')
        assert len(sv.history.rep_history) == 1
        assert 'hip_drop' in sv.history.rep_history[0]
        assert sv.history.rep_history[0]['hip_drop'] > 0

    def test_pushup_records_history(self, validator):
        up = _make_landmarks({
            L_SHOULDER: (0.2, 0.3), R_SHOULDER: (0.2, 0.3),
            L_HIP: (0.5, 0.4), R_HIP: (0.5, 0.4),
            L_ANKLE: (0.8, 0.5), R_ANKLE: (0.8, 0.5),
        })
        validator.update('pushup', up)

        down = _make_landmarks({
            L_SHOULDER: (0.2, 0.5), R_SHOULDER: (0.2, 0.5),
            L_HIP: (0.5, 0.6), R_HIP: (0.5, 0.6),
            L_ANKLE: (0.8, 0.7), R_ANKLE: (0.8, 0.7),
        })
        validator.update('pushup', down)
        validator.validate_rep('pushup')

        pv = validator.get_validator('pushup')
        assert len(pv.history.rep_history) == 1
        assert 'shoulder_drop' in pv.history.rep_history[0]

    def test_curl_records_history(self, validator):
        down = _make_landmarks({
            L_WRIST: (0.3, 0.7), R_WRIST: (0.3, 0.7),
        })
        validator.update('curl', down)

        up = _make_landmarks({
            L_WRIST: (0.3, 0.5), R_WRIST: (0.3, 0.5),
        })
        validator.update('curl', up)
        validator.validate_rep('curl')

        cv = validator.get_validator('curl')
        assert len(cv.history.rep_history) == 1
        assert 'wrist_rise' in cv.history.rep_history[0]

    def test_get_trends_via_manager(self, validator):
        """FormValidator.get_trends() delegates to history."""
        for _ in range(3):
            validator.update('squat', _make_landmarks({
                L_HIP: (0.5, 0.3), R_HIP: (0.5, 0.3),
                L_SHOULDER: (0.45, 0.1), R_SHOULDER: (0.45, 0.1),
                L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
            }))
            validator.update('squat', _make_landmarks({
                L_HIP: (0.5, 0.6), R_HIP: (0.5, 0.6),
                L_SHOULDER: (0.45, 0.3), R_SHOULDER: (0.45, 0.3),
                L_ANKLE: (0.5, 0.85), R_ANKLE: (0.5, 0.85),
            }))
            validator.validate_rep('squat')

        trend = validator.get_trends('squat', 'hip_drop', last_n=3)
        assert trend['count'] == 3
        assert trend['avg'] > 0
