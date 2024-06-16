import math
import datetime
from kerykeion.kr_types import KerykeionException, ChartType
from typing import Union


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
            {"name": "aries", "element": "fire"}
        - r (Union[int, float]): The value of r.
        - style (str): The CSS inline style.
        - type (str): The type ?. In OpenAstro, it was the symbol of the sign. Eg: "aries".
            self.zodiac[i]["name"]

    Returns:
        - str: The zodiac slice and symbol as an SVG path.
    """

    # pie slices
    offset = 360 - seventh_house_degree_ut
    # check transit
    if chart_type == "Transit" or chart_type == "Synastry":
        dropin = 0
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
    degA: Union[int, float],
    degB: Union[int, float],
    color: str,
    seventh_house_degree_ut: Union[int, float],
) -> str:
    """Draws svg aspects: ring, aspect ring, degreeA degreeB

    Args:
        - r (Union[int, float]): The value of r.
        - ar (Union[int, float]): The value of ar.
        - degA (Union[int, float]): The degree of A.
        - degB (Union[int, float]): The degree of B.
        - color (str): The color of the aspect.
        - seventh_house_degree_ut (Union[int, float]): The degree of the seventh house.

    Returns:
        str: The SVG line element as a string.
    """

    first_offset = (int(seventh_house_degree_ut) / -1) + int(degA)
    x1 = sliceToX(0, ar, first_offset) + (r - ar)
    y1 = sliceToY(0, ar, first_offset) + (r - ar)

    second_offset = (int(seventh_house_degree_ut) / -1) + int(degB)
    x2 = sliceToX(0, ar, second_offset) + (r - ar)
    y2 = sliceToY(0, ar, second_offset) + (r - ar)

    out = f'<line class="aspect" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {color}; stroke-width: 1; stroke-opacity: .9;"/>'

    return out


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

    out = '<g transform="translate(-30,79)">'
    out += f'<text y="0" style="fill:#ff6600; font-size: 10px;">{fire_label}  {str(fire_percentage)}%</text>'
    out += f'<text y="12" style="fill:#6a2d04; font-size: 10px;">{earth_label} {str(earth_percentage)}%</text>'
    out += f'<text y="24" style="fill:#6f76d1; font-size: 10px;">{air_label}   {str(air_percentage)}%</text>'
    out += f'<text y="36" style="fill:#630e73; font-size: 10px;">{water_label} {str(water_percentage)}%</text>'
    out += "</g>"

    return out


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


def draw_degree_ring(r: Union[int, float], c1: Union[int, float], seventh_house_degree_ut: Union[int, float], stroke_color: str) -> str:
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


def draw_first_circle(r: Union[int, float], stroke_color: str, chart_type: ChartType, c1: Union[int, float, None] = None) -> str:
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

        return f'<circle cx="{r}" cy="{r}" r="{r - c1}" style="fill: none; stroke: {stroke_color}; stroke-width: 1px; " />'


def draw_second_circle(r: Union[int, float], stroke_color: str, fill_color: str, chart_type: ChartType, c2: Union[int, float, None] = None) -> str:
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