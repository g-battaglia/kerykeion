"""
Test suite for enhanced calculate_aspect_movement function.
Tests focus on precision improvements, edge cases, and validation.
"""

import pytest
from kerykeion.aspects.aspects_utils import calculate_aspect_movement


class TestInputValidation:
    """Test input validation improvements"""

    def test_none_speed_raises_error(self):
        """Should raise ValueError when speed is None"""
        with pytest.raises(ValueError, match="Speed values for both points are required"):
            calculate_aspect_movement(10.0, 20.0, 0.0, None, 1.0)

        with pytest.raises(ValueError, match="Speed values for both points are required"):
            calculate_aspect_movement(10.0, 20.0, 0.0, 1.0, None)

    def test_invalid_position_raises_error(self):
        """Should raise ValueError when position is out of range [0, 360)"""
        with pytest.raises(ValueError, match="Positions must be in range"):
            calculate_aspect_movement(-1.0, 20.0, 0.0, 1.0, 1.0)

        with pytest.raises(ValueError, match="Positions must be in range"):
            calculate_aspect_movement(10.0, 361.0, 0.0, 1.0, 1.0)

    def test_negative_aspect_raises_error(self):
        """Should raise ValueError when aspect is negative"""
        with pytest.raises(ValueError, match="Aspect degrees must be non-negative"):
            calculate_aspect_movement(10.0, 20.0, -30.0, 1.0, 1.0)


class TestPrecisionImprovements:
    """Test precision-related improvements"""

    def test_orb_epsilon_handling(self):
        """Orb changes below ORB_EPSILON (1e-6) should be Static"""
        # Very small orb change should be Static
        result = calculate_aspect_movement(10.0, 10.0000001, 0.0, 0.001, 0.001001)
        assert result == "Static"

    def test_speed_epsilon_handling(self):
        """Speed differences below SPEED_EPSILON (1e-9) should be Static"""
        # Identical speeds (within epsilon)
        result = calculate_aspect_movement(10.0, 20.0, 0.0, 1.0, 1.0000000001)
        assert result == "Static"

        # Exactly identical speeds
        result = calculate_aspect_movement(10.0, 20.0, 0.0, 1.0, 1.0)
        assert result == "Static"

    def test_exact_aspect_with_minimal_movement(self):
        """At exact aspect with very small speeds"""
        result = calculate_aspect_movement(10.0, 10.0, 0.0, 0.0001, 0.0002)
        # At exact aspect, very small speed difference creates minimal orb change
        # which is below ORB_EPSILON, so it's Static
        assert result == "Static"

    def test_near_exact_aspect_boundary(self):
        """Test behavior very close to exact aspect"""
        # Just before exact aspect, applying
        result = calculate_aspect_movement(10.0, 9.99, 0.0, 0.0, 1.0)
        assert result == "Applying"

        # Just after exact aspect, separating
        result = calculate_aspect_movement(10.0, 10.01, 0.0, 0.0, 1.0)
        assert result == "Separating"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_crossing_zero_boundary_static(self):
        """Crossing 0°/360° with equal speeds should be Static"""
        result = calculate_aspect_movement(359.5, 0.5, 0.0, 1.0, 1.0)
        assert result == "Static"

    def test_crossing_zero_boundary_applying(self):
        """Crossing 0°/360° while applying"""
        result = calculate_aspect_movement(359.0, 355.0, 0.0, 1.0, 13.0)
        assert result == "Applying"

    def test_aspect_180_exact(self):
        """Test exact opposition (180°)"""
        result = calculate_aspect_movement(0.0, 180.0, 180.0, 0.5, 0.6)
        assert result == "Separating"

    def test_aspect_greater_than_180(self):
        """Aspects > 180° should be normalized correctly"""
        # 240° aspect should be treated as 120°
        result = calculate_aspect_movement(10.0, 250.0, 240.0, 1.0, 1.5)
        assert result == "Separating"

    def test_extreme_speed_difference(self):
        """Test with extreme speed differences (e.g., Ascendant vs planet)"""
        # Ascendant: 360°/day, Planet: 0.01°/day
        result = calculate_aspect_movement(100.0, 190.0, 90.0, 360.0, 0.01)
        assert result == "Separating"

    def test_very_small_speeds(self):
        """Test with very small but non-zero speeds"""
        # Very small relative speed creates orb change below ORB_EPSILON
        result = calculate_aspect_movement(10.0, 11.0, 0.0, 0.0001, 0.00009)
        assert result == "Static"

        # Larger relative speed should give meaningful result
        # P1=10, P2=11, aspect=0 -> P2 ahead by 1°
        # P1 speed=0.01, P2 speed=0.02 -> P2 faster, moving further away
        result = calculate_aspect_movement(10.0, 11.0, 0.0, 0.01, 0.02)
        assert result == "Separating"

    def test_both_retrograde_different_speeds(self):
        """Both points retrograde with different speeds"""
        # P2 faster retrograde, should catch up
        result = calculate_aspect_movement(100.0, 110.0, 0.0, -0.5, -1.0)
        assert result == "Applying"

    def test_both_retrograde_same_speed(self):
        """Both points retrograde with same speed"""
        result = calculate_aspect_movement(100.0, 110.0, 0.0, -1.0, -1.0)
        assert result == "Static"

    def test_aspect_crossing_with_small_dt(self):
        """Point crossing exact aspect within dt"""
        # This should be Static due to ORB_EPSILON
        result = calculate_aspect_movement(10.0, 9.9995, 0.0, 0.0, 1.0)
        assert result == "Static"


class TestNonStandardAspects:
    """Test with less common aspect angles"""

    def test_quintile_72_degrees(self):
        """Test quintile aspect (72°)"""
        result = calculate_aspect_movement(10.0, 82.0, 72.0, 1.0, 1.2)
        assert result == "Separating"

    def test_biquintile_144_degrees(self):
        """Test biquintile aspect (144°)"""
        # P1=10, P2=154, aspect=144 -> exact aspect
        # P1 speed=1.0, P2 speed=0.8 -> P1 is faster, moving away
        result = calculate_aspect_movement(10.0, 154.0, 144.0, 1.0, 0.8)
        assert result == "Separating"

        # To get Applying, P2 should be faster or P2 should be behind the aspect
        result = calculate_aspect_movement(10.0, 150.0, 144.0, 1.0, 2.0)
        assert result == "Applying"

    def test_septile_51_degrees(self):
        """Test septile aspect (~51.43°)"""
        result = calculate_aspect_movement(10.0, 61.43, 51.43, 1.0, 1.5)
        assert result == "Separating"


class TestNumericalStability:
    """Test numerical stability with various dt values"""

    def test_stability_across_dt_values(self):
        """Result should be consistent across reasonable dt values"""
        # The function uses fixed dt=0.001, but we test the concept
        # All these should give Applying
        p1, p2, aspect = 10.0, 50.0, 60.0
        speed1, speed2 = 1.0, 15.0

        result = calculate_aspect_movement(p1, p2, aspect, speed1, speed2)
        assert result == "Applying"

        # With very close positions, should still work
        result = calculate_aspect_movement(10.0, 10.1, 0.0, 0.5, 1.0)
        assert result == "Separating"


class TestDocumentedBehavior:
    """Test behavior as documented in docstring"""

    def test_retrograde_motion(self):
        """Test negative speeds (retrograde) work correctly"""
        # Mercury retrograde approaching Sun
        result = calculate_aspect_movement(10.0, 15.0, 0.0, 1.0, -1.0)
        assert result == "Applying"

        # Mercury retrograde separating from Sun
        result = calculate_aspect_movement(10.0, 5.0, 0.0, 1.0, -1.0)
        assert result == "Separating"

    def test_all_major_aspects(self):
        """Test all major aspects work correctly"""
        aspects = [0, 60, 90, 120, 180]  # Conjunction, Sextile, Square, Trine, Opposition

        for aspect in aspects:
            # Test applying
            result = calculate_aspect_movement(10.0, 10.0 + aspect - 5.0, aspect, 0.5, 2.0)
            assert result == "Applying"

            # Test separating
            result = calculate_aspect_movement(10.0, 10.0 + aspect + 5.0, aspect, 0.5, 2.0)
            assert result == "Separating"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
