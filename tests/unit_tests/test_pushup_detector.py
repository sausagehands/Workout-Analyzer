"""Unit tests for PushupDetector module.

Tests the pushup state machine: state transitions, rep counting,
cooldown behavior, hysteresis, and reset. Uses real thresholds
from app_constants (UP=155, DOWN=110, COOLDOWN=20).

Arranged in nominal and edge cases.
"""
import pytest

from core_cv2.exercises.pushup_detector import PushupDetector, PushupState
from config.app_constants import PUSHUP_THRESHOLDS


# ---------------------------------------------------------------------------
# Constants – readable aliases for test clarity
# ---------------------------------------------------------------------------
UP_ANGLE = 170              # well above 155
DOWN_ANGLE = 85             # well below 110
HYSTERESIS_ANGLE = 130      # between 110 and 155
THRESHOLD_UP = PUSHUP_THRESHOLDS['UP']                # 155
THRESHOLD_DOWN = PUSHUP_THRESHOLDS['DOWN']             # 110
COOLDOWN = PUSHUP_THRESHOLDS['COOLDOWN_FRAMES']        # 20


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def detector():
    """Return a fresh PushupDetector."""
    return PushupDetector()


def _drain_cooldown(detector):
    """Feed enough up frames to exhaust the cooldown timer."""
    for _ in range(COOLDOWN + 1):
        detector.update(UP_ANGLE)


def _complete_one_rep(detector):
    """Drive the detector through one full down → up cycle."""
    detector.update(DOWN_ANGLE)   # enter DOWN
    detector.update(UP_ANGLE)     # transition → UP = rep


# ---------------------------------------------------------------------------
# __init__ – nominal cases
# ---------------------------------------------------------------------------
class TestInitNominal:
    """Verify PushupDetector initializes correctly."""

    def test_name_is_pushup(self, detector):
        assert detector.name == "pushup"

    def test_rep_count_starts_zero(self, detector):
        assert detector.rep_count == 0

    def test_initial_state_is_unknown(self, detector):
        assert detector.current_state == PushupState.UNKNOWN

    def test_up_threshold_from_config(self, detector):
        assert detector.UP_THRESHOLD == THRESHOLD_UP

    def test_down_threshold_from_config(self, detector):
        assert detector.DOWN_THRESHOLD == THRESHOLD_DOWN

    def test_cooldown_period_from_config(self, detector):
        assert detector.COOLDOWN_PERIOD == COOLDOWN


# ---------------------------------------------------------------------------
# State transitions – nominal cases
# ---------------------------------------------------------------------------
class TestStateTransitionsNominal:
    """Verify angle → state mapping."""

    def test_high_angle_sets_up(self, detector):
        detector.update(UP_ANGLE)

        assert detector.current_state == PushupState.UP

    def test_low_angle_sets_down(self, detector):
        detector.update(DOWN_ANGLE)

        assert detector.current_state == PushupState.DOWN

    def test_up_to_down(self, detector):
        detector.update(UP_ANGLE)
        detector.update(DOWN_ANGLE)

        assert detector.current_state == PushupState.DOWN

    def test_down_to_up(self, detector):
        detector.update(DOWN_ANGLE)
        detector.update(UP_ANGLE)

        assert detector.current_state == PushupState.UP


# ---------------------------------------------------------------------------
# State transitions – edge cases
# ---------------------------------------------------------------------------
class TestStateTransitionsEdge:
    """Edge cases for state transitions."""

    def test_exactly_at_up_threshold_stays_current(self, detector):
        """Angle == 155 is NOT > 155, so hysteresis kicks in."""
        detector.update(UP_ANGLE)  # set to UP first
        detector.update(THRESHOLD_UP)

        assert detector.current_state == PushupState.UP

    def test_exactly_at_down_threshold_stays_current(self, detector):
        """Angle == 110 is NOT < 110, so hysteresis kicks in."""
        detector.update(DOWN_ANGLE)  # set to DOWN first
        detector.update(THRESHOLD_DOWN)

        assert detector.current_state == PushupState.DOWN

    def test_one_above_up_threshold_is_up(self, detector):
        detector.update(THRESHOLD_UP + 1)

        assert detector.current_state == PushupState.UP

    def test_one_below_down_threshold_is_down(self, detector):
        detector.update(THRESHOLD_DOWN - 1)

        assert detector.current_state == PushupState.DOWN

    def test_none_angle_does_not_change_state(self, detector):
        detector.update(UP_ANGLE)

        detector.update(None)

        assert detector.current_state == PushupState.UP

    def test_none_angle_from_unknown_stays_unknown(self, detector):
        detector.update(None)

        assert detector.current_state == PushupState.UNKNOWN


# ---------------------------------------------------------------------------
# Hysteresis – nominal cases
# ---------------------------------------------------------------------------
class TestHysteresisNominal:
    """Angles in the dead zone keep the current state."""

    def test_hysteresis_preserves_up(self, detector):
        detector.update(UP_ANGLE)
        detector.update(HYSTERESIS_ANGLE)

        assert detector.current_state == PushupState.UP

    def test_hysteresis_preserves_down(self, detector):
        detector.update(DOWN_ANGLE)
        detector.update(HYSTERESIS_ANGLE)

        assert detector.current_state == PushupState.DOWN

    def test_multiple_hysteresis_frames_no_state_change(self, detector):
        detector.update(UP_ANGLE)

        for _ in range(10):
            detector.update(HYSTERESIS_ANGLE)

        assert detector.current_state == PushupState.UP


# ---------------------------------------------------------------------------
# Rep counting – nominal cases
# ---------------------------------------------------------------------------
class TestRepCountingNominal:
    """Verify reps are counted on DOWN → UP transitions."""

    def test_one_rep(self, detector):
        _complete_one_rep(detector)

        assert detector.rep_count == 1

    def test_update_returns_true_on_rep(self, detector):
        detector.update(DOWN_ANGLE)
        result = detector.update(UP_ANGLE)

        assert result is True

    def test_update_returns_false_when_no_rep(self, detector):
        result = detector.update(UP_ANGLE)

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

    def test_full_pushup_motion_sequence(self, detector):
        """Simulate realistic angle sequence: up → down → up."""
        angles = [170, 165, 140, 110, 85, 80, 85, 110, 140, 165, 170]
        reps = sum(detector.update(a) for a in angles)

        assert reps == 1
        assert detector.rep_count == 1


# ---------------------------------------------------------------------------
# Rep counting – edge cases
# ---------------------------------------------------------------------------
class TestRepCountingEdge:
    """Edge cases for rep counting."""

    def test_up_to_up_no_rep(self, detector):
        detector.update(UP_ANGLE)
        result = detector.update(UP_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_down_to_down_no_rep(self, detector):
        detector.update(DOWN_ANGLE)
        result = detector.update(DOWN_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_up_to_down_no_rep(self, detector):
        """Going down is not a rep — only pushing back up counts."""
        detector.update(UP_ANGLE)
        result = detector.update(DOWN_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_unknown_to_up_no_rep(self, detector):
        """First up frame from UNKNOWN is not a rep."""
        result = detector.update(UP_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_none_angle_during_pushup_no_rep(self, detector):
        """None angle mid-pushup doesn't trigger rep."""
        detector.update(DOWN_ANGLE)
        result = detector.update(None)

        assert result is False
        assert detector.rep_count == 0

    def test_hysteresis_does_not_trigger_rep(self, detector):
        """Going from down through hysteresis zone doesn't count."""
        detector.update(DOWN_ANGLE)
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

        detector.update(DOWN_ANGLE)
        result = detector.update(UP_ANGLE)

        assert result is False
        assert detector.rep_count == 1

    def test_rep_allowed_after_cooldown_expires(self, detector):
        _complete_one_rep(detector)
        _drain_cooldown(detector)

        detector.update(DOWN_ANGLE)
        result = detector.update(UP_ANGLE)

        assert result is True
        assert detector.rep_count == 2

    def test_cooldown_decrements_each_update(self, detector):
        _complete_one_rep(detector)

        initial = detector.cooldown_frames
        detector.update(UP_ANGLE)

        assert detector.cooldown_frames == initial - 1

    def test_cooldown_starts_at_period_value(self, detector):
        _complete_one_rep(detector)

        assert detector.cooldown_frames == COOLDOWN


# ---------------------------------------------------------------------------
# Cooldown – edge cases
# ---------------------------------------------------------------------------
class TestCooldownEdge:
    """Edge cases for cooldown behavior."""

    def test_rapid_down_up_during_cooldown_no_rep(self, detector):
        """Multiple down/up cycles during cooldown all blocked."""
        _complete_one_rep(detector)

        for _ in range(3):
            detector.update(DOWN_ANGLE)
            detector.update(UP_ANGLE)

        assert detector.rep_count == 1

    def test_exactly_at_cooldown_expiry(self, detector):
        """Rep should work on the exact frame cooldown hits 0."""
        _complete_one_rep(detector)

        for _ in range(COOLDOWN):
            detector.update(UP_ANGLE)

        assert detector.cooldown_frames == 0

        detector.update(DOWN_ANGLE)
        result = detector.update(UP_ANGLE)

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
        detector.update(UP_ANGLE)

        detector.reset()

        assert detector.current_state == PushupState.UNKNOWN

    def test_reset_preserves_thresholds(self, detector):
        detector.reset()

        assert detector.UP_THRESHOLD == THRESHOLD_UP
        assert detector.DOWN_THRESHOLD == THRESHOLD_DOWN
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

    def test_up(self, detector):
        detector.update(UP_ANGLE)

        assert detector.get_state_name() == "up"

    def test_down(self, detector):
        detector.update(DOWN_ANGLE)

        assert detector.get_state_name() == "down"


# ---------------------------------------------------------------------------
# update_thresholds integration
# ---------------------------------------------------------------------------
class TestUpdateThresholds:
    """Verify base class update_thresholds works with pushup attrs."""

    def test_update_up_threshold(self, detector):
        detector.update_thresholds(UP_THRESHOLD=160)

        assert detector.UP_THRESHOLD == 160

    def test_update_down_threshold(self, detector):
        detector.update_thresholds(DOWN_THRESHOLD=100)

        assert detector.DOWN_THRESHOLD == 100

    def test_updated_threshold_affects_state_machine(self, detector):
        """Lower the up threshold — angle that was hysteresis now triggers UP."""
        detector.update_thresholds(UP_THRESHOLD=120)

        detector.update(DOWN_ANGLE)
        # 130 is now > 120 (new threshold), so this transitions to UP
        result = detector.update(HYSTERESIS_ANGLE)

        assert result is True
        assert detector.rep_count == 1
