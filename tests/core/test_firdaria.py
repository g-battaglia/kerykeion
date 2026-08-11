# -*- coding: utf-8 -*-
"""
Tests for firdaria (kerykeion.firdaria).

Structural invariants against the John Lennon reference chart: the opening
lord matches the chart's sect luminary, the 75-year cycle is contiguous and
repeats, planetary periods carry seven contiguous sub-periods opening with
their own lord, node periods carry none, and the current pointers track a
target date. A subject without a boolean sect is refused, never guessed.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from datetime import datetime
from types import SimpleNamespace

import pytest
from pytest import approx

from kerykeion import FirdariaFactory
from kerykeion.firdaria.factory import (
    DIURNAL_SEQUENCE,
    JULIAN_YEAR_DAYS,
    NOCTURNAL_SEQUENCE,
    NODES,
)
from kerykeion.schemas.exceptions import KerykeionException

pytestmark = pytest.mark.core

TARGET = "2024-06-15"


def _days(start: str, end: str) -> int:
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days


def test_opening_lord_matches_sect(john_lennon):
    firdaria = FirdariaFactory.from_subject(john_lennon, target_date=TARGET)
    assert firdaria.is_diurnal == john_lennon.is_diurnal
    expected_first = "Sun" if firdaria.is_diurnal else "Moon"
    assert firdaria.periods[0].lord == expected_first


def test_cycle_is_75_years_and_repeats(john_lennon):
    firdaria = FirdariaFactory.from_subject(john_lennon, target_date=TARGET)
    sequence = DIURNAL_SEQUENCE if firdaria.is_diurnal else NOCTURNAL_SEQUENCE
    lords = [lord for lord, _years in sequence]
    years = [entry_years for _lord, entry_years in sequence]
    assert sum(years) == 75

    # The output replays the sequence in order, cycling past 75 years.
    for index, period in enumerate(firdaria.periods):
        assert period.lord == lords[index % len(lords)]
        assert period.years == years[index % len(years)]

    # Ages are contiguous and the cap is honoured (last period may overhang).
    for prev, nxt in zip(firdaria.periods, firdaria.periods[1:]):
        assert prev.age_end == nxt.age_start
        assert prev.end == nxt.start
    assert firdaria.periods[0].age_start == 0
    assert firdaria.periods[-1].age_start < 120 <= firdaria.periods[-1].age_end + 75


def test_period_lengths_use_julian_years(john_lennon):
    firdaria = FirdariaFactory.from_subject(john_lennon, target_date=TARGET)
    for period in firdaria.periods[:9]:
        assert _days(period.start, period.end) == approx(period.years * JULIAN_YEAR_DAYS, abs=1)


def test_sub_periods_structure(john_lennon):
    firdaria = FirdariaFactory.from_subject(john_lennon, target_date=TARGET)
    for period in firdaria.periods[:9]:
        if period.lord in NODES:
            assert period.sub_periods == []
            continue
        subs = firdaria_subs = period.sub_periods
        assert len(subs) == 7
        # Opens with the period's own lord, contiguous, spans the period.
        assert subs[0].lord == period.lord
        for prev, nxt in zip(subs, subs[1:]):
            assert prev.end == nxt.start
        assert subs[0].start == period.start
        assert subs[-1].end == period.end
        # No node ever rules a sub-period.
        assert all(sub.lord not in NODES for sub in firdaria_subs)


def test_current_pointers_track_target(john_lennon):
    firdaria = FirdariaFactory.from_subject(john_lennon, target_date=TARGET)
    assert firdaria.current is not None
    assert firdaria.current.start <= TARGET < firdaria.current.end
    if firdaria.current.lord in NODES:
        assert firdaria.current_sub is None
    else:
        assert firdaria.current_sub is not None
        assert firdaria.current_sub.start <= TARGET < firdaria.current_sub.end


def test_unresolvable_sect_is_refused():
    composite_like = SimpleNamespace(is_diurnal=None, iso_formatted_local_datetime="1990-06-15T12:00:00")
    with pytest.raises(KerykeionException, match="sect"):
        FirdariaFactory.from_subject(composite_like)  # type: ignore[arg-type]


def test_invalid_target_raises(john_lennon):
    with pytest.raises(KerykeionException, match="Invalid target_date"):
        FirdariaFactory.from_subject(john_lennon, target_date="not-a-date")


# ---------------------------------------------------------------------------
# BCE support: JD-based arithmetic must build a timeline for deep-antiquity
# births the engine supports elsewhere. Synthetic subject: the factory only
# reads fields, so no ephemeris tier is required.
# ---------------------------------------------------------------------------

def test_bce_subject_builds_firdaria():
    subject = SimpleNamespace(
        year=-562, month=10, day=7, hour=6, minute=30, tz_str="UTC", is_diurnal=True
    )
    firdaria = FirdariaFactory.from_subject(subject, target_date="2024-06-15")  # type: ignore[arg-type]
    assert firdaria.periods[0].start == "-0562-10-07T06:30:00"
    assert firdaria.periods[0].lord == "Sun"
    # Contiguity holds across the era boundary too.
    for prev, nxt in zip(firdaria.periods, firdaria.periods[1:]):
        assert prev.end == nxt.start
    # The 2024 target falls far beyond the 120-year cap: no current period.
    assert firdaria.current is None


def test_bce_anchor_uses_the_julian_calendar():
    """The subject factory interprets year<1 components as Julian-calendar
    dates; the firdaria anchor must live on that same instant (the two
    calendars are six days apart at year -562)."""
    from kerykeion.ephemeris_backend import ephe
    from kerykeion.utilities import civil_jd, jd_to_iso_date, jd_to_iso_datetime

    bce_jd = civil_jd(-562, 10, 7, 6.5)
    assert bce_jd == approx(ephe.julday(-562, 10, 7, 6.5, ephe.JUL_CAL))
    assert jd_to_iso_date(bce_jd) == "-0562-10-07"
    assert jd_to_iso_datetime(bce_jd) == "-0562-10-07T06:30:00"
    # CE stays proleptic Gregorian, exactly as before.
    ce_jd = civil_jd(1940, 10, 9, 18.5)
    assert ce_jd == approx(ephe.julday(1940, 10, 9, 18.5, ephe.GREG_CAL))
    assert jd_to_iso_date(ce_jd) == "1940-10-09"


def test_bce_target_date_resolves_current():
    """Astronomical-year targets parse (datetime.fromisoformat cannot) and
    resolve against the Julian-calendar timeline: ten firdaria years are
    3652.5 days, half a day short of ten Julian-calendar years here."""
    subject = SimpleNamespace(
        year=-562, month=10, day=7, hour=6, minute=30, tz_str="UTC", is_diurnal=True
    )
    at_birth = FirdariaFactory.from_subject(subject, target_date="-0562-10-08")  # type: ignore[arg-type]
    assert at_birth.current is not None and at_birth.current.lord == "Sun"
    assert at_birth.current_sub is not None and at_birth.current_sub.lord == "Sun"
    # -0552-10-07 00:00 falls ~5.5 hours after the Sun period's end.
    next_period = FirdariaFactory.from_subject(subject, target_date="-0552-10-07")  # type: ignore[arg-type]
    assert next_period.current is not None and next_period.current.lord == "Venus"


def test_timezone_aware_target_refused(john_lennon):
    with pytest.raises(KerykeionException, match="timezone-naive"):
        FirdariaFactory.from_subject(john_lennon, target_date="2024-06-15T12:00:00+02:00")


def test_boundaries_carry_the_birth_time(john_lennon):
    """Boundaries fall at the birth time of day, not at midnight: a chart
    born at 18:30 flips its periods at 18:30 (± the .25-day steps of the
    365.25-day year), and the serialized timestamps must say so."""
    firdaria = FirdariaFactory.from_subject(john_lennon, target_date=TARGET)
    assert firdaria.periods[0].start.endswith("T18:30:00")
    # Each 365.25-day year shifts a boundary by 6 hours: Lennon's opening
    # Moon period (night chart, 9 years) ends 6 hours past the birth time.
    assert firdaria.periods[0].end.endswith("T00:30:00")


def test_serialized_boundary_agrees_with_selection(john_lennon):
    """Feeding a serialized boundary back as target_date must select the
    NEXT period (end-exclusive): the public timestamps and the current
    selection live on the same whole-second grid."""
    firdaria = FirdariaFactory.from_subject(john_lennon, target_date=TARGET)
    at_boundary = FirdariaFactory.from_subject(john_lennon, target_date=firdaria.periods[0].end)
    assert at_boundary.current == firdaria.periods[1]
    sub_boundary = firdaria.periods[0].sub_periods[0].end
    at_sub_boundary = FirdariaFactory.from_subject(john_lennon, target_date=sub_boundary)
    assert at_sub_boundary.current == firdaria.periods[0]
    assert at_sub_boundary.current_sub == firdaria.periods[0].sub_periods[1]
