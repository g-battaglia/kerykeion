# -*- coding: utf-8 -*-
"""The lunar phase name is a window centred on the event it names.

Before this, the name came from the 1-28 lunation day: bin 1 was [0°, 12.857°),
so "New Moon" began AT the conjunction and covered only the twelve and a half
degrees after it, "Full Moon" was bin 14 = [167.143°, 180°) and ENDED at the
opposition, and the quarters were three bins each, offset the same way. A minute
after an exact full moon a chart therefore read "Waning Gibbous" beside an
illumination of 100%.

The windows are now centred on the four events and each is as wide as it was:
half a bin either side of the syzygies, one and a half bins either side of the
quarters. What this file pins:

    1. the eight windows, checked one thousandth of a degree either side of
       every one of their eight boundaries;
    2. that the name and the emoji do not move across an exact syzygy, taken a
       minute before and a minute after a real one;
    3. that a subject and the moon-phase endpoint answer with the same
       ``phase_name``, ``major_phase`` and ``stage`` for the same instant —
       they read one definition now, and this is what says so;
    4. that the lunation day 1-28 is EXACTLY what it was: it is the "Lunation
       Day" the charts, the reports and the XML context print, and the fix must
       not have touched it.
"""

from __future__ import annotations

import pytest

from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory
from kerykeion.moon_phase_details.factory import MoonPhaseDetailsFactory
from kerykeion.utilities import (
    calculate_moon_phase,
    lunar_major_phase_from_degrees,
    lunar_phase_name_from_degrees,
    lunar_stage_from_degrees,
)


# Greenwich: neutral location, UTC, no DST ambiguity.
_LAT = 51.4769
_LNG = 0.0
_TZ = "UTC"

#: A hair, in degrees. The Moon covers roughly 0.0082° relative to the Sun in a
#: minute, so a thousandth of a degree is well inside the resolution the windows
#: are meant to have and still an unambiguous side of a boundary.
_EPS = 0.001


def _subject(year: int, month: int, day: int, hour: int, minute: int, second: int = 0):
    return AstrologicalSubjectFactory.from_birth_data(
        "Lunar phase probe",
        year,
        month,
        day,
        hour,
        minute,
        lat=_LAT,
        lng=_LNG,
        tz_str=_TZ,
        city="Greenwich",
        nation="GB",
        seconds=second,
        geonames_username=None,
    )


# ---------------------------------------------------------------------------
# 1. The eight windows
# ---------------------------------------------------------------------------

#: Every boundary, with the name owed to a thousandth of a degree below it and a
#: thousandth above. Read down the column and the eight windows are complete.
_WINDOW_BOUNDARIES = [
    # boundary°, name below, name above
    (6.428571, "New Moon", "Waxing Crescent"),
    (70.714286, "Waxing Crescent", "First Quarter"),
    (109.285714, "First Quarter", "Waxing Gibbous"),
    (173.571429, "Waxing Gibbous", "Full Moon"),
    (186.428571, "Full Moon", "Waning Gibbous"),
    (250.714286, "Waning Gibbous", "Last Quarter"),
    (289.285714, "Last Quarter", "Waning Crescent"),
    (353.571429, "Waning Crescent", "New Moon"),
]

_EMOJI_OF = {
    "New Moon": "🌑",
    "Waxing Crescent": "🌒",
    "First Quarter": "🌓",
    "Waxing Gibbous": "🌔",
    "Full Moon": "🌕",
    "Waning Gibbous": "🌖",
    "Last Quarter": "🌗",
    "Waning Crescent": "🌘",
}


@pytest.mark.parametrize(
    "boundary,name_below,name_above",
    _WINDOW_BOUNDARIES,
    ids=[f"{b:.3f}" for b, _, _ in _WINDOW_BOUNDARIES],
)
def test_window_boundaries(boundary: float, name_below: str, name_above: str) -> None:
    """Each boundary separates exactly the two names it is meant to separate."""
    below = lunar_phase_name_from_degrees(boundary - _EPS)
    above = lunar_phase_name_from_degrees(boundary + _EPS)

    assert below == (name_below, _EMOJI_OF[name_below]), f"{boundary - _EPS:.6f}° gave {below}"
    assert above == (name_above, _EMOJI_OF[name_above]), f"{boundary + _EPS:.6f}° gave {above}"


@pytest.mark.parametrize(
    "degrees,expected",
    [
        (0.0, "New Moon"),
        (359.999, "New Moon"),  # the New Moon window straddles 0°
        (90.0, "First Quarter"),
        (180.0, "Full Moon"),
        (270.0, "Last Quarter"),
        (45.0, "Waxing Crescent"),
        (135.0, "Waxing Gibbous"),
        (225.0, "Waning Gibbous"),
        (315.0, "Waning Crescent"),
        # The separation the downstream API pins as Waning Crescent: it must
        # stay one, which is why the quarter windows were not widened to 45°.
        (290.649, "Waning Crescent"),
    ],
)
def test_names_inside_the_windows(degrees: float, expected: str) -> None:
    """The four events, the four midpoints, and the wrap across 0°."""
    name, emoji = lunar_phase_name_from_degrees(degrees)
    assert name == expected
    assert emoji == _EMOJI_OF[expected]


def test_name_is_modulo_360() -> None:
    """A separation outside [0, 360) is reduced, not rejected."""
    assert lunar_phase_name_from_degrees(360.0) == lunar_phase_name_from_degrees(0.0)
    assert lunar_phase_name_from_degrees(-1.0) == lunar_phase_name_from_degrees(359.0)
    assert lunar_phase_name_from_degrees(720.0 + 180.0) == lunar_phase_name_from_degrees(180.0)


def test_windows_cover_the_whole_circle_without_a_gap() -> None:
    """Sampled at a hundredth of a degree, the eight names tile 0-360 in order.

    A window that overlapped its neighbour, or left a gap, would show up here as
    a name appearing twice in the sequence of transitions.
    """
    seen_order = []
    step = 0.01
    angle = 0.0
    while angle < 360.0:
        name, _ = lunar_phase_name_from_degrees(angle)
        if not seen_order or seen_order[-1] != name:
            seen_order.append(name)
        angle += step

    # Starts inside the New Moon window (which straddles 0°) and comes back to it.
    assert seen_order == [
        "New Moon",
        "Waxing Crescent",
        "First Quarter",
        "Waxing Gibbous",
        "Full Moon",
        "Waning Gibbous",
        "Last Quarter",
        "Waning Crescent",
        "New Moon",
    ]


# ---------------------------------------------------------------------------
# 2. A minute either side of an exact syzygy
# ---------------------------------------------------------------------------

#: Full moon of 2026-08-28, 04:18:32 UTC (LunationFinderFactory).
_FULL_MOON_2026 = (2026, 8, 28, 4, 18, 32)


@pytest.mark.parametrize("offset_minutes", [-1, 0, 1])
def test_name_holds_across_an_exact_full_moon(offset_minutes: int) -> None:
    """A minute before, at, and a minute after: still a Full Moon, still 🌕.

    This is the failure the whole change is about. A minute after the exact
    opposition the separation is 180.008°, which the 28-bin lookup put in bin 15
    and named "Waning Gibbous" — beside an illumination the continuous formula
    was still printing as 100%.
    """
    year, month, day, hour, minute, second = _FULL_MOON_2026
    subject = _subject(year, month, day, hour, minute + offset_minutes, second)
    lunar = subject.lunar_phase
    assert lunar is not None

    assert lunar.moon_phase_name == "Full Moon", (
        f"{offset_minutes:+d} min from the exact full moon: name '{lunar.moon_phase_name}' "
        f"at {lunar.degrees_between_s_m:.6f}°"
    )
    assert lunar.moon_emoji == "🌕"
    assert lunar.major_phase == "Full Moon"


def test_lunation_day_still_turns_over_at_the_opposition() -> None:
    """The name holds across the syzygy; the lunation day is still a counter.

    The two answer different questions and the fix kept it that way: bin 14 ends
    at 180°, so the day rolls to 15 the moment the opposition is past.
    """
    year, month, day, hour, minute, second = _FULL_MOON_2026
    before = _subject(year, month, day, hour, minute - 1, second).lunar_phase
    after = _subject(year, month, day, hour, minute + 1, second).lunar_phase
    assert before is not None and after is not None

    assert before.moon_phase == 14
    assert after.moon_phase == 15
    assert before.moon_phase_name == after.moon_phase_name == "Full Moon"


def test_stage_turns_over_at_the_opposition() -> None:
    """Waxing up to the opposition, waning after it — the name spans both."""
    year, month, day, hour, minute, second = _FULL_MOON_2026
    before = _subject(year, month, day, hour, minute - 1, second).lunar_phase
    after = _subject(year, month, day, hour, minute + 1, second).lunar_phase
    assert before is not None and after is not None

    assert before.stage == "waxing"
    assert after.stage == "waning"


# ---------------------------------------------------------------------------
# 3. A subject and the moon-phase endpoint agree
# ---------------------------------------------------------------------------

#: One instant per major phase plus two ordinary days, all 2026, UTC.
_PARITY_MOMENTS = [
    (2026, 1, 18, 19, 52),  # new moon
    (2026, 8, 28, 4, 18),  # full moon
    (2026, 8, 20, 2, 46),  # first quarter
    (2026, 3, 11, 9, 39),  # last quarter
    (2026, 5, 2, 12, 0),  # nothing in particular
    (2026, 11, 7, 21, 30),  # nothing in particular
]


@pytest.mark.parametrize(
    "y,m,d,h,mi",
    _PARITY_MOMENTS,
    ids=[f"{y}-{m:02d}-{d:02d}T{h:02d}:{mi:02d}" for y, m, d, h, mi in _PARITY_MOMENTS],
)
def test_subject_and_overview_agree(y: int, m: int, d: int, h: int, mi: int) -> None:
    """One definition of the windows, the major phase and the stage — so the
    subject's ``lunar_phase`` and the moon-phase overview cannot disagree."""
    subject = _subject(y, m, d, h, mi)
    lunar = subject.lunar_phase
    assert lunar is not None

    overview = MoonPhaseDetailsFactory.from_subject(subject)
    assert overview.moon is not None

    assert overview.moon.phase_name == lunar.moon_phase_name
    assert overview.moon.emoji == lunar.moon_emoji
    assert overview.moon.major_phase == lunar.major_phase
    assert overview.moon.stage == lunar.stage


@pytest.mark.parametrize(
    "degrees,expected_major,expected_stage",
    [
        (0.0, "New Moon", "waxing"),
        (44.0, "New Moon", "waxing"),
        (46.0, "First Quarter", "waxing"),
        (90.0, "First Quarter", "waxing"),
        (135.0, "First Quarter", "waxing"),  # equidistant: the earlier one wins
        (180.0, "Full Moon", "waning"),
        (225.0, "Full Moon", "waning"),  # equidistant: the earlier one wins
        (270.0, "Last Quarter", "waning"),
        (315.0, "New Moon", "waning"),  # equidistant: the earlier one wins
        (359.9, "New Moon", "waning"),
    ],
)
def test_major_phase_and_stage_from_degrees(degrees: float, expected_major: str, expected_stage: str) -> None:
    """The major phase is always one of the four, whatever the eight-name says."""
    assert lunar_major_phase_from_degrees(degrees) == expected_major
    assert lunar_stage_from_degrees(degrees) == expected_stage

    lunar = calculate_moon_phase(degrees, 0.0)
    assert lunar.major_phase == expected_major
    assert lunar.stage == expected_stage


# ---------------------------------------------------------------------------
# 4. The lunation day 1-28 is untouched
# ---------------------------------------------------------------------------

#: Separation → lunation day, as the 1/28th binning has always answered. These
#: are the values printed as "Lunation Day" on charts, in reports and in the XML
#: context; the name windows moved and these must not have.
_LUNATION_DAYS = [
    (0.0, 1),
    (6.0, 1),
    (12.9, 2),
    (45.0, 4),
    (90.0, 7),
    (96.43, 8),
    (120.0, 10),
    (173.57, 14),
    (180.0, 14),
    (200.0, 16),
    (250.0, 20),
    (263.57, 21),
    (270.0, 21),
    (300.0, 24),
    (353.6, 28),
    (359.99, 28),
]


@pytest.mark.parametrize(
    "degrees,expected_day",
    _LUNATION_DAYS,
    ids=[f"{d}" for d, _ in _LUNATION_DAYS],
)
def test_lunation_day_is_unchanged(degrees: float, expected_day: int) -> None:
    assert calculate_moon_phase(degrees, 0.0).moon_phase == expected_day


def test_lunation_day_stays_in_range_all_around_the_circle() -> None:
    """Sampled at a hundredth of a degree, the day is always 1-28 and monotonic."""
    previous = 0
    angle = 0.0
    while angle < 360.0:
        day = calculate_moon_phase(angle, 0.0).moon_phase
        assert 1 <= day <= 28, f"{angle:.2f}° gave lunation day {day}"
        assert day >= previous, f"{angle:.2f}° went backwards: {previous} → {day}"
        previous = day
        angle += 0.01
