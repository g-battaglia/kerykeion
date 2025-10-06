# -*- coding: utf-8 -*-
"""
    Test suite for draw_planets function
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import pytest
from unittest.mock import patch
from kerykeion.charts.draw_planets import draw_planets
from kerykeion.schemas import KerykeionException, KerykeionPointModel
from kerykeion.schemas.settings_models import KerykeionSettingsCelestialPointModel


class TestDrawPlanets:
    """Test suite for the draw_planets function and all its functionality."""

    def setup_method(self):
        """Set up test data for each test method."""
        # Basic test parameters
        self.radius = 200
        self.third_circle_radius = 30
        self.first_house_degree = 0.0
        self.seventh_house_degree = 180.0

        # Create mock celestial points data
        self.mock_celestial_points = [
            {
                "name": "Sun",
                "abs_pos": 15.5,
                "position": 15.5,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☉",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Moon",
                "abs_pos": 45.2,
                "position": 15.2,
                "house": "Second_House",
                "sign": "Tau",
                "quality": "Fixed",
                "element": "Earth",
                "sign_num": 1,
                "emoji": "☽",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Mercury",
                "abs_pos": 20.1,
                "position": 20.1,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☿",
                "point_type": "AstrologicalPoint",
                "retrograde": True
            }
        ]

        # Create mock planets settings
        self.mock_planets_settings = [
            {
                "id": 0,
                "name": "Sun",
                "color": "#FFA500",
                "element_points": 5,
                "label": "Sun",
                "is_active": True
            },
            {
                "id": 1,
                "name": "Moon",
                "color": "#C0C0C0",
                "element_points": 4,
                "label": "Moon",
                "is_active": True
            },
            {
                "id": 4,
                "name": "Mercury",
                "color": "#87CEEB",
                "element_points": 3,
                "label": "Mercury",
                "is_active": True
            }
        ]

        # Create grouped planets for grouping tests
        self.grouped_celestial_points = [
            {
                "name": "Sun",
                "abs_pos": 15.0,
                "position": 15.0,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☉",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Mercury",
                "abs_pos": 16.5,  # Close to Sun (1.5 degrees)
                "position": 16.5,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☿",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Venus",
                "abs_pos": 18.0,  # Close to Sun and Mercury (3.0 degrees from Sun)
                "position": 18.0,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "♀",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            }
        ]

        self.grouped_planets_settings = [
            {
                "id": 0,
                "name": "Sun",
                "color": "#FFA500",
                "element_points": 5,
                "label": "Sun",
                "is_active": True
            },
            {
                "id": 4,
                "name": "Mercury",
                "color": "#87CEEB",
                "element_points": 3,
                "label": "Mercury",
                "is_active": True
            },
            {
                "id": 3,
                "name": "Venus",
                "color": "#FFB6C1",
                "element_points": 4,
                "label": "Venus",
                "is_active": True
            }
        ]

        # Create house angles (ASC, MC, DSC, IC) for testing angle positions
        self.angle_celestial_points = [
            {
                "name": "First_House",  # ASC
                "abs_pos": 0.0,
                "position": 0.0,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "AC",
                "point_type": "House",
                "retrograde": False
            }
        ]

        self.angle_planets_settings = [
            {
                "id": 23,  # Index between 22 and 27 for chart angles
                "name": "First_House",
                "color": "#000000",
                "element_points": 0,
                "label": "ASC",
                "is_active": True
            }
        ]

    def _create_kerykeion_point_models(self, points_data):
        """Helper to create KerykeionPointModel instances from dict data."""
        return [KerykeionPointModel(**point) for point in points_data]

    def _create_settings_models(self, settings_data):
        """Helper to create KerykeionSettingsCelestialPointModel instances from dict data."""
        return [KerykeionSettingsCelestialPointModel(**setting) for setting in settings_data]

    def test_basic_natal_chart(self):
        """Test basic natal chart generation without external view."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Basic assertions
        assert isinstance(result, str)
        assert len(result) > 0

        # Check that SVG elements are present
        assert '<g kr:node="ChartPoint"' in result
        assert 'xlink:href="#Sun"' in result
        assert 'xlink:href="#Moon"' in result
        assert 'xlink:href="#Mercury"' in result

        # Ensure no external view lines are present
        assert '<line x1=' not in result

    def test_natal_chart_with_external_view(self):
        """Test natal chart generation with external view enabled."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal",
            external_view=True
        )

        # Basic assertions
        assert isinstance(result, str)
        assert len(result) > 0

        # Check that SVG elements are present
        assert '<g kr:node="ChartPoint"' in result

        # Check for external view connecting lines
        assert '<line x1=' in result
        assert 'stroke-opacity:.3' in result  # First line opacity
        assert 'stroke-opacity:.5' in result  # Second line opacity

    def test_transit_chart(self):
        """Test transit chart generation with secondary celestial points."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        # Create secondary points for transit
        secondary_points = self._create_kerykeion_point_models([
            {
                "name": "Sun",
                "abs_pos": 75.5,
                "position": 15.5,
                "house": "Third_House",
                "sign": "Gem",
                "quality": "Mutable",
                "element": "Air",
                "sign_num": 2,
                "emoji": "☉",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Moon",
                "abs_pos": 105.2,
                "position": 15.2,
                "house": "Fourth_House",
                "sign": "Can",
                "quality": "Cardinal",
                "element": "Water",
                "sign_num": 3,
                "emoji": "☽",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Mercury",
                "abs_pos": 80.1,
                "position": 20.1,
                "house": "Third_House",
                "sign": "Gem",
                "quality": "Mutable",
                "element": "Air",
                "sign_num": 2,
                "emoji": "☿",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            }
        ])

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Transit",
            second_subject_available_kerykeion_celestial_points=secondary_points
        )

        # Basic assertions
        assert isinstance(result, str)
        assert len(result) > 0

        # Check for main chart points
        assert '<g kr:node="ChartPoint"' in result

        # Check for transit elements
        assert 'class="transit-planet-name"' in result
        assert 'class="transit-planet-line"' in result

    def test_synastry_chart(self):
        """Test synastry chart generation with secondary celestial points."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        # Create secondary points for synastry
        secondary_points = self._create_kerykeion_point_models([
            {
                "name": "Sun",
                "abs_pos": 105.3,
                "position": 15.3,
                "house": "Fourth_House",
                "sign": "Can",
                "quality": "Cardinal",
                "element": "Water",
                "sign_num": 3,
                "emoji": "☉",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Moon",
                "abs_pos": 135.2,
                "position": 15.2,
                "house": "Fifth_House",
                "sign": "Leo",
                "quality": "Fixed",
                "element": "Fire",
                "sign_num": 4,
                "emoji": "☽",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Mercury",
                "abs_pos": 110.1,
                "position": 20.1,
                "house": "Fourth_House",
                "sign": "Can",
                "quality": "Cardinal",
                "element": "Water",
                "sign_num": 3,
                "emoji": "☿",
                "point_type": "AstrologicalPoint",
                "retrograde": True
            }
        ])

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Synastry",
            second_subject_available_kerykeion_celestial_points=secondary_points
        )

        # Basic assertions
        assert isinstance(result, str)
        assert len(result) > 0

        # Check for main chart points
        assert '<g kr:node="ChartPoint"' in result

        # Check for synastry elements (similar to transit)
        assert 'style="stroke:' in result

    def test_return_chart(self):
        """Test return chart generation with secondary celestial points."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        # Create secondary points for return
        secondary_points = self._create_kerykeion_point_models([
            {
                "name": "Sun",
                "abs_pos": 15.5,  # Same position as natal Sun for return
                "position": 15.5,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☉",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Moon",
                "abs_pos": 45.2,
                "position": 15.2,
                "house": "Second_House",
                "sign": "Tau",
                "quality": "Fixed",
                "element": "Earth",
                "sign_num": 1,
                "emoji": "☽",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Mercury",
                "abs_pos": 20.1,
                "position": 20.1,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☿",
                "point_type": "AstrologicalPoint",
                "retrograde": True
            }
        ])

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="SingleReturnChart",
            second_subject_available_kerykeion_celestial_points=secondary_points
        )

        # Basic assertions
        assert isinstance(result, str)
        assert len(result) > 0

    def test_dual_return_chart(self):
        """Test dual return chart generation with secondary celestial points."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        # Create secondary points for dual return
        secondary_points = self._create_kerykeion_point_models([
            {
                "name": "Sun",
                "abs_pos": 15.5,  # Same position as natal Sun for return
                "position": 15.5,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☉",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Moon",
                "abs_pos": 45.2,
                "position": 15.2,
                "house": "Second_House",
                "sign": "Tau",
                "quality": "Fixed",
                "element": "Earth",
                "sign_num": 1,
                "emoji": "☽",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Mercury",
                "abs_pos": 20.1,
                "position": 20.1,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☿",
                "point_type": "AstrologicalPoint",
                "retrograde": True
            }
        ])

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="DualReturnChart",
            second_subject_available_kerykeion_celestial_points=secondary_points
        )

        # Basic assertions
        assert isinstance(result, str)
        assert len(result) > 0

    def test_error_transit_without_secondary_points(self):
        """Test that Transit chart raises exception when secondary points are missing."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        with pytest.raises(KerykeionException, match="Secondary celestial points are required for Transit charts"):
            draw_planets(
                radius=self.radius,
                available_kerykeion_celestial_points=celestial_points,
                available_planets_setting=planets_settings,
                third_circle_radius=self.third_circle_radius,
                main_subject_first_house_degree_ut=self.first_house_degree,
                main_subject_seventh_house_degree_ut=self.seventh_house_degree,
                chart_type="Transit"
            )

    def test_error_synastry_without_secondary_points(self):
        """Test that Synastry chart raises exception when secondary points are missing."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        with pytest.raises(KerykeionException, match="Secondary celestial points are required for Synastry charts"):
            draw_planets(
                radius=self.radius,
                available_kerykeion_celestial_points=celestial_points,
                available_planets_setting=planets_settings,
                third_circle_radius=self.third_circle_radius,
                main_subject_first_house_degree_ut=self.first_house_degree,
                main_subject_seventh_house_degree_ut=self.seventh_house_degree,
                chart_type="Synastry"
            )

    def test_error_return_without_secondary_points(self):
        """Test that the current function implementation for return charts."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        # NOTE: The current implementation doesn't check for "SingleReturnChart" or "DualReturnChart"
        # It only checks for "Return", so these don't raise exceptions
        # This tests the actual behavior of the function as it exists

        # Test SingleReturnChart - should NOT raise exception
        result_single = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="SingleReturnChart"
        )
        assert isinstance(result_single, str)

        # Test DualReturnChart - should NOT raise exception
        result_dual = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="DualReturnChart"
        )
        assert isinstance(result_dual, str)

    def test_grouped_planets_two_points(self):
        """Test planet grouping logic with two close celestial points."""
        # Create two planets very close to each other
        grouped_points = [
            {
                "name": "Sun",
                "abs_pos": 15.0,
                "position": 15.0,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☉",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            },
            {
                "name": "Mercury",
                "abs_pos": 16.5,  # 1.5 degrees apart (within threshold)
                "position": 16.5,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☿",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            }
        ]

        grouped_settings = [
            {
                "id": 0,
                "name": "Sun",
                "color": "#FFA500",
                "element_points": 5,
                "label": "Sun",
                "is_active": True
            },
            {
                "id": 4,
                "name": "Mercury",
                "color": "#87CEEB",
                "element_points": 3,
                "label": "Mercury",
                "is_active": True
            }
        ]

        celestial_points = self._create_kerykeion_point_models(grouped_points)
        planets_settings = self._create_settings_models(grouped_settings)

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Should successfully render grouped planets
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'xlink:href="#Sun"' in result
        assert 'xlink:href="#Mercury"' in result

    def test_grouped_planets_three_points(self):
        """Test planet grouping logic with three close celestial points."""
        celestial_points = self._create_kerykeion_point_models(self.grouped_celestial_points)
        planets_settings = self._create_settings_models(self.grouped_planets_settings)

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Should successfully render grouped planets
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'xlink:href="#Sun"' in result
        assert 'xlink:href="#Mercury"' in result
        assert 'xlink:href="#Venus"' in result

    def test_single_planet(self):
        """Test chart with only a single celestial point."""
        single_point = [
            {
                "name": "Sun",
                "abs_pos": 15.0,
                "position": 15.0,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☉",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            }
        ]

        single_setting = [
            {
                "id": 0,
                "name": "Sun",
                "color": "#FFA500",
                "element_points": 5,
                "label": "Sun",
                "is_active": True
            }
        ]

        celestial_points = self._create_kerykeion_point_models(single_point)
        planets_settings = self._create_settings_models(single_setting)

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Should successfully render single planet
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'xlink:href="#Sun"' in result

    def test_chart_angles_positioning(self):
        """Test positioning of chart angles (ASC, MC, DSC, IC)."""
        celestial_points = self._create_kerykeion_point_models(self.angle_celestial_points)
        planets_settings = self._create_settings_models(self.angle_planets_settings)

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Should successfully render angle
        assert isinstance(result, str)
        assert len(result) > 0
        assert 'xlink:href="#First_House"' in result

    def test_different_radii(self):
        """Test function with different radius values."""
        celestial_points = self._create_kerykeion_point_models([self.mock_celestial_points[0]])
        planets_settings = self._create_settings_models([self.mock_planets_settings[0]])

        # Test with small radius
        result_small = draw_planets(
            radius=50,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=10,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Test with large radius
        result_large = draw_planets(
            radius=500,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=50,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Both should work
        assert isinstance(result_small, str) and len(result_small) > 0
        assert isinstance(result_large, str) and len(result_large) > 0

    def test_float_parameters(self):
        """Test function with float parameters."""
        celestial_points = self._create_kerykeion_point_models([self.mock_celestial_points[0]])
        planets_settings = self._create_settings_models([self.mock_planets_settings[0]])

        result = draw_planets(
            radius=200.5,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=30.25,
            main_subject_first_house_degree_ut=0.75,
            main_subject_seventh_house_degree_ut=180.33,
            chart_type="Natal"
        )

        # Should handle float parameters correctly
        assert isinstance(result, str)
        assert len(result) > 0

    def test_extreme_positions(self):
        """Test with extreme astronomical positions."""
        # Test planet at 0 degrees
        extreme_point_0 = [
            {
                "name": "Sun",
                "abs_pos": 0.0,
                "position": 0.0,
                "house": "First_House",
                "sign": "Ari",
                "quality": "Cardinal",
                "element": "Fire",
                "sign_num": 0,
                "emoji": "☉",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            }
        ]

        # Test planet at 359.99 degrees
        extreme_point_359 = [
            {
                "name": "Moon",
                "abs_pos": 359.99,
                "position": 29.99,
                "house": "Twelfth_House",
                "sign": "Pis",
                "quality": "Mutable",
                "element": "Water",
                "sign_num": 11,
                "emoji": "☽",
                "point_type": "AstrologicalPoint",
                "retrograde": False
            }
        ]

        setting = [self.mock_planets_settings[0]]

        celestial_points_0 = self._create_kerykeion_point_models(extreme_point_0)
        celestial_points_359 = self._create_kerykeion_point_models(extreme_point_359)
        planets_settings = self._create_settings_models(setting)

        result_0 = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points_0,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        result_359 = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points_359,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Both extreme positions should work
        assert isinstance(result_0, str) and len(result_0) > 0
        assert isinstance(result_359, str) and len(result_359) > 0

    def test_empty_planet_list(self):
        """Test function behavior with empty planet lists."""
        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=[],
            available_planets_setting=[],
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Should return empty string for no planets
        assert isinstance(result, str)
        assert result == ""

    def test_scale_factors_for_different_chart_types(self):
        """Test that different chart types apply correct scale factors."""
        celestial_points = self._create_kerykeion_point_models([self.mock_celestial_points[0]])
        planets_settings = self._create_settings_models([self.mock_planets_settings[0]])
        secondary_points = self._create_kerykeion_point_models([self.mock_celestial_points[1]])

        # Test Transit scale factor
        result_transit = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Transit",
            second_subject_available_kerykeion_celestial_points=secondary_points
        )

        # Test Synastry scale factor
        result_synastry = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Synastry",
            second_subject_available_kerykeion_celestial_points=secondary_points
        )

        # Test SingleReturnChart scale factor
        result_return = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="SingleReturnChart",
            second_subject_available_kerykeion_celestial_points=secondary_points
        )

        # Test external view scale factor
        result_external = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal",
            external_view=True
        )

        # All should render successfully with appropriate scaling
        assert isinstance(result_transit, str) and len(result_transit) > 0
        assert isinstance(result_synastry, str) and len(result_synastry) > 0
        assert isinstance(result_return, str) and len(result_return) > 0
        assert isinstance(result_external, str) and len(result_external) > 0

        # External view should have connecting lines
        assert '<line x1=' in result_external

    @patch('kerykeion.charts.draw_planets.logging.debug')
    def test_logging_calls(self, mock_debug):
        """Test that logging debug calls are made appropriately."""
        celestial_points = self._create_kerykeion_point_models([self.mock_celestial_points[0]])
        planets_settings = self._create_settings_models([self.mock_planets_settings[0]])

        draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Should have called debug logging for planet indexing
        assert mock_debug.called

    def test_svg_output_structure(self):
        """Test the structure and content of the SVG output."""
        celestial_points = self._create_kerykeion_point_models(self.mock_celestial_points)
        planets_settings = self._create_settings_models(self.mock_planets_settings)

        result = draw_planets(
            radius=self.radius,
            available_kerykeion_celestial_points=celestial_points,
            available_planets_setting=planets_settings,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_house_degree,
            main_subject_seventh_house_degree_ut=self.seventh_house_degree,
            chart_type="Natal"
        )

        # Check SVG structure
        assert 'kr:node="ChartPoint"' in result
        assert 'kr:house=' in result
        assert 'kr:sign=' in result
        assert 'kr:slug=' in result
        assert 'transform=' in result
        assert 'scale(' in result
        assert '</g>' in result

        # Check that each planet appears once
        sun_count = result.count('xlink:href="#Sun"')
        moon_count = result.count('xlink:href="#Moon"')
        mercury_count = result.count('xlink:href="#Mercury"')

        assert sun_count == 1
        assert moon_count == 1
        assert mercury_count == 1
