"""
Regression tests for compute_lunar_phase_jd search directions.

The normalized Sun-Moon angular difference is a sawtooth with a ±180° wrap
once per synodic month. A plain bisection over a 30-day window could converge
on the wrap (returning the *opposite* phase — every backward search did this)
or collapse onto a window edge (a rarer forward failure when the wrap split
the bracket). These tests pin the bracketing-based implementation with the
real ephemeris, both through angular properties and independent almanac dates.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from kerykeion.moon_phase_details.utils import (
    compute_lunar_phase_jd,
    configure_ephemeris_path,
)
import swisseph as ephe
from kerykeion.utilities import datetime_to_julian

# Spacing of consecutive same-phase instants. New-moon-to-new-moon spans
# 29.26-29.80 days (AstroPixels), but quarter-to-quarter intervals swing a
# little wider with the lunar anomaly, so the property bound is looser.
_SYNODIC_MIN = 29.0
_SYNODIC_MAX = 30.0

# ~9 s of Moon-Sun relative motion; the bisection tolerance is 1 s.
_ANGLE_TOL = 0.0015

_PHASE_TARGETS = (0.0, 90.0, 180.0, 270.0)

# Spread across the synodic cycle and across years/seasons.
_REFERENCE_DATES = (
    datetime(1993, 10, 10, 12, 12, tzinfo=timezone.utc),
    datetime(2020, 3, 20, 3, 49, tzinfo=timezone.utc),
    datetime(2024, 10, 27, 0, 30, tzinfo=timezone.utc),
    datetime(2026, 1, 13, 12, 0, tzinfo=timezone.utc),
    datetime(2031, 7, 1, 23, 59, tzinfo=timezone.utc),
)


def _phase_angle(jd: float) -> float:
    """Compute the geocentric Sun–Moon separation at a Julian day."""
    configure_ephemeris_path()
    iflag = ephe.FLG_SWIEPH
    sun = ephe.calc_ut(jd, ephe.SUN, iflag)[0]
    moon = ephe.calc_ut(jd, ephe.MOON, iflag)[0]
    return (float(moon[0]) - float(sun[0])) % 360.0


def _angle_error(jd: float, target: float) -> float:
    """Return the smallest angular distance from the requested phase."""
    return abs((_phase_angle(jd) - target + 180.0) % 360.0 - 180.0)


@pytest.mark.parametrize("reference", _REFERENCE_DATES, ids=lambda d: d.strftime("%Y-%m-%d"))
@pytest.mark.parametrize("target", _PHASE_TARGETS, ids=("NM", "FQ", "FM", "LQ"))
def test_backward_and_forward_bracket_the_reference(reference: datetime, target: float) -> None:
    """Find genuine adjacent phases on either side of the reference instant."""
    jd_ref = datetime_to_julian(reference)

    last = compute_lunar_phase_jd(jd_ref, target, forward=False)
    nxt = compute_lunar_phase_jd(jd_ref, target, forward=True)

    assert last is not None and nxt is not None

    # Direction semantics: most recent at/before vs first after.
    assert last <= jd_ref + 1e-9
    assert nxt >= jd_ref - 1e-9

    # Both instants are genuine occurrences of the requested phase — the
    # pre-fix backward search returned the opposite phase (error ≈ 180°).
    assert _angle_error(last, target) < _ANGLE_TOL
    assert _angle_error(nxt, target) < _ANGLE_TOL

    # Consecutive same-phase instants are one synodic month apart.
    assert _SYNODIC_MIN < (nxt - last) < _SYNODIC_MAX


# US Naval Observatory, Universal Time, rounded to the nearest minute:
# https://aa.usno.navy.mil/api/moon/phases/date?date=1993-09-01&nump=12
# https://aa.usno.navy.mil/api/moon/phases/date?date=2024-05-01&nump=12
# https://aa.usno.navy.mil/api/moon/phases/date?date=2026-09-01&nump=12
_ALMANAC_WINDOWS = (
    (
        "1993-10-10T11:12:00+00:00",
        (
            (0, "1993-09-16T03:10", "1993-10-15T11:36"),
            (90, "1993-09-22T19:32", "1993-10-22T08:52"),
            (180, "1993-09-30T18:54", "1993-10-30T12:38"),
            (270, "1993-10-08T19:35", "1993-11-07T06:36"),
        ),
    ),
    (
        "2024-06-01T12:30:00+00:00",
        (
            (0, "2024-05-08T03:22", "2024-06-06T12:38"),
            (90, "2024-05-15T11:48", "2024-06-14T05:18"),
            (180, "2024-05-23T13:53", "2024-06-22T01:08"),
            (270, "2024-05-30T17:13", "2024-06-28T21:53"),
        ),
    ),
    (
        "2026-09-29T18:51:02+00:00",
        (
            (0, "2026-09-11T03:27", "2026-10-10T15:50"),
            (90, "2026-09-18T20:44", "2026-10-18T16:12"),
            (180, "2026-09-26T16:49", "2026-10-26T04:12"),
            (270, "2026-09-04T07:51", "2026-10-03T13:25"),
        ),
    ),
)


@pytest.mark.parametrize("reference,windows", _ALMANAC_WINDOWS, ids=("1993", "2024", "2026"))
def test_phase_windows_match_independent_almanac(reference, windows):
    """Compare both directions with USNO dates tabulated to the minute."""
    jd_ref = datetime_to_julian(datetime.fromisoformat(reference))
    for target, last, nxt in windows:
        for forward, expected in ((False, last), (True, nxt)):
            actual = compute_lunar_phase_jd(jd_ref, target, forward=forward)
            expected_jd = datetime_to_julian(datetime.fromisoformat(expected).replace(tzinfo=timezone.utc))
            assert actual is not None
            assert abs(actual - expected_jd) * 86400 < 60


@pytest.mark.parametrize("target", _PHASE_TARGETS)
@pytest.mark.parametrize("offset_seconds", (-120, 120))
def test_nearest_occurrence_on_both_sides_of_real_phase(target, offset_seconds):
    """Select the nearest phase when starting two minutes before or after it."""
    jd_ref = datetime_to_julian(datetime(2026, 9, 1, tzinfo=timezone.utc))
    phase = compute_lunar_phase_jd(jd_ref, target)
    assert phase is not None
    reference = phase + offset_seconds / 86400
    last = compute_lunar_phase_jd(reference, target, forward=False)
    nxt = compute_lunar_phase_jd(reference, target, forward=True)
    assert last is not None and nxt is not None
    assert last <= reference <= nxt
    nearest = nxt if offset_seconds < 0 else last
    assert abs(nearest - phase) * 86400 < 2
    assert _SYNODIC_MIN < nxt - last < _SYNODIC_MAX


@pytest.mark.parametrize("target", (0, 90, 180, 270, -90, 360))
def test_exact_phase_boundary_and_angle_normalization(monkeypatch, target):
    """Include an exact phase in backward searches and skip it going forward."""

    # A uniform 30-day cycle with an exact root at JD 100. This also crosses
    # the opposite-phase discontinuity midway through the forward search.
    def positions(jd, body, flags):
        """Model a uniform lunar cycle with an exact phase at Julian day 100."""
        longitude = 0 if body == ephe.SUN else (target + 12 * (jd - 100)) % 360
        return ((longitude, 0, 0, 0, 0, 0), flags)

    monkeypatch.setattr(ephe, "calc_ut", positions)
    last = compute_lunar_phase_jd(100, target, forward=False)
    nxt = compute_lunar_phase_jd(100, target, forward=True)
    assert last is not None and nxt is not None
    assert 0 <= 100 - last < 1 / 86400
    assert abs(nxt - 130) < 1 / 86400


def test_missing_crossing_returns_none(monkeypatch):
    """Report no phase when the ephemeris never crosses the target angle."""
    monkeypatch.setattr(ephe, "calc_ut", lambda jd, body, flags: ((0, 0, 0, 0, 0, 0), flags))
    assert compute_lunar_phase_jd(100, 90) is None
    assert compute_lunar_phase_jd(100, 90, forward=False) is None


def test_ephemeris_failure_returns_none(monkeypatch):
    """Preserve the None fallback when ephemeris calculations fail."""

    def unavailable(*args):
        """Simulate the existing RuntimeError failure contract."""
        raise RuntimeError("Ephemeris unavailable")

    monkeypatch.setattr(ephe, "calc_ut", unavailable)
    assert compute_lunar_phase_jd(100, 90) is None
