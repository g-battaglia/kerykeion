"""
Kerykeion Utilities Module

This module provides utility functions for astrological calculations including:
- Zodiac position conversions and validations
- House position determinations
- Lunar phase calculations
- Angular mathematics (circular mean, sorting)
- Date/time conversions (Julian Day)
- SVG processing utilities

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
    ZodiacType,
)
from kerykeion.schemas.kr_literals import (
    LunarPhaseEmoji,
    LunarPhaseName,
    PointType,
    AstrologicalPoint,
    Houses,
)
from typing import Union, Optional, get_args, cast
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, basicConfig, getLogger
import math
import re
from datetime import datetime


logger = getLogger(__name__)


# =============================================================================
# CONSTANTS AND MAPPINGS
# =============================================================================

# Mapping of astrological point names to Swiss Ephemeris IDs
_POINT_NUMBER_MAP: dict[str, int] = {
    "Sun": 0,
    "Moon": 1,
    "Mercury": 2,
    "Venus": 3,
    "Mars": 4,
    "Jupiter": 5,
    "Saturn": 6,
    "Uranus": 7,
    "Neptune": 8,
    "Pluto": 9,
    "Mean_North_Lunar_Node": 10,
    "True_North_Lunar_Node": 11,
    # Swiss Ephemeris has no dedicated IDs for the south nodes; we reserve high values.
    "Mean_South_Lunar_Node": 1000,
    "True_South_Lunar_Node": 1100,
    "Chiron": 15,
    "Mean_Lilith": 12,
    "Ascendant": 9900,
    "Descendant": 9901,
    "Medium_Coeli": 9902,
    "Imum_Coeli": 9903,
}

# Zodiac sign properties lookup table
_ZODIAC_SIGNS: dict[int, ZodiacSignModel] = {
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

# House name mappings
_HOUSE_NAMES: dict[int, Houses] = {
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

_HOUSE_NUMBERS: dict[Houses, int] = {v: k for k, v in _HOUSE_NAMES.items()}


# =============================================================================
# LOGGING UTILITIES
# =============================================================================


def setup_logging(level: str) -> None:
    """
    Configure the root logger for consistent formatting across the library.

    Args:
        level: Logging level as string (debug, info, warning, error, critical).
               Case-insensitive. Defaults to INFO if invalid.
    """
    normalized_level = (level or "").strip().lower()
    level_map: dict[str, int] = {
        "debug": DEBUG,
        "info": INFO,
        "warning": WARNING,
        "error": ERROR,
        "critical": CRITICAL,
    }

    selected_level = level_map.get(normalized_level, INFO)
    basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=selected_level,
    )
    logger.setLevel(selected_level)


# =============================================================================
# ZODIAC AND POINT UTILITIES
# =============================================================================


def normalize_zodiac_type(value: str) -> ZodiacType:
    """
    Normalize a zodiac type string to its canonical representation.

    Handles case-insensitive matching and legacy formats like "tropic" or "Tropic",
    automatically converting them to the canonical forms "Tropical" or "Sidereal".

    Args:
        value: Input zodiac type string (case-insensitive).

    Returns:
        ZodiacType: Canonical zodiac type ("Tropical" or "Sidereal").

    Raises:
        ValueError: If `value` is not a recognized zodiac type.

    Examples:
        >>> normalize_zodiac_type("tropical")
        'Tropical'
        >>> normalize_zodiac_type("Tropic")
        'Tropical'
        >>> normalize_zodiac_type("SIDEREAL")
        'Sidereal'
    """
    value_lower = value.lower()

    if value_lower in ("tropical", "tropic"):
        return cast(ZodiacType, "Tropical")
    elif value_lower == "sidereal":
        return cast(ZodiacType, "Sidereal")
    else:
        raise ValueError(
            "'{value}' is not a valid zodiac type. Accepted values are: Tropical, Sidereal "
            "(case-insensitive, 'tropic' also accepted as legacy).".format(value=value)
        )


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
    try:
        return _POINT_NUMBER_MAP[str(name)]
    except KeyError as exc:
        raise KerykeionException(f"Error in getting number from name! Name: {name}") from exc


def get_kerykeion_point_from_degree(
    degree: Union[int, float],
    name: Union[AstrologicalPoint, Houses],
    point_type: PointType,
    speed: Optional[float] = None,
    declination: Optional[float] = None,
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
    # Normalize negative degrees
    if degree < 0:
        degree = degree % 360

    if degree >= 360:
        raise KerykeionException(f"Error in calculating positions! Degrees: {degree}")

    sign_index = int(degree // 30)
    sign_degree = degree % 30
    zodiac_sign = _ZODIAC_SIGNS[sign_index]

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


# =============================================================================
# HOUSE UTILITIES
# =============================================================================


def is_point_between(
    start_angle: Union[int, float], end_angle: Union[int, float], candidate: Union[int, float]
) -> bool:
    """
    Check if a candidate angle lies on the clockwise arc from start to end angle.

    Args:
        start_angle: Starting angle in degrees
        end_angle: Ending angle in degrees
        candidate: Angle to check

    Returns:
        True if candidate is on the clockwise arc from start to end

    Raises:
        KerykeionException: If the arc exceeds 180°
    """
    normalize = lambda value: value % 360

    start = normalize(start_angle)
    end = normalize(end_angle)
    target = normalize(candidate)
    span = (end - start) % 360

    if span > 180:
        raise KerykeionException(f"The angle between start and end point is not allowed to exceed 180°, yet is: {span}")
    if target == start:
        return True
    if target == end:
        return False
    distance_from_start = (target - start) % 360
    return distance_from_start < span


def get_planet_house(planet_degree: Union[int, float], houses_degree_ut_list: list) -> Houses:
    """
    Determine which house contains a planet based on its degree position.

    Args:
        planet_degree: The planet's position in degrees (0-360)
        houses_degree_ut_list: List of house cusp degrees

    Returns:
        The house name containing the planet

    Raises:
        ValueError: If the planet's position doesn't fall within any house range
    """
    house_names = get_args(Houses)

    for i in range(len(house_names)):
        start_degree = houses_degree_ut_list[i]
        end_degree = houses_degree_ut_list[(i + 1) % len(houses_degree_ut_list)]

        if is_point_between(start_degree, end_degree, planet_degree):
            return house_names[i]

    raise ValueError(f"Error in house calculation, planet: {planet_degree}, houses: {houses_degree_ut_list}")


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
    name = _HOUSE_NAMES.get(house_number, None)
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
    number = _HOUSE_NUMBERS.get(house_name, None)
    if number is None:
        raise ValueError(f"Invalid house name: {house_name}")
    return number


def get_houses_list(
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
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


def get_available_astrological_points_list(subject: AstrologicalSubjectModel) -> list[KerykeionPointModel]:
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


def find_common_active_points(
    first_points: list[AstrologicalPoint], second_points: list[AstrologicalPoint]
) -> list[AstrologicalPoint]:
    """
    Find astrological points that appear in both input lists.

    Args:
        first_points: First list of astrological points
        second_points: Second list of astrological points

    Returns:
        List of points common to both input lists (without duplicates)
    """
    return list(set(first_points) & set(second_points))


# =============================================================================
# LUNAR PHASE UTILITIES
# =============================================================================


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
        logger.info("Latitude capped at 66° to keep house calculations stable.")

    elif latitude < -66.0:
        latitude = -66.0
        logger.info("Latitude capped at -66° to keep house calculations stable.")

    return latitude


# =============================================================================
# ANGULAR MATHEMATICS
# =============================================================================


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

    if mean_position < 0:
        mean_position += 360

    return mean_position


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
    if not degrees:
        raise ValueError("Input list cannot be empty")

    if not all(isinstance(degree, (int, float)) for degree in degrees):
        invalid = next(d for d in degrees if not isinstance(d, (int, float)))
        raise ValueError(f"All elements must be numeric, found: {invalid} of type {type(invalid).__name__}")

    if len(degrees) <= 1:
        return degrees.copy()

    reference = degrees[0]

    def clockwise_distance(angle: Union[int, float]) -> Union[int, float]:
        ref_norm = reference % 360
        angle_norm = angle % 360
        distance = angle_norm - ref_norm
        if distance < 0:
            distance += 360
        return distance

    remaining = degrees[1:]
    sorted_remaining = sorted(remaining, key=clockwise_distance)

    return [reference] + sorted_remaining


# =============================================================================
# DATE/TIME UTILITIES
# =============================================================================


def datetime_to_julian(dt: datetime) -> float:
    """
    Convert a Python datetime object to Julian Day Number.

    Args:
        dt: The datetime object to convert

    Returns:
        The corresponding Julian Day Number (JD) as a float
    """
    year = dt.year
    month = dt.month
    day = dt.day

    if month <= 2:
        year -= 1
        month += 12

    a = year // 100
    b = 2 - a + (a // 4)

    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5

    hour = dt.hour
    minute = dt.minute
    second = dt.second
    microsecond = dt.microsecond

    jd += (hour + minute / 60 + second / 3600 + microsecond / 3600000000) / 24

    return jd


def julian_to_datetime(jd: float) -> datetime:
    """
    Convert a Julian Day Number to a Python datetime object.

    Args:
        jd: Julian Day Number as a float

    Returns:
        The corresponding datetime object
    """
    jd_plus = jd + 0.5

    Z = int(jd_plus)
    F = jd_plus - Z

    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)

    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day = B - D - int(30.6001 * E) + F
    day_int = int(day)

    day_frac = day - day_int
    hours = int(day_frac * 24)
    minutes = int((day_frac * 24 - hours) * 60)
    seconds = int((day_frac * 24 * 60 - hours * 60 - minutes) * 60)
    microseconds = int(((day_frac * 24 * 60 - hours * 60 - minutes) * 60 - seconds) * 1000000)

    if E < 14:
        month = E - 1
    else:
        month = E - 13

    if month > 2:
        year = C - 4716
    else:
        year = C - 4715

    return datetime(year, month, day_int, hours, minutes, seconds, microseconds)


# =============================================================================
# SVG PROCESSING UTILITIES
# =============================================================================


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
    css_variable_map = {}
    style_tag_pattern = re.compile(r"<style.*?>(.*?)</style>", re.DOTALL)
    style_blocks = style_tag_pattern.findall(svg_content)

    for style_block in style_blocks:
        css_variable_pattern = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;]+);")
        for match in css_variable_pattern.finditer(style_block):
            variable_name = match.group(1)
            variable_value = match.group(2).strip()
            css_variable_map[f"--{variable_name}"] = variable_value

    svg_without_style_blocks = style_tag_pattern.sub("", svg_content)

    def replace_css_variable_reference(match):
        variable_name = match.group(1).strip()
        fallback_value = match.group(3) if match.group(3) else None

        if variable_name in css_variable_map:
            return css_variable_map[variable_name]
        elif fallback_value:
            return fallback_value.strip()
        else:
            return ""

    variable_usage_pattern = re.compile(r"var\(\s*(--[\w-]+)\s*(,\s*([^)]+))?\s*\)")

    processed_svg = svg_without_style_blocks
    while variable_usage_pattern.search(processed_svg):
        processed_svg = variable_usage_pattern.sub(lambda m: replace_css_variable_reference(m), processed_svg)

    return processed_svg


# =============================================================================
# STATISTICAL UTILITIES
# =============================================================================


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

    percentages = {key: value * 100 / total for key, value in values.items()}
    integer_parts = {key: int(value) for key, value in percentages.items()}
    remainders = {key: percentages[key] - integer_parts[key] for key in percentages.keys()}

    current_sum = sum(integer_parts.values())
    needed = 100 - current_sum

    sorted_by_remainder = sorted(remainders.items(), key=lambda x: x[1], reverse=True)

    result = integer_parts.copy()
    for i in range(needed):
        if i < len(sorted_by_remainder):
            key = sorted_by_remainder[i][0]
            result[key] += 1

    return result


def calculate_moon_phase(moon_abs_pos: float, sun_abs_pos: float) -> LunarPhaseModel:
    """
    Calculate lunar phase information from Sun and Moon positions.

    Args:
        moon_abs_pos: Absolute position of the Moon in degrees
        sun_abs_pos: Absolute position of the Sun in degrees

    Returns:
        LunarPhaseModel containing phase data, emoji, and name
    """
    # Calculate the anti-clockwise degrees between the sun and moon
    degrees_between = (moon_abs_pos - sun_abs_pos) % 360

    # Calculate the moon phase (1-28) based on the degrees between the sun and moon
    step = 360.0 / 28.0
    moon_phase = int(degrees_between // step) + 1

    return LunarPhaseModel(
        degrees_between_s_m=degrees_between,
        moon_phase=moon_phase,
        moon_emoji=get_moon_emoji_from_phase_int(moon_phase),
        moon_phase_name=get_moon_phase_name_from_phase_int(moon_phase),
    )
