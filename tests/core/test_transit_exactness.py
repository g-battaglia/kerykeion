# -*- coding: utf-8 -*-
"""Tests for the transit exactness timeline feature."""

import pytest
from datetime import datetime, timedelta

from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory


@pytest.fixture(scope="module")
def transit_factory():
    natal = AstrologicalSubjectFactory.from_birth_data(
        "Transit Test", 1990, 6, 15, 14, 30,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )
    start = datetime(2025, 1, 1)
    end = start + timedelta(days=30)
    ephemeris = EphemerisDataFactory(
        start_datetime=start, end_datetime=end,
        step_type="days", step=1,
        lat=41.9028, lng=12.4964, tz_str="Europe/Rome",
    )
    eph_data = ephemeris.get_ephemeris_data_as_astrological_subjects()
    return TransitsTimeRangeFactory(natal_chart=natal, ephemeris_data_points=eph_data)


class TestTransitEvents:
    def test_returns_events(self, transit_factory):
        result = transit_factory.get_transit_events()
        assert result is not None
        assert len(result.events) > 0

    def test_events_have_required_fields(self, transit_factory):
        result = transit_factory.get_transit_events()
        for event in result.events:
            assert event.p1_name is not None
            assert event.p2_name is not None
            assert event.aspect is not None
            assert event.exact_moment is not None
            assert event.min_orb >= 0

    def test_events_sorted_by_exact_moment(self, transit_factory):
        result = transit_factory.get_transit_events()
        for i in range(len(result.events) - 1):
            assert result.events[i].exact_moment <= result.events[i + 1].exact_moment

    def test_event_has_applying_and_separating(self, transit_factory):
        result = transit_factory.get_transit_events()
        # At least some events should have applying_start and separating_end
        events_with_range = [e for e in result.events if e.applying_start and e.separating_end]
        assert len(events_with_range) > 0

    def test_min_orb_is_small(self, transit_factory):
        result = transit_factory.get_transit_events()
        for event in result.events:
            # Min orb should be within the aspect orb (max 10 degrees for conjunction)
            assert event.min_orb <= 10.0

    def test_subject_preserved(self, transit_factory):
        result = transit_factory.get_transit_events()
        assert result.subject is not None
        assert result.subject.name == "Transit Test"

    def test_unique_events_per_exact_moment(self, transit_factory):
        """Each (p1, p2, aspect, exact_moment) combination should be unique.

        Note: the same (p1, p2, aspect) triple *can* appear more than once
        in a 30-day window due to retrograde motion causing multiple exact
        passes.  We only check that the exact same moment is not duplicated.
        """
        result = transit_factory.get_transit_events()
        keys = set()
        for event in result.events:
            key = (event.p1_name, event.p2_name, event.aspect, event.exact_moment)
            assert key not in keys, f"Duplicate event at same moment: {key}"
            keys.add(key)
