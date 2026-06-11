"""
Regression tests for compute_lunar_phase_jd search directions.

The normalized Sun-Moon angular difference is a sawtooth with a ±180° wrap
once per synodic month. A plain bisection over a 30-day window could converge
on the wrap (returning the *opposite* phase — every backward search did this)
or collapse onto a window edge (a rarer forward failure when the wrap split
the bracket). These tests pin the bracketing-based implementation with the
real ephemeris, property-style, so no almanac constants are needed.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from kerykeion.moon_phase_details.utils import (
    compute_lunar_phase_jd,
    configure_ephemeris_path,
)
from kerykeion.ephemeris_backend import swe
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
    configure_ephemeris_path()
    iflag = swe.FLG_SWIEPH
    sun = swe.calc_ut(jd, swe.SUN, iflag)[0]
    moon = swe.calc_ut(jd, swe.MOON, iflag)[0]
    return (float(moon[0]) - float(sun[0])) % 360.0


def _angle_error(jd: float, target: float) -> float:
    return abs((_phase_angle(jd) - target + 180.0) % 360.0 - 180.0)


@pytest.mark.parametrize("reference", _REFERENCE_DATES, ids=lambda d: d.strftime("%Y-%m-%d"))
@pytest.mark.parametrize("target", _PHASE_TARGETS, ids=("NM", "FQ", "FM", "LQ"))
def test_backward_and_forward_bracket_the_reference(reference: datetime, target: float) -> None:
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
