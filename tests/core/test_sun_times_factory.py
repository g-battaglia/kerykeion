"""Unit tests for SunTimesFactory."""

from __future__ import annotations

import pytest

import kerykeion.sun_times.utils as sun_times_utils
from kerykeion import SunTimesFactory
from kerykeion.schemas.kerykeion_exception import KerykeionException

# Rome
ROME = dict(latitude=41.9028, longitude=12.4964, tz_str="Europe/Rome")
# Tromsø, well inside the Arctic Circle
TROMSO = dict(latitude=69.6492, longitude=18.9553, tz_str="Europe/Oslo")


def test_rome_late_may():
    s = SunTimesFactory.from_date(2026, 5, 28, **ROME)
    assert s.date == "2026-05-28"
    assert s.timezone == "Europe/Rome"
    assert not s.is_polar_day and not s.is_polar_night
    assert s.sunrise is not None and s.sunset is not None
    # Ordering and consistency.
    assert s.sunrise < s.solar_noon < s.sunset
    assert s.day_length == s.sunset - s.sunrise
    # Late May in Rome: a long day, ~14.5-15.5 h.
    hours = s.day_length.total_seconds() / 3600
    assert 14.0 < hours < 15.5
    # All instants are timezone-aware UTC.
    assert s.sunrise.utcoffset().total_seconds() == 0


def test_polar_day():
    s = SunTimesFactory.from_date(2026, 6, 21, **TROMSO)
    assert s.is_polar_day is True
    assert s.is_polar_night is False
    assert s.sunrise is None and s.sunset is None and s.day_length is None


def test_high_latitude_transition_pairs_sunset_after_sunrise():
    s = SunTimesFactory.from_date(2026, 5, 17, **TROMSO)
    assert s.sunrise is not None and s.sunset is not None
    assert s.sunrise < s.sunset
    assert s.day_length == s.sunset - s.sunrise


def test_polar_boundary_uses_apparent_horizon_flags():
    s = SunTimesFactory.from_date(2026, 5, 19, **TROMSO)
    assert s.is_polar_day is True
    assert s.is_polar_night is False
    assert s.sunrise is None and s.sunset is None


def test_sunset_after_local_midnight_is_not_nulled():
    """Mirror of the sunset-before-sunrise case: at high latitude a real sunset
    just PAST local midnight was nulled by the civil-day bound, returning
    sunset/day_length/solar_noon = None with neither polar flag set on a
    non-polar day. It must now report the continuous daylight span."""
    # 69.0N is below the Tromsø latitude, so 2026-05-19 is not yet polar there —
    # the Sun rises and sets ~00:07 local the next day.
    s = SunTimesFactory.from_date(2026, 5, 19, latitude=69.0, longitude=18.0, tz_str="Europe/Oslo")
    assert s.is_polar_day is False and s.is_polar_night is False
    assert s.sunrise is not None and s.sunset is not None
    assert s.day_length is not None and s.solar_noon is not None
    assert s.sunset > s.sunrise
    # Daylight span crosses local midnight -> longer than 20h but under 24h.
    assert s.day_length.total_seconds() > 20 * 3600


def test_polar_night():
    s = SunTimesFactory.from_date(2026, 12, 21, **TROMSO)
    assert s.is_polar_night is True
    assert s.is_polar_day is False
    assert s.sunrise is None and s.sunset is None


def test_dst_spring_forward_midnight_gap_sao_paulo():
    # Regression: on 2018-11-04 America/Sao_Paulo clocks jumped straight from
    # 00:00 to 01:00, so the civil midnight used internally to anchor the day
    # does not exist. The factory must resolve the gap forward instead of
    # raising on the non-existent wall time, and still return a sane sunrise/sunset.
    from zoneinfo import ZoneInfo

    from kerykeion.sun_times.utils import _localize_civil_midnight

    s = SunTimesFactory.from_date(
        2018, 11, 4, latitude=-23.5505, longitude=-46.6333, tz_str="America/Sao_Paulo"
    )
    assert s.sunrise is not None and s.sunset is not None
    assert s.sunrise < s.solar_noon < s.sunset
    sp = ZoneInfo("America/Sao_Paulo")
    first_instant = _localize_civil_midnight(2018, 11, 4, sp)
    # The helper promises the real first instant, not an imaginary
    # 00:00-03:00 wall time that merely maps to it after UTC conversion.
    assert (first_instant.hour, first_instant.utcoffset().total_seconds()) == (1, -2 * 3600)
    sunrise_local = s.sunrise.astimezone(sp)
    assert sunrise_local.date().isoformat() == "2018-11-04"
    assert 5 <= sunrise_local.hour <= 7  # ~06:18 local (DST)
    # Early-November day at -23.5 deg latitude lasts ~13 h.
    hours = s.day_length.total_seconds() / 3600
    assert 12.0 < hours < 14.0


def test_dst_spring_forward_midnight_gap_santiago():
    # Regression: 2022-09-11 America/Santiago also jumps 00:00 -> 01:00.
    from zoneinfo import ZoneInfo

    s = SunTimesFactory.from_date(
        2022, 9, 11, latitude=-33.4489, longitude=-70.6693, tz_str="America/Santiago"
    )
    assert s.sunrise is not None and s.sunset is not None
    assert s.sunrise < s.solar_noon < s.sunset
    scl = ZoneInfo("America/Santiago")
    sunrise_local = s.sunrise.astimezone(scl)
    assert sunrise_local.date().isoformat() == "2022-09-11"
    assert 6 <= sunrise_local.hour <= 9  # ~07:47 local (DST starts this day)
    # Mid-September day at -33.4 deg latitude lasts ~11.5-12.5 h.
    hours = s.day_length.total_seconds() / 3600
    assert 11.0 < hours < 13.0


def test_historical_date_supported():
    # The factory works across the full civil range; 1700 is comfortably in range.
    s = SunTimesFactory.from_date(1700, 3, 15, **ROME)
    assert s.sunrise is not None and s.sunset is not None
    assert s.sunrise < s.sunset


def test_bce_year_raises_clean_exception():
    # These timezone-anchored factories support civil years 1-9999 CE; a BCE year
    # must raise a clean KerykeionException, not a raw ValueError.
    with pytest.raises(KerykeionException):
        SunTimesFactory.from_date(-43, 3, 15, **ROME)


def test_civil_day_bounds_last_day_falls_back():
    # The upper bound is normally the NEXT local midnight, which is what makes a
    # DST day come out 23 or 25 hours long rather than a flat 24. On the very last
    # civil date there is no next date to localize at all — `date(9999, 12, 31) + 1
    # day` overflows — so the bound falls back to jd_midnight + 1. Without that
    # fallback the call raises instead of returning, so the assertion is load-bearing.
    from zoneinfo import ZoneInfo

    from kerykeion.sun_times.utils import _civil_day_bounds

    lo, hi = _civil_day_bounds(9999, 12, 31, ZoneInfo("America/New_York"))
    assert hi == pytest.approx(lo + 1.0)

    # The non-fallback path is the contrast that proves the above is a fallback and
    # not the general rule: on a real transition day the span is not 24 hours.
    rome = ZoneInfo("Europe/Rome")
    spring_lo, spring_hi = _civil_day_bounds(2026, 3, 29, rome)
    assert (spring_hi - spring_lo) * 24 == pytest.approx(23.0)
    autumn_lo, autumn_hi = _civil_day_bounds(2026, 10, 25, rome)
    assert (autumn_hi - autumn_lo) * 24 == pytest.approx(25.0)


def test_civil_range_edge_is_sign_dependent_not_symmetric():
    # DELIBERATE CONTRACT CHANGE. Resolving a wall time to an instant subtracts the
    # zone's UTC offset, so only an EAST-of-UTC offset can push 0001-01-01 below the
    # representable range. The limit therefore depends on the sign of the offset and
    # is not a symmetric "first and last civil day are unsupported" rule:
    #   * year 1 east of UTC (Rome)  -> still unsupported, and for a stated reason
    #   * year 9999 east of UTC      -> now legitimately resolvable; a negative
    #                                   offset is subtracted, moving it further
    #                                   INSIDE the range, so nothing overflows
    #   * year 1 west of UTC (New York) -> resolvable for the same reason
    # The timezone layer is asserted directly because the public factories cannot
    # reach year 9999 for an unrelated reason (see the ephemeris-coverage test below).
    from zoneinfo import ZoneInfo

    from kerykeion.sun_times.utils import _localize_civil_midnight, localize_datetime

    rome, new_york = ZoneInfo("Europe/Rome"), ZoneInfo("America/New_York")

    with pytest.raises(KerykeionException, match="east-of-UTC"):
        _localize_civil_midnight(1, 1, 1, rome)
    with pytest.raises(KerykeionException, match="east-of-UTC"):
        localize_datetime(1, 1, 1, 0, 30, tz=rome)

    assert _localize_civil_midnight(9999, 12, 31, rome).year == 9999
    assert localize_datetime(9999, 12, 31, 23, 30, tz=rome).year == 9999
    assert _localize_civil_midnight(1, 1, 1, new_york).year == 1
    assert localize_datetime(1, 1, 1, 0, 30, tz=new_york).year == 1


def test_civil_range_edge_days_raise_clean_exception():
    # Whatever the cause, a caller must see a KerykeionException and never a raw
    # OverflowError or backend error. The two ends now fail for DIFFERENT reasons:
    # year 1 east of UTC fails in the timezone layer (above), while year 9999 gets
    # past the timezone layer and is stopped by the ephemeris coverage range. Both
    # are asserted here because the guarantee this test protects is the exception
    # TYPE at the public boundary, which must hold either way.
    from kerykeion.planetary_hours import PlanetaryHoursFactory
    from kerykeion.void_of_course_moon import VoidOfCourseMoonFactory

    with pytest.raises(KerykeionException, match="east-of-UTC"):
        SunTimesFactory.from_date(1, 1, 1, **ROME)
    with pytest.raises(KerykeionException):
        SunTimesFactory.from_date(9999, 12, 31, **ROME)
    with pytest.raises(KerykeionException, match="east-of-UTC"):
        PlanetaryHoursFactory.from_datetime(1, 1, 1, 0, 30, **ROME)
    with pytest.raises(KerykeionException):
        PlanetaryHoursFactory.from_datetime(9999, 12, 31, 23, 30, **ROME)
    with pytest.raises(KerykeionException, match="east-of-UTC"):
        VoidOfCourseMoonFactory.from_datetime(1, 1, 1, 0, 30, tz_str=ROME["tz_str"])
    with pytest.raises(KerykeionException):
        VoidOfCourseMoonFactory.from_datetime(9999, 12, 31, 23, 30, tz_str=ROME["tz_str"])


def test_invalid_timezone_raises():
    with pytest.raises(KerykeionException):
        SunTimesFactory.from_date(2026, 5, 28, latitude=0.0, longitude=0.0, tz_str="Not/AZone")


def test_polar_edge_does_not_return_next_day_events():
    # Regression: rise_trans searches forward with no upper bound, so on a polar-edge
    # date it returns the *next* civil day's rise/set. Those out-of-day events must be
    # discarded so the day is reported as polar, not as a day whose sun rises/sets on a
    # later date. Tromsø 2026-07-25 is still inside the midnight-sun season (polar day).
    s = SunTimesFactory.from_date(2026, 7, 25, **TROMSO)
    assert s.is_polar_day is True
    assert s.is_polar_night is False
    assert s.sunrise is None and s.sunset is None
    assert s.solar_noon is None and s.day_length is None


def test_no_events_but_not_polar_raises(monkeypatch):
    # Regression: when the backend cannot produce rise/set (returns (None, None)) yet
    # the geometry is not polar (here, the equator), the factory must raise a clean
    # KerykeionException rather than return an impossible "no sun, not polar" model.
    monkeypatch.setattr(sun_times_utils, "compute_sun_rise_set_ephe", lambda *a, **k: (None, None))
    with pytest.raises(KerykeionException):
        SunTimesFactory.from_date(2026, 3, 20, latitude=0.0, longitude=0.0, tz_str="UTC")


def test_polar_state_backend_failure_raises(monkeypatch):
    # Regression: a raw backend error while classifying polar day/night must surface as
    # a KerykeionException, not leak as a low-level ephemeris error.
    monkeypatch.setattr(sun_times_utils, "compute_sun_rise_set_ephe", lambda *a, **k: (None, None))

    def _raise(*a, **k):
        raise RuntimeError("ephemeris out of range")

    monkeypatch.setattr(sun_times_utils, "_polar_state", _raise)
    with pytest.raises(KerykeionException):
        SunTimesFactory.from_date(2026, 6, 21, **TROMSO)


def test_twilight_ordering_rome():
    # Civil/nautical/astronomical dawn precede sunrise (deepest depression first),
    # and the dusks follow sunset in the mirror order — a strictly increasing run.
    s = SunTimesFactory.from_date(2026, 5, 28, **ROME)
    sequence = [
        s.astronomical_dawn,
        s.nautical_dawn,
        s.civil_dawn,
        s.sunrise,
        s.sunset,
        s.civil_dusk,
        s.nautical_dusk,
        s.astronomical_dusk,
    ]
    assert all(moment is not None for moment in sequence)
    assert all(earlier < later for earlier, later in zip(sequence, sequence[1:]))
    # Twilight instants are timezone-aware UTC, like the rest of the model.
    assert s.civil_dawn.utcoffset().total_seconds() == 0


def test_twilight_none_on_polar_day():
    # On polar day the Sun never crosses any depression angle, so every twilight
    # boundary is None (matching the None sunrise/sunset).
    s = SunTimesFactory.from_date(2026, 6, 21, **TROMSO)
    assert s.is_polar_day is True
    assert s.civil_dawn is None and s.civil_dusk is None
    assert s.nautical_dawn is None and s.nautical_dusk is None
    assert s.astronomical_dawn is None and s.astronomical_dusk is None


def test_twilight_partial_high_latitude():
    # London at the summer solstice has no astronomical night (the Sun never sinks
    # to -18 degrees), so astronomical dawn/dusk are None while civil and nautical
    # twilight still occur. The day is not polar.
    s = SunTimesFactory.from_date(2026, 6, 21, latitude=51.5074, longitude=-0.1278, tz_str="Europe/London")
    assert not s.is_polar_day and not s.is_polar_night
    assert s.civil_dawn is not None and s.civil_dusk is not None
    assert s.nautical_dawn is not None and s.nautical_dusk is not None
    assert s.astronomical_dawn is None and s.astronomical_dusk is None
    # Deeper twilight begins earlier in the morning.
    assert s.nautical_dawn < s.civil_dawn


def test_twilight_extreme_latitude_does_not_raise():
    # Deep in the Arctic on polar day the backend can refuse a twilight crossing
    # (circumpolar at the depression angle); the factory must degrade to None
    # rather than propagate a backend error.
    s = SunTimesFactory.from_date(2026, 6, 21, latitude=78.22, longitude=15.65, tz_str="Arctic/Longyearbyen")
    assert s.is_polar_day is True
    assert s.civil_dawn is None and s.nautical_dawn is None and s.astronomical_dawn is None
    assert s.civil_dusk is None and s.nautical_dusk is None and s.astronomical_dusk is None


def test_twilight_dusk_crosses_midnight_high_latitude():
    # Near the solstice at ~43-48N the astronomical "night" falls in the small hours,
    # so the evening dusk lands on the next civil date. Searching dusk from local noon
    # keeps it the evening crossing (dawn < dusk, ~a full day after dawn); a
    # midnight-anchored search would instead return a pre-dawn value (dusk < dawn).
    from zoneinfo import ZoneInfo

    s = SunTimesFactory.from_date(2026, 6, 21, latitude=48.0, longitude=2.35, tz_str="Europe/Paris")
    assert s.astronomical_dawn is not None and s.astronomical_dusk is not None
    assert s.astronomical_dawn < s.astronomical_dusk
    assert (s.astronomical_dusk - s.astronomical_dawn).total_seconds() > 12 * 3600
    assert s.sunset < s.civil_dusk < s.nautical_dusk < s.astronomical_dusk
    # The evening astronomical dusk spills past local midnight onto the next date.
    paris = ZoneInfo("Europe/Paris")
    assert s.astronomical_dusk.astimezone(paris).date() > s.sunset.astimezone(paris).date()


def test_twilight_during_polar_night():
    # Polar night is not the same as no twilight: at Svalbard in midwinter the Sun
    # still climbs above the deeper depression angles around local noon, so nautical
    # and astronomical twilight exist even though sunrise/sunset (and the shallower
    # civil twilight) are None.
    s = SunTimesFactory.from_date(2026, 12, 21, latitude=78.22, longitude=15.65, tz_str="Arctic/Longyearbyen")
    assert s.is_polar_night is True
    assert s.sunrise is None and s.sunset is None
    assert s.civil_dawn is None and s.civil_dusk is None
    assert s.nautical_dawn is not None and s.nautical_dusk is not None
    assert s.astronomical_dawn is not None and s.astronomical_dusk is not None


def test_planetary_hours_rejects_out_of_range_coordinates():
    # Mirrors SunTimesFactory's contract; lat=95 used to produce a misleading
    # polar-day message and lng=200 was silently accepted.
    from kerykeion.planetary_hours import PlanetaryHoursFactory

    with pytest.raises(KerykeionException, match="Latitude"):
        PlanetaryHoursFactory.from_datetime(
            2026, 6, 1, 12, 0, latitude=95.0, longitude=12.5, tz_str="Europe/Rome"
        )
    with pytest.raises(KerykeionException, match="Longitude"):
        PlanetaryHoursFactory.from_datetime(
            2026, 6, 1, 12, 0, latitude=41.9, longitude=200.0, tz_str="Europe/Rome"
        )
