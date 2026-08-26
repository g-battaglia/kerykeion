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

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_backend import BACKEND_NAME
from kerykeion.planetary_returns import factory as factory_module
from kerykeion.planetary_returns.factory import PlanetaryReturnFactory
from kerykeion.schemas import KerykeionException
from kerykeion.utilities import datetime_to_julian

pytestmark = pytest.mark.skipif(
    BACKEND_NAME == "swisseph",
    reason="Backward return searches require the libephemeris backend (documented contract).",
)

# Upper bounds on the gap between consecutive returns of each kind, in days.
# Generous on purpose: the tests assert order and exactness, not cycle length.
MAX_GAP_DAYS = {
    "Solar": 367.0,
    "Lunar": 28.0,
    "Node": 16.0,  # the Moon meets either node every ~12.4-14.7 days (half a draconic month)
    "Mars": 800.0,  # heliocentric Mars, ~687 days
}

# Heliocentric planets whose solver tolerance is under a second of their own
# motion, with their sidereal periods rounded up, in days. The slow bodies
# (Uranus outward, Chiron) are pinned separately below: their crossings are
# settled by the factory itself. The lunar nodes and Liliths have no
# heliocentric longitude in the backend and are outside the contract.
HELIOCENTRIC_MAX_GAP_DAYS = {
    "Mercury": 100.0,
    "Venus": 240.0,
    "Mars": 800.0,
    "Jupiter": 4500.0,
    "Saturn": 11000.0,
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


@pytest.mark.parametrize("planet", sorted(HELIOCENTRIC_MAX_GAP_DAYS))
def test_every_solved_heliocentric_planet_steps_from_its_reported_instant(factory, planet):
    first = _step(factory, planet, START)
    second = _step(factory, planet, first.iso_formatted_utc_datetime)
    back = _step(factory, planet, second.iso_formatted_utc_datetime, backwards=True)

    gap = second.julian_day - first.julian_day
    assert 0 < gap < HELIOCENTRIC_MAX_GAP_DAYS[planet], f"{planet}: {gap:.2f} days"
    assert back.iso_formatted_utc_datetime == first.iso_formatted_utc_datetime


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

    Forward: ``T + 0.5s`` and ``T`` are the same second, so both step to the
    following return; ``T - 0.5s`` belongs to the second before, so the return
    reported at ``T`` is still ahead of it. Backward, mirrored: from ``T`` and
    from ``T + 0.5s`` the return reported at ``T`` is not before the seed, so
    the preceding return is found; from ``T + 1s`` it is, and it is found — a
    crossing a fraction of a second before the seed is not skipped.
    """
    first = factory.next_return_from_iso_formatted_time(START, "Solar")
    reported = first.iso_formatted_utc_datetime

    from_reported = factory.next_return_from_iso_formatted_time(reported, "Solar")
    from_half_after = factory.next_return_from_iso_formatted_time(_shift(reported, 0.5), "Solar")
    from_half_before = factory.next_return_from_iso_formatted_time(_shift(reported, -0.5), "Solar")

    assert from_half_after.iso_formatted_utc_datetime == from_reported.iso_formatted_utc_datetime
    assert from_half_before.iso_formatted_utc_datetime == reported

    back_from_reported = factory.next_return_from_iso_formatted_time(reported, "Solar", backwards=True)
    back_from_half_after = factory.next_return_from_iso_formatted_time(_shift(reported, 0.5), "Solar", backwards=True)
    back_from_next_second = factory.next_return_from_iso_formatted_time(_shift(reported, 1), "Solar", backwards=True)

    assert back_from_reported.julian_day < first.julian_day
    assert back_from_half_after.iso_formatted_utc_datetime == back_from_reported.iso_formatted_utc_datetime
    assert back_from_next_second.iso_formatted_utc_datetime == reported


@pytest.mark.parametrize("kind", ["Lunar", "Node", *sorted(HELIOCENTRIC_MAX_GAP_DAYS)])
def test_a_crossing_a_fraction_before_the_seed_is_found_backward(factory, kind):
    """Every kind, every solved heliocentric planet: ``previous`` from the
    second after a reported instant finds that very return, not the one a
    whole cycle earlier. (The old seed, one second earlier still, passed the
    forward/backward walk yet failed exactly this.)"""
    first = _step(factory, kind, START)
    back = _step(factory, kind, _shift(first.iso_formatted_utc_datetime, 1), backwards=True)
    assert back.iso_formatted_utc_datetime == first.iso_formatted_utc_datetime


@pytest.mark.parametrize(
    "start",
    [
        # The first three are solar returns whose exact crossing falls in the
        # last ~90 ms of its reported second — inside the backend's at-crossing
        # dead band, where a backward search from the next second used to jump
        # a whole year. The fourth is a control from outside the band.
        "1984-03-01T00:00:00+00:00",  # 52 ms before the next second
        "2004-03-01T00:00:00+00:00",  # 76 ms
        "2021-03-01T00:00:00+00:00",  # 6 ms
        "2024-03-01T00:00:00+00:00",  # a control from outside the band
    ],
)
def test_a_solar_return_in_the_dead_band_is_still_found_backward(factory, start):
    first = _step(factory, "Solar", start)
    back = _step(factory, "Solar", _shift(first.iso_formatted_utc_datetime, 1), backwards=True)
    assert back.iso_formatted_utc_datetime == first.iso_formatted_utc_datetime


def test_twenty_consecutive_solar_returns_are_found_from_the_second_after(factory):
    """The dead band catches ~9% of solar returns at random; a run of twenty
    consecutive ones leaves no room for luck."""
    # From 1986: the 1985 return's crossing sits 15 µs before a whole second,
    # under the ephemeris' own resolution — indistinguishable from a crossing
    # at that second, and treated as one (see _crossing_between).
    current = _step(factory, "Solar", "1986-01-01T00:00:00+00:00")
    for _ in range(20):
        back = _step(factory, "Solar", _shift(current.iso_formatted_utc_datetime, 1), backwards=True)
        assert back.iso_formatted_utc_datetime == current.iso_formatted_utc_datetime
        current = _step(factory, "Solar", current.iso_formatted_utc_datetime)


# The slow heliocentric bodies: the solver's 0.001″ tolerance is seconds of
# their motion, so a seed one second past a crossing used to be handed back
# as its own answer (the same crossing reported a second later). Settled to a
# millisecond and held to the ordering contract, they step like the rest.
SLOW_HELIOCENTRIC_MAX_GAP_DAYS = {
    "Uranus": 31000.0,
    "Neptune": 61000.0,
    "Pluto": 92000.0,
    "Chiron": 19000.0,
}


@pytest.mark.parametrize("planet", sorted(SLOW_HELIOCENTRIC_MAX_GAP_DAYS))
def test_slow_heliocentric_bodies_step_and_come_back(factory, planet):
    first = _step(factory, planet, START)
    second = _step(factory, planet, first.iso_formatted_utc_datetime)
    back = _step(factory, planet, second.iso_formatted_utc_datetime, backwards=True)
    from_next_second = _step(factory, planet, _shift(first.iso_formatted_utc_datetime, 1), backwards=True)

    gap = second.julian_day - first.julian_day
    assert 1.0 < gap < SLOW_HELIOCENTRIC_MAX_GAP_DAYS[planet], f"{planet}: {gap:.2f} days"
    assert back.iso_formatted_utc_datetime == first.iso_formatted_utc_datetime
    assert from_next_second.iso_formatted_utc_datetime == first.iso_formatted_utc_datetime


def test_crossing_between_finds_a_sign_change_to_a_millisecond():
    root = 2460000.123456
    crossing = PlanetaryReturnFactory._crossing_between(lambda jd: jd - root, root - 1.0, root + 1.0)
    assert crossing is not None and abs(crossing - root) * 86400.0 < 1e-3

    assert PlanetaryReturnFactory._crossing_between(lambda jd: jd - root, root + 1.0, root + 2.0) is None
    assert PlanetaryReturnFactory._crossing_between(lambda jd: jd - root, root, root + 1.0) == root
    # A decreasing offset (the Moon's latitude at a descending node) is a sign change too.
    falling = PlanetaryReturnFactory._crossing_between(lambda jd: root - jd, root - 1.0, root + 1.0)
    assert falling is not None and abs(falling - root) * 86400.0 < 1e-3

    # A root AT the window's end is not inside it: the natal instant is a
    # crossing by construction, and a backward seed on it must not be told
    # there is a return a millisecond before itself.
    assert PlanetaryReturnFactory._crossing_between(lambda jd: jd - root, root - 1.0, root) is None
    almost = root - 0.05e-3 / 86400.0  # 50 µs before the seed: below the resolution, at the seed
    assert PlanetaryReturnFactory._crossing_between(lambda jd: jd - almost, root - 1.0, root) is None
    near = root - 0.3e-3 / 86400.0  # 300 µs before the seed: a crossing before it
    found = PlanetaryReturnFactory._crossing_between(lambda jd: jd - near, root - 1.0, root)
    assert found is not None and abs(found - near) * 86400.0 < 0.2e-3

    # A signed arc flips sign at the antipode too; that is an opposition, not a
    # crossing. A slow sweep through 180°: +179.9° at one end, -179.9° at the other.
    def arc_through_the_antipode(jd: float) -> float:
        return PlanetaryReturnFactory._signed_arc(180.0 + (jd - root) * 0.1, 0.0)

    assert PlanetaryReturnFactory._crossing_between(arc_through_the_antipode, root - 1.0, root + 1.0) is None


def test_previous_from_the_natal_instant_is_the_return_before_birth():
    """The natal instant is a crossing by construction (every body sits at its
    natal position). Seeded with it, ``previous`` must find the cycle before
    birth — never a return a second before the birth itself."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Natal Seed",
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
    factory = PlanetaryReturnFactory(
        subject, city="Montichiari", nation="IT", lat=45.41, lng=10.39, tz_str="Europe/Rome", online=False
    )
    natal = subject.iso_formatted_utc_datetime

    for kind, min_gap_days in (("Solar", 300.0), ("Lunar", 20.0), ("Jupiter", 4000.0)):
        before = _step(factory, kind, natal, backwards=True)
        gap = subject.julian_day - before.julian_day
        assert gap > min_gap_days, (
            f"{kind}: previous from the natal instant returned {before.iso_formatted_utc_datetime}"
        )


def test_a_seed_just_past_an_opposition_does_not_return_the_opposition(factory):
    """A backward seed one second after the Sun opposed the natal Sun: the
    signed arc flips sign in that second, at the antipode. The answer is the
    previous solar return, not the opposition."""
    natal_sun = factory.subject.sun.abs_pos
    opposition_jd = factory_module.ephe.solcross_ut(
        (natal_sun + 180.0) % 360.0, datetime_to_julian(datetime(2024, 3, 1, tzinfo=timezone.utc))
    )
    opposition = factory_module.julian_to_datetime(opposition_jd).replace(tzinfo=timezone.utc, microsecond=0)
    seed = (opposition + timedelta(seconds=1)).isoformat()

    before = factory.next_return_from_iso_formatted_time(seed, "Solar", backwards=True)
    arc = PlanetaryReturnFactory._signed_arc(before.sun.abs_pos, natal_sun)
    assert abs(arc) < 0.01, f"the 'return' sits {arc:.3f} degrees from the natal Sun"
    assert before.julian_day < opposition_jd - 1.0


def test_date_and_iso_entry_points_agree_away_from_the_boundary(factory):
    """Away from a date's first second, the date wrapper and an ISO midnight
    seed select the same return."""
    by_date = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
    by_iso = factory.next_return_from_iso_formatted_time("2024-01-01T00:00:00+00:00", "Solar")
    assert by_date.iso_formatted_utc_datetime == by_iso.iso_formatted_utc_datetime
    assert by_date.iso_formatted_utc_datetime.startswith("2024-06-")


def test_date_wrapper_keeps_its_midnight_seed_inclusive(factory):
    """``next_return_from_date`` promises the first return ON OR AFTER the date:
    its seed is midnight itself, not the second after it. Only the ISO entry
    point snaps its seed past its own second (a reported instant must step)."""
    midnight = datetime(2024, 1, 1, tzinfo=timezone.utc)
    original = factory_module.ephe.solcross_ut

    with patch.object(factory_module.ephe, "solcross_ut", wraps=original) as spy:
        factory.next_return_from_date(2024, 1, 1, return_type="Solar")
        assert spy.call_args.args[1] == datetime_to_julian(midnight)

    with patch.object(factory_module.ephe, "solcross_ut", wraps=original) as spy:
        factory.next_return_from_iso_formatted_time(midnight.isoformat(), "Solar")
        assert spy.call_args.args[1] == datetime_to_julian(midnight + timedelta(seconds=1))


def test_a_return_in_the_first_second_of_a_date_belongs_to_that_date():
    """Born at 00:00:00 UTC, the natal Sun sits exactly where the year's crossing
    is found: a return in the first second of that date. The date wrapper keeps
    it; the ISO entry point, seeded with that same instant, steps a year on."""
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Midnight",
        1990,
        6,
        15,
        0,
        0,
        seconds=0,
        lat=51.5,
        lng=0.0,
        tz_str="UTC",
        online=False,
        suppress_geonames_warning=True,
    )
    factory = PlanetaryReturnFactory(
        subject, city="Greenwich", nation="GB", lat=51.5, lng=0.0, tz_str="UTC", online=False
    )

    by_date = factory.next_return_from_date(1990, 6, 15, return_type="Solar")
    assert abs(by_date.julian_day - subject.julian_day) * 86400 < 1.5, by_date.iso_formatted_utc_datetime

    by_iso = factory.next_return_from_iso_formatted_time("1990-06-15T00:00:00+00:00", "Solar")
    assert by_iso.iso_formatted_utc_datetime.startswith("1991-06-")


def test_seed_is_normalized_to_utc_before_it_is_stepped():
    """The civil range is a range of instants: a local wall time at its edge
    whose UTC instant is well inside it must seed normally, and an aware
    timestamp whose UTC instant is already past the edge must refuse."""
    seed = PlanetaryReturnFactory._search_start_jd

    forward_edge = seed("9999-12-31T23:59:59+14:00", backwards=False)
    assert forward_edge == datetime_to_julian(datetime(9999, 12, 31, 10, 0, 0, tzinfo=timezone.utc))

    backward_edge = seed("0001-01-01T00:00:00-14:00", backwards=True)
    assert backward_edge == datetime_to_julian(datetime(1, 1, 1, 14, 0, 0, tzinfo=timezone.utc))

    with pytest.raises(KerykeionException, match="civil range"):
        seed("9999-12-31T23:59:59-14:00", backwards=False)  # already year 10000 in UTC
    with pytest.raises(KerykeionException, match="civil range"):
        seed("0001-01-01T00:00:00+14:00", backwards=True)  # already year 0 in UTC


def test_search_refuses_to_start_outside_the_civil_range(factory):
    with pytest.raises(KerykeionException, match="civil range"):
        factory.next_return_from_iso_formatted_time("9999-12-31T23:59:59+00:00", "Solar")
    # The first second of 1 CE is a valid backward seed; the search itself then
    # runs out of the civil range and refuses through the library's exception.
    with pytest.raises(KerykeionException, match=r"1 CE|civil range|range"):
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
