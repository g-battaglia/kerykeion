import math
import datetime
from kerykeion.kr_types import KerykeionException, ChartType
from typing import Union
from kerykeion.kr_types.kr_models import AspectModel, KerykeionPointModel
from kerykeion.kr_types.settings_models import KerykeionLanguageCelestialPointModel, KerykeionSettingsAspectModel


def get_decoded_kerykeion_celestial_point_name(input_planet_name: str, celestial_point_language: KerykeionLanguageCelestialPointModel) -> str:
    """
    Decode the given celestial point name based on the provided language model.

    Args:
        input_planet_name (str): The name of the celestial point to decode.
        celestial_point_language (KerykeionLanguageCelestialPointModel): The language model containing celestial point names.

    Returns:
        str: The decoded celestial point name.
    """

    # Dictionary for special house names
    special_house_names = {
        "First_House": "Asc",
        "Seventh_House": "Dsc",
        "Tenth_House": "Mc",
        "Fourth_House": "Ic"
    }

    # Get the language model keys
    language_keys = celestial_point_language.model_dump().keys()

    # Check if the input planet name exists in the language model
    if input_planet_name in language_keys:
        return celestial_point_language[input_planet_name]

    # Return the special house name if it exists, otherwise return an empty string
    return special_house_names.get(input_planet_name, "")


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
    """Calculate the difference between two degrees.

    Args:
        - a (int | float): first degree
        - b (int | float): second degree

    Returns:
        float: difference between a and b
    """

    out = float()
    if a > b:
        out = a - b
    if a < b:
        out = b - a
    if out > 180.0:
        out = 360.0 - out
    return out


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
    if chart_type == "Transit" or chart_type == "Synastry":
        dropin: Union[int, float] = 0
    else:
        dropin = c1
    slice = f'<path d="M{str(r)},{str(r)} L{str(dropin + sliceToX(num, r - dropin, offset))},{str(dropin + sliceToY(num, r - dropin, offset))} A{str(r - dropin)},{str(r - dropin)} 0 0,0 {str(dropin + sliceToX(num + 1, r - dropin, offset))},{str(dropin + sliceToY(num + 1, r - dropin, offset))} z" style="{style}"/>'

    # symbols
    offset = offset + 15
    # check transit
    if chart_type == "Transit" or chart_type == "Synastry":
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


def draw_elements_percentages(
    fire_label: str,
    fire_points: float,
    earth_label: str,
    earth_points: float,
    air_label: str,
    air_points: float,
    water_label: str,
    water_points: float,
) -> str:
    """Draw the elements grid.

    Args:
        - fire_label (str): Label for fire
        - fire_points (float): Points for fire
        - earth_label (str): Label for earth
        - earth_points (float): Points for earth
        - air_label (str): Label for air
        - air_points (float): Points for air
        - water_label (str): Label for water
        - water_points (float): Points for water

    Returns:
        str: The SVG elements grid as a string.
    """
    total = fire_points + earth_points + air_points + water_points

    fire_percentage = int(round(100 * fire_points / total))
    earth_percentage = int(round(100 * earth_points / total))
    air_percentage = int(round(100 * air_points / total))
    water_percentage = int(round(100 * water_points / total))

    return (
        f'<g transform="translate(-30,79)">'
        f'<text y="0" style="fill:#ff6600; font-size: 10px;">{fire_label}  {str(fire_percentage)}%</text>'
        f'<text y="12" style="fill:#6a2d04; font-size: 10px;">{earth_label} {str(earth_percentage)}%</text>'
        f'<text y="24" style="fill:#6f76d1; font-size: 10px;">{air_label}   {str(air_percentage)}%</text>'
        f'<text y="36" style="fill:#630e73; font-size: 10px;">{water_label} {str(water_percentage)}%</text>'
        f"</g>"
    )


def convert_decimal_to_degree_string(dec: float, type="3") -> str:
    """
    Coverts decimal float to degrees in format a°b'c".

    Args:
        - dec (float): decimal float
        - type (str): type of format:
            - 1: a°
            - 2: a°b'
            - 3: a°b'c"

    Returns:
        str: degrees in format a°b'c"
    """

    dec = float(dec)
    a = int(dec)
    a_new = (dec - float(a)) * 60.0
    b_rounded = int(round(a_new))
    b = int(a_new)
    c = int(round((a_new - float(b)) * 60.0))

    if type == "3":
        out = f"{a:02d}&#176;{b:02d}&#39;{c:02d}&#34;"
    elif type == "2":
        out = f"{a:02d}&#176;{b_rounded:02d}&#39;"
    elif type == "1":
        out = f"{a:02d}&#176;"
    else:
        raise KerykeionException(f"Wrong type: {type}, it must be 1, 2 or 3.")

    return str(out)


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
    if chart_type == "Synastry" or chart_type == "Transit":
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

    if chart_type == "Synastry" or chart_type == "Transit":
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
    if chart_type in {"Synastry", "Transit"}:
        # For Synastry and Transit charts, use a fixed radius adjustment of 160
        return f'<circle cx="{radius}" cy="{radius}" r="{radius - 160}" style="fill: {fill_color}; fill-opacity:.8; stroke: {stroke_color}; stroke-width: 1px" />'

    else:
        return f'<circle cx="{radius}" cy="{radius}" r="{radius - c3}" style="fill: {fill_color}; fill-opacity:.8; stroke: {stroke_color}; stroke-width: 1px" />'


def draw_aspect_grid(stroke_color: str, available_planets_list: list, aspects_list: list) -> str:
    """
    Draws the aspect grid.

    Args:
        - stroke_color (str): The color of the stroke.
        - available_planets_list (list): List of all the planets, they will be actually filtered to so if they have
            the "is_active" key set to True inside the function to have the correct list of just the active planets.
        - aspects_list (list): List of aspects.

    """

    out = ""
    style = f"stroke:{stroke_color}; stroke-width: 1px; stroke-opacity:.6; fill:none"
    xindent = 380
    yindent = 468
    box = 14
    counter = 0

    actual_planets = []
    for planet in available_planets_list:
        if planet.is_active:
            actual_planets.append(planet)

    first_iteration_revers_planets = actual_planets[::-1]
    for index, a in enumerate(first_iteration_revers_planets):
        counter += 1
        out += f'<rect x="{xindent}" y="{yindent}" width="{box}" height="{box}" style="{style}"/>'
        out += f'<use transform="scale(0.4)" x="{(xindent+2)*2.5}" y="{(yindent+1)*2.5}" xlink:href="#{a["name"]}" />'

        xindent = xindent + box
        yindent = yindent - box

        xorb = xindent
        yorb = yindent + box

        second_iteration_revers_planets = first_iteration_revers_planets[index + 1 :]
        for b in second_iteration_revers_planets:
            out += f'<rect x="{xorb}" y="{yorb}" width="{box}" height="{box}" style="{style}"/>'
            xorb = xorb + box

            for aspect in aspects_list:
                if (aspect["p1"] == a["id"] and aspect["p2"] == b["id"]) or (
                    aspect["p1"] == b["id"] and aspect["p2"] == a["id"]
                ):
                    out += f'<use  x="{xorb-box+1}" y="{yorb+1}" xlink:href="#orb{aspect["aspect_degrees"]}" />'

    return out


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
        dropin, roff, t_roff = (160, 72, 36) if chart_type in ["Transit", "Synastry"] else (c3, c1, False)

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

        if chart_type in ["Transit", "Synastry"]:
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
            path += f'<text style="fill: #00f; fill-opacity: {fill_opacity}; font-size: 14px"><tspan x="{xtext - 3}" y="{ytext + 3}">{i + 1}</tspan></text>'
            path += f"</g>"

            # Add the house cusp line for the second subject
            stroke_opacity = "0" if chart_type == "Transit" else ".3"
            path += f'<g kr:node="Cusp">'
            path += f"<line x1='{t_x1}' y1='{t_y1}' x2='{t_x2}' y2='{t_y2}' style='stroke: {t_linecolor}; stroke-width: 1px; stroke-opacity:{stroke_opacity};'/>"
            path += f"</g>"

        # Adjust dropin based on chart type
        dropin = {"Transit": 84, "Synastry": 84, "ExternalNatal": 100}.get(chart_type, 48)
        xtext = sliceToX(0, (r - dropin), text_offset) + dropin
        ytext = sliceToY(0, (r - dropin), text_offset) + dropin

        # Add the house cusp line for the first subject
        path += f'<g kr:node="Cusp">'
        path += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {linecolor}; stroke-width: 1px; stroke-dasharray:3,2; stroke-opacity:.4;"/>'
        path += f"</g>"

        # Add the house number text for the first subject
        path += f'<g kr:node="HouseNumber">'
        path += f'<text style="fill: #f00; fill-opacity: .6; font-size: 14px"><tspan x="{xtext - 3}" y="{ytext + 3}">{i + 1}</tspan></text>'
        path += f"</g>"

    return path


def draw_aspect_transit_grid(
    grid_title: str,
    aspects_list: Union[list[AspectModel], list[dict]],
    celestial_point_language: Union[KerykeionLanguageCelestialPointModel, dict],
    aspects_settings: Union[KerykeionSettingsAspectModel, dict],
) -> str:
    """
    Generates the SVG output for the aspect transit grid.

    Parameters:
    - grid_title: Title of the grid.
    - aspects_list: List of aspects.
    - planets_labels: Dictionary containing the planet labels.
    - aspects_settings: Dictionary containing the aspect settings.

    Returns:
    - A string containing the SVG path data for the aspect transit grid.
    """
    
    if isinstance(celestial_point_language, dict):
        celestial_point_language = KerykeionLanguageCelestialPointModel(**celestial_point_language)

    if isinstance(aspects_settings, dict):
        aspects_settings = KerykeionSettingsAspectModel(**aspects_settings)

    # If not instance of AspectModel, convert to AspectModel
    if isinstance(aspects_list[0], dict):
        aspects_list = [AspectModel(**aspect) for aspect in aspects_list] # type: ignore

    line = 0
    nl = 0
    inner_path = ""
    scale = 1
    for i, aspect in enumerate(aspects_list):
        # Adjust the vertical position for every 12 aspects
        if i == 12:
            nl = 100
            line = 0

        elif i == 24:
            nl = 200
            line = 0

        elif i == 36:
            nl = 300
            line = 0

        elif i == 48:
            nl = 400
            # When there are more than 60 aspects, the text is moved up
            if len(aspects_list) > 60:
                line = -1 * (len(aspects_list) - 60) * 14
            else:
                line = 0

        inner_path += f'<g transform="translate({nl},{line})">'

        # first planet symbol
        inner_path += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{celestial_point_language[aspects_list[i]["p1"]]["name"]}" />'

        # aspect symbol
        inner_path += f'<use  x="15" y="0" xlink:href="#orb{aspects_settings[aspects_list[i]["aid"]]["degree"]}" />'

        # second planet symbol
        inner_path += f'<g transform="translate(30,0)">'
        inner_path += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{celestial_point_language[aspects_list[i]["p2"]]["name"]}" />'
        inner_path += f"</g>"

        # difference in degrees
        inner_path += f'<text y="8" x="45" style="fill:#000000; font-size: 10px;">{convert_decimal_to_degree_string(aspects_list[i]["orbit"])}</text>'
        # line
        inner_path += f"</g>"
        line = line + 14

    out = f'<g style="transform: translate(47%, 61%) scale({scale})">'
    out += f'<text y="-15" x="0" style="fill:#000000; font-size: 14px;">{grid_title}:</text>'
    out += inner_path
    out += "</g>"

    return out


def draw_moon_phase(
    degrees_between_sun_and_moon: float,
    latitude: float,
    lunar_phase_outline_color: str = "#000000",
    dark_color: str = "#000000",
    light_color: str = "#ffffff",
) -> str:
    """
    Draws the moon phase based on the degrees between the sun and the moon.

    Parameters:
    - degrees_between_sun_and_moon (float): The degrees between the sun and the moon.
    - latitude (float): The latitude for rotation calculation.
    - lunar_phase_outline_color (str): The color for the lunar phase outline.
    - dark_color (str): The color for the dark part of the moon.
    - light_color (str): The color for the light part of the moon.

    Returns:
    - str: The SVG element as a string.
    """
    deg = degrees_between_sun_and_moon

    # Initialize variables for lunar phase properties
    fill_color_foreground = None
    fill_color_background = None
    circle_center_x = None
    circle_radius = None

    # Determine lunar phase properties based on the degree
    if deg < 90.0:
        max_radius = deg
        if deg > 80.0:
            max_radius = max_radius * max_radius
        circle_center_x = 20.0 + (deg / 90.0) * (max_radius + 10.0)
        circle_radius = 10.0 + (deg / 90.0) * max_radius
        fill_color_foreground = dark_color
        fill_color_background = light_color

    elif deg < 180.0:
        max_radius = 180.0 - deg
        if deg < 100.0:
            max_radius = max_radius * max_radius
        circle_center_x = 20.0 + ((deg - 90.0) / 90.0 * (max_radius + 10.0)) - (max_radius + 10.0)
        circle_radius = 10.0 + max_radius - ((deg - 90.0) / 90.0 * max_radius)
        fill_color_foreground = light_color
        fill_color_background = dark_color

    elif deg < 270.0:
        max_radius = deg - 180.0
        if deg > 260.0:
            max_radius = max_radius * max_radius
        circle_center_x = 20.0 + ((deg - 180.0) / 90.0 * (max_radius + 10.0))
        circle_radius = 10.0 + ((deg - 180.0) / 90.0 * max_radius)
        fill_color_foreground = light_color
        fill_color_background = dark_color

    elif deg < 361.0:
        max_radius = 360.0 - deg
        if deg < 280.0:
            max_radius = max_radius * max_radius
        circle_center_x = 20.0 + ((deg - 270.0) / 90.0 * (max_radius + 10.0)) - (max_radius + 10.0)
        circle_radius = 10.0 + max_radius - ((deg - 270.0) / 90.0 * max_radius)
        fill_color_foreground = dark_color
        fill_color_background = light_color

    else:
        raise KerykeionException(f"Invalid degree value: {deg}")


    # Calculate rotation based on latitude
    lunar_phase_rotate = -90.0 - latitude

    # Return the SVG element as a string
    return (
        f'<g transform="rotate({lunar_phase_rotate} 20 10)">'
        f'    <defs>'
        f'        <clipPath id="moonPhaseCutOffCircle">'
        f'        <circle cx="20" cy="10" r="10" />'
        f'        </clipPath>'
        f'    </defs>'
        f'    <circle cx="20" cy="10" r="10" style="fill: {fill_color_background}" />'
        f'    <circle cx="{circle_center_x}" cy="10" r="{circle_radius}" style="fill: {fill_color_foreground}" clip-path="url(#moonPhaseCutOffCircle)" />'
        f'    <circle cx="20" cy="10" r="10" style="fill: none; stroke: {lunar_phase_outline_color}; stroke-width: 0.5px; stroke-opacity: 0.5" />'
        f'</g>'
    )


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
    
    if chart_type in ["Synastry", "Transit"] and secondary_subject_houses_list is None:
        raise KerykeionException("secondary_houses is None")

    svg_output = '<g transform="translate(610,-20)">'

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

    if chart_type == "Synastry":
        svg_output += '<!-- Synastry Houses -->'
        svg_output += '<g transform="translate(850, -20)">'
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

    svg_output = (
        f'<g transform="translate(510,-20)">'
        f'<g transform="translate(140, -15)">'
        f'<text text-anchor="end" style="fill:{text_color}; font-size: 14px;">{planets_and_houses_grid_title} {subject_name}:</text>'
        f'</g>'
    )

    end_of_line = "</g>"

    for i, planet in enumerate(available_kerykeion_celestial_points):
        if i == 27:
            line_height = 10
            offset = -120

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

    if chart_type in ["Transit", "Synastry"]:
        if second_subject_available_kerykeion_celestial_points is None:
            raise KerykeionException("second_subject_available_kerykeion_celestial_points is None")

        if chart_type == "Transit":
            svg_output += (
                f'<g transform="translate(320, -15)">'
                f'<text text-anchor="end" style="fill:{text_color}; font-size: 14px;">{second_subject_name}:</text>'
            )
        else:
            svg_output += (
                f'<g transform="translate(380, -15)">'
                f'<text text-anchor="end" style="fill:{text_color}; font-size: 14px;">{planets_and_houses_grid_title} {second_subject_name}:</text>'
            )

        svg_output += end_of_line

        second_line_height = 10
        second_offset = 250

        for i, t_planet in enumerate(second_subject_available_kerykeion_celestial_points):
            if i == 27:
                second_line_height = 10
                second_offset = -120

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

    svg_output += end_of_line
    return svg_output