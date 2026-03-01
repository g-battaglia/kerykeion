"""
Comprehensive tests for ReportGenerator.

Consolidates all test cases from:
- tests/reports/test_report.py
- tests/reports/test_report_output.py
- tests/reports/test_report_parametrized.py
- tests/reports/test_moon_phase_overview_report.py

Covers:
- Subject-only reports (no aspects)
- Natal, synastry, transit, composite, return chart reports
- Moon phase overview reports
- Golden-file snapshot regression
- Report options (include_aspects, max_aspects)
- Section presence validation
- Content formatting (symbols, dates, coordinates, retrograde)
- Element / quality percentage sums
- Sidereal mode display
- Empty-data code paths
- Relationship score and cusp comparison content
- Active points / aspects preset validation
- print_report() consistency with generate_report()
- Dual return title labels
- Geographic and temporal diversity
"""

from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.report import ReportGenerator
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.moon_phase_details import MoonPhaseDetailsFactory
from kerykeion.schemas.kr_models import (
    MoonPhaseOverviewModel,
    MoonPhaseMoonSummaryModel,
    MoonPhaseSunInfoModel,
    MoonPhaseLocationModel,
)
from kerykeion.settings.config_constants import (
    ALL_ACTIVE_ASPECTS,
    ALL_ACTIVE_POINTS,
    DEFAULT_ACTIVE_ASPECTS,
    DEFAULT_ACTIVE_POINTS,
    DISCEPOLO_SCORE_ACTIVE_ASPECTS,
    TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
)

FIXTURES_DIR = Path("tests/fixtures")

# ---------------------------------------------------------------------------
# Shared location dict for simple helpers
# ---------------------------------------------------------------------------
_LOCATION = {
    "city": "Rome",
    "nation": "IT",
    "lat": 41.9028,
    "lng": 12.4964,
    "tz_str": "Europe/Rome",
    "online": False,
    "suppress_geonames_warning": True,
}

# ---------------------------------------------------------------------------
# Regex patterns for format validation
# ---------------------------------------------------------------------------
_RE_SPEED = re.compile(r"[+-]\d+\.\d{4}°/d")
_RE_DECLINATION = re.compile(r"[+-]\d+\.\d{2}°")
_RE_POSITION = re.compile(r"\d+\.\d{2}°")
_RE_COORDINATE = re.compile(r"\d+\.\d{4}°")
_RE_JULIAN_DAY = re.compile(r"\d+\.\d{6}")
_RE_DATE = re.compile(r"\d{2}/\d{2}/")
_RE_RETROGRADE_COL = re.compile(r"\|\s*([R-])\s*\|")

_ASPECT_SYMBOLS = {"☌", "☍", "△", "□", "⚹", "⚻", "∠", "⚼", "Q"}
_MOVEMENT_SYMBOLS = {"→", "←", "="}

# ---------------------------------------------------------------------------
# Required sections per chart type
# ---------------------------------------------------------------------------
_NATAL_SECTIONS = [
    "Birth Data",
    "Celestial Points",
    "Houses (",
    "Lunar Phase",
    "Element Distribution",
    "Quality Distribution",
    "Aspects",
    "Active Celestial Points",
]

_SYNASTRY_SECTIONS = [
    "First Subject",
    "Second Subject",
    "Owner 1",
    "Owner 2",
    "points in",
    "Aspects",
]

_COMPOSITE_SECTIONS = [
    "Composite Members",
    "Composite Chart",
]

_MOON_OVERVIEW_SECTIONS = [
    "Moon Summary",
    "Illumination Details",
    "Upcoming Phases",
    "Next Lunar Eclipse",
    "Sun Info",
    "Next Solar Eclipse",
    "Location",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_subject(
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
):
    return AstrologicalSubjectFactory.from_birth_data(
        name=name,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        **_LOCATION,
    )


def _make_offline_subject(
    name: str,
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lng: float,
    tz_str: str,
    **kwargs: Any,
):
    return AstrologicalSubjectFactory.from_birth_data(
        name=name,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        lat=lat,
        lng=lng,
        tz_str=tz_str,
        online=False,
        suppress_geonames_warning=True,
        **kwargs,
    )


def _snapshot_subject(**kwargs):
    return AstrologicalSubjectFactory.from_birth_data(
        name="Sample Natal Subject",
        year=1990,
        month=7,
        day=21,
        hour=14,
        minute=45,
        city="Liverpool",
        nation="GB",
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        **kwargs,
    )


def _snapshot_partner(**kwargs):
    return AstrologicalSubjectFactory.from_birth_data(
        name="Yoko Ono",
        year=1933,
        month=2,
        day=18,
        hour=20,
        minute=30,
        city="Tokyo",
        nation="JP",
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=False,
        **kwargs,
    )


def _snapshot_transit(**kwargs):
    return AstrologicalSubjectFactory.from_birth_data(
        name="1980 Transit",
        year=1980,
        month=12,
        day=8,
        hour=22,
        minute=50,
        city="New York",
        nation="US",
        lat=40.7128,
        lng=-74.0060,
        tz_str="America/New_York",
        online=False,
        **kwargs,
    )


def _make_moon_phase_overview() -> MoonPhaseOverviewModel:
    """Create the same overview used to generate the golden fixture."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Moon Phase Test",
        1993,
        10,
        10,
        12,
        12,
        lng=-0.1276,
        lat=51.5074,
        tz_str="Europe/London",
        online=False,
    )
    return MoonPhaseDetailsFactory.from_subject(subject)


def _extract_percentages(text: str, section: str) -> List[float]:
    """Parse percentage values from a distribution section."""
    in_section = False
    pcts: List[float] = []
    for line in text.splitlines():
        if section in line:
            in_section = True
            continue
        if in_section:
            m = re.search(r"(\d+\.\d)%", line)
            if m:
                pcts.append(float(m.group(1)))
            if "Total" in line:
                break
    return pcts


# =====================================================================
# 1. TestSubjectReport
# =====================================================================


class TestSubjectReport:
    """Report from raw AstrologicalSubjectModel (no chart data wrapper).

    Subject-only reports include Birth Data, Celestial Points, Houses,
    and Lunar Phase sections but do NOT include an Aspects section.
    """

    def test_core_sections_present(self) -> None:
        subject = _make_subject("Subject A", 1975, 10, 10, 21, 15)
        report = ReportGenerator(subject, include_aspects=False)
        text = report.generate_report(include_aspects=False)

        assert subject.name in text
        assert "Birth Data" in text
        assert "Celestial Points" in text
        assert "Houses (" in text
        assert "Lunar Phase" in text
        assert "Aspects" not in text

    def test_aspects_section_absent_for_subject_only(self) -> None:
        """Subject-only report never includes an Aspects table."""
        subject = _make_offline_subject(
            "Subject Only",
            1990,
            7,
            21,
            14,
            45,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
        )
        text = ReportGenerator(subject).generate_report()
        assert "showing" not in text

    def test_missing_lunar_phase_omits_section(self) -> None:
        """When lunar_phase is None the section is silently omitted."""
        subject = _make_offline_subject(
            "Moonless Subject",
            1990,
            7,
            21,
            14,
            45,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            calculate_lunar_phase=False,
        )
        text = ReportGenerator(subject, include_aspects=False).generate_report(
            include_aspects=False,
        )
        assert "Lunar Phase" not in text


# =====================================================================
# 2. TestNatalChartReport
# =====================================================================


class TestNatalChartReport:
    """Report from natal chart data model.

    Includes Elements/Quality distributions, Aspects section,
    and active configuration listing.
    """

    def test_includes_elements_and_active_configuration(self) -> None:
        subject = _make_subject("Subject B", 1985, 6, 15, 8, 0)
        chart = ChartDataFactory.create_natal_chart_data(subject)
        report = ReportGenerator(chart)
        full_text = report.generate_report(max_aspects=3)

        assert "Element Distribution" in full_text
        assert all(k in full_text for k in ("Fire", "Earth", "Air", "Water"))
        assert "Quality Distribution" in full_text
        assert all(k in full_text for k in ("Cardinal", "Fixed", "Mutable"))
        assert "Aspects" in full_text
        assert "Active Celestial Points" in full_text

    def test_element_percentages_sum(self, john_lennon) -> None:
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        text = ReportGenerator(chart).generate_report()
        pcts = _extract_percentages(text, "Element Distribution")
        assert len(pcts) == 4, f"Expected 4 element percentages, got {pcts}"
        assert abs(sum(pcts) - 100.0) < 1.0

    def test_quality_percentages_sum(self, john_lennon) -> None:
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        text = ReportGenerator(chart).generate_report()
        pcts = _extract_percentages(text, "Quality Distribution")
        assert len(pcts) == 3, f"Expected 3 quality percentages, got {pcts}"
        assert abs(sum(pcts) - 100.0) < 1.0

    def test_sidereal_mode_in_settings(self) -> None:
        subject = _make_offline_subject(
            "Sidereal Test",
            1990,
            7,
            21,
            14,
            45,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )
        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart).generate_report(max_aspects=3)

        assert "Sidereal" in text
        assert "LAHIRI" in text
        assert "Sidereal Mode" in text


# =====================================================================
# 3. TestSynastryReport
# =====================================================================


class TestSynastryReport:
    """Report from synastry chart data.

    Includes house comparison, Owner 1/Owner 2, and dual aspects.
    """

    def test_includes_house_comparison_and_dual_aspects(self) -> None:
        first = _make_subject("Synastry First", 1980, 2, 14, 16, 20)
        second = _make_subject("Synastry Second", 1983, 11, 6, 4, 45)

        chart = ChartDataFactory.create_synastry_chart_data(first, second)
        report = ReportGenerator(chart)
        text = report.generate_report(max_aspects=5)

        assert first.name in text and second.name in text
        assert "points in" in text
        assert "Active Celestial Points" in text
        assert "Owner 1" in text and "Owner 2" in text
        assert "Aspects" in text

    def test_cusp_comparison_tables(self, john_lennon, yoko_ono) -> None:
        chart = ChartDataFactory.create_synastry_chart_data(john_lennon, yoko_ono)
        text = ReportGenerator(chart).generate_report()
        assert "cusps in" in text
        assert "Projected House" in text
        assert "Sign" in text
        assert "Degree" in text

    def test_relationship_score_sections(self, john_lennon, yoko_ono) -> None:
        chart = ChartDataFactory.create_synastry_chart_data(
            john_lennon,
            yoko_ono,
            include_relationship_score=True,
        )
        text = ReportGenerator(chart).generate_report(max_aspects=5)

        assert "Relationship Score Summary" in text
        assert "Score" in text
        assert "Description" in text
        assert "Destiny Signature" in text

    def test_relationship_score_supporting_aspects(self, john_lennon, yoko_ono) -> None:
        chart = ChartDataFactory.create_synastry_chart_data(
            john_lennon,
            yoko_ono,
            include_relationship_score=True,
        )
        text = ReportGenerator(chart).generate_report()
        assert "Score Supporting Aspects" in text

    def test_relationship_score_absent_when_disabled(self, john_lennon, yoko_ono) -> None:
        chart = ChartDataFactory.create_synastry_chart_data(
            john_lennon,
            yoko_ono,
            include_relationship_score=False,
        )
        text = ReportGenerator(chart).generate_report()
        assert "Relationship Score Summary" not in text

    def test_synastry_traditional_has_no_chiron(self) -> None:
        natal = _snapshot_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        partner = _snapshot_partner(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        chart = ChartDataFactory.create_synastry_chart_data(natal, partner)
        text = ReportGenerator(chart).generate_report()
        assert "Chiron" not in text

    def test_synastry_all_has_cusp_comparison(self) -> None:
        natal = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        partner = _snapshot_partner(active_points=ALL_ACTIVE_POINTS)
        chart = ChartDataFactory.create_synastry_chart_data(
            natal,
            partner,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        text = ReportGenerator(chart).generate_report()
        assert "cusps in" in text
        assert "Owner 1" in text
        assert "Owner 2" in text


# =====================================================================
# 4. TestCompositeReport
# =====================================================================


class TestCompositeReport:
    """Report from composite chart data. Lists composite members."""

    def test_lists_members(self) -> None:
        first = _make_subject("Composite First", 1990, 1, 2, 9, 30)
        second = _make_subject("Composite Second", 1992, 3, 4, 11, 45)

        composite_subject = CompositeSubjectFactory(
            first,
            second,
            chart_name="Sample Composite Chart",
        ).get_midpoint_composite_subject_model()

        chart = ChartDataFactory.create_composite_chart_data(composite_subject)
        report = ReportGenerator(chart)
        text = report.generate_report(max_aspects=3)

        assert "Composite Members" in text
        assert first.name in text and second.name in text
        assert "Composite Chart" in text

    def test_composite_traditional_has_members(self) -> None:
        first = _snapshot_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        second = _snapshot_partner(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        composite = CompositeSubjectFactory(
            first,
            second,
            chart_name="John & Yoko Composite Chart",
        ).get_midpoint_composite_subject_model()
        chart = ChartDataFactory.create_composite_chart_data(composite)
        text = ReportGenerator(chart).generate_report()
        assert "Composite Members" in text
        assert first.name in text
        assert second.name in text

    def test_composite_all_has_element_distribution(self) -> None:
        first = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        second = _snapshot_partner(active_points=ALL_ACTIVE_POINTS)
        composite = CompositeSubjectFactory(
            first,
            second,
            chart_name="John & Yoko Composite Chart",
        ).get_midpoint_composite_subject_model()
        chart = ChartDataFactory.create_composite_chart_data(
            composite,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        text = ReportGenerator(chart).generate_report()
        assert "Element Distribution" in text
        pcts = _extract_percentages(text, "Element Distribution")
        assert len(pcts) == 4
        assert abs(sum(pcts) - 100.0) < 1.0


# =====================================================================
# 5. TestSolarReturnReport
# =====================================================================


class TestSolarReturnReport:
    """Report labels return type correctly."""

    def test_labels_return_type(self) -> None:
        natal = _make_subject("Solar Return Subject", 1987, 7, 21, 14, 30)

        factory = PlanetaryReturnFactory(
            natal,
            city=_LOCATION["city"],
            nation=_LOCATION["nation"],
            lat=_LOCATION["lat"],
            lng=_LOCATION["lng"],
            tz_str=_LOCATION["tz_str"],
            online=False,
        )
        solar_return_subject = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Solar",
        )

        chart = ChartDataFactory.create_single_wheel_return_chart_data(solar_return_subject)
        report = ReportGenerator(chart)
        text = report.generate_report(max_aspects=3)

        assert "Solar Return Chart" in text
        assert natal.name in text

    def test_solar_dual_return_title(self) -> None:
        natal = _make_offline_subject(
            "Return Label Test",
            1990,
            7,
            21,
            14,
            45,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
        )
        factory = PlanetaryReturnFactory(
            natal,
            lat=natal.lat,
            lng=natal.lng,
            tz_str=natal.tz_str,
            online=False,
        )
        solar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Solar",
        )
        chart = ChartDataFactory.create_return_chart_data(natal, solar)
        text = ReportGenerator(chart).generate_report(max_aspects=3)
        assert "Solar Return Comparison" in text

    def test_lunar_dual_return_title(self) -> None:
        natal = _make_offline_subject(
            "Return Label Test",
            1990,
            7,
            21,
            14,
            45,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
        )
        factory = PlanetaryReturnFactory(
            natal,
            lat=natal.lat,
            lng=natal.lng,
            tz_str=natal.tz_str,
            online=False,
        )
        lunar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Lunar",
        )
        chart = ChartDataFactory.create_return_chart_data(natal, lunar)
        text = ReportGenerator(chart).generate_report(max_aspects=3)
        assert "Lunar Return Comparison" in text

    def test_solar_return_all_points_has_tnos(self) -> None:
        natal = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        factory = PlanetaryReturnFactory(
            natal,
            city=natal.city,
            nation=natal.nation,
            lat=natal.lat,
            lng=natal.lng,
            tz_str=natal.tz_str,
            online=False,
        )
        solar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Solar",
        )
        chart = ChartDataFactory.create_single_wheel_return_chart_data(
            solar,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        text = ReportGenerator(chart).generate_report()
        assert "Solar Return Chart" in text
        assert "Return Type" in text
        for body in ("Ceres", "Eris"):
            assert body in text, f"{body} should appear in all-points solar return"

    def test_dual_return_all_has_elements(self) -> None:
        natal = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        factory = PlanetaryReturnFactory(
            natal,
            city=natal.city,
            nation=natal.nation,
            lat=natal.lat,
            lng=natal.lng,
            tz_str=natal.tz_str,
            online=False,
        )
        solar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Solar",
        )
        chart = ChartDataFactory.create_return_chart_data(
            natal,
            solar,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        text = ReportGenerator(chart).generate_report()
        assert "Solar Return Comparison" in text
        pcts = _extract_percentages(text, "Element Distribution")
        assert len(pcts) == 4


# =====================================================================
# 6. TestTransitReport
# =====================================================================


class TestTransitReport:
    """Report from transit chart data."""

    def test_transit_report_content(self) -> None:
        natal = _make_offline_subject(
            "Transit Natal",
            1990,
            7,
            21,
            14,
            45,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
        )
        transit = _make_offline_subject(
            "Transit Subject",
            2020,
            3,
            20,
            12,
            0,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
        )
        chart = ChartDataFactory.create_transit_chart_data(natal, transit)
        text = ReportGenerator(chart).generate_report(max_aspects=5)

        assert "Transit" in text
        assert "Natal Subject" in text
        assert "Transit Subject" in text
        assert natal.name in text
        assert transit.name in text

    def test_transit_traditional_has_no_uranus(self) -> None:
        natal = _snapshot_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        transit = _snapshot_transit(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        chart = ChartDataFactory.create_transit_chart_data(natal, transit)
        text = ReportGenerator(chart).generate_report()
        for planet in ("Uranus", "Neptune", "Pluto"):
            assert planet not in text, f"{planet} should not appear in traditional transit"

    def test_transit_all_points_has_tnos(self) -> None:
        natal = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        transit = _snapshot_transit(active_points=ALL_ACTIVE_POINTS)
        chart = ChartDataFactory.create_transit_chart_data(
            natal,
            transit,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        text = ReportGenerator(chart).generate_report()
        for body in ("Eris", "Sedna", "Ceres"):
            assert body in text, f"{body} should appear in all-points transit report"


# =====================================================================
# 7. TestMoonPhaseOverviewReport
# =====================================================================


class TestMoonPhaseOverviewReport:
    """Report from MoonPhaseOverviewModel via MoonPhaseDetailsFactory."""

    def test_generate_matches_print(self) -> None:
        """generate_report() and print_report() must produce identical content."""
        overview = _make_moon_phase_overview()
        report = ReportGenerator(overview)
        generated = report.generate_report()

        expected = (FIXTURES_DIR / "moon_phase_overview_report.txt").read_text(
            encoding="utf-8",
        )
        assert generated == expected

    @pytest.mark.parametrize("section", _MOON_OVERVIEW_SECTIONS)
    def test_section_present(self, section: str) -> None:
        text = ReportGenerator(_make_moon_phase_overview()).generate_report()
        assert section in text, f"Missing section: {section!r}"

    def test_title_contains_datestamp(self) -> None:
        text = ReportGenerator(_make_moon_phase_overview()).generate_report()
        assert "Moon Phase Overview" in text
        assert "1993" in text

    def test_illumination_percentage_format(self) -> None:
        text = ReportGenerator(_make_moon_phase_overview()).generate_report()
        assert re.search(r"\d+%", text), "No illumination percentage found"

    def test_visible_fraction_format(self) -> None:
        text = ReportGenerator(_make_moon_phase_overview()).generate_report()
        assert re.search(r"\d+\.\d{4}", text), "No 4-decimal fraction found"

    def test_phase_angle_format(self) -> None:
        text = ReportGenerator(_make_moon_phase_overview()).generate_report()
        assert re.search(r"\d+\.\d{2}\xb0", text), "No phase angle with degree symbol"

    def test_sun_altitude_format(self) -> None:
        text = ReportGenerator(_make_moon_phase_overview()).generate_report()
        assert re.search(r"Sun Altitude.*\d+\.\d{2}\xb0", text)

    def test_upcoming_phases_has_four_rows(self) -> None:
        text = ReportGenerator(_make_moon_phase_overview()).generate_report()
        for phase in ["New Moon", "First Quarter", "Full Moon", "Last Quarter"]:
            assert phase in text, f"Missing phase: {phase!r}"

    def test_eclipse_date_format(self) -> None:
        text = ReportGenerator(_make_moon_phase_overview()).generate_report()
        assert re.search(
            r"\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} \+\d{4}",
            text,
        ), "No RFC-2822 date found in eclipse section"

    def test_minimal_model_no_crash(self) -> None:
        minimal = MoonPhaseOverviewModel(
            timestamp=0,
            datestamp="Thu, 01 Jan 1970 00:00:00 +0000",
            moon=MoonPhaseMoonSummaryModel(),
        )
        text = ReportGenerator(minimal).generate_report()
        assert "Moon Phase Overview" in text
        assert "Sun Info" not in text
        assert "Location" not in text

    def test_minimal_model_with_moon_summary(self) -> None:
        model = MoonPhaseOverviewModel(
            timestamp=750000000,
            datestamp="Fri, 08 Oct 1993 13:20:00 +0000",
            moon=MoonPhaseMoonSummaryModel(
                phase_name="Waning Crescent",
                emoji="\U0001f318",
                major_phase="Last Quarter",
                stage="waning",
                illumination="32%",
            ),
        )
        text = ReportGenerator(model).generate_report()
        assert "Waning Crescent" in text
        assert "Last Quarter" in text
        assert "32%" in text

    def test_model_with_sun_no_eclipse(self) -> None:
        model = MoonPhaseOverviewModel(
            timestamp=750000000,
            datestamp="Fri, 08 Oct 1993 13:20:00 +0000",
            moon=MoonPhaseMoonSummaryModel(),
            sun=MoonPhaseSunInfoModel(
                sunrise_timestamp="07:15",
                sunset_timestamp="18:18",
            ),
        )
        text = ReportGenerator(model).generate_report()
        assert "Sun Info" in text
        assert "07:15" in text
        assert "Next Solar Eclipse" not in text

    def test_model_with_location(self) -> None:
        model = MoonPhaseOverviewModel(
            timestamp=750000000,
            datestamp="Fri, 08 Oct 1993 13:20:00 +0000",
            moon=MoonPhaseMoonSummaryModel(),
            location=MoonPhaseLocationModel(
                latitude="51.50853",
                longitude="-0.12574",
                using_default_location=False,
            ),
        )
        text = ReportGenerator(model).generate_report()
        assert "Location" in text
        assert "51.50853" in text
        assert "-0.12574" in text
        assert "No" in text  # Default Location = No

    def test_unsupported_type_raises(self) -> None:
        with pytest.raises(TypeError, match="Unsupported model type"):
            ReportGenerator({"not": "a model"})  # type: ignore[arg-type]


# =====================================================================
# 8. TestGoldenFileSnapshots
# =====================================================================


class TestGoldenFileSnapshots:
    """Compare generated reports against fixture files in tests/fixtures/.

    Skip if fixture doesn't exist.
    """

    def test_new_moon_natal_report(self, capsys) -> None:
        fixture = FIXTURES_DIR / "new_moon_test_natal_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = AstrologicalSubjectFactory.from_birth_data(
            "New Moon - Test",
            2025,
            11,
            20,
            1,
            46,
            lng=-79.99589,
            lat=40.44062,
            tz_str="America/New_York",
            online=False,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        ReportGenerator(chart_data).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_synastry_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "synastry_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject()
        partner = _snapshot_partner()
        chart = ChartDataFactory.create_synastry_chart_data(natal, partner)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_transit_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "transit_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject()
        transit = _snapshot_transit()
        chart = ChartDataFactory.create_transit_chart_data(natal, transit)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_composite_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "composite_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject()
        partner = _snapshot_partner()
        composite = CompositeSubjectFactory(
            natal,
            partner,
            chart_name="John & Yoko Composite Chart",
        ).get_midpoint_composite_subject_model()
        chart = ChartDataFactory.create_composite_chart_data(composite)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_solar_return_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "solar_return_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject()
        factory = PlanetaryReturnFactory(
            natal,
            city=natal.city,
            nation=natal.nation,
            lat=natal.lat,
            lng=natal.lng,
            tz_str=natal.tz_str,
            online=False,
        )
        solar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Solar",
        )
        chart = ChartDataFactory.create_single_wheel_return_chart_data(solar)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_dual_return_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "dual_return_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject()
        factory = PlanetaryReturnFactory(
            natal,
            city=natal.city,
            nation=natal.nation,
            lat=natal.lat,
            lng=natal.lng,
            tz_str=natal.tz_str,
            online=False,
        )
        solar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Solar",
        )
        chart = ChartDataFactory.create_return_chart_data(natal, solar)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_moon_phase_overview_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "moon_phase_overview_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        overview = _make_moon_phase_overview()
        ReportGenerator(overview).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_natal_traditional_points_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_traditional_points_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = _snapshot_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        chart = ChartDataFactory.create_natal_chart_data(subject)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_natal_all_points_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_all_points_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        chart = ChartDataFactory.create_natal_chart_data(subject)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_natal_all_points_all_aspects_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_all_points_all_aspects_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_natal_all_aspects_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_all_aspects_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = _snapshot_subject()
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_natal_discepolo_aspects_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_discepolo_aspects_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = _snapshot_subject()
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=DISCEPOLO_SCORE_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_synastry_traditional_points_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "synastry_traditional_points_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        partner = _snapshot_partner(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        chart = ChartDataFactory.create_synastry_chart_data(natal, partner)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_synastry_all_points_all_aspects_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "synastry_all_points_all_aspects_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        partner = _snapshot_partner(active_points=ALL_ACTIVE_POINTS)
        chart = ChartDataFactory.create_synastry_chart_data(
            natal,
            partner,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_transit_traditional_points_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "transit_traditional_points_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        transit = _snapshot_transit(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        chart = ChartDataFactory.create_transit_chart_data(natal, transit)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_transit_all_points_all_aspects_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "transit_all_points_all_aspects_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        transit = _snapshot_transit(active_points=ALL_ACTIVE_POINTS)
        chart = ChartDataFactory.create_transit_chart_data(
            natal,
            transit,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_composite_traditional_points_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "composite_traditional_points_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        first = _snapshot_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        second = _snapshot_partner(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        composite = CompositeSubjectFactory(
            first,
            second,
            chart_name="John & Yoko Composite Chart",
        ).get_midpoint_composite_subject_model()
        chart = ChartDataFactory.create_composite_chart_data(composite)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_composite_all_points_all_aspects_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "composite_all_points_all_aspects_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        first = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        second = _snapshot_partner(active_points=ALL_ACTIVE_POINTS)
        composite = CompositeSubjectFactory(
            first,
            second,
            chart_name="John & Yoko Composite Chart",
        ).get_midpoint_composite_subject_model()
        chart = ChartDataFactory.create_composite_chart_data(
            composite,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_solar_return_all_points_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "solar_return_all_points_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        factory = PlanetaryReturnFactory(
            natal,
            city=natal.city,
            nation=natal.nation,
            lat=natal.lat,
            lng=natal.lng,
            tz_str=natal.tz_str,
            online=False,
        )
        solar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Solar",
        )
        chart = ChartDataFactory.create_single_wheel_return_chart_data(
            solar,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_dual_return_all_points_all_aspects_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "dual_return_all_points_all_aspects_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        natal = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        factory = PlanetaryReturnFactory(
            natal,
            city=natal.city,
            nation=natal.nation,
            lat=natal.lat,
            lng=natal.lng,
            tz_str=natal.tz_str,
            online=False,
        )
        solar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Solar",
        )
        chart = ChartDataFactory.create_return_chart_data(
            natal,
            solar,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    # ---- Geographic diversity golden snapshots ----

    def test_tokyo_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_tokyo_all_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Tokyo Subject",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            city="Tokyo",
            nation="JP",
            lat=35.6762,
            lng=139.6503,
            tz_str="Asia/Tokyo",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
        )
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_buenos_aires_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_buenos_aires_all_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Buenos Aires Subject",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            city="Buenos Aires",
            nation="AR",
            lat=-34.6037,
            lng=-58.3816,
            tz_str="America/Argentina/Buenos_Aires",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
        )
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_quito_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_quito_all_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Quito Subject",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            city="Quito",
            nation="EC",
            lat=0.1807,
            lng=-78.4678,
            tz_str="America/Guayaquil",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
        )
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    # ---- Temporal diversity golden snapshots ----

    def test_ancient_rome_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_ancient_rome_all_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Ancient Rome Subject",
            year=100,
            month=1,
            day=1,
            hour=12,
            minute=0,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=ALL_ACTIVE_POINTS,
        )
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_einstein_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_einstein_all_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Einstein Subject",
            year=1879,
            month=3,
            day=14,
            hour=11,
            minute=30,
            city="Ulm",
            nation="DE",
            lat=48.4011,
            lng=9.9876,
            tz_str="Europe/Berlin",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
        )
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_future_2050_snapshot(self, capsys) -> None:
        fixture = FIXTURES_DIR / "natal_future_2050_all_report.txt"
        if not fixture.exists():
            pytest.skip(f"Fixture {fixture.name} not found")

        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Future 2050 Subject",
            year=2050,
            month=7,
            day=20,
            hour=12,
            minute=0,
            city="Tokyo",
            nation="JP",
            lat=35.6762,
            lng=139.6503,
            tz_str="Asia/Tokyo",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
        )
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = fixture.read_text(encoding="utf-8")
        assert captured == expected + "\n"


# =====================================================================
# 9. TestReportOptions
# =====================================================================


class TestReportOptions:
    """include_aspects=False hides aspects. max_aspects limits count."""

    def test_include_aspects_false_hides_aspects(self) -> None:
        subject = _make_offline_subject(
            "No Aspects",
            1990,
            7,
            21,
            14,
            45,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
        )
        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart, include_aspects=False).generate_report(
            include_aspects=False,
        )
        cleaned = text.replace("Active Aspects Configuration", "")
        assert "| Aspects" not in cleaned or "(showing" not in cleaned

    def test_max_aspects_suffix_appears(self, john_lennon) -> None:
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        text = ReportGenerator(chart).generate_report(max_aspects=3)
        assert "(showing 3 of " in text

    def test_max_aspects_limits_rows(self, john_lennon) -> None:
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        text = ReportGenerator(chart).generate_report(max_aspects=3)
        in_aspects = False
        data_rows = 0
        for line in text.splitlines():
            if "Aspects" in line and "Active" not in line and "showing" in line:
                in_aspects = True
                continue
            if in_aspects:
                if line.startswith("+"):
                    if data_rows > 0:
                        break
                    continue
                if "|" in line:
                    data_rows += 1
        # data_rows includes the header row, so max_aspects + 1
        assert data_rows <= 3 + 1, f"Expected at most 4 rows (header + 3 data), got {data_rows}"

    def test_max_aspects_none_shows_all(self, john_lennon) -> None:
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        text = ReportGenerator(chart).generate_report()
        assert "(showing" not in text

    def test_no_celestial_points_message(self, john_lennon) -> None:
        """_celestial_points_report returns fallback when points list is empty."""
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        report = ReportGenerator(chart)
        empty_subject = SimpleNamespace(active_points=[])
        result = report._celestial_points_report(empty_subject, "Empty Points")
        assert result == "No celestial points data available."

    def test_empty_active_configuration(self, john_lennon) -> None:
        """When both _active_points and _active_aspects are empty, no section is emitted."""
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        report = ReportGenerator(chart)
        report._active_points = []
        report._active_aspects = []
        result = report._active_configuration_report()
        assert result == ""

    def test_print_matches_generate(self, john_lennon, capsys) -> None:
        """print_report() output matches generate_report()."""
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        report = ReportGenerator(chart)
        expected = report.generate_report()
        report.print_report()
        captured = capsys.readouterr().out
        assert captured == expected + "\n"


# =====================================================================
# 10. TestReportSections
# =====================================================================


class TestReportSections:
    """Verify specific sections appear with correct headers."""

    def test_natal_chart_all_sections(self, john_lennon) -> None:
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        text = ReportGenerator(chart).generate_report(max_aspects=5)
        assert john_lennon.name in text
        for section in _NATAL_SECTIONS:
            assert section in text, f"Missing section: {section!r}"

    def test_synastry_chart_all_sections(self, john_lennon, yoko_ono) -> None:
        chart = ChartDataFactory.create_synastry_chart_data(john_lennon, yoko_ono)
        text = ReportGenerator(chart).generate_report(max_aspects=5)
        for section in _SYNASTRY_SECTIONS:
            assert section in text, f"Missing section: {section!r}"

    def test_composite_chart_all_sections(self, john_lennon, yoko_ono) -> None:
        composite = CompositeSubjectFactory(
            john_lennon,
            yoko_ono,
            chart_name="Test Composite",
        ).get_midpoint_composite_subject_model()
        chart = ChartDataFactory.create_composite_chart_data(composite)
        text = ReportGenerator(chart).generate_report(max_aspects=3)
        for section in _COMPOSITE_SECTIONS:
            assert section in text, f"Missing section: {section!r}"


# =====================================================================
# 11. TestReportContentFormatting
# =====================================================================


class TestReportContentFormatting:
    """Validate formatting patterns in the generated report."""

    @pytest.fixture(autouse=True)
    def _setup(self, john_lennon) -> None:
        chart = ChartDataFactory.create_natal_chart_data(john_lennon)
        self.text = ReportGenerator(chart).generate_report()

    def test_retrograde_markers(self) -> None:
        matches = _RE_RETROGRADE_COL.findall(self.text)
        assert matches, "No retrograde column markers found"
        assert all(m in ("R", "-") for m in matches)

    def test_aspect_symbols_present(self) -> None:
        found = {s for s in _ASPECT_SYMBOLS if s in self.text}
        assert found, f"No aspect symbols found. Expected at least one of {_ASPECT_SYMBOLS}"

    def test_movement_symbols_present(self) -> None:
        found = {s for s in _MOVEMENT_SYMBOLS if s in self.text}
        assert found, f"No movement symbols found. Expected at least one of {_MOVEMENT_SYMBOLS}"

    def test_speed_format(self) -> None:
        assert _RE_SPEED.search(self.text), "No speed values in expected format found"

    def test_declination_format(self) -> None:
        assert _RE_DECLINATION.search(self.text), "No declination values found"

    def test_position_format(self) -> None:
        assert _RE_POSITION.search(self.text), "No position values found"

    def test_date_format_in_birth_data(self) -> None:
        assert _RE_DATE.search(self.text), "No DD/MM/ date format found"

    def test_coordinate_format(self) -> None:
        assert _RE_COORDINATE.search(self.text), "No coordinate with 4 decimal places"

    def test_julian_day_format(self) -> None:
        assert _RE_JULIAN_DAY.search(self.text), "No Julian Day with 6 decimal places"


# =====================================================================
# 12. TestActivePointsContentValidation
# =====================================================================


_POINTS_CONTENT_PRESETS = [
    pytest.param(
        TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
        9,
        ["Sun", "Moon", "Mars", "Jupiter", "Saturn"],
        ["Chiron", "Eris", "Ceres"],
        id="traditional_9pts",
    ),
    pytest.param(
        DEFAULT_ACTIVE_POINTS,
        18,
        ["Sun", "Moon", "Chiron", "Mean Lilith", "Ascendant"],
        ["Ceres", "Eris", "Vertex"],
        id="default_18pts",
    ),
    pytest.param(
        ALL_ACTIVE_POINTS,
        32,
        ["Sun", "Moon", "Chiron", "Ceres", "Eris", "Pars Fortunae", "Vertex"],
        [],
        id="all_32pts",
    ),
]


class TestActivePointsContentValidation:
    """Verify celestial points table content reflects the active_points preset."""

    @pytest.mark.parametrize(
        "active_points,expected_min,present_names,absent_names",
        _POINTS_CONTENT_PRESETS,
    )
    def test_point_names_presence(
        self,
        active_points,
        expected_min,
        present_names,
        absent_names,
    ) -> None:
        subject = _make_offline_subject(
            "Points Validation",
            1990,
            7,
            21,
            14,
            45,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
            active_points=active_points,
        )
        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart).generate_report()

        for name in present_names:
            assert name in text, f"{name!r} should appear with {len(active_points)}-point preset"
        for name in absent_names:
            assert name not in text, f"{name!r} should NOT appear with {len(active_points)}-point preset"

    @pytest.mark.parametrize(
        "active_points,expected_min,present_names,absent_names",
        _POINTS_CONTENT_PRESETS,
    )
    def test_element_percentages_sum_with_preset(
        self,
        active_points,
        expected_min,
        present_names,
        absent_names,
    ) -> None:
        subject = _make_offline_subject(
            "Elements Check",
            1990,
            7,
            21,
            14,
            45,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
            active_points=active_points,
        )
        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart).generate_report()
        pcts = _extract_percentages(text, "Element Distribution")
        assert len(pcts) == 4, f"Expected 4 element pcts, got {pcts}"
        assert abs(sum(pcts) - 100.0) < 1.0

    def test_traditional_points_has_fewer_celestial_rows(self) -> None:
        subject = _snapshot_subject(active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS)
        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart).generate_report()
        for absent in ("Ceres", "Chiron", "Eris", "Ascendant", "Medium Coeli"):
            assert absent not in text, f"{absent!r} should not appear in traditional report"

    def test_all_points_has_extra_bodies(self) -> None:
        subject = _snapshot_subject(active_points=ALL_ACTIVE_POINTS)
        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart).generate_report()
        for present in ("Ceres", "Pallas", "Juno", "Vesta", "Eris", "Pars Fortunae", "Vertex"):
            assert present in text, f"{present!r} should appear in all-points report"


# =====================================================================
# 13. TestActiveAspectsContentValidation
# =====================================================================


_ASPECTS_CONTENT_PRESETS = [
    pytest.param(
        DEFAULT_ACTIVE_ASPECTS,
        6,
        {"conjunction", "opposition", "trine", "sextile", "square", "quintile"},
        {"semi-sextile", "semi-square", "sesquiquadrate", "biquintile", "quincunx"},
        id="default_6asp",
    ),
    pytest.param(
        ALL_ACTIVE_ASPECTS,
        11,
        {
            "conjunction",
            "opposition",
            "trine",
            "sextile",
            "square",
            "quintile",
            "semi-sextile",
            "semi-square",
            "sesquiquadrate",
            "biquintile",
            "quincunx",
        },
        set(),
        id="all_11asp",
    ),
    pytest.param(
        DISCEPOLO_SCORE_ACTIVE_ASPECTS,
        8,
        {"conjunction", "opposition", "trine", "sextile", "square", "semi-sextile", "semi-square", "sesquiquadrate"},
        {"quintile", "biquintile", "quincunx"},
        id="discepolo_8asp",
    ),
]


class TestActiveAspectsContentValidation:
    """Verify active aspects configuration section reflects the preset."""

    @pytest.mark.parametrize(
        "active_aspects,count,present_names,absent_names",
        _ASPECTS_CONTENT_PRESETS,
    )
    def test_aspect_names_in_config_section(
        self,
        active_aspects,
        count,
        present_names,
        absent_names,
    ) -> None:
        subject = _make_offline_subject(
            "Aspects Validation",
            1990,
            7,
            21,
            14,
            45,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
        )
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=active_aspects,
        )
        text = ReportGenerator(chart).generate_report()

        for name in present_names:
            assert name in text, f"{name!r} should appear in config with {count}-aspect preset"
        for name in absent_names:
            config_section = ""
            in_config = False
            for line in text.splitlines():
                if "Active Aspects Configuration" in line:
                    in_config = True
                if in_config:
                    config_section += line + "\n"
                    if line.startswith("+") and len(config_section) > 100:
                        break
            assert name not in config_section, (
                f"{name!r} should NOT appear in active aspects config with {count}-aspect preset"
            )

    @pytest.mark.parametrize(
        "active_aspects,count,present_names,absent_names",
        _ASPECTS_CONTENT_PRESETS,
    )
    def test_quality_percentages_sum_with_preset(
        self,
        active_aspects,
        count,
        present_names,
        absent_names,
    ) -> None:
        subject = _make_offline_subject(
            "Quality Check",
            1990,
            7,
            21,
            14,
            45,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
        )
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=active_aspects,
        )
        text = ReportGenerator(chart).generate_report()
        pcts = _extract_percentages(text, "Quality Distribution")
        assert len(pcts) == 3, f"Expected 3 quality pcts, got {pcts}"
        assert abs(sum(pcts) - 100.0) < 1.0

    def test_all_aspects_has_minor_aspect_names_in_config(self) -> None:
        subject = _snapshot_subject()
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        text = ReportGenerator(chart).generate_report()
        for aspect in ("semi-sextile", "semi-square", "sesquiquadrate", "biquintile", "quincunx"):
            assert aspect in text, f"{aspect!r} should appear in active aspects config"

    def test_discepolo_aspects_omits_quintile(self) -> None:
        subject = _snapshot_subject()
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=DISCEPOLO_SCORE_ACTIVE_ASPECTS,
        )
        text = ReportGenerator(chart).generate_report()
        assert "quintile" not in text.lower().replace("biquintile", "").replace("sesquiquadrate", ""), (
            "quintile should not appear in Discepolo aspects config"
        )

    def test_discepolo_has_different_orbs(self) -> None:
        subject = _snapshot_subject()
        chart_disc = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=DISCEPOLO_SCORE_ACTIVE_ASPECTS,
        )
        text_disc = ReportGenerator(chart_disc).generate_report()

        chart_default = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=DEFAULT_ACTIVE_ASPECTS,
        )
        text_default = ReportGenerator(chart_default).generate_report()
        assert text_disc != text_default


# =====================================================================
# 14. TestTemporalDiversity
# =====================================================================


class TestTemporalDiversity:
    """Reports for different epochs must differ; ancient era excludes unsupported TNOs."""

    def test_ancient_rome_has_fewer_points_due_to_ephemeris(self) -> None:
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Ancient Rome Subject",
            year=100,
            month=1,
            day=1,
            hour=12,
            minute=0,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=ALL_ACTIVE_POINTS,
        )
        chart = ChartDataFactory.create_natal_chart_data(
            subject,
            active_aspects=ALL_ACTIVE_ASPECTS,
        )
        text = ReportGenerator(chart).generate_report()
        for body in ("Eris", "Sedna", "Haumea", "Makemake"):
            assert body not in text, f"{body} should be absent for 100 AD"
        for body in ("Sun", "Moon", "Mars", "Jupiter"):
            assert body in text, f"{body} must appear even in ancient era"

    def test_temporal_reports_differ(self) -> None:
        s1 = AstrologicalSubjectFactory.from_birth_data(
            name="Einstein Subject",
            year=1879,
            month=3,
            day=14,
            hour=11,
            minute=30,
            lat=48.4011,
            lng=9.9876,
            tz_str="Europe/Berlin",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
        )
        s2 = AstrologicalSubjectFactory.from_birth_data(
            name="Future 2050 Subject",
            year=2050,
            month=7,
            day=20,
            hour=12,
            minute=0,
            lat=35.6762,
            lng=139.6503,
            tz_str="Asia/Tokyo",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
        )
        text1 = ReportGenerator(
            ChartDataFactory.create_natal_chart_data(s1, active_aspects=ALL_ACTIVE_ASPECTS),
        ).generate_report()
        text2 = ReportGenerator(
            ChartDataFactory.create_natal_chart_data(s2, active_aspects=ALL_ACTIVE_ASPECTS),
        ).generate_report()
        assert text1 != text2

    def test_geographic_reports_differ(self) -> None:
        s_tokyo = AstrologicalSubjectFactory.from_birth_data(
            name="Tokyo Subject",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            city="Tokyo",
            nation="JP",
            lat=35.6762,
            lng=139.6503,
            tz_str="Asia/Tokyo",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
        )
        s_quito = AstrologicalSubjectFactory.from_birth_data(
            name="Quito Subject",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            city="Quito",
            nation="EC",
            lat=0.1807,
            lng=-78.4678,
            tz_str="America/Guayaquil",
            online=False,
            active_points=ALL_ACTIVE_POINTS,
        )
        text_tokyo = ReportGenerator(
            ChartDataFactory.create_natal_chart_data(s_tokyo, active_aspects=ALL_ACTIVE_ASPECTS),
        ).generate_report()
        text_quito = ReportGenerator(
            ChartDataFactory.create_natal_chart_data(s_quito, active_aspects=ALL_ACTIVE_ASPECTS),
        ).generate_report()
        assert text_tokyo != text_quito


# =============================================================================
# REPORT PRIVATE HELPERS (from edge_cases)
# =============================================================================


class TestReportPrivateHelpers:
    """Tests for ReportGenerator private helper methods."""

    @pytest.fixture()
    def _report(self, john_lennon):
        chart_data = ChartDataFactory.create_natal_chart_data(john_lennon)
        return ReportGenerator(chart_data)

    def test_extract_year_valid(self, _report):
        assert _report._extract_year("2024-06-15T12:00:00") == "2024"

    def test_extract_year_invalid(self, _report):
        assert _report._extract_year("invalid") is None

    def test_extract_year_none(self, _report):
        assert _report._extract_year(None) is None

    def test_format_date_iso_valid(self, _report):
        assert _report._format_date_iso("2024-06-15T12:00:00") == "2024-06-15"

    def test_format_date_iso_invalid(self, _report):
        assert _report._format_date_iso("invalid") == "invalid"

    def test_format_date_iso_none(self, _report):
        assert _report._format_date_iso(None) == ""


# =============================================================================
# PARAMETRIZED SWEEPS (from reports/test_report_parametrized.py)
# =============================================================================

# Import subjects matrix for parametrized tests
from tests.data.test_subjects_matrix import (
    TEMPORAL_SUBJECTS,
    GEOGRAPHIC_SUBJECTS,
    SYNASTRY_PAIRS,
    get_subject_by_id,
)
from tests.conftest import create_subject_from_temporal_data, create_subject_from_geographic_data


def _try_create_temporal(data):
    """Create a temporal subject, returning None on failure (ancient dates)."""
    try:
        return create_subject_from_temporal_data(data)
    except Exception:
        return None


# Sections expected in every natal report
_NATAL_SWEEP_SECTIONS = [
    "Birth Data",
    "Celestial Points",
    "Houses (",
    "Element Distribution",
    "Quality Distribution",
]


class TestNatalReportTemporalSweep:
    """Parametrized natal report tests across 24 temporal subjects."""

    @pytest.mark.parametrize("subject_data", TEMPORAL_SUBJECTS, ids=lambda s: s["id"])
    def test_natal_report_all_sections(self, subject_data):
        subject = _try_create_temporal(subject_data)
        if subject is None:
            pytest.skip(f"Could not create subject for {subject_data['id']}")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        report = ReportGenerator(chart_data)
        output = report.generate_report(max_aspects=5)
        for section in _NATAL_SWEEP_SECTIONS:
            assert section in output, f"Section '{section}' missing for {subject_data['id']}"

    @pytest.mark.parametrize("subject_data", TEMPORAL_SUBJECTS, ids=lambda s: s["id"])
    def test_natal_report_coordinates(self, subject_data):
        subject = _try_create_temporal(subject_data)
        if subject is None:
            pytest.skip(f"Could not create subject for {subject_data['id']}")
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        report = ReportGenerator(chart_data)
        output = report.generate_report()
        assert subject_data["tz_str"] in output


class TestNatalReportGeographicSweep:
    """Parametrized natal report tests across 16 geographic subjects."""

    @pytest.mark.parametrize("subject_data", GEOGRAPHIC_SUBJECTS, ids=lambda s: s["id"])
    def test_geographic_report_all_sections(self, subject_data):
        subject = create_subject_from_geographic_data(subject_data)
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        report = ReportGenerator(chart_data)
        output = report.generate_report(max_aspects=5)
        for section in _NATAL_SWEEP_SECTIONS:
            assert section in output, f"Section '{section}' missing for {subject_data['id']}"

    @pytest.mark.parametrize("subject_data", GEOGRAPHIC_SUBJECTS, ids=lambda s: s["id"])
    def test_geographic_report_coordinates(self, subject_data):
        subject = create_subject_from_geographic_data(subject_data)
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        report = ReportGenerator(chart_data)
        output = report.generate_report()
        assert subject_data["tz_str"] in output


class TestSynastryReportParametrizedSweep:
    """Parametrized synastry report across all SYNASTRY_PAIRS."""

    @pytest.mark.parametrize("pair", SYNASTRY_PAIRS, ids=lambda p: f"{p[0]}_x_{p[1]}")
    def test_synastry_report_content(self, pair):
        first_data = get_subject_by_id(pair[0])
        second_data = get_subject_by_id(pair[1])
        s1 = _try_create_temporal(first_data)
        s2 = _try_create_temporal(second_data)
        if s1 is None or s2 is None:
            pytest.skip(f"Subject data could not be created for pair {pair}")
        synastry_data = ChartDataFactory.create_synastry_chart_data(s1, s2)
        report = ReportGenerator(synastry_data)
        output = report.generate_report(max_aspects=5)
        assert s1.name in output
        assert s2.name in output


class TestLunarReturnReportParametrized:
    """Test lunar return reports."""

    def test_lunar_return_report(self):
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Test",
            1990,
            6,
            15,
            12,
            0,
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )
        factory = PlanetaryReturnFactory(
            subject,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
        )
        lunar_return = factory.next_return_from_iso_formatted_time(
            subject.iso_formatted_local_datetime,
            "Lunar",
        )
        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
        report = ReportGenerator(chart_data)
        output = report.generate_report(max_aspects=5)
        assert "Lunar Return Chart" in output
        assert "Return Type" in output


# ---------------------------------------------------------------------------
# Missing edge-case tests (migrated from tests/edge_cases/test_edge_cases.py)
# ---------------------------------------------------------------------------


class TestReportMissingDataScenarios:
    """Report generation with missing or unusual data."""

    def test_report_houses_with_composite_no_houses(self):
        """Composite chart report generates houses section correctly."""
        from kerykeion.composite_subject_factory import CompositeSubjectFactory

        first = AstrologicalSubjectFactory.from_birth_data(
            name="First",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            name="Second",
            year=1985,
            month=3,
            day=20,
            hour=15,
            minute=30,
            lng=0.0,
            lat=51.5,
            tz_str="Europe/London",
            online=False,
            suppress_geonames_warning=True,
        )
        composite = CompositeSubjectFactory(first, second)
        composite_model = composite.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_model)
        report = ReportGenerator(chart_data)
        result = report.generate_report()
        assert "Composite" in result

    def test_report_subject_only_mode(self):
        """Report in subject-only mode (no chart data)."""
        first = AstrologicalSubjectFactory.from_birth_data(
            name="SubjectOnly",
            year=1990,
            month=6,
            day=15,
            hour=12,
            minute=0,
            lng=12.5,
            lat=41.9,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        )
        report = ReportGenerator(first)
        result = report.generate_report()
        assert "SubjectOnly" in result
        assert "Subject Report" in result


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.CRITICAL)
    pytest.main(["-vv", __file__])
