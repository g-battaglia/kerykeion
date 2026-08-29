"""
Mocked unit tests for MoonPhaseDetailsFactory.

These tests mock the ephemeris utility layer so the factory logic can be
verified without ephemeris data files or real ephe calls. This isolates the
factory's orchestration, model assembly, and edge-case handling.

Mocking strategy:
    All SEVEN ephemeris helpers imported by factory.py are patched via
    ``kerykeion.moon_phase_details.factory.<function>``. The transit and the
    generalized rise/set call (the Moon's) are patched by a MODULE-level autouse
    fixture rather than per class: both were added after this file was written,
    and patching such a helper only in the two blocks that obviously needed it
    left thirteen tests in this file making real backend calls — including the
    one asserting that solar noon survives a rise/set failure, whose green then
    depended on a real ephemeris succeeding. A per-class fixture cannot prevent
    that recurring; a module-level one can. The two NON-mocked classes at the
    bottom (`TestMoonPhaseDetailsIntegration`, `TestFactoryFromSubjectRangeEdge`)
    override it back to the real call: an earlier revision blindfolded them too,
    silently zeroing the file's only real-ephemeris transit coverage while the
    commit message claimed the opposite.

    The patched helpers:
        - compute_lunar_phase_jd
        - compute_next_solar_eclipse_jd
        - compute_next_lunar_eclipse_jd
        - compute_sun_rise_set_ephe   (the Sun's rise/set, via its alias)
        - compute_rise_set_ephe       (the Moon's, called with body=ephe.MOON)
        - compute_sun_transit_ephe
        - compute_sun_position
"""

from __future__ import annotations

import math
from datetime import date, datetime, timezone
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
from kerykeion.moon_phase_details.utils import safe_parse_iso_datetime
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.models import (
    AstrologicalSubjectModel,
    LunarPhaseModel,
    MoonPhaseOverviewModel,
    MoonPhaseIlluminationDetailsModel,
    MoonPhaseUpcomingPhasesModel,
    MoonPhaseMajorPhaseWindowModel,
    MoonPhaseEventMomentModel,
)
from kerykeion.utilities import calculate_moon_phase


# ---------------------------------------------------------------------------
# Constants for mock data
# ---------------------------------------------------------------------------

# Julian Day for 1993-10-10 12:12:00 UTC (reference moment)
_REF_JD = 2449271.00833

# Julian Days for surrounding phase events (true ephemeris values for Oct 1993,
# matching what compute_lunar_phase_jd returns around _REF_JD)
_LAST_NEW_MOON_JD = 2449246.63215  # Sep 16, 1993 ~03:10 UTC
_NEXT_NEW_MOON_JD = 2449275.98330  # Oct 15, 1993 ~11:35 UTC
_LAST_FIRST_QUARTER_JD = 2449253.31394  # Sep 22, 1993 ~19:32 UTC
_NEXT_FIRST_QUARTER_JD = 2449282.86947  # Oct 22, 1993 ~08:52 UTC
_LAST_FULL_MOON_JD = 2449261.28738  # Sep 30, 1993 ~18:53 UTC
_NEXT_FULL_MOON_JD = 2449291.02613  # Oct 30, 1993 ~12:37 UTC
_LAST_QUARTER_LAST_JD = 2449269.31621  # Oct 8, 1993 ~19:35 UTC
_LAST_QUARTER_NEXT_JD = 2449298.77488  # Nov 7, 1993 ~06:35 UTC

# Eclipse Julian Days
_LUNAR_ECLIPSE_JD = 2449320.76813  # Nov 29, 1993
_SOLAR_ECLIPSE_JD = 2449305.40616  # Nov 13, 1993

# Sunrise/sunset Julian Days for London on Oct 10, 1993
_SUNRISE_JD = 2449270.80208
# The REAL meridian transit for this subject (London, 1993-10-10 11:47:30 UTC),
# not the midpoint of the pair above. Using the midpoint would encode the very
# definition this release removes, and would make `sunrise < solar_noon <
# sunset` tautological — it is 59 minutes from the true transit, and that
# assertion is one of the few things here that still says something.
_SOLAR_NOON_JD = 2449270.9913192377
_SUNSET_JD = 2449271.26250

# Moonrise/moonset for the same subject and the same civil day (London,
# 1993-10-10, which starts at 1993-10-09T23:00Z under BST). Real values, and —
# unlike the Sun's — they have to be: the factory keeps only events that fall
# inside the civil day, so a fabricated pair outside it would be filtered to
# None and every assertion below would read as a missing event.
_MOONRISE_JD = 2449270.48193  # 1993-10-09 23:33:59 UTC = 00:33 BST
_MOONSET_JD = 2449271.10791  # 1993-10-10 14:35:23 UTC = 15:35 BST


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



@pytest.fixture(autouse=True)
def _no_real_backend_calls():
    """Patch the late-arriving helpers for EVERY test in this module.

    Module-scoped autouse, deliberately. `compute_sun_transit_ephe` arrived after
    this file was written, and patching it inside the two fixtures that obviously
    needed it left thirteen tests calling the real backend — the exact thing the
    module docstring promises does not happen. `compute_rise_set_ephe` (the
    moonrise/moonset path) arrived later still and would have repeated the
    lesson exactly, so it joins the same floor rather than the per-class
    fixtures. Tests that want their own values still override with a nested
    `patch`; this only guarantees the floor. The two real-ephemeris classes
    shadow this fixture with a no-op, or their coverage of these paths would be
    silently zero.
    """
    with (
        patch(f"{_FACTORY}.compute_sun_transit_ephe", return_value=_SOLAR_NOON_JD),
        patch(f"{_FACTORY}.compute_rise_set_ephe", return_value=(_MOONRISE_JD, _MOONSET_JD)),
    ):
        yield

class TestSafeParseIsoDatetime:
    """safe_parse_iso_datetime: tolerant on format, strict on invalid input."""

    def test_standard_iso_with_offset(self) -> None:
        dt = safe_parse_iso_datetime("1993-10-10T12:12:00+01:00")
        assert dt == datetime(1993, 10, 10, 11, 12, tzinfo=timezone.utc)
        assert dt.tzinfo == timezone.utc

    def test_z_suffix_accepted(self) -> None:
        dt = safe_parse_iso_datetime("1993-10-10T11:12:00Z")
        assert dt == datetime(1993, 10, 10, 11, 12, tzinfo=timezone.utc)

    def test_naive_treated_as_utc(self) -> None:
        dt = safe_parse_iso_datetime("1993-10-10T11:12:00")
        assert dt.tzinfo == timezone.utc
        assert dt.hour == 11

    @pytest.mark.parametrize("bad_value", [None, "", "not-a-datetime", "1993-13-45T99:00:00"])
    def test_invalid_input_raises(self, bad_value) -> None:
        # An empty or malformed value used to fall back silently to
        # datetime.now(UTC) — a plausible-looking but wrong result. It must
        # raise the library's own exception instead.
        with pytest.raises(KerykeionException):
            safe_parse_iso_datetime(bad_value)


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
    """Test MoonPhaseDetailsFactory.from_subject with mocked ephe utilities."""

    @pytest.fixture(autouse=True)
    def _patch_swe(self):
        """Patch all Swiss Ephemeris utility functions used by the factory."""
        # ECL_TOTAL=4, ECL_PARTIAL=16 in Swiss Ephemeris
        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", side_effect=_side_effect_lunar_phase_jd),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=(16, _SOLAR_ECLIPSE_JD)),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=(4, _LUNAR_ECLIPSE_JD)),
            patch(f"{_FACTORY}.compute_sun_rise_set_ephe", return_value=(_SUNRISE_JD, _SUNSET_JD)),
            # The transit is a SIXTH backend call, added when solar noon stopped
            # being the midpoint. Unpatched it ran for real inside the suite whose
            # whole premise is that it does not, and `test_sun_info_populated`
            # then compared a real transit against two fabricated JD constants —
            # passing only because the fabricated window happened to bracket it.
            patch(f"{_FACTORY}.compute_sun_transit_ephe", return_value=_SOLAR_NOON_JD),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(31.25, 169.67, 149_200_000.0)),
        ):
            yield

    def test_returns_overview_model(self) -> None:
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        assert isinstance(overview, MoonPhaseOverviewModel)

    def test_moonrise_and_moonset_are_populated(self) -> None:
        """The four fields existed on the model from the start and were never
        written: the summary simply did not pass them."""
        subject = _make_mock_subject()
        moon = MoonPhaseDetailsFactory.from_subject(subject).moon

        assert moon.moonrise is not None
        assert moon.moonset is not None
        assert moon.moonrise_timestamp is not None
        assert moon.moonset_timestamp is not None

    def test_moonrise_carries_the_subject_local_zone(self) -> None:
        """Same zone as `sun.sunrise` — the moon-phase context is presented for
        the subject's civil day, so both endpoints read in its clock."""
        subject = _make_mock_subject()
        overview = MoonPhaseDetailsFactory.from_subject(subject)

        moonrise = datetime.fromisoformat(overview.moon.moonrise)
        assert moonrise.utcoffset() is not None
        assert moonrise.utcoffset() == overview.sun.sunrise.utcoffset()
        # 1993-10-09 23:33:59 UTC read in BST: the civil day is 1993-10-10.
        assert moonrise.date().isoformat() == "1993-10-10"
        assert moonrise.strftime("%H:%M") == "00:33"

    def test_moon_timestamps_are_the_utc_instants(self) -> None:
        subject = _make_mock_subject()
        moon = MoonPhaseDetailsFactory.from_subject(subject).moon

        for iso, timestamp in ((moon.moonrise, moon.moonrise_timestamp), (moon.moonset, moon.moonset_timestamp)):
            assert timestamp == int(datetime.fromisoformat(iso).timestamp())

    def test_moon_times_are_asked_of_the_moon(self) -> None:
        """The generalized helper is called with the Moon's body id — not left
        at its Sun default, which would silently republish the sunrise."""
        from kerykeion.ephemeris_backend.backend import ephe as _ephe

        subject = _make_mock_subject()
        with patch(
            f"{_FACTORY}.compute_rise_set_ephe", return_value=(_MOONRISE_JD, _MOONSET_JD)
        ) as mocked:
            MoonPhaseDetailsFactory.from_subject(subject)

        assert mocked.call_args is not None
        assert mocked.call_args.kwargs["body"] == _ephe.MOON

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

        # Age = _REF_JD - _LAST_NEW_MOON_JD: Oct 10 11:12 UTC - Sep 16 03:10
        # ≈ 24.33 days, consistent with the mocked 290.65° waning-crescent
        # phase angle.
        assert overview.moon.age_days is not None
        assert 24 <= overview.moon.age_days <= 25

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
        assert overview.sun.sunrise is not None
        assert overview.sun.sunset is not None
        assert overview.sun.solar_noon is not None
        assert overview.sun.day_length is not None
        # Solar noon sits between sunrise and sunset; day length is their span.
        assert overview.sun.sunrise < overview.sun.solar_noon < overview.sun.sunset
        assert overview.sun.day_length == overview.sun.sunset - overview.sun.sunrise

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
    """Test factory gracefully handles None returns from ephe utilities."""

    def test_no_lunar_phase_on_subject(self) -> None:
        """Subject without lunar_phase should produce minimal moon summary."""
        subject = _make_mock_subject(has_lunar_phase=False)

        with (
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_sun_rise_set_ephe", return_value=(None, None)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(None, None, None)),
        ):
            overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.moon.phase is None
        assert overview.moon.phase_name is None
        assert overview.moon.stage is None
        assert overview.moon.detailed is None

    def test_moonrise_moonset_fail(self) -> None:
        """A day with no moonrise or moonset (or a backend that cannot answer)
        leaves the four fields None — never an exception, and never a stale
        value borrowed from another day."""
        subject = _make_mock_subject()

        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", side_effect=_side_effect_lunar_phase_jd),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_sun_rise_set_ephe", return_value=(_SUNRISE_JD, _SUNSET_JD)),
            patch(f"{_FACTORY}.compute_rise_set_ephe", return_value=(None, None)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(None, None, None)),
        ):
            overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.moon.moonrise is None
        assert overview.moon.moonrise_timestamp is None
        assert overview.moon.moonset is None
        assert overview.moon.moonset_timestamp is None
        # The rest of the summary is unharmed: a missing horizon crossing says
        # nothing about the phase.
        assert overview.moon.phase is not None

    def test_moon_event_outside_the_civil_day_is_not_reported(self) -> None:
        """`rise_trans` always answers with the NEXT event, so on a day with no
        moonrise it hands back tomorrow's. Reporting that as today's moonrise —
        a day late, and paired with today's moonset — is the failure the window
        exists to prevent."""
        subject = _make_mock_subject()

        with patch(
            f"{_FACTORY}.compute_rise_set_ephe",
            # +1 day: still the next event, but it belongs to 1993-10-11.
            return_value=(_MOONRISE_JD + 1.0, _MOONSET_JD),
        ):
            overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.moon.moonrise is None
        assert overview.moon.moonrise_timestamp is None
        assert overview.moon.moonset is not None

    def test_eclipse_calculation_fails(self) -> None:
        """Factory handles None eclipse results gracefully."""
        subject = _make_mock_subject()

        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", side_effect=_side_effect_lunar_phase_jd),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_sun_rise_set_ephe", return_value=(_SUNRISE_JD, _SUNSET_JD)),
            # The transit is a SIXTH backend call, added when solar noon stopped
            # being the midpoint. Unpatched it ran for real inside the suite whose
            # whole premise is that it does not, and `test_sun_info_populated`
            # then compared a real transit against two fabricated JD constants —
            # passing only because the fabricated window happened to bracket it.
            patch(f"{_FACTORY}.compute_sun_transit_ephe", return_value=_SOLAR_NOON_JD),
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
            patch(f"{_FACTORY}.compute_sun_rise_set_ephe", return_value=(None, None)),
            patch(f"{_FACTORY}.compute_sun_position", return_value=(None, None, None)),
        ):
            overview = MoonPhaseDetailsFactory.from_subject(subject)

        assert overview.sun.sunrise is None
        assert overview.sun.sunset is None
        # solar_noon survives a rise/set failure now, and that is the point: a
        # transit is a meridian crossing, so it exists on a day with no horizon
        # crossing and does not depend on the pair. Only day_length does.
        assert overview.sun.solar_noon is not None
        assert overview.sun.day_length is None
        assert overview.sun.position is None

    def test_lunar_phase_jd_returns_none(self) -> None:
        """When compute_lunar_phase_jd fails, upcoming phases have None windows."""
        subject = _make_mock_subject()

        with (
            patch(f"{_FACTORY}.compute_lunar_phase_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_solar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_next_lunar_eclipse_jd", return_value=None),
            patch(f"{_FACTORY}.compute_sun_rise_set_ephe", return_value=(None, None)),
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
            patch(f"{_FACTORY}.compute_sun_rise_set_ephe", return_value=(None, None)),
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
            patch(f"{_FACTORY}.compute_sun_rise_set_ephe", return_value=(None, None)),
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
        """The lunar phase a subject carries at a given Sun-Moon separation.

        Built from the separation rather than hand-written: this used to pin
        "Waning Crescent" / 🌘 / lunation day 23 whatever ``degrees`` was, so the
        90° and 180° probes below were handed a model whose own name contradicted
        the angle the metrics then read.
        """
        return calculate_moon_phase(degrees, 0.0)

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
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        result = _compute_lunar_phase_metrics(lunar, base_dt, upcoming)
        # (phase, phase_name, emoji, stage, major_phase, illumination_str,
        #  age_days, age_days_precise, lunar_cycle_str, illumination_details)
        assert len(result) == 10
        # age_days is the rounded form of age_days_precise, always paired.
        assert result[6] == round(result[7])

    def test_phase_fraction(self) -> None:
        lunar = self._make_lunar_phase(degrees=180.0)
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        phase, *_ = _compute_lunar_phase_metrics(lunar, base_dt, upcoming)
        assert phase == pytest.approx(0.5)

    def test_waning_stage(self) -> None:
        lunar = self._make_lunar_phase(degrees=200.0)
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        _, _, _, stage, *_ = _compute_lunar_phase_metrics(lunar, base_dt, upcoming)
        assert stage == "waning"

    def test_waxing_stage(self) -> None:
        lunar = self._make_lunar_phase(degrees=90.0)
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        _, _, _, stage, *_ = _compute_lunar_phase_metrics(lunar, base_dt, upcoming)
        assert stage == "waxing"

    def test_illumination_details_model(self) -> None:
        degrees = 120.0
        lunar = self._make_lunar_phase(degrees=degrees)
        base_dt = datetime(1993, 10, 10, 11, 12, 0, tzinfo=timezone.utc)
        upcoming = self._make_upcoming_phases()

        *_, illumination_details = _compute_lunar_phase_metrics(lunar, base_dt, upcoming)
        assert isinstance(illumination_details, MoonPhaseIlluminationDetailsModel)
        expected = 0.5 * (1.0 - math.cos(math.radians(degrees)))
        assert illumination_details.visible_fraction == pytest.approx(expected)
        assert illumination_details.phase_angle == pytest.approx(degrees)


# =============================================================================
# INTEGRATION TEST (non-mocked, from tests/test_lunar_phase_details_factory.py)
# =============================================================================


class TestMoonPhaseDetailsIntegration:
    """Integration test exercising real ephemeris backend calls."""

    @pytest.fixture(autouse=True)
    def _no_real_backend_calls(self):
        """Shadow the module blindfold: this class IS the real-ephemeris path.

        With the module fixture active its transit coverage was silently zero —
        five real helpers plus one fake, while the commit message said six. The
        moonrise/moonset call is shadowed for the same reason.
        """
        yield

    def test_from_subject_returns_valid_overview(self):
        from kerykeion.moon_phase_details import MoonPhaseDetailsFactory
        from kerykeion.schemas.models import MoonPhaseOverviewModel

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
        # 1940-10-09 at Liverpool has both crossings; through the real path they
        # are filled and read in the subject's own zone (BST that day).
        assert overview.moon.moonrise is not None
        assert overview.moon.moonset is not None
        assert overview.moon.moonrise_timestamp is not None
        assert overview.moon.moonset_timestamp is not None
        assert datetime.fromisoformat(overview.moon.moonrise).date().isoformat() == "1940-10-09"


class TestRiseSetRealValues:
    """Real ephemeris, no mocks: the generalized rise/set call.

    Two things are pinned here. First, that generalizing the helper left the
    SUN alone — same pressure, same temperature, same flags, same refracted
    upper limb, to the last bit. Second, the Moon's own answer against
    independently checked times, and against the days it simply has no answer
    for.
    """

    # Royal Observatory, Greenwich. The reference times below were measured at
    # this latitude; 51.5 is ~2 arcseconds of time away, which the 1 s window
    # would not forgive.
    _LAT = 51.4779
    _LNG = 0.0

    @pytest.fixture(autouse=True)
    def _no_real_backend_calls(self):
        """Shadow the module blindfold: this class IS the real backend."""
        yield

    @staticmethod
    def _jd_midnight_utc(year: int, month: int, day: int) -> float:
        from kerykeion.utilities.core import datetime_to_julian

        return datetime_to_julian(datetime(year, month, day, tzinfo=timezone.utc))

    def test_the_sun_path_is_unchanged(self) -> None:
        """`compute_sun_rise_set_ephe` is now an alias. Exact equality, not
        approximate: a changed flag or a dropped refraction constant would move
        the answer by seconds, and seconds are what this file measures in."""
        from kerykeion.ephemeris_backend.backend import ephe as _ephe, ephemeris_session
        from kerykeion.moon_phase_details.utils import (
            compute_rise_set_ephe,
            compute_sun_rise_set_ephe,
        )

        jd = self._jd_midnight_utc(2026, 8, 28)
        with ephemeris_session():
            alias = compute_sun_rise_set_ephe(jd, self._LAT, self._LNG)
            explicit = compute_rise_set_ephe(jd, self._LAT, self._LNG, body=_ephe.SUN)
            defaulted = compute_rise_set_ephe(jd, self._LAT, self._LNG)

        assert alias[0] is not None and alias[1] is not None
        assert alias == explicit == defaulted

    def test_the_moon_is_not_the_sun(self) -> None:
        """Guards the default: a `body` left at SUN would have republished the
        sunrise under the moonrise's name, and every 'is not None' assertion in
        this file would still have passed."""
        from kerykeion.ephemeris_backend.backend import ephe as _ephe, ephemeris_session
        from kerykeion.moon_phase_details.utils import compute_rise_set_ephe

        jd = self._jd_midnight_utc(2026, 8, 28)
        with ephemeris_session():
            sun = compute_rise_set_ephe(jd, self._LAT, self._LNG, body=_ephe.SUN)
            moon = compute_rise_set_ephe(jd, self._LAT, self._LNG, body=_ephe.MOON)

        assert abs(sun[0] - moon[0]) > 1.0 / 24.0
        assert abs(sun[1] - moon[1]) > 1.0 / 24.0

    def test_greenwich_2026_08_28_moon_times(self) -> None:
        """Independently checked: moonrise 18:56:01 UTC, moonset 05:15:21 UTC.
        One second of tolerance — enough for the last bits of the Julian Day,
        not enough for a wrong horizon convention."""
        from kerykeion.moon_phase_details.factory import _compute_moon_times

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Greenwich Moon", 2026, 8, 28, 12, 0,
            lng=self._LNG, lat=self._LAT, tz_str="Etc/UTC",
            city="Greenwich", nation="GB", online=False,
            suppress_geonames_warning=True,
        )
        moonrise, moonset = _compute_moon_times(subject)

        assert moonrise is not None and moonset is not None
        assert abs((moonrise - datetime(2026, 8, 28, 18, 56, 1, tzinfo=timezone.utc)).total_seconds()) <= 1.0
        assert abs((moonset - datetime(2026, 8, 28, 5, 15, 21, tzinfo=timezone.utc)).total_seconds()) <= 1.0

    @pytest.mark.parametrize(
        "year, month, day, expect_rise, expect_set",
        [
            # The Moon rises ~50 min later each day, so it skips one civil day
            # in roughly thirty: on 2026-01-09 at Greenwich it never rises, and
            # on 2026-01-25 it never sets. Both must read None rather than
            # borrowing tomorrow's event, which is what `rise_trans` hands back.
            (2026, 1, 9, False, True),
            (2026, 1, 25, True, False),
            (2026, 8, 28, True, True),
        ],
        ids=["no-moonrise", "no-moonset", "both"],
    )
    def test_days_without_a_moonrise_or_a_moonset(
        self, year: int, month: int, day: int, expect_rise: bool, expect_set: bool
    ) -> None:
        from kerykeion.moon_phase_details.factory import _compute_moon_times

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Greenwich", year, month, day, 12, 0,
            lng=self._LNG, lat=self._LAT, tz_str="Etc/UTC",
            city="Greenwich", nation="GB", online=False,
            suppress_geonames_warning=True,
        )
        moonrise, moonset = _compute_moon_times(subject)

        assert (moonrise is not None) is expect_rise
        assert (moonset is not None) is expect_set
        for event in (moonrise, moonset):
            if event is not None:
                assert event.date() == datetime(year, month, day).date()

    def test_the_overview_carries_the_real_times(self) -> None:
        """The four model fields, filled by the real factory path."""
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Greenwich Overview", 2026, 8, 28, 12, 0,
            lng=self._LNG, lat=self._LAT, tz_str="Etc/UTC",
            city="Greenwich", nation="GB", online=False,
            suppress_geonames_warning=True,
        )
        moon = MoonPhaseDetailsFactory.from_subject(subject).moon

        assert moon.moonrise is not None and moon.moonrise.startswith("2026-08-28T18:56:0")
        assert moon.moonset is not None and moon.moonset.startswith("2026-08-28T05:15:2")
        assert moon.moonrise_timestamp == int(datetime.fromisoformat(moon.moonrise).timestamp())
        assert moon.moonset_timestamp == int(datetime.fromisoformat(moon.moonset).timestamp())


class TestTheLastCivilDayOfTheCalendar:
    """9999-12-31 has no tomorrow that `datetime` can name.

    The midnight that CLOSES the civil day belongs to the Moon alone — it is how
    a day with no moonrise is told apart from one whose moonrise the backend
    borrowed from tomorrow. Computing it in the shared window made it the first
    thing BOTH paths did, so on `date.max` a bare
    `datetime(...) + timedelta(days=1)` raised `OverflowError` and took the Sun's
    answer down with a question the Sun had never asked. It is lazy now, and the
    lunar path names the exception it can meet.
    """

    _LAT = 51.4779
    _LNG = 0.0

    @pytest.fixture(autouse=True)
    def _no_real_backend_calls(self):
        """Shadow the module blindfold: the real backend answers here."""
        yield

    @staticmethod
    def _greenwich(name: str):
        return AstrologicalSubjectFactory.from_birth_data(
            name, 2026, 8, 28, 12, 0,
            lng=TestTheLastCivilDayOfTheCalendar._LNG,
            lat=TestTheLastCivilDayOfTheCalendar._LAT,
            tz_str="Etc/UTC", city="Greenwich", nation="GB", online=False,
            suppress_geonames_warning=True,
        )

    @pytest.fixture
    def last_day(self):
        """A real subject re-dated to `date.max`.

        No ephemeris covers the year 9999, so a chart cannot be cast there at
        all; the day is reached the only way it can be, by moving a valid
        subject's timestamps onto it. Both functions under test read exactly
        those two fields (through `_get_utc_datetime`) plus the coordinates.
        """
        return self._greenwich("Greenwich").model_copy(
            update={
                "iso_formatted_utc_datetime": f"{date.max.isoformat()}T12:00:00+00:00",
                "iso_formatted_local_datetime": f"{date.max.isoformat()}T12:00:00+00:00",
            }
        )

    def test_the_window_opens_but_tomorrow_does_not_exist(self, last_day) -> None:
        """The split, stated: the day resolves, its successor cannot — which is
        precisely why the successor is computed lazily and only for the Moon."""
        from kerykeion.moon_phase_details.factory import (
            _local_civil_day_window,
            _next_local_midnight,
        )

        window = _local_civil_day_window(last_day)
        assert window is not None
        tzinfo, dt_local, jd_midnight = window
        assert dt_local.date() == date.max
        assert isinstance(jd_midnight, float)

        with pytest.raises(OverflowError):
            _next_local_midnight(dt_local, tzinfo)

    def test_the_sun_still_answers(self, last_day) -> None:
        """No exception, and the same shape as any other day: a 3-tuple whose
        elements the caller tests. Whether the backend can reach the year 9999
        is its own business — raising was not."""
        from kerykeion.moon_phase_details.factory import _compute_sun_times

        result = _compute_sun_times(last_day)

        assert result is not None
        assert len(result) == 3

    def test_the_moon_answers_none(self, last_day) -> None:
        """A day whose window cannot be closed has no event that can be proved
        to fall inside it, so both are None — reported, not raised."""
        from kerykeion.moon_phase_details.factory import _compute_moon_times

        assert _compute_moon_times(last_day) == (None, None)

    def test_the_sun_never_asks_for_tomorrows_midnight(self, monkeypatch) -> None:
        """The structural guard on an ordinary day: if the Sun ever reaches for
        the closing midnight again, this fails long before `date.max` does."""
        from kerykeion.moon_phase_details.factory import _compute_sun_times

        def _boom(*_args, **_kwargs):
            raise AssertionError("the Sun asked for tomorrow's midnight")

        monkeypatch.setattr(f"{_FACTORY}._next_local_midnight", _boom)

        sunrise, sunset, solar_noon = _compute_sun_times(self._greenwich("Greenwich Sun"))

        assert sunrise is not None and sunset is not None and solar_noon is not None


class TestFactoryFromSubjectRangeEdge:
    """R23 regression (real ephe, NOT mocked): a subject within ~1 synodic month
    of the ephemeris range end makes the forward phase scan walk off the edge.
    The backend range error must degrade to None fields (documented "Returns None
    if calculation fails"), not leak a raw EphemerisRangeError.

    Range semantics of the medium (DE440) LEB series since libephemeris
    3.0.0rc14: the "1550-2650" shorthand means [1550-01-01, 2650-01-01) — JD
    [2287185.5, 2688952.5) — i.e. the upper year is *exclusive* (only the very
    first instant of 2650-01-01 is inside the coverage inventory, and even that
    instant is unusable because interpolation needs interior neighbours). A
    date beyond the edge no longer degrades to a silently substituted
    lower-precision source (the rc12 behaviour): sealed LEB mode raises the
    typed ``EphemerisRangeError`` by deliberate contract ("LEB mode does not
    silently substitute a lower-precision source")."""

    @pytest.fixture(autouse=True)
    def _no_real_backend_calls(self):
        """Shadow the module blindfold — same reason as the class above: the
        whole point of this class is that the REAL backend degrades cleanly,
        transit and moonrise/moonset included (they compute fine at 2649-12-20;
        the edge the class exercises is the forward phase scan)."""
        yield

    def test_range_end_subject_returns_model(self) -> None:
        # 2649-12-20 is inside the final synodic month of the medium (DE440)
        # series, whose REAL coverage ends at JD 2688952.5 = 2650-01-01T00:00
        # (exclusive — see the class docstring). The subject itself computes,
        # but the forward Full/quarter phase scans overshoot the edge and must
        # degrade to None fields instead of leaking the backend range error.
        # The date presumes at least the medium kernel: on base kernels the
        # subject itself is out of range. On extended kernels no edge is
        # hit — the model is still returned, just without exercising the
        # degradation path.
        from tests.conftest import _detect_ephemeris_tier

        if _detect_ephemeris_tier() == "base":
            pytest.skip("2649 is outside the base kernel's range (1849-2150).")
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Range Edge", 2649, 12, 20, 12, 0,
            lat=41.9028, lng=12.4964, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False, suppress_geonames_warning=True,
        )
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        assert isinstance(overview, MoonPhaseOverviewModel)

    def test_beyond_range_end_raises_typed_error(self) -> None:
        # Complement of the case above: 2650-01-20 lies ~19.5 days BEYOND the
        # real end of the medium (DE440) series (JD 2688952.5 = 2650-01-01),
        # so the subject's own Sun/Moon cannot be computed at all. Under
        # libephemeris 3.0.0rc14 sealed LEB mode this is a deliberate
        # contract: the backend raises the typed EphemerisRangeError instead
        # of silently substituting a lower-precision source (which is what
        # rc12 did, and why this date used to build a subject). Kerykeion
        # wraps luminary failures in KerykeionException with the backend
        # error chained as __cause__, so we assert on the cause chain by
        # exception name (no hard libephemeris import needed here).
        # Gate to the exact configuration under test: on extended kernels the
        # date is covered (no edge); on base it is out of range too, but of a
        # different boundary; on the swisseph backend the sealed-LEB contract
        # does not exist.
        from kerykeion.ephemeris_backend import BACKEND_NAME
        from tests.conftest import _detect_ephemeris_tier

        if BACKEND_NAME != "libephemeris":
            pytest.skip("The sealed-LEB range contract is libephemeris-specific.")
        if _detect_ephemeris_tier() != "medium":
            pytest.skip(
                "2650-01-20 is just-beyond-range only on the medium (DE440) "
                "kernel: extended covers it, base ends at 2150."
            )
        with pytest.raises(KerykeionException) as excinfo:
            AstrologicalSubjectFactory.from_birth_data(
                "Beyond Range End", 2650, 1, 20, 12, 0,
                lat=41.9028, lng=12.4964, tz_str="Europe/Rome",
                city="Rome", nation="IT", online=False, suppress_geonames_warning=True,
            )
        cause_names = []
        cause = excinfo.value.__cause__
        while cause is not None:
            cause_names.append(type(cause).__name__)
            cause = cause.__cause__
        assert "EphemerisRangeError" in cause_names, (
            "Expected the typed libephemeris EphemerisRangeError in the "
            f"exception cause chain; got {cause_names or [repr(excinfo.value)]}"
        )

    def test_normal_date_subject_unaffected(self) -> None:
        subject = AstrologicalSubjectFactory.from_birth_data(
            "Normal", 1990, 6, 15, 12, 0,
            lat=41.9028, lng=12.4964, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False, suppress_geonames_warning=True,
        )
        overview = MoonPhaseDetailsFactory.from_subject(subject)
        assert isinstance(overview, MoonPhaseOverviewModel)
        assert overview.moon is not None
        assert overview.moon.detailed is not None
        assert overview.moon.detailed.upcoming_phases is not None


class TestTheMidnightThatOpensADayOfUnusualLength:
    """A civil midnight is not always one instant, and one rule has to name it.

    Both ends of the rise/set window are a midnight: the one that opens the day
    and the one that opens the next. When a zone changes its offset AT 00:00 the
    two readings of that wall time are an hour apart, and the choice is not free
    — whatever the opening boundary excludes, the closing boundary of the
    previous day has to include, or an hour of the calendar belongs to two days
    or to none.

    Inside a fall-back FOLD the day opens at the FIRST occurrence: the repeated
    hour is already the new civil day. Both boundaries used to take the second,
    which opened the day an hour late and closed the day before an hour late, so
    a moonrise in that hour was filed under the wrong date.

    Across a spring-forward GAP midnight never happens, and the reading that
    lands past the gap — the day's real first instant — is the other one. The
    resolver has to tell the two cases apart; a single ``is_dst`` cannot.
    """

    _HAVANA = dict(
        lng=-82.3589, lat=23.1136, tz_str="America/Havana", city="Havana", nation="CU"
    )
    _SANTIAGO = dict(
        lng=-70.6483, lat=-33.4569, tz_str="America/Santiago", city="Santiago", nation="CL"
    )

    @pytest.fixture(autouse=True)
    def _no_real_backend_calls(self):
        """Shadow the module blindfold: the real backend answers here."""
        yield

    @staticmethod
    def _subject(name: str, year: int, month: int, day: int, **location):
        return AstrologicalSubjectFactory.from_birth_data(
            name, year, month, day, 12, 0,
            online=False, suppress_geonames_warning=True, **location,
        )

    @staticmethod
    def _window(subject) -> tuple[float, float]:
        """``(jd_midnight, jd_next_midnight)`` — the day's two boundaries."""
        from kerykeion.moon_phase_details.factory import (
            _local_civil_day_window,
            _next_local_midnight,
        )

        window = _local_civil_day_window(subject)
        assert window is not None
        tzinfo, dt_local, jd_midnight = window
        return jd_midnight, _next_local_midnight(dt_local, tzinfo)

    @staticmethod
    def _jd_of_utc(year: int, month: int, day: int, hour: int) -> float:
        from kerykeion.utilities.core import datetime_to_julian

        return datetime_to_julian(datetime(year, month, day, hour, tzinfo=timezone.utc))

    def test_the_two_zones_really_do_it_at_midnight(self) -> None:
        """The premise, asserted rather than assumed: a tz database that moved
        either transition off 00:00 would leave the tests below green for a
        reason that has nothing to do with the resolver."""
        from zoneinfo import ZoneInfo

        from kerykeion.utilities.core import is_ambiguous, is_nonexistent

        assert is_ambiguous(datetime(2026, 11, 1), ZoneInfo("America/Havana"))
        assert is_nonexistent(datetime(2026, 9, 6), ZoneInfo("America/Santiago"))

    def test_a_folded_midnight_opens_the_day_at_its_first_occurrence(self) -> None:
        """Havana's clocks fall back at 00:00 on 2026-11-01, so the day is 25
        hours long and opens at 04:00 UTC — the summer reading. The second
        occurrence, 05:00 UTC, is already an hour into the day."""
        jd_midnight, jd_next = self._window(
            self._subject("Havana fold", 2026, 11, 1, **self._HAVANA)
        )

        assert jd_midnight == pytest.approx(self._jd_of_utc(2026, 11, 1, 4), abs=1e-9)
        assert jd_next == pytest.approx(self._jd_of_utc(2026, 11, 2, 5), abs=1e-9)
        assert (jd_next - jd_midnight) * 24.0 == pytest.approx(25.0, abs=1e-6)

    def test_the_day_before_the_fold_ends_where_the_folded_day_begins(self) -> None:
        """The invariant the shared resolver exists for: the two boundaries are
        the same instant, so the repeated hour is counted once, on the right
        side. October 31 is an ordinary 24-hour day."""
        jd_midnight_31, jd_next_31 = self._window(
            self._subject("Havana eve", 2026, 10, 31, **self._HAVANA)
        )
        jd_midnight_01, _ = self._window(
            self._subject("Havana fold", 2026, 11, 1, **self._HAVANA)
        )

        assert jd_next_31 == pytest.approx(jd_midnight_01, abs=1e-9)
        assert (jd_next_31 - jd_midnight_31) * 24.0 == pytest.approx(24.0, abs=1e-6)

    def test_a_midnight_inside_a_gap_still_opens_the_day_after_it(self) -> None:
        """Santiago's clocks jump 00:00 -> 01:00 on 2026-09-06: midnight never
        happens, the day is 23 hours long, and it opens at the first instant
        that does exist. Unchanged by the fold correction."""
        jd_midnight, jd_next = self._window(
            self._subject("Santiago gap", 2026, 9, 6, **self._SANTIAGO)
        )

        assert jd_midnight == pytest.approx(self._jd_of_utc(2026, 9, 6, 4), abs=1e-9)
        assert jd_next == pytest.approx(self._jd_of_utc(2026, 9, 7, 3), abs=1e-9)
        assert (jd_next - jd_midnight) * 24.0 == pytest.approx(23.0, abs=1e-6)

    def test_the_sunrise_does_not_move_with_the_boundary(self) -> None:
        """The correction moves the day's opening an hour earlier; the Sun's
        answer is unchanged, because sunrise is found by searching FORWARD and
        the Havana sunrise is six hours past both readings of midnight. Asserted
        rather than assumed: a resolver change that DID move the Sun would be a
        different release."""
        from kerykeion.ephemeris_backend.backend import ephemeris_session
        from kerykeion.moon_phase_details.factory import _compute_sun_times
        from kerykeion.moon_phase_details.utils import compute_sun_rise_set_ephe
        from kerykeion.utilities.core import julian_to_datetime

        subject = self._subject("Havana sun", 2026, 11, 1, **self._HAVANA)
        result = _compute_sun_times(subject)
        assert result is not None
        sunrise, sunset, _solar_noon = result
        assert sunrise is not None and sunset is not None
        assert sunrise.date() == date(2026, 11, 1)

        jd_midnight, _jd_next = self._window(subject)
        with ephemeris_session():
            # The pre-fix boundary: the fold's SECOND occurrence, an hour later.
            from_the_later_reading, _ = compute_sun_rise_set_ephe(
                jd_midnight + 1.0 / 24.0, subject.lat, subject.lng
            )
        assert from_the_later_reading is not None
        from_the_later_reading_local = julian_to_datetime(from_the_later_reading).replace(
            tzinfo=timezone.utc
        ).astimezone(sunrise.tzinfo)
        # Same sunrise, to well inside a second: the backend's root-finder starts
        # from the boundary it is given, so the two runs differ only by the last
        # digits of its own convergence.
        assert abs((from_the_later_reading_local - sunrise).total_seconds()) < 1.0
