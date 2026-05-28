"""Unit tests for PlanetaryHoursFactory."""

from __future__ import annotations

import pytest

from kerykeion import PlanetaryHoursFactory
from kerykeion.planetary_hours.utils import CHALDEAN_ORDER
from kerykeion.schemas.kerykeion_exception import KerykeionException

ROME = dict(latitude=41.9028, longitude=12.4964, tz_str="Europe/Rome")
TROMSO = dict(latitude=69.6492, longitude=18.9553, tz_str="Europe/Oslo")


def test_thursday_structure():
    # 2026-05-28 is a Thursday → ruled by Jupiter.
    ph = PlanetaryHoursFactory.from_datetime(2026, 5, 28, 11, 30, **ROME)
    assert ph.date == "2026-05-28"
    assert ph.day_ruler == "Jupiter"
    assert len(ph.hours) == 24
    # The first hour of the day is ruled by the day ruler.
    assert ph.hours[0].ruler == ph.day_ruler
    # Twelve day hours, then twelve night hours.
    assert [h.is_diurnal for h in ph.hours] == [True] * 12 + [False] * 12
    assert [h.index for h in ph.hours] == list(range(1, 25))
    # The current hour bounds the requested moment and matches the table.
    assert 1 <= ph.current_index <= 24
    assert ph.current_ruler == ph.hours[ph.current_index - 1].ruler
    # Hours tile the day with no gaps.
    for earlier, later in zip(ph.hours, ph.hours[1:]):
        assert earlier.end == later.start
    assert ph.hours[0].start == ph.sunrise
    assert ph.hours[11].end == ph.sunset
    assert ph.hours[12].start == ph.sunset
    assert ph.hours[-1].end == ph.next_sunrise


def test_chaldean_sequence():
    ph = PlanetaryHoursFactory.from_datetime(2026, 5, 28, 11, 30, **ROME)
    order = list(CHALDEAN_ORDER)
    rulers = [h.ruler for h in ph.hours]
    start = order.index(rulers[0])
    assert rulers == [order[(start + i) % 7] for i in range(24)]


def test_before_sunrise_is_previous_planetary_day():
    # 02:00 local is before sunrise → belongs to Wednesday's planetary day (Mercury).
    ph = PlanetaryHoursFactory.from_datetime(2026, 5, 28, 2, 0, **ROME)
    assert ph.date == "2026-05-27"
    assert ph.day_ruler == "Mercury"
    assert ph.hours[ph.current_index - 1].is_diurnal is False


def test_polar_day_raises():
    with pytest.raises(KerykeionException):
        PlanetaryHoursFactory.from_datetime(2026, 6, 21, 12, 0, **TROMSO)


def test_high_latitude_transition_day_does_not_build_negative_hours():
    ph = PlanetaryHoursFactory.from_datetime(2026, 5, 17, 12, 0, **TROMSO)
    assert ph.sunrise < ph.sunset < ph.next_sunrise
    assert ph.hours[0].start == ph.sunrise
    assert ph.hours[-1].end == ph.next_sunrise


def test_nonexistent_local_time_raises():
    with pytest.raises(KerykeionException):
        PlanetaryHoursFactory.from_datetime(2026, 3, 29, 2, 30, **ROME)


def test_ambiguous_local_time_raises():
    with pytest.raises(KerykeionException):
        PlanetaryHoursFactory.from_datetime(2026, 10, 25, 2, 30, **ROME)


def test_invalid_timezone_raises():
    with pytest.raises(KerykeionException):
        PlanetaryHoursFactory.from_datetime(2026, 5, 28, 12, 0, latitude=0.0, longitude=0.0, tz_str="Not/AZone")
