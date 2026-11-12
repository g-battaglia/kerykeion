"""Independent orientation checks for model-versioned chart fixtures.

Skyfield supplies an IAU/equinox-based apparent sidereal clock and date-frame
poles. Closed-form horizon/meridian intersections below independently check
ASC/MC. No value from the native engine is fed back as the expected angle.
These are consumer-budget checks, not absolute accuracy certification.
"""

from __future__ import annotations

from functools import lru_cache
import math


@lru_cache(maxsize=1)
def timescale():
    """Provide the independent oracle timescale."""
    from skyfield.api import load

    return load.timescale(builtin=True)


def angular_distance(left: float, right: float) -> float:
    """Return the wrapped angular separation used by the independent oracle."""
    return abs((left - right + 180.0) % 360.0 - 180.0)


def orientation(jd_ut1: float, latitude: float, longitude: float) -> dict[str, float]:
    """Independent apparent ARMC, true obliquity, ASC and MC in degrees.

    The horizon intersection is qualified only away from the polar degeneracy;
    callers must separately preserve the production polar-house contracts.
    """
    from skyfield.framelib import ecliptic_frame

    if abs(latitude) >= 60.0:
        raise ValueError("independent horizon check requires a non-polar latitude")
    time = timescale().ut1_jd(jd_ut1)
    equator_pole = time.M[2]
    ecliptic_pole = ecliptic_frame.rotation_at(time)[2]
    dot = float(sum(a * b for a, b in zip(equator_pole, ecliptic_pole)))
    epsilon = math.acos(max(-1.0, min(1.0, dot)))
    armc = (float(time.gast) * 15.0 + longitude) % 360.0
    theta = math.radians(armc)
    phi = math.radians(latitude)
    mc = math.degrees(math.atan2(math.sin(theta), math.cos(theta) * math.cos(epsilon))) % 360.0
    asc = (
        math.degrees(
            math.atan2(math.cos(theta), -(math.sin(theta) * math.cos(epsilon) + math.tan(phi) * math.sin(epsilon)))
        )
        % 360.0
    )
    return {"armc": armc, "obliquity": math.degrees(epsilon), "ascendant": asc, "medium_coeli": mc}
