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

    This implementation uses a "lookahead" approach:
    1. Calculate the current orb (deviation from exact aspect).
    2. Project positions forward by a small time step (dt).
    3. Calculate the future orb.
    4. Compare: if future_orb < current_orb => Applying, else Separating.

    Args:
        point_one_abs_pos (float): Absolute position of point 1 (0-360).
        point_two_abs_pos (float): Absolute position of point 2 (0-360).
        aspect_degrees (float): The exact aspect angle (e.g., 0, 60, 90, 120, 180).
        point_one_speed (float): Speed of point 1 in degrees/day (negative for retrograde).
        point_two_speed (float): Speed of point 2 in degrees/day (negative for retrograde).

    Returns:
        AspectMovementType: "Applying", "Separating", or "Static".
    """

    if point_one_speed is None or point_two_speed is None:
        raise ValueError(
            "Speed values for both points are required to compute aspect "
            "movement correctly. point_one_speed and point_two_speed "
            "cannot be None."
        )

    # If relative speed is effectively zero, the aspect is static.
    if abs(point_one_speed - point_two_speed) < 1e-9:
        return "Static"
    
    # Helper to calculate the orb (distance from exact aspect)
    def get_orb(p1: float, p2: float, aspect: float) -> float:
        # Calculate shortest distance between points on the circle
        diff = abs(difdeg2n(p1, p2))
        # The orb is the absolute difference between the actual separation and the aspect angle
        return abs(diff - aspect)

    # Normalize aspect to [0, 360) and then to [0, 180]
    # This is necessary because difdeg2n returns the shortest distance (<= 180)
    aspect_norm = aspect_degrees % 360.0
    if aspect_norm > 180.0:
        aspect_norm = 360.0 - aspect_norm

    # 1. Current state
    current_orb = get_orb(point_one_abs_pos, point_two_abs_pos, aspect_norm)

    # 2. Future state (lookahead)
    # We use a small time step. Since speed is deg/day, dt=0.001 days is ~1.4 minutes.
    # Small enough to be linear, large enough to avoid float precision issues if speeds are reasonable.
    dt = 0.001
    p1_future = (point_one_abs_pos + point_one_speed * dt) % 360.0
    p2_future = (point_two_abs_pos + point_two_speed * dt) % 360.0
    
    future_orb = get_orb(p1_future, p2_future, aspect_norm)

    # 3. Compare
    if future_orb < current_orb:
        return "Applying"
    elif future_orb > current_orb:
        return "Separating"
    else:
        # Should be rare with floats, but technically possible if moving exactly parallel to the aspect circle?
        # Or if speeds are 0.
        return "Static"


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
