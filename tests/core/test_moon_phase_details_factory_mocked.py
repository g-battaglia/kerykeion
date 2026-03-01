"""
Mocked unit tests for MoonPhaseDetailsFactory.

These tests mock the Swiss Ephemeris utility layer so the factory logic can be
verified without ephemeris data files or real swe calls. This isolates the
factory's orchestration, model assembly, and edge-case handling.

Mocking strategy:
    All five Swiss Ephemeris utility functions imported by factory.py are
    patched via ``kerykeion.moon_phase_details.factory.<function>``:
        - compute_lunar_phase_jd
        - compute_next_solar_eclipse_jd
        - compute_next_lunar_eclipse_jd
        - compute_sun_rise_set_swe
        - compute_sun_position
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.moon_phase_details.factory import (
    MoonPhaseDetailsFactory,
    _compute_major_phase_name,
    _create_event_moment,
    _compute_lunar_phase_metrics,
    _build_moon_zodiac_info,
)
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    LunarPhaseModel,
    MoonPhaseOverviewModel,
    MoonPhaseIlluminationDetailsModel,
    MoonPhaseUpcomingPhasesModel,
    MoonPhaseMajorPhaseWindowModel,
    MoonPhaseEventMomentModel,
)


# ---------------------------------------------------------------------------
# Constants for mock data
# ---------------------------------------------------------------------------

# Julian Day for 1993-10-10 12:12:00 UTC (reference moment)
_REF_JD = 2449271.00833

# Julian Days for surrounding phase events (realistic values for Oct 1993)
_LAST_NEW_MOON_JD = 2449261.28738  # Sep 30, 1993 ~18:53 UTC
_NEXT_NEW_MOON_JD = 2449276.98328  # Oct 15, 1993 ~11:35 UTC
_LAST_FIRST_QUARTER_JD = 2449269.31616  # Oct 8, 1993 ~19:35 UTC
_NEXT_FIRST_QUARTER_JD = 2449282.86945  # Oct 22, 1993 ~08:52 UTC
_LAST_FULL_MOON_JD = 2449247.63213  # Sep 16, 1993 ~03:10 UTC
_NEXT_FULL_MOON_JD = 2449291.02613  # Oct 30, 1993 ~12:37 UTC
_LAST_QUARTER_LAST_JD = 2449253.31394  # Sep 22, 1993 ~19:32 UTC
_LAST_QUARTER_NEXT_JD = 2449299.77491  # Nov 7, 1993 ~06:35 UTC

# Eclipse Julian Days
_LUNAR_ECLIPSE_JD = 2449320.76813  # Nov 29, 1993
_SOLAR_ECLIPSE_JD = 2449305.40616  # Nov 13, 1993

# Sunrise/sunset Julian Days for London on Oct 10, 1993
_SUNRISE_JD = 2449270.80208
_SUNSET_JD = 2449271.26250


# ---------------------------------------------------------------------------
# Patch target prefix
# ---------------------------------------------------------------------------
_FACTORY = "kerykeion.moon_phase_details.factory"


# ---------------------------------------------------------------------------
# Mock subject builder
# ---------------------------------------------------------------------------


def _make_mock_subject(
    *,
    name: str = "Mock Subject",
    year: int = 1993,
    month: int = 10,
    day: int = 10,
    hour: int = 12,
    minute: int = 12,
    lat: float = 51.50853,
    lng: float = -0.12574,
    tz_str: str = "Europe/London",
    iso_utc: str = "1993-10-10T11:12:00+00:00",
    iso_local: str = "1993-10-10T12:12:00+01:00",
    degrees_between: float = 290.65,
    moon_phase: int = 23,
    moon_emoji: str = "\U0001f318",
    moon_phase_name: str = "Waning Crescent",
    sun_sign: str = "Lib",
    moon_sign: str = "Leo",
    has_lunar_phase: bool = True,
) -> MagicMock:
    """Create a mock AstrologicalSubjectModel with predictable attributes."""
    subject = MagicMock(spec=AstrologicalSubjectModel)
    subject.name = name
    subject.year = year
    subject.month = month
    subject.day = day
    subject.hour = hour
    subject.minute = minute
    subject.lat = lat
    subject.lng = lng
    subject.tz_str = tz_str
    subject.iso_formatted_utc_datetime = iso_utc
    subject.iso_formatted_local_datetime = iso_local
    subject.city = "London"
    subject.nation = "GB"

    if has_lunar_phase:
        lunar = MagicMock(spec=LunarPhaseModel)
        lunar.degrees_between_s_m = degrees_between
        lunar.moon_phase = moon_phase
        lunar.moon_emoji = moon_emoji
        lunar.moon_phase_name = moon_phase_name
        subject.lunar_phase = lunar
    else:
        subject.lunar_phase = None

    sun = SimpleNamespace(sign=sun_sign)
    moon = SimpleNamespace(sign=moon_sign)
    subject.sun = sun
    subject.moon = moon

    return subject


def _side_effect_lunar_phase_jd(jd_start: float, target_angle: float, forward: bool = True) -> Optional[float]:
    """Deterministic mock for compute_lunar_phase_jd returning realistic JDs."""
    lookup = {
        (0.0, False): _LAST_NEW_MOON_JD,
        (0.0, True): _NEXT_NEW_MOON_JD,
        (90.0, False): _LAST_FIRST_QUARTER_JD,
        (90.0, True): _NEXT_FIRST_QUARTER_JD,
        (180.0, False): _LAST_FULL_MOON_JD,
        (180.0, True): _NEXT_FULL_MOON_JD,
        (270.0, False): _LAST_QUARTER_LAST_JD,
        (270.0, True): _LAST_QUARTER_NEXT_JD,
    }
    return lookup.get((target_angle, forward))


# ---------------------------------------------------------------------------
# 1. Pure utility function tests (no mocking needed)
# ---------------------------------------------------------------------------


class TestComputeMajorPhaseName:
    """Test _compute_major_phase_name for correct nearest-phase classification."""

    @pytest.mark.parametrize(
        "angle, expected",
        [
            (0.0, "New Moon"),
            (5.0, "New Moon"),
            (44.0, "New Moon"),
            (46.0, "First Quarter"),
            (89.0, "First Quarter"),
            (90.0, "First Quarter"),
            (91.0, "First Quarter"),
            (135.0, "First Quarter"),  # equidistant: min() picks first in list
            (180.0, "Full Moon"),
            (225.0, "Full Moon"),  # equidistant: min() picks first in list
            (270.0, "Last Quarter"),
            (315.0, "New Moon"),
            (355.0, "New Moon"),
            (359.9, "New Moon"),
            (360.0, "New Moon"),  # wraps to 0
        ],
    )
    def test_nearest_major_phase(self, angle: float, expected: str) -> None:
        assert _compute_major_phase_name(angle) == expected


class TestCreateEventMoment:
    """Test _create_event_moment timestamp formatting and day calculation."""

    def test_past_event(self) -> None:
        event_dt = datetime(1993, 9, 30, 18, 53, 51, tzinfo=timezone.utc)
        ref_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        moment = _create_event_moment(event_dt, ref_dt, is_past=True)

        assert moment.timestamp == int(event_dt.timestamp())
        assert moment.datestamp is not None and "30 Sep 1993" in moment.datestamp
        assert moment.days_ago is not None
        assert moment.days_ago == 10  # ~9.68 days rounds to 10
        assert moment.days_ahead is None

    def test_future_event(self) -> None:
        event_dt = datetime(1993, 10, 15, 11, 35, 55, tzinfo=timezone.utc)
        ref_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        moment = _create_event_moment(event_dt, ref_dt, is_past=False)

        assert moment.timestamp == int(event_dt.timestamp())
        assert moment.datestamp is not None and "15 Oct 1993" in moment.datestamp
        assert moment.days_ahead is not None
        assert moment.days_ahead == 5  # ~5.02 days rounds to 5
        assert moment.days_ago is None


class TestBuildMoonZodiacInfo:
    """Test _build_moon_zodiac_info with various input combinations."""

    def test_valid_signs(self) -> None:
        sun = SimpleNamespace(sign="Lib")
        moon = SimpleNamespace(sign="Leo")
        result = _build_moon_zodiac_info(sun, moon)
        assert result is not None
        assert result.sun_sign == "Lib"
        assert result.moon_sign == "Leo"

    def test_none_sun(self) -> None:
        moon = SimpleNamespace(sign="Leo")
        assert _build_moon_zodiac_info(None, moon) is None

    def test_none_moon(self) -> None:
        sun = SimpleNamespace(sign="Lib")
        assert _build_moon_zodiac_info(sun, None) is None

    def test_empty_sign(self) -> None:
        sun = SimpleNamespace(sign="")
        moon = SimpleNamespace(sign="Leo")
        assert _build_moon_zodiac_info(sun, moon) is None


# ---------------------------------------------------------------------------
# 2. Factory.from_subject with fully mocked Swiss Ephemeris layer
# ---------------------------------------------------------------------------


class TestFactoryFromSubjectMocked:
    """Test MoonPhaseDetailsFactory.from_subject with mocked swe utilities."""

    @pytest.fixture(autouse=True)
    def _patch_swe(self):
        """Patch all Swiss Ephemeris utility functions used by the factory."""
        # ECL_TOTAL=4, ECL_PARTIAL=16 in Swiss Ephemeris
        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", side_effect=_side_effect_lunar_phase_jd),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=(16, _SOLAR_ECLIPSE_JD)),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=(4, _LUNAR_ECLIPSE_JD)),
            patch(f"{_FACTORY}.compute_sun_rise_set_swe", return_value=(_SUNRISE_JD, _SUNSET_JD)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(31.25, 169.67, 149_200_000.0)),
        ):
            yield

    def test_returns_overview_model(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        assert isinstance(overview, MoonPhaseOverviewModel)

    def test_timestamp_and_datestamp(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        assert overview.timestamp > 0
        assert "1993" in overview.datestamp

    def test_moon_summary_phase_fields(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        moon = overview.moon

        assert moon.phase is not None
        assert moon.phase_name == "Waning Crescent"
        assert moon.emoji == "\U0001f318"
        assert moon.stage == "waning"
        assert moon.major_phase == "Last Quarter"

    def test_illumination_computation(self) -> None:
        """Verify k = 0.5 * (1 - cos(angle)) formula."""
        subject = _make_mock_subject(degrees_between=290.65)
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        moon = overview.moon

        expected_frac = 0.5 * (1.0 - math.cos(math.radians(290.65)))
        expected_pct = round(expected_frac * 100)

        assert moon.illumination == f"{expected_pct}%"
        assert moon.detailed is not None
        assert moon.detailed.illumination_details is not None
        assert moon.detailed.illumination_details.percentage == expected_pct
        assert moon.detailed.illumination_details.visible_fraction is not None
        assert abs(moon.detailed.illumination_details.visible_fraction - expected_frac) < 1e-6
        assert moon.detailed.illumination_details.phase_angle is not None
        assert abs(moon.detailed.illumination_details.phase_angle - 290.65) < 1e-6

    def test_age_days_from_last_new_moon(self) -> None:
        """Age should be computed from actual last new moon, not approximation."""
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        # Age should be roughly 10 days (Oct 10 - Sep 30)
        assert overview.moon.age_days is not None
        assert 9 <= overview.moon.age_days <= 11

    def test_zodiac_info(self) -> None:
        subject = _make_mock_subject(sun_sign="Lib", moon_sign="Leo")
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.moon.zodiac is not None
        assert overview.moon.zodiac.sun_sign == "Lib"
        assert overview.moon.zodiac.moon_sign == "Leo"

    def test_upcoming_phases_populated(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        phases = overview.moon.detailed.upcoming_phases

        assert phases is not None
        assert phases.new_moon is not None
        assert phases.new_moon.last is not None
        assert phases.new_moon.next is not None
        assert phases.first_quarter is not None
        assert phases.full_moon is not None
        assert phases.last_quarter is not None

    def test_next_lunar_eclipse(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.moon.next_lunar_eclipse is not None
        assert overview.moon.next_lunar_eclipse.timestamp is not None
        assert overview.moon.next_lunar_eclipse.type == "Total Lunar Eclipse"

    def test_sun_info_populated(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.sun is not None
        assert overview.sun.sunrise_timestamp is not None
        assert overview.sun.sunset_timestamp is not None
        assert overview.sun.solar_noon is not None
        assert overview.sun.day_length is not None

    def test_sun_position_populated(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.sun.position is not None
        assert overview.sun.position.altitude == pytest.approx(31.25)
        assert overview.sun.position.azimuth == pytest.approx(169.67)

    def test_next_solar_eclipse(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.sun.next_solar_eclipse is not None
        assert overview.sun.next_solar_eclipse.timestamp is not None
        assert overview.sun.next_solar_eclipse.type is not None
        assert "Partial Solar Eclipse" in overview.sun.next_solar_eclipse.type

    def test_location_populated(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.location is not None
        assert overview.location.latitude == "51.50853"
        assert overview.location.longitude == "-0.12574"

    def test_using_default_location_flag(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject, using_default_location=True)

        assert overview.location.using_default_location is True


# ---------------------------------------------------------------------------
# 3. Edge cases: missing/failing Swiss Ephemeris data
# ---------------------------------------------------------------------------


class TestFactoryEdgeCasesNullReturns:
    """Test factory gracefully handles None returns from swe utilities."""

    def test_no_lunar_phase_on_subject(self) -> None:
        """Subject without lunar_phase should produce minimal moon summary."""
        subject = _make_mock_subject(has_lunar_phase=False)

        with (
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_sun_rise_set_swe", return_value=(None, None)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(None, None, None)),
        ):
            overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.moon.phase is None
        assert overview.moon.phase_name is None
        assert overview.moon.stage is None
        assert overview.moon.detailed is None

    def test_eclipse_calculation_fails(self) -> None:
        """Factory handles None eclipse results gracefully."""
        subject = _make_mock_subject()

        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", side_effect=_side_effect_lunar_phase_jd),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_sun_rise_set_swe", return_value=(_SUNRISE_JD, _SUNSET_JD)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(31.25, 169.67, 149_200_000.0)),
        ):
            overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.moon.next_lunar_eclipse is None
        assert overview.sun.next_solar_eclipse is None

    def test_sunrise_sunset_fails(self) -> None:
        """Factory handles missing sunrise/sunset (polar regions)."""
        subject = _make_mock_subject()

        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", side_effect=_side_effect_lunar_phase_jd),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=(4, _SOLAR_ECLIPSE_JD)),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=(1, _LUNAR_ECLIPSE_JD)),
            patch(f"{_FACTORY}.compute_sun_rise_set_swe", return_value=(None, None)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(None, None, None)),
        ):
            overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.sun.sunrise_timestamp is None
        assert overview.sun.sunset_timestamp is None
        assert overview.sun.solar_noon is None
        assert overview.sun.day_length is None
        assert overview.sun.position is None

    def test_lunar_phase_jd_returns_none(self) -> None:
        """When compute_lunar_phase_jd fails, upcoming phases have None windows."""
        subject = _make_mock_subject()

        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_sun_rise_set_swe", return_value=(None, None)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(None, None, None)),
        ):
            overview = MoonPhaseDetailsFactory.from_subject(subject)

        phases = overview.moon.detailed.upcoming_phases
        assert phases is not None
        # Each window should have last=None, next=None due to failed calculation
        assert phases.new_moon.last is None
        assert phases.new_moon.next is None
        assert phases.full_moon.last is None
        assert phases.full_moon.next is None

    def test_subject_without_coordinates(self) -> None:
        """Subject with no lat/lng should still produce an overview."""
        subject = _make_mock_subject()
        subject.lat = None
        subject.lng = None

        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", side_effect=_side_effect_lunar_phase_jd),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=(1, _LUNAR_ECLIPSE_JD)),
            patch(f"{_FACTORY}.compute_sun_rise_set_swe", return_value=(None, None)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(None, None, None)),
        ):
            overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.location.latitude is None
        assert overview.location.longitude is None


# ---------------------------------------------------------------------------
# 4. Phase angle boundary tests
# ---------------------------------------------------------------------------


class TestPhaseAngleBoundaries:
    """Verify illumination and stage at critical angular boundaries."""

    @pytest.fixture(autouse=True)
    def _patch_swe(self):
        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", side_effect=_side_effect_lunar_phase_jd),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_sun_rise_set_swe", return_value=(None, None)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(None, None, None)),
        ):
            yield

    @pytest.mark.parametrize(
        "angle, expected_stage, expected_major",
        [
            (0.001, "waxing", "New Moon"),
            (89.9, "waxing", "First Quarter"),
            (90.0, "waxing", "First Quarter"),
            (179.9, "waxing", "Full Moon"),
            (180.002, "waning", "Full Moon"),
            (270.0, "waning", "Last Quarter"),
            (359.9, "waning", "New Moon"),
        ],
    )
    def test_stage_and_major_phase(self, angle: float, expected_stage: str, expected_major: str) -> None:
        subject = _make_mock_subject(degrees_between=angle)
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.moon.stage == expected_stage
        assert overview.moon.major_phase == expected_major

    def test_new_moon_illumination_zero(self) -> None:
        """At 0° (New Moon), illumination should be 0%."""
        subject = _make_mock_subject(degrees_between=0.0)
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        assert overview.moon.illumination == "0%"

    def test_full_moon_illumination_hundred(self) -> None:
        """At 180° (Full Moon), illumination should be 100%."""
        subject = _make_mock_subject(degrees_between=180.0)
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        assert overview.moon.illumination == "100%"

    def test_quarter_illumination_fifty(self) -> None:
        """At 90° (First Quarter), illumination should be 50%."""
        subject = _make_mock_subject(degrees_between=90.0)
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        assert overview.moon.illumination == "50%"


# ---------------------------------------------------------------------------
# 5. _compute_lunar_phase_metrics unit tests
# ---------------------------------------------------------------------------


class TestComputeLunarPhaseMetrics:
    """Test _compute_lunar_phase_metrics with controlled inputs."""

    @staticmethod
    def _make_lunar_phase(degrees: float = 290.65) -> LunarPhaseModel:
        return LunarPhaseModel(
            degrees_between_s_m=degrees,
            moon_phase=23,
            moon_emoji="\U0001f318",
            moon_phase_name="Waning Crescent",
        )

    @staticmethod
    def _make_upcoming_phases() -> MoonPhaseUpcomingPhasesModel:
        """Build a minimal upcoming phases model with last new moon timestamp."""
        last_new = MoonPhaseEventMomentModel(
            timestamp=749411631,  # Sep 30, 1993 ~18:53 UTC
            datestamp="Thu, 30 Sep 1993 18:53:51 +0000",
            days_ago=10,
        )
        return MoonPhaseUpcomingPhasesModel(
            new_moon=MoonPhaseMajorPhaseWindowModel(last=last_new, next=None),
        )

    def test_returns_correct_tuple_length(self) -> None:
        lunar = self._make_lunar_phase()
        sun = SimpleNamespace(sign="Lib")
        moon = SimpleNamespace(sign="Leo")
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        result = _compute_lunar_phase_metrics(lunar, sun, moon, base_dt, upcoming)
        assert len(result) == 9

    def test_phase_fraction(self) -> None:
        lunar = self._make_lunar_phase(degrees=180.0)
        sun = SimpleNamespace(sign="Lib")
        moon = SimpleNamespace(sign="Leo")
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        phase, *_ = _compute_lunar_phase_metrics(lunar, sun, moon, base_dt, upcoming)
        assert phase == pytest.approx(0.5)

    def test_waning_stage(self) -> None:
        lunar = self._make_lunar_phase(degrees=200.0)
        sun = SimpleNamespace(sign="Lib")
        moon = SimpleNamespace(sign="Leo")
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        _, _, _, stage, *_ = _compute_lunar_phase_metrics(lunar, sun, moon, base_dt, upcoming)
        assert stage == "waning"

    def test_waxing_stage(self) -> None:
        lunar = self._make_lunar_phase(degrees=90.0)
        sun = SimpleNamespace(sign="Lib")
        moon = SimpleNamespace(sign="Leo")
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        _, _, _, stage, *_ = _compute_lunar_phase_metrics(lunar, sun, moon, base_dt, upcoming)
        assert stage == "waxing"

    def test_illumination_details_model(self) -> None:
        degrees = 120.0
        lunar = self._make_lunar_phase(degrees=degrees)
        sun = SimpleNamespace(sign="Lib")
        moon = SimpleNamespace(sign="Leo")
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        *_, illumination_details = _compute_lunar_phase_metrics(lunar, sun, moon, base_dt, upcoming)
        assert isinstance(illumination_details, MoonPhaseIlluminationDetailsModel)
        expected = 0.5 * (1.0 - math.cos(math.radians(degrees)))
        assert illumination_details.visible_fraction == pytest.approx(expected)
        assert illumination_details.phase_angle == pytest.approx(degrees)


# =============================================================================
# INTEGRATION TEST (non-mocked, from tests/test_lunar_phase_details_factory.py)
# =============================================================================


class TestMoonPhaseDetailsIntegration:
    """Integration test exercising real Swiss Ephemeris calls."""

    def test_from_subject_returns_valid_overview(self):
        from kerykeion.moon_phase_details import MoonPhaseDetailsFactory
        from kerykeion.schemas.kr_models import MoonPhaseOverviewModel

        subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon",
            1940,
            10,
            9,
            18,
            30,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
            online=False,
            suppress_geonames_warning=True,
        )
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert isinstance(overview, MoonPhaseOverviewModel)
        assert overview.moon is not None
        assert overview.moon.phase is not None
        assert overview.moon.phase_name == subject.lunar_phase.moon_phase_name
        assert overview.moon.emoji == subject.lunar_phase.moon_emoji
        assert overview.moon.detailed is not None
        assert overview.moon.detailed.illumination_details is not None
        assert overview.moon.detailed.upcoming_phases is not None
        assert overview.moon.detailed.upcoming_phases.full_moon is not None
        assert overview.moon.next_lunar_eclipse is not None
        assert isinstance(overview.moon.next_lunar_eclipse.timestamp, int)
        assert overview.moon.next_lunar_eclipse.type is not None
        assert overview.location is not None
        assert overview.sun is not None
        assert overview.sun.next_solar_eclipse is not None
        assert isinstance(overview.sun.next_solar_eclipse.timestamp, int)
        assert overview.sun.next_solar_eclipse.type is not None
        assert overview.sun.sunrise is not None
        assert overview.sun.sunset is not None
        assert overview.sun.solar_noon is not None
        assert overview.sun.day_length is not None
        assert overview.sun.position is not None
