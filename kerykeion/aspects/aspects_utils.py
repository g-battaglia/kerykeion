# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""
# TODO: Better documentation and unit tests

from kerykeion.settings import KerykeionSettingsModel
from swisseph import difdeg2n
from typing import Union, TYPE_CHECKING
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel
from kerykeion.kr_types.kr_literals import AstrologicalPoint
from kerykeion.kr_types.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.settings.legacy.legacy_celestial_points_settings import DEFAULT_CELESTIAL_POINTS_SETTINGS


if TYPE_CHECKING:
    from kerykeion import AstrologicalSubjectFactory

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
        "orbit": distance - aspect_degrees,
        "distance": distance - aspect_degrees,
        "aspect_degrees": aspect_degrees,
        "diff": diff,
    }


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
