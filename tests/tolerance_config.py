"""
Centralized tolerance configuration for Kerykeion tests.

This module provides:
- Centralized tolerance constants for all numerical comparisons
- Environment variable overrides for CI/CD flexibility
- Body-specific tolerance helpers for lunar nodes

Rationale for tolerances:
- POSITION_TOL (0.2° = 12 arcmin): Standard tolerance for planet/house positions.
  LibEphemeris and SwissEphemeris use different astronomical models:
  - LibEphemeris: DE441, ICRF 3.0, IAU 2006/2000A (1365 terms)
  - SwissEphemeris: DE431, ICRF 2.0, IAU 2000B (77 terms)
  These differences can cause variations up to ~0.15° for historical dates.

- SPEED_TOL (0.01° = 36 arcsec/day): Lunar speed varies ~11-15°/day.
  Increased to account for model differences.

- DECLINATION_TOL (0.05° = 3 arcmin): Declination calculations involve
  different nutation models.

- TRUE_NODE_TOL (0.01° = 36 arcsec): True lunar nodes use geometric
  method (h = r × v) in LibEphemeris vs osculating elements in SWE.

- TRUE_LILITH_TOL (0.05° = 3 arcmin): True Lilith (apogee) has larger
  variation due to orbital perturbation model differences.

- MEAN_LUNAR_TOL (0.01° = 36 arcsec): Mean nodes/Lilith may differ
  due to polynomial range limitations for historical dates.

- SVG_REL_TOL (5.0°): SVG rendering comparison - large tolerance for
  coordinate differences between ephemeris libraries.

- SVG_ABS_TOL (5.0°): SVG rendering comparison.

Environment Variables:
    KERYKEION_POSITION_TOL: Override position tolerance
    KERYKEION_SPEED_TOL: Override speed tolerance
    KERYKEION_DECLINATION_TOL: Override declination tolerance
    KERYKEION_TRUE_NODE_TOL: Override true node tolerance
    KERYKEION_TRUE_LILITH_TOL: Override true Lilith tolerance
    KERYKEION_MEAN_LUNAR_TOL: Override mean lunar tolerance
    KERYKEION_SVG_REL_TOL: Override SVG relative tolerance
    KERYKEION_SVG_ABS_TOL: Override SVG absolute tolerance
"""

import os
from typing import Literal


POSITION_TOL = float(os.environ.get("KERYKEION_POSITION_TOL", "0.2"))
SPEED_TOL = float(os.environ.get("KERYKEION_SPEED_TOL", "0.01"))
DECLINATION_TOL = float(os.environ.get("KERYKEION_DECLINATION_TOL", "0.05"))
TRUE_NODE_TOL = float(os.environ.get("KERYKEION_TRUE_NODE_TOL", "0.01"))
TRUE_LILITH_TOL = float(os.environ.get("KERYKEION_TRUE_LILITH_TOL", "0.05"))
MEAN_LUNAR_TOL = float(os.environ.get("KERYKEION_MEAN_LUNAR_TOL", "0.01"))
SVG_REL_TOL = float(os.environ.get("KERYKEION_SVG_REL_TOL", "5.0"))
SVG_ABS_TOL = float(os.environ.get("KERYKEION_SVG_ABS_TOL", "5.0"))


def get_tolerance_for_body(body_name: str, attr: Literal["position", "speed", "declination"] = "position") -> float:
    """
    Get appropriate tolerance for a specific body and attribute.

    Args:
        body_name: Name of the astrological body (e.g., "sun", "true_north_lunar_node")
        attr: Attribute being tested ("position", "speed", or "declination")

    Returns:
        Appropriate tolerance in degrees

    Examples:
        >>> get_tolerance_for_body("sun", "position")
        0.01
        >>> get_tolerance_for_body("moon", "speed")
        0.0003
        >>> get_tolerance_for_body("true_north_lunar_node", "position")
        0.003
    """
    body_lower = body_name.lower()

    if attr == "speed":
        return SPEED_TOL

    if attr == "declination":
        return DECLINATION_TOL

    if "true_north" in body_lower or "true_south" in body_lower:
        return TRUE_NODE_TOL

    if "true_lilith" in body_lower:
        return TRUE_LILITH_TOL

    if "mean_north" in body_lower or "mean_south" in body_lower or "mean_lilith" in body_lower:
        return MEAN_LUNAR_TOL

    return POSITION_TOL
