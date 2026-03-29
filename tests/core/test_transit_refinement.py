# -*- coding: utf-8 -*-
"""Tests for transit exact moment refinement via bisection (v6.0)."""

import pytest
from datetime import datetime, timedelta
from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory


@pytest.fixture(scope="module")
def natal_chart():
    return AstrologicalSubjectFactory.from_birth_data(
        "Transit Test", 1990, 1, 1, 12, 0,
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        city="Rome", nation="IT", online=False,
    )


@pytest.fixture(scope="module")
def transit_factory(natal_chart):
    start = datetime(2025, 1, 1)
    end = start + timedelta(days=30)
    ephemeris = EphemerisDataFactory(
        start_datetime=start,
        end_datetime=end,
        step_type="days",
        step=1,
        lat=natal_chart.lat,
        lng=natal_chart.lng,
        tz_str=natal_chart.tz_str,
    )
    data_points = ephemeris.get_ephemeris_data_as_astrological_subjects()
    return TransitsTimeRangeFactory(
        natal_chart=natal_chart,
        ephemeris_data_points=data_points,
    )


class TestTransitRefinement:
    def test_events_without_refinement(self, transit_factory):
        """get_transit_events() should work without refinement (baseline)."""
        events = transit_factory.get_transit_events()
        assert events is not None
        assert isinstance(events.events, list)

    def test_events_with_refinement(self, transit_factory):
        """get_transit_events(refine_exact_moments=True) should work."""
        events = transit_factory.get_transit_events(refine_exact_moments=True)
        assert events is not None
        assert isinstance(events.events, list)

    def test_refined_events_have_smaller_orb(self, transit_factory):
        """Refined events should have orbs <= unrefined orbs (or very close)."""
        unrefined = transit_factory.get_transit_events(refine_exact_moments=False)
        refined = transit_factory.get_transit_events(refine_exact_moments=True)

        # Build lookup by (p1, p2, aspect)
        unrefined_lookup = {
            (e.p1_name, e.p2_name, e.aspect): e.min_orb
            for e in unrefined.events
        }

        improved_count = 0
        for event in refined.events:
            key = (event.p1_name, event.p2_name, event.aspect)
            if key in unrefined_lookup:
                if event.min_orb <= unrefined_lookup[key] + 0.001:
                    improved_count += 1

        # Most events should have equal or better orb after refinement
        if len(refined.events) > 0:
            assert improved_count / len(refined.events) >= 0.8, (
                f"Only {improved_count}/{len(refined.events)} events improved"
            )

    def test_refined_exact_moment_differs(self, transit_factory):
        """At least some refined exact_moments should differ from unrefined.

        Refinement only applies to events where the minimum orb is NOT
        at the first or last step of the track (needs bracketing steps on both sides).
        This test verifies that refinement actually changes at least one event,
        so the test would fail if the refinement code were a no-op.
        """
        unrefined = transit_factory.get_transit_events(refine_exact_moments=False)
        refined = transit_factory.get_transit_events(refine_exact_moments=True)

        unrefined_lookup = {
            (e.p1_name, e.p2_name, e.aspect): e
            for e in unrefined.events
        }

        different_count = 0
        comparable_count = 0
        for event in refined.events:
            key = (event.p1_name, event.p2_name, event.aspect)
            unref = unrefined_lookup.get(key)
            if unref is None:
                continue
            comparable_count += 1
            if event.exact_moment != unref.exact_moment or event.min_orb < unref.min_orb:
                different_count += 1

        assert comparable_count > 0, "No comparable events found"
        # The critical assertion: refinement must actually change some events.
        # With 30 days of daily steps, there should be several events with
        # bracketing steps eligible for bisection refinement.
        assert different_count > 0, (
            f"Refinement was a no-op: {comparable_count} comparable events but "
            f"none had a different exact_moment or improved orb"
        )

    def test_refined_orb_not_worse_than_unrefined(self, transit_factory):
        """For matched events, the refined orb should be <= the unrefined orb."""
        unrefined = transit_factory.get_transit_events(refine_exact_moments=False)
        refined = transit_factory.get_transit_events(refine_exact_moments=True)

        unrefined_lookup = {
            (e.p1_name, e.p2_name, e.aspect): e
            for e in unrefined.events
        }

        checked = 0
        for event in refined.events:
            key = (event.p1_name, event.p2_name, event.aspect)
            unref = unrefined_lookup.get(key)
            if unref is None:
                continue
            # Allow a tiny floating-point tolerance (1e-6 degrees ~ 0.004 arcsec)
            assert event.min_orb <= unref.min_orb + 1e-6, (
                f"Refined orb ({event.min_orb}) is worse than unrefined "
                f"({unref.min_orb}) for {key}"
            )
            checked += 1

        assert checked > 0, "No comparable events to check orbs"

    def test_refined_exact_moment_within_event_window(self, transit_factory):
        """The refined exact_moment must fall between applying_start and separating_end."""
        refined = transit_factory.get_transit_events(refine_exact_moments=True)

        checked = 0
        for event in refined.events:
            if event.applying_start is None or event.separating_end is None:
                continue

            exact_dt = datetime.fromisoformat(event.exact_moment)
            start_dt = datetime.fromisoformat(event.applying_start)
            end_dt = datetime.fromisoformat(event.separating_end)

            assert start_dt <= exact_dt <= end_dt, (
                f"Refined exact_moment {event.exact_moment} is outside the event "
                f"window [{event.applying_start}, {event.separating_end}] "
                f"for ({event.p1_name}, {event.p2_name}, {event.aspect})"
            )
            checked += 1

        assert checked > 0, "No events with both applying_start and separating_end"

    def test_event_structure_preserved(self, transit_factory):
        """Refined events should have all required fields."""
        events = transit_factory.get_transit_events(refine_exact_moments=True)
        for event in events.events:
            assert event.p1_name is not None
            assert event.p2_name is not None
            assert event.aspect is not None
            assert event.exact_moment is not None
            assert event.min_orb >= 0


class TestRefineExactMomentEdgeCases:
    """Test edge-case/error paths in _refine_exact_moment."""

    def test_refine_unknown_natal_planet_returns_none(self, transit_factory):
        """If p2_name doesn't match any natal point, should return None."""
        result = transit_factory._refine_exact_moment(
            p1_name="Sun",
            p2_name="NonExistentPlanet",
            aspect_name="conjunction",
            left_date_str="2025-01-01T00:00:00",
            right_date_str="2025-01-03T00:00:00",
        )
        assert result is None

    def test_refine_unknown_transit_planet_returns_none(self, transit_factory):
        """If p1_name doesn't match any known planet, should return None."""
        result = transit_factory._refine_exact_moment(
            p1_name="NonExistentTransitPlanet",
            p2_name="Sun",
            aspect_name="conjunction",
            left_date_str="2025-01-01T00:00:00",
            right_date_str="2025-01-03T00:00:00",
        )
        assert result is None

    def test_refine_invalid_aspect_returns_none(self, transit_factory):
        """If aspect_name doesn't match any chart aspect, should return None."""
        result = transit_factory._refine_exact_moment(
            p1_name="Sun",
            p2_name="Moon",
            aspect_name="nonexistent_aspect",
            left_date_str="2025-01-01T00:00:00",
            right_date_str="2025-01-03T00:00:00",
        )
        assert result is None

    def test_refine_invalid_date_returns_none(self, transit_factory):
        """If date strings are invalid, should return None."""
        result = transit_factory._refine_exact_moment(
            p1_name="Sun",
            p2_name="Moon",
            aspect_name="conjunction",
            left_date_str="not-a-date",
            right_date_str="also-not-a-date",
        )
        assert result is None

    def test_refine_calc_ut_exception_returns_none(self, transit_factory):
        """If swe.calc_ut raises during refinement, should return None."""
        from unittest.mock import patch
        with patch(
            "swisseph.calc_ut",
            side_effect=RuntimeError("Mock swe failure"),
        ):
            result = transit_factory._refine_exact_moment(
                p1_name="Sun",
                p2_name="Moon",
                aspect_name="conjunction",
                left_date_str="2025-01-01T00:00:00",
                right_date_str="2025-01-03T00:00:00",
            )
            assert result is None

    def test_refine_tno_planet_path(self, transit_factory):
        """If p1_name is a TNO like 'Eris', should use AST_OFFSET + tno_num path."""
        # Eris is a TNO, so it goes through the TNO_PLANETS lookup
        # If natal chart doesn't have Eris as p2, this tests the p1 TNO path
        result = transit_factory._refine_exact_moment(
            p1_name="Eris",
            p2_name="Sun",
            aspect_name="conjunction",
            left_date_str="2025-01-01T00:00:00",
            right_date_str="2025-01-03T00:00:00",
        )
        # Should return a result (or None if Eris is not found), but shouldn't crash
        assert result is None or isinstance(result, tuple)

    def test_refine_quarter_point_exception_returns_none(self, transit_factory):
        """If swe.calc_ut raises during quarter-point evaluation, should return None."""
        from unittest.mock import patch
        from kerykeion.ephemeris_backend import swe

        original_calc_ut = swe.calc_ut
        call_count = [0]

        def mock_calc_ut(jd, planet_id, iflag):
            call_count[0] += 1
            # Let the first call (midpoint) succeed, fail on subsequent (quarter points)
            if call_count[0] <= 1:
                return original_calc_ut(jd, planet_id, iflag)
            raise RuntimeError("Mock quarter-point failure")

        with patch("swisseph.calc_ut", side_effect=mock_calc_ut):
            result = transit_factory._refine_exact_moment(
                p1_name="Sun",
                p2_name="Moon",
                aspect_name="conjunction",
                left_date_str="2025-01-01T00:00:00",
                right_date_str="2025-01-03T00:00:00",
            )
            assert result is None
