import math
import datetime
from kerykeion.kr_types import KerykeionException, ChartType
from kerykeion.kr_types.kr_literals import AstrologicalPoint
from typing import Union, Literal, TYPE_CHECKING
from kerykeion.kr_types.kr_models import AspectModel, KerykeionPointModel, CompositeSubjectModel, PlanetReturnModel, AstrologicalSubjectModel
from kerykeion.kr_types.settings_models import KerykeionLanguageCelestialPointModel, KerykeionSettingsCelestialPointModel


if TYPE_CHECKING:
    from kerykeion import HouseComparisonModel

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
    if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
        dropin: Union[int, float] = 0
    else:
        dropin = c1
    slice = f'<path d="M{str(r)},{str(r)} L{str(dropin + sliceToX(num, r - dropin, offset))},{str(dropin + sliceToY(num, r - dropin, offset))} A{str(r - dropin)},{str(r - dropin)} 0 0,0 {str(dropin + sliceToX(num + 1, r - dropin, offset))},{str(dropin + sliceToY(num + 1, r - dropin, offset))} z" style="{style}"/>'

    # symbols
    offset = offset + 15
    # check transit
    if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
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
        f'<g kr:node="Aspect" kr:aspectname="{aspect["aspect"]}" kr:to="{aspect["p1_name"]}" kr:tooriginaldegrees="{aspect["p1_abs_pos"]}" kr:from="{aspect["p2_name"]}" kr:fromoriginaldegrees="{aspect["p2_abs_pos"]}">'
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
    if chart_type == "Synastry" or chart_type == "Transit" or chart_type == "Return":
        return f'<circle cx="{r}" cy="{r}" r="{r - 36}" style="fill: none; stroke: {stroke_color}; stroke-width: 1px; stroke-opacity:.4;" />'
    else:
        if c1 is None:
            raise KerykeionException("c1 is None")

        return (
            f'<circle cx="{r}" cy="{r}" r="{r - c1}" style="fill: none; stroke: {stroke_color}; stroke-width: 1px; " />'
        )


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

    if chart_type == "Synastry" or chart_type == "Transit" or chart_type == "Return":
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
    if chart_type in {"Synastry", "Transit", "Return"}:
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

    Returns:
    - A string containing the SVG path for the houses cusps and text numbers.
    """

    path = ""
    xr = 12

    for i in range(xr):
        # Determine offsets based on chart type
        dropin, roff, t_roff = (160, 72, 36) if chart_type in ["Transit", "Synastry", "Return"] else (c3, c1, False)

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

        if chart_type in ["Transit", "Synastry", "Return"]:
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
            path += f'<g kr:node="HouseNumber">'
            path += f'<text style="fill: var(--kerykeion-chart-color-house-number); fill-opacity: {fill_opacity}; font-size: 14px"><tspan x="{xtext - 3}" y="{ytext + 3}">{i + 1}</tspan></text>'
            path += f"</g>"

            # Add the house cusp line for the second subject
            stroke_opacity = "0" if chart_type == "Transit" else ".3"
            path += f'<g kr:node="Cusp">'
            path += f"<line x1='{t_x1}' y1='{t_y1}' x2='{t_x2}' y2='{t_y2}' style='stroke: {t_linecolor}; stroke-width: 1px; stroke-opacity:{stroke_opacity};'/>"
            path += f"</g>"

        # Adjust dropin based on chart type
        dropin = {"Transit": 84, "Synastry": 84, "Return": 84, "ExternalNatal": 100}.get(chart_type, 48)
        xtext = sliceToX(0, (r - dropin), text_offset) + dropin
        ytext = sliceToY(0, (r - dropin), text_offset) + dropin

        # Add the house cusp line for the first subject
        path += f'<g kr:node="Cusp">'
        path += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {linecolor}; stroke-width: 1px; stroke-dasharray:3,2; stroke-opacity:.4;"/>'
        path += f"</g>"

        # Add the house number text for the first subject
        path += f'<g kr:node="HouseNumber">'
        path += f'<text style="fill: var(--kerykeion-chart-color-house-number); fill-opacity: .6; font-size: 14px"><tspan x="{xtext - 3}" y="{ytext + 3}">{i + 1}</tspan></text>'
        path += f"</g>"

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
    max_columns: int = 6
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

    Returns:
    - A string containing the SVG path data for the aspect transit grid.
    """

    if isinstance(celestial_point_language, dict):
        celestial_point_language = KerykeionLanguageCelestialPointModel(**celestial_point_language)

    # If not instance of AspectModel, convert to AspectModel
    if aspects_list and isinstance(aspects_list[0], dict):
        aspects_list = [AspectModel(**aspect) for aspect in aspects_list]  # type: ignore

    inner_path = ""

    for i, aspect in enumerate(aspects_list):
        # Calculate which column this aspect belongs in
        current_column = i // aspects_per_column

        # Calculate horizontal position based on column
        horizontal_position = current_column * column_width

        # Calculate vertical position within the column
        current_line = i % aspects_per_column
        vertical_position = current_line * line_height

        # Special handling for many aspects - if we exceed max_columns
        if current_column >= max_columns:
            # Calculate how many aspects will overflow beyond the max columns
            overflow_aspects = len(aspects_list) - (aspects_per_column * max_columns)
            if overflow_aspects > 0:
                # Adjust the starting vertical position to move text up
                vertical_position = vertical_position - (overflow_aspects * line_height)

        inner_path += f'<g transform="translate({horizontal_position},{vertical_position})">'

        # First planet symbol
        inner_path += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{celestial_point_language[aspect["p1"]]["name"]}" />'

        # Aspect symbol
        aspect_name = aspect["aspect"]
        id_value = next((a["degree"] for a in aspects_settings if a["name"] == aspect_name), None)  # type: ignore
        inner_path += f'<use x="15" y="0" xlink:href="#orb{id_value}" />'

        # Second planet symbol
        inner_path += f'<g transform="translate(30,0)">'
        inner_path += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{celestial_point_language[aspect["p2"]]["name"]}" />'
        inner_path += f"</g>"

        # Difference in degrees
        inner_path += f'<text y="8" x="45" style="fill: var(--kerykeion-chart-color-paper-0); font-size: 10px;">{convert_decimal_to_degree_string(aspect["orbit"])}</text>'

        inner_path += f"</g>"

    out = '<g transform="translate(565,273)">'
    out += f'<text y="-15" x="0" style="fill: var(--kerykeion-chart-color-paper-0); font-size: 14px;">{grid_title}:</text>'
    out += inner_path
    out += '</g>'

    return out


def calculate_moon_phase_chart_params(
    degrees_between_sun_and_moon: float,
    latitude: float
) -> dict:
    """
    Calculate the parameters for the moon phase chart.

    Parameters:
    - degrees_between_sun_and_moon (float): The degrees between the sun and the moon.
    - latitude (float): The latitude for rotation calculation.

    Returns:
    - dict: The moon phase chart parameters.
    """
    deg = degrees_between_sun_and_moon

    # Initialize variables for lunar phase properties
    circle_center_x = None
    circle_radius = None

    # Determine lunar phase properties based on the degree
    if deg < 90.0:
        max_radius = deg
        if deg > 80.0:
            max_radius = max_radius * max_radius
        circle_center_x = 20.0 + (deg / 90.0) * (max_radius + 10.0)
        circle_radius = 10.0 + (deg / 90.0) * max_radius

    elif deg < 180.0:
        max_radius = 180.0 - deg
        if deg < 100.0:
            max_radius = max_radius * max_radius
        circle_center_x = 20.0 + ((deg - 90.0) / 90.0 * (max_radius + 10.0)) - (max_radius + 10.0)
        circle_radius = 10.0 + max_radius - ((deg - 90.0) / 90.0 * max_radius)

    elif deg < 270.0:
        max_radius = deg - 180.0
        if deg > 260.0:
            max_radius = max_radius * max_radius
        circle_center_x = 20.0 + ((deg - 180.0) / 90.0 * (max_radius + 10.0))
        circle_radius = 10.0 + ((deg - 180.0) / 90.0 * max_radius)

    elif deg < 361.0:
        max_radius = 360.0 - deg
        if deg < 280.0:
            max_radius = max_radius * max_radius
        circle_center_x = 20.0 + ((deg - 270.0) / 90.0 * (max_radius + 10.0)) - (max_radius + 10.0)
        circle_radius = 10.0 + max_radius - ((deg - 270.0) / 90.0 * max_radius)

    else:
        raise KerykeionException(f"Invalid degree value: {deg}")


    # Calculate rotation based on latitude
    lunar_phase_rotate = -90.0 - latitude

    return {
        "circle_center_x": circle_center_x,
        "circle_radius": circle_radius,
        "lunar_phase_rotate": lunar_phase_rotate,
    }


def draw_house_grid(
        main_subject_houses_list: list[KerykeionPointModel],
        chart_type: ChartType,
        secondary_subject_houses_list: Union[list[KerykeionPointModel], None] = None,
        text_color: str = "#000000",
        house_cusp_generale_name_label: str = "Cusp",
    ) -> str:
    """
    Generate SVG code for a grid of astrological houses.

    Parameters:
    - main_houses (list[KerykeionPointModel]): List of houses for the main subject.
    - chart_type (ChartType): Type of the chart (e.g., Synastry, Transit).
    - secondary_houses (list[KerykeionPointModel], optional): List of houses for the secondary subject.
    - text_color (str): Color of the text.
    - cusp_label (str): Label for the house cusp.

    Returns:
    - str: The SVG code for the grid of houses.
    """

    if chart_type in ["Synastry", "Transit", "Return"] and secondary_subject_houses_list is None:
        raise KerykeionException("secondary_houses is None")

    svg_output = '<g transform="translate(700,0)">'

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

    if chart_type == "Synastry" or chart_type == "Return":
        svg_output += '<!-- Synastry Houses -->'
        svg_output += '<g transform="translate(950, 0)">'
        line_increment = 10

        for i, house in enumerate(secondary_subject_houses_list): # type: ignore
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


def draw_planet_grid(
        planets_and_houses_grid_title: str,
        subject_name: str,
        available_kerykeion_celestial_points: list[KerykeionPointModel],
        chart_type: ChartType,
        celestial_point_language: KerykeionLanguageCelestialPointModel,
        second_subject_name: Union[str, None] = None,
        second_subject_available_kerykeion_celestial_points: Union[list[KerykeionPointModel], None] = None,
        text_color: str = "#000000",
    ) -> str:
    """
    Draws the planet grid for the given celestial points and chart type.

    Args:
        planets_and_houses_grid_title (str): Title of the grid.
        subject_name (str): Name of the subject.
        available_kerykeion_celestial_points (list[KerykeionPointModel]): List of celestial points for the subject.
        chart_type (ChartType): Type of the chart.
        celestial_point_language (KerykeionLanguageCelestialPointModel): Language model for celestial points.
        second_subject_name (str, optional): Name of the second subject. Defaults to None.
        second_subject_available_kerykeion_celestial_points (list[KerykeionPointModel], optional): List of celestial points for the second subject. Defaults to None.
        text_color (str, optional): Color of the text. Defaults to "#000000".

    Returns:
        str: The SVG output for the planet grid.
    """
    line_height = 10
    offset = 0
    offset_between_lines = 14

    if chart_type == "Synastry":
        svg_output = (
            f'<g transform="translate(0, -15)">'
            f'<text style="fill:{text_color}; font-size: 14px;">{planets_and_houses_grid_title} {subject_name}</text>'
            f'</g>'
        )
    elif chart_type == "Transit":
        svg_output = (
            f'<g transform="translate(0, -15)">'
            f'<text style="fill:{text_color}; font-size: 14px;">{planets_and_houses_grid_title} {subject_name}</text>'
            f'</g>'
        )
    elif chart_type == "Return":
        svg_output = (
            f'<g transform="translate(0, -15)">'
            f'<text style="fill:{text_color}; font-size: 14px;">{planets_and_houses_grid_title} {subject_name}</text>'
            f'</g>'
        )
    else:
        svg_output = ""

    end_of_line = "</g>"

    for i, planet in enumerate(available_kerykeion_celestial_points):
        if i == 22:
            line_height = 10
            offset = -125

        decoded_name = get_decoded_kerykeion_celestial_point_name(planet["name"], celestial_point_language)
        svg_output += (
            f'<g transform="translate({offset},{line_height})">'
            f'<text text-anchor="end" style="fill:{text_color}; font-size: 10px;">{decoded_name}</text>'
            f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{planet["name"]}" /></g>'
            f'<text text-anchor="start" x="19" style="fill:{text_color}; font-size: 10px;">{convert_decimal_to_degree_string(planet["position"])}</text>'
            f'<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#{planet["sign"]}" /></g>'
        )

        if planet["retrograde"]:
            svg_output += '<g transform="translate(74,-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'

        svg_output += end_of_line
        line_height += offset_between_lines

    if chart_type in ["Transit", "Synastry", "Return"]:
        if second_subject_available_kerykeion_celestial_points is None:
            raise KerykeionException("second_subject_available_kerykeion_celestial_points is None")

        if chart_type == "Transit":
            svg_output += (
                f'<g transform="translate(200, -15)">'
                f'<text style="fill:{text_color}; font-size: 14px;">{second_subject_name}</text>'
            )
        elif chart_type == "Return":
            svg_output += (
                f'<g transform="translate(250, -15)">'
                f'<text style="fill:{text_color}; font-size: 14px;">{planets_and_houses_grid_title} {second_subject_name}</text>'
            )
        else:
            svg_output += (
                f'<g transform="translate(250, -15)">'
                f'<text style="fill:{text_color}; font-size: 14px;">{planets_and_houses_grid_title} {second_subject_name}</text>'
            )

        svg_output += end_of_line

        second_line_height = 10
        second_offset = 250

        for i, t_planet in enumerate(second_subject_available_kerykeion_celestial_points):
            # if i == 27:
            #     second_line_height = 10
            #    second_offset = -120

            second_decoded_name = get_decoded_kerykeion_celestial_point_name(t_planet["name"], celestial_point_language)
            svg_output += (
                f'<g transform="translate({second_offset},{second_line_height})">'
                f'<text text-anchor="end" style="fill:{text_color}; font-size: 10px;">{second_decoded_name}</text>'
                f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{t_planet["name"]}" /></g>'
                f'<text text-anchor="start" x="19" style="fill:{text_color}; font-size: 10px;">{convert_decimal_to_degree_string(t_planet["position"])}</text>'
                f'<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#{t_planet["sign"]}" /></g>'
            )

            if t_planet["retrograde"]:
                svg_output += '<g transform="translate(74,-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'

            svg_output += end_of_line
            second_line_height += offset_between_lines

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
        planets_settings: list[KerykeionSettingsCelestialPointModel],
        celestial_points_names: list[str],
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    ):
    """
    Calculate elemental point totals based on planetary positions.

    Args:
        planets_settings (list): List of planet configuration dictionaries
        celestial_points_names (list): List of celestial point names to process
        subject: Astrological subject with get() method for accessing planet data

    Returns:
        dict: Dictionary with element point totals for 'fire', 'earth', 'air', and 'water'
    """
    ZODIAC = (
        {"name": "Ari", "element": "fire"},
        {"name": "Tau", "element": "earth"},
        {"name": "Gem", "element": "air"},
        {"name": "Can", "element": "water"},
        {"name": "Leo", "element": "fire"},
        {"name": "Vir", "element": "earth"},
        {"name": "Lib", "element": "air"},
        {"name": "Sco", "element": "water"},
        {"name": "Sag", "element": "fire"},
        {"name": "Cap", "element": "earth"},
        {"name": "Aqu", "element": "air"},
        {"name": "Pis", "element": "water"},
    )

    # Initialize element point totals
    element_totals = {
        "fire": 0.0,
        "earth": 0.0,
        "air": 0.0,
        "water": 0.0
    }

    # Make list of the points sign
    points_sign = [subject.get(planet).sign_num for planet in celestial_points_names]

    for i in range(len(planets_settings)):
        # Add points to appropriate element
        element = ZODIAC[points_sign[i]]["element"]
        element_totals[element] += planets_settings[i]["element_points"]

    return element_totals


def calculate_synastry_element_points(
        planets_settings: list[KerykeionSettingsCelestialPointModel],
        celestial_points_names: list[str],
        subject1: AstrologicalSubjectModel,
        subject2: AstrologicalSubjectModel,
    ):
    """
    Calculate elemental point totals for both subjects in a synastry chart.

    Args:
        planets_settings (list): List of planet configuration dictionaries
        celestial_points_names (list): List of celestial point names to process
        subject1: First astrological subject with get() method for accessing planet data
        subject2: Second astrological subject with get() method for accessing planet data

    Returns:
        dict: Dictionary with element point totals as percentages, where the sum equals 100%
    """
    ZODIAC = (
        {"name": "Ari", "element": "fire"},
        {"name": "Tau", "element": "earth"},
        {"name": "Gem", "element": "air"},
        {"name": "Can", "element": "water"},
        {"name": "Leo", "element": "fire"},
        {"name": "Vir", "element": "earth"},
        {"name": "Lib", "element": "air"},
        {"name": "Sco", "element": "water"},
        {"name": "Sag", "element": "fire"},
        {"name": "Cap", "element": "earth"},
        {"name": "Aqu", "element": "air"},
        {"name": "Pis", "element": "water"},
    )

    # Initialize combined element point totals
    combined_totals = {
        "fire": 0.0,
        "earth": 0.0,
        "air": 0.0,
        "water": 0.0
    }

    # Make list of the points sign for both subjects
    subject1_points_sign = [subject1.get(planet).sign_num for planet in celestial_points_names]
    subject2_points_sign = [subject2.get(planet).sign_num for planet in celestial_points_names]

    # Calculate element points for subject 1
    for i in range(len(planets_settings)):
        # Add points to appropriate element
        element1 = ZODIAC[subject1_points_sign[i]]["element"]
        combined_totals[element1] += planets_settings[i]["element_points"]

    # Calculate element points for subject 2
    for i in range(len(planets_settings)):
        # Add points to appropriate element
        element2 = ZODIAC[subject2_points_sign[i]]["element"]
        combined_totals[element2] += planets_settings[i]["element_points"]

    # Calculate total points across all elements
    total_points = sum(combined_totals.values())

    # Convert to percentages (total = 100%)
    if total_points > 0:
        for element in combined_totals:
            combined_totals[element] = (combined_totals[element] / total_points) * 100.0

    return combined_totals


def draw_house_comparison_grid(
        house_comparison: "HouseComparisonModel",
        celestial_point_language: KerykeionLanguageCelestialPointModel,
        active_points: list[AstrologicalPoint],
        *,
        points_owner_subject_number: Literal[1, 2] = 1,
        text_color: str = "var(--kerykeion-color-neutral-content)",
        house_position_comparison_label: str = "House Position Comparison",
        return_point_label: str = "Return Point",
        return_label: str = "Return",
        radix_label: str = "Radix",
        x_position: int = 1030,
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
    - latitude (float): Observer's latitude for correct orientation

    Returns:
    - str: SVG representation of lunar phase
    """
    # Calculate parameters for the lunar phase visualization
    params = calculate_moon_phase_chart_params(degrees_between_sun_and_moon, latitude)

    # Extract the calculated values
    lunar_phase_circle_center_x = params["circle_center_x"]
    lunar_phase_circle_radius = params["circle_radius"]
    lunar_phase_rotate = params["lunar_phase_rotate"]

    # Generate the SVG for the lunar phase
    svg = (
        f'<g transform="rotate({lunar_phase_rotate} 20 10)">\n'
        f'    <defs>\n'
        f'        <clipPath id="moonPhaseCutOffCircle">\n'
        f'            <circle cx="20" cy="10" r="10" />\n'
        f'        </clipPath>\n'
        f'    </defs>\n'
        f'    <circle cx="20" cy="10" r="10" style="fill: var(--kerykeion-chart-color-lunar-phase-0)" />\n'
        f'    <circle cx="{lunar_phase_circle_center_x}" cy="10" r="{lunar_phase_circle_radius}" style="fill: var(--kerykeion-chart-color-lunar-phase-1)" clip-path="url(#moonPhaseCutOffCircle)" />\n'
        f'    <circle cx="20" cy="10" r="10" style="fill: none; stroke: var(--kerykeion-chart-color-lunar-phase-0); stroke-width: 0.5px; stroke-opacity: 0.5" />\n'
        f'</g>'
    )

    return svg


def calculate_quality_points(
        planets_settings: list[KerykeionSettingsCelestialPointModel],
        celestial_points_names: list[str],
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
    ):
    """
    Calculate quality point totals based on planetary positions.

    Args:
        planets_settings (list): List of planet configuration dictionaries
        celestial_points_names (list): List of celestial point names to process
        subject: Astrological subject with get() method for accessing planet data
        planet_in_zodiac_extra_points (int): Extra points awarded for planets in their home sign

    Returns:
        dict: Dictionary with quality point totals for 'cardinal', 'fixed', and 'mutable'
    """
    ZODIAC = (
        {"name": "Ari", "quality": "cardinal"},
        {"name": "Tau", "quality": "fixed"},
        {"name": "Gem", "quality": "mutable"},
        {"name": "Can", "quality": "cardinal"},
        {"name": "Leo", "quality": "fixed"},
        {"name": "Vir", "quality": "mutable"},
        {"name": "Lib", "quality": "cardinal"},
        {"name": "Sco", "quality": "fixed"},
        {"name": "Sag", "quality": "mutable"},
        {"name": "Cap", "quality": "cardinal"},
        {"name": "Aqu", "quality": "fixed"},
        {"name": "Pis", "quality": "mutable"},
    )

    # Initialize quality point totals
    quality_totals = {
        "cardinal": 0.0,
        "fixed": 0.0,
        "mutable": 0.0
    }

    # Make list of the points sign
    points_sign = [subject.get(planet).sign_num for planet in celestial_points_names]

    for i in range(len(planets_settings)):
        # Add points to appropriate quality
        quality = ZODIAC[points_sign[i]]["quality"]
        quality_totals[quality] += planets_settings[i]["element_points"]

    return quality_totals


def calculate_synastry_quality_points(
        planets_settings: list[KerykeionSettingsCelestialPointModel],
        celestial_points_names: list[str],
        subject1: AstrologicalSubjectModel,
        subject2: AstrologicalSubjectModel,
    ):
    """
    Calculate quality point totals for both subjects in a synastry chart.

    Args:
        planets_settings (list): List of planet configuration dictionaries
        celestial_points_names (list): List of celestial point names to process
        subject1: First astrological subject with get() method for accessing planet data
        subject2: Second astrological subject with get() method for accessing planet data

    Returns:
        dict: Dictionary with quality point totals as percentages, where the sum equals 100%
    """
    ZODIAC = (
        {"name": "Ari", "quality": "cardinal"},
        {"name": "Tau", "quality": "fixed"},
        {"name": "Gem", "quality": "mutable"},
        {"name": "Can", "quality": "cardinal"},
        {"name": "Leo", "quality": "fixed"},
        {"name": "Vir", "quality": "mutable"},
        {"name": "Lib", "quality": "cardinal"},
        {"name": "Sco", "quality": "fixed"},
        {"name": "Sag", "quality": "mutable"},
        {"name": "Cap", "quality": "cardinal"},
        {"name": "Aqu", "quality": "fixed"},
        {"name": "Pis", "quality": "mutable"},
    )

    # Initialize combined quality point totals
    combined_totals = {
        "cardinal": 0.0,
        "fixed": 0.0,
        "mutable": 0.0
    }

    # Make list of the points sign for both subjects
    subject1_points_sign = [subject1.get(planet).sign_num for planet in celestial_points_names]
    subject2_points_sign = [subject2.get(planet).sign_num for planet in celestial_points_names]

    # Calculate quality points for subject 1
    for i in range(len(planets_settings)):
        # Add points to appropriate quality
        quality1 = ZODIAC[subject1_points_sign[i]]["quality"]
        combined_totals[quality1] += planets_settings[i]["element_points"]

    # Calculate quality points for subject 2
    for i in range(len(planets_settings)):
        # Add points to appropriate quality
        quality2 = ZODIAC[subject2_points_sign[i]]["quality"]
        combined_totals[quality2] += planets_settings[i]["element_points"]

    # Calculate total points across all qualities
    total_points = sum(combined_totals.values())

    # Convert to percentages (total = 100%)
    if total_points > 0:
        for quality in combined_totals:
            combined_totals[quality] = (combined_totals[quality] / total_points) * 100.0

    return combined_totals
