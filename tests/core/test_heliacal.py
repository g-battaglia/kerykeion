# -*- coding: utf-8 -*-
"""
Tests for the HeliacalFactory module.

Verifies heliacal rising/setting calculations using swe.heliacal_ut()
with default atmospheric parameters.
"""

import pytest
from kerykeion.ephemeris_backend import swe

from kerykeion.heliacal import (
    HeliacalFactory,
    HeliacalEventModel,
    HELIACAL_RISING,
    HELIACAL_SETTING,
)
from kerykeion.heliacal.heliacal_factory import (
    DEFAULT_PRESSURE,
    DEFAULT_TEMPERATURE,
    DEFAULT_HUMIDITY,
    DEFAULT_EXTINCTION,
)


# Fixtures -------------------------------------------------------------------

ROME_GEOPOS = (12.4964, 41.9028, 50.0)  # lng, lat, altitude
START_JD = swe.julday(2026, 3, 26, 0)   # 2026-03-26 00:00 UT


@pytest.fixture(scope="module")
def factory() -> HeliacalFactory:
    """Return a HeliacalFactory with the default ephemeris path (module-scoped)."""
    return HeliacalFactory()


# Cached results to avoid repeating expensive heliacal_ut() calls
_heliacal_cache: dict = {}


def _cached_rising(factory, planet):
    if planet not in _heliacal_cache:
        _heliacal_cache[planet] = factory.next_heliacal_rising(
            julian_day=START_JD, planet_name_or_star=planet, geopos=ROME_GEOPOS,
        )
    return _heliacal_cache[planet]


# Tests: next_heliacal_rising ------------------------------------------------

class TestNextHeliacalRising:
    """Tests for HeliacalFactory.next_heliacal_rising()."""

    def test_returns_valid_event_model(self, factory: HeliacalFactory):
        event = _cached_rising(factory, "Venus")
        assert isinstance(event, HeliacalEventModel)
        assert event.event_type == "heliacal_rising"
        assert event.planet_name == "Venus"
        assert event.julian_day > 0
        assert len(event.datestamp) == 10

    def test_julian_day_is_in_future(self, factory: HeliacalFactory):
        event = _cached_rising(factory, "Mars")
        assert event.julian_day > START_JD

    def test_different_planets_give_different_dates(self, factory: HeliacalFactory):
        venus = _cached_rising(factory, "Venus")
        mars = _cached_rising(factory, "Mars")
        assert venus.julian_day != mars.julian_day

    def test_default_atmospheric_parameters_work(self, factory: HeliacalFactory):
        event = _cached_rising(factory, "Jupiter")
        assert event.event_type == "heliacal_rising"
        assert event.julian_day > START_JD

    def test_custom_atmospheric_parameters(self, factory: HeliacalFactory):
        atmo = (DEFAULT_PRESSURE, DEFAULT_TEMPERATURE, DEFAULT_HUMIDITY, DEFAULT_EXTINCTION)
        event = factory.next_heliacal_rising(
            julian_day=START_JD, planet_name_or_star="Venus",
            geopos=ROME_GEOPOS, atmo=atmo,
        )
        assert event.event_type == "heliacal_rising"
        assert event.julian_day > START_JD


# Tests: search_events -------------------------------------------------------

_search_cache: dict = {}


class TestSearchEvents:
    """Tests for HeliacalFactory.search_events()."""

    def _get_events(self, factory, count=2):
        if count not in _search_cache:
            _search_cache[count] = factory.search_events(
                julian_day=START_JD, geopos=ROME_GEOPOS, count=count,
            )
        return _search_cache[count]

    def test_returns_list_of_events(self, factory: HeliacalFactory):
        events = self._get_events(factory, count=2)
        assert isinstance(events, list)
        assert len(events) <= 2
        assert all(isinstance(e, HeliacalEventModel) for e in events)

    def test_events_are_sorted_chronologically(self, factory: HeliacalFactory):
        events = self._get_events(factory, count=2)
        jds = [e.julian_day for e in events]
        assert jds == sorted(jds)

    def test_all_events_in_future(self, factory: HeliacalFactory):
        events = self._get_events(factory, count=2)
        for event in events:
            assert event.julian_day > START_JD

    def test_count_limits_results(self, factory: HeliacalFactory):
        events = self._get_events(factory, count=2)
        assert len(events) <= 2

    def test_subscriptable_access(self, factory: HeliacalFactory):
        event = _cached_rising(factory, "Venus")
        assert event["event_type"] == event.event_type
        assert event["planet_name"] == event.planet_name
        assert event["julian_day"] == event.julian_day
        assert event["datestamp"] == event.datestamp


# Tests: default constants ---------------------------------------------------

class TestDefaultConstants:
    """Verify that default atmospheric constants are set correctly."""

    def test_default_pressure(self):
        assert DEFAULT_PRESSURE == 1013.25

    def test_default_temperature(self):
        assert DEFAULT_TEMPERATURE == 15.0

    def test_default_humidity(self):
        assert DEFAULT_HUMIDITY == 40.0

    def test_default_extinction(self):
        assert DEFAULT_EXTINCTION == 0.2


# Tests: swe reference ---------------------------------------------------------

class TestSweReference:
    """Compare factory output with direct swe.heliacal_ut() calls."""

    def test_venus_heliacal_rising_matches_swe(self, factory: HeliacalFactory):
        """Factory next_heliacal_rising JD must equal raw swe.heliacal_ut dret[0]."""
        from kerykeion.heliacal.heliacal_factory import DEFAULT_ATMO, DEFAULT_OBSERVER

        event = _cached_rising(factory, "Venus")

        dret = swe.heliacal_ut(
            START_JD, ROME_GEOPOS, DEFAULT_ATMO, DEFAULT_OBSERVER,
            "Venus", swe.HELIACAL_RISING, 0,
        )
        assert event.julian_day == pytest.approx(dret[0], abs=1e-6)

    def test_mars_heliacal_rising_matches_swe(self, factory: HeliacalFactory):
        """Same check for Mars to ensure it generalises across planets."""
        from kerykeion.heliacal.heliacal_factory import DEFAULT_ATMO, DEFAULT_OBSERVER

        event = _cached_rising(factory, "Mars")

        dret = swe.heliacal_ut(
            START_JD, ROME_GEOPOS, DEFAULT_ATMO, DEFAULT_OBSERVER,
            "Mars", swe.HELIACAL_RISING, 0,
        )
        assert event.julian_day == pytest.approx(dret[0], abs=1e-6)
