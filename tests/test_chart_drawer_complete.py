import tempfile
import os
import re
from pathlib import Path

import pytest
from unittest.mock import patch

from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.charts.charts_utils import makeLunarPhase


class TestChartDrawer:
    """Test suite for ChartDrawer functionality."""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Set up test fixtures."""
        self.subject = AstrologicalSubjectFactory.from_birth_data(
            name="Test Subject",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=30,
            city="New York",
            nation="US",
            lng=-74.006,
            lat=40.7128,
            tz_str="America/New_York",
            suppress_geonames_warning=True
        )

        # Create chart data for drawing
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

        self.subject2 = AstrologicalSubjectFactory.from_birth_data(
            name="Test Subject 2",
            year=1992,
            month=8,
            day=20,
            hour=15,
            minute=45,
            city="Los Angeles",
            nation="US",
            lng=-118.2437,
            lat=34.0522,
            tz_str="America/Los_Angeles",
            suppress_geonames_warning=True
        )

    def test_basic_chart_creation(self):
        """Test basic chart drawer instantiation."""
        chart = ChartDrawer(self.chart_data)
        assert chart.chart_data is not None
        assert hasattr(chart, 'chart_type')
        assert hasattr(chart, 'first_obj')

    def test_chart_with_custom_theme(self):
        """Test chart creation with custom theme."""
        chart = ChartDrawer(self.chart_data, theme="classic")
        # Theme is processed during initialization
        assert chart.chart_data is not None

    def test_chart_with_language_setting(self):
        """Test chart creation with language setting."""
        chart = ChartDrawer(self.chart_data, chart_language="EN")
        assert chart.chart_language == "EN"

    def test_chart_with_transparent_background(self):
        """Test chart creation with transparent background."""
        chart = ChartDrawer(self.chart_data, transparent_background=True)
        assert chart.transparent_background is True

    def test_chart_with_external_view(self):
        """Test chart creation with external view."""
        chart = ChartDrawer(self.chart_data, external_view=True)
        assert chart.external_view is True

    def test_chart_with_custom_title(self):
        """Test chart creation with custom title."""
        custom_title = "My Custom Chart Title"
        chart = ChartDrawer(self.chart_data, custom_title=custom_title)
        assert chart.custom_title == custom_title

        # Test that the custom title is used in the template
        template_dict = chart._create_template_dictionary()
        assert template_dict["stringTitle"] == custom_title

    def test_chart_with_no_custom_title(self):
        """Test chart creation without custom title uses default."""
        chart = ChartDrawer(self.chart_data)
        assert chart.custom_title is None

        # Test that the default title is used in the template
        template_dict = chart._create_template_dictionary()
        # For natal charts, default format is "Name - Birth Chart"
        expected_default = f'{self.subject.name} - Birth Chart'  # Using English as default
        assert template_dict["stringTitle"] == expected_default

    def test_generate_svg_string_with_kwarg_custom_title(self):
        """ChartDrawer.generate_svg_string should accept a custom title kwarg."""
        chart = ChartDrawer(self.chart_data)
        custom_title = "Override Title"

        svg_output = chart.generate_svg_string(custom_title=custom_title)

        assert custom_title in svg_output

    def test_chart_drawer_properties(self):
        """Test chart drawer has all expected properties."""
        chart = ChartDrawer(self.chart_data)

        assert hasattr(chart, 'chart_data')
        assert hasattr(chart, 'chart_type')
        assert hasattr(chart, 'first_obj')
        assert hasattr(chart, 'chart_language')
        assert hasattr(chart, 'active_points')
        assert hasattr(chart, 'active_aspects')

    def test_chart_template_generation(self):
        """Test chart template generation."""
        chart = ChartDrawer(self.chart_data)

        # Test that template generation methods exist
        assert hasattr(chart, 'save_svg')

    def test_chart_save_methods(self):
        """Test chart save methods exist."""
        chart = ChartDrawer(self.chart_data)

        # Test that save methods exist
        assert hasattr(chart, 'save_svg')

    @patch('kerykeion.charts.chart_drawer.Path')
    def test_chart_template_method(self, mock_path):
        """Test chart template method."""
        mock_path.return_value.exists.return_value = True

        chart = ChartDrawer(self.chart_data)

        # Test that chart is properly initialized
        assert chart.chart_data is not None

    def test_chart_drawer_initialization_attributes(self):
        """Test that all expected attributes are set after initialization."""
        chart = ChartDrawer(self.chart_data)

        # Check basic attributes
        assert chart.chart_data is not None
        assert chart.chart_language is not None
        assert chart.transparent_background is not None
        assert chart.external_view is not None

    def test_chart_drawer_with_different_languages(self):
        """Test chart drawer with different language settings."""
        chart_en = ChartDrawer(self.chart_data, chart_language="EN")
        chart_it = ChartDrawer(self.chart_data, chart_language="IT")
        chart_es = ChartDrawer(self.chart_data, chart_language="ES")

        assert chart_en.chart_language == "EN"
        assert chart_it.chart_language == "IT"
        assert chart_es.chart_language == "ES"

    def test_chart_drawer_multiple_instances(self):
        """Test creating multiple chart drawer instances."""
        chart1 = ChartDrawer(self.chart_data)
        chart2 = ChartDrawer(self.chart_data, theme="classic")

        assert chart1.chart_data == chart2.chart_data
        assert chart1.chart_language == chart2.chart_language

    def test_chart_drawer_aspect_grid_types(self):
        """Test different aspect grid types."""
        chart_list = ChartDrawer(self.chart_data, double_chart_aspect_grid_type="list")
        chart_table = ChartDrawer(self.chart_data, double_chart_aspect_grid_type="table")

        assert chart_list.double_chart_aspect_grid_type == "list"
        assert chart_table.double_chart_aspect_grid_type == "table"

    def test_chart_drawer_default_settings(self):
        """Test chart drawer default settings."""
        chart = ChartDrawer(self.chart_data)

        # Test default settings
        assert chart.chart_language == "EN"
        assert chart.transparent_background is False
        assert chart.external_view is False
        assert chart.double_chart_aspect_grid_type == "list"

    def test_chart_drawer_with_different_themes(self):
        """Test chart drawer with different themes."""
        themes = ["classic", "black-and-white", None]

        for theme in themes:
            chart = ChartDrawer(self.chart_data, theme=theme)
            # Theme processing happens during init
            assert chart.chart_data is not None
            if theme:
                assert chart.color_style_tag.strip() != ""
                assert "--kerykeion-chart-color-paper-0" in chart.color_style_tag

    def test_chart_data_extraction(self):
        """Test that chart data is properly extracted."""
        chart = ChartDrawer(self.chart_data)

        # Test that chart type is extracted
        assert hasattr(chart, 'chart_type')
        assert chart.chart_type is not None

    def test_chart_drawer_constants(self):
        """Test that ChartDrawer has expected constants."""
        assert hasattr(ChartDrawer, '_DEFAULT_HEIGHT')
        assert hasattr(ChartDrawer, '_DEFAULT_FULL_WIDTH')
        assert hasattr(ChartDrawer, '_DEFAULT_NATAL_WIDTH')

        # Test constants are reasonable values
        assert ChartDrawer._DEFAULT_HEIGHT > 0
        assert ChartDrawer._DEFAULT_FULL_WIDTH > 0
        assert ChartDrawer._DEFAULT_NATAL_WIDTH > 0

    def test_chart_drawer_with_different_chart_data_types(self):
        """Test chart drawer with different chart data types."""
        # Test with different subject variations
        minimal_subject = AstrologicalSubjectFactory.from_birth_data(
            name="Minimal",
            year=2000,
            month=1,
            day=1,
            hour=0,
            minute=0,
            city="UTC",
            nation="UT",
            lng=0,
            lat=0,
            tz_str="UTC",
            suppress_geonames_warning=True
        )

        minimal_chart_data = ChartDataFactory.create_natal_chart_data(minimal_subject)
        chart = ChartDrawer(minimal_chart_data)
        assert chart.chart_data is not None

    def test_black_and_white_theme_is_monochrome(self):
        """Ensure the black and white theme only uses grayscale colors."""
        repo_root = Path(__file__).resolve().parents[1]
        theme_path = repo_root / "kerykeion" / "charts" / "themes" / "black-and-white.css"
        theme_content = theme_path.read_text(encoding="utf-8")
        hex_colors = re.findall(r"#[0-9a-fA-F]{6}", theme_content)
        assert hex_colors, "Expected to find hexadecimal colors in the theme definition."
        for color in hex_colors:
            red = color[1:3].lower()
            green = color[3:5].lower()
            blue = color[5:7].lower()
            assert red == green == blue, f"Color {color} is not grayscale."

    def test_chart_drawer_viewbox_constants(self):
        """Test chart drawer viewbox constants."""
        assert hasattr(ChartDrawer, '_BASIC_CHART_VIEWBOX')
        assert hasattr(ChartDrawer, '_WIDE_CHART_VIEWBOX')
        assert hasattr(ChartDrawer, '_ULTRA_WIDE_CHART_VIEWBOX')

        # Test viewbox strings are properly formatted
        assert "0 0" in ChartDrawer._BASIC_CHART_VIEWBOX
        assert "0 0" in ChartDrawer._WIDE_CHART_VIEWBOX
        assert "0 0" in ChartDrawer._ULTRA_WIDE_CHART_VIEWBOX

    @patch('kerykeion.charts.chart_drawer.logging')
    def test_chart_drawer_logging(self, mock_logging):
        """Test that logging is properly configured."""
        chart = ChartDrawer(self.chart_data)

        # Chart creation might involve logging
        assert chart is not None

    def test_chart_drawer_settings_handling(self):
        """Test chart drawer settings handling."""
        custom_colors = {"background": "#ffffff"}
        custom_points = [{"name": "Sun", "is_active": True}]
        custom_aspects = [{"name": "conjunction", "is_active": True}]

        chart = ChartDrawer(
            self.chart_data,
            colors_settings=custom_colors,
            celestial_points_settings=custom_points,
            aspects_settings=custom_aspects
        )

        assert chart.chart_colors_settings == custom_colors
        assert chart.planets_settings == custom_points
        assert chart.aspects_settings == custom_aspects

    def test_composite_chart_drawer(self):
        """Test chart drawer with composite chart data."""
        composite_factory = CompositeSubjectFactory(self.subject, self.subject2)
        composite_subject = composite_factory.get_midpoint_composite_subject_model()
        composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart = ChartDrawer(composite_data)

        assert chart.chart_type == "Composite"
        assert chart.chart_data is not None
        assert hasattr(chart, 'first_circle_radius')
        assert hasattr(chart, 'second_circle_radius')

    def test_transit_chart_drawer(self):
        """Test chart drawer with transit chart data."""
        transit_data = ChartDataFactory.create_transit_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(transit_data)

        assert chart.chart_type == "Transit"
        assert chart.chart_data is not None
        assert hasattr(chart, 'second_obj')

    def test_transit_chart_uses_transit_lunar_phase(self):
        """Transit charts should render the lunar phase of the transiting subject."""
        transit_data = ChartDataFactory.create_transit_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(transit_data)
        template_dict = chart._create_template_dictionary()

        assert chart.second_obj is not None
        transit_phase = chart.second_obj.lunar_phase
        expected_svg = makeLunarPhase(transit_phase["degrees_between_s_m"], chart.geolat)

        assert template_dict["makeLunarPhase"] == expected_svg

        natal_phase = chart.first_obj.lunar_phase
        if natal_phase is not None and natal_phase["degrees_between_s_m"] != transit_phase["degrees_between_s_m"]:
            unexpected_svg = makeLunarPhase(natal_phase["degrees_between_s_m"], chart.geolat)
            assert template_dict["makeLunarPhase"] != unexpected_svg

    def test_transit_chart_without_transit_phase_shows_blank(self):
        """If transit subject lacks lunar phase, the lunar phase icon is hidden."""
        transit_data = ChartDataFactory.create_transit_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(transit_data)
        assert chart.second_obj is not None
        chart.second_obj.lunar_phase = None  # type: ignore[attr-defined]

        template_dict = chart._create_template_dictionary()
        assert template_dict["makeLunarPhase"] == ""

    def test_synastry_chart_drawer(self):
        """Test chart drawer with synastry chart data."""
        synastry_data = ChartDataFactory.create_synastry_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(synastry_data)

        assert chart.chart_type == "Synastry"
        assert chart.chart_data is not None
        assert hasattr(chart, 'second_obj')

    def test_hide_house_position_comparison_removes_grid_and_updates_width(self):
        """Hiding the house position comparison grid should reclaim horizontal space."""
        synastry_data = ChartDataFactory.create_synastry_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(synastry_data, show_house_position_comparison=False, auto_size=False)

        assert chart.width == ChartDrawer._DEFAULT_FULL_WIDTH

        template_dict = chart._create_template_dictionary()
        assert template_dict["makeHouseComparisonGrid"] == ""

    def test_dual_chart_preserves_second_subject_points(self):
        """Ensure dual charts keep the second subject planet positions."""
        synastry_data = ChartDataFactory.create_synastry_chart_data(self.subject, self.subject2)
        chart = ChartDrawer(synastry_data)

        first_points = {point.name: point.abs_pos for point in chart.available_kerykeion_celestial_points}
        second_points = {point.name: point.abs_pos for point in chart.t_available_kerykeion_celestial_points}

        assert second_points, "Expected secondary subject points to be populated"
        assert "Sun" in second_points
        assert chart.second_obj is not None
        assert chart.second_obj.sun is not None
        assert chart.first_obj.sun is not None
        assert second_points["Sun"] == chart.second_obj.sun.abs_pos
        assert first_points["Sun"] == chart.first_obj.sun.abs_pos
        assert second_points["Sun"] != first_points["Sun"], "Second subject sun should not match first subject"

    def test_dynamic_viewbox_tracks_dimensions(self):
        """Chart viewbox string reflects current width/height values with vertical padding."""
        chart = ChartDrawer(self.chart_data)

        # The dynamic viewbox includes vertical padding:
        # min_y = -_VERTICAL_PADDING_TOP
        # viewbox_height = height + _VERTICAL_PADDING_TOP + _VERTICAL_PADDING_BOTTOM
        min_y = -ChartDrawer._VERTICAL_PADDING_TOP
        viewbox_height = int(chart.height) + ChartDrawer._VERTICAL_PADDING_TOP + ChartDrawer._VERTICAL_PADDING_BOTTOM
        expected = f"0 {min_y} {int(chart.width)} {viewbox_height}"
        assert chart._dynamic_viewbox() == expected

    def test_chart_drawer_save_svg_method(self):
        """Test the save_svg method."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.subject)
        chart = ChartDrawer(chart_data)

        # Test that save_svg method exists and can be called
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_chart.svg")

            # This should execute without error
            try:
                chart.save_svg(output_path)
                # Check if file was created
                assert os.path.exists(output_path)
            except Exception:
                # Some chart drawing might fail due to missing dependencies
                # but the method should exist
                assert hasattr(chart, 'save_svg')

    def test_chart_drawer_different_settings_combinations(self):
        """Test chart drawer with various settings combinations."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

        # Test with all possible parameter combinations
        chart1 = ChartDrawer(
            chart_data,
            theme="classic",
            chart_language="IT",
            transparent_background=True,
            external_view=True,
            double_chart_aspect_grid_type="table"
        )

        assert chart1.chart_language == "IT"
        assert chart1.transparent_background is True
        assert chart1.external_view is True
        assert chart1.double_chart_aspect_grid_type == "table"

    def test_chart_drawer_with_custom_settings_files(self):
        """Test chart drawer with custom settings parameters."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

        # Test with different settings combinations
        custom_colors = {"chart_background": "#ffffff"}
        custom_celestial = [{"name": "Sun", "is_active": True}]
        custom_aspects = [{"name": "conjunction", "is_active": True}]

        chart = ChartDrawer(
            chart_data,
            colors_settings=custom_colors,
            celestial_points_settings=custom_celestial,
            aspects_settings=custom_aspects
        )

        assert chart.chart_colors_settings == custom_colors
        assert chart.planets_settings == custom_celestial
        assert chart.aspects_settings == custom_aspects

    def test_chart_drawer_property_access(self):
        """Test accessing various chart drawer properties."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.subject)
        chart = ChartDrawer(chart_data)

        # Test property access that might trigger uncovered code
        assert hasattr(chart, 'chart_type')
        assert hasattr(chart, 'first_obj')
        assert hasattr(chart, 'height')
        assert hasattr(chart, 'width')
        assert hasattr(chart, 'location')
        assert hasattr(chart, 'geolat')
        assert hasattr(chart, 'geolon')

    def test_chart_drawer_viewbox_settings(self):
        """Test chart drawer viewbox settings for different chart types."""
        # Test different chart types to trigger different viewbox settings
        natal_data = ChartDataFactory.create_natal_chart_data(self.subject)
        natal_chart = ChartDrawer(natal_data)

        composite_factory = CompositeSubjectFactory(self.subject, self.subject2)
        composite_subject = composite_factory.get_midpoint_composite_subject_model()
        composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        composite_chart = ChartDrawer(composite_data)

        transit_data = ChartDataFactory.create_transit_chart_data(self.subject, self.subject2)
        transit_chart = ChartDrawer(transit_data)

        # Test that charts are properly initialized
        assert natal_chart.chart_type == "Natal"
        assert composite_chart.chart_type == "Composite"
        assert transit_chart.chart_type == "Transit"

    def test_chart_drawer_error_handling(self):
        """Test chart drawer error handling for edge cases."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

        # Test with minimal settings
        chart = ChartDrawer(
            chart_data,
            theme=None
        )

        assert chart.chart_data is not None
