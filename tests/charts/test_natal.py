# -*- coding: utf-8 -*-
"""
Natal Chart SVG Tests

This module tests natal chart generation including:
- Basic natal charts (standard, external view, minified)
- Theme variations (dark, light, black-and-white, dark-high-contrast, strawberry)
- Sidereal modes (all 20 ayanamsas)
- House systems (all 23 systems)
- Perspective types (Heliocentric, Topocentric, True Geocentric)
- Language tests (10 supported languages)

Usage:
    pytest tests/charts/test_natal.py -v
"""

from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.chart_data_factory import ChartDataFactory

from .conftest import (
    SVG_DIR,
    JOHN_LENNON_BIRTH_DATA,
    HOUSE_SYSTEM_NAMES,
    SIDEREAL_MODES,
    compare_chart_svg,
    create_sidereal_subject,
)


class TestNatalChartBasic:
    """Basic natal chart tests."""

    def test_natal_chart(self, john_lennon):
        """Test basic natal chart generation."""
        chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - Natal Chart.svg", chart_svg)

    def test_natal_chart_from_model(self, john_lennon):
        """Test natal chart generation from model (duplicate for compatibility)."""
        chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - Natal Chart.svg", chart_svg)

    def test_external_natal_chart(self):
        """Test natal chart with external view (planets on outer ring)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - ExternalNatal", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - ExternalNatal - Natal Chart.svg", chart_svg)

    def test_minified_natal_chart(self):
        """Test minified SVG output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Minified", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string(minify=True)
        compare_chart_svg("John Lennon - Minified - Natal Chart.svg", chart_svg)


class TestNatalChartThemes:
    """Theme-based natal chart tests."""

    def test_dark_theme_natal_chart(self):
        """Test natal chart with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Dark Theme", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        compare_chart_svg("John Lennon - Dark Theme - Natal Chart.svg", chart_svg)

    def test_dark_high_contrast_theme_natal_chart(self):
        """Test natal chart with dark high contrast theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Dark High Contrast Theme", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="dark-high-contrast").generate_svg_string()
        compare_chart_svg("John Lennon - Dark High Contrast Theme - Natal Chart.svg", chart_svg)

    def test_light_theme_natal_chart(self):
        """Test natal chart with light theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Light Theme", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_svg_string()
        compare_chart_svg("John Lennon - Light Theme - Natal Chart.svg", chart_svg)

    def test_black_and_white_natal_chart(self, john_lennon):
        """Test natal chart with black-and-white theme."""
        chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme - Natal Chart.svg", chart_svg)

    def test_dark_theme_external_natal_chart(self):
        """Test external natal chart with dark theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Dark Theme External", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="dark", external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - Dark Theme External - Natal Chart.svg", chart_svg)

    def test_light_theme_external_natal_chart(self):
        """Test external natal chart with light theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Light Theme External", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="light", external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - Light Theme External - Natal Chart.svg", chart_svg)

    def test_black_and_white_external_natal_chart(self):
        """Test external natal chart with black-and-white theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Black and White Theme External", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="black-and-white", external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - Black and White Theme External - Natal Chart.svg", chart_svg)

    def test_transparent_background_natal_chart(self):
        """Test natal chart with transparent background."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Transparent Background", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, transparent_background=True).generate_svg_string()
        compare_chart_svg("John Lennon - Transparent Background - Natal Chart.svg", chart_svg)

    def test_strawberry_natal_chart(self):
        """Test natal chart with Strawberry theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Strawberry Theme", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="strawberry").generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme - Natal Chart.svg", chart_svg)

    def test_strawberry_external_natal_chart(self):
        """Test external natal chart with Strawberry theme."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Strawberry Theme External", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="strawberry", external_view=True).generate_svg_string()
        compare_chart_svg("John Lennon - Strawberry Theme External - Natal Chart.svg", chart_svg)


class TestNatalChartSiderealModes:
    """Sidereal mode (ayanamsa) natal chart tests."""

    def test_lahiri_birth_chart(self, lahiri_subject):
        """Test sidereal chart using Lahiri ayanamsa."""
        chart_data = ChartDataFactory.create_natal_chart_data(lahiri_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Lahiri - Natal Chart.svg", chart_svg)

    def test_fagan_bradley_birth_chart(self, fagan_bradley_subject):
        """Test sidereal chart using Fagan-Bradley ayanamsa."""
        chart_data = ChartDataFactory.create_natal_chart_data(fagan_bradley_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Fagan-Bradley - Natal Chart.svg", chart_svg)

    def test_deluce_birth_chart(self, deluce_subject):
        """Test sidereal chart using DeLuce ayanamsa."""
        chart_data = ChartDataFactory.create_natal_chart_data(deluce_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon DeLuce - Natal Chart.svg", chart_svg)

    def test_j2000_birth_chart(self, j2000_subject):
        """Test sidereal chart using J2000 ayanamsa."""
        chart_data = ChartDataFactory.create_natal_chart_data(j2000_subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon J2000 - Natal Chart.svg", chart_svg)

    def test_raman_birth_chart(self):
        """Test sidereal chart using Raman ayanamsa."""
        subject = create_sidereal_subject("Raman", "RAMAN")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Raman - Natal Chart.svg", chart_svg)

    def test_ushashashi_birth_chart(self):
        """Test sidereal chart using Ushashashi ayanamsa."""
        subject = create_sidereal_subject("Ushashashi", "USHASHASHI")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Ushashashi - Natal Chart.svg", chart_svg)

    def test_krishnamurti_birth_chart(self):
        """Test sidereal chart using Krishnamurti ayanamsa."""
        subject = create_sidereal_subject("Krishnamurti", "KRISHNAMURTI")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Krishnamurti - Natal Chart.svg", chart_svg)

    def test_djwhal_khul_birth_chart(self):
        """Test sidereal chart using Djwhal Khul ayanamsa."""
        subject = create_sidereal_subject("Djwhal Khul", "DJWHAL_KHUL")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Djwhal Khul - Natal Chart.svg", chart_svg)

    def test_yukteshwar_birth_chart(self):
        """Test sidereal chart using Yukteshwar ayanamsa."""
        subject = create_sidereal_subject("Yukteshwar", "YUKTESHWAR")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Yukteshwar - Natal Chart.svg", chart_svg)

    def test_jn_bhasin_birth_chart(self):
        """Test sidereal chart using JN Bhasin ayanamsa."""
        subject = create_sidereal_subject("JN Bhasin", "JN_BHASIN")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon JN Bhasin - Natal Chart.svg", chart_svg)

    def test_babyl_kugler1_birth_chart(self):
        """Test sidereal chart using Babylonian Kugler 1 ayanamsa."""
        subject = create_sidereal_subject("Babyl Kugler1", "BABYL_KUGLER1")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Babyl Kugler1 - Natal Chart.svg", chart_svg)

    def test_babyl_kugler2_birth_chart(self):
        """Test sidereal chart using Babylonian Kugler 2 ayanamsa."""
        subject = create_sidereal_subject("Babyl Kugler2", "BABYL_KUGLER2")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Babyl Kugler2 - Natal Chart.svg", chart_svg)

    def test_babyl_kugler3_birth_chart(self):
        """Test sidereal chart using Babylonian Kugler 3 ayanamsa."""
        subject = create_sidereal_subject("Babyl Kugler3", "BABYL_KUGLER3")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Babyl Kugler3 - Natal Chart.svg", chart_svg)

    def test_babyl_huber_birth_chart(self):
        """Test sidereal chart using Babylonian Huber ayanamsa."""
        subject = create_sidereal_subject("Babyl Huber", "BABYL_HUBER")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Babyl Huber - Natal Chart.svg", chart_svg)

    def test_babyl_etpsc_birth_chart(self):
        """Test sidereal chart using Babylonian ETPSC ayanamsa."""
        subject = create_sidereal_subject("Babyl Etpsc", "BABYL_ETPSC")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Babyl Etpsc - Natal Chart.svg", chart_svg)

    def test_aldebaran_15tau_birth_chart(self):
        """Test sidereal chart using Aldebaran 15 Tau ayanamsa."""
        subject = create_sidereal_subject("Aldebaran 15Tau", "ALDEBARAN_15TAU")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Aldebaran 15Tau - Natal Chart.svg", chart_svg)

    def test_hipparchos_birth_chart(self):
        """Test sidereal chart using Hipparchos ayanamsa."""
        subject = create_sidereal_subject("Hipparchos", "HIPPARCHOS")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Hipparchos - Natal Chart.svg", chart_svg)

    def test_sassanian_birth_chart(self):
        """Test sidereal chart using Sassanian ayanamsa."""
        subject = create_sidereal_subject("Sassanian", "SASSANIAN")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon Sassanian - Natal Chart.svg", chart_svg)

    def test_j1900_birth_chart(self):
        """Test sidereal chart using J1900 ayanamsa."""
        subject = create_sidereal_subject("J1900", "J1900")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon J1900 - Natal Chart.svg", chart_svg)

    def test_b1950_birth_chart(self):
        """Test sidereal chart using B1950 ayanamsa."""
        subject = create_sidereal_subject("B1950", "B1950")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon B1950 - Natal Chart.svg", chart_svg)

    def test_sidereal_lahiri_dark_wheel_only(self):
        """Test sidereal Lahiri with dark theme wheel-only output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon Lahiri - Dark Theme",
            *JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="dark").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon Lahiri - Dark Theme - Natal Chart - Wheel Only.svg", chart_svg)

    def test_sidereal_fagan_bradley_light_wheel_only(self):
        """Test sidereal Fagan-Bradley with light theme wheel-only output."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon Fagan-Bradley - Light Theme",
            *JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode="FAGAN_BRADLEY",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme="light").generate_wheel_only_svg_string()
        compare_chart_svg("John Lennon Fagan-Bradley - Light Theme - Natal Chart - Wheel Only.svg", chart_svg)


class TestNatalChartHouseSystems:
    """House system natal chart tests."""

    def _test_house_system(self, house_id: str, house_name: str):
        """Helper method to test a specific house system."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            f"John Lennon - House System {house_name}",
            *JOHN_LENNON_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg(f"John Lennon - House System {house_name} - Natal Chart.svg", chart_svg)

    def test_morinus_house_system_birth_chart(self):
        """Test natal chart with Morinus house system (M)."""
        self._test_house_system("M", "Morinus")

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


class TestNatalChartPerspectives:
    """Perspective type natal chart tests."""

    def test_heliocentric_perspective_natal_chart(self):
        """Test natal chart with heliocentric perspective."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Heliocentric",
            *JOHN_LENNON_BIRTH_DATA,
            perspective_type="Heliocentric",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - Heliocentric - Natal Chart.svg", chart_svg)

    def test_topocentric_perspective_natal_chart(self):
        """Test natal chart with topocentric perspective."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - Topocentric",
            *JOHN_LENNON_BIRTH_DATA,
            perspective_type="Topocentric",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - Topocentric - Natal Chart.svg", chart_svg)

    def test_true_geocentric_perspective_natal_chart(self):
        """Test natal chart with true geocentric perspective."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - True Geocentric",
            *JOHN_LENNON_BIRTH_DATA,
            perspective_type="True Geocentric",
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - True Geocentric - Natal Chart.svg", chart_svg)


class TestNatalChartLanguages:
    """Language-specific natal chart tests."""

    def test_chinese_chart(self, chinese_subject):
        """Test natal chart with Chinese language."""
        chart_data = ChartDataFactory.create_natal_chart_data(chinese_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="CN").generate_svg_string()
        compare_chart_svg("Hua Chenyu - Natal Chart.svg", chart_svg)

    def test_french_chart(self, french_subject):
        """Test natal chart with French language."""
        chart_data = ChartDataFactory.create_natal_chart_data(french_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="FR").generate_svg_string()
        compare_chart_svg("Jeanne Moreau - Natal Chart.svg", chart_svg)

    def test_spanish_chart(self, spanish_subject):
        """Test natal chart with Spanish language."""
        chart_data = ChartDataFactory.create_natal_chart_data(spanish_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="ES").generate_svg_string()
        compare_chart_svg("Antonio Banderas - Natal Chart.svg", chart_svg)

    def test_portuguese_chart(self, portuguese_subject):
        """Test natal chart with Portuguese language."""
        chart_data = ChartDataFactory.create_natal_chart_data(portuguese_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="PT").generate_svg_string()
        compare_chart_svg("Cristiano Ronaldo - Natal Chart.svg", chart_svg)

    def test_italian_chart(self, italian_subject):
        """Test natal chart with Italian language."""
        chart_data = ChartDataFactory.create_natal_chart_data(italian_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="IT").generate_svg_string()
        compare_chart_svg("Sophia Loren - Natal Chart.svg", chart_svg)

    def test_russian_chart(self, russian_subject):
        """Test natal chart with Russian language."""
        chart_data = ChartDataFactory.create_natal_chart_data(russian_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="RU").generate_svg_string()
        compare_chart_svg("Mikhail Bulgakov - Natal Chart.svg", chart_svg)

    def test_turkish_chart(self, turkish_subject):
        """Test natal chart with Turkish language."""
        chart_data = ChartDataFactory.create_natal_chart_data(turkish_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="TR").generate_svg_string()
        compare_chart_svg("Mehmet Oz - Natal Chart.svg", chart_svg)

    def test_german_chart(self, german_subject):
        """Test natal chart with German language."""
        chart_data = ChartDataFactory.create_natal_chart_data(german_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="DE").generate_svg_string()
        compare_chart_svg("Albert Einstein - Natal Chart.svg", chart_svg)

    def test_hindi_chart(self, hindi_subject):
        """Test natal chart with Hindi language."""
        chart_data = ChartDataFactory.create_natal_chart_data(hindi_subject)
        chart_svg = ChartDrawer(chart_data, chart_language="HI").generate_svg_string()
        compare_chart_svg("Amitabh Bachchan - Natal Chart.svg", chart_svg)

    def test_english_natal_chart(self):
        """Test natal chart with explicit English language."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - EN", *JOHN_LENNON_BIRTH_DATA, suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, chart_language="EN").generate_svg_string()
        compare_chart_svg("John Lennon - EN - Natal Chart.svg", chart_svg)


class TestNatalChartAllActivePoints:
    """All active points natal chart tests."""

    def test_all_active_points_natal_chart(self, all_active_points_subject):
        """Test natal chart with all active points enabled."""
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        chart_data = ChartDataFactory.create_natal_chart_data(
            all_active_points_subject, active_points=ALL_ACTIVE_POINTS
        )
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("John Lennon - All Active Points - Natal Chart.svg", chart_svg)


class TestNatalChartOther:
    """Other natal chart test cases."""

    def test_kanye_west_natal_chart(self):
        """Test natal chart with different birth data (Kanye West)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Kanye", 1977, 6, 8, 8, 45, "Atlanta", "US", suppress_geonames_warning=True
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        compare_chart_svg("Kanye - Natal Chart.svg", chart_svg)
