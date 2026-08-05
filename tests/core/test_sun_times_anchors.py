"""Sunrise, sunset and solar noon against two national observatories.

*** NO REGENERATION SCRIPT WRITES THIS FILE. ***

Every expected value below was transcribed by hand from a published service on
the capture date recorded in `_CAPTURED`. Nothing in this repository can rewrite
them, and that is the point: the golden report snapshots next door encode what
this library produced, which is *constancy*; these encode what two independent
observatories say the sky did, which is *truth*. A blind regeneration can bless a
wrong number in the first class and cannot touch the second. If an anchor turns
red, the fix is a new capture with a new date — never an edit to make the number
match the code.

Sources, both public, both national institutions, both queried for the same UTC
civil day so no timezone handling of ours sits between us and them:

  * United States Naval Observatory, Astronomical Applications Department
    https://aa.usno.navy.mil/api/rstt/oneday   (API version 4.0.1)
  * Institut de mecanique celeste et de calcul des ephemerides (IMCCE),
    Observatoire de Paris
    https://ssp.imcce.fr/webservices/miriade/api/rts.php

Why two, and why the tolerances are shaped the way they are
-----------------------------------------------------------
Because they disagree with each other, and the size of that disagreement is the
real floor on how tightly anyone can be anchored. Over this grid the two agree on
sunrise and on transit, but IMCCE's sunset runs about two minutes earlier than
USNO's throughout — a horizon-convention difference, not an error by either.
Wellington reverses it: there IMCCE and this library agree while USNO sits 82 s
away. Publishing to the whole minute adds another +/-30 s on top.

So the file makes two claims of different strengths rather than one dishonest one:

  * a TIGHT claim on the two quantities the sources agree on — sunrise and
    solar noon must land within `_USNO_TOL_S` of USNO;
  * an ENVELOPE claim on all three — our value must lie inside the span the two
    observatories bracket, padded by `_ENVELOPE_PAD_S` for their rounding.

Above `_ANCHOR_MAX_ABS_LAT` no time-domain claim is made at all. That is not
squeamishness, it is conditioning: near the poles the Sun grazes the horizon, so
`dh/dt` collapses and a milliarcsecond of altitude becomes minutes of clock. The
two sources demonstrate it themselves — at Tromso (69.6 N) they differ by 10 and
11 minutes on the same two events they agree on everywhere else, and
`test_the_cut_off_latitude_is_earned` asserts exactly that rather than taking it
on trust. Those latitudes are covered instead by
`test_sun_times_altitude_invariant.py`, which measures an angle and stays well
conditioned everywhere.
"""

from __future__ import annotations

import datetime as dt

import pytest

from kerykeion import SunTimesFactory

#: Capture date of every reference value in this module. Bump it only together
#: with a fresh capture from both services.
_CAPTURED = "2026-08-05"

#: Sunrise and solar noon must land this close to USNO. The residuals measured
#: at capture time span -28.7 s to +31.3 s, which is USNO's own published
#: accuracy (about a minute) plus its rounding to the whole minute; 45 s leaves
#: roughly 1.4x headroom over the worst observed case without ever admitting a
#: real defect, the smallest of which in this area is tens of seconds.
_USNO_TOL_S = 45.0

#: Padding on the two-source envelope, for the fact that both publish whole
#: minutes (so each printed value is up to 30 s from its own true instant) plus
#: a little slack. Sunset needs the envelope rather than a single-source
#: tolerance because the two sources genuinely disagree there.
_ENVELOPE_PAD_S = 60.0

#: Above this latitude a time-domain anchor measures conditioning, not accuracy.
_ANCHOR_MAX_ABS_LAT = 60.0

#: (rise, transit, set) as published, UTC, HH:MM.
_REFERENCE = {
    "quito_equinox": dict(
        lat=-0.1807, lon=-78.4678, date=(2026, 3, 20),
        usno=("11:18", "17:21", "23:24"), imcce=("11:18", "17:21", "23:23"),
        why="equator, equinox: fastest declination change",
    ),
    "nairobi_january": dict(
        lat=-1.2921, lon=36.8219, date=(2026, 1, 15),
        usno=("03:36", "09:42", "15:48"), imcce=("03:37", "09:42", "15:46"),
        why="just south of the equator, northern winter",
    ),
    "singapore_august": dict(
        lat=1.3521, lon=103.8198, date=(2026, 8, 5),
        usno=("23:06", "05:11", "11:16"), imcce=("23:06", "05:10", "11:14"),
        why="near-equatorial, and the rise straddles the UTC day boundary",
    ),
    "rome_equinox": dict(
        lat=41.9028, lon=12.4964, date=(2026, 3, 20),
        usno=("05:14", "11:17", "17:22"), imcce=("05:14", "11:17", "17:20"),
        why="mid-north at the equinox: where a midpoint solar noon drifts most",
    ),
    "rome_solstice": dict(
        lat=41.9028, lon=12.4964, date=(2026, 6, 21),
        usno=("03:35", "11:12", "18:49"), imcce=("03:36", "11:11", "18:47"),
        why="the same place at the solstice, where the declination is stationary",
    ),
    "london_august": dict(
        lat=51.5074, lon=-0.1278, date=(2026, 8, 5),
        usno=("04:30", "12:07", "19:42"), imcce=("04:31", "12:06", "19:40"),
        why="the case this investigation started from",
    ),
    "newyork_december": dict(
        lat=40.7128, lon=-74.006, date=(2026, 12, 21),
        usno=("12:17", "16:54", "21:32"), imcce=("12:17", "16:54", "21:30"),
        why="mid-north, winter solstice, western hemisphere",
    ),
    "tokyo_june": dict(
        lat=35.6762, lon=139.6503, date=(2026, 6, 15),
        usno=("19:25", "02:42", "09:59"), imcce=("19:26", "02:41", "09:57"),
        why="far-east longitude: transit lands early in the UTC day",
    ),
    "sydney_solstice": dict(
        lat=-33.8688, lon=151.2093, date=(2026, 12, 21),
        usno=("18:41", "01:53", "09:05"), imcce=("18:42", "01:53", "09:04"),
        why="mid-south, austral summer solstice",
    ),
    "capetown_may": dict(
        lat=-33.9249, lon=18.4241, date=(2026, 5, 10),
        usno=("05:28", "10:43", "15:57"), imcce=("05:28", "10:42", "15:56"),
        why="mid-south, austral autumn",
    ),
    "santiago_september": dict(
        lat=-33.4489, lon=-70.6693, date=(2026, 9, 22),
        usno=("10:32", "16:35", "22:39"), imcce=("10:33", "16:35", "22:38"),
        why="mid-south at the equinox",
    ),
    "buenosaires_march": dict(
        lat=-34.6037, lon=-58.3816, date=(2026, 3, 20),
        usno=("09:57", "16:01", "22:05"), imcce=("09:57", "16:00", "22:03"),
        why="mid-south equinox, western hemisphere",
    ),
    "madrid_november": dict(
        lat=40.4168, lon=-3.7038, date=(2026, 11, 1),
        usno=("06:44", "11:58", "17:12"), imcce=("06:45", "11:58", "17:10"),
        why="well west of the meridian its civil time follows",
    ),
    "urumqi_february": dict(
        lat=43.8256, lon=87.6168, date=(2026, 2, 10),
        usno=("01:16", "06:24", "11:32"), imcce=("01:17", "06:23", "11:30"),
        why="the extreme case of a single national timezone: solar noon near 14:00 local",
    ),
    "stockholm_october": dict(
        lat=59.3293, lon=18.0686, date=(2026, 10, 15),
        usno=("05:25", "10:34", "15:41"), imcce=("05:27", "10:33", "15:38"),
        why="just under the cut-off, where the sources start to spread",
    ),
    "ushuaia_july": dict(
        lat=-54.8019, lon=-68.303, date=(2026, 7, 1),
        usno=("12:58", "16:37", "20:16"), imcce=("13:00", "16:37", "20:14"),
        why="the far south in austral winter, a short day at high latitude",
    ),
    "wellington_april": dict(
        lat=-41.2866, lon=174.7756, date=(2026, 4, 20),
        usno=("18:57", "00:20", "05:43"), imcce=("18:58", "00:19", "05:41"),
        why="date-line side; and the one case where USNO, not IMCCE, is the outlier",
    ),
    # Above the cut-off. Kept in the table on purpose: they are what
    # `test_the_cut_off_latitude_is_earned` measures.
    "reykjavik_april": dict(
        lat=64.1466, lon=-21.9426, date=(2026, 4, 15),
        usno=("05:56", "13:28", "21:01"), imcce=("05:58", "13:27", "20:59"),
        why="above the cut-off: the altitude invariant covers it instead",
    ),
    "tromso_may": dict(
        lat=69.6492, lon=18.9553, date=(2026, 5, 15),
        usno=("23:32", "10:41", "21:48"), imcce=("23:42", "10:40", "21:37"),
        why="above the cut-off, and the proof that the cut-off is needed",
    ),
}

_EVENTS = ("rise", "transit", "set")


def _published_instant(reference_hhmm: str, ours: dt.datetime) -> dt.datetime:
    """The published HH:MM placed on the same UTC day as our own instant.

    Anchored to `ours` rather than to the requested date because an event can
    legitimately fall on either side of midnight UTC (Singapore, Tokyo,
    Wellington all do). The caller unwraps the result onto the nearest day.
    """
    hour, minute = (int(part) for part in reference_hhmm.split(":"))
    return ours.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _signed_delta_seconds(ours: dt.datetime, reference_hhmm: str) -> float:
    """``ours - published`` in seconds, unwrapped to the nearest day.

    Without the unwrap a 23:5x event compared against a 00:0x publication would
    read as a 24-hour error instead of a few seconds.
    """
    delta = (ours - _published_instant(reference_hhmm, ours)).total_seconds()
    if delta > 43200.0:
        delta -= 86400.0
    if delta < -43200.0:
        delta += 86400.0
    return delta


def _our_events(case: dict) -> dict[str, dt.datetime | None]:
    year, month, day = case["date"]
    model = SunTimesFactory.from_date(
        year, month, day, latitude=case["lat"], longitude=case["lon"], tz_str="UTC"
    )
    return {"rise": model.sunrise, "transit": model.solar_noon, "set": model.sunset}


_ANCHORED = [name for name, case in _REFERENCE.items() if abs(case["lat"]) <= _ANCHOR_MAX_ABS_LAT]
_ABOVE_CUT_OFF = [name for name in _REFERENCE if name not in _ANCHORED]


def test_the_grid_actually_has_cases_on_both_sides_of_the_cut_off():
    """Guards every case below: an empty list would make them all vacuous.

    The whole file is parametrised off `_REFERENCE`, so a bad edit that emptied
    or mis-filtered it would turn a suite of anchors into a suite of no-ops that
    still reports green — the exact failure mode anchors exist to prevent.
    """
    assert len(_ANCHORED) >= 15, f"only {len(_ANCHORED)} anchored cases"
    assert len(_ABOVE_CUT_OFF) >= 2, f"only {len(_ABOVE_CUT_OFF)} cases above the cut-off"
    assert {case["lat"] for case in _REFERENCE.values()}, "no latitudes at all"
    # Both hemispheres and a real spread, or "global coverage" is a story.
    latitudes = [case["lat"] for case in _REFERENCE.values()]
    assert min(latitudes) < -30.0 and max(latitudes) > 60.0


@pytest.mark.parametrize("name", _ANCHORED)
def test_sunrise_and_solar_noon_match_the_naval_observatory(name):
    """The tight claim, on the two quantities the two sources agree about."""
    case = _REFERENCE[name]
    ours = _our_events(case)

    failures: list[str] = []
    for event in ("rise", "transit"):
        moment = ours[event]
        if moment is None:
            failures.append(f"{event}: we produced nothing")
            continue
        published = case["usno"][_EVENTS.index(event)]
        delta = _signed_delta_seconds(moment, published)
        if abs(delta) > _USNO_TOL_S:
            failures.append(
                f"{event}: ours {moment:%H:%M:%S} vs published {published} "
                f"-> {delta:+.1f} s (limit {_USNO_TOL_S:.0f} s)"
            )

    assert not failures, (
        f"{name} ({case['why']}) diverged from the reference captured {_CAPTURED}:\n  "
        + "\n  ".join(failures)
        + "\n\nDo NOT edit the constants to match. Re-capture from the source and "
          "record the new date, or find what moved."
    )


@pytest.mark.parametrize("name", _ANCHORED)
def test_every_event_lies_inside_the_span_of_the_two_observatories(name):
    """The envelope claim, including sunset, where the sources disagree.

    Stated as "inside the band the two of them bracket" rather than "close to
    one of them", because with a two-minute convention gap between the sources
    picking a favourite would be asserting a preference, not a measurement.
    """
    case = _REFERENCE[name]
    ours = _our_events(case)

    failures: list[str] = []
    for index, event in enumerate(_EVENTS):
        moment = ours[event]
        if moment is None:
            failures.append(f"{event}: we produced nothing")
            continue
        deltas = [_signed_delta_seconds(moment, case[src][index]) for src in ("usno", "imcce")]
        low, high = min(deltas), max(deltas)
        # Inside the bracket means our value is not beyond BOTH sources on the
        # same side by more than the padding.
        if low > _ENVELOPE_PAD_S or high < -_ENVELOPE_PAD_S:
            failures.append(
                f"{event}: ours {moment:%H:%M:%S}, published {case['usno'][index]} and "
                f"{case['imcce'][index]} -> {deltas[0]:+.1f} s / {deltas[1]:+.1f} s, "
                f"outside the bracket by more than {_ENVELOPE_PAD_S:.0f} s"
            )

    assert not failures, (
        f"{name} ({case['why']}) fell outside the two-source span captured {_CAPTURED}:\n  "
        + "\n  ".join(failures)
    )


def test_the_cut_off_latitude_is_earned():
    """The reason there is no time-domain anchor above 60 degrees, measured.

    A cut-off chosen for convenience is a way of hiding failures. This one is a
    statement about conditioning, so it has to be demonstrable: the same two
    services that agree to a minute at mid-latitudes must be seen to fall apart
    above the cut-off, on their own, with this library taking no part in it.
    """
    spreads: dict[str, float] = {}
    for name, case in _REFERENCE.items():
        worst = 0.0
        for index in range(len(_EVENTS)):
            usno_hour, usno_minute = (int(p) for p in case["usno"][index].split(":"))
            imcce_hour, imcce_minute = (int(p) for p in case["imcce"][index].split(":"))
            gap = (imcce_hour * 60 + imcce_minute) - (usno_hour * 60 + usno_minute)
            gap = (gap + 720) % 1440 - 720
            worst = max(worst, abs(gap) * 60.0)
        spreads[name] = worst

    below = [spreads[name] for name in _ANCHORED]
    assert max(below) <= 3 * 60.0, (
        "below the cut-off the two sources are expected to stay within a few minutes "
        f"of each other; worst was {max(below) / 60.0:.0f} min"
    )

    tromso = spreads["tromso_may"]
    assert tromso >= 10 * 60.0, (
        "the cut-off is justified by the sources diverging above it; at Tromso they "
        f"differ by only {tromso / 60.0:.0f} min, so the cut-off may no longer be needed"
    )


@pytest.mark.parametrize("name", _ABOVE_CUT_OFF)
def test_above_the_cut_off_we_still_produce_something_sane(name):
    """No time-domain claim up here, but silence would hide a real breakage.

    Ordering and presence only: the numbers themselves are adjudicated by the
    altitude invariant, which does not degrade with latitude.
    """
    case = _REFERENCE[name]
    ours = _our_events(case)
    assert ours["transit"] is not None, "the Sun culminates every day, even a polar one"
    if ours["rise"] is not None and ours["set"] is not None:
        assert ours["set"] > ours["rise"], "a paired sunset must follow its sunrise"
