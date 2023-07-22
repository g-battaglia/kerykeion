from kerykeion.kr_types import KerykeionPointModel, KerykeionException
from pathlib import Path
from typing import Union, Literal
from logging import getLogger

logger = getLogger(__name__)


def get_number_from_name(name: str) -> int:
    """Utility function, gets planet id from the name."""
    name = name.lower()

    if name == "sun":
        return 0
    elif name == "moon":
        return 1
    elif name == "mercury":
        return 2
    elif name == "venus":
        return 3
    elif name == "mars":
        return 4
    elif name == "jupiter":
        return 5
    elif name == "saturn":
        return 6
    elif name == "uranus":
        return 7
    elif name == "neptune":
        return 8
    elif name == "pluto":
        return 9
    elif name == "mean_node":
        return 10
    elif name == "true_node":
        return 11
    elif name == "chiron":
        return 15
    else:
        return int(name)


def calculate_position(
    degree: Union[int, float], number_name: str, point_type: Literal["Planet", "House"]
) -> KerykeionPointModel:
    """Utility function to create a dictionary dividing the houses or the planets list."""

    if degree < 30:
        dictionary = {
            "name": number_name,
            "quality": "Cardinal",
            "element": "Fire",
            "sign": "Ari",
            "sign_num": 0,
            "position": degree,
            "abs_pos": degree,
            "emoji": "♈️",
            "point_type": point_type,
        }

    elif degree < 60:
        result = degree - 30
        dictionary = {
            "name": number_name,
            "quality": "Fixed",
            "element": "Earth",
            "sign": "Tau",
            "sign_num": 1,
            "position": result,
            "abs_pos": degree,
            "emoji": "♉️",
            "point_type": point_type,
        }
    elif degree < 90:
        result = degree - 60
        dictionary = {
            "name": number_name,
            "quality": "Mutable",
            "element": "Air",
            "sign": "Gem",
            "sign_num": 2,
            "position": result,
            "abs_pos": degree,
            "emoji": "♊️",
            "point_type": point_type,
        }
    elif degree < 120:
        result = degree - 90
        dictionary = {
            "name": number_name,
            "quality": "Cardinal",
            "element": "Water",
            "sign": "Can",
            "sign_num": 3,
            "position": result,
            "abs_pos": degree,
            "emoji": "♋️",
            "point_type": point_type,
        }
    elif degree < 150:
        result = degree - 120
        dictionary = {
            "name": number_name,
            "quality": "Fixed",
            "element": "Fire",
            "sign": "Leo",
            "sign_num": 4,
            "position": result,
            "abs_pos": degree,
            "emoji": "♌️",
            "point_type": point_type,
        }
    elif degree < 180:
        result = degree - 150
        dictionary = {
            "name": number_name,
            "quality": "Mutable",
            "element": "Earth",
            "sign": "Vir",
            "sign_num": 5,
            "position": result,
            "abs_pos": degree,
            "emoji": "♍️",
            "point_type": point_type,
        }
    elif degree < 210:
        result = degree - 180
        dictionary = {
            "name": number_name,
            "quality": "Cardinal",
            "element": "Air",
            "sign": "Lib",
            "sign_num": 6,
            "position": result,
            "abs_pos": degree,
            "emoji": "♎️",
            "point_type": point_type,
        }
    elif degree < 240:
        result = degree - 210
        dictionary = {
            "name": number_name,
            "quality": "Fixed",
            "element": "Water",
            "sign": "Sco",
            "sign_num": 7,
            "position": result,
            "abs_pos": degree,
            "emoji": "♏️",
            "point_type": point_type,
        }
    elif degree < 270:
        result = degree - 240
        dictionary = {
            "name": number_name,
            "quality": "Mutable",
            "element": "Fire",
            "sign": "Sag",
            "sign_num": 8,
            "position": result,
            "abs_pos": degree,
            "emoji": "♐️",
            "point_type": point_type,
        }
    elif degree < 300:
        result = degree - 270
        dictionary = {
            "name": number_name,
            "quality": "Cardinal",
            "element": "Earth",
            "sign": "Cap",
            "sign_num": 9,
            "position": result,
            "abs_pos": degree,
            "emoji": "♑️",
            "point_type": point_type,
        }
    elif degree < 330:
        result = degree - 300
        dictionary = {
            "name": number_name,
            "quality": "Fixed",
            "element": "Air",
            "sign": "Aqu",
            "sign_num": 10,
            "position": result,
            "abs_pos": degree,
            "emoji": "♒️",
            "point_type": point_type,
        }
    elif degree < 360:
        result = degree - 330
        dictionary = {
            "name": number_name,
            "quality": "Mutable",
            "element": "Water",
            "sign": "Pis",
            "sign_num": 11,
            "position": result,
            "abs_pos": degree,
            "emoji": "♓️",
            "point_type": point_type,
        }
    else:
        raise KerykeionException(f"Error in calculating positions! Degrees: {degree}")

    return KerykeionPointModel(**dictionary)

