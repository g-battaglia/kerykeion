"""
Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from kerykeion.schemas import (
    KerykeionPointModel,
    KerykeionException,
    ZodiacSignModel,
    AstrologicalSubjectModel,
    LunarPhaseModel,
    CompositeSubjectModel,
    PlanetReturnModel,
)
from kerykeion.schemas.kr_literals import LunarPhaseEmoji, LunarPhaseName, PointType, AstrologicalPoint, Houses
from typing import Union, Optional, get_args, TYPE_CHECKING
import logging
import math
import re
from datetime import datetime

if TYPE_CHECKING:
    pass


def get_number_from_name(name: AstrologicalPoint) -> int:
    """
    Convert an astrological point name to its corresponding numerical identifier.

    Args:
        name: The name of the astrological point

    Returns:
        The numerical identifier used in Swiss Ephemeris calculations

    Raises:
        KerykeionException: If the name is not recognized
    """

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
    elif name == "Mean_North_Lunar_Node":
        return 10
    elif name == "True_North_Lunar_Node":
        return 11
    # Note: Swiss ephemeris library has no constants for south nodes. We're using integers >= 1000 for them.
    elif name == "Mean_South_Lunar_Node":
        return 1000
    elif name == "True_South_Lunar_Node":
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
    degree: Union[int, float], name: Union[AstrologicalPoint, Houses], point_type: PointType, speed: Optional[float] = None, declination: Optional[float] = None
) -> KerykeionPointModel:
    """
    Create a KerykeionPointModel from a degree position.

    Args:
        degree: The degree position (0-360, negative values are converted to positive)
        name: The name of the celestial point or house
        point_type: The type classification of the point
        speed: The velocity/speed of the celestial point in degrees per day (optional)
        declination: The declination of the celestial point in degrees (optional)

    Returns:
        A KerykeionPointModel with calculated zodiac sign, position, and properties

    Raises:
        KerykeionException: If the degree is >= 360 after normalization
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
        speed=speed,
        declination=declination,
    )


def setup_logging(level: str) -> None:
    """
    Configure logging for the application.

    Args:
        level: Log level as string (debug, info, warning, error, critical)
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
    Determine if a point lies between two other points on a circle.

    Special rules:
    - If evaluated_point equals start_point, returns True
    - If evaluated_point equals end_point, returns False
    - The arc between start_point and end_point must not exceed 180°

    Args:
        start_point: The starting point on the circle
        end_point: The ending point on the circle
        evaluated_point: The point to evaluate

    Returns:
        True if evaluated_point is between start_point and end_point, False otherwise

    Raises:
        KerykeionException: If the angular difference exceeds 180°
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
    Determine which house contains a planet based on its degree position.

    Args:
        planet_position_degree: The planet's position in degrees (0-360)
        houses_degree_ut_list: List of house cusp degrees

    Returns:
        The house name containing the planet

    Raises:
        ValueError: If the planet's position doesn't fall within any house range
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
    Get the emoji representation of a lunar phase.

    Args:
        phase: The lunar phase number (0-28)

    Returns:
        The corresponding emoji for the lunar phase

    Raises:
        KerykeionException: If phase is outside valid range
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
    Get the name of a lunar phase from its numerical value.

    Args:
        phase: The lunar phase number (0-28)

    Returns:
        The corresponding name for the lunar phase

    Raises:
        KerykeionException: If phase is outside valid range
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
    Adjust latitude values for polar regions to prevent calculation errors.

    Latitudes beyond ±66° are clamped to ±66° for house calculations.

    Args:
        latitude: The original latitude value

    Returns:
        The adjusted latitude value, clamped between -66° and 66°
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
    Get a list of house objects in order from the subject.

    Args:
        subject: The astrological subject containing house data

    Returns:
        List of KerykeionPointModel objects representing the houses
    """
    houses_absolute_position_list = []
    for house in subject.houses_names_list:
        houses_absolute_position_list.append(subject[house.lower()])

    return houses_absolute_position_list


def get_available_astrological_points_list(
    subject: AstrologicalSubjectModel
) -> list[KerykeionPointModel]:
    """
    Get a list of active astrological point objects from the subject.

    Args:
        subject: The astrological subject containing point data

    Returns:
        List of KerykeionPointModel objects for all active points
    """
    planets_absolute_position_list = []
    for planet in subject.active_points:
        planets_absolute_position_list.append(subject[planet.lower()])

    return planets_absolute_position_list


def circular_mean(first_position: Union[int, float], second_position: Union[int, float]) -> float:
    """
    Calculate the circular mean of two angular positions.

    This method correctly handles positions that cross the 0°/360° boundary,
    avoiding errors that occur with simple arithmetic means.

    Args:
        first_position: First angular position in degrees (0-360)
        second_position: Second angular position in degrees (0-360)

    Returns:
        The circular mean position in degrees (0-360)
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
    Calculate lunar phase information from Sun and Moon positions.

    Args:
        moon_abs_pos: Absolute position of the Moon in degrees
        sun_abs_pos: Absolute position of the Sun in degrees

    Returns:
        LunarPhaseModel containing phase data, emoji, and name
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
    Sort degrees in circular clockwise progression starting from the first element.

    Args:
        degrees: List of numeric degree values

    Returns:
        List sorted by clockwise distance from the first element

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
    Replace CSS custom properties (variables) with their values in SVG content.

    Extracts CSS variables from style blocks, replaces var() references with actual values,
    and removes all style blocks from the SVG.

    Args:
        svg_content: The original SVG string with CSS variables

    Returns:
        Modified SVG with CSS variables inlined and style blocks removed
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
        """
        Replace CSS variable references with their actual values.

        Args:
            match: Regular expression match object containing variable name and optional fallback.

        Returns:
            str: The resolved CSS variable value or fallback value.
        """
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
    Convert a Python datetime object to Julian Day Number.

    Args:
        dt: The datetime object to convert

    Returns:
        The corresponding Julian Day Number (JD) as a float
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
    Convert a Julian Day Number to a Python datetime object.

    Args:
        jd: Julian Day Number as a float

    Returns:
        The corresponding datetime object
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
    Convert a house number to its corresponding house name.

    Args:
        house_number: House number (1-12)

    Returns:
        The house name

    Raises:
        ValueError: If house_number is not in range 1-12
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
    Convert a house name to its corresponding house number.

    Args:
        house_name: The house name

    Returns:
        House number (1-12)

    Raises:
        ValueError: If house_name is not recognized
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
    Find astrological points that appear in both input lists.

    Args:
        first_points: First list of astrological points
        second_points: Second list of astrological points

    Returns:
        List of points common to both input lists (without duplicates)
    """
    common_points = list(set(first_points) & set(second_points))

    return common_points


def distribute_percentages_to_100(values: dict[str, float]) -> dict[str, int]:
    """
    Distribute percentages so they sum to exactly 100.

    This function uses a largest remainder method to ensure that
    the percentage total equals 100 even after rounding.

    Args:
        values: Dictionary with keys and their raw percentage values

    Returns:
        Dictionary with the same keys and integer percentages that sum to 100
    """
    if not values:
        return {}

    total = sum(values.values())
    if total == 0:
        return {key: 0 for key in values.keys()}

    # Calculate base percentages
    percentages = {key: value * 100 / total for key, value in values.items()}

    # Get integer parts and remainders
    integer_parts = {key: int(value) for key, value in percentages.items()}
    remainders = {key: percentages[key] - integer_parts[key] for key in percentages.keys()}

    # Calculate how many we need to add to reach 100
    current_sum = sum(integer_parts.values())
    needed = 100 - current_sum

    # Sort by remainder (largest first) and add 1 to the largest remainders
    sorted_by_remainder = sorted(remainders.items(), key=lambda x: x[1], reverse=True)

    result = integer_parts.copy()
    for i in range(needed):
        if i < len(sorted_by_remainder):
            key = sorted_by_remainder[i][0]
            result[key] += 1

    return result
