# -*- coding: utf-8 -*-
"""Tests for the transit exactness timeline feature."""

import logging
from types import SimpleNamespace

import pytest
from datetime import datetime, timedelta

from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.schemas.kr_models import AspectModel, TransitMomentModel, TransitsTimeRangeModel
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


# ---------------------------------------------------------------------------
# v6 regression: recurring aspects must yield one event per pass
# ---------------------------------------------------------------------------


def _make_aspect(p1: str, p2: str, aspect: str, orbit: float, movement: str) -> AspectModel:
    return AspectModel(
        p1_name=p1,
        p1_owner="Transit",
        p1_abs_pos=0.0,
        p2_name=p2,
        p2_owner="Natal",
        p2_abs_pos=0.0,
        aspect=aspect,
        orbit=orbit,
        aspect_degrees=0,
        diff=orbit,
        p1=0,
        p2=1,
        aspect_movement=movement,
    )


def _make_synthetic_factory(natal_chart, samples):
    """Factory whose get_transit_moments() returns a hand-built daily timeline.

    ``samples`` maps day index -> list of (p1, p2, aspect, orbit, movement)
    in-orb aspects at that day. Days run from 2025-01-01, daily step.
    """
    n_days = max(samples) + 1 if samples else 0
    dates = [
        (datetime(2025, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        for i in range(n_days)
    ]
    moments = [
        TransitMomentModel(
            date=dates[i],
            aspects=[_make_aspect(*entry) for entry in samples.get(i, [])],
        )
        for i in range(n_days)
    ]
    # Lightweight stand-ins for the ephemeris points: only the UTC datetime
    # attribute is used (for the sampling-step estimate).
    fake_points = [SimpleNamespace(iso_formatted_utc_datetime=d) for d in dates]

    factory = TransitsTimeRangeFactory(natal_chart=natal_chart, ephemeris_data_points=fake_points)
    factory.get_transit_moments = lambda: TransitsTimeRangeModel(  # type: ignore[method-assign]
        transits=moments, subject=natal_chart, dates=dates
    )
    return factory, dates


class TestTransitEventSplitting:
    """Regression tests: tracks keyed (p1, p2, aspect) must split per pass."""

    def test_two_passes_yield_two_events(self, transit_factory):
        """Two in-orb runs separated by an out-of-orb gap → two events."""
        samples = {
            # First pass (already separating at range start → truncated)
            0: [("Moon", "Sun", "conjunction", 1.0, "Separating")],
            1: [("Moon", "Sun", "conjunction", 2.5, "Separating")],
            # days 2-4: out of orb
            # Second pass (complete: applies, peaks, separates)
            5: [("Moon", "Sun", "conjunction", 2.0, "Applying")],
            6: [("Moon", "Sun", "conjunction", 0.5, "Applying")],
            7: [("Moon", "Sun", "conjunction", 1.5, "Separating")],
            # trailing empty days so day 7 is not the range end
            9: [],
        }
        factory, dates = _make_synthetic_factory(transit_factory.natal_chart, samples)
        events = factory.get_transit_events().events

        moon_sun = [e for e in events if (e.p1_name, e.p2_name, e.aspect) == ("Moon", "Sun", "conjunction")]
        assert len(moon_sun) == 2, f"Expected 2 events (one per pass), got {len(moon_sun)}"

        first, second = sorted(moon_sun, key=lambda e: e.exact_moment)
        assert first.exact_moment == dates[0]
        assert first.min_orb == pytest.approx(1.0)
        assert second.exact_moment == dates[6]
        assert second.min_orb == pytest.approx(0.5)

    def test_truncated_event_has_none_edges(self, transit_factory):
        """An event already separating at the range start has no applying_start."""
        samples = {
            0: [("Moon", "Sun", "conjunction", 1.0, "Separating")],
            1: [("Moon", "Sun", "conjunction", 2.5, "Separating")],
            5: [("Moon", "Sun", "conjunction", 2.0, "Applying")],
            6: [("Moon", "Sun", "conjunction", 0.5, "Applying")],
            7: [("Moon", "Sun", "conjunction", 1.5, "Separating")],
            9: [],
        }
        factory, dates = _make_synthetic_factory(transit_factory.natal_chart, samples)
        events = sorted(
            (e for e in factory.get_transit_events().events if e.p1_name == "Moon"),
            key=lambda e: e.exact_moment,
        )
        first, second = events

        # First pass: truncated at the range start → applying side unknown
        assert first.applying_start is None
        assert first.separating_end == dates[1]

        # Second pass: fully observed → both edges present
        assert second.applying_start == dates[5]
        assert second.separating_end == dates[7]

    def test_event_truncated_at_range_end(self, transit_factory):
        """An event still applying on the last sample has no separating_end."""
        samples = {
            0: [],
            3: [("Moon", "Sun", "conjunction", 2.0, "Applying")],
            4: [("Moon", "Sun", "conjunction", 0.5, "Applying")],
        }
        factory, dates = _make_synthetic_factory(transit_factory.natal_chart, samples)
        events = [e for e in factory.get_transit_events().events if e.p1_name == "Moon"]
        assert len(events) == 1
        assert events[0].applying_start == dates[3]
        assert events[0].separating_end is None

    def test_orb_rate_is_degrees_per_day(self, transit_factory):
        """orb_rate = (orb_after - min_orb) / step in degrees/day."""
        samples = {
            0: [],
            5: [("Moon", "Sun", "conjunction", 2.0, "Applying")],
            6: [("Moon", "Sun", "conjunction", 0.5, "Applying")],
            7: [("Moon", "Sun", "conjunction", 1.5, "Separating")],
            9: [],
        }
        factory, _dates = _make_synthetic_factory(transit_factory.natal_chart, samples)
        events = [e for e in factory.get_transit_events().events if e.p1_name == "Moon"]
        assert len(events) == 1
        # (1.5 - 0.5) / 1 day = 1.0 deg/day
        assert events[0].orb_rate == pytest.approx(1.0)

    def test_real_lunar_recurrence_splits(self):
        """60 days of daily samples: lunar aspects must recur as separate events.

        Before the v6 fix, all recurrences of the same (p1, p2, aspect) were
        merged into one event spanning the whole range.
        """
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Recurrence Test", 1990, 6, 15, 14, 30,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
        )
        start = datetime(2025, 1, 1)
        ephemeris = EphemerisDataFactory(
            start_datetime=start, end_datetime=start + timedelta(days=60),
            step_type="days", step=1,
            lat=41.9028, lng=12.4964, tz_str="Europe/Rome",
        )
        factory = TransitsTimeRangeFactory(
            natal_chart=natal,
            ephemeris_data_points=ephemeris.get_ephemeris_data_as_astrological_subjects(),
        )
        events = factory.get_transit_events().events

        moon_event_counts: dict = {}
        for e in events:
            if e.p1_name == "Moon":
                key = (e.p1_name, e.p2_name, e.aspect)
                moon_event_counts[key] = moon_event_counts.get(key, 0) + 1

        assert moon_event_counts, "No lunar transit events found in 60 days"
        assert max(moon_event_counts.values()) >= 2, (
            "The Moon recurs over every natal point ~monthly: 60 days of data "
            f"must produce repeated events per aspect, got {moon_event_counts}"
        )

        # Distinct events of the same key must not overlap in time
        for key, count in moon_event_counts.items():
            if count < 2:
                continue
            same_key = sorted(
                (e for e in events if (e.p1_name, e.p2_name, e.aspect) == key),
                key=lambda e: e.exact_moment,
            )
            for earlier, later in zip(same_key, same_key[1:]):
                assert earlier.exact_moment < later.exact_moment


class TestUndersamplingWarning:
    """A coarse ephemeris step with fast movers active must log a warning."""

    def test_daily_step_with_moon_warns(self, transit_factory, caplog):
        factory = TransitsTimeRangeFactory(
            natal_chart=transit_factory.natal_chart,
            ephemeris_data_points=transit_factory.ephemeris_data_points,
        )
        with caplog.at_level(logging.WARNING):
            factory.get_transit_moments()
        assert "sampling step" in caplog.text, (
            "Daily sampling with the Moon active must log an undersampling warning"
        )

    def test_slow_points_do_not_warn(self, transit_factory, caplog):
        factory = TransitsTimeRangeFactory(
            natal_chart=transit_factory.natal_chart,
            ephemeris_data_points=transit_factory.ephemeris_data_points,
            active_points=["Jupiter", "Saturn"],
        )
        with caplog.at_level(logging.WARNING):
            factory.get_transit_moments()
        assert "sampling step" not in caplog.text, (
            "Slow movers within orb for weeks must not trigger the warning at daily steps"
        )
