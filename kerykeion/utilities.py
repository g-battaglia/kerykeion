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
from kerykeion.settings.config_constants import POINT_NUMBER_MAP as _POINT_NUMBER_MAP_IMPORT
from typing import Union, Optional, get_args, cast
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL, basicConfig, getLogger
import math
import re
from datetime import datetime, timedelta, timezone


logger = getLogger(__name__)


# Pre-compiled regex patterns (invariant, compiled once at module load)
_CSS_VARIABLE_PATTERN = re.compile(r"--([a-zA-Z0-9_-]+)\s*:\s*([^;]+);")

# Cached get_args() tuples (type introspection is expensive, values are invariant)
_HOUSE_NAMES_TUPLE: tuple[Houses, ...] = get_args(Houses)
_LUNAR_PHASE_EMOJIS: tuple[LunarPhaseEmoji, ...] = get_args(LunarPhaseEmoji)
_LUNAR_PHASE_NAMES: tuple[LunarPhaseName, ...] = get_args(LunarPhaseName)


# =============================================================================
# CONSTANTS AND MAPPINGS
# =============================================================================

# Maximum latitude for reliable house calculations
_POLAR_LATITUDE_LIMIT = 66.0

# Mapping of astrological point names to Swiss Ephemeris IDs.
# Canonical definition lives in `kerykeion.settings.config_constants.POINT_NUMBER_MAP`
# (shared with STANDARD_PLANETS in astrological_subject_factory). The historical
# module-private alias is preserved here for backward compatibility.
_POINT_NUMBER_MAP: dict[str, int] = _POINT_NUMBER_MAP_IMPORT

HOUSE_FIELD_NAMES: tuple[str, ...] = (
    "first_house", "second_house", "third_house", "fourth_house",
    "fifth_house", "sixth_house", "seventh_house", "eighth_house",
    "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
)

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
            f"'{value}' is not a valid zodiac type. Accepted values are: Tropical, Sidereal "
            "(case-insensitive, 'tropic' also accepted as legacy)."
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
    magnitude: Optional[float] = None,
    ecliptic_latitude: Optional[float] = None,
) -> KerykeionPointModel:
    """
    Create a KerykeionPointModel from a degree position.

    Args:
        degree: The degree position (0-360, negative values are converted to positive)
        name: The name of the celestial point or house
        point_type: The type classification of the point
        speed: The velocity/speed of the celestial point in degrees per day (optional)
        declination: The declination of the celestial point in degrees (optional)
        magnitude: The apparent visual magnitude for fixed stars (optional)
        ecliptic_latitude: The ecliptic latitude of the body in degrees (optional)

    Returns:
        A KerykeionPointModel with calculated zodiac sign, position, and properties

    Raises:
        KerykeionException: If degree is non-finite (NaN or infinite). Any finite
            degree (negative or >= 360) is wrapped into [0, 360), not rejected.
    """
    # A non-finite degree is a genuine calculation failure — fail loudly.
    if not math.isfinite(degree):
        raise KerykeionException(f"Error in calculating positions! Degrees: {degree}")

    # Normalize any finite degree into [0, 360). Modulo alone handles negatives
    # and values >= 360 (e.g. a positive exactly 360.0 from swe_degnorm rounding
    # on a non-pre-normalized point — axis/fixed-star/cusp — which used to abort
    # subject creation), but float64 `%` can itself return exactly 360.0 for a
    # tiny-negative input ((-1e-14) % 360 == 360.0), so fold that edge back.
    degree = degree % 360.0
    if degree >= 360.0:
        degree -= 360.0

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
        magnitude=magnitude,
        ecliptic_latitude=ecliptic_latitude,
    )


# =============================================================================
# HOUSE UTILITIES
# =============================================================================


def is_point_between(
    start_angle: Union[int, float],
    end_angle: Union[int, float],
    candidate: Union[int, float],
    *,
    allow_reflex: bool = False,
) -> bool:
    """
    Check if a candidate angle lies on the clockwise arc from start to end angle.

    The arc is start-inclusive and end-exclusive: a candidate exactly on
    ``start`` belongs to the arc, one exactly on ``end`` does not.

    Args:
        start_angle: Starting angle in degrees
        end_angle: Ending angle in degrees
        candidate: Angle to check
        allow_reflex: When False (default) a span exceeding 180° is rejected with
            a ``KerykeionException`` (quadrant house systems never produce one).
            Set True to accept reflex arcs (> 180°), as needed by non-quadrant
            house systems (e.g. 'H' Horizon) whose cusps can span more than 180°.

    Returns:
        True if candidate is on the clockwise arc from start to end

    Raises:
        KerykeionException: If the arc exceeds 180° and ``allow_reflex`` is False
    """
    start = start_angle % 360
    end = end_angle % 360
    target = candidate % 360
    span = (end - start) % 360

    if span > 180 and not allow_reflex:
        raise KerykeionException(f"The angle between start and end point is not allowed to exceed 180°, yet is: {span}")
    if math.isclose(target, start, rel_tol=1e-9, abs_tol=1e-12):
        return True
    if math.isclose(target, end, rel_tol=1e-9, abs_tol=1e-12):
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
    n = len(_HOUSE_NAMES_TUPLE)
    # A house is the arc from its own cusp to the NEXT cusp, but the cusps do
    # not always run in increasing longitude: some systems return them in
    # decreasing (clockwise) order — notably 'H' Horizon near the equator and
    # 'T' Polich-Page at high latitude — and quadrant systems can go
    # non-monotonic near the poles. Assuming a forward (increasing) arc there
    # turns house 1 into a ~350° reflex arc that swallows every planet. Instead,
    # a point belongs to the house whose cusp→next-cusp arc contains it via the
    # SHORTEST path (the real house span is always < 180°); a point exactly on a
    # cusp belongs to the house that cusp opens.
    for i in range(n):
        if abs((planet_degree - houses_degree_ut_list[i] + 180.0) % 360.0 - 180.0) < 1e-9:
            return _HOUSE_NAMES_TUPLE[i]

    best_index = None
    best_span = 360.0 + 1.0
    for i in range(n):
        start = houses_degree_ut_list[i]
        end = houses_degree_ut_list[(i + 1) % n]
        fwd = (end - start) % 360.0
        if fwd == 0:
            continue  # coincident cusps can't contain a point in their arc
        # Distance from the cusp to the point, in whichever direction the arc
        # to the next cusp actually runs (forward if fwd is the short way,
        # backward otherwise).
        if fwd <= 180.0:
            inside = (planet_degree - start) % 360.0 < fwd
            span = fwd
        else:
            back = 360.0 - fwd
            inside = (start - planet_degree) % 360.0 < back
            span = back
        if inside and span < best_span:
            best_index = i
            best_span = span

    if best_index is not None:
        return _HOUSE_NAMES_TUPLE[best_index]

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
        List of points common to both input lists (without duplicates),
        preserving the conventional astrological order of ``first_points``
        (Sun, Moon, Mercury, ...) rather than sorting alphabetically — so a
        dual chart's active_points read in the same order as a single chart's.
    """
    common = set(second_points)
    seen: set = set()
    result = []
    for point in first_points:
        if point in common and point not in seen:
            seen.add(point)
            result.append(point)
    return result


# =============================================================================
# LUNAR PHASE UTILITIES
# =============================================================================


def _get_lunar_phase_index(phase: int) -> int:
    """
    Get the index for lunar phase lookup based on phase number.

    Args:
        phase: The lunar phase number (1-28)

    Returns:
        Index (0-7) for lunar phase lookup arrays

    Raises:
        KerykeionException: If phase is outside valid range
    """
    if phase < 1:
        # Valid phases are 1-28; without this, phase <= 0 (and negatives) fell
        # through the `phase < 7` branch and returned Waxing Crescent instead
        # of raising as the docstring promises.
        raise KerykeionException(f"Error in lunar phase calculation! Phase: {phase}")
    if phase == 1:
        return 0
    elif phase < 7:
        return 1
    elif 7 <= phase <= 9:
        return 2
    elif phase < 14:
        return 3
    elif phase == 14:
        return 4
    elif phase < 20:
        return 5
    elif 20 <= phase <= 22:
        return 6
    elif phase <= 28:
        return 7
    else:
        raise KerykeionException(f"Error in lunar phase calculation! Phase: {phase}")


def get_moon_emoji_from_phase_int(phase: int) -> LunarPhaseEmoji:
    """
    Get the emoji representation of a lunar phase.

    Args:
        phase: The lunar phase number (1-28)

    Returns:
        The corresponding emoji for the lunar phase

    Raises:
        KerykeionException: If phase is outside valid range
    """
    index = _get_lunar_phase_index(phase)
    return _LUNAR_PHASE_EMOJIS[index]


def get_moon_phase_name_from_phase_int(phase: int) -> LunarPhaseName:
    """
    Get the name of a lunar phase from its numerical value.

    Args:
        phase: The lunar phase number (1-28)

    Returns:
        The corresponding name for the lunar phase

    Raises:
        KerykeionException: If phase is outside valid range
    """
    index = _get_lunar_phase_index(phase)
    return _LUNAR_PHASE_NAMES[index]


def check_and_adjust_polar_latitude(latitude: float) -> float:
    """
    Adjust latitude values for polar regions to prevent calculation errors.

    Latitudes beyond ±66° are clamped to ±66° for house calculations.

    Args:
        latitude: The original latitude value

    Returns:
        The adjusted latitude value, clamped between -66° and 66°

    Raises:
        KerykeionException: If the latitude is geometrically impossible
            (outside [-90, 90]) — a corrupt/mistyped value, not a polar one.
    """
    # Reject geometrically-impossible latitudes rather than silently clamping
    # them to the polar limit (which would turn a mistyped lat=100 into a
    # plausible-but-wrong chart at 66N). The ephemeris backend validates this
    # symmetrically with longitude; only genuinely-polar-but-valid latitudes
    # (66 < |lat| <= 90) are clamped below for house stability.
    if not -90.0 <= latitude <= 90.0:
        raise KerykeionException(
            f"Latitude {latitude} is out of range; it must be between -90 and 90 degrees."
        )
    if latitude > _POLAR_LATITUDE_LIMIT:
        latitude = _POLAR_LATITUDE_LIMIT
        logger.info(f"Latitude capped at {_POLAR_LATITUDE_LIMIT:.0f}° to keep house calculations stable.")

    elif latitude < -_POLAR_LATITUDE_LIMIT:
        latitude = -_POLAR_LATITUDE_LIMIT
        logger.info(f"Latitude capped at -{_POLAR_LATITUDE_LIMIT:.0f}° to keep house calculations stable.")

    return latitude


def normalize_longitude(longitude: float) -> float:
    """Normalize a longitude to the [-180, 180) range the ephemeris backend expects.

    A caller passing an un-normalized longitude (e.g. 370° == 10° E, or -190°
    == 170° E) would otherwise leak a raw backend CoordinateError from the
    houses call. Wrap it into range instead, matching the astronomical meaning.

    A longitude already in range is returned UNCHANGED (no modulo round-off), so
    ordinary inputs keep their exact value.
    """
    if -180.0 <= longitude < 180.0:
        return longitude
    return (longitude + 180.0) % 360.0 - 180.0


def safe_timezone(tz_str: str):
    """Resolve an IANA timezone string, raising ``KerykeionException`` if invalid.

    ``pytz.timezone`` raises ``UnknownTimeZoneError`` — a ``KeyError`` subclass,
    NOT a ``KerykeionException`` — so a caller catching only the library's own
    exception around a public entry point (from_iso_utc_time, from_current_time,
    EphemerisDataFactory, RelocatedChartFactory.relocate) would be broken by an
    invalid ``tz_str``. This is the single wrapper every such entry point should
    use so the failure mode is uniform (mirrors the guard in from_birth_data's
    _calculate_time_conversions and sun_times.resolve_timezone).
    """
    import pytz

    try:
        return pytz.timezone(tz_str)
    except pytz.exceptions.UnknownTimeZoneError as exc:
        raise KerykeionException(
            f"Unknown timezone: {tz_str!r}. Use a valid IANA timezone name "
            "(e.g. 'Europe/Rome', 'America/New_York')."
        ) from exc


# =============================================================================
# ANGULAR MATHEMATICS
# =============================================================================


def wrap_180(angle: Union[int, float]) -> float:
    """Wrap an angle in degrees into the signed range ``[-180, 180)``.

    Useful both for signed angular differences (``wrap_180(a - b)``) and for
    normalizing geographic longitudes; exactly 180° maps to -180° (the same
    meridian/separation).
    """
    return (angle + 180.0) % 360.0 - 180.0


def circular_mean(first_position: Union[int, float], second_position: Union[int, float]) -> float:
    """
    Calculate the circular mean of two angular positions.

    This method correctly handles positions that cross the 0°/360° boundary,
    avoiding errors that occur with simple arithmetic means.

    Exactly antipodal positions (180° apart) have no unique circular mean;
    they are resolved deterministically as the plain average of the
    normalized positions, ``((a + b) / 2) % 360``. This is the shorter-arc
    midpoint convention of the midpoint literature (Ebertin, Witte), and
    ``MidpointFactory._shorter_arc_midpoint`` delegates here.

    Args:
        first_position: First angular position in degrees (0-360)
        second_position: Second angular position in degrees (0-360)

    Returns:
        The circular mean position in degrees, always in the range [0, 360)
    """
    x = (math.cos(math.radians(first_position)) + math.cos(math.radians(second_position))) / 2
    y = (math.sin(math.radians(first_position)) + math.sin(math.radians(second_position))) / 2

    # Antipodal positions cancel out to a (near-)zero resultant vector, so
    # atan2 would return floating-point noise. Tie-break deterministically.
    if math.hypot(x, y) < 1e-12:
        return (((first_position % 360.0) + (second_position % 360.0)) / 2.0) % 360.0

    mean_position = math.degrees(math.atan2(y, x))

    if mean_position < 0:
        mean_position += 360

    # Float rounding can push the result to exactly 360.0 (e.g. 350° and 10°
    # yield 360 - 4.6e-15, which rounds to 360.0); normalize back to [0, 360)
    # so downstream consumers such as get_kerykeion_point_from_degree accept it.
    return mean_position % 360.0


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


def format_iso_display(iso_datetime_string: str, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format an ISO datetime string for display, supporting BCE dates.

    For modern dates (year >= 1), delegates to ``datetime.fromisoformat`` +
    ``strftime``.  For BCE dates (leading ``-``), parses the components
    manually and applies a subset of strftime-style directives.

    Supported format codes: ``%Y``, ``%m``, ``%d``, ``%H``, ``%M``, ``%S``.

    Args:
        iso_datetime_string: ISO 8601 string, possibly with a negative year.
        fmt: strftime-compatible format string.

    Returns:
        Formatted date/time string.
    """
    if not iso_datetime_string.startswith("-"):
        return datetime.fromisoformat(iso_datetime_string).strftime(fmt)

    # Parse "-YYYY-MM-DDThh:mm:ss±HH:MM" manually
    rest = iso_datetime_string[1:]  # strip leading minus
    year_str, remainder = rest.split("-", 1)
    year_str = "-" + year_str  # e.g. "-0500"
    parts = remainder.split("T", 1)
    date_tokens = parts[0].split("-")  # ["03", "21"]
    time_str = parts[1] if len(parts) > 1 else "00:00:00"
    # Strip timezone offset for time parsing
    for i in range(len(time_str) - 1, 0, -1):
        if time_str[i] in ("+", "-"):
            time_str = time_str[:i]
            break
    time_tokens = time_str.split(":")  # ["12", "00", "00"]

    result = fmt
    result = result.replace("%Y", year_str)
    result = result.replace("%m", date_tokens[0] if len(date_tokens) > 0 else "01")
    result = result.replace("%d", date_tokens[1] if len(date_tokens) > 1 else "01")
    result = result.replace("%H", time_tokens[0] if len(time_tokens) > 0 else "00")
    result = result.replace("%M", time_tokens[1] if len(time_tokens) > 1 else "00")
    result = result.replace("%S", time_tokens[2] if len(time_tokens) > 2 else "00")
    return result


def extract_year_from_iso(iso_datetime_string: str) -> int:
    """Extract the year as an integer from an ISO datetime string, including BCE dates.

    Args:
        iso_datetime_string: ISO 8601 string, possibly with a negative year.

    Returns:
        Year as integer (e.g. -500, 0, 1940).
    """
    if iso_datetime_string.startswith("-"):
        rest = iso_datetime_string[1:]
        year_str, _ = rest.split("-", 1)
        return -int(year_str)
    return datetime.fromisoformat(iso_datetime_string).year


def format_timedelta_hhmm(td: timedelta) -> str:
    """Render a duration as ``H:MM`` (rounded to whole minutes).

    Shared by the report and LLM-context serializers so both surfaces display a
    duration (e.g. the Sun's day length) in the same ``H:MM`` form rather than
    diverging into ``str(timedelta)`` (``H:MM:SS``).
    """
    # Half-up rounding to whole minutes (callers always pass non-negative
    # durations); avoids round()'s ties-to-even, which would render e.g. 0:30 as
    # 0:00 and 2:30 as 0:02.
    total_minutes = int(td.total_seconds() + 30) // 60
    return f"{total_minutes // 60}:{total_minutes % 60:02d}"


def _next_proleptic_julian_day(year: int, month: int, day: int) -> tuple[int, int, int]:
    """Return the calendar date one day after ``(year, month, day)``.

    Uses proleptic Julian-calendar rules (leap year when ``year % 4 == 0`` in
    astronomical numbering, where year 0 = 1 BCE), matching the ``JUL_CAL`` the
    BCE code path feeds into :func:`format_ancient_iso`. Crossing year 0 → 1 is
    the correct 1 BCE → 1 CE astronomical transition.
    """
    is_leap = (year % 4) == 0
    month_lengths = [31, 29 if is_leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    day += 1
    if day > month_lengths[month - 1]:
        day = 1
        month += 1
        if month > 12:
            month = 1
            year += 1
    return year, month, day


def _split_decimal_hour_with_carry(
    year: int, month: int, day: int, decimal_hour: float
) -> tuple[int, int, int, int, int, int]:
    """Decompose ``decimal_hour`` into integer ``(year, month, day, h, m, s)``.

    Rounds to the nearest second (the BCE path feeds a float from ``ephe.revjul``
    that is almost never an exact integer, so truncating each component lost up to
    ~1 second) and carries a value within ~0.5 s of midnight (rounds to 86400)
    into the next proleptic-Julian day, so the result can never contain an invalid
    24:00:00 or a misdated 23:59:59.

    Shared by :func:`format_ancient_iso` and the BCE branch of
    ``RelocatedChartFactory`` so the stored integer h/m/s fields and the ISO
    string can never drift apart at a second boundary.
    """
    total_seconds = round(decimal_hour * 3600)
    if total_seconds >= 86400:
        total_seconds -= 86400
        year, month, day = _next_proleptic_julian_day(year, month, day)
    return year, month, day, total_seconds // 3600, (total_seconds % 3600) // 60, total_seconds % 60


def _assemble_ancient_iso(
    year: int, month: int, day: int, hour: int, minute: int, second: int, utc_offset_hours: float
) -> str:
    """Assemble an ISO 8601 extended-year string from already-split integer fields.

    Shared by :func:`format_ancient_iso` and the BCE branch of
    ``RelocatedChartFactory`` so a date already decomposed by
    :func:`_split_decimal_hour_with_carry` is not split a second time. The h/m/s
    values are taken verbatim — no rounding or carry happens here, so callers must
    pass fields that already encode any midnight rollover.
    """
    # ISO 8601 extended year: negative sign for years <= 0
    year_str = f"{year:04d}" if year > 0 else f"-{abs(year):04d}"

    # UTC offset string
    if utc_offset_hours == 0.0:
        offset_str = "+00:00"
    else:
        sign = "+" if utc_offset_hours >= 0 else "-"
        abs_off = abs(utc_offset_hours)
        # Carry a rounded-up 60 into the hour (e.g. 0.99333 h -> 00:60 -> 01:00):
        # rounding minutes independently of hours could otherwise emit ":60",
        # which is not a valid ISO 8601 offset field (minutes must be 0-59).
        oh, om = divmod(round(abs_off * 60), 60)
        offset_str = f"{sign}{oh:02d}:{om:02d}"

    return f"{year_str}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}{offset_str}"


def format_ancient_iso(year: int, month: int, day: int, decimal_hour: float, utc_offset_hours: float) -> str:
    """Format a date with potentially negative year as an ISO 8601 extended-year string.

    Produces strings like ``"-0500-03-21T12:00:00+01:35"`` for dates that
    Python's ``datetime`` cannot represent (year < 1).

    Args:
        year: Calendar year in astronomical numbering (0 = 1 BCE, −1 = 2 BCE, etc.).
        month: Month (1–12).
        day: Day of month (1–31).
        decimal_hour: Hour as a decimal (e.g. 14.5 = 14:30:00).
        utc_offset_hours: UTC offset in decimal hours (east-positive).

    Returns:
        ISO 8601 formatted string with extended year.
    """
    # Round to the nearest second (with midnight day-carry) via the shared helper
    # so this and the BCE branch of RelocatedChartFactory decompose identically.
    year, month, day, h, m, s = _split_decimal_hour_with_carry(year, month, day, decimal_hour)
    return _assemble_ancient_iso(year, month, day, h, m, s, utc_offset_hours)


def datetime_to_julian(dt: datetime) -> float:
    """
    Convert a Python datetime object to Julian Day Number.

    The datetime is interpreted in the proleptic Gregorian calendar (the
    calendar Python's ``datetime`` uses), matching ``julian_to_datetime``
    so the two functions round-trip for all representable dates.

    Timezone-aware datetimes are converted to UTC first; naive datetimes
    are assumed to already be in UT.

    Args:
        dt: The datetime object to convert

    Returns:
        The corresponding Julian Day Number (JD) as a float
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)

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

    The result is expressed in the proleptic Gregorian calendar — the
    calendar Python's ``datetime`` natively uses — for ALL dates, including
    those before the 1582 Gregorian reform. This makes the function the
    exact inverse of ``datetime_to_julian``; the historical Julian-calendar
    branch used previously broke the round trip by ~10 days for
    pre-1582 dates.

    Args:
        jd: Julian Day Number as a float

    Returns:
        The corresponding datetime object (proleptic Gregorian, UT)

    Raises:
        ValueError: For JDs before year 1 CE (datetime cannot represent
            BCE dates; use the ephemeris backend's ``revjul`` for those).
    """
    jd_plus = jd + 0.5

    Z = int(jd_plus)
    F = jd_plus - Z

    # math.floor (not int()) so the century correction also holds for early
    # CE dates, where these intermediates are negative.
    alpha = math.floor((Z - 1867216.25) / 36524.25)
    A = Z + 1 + alpha - math.floor(alpha / 4)

    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day = B - D - int(30.6001 * E) + F
    day_int = int(day)

    day_frac = day - day_int

    if E < 14:
        month = E - 1
    else:
        month = E - 13

    if month > 2:
        year = C - 4716
    else:
        year = C - 4715

    if year < 1:
        # Explicit guard so the documented contract holds with a clear message,
        # rather than relying on datetime()'s terse "year 0 is out of range".
        raise ValueError(
            f"julian_to_datetime cannot represent JD {jd} (proleptic year {year} < 1 CE): "
            "Python's datetime has no BCE support. Use the ephemeris backend's "
            "revjul for BCE dates."
        )

    # Build from the integer date plus the day fraction so seconds/microseconds
    # carries normalize automatically (avoids a latent seconds==60 ValueError from
    # independent int() truncation of each component).
    return datetime(year, month, day_int) + timedelta(days=day_frac)


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
        for match in _CSS_VARIABLE_PATTERN.finditer(style_block):
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
