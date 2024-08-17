from kerykeion.kr_types import KerykeionPointModel, KerykeionException, ZodiacSignModel
from kerykeion.kr_types.kr_literals import LunarPhaseEmoji, LunarPhaseName, PointType, Planet, Houses
from typing import Union
import logging
import math



def get_number_from_name(name: Planet) -> int:
    """Utility function, gets planet id from the name."""

    if name == "Sun":
        return 0
    elif name == "Moon":
        return 1
    elif name == "Mercury":
        return 2
    elif name == "Venus":
        return 3
    elif name == "Mars":
        return 4
    elif name == "Jupiter":
        return 5
    elif name == "Saturn":
        return 6
    elif name == "Uranus":
        return 7
    elif name == "Neptune":
        return 8
    elif name == "Pluto":
        return 9
    elif name == "Mean_Node":
        return 10
    elif name == "True_Node":
        return 11
    elif name == "Chiron":
        return 15
    elif name == "Mean_Lilith":
        return 12
    else:
        raise KerykeionException(f"Error in getting number from name! Name: {name}")


def get_kerykeion_point_from_degree(
    degree: Union[int, float], name: Union[Planet, Houses], point_type: PointType
) -> KerykeionPointModel:
    """
    Returns a KerykeionPointModel object based on the given degree.

    Args:
        degree (Union[int, float]): The degree of the celestial point.
        name (str): The name of the celestial point.
        point_type (PointType): The type of the celestial point.

    Raises:
        KerykeionException: If the degree is not within the valid range (0-360).

    Returns:
        KerykeionPointModel: The model representing the celestial point.
    """

    if degree < 0 or degree >= 360:
        raise KerykeionException(f"Error in calculating positions! Degrees: {degree}")

    ZODIAC_SIGNS = {
        0: ZodiacSignModel(sign="Ari", quality="Cardinal", element="Fire", emoji="♈️", sign_num=0),
        1: ZodiacSignModel(sign="Tau", quality="Fixed", element="Earth", emoji="♉️", sign_num=1),
        2: ZodiacSignModel(sign="Gem", quality="Mutable", element="Air", emoji="♊️", sign_num=2),
        3: ZodiacSignModel(sign="Can", quality="Cardinal", element="Water", emoji="♋️", sign_num=3),
        4: ZodiacSignModel(sign="Leo", quality="Fixed", element="Fire", emoji="♌️", sign_num=4),
        5: ZodiacSignModel(sign="Vir", quality="Mutable", element="Earth", emoji="♍️", sign_num=5),
        6: ZodiacSignModel(sign="Lib", quality="Cardinal", element="Air", emoji="♎️", sign_num=6),
        7: ZodiacSignModel(sign="Sco", quality="Fixed", element="Water", emoji="♏️", sign_num=7),
        8: ZodiacSignModel(sign="Sag", quality="Mutable", element="Fire", emoji="♐️", sign_num=8),
        9: ZodiacSignModel(sign="Cap", quality="Cardinal", element="Earth", emoji="♑️", sign_num=9),
        10: ZodiacSignModel(sign="Aqu", quality="Fixed", element="Air", emoji="♒️", sign_num=10),
        11: ZodiacSignModel(sign="Pis", quality="Mutable", element="Water", emoji="♓️", sign_num=11),
    }

    sign_index = int(degree // 30)
    sign_degree = degree % 30
    zodiac_sign = ZODIAC_SIGNS[sign_index]

    return KerykeionPointModel(
        name=name,
        quality=zodiac_sign.quality,
        element=zodiac_sign.element,
        sign=zodiac_sign.sign,
        sign_num=zodiac_sign.sign_num,
        position=sign_degree,
        abs_pos=degree,
        emoji=zodiac_sign.emoji,
        point_type=point_type,
    )

def setup_logging(level: str) -> None:
    """
    Setup logging for testing.

    Args:
        level: Log level as a string, options: debug, info, warning, error
    """
    logging_options: dict[str, int] = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    loglevel: int = logging_options.get(level, logging.INFO)
    logging.basicConfig(format=format, level=loglevel)

def check_if_point_between(
    start_point: Union[int, float], end_point: Union[int, float], evaluated_point: Union[int, float]
) -> bool:
    """
    Finds if a point is between two other in a circle.

    Args:
        - start_point: The first point
        - end_point: The second point
        - point: The point to check if it is between start_point and end_point

    Returns:
        - True if point is between start_point and end_point, False otherwise
    """

    p1_p2 = math.fmod(end_point - start_point + 360, 360)
    p1_p3 = math.fmod(evaluated_point - start_point + 360, 360)

    if (p1_p2 <= 180) != (p1_p3 > p1_p2):
        return True
    else:
        return False


def get_planet_house(planet_position_degree: Union[int, float], houses_degree_ut_list: list) -> Houses:
    """
    Returns the house in which a planet is located.

    Args:
        - planet_position_degree: The position of the planet in degrees
        - houses_degree_ut_list: A list of the houses in degrees (0-360)

    Returns:
        - The house in which the planet is located
    """

    house = None
    if check_if_point_between(houses_degree_ut_list[0], houses_degree_ut_list[1], planet_position_degree) == True:
        house = "First_House"
    elif check_if_point_between(houses_degree_ut_list[1], houses_degree_ut_list[2], planet_position_degree) == True:
        house = "Second_House"
    elif check_if_point_between(houses_degree_ut_list[2], houses_degree_ut_list[3], planet_position_degree) == True:
        house = "Third_House"
    elif check_if_point_between(houses_degree_ut_list[3], houses_degree_ut_list[4], planet_position_degree) == True:
        house = "Fourth_House"
    elif check_if_point_between(houses_degree_ut_list[4], houses_degree_ut_list[5], planet_position_degree) == True:
        house = "Fifth_House"
    elif check_if_point_between(houses_degree_ut_list[5], houses_degree_ut_list[6], planet_position_degree) == True:
        house = "Sixth_House"
    elif check_if_point_between(houses_degree_ut_list[6], houses_degree_ut_list[7], planet_position_degree) == True:
        house = "Seventh_House"
    elif check_if_point_between(houses_degree_ut_list[7], houses_degree_ut_list[8], planet_position_degree) == True:
        house = "Eighth_House"
    elif check_if_point_between(houses_degree_ut_list[8], houses_degree_ut_list[9], planet_position_degree) == True:
        house = "Ninth_House"
    elif check_if_point_between(houses_degree_ut_list[9], houses_degree_ut_list[10], planet_position_degree) == True:
        house = "Tenth_House"
    elif check_if_point_between(houses_degree_ut_list[10], houses_degree_ut_list[11], planet_position_degree) == True:
        house = "Eleventh_House"
    elif check_if_point_between(houses_degree_ut_list[11], houses_degree_ut_list[0], planet_position_degree) == True:
        house = "Twelfth_House"
    else:
        raise ValueError("Error in house calculation, planet: ", planet_position_degree, "houses: ", houses_degree_ut_list)

    return house

def get_moon_emoji_from_phase_int(phase: int) -> LunarPhaseEmoji:
    """
    Returns the emoji of the moon phase.
    
    Args:
        - phase: The phase of the moon (0-28)
    
    Returns:
        - The emoji of the moon phase
    """
    
    if phase == 1:
        result = "🌑"
    elif phase < 7:
        result = "🌒"
    elif 7 <= phase <= 9:
        result = "🌓"
    elif phase < 14:
        result = "🌔"
    elif phase == 14:
        result = "🌕"
    elif phase < 20:
        result = "🌖"
    elif 20 <= phase <= 22:
        result = "🌗"
    elif phase <= 28:
        result = "🌘"

    else:
        raise KerykeionException(f"Error in moon emoji calculation! Phase: {phase}")

    return result

def get_moon_phase_name_from_phase_int(phase: int) -> LunarPhaseName:
    """
    Returns the name of the moon phase.
    
    Args:
        - phase: The phase of the moon (0-28)
    
    Returns:
        - The name of the moon phase
    """
    
    if phase == 1:
        result = "New Moon"
    elif phase < 7:
        result = "Waxing Crescent"
    elif 7 <= phase <= 9:
        result = "First Quarter"
    elif phase < 14:
        result = "Waxing Gibbous"
    elif phase == 14:
        result = "Full Moon"
    elif phase < 20:
        result = "Waning Gibbous"
    elif 20 <= phase <= 22:
        result = "Last Quarter"
    elif phase <= 28:
        result = "Waning Crescent"

    else:
        raise KerykeionException(f"Error in moon name calculation! Phase: {phase}")
    
    return result


def check_and_adjust_polar_latitude(latitude: float) -> float:
    """
        Utility function to check if the location is in the polar circle.
        If it is, it sets the latitude to 66 or -66 degrees.
    """
    if latitude > 66.0:
        latitude = 66.0
        logging.info("Polar circle override for houses, using 66 degrees")

    elif latitude < -66.0:
        latitude = -66.0
        logging.info("Polar circle override for houses, using -66 degrees")

    return latitude
