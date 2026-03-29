# -*- coding: utf-8 -*-
"""Tests for Out-of-Bounds detection and declination aspects (parallels/contra-parallels)."""

import pytest
swe = pytest.importorskip("swisseph")
from kerykeion import AstrologicalSubjectFactory, AspectsFactory


@pytest.fixture(scope="module")
def john_lennon():
    return AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", 1940, 10, 9, 18, 30,
        lng=-2.9916, lat=53.4084, tz_str="Europe/London",
        city="Liverpool", nation="GB", online=False,
    )


@pytest.fixture(scope="module")
def yoko_ono():
    return AstrologicalSubjectFactory.from_birth_data(
        "Yoko Ono", 1933, 2, 18, 20, 30,
        lng=139.6503, lat=35.6762, tz_str="Asia/Tokyo",
        city="Tokyo", nation="JP", online=False,
    )


class TestOutOfBounds:
    def test_oob_field_populated(self, john_lennon):
        """All planets with declination should have is_out_of_bounds set."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(john_lennon, name)
            if point is not None and point.declination is not None:
                assert point.is_out_of_bounds is not None, f"{name} should have is_out_of_bounds"
                assert isinstance(point.is_out_of_bounds, bool)

    def test_sun_never_oob(self, john_lennon):
        """The Sun's declination equals the obliquity boundary — it should not be OOB."""
        # The Sun defines the obliquity, so abs(sun_dec) <= true_obliquity always
        assert john_lennon.sun.is_out_of_bounds is False

    def test_oob_is_boolean(self, john_lennon):
        """OOB should be a strict boolean, not a truthy value."""
        for name in ["sun", "moon", "mercury", "venus", "mars"]:
            point = getattr(john_lennon, name)
            if point is not None and point.is_out_of_bounds is not None:
                assert type(point.is_out_of_bounds) is bool

    def test_oob_respects_obliquity(self, john_lennon):
        """OOB planets should have declination exceeding ~23.44 degrees."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(john_lennon, name)
            if point is not None and point.is_out_of_bounds is True:
                assert abs(point.declination) > 23.0, (
                    f"{name} marked OOB but declination {point.declination} is below 23 deg"
                )

    def test_non_oob_within_obliquity(self, john_lennon):
        """Non-OOB planets should have declination within obliquity."""
        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(john_lennon, name)
            if point is not None and point.is_out_of_bounds is False:
                assert abs(point.declination) <= 23.5, (
                    f"{name} not OOB but declination {point.declination} exceeds 23.5 deg"
                )

    def test_sun_declination_matches_swe_reference(self, john_lennon):
        """Sun declination must match swe.calc_ut with FLG_EQUATORIAL within 0.001 deg."""
        jd = john_lennon.julian_day
        swe.set_ephe_path("")
        sun_eq = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0]
        expected_dec = sun_eq[1]
        assert abs(john_lennon.sun.declination - expected_dec) < 0.001, (
            f"Sun declination {john_lennon.sun.declination} != "
            f"swe reference {expected_dec}"
        )

    def test_moon_declination_matches_swe_reference(self, john_lennon):
        """Moon declination must match swe.calc_ut with FLG_EQUATORIAL within 0.001 deg."""
        jd = john_lennon.julian_day
        swe.set_ephe_path("")
        moon_eq = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH | swe.FLG_EQUATORIAL)[0]
        expected_dec = moon_eq[1]
        assert abs(john_lennon.moon.declination - expected_dec) < 0.001, (
            f"Moon declination {john_lennon.moon.declination} != "
            f"swe reference {expected_dec}"
        )

    def test_oob_flag_consistent_with_obliquity(self, john_lennon):
        """is_out_of_bounds must equal abs(declination) > true obliquity from swe."""
        jd = john_lennon.julian_day
        swe.set_ephe_path("")
        nut_data = swe.calc_ut(jd, swe.ECL_NUT, swe.FLG_SWIEPH)[0]
        true_obliquity = nut_data[0]

        for name in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            point = getattr(john_lennon, name)
            if point is not None and point.declination is not None:
                expected_oob = abs(point.declination) > true_obliquity
                assert point.is_out_of_bounds == expected_oob, (
                    f"{name}: is_out_of_bounds={point.is_out_of_bounds} but "
                    f"|dec|={abs(point.declination):.4f} vs obliquity={true_obliquity:.4f} "
                    f"=> expected {expected_oob}"
                )


class TestDeclinationAspects:
    def test_single_chart_declination_aspects(self, john_lennon):
        """Single chart declination aspects should return parallels/contra-parallels."""
        aspects = AspectsFactory.single_chart_declination_aspects(john_lennon, orb=1.5)
        assert isinstance(aspects, list)
        for aspect in aspects:
            assert aspect.aspect in ("parallel", "contra_parallel")
            assert aspect.orbit >= 0
            assert aspect.orbit <= 1.5

    def test_parallel_same_sign_declination(self, john_lennon):
        """Parallels should have declinations with similar absolute values and same sign."""
        aspects = AspectsFactory.single_chart_declination_aspects(john_lennon, orb=1.5)
        parallels = [a for a in aspects if a.aspect == "parallel"]
        for p in parallels:
            # Retrieve declinations from subject
            p1 = getattr(john_lennon, p.p1_name.lower(), None)
            p2 = getattr(john_lennon, p.p2_name.lower(), None)
            if p1 and p2 and p1.declination is not None and p2.declination is not None:
                diff = abs(p1.declination - p2.declination)
                assert diff <= 1.5 + 0.01  # Within orb + float tolerance

    def test_contra_parallel_opposite_declination(self, john_lennon):
        """Contra-parallels should have declinations with similar absolute values but opposite signs."""
        aspects = AspectsFactory.single_chart_declination_aspects(john_lennon, orb=1.5)
        contras = [a for a in aspects if a.aspect == "contra_parallel"]
        for cp in contras:
            p1 = getattr(john_lennon, cp.p1_name.lower(), None)
            p2 = getattr(john_lennon, cp.p2_name.lower(), None)
            if p1 and p2 and p1.declination is not None and p2.declination is not None:
                sum_dec = abs(p1.declination + p2.declination)
                assert sum_dec <= 1.5 + 0.01

    def test_dual_chart_declination_aspects(self, john_lennon, yoko_ono):
        """Dual chart declination aspects should work between two subjects."""
        aspects = AspectsFactory.dual_chart_declination_aspects(
            john_lennon, yoko_ono, orb=1.0
        )
        assert isinstance(aspects, list)
        for aspect in aspects:
            assert aspect.aspect in ("parallel", "contra_parallel")
            assert aspect.p1_owner == "John Lennon"
            assert aspect.p2_owner == "Yoko Ono"

    def test_stricter_orb_fewer_aspects(self, john_lennon):
        """Smaller orb should produce fewer or equal aspects."""
        wide = AspectsFactory.single_chart_declination_aspects(john_lennon, orb=2.0)
        narrow = AspectsFactory.single_chart_declination_aspects(john_lennon, orb=0.5)
        assert len(narrow) <= len(wide)

    def test_zero_orb_exact_only(self, john_lennon):
        """Zero orb should only return exact parallels (very few or none)."""
        aspects = AspectsFactory.single_chart_declination_aspects(john_lennon, orb=0.0)
        for a in aspects:
            assert a.orbit == 0.0

    def test_no_duplicate_pairs(self, john_lennon):
        """Each planet pair should appear at most once (no parallel AND contra-parallel)."""
        aspects = AspectsFactory.single_chart_declination_aspects(john_lennon, orb=2.0)
        seen_pairs = set()
        for a in aspects:
            pair = (a.p1_name, a.p2_name)
            assert pair not in seen_pairs, (
                f"Duplicate pair {pair}: both parallel and contra-parallel reported"
            )
            seen_pairs.add(pair)

    def test_parallel_same_sign(self, john_lennon):
        """Parallels should only occur between same-sign declinations."""
        aspects = AspectsFactory.single_chart_declination_aspects(john_lennon, orb=2.0)
        for a in aspects:
            if a.aspect == "parallel":
                p1 = getattr(john_lennon, a.p1_name.lower(), None)
                p2 = getattr(john_lennon, a.p2_name.lower(), None)
                if p1 and p2 and p1.declination is not None and p2.declination is not None:
                    assert (p1.declination >= 0) == (p2.declination >= 0), (
                        f"Parallel between {a.p1_name} (dec={p1.declination:.2f}) and "
                        f"{a.p2_name} (dec={p2.declination:.2f}) but signs differ"
                    )

    def test_contra_parallel_opposite_sign(self, john_lennon):
        """Contra-parallels should only occur between opposite-sign declinations."""
        aspects = AspectsFactory.single_chart_declination_aspects(john_lennon, orb=2.0)
        for a in aspects:
            if a.aspect == "contra_parallel":
                p1 = getattr(john_lennon, a.p1_name.lower(), None)
                p2 = getattr(john_lennon, a.p2_name.lower(), None)
                if p1 and p2 and p1.declination is not None and p2.declination is not None:
                    assert (p1.declination >= 0) != (p2.declination >= 0), (
                        f"Contra-parallel between {a.p1_name} (dec={p1.declination:.2f}) and "
                        f"{a.p2_name} (dec={p2.declination:.2f}) but signs are same"
                    )
