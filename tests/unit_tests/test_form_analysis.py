"""Unit tests for form_analysis module.

Tests the core analyze_form function and the three exercise-specific
wrappers: analyze_squat_form, analyze_pushup_form, analyze_curl_form.
Arranged in nominal and edge cases.

Thresholds from app_constants:
  Squat:  STANDING=155, EXCELLENT=90, GOOD=105
  Pushup: UP=155,       EXCELLENT=90, GOOD=110
  Curl:   DOWN=155,     EXCELLENT=50, GOOD=70
"""
import pytest

from core_cv2.analysis.form_analysis import (
    analyze_form,
    analyze_squat_form,
    analyze_pushup_form,
    analyze_curl_form,
)
from config.app_constants import SQUAT_THRESHOLDS, PUSHUP_THRESHOLDS, CURL_THRESHOLDS


# ---------------------------------------------------------------------------
# Test feedback config for analyze_form tests
# ---------------------------------------------------------------------------
TEST_FEEDBACK = {
    'unknown': 'No pose detected',
    'excellent': 'Great!',
    'good': 'Decent',
    'poor': 'Try harder',
}


# ---------------------------------------------------------------------------
# analyze_form (core function) – nominal cases
# ---------------------------------------------------------------------------
class TestAnalyzeFormNominal:
    """Verify the core analyze_form function."""

    def test_none_returns_unknown(self):
        result = analyze_form(None, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'unknown'
        assert result['feedback'] == 'No pose detected'

    def test_above_neutral_returns_neutral(self):
        result = analyze_form(160, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'neutral'
        assert result['feedback'] == ''

    def test_at_or_below_excellent_returns_excellent(self):
        result = analyze_form(85, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'excellent'
        assert result['feedback'] == 'Great!'

    def test_between_excellent_and_good_returns_good(self):
        result = analyze_form(100, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'good'
        assert result['feedback'] == 'Decent'

    def test_above_good_returns_poor(self):
        result = analyze_form(120, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'poor'
        assert result['feedback'] == 'Try harder'

    def test_returns_dict_with_quality_and_feedback(self):
        result = analyze_form(100, 150, 90, 110, TEST_FEEDBACK)

        assert isinstance(result, dict)
        assert set(result.keys()) == {'quality', 'feedback'}

    def test_custom_thresholds(self):
        """Different thresholds produce correct classification."""
        feedback = {'unknown': 'x', 'excellent': 'x', 'good': 'x', 'poor': 'x'}
        assert analyze_form(55, 50, 20, 40, feedback)['quality'] == 'neutral'
        assert analyze_form(15, 50, 20, 40, feedback)['quality'] == 'excellent'
        assert analyze_form(30, 50, 20, 40, feedback)['quality'] == 'good'
        assert analyze_form(45, 50, 20, 40, feedback)['quality'] == 'poor'


# ---------------------------------------------------------------------------
# analyze_form (core function) – edge cases
# ---------------------------------------------------------------------------
class TestAnalyzeFormEdge:
    """Edge cases for the core analyze_form function."""

    def test_exactly_at_neutral_threshold(self):
        """150 is NOT > 150, falls to quality evaluation."""
        result = analyze_form(150, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] != 'neutral'

    def test_one_above_neutral_threshold(self):
        result = analyze_form(151, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'neutral'

    def test_exactly_at_excellent_threshold(self):
        result = analyze_form(90, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'excellent'

    def test_one_above_excellent_threshold(self):
        result = analyze_form(91, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] != 'excellent'

    def test_exactly_at_good_threshold(self):
        result = analyze_form(110, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'good'

    def test_one_above_good_threshold(self):
        result = analyze_form(111, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'poor'

    def test_zero_angle(self):
        result = analyze_form(0, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'excellent'

    def test_negative_angle(self):
        result = analyze_form(-10, 150, 90, 110, TEST_FEEDBACK)

        assert result['quality'] == 'excellent'

    def test_uses_custom_feedback_strings(self):
        custom = {
            'unknown': 'CUSTOM_UNKNOWN',
            'excellent': 'CUSTOM_EXCELLENT',
            'good': 'CUSTOM_GOOD',
            'poor': 'CUSTOM_POOR',
        }
        assert analyze_form(None, 150, 90, 110, custom)['feedback'] == 'CUSTOM_UNKNOWN'
        assert analyze_form(80, 150, 90, 110, custom)['feedback'] == 'CUSTOM_EXCELLENT'
        assert analyze_form(100, 150, 90, 110, custom)['feedback'] == 'CUSTOM_GOOD'
        assert analyze_form(120, 150, 90, 110, custom)['feedback'] == 'CUSTOM_POOR'


# ---------------------------------------------------------------------------
# analyze_squat_form – nominal cases
# ---------------------------------------------------------------------------
class TestSquatFormNominal:
    """Verify squat form quality classification."""

    def test_none_returns_unknown(self):
        result = analyze_squat_form(None)

        assert result['quality'] == 'unknown'
        assert result['feedback'] == 'Move into frame'

    def test_standing_returns_neutral(self):
        result = analyze_squat_form(170)

        assert result['quality'] == 'neutral'
        assert result['feedback'] == ''

    def test_excellent_depth(self):
        result = analyze_squat_form(85)

        assert result['quality'] == 'excellent'
        assert 'Perfect' in result['feedback']

    def test_good_depth(self):
        result = analyze_squat_form(100)

        assert result['quality'] == 'good'
        assert 'Good' in result['feedback']

    def test_poor_depth(self):
        result = analyze_squat_form(120)

        assert result['quality'] == 'poor'
        assert 'deeper' in result['feedback']

    def test_returns_dict(self):
        result = analyze_squat_form(90)

        assert isinstance(result, dict)
        assert 'quality' in result
        assert 'feedback' in result


# ---------------------------------------------------------------------------
# analyze_squat_form – edge cases
# ---------------------------------------------------------------------------
class TestSquatFormEdge:
    """Edge cases for squat form analysis."""

    def test_exactly_at_standing_threshold(self):
        """155 is NOT > 155, so falls to squat evaluation."""
        result = analyze_squat_form(SQUAT_THRESHOLDS['STANDING'])

        assert result['quality'] != 'neutral'

    def test_one_above_standing_threshold(self):
        result = analyze_squat_form(SQUAT_THRESHOLDS['STANDING'] + 1)

        assert result['quality'] == 'neutral'

    def test_exactly_at_excellent_threshold(self):
        """90 is <= 90, so excellent."""
        result = analyze_squat_form(SQUAT_THRESHOLDS['EXCELLENT'])

        assert result['quality'] == 'excellent'

    def test_one_above_excellent_threshold(self):
        """91 is NOT <= 90, falls to good check."""
        result = analyze_squat_form(SQUAT_THRESHOLDS['EXCELLENT'] + 1)

        assert result['quality'] != 'excellent'

    def test_exactly_at_good_threshold(self):
        """105 is <= 105, so good."""
        result = analyze_squat_form(SQUAT_THRESHOLDS['GOOD'])

        assert result['quality'] == 'good'

    def test_one_above_good_threshold(self):
        """106 is NOT <= 105, falls to poor."""
        result = analyze_squat_form(SQUAT_THRESHOLDS['GOOD'] + 1)

        assert result['quality'] == 'poor'

    def test_zero_angle(self):
        result = analyze_squat_form(0)

        assert result['quality'] == 'excellent'

    def test_very_deep_squat(self):
        result = analyze_squat_form(30)

        assert result['quality'] == 'excellent'

    def test_180_degrees(self):
        result = analyze_squat_form(180)

        assert result['quality'] == 'neutral'


# ---------------------------------------------------------------------------
# analyze_pushup_form – nominal cases
# ---------------------------------------------------------------------------
class TestPushupFormNominal:
    """Verify pushup form quality classification."""

    def test_none_returns_unknown(self):
        result = analyze_pushup_form(None)

        assert result['quality'] == 'unknown'
        assert result['feedback'] == 'Move into frame'

    def test_arms_extended_returns_neutral(self):
        result = analyze_pushup_form(170)

        assert result['quality'] == 'neutral'
        assert result['feedback'] == ''

    def test_excellent_depth(self):
        result = analyze_pushup_form(85)

        assert result['quality'] == 'excellent'
        assert 'Perfect' in result['feedback']

    def test_good_depth(self):
        result = analyze_pushup_form(100)

        assert result['quality'] == 'good'
        assert 'Good' in result['feedback']

    def test_poor_depth(self):
        result = analyze_pushup_form(130)

        assert result['quality'] == 'poor'
        assert 'lower' in result['feedback'].lower()

    def test_returns_dict(self):
        result = analyze_pushup_form(90)

        assert isinstance(result, dict)
        assert 'quality' in result
        assert 'feedback' in result


# ---------------------------------------------------------------------------
# analyze_pushup_form – edge cases
# ---------------------------------------------------------------------------
class TestPushupFormEdge:
    """Edge cases for pushup form analysis."""

    def test_exactly_at_up_threshold(self):
        """155 is NOT > 155, so falls to pushup evaluation."""
        result = analyze_pushup_form(PUSHUP_THRESHOLDS['UP'])

        assert result['quality'] != 'neutral'

    def test_one_above_up_threshold(self):
        result = analyze_pushup_form(PUSHUP_THRESHOLDS['UP'] + 1)

        assert result['quality'] == 'neutral'

    def test_exactly_at_excellent_threshold(self):
        """90 is <= 90, so excellent."""
        result = analyze_pushup_form(PUSHUP_THRESHOLDS['EXCELLENT'])

        assert result['quality'] == 'excellent'

    def test_one_above_excellent_threshold(self):
        result = analyze_pushup_form(PUSHUP_THRESHOLDS['EXCELLENT'] + 1)

        assert result['quality'] != 'excellent'

    def test_exactly_at_good_threshold(self):
        """110 is <= 110, so good."""
        result = analyze_pushup_form(PUSHUP_THRESHOLDS['GOOD'])

        assert result['quality'] == 'good'

    def test_one_above_good_threshold(self):
        """111 is NOT <= 110, falls to poor."""
        result = analyze_pushup_form(PUSHUP_THRESHOLDS['GOOD'] + 1)

        assert result['quality'] == 'poor'

    def test_zero_angle(self):
        result = analyze_pushup_form(0)

        assert result['quality'] == 'excellent'

    def test_180_degrees(self):
        result = analyze_pushup_form(180)

        assert result['quality'] == 'neutral'


# ---------------------------------------------------------------------------
# analyze_curl_form – nominal cases
# ---------------------------------------------------------------------------
class TestCurlFormNominal:
    """Verify curl form quality classification."""

    def test_none_returns_unknown(self):
        result = analyze_curl_form(None)

        assert result['quality'] == 'unknown'
        assert result['feedback'] == 'Move into frame'

    def test_arm_extended_returns_neutral(self):
        result = analyze_curl_form(170)

        assert result['quality'] == 'neutral'
        assert result['feedback'] == ''

    def test_excellent_curl(self):
        result = analyze_curl_form(40)

        assert result['quality'] == 'excellent'
        assert 'Full curl' in result['feedback']

    def test_good_curl(self):
        result = analyze_curl_form(60)

        assert result['quality'] == 'good'
        assert 'Good' in result['feedback']

    def test_poor_curl(self):
        result = analyze_curl_form(100)

        assert result['quality'] == 'poor'
        assert 'Curl' in result['feedback']

    def test_returns_dict(self):
        result = analyze_curl_form(50)

        assert isinstance(result, dict)
        assert 'quality' in result
        assert 'feedback' in result


# ---------------------------------------------------------------------------
# analyze_curl_form – edge cases
# ---------------------------------------------------------------------------
class TestCurlFormEdge:
    """Edge cases for curl form analysis."""

    def test_exactly_at_down_threshold(self):
        """155 is NOT > 155, so falls to curl evaluation."""
        result = analyze_curl_form(CURL_THRESHOLDS['DOWN'])

        assert result['quality'] != 'neutral'

    def test_one_above_down_threshold(self):
        result = analyze_curl_form(CURL_THRESHOLDS['DOWN'] + 1)

        assert result['quality'] == 'neutral'

    def test_exactly_at_excellent_threshold(self):
        """50 is <= 50, so excellent."""
        result = analyze_curl_form(CURL_THRESHOLDS['EXCELLENT'])

        assert result['quality'] == 'excellent'

    def test_one_above_excellent_threshold(self):
        result = analyze_curl_form(CURL_THRESHOLDS['EXCELLENT'] + 1)

        assert result['quality'] != 'excellent'

    def test_exactly_at_good_threshold(self):
        """70 is <= 70, so good."""
        result = analyze_curl_form(CURL_THRESHOLDS['GOOD'])

        assert result['quality'] == 'good'

    def test_one_above_good_threshold(self):
        """71 is NOT <= 70, falls to poor."""
        result = analyze_curl_form(CURL_THRESHOLDS['GOOD'] + 1)

        assert result['quality'] == 'poor'

    def test_zero_angle(self):
        result = analyze_curl_form(0)

        assert result['quality'] == 'excellent'

    def test_180_degrees(self):
        result = analyze_curl_form(180)

        assert result['quality'] == 'neutral'


# ---------------------------------------------------------------------------
# No color key – all three functions
# ---------------------------------------------------------------------------
class TestNoColorKey:
    """Verify color key is no longer returned (commented out)."""

    def test_squat_no_color(self):
        assert 'color' not in analyze_squat_form(None)
        assert 'color' not in analyze_squat_form(170)
        assert 'color' not in analyze_squat_form(85)
        assert 'color' not in analyze_squat_form(100)
        assert 'color' not in analyze_squat_form(120)

    def test_pushup_no_color(self):
        assert 'color' not in analyze_pushup_form(None)
        assert 'color' not in analyze_pushup_form(170)
        assert 'color' not in analyze_pushup_form(85)
        assert 'color' not in analyze_pushup_form(100)
        assert 'color' not in analyze_pushup_form(130)

    def test_curl_no_color(self):
        assert 'color' not in analyze_curl_form(None)
        assert 'color' not in analyze_curl_form(170)
        assert 'color' not in analyze_curl_form(40)
        assert 'color' not in analyze_curl_form(60)
        assert 'color' not in analyze_curl_form(100)


# ---------------------------------------------------------------------------
# Quality values are valid strings
# ---------------------------------------------------------------------------
class TestQualityValues:
    """Verify quality is always one of the expected strings."""

    VALID_QUALITIES = {'excellent', 'good', 'poor', 'neutral', 'unknown'}

    @pytest.mark.parametrize("angle", [None, 0, 30, 85, 90, 91, 100, 105, 106, 120, 155, 156, 170, 180])
    def test_squat_quality_always_valid(self, angle):
        result = analyze_squat_form(angle)
        assert result['quality'] in self.VALID_QUALITIES

    @pytest.mark.parametrize("angle", [None, 0, 30, 85, 90, 91, 100, 110, 111, 130, 155, 156, 170, 180])
    def test_pushup_quality_always_valid(self, angle):
        result = analyze_pushup_form(angle)
        assert result['quality'] in self.VALID_QUALITIES

    @pytest.mark.parametrize("angle", [None, 0, 30, 40, 50, 51, 60, 70, 71, 100, 155, 156, 170, 180])
    def test_curl_quality_always_valid(self, angle):
        result = analyze_curl_form(angle)
        assert result['quality'] in self.VALID_QUALITIES
