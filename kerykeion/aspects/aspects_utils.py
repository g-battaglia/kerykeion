# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""
# TODO: Better documentation and unit tests

from kerykeion import AstrologicalSubject
from kerykeion.settings import KerykeionSettingsModel
from swisseph import difdeg2n
from typing import Union


def get_aspect_from_two_points(aspects_settings: dict, point_one: Union[float, int], point_two: Union[float, int]):
    """
    Utility function.
    It calculates the aspects between the 2 points.
    Args: first point, second point.
    """

    distance = abs(difdeg2n(point_one, point_two))
    diff = abs(point_one - point_two)

    if int(distance) <= aspects_settings[0]["orb"]:
        name = aspects_settings[0]["name"]
        aspect_degrees = aspects_settings[0]["degree"]
        verdict = True
        aid = 0

    elif (
        (aspects_settings[1]["degree"] - aspects_settings[1]["orb"])
        <= int(distance)
        <= (aspects_settings[1]["degree"] + aspects_settings[1]["orb"])
    ):
        name = aspects_settings[1]["name"]
        aspect_degrees = aspects_settings[1]["degree"]
        verdict = True
        aid = 1

    elif (
        (aspects_settings[2]["degree"] - aspects_settings[2]["orb"])
        <= int(distance)
        <= (aspects_settings[2]["degree"] + aspects_settings[2]["orb"])
    ):
        name = aspects_settings[2]["name"]
        aspect_degrees = aspects_settings[2]["degree"]
        verdict = True
        aid = 2

    elif (
        (aspects_settings[3]["degree"] - aspects_settings[3]["orb"])
        <= int(distance)
        <= (aspects_settings[3]["degree"] + aspects_settings[3]["orb"])
    ):
        name = aspects_settings[3]["name"]
        aspect_degrees = aspects_settings[3]["degree"]
        verdict = True
        aid = 3

    elif (
        (aspects_settings[4]["degree"] - aspects_settings[4]["orb"])
        <= int(distance)
        <= (aspects_settings[4]["degree"] + aspects_settings[4]["orb"])
    ):
        name = aspects_settings[4]["name"]
        aspect_degrees = aspects_settings[4]["degree"]
        verdict = True
        aid = 4

    elif (
        (aspects_settings[5]["degree"] - aspects_settings[5]["orb"])
        <= int(distance)
        <= (aspects_settings[5]["degree"] + aspects_settings[5]["orb"])
    ):
        name = aspects_settings[5]["name"]
        aspect_degrees = aspects_settings[5]["degree"]
        verdict = True
        aid = 5

    elif (
        (aspects_settings[6]["degree"] - aspects_settings[6]["orb"])
        <= int(distance)
        <= (aspects_settings[6]["degree"] + aspects_settings[6]["orb"])
    ):
        name = aspects_settings[6]["name"]
        aspect_degrees = aspects_settings[6]["degree"]
        verdict = True
        aid = 6

    elif (
        (aspects_settings[7]["degree"] - aspects_settings[7]["orb"])
        <= int(distance)
        <= (aspects_settings[7]["degree"] + aspects_settings[7]["orb"])
    ):
        name = aspects_settings[7]["name"]
        aspect_degrees = aspects_settings[7]["degree"]
        verdict = True
        aid = 7

    elif (
        (aspects_settings[8]["degree"] - aspects_settings[8]["orb"])
        <= int(distance)
        <= (aspects_settings[8]["degree"] + aspects_settings[8]["orb"])
    ):
        name = aspects_settings[8]["name"]
        aspect_degrees = aspects_settings[8]["degree"]
        verdict = True
        aid = 8

    elif (
        (aspects_settings[9]["degree"] - aspects_settings[9]["orb"])
        <= int(distance)
        <= (aspects_settings[9]["degree"] + aspects_settings[9]["orb"])
    ):
        name = aspects_settings[9]["name"]
        aspect_degrees = aspects_settings[9]["degree"]
        verdict = True
        aid = 9

    elif (
        (aspects_settings[10]["degree"] - aspects_settings[10]["orb"])
        <= int(distance)
        <= (aspects_settings[10]["degree"] + aspects_settings[10]["orb"])
    ):
        name = aspects_settings[10]["name"]
        aspect_degrees = aspects_settings[10]["degree"]
        verdict = True
        aid = 10

    else:
        verdict = False
        name = None
        distance = 0
        aspect_degrees = 0
        color = None
        aid = None

    return (
        verdict,
        name,
        distance - aspect_degrees,
        aspect_degrees,
        aid,
        diff,
    )


def planet_id_decoder(planets_settings: dict, name: str):
    """
    Check if the name of the planet is the same in the settings and return
    the correct id for the planet.
    """
    str_name = str(name)
    for planet in planets_settings:
        if planet["name"] == str_name:
            result = planet["id"]
            return result


def get_active_points_list(subject: AstrologicalSubject, settings: Union[KerykeionSettingsModel, dict]) -> list:
    """
    Given an astrological subject and the settings, return a list of the active points.
    Args:
        subject (AstrologicalSubject): The astrological subject to get the active points from.
        settings (Union[KerykeionSettingsModel, dict]): Settings model o dictionary.

    Returns:
        list: List of the active points.
    """
    point_list = []
    for planet in settings["celestial_points"]:
        if planet["is_active"] == True:
            point_list.append(subject[planet["name"].lower()])

    return point_list
