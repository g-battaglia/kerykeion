from kerykeion import KerykeionException
from kerykeion.utilities import (
    is_point_between,
    julian_to_datetime,
    datetime_to_julian,
    get_number_from_name,
    get_kerykeion_point_from_degree,
    setup_logging,
    get_planet_house,
    check_and_adjust_polar_latitude,
    circular_mean,
    calculate_moon_phase,
    get_moon_emoji_from_phase_int,
    get_moon_phase_name_from_phase_int,
    inline_css_variables_in_svg,
    find_common_active_points
)
import pytest
import math
import logging
from datetime import datetime


class TestUtilities:
    def test_get_number_from_name(self):
        # Test all known planets with their expected IDs
        known_planets = {
            "Sun": 0,
            "Moon": 1,
            "Mercury": 2,
            "Venus": 3,
            "Mars": 4,
            "Jupiter": 5,
            "Saturn": 6,
            "Uranus": 7,
            "Neptune": 8,
            "Pluto": 9,
            "Mean_North_Lunar_Node": 10,
            "True_North_Lunar_Node": 11,
            "Mean_South_Lunar_Node": 1000,
            "True_South_Lunar_Node": 1100,
            "Chiron": 15,
            "Mean_Lilith": 12,
            "Ascendant": 9900,
            "Descendant": 9901,
            "Medium_Coeli": 9902,
            "Imum_Coeli": 9903,
        }

        for name, expected_id in known_planets.items():
            result = get_number_from_name(name)
            assert result == expected_id, f"Expected {expected_id} for {name}, got {result}"

        # Test error handling for unknown planet names
        with pytest.raises(KerykeionException) as exc_info:
            get_number_from_name("UnknownPlanet")  # type: ignore

        assert "Error in getting number from name" in str(exc_info.value)
        assert "UnknownPlanet" in str(exc_info.value)

    def test_get_kerykeion_point_from_degree(self):
        # Test positive degrees
        pt = get_kerykeion_point_from_degree(45, "Sun", "AstrologicalPoint")
        assert pt.sign == "Tau"

        # Test negative degree normalization
        pt2 = get_kerykeion_point_from_degree(-30, "Sun", "AstrologicalPoint")  # type: ignore
        assert pt2.abs_pos == 330  # -30 should become 330
        assert pt2.sign == "Pis"  # Pisces sign (330-360° range)
        assert pt2.position == 0  # Position within the sign should be 0

        # Test general negative degree case
        pt3 = get_kerykeion_point_from_degree(-15, "Sun", "AstrologicalPoint")
        assert 0 <= pt3.abs_pos < 360

        # Test error handling for degrees >= 360
        with pytest.raises(KerykeionException) as exc_info:
            get_kerykeion_point_from_degree(360, "Sun", "AstrologicalPoint")  # type: ignore
        assert "Error in calculating positions" in str(exc_info.value)

        # Test extreme values
        with pytest.raises((ValueError, KerykeionException)):
            get_kerykeion_point_from_degree(1000, "Sun", "AstrologicalPoint")  # type: ignore

    def test_get_planet_house(self):
        # 12 houses, each 30 degrees
        houses = [i*30 for i in range(12)]
        # Should be in first house
        assert get_planet_house(0, houses) == "First_House"
        # Should be in last house
        assert get_planet_house(359, houses) == "Twelfth_House"

        # Test planet at exact house boundary
        houses_degrees_list = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
        house = get_planet_house(30.0, houses_degrees_list)
        assert house == "Second_House"

    def test_get_moon_emoji_from_phase_int(self):
        # Test all valid branches
        for phase in [1, 2, 7, 10, 14, 15, 20, 21, 23, 28]:
            assert get_moon_emoji_from_phase_int(phase)

        # Test all possible phase integers (0-27)
        for phase in range(28):
            emoji = get_moon_emoji_from_phase_int(phase)
            assert isinstance(emoji, str)
            assert len(emoji) > 0

        # Test error handling
        with pytest.raises(Exception):
            get_moon_emoji_from_phase_int(100)

    def test_get_moon_phase_name_from_phase_int(self):
        # Test valid branches
        for phase in [1, 2, 7, 10, 14, 15, 20, 21, 23, 28]:
            assert get_moon_phase_name_from_phase_int(phase)

        # Test all possible phase integers (0-27)
        for phase in range(28):
            name = get_moon_phase_name_from_phase_int(phase)
            assert isinstance(name, str)
            assert len(name) > 0

        # Test error handling
        with pytest.raises(Exception):
            get_moon_phase_name_from_phase_int(100)

    def test_check_and_adjust_polar_latitude(self):
        # Test normal cases
        assert check_and_adjust_polar_latitude(0) == 0
        assert check_and_adjust_polar_latitude(70) == 66.0
        assert check_and_adjust_polar_latitude(-70) == -66.0

        # Test edge cases
        assert check_and_adjust_polar_latitude(80.0) == 66.0
        assert check_and_adjust_polar_latitude(-80.0) == -66.0
        assert check_and_adjust_polar_latitude(45.0) == 45.0

    def test_circular_mean(self):
        # Normal mean
        result = circular_mean(10, 20)
        assert 0 <= result < 360
        # Across 0/360 boundary
        mean = circular_mean(350, 10)
        assert 0 <= mean <= 360  # Allow 360 as edge case

        # Test crossing 0/360 boundary edge case
        result = circular_mean(350, 10)
        assert isinstance(result, float)

    def setup_class(self):
        pass

    def test_is_point_between(self):
        assert is_point_between(10, 30, 25) is True
        assert is_point_between(10, 30, 35) is False
        assert is_point_between(10, 30, 4) is False

        assert is_point_between(340, 10, 350) is True
        assert is_point_between(340, 10, 4) is True
        assert is_point_between(340, 10, 320) is False
        assert is_point_between(340, 10, 20) is False

        # Edge cases
        assert is_point_between(10, 30, 10) is True
        assert is_point_between(10, 30, 30) is False

        assert is_point_between(340, 10, 340) is True
        assert is_point_between(340, 10, 10) is False

        assert is_point_between(0, 20, 0) is True
        assert is_point_between(0, 20, 20) is False

        assert is_point_between(340, 360, 340) is True
        assert is_point_between(340, 360, 360) is False

        assert is_point_between(360, 20, 0) is True
        assert is_point_between(360, 20, 20) is False
        assert is_point_between(360, 20, 360) is True

        assert is_point_between(340, 0, 340) is True
        assert is_point_between(340, 0, 0) is False
        assert is_point_between(360, 20, 360) is True

        assert is_point_between(10, 30, 10.00000000001) is True
        assert is_point_between(10, 30, 9.999999999999) is False
        assert is_point_between(10, 30, 29.999999999999) is True
        assert is_point_between(10, 30, 30.00000000001) is False

        assert is_point_between(97.89789490940346, 116.14575774583493, 97.89789490940348) is True
        assert is_point_between(97.89789490940346, 116.14575774583493, 97.89789490940340) is False
        assert is_point_between(97.89789490940346, 116.14575774583493, 116.14575774583490) is True
        assert is_point_between(97.89789490940346, 116.14575774583493, 116.14575774583496) is False


    def test_is_point_between_with_exception(self):
        with pytest.raises(KerykeionException) as ex:
            is_point_between(5, 200, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")

        with pytest.raises(KerykeionException) as ex:
            is_point_between(250, 200, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")

        with pytest.raises(KerykeionException) as ex:
            is_point_between(0, 180.1, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")

        with pytest.raises(KerykeionException) as ex:
            is_point_between(359.9, 180, 15)
            assert str(ex.value).startswith("The angle between start and end point is not allowed to exceed 180°")


    def test_julian_to_datetime(self):
        # Test with a known Julian date
        julian_date = 2451545.0
        expected_datetime = datetime(2000, 1, 1, 12, 0)
        result = julian_to_datetime(julian_date)
        delta = abs((result - expected_datetime).total_seconds())
        assert delta < 1, f"Expected {expected_datetime}, but got {result} (Δ={delta:.6f}s)"

        # Test with a Julian date that is not an integer
        julian_date = 2460795.413194
        expected_datetime = datetime(2025, 4, 29, 21, 54, 59)
        result = julian_to_datetime(julian_date)
        delta = abs((result - expected_datetime).total_seconds())
        assert delta < 1, f"Expected {expected_datetime}, but got {result} (Δ={delta:.6f}s)"


    def test_datetime_to_julian(self):
        # Test with a known datetime
        dt = datetime(2000, 1, 1, 12, 0)
        expected_julian = 2451545.0
        result = datetime_to_julian(dt)
        assert math.isclose(result, expected_julian, rel_tol=1e-9), f"Expected {expected_julian}, but got {result}"

        # Test with a datetime that is not at noon
        dt = datetime(2025, 4, 29, 21, 54, 59)
        expected_julian = 2460795.413194
        result = datetime_to_julian(dt)
        assert math.isclose(result, expected_julian, rel_tol=1e-9), f"Expected {expected_julian}, but got {result}"


    def test_julian_to_datetime_and_back(self):
        julian_date = 2451545.0
        dt = julian_to_datetime(julian_date)
        result = datetime_to_julian(dt)
        assert result == julian_date, f"Expected {julian_date}, but got {result}"

        # Test with a Julian date that is not an integer
        julian_date = 2460795.413194
        dt = julian_to_datetime(julian_date)
        result = datetime_to_julian(dt)
        assert result == julian_date, f"Expected {julian_date}, but got {result}"

    def test_setup_logging(self):
        """Test logging setup with all log levels."""
        # Test all valid log levels
        valid_levels = ["debug", "info", "warning", "error", "critical"]

        for level in valid_levels:
            setup_logging(level)
            # Just verify it doesn't raise an exception

        # Test invalid level - should default to INFO
        setup_logging("invalid_level")

    def test_calculate_moon_phase(self):
        """Test moon phase calculation edge cases."""
        # Test different moon phases
        result = calculate_moon_phase(0, 0)  # Same position
        assert result.moon_phase_name == "New Moon"

        result = calculate_moon_phase(180, 0)  # Opposition
        assert result.moon_phase_name == "Full Moon"

    def test_inline_css_variables_in_svg(self):
        """Test CSS variable inlining edge cases."""
        # Test SVG with CSS variables
        svg_content = """
        <svg>
            <style>
                :root {
                    --color: #ff0000;
                }
                .element {
                    fill: var(--color);
                }
            </style>
            <rect class="element" />
        </svg>
        """

        result = inline_css_variables_in_svg(svg_content)
        # Should process without error
        assert isinstance(result, str)

    def test_find_common_active_points(self):
        """Test finding common active points edge cases."""
        # Test with empty lists
        result = find_common_active_points([], [])
        assert result == []

        # Test with no common points
        first_points = ["Sun", "Moon"]  # type: ignore
        second_points = ["Mars", "Venus"]  # type: ignore
        result = find_common_active_points(first_points, second_points)
        assert result == []

        # Test with some common points
        first_points = ["Sun", "Moon", "Mars"]  # type: ignore
        second_points = ["Moon", "Mars", "Venus"]  # type: ignore
        result = find_common_active_points(first_points, second_points)
        assert "Moon" in result
        assert "Mars" in result
        assert "Sun" not in result
        assert "Venus" not in result

    def test_is_point_between_additional_edge_cases(self):
        """Test additional edge cases for is_point_between function."""
        # Test exactly at start point
        assert is_point_between(0, 30, 0) == True

        # Test exactly at end point (should be False according to function docs)
        assert is_point_between(0, 30, 30) == False

        # Test crossing 360/0 boundary
        assert is_point_between(350, 20, 10) == True
        assert is_point_between(350, 20, 350) == True

    def test_julian_datetime_conversion_additional_edge_cases(self):
        """Test Julian day number conversion edge cases."""
        # Test with very early dates
        early_date = datetime(1900, 1, 1, 0, 0, 0)
        julian = datetime_to_julian(early_date)
        converted_back = julian_to_datetime(julian)

        # Allow small differences due to floating point precision
        assert abs((early_date - converted_back).total_seconds()) < 1

if __name__ == "__main__":
    pytest.main([__file__])
