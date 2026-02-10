"""Unit tests for SquatDetector module.

Tests the squat state machine: state transitions, rep counting,
cooldown behavior, hysteresis, and reset. Uses real thresholds
from app_constants (STANDING=155, SQUATTING=110, COOLDOWN=25).

Arranged in nominal and edge cases.
"""
import pytest

from core_cv.exercises.squat_detector import SquatDetector, SquatState
from config.app_constants import SQUAT_THRESHOLDS


# ---------------------------------------------------------------------------
# Constants – readable aliases for test clarity
# ---------------------------------------------------------------------------
STANDING_ANGLE = 170       # well above 155
SQUATTING_ANGLE = 90       # well below 110
HYSTERESIS_ANGLE = 130     # between 110 and 155
THRESHOLD_STANDING = SQUAT_THRESHOLDS['STANDING']   # 155
THRESHOLD_SQUATTING = SQUAT_THRESHOLDS['SQUATTING']  # 110
COOLDOWN = SQUAT_THRESHOLDS['COOLDOWN_FRAMES']       # 25


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def detector():
    """Return a fresh SquatDetector."""
    return SquatDetector()


def _drain_cooldown(detector):
    """Feed enough standing frames to exhaust the cooldown timer."""
    for _ in range(COOLDOWN + 1):
        detector.update(STANDING_ANGLE)


def _complete_one_rep(detector):
    """Drive the detector through one full squat → stand cycle."""
    detector.update(SQUATTING_ANGLE)   # enter SQUATTING
    detector.update(STANDING_ANGLE)    # transition → STANDING = rep


# ---------------------------------------------------------------------------
# __init__ – nominal cases
# ---------------------------------------------------------------------------
class TestInitNominal:
    """Verify SquatDetector initializes correctly."""

    def test_name_is_squat(self, detector):
        assert detector.name == "squat"

    def test_rep_count_starts_zero(self, detector):
        assert detector.rep_count == 0

    def test_initial_state_is_unknown(self, detector):
        assert detector.current_state == SquatState.UNKNOWN

    def test_standing_threshold_from_config(self, detector):
        assert detector.STANDING_THRESHOLD == THRESHOLD_STANDING

    def test_squatting_threshold_from_config(self, detector):
        assert detector.SQUATTING_THRESHOLD == THRESHOLD_SQUATTING

    def test_cooldown_period_from_config(self, detector):
        assert detector.COOLDOWN_PERIOD == COOLDOWN


# ---------------------------------------------------------------------------
# State transitions – nominal cases
# ---------------------------------------------------------------------------
class TestStateTransitionsNominal:
    """Verify angle → state mapping."""

    def test_high_angle_sets_standing(self, detector):
        detector.update(STANDING_ANGLE)

        assert detector.current_state == SquatState.STANDING

    def test_low_angle_sets_squatting(self, detector):
        detector.update(SQUATTING_ANGLE)

        assert detector.current_state == SquatState.SQUATTING

    def test_standing_to_squatting(self, detector):
        detector.update(STANDING_ANGLE)
        detector.update(SQUATTING_ANGLE)

        assert detector.current_state == SquatState.SQUATTING

    def test_squatting_to_standing(self, detector):
        detector.update(SQUATTING_ANGLE)
        detector.update(STANDING_ANGLE)

        assert detector.current_state == SquatState.STANDING


# ---------------------------------------------------------------------------
# State transitions – edge cases
# ---------------------------------------------------------------------------
class TestStateTransitionsEdge:
    """Edge cases for state transitions."""

    def test_exactly_at_standing_threshold_stays_current(self, detector):
        """Angle == 155 is NOT > 155, so hysteresis kicks in."""
        detector.update(STANDING_ANGLE)  # set to STANDING first
        detector.update(THRESHOLD_STANDING)  # exactly 155

        # 155 is not > 155, so hysteresis keeps STANDING
        assert detector.current_state == SquatState.STANDING

    def test_exactly_at_squatting_threshold_stays_current(self, detector):
        """Angle == 110 is NOT < 110, so hysteresis kicks in."""
        detector.update(SQUATTING_ANGLE)  # set to SQUATTING first
        detector.update(THRESHOLD_SQUATTING)  # exactly 110

        # 110 is not < 110, so hysteresis keeps SQUATTING
        assert detector.current_state == SquatState.SQUATTING

    def test_one_above_standing_threshold_is_standing(self, detector):
        detector.update(THRESHOLD_STANDING + 1)

        assert detector.current_state == SquatState.STANDING

    def test_one_below_squatting_threshold_is_squatting(self, detector):
        detector.update(THRESHOLD_SQUATTING - 1)

        assert detector.current_state == SquatState.SQUATTING

    def test_none_angle_does_not_change_state(self, detector):
        detector.update(STANDING_ANGLE)

        detector.update(None)

        # State stays STANDING (UNKNOWN doesn't overwrite)
        assert detector.current_state == SquatState.STANDING

    def test_none_angle_from_unknown_stays_unknown(self, detector):
        detector.update(None)

        assert detector.current_state == SquatState.UNKNOWN


# ---------------------------------------------------------------------------
# Hysteresis – nominal cases
# ---------------------------------------------------------------------------
class TestHysteresisNominal:
    """Angles in the dead zone keep the current state."""

    def test_hysteresis_preserves_standing(self, detector):
        detector.update(STANDING_ANGLE)
        detector.update(HYSTERESIS_ANGLE)

        assert detector.current_state == SquatState.STANDING

    def test_hysteresis_preserves_squatting(self, detector):
        detector.update(SQUATTING_ANGLE)
        detector.update(HYSTERESIS_ANGLE)

        assert detector.current_state == SquatState.SQUATTING

    def test_multiple_hysteresis_frames_no_state_change(self, detector):
        detector.update(STANDING_ANGLE)

        for _ in range(10):
            detector.update(HYSTERESIS_ANGLE)

        assert detector.current_state == SquatState.STANDING


# ---------------------------------------------------------------------------
# Rep counting – nominal cases
# ---------------------------------------------------------------------------
class TestRepCountingNominal:
    """Verify reps are counted on SQUATTING → STANDING transitions."""

    def test_one_rep(self, detector):
        _complete_one_rep(detector)

        assert detector.rep_count == 1

    def test_update_returns_true_on_rep(self, detector):
        detector.update(SQUATTING_ANGLE)
        result = detector.update(STANDING_ANGLE)

        assert result is True

    def test_update_returns_false_when_no_rep(self, detector):
        result = detector.update(STANDING_ANGLE)

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

    def test_full_squat_motion_sequence(self, detector):
        """Simulate realistic angle sequence: stand → squat → stand."""
        angles = [175, 170, 150, 120, 90, 85, 90, 120, 150, 170, 175]
        reps = sum(detector.update(a) for a in angles)

        assert reps == 1
        assert detector.rep_count == 1


# ---------------------------------------------------------------------------
# Rep counting – edge cases
# ---------------------------------------------------------------------------
class TestRepCountingEdge:
    """Edge cases for rep counting."""

    def test_standing_to_standing_no_rep(self, detector):
        detector.update(STANDING_ANGLE)
        result = detector.update(STANDING_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_squatting_to_squatting_no_rep(self, detector):
        detector.update(SQUATTING_ANGLE)
        result = detector.update(SQUATTING_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_standing_to_squatting_no_rep(self, detector):
        """Going down is not a rep — only coming back up counts."""
        detector.update(STANDING_ANGLE)
        result = detector.update(SQUATTING_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_unknown_to_standing_no_rep(self, detector):
        """First standing frame from UNKNOWN is not a rep."""
        result = detector.update(STANDING_ANGLE)

        assert result is False
        assert detector.rep_count == 0

    def test_none_angle_during_squat_no_rep(self, detector):
        """None angle mid-squat doesn't trigger rep."""
        detector.update(SQUATTING_ANGLE)
        result = detector.update(None)

        assert result is False
        assert detector.rep_count == 0

    def test_hysteresis_does_not_trigger_rep(self, detector):
        """Going from squatting through hysteresis zone doesn't count."""
        detector.update(SQUATTING_ANGLE)
        # Stay in hysteresis — state stays SQUATTING
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

        # Immediately try another rep — should be blocked
        detector.update(SQUATTING_ANGLE)
        result = detector.update(STANDING_ANGLE)

        assert result is False
        assert detector.rep_count == 1

    def test_rep_allowed_after_cooldown_expires(self, detector):
        _complete_one_rep(detector)
        _drain_cooldown(detector)

        detector.update(SQUATTING_ANGLE)
        result = detector.update(STANDING_ANGLE)

        assert result is True
        assert detector.rep_count == 2

    def test_cooldown_decrements_each_update(self, detector):
        _complete_one_rep(detector)

        initial = detector.cooldown_frames
        detector.update(STANDING_ANGLE)

        assert detector.cooldown_frames == initial - 1

    def test_cooldown_starts_at_period_value(self, detector):
        _complete_one_rep(detector)

        assert detector.cooldown_frames == COOLDOWN


# ---------------------------------------------------------------------------
# Cooldown – edge cases
# ---------------------------------------------------------------------------
class TestCooldownEdge:
    """Edge cases for cooldown behavior."""

    def test_rapid_squat_stand_during_cooldown_no_rep(self, detector):
        """Multiple squat/stand cycles during cooldown all blocked."""
        _complete_one_rep(detector)

        for _ in range(3):
            detector.update(SQUATTING_ANGLE)
            detector.update(STANDING_ANGLE)

        assert detector.rep_count == 1

    def test_exactly_at_cooldown_expiry(self, detector):
        """Rep should work on the exact frame cooldown hits 0."""
        _complete_one_rep(detector)

        # Drain cooldown with standing frames (COOLDOWN updates)
        for _ in range(COOLDOWN):
            detector.update(STANDING_ANGLE)

        assert detector.cooldown_frames == 0

        # Now a rep should count
        detector.update(SQUATTING_ANGLE)
        result = detector.update(STANDING_ANGLE)

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
        detector.update(STANDING_ANGLE)

        detector.reset()

        assert detector.current_state == SquatState.UNKNOWN

    def test_reset_preserves_thresholds(self, detector):
        detector.reset()

        assert detector.STANDING_THRESHOLD == THRESHOLD_STANDING
        assert detector.SQUATTING_THRESHOLD == THRESHOLD_SQUATTING
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

    def test_standing(self, detector):
        detector.update(STANDING_ANGLE)

        assert detector.get_state_name() == "standing"

    def test_squatting(self, detector):
        detector.update(SQUATTING_ANGLE)

        assert detector.get_state_name() == "squatting"


# ---------------------------------------------------------------------------
# update_thresholds integration
# ---------------------------------------------------------------------------
class TestUpdateThresholds:
    """Verify base class update_thresholds works with squat attrs."""

    def test_update_standing_threshold(self, detector):
        detector.update_thresholds(STANDING_THRESHOLD=160)

        assert detector.STANDING_THRESHOLD == 160

    def test_update_squatting_threshold(self, detector):
        detector.update_thresholds(SQUATTING_THRESHOLD=100)

        assert detector.SQUATTING_THRESHOLD == 100

    def test_updated_threshold_affects_state_machine(self, detector):
        """Lower the standing threshold — angle that was hysteresis now triggers STANDING."""
        detector.update_thresholds(STANDING_THRESHOLD=120)

        detector.update(SQUATTING_ANGLE)
        # 130 is now > 120 (new threshold), so this transitions to STANDING
        result = detector.update(HYSTERESIS_ANGLE)

        assert result is True
        assert detector.rep_count == 1
