from kerykeion.kr_types import KerykeionPointModel, KerykeionException, ZodiacSignModel, AstrologicalSubjectModel
from kerykeion.kr_types.kr_literals import LunarPhaseEmoji, LunarPhaseName, PointType, Planet, Houses, AxialCusps
from typing import Union, get_args, TYPE_CHECKING
import logging
import math

if TYPE_CHECKING:
    from kerykeion import AstrologicalSubject


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
    # Note: Swiss ephemeris library has no constants for south nodes. We're using integers >= 1000 for them.
    elif name == "Mean_South_Node":
        return 1000
    elif name == "True_South_Node":
        return 1100
    elif name == "Chiron":
        return 15
    elif name == "Mean_Lilith":
        return 12
    elif name == "Ascendant": # TODO: Is this needed?
        return 9900
    elif name == "Descendant": # TODO: Is this needed?
        return 9901
    elif name == "Medium_Coeli": # TODO: Is this needed?
        return 9902
    elif name == "Imum_Coeli": # TODO: Is this needed?
        return 9903
    else:
        raise KerykeionException(f"Error in getting number from name! Name: {name}")


def get_kerykeion_point_from_degree(
    degree: Union[int, float], name: Union[Planet, Houses, AxialCusps], point_type: PointType
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
        "critical": logging.CRITICAL,
    }
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    loglevel: int = logging_options.get(level, logging.INFO)
    logging.basicConfig(format=format, level=loglevel)


def is_point_between(
    start_point: Union[int, float],
    end_point: Union[int, float],
    evaluated_point: Union[int, float]
) -> bool:
    """
    Determines if a point is between two others on a circle, with additional rules:
    - If evaluated_point == start_point, it is considered between.
    - If evaluated_point == end_point, it is NOT considered between.
    - The range between start_point and end_point must not exceed 180°.

    Args:
        - start_point: The first point on the circle.
        - end_point: The second point on the circle.
        - evaluated_point: The point to check.

    Returns:
        - True if evaluated_point is between start_point and end_point, False otherwise.
    """

    # Normalize angles to [0, 360)
    start_point = start_point % 360
    end_point = end_point % 360
    evaluated_point = evaluated_point % 360

    # Compute angular difference
    angular_difference = math.fmod(end_point - start_point + 360, 360)

    # Ensure the range is not greater than 180°. Otherwise, it is not truly defined what
    # being located in between two points on a circle actually means.
    if angular_difference > 180:
        raise KerykeionException(f"The angle between start and end point is not allowed to exceed 180°, yet is: {angular_difference}")

    # Handle explicitly when evaluated_point == start_point. Note: It may happen for mathematical
    # reasons that evaluated_point and start_point deviate very slightly from each other, but
    # should really be same value. This case is captured later below by the term 0 <= p1_p3.
    if evaluated_point == start_point:
        return True

    # Handle explicitly when evaluated_point == end_point
    if evaluated_point == end_point:
        return False

    # Compute angular differences for evaluation
    p1_p3 = math.fmod(evaluated_point - start_point + 360, 360)

    # Check if point lies in the interval
    return (0 <= p1_p3) and (p1_p3 < angular_difference)



def get_planet_house(planet_position_degree: Union[int, float], houses_degree_ut_list: list) -> Houses:
    """
    Determines the house in which a planet is located based on its position in degrees.

    Args:
        planet_position_degree (Union[int, float]): The position of the planet in degrees.
        houses_degree_ut_list (list): A list of the houses in degrees (0-360).

    Returns:
        str: The house in which the planet is located.

    Raises:
        ValueError: If the planet's position does not fall within any house range.
    """

    house_names = get_args(Houses)

    # Iterate through the house boundaries to find the correct house
    for i in range(len(house_names)):
        start_degree = houses_degree_ut_list[i]
        end_degree = houses_degree_ut_list[(i + 1) % len(houses_degree_ut_list)]

        if is_point_between(start_degree, end_degree, planet_position_degree):
            return house_names[i]

    # If no house is found, raise an error
    raise ValueError(f"Error in house calculation, planet: {planet_position_degree}, houses: {houses_degree_ut_list}")


def get_moon_emoji_from_phase_int(phase: int) -> LunarPhaseEmoji:
    """
    Returns the emoji of the moon phase.

    Args:
        - phase: The phase of the moon (0-28)

    Returns:
        - The emoji of the moon phase
    """

    lunar_phase_emojis = get_args(LunarPhaseEmoji)

    if phase == 1:
        result = lunar_phase_emojis[0]
    elif phase < 7:
        result = lunar_phase_emojis[1]
    elif 7 <= phase <= 9:
        result = lunar_phase_emojis[2]
    elif phase < 14:
        result = lunar_phase_emojis[3]
    elif phase == 14:
        result = lunar_phase_emojis[4]
    elif phase < 20:
        result = lunar_phase_emojis[5]
    elif 20 <= phase <= 22:
        result = lunar_phase_emojis[6]
    elif phase <= 28:
        result = lunar_phase_emojis[7]

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
    lunar_phase_names = get_args(LunarPhaseName)


    if phase == 1:
        result = lunar_phase_names[0]
    elif phase < 7:
        result =  lunar_phase_names[1]
    elif 7 <= phase <= 9:
        result = lunar_phase_names[2]
    elif phase < 14:
        result = lunar_phase_names[3]
    elif phase == 14:
        result = lunar_phase_names[4]
    elif phase < 20:
        result = lunar_phase_names[5]
    elif 20 <= phase <= 22:
        result = lunar_phase_names[6]
    elif phase <= 28:
        result = lunar_phase_names[7]

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


def get_houses_list(subject: Union["AstrologicalSubject", AstrologicalSubjectModel]) -> list[KerykeionPointModel]:
    """
    Return the names of the houses in the order of the houses.
    """
    houses_absolute_position_list = []
    for house in subject.houses_names_list:
            houses_absolute_position_list.append(subject[house.lower()])

    return houses_absolute_position_list


def get_available_astrological_points_list(subject: Union["AstrologicalSubject", AstrologicalSubjectModel]) -> list[KerykeionPointModel]:
    """
    Return the names of the planets in the order of the planets.
    The names can be used to access the planets from the AstrologicalSubject object with the __getitem__ method or the [] operator.
    """
    planets_absolute_position_list = []
    for planet in subject.planets_names_list:
            planets_absolute_position_list.append(subject[planet.lower()])

    for axis in subject.axial_cusps_names_list:
        planets_absolute_position_list.append(subject[axis.lower()])

    return planets_absolute_position_list
