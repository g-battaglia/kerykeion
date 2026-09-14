# -*- coding: utf-8 -*-
"""
Tests for the zodiacal releasing calculator (kerykeion.zodiacal_releasing).

Structural invariants are checked against the John Lennon reference chart
(Part of Fortune ~2° Capricorn, per the dominants anchor): the L1 sequence
starts at the lot's sign, periods are contiguous and last their general years,
angular/peak periods sit 1/4/7/10 from the lot, the loosing-of-the-bond jump
fires, and the current-path tracks a target date.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from datetime import datetime
from itertools import pairwise

import pytest
from pytest import approx

from kerykeion import ZodiacalReleasingFactory
from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.zodiacal_releasing.factory import GENERAL_YEARS, TROPICAL_YEAR_DAYS

pytestmark = pytest.mark.core


def _days(start: str, end: str) -> int:
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days


def test_fortune_lot_sign(john_lennon):
    """Lennon's Part of Fortune falls in Capricorn — the L1 release starts there."""
    zr = ZodiacalReleasingFactory.from_subject(john_lennon, lot="fortune")
    assert zr.lot == "fortune"
    assert zr.lot_sign == "Cap"
    assert zr.periods[0].sign == "Cap"


def test_l1_contiguous_and_correct_lengths(john_lennon):
    """L1 periods abut one another and last their sign's general years."""
    zr = ZodiacalReleasingFactory.from_subject(john_lennon, lot="fortune")
    periods = zr.periods
    assert len(periods) >= 2

    for prev, nxt in pairwise(periods):
        assert prev.end == nxt.start  # contiguous

    # First (non-truncated) period spans its general years.
    first = periods[0]
    assert _days(first.start, first.end) == approx(GENERAL_YEARS["Cap"] * TROPICAL_YEAR_DAYS, abs=2)


def test_angular_periods_are_pivots_from_lot(john_lennon):
    """Angular (peak) periods are 1st/4th/7th/10th from the lot sign."""
    zr = ZodiacalReleasingFactory.from_subject(john_lennon, lot="fortune")
    # Capricorn lot → angular signs are Cap, Ari, Can, Lib.
    angular_signs = {p.sign for p in zr.periods if p.is_angular}
    assert angular_signs <= {"Cap", "Ari", "Can", "Lib"}
    assert "Cap" in angular_signs


def test_current_path_tracks_target_date(john_lennon):
    """With a target date, the current path is reported from L1 down."""
    zr = ZodiacalReleasingFactory.from_subject(
        john_lennon, lot="fortune", levels=3, target_date="2000-01-01"
    )
    assert zr.current_path, "expected a non-empty current path"
    target = datetime(2000, 1, 1)

    # Each step in the path actually contains the target date and descends levels.
    for depth, period in enumerate(zr.current_path, start=1):
        assert period.level == depth
        assert datetime.fromisoformat(period.start) <= target < datetime.fromisoformat(period.end)


def test_loosing_of_the_bond_fires_in_subperiods(john_lennon):
    """A long L1 period is filled by L2 sub-periods that loose the bond."""
    zr = ZodiacalReleasingFactory.from_subject(john_lennon, lot="fortune", levels=2)
    # Aquarius (30y) is the longest period; its L2 chain must wrap and jump.
    flagged = any(
        sub.is_loosing_the_bond for period in zr.periods for sub in period.subperiods
    )
    assert flagged


def test_spirit_lot_differs(john_lennon):
    """The Spirit lot is the mirror of Fortune and generally starts elsewhere."""
    fortune = ZodiacalReleasingFactory.from_subject(john_lennon, lot="fortune")
    spirit = ZodiacalReleasingFactory.from_subject(john_lennon, lot="spirit")
    assert spirit.lot == "spirit"
    assert spirit.lot_sign != fortune.lot_sign


def test_spirit_release_peaks_are_fortune_relative(john_lennon):
    """Releasing from Spirit, peak (angular) periods still count from FORTUNE.

    Valens counts the 1st/4th/7th/10th places from the natal Lot of Fortune
    whichever lot is being released. Lennon is a night chart: Fortune ~2° Cap,
    Spirit ~6° Leo. Leo is angular from Spirit but NOT from Fortune, so a
    Spirit-relative implementation would flag the opening Leo period as a peak;
    the correct (Fortune-relative) flags mark Cap/Ari/Can/Lib instead.
    """
    zr = ZodiacalReleasingFactory.from_subject(john_lennon, lot="spirit", levels=2)
    assert zr.lot_sign == "Leo"
    assert zr.periods[0].sign == "Leo"

    fortune_angular = {"Cap", "Ari", "Can", "Lib"}  # 1/4/7/10 from Capricorn
    for period in zr.periods:
        assert period.is_angular == (period.sign in fortune_angular), (
            f"L1 {period.sign}: is_angular={period.is_angular} must follow Fortune (Cap), "
            "not the released lot (Leo)"
        )
        for sub in period.subperiods:
            assert sub.is_angular == (sub.sign in fortune_angular), (
                f"L2 {sub.sign}: is_angular={sub.is_angular} must follow Fortune (Cap)"
            )

    # The lot's own opening period is explicitly NOT a peak (it would be, were
    # angularity Spirit-relative), while the Fortune sign itself is.
    assert zr.periods[0].is_angular is False
    assert any(p.is_angular and p.sign == "Cap" for p in zr.periods)


def test_unknown_lot_raises(john_lennon):
    with pytest.raises(KerykeionException):
        ZodiacalReleasingFactory.from_subject(john_lennon, lot="ascendant")  # type: ignore[arg-type]


def test_levels_are_bounded_off_path(john_lennon):
    """L2 is built for every L1 period; L3 only along the target path."""
    zr = ZodiacalReleasingFactory.from_subject(
        john_lennon, lot="fortune", levels=3, target_date="2000-01-01"
    )
    # Every L1 period has L2 children.
    assert all(p.subperiods for p in zr.periods)

    # L3 exists only under the current path, not under every L2 period.
    current_l1 = zr.current_path[0]
    l2_with_children = [s for s in current_l1.subperiods if s.subperiods]
    assert l2_with_children, "current L1 should contain at least one L2 with L3 children"


def test_life_cap_is_honored(john_lennon):
    """A small life_cap_years bounds the L1 horizon (last period truncated)."""
    cap_years = 5
    zr = ZodiacalReleasingFactory.from_subject(
        john_lennon, lot="fortune", levels=1, life_cap_years=cap_years
    )
    total = _days(zr.periods[0].start, zr.periods[-1].end)
    assert total <= cap_years * TROPICAL_YEAR_DAYS + 1


def test_timezone_aware_target_raises(john_lennon):
    """A timezone-aware target_date is rejected with KerykeionException, not TypeError."""
    with pytest.raises(KerykeionException):
        ZodiacalReleasingFactory.from_subject(
            john_lennon, lot="fortune", target_date="2026-06-04T00:00:00+02:00"
        )


def test_current_path_is_internally_consistent(john_lennon):
    """Each step of the current path is a real child of the previous one."""
    zr = ZodiacalReleasingFactory.from_subject(
        john_lennon, lot="fortune", levels=3, target_date="2000-01-01"
    )
    for parent, child in pairwise(zr.current_path):
        assert child in parent.subperiods


def test_from_subject_accepts_return_and_davison_models():
    """PlanetReturnModel/CompositeSubjectModel lack the split year/month/day
    fields; from_subject used to crash with a raw AttributeError instead of
    using their ISO timestamp (a return or Davison chart is a real moment)."""
    from kerykeion import (
        AstrologicalSubjectFactory,
        CompositeSubjectFactory,
        PlanetaryReturnFactory,
    )
    from kerykeion.schemas import KerykeionException
    from kerykeion.zodiacal_releasing import ZodiacalReleasingFactory

    common = dict(
        lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
        online=False, suppress_geonames_warning=True,
    )
    natal = AstrologicalSubjectFactory.from_birth_data("N", 1990, 6, 15, 12, 0, **common)
    partner = AstrologicalSubjectFactory.from_birth_data("B", 1985, 3, 10, 4, 20, **common)

    solar_return = PlanetaryReturnFactory(
        natal, lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
    ).next_return_from_date(2025, 1, 1, return_type="Solar")
    assert ZodiacalReleasingFactory.from_subject(solar_return).periods

    davison = CompositeSubjectFactory(natal, partner).get_davison_composite_subject_model()
    assert ZodiacalReleasingFactory.from_subject(davison).periods

    midpoint = CompositeSubjectFactory(natal, partner).get_midpoint_composite_subject_model()
    with pytest.raises(KerykeionException, match="moment in time"):
        ZodiacalReleasingFactory.from_subject(midpoint)
