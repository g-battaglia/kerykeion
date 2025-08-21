import pytest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path
import tempfile
import os

from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.schemas.kr_models import AstrologicalSubjectModel


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
            tz_str="America/New_York"
        )

        # Create chart data for drawing
        self.chart_data = ChartDataFactory.create_natal_chart_data(self.subject)

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
        themes = ["classic", None]

        for theme in themes:
            chart = ChartDrawer(self.chart_data, theme=theme)
            # Theme processing happens during init
            assert chart.chart_data is not None

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
            tz_str="UTC"
        )

        minimal_chart_data = ChartDataFactory.create_natal_chart_data(minimal_subject)
        chart = ChartDrawer(minimal_chart_data)
        assert chart.chart_data is not None

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
