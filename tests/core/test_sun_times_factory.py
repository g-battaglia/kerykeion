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


def test_polar_night():
    s = SunTimesFactory.from_date(2026, 12, 21, **TROMSO)
    assert s.is_polar_night is True
    assert s.is_polar_day is False
    assert s.sunrise is None and s.sunset is None


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
    monkeypatch.setattr(sun_times_utils, "compute_sun_rise_set_swe", lambda *a, **k: (None, None))
    with pytest.raises(KerykeionException):
        SunTimesFactory.from_date(2026, 3, 20, latitude=0.0, longitude=0.0, tz_str="UTC")


def test_polar_state_backend_failure_raises(monkeypatch):
    # Regression: a raw backend error while classifying polar day/night must surface as
    # a KerykeionException, not leak as a low-level ephemeris error.
    monkeypatch.setattr(sun_times_utils, "compute_sun_rise_set_swe", lambda *a, **k: (None, None))

    def _raise(*a, **k):
        raise RuntimeError("ephemeris out of range")

    monkeypatch.setattr(sun_times_utils, "_polar_state", _raise)
    with pytest.raises(KerykeionException):
        SunTimesFactory.from_date(2026, 6, 21, **TROMSO)
