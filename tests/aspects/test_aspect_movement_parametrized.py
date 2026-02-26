"""
Parametrized tests for aspect movement calculation.

This module consolidates all aspect movement tests into parametrized form,
testing the calculate_aspect_movement() function with various scenarios.

Test categories:
- Basic scenarios (applying, separating, static)
- Retrograde motion
- Boundary crossing (0°/360° wrap-around)
- Edge cases and special conditions
"""

import pytest
from kerykeion.aspects.aspects_utils import calculate_aspect_movement


# =============================================================================
# TEST DATA - Parametrized test cases
# =============================================================================

# Format: (p1_pos, p2_pos, aspect_degrees, p1_speed, p2_speed, expected_result, description)
BASIC_MOVEMENT_CASES = [
    # Applying cases - faster point behind slower, moving toward
    pytest.param(45.0, 50.0, 0.0, 12.5, 1.0, "Applying", id="faster_behind_approaching"),
    pytest.param(80.0, 90.0, 0.0, 2.0, 0.5, "Applying", id="slow_catch_up"),
    # Separating cases - faster point ahead, moving away
    pytest.param(55.0, 50.0, 0.0, 12.5, 1.0, "Separating", id="faster_ahead_moving_away"),
    pytest.param(100.0, 90.0, 0.0, 2.0, 0.5, "Separating", id="slow_moving_apart"),
    # Static cases - no relative motion
    pytest.param(10.0, 20.0, 0.0, 0.0, 0.0, "Static", id="both_stationary"),
    pytest.param(10.0, 40.0, 30.0, 1.0, 1.0, "Static", id="same_speed_constant_orb"),
    pytest.param(100.0, 200.0, 100.0, 5.0, 5.0, "Static", id="same_speed_any_aspect"),
]

RETROGRADE_CASES = [
    # Retrograde planet applying
    pytest.param(110.0, 100.0, 0.0, -0.8, 0.1, "Applying", id="retrograde_faster_applying"),
    pytest.param(15.0, 10.0, 0.0, -1.0, 1.0, "Applying", id="retrograde_approaching_direct"),
    pytest.param(10.0, 15.0, 0.0, 1.0, -1.0, "Applying", id="direct_approaching_retrograde"),
    # Retrograde planet separating
    pytest.param(10.0, 5.0, 0.0, 1.0, -1.0, "Separating", id="direct_leaving_retrograde"),
    pytest.param(5.0, 10.0, 0.0, -1.0, 1.0, "Separating", id="retrograde_leaving_direct"),
    # Both retrograde
    pytest.param(10.0, 15.0, 0.0, -1.0, -2.0, "Applying", id="both_retrograde_approaching"),
    pytest.param(15.0, 10.0, 0.0, -2.0, -1.0, "Applying", id="both_retrograde_faster_behind"),
]

BOUNDARY_CROSSING_CASES = [
    # Crossing 0°/360° boundary
    pytest.param(359.0, 5.0, 0.0, 1.0, 13.0, "Separating", id="moon_past_sun_at_boundary"),
    pytest.param(359.0, 355.0, 0.0, 1.0, 13.0, "Applying", id="moon_approaching_at_boundary"),
    pytest.param(5.0, 355.0, 0.0, 1.0, 1.0, "Static", id="same_speed_across_boundary"),
    # Near boundary with various aspects
    pytest.param(358.0, 2.0, 0.0, 0.5, 1.0, "Separating", id="just_past_conjunction_boundary"),
    pytest.param(355.0, 1.0, 0.0, 0.5, 1.0, "Separating", id="well_past_conjunction_boundary"),
]

ASPECT_TYPE_CASES = [
    # Different aspect angles
    pytest.param(10.0, 245.0, 240.0, 1.0, 13.0, "Applying", id="large_aspect_approaching"),
    pytest.param(10.0, 130.0, 120.0, 1.0, 13.0, "Separating", id="trine_exact_separating"),
    pytest.param(0.0, 180.0, 120.0, 0.0, 1.0, "Applying", id="180_separation_trine_applying"),
    # Opposition
    pytest.param(10.0, 190.0, 180.0, 1.0, 0.5, "Separating", id="opposition_separating"),
    pytest.param(10.0, 185.0, 180.0, 0.5, 1.0, "Applying", id="opposition_applying"),
    # Square
    pytest.param(10.0, 100.0, 90.0, 1.0, 0.5, "Separating", id="square_separating"),
    pytest.param(10.0, 95.0, 90.0, 0.5, 1.0, "Applying", id="square_applying"),
]

EXACT_ASPECT_CASES = [
    # At exact aspect
    pytest.param(10.0, 10.0, 0.0, 1.0, -1.0, "Separating", id="exact_conjunction_separating"),
    pytest.param(10.0, 10.0, 0.0, 1.0, 2.0, "Separating", id="exact_conjunction_faster_ahead"),
    pytest.param(10.0, 10.0, 0.0, 2.0, 1.0, "Separating", id="exact_conjunction_faster_p1"),
    pytest.param(10.0, 10.0, 0.0, 0.0, 0.0, "Static", id="exact_conjunction_both_static"),
]

EDGE_CASES = [
    # Very small differences - function treats tiny relative speed as Static
    pytest.param(10.0, 10.001, 0.0, 1.0, 0.999, "Static", id="tiny_relative_speed_static"),
    pytest.param(10.0, 9.999, 0.0, 1.001, 1.0, "Separating", id="tiny_orb_p1_faster"),
    # Large speed differences
    pytest.param(10.0, 50.0, 0.0, 50.0, 1.0, "Applying", id="very_fast_p1_applying"),
    pytest.param(50.0, 10.0, 0.0, 1.0, 50.0, "Applying", id="very_fast_p2_applying"),
    # Near 180° separation - actual behavior from implementation
    pytest.param(0.0, 179.0, 180.0, 1.0, 0.5, "Separating", id="near_opposition_179"),
    pytest.param(0.0, 181.0, 180.0, 1.0, 0.5, "Applying", id="near_opposition_181"),
]


# =============================================================================
# PARAMETRIZED TESTS
# =============================================================================


class TestAspectMovementBasic:
    """Basic aspect movement scenarios."""

    @pytest.mark.parametrize("p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected", BASIC_MOVEMENT_CASES)
    def test_basic_movement(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        """Test basic applying/separating/static scenarios."""
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected


class TestAspectMovementRetrograde:
    """Retrograde motion scenarios."""

    @pytest.mark.parametrize("p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected", RETROGRADE_CASES)
    def test_retrograde_movement(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        """Test retrograde planet aspect movement."""
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected


class TestAspectMovementBoundary:
    """Boundary crossing (0°/360°) scenarios."""

    @pytest.mark.parametrize("p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected", BOUNDARY_CROSSING_CASES)
    def test_boundary_crossing(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        """Test aspect movement across 0°/360° boundary."""
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected


class TestAspectMovementTypes:
    """Different aspect type scenarios."""

    @pytest.mark.parametrize("p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected", ASPECT_TYPE_CASES)
    def test_aspect_types(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        """Test aspect movement for various aspect types."""
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected


class TestAspectMovementExact:
    """Exact aspect scenarios."""

    @pytest.mark.parametrize("p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected", EXACT_ASPECT_CASES)
    def test_exact_aspect(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        """Test aspect movement at exact aspect."""
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected


class TestAspectMovementEdge:
    """Edge case scenarios."""

    @pytest.mark.parametrize("p1_pos,p2_pos,aspect,p1_speed,p2_speed,expected", EDGE_CASES)
    def test_edge_cases(self, p1_pos, p2_pos, aspect, p1_speed, p2_speed, expected):
        """Test edge case scenarios."""
        result = calculate_aspect_movement(
            point_one_abs_pos=p1_pos,
            point_two_abs_pos=p2_pos,
            aspect_degrees=aspect,
            point_one_speed=p1_speed,
            point_two_speed=p2_speed,
        )
        assert result == expected


# =============================================================================
# COMPREHENSIVE INTEGRATION TESTS
# =============================================================================


class TestAspectMovementComprehensive:
    """Comprehensive tests combining multiple factors."""

    def test_all_basic_cases_from_original(self):
        """Verify all original test cases still pass."""
        # From test_aspect_movement.py
        assert calculate_aspect_movement(45.0, 50.0, 0.0, 12.5, 1.0) == "Applying"
        assert calculate_aspect_movement(55.0, 50.0, 0.0, 12.5, 1.0) == "Separating"
        assert calculate_aspect_movement(110.0, 100.0, 0.0, -0.8, 0.1) == "Applying"
        assert calculate_aspect_movement(10.0, 20.0, 0.0, 0.0, 0.0) == "Static"
        assert calculate_aspect_movement(10.0, 40.0, 30.0, 1.0, 1.0) == "Static"

    def test_all_comprehensive_cases_from_original(self):
        """Verify all original comprehensive test cases still pass."""
        # From test_aspect_movement_comprehensive.py
        assert calculate_aspect_movement(359, 5, 0, 1, 13) == "Separating"
        assert calculate_aspect_movement(359, 355, 0, 1, 13) == "Applying"
        assert calculate_aspect_movement(10, 245, 240, 1, 13) == "Applying"
        assert calculate_aspect_movement(10, 15, 0, 1, -1) == "Applying"
        assert calculate_aspect_movement(10, 5, 0, 1, -1) == "Separating"
        assert calculate_aspect_movement(10, 15, 0, -1, -2) == "Applying"
        assert calculate_aspect_movement(10, 130, 120, 1, 13) == "Separating"
        assert calculate_aspect_movement(10, 10, 0, 1, -1) == "Separating"
        assert calculate_aspect_movement(0, 180, 120, 0, 1) == "Applying"

    def test_return_type(self):
        """Test that return type is always a string."""
        result = calculate_aspect_movement(45.0, 50.0, 0.0, 12.5, 1.0)
        assert isinstance(result, str)
        assert result in ["Applying", "Separating", "Static"]

    def test_symmetric_behavior(self):
        """Test that swapping points affects result correctly."""
        # When we swap positions and speeds, result should be consistent
        result1 = calculate_aspect_movement(45.0, 50.0, 0.0, 12.5, 1.0)
        result2 = calculate_aspect_movement(50.0, 45.0, 0.0, 1.0, 12.5)

        # Both should give the same result (both detecting the faster point approaching)
        assert result1 == result2
