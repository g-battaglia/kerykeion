from kerykeion.kr_types import (
    KerykeionPointModel,
    KerykeionException,
    ZodiacSignModel,
    AstrologicalSubjectModel,
    LunarPhaseModel,
    CompositeSubjectModel,
    PlanetReturnModel,
)
from kerykeion.kr_types.kr_literals import LunarPhaseEmoji, LunarPhaseName, PointType, AstrologicalPoint, Houses
from typing import Union, get_args, TYPE_CHECKING
import logging
import math
import re
from datetime import datetime

if TYPE_CHECKING:
    from kerykeion import AstrologicalSubjectFactory


def get_number_from_name(name: AstrologicalPoint) -> int:
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
    elif name == "Ascendant":  # TODO: Is this needed?
        return 9900
    elif name == "Descendant":  # TODO: Is this needed?
        return 9901
    elif name == "Medium_Coeli":  # TODO: Is this needed?
        return 9902
    elif name == "Imum_Coeli":  # TODO: Is this needed?
        return 9903
    else:
        raise KerykeionException(f"Error in getting number from name! Name: {name}")


def get_kerykeion_point_from_degree(
    degree: Union[int, float], name: Union[AstrologicalPoint, Houses], point_type: PointType
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
    # If - single degree is given, convert it to a positive degree
    if degree < 0:
        degree = degree % 360

    if degree >= 360:
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
    start_point: Union[int, float], end_point: Union[int, float], evaluated_point: Union[int, float]
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
        raise KerykeionException(
            f"The angle between start and end point is not allowed to exceed 180°, yet is: {angular_difference}"
        )

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
        result = lunar_phase_names[1]
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


def get_houses_list(
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel]
) -> list[KerykeionPointModel]:
    """
    Return the names of the houses in the order of the houses.
    """
    houses_absolute_position_list = []
    for house in subject.houses_names_list:
        houses_absolute_position_list.append(subject[house.lower()])

    return houses_absolute_position_list


def get_available_astrological_points_list(
    subject: AstrologicalSubjectModel
) -> list[KerykeionPointModel]:
    """
    Return the names of the planets in the order of the planets.
    The names can be used to access the planets from the AstrologicalSubject object with the __getitem__ method or the [] operator.
    """
    planets_absolute_position_list = []
    for planet in subject.active_points:
        planets_absolute_position_list.append(subject[planet.lower()])

    return planets_absolute_position_list


def circular_mean(first_position: Union[int, float], second_position: Union[int, float]) -> float:
    """
    Computes the circular mean of two astrological positions (e.g., house cusps, planets).

    This function ensures that positions crossing 0° Aries (360°) are correctly averaged,
    avoiding errors that occur with simple linear means.

    Args:
        position1 (Union[int, float]): First position in degrees (0-360).
        position2 (Union[int, float]): Second position in degrees (0-360).

    Returns:
        float: The circular mean position in degrees (0-360).
    """
    x = (math.cos(math.radians(first_position)) + math.cos(math.radians(second_position))) / 2
    y = (math.sin(math.radians(first_position)) + math.sin(math.radians(second_position))) / 2
    mean_position = math.degrees(math.atan2(y, x))

    # Ensure the result is within 0-360°
    if mean_position < 0:
        mean_position += 360

    return mean_position


def calculate_moon_phase(moon_abs_pos: float, sun_abs_pos: float) -> LunarPhaseModel:
    """
    Calculate the lunar phase based on the positions of the moon and sun.

    Args:
    - moon_abs_pos (float): The absolute position of the moon.
    - sun_abs_pos (float): The absolute position of the sun.

    Returns:
    - dict: A dictionary containing the lunar phase information.
    """
    # Initialize moon_phase and sun_phase to None in case of an error
    moon_phase, sun_phase = None, None

    # Calculate the anti-clockwise degrees between the sun and moon
    degrees_between = (moon_abs_pos - sun_abs_pos) % 360

    # Calculate the moon phase (1-28) based on the degrees between the sun and moon
    step = 360.0 / 28.0
    moon_phase = int(degrees_between // step) + 1

    # Define the sun phase steps
    sunstep = [
        0, 30, 40, 50, 60, 70, 80, 90, 120, 130, 140, 150, 160, 170, 180,
        210, 220, 230, 240, 250, 260, 270, 300, 310, 320, 330, 340, 350
    ]

    # Calculate the sun phase (1-28) based on the degrees between the sun and moon
    for x in range(len(sunstep)):
        low = sunstep[x]
        high = sunstep[x + 1] if x < len(sunstep) - 1 else 360
        if low <= degrees_between < high:
            sun_phase = x + 1
            break

    # Create a dictionary with the lunar phase information
    lunar_phase_dictionary = {
        "degrees_between_s_m": degrees_between,
        "moon_phase": moon_phase,
        "sun_phase": sun_phase,
        "moon_emoji": get_moon_emoji_from_phase_int(moon_phase),
        "moon_phase_name": get_moon_phase_name_from_phase_int(moon_phase),
    }

    return LunarPhaseModel(**lunar_phase_dictionary)


def circular_sort(degrees: list[Union[int, float]]) -> list[Union[int, float]]:
    """
    Sort a list of degrees in a circular manner, starting from the first element
    and progressing clockwise around the circle.

    Args:
        degrees: A list of numeric values representing degrees

    Returns:
        A list sorted based on circular clockwise progression from the first element

    Raises:
        ValueError: If the list is empty or contains non-numeric values
    """
    # Input validation
    if not degrees:
        raise ValueError("Input list cannot be empty")

    if not all(isinstance(degree, (int, float)) for degree in degrees):
        invalid = next(d for d in degrees if not isinstance(d, (int, float)))
        raise ValueError(f"All elements must be numeric, found: {invalid} of type {type(invalid).__name__}")

    # If list has 0 or 1 element, return it as is
    if len(degrees) <= 1:
        return degrees.copy()

    # Save the first element as the reference
    reference = degrees[0]

    # Define a function to calculate clockwise distance from reference
    def clockwise_distance(angle: Union[int, float]) -> Union[int, float]:
        # Normalize angles to 0-360 range
        ref_norm = reference % 360
        angle_norm = angle % 360

        # Calculate clockwise distance
        distance = angle_norm - ref_norm
        if distance < 0:
            distance += 360

        return distance

    # Sort the rest of the elements based on circular distance
    remaining = degrees[1:]
    sorted_remaining = sorted(remaining, key=clockwise_distance)

    # Return the reference followed by the sorted remaining elements
    return [reference] + sorted_remaining


def inline_css_variables_in_svg(svg_content: str) -> str:
    """
    Process an SVG string to inline all CSS custom properties.

    Args:
        svg_content (str): The original SVG string with CSS variables

    Returns:
        str: The modified SVG with all CSS variables replaced by their values
             and all style blocks removed
    """
    # Find and extract CSS custom properties from style tags
    css_variable_map = {}
    style_tag_pattern = re.compile(r"<style.*?>(.*?)</style>", re.DOTALL)
    style_blocks = style_tag_pattern.findall(svg_content)

    # Parse all CSS custom properties from style blocks
    for style_block in style_blocks:
        # Match patterns like --color-primary: #ff0000;
        css_variable_pattern = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;]+);")
        for match in css_variable_pattern.finditer(style_block):
            variable_name = match.group(1)
            variable_value = match.group(2).strip()
            css_variable_map[f"--{variable_name}"] = variable_value

    # Remove all style blocks from the SVG
    svg_without_style_blocks = style_tag_pattern.sub("", svg_content)

    # Function to replace var() references with their actual values
    def replace_css_variable_reference(match):
        variable_name = match.group(1).strip()
        fallback_value = match.group(2) if match.group(2) else None

        if variable_name in css_variable_map:
            return css_variable_map[variable_name]
        elif fallback_value:
            return fallback_value.strip(", ")
        else:
            return ""  # If variable not found and no fallback provided

    # Pattern to match var(--name) or var(--name, fallback)
    variable_usage_pattern = re.compile(r"var\(\s*(--([\w-]+))\s*(,\s*([^)]+))?\s*\)")

    # Repeatedly replace all var() references until none remain
    # This handles nested variables or variables that reference other variables
    processed_svg = svg_without_style_blocks
    while variable_usage_pattern.search(processed_svg):
        processed_svg = variable_usage_pattern.sub(lambda m: replace_css_variable_reference(m), processed_svg)

    return processed_svg


def datetime_to_julian(dt: datetime) -> float:
    """
    Converts a Python datetime object to Julian day.

    Args:
        dt: A datetime object

    Returns:
        float: The corresponding Julian day (JD)
    """
    # Extract year, month and day
    year = dt.year
    month = dt.month
    day = dt.day

    # Adjust month and year according to the conversion formula
    if month <= 2:
        year -= 1
        month += 12

    # Calculate century and year in century
    a = year // 100
    b = 2 - a + (a // 4)

    # Calculate the Julian day
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5

    # Add the time portion
    hour = dt.hour
    minute = dt.minute
    second = dt.second
    microsecond = dt.microsecond

    jd += (hour + minute / 60 + second / 3600 + microsecond / 3600000000) / 24

    return jd


def julian_to_datetime(jd):
    """
    Converts a Julian day to a Python datetime object.

    Args:
        jd: Julian day number (float)

    Returns:
        datetime: The corresponding datetime object
    """
    # Add 0.5 to the Julian day to adjust for noon-based Julian day
    jd_plus = jd + 0.5

    # Integer and fractional parts
    Z = int(jd_plus)
    F = jd_plus - Z

    # Calculate alpha
    if Z < 2299161:
        A = Z  # Julian calendar
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)  # Gregorian calendar

    # Calculate B
    B = A + 1524

    # Calculate C
    C = int((B - 122.1) / 365.25)

    # Calculate D
    D = int(365.25 * C)

    # Calculate E
    E = int((B - D) / 30.6001)

    # Calculate day and month
    day = B - D - int(30.6001 * E) + F

    # Integer part of day
    day_int = int(day)

    # Fractional part converted to hours, minutes, seconds, microseconds
    day_frac = day - day_int
    hours = int(day_frac * 24)
    minutes = int((day_frac * 24 - hours) * 60)
    seconds = int((day_frac * 24 * 60 - hours * 60 - minutes) * 60)
    microseconds = int(((day_frac * 24 * 60 - hours * 60 - minutes) * 60 - seconds) * 1000000)

    # Calculate month
    if E < 14:
        month = E - 1
    else:
        month = E - 13

    # Calculate year
    if month > 2:
        year = C - 4716
    else:
        year = C - 4715

    # Create and return datetime object
    return datetime(year, month, day_int, hours, minutes, seconds, microseconds)


def get_house_name(house_number: int) -> Houses:
    """
    Returns the name of the house based on its number.

    Args:
        house_number: House number (1-12)

    Returns:
        Name of the house
    """
    house_names: dict[int, Houses] = {
        1: "First_House",
        2: "Second_House",
        3: "Third_House",
        4: "Fourth_House",
        5: "Fifth_House",
        6: "Sixth_House",
        7: "Seventh_House",
        8: "Eighth_House",
        9: "Ninth_House",
        10: "Tenth_House",
        11: "Eleventh_House",
        12: "Twelfth_House",
    }

    name = house_names.get(house_number, None)
    if name is None:
        raise ValueError(f"Invalid house number: {house_number}")

    return name


def get_house_number(house_name: Houses) -> int:
    """
    Returns the number of the house based on its name.

    Args:
        house_name: Name of the house

    Returns:
        House number (1-12)
    """
    house_numbers: dict[Houses, int] = {
        "First_House": 1,
        "Second_House": 2,
        "Third_House": 3,
        "Fourth_House": 4,
        "Fifth_House": 5,
        "Sixth_House": 6,
        "Seventh_House": 7,
        "Eighth_House": 8,
        "Ninth_House": 9,
        "Tenth_House": 10,
        "Eleventh_House": 11,
        "Twelfth_House": 12,
    }

    number = house_numbers.get(house_name, None)
    if number is None:
        raise ValueError(f"Invalid house name: {house_name}")

    return number


def find_common_active_points(first_points: list[AstrologicalPoint], second_points: list[AstrologicalPoint]) -> list[AstrologicalPoint]:
    """
        Find the common astrological points between those available in the subject and those requested.

        Args:
            first_points: List of points available in the astrological subject
            second_points: List of points requested by the user

        Returns:
            List containing only the requested points that are also available in the subject
    """
    common_points: list[AstrologicalPoint]
    common_points = [point for point in second_points if point in first_points]

    ignored_points = set(second_points) - set(common_points)

    return common_points
