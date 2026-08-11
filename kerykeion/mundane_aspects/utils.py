# -*- coding: utf-8 -*-
"""
Low-level scan engine for :class:`MundaneAspectFactory`.

A *mundane* (transiting-to-transiting) aspect perfects at the instant the
signed ecliptic separation between two moving bodies equals the aspect angle.
Unlike the void-of-course engine — where the Moon always outruns every target
and Newton iteration converges safely — a mutual pair of slow planets can have
a relative speed arbitrarily close to zero (e.g. Jupiter–Saturn near mutual
stations), where Newton diverges. This engine therefore samples the signed
separation on a uniform grid and refines every bracketed sign change by
bisection, which is unconditionally convergent.

Grid safety: the fastest relative motion is Moon vs retrograde Mercury,
≈ 16.8°/day → ≈ 4.2° per 6-hour step. The smallest gap between adjacent
signed aspect targets (with the full minor-aspect vocabulary enabled) is 6°
(144° → 150°), so a single step can never jump across two targets. The only
crossing a bracket can hide is a there-and-back excursion around one target,
which requires a relative-motion reversal inside the step — detected via the
endpoint relative speeds and resolved by splitting the interval at its
midpoint (the same probe idea as ``SignIngressFactory._emit_segment``).

Swiss Ephemeris / libephemeris functions used:
    - ephe.calc_ut(jd, planet_id, iflag)  (iflag includes FLG_SPEED)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

from kerykeion.aspects.utils import difdeg2n
from kerykeion.ephemeris_backend import ephe
from kerykeion.schemas.exceptions import KerykeionException

# Uniform sampling step (days). See module docstring for the safety argument.
_STEP_DAYS = 0.25
# Bisection iterations: 27 halvings on a 6-hour bracket resolve ~2 ms — far
# below the 1-second rounding of the ISO output.
_BISECTION_ITERS = 27
# Backstop on grid samples per scan (~1,370 years at the 6-hour step — every
# sample costs one calc_ut per requested body); oversized ranges are rejected
# explicitly, never silently truncated. Same order of magnitude as
# SignIngressFactory's per-planet cap.
_MAX_SAMPLES = 2_000_000
# Midpoint-split recursion depth for relative-motion reversals inside a step.
_MAX_SPLIT_DEPTH = 2


@dataclass(frozen=True)
class MundaneAspectEvent:
    """An exact aspect between two transiting bodies, at a Julian Day (UT)."""

    point_a: str
    point_b: str
    aspect: str
    degrees: float
    julian_day: float


def _lon_speed(jd: float, body_id: int, iflag: int) -> Tuple[float, float]:
    """Return ``(ecliptic_longitude, longitude_speed_deg_per_day)`` at ``jd``."""
    try:
        values = ephe.calc_ut(jd, body_id, iflag)[0]
    except Exception as exc:
        # Range errors (libephemeris EphemerisRangeError, swisseph.Error)
        # propagate raw from calc_ut — normalize to the documented exception
        # type, mirroring SignIngressFactory._lon.
        raise KerykeionException(
            f"Mundane aspect search failed at JD {jd:.5f}: {exc}. This usually "
            f"means the date falls outside the available ephemeris range; "
            f"narrow the date range."
        ) from exc
    return float(values[0]) % 360.0, float(values[3])


def _signed_targets(degrees: float) -> Tuple[float, ...]:
    """Signed separation targets for an aspect angle (VoC engine convention)."""
    if degrees in (0.0, 180.0):
        return (degrees,)
    return (degrees, -degrees)


def _bisect_aspect(
    body_a: int,
    body_b: int,
    a: float,
    b: float,
    target: float,
    iflag: int,
) -> float:
    """Bisect ``[a, b]`` to the JD where the signed separation equals ``target``.

    Precondition: ``h(a)`` and ``h(b)`` have opposite (non-zero) signs, where
    ``h(t) = difdeg2n(separation(t), target)``.
    """
    fa = difdeg2n(
        difdeg2n(_lon_speed(a, body_a, iflag)[0], _lon_speed(a, body_b, iflag)[0]),
        target,
    )
    for _ in range(_BISECTION_ITERS):
        mid = (a + b) / 2.0
        fm = difdeg2n(
            difdeg2n(_lon_speed(mid, body_a, iflag)[0], _lon_speed(mid, body_b, iflag)[0]),
            target,
        )
        if fm == 0.0:
            return mid
        if (fa < 0.0) != (fm < 0.0):
            b = mid
        else:
            a, fa = mid, fm
    return (a + b) / 2.0


def _emit_targets_in_segment(
    name_a: str,
    name_b: str,
    body_a: int,
    body_b: int,
    t0: float,
    t1: float,
    sep0: float,
    sep1: float,
    rel0: float,
    rel1: float,
    aspects: Sequence[Tuple[str, float]],
    iflag: int,
    out: List[MundaneAspectEvent],
    depth: int,
) -> None:
    """Emit every aspect perfection inside ``[t0, t1]`` for one body pair.

    ``sep*``/``rel*`` are the signed separation and relative speed at the
    endpoints (already computed by the caller — no redundant lookups).
    """
    # A relative-motion reversal inside the interval can hide a there-and-back
    # double crossing of one target while the endpoint separations show no sign
    # change. Split at the midpoint so each half is (near-)monotonic. Only slow
    # mutual pairs ever reverse, and they move < 0.1°/step, so depth 2 suffices.
    if (rel0 < 0.0) != (rel1 < 0.0) and depth < _MAX_SPLIT_DEPTH:
        mid = (t0 + t1) / 2.0
        lon_a_mid, speed_a_mid = _lon_speed(mid, body_a, iflag)
        lon_b_mid, speed_b_mid = _lon_speed(mid, body_b, iflag)
        sep_mid = difdeg2n(lon_a_mid, lon_b_mid)
        rel_mid = speed_a_mid - speed_b_mid
        _emit_targets_in_segment(
            name_a, name_b, body_a, body_b, t0, mid, sep0, sep_mid, rel0, rel_mid,
            aspects, iflag, out, depth + 1,
        )
        _emit_targets_in_segment(
            name_a, name_b, body_a, body_b, mid, t1, sep_mid, sep1, rel_mid, rel1,
            aspects, iflag, out, depth + 1,
        )
        return

    for aspect_name, degrees in aspects:
        for target in _signed_targets(degrees):
            h0 = difdeg2n(sep0, target)
            h1 = difdeg2n(sep1, target)
            if h0 == 0.0:
                # Exact hit on a grid node; the dedupe pass absorbs the copy the
                # previous interval may have emitted at its right endpoint.
                out.append(MundaneAspectEvent(name_a, name_b, aspect_name, degrees, t0))
            elif h1 == 0.0:
                out.append(MundaneAspectEvent(name_a, name_b, aspect_name, degrees, t1))
            elif (h0 < 0.0) != (h1 < 0.0) and abs(h0) + abs(h1) < 180.0:
                # Opposite signs with a small combined swing = a true crossing of
                # `target`; a large swing means the separation wrapped through the
                # antipode of the target (±180° away), not a perfection.
                jd = _bisect_aspect(body_a, body_b, t0, t1, target, iflag)
                out.append(MundaneAspectEvent(name_a, name_b, aspect_name, degrees, jd))


def scan_mundane_aspects(
    start_jd: float,
    end_jd: float,
    bodies: Sequence[Tuple[str, int]],
    aspects: Sequence[Tuple[str, float]],
    iflag: int,
) -> List[MundaneAspectEvent]:
    """Every exact aspect between distinct body pairs within ``[start_jd, end_jd]``.

    Args:
        start_jd: Julian Day (UT) range start.
        end_jd: Julian Day (UT) range end.
        bodies: ``(name, ephemeris_id)`` pairs, already in canonical order —
            each emitted event keeps ``point_a`` = the earlier entry.
        aspects: ``(name, degrees)`` pairs to search for.
        iflag: Ephemeris flags from the enclosing session (includes FLG_SPEED).

    Returns:
        Chronologically ordered, deduplicated events.
    """
    if end_jd <= start_jd or len(bodies) < 2 or not aspects:
        return []

    n_steps = int((end_jd - start_jd) / _STEP_DAYS) + 1
    if n_steps > _MAX_SAMPLES:
        raise ValueError(
            f"Date range too large to scan at the current resolution "
            f"(> {_MAX_SAMPLES} samples). Narrow the date range."
        )

    # Grid of sample times: uniform 6-hour steps, exact range end appended so
    # the final partial interval is scanned too.
    grid: List[float] = [start_jd + i * _STEP_DAYS for i in range(n_steps)]
    if grid[-1] < end_jd:
        grid.append(end_jd)

    # One calc_ut per (sample, body), shared across every pair.
    lons: Dict[str, List[float]] = {}
    speeds: Dict[str, List[float]] = {}
    for name, body_id in bodies:
        lon_list: List[float] = []
        speed_list: List[float] = []
        for t in grid:
            lon, speed = _lon_speed(t, body_id, iflag)
            lon_list.append(lon)
            speed_list.append(speed)
        lons[name] = lon_list
        speeds[name] = speed_list

    events: List[MundaneAspectEvent] = []
    for i_a in range(len(bodies) - 1):
        name_a, body_a = bodies[i_a]
        for i_b in range(i_a + 1, len(bodies)):
            name_b, body_b = bodies[i_b]
            for k in range(len(grid) - 1):
                sep0 = difdeg2n(lons[name_a][k], lons[name_b][k])
                sep1 = difdeg2n(lons[name_a][k + 1], lons[name_b][k + 1])
                rel0 = speeds[name_a][k] - speeds[name_b][k]
                rel1 = speeds[name_a][k + 1] - speeds[name_b][k + 1]
                _emit_targets_in_segment(
                    name_a, name_b, body_a, body_b,
                    grid[k], grid[k + 1], sep0, sep1, rel0, rel1,
                    aspects, iflag, events, 0,
                )

    # Dedupe grid-boundary double hits (exact node hits, or two adjacent
    # brackets converging on the same instant): identity is the pair + aspect
    # + the second-rounded instant.
    unique: Dict[Tuple[str, str, str, int], MundaneAspectEvent] = {}
    for event in events:
        key = (event.point_a, event.point_b, event.aspect, round(event.julian_day * 86400.0))
        unique.setdefault(key, event)
    return sorted(unique.values(), key=lambda e: e.julian_day)
