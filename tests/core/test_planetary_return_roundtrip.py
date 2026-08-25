"""
Round-trip tests for PlanetaryReturnFactory: reported instants as seeds.

Return instants are reported truncated to the whole second. A caller walking
the sequence of returns re-feeds the instant it was given as the seed of the
next search — the exact crossing sits a fraction of a second AFTER that seed,
so a raw forward search found the same return again. These tests pin the
contract that fixes it: ordering between a seed and a return is decided at the
library's reporting resolution, so for every supported kind

    next(reported(N))     == N + 1
    previous(reported(N)) == N - 1
    previous(next(r))     == r        (an exact involution on the walk)

and a walk of steps lands on each return exactly once, in order. The mirror
image of ``test_planetary_return_backwards.py::test_back_is_one_cycle_earlier``,
which only ever seeded the direction the truncation happened to favour.

Two calendar facts are pinned alongside, because they are why a return is
identified by its instant and never by a year or a month: a leap year can hold
two solar returns, and a month can hold two lunar returns.

Backward search requires the libephemeris backend; the module skips on
pyswisseph, like the backwards suite.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_backend import BACKEND_NAME
from kerykeion.planetary_returns.factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException

pytestmark = pytest.mark.skipif(
    BACKEND_NAME == "swisseph",
    reason="Backward return searches require the libephemeris backend (documented contract).",
)

# Upper bounds on the gap between consecutive returns of each kind, in days.
# Generous on purpose: the tests assert order and exactness, not cycle length.
MAX_GAP_DAYS = {
    "Solar": 367.0,
    "Lunar": 28.0,
    "Node": 15.0,  # the Moon meets either node every half draconic month
    "Mars": 800.0,  # heliocentric Mars, ~687 days
}


@pytest.fixture(scope="module")
def factory():
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Round Trip",
        1985,
        6,
        10,
        12,
        23,
        lat=45.41,
        lng=10.39,
        tz_str="Europe/Rome",
        online=False,
        suppress_geonames_warning=True,
    )
    return PlanetaryReturnFactory(
        subject,
        city="Montichiari",
        nation="IT",
        lat=45.41,
        lng=10.39,
        tz_str="Europe/Rome",
        online=False,
    )


def _step(factory: PlanetaryReturnFactory, kind: str, seed_iso: str, backwards: bool = False):
    """One search of the given kind from an ISO seed — the four entry points behind one door."""
    if kind in ("Solar", "Lunar"):
        return factory.next_return_from_iso_formatted_time(seed_iso, kind, backwards=backwards)
    if kind == "Node":
        return factory.next_lunar_node_crossing_from_iso_formatted_time(seed_iso, backwards=backwards)
    return factory.next_heliocentric_return_from_iso_formatted_time(kind, seed_iso, backwards=backwards)


def _shift(iso: str, seconds: float) -> str:
    return (datetime.fromisoformat(iso) + timedelta(seconds=seconds)).isoformat()


KINDS = ["Solar", "Lunar", "Node", "Mars"]
START = "2024-03-01T00:00:00+00:00"


@pytest.mark.parametrize("kind", KINDS)
def test_next_from_reported_instant_is_the_following_return(factory, kind):
    first = _step(factory, kind, START)
    second = _step(factory, kind, first.iso_formatted_utc_datetime)

    gap = second.julian_day - first.julian_day
    assert gap > 0, f"{kind}: seeding from the reported instant found the same return again"
    assert gap < MAX_GAP_DAYS[kind], f"{kind}: a return was skipped ({gap:.2f} days)"


@pytest.mark.parametrize("kind", KINDS)
def test_previous_from_reported_instant_is_the_preceding_return(factory, kind):
    first = _step(factory, kind, START)
    before = _step(factory, kind, first.iso_formatted_utc_datetime, backwards=True)

    gap = first.julian_day - before.julian_day
    assert gap > 0, f"{kind}: seeding backward from the reported instant found the same return again"
    assert gap < MAX_GAP_DAYS[kind], f"{kind}: a return was skipped ({gap:.2f} days)"


@pytest.mark.parametrize("kind", KINDS)
def test_previous_of_next_is_an_exact_involution(factory, kind):
    first = _step(factory, kind, START)
    forward = _step(factory, kind, first.iso_formatted_utc_datetime)
    back = _step(factory, kind, forward.iso_formatted_utc_datetime, backwards=True)

    assert back.iso_formatted_utc_datetime == first.iso_formatted_utc_datetime
    assert back.julian_day == first.julian_day


@pytest.mark.parametrize("kind", ["Solar", "Lunar", "Node"])
def test_a_walk_visits_each_return_once_and_comes_back(factory, kind):
    steps = 5
    origin = _step(factory, kind, START)

    outbound = [origin]
    for _ in range(steps):
        outbound.append(_step(factory, kind, outbound[-1].iso_formatted_utc_datetime))

    instants = [r.iso_formatted_utc_datetime for r in outbound]
    assert len(set(instants)) == len(instants), f"{kind}: a step stood still: {instants}"
    assert [r.julian_day for r in outbound] == sorted(r.julian_day for r in outbound)

    current = outbound[-1]
    for expected in reversed(outbound[:-1]):
        current = _step(factory, kind, current.iso_formatted_utc_datetime, backwards=True)
        assert current.iso_formatted_utc_datetime == expected.iso_formatted_utc_datetime

    assert current.iso_formatted_utc_datetime == origin.iso_formatted_utc_datetime


def test_sub_second_seeds_are_ordered_at_reporting_resolution(factory):
    """A seed inside the same whole second as a reported instant means that instant.

    ``T + 0.5s`` and ``T`` are the same second, so both step to the following
    return; ``T - 0.5s`` belongs to the second before, so the return reported
    at ``T`` is still ahead of it.
    """
    first = factory.next_return_from_iso_formatted_time(START, "Solar")
    reported = first.iso_formatted_utc_datetime

    from_reported = factory.next_return_from_iso_formatted_time(reported, "Solar")
    from_half_after = factory.next_return_from_iso_formatted_time(_shift(reported, 0.5), "Solar")
    from_half_before = factory.next_return_from_iso_formatted_time(_shift(reported, -0.5), "Solar")

    assert from_half_after.iso_formatted_utc_datetime == from_reported.iso_formatted_utc_datetime
    assert from_half_before.iso_formatted_utc_datetime == reported


def test_date_and_year_entry_points_are_unchanged(factory):
    """Whole-second seeds already start the search where they did: the first
    return after midnight of a date is never inside that midnight second."""
    by_date = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
    by_iso = factory.next_return_from_iso_formatted_time("2024-01-01T00:00:00+00:00", "Solar")
    assert by_date.iso_formatted_utc_datetime == by_iso.iso_formatted_utc_datetime
    assert by_date.iso_formatted_utc_datetime.startswith("2024-06-")


def test_search_refuses_to_start_outside_the_civil_range(factory):
    with pytest.raises(KerykeionException, match="civil range"):
        factory.next_return_from_iso_formatted_time("9999-12-31T23:59:59+00:00", "Solar")
    with pytest.raises(KerykeionException, match="civil range"):
        factory.next_return_from_iso_formatted_time("0001-01-01T00:00:00+00:00", "Solar", backwards=True)


# ---------------------------------------------------------------------------
# Why a return is identified by its instant, never by a calendar period
# ---------------------------------------------------------------------------


def _walk(factory: PlanetaryReturnFactory, kind: str, seed_iso: str, count: int) -> list[str]:
    instants = [_step(factory, kind, seed_iso).iso_formatted_utc_datetime]
    while len(instants) < count:
        instants.append(_step(factory, kind, instants[-1]).iso_formatted_utc_datetime)
    return instants


def test_a_leap_year_can_hold_two_solar_returns():
    """Born on 1 January: the 2024 return falls on 1 January and the next on
    31 December of the same year. Stepping by "the return of year Y" would
    never reach the second one."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "New Year",
        1985,
        1,
        1,
        2,
        0,
        lat=51.5,
        lng=0.0,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )
    factory = PlanetaryReturnFactory(
        subject,
        city="London",
        nation="GB",
        lat=51.5,
        lng=0.0,
        tz_str="Europe/London",
        online=False,
    )
    years = [datetime.fromisoformat(i).year for i in _walk(factory, "Solar", "2023-01-01T00:00:00+00:00", 5)]
    assert years == [2023, 2024, 2024, 2026, 2027]


def test_a_month_can_hold_two_lunar_returns(factory):
    months = [i[:7] for i in _walk(factory, "Lunar", "2026-01-01T00:00:00+00:00", 10)]
    assert months.count("2026-08") == 2, months
