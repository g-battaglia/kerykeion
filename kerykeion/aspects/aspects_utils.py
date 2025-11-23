# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""
# TODO: Better documentation and unit tests

from swisseph import difdeg2n
from typing import Union
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel
from kerykeion.schemas.kr_literals import AspectMovementType
from kerykeion.schemas.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS


def get_aspect_from_two_points(
    aspects_settings: Union[list[dict], list[dict]],
    point_one: Union[float, int],
    point_two: Union[float, int],
):
    """
    Utility function to calculate the aspects between two points.

    Args:
        aspects_settings (dict): Dictionary containing aspect settings.
        point_one (Union[float, int]): First point.
        point_two (Union[float, int]): Second point.

    Returns:
        dict: Dictionary containing the aspect details.
    """
    distance = abs(difdeg2n(point_one, point_two))
    diff = abs(point_one - point_two)

    for aid, aspect in enumerate(aspects_settings):
        # TODO: Remove the "degree" element EVERYWHERE!
        aspect_degree = aspect["degree"] # type: ignore
        aspect_orb = aspect["orb"] # type: ignore

        if (aspect_degree - aspect_orb) <= int(distance) <= (aspect_degree + aspect_orb):
            name = aspect["name"] # type: ignore
            aspect_degrees = aspect_degree
            verdict = True
            break
    else:
        verdict = False
        name = None
        aspect_degrees = 0

    return {
        "verdict": verdict,
        "name": name,
        "orbit": abs(distance - aspect_degrees),
        "distance": abs(distance - aspect_degrees),
        "aspect_degrees": aspect_degrees,
        "diff": diff,
    }


def _sign(x: float) -> int:
    """
    Return the sign of ``x``.

    Returns +1 if ``x`` > 0, -1 if ``x`` < 0, and 0 if ``x`` == 0.
    """
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0


def calculate_aspect_movement(
    point_one_abs_pos: float,
    point_two_abs_pos: float,
    aspect_degrees: float,
    point_one_speed: float,
    point_two_speed: float,
) -> AspectMovementType:
    """
    Determine whether the aspect orb is decreasing (Applying), increasing
    (Separating), or not changing (Static).

    How it works:
    - The point with the largest absolute speed is treated as the "faster" one
      (retrograde included).
    - We measure the signed separation from the slower point to the faster one
      using ``difdeg2n`` and compare it to the exact aspect angle.
    - The product of three signs tells us whether the orb shrinks or grows:
        1. sign of the separation (is the faster point ahead or behind?)
        2. sign of the distance from exactness (inside orb vs beyond)
        3. sign of the relative speed (direction of the faster point w.r.t. slower)
      A negative product => Applying; positive => Separating.
    - If both points are effectively motionless, or their relative speed is
      zero, we return "Static".

    Speeds are signed (direct > 0, retrograde < 0). Longitudes are normalized to
    [0, 360) and aspect angles are mirrored to [0, 180].
    """

    if point_one_speed is None or point_two_speed is None:
        raise ValueError(
            "Speed values for both points are required to compute aspect "
            "movement correctly. point_one_speed and point_two_speed "
            "cannot be None."
        )

    # Normalize longitudes to [0, 360)
    p1 = point_one_abs_pos % 360.0
    p2 = point_two_abs_pos % 360.0

    # Normalize aspect to [0, 360) and then to [0, 180]
    aspect = aspect_degrees % 360.0
    if aspect > 180.0:
        aspect = 360.0 - aspect  # es. 240 -> 120

    if point_one_speed == 0 and point_two_speed == 0:
        return "Static"

    # Identify the faster point by absolute speed.
    if abs(point_one_speed) > abs(point_two_speed):
        fast_pos, fast_speed = p1, point_one_speed
        slow_pos, slow_speed = p2, point_two_speed
    else:
        fast_pos, fast_speed = p2, point_two_speed
        slow_pos, slow_speed = p1, point_one_speed

    # Signed separation from slow -> fast and relative speed of fast vs slow.
    separation = difdeg2n(fast_pos, slow_pos)
    relative_speed = fast_speed - slow_speed

    # If their relative motion is zero, the orb stays unchanged.
    if relative_speed == 0:
        return "Static"

    sign_sep = _sign(separation)                  # fast ahead of slow (+) or behind (-)
    sign_delta = _sign(abs(separation) - aspect)  # are we inside or beyond the exact angle
    sign_rel = _sign(relative_speed)              # direction of fast relative to slow

    orb_trend = sign_delta * sign_sep * sign_rel
    return "Applying" if orb_trend < 0 else "Separating"


def planet_id_decoder(planets_settings: list[KerykeionSettingsCelestialPointModel], name: str) -> int:
    """
    Check if the name of the planet is the same in the settings and return
    the correct id for the planet.
    """
    str_name = str(name)
    for planet in planets_settings:
        if planet["name"] == str_name:
            result = planet["id"]
            return result

    raise ValueError(f"Planet {name} not found in the settings")


def get_active_points_list(
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    active_points: list = [],
    *,
    celestial_points: list[dict] = DEFAULT_CELESTIAL_POINTS_SETTINGS,
) -> list:
    """
    Given an astrological subject and the settings, return a list of the active points.
    Args:
        subject (AstrologicalSubject): The astrological subject to get the active points from.
        settings (Union[KerykeionSettingsModel, dict]): Settings model o dictionary.

    Returns:
        list: List of the active points.
    """
    point_list = []
    for planet in celestial_points:
        if planet["name"] in active_points:
            point_list.append(subject[planet["name"].lower()])

    return point_list
