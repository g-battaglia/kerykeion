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
    aspect_degrees: int,
    exact_orb_threshold: float = 0.05
) -> AspectMovementType:
    """
    Calculate whether an aspect is applying, separating, or exact.

    An aspect is:
    - "Exact": When the orb is very tight (default < 0.17°)
    - "Applying": When the faster planet is moving toward the exact aspect
    - "Separating": When the faster planet is moving away from the exact aspect

    For simplicity, we assume the first planet (p1) is faster than the second (p2).
    This is generally true for:
    - Moon vs outer planets
    - Inner planets vs outer planets
    - Transits (transiting planet vs natal planet)

    Args:
        point_one_abs_pos: Absolute position of first point (0-360°)
        point_two_abs_pos: Absolute position of second point (0-360°)
        aspect_degrees: The exact degree of the aspect (0, 60, 90, 120, 180, etc.)
        exact_orb_threshold: Maximum orb to consider aspect "exact" (default 0.17°)

    Returns:
        "Applying", "Separating", or "Exact"

    Example:
        >>> # Moon at 45° applying to Sun at 50° (conjunction at 0°/360°)
        >>> calculate_aspect_movement(45, 50, 0)
        'Applying'
        >>> # Moon at 55° separating from Sun at 50° (conjunction)
        >>> calculate_aspect_movement(55, 50, 0)
        'Separating'
    """

    # Calculate the angular distance
    distance = abs(difdeg2n(point_one_abs_pos, point_two_abs_pos))
    orbit = abs(distance - aspect_degrees)

    # Check if aspect is exact (within tight orb)
    if orbit <= exact_orb_threshold:
        return "Exact"

    # Calculate if p1 is ahead or behind p2 relative to the aspect
    # We need to determine the direction of movement
    diff = difdeg2n(point_one_abs_pos, point_two_abs_pos)

    # For conjunction (0°) or opposition (180°)
    if aspect_degrees == 0 or aspect_degrees == 360:
        # If p1 is behind p2 (negative diff), it's applying
        # If p1 is ahead of p2 (positive diff), it's separating
        return "Applying" if diff < 0 else "Separating"

    elif aspect_degrees == 180:
        # For opposition, the logic is reversed
        return "Applying" if abs(diff) < 180 else "Separating"

    else:
        # For other aspects (60°, 90°, 120°, 150°)
        # Check if the distance is increasing or decreasing
        # If distance < aspect_degrees and diff < 0: applying
        # If distance > aspect_degrees or diff > 0: separating
        if abs(diff) < aspect_degrees:
            return "Applying" if diff < 0 else "Separating"
        else:
            return "Separating" if diff > 0 else "Applying"


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
