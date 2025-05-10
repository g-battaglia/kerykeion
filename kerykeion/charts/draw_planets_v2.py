from kerykeion.charts.charts_utils import degreeDiff, sliceToX, sliceToY, convert_decimal_to_degree_string
from kerykeion.kr_types import KerykeionException, ChartType, KerykeionPointModel
from kerykeion.kr_types.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.kr_types.kr_literals import Houses
import logging
from typing import Union, get_args


def draw_planets_v2(
    radius: Union[int, float],
    available_kerykeion_celestial_points: list[KerykeionPointModel],
    available_planets_setting: list[KerykeionSettingsCelestialPointModel],
    third_circle_radius: Union[int, float],
    main_subject_first_house_degree_ut: Union[int, float],
    main_subject_seventh_house_degree_ut: Union[int, float],
    chart_type: ChartType,
    second_subject_available_kerykeion_celestial_points: Union[list[KerykeionPointModel], None] = None,
) -> str:
    """
    Draws the planets on an astrological chart based on the provided parameters.

    This function calculates positions, handles overlap of celestial points, and draws SVG
    elements for each planet/point on the chart. It supports different chart types including
    natal charts, transits, synastry, and returns.

    Args:
        radius (Union[int, float]): The radius of the chart in pixels.
        available_kerykeion_celestial_points (list[KerykeionPointModel]): List of celestial points for the main subject.
        available_planets_setting (list[KerykeionSettingsCelestialPointModel]): Settings for the celestial points.
        third_circle_radius (Union[int, float]): Radius of the third circle in the chart.
        main_subject_first_house_degree_ut (Union[int, float]): Degree of the first house for the main subject.
        main_subject_seventh_house_degree_ut (Union[int, float]): Degree of the seventh house for the main subject.
        chart_type (ChartType): Type of the chart (e.g., "Transit", "Synastry", "Return", "ExternalNatal").
        second_subject_available_kerykeion_celestial_points (Union[list[KerykeionPointModel], None], optional):
            List of celestial points for the second subject, required for "Transit", "Synastry", or "Return" charts.
            Defaults to None.

    Raises:
        KerykeionException: If secondary celestial points are required but not provided.

    Returns:
        str: SVG output for the chart with the planets drawn.
    """
    # Constants and initialization
    PLANET_GROUPING_THRESHOLD = 3.4  # Distance threshold to consider planets as grouped
    TRANSIT_RING_EXCLUDE_POINTS_NAMES = get_args(Houses)
    output = ""

    # -----------------------------------------------------------
    # 1. Validate inputs and prepare data
    # -----------------------------------------------------------
    if chart_type == "Transit" and second_subject_available_kerykeion_celestial_points is None:
        raise KerykeionException(f"Secondary celestial points are required for Transit charts")
    elif chart_type == "Synastry" and second_subject_available_kerykeion_celestial_points is None:
        raise KerykeionException(f"Secondary celestial points are required for Synastry charts")
    elif chart_type == "Return" and second_subject_available_kerykeion_celestial_points is None:
        raise KerykeionException(f"Secondary celestial points are required for Return charts")

    # Extract absolute and relative positions for main celestial points
    main_points_abs_positions = [planet.abs_pos for planet in available_kerykeion_celestial_points]
    main_points_rel_positions = [planet.position for planet in available_kerykeion_celestial_points]

    # Extract absolute and relative positions for secondary celestial points if needed
    secondary_points_abs_positions = []
    secondary_points_rel_positions = []
    if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
        secondary_points_abs_positions = [
            planet.abs_pos for planet in second_subject_available_kerykeion_celestial_points
        ]
        secondary_points_rel_positions = [
            planet.position for planet in second_subject_available_kerykeion_celestial_points
        ]

    # -----------------------------------------------------------
    # 2. Create position lookup dictionary for main celestial points
    # -----------------------------------------------------------
    # Map absolute degree to index in the settings array
    position_index_map = {}
    for i in range(len(available_planets_setting)):
        position_index_map[main_points_abs_positions[i]] = i
        logging.debug(f"Planet index: {i}, degree: {main_points_abs_positions[i]}")

    # Sort positions for ordered processing
    sorted_positions = sorted(position_index_map.keys())

    # -----------------------------------------------------------
    # 3. Identify groups of celestial points that are close to each other
    # -----------------------------------------------------------
    point_groups = []
    current_group = []
    is_group_open = False
    planets_by_position = [None] * len(position_index_map)

    # Process each celestial point to find groups
    for position_idx, abs_position in enumerate(sorted_positions):
        point_idx = position_index_map[abs_position]

        # Find previous and next point positions for distance calculations
        if position_idx == 0:
            prev_position = main_points_abs_positions[position_index_map[sorted_positions[-1]]]
            next_position = main_points_abs_positions[position_index_map[sorted_positions[1]]]
        elif position_idx == len(sorted_positions) - 1:
            prev_position = main_points_abs_positions[position_index_map[sorted_positions[position_idx - 1]]]
            next_position = main_points_abs_positions[position_index_map[sorted_positions[0]]]
        else:
            prev_position = main_points_abs_positions[position_index_map[sorted_positions[position_idx - 1]]]
            next_position = main_points_abs_positions[position_index_map[sorted_positions[position_idx + 1]]]

        # Calculate distance to adjacent points
        distance_to_prev = degreeDiff(prev_position, main_points_abs_positions[point_idx])
        distance_to_next = degreeDiff(next_position, main_points_abs_positions[point_idx])

        # Store position and distance information
        planets_by_position[position_idx] = [point_idx, distance_to_prev, distance_to_next]

        label = available_planets_setting[point_idx]["label"]
        logging.debug(f"{label}, distance_to_prev: {distance_to_prev}, distance_to_next: {distance_to_next}")

        # Group points that are close to each other
        if distance_to_next < PLANET_GROUPING_THRESHOLD:
            point_data = [position_idx, distance_to_prev, distance_to_next, label]
            if is_group_open:
                point_groups[-1].append(point_data)
            else:
                is_group_open = True
                point_groups.append([point_data])
        else:
            if is_group_open:
                point_data = [position_idx, distance_to_prev, distance_to_next, label]
                point_groups[-1].append(point_data)
            is_group_open = False

    # -----------------------------------------------------------
    # 4. Calculate position adjustments to avoid overlapping
    # -----------------------------------------------------------
    position_adjustments = [0] * len(available_planets_setting)

    # Process each group to calculate position adjustments
    for group in point_groups:
        group_size = len(group)

        # Handle groups of two celestial points
        if group_size == 2:
            handle_two_point_group(group, planets_by_position, position_adjustments, PLANET_GROUPING_THRESHOLD)

        # Handle groups of three or more celestial points
        elif group_size >= 3:
            handle_multi_point_group(group, position_adjustments, PLANET_GROUPING_THRESHOLD)

    # -----------------------------------------------------------
    # 5. Draw main celestial points
    # -----------------------------------------------------------
    for position_idx, abs_position in enumerate(sorted_positions):
        point_idx = position_index_map[abs_position]

        # Determine radius based on chart type and point type
        point_radius = determine_point_radius(point_idx, chart_type, bool(position_idx % 2))

        # Calculate position offset for the point
        adjusted_offset = calculate_point_offset(
            main_subject_seventh_house_degree_ut,
            main_points_abs_positions[point_idx],
            position_adjustments[position_idx],
        )

        # Calculate true position without adjustment (used for connecting lines)
        true_offset = calculate_point_offset(
            main_subject_seventh_house_degree_ut,
            main_points_abs_positions[point_idx],
            0
        )

        # Calculate point coordinates
        point_x = sliceToX(0, radius - point_radius, adjusted_offset) + point_radius
        point_y = sliceToY(0, radius - point_radius, adjusted_offset) + point_radius

        # Determine scale factor based on chart type
        scale_factor = 1.0
        if chart_type == "Transit":
            scale_factor = 0.8
        elif chart_type == "Synastry":
            scale_factor = 0.8
        elif chart_type == "Return":
            scale_factor = 0.8
        elif chart_type == "ExternalNatal":
            scale_factor = 0.8

        # Draw connecting lines for ExternalNatal chart type
        if chart_type == "ExternalNatal":
            output = draw_external_natal_lines(
                output,
                radius,
                third_circle_radius,
                point_radius,
                true_offset,
                adjusted_offset,
                available_planets_setting[point_idx]["color"],
            )

        # Draw the celestial point SVG element
        point_details = available_kerykeion_celestial_points[point_idx]
        output += generate_point_svg(
            point_details, point_x, point_y, scale_factor, available_planets_setting[point_idx]["name"]
        )

    # -----------------------------------------------------------
    # 6. Draw transit/secondary celestial points
    # -----------------------------------------------------------
    if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
        output = draw_secondary_points(
            output,
            radius,
            main_subject_first_house_degree_ut,
            main_subject_seventh_house_degree_ut,
            secondary_points_abs_positions,
            secondary_points_rel_positions,
            available_planets_setting,
            chart_type,
            TRANSIT_RING_EXCLUDE_POINTS_NAMES,
            adjusted_offset,
        )

    return output


def handle_two_point_group(
    group: list, planets_by_position: list, position_adjustments: list, threshold: float
) -> None:
    """
    Handle positioning for a group of two celestial points that are close to each other.

    Adjusts positions to prevent overlapping by calculating appropriate offsets
    based on available space around the points.

    Args:
        group (list): A list containing data about two closely positioned points.
        planets_by_position (list): A list with data about all planets positions.
        position_adjustments (list): The list to store calculated position adjustments.
        threshold (float): The minimum distance threshold for considering points as grouped.
    """
    next_to_a = group[0][0] - 1
    next_to_b = 0 if group[1][0] == (len(planets_by_position) - 1) else group[1][0] + 1

    # If both points have room
    if (group[0][1] > (2 * threshold)) and (group[1][2] > (2 * threshold)):
        position_adjustments[group[0][0]] = -(threshold - group[0][2]) / 2
        position_adjustments[group[1][0]] = +(threshold - group[0][2]) / 2

    # If only first point has room
    elif group[0][1] > (2 * threshold):
        position_adjustments[group[0][0]] = -threshold

    # If only second point has room
    elif group[1][2] > (2 * threshold):
        position_adjustments[group[1][0]] = +threshold

    # If points adjacent to group have room
    elif (planets_by_position[next_to_a][1] > (2.4 * threshold)) and (planets_by_position[next_to_b][2] > (2.4 * threshold)):
        position_adjustments[next_to_a] = group[0][1] - threshold * 2
        position_adjustments[group[0][0]] = -threshold * 0.5
        position_adjustments[next_to_b] = -(group[1][2] - threshold * 2)
        position_adjustments[group[1][0]] = +threshold * 0.5

    # If only point adjacent to first has room
    elif planets_by_position[next_to_a][1] > (2 * threshold):
        position_adjustments[next_to_a] = group[0][1] - threshold * 2.5
        position_adjustments[group[0][0]] = -threshold * 1.2

    # If only point adjacent to second has room
    elif planets_by_position[next_to_b][2] > (2 * threshold):
        position_adjustments[next_to_b] = -(group[1][2] - threshold * 2.5)
        position_adjustments[group[1][0]] = +threshold * 1.2


def handle_multi_point_group(group: list, position_adjustments: list, threshold: float) -> None:
    """
    Handle positioning for a group of three or more celestial points that are close to each other.

    Distributes points evenly within the available space to prevent overlapping.

    Args:
        group (list): A list containing data about grouped points.
        position_adjustments (list): The list to store calculated position adjustments.
        threshold (float): The minimum distance threshold for considering points as grouped.
    """
    group_size = len(group)

    # Calculate available space
    available_space = group[0][1]  # Distance before first point
    for i in range(group_size):
        available_space += group[i][2]  # Add distance after each point

    # Calculate needed space
    needed_space = (3 * threshold) + (1.2 * (group_size - 1) * threshold)
    leftover_space = available_space - needed_space

    # Get spacing before first and after last point
    space_before_first = group[0][1]
    space_after_last = group[group_size - 1][2]

    # Position points based on available space
    if (space_before_first > (needed_space * 0.5)) and (space_after_last > (needed_space * 0.5)):
        # Center the group
        start_position = space_before_first - (needed_space * 0.5)
    else:
        # Distribute leftover space proportionally
        start_position = (leftover_space / (space_before_first + space_after_last)) * space_before_first

    # Apply positions if there's enough space
    if available_space > needed_space:
        position_adjustments[group[0][0]] = start_position - group[0][1] + (1.5 * threshold)

        # Position each subsequent point relative to the previous one
        for i in range(group_size - 1):
            position_adjustments[group[i + 1][0]] = 1.2 * threshold + position_adjustments[group[i][0]] - group[i][2]


def determine_point_radius(
    point_idx: int,
    chart_type: str,
    is_alternate_position: bool
) -> int:
    """
    Determine the radius for placing a celestial point based on its type and chart type.

    Args:
        point_idx (int): Index of the celestial point.
        chart_type (str): Type of the chart.
        is_alternate_position (bool): Whether to use alternate positioning.

    Returns:
        int: Radius value for the point.
    """
    # Check if point is an angle of the chart (ASC, MC, DSC, IC)
    is_chart_angle = 22 < point_idx < 27

    if chart_type == "Transit":
        if is_chart_angle:
            return 76
        else:
            return 110 if is_alternate_position else 130
    elif chart_type == "Synastry":
        if is_chart_angle:
            return 76
        else:
            return 110 if is_alternate_position else 130
    elif chart_type == "Return":
        if is_chart_angle:
            return 76
        else:
            return 110 if is_alternate_position else 130
    else:
        # Default natal chart and ExternalNatal handling
        # if 22 < point_idx < 27 it is asc,mc,dsc,ic (angles of chart)
        amin, bmin, cmin = 0, 0, 0
        if chart_type == "ExternalNatal":
            amin = 74 - 10
            bmin = 94 - 10
            cmin = 40 - 10

        if is_chart_angle:
            return 40 - cmin
        elif is_alternate_position:
            return 74 - amin
        else:
            return 94 - bmin


def calculate_point_offset(
    seventh_house_degree: Union[int, float], point_degree: Union[int, float], adjustment: Union[int, float]
) -> float:
    """
    Calculate the offset position of a celestial point on the chart.

    Args:
        seventh_house_degree (Union[int, float]): Degree of the seventh house.
        point_degree (Union[int, float]): Degree of the celestial point.
        adjustment (Union[int, float]): Adjustment value to prevent overlapping.

    Returns:
        float: The calculated offset position.
    """
    return (int(seventh_house_degree) / -1) + int(point_degree + adjustment)


def draw_external_natal_lines(
    output: str,
    radius: Union[int, float],
    third_circle_radius: Union[int, float],
    point_radius: Union[int, float],
    true_offset: Union[int, float],
    adjusted_offset: Union[int, float],
    color: str,
) -> str:
    """
    Draw connecting lines for the ExternalNatal chart type.

    Creates two line segments: one from the circle to the original position,
    and another from the original position to the adjusted position.

    Args:
        output (str): The SVG output string to append to.
        radius (Union[int, float]): Chart radius.
        third_circle_radius (Union[int, float]): Radius of the third circle.
        point_radius (Union[int, float]): Radius of the celestial point.
        true_offset (Union[int, float]): True position offset.
        adjusted_offset (Union[int, float]): Adjusted position offset.
        color (str): Line color.

    Returns:
        str: Updated SVG output with added line elements.
    """
    # First line - from circle to outer position
    x1 = sliceToX(0, radius - third_circle_radius, true_offset) + third_circle_radius
    y1 = sliceToY(0, radius - third_circle_radius, true_offset) + third_circle_radius
    x2 = sliceToX(0, radius - point_radius - 30, true_offset) + point_radius + 30
    y2 = sliceToY(0, radius - point_radius - 30, true_offset) + point_radius + 30
    output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke-width:1px;stroke:{color};stroke-opacity:.3;"/>\n'

    # Second line - from outer position to adjusted position
    x1 = x2
    y1 = y2
    x2 = sliceToX(0, radius - point_radius - 10, adjusted_offset) + point_radius + 10
    y2 = sliceToY(0, radius - point_radius - 10, adjusted_offset) + point_radius + 10
    output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke-width:1px;stroke:{color};stroke-opacity:.5;"/>\n'

    return output


def generate_point_svg(point_details: KerykeionPointModel, x: float, y: float, scale: float, point_name: str) -> str:
    """
    Generate the SVG element for a celestial point.

    Args:
        point_details (KerykeionPointModel): Details about the celestial point.
        x (float): X-coordinate for the point.
        y (float): Y-coordinate for the point.
        scale (float): Scale factor for the point.
        point_name (str): Name of the celestial point.

    Returns:
        str: SVG element for the celestial point.
    """
    svg = f'<g kr:node="ChartPoint" kr:house="{point_details["house"]}" kr:sign="{point_details["sign"]}" '
    svg += f'kr:slug="{point_details["name"]}" transform="translate(-{12 * scale},-{12 * scale}) scale({scale})">'
    svg += f'<use x="{x * (1/scale)}" y="{y * (1/scale)}" xlink:href="#{point_name}" />'
    svg += "</g>"
    return svg


def draw_secondary_points(
    output: str,
    radius: Union[int, float],
    first_house_degree: Union[int, float],
    seventh_house_degree: Union[int, float],
    points_abs_positions: list[Union[int, float]],
    points_rel_positions: list[Union[int, float]],
    points_settings: list[KerykeionSettingsCelestialPointModel],
    chart_type: str,
    exclude_points: list[str],
    main_offset: float,
) -> str:
    """
    Draw secondary celestial points (transit/synastry/return) on the chart.

    Args:
        output (str): Current SVG output to append to.
        radius (Union[int, float]): Chart radius.
        first_house_degree (Union[int, float]): Degree of the first house.
        seventh_house_degree (Union[int, float]): Degree of the seventh house.
        points_abs_positions (list[Union[int, float]]): Absolute positions of points.
        points_rel_positions (list[Union[int, float]]): Relative positions of points.
        points_settings (list[KerykeionSettingsCelestialPointModel]): Settings for points.
        chart_type (str): Type of chart.
        exclude_points (list[str]): List of point names to exclude.
        main_offset (float): Offset position for the main point.

    Returns:
        str: Updated SVG output with added secondary points.
    """
    # Initialize position adjustments for grouped points
    position_adjustments = {i: 0 for i in range(len(points_settings))}

    # Map absolute position to point index
    position_index_map = {}
    for i in range(len(points_settings)):
        if chart_type == "Transit" and points_settings[i]["name"] in exclude_points:
            continue
        position_index_map[points_abs_positions[i]] = i

    # Sort positions
    sorted_positions = sorted(position_index_map.keys())

    # Find groups of points that are close to each other
    point_groups = []
    in_group = False

    for pos_idx, abs_position in enumerate(sorted_positions):
        point_a_idx = position_index_map[abs_position]

        # Get next point
        if pos_idx == len(sorted_positions) - 1:
            point_b_idx = position_index_map[sorted_positions[0]]
        else:
            point_b_idx = position_index_map[sorted_positions[pos_idx + 1]]

        # Check distance between points
        position_a = points_abs_positions[point_a_idx]
        position_b = points_abs_positions[point_b_idx]
        distance = degreeDiff(position_a, position_b)

        # Group points that are close
        if distance <= 2.5:
            if in_group:
                point_groups[-1].append(point_b_idx)
            else:
                point_groups.append([point_a_idx])
                point_groups[-1].append(point_b_idx)
                in_group = True
        else:
            in_group = False

    # Set position adjustments for grouped points
    for group in point_groups:
        if len(group) == 2:
            position_adjustments[group[0]] = -1.0
            position_adjustments[group[1]] = 1.0
        elif len(group) == 3:
            position_adjustments[group[0]] = -1.5
            position_adjustments[group[1]] = 0
            position_adjustments[group[2]] = 1.5
        elif len(group) == 4:
            position_adjustments[group[0]] = -2.0
            position_adjustments[group[1]] = -1.0
            position_adjustments[group[2]] = 1.0
            position_adjustments[group[3]] = 2.0

    # Draw each secondary point
    alternate_position = False

    for pos_idx, abs_position in enumerate(sorted_positions):
        point_idx = position_index_map[abs_position]

        if chart_type == "Transit" and points_settings[point_idx]["name"] in exclude_points:
            continue

        # Determine radius based on point type
        if 22 < point_idx < 27:  # Chart angles
            point_radius = 9
        elif alternate_position:
            point_radius = 18
            alternate_position = False
        else:
            point_radius = 26
            alternate_position = True

        # Calculate position
        zero_point = 360 - seventh_house_degree
        point_offset = zero_point + points_abs_positions[point_idx]
        if point_offset > 360:
            point_offset -= 360

        # Draw point symbol
        point_x = sliceToX(0, radius - point_radius, point_offset) + point_radius
        point_y = sliceToY(0, radius - point_radius, point_offset) + point_radius
        output += f'<g class="transit-planet-name" transform="translate(-6,-6)"><g transform="scale(0.5)">'
        output += f'<use x="{point_x*2}" y="{point_y*2}" xlink:href="#{points_settings[point_idx]["name"]}" /></g></g>'

        # Draw connecting line
        x1 = sliceToX(0, radius + 3, point_offset) - 3
        y1 = sliceToY(0, radius + 3, point_offset) - 3
        x2 = sliceToX(0, radius - 3, point_offset) + 3
        y2 = sliceToY(0, radius - 3, point_offset) + 3
        output += f'<line class="transit-planet-line" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        output += f'style="stroke: {points_settings[point_idx]["color"]}; stroke-width: 1px; stroke-opacity:.8;"/>'

        # Draw degree text with rotation
        rotation = first_house_degree - points_abs_positions[point_idx]
        text_anchor = "end"

        # Adjust text rotation and anchor for readability
        if -90 > rotation > -270:
            rotation += 180.0
            text_anchor = "start"
        if 270 > rotation > 90:
            rotation -= 180.0
            text_anchor = "start"

        # Position the degree text
        x_offset = 1 if text_anchor == "end" else -1
        adjusted_point_offset = point_offset + position_adjustments[point_idx]
        text_radius = -3.0

        deg_x = sliceToX(0, radius - text_radius, adjusted_point_offset + x_offset) + text_radius
        deg_y = sliceToY(0, radius - text_radius, adjusted_point_offset + x_offset) + text_radius

        # Format and output the degree text
        degree_text = convert_decimal_to_degree_string(points_rel_positions[point_idx], format_type="1")
        output += f'<g transform="translate({deg_x},{deg_y})">'
        output += f'<text transform="rotate({rotation})" text-anchor="{text_anchor}" '
        output += f'style="fill: {points_settings[point_idx]["color"]}; font-size: 10px;">{degree_text}</text></g>'

    # Draw connecting lines for the main point
    dropin = 0
    if chart_type == "Transit":
        dropin = 36
    elif chart_type == "Synastry":
        dropin = 36
    elif chart_type == "Return":
        dropin = 36

    # First connecting line segment
    x1 = sliceToX(0, radius - (dropin + 3), main_offset) + (dropin + 3)
    y1 = sliceToY(0, radius - (dropin + 3), main_offset) + (dropin + 3)
    x2 = sliceToX(0, radius - (dropin - 3), main_offset) + (dropin - 3)
    y2 = sliceToY(0, radius - (dropin - 3), main_offset) + (dropin - 3)

    point_color = points_settings[point_idx]["color"]
    output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
    output += f'style="stroke: {point_color}; stroke-width: 2px; stroke-opacity:.6;"/>'

    # Second connecting line segment
    dropin = 120
    if chart_type == "Transit":
        dropin = 160
    elif chart_type == "Synastry":
        dropin = 160
    elif chart_type == "Return":
        dropin = 160

    x1 = sliceToX(0, radius - dropin, main_offset) + dropin
    y1 = sliceToY(0, radius - dropin, main_offset) + dropin
    x2 = sliceToX(0, radius - (dropin - 3), main_offset) + (dropin - 3)
    y2 = sliceToY(0, radius - (dropin - 3), main_offset) + (dropin - 3)

    output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
    output += f'style="stroke: {point_color}; stroke-width: 2px; stroke-opacity:.6;"/>'

    return output
