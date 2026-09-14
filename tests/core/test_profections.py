# -*- coding: utf-8 -*-
"""
Tests for annual profections (kerykeion.profections).

Structural invariants against the John Lennon reference chart (born
1940-10-09): ages advance one house per year cycling every 12, the sign is the
one on the profected cusp, the Lord of the Year is the sign's traditional
ruler, and year boundaries fall on birthday anniversaries.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import pytest

from kerykeion import ProfectionsFactory
from kerykeion.dignities import get_domicile_ruler
from kerykeion.profections.factory import HOUSE_CUSP_FIELDS
from kerykeion.schemas.exceptions import KerykeionException

pytestmark = pytest.mark.core

TARGET = "2024-06-15"  # Lennon's age on this date: 83 (birthday not yet reached)


def test_current_year_age_and_house(john_lennon):
    profections = ProfectionsFactory.from_subject(john_lennon, target_date=TARGET)
    assert profections.current.age == 83
    assert profections.current.house == (83 % 12) + 1  # 12th house


def test_age_rolls_on_the_birthday(john_lennon):
    before = ProfectionsFactory.from_subject(john_lennon, target_date="2024-10-08")
    on_day = ProfectionsFactory.from_subject(john_lennon, target_date="2024-10-09")
    assert before.current.age == 83
    assert on_day.current.age == 84
    assert on_day.current.house == (before.current.house % 12) + 1


def test_sign_comes_from_the_profected_cusp(john_lennon):
    profections = ProfectionsFactory.from_subject(john_lennon, target_date=TARGET)
    for entry in profections.years:
        cusp = getattr(john_lennon, HOUSE_CUSP_FIELDS[entry.house - 1])
        assert entry.sign == cusp.sign
        assert entry.lord == get_domicile_ruler(entry.sign)


def test_window_and_boundaries(john_lennon):
    profections = ProfectionsFactory.from_subject(john_lennon, target_date=TARGET)
    ages = [entry.age for entry in profections.years]
    assert ages == list(range(80, 88))  # default window: 3 before, 4 after
    for entry in profections.years:
        assert entry.year_start == f"{1940 + entry.age}-10-09"
        assert entry.year_end == f"{1941 + entry.age}-10-09"
    # Consecutive years abut.
    for prev, nxt in zip(profections.years, profections.years[1:]):
        assert prev.year_end == nxt.year_start


def test_twelve_year_cycle(john_lennon):
    """Ages 12 years apart profect the same house."""
    a = ProfectionsFactory.from_subject(john_lennon, target_date="1953-01-01")  # age 12
    b = ProfectionsFactory.from_subject(john_lennon, target_date="1941-01-01")  # age 0
    assert a.current.house == b.current.house == 1


def test_target_before_birth_raises(john_lennon):
    with pytest.raises(KerykeionException, match="precedes the birth date"):
        ProfectionsFactory.from_subject(john_lennon, target_date="1939-01-01")


def test_invalid_target_raises(john_lennon):
    with pytest.raises(KerykeionException, match="Invalid target_date"):
        ProfectionsFactory.from_subject(john_lennon, target_date="not-a-date")


# ---------------------------------------------------------------------------
# BCE support: the engine renders deep-antiquity charts, so the time-lord
# techniques must too. All date arithmetic is calendar-integer/JD based —
# Python's date/datetime year-1 floor must never be hit. The subjects are
# synthetic (the factories only read fields), so the tests run on any
# ephemeris tier.
# ---------------------------------------------------------------------------

def _bce_subject():
    from types import SimpleNamespace

    signs = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
    fields = {
        name: SimpleNamespace(sign=signs[i])
        for i, name in enumerate(HOUSE_CUSP_FIELDS)
    }
    return SimpleNamespace(
        year=-562, month=10, day=7, hour=6, minute=30, tz_str="UTC", is_diurnal=True, **fields
    )


def test_bce_subject_builds_profections():
    profections = ProfectionsFactory.from_subject(_bce_subject(), target_date="2024-06-15")
    # Age spans the whole era gap (astronomical years: -562 -> 2024, birthday
    # Oct 7 not yet reached on June 15).
    assert profections.current.age == 2024 - (-562) - 1
    assert 1 <= profections.current.house <= 12
    # Boundaries keep the birthday and 4-digit CE years.
    assert profections.current.year_start == "2023-10-07"
    assert profections.current.year_end == "2024-10-07"


def test_bce_target_in_antiquity():
    profections = ProfectionsFactory.from_subject(_bce_subject(), target_date="0001-01-01")
    assert profections.current.age == 1 - (-562) - 1  # birthday Oct 7 not yet reached
    # A window straddling year zero formats negative years astronomically.
    starts = [entry.year_start for entry in profections.years]
    assert any(value.startswith("-") or value.startswith("0000") for value in starts)


def test_bce_target_date_parses():
    """Astronomical-year targets parse — the factory itself emits such
    boundaries, so it must also accept them to resolve `current`."""
    profections = ProfectionsFactory.from_subject(_bce_subject(), target_date="-0550-10-07")
    # The twelfth birthday: the profection wheel returns to the 1st house.
    assert profections.current.age == 12
    assert profections.current.house == 1
    assert profections.current.year_start == "-0550-10-07"


def test_bce_leap_anniversary_uses_the_julian_rule():
    """BCE dates are Julian-calendar in the engine's convention, where every
    fourth astronomical year — century years included — is leap. A Feb-29
    birthday therefore keeps its day in year -100; the Gregorian century
    rule only applies from 1 CE on."""
    from kerykeion.profections.factory import _anniversary

    assert _anniversary(-100, 2, 29) == (2, 29)  # Julian leap century year
    assert _anniversary(1900, 2, 29) == (3, 1)  # Gregorian common century year
    assert _anniversary(2000, 2, 29) == (2, 29)  # Gregorian leap year
