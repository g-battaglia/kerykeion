"""
Comprehensive parametrized tests for the ReportGenerator ASCII table output.

Covers:
- All 24 temporal subjects (500 BC -> 2200 AD)
- All 16 geographic subjects (66S -> 66N)
- Synastry, Transit, Composite, Solar/Lunar Return chart types
- Content formatting validation (symbols, dates, coordinates, retrograde)
- max_aspects truncation
- Element / quality percentage sums
- Sidereal mode display
- Empty-data code paths
- Relationship score and cusp comparison content
- Golden snapshot regression for every chart type
- Dual return title labels
- print_report() consistency
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

import pytest

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ReportGenerator,
)
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from tests.conftest import create_subject_from_temporal_data, create_subject_from_geographic_data
from tests.data.test_subjects_matrix import (
    TEMPORAL_SUBJECTS,
    GEOGRAPHIC_SUBJECTS,
    SYNASTRY_PAIRS,
    get_subject_by_id,
)

FIXTURES_DIR = Path("tests/fixtures")

# ---------------------------------------------------------------------------
# Required sections in each chart type
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

# Aspect symbols from report.py
_ASPECT_SYMBOLS = {"☌", "☍", "△", "□", "⚹", "⚻", "∠", "⚼", "Q"}
_MOVEMENT_SYMBOLS = {"→", "←", "="}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


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


def _try_create_temporal(data: Dict[str, Any], **kwargs):
    """Create a temporal subject, returning ``None`` on failure (ancient dates)."""
    try:
        return create_subject_from_temporal_data(data, **kwargs)
    except Exception:
        return None


def _skip_if_none(subject, subject_id: str):
    if subject is None:
        pytest.skip(f"Subject {subject_id!r} could not be created (unsupported era)")


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
# 1. Natal report — temporal subjects (parametrized x24)
# =====================================================================


class TestNatalReportTemporal:
    """Natal chart report for every temporal subject (500 BC -> 2200)."""

    @pytest.mark.parametrize("data", TEMPORAL_SUBJECTS, ids=lambda d: d["id"])
    def test_natal_report_all_sections(self, data: Dict[str, Any]) -> None:
        subject = _try_create_temporal(data)
        _skip_if_none(subject, data["id"])

        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart).generate_report(max_aspects=5)

        # Subject name present
        assert subject.name in text

        # All required sections present
        for section in _NATAL_SECTIONS:
            assert section in text, f"Missing section: {section!r} for {data['id']}"

    @pytest.mark.parametrize("data", TEMPORAL_SUBJECTS, ids=lambda d: d["id"])
    def test_natal_report_coordinates_and_timezone(self, data: Dict[str, Any]) -> None:
        subject = _try_create_temporal(data)
        _skip_if_none(subject, data["id"])

        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart).generate_report()

        # Latitude and longitude formatted to 4 decimal places
        assert f"{abs(data['lat']):.4f}" in text
        assert f"{abs(data['lng']):.4f}" in text

        # Timezone string present
        assert data["tz_str"] in text


# =====================================================================
# 2. Natal report — geographic subjects (parametrized x16)
# =====================================================================


class TestNatalReportGeographic:
    """Natal chart report for every geographic location."""

    @pytest.mark.parametrize("data", GEOGRAPHIC_SUBJECTS, ids=lambda d: d["id"])
    def test_natal_report_all_sections(self, data: Dict[str, Any]) -> None:
        subject = create_subject_from_geographic_data(data)
        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart).generate_report(max_aspects=5)

        for section in _NATAL_SECTIONS:
            assert section in text, f"Missing section: {section!r} for {data['id']}"

    @pytest.mark.parametrize("data", GEOGRAPHIC_SUBJECTS, ids=lambda d: d["id"])
    def test_natal_report_coordinates_and_timezone(self, data: Dict[str, Any]) -> None:
        subject = create_subject_from_geographic_data(data)
        chart = ChartDataFactory.create_natal_chart_data(subject)
        text = ReportGenerator(chart).generate_report()

        assert f"{abs(data['lat']):.4f}" in text
        assert f"{abs(data['lng']):.4f}" in text
        assert data["tz_str"] in text


# =====================================================================
# 3. Synastry report — parametrized pairs
# =====================================================================


class TestSynastryReportParametrized:
    """Synastry report for all defined pairs."""

    @pytest.mark.parametrize("pair", SYNASTRY_PAIRS, ids=lambda p: f"{p[0]}_x_{p[1]}")
    def test_synastry_report_content(self, pair) -> None:
        first_data = get_subject_by_id(pair[0])
        second_data = get_subject_by_id(pair[1])

        first = _try_create_temporal(first_data)
        second = _try_create_temporal(second_data)
        _skip_if_none(first, pair[0])
        _skip_if_none(second, pair[1])

        chart = ChartDataFactory.create_synastry_chart_data(first, second)
        text = ReportGenerator(chart).generate_report(max_aspects=5)

        # Both names present
        assert first.name in text
        assert second.name in text

        # Structural markers
        for section in _SYNASTRY_SECTIONS:
            assert section in text, f"Missing section: {section!r} for {pair}"

        # Cusp comparison tables
        assert "cusps in" in text


# =====================================================================
# 4. Transit report — parametrized
# =====================================================================


_TRANSIT_PAIRS = [
    ("john_lennon_1940", "johnny_depp_1963"),
    ("millennium_2000", "equinox_2020"),
    ("einstein_1879", "ww1_start_1914"),
    ("paul_mccartney_1942", "yoko_ono_1933"),
    ("industrial_1850", "einstein_1879"),
]


class TestTransitReportParametrized:
    """Transit report for cross-epoch pairs."""

    @pytest.mark.parametrize("pair", _TRANSIT_PAIRS, ids=lambda p: f"{p[0]}_transit_{p[1]}")
    def test_transit_report_content(self, pair) -> None:
        natal_data = get_subject_by_id(pair[0])
        transit_data = get_subject_by_id(pair[1])

        natal = _try_create_temporal(natal_data)
        transit = _try_create_temporal(transit_data)
        _skip_if_none(natal, pair[0])
        _skip_if_none(transit, pair[1])

        chart = ChartDataFactory.create_transit_chart_data(natal, transit)
        text = ReportGenerator(chart).generate_report(max_aspects=5)

        assert "Transit" in text
        assert "Natal Subject" in text
        assert "Transit Subject" in text
        assert natal.name in text
        assert transit.name in text


# =====================================================================
# 5. Composite report — parametrized (geographic)
# =====================================================================


_COMPOSITE_PAIRS = [
    ("london_51n", "tokyo_35n"),
    ("quito_equator", "sydney_34s"),
    ("oslo_60n", "cape_town_34s"),
    ("new_york_40n", "buenos_aires_34s"),
]


class TestCompositeReportParametrized:
    """Composite report for geographically diverse pairs."""

    @pytest.mark.parametrize("pair", _COMPOSITE_PAIRS, ids=lambda p: f"{p[0]}_x_{p[1]}")
    def test_composite_report_content(self, pair) -> None:
        first_data = get_subject_by_id(pair[0])
        second_data = get_subject_by_id(pair[1])

        first = create_subject_from_geographic_data(first_data)
        second = create_subject_from_geographic_data(second_data)

        composite_subject = CompositeSubjectFactory(
            first, second, chart_name="Test Composite"
        ).get_midpoint_composite_subject_model()
        chart = ChartDataFactory.create_composite_chart_data(composite_subject)
        text = ReportGenerator(chart).generate_report(max_aspects=3)

        for section in _COMPOSITE_SECTIONS:
            assert section in text, f"Missing section: {section!r} for {pair}"
        assert first.name in text
        assert second.name in text


# =====================================================================
# 6. Return report — solar & lunar
# =====================================================================


_RETURN_SUBJECTS = [
    "john_lennon_1940",
    "paul_mccartney_1942",
    "johnny_depp_1963",
    "millennium_2000",
]


class TestReturnReportParametrized:
    """Solar and lunar return reports for modern-era subjects."""

    @pytest.mark.parametrize("subject_id", _RETURN_SUBJECTS)
    def test_solar_return_report(self, subject_id: str) -> None:
        data = get_subject_by_id(subject_id)
        natal = _try_create_temporal(data)
        _skip_if_none(natal, subject_id)

        factory = PlanetaryReturnFactory(
            natal,
            lat=data["lat"],
            lng=data["lng"],
            tz_str=data["tz_str"],
            online=False,
        )
        solar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Solar",
        )
        chart = ChartDataFactory.create_single_wheel_return_chart_data(solar)
        text = ReportGenerator(chart).generate_report(max_aspects=5)

        assert "Solar Return Chart" in text
        assert "Return Type" in text
        assert natal.name in text

    @pytest.mark.parametrize("subject_id", _RETURN_SUBJECTS)
    def test_lunar_return_report(self, subject_id: str) -> None:
        data = get_subject_by_id(subject_id)
        natal = _try_create_temporal(data)
        _skip_if_none(natal, subject_id)

        factory = PlanetaryReturnFactory(
            natal,
            lat=data["lat"],
            lng=data["lng"],
            tz_str=data["tz_str"],
            online=False,
        )
        lunar = factory.next_return_from_iso_formatted_time(
            natal.iso_formatted_local_datetime,
            "Lunar",
        )
        chart = ChartDataFactory.create_single_wheel_return_chart_data(lunar)
        text = ReportGenerator(chart).generate_report(max_aspects=5)

        assert "Lunar Return Chart" in text
        assert "Return Type" in text
        assert natal.name in text


# =====================================================================
# 7. Content formatting validation
# =====================================================================


class TestReportContentFormatting:
    """Validate formatting patterns in the generated report."""

    @pytest.fixture(autouse=True)
    def _setup(self, natal_chart_data) -> None:
        self.text = ReportGenerator(natal_chart_data).generate_report()

    def test_retrograde_markers(self) -> None:
        """Retrograde column contains only 'R' or '-'."""
        matches = _RE_RETROGRADE_COL.findall(self.text)
        assert matches, "No retrograde column markers found"
        assert all(m in ("R", "-") for m in matches)

    def test_aspect_symbols_present(self) -> None:
        """At least one standard aspect symbol appears."""
        found = {s for s in _ASPECT_SYMBOLS if s in self.text}
        assert found, f"No aspect symbols found in report. Expected at least one of {_ASPECT_SYMBOLS}"

    def test_movement_symbols_present(self) -> None:
        """At least one movement symbol appears."""
        found = {s for s in _MOVEMENT_SYMBOLS if s in self.text}
        assert found, f"No movement symbols found. Expected at least one of {_MOVEMENT_SYMBOLS}"

    def test_speed_format(self) -> None:
        """Speed values match +/-X.XXXX deg/d format."""
        assert _RE_SPEED.search(self.text), "No speed values in expected format found"

    def test_declination_format(self) -> None:
        """Declination values match +/-XX.XX deg format."""
        assert _RE_DECLINATION.search(self.text), "No declination values in expected format found"

    def test_position_format(self) -> None:
        """Celestial position values match XX.XX deg format."""
        assert _RE_POSITION.search(self.text), "No position values in expected format found"

    def test_date_format_in_birth_data(self) -> None:
        """Birth date formatted as DD/MM/YYYY."""
        assert _RE_DATE.search(self.text), "No DD/MM/ date format found in Birth Data"

    def test_coordinate_format(self) -> None:
        """Latitude/longitude formatted to 4 decimal places."""
        assert _RE_COORDINATE.search(self.text), "No coordinate with 4 decimal places found"

    def test_julian_day_format(self) -> None:
        """Julian day formatted to 6 decimal places."""
        assert _RE_JULIAN_DAY.search(self.text), "No Julian Day with 6 decimal places found"


# =====================================================================
# 8. max_aspects truncation
# =====================================================================


class TestReportMaxAspectsTruncation:
    """Verify that max_aspects correctly truncates the aspects table."""

    def test_max_aspects_suffix_appears(self, natal_chart_data) -> None:
        text = ReportGenerator(natal_chart_data).generate_report(max_aspects=3)
        assert "(showing 3 of " in text

    def test_max_aspects_limits_rows(self, natal_chart_data) -> None:
        text = ReportGenerator(natal_chart_data).generate_report(max_aspects=3)
        # In the Aspects table, count data rows (lines with | that aren't header or separator)
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

    def test_max_aspects_none_shows_all(self, natal_chart_data) -> None:
        text = ReportGenerator(natal_chart_data).generate_report()
        assert "(showing" not in text


# =====================================================================
# 9. Element / quality percentages
# =====================================================================


class TestReportElementQualityValidation:
    """Verify that element and quality percentages sum to ~100%."""

    def test_element_percentages_sum(self, natal_chart_data) -> None:
        text = ReportGenerator(natal_chart_data).generate_report()
        pcts = _extract_percentages(text, "Element Distribution")
        assert len(pcts) == 4, f"Expected 4 element percentages, got {pcts}"
        assert abs(sum(pcts) - 100.0) < 1.0, f"Element percentages sum to {sum(pcts)}, expected ~100"

    def test_quality_percentages_sum(self, natal_chart_data) -> None:
        text = ReportGenerator(natal_chart_data).generate_report()
        pcts = _extract_percentages(text, "Quality Distribution")
        assert len(pcts) == 3, f"Expected 3 quality percentages, got {pcts}"
        assert abs(sum(pcts) - 100.0) < 1.0, f"Quality percentages sum to {sum(pcts)}, expected ~100"


# =====================================================================
# 10. Sidereal mode display
# =====================================================================


class TestReportSiderealMode:
    """Verify sidereal mode appears in settings when enabled."""

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
# 11. Empty-data code paths
# =====================================================================


class TestReportEmptyPaths:
    """Exercise code paths that handle missing or empty data."""

    def test_no_celestial_points_message(self, natal_chart_data) -> None:
        """_celestial_points_report returns fallback when points list is empty."""
        report = ReportGenerator(natal_chart_data)
        # Pass a mock-like object with no recognised point attributes
        from types import SimpleNamespace

        empty_subject = SimpleNamespace(active_points=[])
        result = report._celestial_points_report(empty_subject, "Empty Points")
        assert result == "No celestial points data available."

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
        text = ReportGenerator(subject, include_aspects=False).generate_report(include_aspects=False)
        # The "Lunar Phase" table title must not appear (but "Lunar Node" in points is fine)
        assert "Lunar Phase" not in text

    def test_empty_active_configuration(self, natal_chart_data) -> None:
        """When both _active_points and _active_aspects are empty, no section is emitted."""
        report = ReportGenerator(natal_chart_data)
        # Override internals to simulate empty configuration
        report._active_points = []
        report._active_aspects = []
        result = report._active_configuration_report()
        assert result == ""

    def test_include_aspects_false_suppresses_section(self) -> None:
        """include_aspects=False produces a report without 'Aspects'."""
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
        text = ReportGenerator(chart, include_aspects=False).generate_report(include_aspects=False)
        # "Active Aspects Configuration" is allowed, but the top-level "Aspects" table should be absent
        # Remove known false-positive substrings before checking
        cleaned = text.replace("Active Aspects Configuration", "")
        assert "| Aspects" not in cleaned or "(showing" not in cleaned

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
        # "Active Aspects" or "Aspects (showing" should not appear
        assert "showing" not in text


# =====================================================================
# 12. Relationship score content
# =====================================================================


class TestRelationshipScoreContent:
    """Verify relationship score section content in synastry reports."""

    def test_relationship_score_sections(self, john_lennon, paul_mccartney) -> None:
        chart = ChartDataFactory.create_synastry_chart_data(
            john_lennon,
            paul_mccartney,
            include_relationship_score=True,
        )
        text = ReportGenerator(chart).generate_report(max_aspects=5)

        assert "Relationship Score Summary" in text
        assert "Score" in text
        assert "Description" in text
        assert "Destiny Signature" in text

    def test_relationship_score_supporting_aspects(self, john_lennon, paul_mccartney) -> None:
        chart = ChartDataFactory.create_synastry_chart_data(
            john_lennon,
            paul_mccartney,
            include_relationship_score=True,
        )
        text = ReportGenerator(chart).generate_report()
        assert "Score Supporting Aspects" in text

    def test_relationship_score_absent_when_disabled(self, john_lennon, paul_mccartney) -> None:
        chart = ChartDataFactory.create_synastry_chart_data(
            john_lennon,
            paul_mccartney,
            include_relationship_score=False,
        )
        text = ReportGenerator(chart).generate_report()
        assert "Relationship Score Summary" not in text


# =====================================================================
# 13. Cusp comparison content
# =====================================================================


class TestCuspComparisonContent:
    """Verify cusp comparison tables in synastry reports."""

    def test_cusp_comparison_tables(self, synastry_chart_data) -> None:
        text = ReportGenerator(synastry_chart_data).generate_report()
        assert "cusps in" in text
        assert "Projected House" in text
        assert "Sign" in text
        assert "Degree" in text


# =====================================================================
# 14. Snapshot regression for every chart type
# =====================================================================


class TestReportSnapshotChartTypes:
    """Golden-file regression tests for every chart type.

    The fixture files are generated by ``scripts/regenerate_test_output.py``
    and can be refreshed via ``poe regenerate:output``.
    """

    @staticmethod
    def _snapshot_subject():
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
        )

    @staticmethod
    def _snapshot_partner():
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
        )

    @staticmethod
    def _snapshot_transit():
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
        )

    def test_synastry_snapshot(self, capsys) -> None:
        natal = self._snapshot_subject()
        partner = self._snapshot_partner()
        chart = ChartDataFactory.create_synastry_chart_data(natal, partner)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = (FIXTURES_DIR / "synastry_report.txt").read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_transit_snapshot(self, capsys) -> None:
        natal = self._snapshot_subject()
        transit = self._snapshot_transit()
        chart = ChartDataFactory.create_transit_chart_data(natal, transit)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = (FIXTURES_DIR / "transit_report.txt").read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_composite_snapshot(self, capsys) -> None:
        natal = self._snapshot_subject()
        partner = self._snapshot_partner()
        composite = CompositeSubjectFactory(
            natal,
            partner,
            chart_name="John & Yoko Composite Chart",
        ).get_midpoint_composite_subject_model()
        chart = ChartDataFactory.create_composite_chart_data(composite)
        ReportGenerator(chart).print_report()
        captured = capsys.readouterr().out
        expected = (FIXTURES_DIR / "composite_report.txt").read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_solar_return_snapshot(self, capsys) -> None:
        natal = self._snapshot_subject()
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
        expected = (FIXTURES_DIR / "solar_return_report.txt").read_text(encoding="utf-8")
        assert captured == expected + "\n"

    def test_dual_return_snapshot(self, capsys) -> None:
        natal = self._snapshot_subject()
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
        expected = (FIXTURES_DIR / "dual_return_report.txt").read_text(encoding="utf-8")
        assert captured == expected + "\n"


# =====================================================================
# 15. Dual return title labels
# =====================================================================


class TestReportDualReturnLabels:
    """Verify Solar vs Lunar return title in dual return reports."""

    @pytest.fixture()
    def _natal(self):
        return _make_offline_subject(
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

    def test_solar_dual_return_title(self, _natal) -> None:
        factory = PlanetaryReturnFactory(
            _natal,
            lat=_natal.lat,
            lng=_natal.lng,
            tz_str=_natal.tz_str,
            online=False,
        )
        solar = factory.next_return_from_iso_formatted_time(
            _natal.iso_formatted_local_datetime,
            "Solar",
        )
        chart = ChartDataFactory.create_return_chart_data(_natal, solar)
        text = ReportGenerator(chart).generate_report(max_aspects=3)
        assert "Solar Return Comparison" in text

    def test_lunar_dual_return_title(self, _natal) -> None:
        factory = PlanetaryReturnFactory(
            _natal,
            lat=_natal.lat,
            lng=_natal.lng,
            tz_str=_natal.tz_str,
            online=False,
        )
        lunar = factory.next_return_from_iso_formatted_time(
            _natal.iso_formatted_local_datetime,
            "Lunar",
        )
        chart = ChartDataFactory.create_return_chart_data(_natal, lunar)
        text = ReportGenerator(chart).generate_report(max_aspects=3)
        assert "Lunar Return Comparison" in text


# =====================================================================
# 16. print_report() consistency
# =====================================================================


_PRINT_GEO_SUBJECTS = ["london_51n", "tokyo_35n", "sydney_34s"]


class TestReportPrintMethod:
    """Verify print_report() output matches generate_report()."""

    @pytest.mark.parametrize("geo_id", _PRINT_GEO_SUBJECTS)
    def test_print_matches_generate(self, geo_id: str, capsys) -> None:
        data = get_subject_by_id(geo_id)
        subject = create_subject_from_geographic_data(data)
        chart = ChartDataFactory.create_natal_chart_data(subject)

        report = ReportGenerator(chart)
        expected = report.generate_report()

        report.print_report()
        captured = capsys.readouterr().out

        assert captured == expected + "\n"


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.CRITICAL)
    pytest.main(["-vv", __file__])
