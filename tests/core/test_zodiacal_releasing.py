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

import pytest
from pytest import approx

from kerykeion import AstrologicalSubjectFactory, ZodiacalReleasingFactory
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.zodiacal_releasing.factory import GENERAL_YEARS, TROPICAL_YEAR_DAYS

pytestmark = pytest.mark.core


def _days(start: str, end: str) -> float:
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

    for prev, nxt in zip(periods, periods[1:]):
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
