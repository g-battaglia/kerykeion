import math
import datetime
from typing import Mapping, Optional, Sequence, Union, Literal

from kerykeion.schemas import KerykeionException, ChartType
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import AspectModel, KerykeionPointModel, CompositeSubjectModel, PlanetReturnModel, AstrologicalSubjectModel, HouseComparisonModel
from kerykeion.schemas.settings_models import KerykeionLanguageCelestialPointModel, KerykeionSettingsCelestialPointModel


ElementQualityDistributionMethod = Literal["pure_count", "weighted"]
"""Supported strategies for calculating element and modality distributions."""

_SIGN_TO_ELEMENT: tuple[str, ...] = (
    "fire",    # Aries
    "earth",   # Taurus
    "air",     # Gemini
    "water",   # Cancer
    "fire",    # Leo
    "earth",   # Virgo
    "air",     # Libra
    "water",   # Scorpio
    "fire",    # Sagittarius
    "earth",   # Capricorn
    "air",     # Aquarius
    "water",   # Pisces
)

_SIGN_TO_QUALITY: tuple[str, ...] = (
    "cardinal",  # Aries
    "fixed",     # Taurus
    "mutable",   # Gemini
    "cardinal",  # Cancer
    "fixed",     # Leo
    "mutable",   # Virgo
    "cardinal",  # Libra
    "fixed",     # Scorpio
    "mutable",   # Sagittarius
    "cardinal",  # Capricorn
    "fixed",     # Aquarius
    "mutable",   # Pisces
)

_ELEMENT_KEYS: tuple[str, ...] = ("fire", "earth", "air", "water")
_QUALITY_KEYS: tuple[str, ...] = ("cardinal", "fixed", "mutable")

_DEFAULT_WEIGHTED_FALLBACK = 1.0
DEFAULT_WEIGHTED_POINT_WEIGHTS: dict[str, float] = {
    # Core luminaries & angles
    "sun": 2.0,
    "moon": 2.0,
    "ascendant": 2.0,
    "medium_coeli": 1.5,
    "descendant": 1.5,
    "imum_coeli": 1.5,
    "vertex": 0.8,
    "anti_vertex": 0.8,
    # Personal planets
    "mercury": 1.5,
    "venus": 1.5,
    "mars": 1.5,
    # Social planets
    "jupiter": 1.0,
    "saturn": 1.0,
    # Outer/transpersonal
    "uranus": 0.5,
    "neptune": 0.5,
    "pluto": 0.5,
    # Lunar nodes (mean/true variants)
    "mean_north_lunar_node": 0.5,
    "true_north_lunar_node": 0.5,
    "mean_south_lunar_node": 0.5,
    "true_south_lunar_node": 0.5,
    # Chiron, Lilith variants
    "chiron": 0.6,
    "mean_lilith": 0.5,
    "true_lilith": 0.5,
    # Asteroids / centaurs
    "ceres": 0.5,
    "pallas": 0.4,
    "juno": 0.4,
    "vesta": 0.4,
    "pholus": 0.3,
    # Dwarf planets & TNOs
    "eris": 0.3,
    "sedna": 0.3,
    "haumea": 0.3,
    "makemake": 0.3,
    "ixion": 0.3,
    "orcus": 0.3,
    "quaoar": 0.3,
    # Arabic Parts
    "pars_fortunae": 0.8,
    "pars_spiritus": 0.7,
    "pars_amoris": 0.6,
    "pars_fidei": 0.6,
    # Fixed stars
    "regulus": 0.2,
    "spica": 0.2,
    # Other
    "earth": 0.3,
}


def _prepare_weight_lookup(
    method: ElementQualityDistributionMethod,
    custom_weights: Optional[Mapping[str, float]] = None,
) -> tuple[dict[str, float], float]:
    """
    Normalize and merge default weights with any custom overrides.

    Args:
        method: Calculation strategy to use.
        custom_weights: Optional mapping of point name (case-insensitive) to weight.
                        Supports special key "__default__" as fallback weight.

    Returns:
        A tuple containing the weight lookup dictionary and fallback weight.
    """
    normalized_custom = (
        {key.lower(): float(value) for key, value in custom_weights.items()}
        if custom_weights
        else {}
    )

    if method == "weighted":
        weight_lookup: dict[str, float] = dict(DEFAULT_WEIGHTED_POINT_WEIGHTS)
        fallback_weight = _DEFAULT_WEIGHTED_FALLBACK
    else:
        weight_lookup = {}
        fallback_weight = 1.0

    fallback_weight = normalized_custom.get("__default__", fallback_weight)

    for key, value in normalized_custom.items():
        if key == "__default__":
            continue
        weight_lookup[key] = float(value)

    return weight_lookup, fallback_weight


def _calculate_distribution_for_subject(
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    celestial_points_names: Sequence[str],
    sign_to_group_map: Sequence[str],
    group_keys: Sequence[str],
    weight_lookup: Mapping[str, float],
    fallback_weight: float,
) -> dict[str, float]:
    """
    Accumulate distribution totals for a single subject.

    Args:
        subject: Subject providing planetary positions.
        celestial_points_names: Names of celestial points to consider (lowercase).
        sign_to_group_map: Mapping from sign index to element/modality key.
        group_keys: Iterable of expected keys for the resulting totals.
        weight_lookup: Precomputed mapping of weights per point.
        fallback_weight: Default weight if point missing in lookup.

    Returns:
        Dictionary with accumulated totals keyed by element/modality.
    """
    totals = {key: 0.0 for key in group_keys}

    for point_name in celestial_points_names:
        point = subject.get(point_name)
        if point is None:
            continue

        sign_index = getattr(point, "sign_num", None)
        if sign_index is None or not (0 <= sign_index < len(sign_to_group_map)):
            continue

        group_key = sign_to_group_map[sign_index]
        weight = weight_lookup.get(point_name, fallback_weight)
        totals[group_key] += weight

    return totals


_SECOND_COLUMN_THRESHOLD = 20
_THIRD_COLUMN_THRESHOLD = 28
_FOURTH_COLUMN_THRESHOLD = 36

_DOUBLE_CHART_TYPES: tuple[ChartType, ...] = ("Synastry", "Transit", "DualReturnChart")
_GRID_COLUMN_WIDTH = 125


def _select_planet_grid_thresholds(chart_type: ChartType) -> tuple[int, int, int]:
    """Return column thresholds for the planet grids based on chart type."""
    if chart_type in _DOUBLE_CHART_TYPES:
        return (
            1_000_000, # effectively disable first column
            1_000_008, # effectively disable second column
            1_000_016, # effectively disable third column
        )
    return _SECOND_COLUMN_THRESHOLD, _THIRD_COLUMN_THRESHOLD, _FOURTH_COLUMN_THRESHOLD


def _planet_grid_layout_position(
    index: int, thresholds: Optional[tuple[int, int, int]] = None
) -> tuple[int, int]:
    """Return horizontal offset and row index for planet grids."""
    second_threshold, third_threshold, fourth_threshold = (
        thresholds
        if thresholds is not None
        else (_SECOND_COLUMN_THRESHOLD, _THIRD_COLUMN_THRESHOLD, _FOURTH_COLUMN_THRESHOLD)
    )

    if index < second_threshold:
        column = 0
        row = index
    elif index < third_threshold:
        column = 1
        row = index - second_threshold
    elif index < fourth_threshold:
        column = 2
        row = index - third_threshold
    else:
        column = 3
        row = index - fourth_threshold

    offset = -(_GRID_COLUMN_WIDTH * column)
    return offset, row



def get_decoded_kerykeion_celestial_point_name(input_planet_name: str, celestial_point_language: KerykeionLanguageCelestialPointModel) -> str:
    """
    Decode the given celestial point name based on the provided language model.

    Args:
        input_planet_name (str): The name of the celestial point to decode.
        celestial_point_language (KerykeionLanguageCelestialPointModel): The language model containing celestial point names.

    Returns:
        str: The decoded celestial point name.
    """


    # Get the language model keys
    language_keys = celestial_point_language.model_dump().keys()

    # Check if the input planet name exists in the language model
    if input_planet_name in language_keys:
        return celestial_point_language[input_planet_name]
    else:
        raise KerykeionException(f"Celestial point {input_planet_name} not found in language model.")


def decHourJoin(inH: int, inM: int, inS: int) -> float:
    """Join hour, minutes, seconds, timezone integer to hour float.

    Args:
        - inH (int): hour
        - inM (int): minutes
        - inS (int): seconds
    Returns:
        float: hour in float format
    """

    dh = float(inH)
    dm = float(inM) / 60
    ds = float(inS) / 3600
    output = dh + dm + ds
    return output


def degreeDiff(a: Union[int, float], b: Union[int, float]) -> float:
    """Calculate the smallest difference between two angles in degrees.

    Args:
        a (int | float): first angle in degrees
        b (int | float): second angle in degrees

    Returns:
        float: smallest difference between a and b (0 to 180 degrees)
    """
    diff = math.fmod(abs(a - b), 360)  # Assicura che il valore sia in [0, 360)
    return min(diff, 360 - diff)  # Prende l'angolo più piccolo tra i due possibili


def degreeSum(a: Union[int, float], b: Union[int, float]) -> float:
    """Calculate the sum of two angles in degrees, normalized to [0, 360).

    Args:
        a (int | float): first angle in degrees
        b (int | float): second angle in degrees

    Returns:
        float: normalized sum of a and b in the range [0, 360)
    """
    return math.fmod(a + b, 360) if (a + b) % 360 != 0 else 0.0


def normalizeDegree(angle: Union[int, float]) -> float:
    """Normalize an angle to the range [0, 360).

    Args:
        angle (int | float): The input angle in degrees.

    Returns:
        float: The normalized angle in the range [0, 360).
    """
    return angle % 360 if angle % 360 != 0 else 0.0


def offsetToTz(datetime_offset: Union[datetime.timedelta, None]) -> float:
    """Convert datetime offset to float in hours.

    Args:
        - datetime_offset (datetime.timedelta): datetime offset

    Returns:
        - float: offset in hours
    """

    if datetime_offset is None:
        raise KerykeionException("datetime_offset is None")

    # days to hours
    dh = float(datetime_offset.days * 24)
    # seconds to hours
    sh = float(datetime_offset.seconds / 3600.0)
    # total hours
    output = dh + sh
    return output


def sliceToX(slice: Union[int, float], radius: Union[int, float], offset: Union[int, float]) -> float:
    """Calculates the x-coordinate of a point on a circle based on the slice, radius, and offset.

    Args:
        - slice (int | float): Represents the
            slice of the circle to calculate the x-coordinate for.
            It must be  between 0 and 11 (inclusive).
        - radius (int | float): Represents the radius of the circle.
        - offset (int | float): Represents the offset in degrees.
            It must be between 0 and 360 (inclusive).

    Returns:
        float: The x-coordinate of the point on the circle.

    Example:
        >>> import math
        >>> sliceToX(3, 5, 45)
        2.5000000000000018
    """

    plus = (math.pi * offset) / 180
    radial = ((math.pi / 6) * slice) + plus
    return radius * (math.cos(radial) + 1)


def sliceToY(slice: Union[int, float], r: Union[int, float], offset: Union[int, float]) -> float:
    """Calculates the y-coordinate of a point on a circle based on the slice, radius, and offset.

    Args:
        - slice (int | float): Represents the slice of the circle to calculate
            the y-coordinate for. It must be between 0 and 11 (inclusive).
        - r (int | float): Represents the radius of the circle.
        - offset (int | float): Represents the offset in degrees.
            It must be between 0 and 360 (inclusive).

    Returns:
        float: The y-coordinate of the point on the circle.

    Example:
        >>> import math
        >>> __sliceToY(3, 5, 45)
        -4.330127018922194
    """
    plus = (math.pi * offset) / 180
    radial = ((math.pi / 6) * slice) + plus
    return r * ((math.sin(radial) / -1) + 1)


def draw_zodiac_slice(
    c1: Union[int, float],
    chart_type: ChartType,
    seventh_house_degree_ut: Union[int, float],
    num: int,
    r: Union[int, float],
    style: str,
    type: str,
) -> str:
    """Draws a zodiac slice based on the given parameters.

    Args:
        - c1 (Union[int, float]): The value of c1.
        - chart_type (ChartType): The type of chart.
        - seventh_house_degree_ut (Union[int, float]): The degree of the seventh house.
        - num (int): The number of the sign. Note: In OpenAstro it did refer to self.zodiac,
            which is a list of the signs in order, starting with Aries. Eg:
            {"name": "Ari", "element": "fire"}
        - r (Union[int, float]): The value of r.
        - style (str): The CSS inline style.
        - type (str): The type ?. In OpenAstro, it was the symbol of the sign. Eg: "Ari".
            self.zodiac[i]["name"]

    Returns:
        - str: The zodiac slice and symbol as an SVG path.
    """

    # pie slices
    offset = 360 - seventh_house_degree_ut
    # check transit
    if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "DualReturnChart":
        dropin: Union[int, float] = 0
    else:
        dropin = c1
    slice = f'<path d="M{str(r)},{str(r)} L{str(dropin + sliceToX(num, r - dropin, offset))},{str(dropin + sliceToY(num, r - dropin, offset))} A{str(r - dropin)},{str(r - dropin)} 0 0,0 {str(dropin + sliceToX(num + 1, r - dropin, offset))},{str(dropin + sliceToY(num + 1, r - dropin, offset))} z" style="{style}"/>'

    # symbols
    offset = offset + 15
    # check transit
    if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "DualReturnChart":
        dropin = 54
    else:
        dropin = 18 + c1
    sign = f'<g transform="translate(-16,-16)"><use x="{str(dropin + sliceToX(num, r - dropin, offset))}" y="{str(dropin + sliceToY(num, r - dropin, offset))}" xlink:href="#{type}" /></g>'

    return slice + "" + sign


def convert_latitude_coordinate_to_string(coord: Union[int, float], north_label: str, south_label: str) -> str:
    """Converts a floating point latitude to string with
    degree, minutes and seconds and the appropriate sign
    (north or south). Eg. 52.1234567 -> 52°7'25" N

    Args:
        - coord (float | int): latitude in floating or integer format
        - north_label (str): String label for north
        - south_label (str): String label for south
    Returns:
        - str: latitude in string format with degree, minutes,
        seconds and sign (N/S)
    """

    sign = north_label
    if coord < 0.0:
        sign = south_label
        coord = abs(coord)
    deg = int(coord)
    min = int((float(coord) - deg) * 60)
    sec = int(round(float(((float(coord) - deg) * 60) - min) * 60.0))
    return f"{deg}°{min}'{sec}\" {sign}"


def convert_longitude_coordinate_to_string(coord: Union[int, float], east_label: str, west_label: str) -> str:
    """Converts a floating point longitude to string with
    degree, minutes and seconds and the appropriate sign
    (east or west). Eg. 52.1234567 -> 52°7'25" E

    Args:
        - coord (float|int): longitude in floating point format
        - east_label (str): String label for east
        - west_label (str): String label for west
    Returns:
        str: longitude in string format with degree, minutes,
            seconds and sign (E/W)
    """

    sign = east_label
    if coord < 0.0:
        sign = west_label
        coord = abs(coord)
    deg = int(coord)
    min = int((float(coord) - deg) * 60)
    sec = int(round(float(((float(coord) - deg) * 60) - min) * 60.0))
    return f"{deg}°{min}'{sec}\" {sign}"


def draw_aspect_line(
    r: Union[int, float],
    ar: Union[int, float],
    aspect: Union[AspectModel, dict],
    color: str,
    seventh_house_degree_ut: Union[int, float],
) -> str:
    """Draws svg aspects: ring, aspect ring, degreeA degreeB

    Args:
        - r (Union[int, float]): The value of r.
        - ar (Union[int, float]): The value of ar.
        - aspect_dict (dict): The aspect dictionary.
        - color (str): The color of the aspect.
        - seventh_house_degree_ut (Union[int, float]): The degree of the seventh house.

    Returns:
        str: The SVG line element as a string.
    """

    if isinstance(aspect, dict):
        aspect = AspectModel(**aspect)

    first_offset = (int(seventh_house_degree_ut) / -1) + int(aspect["p1_abs_pos"])
    x1 = sliceToX(0, ar, first_offset) + (r - ar)
    y1 = sliceToY(0, ar, first_offset) + (r - ar)

    second_offset = (int(seventh_house_degree_ut) / -1) + int(aspect["p2_abs_pos"])
    x2 = sliceToX(0, ar, second_offset) + (r - ar)
    y2 = sliceToY(0, ar, second_offset) + (r - ar)

    return (
        f'<g kr:node="Aspect" kr:aspectname="{aspect["aspect"]}" kr:to="{aspect["p1_name"]}" kr:tooriginaldegrees="{aspect["p1_abs_pos"]}" kr:from="{aspect["p2_name"]}" kr:fromoriginaldegrees="{aspect["p2_abs_pos"]}" kr:orb="{aspect["orbit"]}" kr:aspectdegrees="{aspect["aspect_degrees"]}" kr:planetsdiff="{aspect["diff"]}" kr:aspectmovement="{aspect["aspect_movement"]}">'
        f'<line class="aspect" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {color}; stroke-width: 1; stroke-opacity: .9;"/>'
        f"</g>"
    )


def convert_decimal_to_degree_string(dec: float, format_type: Literal["1", "2", "3"] = "3") -> str:
    """
    Converts a decimal float to a degrees string in the specified format.

    Args:
        dec (float): The decimal float to convert.
        format_type (str): The format type:
            - "1": a°
            - "2": a°b'
            - "3": a°b'c" (default)

    Returns:
        str: The degrees string in the specified format.
    """
    # Ensure the input is a float
    dec = float(dec)

    # Calculate degrees, minutes, and seconds
    degrees = int(dec)
    minutes = int((dec - degrees) * 60)
    seconds = int(round((dec - degrees - minutes / 60) * 3600))

    # Format the output based on the specified type
    if format_type == "1":
        return f"{degrees}°"
    elif format_type == "2":
        return f"{degrees}°{minutes:02d}'"
    elif format_type == "3":
        return f"{degrees}°{minutes:02d}'{seconds:02d}\""


def draw_transit_ring_degree_steps(r: Union[int, float], seventh_house_degree_ut: Union[int, float]) -> str:
    """Draws the transit ring degree steps.

    Args:
        - r (Union[int, float]): The value of r.
        - seventh_house_degree_ut (Union[int, float]): The degree of the seventh house.

    Returns:
        str: The SVG path of the transit ring degree steps.
    """

    out = '<g id="transitRingDegreeSteps">'
    for i in range(72):
        offset = float(i * 5) - seventh_house_degree_ut
        if offset < 0:
            offset = offset + 360.0
        elif offset > 360:
            offset = offset - 360.0
        x1 = sliceToX(0, r, offset)
        y1 = sliceToY(0, r, offset)
        x2 = sliceToX(0, r + 2, offset) - 2
        y2 = sliceToY(0, r + 2, offset) - 2
        out += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: #F00; stroke-width: 1px; stroke-opacity:.9;"/>'
    out += "</g>"

    return out


def draw_degree_ring(
    r: Union[int, float], c1: Union[int, float], seventh_house_degree_ut: Union[int, float], stroke_color: str
) -> str:
    """Draws the degree ring.

    Args:
        - r (Union[int, float]): The value of r.
        - c1 (Union[int, float]): The value of c1.
        - seventh_house_degree_ut (Union[int, float]): The degree of the seventh house.
        - stroke_color (str): The color of the stroke.

    Returns:
        str: The SVG path of the degree ring.
    """
    out = '<g id="degreeRing">'
    for i in range(72):
        offset = float(i * 5) - seventh_house_degree_ut
        if offset < 0:
            offset = offset + 360.0
        elif offset > 360:
            offset = offset - 360.0
        x1 = sliceToX(0, r - c1, offset) + c1
        y1 = sliceToY(0, r - c1, offset) + c1
        x2 = sliceToX(0, r + 2 - c1, offset) - 2 + c1
        y2 = sliceToY(0, r + 2 - c1, offset) - 2 + c1

        out += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {stroke_color}; stroke-width: 1px; stroke-opacity:.9;"/>'
    out += "</g>"

    return out


def draw_transit_ring(r: Union[int, float], paper_1_color: str, zodiac_transit_ring_3_color: str) -> str:
    """
    Draws the transit ring.

    Args:
        - r (Union[int, float]): The value of r.
        - paper_1_color (str): The color of paper 1.
        - zodiac_transit_ring_3_color (str): The color of the zodiac transit ring

    Returns:
        str: The SVG path of the transit ring.
    """
    radius_offset = 18

    out = f'<circle cx="{r}" cy="{r}" r="{r - radius_offset}" style="fill: none; stroke: {paper_1_color}; stroke-width: 36px; stroke-opacity: .4;"/>'
    out += f'<circle cx="{r}" cy="{r}" r="{r}" style="fill: none; stroke: {zodiac_transit_ring_3_color}; stroke-width: 1px; stroke-opacity: .6;"/>'

    return out


def draw_first_circle(
    r: Union[int, float], stroke_color: str, chart_type: ChartType, c1: Union[int, float, None] = None
) -> str:
    """
    Draws the first circle.

    Args:
        - r (Union[int, float]): The value of r.
        - color (str): The color of the circle.
        - chart_type (ChartType): The type of chart.
        - c1 (Union[int, float]): The value of c1.

    Returns:
        str: The SVG path of the first circle.
    """
    if chart_type == "Synastry" or chart_type == "Transit" or chart_type == "DualReturnChart":
        return f'<circle cx="{r}" cy="{r}" r="{r - 36}" style="fill: none; stroke: {stroke_color}; stroke-width: 1px; stroke-opacity:.4;" />'
    else:
        if c1 is None:
            raise KerykeionException("c1 is None")

        return (
            f'<circle cx="{r}" cy="{r}" r="{r - c1}" style="fill: none; stroke: {stroke_color}; stroke-width: 1px; " />'
        )


def draw_background_circle(r: Union[int, float], stroke_color: str, fill_color: str) -> str:
    """
    Draws the background circle.

    Args:
        - r (Union[int, float]): The value of r.
        - stroke_color (str): The color of the stroke.
        - fill_color (str): The color of the fill.

    Returns:
        str: The SVG path of the background circle.
    """
    return f'<circle cx="{r}" cy="{r}" r="{r}" style="fill: {fill_color}; stroke: {stroke_color}; stroke-width: 1px;" />'


def draw_second_circle(
    r: Union[int, float], stroke_color: str, fill_color: str, chart_type: ChartType, c2: Union[int, float, None] = None
) -> str:
    """
    Draws the second circle.

    Args:
        - r (Union[int, float]): The value of r.
        - stroke_color (str): The color of the stroke.
        - fill_color (str): The color of the fill.
        - chart_type (ChartType): The type of chart.
        - c2 (Union[int, float]): The value of c2.

    Returns:
        str: The SVG path of the second circle.
    """

    if chart_type == "Synastry" or chart_type == "Transit" or chart_type == "DualReturnChart":
        return f'<circle cx="{r}" cy="{r}" r="{r - 72}" style="fill: {fill_color}; fill-opacity:.4; stroke: {stroke_color}; stroke-opacity:.4; stroke-width: 1px" />'

    else:
        if c2 is None:
            raise KerykeionException("c2 is None")

        return f'<circle cx="{r}" cy="{r}" r="{r - c2}" style="fill: {fill_color}; fill-opacity:.2; stroke: {stroke_color}; stroke-opacity:.4; stroke-width: 1px" />'


def draw_third_circle(
    radius: Union[int, float],
    stroke_color: str,
    fill_color: str,
    chart_type: ChartType,
    c3: Union[int, float]
) -> str:
    """
    Draws the third circle in an SVG chart.

    Parameters:
    - radius (Union[int, float]): The radius of the circle.
    - stroke_color (str): The stroke color of the circle.
    - fill_color (str): The fill color of the circle.
    - chart_type (ChartType): The type of the chart.
    - c3 (Union[int, float, None], optional): The radius adjustment for non-Synastry and non-Transit charts.

    Returns:
    - str: The SVG element as a string.
    """
    if chart_type in {"Synastry", "Transit", "DualReturnChart"}:
        # For Synastry and Transit charts, use a fixed radius adjustment of 160
        return f'<circle cx="{radius}" cy="{radius}" r="{radius - 160}" style="fill: {fill_color}; fill-opacity:.8; stroke: {stroke_color}; stroke-width: 1px" />'

    else:
        return f'<circle cx="{radius}" cy="{radius}" r="{radius - c3}" style="fill: {fill_color}; fill-opacity:.8; stroke: {stroke_color}; stroke-width: 1px" />'


def draw_aspect_grid(
        stroke_color: str,
        available_planets: list,
        aspects: list,
        x_start: int = 510,
        y_start: int = 468,
    ) -> str:
    """
    Draws the aspect grid for the given planets and aspects.

    Args:
        stroke_color (str): The color of the stroke.
        available_planets (list): List of all planets. Only planets with "is_active" set to True will be used.
        aspects (list): List of aspects.
        x_start (int): The x-coordinate starting point.
        y_start (int): The y-coordinate starting point.

    Returns:
        str: SVG string representing the aspect grid.
    """
    svg_output = ""
    style = f"stroke:{stroke_color}; stroke-width: 1px; stroke-width: 0.5px; fill:none"
    box_size = 14

    # Filter active planets
    active_planets = [planet for planet in available_planets if planet["is_active"]]

    # Reverse the list of active planets for the first iteration
    reversed_planets = active_planets[::-1]

    for index, planet_a in enumerate(reversed_planets):
        # Draw the grid box for the planet
        svg_output += f'<rect kr:node="AspectsGridRect" x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'
        svg_output += f'<use transform="scale(0.4)" x="{(x_start + 2) * 2.5}" y="{(y_start + 1) * 2.5}" xlink:href="#{planet_a["name"]}" />'

        # Update the starting coordinates for the next box
        x_start += box_size
        y_start -= box_size

        # Coordinates for the aspect symbols
        x_aspect = x_start
        y_aspect = y_start + box_size

        # Iterate over the remaining planets
        for planet_b in reversed_planets[index + 1:]:
            # Draw the grid box for the aspect
            svg_output += f'<rect kr:node="AspectsGridRect" x="{x_aspect}" y="{y_aspect}" width="{box_size}" height="{box_size}" style="{style}"/>'
            x_aspect += box_size

            # Check for aspects between the planets
            for aspect in aspects:
                if (aspect["p1"] == planet_a["id"] and aspect["p2"] == planet_b["id"]) or (
                    aspect["p1"] == planet_b["id"] and aspect["p2"] == planet_a["id"]
                ):
                    svg_output += f'<use  x="{x_aspect - box_size + 1}" y="{y_aspect + 1}" xlink:href="#orb{aspect["aspect_degrees"]}" />'

    return svg_output


def draw_houses_cusps_and_text_number(
    r: Union[int, float],
    first_subject_houses_list: list[KerykeionPointModel],
    standard_house_cusp_color: str,
    first_house_color: str,
    tenth_house_color: str,
    seventh_house_color: str,
    fourth_house_color: str,
    c1: Union[int, float],
    c3: Union[int, float],
    chart_type: ChartType,
    second_subject_houses_list: Union[list[KerykeionPointModel], None] = None,
    transit_house_cusp_color: Union[str, None] = None,
    external_view: bool = False,
) -> str:
    """
    Draws the houses cusps and text numbers for a given chart type.

    Parameters:
    - r: Radius of the chart.
    - first_subject_houses_list: List of house for the first subject.
    - standard_house_cusp_color: Default color for house cusps.
    - first_house_color: Color for the first house cusp.
    - tenth_house_color: Color for the tenth house cusp.
    - seventh_house_color: Color for the seventh house cusp.
    - fourth_house_color: Color for the fourth house cusp.
    - c1: Offset for the first subject.
    - c3: Offset for the third subject.
    - chart_type: Type of the chart (e.g., Transit, Synastry).
    - second_subject_houses_list: List of house for the second subject (optional).
    - transit_house_cusp_color: Color for transit house cusps (optional).
    - external_view: Whether to use external view mode for positioning (optional).

    Returns:
    - A string containing SVG elements for house cusps and numbers.
    """

    path = ""
    xr = 12

    for i in range(xr):
        # Determine offsets based on chart type
        dropin, roff, t_roff = (160, 72, 36) if chart_type in ["Transit", "Synastry", "DualReturnChart"] else (c3, c1, False)

        # Calculate the offset for the current house cusp
        offset = (int(first_subject_houses_list[int(xr / 2)].abs_pos) / -1) + int(first_subject_houses_list[i].abs_pos)

        # Calculate the coordinates for the house cusp lines
        x1 = sliceToX(0, (r - dropin), offset) + dropin
        y1 = sliceToY(0, (r - dropin), offset) + dropin
        x2 = sliceToX(0, r - roff, offset) + roff
        y2 = sliceToY(0, r - roff, offset) + roff

        # Calculate the text offset for the house number
        next_index = (i + 1) % xr
        text_offset = offset + int(
            degreeDiff(first_subject_houses_list[next_index].abs_pos, first_subject_houses_list[i].abs_pos) / 2
        )

        # Determine the line color based on the house index
        linecolor = {0: first_house_color, 9: tenth_house_color, 6: seventh_house_color, 3: fourth_house_color}.get(
            i, standard_house_cusp_color
        )

        if chart_type in ["Transit", "Synastry", "DualReturnChart"]:
            if second_subject_houses_list is None or transit_house_cusp_color is None:
                raise KerykeionException("second_subject_houses_list_ut or transit_house_cusp_color is None")

            # Calculate the offset for the second subject's house cusp
            zeropoint = 360 - first_subject_houses_list[6].abs_pos
            t_offset = (zeropoint + second_subject_houses_list[i].abs_pos) % 360

            # Calculate the coordinates for the second subject's house cusp lines
            t_x1 = sliceToX(0, (r - t_roff), t_offset) + t_roff
            t_y1 = sliceToY(0, (r - t_roff), t_offset) + t_roff
            t_x2 = sliceToX(0, r, t_offset)
            t_y2 = sliceToY(0, r, t_offset)

            # Calculate the text offset for the second subject's house number
            t_text_offset = t_offset + int(
                degreeDiff(second_subject_houses_list[next_index].abs_pos, second_subject_houses_list[i].abs_pos) / 2
            )
            t_linecolor = linecolor if i in [0, 9, 6, 3] else transit_house_cusp_color
            xtext = sliceToX(0, (r - 8), t_text_offset) + 8
            ytext = sliceToY(0, (r - 8), t_text_offset) + 8

            # Add the house number text for the second subject
            fill_opacity = "0" if chart_type == "Transit" else ".4"
            path += '<g kr:node="HouseNumber">'
            path += f'<text style="fill: var(--kerykeion-chart-color-house-number); fill-opacity: {fill_opacity}; font-size: 14px"><tspan x="{xtext - 3}" y="{ytext + 3}">{i + 1}</tspan></text>'
            path += "</g>"

            # Add the house cusp line for the second subject
            stroke_opacity = "0" if chart_type == "Transit" else ".3"
            path += f'<g kr:node="Cusp" kr:absoluteposition="{second_subject_houses_list[i].abs_pos}" kr:signposition="{second_subject_houses_list[i].position}" kr:sing="{second_subject_houses_list[i].sign}" kr:slug="{second_subject_houses_list[i].name}">'
            path += f"<line x1='{t_x1}' y1='{t_y1}' x2='{t_x2}' y2='{t_y2}' style='stroke: {t_linecolor}; stroke-width: 1px; stroke-opacity:{stroke_opacity};'/>"
            path += "</g>"

        # Adjust dropin based on chart type and external view
        dropin_map = {"Transit": 84, "Synastry": 84, "DualReturnChart": 84}
        if external_view:
            dropin = 100
        else:
            dropin = dropin_map.get(chart_type, 48)
        xtext = sliceToX(0, (r - dropin), text_offset) + dropin
        ytext = sliceToY(0, (r - dropin), text_offset) + dropin

        # Add the house cusp line for the first subject
        path += f'<g kr:node="Cusp" kr:absoluteposition="{first_subject_houses_list[i].abs_pos}" kr:signposition="{first_subject_houses_list[i].position}" kr:sing="{first_subject_houses_list[i].sign}" kr:slug="{first_subject_houses_list[i].name}">'
        path += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {linecolor}; stroke-width: 1px; stroke-dasharray:3,2; stroke-opacity:.4;"/>'
        path += "</g>"

        # Add the house number text for the first subject
        path += '<g kr:node="HouseNumber">'
        path += f'<text style="fill: var(--kerykeion-chart-color-house-number); fill-opacity: .6; font-size: 14px"><tspan x="{xtext - 3}" y="{ytext + 3}">{i + 1}</tspan></text>'
        path += "</g>"

    return path


def draw_transit_aspect_list(
    grid_title: str,
    aspects_list: Union[list[AspectModel], list[dict]],
    celestial_point_language: Union[KerykeionLanguageCelestialPointModel, dict],
    aspects_settings: dict,
    *,
    aspects_per_column: int = 14,
    column_width: int = 100,
    line_height: int = 14,
    max_columns: int = 6,
    chart_height: Optional[int] = None,
) -> str:
    """
    Generates the SVG output for the aspect transit grid.

    Parameters:
    - grid_title: Title of the grid.
    - aspects_list: List of aspects.
    - celestial_point_language: Dictionary containing the celestial point language data.
    - aspects_settings: Dictionary containing the aspect settings.
    - aspects_per_column: Number of aspects to display per column (default: 14).
    - column_width: Width in pixels for each column (default: 100).
    - line_height: Height in pixels for each line (default: 14).
    - max_columns: Maximum number of columns before vertical adjustment (default: 6).
    - chart_height: Total chart height. When provided, columns from the 12th onward
      leverage the taller layout capacity (default: None).

    Returns:
    - A string containing the SVG path data for the aspect transit grid.
    """

    if isinstance(celestial_point_language, dict):
        celestial_point_language = KerykeionLanguageCelestialPointModel(**celestial_point_language)

    # If not instance of AspectModel, convert to AspectModel
    if aspects_list and isinstance(aspects_list[0], dict):
        aspects_list = [AspectModel(**aspect) for aspect in aspects_list]  # type: ignore

    # Type narrowing: at this point aspects_list contains AspectModel instances
    typed_aspects_list: list[AspectModel] = aspects_list  # type: ignore

    translate_x = 565
    translate_y = 273
    title_clearance = 18
    top_limit_y: float = -translate_y + title_clearance
    bottom_padding = 40
    baseline_index = aspects_per_column - 1
    top_limit_index = math.ceil(top_limit_y / line_height)
    # `top_limit_index` identifies the highest row index we can reach without
    # touching the title block. Combined with the baseline index we know how many
    # rows a "tall" column may contain.
    max_capacity_by_top = baseline_index - top_limit_index + 1

    inner_path = ""

    full_height_column_index = 10  # 0-based index → 11th column onward
    if chart_height is not None:
        available_height = max(chart_height - translate_y - bottom_padding, line_height)
        allowed_capacity = max(aspects_per_column, int(available_height // line_height))
        full_height_capacity = max(aspects_per_column, min(allowed_capacity, max_capacity_by_top))
    else:
        full_height_capacity = aspects_per_column

    # Bucket aspects into columns while respecting the capacity of each column.
    columns: list[list[AspectModel]] = []
    column_capacities: list[int] = []

    for aspect in typed_aspects_list:
        if not columns or len(columns[-1]) >= column_capacities[-1]:
            new_col_index = len(columns)
            capacity = aspects_per_column if new_col_index < full_height_column_index else full_height_capacity
            capacity = max(capacity, 1)
            columns.append([])
            column_capacities.append(capacity)
        columns[-1].append(aspect)

    for col_idx, column in enumerate(columns):
        capacity = column_capacities[col_idx]
        horizontal_position = col_idx * column_width
        column_len = len(column)

        for row_idx, aspect in enumerate(column):
            # Default top-aligned placement
            vertical_position = row_idx * line_height

            # Full-height columns reuse the shared baseline so every column
            # finishes at the same vertical position and grows upwards.
            if col_idx >= full_height_column_index:
                vertical_index = baseline_index - (column_len - 1 - row_idx)
                vertical_position = vertical_index * line_height
            # Legacy overflow columns (before the 12th) keep the older behaviour:
            # once we exceed the configured column count, bottom-align the content
            # so the shorter columns do not look awkwardly padded at the top.
            elif col_idx >= max_columns and capacity == aspects_per_column:
                top_offset_lines = max(0, capacity - len(column))
                vertical_position = (top_offset_lines + row_idx) * line_height

            inner_path += f'<g transform="translate({horizontal_position},{vertical_position})">'

            # First planet symbol
            inner_path += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{celestial_point_language[aspect["p1"]]["name"]}" />'

            # Aspect symbol
            aspect_name = aspect["aspect"]
            id_value = next((a["degree"] for a in aspects_settings if a["name"] == aspect_name), None)  # type: ignore
            inner_path += f'<use x="15" y="0" xlink:href="#orb{id_value}" />'

            # Second planet symbol
            inner_path += '<g transform="translate(30,0)">'
            inner_path += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{celestial_point_language[aspect["p2"]]["name"]}" />'
            inner_path += "</g>"

            # Difference in degrees
            inner_path += f'<text y="8" x="45" style="fill: var(--kerykeion-chart-color-paper-0); font-size: 10px;">{convert_decimal_to_degree_string(aspect["orbit"])}</text>'

            inner_path += "</g>"

    out = f'<g transform="translate({translate_x},{translate_y})">'
    out += f'<text y="-15" x="0" style="fill: var(--kerykeion-chart-color-paper-0); font-size: 14px;">{grid_title}:</text>'
    out += inner_path
    out += "</g>"

    return out


def calculate_moon_phase_chart_params(
    degrees_between_sun_and_moon: float
) -> dict:
    """
    Calculate normalized parameters used by the moon phase icon.

    Parameters:
    - degrees_between_sun_and_moon (float): The elongation between the sun and moon.

    Returns:
    - dict: Normalized phase data (angle, illuminated fraction, shadow ellipse radius).
    """
    if not math.isfinite(degrees_between_sun_and_moon):
        raise KerykeionException(
            f"Invalid degree value: {degrees_between_sun_and_moon}"
        )

    phase_angle = degrees_between_sun_and_moon % 360.0
    radians = math.radians(phase_angle)
    cosine = math.cos(radians)
    illuminated_fraction = (1.0 - cosine) / 2.0

    # Guard against floating point spillover outside [0, 1].
    illuminated_fraction = max(0.0, min(1.0, illuminated_fraction))

    return {
        "phase_angle": phase_angle,
        "illuminated_fraction": illuminated_fraction,
        "shadow_ellipse_rx": 10.0 * cosine,
    }


def draw_main_house_grid(
        main_subject_houses_list: list[KerykeionPointModel],
        house_cusp_generale_name_label: str = "Cusp",
        text_color: str = "#000000",
        x_position: int = 750,
        y_position: int = 30,
    ) -> str:
    """
    Generate SVG code for a grid of astrological houses for the main subject.

    Parameters:
    - main_subject_houses_list (list[KerykeionPointModel]): List of houses for the main subject.
    - house_cusp_generale_name_label (str): Label for the house cusp. Defaults to "Cusp".
    - text_color (str): Color of the text. Defaults to "#000000".
    - x_position (int): X position for the grid. Defaults to 720.
    - y_position (int): Y position for the grid. Defaults to 30.

    Returns:
    - str: The SVG code for the grid of houses.
    """
    svg_output = f'<g transform="translate({x_position},{y_position})">'

    line_increment = 10
    for i, house in enumerate(main_subject_houses_list):
        cusp_number = f"&#160;&#160;{i + 1}" if i < 9 else str(i + 1)
        svg_output += (
            f'<g transform="translate(0,{line_increment})">'
            f'<text text-anchor="end" x="40" style="fill:{text_color}; font-size: 10px;">{house_cusp_generale_name_label} {cusp_number}:</text>'
            f'<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#{house["sign"]}" /></g>'
            f'<text x="53" style="fill:{text_color}; font-size: 10px;"> {convert_decimal_to_degree_string(house["position"])}</text>'
            f'</g>'
        )
        line_increment += 14

    svg_output += "</g>"
    return svg_output


def draw_secondary_house_grid(
        secondary_subject_houses_list: list[KerykeionPointModel],
        house_cusp_generale_name_label: str = "Cusp",
        text_color: str = "#000000",
        x_position: int = 1015,
        y_position: int = 30,
    ) -> str:
    """
    Generate SVG code for a grid of astrological houses for the secondary subject.

    Parameters:
    - secondary_subject_houses_list (list[KerykeionPointModel]): List of houses for the secondary subject.
    - house_cusp_generale_name_label (str): Label for the house cusp. Defaults to "Cusp".
    - text_color (str): Color of the text. Defaults to "#000000".
    - x_position (int): X position for the grid. Defaults to 970.
    - y_position (int): Y position for the grid. Defaults to 30.

    Returns:
    - str: The SVG code for the grid of houses.
    """
    svg_output = f'<g transform="translate({x_position},{y_position})">'

    line_increment = 10
    for i, house in enumerate(secondary_subject_houses_list):
        cusp_number = f"&#160;&#160;{i + 1}" if i < 9 else str(i + 1)
        svg_output += (
            f'<g transform="translate(0,{line_increment})">'
            f'<text text-anchor="end" x="40" style="fill:{text_color}; font-size: 10px;">{house_cusp_generale_name_label} {cusp_number}:</text>'
            f'<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#{house["sign"]}" /></g>'
            f'<text x="53" style="fill:{text_color}; font-size: 10px;"> {convert_decimal_to_degree_string(house["position"])}</text>'
            f'</g>'
        )
        line_increment += 14

    svg_output += "</g>"
    return svg_output


def draw_main_planet_grid(
        planets_and_houses_grid_title: str,
        subject_name: str,
        available_kerykeion_celestial_points: list[KerykeionPointModel],
        chart_type: ChartType,
        celestial_point_language: KerykeionLanguageCelestialPointModel,
        text_color: str = "#000000",
        x_position: int = 645,
        y_position: int = 0,
    ) -> str:
    """
    Draw the planet grid (main subject) and optional title.

    The entire output is wrapped in a single SVG group `<g>` so the
    whole block can be repositioned by changing the group transform.

    Args:
        planets_and_houses_grid_title: Title prefix to show for eligible chart types.
        subject_name: Subject name to append to the title.
        available_kerykeion_celestial_points: Celestial points to render in the grid.
        chart_type: Chart type identifier (Literal string).
        celestial_point_language: Language model for celestial point decoding.
        text_color: Text color for labels (default: "#000000").
        x_position: X translation applied to the outer `<g>` (default: 620).
        y_position: Y translation applied to the outer `<g>` (default: 0).

    Returns:
        SVG string for the main planet grid wrapped in a `<g>`.
    """
    # Layout constants (kept identical to previous behavior)
    BASE_Y = 30
    HEADER_Y = 15  # Title baseline inside the wrapper
    LINE_START = 10
    LINE_STEP = 14

    # Wrap everything inside a single group so position can be changed once
    svg_output = f'<g transform="translate({x_position},{y_position})">'

    # Add title only for specific chart types
    if chart_type in ("Synastry", "Transit", "DualReturnChart"):
        svg_output += (
            f'<g transform="translate(0, {HEADER_Y})">'
            f'<text style="fill:{text_color}; font-size: 14px;">{planets_and_houses_grid_title} {subject_name}</text>'
            f'</g>'
        )

    end_of_line = "</g>"

    column_thresholds = _select_planet_grid_thresholds(chart_type)

    for i, planet in enumerate(available_kerykeion_celestial_points):
        offset, row_index = _planet_grid_layout_position(i, column_thresholds)
        line_height = LINE_START + (row_index * LINE_STEP)

        decoded_name = get_decoded_kerykeion_celestial_point_name(
            planet["name"],
            celestial_point_language,
        )

        svg_output += (
            f'<g transform="translate({offset},{BASE_Y + line_height})">'
            f'<text text-anchor="end" style="fill:{text_color}; font-size: 10px;">{decoded_name}</text>'
            f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{planet["name"]}" /></g>'
            f'<text text-anchor="start" x="19" style="fill:{text_color}; font-size: 10px;">{convert_decimal_to_degree_string(planet["position"])}</text>'
            f'<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#{planet["sign"]}" /></g>'
        )

        if planet["retrograde"]:
            svg_output += '<g transform="translate(74,-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'

        svg_output += end_of_line

    # Close the wrapper group
    svg_output += "</g>"

    return svg_output


def draw_secondary_planet_grid(
        planets_and_houses_grid_title: str,
        second_subject_name: str,
        second_subject_available_kerykeion_celestial_points: list[KerykeionPointModel],
        chart_type: ChartType,
        celestial_point_language: KerykeionLanguageCelestialPointModel,
        text_color: str = "#000000",
        x_position: int = 910,
        y_position: int = 0,
    ) -> str:
    """
    Draw the planet grid for the secondary subject and its title.

    The entire output is wrapped in a single SVG group `<g>` so the
    whole block can be repositioned by changing the group transform.

    Args:
        planets_and_houses_grid_title: Title prefix (used except for Transit charts).
        second_subject_name: Name of the secondary subject.
        second_subject_available_kerykeion_celestial_points: Celestial points to render for the secondary subject.
        chart_type: Chart type identifier (Literal string).
        celestial_point_language: Language model for celestial point decoding.
        text_color: Text color for labels (default: "#000000").
        x_position: X translation applied to the outer `<g>` (default: 870).
        y_position: Y translation applied to the outer `<g>` (default: 0).

    Returns:
        SVG string for the secondary planet grid wrapped in a `<g>`.
    """
    # Layout constants
    BASE_Y = 30
    HEADER_Y = 15
    LINE_START = 10
    LINE_STEP = 14

    # Open wrapper group
    svg_output = f'<g transform="translate({x_position},{y_position})">'

    # Title content and its relative x offset
    header_text = (
        second_subject_name if chart_type == "Transit"
        else f"{planets_and_houses_grid_title} {second_subject_name}"
    )
    header_x_offset = -50 if chart_type == "Transit" else 0

    svg_output += (
        f'<g transform="translate({header_x_offset}, {HEADER_Y})">'
        f'<text style="fill:{text_color}; font-size: 14px;">{header_text}</text>'
        f'</g>'
    )

    # Grid rows
    line_height = LINE_START
    end_of_line = "</g>"

    column_thresholds = _select_planet_grid_thresholds(chart_type)

    for i, t_planet in enumerate(second_subject_available_kerykeion_celestial_points):
        offset, row_index = _planet_grid_layout_position(i, column_thresholds)
        line_height = LINE_START + (row_index * LINE_STEP)

        second_decoded_name = get_decoded_kerykeion_celestial_point_name(
            t_planet["name"],
            celestial_point_language,
        )
        svg_output += (
            f'<g transform="translate({offset},{BASE_Y + line_height})">'
            f'<text text-anchor="end" style="fill:{text_color}; font-size: 10px;">{second_decoded_name}</text>'
            f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{t_planet["name"]}" /></g>'
            f'<text text-anchor="start" x="19" style="fill:{text_color}; font-size: 10px;">{convert_decimal_to_degree_string(t_planet["position"])}</text>'
            f'<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#{t_planet["sign"]}" /></g>'
        )

        if t_planet["retrograde"]:
            svg_output += '<g transform="translate(74,-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'

        svg_output += end_of_line


    # Close wrapper group
    svg_output += "</g>"

    return svg_output


def draw_transit_aspect_grid(
        stroke_color: str,
        available_planets: list,
        aspects: list,
        x_indent: int = 50,
        y_indent: int = 250,
        box_size: int = 14
    ) -> str:
    """
    Draws the aspect grid for the given planets and aspects. The default args value are specific for a stand alone
    aspect grid.

    Args:
        stroke_color (str): The color of the stroke.
        available_planets (list): List of all planets. Only planets with "is_active" set to True will be used.
        aspects (list): List of aspects.
        x_indent (int): The initial x-coordinate starting point.
        y_indent (int): The initial y-coordinate starting point.

    Returns:
        str: SVG string representing the aspect grid.
    """
    svg_output = ""
    style = f"stroke:{stroke_color}; stroke-width: 1px; stroke-width: 0.5px; fill:none"
    x_start = x_indent
    y_start = y_indent

    # Filter active planets
    active_planets = [planet for planet in available_planets if planet["is_active"]]

    # Reverse the list of active planets for the first iteration
    reversed_planets = active_planets[::-1]
    for index, planet_a in enumerate(reversed_planets):
        # Draw the grid box for the planet
        svg_output += f'<rect x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'
        svg_output += f'<use transform="scale(0.4)" x="{(x_start + 2) * 2.5}" y="{(y_start + 1) * 2.5}" xlink:href="#{planet_a["name"]}" />'
        x_start += box_size

    x_start = x_indent - box_size
    y_start = y_indent - box_size

    for index, planet_a in enumerate(reversed_planets):
        # Draw the grid box for the planet
        svg_output += f'<rect x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'
        svg_output += f'<use transform="scale(0.4)" x="{(x_start + 2) * 2.5}" y="{(y_start + 1) * 2.5}" xlink:href="#{planet_a["name"]}" />'
        y_start -= box_size

    x_start = x_indent
    y_start = y_indent
    y_start = y_start - box_size

    for index, planet_a in enumerate(reversed_planets):
        # Draw the grid box for the planet
        svg_output += f'<rect x="{x_start}" y="{y_start}" width="{box_size}" height="{box_size}" style="{style}"/>'

        # Update the starting coordinates for the next box
        y_start -= box_size

        # Coordinates for the aspect symbols
        x_aspect = x_start
        y_aspect = y_start + box_size

        # Iterate over the remaining planets
        for planet_b in reversed_planets:
            # Draw the grid box for the aspect
            svg_output += f'<rect x="{x_aspect}" y="{y_aspect}" width="{box_size}" height="{box_size}" style="{style}"/>'
            x_aspect += box_size

            # Check for aspects between the planets
            for aspect in aspects:
                if (aspect["p1"] == planet_a["id"] and aspect["p2"] == planet_b["id"]):
                    svg_output += f'<use  x="{x_aspect - box_size + 1}" y="{y_aspect + 1}" xlink:href="#orb{aspect["aspect_degrees"]}" />'

    return svg_output


def format_location_string(location: str, max_length: int = 35) -> str:
    """
    Format a location string to ensure it fits within a specified maximum length.

    If the location is longer than max_length, it attempts to shorten by using only
    the first and last parts separated by commas. If still too long, it truncates
    and adds ellipsis.

    Args:
        location: The original location string
        max_length: Maximum allowed length for the output string (default: 35)

    Returns:
        Formatted location string that fits within max_length
    """
    if len(location) > max_length:
        split_location = location.split(",")
        if len(split_location) > 1:
            shortened = split_location[0] + ", " + split_location[-1]
            if len(shortened) > max_length:
                return shortened[:max_length] + "..."
            return shortened
        else:
            return location[:max_length] + "..."
    return location


def format_datetime_with_timezone(iso_datetime_string: str) -> str:
    """
    Format an ISO datetime string with a custom format that includes properly formatted timezone.

    Args:
        iso_datetime_string: ISO formatted datetime string

    Returns:
        Formatted datetime string with properly formatted timezone offset (HH:MM)
    """
    dt = datetime.datetime.fromisoformat(iso_datetime_string)
    custom_format = dt.strftime('%Y-%m-%d %H:%M [%z]')
    custom_format = custom_format[:-3] + ':' + custom_format[-3:]

    return custom_format


def calculate_element_points(
    planets_settings: Sequence[KerykeionSettingsCelestialPointModel],
    celestial_points_names: Sequence[str],
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    *,
    method: ElementQualityDistributionMethod = "weighted",
    custom_weights: Optional[Mapping[str, float]] = None,
) -> dict[str, float]:
    """
    Calculate elemental totals for a subject using the selected strategy.

    Args:
        planets_settings: Planet configuration list (kept for API compatibility).
        celestial_points_names: Celestial point names to include.
        subject: Astrological subject with planetary data.
        method: Calculation method (pure_count or weighted). Defaults to weighted.
        custom_weights: Optional overrides for point weights keyed by name.

    Returns:
        Dictionary mapping each element to its accumulated total.
    """
    normalized_names = [name.lower() for name in celestial_points_names]
    weight_lookup, fallback_weight = _prepare_weight_lookup(method, custom_weights)

    return _calculate_distribution_for_subject(
        subject,
        normalized_names,
        _SIGN_TO_ELEMENT,
        _ELEMENT_KEYS,
        weight_lookup,
        fallback_weight,
    )


def calculate_synastry_element_points(
    planets_settings: Sequence[KerykeionSettingsCelestialPointModel],
    celestial_points_names: Sequence[str],
    subject1: AstrologicalSubjectModel,
    subject2: AstrologicalSubjectModel,
    *,
    method: ElementQualityDistributionMethod = "weighted",
    custom_weights: Optional[Mapping[str, float]] = None,
) -> dict[str, float]:
    """
    Calculate combined element percentages for a synastry chart.

    Args:
        planets_settings: Planet configuration list (unused but preserved).
        celestial_points_names: Celestial point names to process.
        subject1: First astrological subject.
        subject2: Second astrological subject.
        method: Calculation strategy (pure_count or weighted).
        custom_weights: Optional overrides for point weights.

    Returns:
        Dictionary with element percentages summing to 100.
    """
    normalized_names = [name.lower() for name in celestial_points_names]
    weight_lookup, fallback_weight = _prepare_weight_lookup(method, custom_weights)

    subject1_totals = _calculate_distribution_for_subject(
        subject1,
        normalized_names,
        _SIGN_TO_ELEMENT,
        _ELEMENT_KEYS,
        weight_lookup,
        fallback_weight,
    )
    subject2_totals = _calculate_distribution_for_subject(
        subject2,
        normalized_names,
        _SIGN_TO_ELEMENT,
        _ELEMENT_KEYS,
        weight_lookup,
        fallback_weight,
    )

    combined_totals = {key: subject1_totals[key] + subject2_totals[key] for key in _ELEMENT_KEYS}
    total_points = sum(combined_totals.values())

    if total_points == 0:
        return {key: 0.0 for key in _ELEMENT_KEYS}

    return {key: (combined_totals[key] / total_points) * 100.0 for key in _ELEMENT_KEYS}


def draw_house_comparison_grid(
        house_comparison: "HouseComparisonModel",
        celestial_point_language: KerykeionLanguageCelestialPointModel,
        active_points: list[AstrologicalPoint],
        *,
        points_owner_subject_number: Literal[1, 2] = 1,
        text_color: str = "var(--kerykeion-color-neutral-content)",
        house_position_comparison_label: str = "House Position Comparison",
        return_point_label: str = "Return Point",
        return_label: str = "DualReturnChart",
        radix_label: str = "Radix",
        x_position: int = 1100,
        y_position: int = 0,
) -> str:
    """
    Generate SVG code for displaying a comparison of points across houses between two charts.

    Parameters:
    - house_comparison ("HouseComparisonModel"): Model containing house comparison data,
      including first_subject_name, second_subject_name, and points in houses.
    - celestial_point_language (KerykeionLanguageCelestialPointModel): Language model for celestial points
    - active_celestial_points (list[KerykeionPointModel]): List of active celestial points to display
    - text_color (str): Color for the text elements

    Returns:
    - str: SVG code for the house comparison grid.
    """
    if points_owner_subject_number == 1:
        comparison_data = house_comparison.first_points_in_second_houses
    else:
        comparison_data = house_comparison.second_points_in_first_houses

    svg_output = f'<g transform="translate({x_position},{y_position})">'

    # Add title
    svg_output += f'<text text-anchor="start" x="0" y="-15" style="fill:{text_color}; font-size: 14px;">{house_position_comparison_label}</text>'

    # Add column headers
    line_increment = 10
    svg_output += (
        f'<g transform="translate(0,{line_increment})">'
        f'<text text-anchor="start" x="0" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{return_point_label}</text>'
        f'<text text-anchor="start" x="77" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{return_label}</text>'
        f'<text text-anchor="start" x="132" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{radix_label}</text>'
        f'</g>'
    )
    line_increment += 15

    # Create a dictionary to store all points by name for combined display
    all_points_by_name = {}

    for point in comparison_data:
        # Only process points that are active
        if point.point_name in active_points and point.point_name not in all_points_by_name:
            all_points_by_name[point.point_name] = {
                "name": point.point_name,
                "secondary_house": point.projected_house_number,
                "native_house": point.point_owner_house_number
            }

    # Display all points organized by name
    for name, point_data in all_points_by_name.items():
        native_house = point_data.get("native_house", "-")
        secondary_house = point_data.get("secondary_house", "-")

        svg_output += (
            f'<g transform="translate(0,{line_increment})">'
            f'<g transform="translate(0,-9)"><use transform="scale(0.4)" xlink:href="#{name}" /></g>'
            f'<text text-anchor="start" x="15" style="fill:{text_color}; font-size: 10px;">{get_decoded_kerykeion_celestial_point_name(name, celestial_point_language)}</text>'
            f'<text text-anchor="start" x="90" style="fill:{text_color}; font-size: 10px;">{native_house}</text>'
            f'<text text-anchor="start" x="140" style="fill:{text_color}; font-size: 10px;">{secondary_house}</text>'
            f'</g>'
        )
        line_increment += 12

    svg_output += "</g>"

    return svg_output


def draw_single_house_comparison_grid(
        house_comparison: "HouseComparisonModel",
        celestial_point_language: KerykeionLanguageCelestialPointModel,
        active_points: list[AstrologicalPoint],
        *,
        points_owner_subject_number: Literal[1, 2] = 1,
        text_color: str = "var(--kerykeion-color-neutral-content)",
        house_position_comparison_label: str = "House Position Comparison",
        return_point_label: str = "Return Point",
        natal_house_label: str = "Natal House",
        x_position: int = 1030,
        y_position: int = 0,
) -> str:
    """
    Generate SVG code for displaying celestial points and their house positions.

    Parameters:
    - house_comparison ("HouseComparisonModel"): Model containing house comparison data,
      including first_subject_name, second_subject_name, and points in houses.
    - celestial_point_language (KerykeionLanguageCelestialPointModel): Language model for celestial points
    - active_points (list[AstrologicalPoint]): List of active celestial points to display
    - points_owner_subject_number (Literal[1, 2]): Which subject's points to display (1 for first, 2 for second)
    - text_color (str): Color for the text elements
    - house_position_comparison_label (str): Label for the house position comparison grid
    - return_point_label (str): Label for the return point column
    - house_position_label (str): Label for the house position column
    - x_position (int): X position for the grid
    - y_position (int): Y position for the grid

    Returns:
    - str: SVG code for the house position grid.
    """
    if points_owner_subject_number == 1:
        comparison_data = house_comparison.first_points_in_second_houses
    else:
        comparison_data = house_comparison.second_points_in_first_houses

    svg_output = f'<g transform="translate({x_position},{y_position})">'

    # Add title
    svg_output += f'<text text-anchor="start" x="0" y="-15" style="fill:{text_color}; font-size: 14px;">{house_position_comparison_label}</text>'

    # Add column headers
    line_increment = 10
    svg_output += (
        f'<g transform="translate(0,{line_increment})">'
        f'<text text-anchor="start" x="0" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{return_point_label}</text>'
        f'<text text-anchor="start" x="77" style="fill:{text_color}; font-weight: bold; font-size: 10px;">{natal_house_label}</text>'
        f'</g>'
    )
    line_increment += 15

    # Create a dictionary to store all points by name for combined display
    all_points_by_name = {}

    for point in comparison_data:
        # Only process points that are active
        if point.point_name in active_points and point.point_name not in all_points_by_name:
            all_points_by_name[point.point_name] = {
                "name": point.point_name,
                "house": point.projected_house_number
            }

    # Display all points organized by name
    for name, point_data in all_points_by_name.items():
        house = point_data.get("house", "-")

        svg_output += (
            f'<g transform="translate(0,{line_increment})">'
            f'<g transform="translate(0,-9)"><use transform="scale(0.4)" xlink:href="#{name}" /></g>'
            f'<text text-anchor="start" x="15" style="fill:{text_color}; font-size: 10px;">{get_decoded_kerykeion_celestial_point_name(name, celestial_point_language)}</text>'
            f'<text text-anchor="start" x="90" style="fill:{text_color}; font-size: 10px;">{house}</text>'
            f'</g>'
        )
        line_increment += 12

    svg_output += "</g>"

    return svg_output


def makeLunarPhase(degrees_between_sun_and_moon: float, latitude: float) -> str:
    """
    Generate SVG representation of lunar phase.

    Parameters:
    - degrees_between_sun_and_moon (float): Angle between sun and moon in degrees
    - latitude (float): Observer's latitude (no longer used, kept for backward compatibility)

    Returns:
    - str: SVG representation of lunar phase
    """
    params = calculate_moon_phase_chart_params(degrees_between_sun_and_moon)

    phase_angle = params["phase_angle"]
    illuminated_fraction = 1.0 - params["illuminated_fraction"]
    shadow_ellipse_rx = abs(params["shadow_ellipse_rx"])

    radius = 10.0
    center_x = 20.0
    center_y = 10.0

    bright_color = "var(--kerykeion-chart-color-lunar-phase-1)"
    shadow_color = "var(--kerykeion-chart-color-lunar-phase-0)"

    is_waxing = phase_angle < 180.0

    if illuminated_fraction <= 1e-6:
        base_fill = shadow_color
        overlay_path = ""
        overlay_fill = ""
    elif 1.0 - illuminated_fraction <= 1e-6:
        base_fill = bright_color
        overlay_path = ""
        overlay_fill = ""
    else:
        is_lit_major = illuminated_fraction >= 0.5
        if is_lit_major:
            base_fill = bright_color
            overlay_fill = shadow_color
            overlay_side = "left" if is_waxing else "right"
        else:
            base_fill = shadow_color
            overlay_fill = bright_color
            overlay_side = "right" if is_waxing else "left"

        # The illuminated limb is the orthographic projection of the lunar terminator;
        # it appears as an ellipse with vertical radius equal to the lunar radius and
        # horizontal radius scaled by |cos(phase)|.
        def build_lune_path(side: str, ellipse_rx: float) -> str:
            ellipse_rx = max(0.0, min(radius, ellipse_rx))
            top_y = center_y - radius
            bottom_y = center_y + radius
            circle_sweep = 1 if side == "right" else 0

            if ellipse_rx <= 1e-6:
                return (
                    f"M {center_x:.4f} {top_y:.4f}"
                    f" A {radius:.4f} {radius:.4f} 0 0 {circle_sweep} {center_x:.4f} {bottom_y:.4f}"
                    f" L {center_x:.4f} {top_y:.4f}"
                    " Z"
                )

            return (
                f"M {center_x:.4f} {top_y:.4f}"
                f" A {radius:.4f} {radius:.4f} 0 0 {circle_sweep} {center_x:.4f} {bottom_y:.4f}"
                f" A {ellipse_rx:.4f} {radius:.4f} 0 0 {circle_sweep} {center_x:.4f} {top_y:.4f}"
                " Z"
            )

        overlay_path = build_lune_path(overlay_side, shadow_ellipse_rx)

    svg_lines = [
        '<g transform="rotate(0 20 10)">',
        '    <defs>',
        '        <clipPath id="moonPhaseCutOffCircle">',
        '            <circle cx="20" cy="10" r="10" />',
        '        </clipPath>',
        '    </defs>',
        f'    <circle cx="20" cy="10" r="10" style="fill: {base_fill}" />',
    ]

    if overlay_path:
        svg_lines.append(
            f'    <path d="{overlay_path}" style="fill: {overlay_fill}" clip-path="url(#moonPhaseCutOffCircle)" />'
        )

    svg_lines.append(
        '    <circle cx="20" cy="10" r="10" style="fill: none; stroke: var(--kerykeion-chart-color-lunar-phase-0); stroke-width: 0.5px; stroke-opacity: 0.5" />'
    )
    svg_lines.append('</g>')

    return "\n".join(svg_lines)


def calculate_quality_points(
    planets_settings: Sequence[KerykeionSettingsCelestialPointModel],
    celestial_points_names: Sequence[str],
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    *,
    method: ElementQualityDistributionMethod = "weighted",
    custom_weights: Optional[Mapping[str, float]] = None,
) -> dict[str, float]:
    """
    Calculate modality totals for a subject using the selected strategy.

    Args:
        planets_settings: Planet configuration list (kept for API compatibility).
        celestial_points_names: Celestial point names to include.
        subject: Astrological subject with planetary data.
        method: Calculation method (pure_count or weighted). Defaults to weighted.
        custom_weights: Optional overrides for point weights keyed by name.

    Returns:
        Dictionary mapping each modality to its accumulated total.
    """
    normalized_names = [name.lower() for name in celestial_points_names]
    weight_lookup, fallback_weight = _prepare_weight_lookup(method, custom_weights)

    return _calculate_distribution_for_subject(
        subject,
        normalized_names,
        _SIGN_TO_QUALITY,
        _QUALITY_KEYS,
        weight_lookup,
        fallback_weight,
    )


def calculate_synastry_quality_points(
    planets_settings: Sequence[KerykeionSettingsCelestialPointModel],
    celestial_points_names: Sequence[str],
    subject1: AstrologicalSubjectModel,
    subject2: AstrologicalSubjectModel,
    *,
    method: ElementQualityDistributionMethod = "weighted",
    custom_weights: Optional[Mapping[str, float]] = None,
) -> dict[str, float]:
    """
    Calculate combined modality percentages for a synastry chart.

    Args:
        planets_settings: Planet configuration list (unused but preserved).
        celestial_points_names: Celestial point names to process.
        subject1: First astrological subject.
        subject2: Second astrological subject.
        method: Calculation strategy (pure_count or weighted).
        custom_weights: Optional overrides for point weights.

    Returns:
        Dictionary with modality percentages summing to 100.
    """
    normalized_names = [name.lower() for name in celestial_points_names]
    weight_lookup, fallback_weight = _prepare_weight_lookup(method, custom_weights)

    subject1_totals = _calculate_distribution_for_subject(
        subject1,
        normalized_names,
        _SIGN_TO_QUALITY,
        _QUALITY_KEYS,
        weight_lookup,
        fallback_weight,
    )
    subject2_totals = _calculate_distribution_for_subject(
        subject2,
        normalized_names,
        _SIGN_TO_QUALITY,
        _QUALITY_KEYS,
        weight_lookup,
        fallback_weight,
    )

    combined_totals = {key: subject1_totals[key] + subject2_totals[key] for key in _QUALITY_KEYS}
    total_points = sum(combined_totals.values())

    if total_points == 0:
        return {key: 0.0 for key in _QUALITY_KEYS}

    return {key: (combined_totals[key] / total_points) * 100.0 for key in _QUALITY_KEYS}
