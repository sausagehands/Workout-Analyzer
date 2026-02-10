"""Unit tests for angle_math module.

Tests calculate_angle, get_distance, and normalize_angle using
Arrange-Act-Assert structure with nominal and edge cases.
"""
import math

import pytest
import numpy as np

from core_cv.analysis.angle_math import calculate_angle, get_distance, normalize_angle


# ---------------------------------------------------------------------------
# calculate_angle – nominal cases
# ---------------------------------------------------------------------------
class TestCalculateAngleNominal:
    """Known-good geometric configurations."""

    def test_straight_line_180_degrees(self):
        # Arrange: three collinear points
        p1 = (0, 0)
        p2 = (50, 50)
        p3 = (100, 100)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == pytest.approx(180.0, abs=0.01)

    def test_right_angle_90_degrees(self):
        # Arrange: classic L-shape
        p1 = (0, 0)
        p2 = (0, 100)
        p3 = (100, 100)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == pytest.approx(90.0, abs=0.01)

    def test_acute_angle_45_degrees(self):
        # Arrange: 45-degree angle at origin
        p1 = (100, 0)
        p2 = (0, 0)
        p3 = (100, 100)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == pytest.approx(45.0, abs=0.01)

    def test_obtuse_angle_135_degrees(self):
        # Arrange
        p1 = (0, 0)
        p2 = (100, 100)
        p3 = (200, 100)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == pytest.approx(135.0, abs=0.01)

    def test_60_degree_equilateral(self):
        # Arrange: equilateral triangle vertex
        p1 = (0, 0)
        p2 = (1, 0)
        p3 = (0.5, math.sqrt(3) / 2)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == pytest.approx(60.0, abs=0.01)

    def test_small_angle_approximately_6_degrees(self):
        # Arrange: nearly parallel vectors
        p1 = (100, 0)
        p2 = (0, 0)
        p3 = (100, 10)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert – atan2(10,100) ~ 5.71 degrees
        expected = math.degrees(math.atan2(10, 100))
        assert angle == pytest.approx(expected, abs=0.1)

    def test_return_type_is_float(self):
        # Arrange
        p1 = (1, 0)
        p2 = (0, 0)
        p3 = (0, 1)

        # Act
        result = calculate_angle(p1, p2, p3)

        # Assert
        assert isinstance(result, float)


# ---------------------------------------------------------------------------
# calculate_angle – edge cases
# ---------------------------------------------------------------------------
class TestCalculateAngleEdge:
    """Degenerate, boundary, and unusual inputs."""

    def test_coincident_p1_and_p2_returns_zero(self):
        # Arrange: p1 == p2 -> zero-length vector
        p1 = (5, 5)
        p2 = (5, 5)
        p3 = (10, 10)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == 0.0

    def test_coincident_p2_and_p3_returns_zero(self):
        # Arrange: p2 == p3 -> zero-length vector
        p1 = (10, 10)
        p2 = (5, 5)
        p3 = (5, 5)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == 0.0

    def test_all_three_points_coincident_returns_zero(self):
        # Arrange
        p = (7, 7)

        # Act
        angle = calculate_angle(p, p, p)

        # Assert
        assert angle == 0.0

    def test_very_close_to_zero_angle(self):
        # Arrange: nearly overlapping directions
        p1 = (1_000_000, 0)
        p2 = (0, 0)
        p3 = (1_000_000, 1)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert 0.0 < angle < 0.001

    def test_very_close_to_180_angle(self):
        # Arrange: nearly straight line with tiny bend
        p1 = (-1_000_000, 0)
        p2 = (0, 0)
        p3 = (1_000_000, 1)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert 179.999 < angle < 180.0

    def test_negative_coordinates(self):
        # Arrange: all negative quadrant right angle
        p1 = (-100, -100)
        p2 = (0, 0)
        p3 = (100, -100)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == pytest.approx(90.0, abs=0.01)

    def test_floating_point_inputs(self):
        # Arrange
        p1 = (0.5, 0.5)
        p2 = (1.5, 1.5)
        p3 = (2.5, 2.5)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert – collinear
        assert angle == pytest.approx(180.0, abs=0.01)

    def test_large_coordinate_values(self):
        # Arrange: right angle with very large values
        p1 = (0, 1e12)
        p2 = (0, 0)
        p3 = (1e12, 0)

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == pytest.approx(90.0, abs=0.01)

    def test_numpy_array_inputs(self):
        # Arrange: pass numpy arrays instead of tuples
        p1 = np.array([1, 0])
        p2 = np.array([0, 0])
        p3 = np.array([0, 1])

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == pytest.approx(90.0, abs=0.01)

    def test_list_inputs(self):
        # Arrange: pass lists instead of tuples
        p1 = [1, 0]
        p2 = [0, 0]
        p3 = [0, 1]

        # Act
        angle = calculate_angle(p1, p2, p3)

        # Assert
        assert angle == pytest.approx(90.0, abs=0.01)

    def test_result_always_between_0_and_180(self):
        # Arrange: various angles shouldn't exceed [0, 180]
        cases = [
            ((1, 0), (0, 0), (0, 1)),    # 90
            ((1, 0), (0, 0), (-1, 0)),    # 180
            ((1, 0), (0, 0), (1, 1)),     # 45
            ((1, 0), (0, 0), (-1, 1)),    # 135
        ]

        for p1, p2, p3 in cases:
            # Act
            angle = calculate_angle(p1, p2, p3)

            # Assert
            assert 0.0 <= angle <= 180.0

    def test_order_matters_vertex_at_p2(self):
        # Arrange: swapping p1 and p3 should give the same angle
        p1 = (1, 0)
        p2 = (0, 0)
        p3 = (0, 1)

        # Act
        angle_forward = calculate_angle(p1, p2, p3)
        angle_reversed = calculate_angle(p3, p2, p1)

        # Assert
        assert angle_forward == pytest.approx(angle_reversed, abs=0.001)


# ---------------------------------------------------------------------------
# get_distance – nominal cases
# ---------------------------------------------------------------------------
class TestGetDistanceNominal:
    """Standard Euclidean distance calculations."""

    def test_3_4_5_triangle(self):
        # Arrange
        p1 = (0, 0)
        p2 = (3, 4)

        # Act
        dist = get_distance(p1, p2)

        # Assert
        assert dist == pytest.approx(5.0, abs=0.001)

    def test_horizontal_distance(self):
        # Arrange
        p1 = (0, 0)
        p2 = (10, 0)

        # Act
        dist = get_distance(p1, p2)

        # Assert
        assert dist == pytest.approx(10.0, abs=0.001)

    def test_vertical_distance(self):
        # Arrange
        p1 = (0, 0)
        p2 = (0, 7)

        # Act
        dist = get_distance(p1, p2)

        # Assert
        assert dist == pytest.approx(7.0, abs=0.001)

    def test_diagonal_unit_distance(self):
        # Arrange
        p1 = (0, 0)
        p2 = (1, 1)

        # Act
        dist = get_distance(p1, p2)

        # Assert
        assert dist == pytest.approx(math.sqrt(2), abs=0.001)

    def test_return_type_is_float(self):
        # Arrange
        p1 = (0, 0)
        p2 = (3, 4)

        # Act
        result = get_distance(p1, p2)

        # Assert
        assert isinstance(result, float)

    def test_symmetry(self):
        # Arrange
        p1 = (2, 7)
        p2 = (11, 3)

        # Act
        d1 = get_distance(p1, p2)
        d2 = get_distance(p2, p1)

        # Assert
        assert d1 == pytest.approx(d2, abs=1e-10)


# ---------------------------------------------------------------------------
# get_distance – edge cases
# ---------------------------------------------------------------------------
class TestGetDistanceEdge:
    """Degenerate and boundary conditions for distance."""

    def test_same_point_returns_zero(self):
        # Arrange
        p = (42, 99)

        # Act
        dist = get_distance(p, p)

        # Assert
        assert dist == 0.0

    def test_negative_coordinates(self):
        # Arrange
        p1 = (-3, -4)
        p2 = (0, 0)

        # Act
        dist = get_distance(p1, p2)

        # Assert
        assert dist == pytest.approx(5.0, abs=0.001)

    def test_large_values(self):
        # Arrange
        p1 = (0, 0)
        p2 = (1e8, 0)

        # Act
        dist = get_distance(p1, p2)

        # Assert
        assert dist == pytest.approx(1e8, rel=1e-6)

    def test_fractional_coordinates(self):
        # Arrange
        p1 = (0.1, 0.2)
        p2 = (0.4, 0.6)

        # Act
        dist = get_distance(p1, p2)

        # Assert
        expected = math.sqrt(0.3**2 + 0.4**2)
        assert dist == pytest.approx(expected, abs=1e-10)

    def test_numpy_array_inputs(self):
        # Arrange
        p1 = np.array([0, 0])
        p2 = np.array([3, 4])

        # Act
        dist = get_distance(p1, p2)

        # Assert
        assert dist == pytest.approx(5.0, abs=0.001)

    def test_result_always_non_negative(self):
        # Arrange
        pairs = [
            ((0, 0), (1, 1)),
            ((-5, -5), (5, 5)),
            ((100, 0), (0, 100)),
        ]

        for p1, p2 in pairs:
            # Act
            dist = get_distance(p1, p2)

            # Assert
            assert dist >= 0.0


# ---------------------------------------------------------------------------
# normalize_angle – nominal cases
# ---------------------------------------------------------------------------
class TestNormalizeAngleNominal:
    """Standard angle normalization within expected ranges."""

    def test_zero_stays_zero(self):
        assert normalize_angle(0) == 0

    def test_90_stays_90(self):
        assert normalize_angle(90) == 90

    def test_180_stays_180(self):
        assert normalize_angle(180) == 180

    def test_45_stays_45(self):
        assert normalize_angle(45) == 45

    def test_135_stays_135(self):
        assert normalize_angle(135) == 135


# ---------------------------------------------------------------------------
# normalize_angle – edge cases
# ---------------------------------------------------------------------------
class TestNormalizeAngleEdge:
    """Angles that wrap, are negative, or sit on boundaries."""

    def test_negative_angle_becomes_positive(self):
        # Arrange
        angle = -90

        # Act
        result = normalize_angle(angle)

        # Assert
        assert result == 90

    def test_negative_45_becomes_45(self):
        assert normalize_angle(-45) == 45

    def test_negative_180_becomes_180(self):
        assert normalize_angle(-180) == 180

    def test_270_wraps_to_90(self):
        # Arrange: 360 - 270 = 90
        angle = 270

        # Act
        result = normalize_angle(angle)

        # Assert
        assert result == 90

    def test_360_wraps_to_0(self):
        # Arrange: 360 - 360 = 0
        result = normalize_angle(360)
        assert result == 0

    def test_200_wraps_to_160(self):
        # Arrange: 360 - 200 = 160
        result = normalize_angle(200)
        assert result == 160

    def test_350_wraps_to_10(self):
        # Arrange: 360 - 350 = 10
        result = normalize_angle(350)
        assert result == 10

    def test_negative_270_wraps_to_90(self):
        # Arrange: abs(-270) = 270, 360 - 270 = 90
        result = normalize_angle(-270)
        assert result == 90

    def test_float_input(self):
        # Arrange
        result = normalize_angle(45.5)

        # Assert
        assert result == pytest.approx(45.5, abs=0.001)

    def test_result_always_in_0_to_180(self):
        # Arrange: sweep a range of angles
        test_angles = [0, 45, 90, 135, 180, -45, -90, -135, -180, 200, 270, 350]

        for angle in test_angles:
            # Act
            result = normalize_angle(angle)

            # Assert
            assert 0 <= result <= 180, f"normalize_angle({angle}) = {result} out of range"
