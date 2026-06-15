# -*- coding: utf-8 -*-
"""
Low-level engine for :class:`VoidOfCourseMoonFactory`.

The Moon is *void of course* from the instant it perfects its last exact
Ptolemaic aspect to a traditional planet, while still in its current sign, until
it ingresses into the next sign. Determining this requires (a) the Moon's sign
ingress time and (b) the time of every exact aspect the Moon makes within the
sign.

Rather than scanning time step by step, this module exploits a structural fact:
the Moon is by far the fastest classical body, so its ecliptic longitude relative
to any other planet increases monotonically across a single sign (~2-2.5 days).
That lets us seed each event analytically (assuming locally linear motion) and
then refine it to arc-second precision with a couple of Newton iterations against
real ``ephe.calc_ut`` longitudes. The cost is a few dozen single-body position
lookups — no full astrological subject is ever built.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from kerykeion.aspects.aspects_utils import difdeg2n
from kerykeion.ephemeris_backend import ephe
from kerykeion.schemas.kr_literals import VocAspectName, VocTargetPlanet
from kerykeion.sun_times.utils import julian_day_to_utc
from kerykeion.utilities import datetime_to_julian

# Traditional aspecting bodies (the Moon itself is excluded).
VOC_BODIES: tuple[VocTargetPlanet, ...] = ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn")

# The five Ptolemaic (major) aspects considered for perfection: (name, degrees).
PTOLEMAIC_ASPECTS: tuple[tuple[VocAspectName, float], ...] = (
    ("conjunction", 0.0),
    ("sextile", 60.0),
    ("square", 90.0),
    ("trine", 120.0),
    ("opposition", 180.0),
)

_BODY_ID: dict[str, int] = {
    "Sun": ephe.SUN,
    "Moon": ephe.MOON,
    "Mercury": ephe.MERCURY,
    "Venus": ephe.VENUS,
    "Mars": ephe.MARS,
    "Jupiter": ephe.JUPITER,
    "Saturn": ephe.SATURN,
}

# Newton convergence threshold in degrees (~1e-5° ≈ 0.6 s of Moon travel) and the
# maximum iterations; convergence is quadratic so a handful always suffices.
_ANGLE_EPSILON = 1e-5
_MAX_ITERATIONS = 6
# Mean lunar motion (deg/day), used only as a non-zero guard — the Moon is never
# actually stationary or retrograde in longitude.
_MEAN_LUNAR_SPEED = 13.176


@dataclass(frozen=True)
class AspectEvent:
    """An exact aspect the Moon perfects to another body, with its UTC moment."""

    planet: VocTargetPlanet
    aspect: VocAspectName
    degrees: float
    exact_time: datetime


@dataclass(frozen=True)
class VoidOfCourseResult:
    """Outcome of a void-of-course computation (sign indices are 0=Aries…11=Pisces)."""

    is_void_of_course: bool
    moon_sign_index: int
    next_sign_index: int
    ingress: datetime
    void_start: datetime
    void_end: datetime
    last_aspect: Optional[AspectEvent]
    next_aspect: Optional[AspectEvent]


def _lon_speed(jd: float, body_id: int, iflag: int) -> tuple[float, float]:
    """Return ``(ecliptic_longitude, longitude_speed_deg_per_day)`` at a Julian Day."""
    values = ephe.calc_ut(jd, body_id, iflag)[0]
    return values[0], values[3]


def _moon_crossing_jd(jd0: float, target_longitude: float, guess_days: float, iflag: int) -> float:
    """Newton-refine the Julian Day at which the Moon reaches ``target_longitude``."""
    jd = jd0 + guess_days
    for _ in range(_MAX_ITERATIONS):
        longitude, speed = _lon_speed(jd, ephe.MOON, iflag)
        error = difdeg2n(longitude, target_longitude)  # signed degrees, 0 at crossing
        if not speed or abs(error) < _ANGLE_EPSILON:
            break
        jd -= error / speed
    return jd


def _aspect_perfection_jd(jd_guess: float, body_id: int, signed_target: float, iflag: int) -> Optional[float]:
    """Newton-refine the Julian Day where Moon-body separation equals ``signed_target``.

    Returns ``None`` if the iteration does not reach ``signed_target`` within
    ``_ANGLE_EPSILON`` after ``_MAX_ITERATIONS`` (or the relative speed degenerates),
    so a non-converged iterate is never accepted as an exact aspect instant.
    """
    jd = jd_guess
    for _ in range(_MAX_ITERATIONS):
        moon_lon, moon_speed = _lon_speed(jd, ephe.MOON, iflag)
        body_lon, body_speed = _lon_speed(jd, body_id, iflag)
        separation = difdeg2n(moon_lon, body_lon)
        error = difdeg2n(separation, signed_target)
        relative_speed = moon_speed - body_speed
        if abs(relative_speed) < 1e-10:
            return None
        if abs(error) < _ANGLE_EPSILON:
            return jd
        jd -= error / relative_speed
    return None


def _aspects_in_window(
    jd_ref: float,
    win_start_jd: float,
    win_end_jd: float,
    iflag: int,
    *,
    start_tol: float = 1e-3,
    end_tol: float = 1e-6,
) -> list[AspectEvent]:
    """Every exact Moon→VOC-body aspect perfecting within ``[win_start, win_end)``.

    ``jd_ref`` seeds the linear approximation, so it must lie inside (or very near)
    the window for the analytic seeds to land in range. ``start_tol``/``end_tol``
    widen or tighten each boundary: the in-sign scan keeps the entry side wide (the
    backward Newton seed overshoots, ~86 s) and the cusp side tight; the next-sign
    scan tightens the entry side too so the shared cusp aspect is not double-counted.
    The returned list is deduplicated and ordered by ``exact_time``.
    """
    moon_lon, moon_speed = _lon_speed(jd_ref, ephe.MOON, iflag)
    if moon_speed <= 0:  # defensive: the Moon never goes retrograde in longitude
        moon_speed = _MEAN_LUNAR_SPEED

    events: list[AspectEvent] = []
    for planet in VOC_BODIES:
        body_id = _BODY_ID[planet]
        body_lon, body_speed = _lon_speed(jd_ref, body_id, iflag)
        relative_speed = moon_speed - body_speed
        # Defensive guard only: with real ephemerides the Moon (>= ~11.8 deg/day,
        # even at apogee) always outpaces every VOC body (Mercury peaks near
        # ~2 deg/day geocentrically), so this branch is not expected to trigger.
        # It protects the linear seed below from a non-positive relative speed.
        if relative_speed <= 0:
            continue
        separation0 = difdeg2n(moon_lon, body_lon)
        for aspect_name, degrees in PTOLEMAIC_ASPECTS:
            signed_targets = (degrees,) if degrees in (0.0, 180.0) else (degrees, -degrees)
            for target in signed_targets:
                delta = target - separation0
                for wrap in (-1, 0, 1):
                    guess_jd = jd_ref + (delta + 360.0 * wrap) / relative_speed
                    refined = _aspect_perfection_jd(guess_jd, body_id, target, iflag)
                    if refined is None:
                        continue
                    if win_start_jd - start_tol <= refined < win_end_jd - end_tol:
                        events.append(AspectEvent(planet, aspect_name, degrees, julian_day_to_utc(refined)))

    # Deduplicate events that converged from multiple seeds (one per planet/aspect/minute).
    unique: dict[tuple[str, str, int], AspectEvent] = {}
    for event in events:
        key = (event.planet, event.aspect, round(datetime_to_julian(event.exact_time) * 1440))
        unique.setdefault(key, event)
    return sorted(unique.values(), key=lambda e: e.exact_time)


def compute_void_of_course(moment_utc: datetime, iflag: int) -> VoidOfCourseResult:
    """
    Compute the Moon's void-of-course state at a UTC instant.

    Args:
        moment_utc: The moment to evaluate, as a timezone-aware UTC ``datetime``.
        iflag: Ephemeris calculation flags (``ephe.FLG_SWIEPH | ephe.FLG_SPEED``,
            plus ``ephe.FLG_SIDEREAL`` for sidereal zodiacs; the sidereal mode must
            already be configured via ``ephe.set_sid_mode``).

    Returns:
        VoidOfCourseResult: ingress, void window, and the framing aspects.
    """
    jd0 = datetime_to_julian(moment_utc)
    moon_lon, moon_speed = _lon_speed(jd0, ephe.MOON, iflag)
    if moon_speed <= 0:  # defensive: the Moon never goes retrograde in longitude
        moon_speed = _MEAN_LUNAR_SPEED

    sign_index = int(moon_lon // 30) % 12
    sign_floor = sign_index * 30.0
    sign_ceiling = sign_floor + 30.0

    ingress_jd = _moon_crossing_jd(jd0, sign_ceiling % 360.0, (sign_ceiling - moon_lon) / moon_speed, iflag)
    entry_jd = _moon_crossing_jd(jd0, sign_floor, (sign_floor - moon_lon) / moon_speed, iflag)

    # Aspects the Moon perfects while inside the current sign — these frame the void.
    current = _aspects_in_window(jd0, entry_jd, ingress_jd, iflag)

    ingress_dt = julian_day_to_utc(ingress_jd)

    if current:
        last_aspect = current[-1]
        void_start = last_aspect.exact_time
    else:
        last_aspect = None
        void_start = julian_day_to_utc(entry_jd)

    # Void now iff the last in-sign aspect has already perfected by `moment_utc`.
    is_void = void_start <= moment_utc

    # `next_aspect` is the first exact aspect the Moon makes AFTER it ingresses into
    # the next sign — the aspect that ends the void-of-course lull. It must be sought
    # in the *next* sign, never reused from the current-sign list (doing so collapses
    # it onto `last_aspect` whenever the query precedes that aspect). Seed from the
    # midpoint of the next sign so the linear approximation lands inside the window.
    next_ingress_jd = _moon_crossing_jd(
        ingress_jd, (sign_ceiling + 30.0) % 360.0, 30.0 / moon_speed, iflag
    )
    jd_ref_next = (ingress_jd + next_ingress_jd) / 2.0
    following = _aspects_in_window(jd_ref_next, ingress_jd, next_ingress_jd, iflag, start_tol=1e-6)
    next_aspect = following[0] if following else None

    return VoidOfCourseResult(
        is_void_of_course=is_void,
        moon_sign_index=sign_index,
        next_sign_index=(sign_index + 1) % 12,
        ingress=ingress_dt,
        void_start=void_start,
        void_end=ingress_dt,
        last_aspect=last_aspect,
        next_aspect=next_aspect,
    )
