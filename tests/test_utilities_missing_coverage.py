import pytest
import logging
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

from kerykeion.utilities import (
    get_number_from_name,
    get_kerykeion_point_from_degree,
    setup_logging,
    is_point_between,
    julian_to_datetime,
    datetime_to_julian,
    get_planet_house,
    check_and_adjust_polar_latitude,
    circular_mean,
    calculate_moon_phase,
    get_moon_emoji_from_phase_int,
    get_moon_phase_name_from_phase_int,
    inline_css_variables_in_svg,
    find_common_active_points
)
from kerykeion.schemas.kerykeion_exception import KerykeionException


class TestUtilitiesMissingCoverage:
    """Test suite for uncovered utilities functionality."""

    def test_get_number_from_name_all_cases(self):
        """Test all planet name to ID mappings including edge cases."""
        
        # Test all known planets
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
            "Mean_Node": 10,
            "True_Node": 11,
            "Mean_South_Node": 1000,
            "True_South_Node": 1100,
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

    def test_get_number_from_name_unknown_planet(self):
        """Test error handling for unknown planet names."""
        with pytest.raises(KerykeionException) as exc_info:
            get_number_from_name("UnknownPlanet")
        
        assert "Error in getting number from name" in str(exc_info.value)
        assert "UnknownPlanet" in str(exc_info.value)

    def test_get_kerykeion_point_from_degree_negative_degrees(self):
        """Test degree normalization for negative values."""
        # Test negative degree normalization
        result = get_kerykeion_point_from_degree(-30, "Sun", "AstrologicalPoint")  # type: ignore
        assert result.abs_pos == 330  # -30 should become 330
        assert result.sign == "Pis"  # Pisces sign (330-360° range)
        assert result.position == 0  # Position within the sign should be 0

    def test_get_kerykeion_point_from_degree_large_degrees(self):
        """Test error handling for degrees >= 360."""
        with pytest.raises(KerykeionException) as exc_info:
            get_kerykeion_point_from_degree(360, "Sun", "AstrologicalPoint")  # type: ignore
        
        assert "Error in calculating positions" in str(exc_info.value)

    def test_setup_logging_all_levels(self):
        """Test logging setup with all log levels."""
        # Test all valid log levels
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        
        for level in valid_levels:
            setup_logging(level)
            # Just verify it doesn't raise an exception
            
    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid level defaults to info."""
        # Test invalid level - should default to INFO
        setup_logging("invalid_level")
        # Should not raise an exception

    def test_check_and_adjust_polar_latitude_edge_cases(self):
        """Test polar latitude adjustment edge cases."""
        # Test latitude above 66.0
        result = check_and_adjust_polar_latitude(80.0)
        assert result == 66.0
        
        # Test latitude below -66.0
        result = check_and_adjust_polar_latitude(-80.0)
        assert result == -66.0
        
        # Test normal latitude
        result = check_and_adjust_polar_latitude(45.0)
        assert result == 45.0

    def test_circular_mean_edge_cases(self):
        """Test circular mean calculation edge cases."""
        # Test crossing 0/360 boundary
        result = circular_mean(350, 10)
        # Should handle the circular nature correctly
        assert isinstance(result, float)

    def test_calculate_moon_phase_edge_cases(self):
        """Test moon phase calculation edge cases."""
        # Test different moon phases
        result = calculate_moon_phase(0, 0)  # Same position
        assert result.moon_phase_name == "New Moon"
        
        result = calculate_moon_phase(180, 0)  # Opposition
        assert result.moon_phase_name == "Full Moon"

    def test_get_moon_emoji_from_phase_int_all_phases(self):
        """Test all moon phase emoji mappings."""
        # Test all possible phase integers (0-27)
        for phase in range(28):
            emoji = get_moon_emoji_from_phase_int(phase)
            assert isinstance(emoji, str)
            assert len(emoji) > 0

    def test_get_moon_phase_name_from_phase_int_all_phases(self):
        """Test all moon phase name mappings."""
        # Test all possible phase integers (0-27)
        for phase in range(28):
            name = get_moon_phase_name_from_phase_int(phase)
            assert isinstance(name, str)
            assert len(name) > 0

    def test_get_planet_house_edge_cases(self):
        """Test planet house calculation edge cases."""
        # Test with planet at exact house boundary
        houses_degrees_list = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
        
        # Test planet exactly on house cusp
        house = get_planet_house(30.0, houses_degrees_list)
        assert house == "Second_House"

    def test_inline_css_variables_in_svg_edge_cases(self):
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

    def test_find_common_active_points_edge_cases(self):
        """Test finding common active points edge cases."""
        # Test with empty lists
        result = find_common_active_points([], [])
        assert result == []
        
        # Test with no common points
        first_points = ["Sun", "Moon"]
        second_points = ["Mars", "Venus"]
        result = find_common_active_points(first_points, second_points)
        assert result == []
        
        # Test with some common points
        first_points = ["Sun", "Moon", "Mars"]
        second_points = ["Moon", "Mars", "Venus"]
        result = find_common_active_points(first_points, second_points)
        assert "Moon" in result
        assert "Mars" in result
        assert "Sun" not in result
        assert "Venus" not in result

    def test_is_point_between_edge_cases(self):
        """Test additional edge cases for is_point_between function."""
        # Test exactly at start point
        assert is_point_between(0, 30, 0) == True
        
        # Test exactly at end point (should be False according to function docs)
        assert is_point_between(0, 30, 30) == False
        
        # Test crossing 360/0 boundary
        assert is_point_between(350, 20, 10) == True
        assert is_point_between(350, 20, 350) == True

    def test_julian_datetime_conversion_edge_cases(self):
        """Test Julian day number conversion edge cases."""
        # Test with very early dates
        early_date = datetime(1900, 1, 1, 0, 0, 0)
        julian = datetime_to_julian(early_date)
        converted_back = julian_to_datetime(julian)
        
        # Allow small differences due to floating point precision
        assert abs((early_date - converted_back).total_seconds()) < 1

    def test_utilities_error_paths(self):
        """Test various error paths in utilities."""
        # Test extreme values that might cause errors
        with pytest.raises((ValueError, KerykeionException)):
            # This should trigger some error path
            get_kerykeion_point_from_degree(1000, "Sun", "Planet")  # Way beyond 360
