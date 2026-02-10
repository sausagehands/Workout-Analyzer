"""Unit tests for ExerciseDetector abstract base class.

Tests the concrete methods in base_detector.py using a minimal
stub subclass. Arranged in nominal and edge cases.
"""
import pytest

from core_cv2.detection.detector_blueprint import ExerciseDetector


# ---------------------------------------------------------------------------
# Minimal concrete subclass for testing
# ---------------------------------------------------------------------------
class StubDetector(ExerciseDetector):
    """Minimal subclass that satisfies the ABC contract."""

    def __init__(self, cooldown_frames=15):
        super().__init__(name="stub", cooldown_frames=cooldown_frames)
        self.state = "IDLE"

    def update(self, angle: float) -> bool:
        return False

    def get_state_name(self) -> str:
        return self.state


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def detector():
    """Return a fresh StubDetector with default cooldown."""
    return StubDetector(cooldown_frames=15)


# ---------------------------------------------------------------------------
# __init__ – nominal cases
# ---------------------------------------------------------------------------
class TestInitNominal:
    """Verify base detector initializes correctly."""

    def test_name_stored(self, detector):
        assert detector.name == "stub"

    def test_rep_count_starts_zero(self, detector):
        assert detector.rep_count == 0

    def test_cooldown_frames_starts_zero(self, detector):
        assert detector.cooldown_frames == 0

    def test_cooldown_period_stored(self, detector):
        assert detector.COOLDOWN_PERIOD == 15

    def test_custom_cooldown_period(self):
        d = StubDetector(cooldown_frames=30)
        assert d.COOLDOWN_PERIOD == 30


# ---------------------------------------------------------------------------
# __init__ – edge cases
# ---------------------------------------------------------------------------
class TestInitEdge:
    """Edge cases for initialization."""

    def test_zero_cooldown_period(self):
        d = StubDetector(cooldown_frames=0)
        assert d.COOLDOWN_PERIOD == 0

    def test_large_cooldown_period(self):
        d = StubDetector(cooldown_frames=9999)
        assert d.COOLDOWN_PERIOD == 9999


# ---------------------------------------------------------------------------
# reset – nominal cases
# ---------------------------------------------------------------------------
class TestResetNominal:
    """Verify reset clears counters."""

    def test_reset_clears_rep_count(self, detector):
        detector.rep_count = 10

        detector.reset()

        assert detector.rep_count == 0

    def test_reset_clears_cooldown_frames(self, detector):
        detector.cooldown_frames = 5

        detector.reset()

        assert detector.cooldown_frames == 0

    def test_reset_does_not_change_cooldown_period(self, detector):
        detector.reset()

        assert detector.COOLDOWN_PERIOD == 15

    def test_reset_does_not_change_name(self, detector):
        detector.reset()

        assert detector.name == "stub"


# ---------------------------------------------------------------------------
# reset – edge cases
# ---------------------------------------------------------------------------
class TestResetEdge:
    """Edge cases for reset."""

    def test_reset_when_already_zero(self, detector):
        # Already at defaults
        detector.reset()

        assert detector.rep_count == 0
        assert detector.cooldown_frames == 0

    def test_double_reset(self, detector):
        detector.rep_count = 5
        detector.cooldown_frames = 3

        detector.reset()
        detector.reset()

        assert detector.rep_count == 0
        assert detector.cooldown_frames == 0


# ---------------------------------------------------------------------------
# _increment_rep – nominal cases
# ---------------------------------------------------------------------------
class TestIncrementRepNominal:
    """Verify _increment_rep bumps counter."""

    def test_increments_from_zero(self, detector):
        detector._increment_rep()

        assert detector.rep_count == 1

    def test_increments_sequentially(self, detector):
        detector._increment_rep()
        detector._increment_rep()
        detector._increment_rep()

        assert detector.rep_count == 3


# ---------------------------------------------------------------------------
# _start_cooldown – nominal cases
# ---------------------------------------------------------------------------
class TestStartCooldownNominal:
    """Verify _start_cooldown sets frames to COOLDOWN_PERIOD."""

    def test_sets_cooldown_frames(self, detector):
        detector._start_cooldown()

        assert detector.cooldown_frames == 15

    def test_resets_cooldown_when_called_again(self, detector):
        detector._start_cooldown()
        detector.cooldown_frames = 3  # partially decremented

        detector._start_cooldown()

        assert detector.cooldown_frames == 15


# ---------------------------------------------------------------------------
# _start_cooldown – edge cases
# ---------------------------------------------------------------------------
class TestStartCooldownEdge:
    """Edge cases for _start_cooldown."""

    def test_zero_cooldown_period(self):
        d = StubDetector(cooldown_frames=0)

        d._start_cooldown()

        assert d.cooldown_frames == 0


# ---------------------------------------------------------------------------
# _decrement_cooldown – nominal cases
# ---------------------------------------------------------------------------
class TestDecrementCooldownNominal:
    """Verify _decrement_cooldown decreases counter."""

    def test_decrements_by_one(self, detector):
        detector.cooldown_frames = 5

        detector._decrement_cooldown()

        assert detector.cooldown_frames == 4

    def test_decrements_to_zero(self, detector):
        detector.cooldown_frames = 1

        detector._decrement_cooldown()

        assert detector.cooldown_frames == 0

    def test_full_cooldown_cycle(self, detector):
        detector._start_cooldown()

        for _ in range(15):
            detector._decrement_cooldown()

        assert detector.cooldown_frames == 0


# ---------------------------------------------------------------------------
# _decrement_cooldown – edge cases
# ---------------------------------------------------------------------------
class TestDecrementCooldownEdge:
    """Edge cases for _decrement_cooldown."""

    def test_does_not_go_below_zero(self, detector):
        detector.cooldown_frames = 0

        detector._decrement_cooldown()

        assert detector.cooldown_frames == 0

    def test_multiple_decrements_at_zero(self, detector):
        detector.cooldown_frames = 0

        for _ in range(10):
            detector._decrement_cooldown()

        assert detector.cooldown_frames == 0


# ---------------------------------------------------------------------------
# update_thresholds – nominal cases
# ---------------------------------------------------------------------------
class TestUpdateThresholdsNominal:
    """Verify update_thresholds sets attributes dynamically."""

    def test_updates_direct_attribute(self):
        d = StubDetector()
        d.STANDING = 155  # simulate a threshold attribute

        d.update_thresholds(STANDING=140)

        assert d.STANDING == 140

    def test_updates_threshold_suffix(self):
        d = StubDetector()
        d.ANGLE_THRESHOLD = 90

        d.update_thresholds(ANGLE=75)

        assert d.ANGLE_THRESHOLD == 75

    def test_updates_cooldown_special_case(self, detector):
        detector.update_thresholds(COOLDOWN_FRAMES=25)

        assert detector.COOLDOWN_PERIOD == 25

    def test_updates_multiple_at_once(self):
        d = StubDetector()
        d.STANDING = 155
        d.SQUATTING = 110

        d.update_thresholds(STANDING=150, SQUATTING=95)

        assert d.STANDING == 150
        assert d.SQUATTING == 95


# ---------------------------------------------------------------------------
# update_thresholds – edge cases
# ---------------------------------------------------------------------------
class TestUpdateThresholdsEdge:
    """Edge cases for update_thresholds."""

    def test_unknown_key_is_silently_ignored(self, detector):
        # No exception should be raised
        detector.update_thresholds(NONEXISTENT_ATTR=42)

        assert not hasattr(detector, "NONEXISTENT_ATTR")

    def test_empty_kwargs(self, detector):
        # No exception
        detector.update_thresholds()

        assert detector.COOLDOWN_PERIOD == 15

    def test_direct_attr_takes_priority_over_suffix(self):
        """If both ANGLE and ANGLE_THRESHOLD exist, direct wins."""
        d = StubDetector()
        d.ANGLE = 100
        d.ANGLE_THRESHOLD = 90

        d.update_thresholds(ANGLE=80)

        # Direct attribute updated, suffix untouched
        assert d.ANGLE == 80
        assert d.ANGLE_THRESHOLD == 90


# ---------------------------------------------------------------------------
# ABC contract
# ---------------------------------------------------------------------------
class TestABCContract:
    """Verify the abstract base class enforces its contract."""

    def test_cannot_instantiate_abc_directly(self):
        with pytest.raises(TypeError):
            ExerciseDetector(name="test")

    def test_stub_satisfies_contract(self, detector):
        # Should not raise — StubDetector implements both abstract methods
        assert detector.update(90.0) is False
        assert detector.get_state_name() == "IDLE"
