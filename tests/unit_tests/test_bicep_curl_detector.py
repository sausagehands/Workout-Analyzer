"""Unit tests for BicepCurlDetector module.

Tests the curl state machine: state transitions, rep counting,
cooldown behavior, hysteresis, and reset. Uses real thresholds
from app_constants (DOWN=155, CURLED=70, COOLDOWN=18).

Arranged in nominal and edge cases.
"""
import pytest

from core_cv.exercises.bicep_curl_detector import BicepCurlDetector, CurlState
from config.app_constants import CURL_THRESHOLDS


# ---------------------------------------------------------------------------
# Constants – readable aliases for test clarity
# ---------------------------------------------------------------------------
DOWN_ANGLE = 170            # well above 155
CURLED_ANGLE = 45           # well below 70
HYSTERESIS_ANGLE = 110      # between 70 and 155
THRESHOLD_DOWN = CURL_THRESHOLDS['DOWN']             # 155
THRESHOLD_CURLED = CURL_THRESHOLDS['CURLED']          # 70
COOLDOWN = CURL_THRESHOLDS['COOLDOWN_FRAMES']         # 18


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def detector():
    """Return a fresh BicepCurlDetector."""
    return BicepCurlDetector()


def _drain_cooldown(detector):
    """Feed enough down frames to exhaust the cooldown timer."""
    for _ in range(COOLDOWN + 1):
        detector.update(DOWN_ANGLE)


def _complete_one_rep(detector):
    """Drive the detector through one full curl → down cycle."""
    detector.update(CURLED_ANGLE)   # enter CURLED
    detector.update(DOWN_ANGLE)     # transition → DOWN = rep


# ---------------------------------------------------------------------------
# __init__ – nominal cases
# ---------------------------------------------------------------------------
class TestInitNominal:
    """Verify BicepCurlDetector initializes correctly."""

    def test_name_is_curl(self, detector):
        assert detector.name == "curl"

    def test_rep_count_starts_zero(self, detector):
        assert detector.rep_count == 0

    def test_initial_state_is_unknown(self, detector):
        assert detector.current_state == CurlState.UNKNOWN

    def test_down_threshold_from_config(self, detector):
        assert detector.DOWN_THRESHOLD == THRESHOLD_DOWN

    def test_curled_threshold_from_config(self, detector):
        assert detector.CURLED_THRESHOLD == THRESHOLD_CURLED

    def test_cooldown_period_from_config(self, detector):
        assert detector.COOLDOWN_PERIOD == COOLDOWN


# ---------------------------------------------------------------------------
# State transitions – nominal cases
# ---------------------------------------------------------------------------
class TestStateTransitionsNominal:
    """Verify angle → state mapping."""

    def test_high_angle_sets_down(self, detector):
        detector.update(DOWN_ANGLE)

        assert detector.current_state == CurlState.DOWN

    def test_low_angle_sets_curled(self, detector):
        detector.update(CURLED_ANGLE)

        assert detector.current_state == CurlState.CURLED

    def test_down_to_curled(self, detector):
        detector.update(DOWN_ANGLE)
        detector.update(CURLED_ANGLE)

        assert detector.current_state == CurlState.CURLED

    def test_curled_to_down(self, detector):
        detector.update(CURLED_ANGLE)
        detector.update(DOWN_ANGLE)

        assert detector.current_state == CurlState.DOWN


# ---------------------------------------------------------------------------
# State transitions – edge cases
# ---------------------------------------------------------------------------
class TestStateTransitionsEdge:
    """Edge cases for state transitions."""

    def test_exactly_at_down_threshold_stays_current(self, detector):
        """Angle == 155 is NOT > 155, so hysteresis kicks in."""
        detector.update(DOWN_ANGLE)  # set to DOWN first
        detector.update(THRESHOLD_DOWN)

        assert detector.current_state == CurlState.DOWN

    def test_exactly_at_curled_threshold_stays_current(self, detector):
        """Angle == 70 is NOT < 70, so hysteresis kicks in."""
        detector.update(CURLED_ANGLE)  # set to CURLED first
        detector.update(THRESHOLD_CURLED)

        assert detector.current_state == CurlState.CURLED

    def test_one_above_down_threshold_is_down(self, detector):
        detector.update(THRESHOLD_DOWN + 1)

        assert detector.current_state == CurlState.DOWN

    def test_one_below_curled_threshold_is_curled(self, detector):
        detector.update(THRESHOLD_CURLED - 1)

        assert detector.current_state == CurlState.CURLED

    def test_none_angle_does_not_change_state(self, detector):
        detector.update(DOWN_ANGLE)

        detector.update(None)

        assert detector.current_state == CurlState.DOWN

    def test_none_angle_from_unknown_stays_unknown(self, detector):
        detector.update(None)

        assert detector.current_state == CurlState.UNKNOWN


# ---------------------------------------------------------------------------
# Hysteresis – nominal cases
# ---------------------------------------------------------------------------
class TestHysteresisNominal:
    """Angles in the dead zone keep the current state."""

    def test_hysteresis_preserves_down(self, detector):
        detector.update(DOWN_ANGLE)
        detector.update(HYSTERESIS_ANGLE)

        assert detector.current_state == CurlState.DOWN

    def test_hysteresis_preserves_curled(self, detector):
        detector.update(CURLED_ANGLE)
        detector.update(HYSTERESIS_ANGLE)

        assert detector.current_state == CurlState.CURLED

    def test_multiple_hysteresis_frames_no_state_change(self, detector):
        detector.update(DOWN_ANGLE)

        for _ in range(10):
            detector.update(HYSTERESIS_ANGLE)

        assert detector.current_state == CurlState.DOWN


# ---------------------------------------------------------------------------
# Rep counting – nominal cases
# ---------------------------------------------------------------------------
class TestRepCountingNominal:
    """Verify reps are counted on CURLED → DOWN transitions."""

    def test_one_rep(self, detector):
        _complete_one_rep(detector)

        assert detector.rep_count == 1

    def test_update_returns_true_on_rep(self, detector):
        detector.update(CURLED_ANGLE)
        result = detector.update(DOWN_ANGLE)

        assert result is True

    def test_update_returns_false_when_no_rep(self, detector):
        result = detector.update(DOWN_ANGLE)

        assert result is False

    def test_two_reps_with_cooldown_drained(self, detector):
        _complete_one_rep(detector)
        _drain_cooldown(detector)

        _complete_one_rep(detector)

        assert detector.rep_count == 2

    def test_multiple_reps(self, detector):
        for _ in range(5):
            _complete_one_rep(detector)
            _drain_cooldown(detector)

        assert detector.rep_count == 5

    def test_full_curl_motion_sequence(self, detector):
        """Simulate realistic angle sequence: down → curled → down."""
        angles = [170, 165, 140, 100, 60, 45, 60, 100, 140, 165, 170]
        reps = sum(detector.update(a) for a in angles)

        assert reps == 1
        assert detector.rep_count == 1


# ---------------------------------------------------------------------------
# Rep counting – edge cases
# ---------------------------------------------------------------------------
class TestRepCountingEdge:
    """Edge cases for rep counting."""

    def test_down_to_down_no_rep(self, detector):
        detector.update(DOWN_ANGLE)
        result = detector.update(DOWN_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_curled_to_curled_no_rep(self, detector):
        detector.update(CURLED_ANGLE)
        result = detector.update(CURLED_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_down_to_curled_no_rep(self, detector):
        """Going up (curling) is not a rep — only extending back counts."""
        detector.update(DOWN_ANGLE)
        result = detector.update(CURLED_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_unknown_to_down_no_rep(self, detector):
        """First down frame from UNKNOWN is not a rep."""
        result = detector.update(DOWN_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_none_angle_during_curl_no_rep(self, detector):
        """None angle mid-curl doesn't trigger rep."""
        detector.update(CURLED_ANGLE)
        result = detector.update(None)

        assert result is False
        assert detector.rep_count == 0

    def test_hysteresis_does_not_trigger_rep(self, detector):
        """Going from curled through hysteresis zone doesn't count."""
        detector.update(CURLED_ANGLE)
        result = detector.update(HYSTERESIS_ANGLE)

        assert result is False
        assert detector.rep_count == 0


# ---------------------------------------------------------------------------
# Cooldown – nominal cases
# ---------------------------------------------------------------------------
class TestCooldownNominal:
    """Verify cooldown prevents double-counting."""

    def test_second_rep_blocked_during_cooldown(self, detector):
        _complete_one_rep(detector)

        detector.update(CURLED_ANGLE)
        result = detector.update(DOWN_ANGLE)

        assert result is False
        assert detector.rep_count == 1

    def test_rep_allowed_after_cooldown_expires(self, detector):
        _complete_one_rep(detector)
        _drain_cooldown(detector)

        detector.update(CURLED_ANGLE)
        result = detector.update(DOWN_ANGLE)

        assert result is True
        assert detector.rep_count == 2

    def test_cooldown_decrements_each_update(self, detector):
        _complete_one_rep(detector)

        initial = detector.cooldown_frames
        detector.update(DOWN_ANGLE)

        assert detector.cooldown_frames == initial - 1

    def test_cooldown_starts_at_period_value(self, detector):
        _complete_one_rep(detector)

        assert detector.cooldown_frames == COOLDOWN


# ---------------------------------------------------------------------------
# Cooldown – edge cases
# ---------------------------------------------------------------------------
class TestCooldownEdge:
    """Edge cases for cooldown behavior."""

    def test_rapid_curl_down_during_cooldown_no_rep(self, detector):
        """Multiple curl/down cycles during cooldown all blocked."""
        _complete_one_rep(detector)

        for _ in range(3):
            detector.update(CURLED_ANGLE)
            detector.update(DOWN_ANGLE)

        assert detector.rep_count == 1

    def test_exactly_at_cooldown_expiry(self, detector):
        """Rep should work on the exact frame cooldown hits 0."""
        _complete_one_rep(detector)

        for _ in range(COOLDOWN):
            detector.update(DOWN_ANGLE)

        assert detector.cooldown_frames == 0

        detector.update(CURLED_ANGLE)
        result = detector.update(DOWN_ANGLE)

        assert result is True
        assert detector.rep_count == 2


# ---------------------------------------------------------------------------
# reset – nominal cases
# ---------------------------------------------------------------------------
class TestResetNominal:
    """Verify reset clears all state."""

    def test_reset_clears_rep_count(self, detector):
        _complete_one_rep(detector)

        detector.reset()

        assert detector.rep_count == 0

    def test_reset_clears_cooldown(self, detector):
        _complete_one_rep(detector)

        detector.reset()

        assert detector.cooldown_frames == 0

    def test_reset_sets_state_to_unknown(self, detector):
        detector.update(DOWN_ANGLE)

        detector.reset()

        assert detector.current_state == CurlState.UNKNOWN

    def test_reset_preserves_thresholds(self, detector):
        detector.reset()

        assert detector.DOWN_THRESHOLD == THRESHOLD_DOWN
        assert detector.CURLED_THRESHOLD == THRESHOLD_CURLED
        assert detector.COOLDOWN_PERIOD == COOLDOWN

    def test_rep_counting_works_after_reset(self, detector):
        _complete_one_rep(detector)
        _drain_cooldown(detector)
        _complete_one_rep(detector)
        assert detector.rep_count == 2

        detector.reset()
        _complete_one_rep(detector)

        assert detector.rep_count == 1


# ---------------------------------------------------------------------------
# get_state_name – nominal cases
# ---------------------------------------------------------------------------
class TestGetStateNameNominal:
    """Verify get_state_name returns the enum value string."""

    def test_unknown(self, detector):
        assert detector.get_state_name() == "unknown"

    def test_down(self, detector):
        detector.update(DOWN_ANGLE)

        assert detector.get_state_name() == "down"

    def test_curled(self, detector):
        detector.update(CURLED_ANGLE)

        assert detector.get_state_name() == "curled"


# ---------------------------------------------------------------------------
# update_thresholds integration
# ---------------------------------------------------------------------------
class TestUpdateThresholds:
    """Verify base class update_thresholds works with curl attrs."""

    def test_update_down_threshold(self, detector):
        detector.update_thresholds(DOWN_THRESHOLD=160)

        assert detector.DOWN_THRESHOLD == 160

    def test_update_curled_threshold(self, detector):
        detector.update_thresholds(CURLED_THRESHOLD=60)

        assert detector.CURLED_THRESHOLD == 60

    def test_updated_threshold_affects_state_machine(self, detector):
        """Lower the down threshold — angle that was hysteresis now triggers DOWN."""
        detector.update_thresholds(DOWN_THRESHOLD=100)

        detector.update(CURLED_ANGLE)
        # 110 is now > 100 (new threshold), so this transitions to DOWN
        result = detector.update(HYSTERESIS_ANGLE)

        assert result is True
        assert detector.rep_count == 1
