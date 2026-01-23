# -*- coding: utf-8 -*-
"""
Comprehensive Chart SVG Tests for Kerykeion

This module tests the SVG chart generation functionality by comparing generated
charts against baseline SVG files. It covers all chart types, themes, house systems,
sidereal modes, languages, and various ChartDrawer configuration options.

Test Organization:
==================

1. CORE CHART TYPES
   - Natal Charts (standard, external view, minified)
   - Synastry Charts (with various comparison options)
   - Transit Charts (with various comparison options)
   - Composite Charts
   - Return Charts (Solar/Lunar, Single/Dual wheel)

2. THEMES
   - Classic (default), Dark, Light, Black-and-White

3. SIDEREAL MODES (Ayanamsa)
   - All 20 sidereal modes supported by Swiss Ephemeris

4. HOUSE SYSTEMS
   - All 23 house systems (Placidus, Koch, Whole Sign, etc.)

5. LANGUAGES
   - 10 supported languages (EN, FR, DE, IT, ES, PT, RU, TR, CN, HI)

6. OUTPUT FORMATS
   - Full chart, Wheel-only, Aspect-grid-only

7. CHARTDRAWER OPTIONS
   - Custom title, padding, aspect icons, auto-size, CSS variables, etc.

8. PERSPECTIVE TYPES
   - Apparent Geocentric, Heliocentric, Topocentric, True Geocentric

Usage:
======
    pytest tests/charts/test_charts.py -v

To regenerate baseline SVGs:
    python scripts/regenerate_test_charts.py
"""

from pathlib import Path
from typing import Optional

from kerykeion import AstrologicalSubjectFactory, ChartDrawer, CompositeSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

from .compare_svg_lines import compare_svg_lines


class TestCharts:
    """
    Comprehensive test suite for Kerykeion chart SVG generation.

    This class tests all possible chart configurations by comparing generated
    SVG output against baseline files stored in tests/charts/svg/.

    Attributes:
        SVG_DIR: Path to the directory containing baseline SVG files.
        JOHN_LENNON_BIRTH_DATA: Common birth data tuple for John Lennon tests.
        PAUL_MCCARTNEY_BIRTH_DATA: Common birth data tuple for Paul McCartney tests.
    """

    SVG_DIR = Path(__file__).parent / "svg"

    # Common birth data constants to reduce repetition
    # Format: (name, year, month, day, hour, minute, city, country)
    JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30, "Liverpool", "GB")
    PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30, "Liverpool", "GB")

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _compare_chart_svg(self, file_name: str, chart_svg: str) -> None:
        """
        Compare generated SVG content against a baseline file.

        Args:
            file_name: Name of the baseline SVG file in SVG_DIR.
            chart_svg: Generated SVG string to compare.

        Raises:
            AssertionError: If line counts differ or any line doesn't match.
        """
        chart_svg_lines = chart_svg.splitlines()

        with open(self.SVG_DIR / file_name, "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        assert len(chart_svg_lines) == len(file_content_lines), (
            f"Line count mismatch in {file_name}: Expected {len(file_content_lines)} lines, got {len(chart_svg_lines)}"
        )

        for expected_line, actual_line in zip(file_content_lines, chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def _create_john_lennon_subject(
        self,
        name_suffix: str = "",
        *,
        zodiac_type: str = "Tropical",
        sidereal_mode: Optional[str] = None,
        houses_system_identifier: str = "P",
        perspective_type: str = "Apparent Geocentric",
        active_points: Optional[list] = None,
    ):
        """
        Create a John Lennon astrological subject with custom parameters.

        Args:
            name_suffix: Suffix to append to "John Lennon" name.
            zodiac_type: "Tropical" or "Sidereal".
            sidereal_mode: Sidereal mode (e.g., "LAHIRI", "FAGAN_BRADLEY").
            houses_system_identifier: House system letter (e.g., "P" for Placidus).
            perspective_type: Perspective type (e.g., "Heliocentric").
            active_points: List of active points to include.

        Returns:
            AstrologicalSubjectModel: Configured subject for testing.
        """
        name = f"John Lennon{' - ' + name_suffix if name_suffix else ''}"
        kwargs = {
            "suppress_geonames_warning": True,
            "zodiac_type": zodiac_type,
            "houses_system_identifier": houses_system_identifier,
            "perspective_type": perspective_type,
        }
        if sidereal_mode:
            kwargs["sidereal_mode"] = sidereal_mode
        if active_points:
            kwargs["active_points"] = active_points

        return AstrologicalSubjectFactory.from_birth_data(name, *self.JOHN_LENNON_BIRTH_DATA, **kwargs)

    def _create_return_factory(self):
        """Create a PlanetaryReturnFactory for John Lennon with offline settings."""
        return PlanetaryReturnFactory(
            self.first_subject,
            lng=-2.9833,
            lat=53.4000,
            tz_str="Europe/London",
            online=False,
        )

    # =========================================================================
    # TEST FIXTURES
    # =========================================================================

    @classmethod
    def setup_class(cls):
        """
        Initialize all test subjects used across the test suite.

        Subjects are organized by category for clarity and maintainability.
        """
        # -----------------------------------------------------------------
        # Primary Test Subjects
        # -----------------------------------------------------------------
        cls.first_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.second_subject = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney", *cls.PAUL_MCCARTNEY_BIRTH_DATA, suppress_geonames_warning=True
        )

        # -----------------------------------------------------------------
        # Sidereal Mode Subjects (for existing tests)
        # -----------------------------------------------------------------
        cls.lahiri_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon Lahiri",
            *cls.JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            suppress_geonames_warning=True,
        )
        cls.fagan_bradley_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon Fagan-Bradley",
            *cls.JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="FAGAN_BRADLEY",
            suppress_geonames_warning=True,
        )
        cls.deluce_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon DeLuce",
            *cls.JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="DELUCE",
            suppress_geonames_warning=True,
        )
        cls.j2000_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon J2000",
            *cls.JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="J2000",
            suppress_geonames_warning=True,
        )

        # Sidereal subjects with themes
        cls.sidereal_dark_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon Lahiri - Dark Theme",
            *cls.JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            suppress_geonames_warning=True,
        )
        cls.sidereal_light_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon Fagan-Bradley - Light Theme",
            *cls.JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="FAGAN_BRADLEY",
            suppress_geonames_warning=True,
        )

        # -----------------------------------------------------------------
        # House System Subject (Morinus - others created inline)
        # -----------------------------------------------------------------
        cls.morinus_house_system_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - House System Morinus",
            *cls.JOHN_LENNON_BIRTH_DATA,
            houses_system_identifier="M",
            suppress_geonames_warning=True,
        )

        # -----------------------------------------------------------------
        # Perspective Type Subjects
        # -----------------------------------------------------------------
        cls.heliocentric_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Heliocentric",
            *cls.JOHN_LENNON_BIRTH_DATA,
            perspective_type="Heliocentric",
            suppress_geonames_warning=True,
        )
        cls.topocentric_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Topocentric",
            *cls.JOHN_LENNON_BIRTH_DATA,
            perspective_type="Topocentric",
            suppress_geonames_warning=True,
        )
        cls.true_geocentric_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - True Geocentric",
            *cls.JOHN_LENNON_BIRTH_DATA,
            perspective_type="True Geocentric",
            suppress_geonames_warning=True,
        )

        # -----------------------------------------------------------------
        # Theme Test Subjects
        # -----------------------------------------------------------------
        cls.minified_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Minified", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.dark_theme_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Dark Theme", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.dark_high_contrast_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Dark High Contrast Theme", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.light_theme_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Light Theme", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.dark_theme_external_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Dark Theme External", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.dark_theme_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - DTS", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )

        # -----------------------------------------------------------------
        # Wheel-Only Test Subjects
        # -----------------------------------------------------------------
        cls.wheel_only_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.wheel_external_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel External Only", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.wheel_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Synastry Only", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.wheel_transit_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Transit Only", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )

        # -----------------------------------------------------------------
        # Aspect Grid Test Subjects
        # -----------------------------------------------------------------
        cls.aspect_grid_only_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Only", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.aspect_grid_dark_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Dark Theme", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.aspect_grid_light_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Light Theme", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.aspect_grid_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Synastry", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.aspect_grid_transit_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Transit", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.aspect_grid_dark_synastry_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Dark Synastry", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        cls.transit_table_grid_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - TCWTG", *cls.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )

        # -----------------------------------------------------------------
        # All Active Points Subjects
        # -----------------------------------------------------------------
        cls.all_active_points_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - All Active Points",
            *cls.JOHN_LENNON_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=ALL_ACTIVE_POINTS,
        )
        cls.all_active_points_second_subject = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - All Active Points",
            *cls.PAUL_MCCARTNEY_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=ALL_ACTIVE_POINTS,
        )

        # -----------------------------------------------------------------
        # Language Test Subjects (various celebrities)
        # -----------------------------------------------------------------
        cls.chinese_subject = AstrologicalSubjectFactory.from_birth_data(
            "Hua Chenyu", 1990, 2, 7, 12, 0, "Hunan", "CN", suppress_geonames_warning=True
        )
        cls.french_subject = AstrologicalSubjectFactory.from_birth_data(
            "Jeanne Moreau", 1928, 1, 23, 10, 0, "Paris", "FR", suppress_geonames_warning=True
        )
        cls.spanish_subject = AstrologicalSubjectFactory.from_birth_data(
            "Antonio Banderas", 1960, 8, 10, 12, 0, "Malaga", "ES", suppress_geonames_warning=True
        )
        cls.portuguese_subject = AstrologicalSubjectFactory.from_birth_data(
            "Cristiano Ronaldo", 1985, 2, 5, 5, 25, "Funchal", "PT", suppress_geonames_warning=True
        )
        cls.italian_subject = AstrologicalSubjectFactory.from_birth_data(
            "Sophia Loren", 1934, 9, 20, 2, 0, "Rome", "IT", suppress_geonames_warning=True
        )
        cls.russian_subject = AstrologicalSubjectFactory.from_birth_data(
            "Mikhail Bulgakov", 1891, 5, 15, 12, 0, "Kiev", "UA", suppress_geonames_warning=True
        )
        cls.turkish_subject = AstrologicalSubjectFactory.from_birth_data(
            "Mehmet Oz", 1960, 6, 11, 12, 0, "Istanbul", "TR", suppress_geonames_warning=True
        )
        cls.german_subject = AstrologicalSubjectFactory.from_birth_data(
            "Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE", suppress_geonames_warning=True
        )
        cls.hindi_subject = AstrologicalSubjectFactory.from_birth_data(
            "Amitabh Bachchan", 1942, 10, 11, 4, 0, "Allahabad", "IN", suppress_geonames_warning=True
        )

        # -----------------------------------------------------------------
        # Composite Chart Subjects
        # -----------------------------------------------------------------
        cls.angelina_jolie = AstrologicalSubjectFactory.from_birth_data(
            "Angelina Jolie",
            1975,
            6,
            4,
            9,
            9,
            "Los Angeles",
            "US",
            lng=-118.15,
            lat=34.03,
            tz_str="America/Los_Angeles",
            suppress_geonames_warning=True,
        )
        cls.brad_pitt = AstrologicalSubjectFactory.from_birth_data(
            "Brad Pitt",
            1963,
            12,
            18,
            6,
            31,
            "Shawnee",
            "US",
            lng=-96.56,
            lat=35.20,
            tz_str="America/Chicago",
            suppress_geonames_warning=True,
        )

    def _create_sidereal_subject(self, name_suffix: str, sidereal_mode: str):
        """Helper to create sidereal subjects with consistent naming."""
        return AstrologicalSubjectFactory.from_birth_data(
            f"John Lennon {name_suffix}",
            *self.JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode=sidereal_mode,
            suppress_geonames_warning=True,
        )

    # =========================================================================
    # SECTION 1: CORE NATAL CHART TESTS
    # =========================================================================

    def test_natal_chart(self):
        """Test basic natal chart generation."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.first_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - Natal Chart.svg", chart_svg)

    def test_natal_chart_from_model(self):
        """Test natal chart generation from model (duplicate for compatibility)."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.first_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - Natal Chart.svg", chart_svg)

    def test_external_natal_chart(self):
        """Test natal chart with external view (planets on outer ring)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - ExternalNatal", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, external_view=True).generate_svg_string()
        self._compare_chart_svg("John Lennon - ExternalNatal - Natal Chart.svg", chart_svg)

    def test_minified_natal_chart(self):
        """Test minified SVG output."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.minified_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string(minify=True)
        self._compare_chart_svg("John Lennon - Minified - Natal Chart.svg", chart_svg)

    # =========================================================================
    # SECTION 2: SYNASTRY CHART TESTS
    # =========================================================================

    def test_synastry_chart(self):
        """Test basic synastry chart."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - Synastry Chart.svg", chart_svg)

    def test_synastry_chart_without_house_comparison_grid(self):
        """Test synastry chart with no house/cusp comparison."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Synastry Chart - No House Comparison.svg", chart_svg)

    def test_synastry_chart_with_house_comparison_only(self):
        """Test synastry chart with house comparison only."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Synastry Chart - House Comparison Only.svg", chart_svg)

    def test_synastry_chart_with_cusp_comparison_only(self):
        """Test synastry chart with cusp comparison only."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Synastry Chart - Cusp Comparison Only.svg", chart_svg)

    def test_synastry_chart_with_house_and_cusp_comparison(self):
        """Test synastry chart with both house and cusp comparison."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Synastry Chart - House and Cusp Comparison.svg", chart_svg)

    # =========================================================================
    # SECTION 3: TRANSIT CHART TESTS
    # =========================================================================

    def test_transit_chart(self):
        """Test basic transit chart."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - Transit Chart.svg", chart_svg)

    def test_transit_chart_without_house_comparison_grid(self):
        """Test transit chart with no house/cusp comparison."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Transit Chart - No House Comparison.svg", chart_svg)

    def test_transit_chart_with_house_comparison_only(self):
        """Test transit chart with house comparison only."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Transit Chart - House Comparison Only.svg", chart_svg)

    def test_transit_chart_with_cusp_comparison_only(self):
        """Test transit chart with cusp comparison only."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Transit Chart - Cusp Comparison Only.svg", chart_svg)

    def test_transit_chart_with_house_and_cusp_comparison(self):
        """Test transit chart with both house and cusp comparison."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Transit Chart - House and Cusp Comparison.svg", chart_svg)

    def test_transit_chart_with_table_grid(self):
        """Test transit chart with table grid layout for aspects."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.transit_table_grid_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, double_chart_aspect_grid_type="table", theme="dark").generate_svg_string()
        self._compare_chart_svg("John Lennon - TCWTG - Transit Chart.svg", chart_svg)

    # =========================================================================
    # SECTION 4: COMPOSITE CHART TESTS
    # =========================================================================

    def test_composite_chart(self):
        """Test basic composite chart."""
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart.svg", chart_svg)

    def test_black_and_white_composite_chart(self):
        """Test composite chart with black-and-white theme."""
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Black and White Theme - Composite Chart.svg", chart_svg
        )

    def test_composite_chart_wheel_only(self):
        """Test composite chart wheel-only output."""
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        self._compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Composite Chart - Wheel Only.svg", chart_svg
        )

    def test_composite_chart_aspect_grid_only(self):
        """Test composite chart aspect-grid-only output."""
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        self._compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Composite Chart - Aspect Grid Only.svg", chart_svg
        )

    def test_light_theme_composite_chart(self):
        """Test composite chart with light theme."""
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_svg_string()
        self._compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Light Theme - Composite Chart.svg", chart_svg
        )

    def test_dark_theme_composite_chart(self):
        """Test composite chart with dark theme."""
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        self._compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Dark Theme - Composite Chart.svg", chart_svg
        )

    # =========================================================================
    # SECTION 5: RETURN CHART TESTS (Solar & Lunar)
    # =========================================================================

    def test_dual_return_solar_chart(self):
        """Test dual return chart (Natal + Solar Return)."""
        return_factory = self._create_return_factory()
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(self.first_subject, solar_return)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return.svg", chart_svg)

        # Test with no house comparison
        chart_svg = ChartDrawer(chart_data, show_house_position_comparison=False).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Solar Return - No House Comparison.svg", chart_svg
        )

        # Test with house comparison only
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Solar Return - House Comparison Only.svg", chart_svg
        )

        # Test with cusp comparison only
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Solar Return - Cusp Comparison Only.svg", chart_svg
        )

        # Test with both comparisons
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Solar Return - House and Cusp Comparison.svg", chart_svg
        )

    def test_black_and_white_dual_return_chart(self):
        """Test dual return chart with black-and-white theme."""
        return_factory = self._create_return_factory()
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(self.first_subject, solar_return)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - Black and White Theme - DualReturnChart Chart - Solar Return.svg", chart_svg
        )

    def test_single_return_solar_chart(self):
        """Test single wheel return chart (Solar Return only)."""
        return_factory = self._create_return_factory()
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Solar Return - SingleReturnChart Chart.svg", chart_svg)

    def test_black_and_white_single_return_chart(self):
        """Test single return chart with black-and-white theme."""
        return_factory = self._create_return_factory()
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg(
            "John Lennon Solar Return - Black and White Theme - SingleReturnChart Chart.svg", chart_svg
        )

    def test_dual_return_lunar_chart(self):
        """Test dual return chart (Natal + Lunar Return)."""
        return_factory = self._create_return_factory()
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(self.first_subject, lunar_return)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return.svg", chart_svg)

        # Test with no house comparison
        chart_svg = ChartDrawer(chart_data, show_house_position_comparison=False).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Lunar Return - No House Comparison.svg", chart_svg
        )

        # Test with house comparison only
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Lunar Return - House Comparison Only.svg", chart_svg
        )

        # Test with cusp comparison only
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Lunar Return - Cusp Comparison Only.svg", chart_svg
        )

        # Test with both comparisons
        chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=True,
            show_cusp_position_comparison=True,
        ).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Lunar Return - House and Cusp Comparison.svg", chart_svg
        )

    def test_single_return_lunar_chart(self):
        """Test single wheel return chart (Lunar Return only)."""
        return_factory = self._create_return_factory()
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Lunar Return - SingleReturnChart Chart.svg", chart_svg)

    def test_black_and_white_dual_lunar_return(self):
        """Test dual lunar return chart with black-and-white theme."""
        return_factory = self._create_return_factory()
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_return_chart_data(self.first_subject, lunar_return)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - Black and White Theme - DualReturnChart Chart - Lunar Return.svg", chart_svg
        )

    def test_black_and_white_single_lunar_return(self):
        """Test single lunar return chart with black-and-white theme."""
        return_factory = self._create_return_factory()
        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Lunar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg(
            "John Lennon Lunar Return - Black and White Theme - SingleReturnChart Chart.svg", chart_svg
        )

    def test_return_chart_wheel_only(self):
        """Test solar return chart wheel-only output."""
        return_factory = self._create_return_factory()
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon Solar Return - Wheel Only.svg", chart_svg)

    def test_return_chart_aspect_grid_only(self):
        """Test solar return chart aspect-grid-only output."""
        return_factory = self._create_return_factory()
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00", return_type="Solar"
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon Solar Return - Aspect Grid Only.svg", chart_svg)

    # =========================================================================
    # SECTION 6: THEME TESTS
    # =========================================================================

    def test_dark_theme_natal_chart(self):
        """Test natal chart with dark theme."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.dark_theme_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        self._compare_chart_svg("John Lennon - Dark Theme - Natal Chart.svg", chart_svg)

    def test_dark_high_contrast_theme_natal_chart(self):
        """Test natal chart with dark high contrast theme."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.dark_high_contrast_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark-high-contrast").generate_svg_string()
        self._compare_chart_svg("John Lennon - Dark High Contrast Theme - Natal Chart.svg", chart_svg)

    def test_light_theme_natal_chart(self):
        """Test natal chart with light theme."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.light_theme_subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_svg_string()
        self._compare_chart_svg("John Lennon - Light Theme - Natal Chart.svg", chart_svg)

    def test_black_and_white_natal_chart(self):
        """Test natal chart with black-and-white theme."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.first_subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg("John Lennon - Black and White Theme - Natal Chart.svg", chart_svg)

    def test_black_and_white_synastry_chart(self):
        """Test synastry chart with black-and-white theme."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg("John Lennon - Black and White Theme - Synastry Chart.svg", chart_svg)

    def test_black_and_white_transit_chart(self):
        """Test transit chart with black-and-white theme."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg("John Lennon - Black and White Theme - Transit Chart.svg", chart_svg)

    def test_dark_theme_external_natal_chart(self):
        """Test external natal chart with dark theme."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.dark_theme_external_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark", external_view=True).generate_svg_string()
        self._compare_chart_svg("John Lennon - Dark Theme External - Natal Chart.svg", chart_svg)

    def test_dark_theme_synastry_chart(self):
        """Test synastry chart with dark theme."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.dark_theme_synastry_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        self._compare_chart_svg("John Lennon - DTS - Synastry Chart.svg", chart_svg)

    def test_light_theme_synastry_chart(self):
        """Test synastry chart with light theme."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_svg_string()
        self._compare_chart_svg("John Lennon - Light Theme - Synastry Chart.svg", chart_svg)

    def test_light_theme_transit_chart(self):
        """Test transit chart with light theme."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_svg_string()
        self._compare_chart_svg("John Lennon - Light Theme - Transit Chart.svg", chart_svg)

    def test_dark_theme_transit_chart(self):
        """Test transit chart with dark theme."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        self._compare_chart_svg("John Lennon - Dark Theme - Transit Chart.svg", chart_svg)

    def test_light_theme_external_natal_chart(self):
        """Test external natal chart with light theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Light Theme External", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="light", external_view=True).generate_svg_string()
        self._compare_chart_svg("John Lennon - Light Theme External - Natal Chart.svg", chart_svg)

    def test_black_and_white_external_natal_chart(self):
        """Test external natal chart with black-and-white theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Black and White Theme External", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white", external_view=True).generate_svg_string()
        self._compare_chart_svg("John Lennon - Black and White Theme External - Natal Chart.svg", chart_svg)

    def test_transparent_background_natal_chart(self):
        """Test natal chart with transparent background."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Transparent Background", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, transparent_background=True).generate_svg_string()
        self._compare_chart_svg("John Lennon - Transparent Background - Natal Chart.svg", chart_svg)

    # =========================================================================
    # SECTION 7: SIDEREAL MODES (AYANAMSA) TESTS
    # All 20 sidereal modes supported by Swiss Ephemeris
    # =========================================================================

    def test_lahiri_birth_chart(self):
        """Test sidereal chart using Lahiri ayanamsa."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.lahiri_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Lahiri - Natal Chart.svg", chart_svg)

    def test_fagan_bradley_birth_chart(self):
        """Test sidereal chart using Fagan-Bradley ayanamsa."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.fagan_bradley_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Fagan-Bradley - Natal Chart.svg", chart_svg)

    def test_deluce_birth_chart(self):
        """Test sidereal chart using DeLuce ayanamsa."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.deluce_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon DeLuce - Natal Chart.svg", chart_svg)

    def test_j2000_birth_chart(self):
        """Test sidereal chart using J2000 ayanamsa."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.j2000_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon J2000 - Natal Chart.svg", chart_svg)

    def test_raman_birth_chart(self):
        """Test sidereal chart using Raman ayanamsa."""
        subject = self._create_sidereal_subject("Raman", "RAMAN")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Raman - Natal Chart.svg", chart_svg)

    def test_ushashashi_birth_chart(self):
        """Test sidereal chart using Ushashashi ayanamsa."""
        subject = self._create_sidereal_subject("Ushashashi", "USHASHASHI")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Ushashashi - Natal Chart.svg", chart_svg)

    def test_krishnamurti_birth_chart(self):
        """Test sidereal chart using Krishnamurti ayanamsa."""
        subject = self._create_sidereal_subject("Krishnamurti", "KRISHNAMURTI")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Krishnamurti - Natal Chart.svg", chart_svg)

    def test_djwhal_khul_birth_chart(self):
        """Test sidereal chart using Djwhal Khul ayanamsa."""
        subject = self._create_sidereal_subject("Djwhal Khul", "DJWHAL_KHUL")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Djwhal Khul - Natal Chart.svg", chart_svg)

    def test_yukteshwar_birth_chart(self):
        """Test sidereal chart using Yukteshwar ayanamsa."""
        subject = self._create_sidereal_subject("Yukteshwar", "YUKTESHWAR")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Yukteshwar - Natal Chart.svg", chart_svg)

    def test_jn_bhasin_birth_chart(self):
        """Test sidereal chart using JN Bhasin ayanamsa."""
        subject = self._create_sidereal_subject("JN Bhasin", "JN_BHASIN")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon JN Bhasin - Natal Chart.svg", chart_svg)

    def test_babyl_kugler1_birth_chart(self):
        """Test sidereal chart using Babylonian Kugler 1 ayanamsa."""
        subject = self._create_sidereal_subject("Babyl Kugler1", "BABYL_KUGLER1")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Babyl Kugler1 - Natal Chart.svg", chart_svg)

    def test_babyl_kugler2_birth_chart(self):
        """Test sidereal chart using Babylonian Kugler 2 ayanamsa."""
        subject = self._create_sidereal_subject("Babyl Kugler2", "BABYL_KUGLER2")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Babyl Kugler2 - Natal Chart.svg", chart_svg)

    def test_babyl_kugler3_birth_chart(self):
        """Test sidereal chart using Babylonian Kugler 3 ayanamsa."""
        subject = self._create_sidereal_subject("Babyl Kugler3", "BABYL_KUGLER3")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Babyl Kugler3 - Natal Chart.svg", chart_svg)

    def test_babyl_huber_birth_chart(self):
        """Test sidereal chart using Babylonian Huber ayanamsa."""
        subject = self._create_sidereal_subject("Babyl Huber", "BABYL_HUBER")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Babyl Huber - Natal Chart.svg", chart_svg)

    def test_babyl_etpsc_birth_chart(self):
        """Test sidereal chart using Babylonian ETPSC ayanamsa."""
        subject = self._create_sidereal_subject("Babyl Etpsc", "BABYL_ETPSC")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Babyl Etpsc - Natal Chart.svg", chart_svg)

    def test_aldebaran_15tau_birth_chart(self):
        """Test sidereal chart using Aldebaran 15 Tau ayanamsa."""
        subject = self._create_sidereal_subject("Aldebaran 15Tau", "ALDEBARAN_15TAU")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Aldebaran 15Tau - Natal Chart.svg", chart_svg)

    def test_hipparchos_birth_chart(self):
        """Test sidereal chart using Hipparchos ayanamsa."""
        subject = self._create_sidereal_subject("Hipparchos", "HIPPARCHOS")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Hipparchos - Natal Chart.svg", chart_svg)

    def test_sassanian_birth_chart(self):
        """Test sidereal chart using Sassanian ayanamsa."""
        subject = self._create_sidereal_subject("Sassanian", "SASSANIAN")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon Sassanian - Natal Chart.svg", chart_svg)

    def test_j1900_birth_chart(self):
        """Test sidereal chart using J1900 ayanamsa."""
        subject = self._create_sidereal_subject("J1900", "J1900")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon J1900 - Natal Chart.svg", chart_svg)

    def test_b1950_birth_chart(self):
        """Test sidereal chart using B1950 ayanamsa."""
        subject = self._create_sidereal_subject("B1950", "B1950")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon B1950 - Natal Chart.svg", chart_svg)

    def test_sidereal_lahiri_dark_wheel_only(self):
        """Test sidereal Lahiri with dark theme wheel-only output."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.sidereal_dark_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon Lahiri - Dark Theme - Natal Chart - Wheel Only.svg", chart_svg)

    def test_sidereal_fagan_bradley_light_wheel_only(self):
        """Test sidereal Fagan-Bradley with light theme wheel-only output."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.sidereal_light_subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon Fagan-Bradley - Light Theme - Natal Chart - Wheel Only.svg", chart_svg)

    # =========================================================================
    # SECTION 8: HOUSE SYSTEMS TESTS
    # All 23 house systems supported by Swiss Ephemeris
    # =========================================================================

    def _test_house_system(self, house_id: str, house_name: str):
        """Helper method to test a specific house system."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            f"John Lennon - House System {house_name}",
            *self.JOHN_LENNON_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg(f"John Lennon - House System {house_name} - Natal Chart.svg", chart_svg)

    def test_morinus_house_system_birth_chart(self):
        """Test natal chart with Morinus house system (M)."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.morinus_house_system_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - House System Morinus - Natal Chart.svg", chart_svg)

    def test_equal_house_system_birth_chart(self):
        """Test natal chart with Equal house system (A)."""
        self._test_house_system("A", "Equal")

    def test_alcabitius_house_system_birth_chart(self):
        """Test natal chart with Alcabitius house system (B)."""
        self._test_house_system("B", "Alcabitius")

    def test_campanus_house_system_birth_chart(self):
        """Test natal chart with Campanus house system (C)."""
        self._test_house_system("C", "Campanus")

    def test_equal_mc_house_system_birth_chart(self):
        """Test natal chart with Equal MC house system (D)."""
        self._test_house_system("D", "Equal MC")

    def test_carter_house_system_birth_chart(self):
        """Test natal chart with Carter poli-equatorial house system (F)."""
        self._test_house_system("F", "Carter")

    def test_horizon_house_system_birth_chart(self):
        """Test natal chart with Horizon/Azimut house system (H)."""
        self._test_house_system("H", "Horizon")

    def test_sunshine_house_system_birth_chart(self):
        """Test natal chart with Sunshine house system (I)."""
        self._test_house_system("I", "Sunshine")

    def test_sunshine_alt_house_system_birth_chart(self):
        """Test natal chart with Sunshine alternative house system (i)."""
        self._test_house_system("i", "Sunshine Alt")

    def test_koch_house_system_birth_chart(self):
        """Test natal chart with Koch house system (K)."""
        self._test_house_system("K", "Koch")

    def test_pullen_sd_house_system_birth_chart(self):
        """Test natal chart with Pullen SD house system (L)."""
        self._test_house_system("L", "Pullen SD")

    def test_equal_aries_house_system_birth_chart(self):
        """Test natal chart with Equal/1=Aries house system (N)."""
        self._test_house_system("N", "Equal Aries")

    def test_porphyry_house_system_birth_chart(self):
        """Test natal chart with Porphyry house system (O)."""
        self._test_house_system("O", "Porphyry")

    def test_placidus_house_system_birth_chart(self):
        """Test natal chart with Placidus house system (P) - default."""
        self._test_house_system("P", "Placidus")

    def test_pullen_sr_house_system_birth_chart(self):
        """Test natal chart with Pullen SR house system (Q)."""
        self._test_house_system("Q", "Pullen SR")

    def test_regiomontanus_house_system_birth_chart(self):
        """Test natal chart with Regiomontanus house system (R)."""
        self._test_house_system("R", "Regiomontanus")

    def test_sripati_house_system_birth_chart(self):
        """Test natal chart with Sripati house system (S)."""
        self._test_house_system("S", "Sripati")

    def test_polich_page_house_system_birth_chart(self):
        """Test natal chart with Polich/Page (Topocentric) house system (T)."""
        self._test_house_system("T", "Polich Page")

    def test_krusinski_house_system_birth_chart(self):
        """Test natal chart with Krusinski-Pisa-Goelzer house system (U)."""
        self._test_house_system("U", "Krusinski")

    def test_vehlow_house_system_birth_chart(self):
        """Test natal chart with Equal/Vehlow house system (V)."""
        self._test_house_system("V", "Vehlow")

    def test_whole_sign_house_system_birth_chart(self):
        """Test natal chart with Whole Sign house system (W)."""
        self._test_house_system("W", "Whole Sign")

    def test_meridian_house_system_birth_chart(self):
        """Test natal chart with Axial Rotation/Meridian house system (X)."""
        self._test_house_system("X", "Meridian")

    def test_apc_house_system_birth_chart(self):
        """Test natal chart with APC house system (Y)."""
        self._test_house_system("Y", "APC")

    # =========================================================================
    # SECTION 9: PERSPECTIVE TYPE TESTS
    # =========================================================================

    def test_heliocentric_perspective_natals_chart(self):
        """Test natal chart with heliocentric perspective."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.heliocentric_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - Heliocentric - Natal Chart.svg", chart_svg)

    def test_topocentric_perspective_natals_chart(self):
        """Test natal chart with topocentric perspective."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.topocentric_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - Topocentric - Natal Chart.svg", chart_svg)

    def test_true_geocentric_perspective_natals_chart(self):
        """Test natal chart with true geocentric perspective."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.true_geocentric_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - True Geocentric - Natal Chart.svg", chart_svg)

    def test_heliocentric_synastry_chart(self):
        """Test synastry chart with heliocentric perspective."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Heliocentric Synastry",
            *self.JOHN_LENNON_BIRTH_DATA,
            perspective_type="Heliocentric",
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - Heliocentric",
            *self.PAUL_MCCARTNEY_BIRTH_DATA,
            perspective_type="Heliocentric",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - Heliocentric - Synastry Chart.svg", chart_svg)

    def test_topocentric_transit_chart(self):
        """Test transit chart with topocentric perspective."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Topocentric Transit",
            *self.JOHN_LENNON_BIRTH_DATA,
            perspective_type="Topocentric",
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - Topocentric",
            *self.PAUL_MCCARTNEY_BIRTH_DATA,
            perspective_type="Topocentric",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_transit_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - Topocentric - Transit Chart.svg", chart_svg)

    def test_true_geocentric_synastry_chart(self):
        """Test synastry chart with true geocentric perspective."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - True Geocentric Synastry",
            *self.JOHN_LENNON_BIRTH_DATA,
            perspective_type="True Geocentric",
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - True Geocentric",
            *self.PAUL_MCCARTNEY_BIRTH_DATA,
            perspective_type="True Geocentric",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - True Geocentric - Synastry Chart.svg", chart_svg)

    # =========================================================================
    # SECTION 10: WHEEL-ONLY OUTPUT TESTS
    # =========================================================================

    def test_wheel_only_chart(self):
        """Test natal chart wheel-only output."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.wheel_only_subject)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - Wheel Only - Natal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_external_chart(self):
        """Test external natal chart wheel-only output."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.wheel_external_subject)
        chart_svg = ChartDrawer(chart_data, external_view=True).generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - Wheel External Only - ExternalNatal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_synastry_chart(self):
        """Test synastry chart wheel-only output."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.wheel_synastry_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - Wheel Synastry Only - Synastry Chart - Wheel Only.svg", chart_svg)

    def test_wheel_transit_chart(self):
        """Test transit chart wheel-only output."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.wheel_transit_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - Wheel Transit Only - Transit Chart - Wheel Only.svg", chart_svg)

    def test_wheel_only_dark_natal(self):
        """Test natal chart wheel-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only Dark", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - Wheel Only Dark - Natal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_only_light_natal(self):
        """Test natal chart wheel-only with light theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Only Light", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - Wheel Only Light - Natal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_synastry_dark(self):
        """Test synastry chart wheel-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Synastry Dark", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - Wheel Synastry Dark - Synastry Chart - Wheel Only.svg", chart_svg)

    def test_wheel_transit_dark(self):
        """Test transit chart wheel-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Wheel Transit Dark", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - Wheel Transit Dark - Transit Chart - Wheel Only.svg", chart_svg)

    def test_wheel_only_all_active_points_chart(self):
        """Test natal chart wheel-only with all active points."""
        chart_data = ChartDataFactory.create_natal_chart_data(
            self.all_active_points_subject, active_points=ALL_ACTIVE_POINTS
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Natal Chart - Wheel Only.svg", chart_svg)

    def test_wheel_only_all_active_points_synastry_chart(self):
        """Test synastry chart wheel-only with all active points."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.all_active_points_subject,
            self.all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Wheel Only.svg", chart_svg)

    # =========================================================================
    # SECTION 11: ASPECT GRID ONLY OUTPUT TESTS
    # =========================================================================

    def test_aspect_grid_only_chart(self):
        """Test natal chart aspect-grid-only output."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.aspect_grid_only_subject)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - Aspect Grid Only - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_dark_chart(self):
        """Test natal chart aspect-grid-only with dark theme."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.aspect_grid_dark_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - Aspect Grid Dark Theme - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_light_chart(self):
        """Test natal chart aspect-grid-only with light theme."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.aspect_grid_light_subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - Aspect Grid Light Theme - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_synastry_chart(self):
        """Test synastry chart aspect-grid-only output."""
        chart_data = ChartDataFactory.create_synastry_chart_data(self.aspect_grid_synastry_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - Aspect Grid Synastry - Synastry Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_transit(self):
        """Test transit chart aspect-grid-only output."""
        chart_data = ChartDataFactory.create_transit_chart_data(self.aspect_grid_transit_subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - Aspect Grid Transit - Transit Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_dark_synastry(self):
        """Test synastry chart aspect-grid-only with dark theme."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.aspect_grid_dark_synastry_subject, self.second_subject
        )
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_aspect_grid_only_svg_string()
        self._compare_chart_svg(
            "John Lennon - Aspect Grid Dark Synastry - Synastry Chart - Aspect Grid Only.svg", chart_svg
        )

    def test_aspect_grid_black_and_white_natal(self):
        """Test natal chart aspect-grid-only with black-and-white theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid BW", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - Aspect Grid BW - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_black_and_white_synastry(self):
        """Test synastry chart aspect-grid-only with black-and-white theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid BW Synastry", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_aspect_grid_only_svg_string()
        self._compare_chart_svg(
            "John Lennon - Aspect Grid BW Synastry - Synastry Chart - Aspect Grid Only.svg", chart_svg
        )

    def test_aspect_grid_black_and_white_transit(self):
        """Test transit chart aspect-grid-only with black-and-white theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid BW Transit", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_aspect_grid_only_svg_string()
        self._compare_chart_svg(
            "John Lennon - Aspect Grid BW Transit - Transit Chart - Aspect Grid Only.svg", chart_svg
        )

    def test_aspect_grid_transit_dark(self):
        """Test transit chart aspect-grid-only with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Dark Transit", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_aspect_grid_only_svg_string()
        self._compare_chart_svg(
            "John Lennon - Aspect Grid Dark Transit - Transit Chart - Aspect Grid Only.svg", chart_svg
        )

    def test_aspect_grid_transit_light(self):
        """Test transit chart aspect-grid-only with light theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Aspect Grid Light Transit", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_aspect_grid_only_svg_string()
        self._compare_chart_svg(
            "John Lennon - Aspect Grid Light Transit - Transit Chart - Aspect Grid Only.svg", chart_svg
        )

    def test_aspect_grid_all_active_points_chart(self):
        """Test natal chart aspect-grid-only with all active points."""
        chart_data = ChartDataFactory.create_natal_chart_data(
            self.all_active_points_subject, active_points=ALL_ACTIVE_POINTS
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Natal Chart - Aspect Grid Only.svg", chart_svg)

    def test_aspect_grid_all_active_points_synastry_chart(self):
        """Test synastry chart aspect-grid-only with all active points."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.all_active_points_subject,
            self.all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Aspect Grid Only.svg", chart_svg)

    # =========================================================================
    # SECTION 12: ALL ACTIVE POINTS TESTS
    # =========================================================================

    def test_all_active_points_natal_chart(self):
        """Test natal chart with all active points enabled."""
        chart_data = ChartDataFactory.create_natal_chart_data(
            self.all_active_points_subject, active_points=ALL_ACTIVE_POINTS
        )
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Natal Chart.svg", chart_svg)

    def test_synastry_chart_all_active_points_list(self):
        """Test synastry chart with all active points and list layout."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.all_active_points_subject,
            self.all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data, double_chart_aspect_grid_type="list").generate_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Synastry Chart - List.svg", chart_svg)

    def test_synastry_chart_all_active_points_grid(self):
        """Test synastry chart with all active points and table layout."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.all_active_points_subject,
            self.all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )
        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data, double_chart_aspect_grid_type="table").generate_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Grid.svg", chart_svg)

    def test_transit_all_active_points(self):
        """Test transit chart with all active points enabled."""
        first = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - All Active Points Transit",
            *self.JOHN_LENNON_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=ALL_ACTIVE_POINTS,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - All Active Points Transit",
            *self.PAUL_MCCARTNEY_BIRTH_DATA,
            suppress_geonames_warning=True,
            active_points=ALL_ACTIVE_POINTS,
        )
        chart_data = ChartDataFactory.create_transit_chart_data(first, second, active_points=ALL_ACTIVE_POINTS)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Transit Chart.svg", chart_svg)

    # =========================================================================
    # SECTION 13: LANGUAGE TESTS
    # =========================================================================

    def test_chinese_chart(self):
        """Test natal chart with Chinese language."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.chinese_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="CN").generate_svg_string()
        self._compare_chart_svg("Hua Chenyu - Natal Chart.svg", chart_svg)

    def test_french_chart(self):
        """Test natal chart with French language."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.french_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="FR").generate_svg_string()
        self._compare_chart_svg("Jeanne Moreau - Natal Chart.svg", chart_svg)

    def test_spanish_chart(self):
        """Test natal chart with Spanish language."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.spanish_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="ES").generate_svg_string()
        self._compare_chart_svg("Antonio Banderas - Natal Chart.svg", chart_svg)

    def test_portuguese_chart(self):
        """Test natal chart with Portuguese language."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.portuguese_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="PT").generate_svg_string()
        self._compare_chart_svg("Cristiano Ronaldo - Natal Chart.svg", chart_svg)

    def test_italian_chart(self):
        """Test natal chart with Italian language."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.italian_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="IT").generate_svg_string()
        self._compare_chart_svg("Sophia Loren - Natal Chart.svg", chart_svg)

    def test_russian_chart(self):
        """Test natal chart with Russian language."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.russian_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="RU").generate_svg_string()
        self._compare_chart_svg("Mikhail Bulgakov - Natal Chart.svg", chart_svg)

    def test_turkish_chart(self):
        """Test natal chart with Turkish language."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.turkish_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="TR").generate_svg_string()
        self._compare_chart_svg("Mehmet Oz - Natal Chart.svg", chart_svg)

    def test_german_chart(self):
        """Test natal chart with German language."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.german_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="DE").generate_svg_string()
        self._compare_chart_svg("Albert Einstein - Natal Chart.svg", chart_svg)

    def test_hindi_chart(self):
        """Test natal chart with Hindi language."""
        chart_data = ChartDataFactory.create_natal_chart_data(self.hindi_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="HI").generate_svg_string()
        self._compare_chart_svg("Amitabh Bachchan - Natal Chart.svg", chart_svg)

    def test_english_natal_chart(self):
        """Test natal chart with explicit English language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - EN", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, chart_language="EN").generate_svg_string()
        self._compare_chart_svg("John Lennon - EN - Natal Chart.svg", chart_svg)

    def test_french_synastry_chart(self):
        """Test synastry chart with French language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - FR", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="FR").generate_svg_string()
        self._compare_chart_svg("John Lennon - FR - Synastry Chart.svg", chart_svg)

    def test_german_synastry_chart(self):
        """Test synastry chart with German language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - DE", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="DE").generate_svg_string()
        self._compare_chart_svg("John Lennon - DE - Synastry Chart.svg", chart_svg)

    def test_chinese_transit_chart(self):
        """Test transit chart with Chinese language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - CN", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="CN").generate_svg_string()
        self._compare_chart_svg("John Lennon - CN - Transit Chart.svg", chart_svg)

    def test_spanish_transit_chart(self):
        """Test transit chart with Spanish language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - ES", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="ES").generate_svg_string()
        self._compare_chart_svg("John Lennon - ES - Transit Chart.svg", chart_svg)

    def test_italian_composite_chart(self):
        """Test composite chart with Italian language."""
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="IT").generate_svg_string()
        self._compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - IT - Composite Chart.svg", chart_svg)

    def test_portuguese_composite_chart(self):
        """Test composite chart with Portuguese language."""
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pitt)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="PT").generate_svg_string()
        self._compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - PT - Composite Chart.svg", chart_svg)

    def test_russian_transit_chart(self):
        """Test transit chart with Russian language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - RU", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_transit_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="RU").generate_svg_string()
        self._compare_chart_svg("John Lennon - RU - Transit Chart.svg", chart_svg)

    def test_turkish_synastry_chart(self):
        """Test synastry chart with Turkish language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - TR", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="TR").generate_svg_string()
        self._compare_chart_svg("John Lennon - TR - Synastry Chart.svg", chart_svg)

    # =========================================================================
    # SECTION 14: CHARTDRAWER OPTIONS TESTS
    # =========================================================================

    def test_synastry_chart_with_list_layout(self):
        """Test synastry chart with list layout for aspects."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - SCTWL", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(subject, self.second_subject)
        chart_svg = ChartDrawer(chart_data, double_chart_aspect_grid_type="list", theme="dark").generate_svg_string()
        self._compare_chart_svg("John Lennon - SCTWL - Synastry Chart.svg", chart_svg)

    def test_custom_title_natal_chart(self):
        """Test natal chart with custom title override."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Custom Title", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, custom_title="My Custom Chart Title").generate_svg_string()
        self._compare_chart_svg("John Lennon - Custom Title - Natal Chart.svg", chart_svg)

    def test_show_aspect_icons_false(self):
        """Test natal chart with aspect icons disabled."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - No Aspect Icons", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, show_aspect_icons=False).generate_svg_string()
        self._compare_chart_svg("John Lennon - No Aspect Icons - Natal Chart.svg", chart_svg)

    def test_auto_size_false(self):
        """Test natal chart with auto_size disabled."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Auto Size False", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, auto_size=False).generate_svg_string()
        self._compare_chart_svg("John Lennon - Auto Size False - Natal Chart.svg", chart_svg)

    def test_remove_css_variables(self):
        """Test natal chart with CSS variables removed (inlined)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - No CSS Variables", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string(remove_css_variables=True)
        self._compare_chart_svg("John Lennon - No CSS Variables - Natal Chart.svg", chart_svg)

    def test_custom_padding_natal_chart(self):
        """Test natal chart with custom padding (50px instead of default 20px)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Custom Padding", *self.JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, padding=50).generate_svg_string()
        self._compare_chart_svg("John Lennon - Custom Padding - Natal Chart.svg", chart_svg)

    def test_kanye_west_natal_chart(self):
        """Test natal chart with different birth data (Kanye West)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Kanye", 1977, 6, 8, 8, 45, "Atlanta", "US", suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("Kanye - Natal Chart.svg", chart_svg)

    # =========================================================================
    # SECTION 15: RELATIONSHIP SCORE TESTS
    # =========================================================================

    def test_synastry_with_relationship_score(self):
        """Test synastry chart with relationship score calculation enabled."""
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.first_subject,
            self.second_subject,
            include_relationship_score=True,
        )
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - Relationship Score - Synastry Chart.svg", chart_svg)
