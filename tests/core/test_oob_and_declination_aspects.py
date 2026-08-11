# -*- coding: utf-8 -*-
"""Tests for Out-of-Bounds detection and declination aspects (parallels/contra-parallels)."""

import pytest
from kerykeion.ephemeris_backend import ephe
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
        """Sun declination must match ephe.calc_ut with FLG_EQUATORIAL within 0.001 deg."""
        jd = john_lennon.julian_day
        ephe.set_ephe_path("")
        sun_eq = ephe.calc_ut(jd, ephe.SUN, ephe.FLG_SWIEPH | ephe.FLG_EQUATORIAL)[0]
        expected_dec = sun_eq[1]
        assert abs(john_lennon.sun.declination - expected_dec) < 0.001, (
            f"Sun declination {john_lennon.sun.declination} != "
            f"ephe reference {expected_dec}"
        )

    def test_moon_declination_matches_swe_reference(self, john_lennon):
        """Moon declination must match ephe.calc_ut with FLG_EQUATORIAL within 0.001 deg."""
        jd = john_lennon.julian_day
        ephe.set_ephe_path("")
        moon_eq = ephe.calc_ut(jd, ephe.MOON, ephe.FLG_SWIEPH | ephe.FLG_EQUATORIAL)[0]
        expected_dec = moon_eq[1]
        assert abs(john_lennon.moon.declination - expected_dec) < 0.001, (
            f"Moon declination {john_lennon.moon.declination} != "
            f"ephe reference {expected_dec}"
        )

    def test_oob_flag_consistent_with_obliquity(self, john_lennon):
        """is_out_of_bounds must equal abs(declination) > true obliquity from ephe."""
        jd = john_lennon.julian_day
        ephe.set_ephe_path("")
        nut_data = ephe.calc_ut(jd, ephe.ECL_NUT, ephe.FLG_SWIEPH)[0]
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
            assert aspect.aspect in ("parallel", "contra-parallel")
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
        contras = [a for a in aspects if a.aspect == "contra-parallel"]
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
            assert aspect.aspect in ("parallel", "contra-parallel")
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

    @pytest.mark.parametrize(
        "invalid_orb",
        [float("nan"), float("inf"), float("-inf"), -1.0],
    )
    def test_invalid_orb_rejected(self, john_lennon, yoko_ono, invalid_orb):
        from kerykeion.schemas import KerykeionException

        with pytest.raises(KerykeionException, match="orb"):
            AspectsFactory.single_chart_declination_aspects(john_lennon, orb=invalid_orb)
        with pytest.raises(KerykeionException, match="orb"):
            AspectsFactory.dual_chart_declination_aspects(
                john_lennon,
                yoko_ono,
                orb=invalid_orb,
            )

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
            if a.aspect == "contra-parallel":
                p1 = getattr(john_lennon, a.p1_name.lower(), None)
                p2 = getattr(john_lennon, a.p2_name.lower(), None)
                if p1 and p2 and p1.declination is not None and p2.declination is not None:
                    assert (p1.declination >= 0) != (p2.declination >= 0), (
                        f"Contra-parallel between {a.p1_name} (dec={p1.declination:.2f}) and "
                        f"{a.p2_name} (dec={p2.declination:.2f}) but signs are same"
                    )


class TestDeclinationArtifactFiltering:
    """Geometric opposite pairs and star-star pairs are skipped in declination aspects.

    Derived opposite points (node axes, Lilith/Priapus, ...) carry exactly
    mirrored declinations by construction, so without filtering they would
    report a permanent 0.0-orb contra-parallel in every chart.
    """

    @pytest.fixture(scope="class")
    def all_points_subject(self):
        from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

        return AstrologicalSubjectFactory.from_birth_data(
            "All Points Declination", 1990, 6, 15, 12, 0,
            lng=12.5, lat=41.9, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            active_points=ALL_ACTIVE_POINTS,
        )

    def test_derived_pair_declinations_are_mirrored(self, all_points_subject):
        """Guard against vacuous passes: Lilith/Priapus declinations mirror exactly."""
        lilith = all_points_subject.mean_lilith
        priapus = all_points_subject.mean_priapus
        assert lilith.declination is not None and priapus.declination is not None
        assert lilith.declination == pytest.approx(-priapus.declination, abs=1e-9)

    def test_no_contra_parallel_for_derived_pairs(self, all_points_subject):
        """No parallel/contra-parallel between a derived point and its primary."""
        from kerykeion.astrological_subject_factory import OPPOSITE_PAIRS

        aspects = AspectsFactory.single_chart_declination_aspects(all_points_subject, orb=5.0)
        for derived, config in OPPOSITE_PAIRS.items():
            pair = {derived, config["primary"]}
            offenders = [a for a in aspects if {a.p1_name, a.p2_name} == pair]
            assert offenders == [], (
                f"Artifact declination aspect for locked pair {pair}: "
                f"{[(a.aspect, a.orbit) for a in offenders]}"
            )

    def test_cross_chart_opposite_name_pairs_are_kept(self, all_points_subject):
        """The opposite-pair skip is same-chart only.

        In synastry/transits the two charts' points are independent — one
        chart's Ascendant parallel the other's Descendant (or node axes,
        Lilith/Priapus across charts) is a real aspect, exactly as in the
        longitudinal dual path.
        """
        from kerykeion.aspects.factory import GEOMETRIC_OPPOSITE_PAIRS

        other = AstrologicalSubjectFactory.from_birth_data(
            "Other Declination", 1985, 3, 10, 14, 30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            active_points=list(all_points_subject.active_points),
        )
        # Wide orb so geometry cannot make this vacuous: with 90° every
        # |dec_a ± dec_b| qualifies, so each locked pair MUST appear unless
        # it is being (wrongly) skipped cross-chart.
        aspects = AspectsFactory.dual_chart_declination_aspects(all_points_subject, other, orb=90.0)
        found_pairs = {frozenset((a.p1_name, a.p2_name)) for a in aspects}
        missing = [
            pair for pair in GEOMETRIC_OPPOSITE_PAIRS
            if all(
                getattr(all_points_subject, name.lower(), None) is not None
                and getattr(all_points_subject, name.lower()).declination is not None
                for name in pair
            )
            and pair not in found_pairs
        ]
        assert missing == [], f"Cross-chart opposite-name pairs wrongly skipped: {missing}"

    def test_no_star_star_declination_aspects(self):
        """Star-star parallels are constants across charts — skipped."""
        from kerykeion.settings.config_constants import DEFAULT_FIXED_STARS

        subject = AstrologicalSubjectFactory.from_birth_data(
            "Stars Declination", 1990, 6, 15, 12, 0,
            lng=12.5, lat=41.9, tz_str="Europe/Rome",
            city="Rome", nation="IT", online=False,
            active_fixed_stars=list(DEFAULT_FIXED_STARS),
        )
        stars = {star.name for star in subject.fixed_stars}
        assert stars, "Sanity check: subject should carry calculated fixed stars"
        aspects = AspectsFactory.single_chart_declination_aspects(subject, orb=1.0)
        star_star = [a for a in aspects if a.p1_name in stars and a.p2_name in stars]
        assert star_star == [], (
            f"Unexpected star-star declination aspects: {[(a.p1_name, a.p2_name) for a in star_star]}"
        )
