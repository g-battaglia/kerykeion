# -*- coding: utf-8 -*-
"""
Tests for the HeliacalFactory module.

Verifies heliacal rising/setting calculations using swe.heliacal_ut()
with default atmospheric parameters.
"""

import swisseph as swe
import pytest

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


@pytest.fixture
def factory() -> HeliacalFactory:
    """Return a HeliacalFactory with the default ephemeris path."""
    return HeliacalFactory()


# Tests: next_heliacal_rising ------------------------------------------------

class TestNextHeliacalRising:
    """Tests for HeliacalFactory.next_heliacal_rising()."""

    def test_returns_valid_event_model(self, factory: HeliacalFactory):
        """Factory returns a properly populated HeliacalEventModel."""
        event = factory.next_heliacal_rising(
            julian_day=START_JD,
            planet_name_or_star="Venus",
            geopos=ROME_GEOPOS,
        )

        assert isinstance(event, HeliacalEventModel)
        assert event.event_type == "heliacal_rising"
        assert event.planet_name == "Venus"
        assert event.julian_day > 0
        assert len(event.datestamp) == 10  # YYYY-MM-DD

    def test_julian_day_is_in_future(self, factory: HeliacalFactory):
        """The returned Julian Day must be after the input start JD."""
        event = factory.next_heliacal_rising(
            julian_day=START_JD,
            planet_name_or_star="Mars",
            geopos=ROME_GEOPOS,
        )

        assert event.julian_day > START_JD

    def test_different_planets_give_different_dates(self, factory: HeliacalFactory):
        """Different planets should generally have different heliacal rising dates."""
        venus = factory.next_heliacal_rising(START_JD, "Venus", ROME_GEOPOS)
        mars = factory.next_heliacal_rising(START_JD, "Mars", ROME_GEOPOS)

        # They might coincidentally be the same day, but the JDs should differ.
        assert venus.julian_day != mars.julian_day

    def test_default_atmospheric_parameters_work(self, factory: HeliacalFactory):
        """Calling with no explicit atmo/observer should succeed (defaults apply)."""
        event = factory.next_heliacal_rising(
            julian_day=START_JD,
            planet_name_or_star="Jupiter",
            geopos=ROME_GEOPOS,
        )
        assert event.event_type == "heliacal_rising"
        assert event.julian_day > START_JD

    def test_custom_atmospheric_parameters(self, factory: HeliacalFactory):
        """Explicit atmospheric parameters should be accepted."""
        atmo = (DEFAULT_PRESSURE, DEFAULT_TEMPERATURE, DEFAULT_HUMIDITY, DEFAULT_EXTINCTION)
        event = factory.next_heliacal_rising(
            julian_day=START_JD,
            planet_name_or_star="Saturn",
            geopos=ROME_GEOPOS,
            atmo=atmo,
        )
        assert event.event_type == "heliacal_rising"
        assert event.julian_day > START_JD


# Tests: search_events -------------------------------------------------------

class TestSearchEvents:
    """Tests for HeliacalFactory.search_events()."""

    def test_returns_list_of_events(self, factory: HeliacalFactory):
        """search_events returns a list of HeliacalEventModel instances."""
        events = factory.search_events(
            julian_day=START_JD,
            geopos=ROME_GEOPOS,
            count=5,
        )

        assert isinstance(events, list)
        assert len(events) <= 5
        assert all(isinstance(e, HeliacalEventModel) for e in events)

    def test_events_are_sorted_chronologically(self, factory: HeliacalFactory):
        """Events should be ordered by Julian Day."""
        events = factory.search_events(
            julian_day=START_JD,
            geopos=ROME_GEOPOS,
            count=5,
        )

        jds = [e.julian_day for e in events]
        assert jds == sorted(jds)

    def test_all_events_in_future(self, factory: HeliacalFactory):
        """Every returned event should have a JD after the input start JD."""
        events = factory.search_events(
            julian_day=START_JD,
            geopos=ROME_GEOPOS,
            count=5,
        )

        for event in events:
            assert event.julian_day > START_JD

    def test_count_limits_results(self, factory: HeliacalFactory):
        """Requesting count=2 should return at most 2 events."""
        events = factory.search_events(
            julian_day=START_JD,
            geopos=ROME_GEOPOS,
            count=2,
        )

        assert len(events) <= 2

    def test_subscriptable_access(self, factory: HeliacalFactory):
        """HeliacalEventModel should support dictionary-style access."""
        event = factory.next_heliacal_rising(START_JD, "Venus", ROME_GEOPOS)

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
