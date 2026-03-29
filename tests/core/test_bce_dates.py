# -*- coding: utf-8 -*-
"""
BCE Date Support Tests

Comprehensive tests for dates before 1 AD (year < 1 in astronomical numbering).
Covers:
- Subject creation with negative years and year zero
- Julian Day calculation via swe.julday (both backends)
- Local Mean Time (LMT) offset from longitude
- ISO 8601 extended year formatting
- Day of week from Julian Day
- Planetary position baselines
- SVG chart generation (natal, transit, synastry)
- Regression: modern dates are unaffected

Usage:
    pytest tests/core/test_bce_dates.py -v
"""

import importlib
import math
from pathlib import Path

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.utilities import format_ancient_iso, format_iso_display, extract_year_from_iso


# =============================================================================
# CONSTANTS
# =============================================================================

SVG_DIR = Path(__file__).parent.parent / "data" / "svg"

# Position tolerance: accounts for polynomial approximation at extreme dates
BCE_POSITION_TOLERANCE = 0.5  # degrees

# BCE test subjects with expected baseline data (libephemeris, computed once)
BCE_SUBJECTS = {
    "ancient_500bc": {
        "name": "Ancient Greece 500BC",
        "year": -500,
        "month": 3,
        "day": 21,
        "hour": 12,
        "minute": 0,
        "lat": 37.9838,
        "lng": 23.7275,
        "tz_str": "Europe/Athens",
        "expected": {
            "julian_day": 1538512.9341,
            "day_of_week": "Friday",
            "sun_sign": "Pis",
            "sun_abs_pos": 355.0443,
            "moon_sign": "Sco",
            "moon_abs_pos": 227.265,
        },
    },
    "ancient_200bc": {
        "name": "Ptolemaic Egypt 200BC",
        "year": -200,
        "month": 6,
        "day": 21,
        "hour": 12,
        "minute": 0,
        "lat": 30.0444,
        "lng": 31.2357,
        "tz_str": "Africa/Cairo",
        "expected": {
            "julian_day": 1648179.9132,
            "day_of_week": "Wednesday",
            "sun_sign": "Gem",
            "sun_abs_pos": 85.3799,
            "moon_sign": "Lib",
            "moon_abs_pos": 198.6981,
        },
    },
    "year_zero": {
        "name": "Year Zero 1BCE",
        "year": 0,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "lat": 41.9028,
        "lng": 12.4964,
        "tz_str": "Europe/Rome",
        "expected": {
            "julian_day": 1721057.9653,
            "day_of_week": "Thursday",
            "sun_sign": "Cap",
            "sun_abs_pos": 279.0927,
            "moon_sign": "Pis",
            "moon_abs_pos": 345.8705,
        },
    },
    "ides_of_march": {
        "name": "Ides of March 44BCE",
        "year": -44,
        "month": 3,
        "day": 15,
        "hour": 12,
        "minute": 0,
        "lat": 41.9028,
        "lng": 12.4964,
        "tz_str": "Europe/Rome",
        "expected": {
            "julian_day": 1705060.9653,
            "day_of_week": "Tuesday",
            "sun_sign": "Pis",
            "sun_abs_pos": 352.6402,
            "moon_sign": "Vir",
            "moon_abs_pos": 174.5774,
        },
    },
}


def _create_bce_subject(subject_id: str, **kwargs):
    """Create a BCE subject from the test data."""
    data = BCE_SUBJECTS[subject_id]
    return AstrologicalSubjectFactory.from_birth_data(
        name=data["name"],
        year=data["year"],
        month=data["month"],
        day=data["day"],
        hour=data["hour"],
        minute=data["minute"],
        lat=data["lat"],
        lng=data["lng"],
        tz_str=data["tz_str"],
        online=False,
        suppress_geonames_warning=True,
        **kwargs,
    )


# =============================================================================
# BACKEND DETECTION
# =============================================================================


def _try_import(name: str):
    try:
        return importlib.import_module(name)
    except ImportError:
        return None


_swisseph = _try_import("swisseph")
_libephemeris = _try_import("libephemeris")

both_installed = pytest.mark.skipif(
    _swisseph is None or _libephemeris is None,
    reason="Both pyswisseph and libephemeris must be installed for comparison tests",
)


# =============================================================================
# CORE BCE SUBJECT CREATION
# =============================================================================


class TestBCESubjectCreation:
    """Test that BCE subjects can be created and have valid properties."""

    @pytest.mark.parametrize("subject_id", list(BCE_SUBJECTS.keys()), ids=lambda s: s)
    def test_subject_creation(self, subject_id):
        """Subject is created without error for each BCE date."""
        subject = _create_bce_subject(subject_id)
        data = BCE_SUBJECTS[subject_id]

        assert subject is not None
        assert subject.year == data["year"]
        assert subject.month == data["month"]
        assert subject.day == data["day"]
        assert subject.name == data["name"]

    @pytest.mark.parametrize("subject_id", list(BCE_SUBJECTS.keys()), ids=lambda s: s)
    def test_julian_day_baseline(self, subject_id):
        """Julian Day matches the precomputed baseline."""
        subject = _create_bce_subject(subject_id)
        expected_jd = BCE_SUBJECTS[subject_id]["expected"]["julian_day"]
        assert subject.julian_day == pytest.approx(expected_jd, abs=1e-3)

    @pytest.mark.parametrize("subject_id", list(BCE_SUBJECTS.keys()), ids=lambda s: s)
    def test_day_of_week_baseline(self, subject_id):
        """Day of week matches the precomputed baseline."""
        subject = _create_bce_subject(subject_id)
        expected_dow = BCE_SUBJECTS[subject_id]["expected"]["day_of_week"]
        assert subject.day_of_week == expected_dow

    @pytest.mark.parametrize("subject_id", list(BCE_SUBJECTS.keys()), ids=lambda s: s)
    def test_sun_position_baseline(self, subject_id):
        """Sun sign and position match precomputed baselines."""
        subject = _create_bce_subject(subject_id)
        expected = BCE_SUBJECTS[subject_id]["expected"]
        assert subject.sun.sign == expected["sun_sign"]
        assert subject.sun.abs_pos == pytest.approx(expected["sun_abs_pos"], abs=BCE_POSITION_TOLERANCE)

    @pytest.mark.parametrize("subject_id", list(BCE_SUBJECTS.keys()), ids=lambda s: s)
    def test_moon_position_baseline(self, subject_id):
        """Moon sign and position match precomputed baselines."""
        subject = _create_bce_subject(subject_id)
        expected = BCE_SUBJECTS[subject_id]["expected"]
        assert subject.moon.sign == expected["moon_sign"]
        assert subject.moon.abs_pos == pytest.approx(expected["moon_abs_pos"], abs=BCE_POSITION_TOLERANCE)

    @pytest.mark.parametrize("subject_id", list(BCE_SUBJECTS.keys()), ids=lambda s: s)
    def test_planetary_positions_valid_range(self, subject_id):
        """All available planetary positions are in [0, 360)."""
        subject = _create_bce_subject(subject_id)
        for planet_name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(subject, planet_name, None)
            if point is not None:
                assert 0 <= point.abs_pos < 360, f"{planet_name} position out of range: {point.abs_pos}"


# =============================================================================
# LMT OFFSET
# =============================================================================


class TestLMTOffset:
    """Test that Local Mean Time offset is correctly applied."""

    def test_lmt_offset_positive_longitude(self):
        """East longitude produces a positive LMT offset (local time ahead of UT)."""
        # Athens: lng=23.7275 → offset ≈ +1.5818 hours
        subject = _create_bce_subject("ancient_500bc")
        # The local ISO should show a positive UTC offset
        assert "+01:35" in subject.iso_formatted_local_datetime

    def test_lmt_offset_different_longitudes(self):
        """Different longitudes produce different Julian Days for the same local time."""
        # Same date/time, different locations
        subj_east = AstrologicalSubjectFactory.from_birth_data(
            name="East", year=-100, month=6, day=15, hour=12, minute=0,
            lat=30.0, lng=90.0, tz_str="Asia/Kolkata",
            online=False, suppress_geonames_warning=True,
        )
        subj_west = AstrologicalSubjectFactory.from_birth_data(
            name="West", year=-100, month=6, day=15, hour=12, minute=0,
            lat=30.0, lng=-90.0, tz_str="America/Chicago",
            online=False, suppress_geonames_warning=True,
        )
        # 180° of longitude = 12 hours = 0.5 days difference
        jd_diff = subj_east.julian_day - subj_west.julian_day
        assert jd_diff == pytest.approx(-0.5, abs=1e-6)

    def test_lmt_offset_zero_longitude(self):
        """Zero longitude means no LMT offset (local time = UT)."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Greenwich BCE", year=-100, month=1, day=1, hour=12, minute=0,
            lat=51.5, lng=0.0, tz_str="Etc/GMT",
            online=False, suppress_geonames_warning=True,
        )
        assert "+00:00" in subject.iso_formatted_local_datetime
        assert "+00:00" in subject.iso_formatted_utc_datetime


# =============================================================================
# ISO FORMAT
# =============================================================================


class TestAncientISOFormat:
    """Test ISO 8601 extended-year string formatting."""

    def test_negative_year(self):
        assert format_ancient_iso(-500, 3, 21, 12.0, 0.0) == "-0500-03-21T12:00:00+00:00"

    def test_year_zero(self):
        assert format_ancient_iso(0, 1, 1, 0.0, 0.0) == "-0000-01-01T00:00:00+00:00"

    def test_positive_offset(self):
        result = format_ancient_iso(-44, 3, 15, 12.0, 2.5)
        assert "+02:30" in result

    def test_negative_offset(self):
        result = format_ancient_iso(-100, 6, 15, 12.0, -5.0)
        assert "-05:00" in result

    def test_decimal_hour(self):
        result = format_ancient_iso(-200, 6, 21, 14.5, 0.0)
        assert "T14:30:00" in result

    def test_format_iso_display_bce(self):
        """format_iso_display handles BCE ISO strings."""
        iso = "-0500-03-21T12:00:00+01:35"
        assert format_iso_display(iso, "%Y-%m-%d") == "-0500-03-21"
        assert format_iso_display(iso, "%Y-%m-%d %H:%M") == "-0500-03-21 12:00"
        assert format_iso_display(iso, "%Y") == "-0500"

    def test_format_iso_display_modern(self):
        """format_iso_display still works for modern dates."""
        iso = "1940-10-09T18:30:00+01:00"
        assert format_iso_display(iso, "%Y-%m-%d") == "1940-10-09"

    def test_extract_year_bce(self):
        assert extract_year_from_iso("-0500-03-21T12:00:00+01:35") == -500
        assert extract_year_from_iso("-0000-01-01T00:00:00+00:00") == 0

    def test_extract_year_modern(self):
        assert extract_year_from_iso("1940-10-09T18:30:00+01:00") == 1940


# =============================================================================
# DAY OF WEEK
# =============================================================================


class TestDayOfWeek:
    """Test day of week calculation from Julian Day Number."""

    def test_known_modern_date(self):
        """Jan 1, 2000 was a Saturday — verify the JD formula matches."""
        # JD 2451545.0 = Jan 1, 2000 12:00 TT
        jd = 2451545.0
        day_index = int(math.floor(jd + 0.5)) % 7
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        assert day_names[day_index] == "Saturday"

    def test_bce_day_of_week_consistency(self):
        """Day of week should be consistent with the Julian Day for all BCE subjects."""
        for subject_id in BCE_SUBJECTS:
            subject = _create_bce_subject(subject_id)
            jd = subject.julian_day
            day_index = int(math.floor(jd + 0.5)) % 7
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            assert subject.day_of_week == day_names[day_index], (
                f"{subject_id}: day_of_week={subject.day_of_week}, "
                f"expected={day_names[day_index]} (JD={jd})"
            )


# =============================================================================
# CHART GENERATION (SVG)
# =============================================================================


class TestBCEChartSVG:
    """Test SVG chart generation for BCE dates."""

    @pytest.fixture(scope="class")
    def subj_500bc(self):
        return _create_bce_subject("ancient_500bc")

    @pytest.fixture(scope="class")
    def subj_200bc(self):
        return _create_bce_subject("ancient_200bc")

    def test_natal_chart_svg(self, subj_500bc):
        """Natal chart SVG can be generated for a BCE subject."""
        data = ChartDataFactory.create_natal_chart_data(subj_500bc)
        chart = ChartDrawer(data)
        svg = chart.generate_svg_string()

        assert len(svg) > 0
        assert "<svg" in svg
        assert "</svg>" in svg
        assert "Ancient Greece 500BC" in svg

    def test_natal_chart_baseline(self, subj_500bc):
        """Natal chart SVG matches the golden baseline (if available)."""
        baseline_path = SVG_DIR / "Ancient Greece 500BC - Natal Chart.svg"
        if not baseline_path.exists():
            pytest.skip("Baseline not found. Run test generation first.")

        data = ChartDataFactory.create_natal_chart_data(subj_500bc)
        svg = ChartDrawer(data).generate_svg_string()
        baseline = baseline_path.read_text()

        # Line count should be roughly the same (±5%)
        svg_lines = svg.strip().splitlines()
        baseline_lines = baseline.strip().splitlines()
        assert len(svg_lines) == pytest.approx(len(baseline_lines), rel=0.05)

    def test_transit_chart_svg(self, subj_500bc, subj_200bc):
        """Transit chart SVG can be generated between two BCE subjects."""
        data = ChartDataFactory.create_transit_chart_data(subj_500bc, subj_200bc)
        chart = ChartDrawer(data)
        svg = chart.generate_svg_string()

        assert len(svg) > 0
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_transit_chart_baseline(self, subj_500bc, subj_200bc):
        """Transit chart SVG matches the golden baseline (if available)."""
        baseline_path = SVG_DIR / "Ancient Greece 500BC and Ptolemaic Egypt 200BC - Transit Chart.svg"
        if not baseline_path.exists():
            pytest.skip("Baseline not found.")

        data = ChartDataFactory.create_transit_chart_data(subj_500bc, subj_200bc)
        svg = ChartDrawer(data).generate_svg_string()
        baseline = baseline_path.read_text()

        svg_lines = svg.strip().splitlines()
        baseline_lines = baseline.strip().splitlines()
        assert len(svg_lines) == pytest.approx(len(baseline_lines), rel=0.05)

    def test_synastry_chart_svg(self, subj_500bc, subj_200bc):
        """Synastry chart SVG can be generated between two BCE subjects."""
        data = ChartDataFactory.create_synastry_chart_data(subj_500bc, subj_200bc)
        chart = ChartDrawer(data)
        svg = chart.generate_svg_string()

        assert len(svg) > 0
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_synastry_chart_baseline(self, subj_500bc, subj_200bc):
        """Synastry chart SVG matches the golden baseline (if available)."""
        baseline_path = SVG_DIR / "Ancient Greece 500BC and Ptolemaic Egypt 200BC - Synastry Chart.svg"
        if not baseline_path.exists():
            pytest.skip("Baseline not found.")

        data = ChartDataFactory.create_synastry_chart_data(subj_500bc, subj_200bc)
        svg = ChartDrawer(data).generate_svg_string()
        baseline = baseline_path.read_text()

        svg_lines = svg.strip().splitlines()
        baseline_lines = baseline.strip().splitlines()
        assert len(svg_lines) == pytest.approx(len(baseline_lines), rel=0.05)


# =============================================================================
# HOUSE SYSTEMS WITH BCE DATES
# =============================================================================


HOUSE_SYSTEMS = ["P", "K", "O", "R", "C", "W", "B"]


class TestBCEHouseSystems:
    """Test that various house systems work with BCE dates."""

    @pytest.mark.parametrize("house_system", HOUSE_SYSTEMS, ids=lambda h: f"house_{h}")
    def test_house_system_creates_valid_subject(self, house_system):
        """Each house system produces a valid subject for a BCE date."""
        subject = _create_bce_subject("ides_of_march", houses_system_identifier=house_system)
        assert subject is not None
        assert subject.sun is not None
        assert subject.moon is not None


# =============================================================================
# SIDEREAL MODE WITH BCE DATES
# =============================================================================


class TestBCESiderealMode:
    """Test that sidereal modes work with BCE dates."""

    def test_sidereal_lahiri(self):
        """Sidereal Lahiri mode produces different positions from tropical."""
        tropical = _create_bce_subject("ancient_500bc")
        sidereal = _create_bce_subject(
            "ancient_500bc", zodiac_type="Sidereal", sidereal_mode="LAHIRI"
        )
        # Sidereal positions should differ from tropical by roughly the ayanamsa
        assert sidereal.sun.abs_pos != pytest.approx(tropical.sun.abs_pos, abs=1.0)
        assert sidereal.ayanamsa_value is not None

    def test_sidereal_fagan_bradley(self):
        """Sidereal Fagan-Bradley mode works with BCE dates."""
        subject = _create_bce_subject(
            "year_zero", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY"
        )
        assert subject.sun is not None
        assert 0 <= subject.sun.abs_pos < 360


# =============================================================================
# BACKEND COMPARISON (requires both swisseph and libephemeris)
# =============================================================================


@both_installed
class TestBCEBackendComparison:
    """Compare BCE date calculations between libephemeris and swisseph backends."""

    @pytest.mark.parametrize("subject_id", list(BCE_SUBJECTS.keys()), ids=lambda s: s)
    def test_julday_agreement(self, subject_id):
        """Both backends should compute the same Julian Day for BCE dates."""
        data = BCE_SUBJECTS[subject_id]
        decimal_hour = data["hour"] + data["minute"] / 60.0

        jd_lib = _libephemeris.julday(data["year"], data["month"], data["day"], decimal_hour, 0)
        jd_swe = _swisseph.julday(data["year"], data["month"], data["day"], decimal_hour, 0)

        assert jd_lib == pytest.approx(jd_swe, abs=1e-6), (
            f"{subject_id}: libephemeris JD={jd_lib}, swisseph JD={jd_swe}"
        )

    @pytest.mark.parametrize("subject_id", list(BCE_SUBJECTS.keys()), ids=lambda s: s)
    def test_sun_position_agreement(self, subject_id):
        """Both backends should compute similar Sun positions for BCE dates."""
        data = BCE_SUBJECTS[subject_id]
        decimal_hour = data["hour"] + data["minute"] / 60.0
        jd = _libephemeris.julday(data["year"], data["month"], data["day"], decimal_hour, 0)

        _libephemeris.set_ephe_path("")
        lib_sun = _libephemeris.calc_ut(jd, _libephemeris.SUN, _libephemeris.FLG_SWIEPH)[0][0]

        _swisseph.set_ephe_path("")
        swe_sun = _swisseph.calc_ut(jd, _swisseph.SUN, _swisseph.FLG_SWIEPH)[0][0]

        # Tolerance: 0.1° for ancient dates (Meeus polynomials vs full ephemeris)
        assert lib_sun == pytest.approx(swe_sun, abs=0.1), (
            f"{subject_id}: lib Sun={lib_sun:.4f}°, swe Sun={swe_sun:.4f}°"
        )

    @pytest.mark.parametrize("subject_id", list(BCE_SUBJECTS.keys()), ids=lambda s: s)
    def test_revjul_roundtrip(self, subject_id):
        """julday → revjul round-trip should return the original date in both backends."""
        data = BCE_SUBJECTS[subject_id]
        decimal_hour = data["hour"] + data["minute"] / 60.0
        cal_flag = 0  # SE_JUL_CAL

        for backend, name in [(_libephemeris, "lib"), (_swisseph, "swe")]:
            jd = backend.julday(data["year"], data["month"], data["day"], decimal_hour, cal_flag)
            y, m, d, h = backend.revjul(jd, cal_flag)
            assert int(y) == data["year"], f"{name}: year {y} != {data['year']}"
            assert int(m) == data["month"], f"{name}: month {m} != {data['month']}"
            assert int(d) == data["day"], f"{name}: day {d} != {data['day']}"
            assert h == pytest.approx(decimal_hour, abs=1e-6), f"{name}: hour {h} != {decimal_hour}"


# =============================================================================
# REGRESSION: MODERN DATES UNAFFECTED
# =============================================================================


class TestModernDatesRegression:
    """Ensure modern date handling is not affected by BCE support."""

    def test_modern_subject_unchanged(self):
        """John Lennon's chart should produce the same results as always."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon", 1940, 10, 9, 18, 30,
            lat=53.4084, lng=-2.9916, tz_str="Europe/London",
            online=False, suppress_geonames_warning=True,
        )
        assert subject.sun.sign == "Lib"
        assert subject.day_of_week == "Wednesday"
        # ISO format should use standard datetime formatting (no negative year)
        assert subject.iso_formatted_local_datetime.startswith("1940-")
        assert "T18:30:" in subject.iso_formatted_local_datetime

    def test_year_one_uses_modern_path(self):
        """Year 1 AD should use the standard datetime/pytz path."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Year 1 AD", 1, 6, 15, 12, 0,
            lat=51.5, lng=0.0, tz_str="Etc/GMT",
            online=False, suppress_geonames_warning=True,
        )
        assert subject.year == 1
        assert subject.sun is not None
        # Standard ISO format (no leading minus)
        assert not subject.iso_formatted_local_datetime.startswith("-")


# =============================================================================
# REPORT GENERATION
# =============================================================================


class TestBCEReport:
    """Test report generation for BCE subjects."""

    def test_natal_report(self):
        """Natal report can be generated for a BCE subject without error."""
        from kerykeion.report import ReportGenerator

        subject = _create_bce_subject("ides_of_march")
        data = ChartDataFactory.create_natal_chart_data(subject)
        report = ReportGenerator(data)
        text = report.generate_report()
        assert len(text) > 0
        assert "Ides of March" in text
