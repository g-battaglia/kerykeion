# -*- coding: utf-8 -*-
"""Tests for transit exact moment refinement via bisection (v6.0)."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_backend import ephe as _swe_module
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits.factory import TransitsTimeRangeFactory


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


@pytest.fixture(scope="module")
def unrefined_events(transit_factory):
    return transit_factory.get_transit_events(refine_exact_moments=False)


@pytest.fixture(scope="module")
def refined_events(transit_factory):
    return transit_factory.get_transit_events(refine_exact_moments=True)


class TestTransitRefinement:
    def test_events_without_refinement(self, unrefined_events):
        """get_transit_events() should work without refinement (baseline)."""
        assert unrefined_events is not None
        assert isinstance(unrefined_events.events, list)

    def test_events_with_refinement(self, refined_events):
        """get_transit_events(refine_exact_moments=True) should work."""
        assert refined_events is not None
        assert isinstance(refined_events.events, list)

    @staticmethod
    def _paired_events(unrefined_events, refined_events):
        """Pair refined/unrefined events per (p1, p2, aspect) key, in order.

        The same (p1, p2, aspect) triple legitimately occurs several times in
        the range (one event per pass since the v6 per-run splitting), so the
        events must be matched pairwise in chronological order, not via a
        last-one-wins dict.
        """
        from collections import defaultdict

        unref_by_key = defaultdict(list)
        for e in unrefined_events.events:
            unref_by_key[(e.p1_name, e.p2_name, e.aspect)].append(e)
        ref_by_key = defaultdict(list)
        for e in refined_events.events:
            ref_by_key[(e.p1_name, e.p2_name, e.aspect)].append(e)

        # Iterating only ref keys would silently ignore any key present in just
        # one pass; require the two passes to expose the exact same aspect keys.
        assert set(unref_by_key.keys()) == set(ref_by_key.keys()), (
            "Refined and unrefined passes produced different aspect keys: "
            f"{set(unref_by_key.keys()) ^ set(ref_by_key.keys())}"
        )

        pairs = []
        for key, ref_list in ref_by_key.items():
            unref_list = unref_by_key.get(key, [])
            # Runs are identical between the two passes (splitting happens
            # before refinement), so events correspond one-to-one in order.
            assert len(unref_list) == len(ref_list), f"Event count mismatch for {key}"
            pairs.extend(zip(unref_list, ref_list))
        return pairs

    def test_refined_events_have_smaller_orb(self, unrefined_events, refined_events):
        """Refined events should have orbs <= unrefined orbs (or very close)."""
        pairs = self._paired_events(unrefined_events, refined_events)

        improved_count = sum(1 for unref, ref in pairs if ref.min_orb <= unref.min_orb + 0.001)

        # Most events should have equal or better orb after refinement
        if pairs:
            assert improved_count / len(pairs) >= 0.8, (
                f"Only {improved_count}/{len(pairs)} events improved"
            )

    def test_refined_exact_moment_differs(self, unrefined_events, refined_events):
        """At least some refined exact_moments should differ from unrefined.

        Refinement only applies to events where the minimum orb is NOT
        at the first or last step of the track (needs bracketing steps on both sides).
        This test verifies that refinement actually changes at least one event,
        so the test would fail if the refinement code were a no-op.
        """
        pairs = self._paired_events(unrefined_events, refined_events)

        different_count = sum(
            1
            for unref, ref in pairs
            if ref.exact_moment != unref.exact_moment or ref.min_orb < unref.min_orb
        )

        assert pairs, "No comparable events found"
        # The critical assertion: refinement must actually change some events.
        # With 30 days of daily steps, there should be several events with
        # bracketing steps eligible for bisection refinement.
        assert different_count > 0, (
            f"Refinement was a no-op: {len(pairs)} comparable events but "
            f"none had a different exact_moment or improved orb"
        )

    def test_refined_orb_not_worse_than_unrefined(self, unrefined_events, refined_events):
        """For matched events, the refined orb should be <= the unrefined orb."""
        pairs = self._paired_events(unrefined_events, refined_events)

        for unref, ref in pairs:
            # Allow a tiny floating-point tolerance (1e-6 degrees ~ 0.004 arcsec)
            assert ref.min_orb <= unref.min_orb + 1e-6, (
                f"Refined orb ({ref.min_orb}) is worse than unrefined "
                f"({unref.min_orb}) for ({ref.p1_name}, {ref.p2_name}, {ref.aspect})"
            )

        assert pairs, "No comparable events to check orbs"

    def test_refined_exact_moment_within_event_window(self, refined_events):
        """The refined exact_moment must fall between applying_start and separating_end."""
        refined = refined_events

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

    def test_event_structure_preserved(self, refined_events):
        """Refined events should have all required fields."""
        events = refined_events
        for event in events.events:
            assert event.p1_name is not None
            assert event.p2_name is not None
            assert event.aspect is not None
            assert event.exact_moment is not None
            assert event.min_orb >= 0


@pytest.mark.xdist_group("transit_mock")
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
        """If ephe.calc_ut raises during refinement, should return None."""
        with patch.object(
            _swe_module, "calc_ut",
            side_effect=RuntimeError("Mock ephe failure"),
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

    def test_refine_probe_point_exception_returns_none(self, transit_factory):
        """If ephe.calc_ut raises during a probe-point evaluation, should return None."""
        original_calc_ut = _swe_module.calc_ut
        call_count = [0]

        def mock_calc_ut(jd, planet_id, iflag):
            call_count[0] += 1
            # Let the first call (first probe) succeed, fail on subsequent probes
            if call_count[0] <= 1:
                return original_calc_ut(jd, planet_id, iflag)
            raise RuntimeError("Mock probe-point failure")

        with patch.object(_swe_module, "calc_ut", side_effect=mock_calc_ut):
            result = transit_factory._refine_exact_moment(
                p1_name="Sun",
                p2_name="Moon",
                aspect_name="conjunction",
                left_date_str="2025-01-01T00:00:00",
                right_date_str="2025-01-03T00:00:00",
            )
            assert result is None

    def test_refine_skipped_for_non_geocentric_perspective(self):
        """Non-geocentric natal charts keep the coarse values (no refinement)."""
        helio_natal = AstrologicalSubjectFactory.from_birth_data(
            "Helio Test", 1990, 1, 1, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            perspective_type="Heliocentric",
        )
        factory = TransitsTimeRangeFactory(natal_chart=helio_natal, ephemeris_data_points=[])
        result = factory._refine_exact_moment(
            p1_name="Mars",
            p2_name="Mars",
            aspect_name="conjunction",
            left_date_str="2025-01-01T00:00:00",
            right_date_str="2025-01-03T00:00:00",
        )
        assert result is None


class TestSiderealRefinement:
    """v6 regression: refinement must run in the natal chart's zodiac.

    Before the fix, the bisection compared the SIDEREAL natal position with a
    TROPICAL calc_ut longitude (~24° apart for LAHIRI) and overwrote the
    correct coarse minimum with garbage.
    """

    @pytest.fixture(scope="class")
    def sidereal_factory(self):
        natal = AstrologicalSubjectFactory.from_birth_data(
            "Sidereal Transit Test", 1990, 1, 1, 12, 0,
            lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            zodiac_type="Sidereal", sidereal_mode="LAHIRI",
        )
        start = datetime(2025, 1, 1)
        ephemeris = EphemerisDataFactory(
            start_datetime=start,
            end_datetime=start + timedelta(days=15),
            step_type="days",
            step=1,
            lat=natal.lat,
            lng=natal.lng,
            tz_str=natal.tz_str,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        )
        return TransitsTimeRangeFactory(
            natal_chart=natal,
            ephemeris_data_points=ephemeris.get_ephemeris_data_as_astrological_subjects(),
        )

    def test_sidereal_refined_orbs_not_worse(self, sidereal_factory):
        """Refined orbs must never be worse than the coarse ones (sidereal natal)."""
        from collections import defaultdict

        unrefined = sidereal_factory.get_transit_events(refine_exact_moments=False)
        refined = sidereal_factory.get_transit_events(refine_exact_moments=True)

        unref_by_key = defaultdict(list)
        for e in unrefined.events:
            unref_by_key[(e.p1_name, e.p2_name, e.aspect)].append(e)
        ref_by_key = defaultdict(list)
        for e in refined.events:
            ref_by_key[(e.p1_name, e.p2_name, e.aspect)].append(e)

        checked = 0
        for key, ref_list in ref_by_key.items():
            unref_list = unref_by_key.get(key, [])
            assert len(unref_list) == len(ref_list), f"Event count mismatch for {key}"
            for unref, ref in zip(unref_list, ref_list):
                assert ref.min_orb <= unref.min_orb + 1e-6, (
                    f"Sidereal refinement degraded {key}: {ref.min_orb} > {unref.min_orb}"
                )
                checked += 1

        assert checked > 0, "No sidereal events to compare"

    def test_sidereal_refinement_improves_some_event(self, sidereal_factory):
        """Refinement must still be effective (not silently skipped) for sidereal charts."""
        unrefined = sidereal_factory.get_transit_events(refine_exact_moments=False)
        refined = sidereal_factory.get_transit_events(refine_exact_moments=True)

        unref_orbs = sorted(e.min_orb for e in unrefined.events)
        ref_orbs = sorted(e.min_orb for e in refined.events)
        assert len(unref_orbs) == len(ref_orbs)
        assert any(r < u - 1e-9 for r, u in zip(ref_orbs, unref_orbs)), (
            "No sidereal event improved after refinement — refinement appears to be a no-op"
        )
