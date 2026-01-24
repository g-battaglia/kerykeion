"""
Kerykeion - Draw Planets Module

This module handles the rendering of celestial points (planets, angles, etc.)
on astrological SVG charts. It supports various chart types including
Natal, Transit, Synastry, and Return charts.

Main responsibilities:
- Calculate positions and avoid overlapping of celestial points
- Generate SVG elements for planets with proper styling
- Draw degree indicators and connecting lines
- Support both internal and external view modes

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from kerykeion.charts.charts_utils import degreeDiff, sliceToX, sliceToY, convert_decimal_to_degree_string
from kerykeion.schemas import KerykeionException, ChartType, KerykeionPointModel
from kerykeion.schemas.kr_literals import Houses
import logging
from typing import Union, get_args, List, Optional, Tuple, Sequence, Mapping, Any

# =============================================================================
# CONSTANTS
# =============================================================================

# Grouping thresholds (in degrees)
PLANET_GROUPING_THRESHOLD = 3.4  # Distance to consider planets as grouped
INDICATOR_GROUPING_THRESHOLD = 2.5  # Distance for indicator overlap detection

# Chart angle indices (ASC, MC, DSC, IC are between these indices)
CHART_ANGLE_MIN_INDEX = 22
CHART_ANGLE_MAX_INDEX = 27

# Radius offsets for different chart elements
NATAL_INDICATOR_OFFSET = 72  # Offset for inner chart degree indicators
DUAL_CHART_ANGLE_RADIUS = 76  # Radius for chart angles in dual charts
DUAL_CHART_PLANET_RADIUS_A = 110  # Alternate planet radius in dual charts
DUAL_CHART_PLANET_RADIUS_B = 130  # Default planet radius in dual charts

# Chart types that display two subjects
DUAL_CHART_TYPES = ("Transit", "Synastry", "DualReturnChart")


# =============================================================================
# MAIN FUNCTION
# =============================================================================


def draw_planets(
    radius: Union[int, float],
    available_kerykeion_celestial_points: list[KerykeionPointModel],
    available_planets_setting: Sequence[Mapping[str, Any]],
    third_circle_radius: Union[int, float],
    main_subject_first_house_degree_ut: Union[int, float],
    main_subject_seventh_house_degree_ut: Union[int, float],
    chart_type: ChartType,
    second_subject_available_kerykeion_celestial_points: Union[list[KerykeionPointModel], None] = None,
    external_view: bool = False,
    first_circle_radius: Union[int, float, None] = None,
    second_circle_radius: Union[int, float, None] = None,
    show_degree_indicators: bool = True,
) -> str:
    """
    Draws celestial points on an astrological chart.

    This function orchestrates the rendering of planets and points on various
    chart types. It handles position calculations, overlap prevention, and
    SVG generation for the chart elements.

    Args:
        radius: The overall radius of the chart in pixels.
        available_kerykeion_celestial_points: Celestial points for the main subject.
        available_planets_setting: Display settings for celestial points.
        third_circle_radius: Radius of the inner boundary circle.
        main_subject_first_house_degree_ut: First house cusp degree (Ascendant).
        main_subject_seventh_house_degree_ut: Seventh house cusp degree (Descendant).
        chart_type: Type of chart (Natal, Transit, Synastry, Return, etc.).
        second_subject_available_kerykeion_celestial_points: Points for second subject
            (required for Transit, Synastry, Return charts).
        external_view: If True, render planets on outer ring with connecting lines.
        first_circle_radius: Radius of the outer zodiac ring.
        second_circle_radius: Radius of the middle circle.
        show_degree_indicators: If True, show degree position indicators.

    Returns:
        SVG markup string containing all rendered celestial points.

    Raises:
        KerykeionException: If secondary points are required but not provided.
    """
    # Points to exclude from transit ring (house cusps)
    transit_ring_exclude_points: List[str] = list(get_args(Houses))
    output = ""

    # -------------------------------------------------------------------------
    # 1. Validate inputs for dual charts
    # -------------------------------------------------------------------------
    _validate_dual_chart_inputs(chart_type, second_subject_available_kerykeion_celestial_points)

    # -------------------------------------------------------------------------
    # 2. Extract positions from celestial points
    # -------------------------------------------------------------------------
    main_points_abs_positions = [p.abs_pos for p in available_kerykeion_celestial_points]

    secondary_points_abs_positions = []
    secondary_points_rel_positions = []
    if chart_type in DUAL_CHART_TYPES and second_subject_available_kerykeion_celestial_points:
        secondary_points_abs_positions = [p.abs_pos for p in second_subject_available_kerykeion_celestial_points]
        secondary_points_rel_positions = [p.position for p in second_subject_available_kerykeion_celestial_points]

    # -------------------------------------------------------------------------
    # 3. Build position-to-index mapping and sort for ordered processing
    # -------------------------------------------------------------------------
    position_index_map = {main_points_abs_positions[i]: i for i in range(len(available_planets_setting))}
    sorted_positions = sorted(position_index_map.keys())

    for i, pos in enumerate(sorted_positions):
        logging.debug(f"Planet index: {position_index_map[pos]}, degree: {pos}")

    # -------------------------------------------------------------------------
    # 4. Calculate position adjustments to prevent overlapping
    # -------------------------------------------------------------------------
    position_adjustments = _calculate_planet_adjustments(
        main_points_abs_positions,
        available_planets_setting,
        position_index_map,
        sorted_positions,
    )

    # -------------------------------------------------------------------------
    # 5. Draw main celestial points
    # -------------------------------------------------------------------------
    adjusted_offset = 0.0
    for position_idx, abs_position in enumerate(sorted_positions):
        point_idx = position_index_map[abs_position]

        # Determine radius based on chart type and point type
        point_radius = _determine_point_radius(point_idx, chart_type, bool(position_idx % 2), external_view)

        # Calculate position offsets
        adjusted_offset = _calculate_point_offset(
            main_subject_seventh_house_degree_ut,
            main_points_abs_positions[point_idx],
            position_adjustments[position_idx],
        )
        true_offset = _calculate_point_offset(
            main_subject_seventh_house_degree_ut,
            main_points_abs_positions[point_idx],
            0,
        )

        # Calculate coordinates
        point_x = sliceToX(0, radius - point_radius, adjusted_offset) + point_radius
        point_y = sliceToY(0, radius - point_radius, adjusted_offset) + point_radius

        # Determine scale factor
        scale_factor = 0.8 if chart_type in DUAL_CHART_TYPES or external_view else 1.0

        # Draw connecting lines for external view
        if external_view:
            output = _draw_external_natal_lines(
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
        output += _generate_point_svg(
            point_details,
            point_x,
            point_y,
            scale_factor,
            available_planets_setting[point_idx]["name"],
        )

    # -------------------------------------------------------------------------
    # 6. Draw degree indicators based on chart type
    # -------------------------------------------------------------------------
    if chart_type in ("Natal", "Composite", "SingleReturnChart"):
        # Single charts: draw indicators on outer ring
        if show_degree_indicators and first_circle_radius is not None and not external_view:
            output = _draw_primary_point_indicators(
                output=output,
                radius=radius,
                first_circle_radius=first_circle_radius,
                third_circle_radius=third_circle_radius,
                first_house_degree=main_subject_first_house_degree_ut,
                seventh_house_degree=main_subject_seventh_house_degree_ut,
                points_abs_positions=main_points_abs_positions,
                points_rel_positions=[p.position for p in available_kerykeion_celestial_points],
                points_settings=available_planets_setting,
            )
    elif chart_type in DUAL_CHART_TYPES:
        # Dual charts: draw indicators for both primary and secondary points
        if show_degree_indicators:
            # Secondary/outer points (transit planets)
            if secondary_points_abs_positions and secondary_points_rel_positions:
                output = _draw_secondary_points(
                    output,
                    radius,
                    main_subject_first_house_degree_ut,
                    main_subject_seventh_house_degree_ut,
                    secondary_points_abs_positions,
                    secondary_points_rel_positions,
                    available_planets_setting,
                    chart_type,
                    transit_ring_exclude_points,
                    adjusted_offset,
                )
            # Primary/inner points (natal planets)
            output = _draw_inner_point_indicators(
                output=output,
                radius=radius,
                third_circle_radius=third_circle_radius,
                first_house_degree=main_subject_first_house_degree_ut,
                seventh_house_degree=main_subject_seventh_house_degree_ut,
                points_abs_positions=main_points_abs_positions,
                points_rel_positions=[p.position for p in available_kerykeion_celestial_points],
                points_settings=available_planets_setting,
            )

    return output


# =============================================================================
# VALIDATION HELPERS
# =============================================================================


def _validate_dual_chart_inputs(
    chart_type: ChartType,
    secondary_points: Union[list[KerykeionPointModel], None],
) -> None:
    """Validate that dual charts have the required secondary points."""
    error_messages = {
        "Transit": "Secondary celestial points are required for Transit charts",
        "Synastry": "Secondary celestial points are required for Synastry charts",
    }
    if chart_type in error_messages and secondary_points is None:
        raise KerykeionException(error_messages[chart_type])


# =============================================================================
# POSITION CALCULATION HELPERS
# =============================================================================


def _calculate_planet_adjustments(
    points_abs_positions: Sequence[Any],
    points_settings: Sequence[Mapping[str, Any]],
    position_index_map: dict,
    sorted_positions: Sequence[Any],
) -> List[float]:
    """
    Calculate position adjustments for planets to prevent visual overlapping.

    This function identifies groups of planets that are too close together
    and calculates offset adjustments to spread them apart visually.

    Args:
        points_abs_positions: Absolute positions of all points.
        points_settings: Settings for all points.
        position_index_map: Mapping of position to point index.
        sorted_positions: Positions sorted in ascending order.

    Returns:
        List of adjustment values (in degrees) for each position.
    """
    planets_by_position: List[Optional[List[Union[int, float]]]] = [None] * len(position_index_map)
    point_groups: List[List[List[Union[int, float, str]]]] = []
    position_adjustments: List[float] = [0.0] * len(points_settings)
    is_group_open = False

    # Build position data and identify groups
    for position_idx, abs_position in enumerate(sorted_positions):
        point_idx = position_index_map[abs_position]

        # Calculate distances to adjacent points
        if len(sorted_positions) == 1:
            # Single planet: no adjacent planets to consider
            distance_to_prev = 360.0
            distance_to_next = 360.0
        else:
            prev_pos, next_pos = _get_adjacent_positions(
                position_idx, sorted_positions, position_index_map, points_abs_positions
            )
            distance_to_prev = degreeDiff(prev_pos, points_abs_positions[point_idx])
            distance_to_next = degreeDiff(next_pos, points_abs_positions[point_idx])

        planets_by_position[position_idx] = [point_idx, distance_to_prev, distance_to_next]
        label = points_settings[point_idx]["label"]
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

    # Apply adjustments for each group
    for group in point_groups:
        if len(group) == 2:
            _handle_two_point_group(group, planets_by_position, position_adjustments, PLANET_GROUPING_THRESHOLD)
        elif len(group) >= 3:
            _handle_multi_point_group(group, position_adjustments, PLANET_GROUPING_THRESHOLD)

    return position_adjustments


def _get_adjacent_positions(
    position_idx: int,
    sorted_positions: Sequence[Any],
    position_index_map: dict,
    points_abs_positions: Sequence[Any],
) -> Tuple[float, float]:
    """Get the absolute positions of adjacent points (with wraparound)."""
    total = len(sorted_positions)
    if position_idx == 0:
        prev_idx = position_index_map[sorted_positions[-1]]
        next_idx = position_index_map[sorted_positions[1]]
    elif position_idx == total - 1:
        prev_idx = position_index_map[sorted_positions[position_idx - 1]]
        next_idx = position_index_map[sorted_positions[0]]
    else:
        prev_idx = position_index_map[sorted_positions[position_idx - 1]]
        next_idx = position_index_map[sorted_positions[position_idx + 1]]

    return points_abs_positions[prev_idx], points_abs_positions[next_idx]


def _handle_two_point_group(
    group: list,
    planets_by_position: list,
    position_adjustments: list,
    threshold: float,
) -> None:
    """
    Handle positioning for a group of two celestial points that are close together.

    This function adjusts the positions of two overlapping points to spread
    them apart, using available space on either side.

    Args:
        group: Data about the two grouped points.
        planets_by_position: Position data for all planets.
        position_adjustments: List to store calculated adjustments.
        threshold: Minimum distance threshold for grouping.
    """
    next_to_a = group[0][0] - 1
    next_to_b = 0 if group[1][0] == (len(planets_by_position) - 1) else group[1][0] + 1

    # Both points have room on their outer sides
    if (group[0][1] > (2 * threshold)) and (group[1][2] > (2 * threshold)):
        position_adjustments[group[0][0]] = -(threshold - group[0][2]) / 2
        position_adjustments[group[1][0]] = +(threshold - group[0][2]) / 2
    # Only first point has room
    elif group[0][1] > (2 * threshold):
        position_adjustments[group[0][0]] = -threshold
    # Only second point has room
    elif group[1][2] > (2 * threshold):
        position_adjustments[group[1][0]] = +threshold
    # Adjacent points have room
    elif (planets_by_position[next_to_a][1] > (2.4 * threshold)) and (
        planets_by_position[next_to_b][2] > (2.4 * threshold)
    ):
        position_adjustments[next_to_a] = group[0][1] - threshold * 2
        position_adjustments[group[0][0]] = -threshold * 0.5
        position_adjustments[next_to_b] = -(group[1][2] - threshold * 2)
        position_adjustments[group[1][0]] = +threshold * 0.5
    # Only adjacent to first has room
    elif planets_by_position[next_to_a][1] > (2 * threshold):
        position_adjustments[next_to_a] = group[0][1] - threshold * 2.5
        position_adjustments[group[0][0]] = -threshold * 1.2
    # Only adjacent to second has room
    elif planets_by_position[next_to_b][2] > (2 * threshold):
        position_adjustments[next_to_b] = -(group[1][2] - threshold * 2.5)
        position_adjustments[group[1][0]] = +threshold * 1.2


def _handle_multi_point_group(
    group: list,
    position_adjustments: list,
    threshold: float,
) -> None:
    """
    Handle positioning for a group of three or more celestial points.

    Distributes points evenly within the available space.

    Args:
        group: Data about the grouped points.
        position_adjustments: List to store calculated adjustments.
        threshold: Minimum distance threshold for grouping.
    """
    group_size = len(group)

    # Calculate total available space
    available_space = group[0][1]  # Distance before first point
    for i in range(group_size):
        available_space += group[i][2]  # Add distance after each point

    # Calculate space needed to spread points
    needed_space = (3 * threshold) + (1.2 * (group_size - 1) * threshold)
    leftover_space = available_space - needed_space

    space_before_first = group[0][1]
    space_after_last = group[group_size - 1][2]

    # Determine starting position for the group
    if (space_before_first > (needed_space * 0.5)) and (space_after_last > (needed_space * 0.5)):
        start_position = space_before_first - (needed_space * 0.5)
    else:
        start_position = (leftover_space / (space_before_first + space_after_last)) * space_before_first

    # Apply positions if there's enough space
    if available_space > needed_space:
        position_adjustments[group[0][0]] = start_position - group[0][1] + (1.5 * threshold)
        for i in range(group_size - 1):
            position_adjustments[group[i + 1][0]] = 1.2 * threshold + position_adjustments[group[i][0]] - group[i][2]


def _calculate_point_offset(
    seventh_house_degree: Union[int, float],
    point_degree: Union[int, float],
    adjustment: Union[int, float],
) -> float:
    """Calculate the angular offset for placing a celestial point on the chart."""
    return (int(seventh_house_degree) / -1) + int(point_degree + adjustment)


def _determine_point_radius(
    point_idx: int,
    chart_type: str,
    is_alternate_position: bool,
    external_view: bool = False,
) -> int:
    """
    Determine the radial distance for placing a celestial point.

    Different radii are used to create visual separation between points
    and to distinguish between chart angles and regular planets.

    Args:
        point_idx: Index of the celestial point.
        chart_type: Type of the chart.
        is_alternate_position: Whether to use alternate positioning for visual separation.
        external_view: Whether external view mode is enabled.

    Returns:
        Radius value for the point placement.
    """
    is_chart_angle = CHART_ANGLE_MIN_INDEX < point_idx < CHART_ANGLE_MAX_INDEX

    # Dual charts (Transit, Synastry, Return)
    if chart_type in DUAL_CHART_TYPES:
        if is_chart_angle:
            return DUAL_CHART_ANGLE_RADIUS
        return DUAL_CHART_PLANET_RADIUS_A if is_alternate_position else DUAL_CHART_PLANET_RADIUS_B

    # Natal chart with external view
    # In external view, all points are placed on outer ring with small offset variations
    # Original calculations: amin = 74-10=64, bmin = 94-10=84, cmin = 40-10=30
    # Result: 74 - 64 = 10, 94 - 84 = 10, 40 - 30 = 10
    if external_view:
        if is_chart_angle:
            return 40 - (40 - 10)  # = 10
        elif is_alternate_position:
            return 74 - (74 - 10)  # = 10
        else:
            return 94 - (94 - 10)  # = 10

    # Standard natal chart
    if is_chart_angle:
        return 40
    return 74 if is_alternate_position else 94


# =============================================================================
# INDICATOR HELPERS (Shared Logic)
# =============================================================================


def _calculate_indicator_adjustments(
    points_abs_positions: Sequence[Any],
    points_settings: Sequence[Mapping[str, Any]],
    chart_type: str = "",
    exclude_points: Optional[list[str]] = None,
) -> dict[int, float]:
    """
    Calculate position adjustments for degree indicators to prevent overlapping.

    This helper is used by multiple indicator-drawing functions to spread
    out degree labels that would otherwise overlap.

    Args:
        points_abs_positions: Absolute positions of all points.
        points_settings: Settings for all points.
        chart_type: Type of chart (used for filtering).
        exclude_points: Point names to exclude from processing.

    Returns:
        Dictionary mapping point index to adjustment value.
    """
    position_adjustments: dict[int, float] = {i: 0.0 for i in range(len(points_settings))}
    exclude_points = exclude_points or []

    # Build position-to-index mapping (excluding filtered points)
    position_index_map = {}
    for i in range(len(points_settings)):
        if chart_type == "Transit" and points_settings[i]["name"] in exclude_points:
            continue
        position_index_map[points_abs_positions[i]] = i

    sorted_positions = sorted(position_index_map.keys())

    # Identify groups of close points
    point_groups: List[List[int]] = []
    in_group = False

    for pos_idx, abs_position in enumerate(sorted_positions):
        point_a_idx = position_index_map[abs_position]
        point_b_idx = position_index_map[
            sorted_positions[0] if pos_idx == len(sorted_positions) - 1 else sorted_positions[pos_idx + 1]
        ]

        distance = degreeDiff(points_abs_positions[point_a_idx], points_abs_positions[point_b_idx])

        if distance <= INDICATOR_GROUPING_THRESHOLD:
            if in_group:
                point_groups[-1].append(point_b_idx)
            else:
                point_groups.append([point_a_idx, point_b_idx])
                in_group = True
        else:
            in_group = False

    # Apply adjustments based on group size
    for group in point_groups:
        _apply_group_adjustments(group, position_adjustments)

    return position_adjustments


def _apply_group_adjustments(group: list[int], adjustments: dict[int, float]) -> None:
    """
    Apply position adjustments for a group of overlapping indicators.

    Used for primary indicators (natal/single charts) and inner indicators (dual charts).
    These adjustments provide wider spacing for better visual separation.

    Args:
        group: List of point indices that form an overlapping group.
        adjustments: Dictionary to store the calculated adjustment values.
    """
    size = len(group)
    if size == 2:
        adjustments[group[0]] = -1.5
        adjustments[group[1]] = 1.5
    elif size == 3:
        adjustments[group[0]] = -2.0
        adjustments[group[1]] = 0.0
        adjustments[group[2]] = 2.0
    elif size == 4:
        adjustments[group[0]] = -3.0
        adjustments[group[1]] = -1.0
        adjustments[group[2]] = 1.0
        adjustments[group[3]] = 3.0
    elif size >= 5:
        spread = 1.5
        mid = (size - 1) / 2
        for i, idx in enumerate(group):
            adjustments[idx] = (i - mid) * spread


def _apply_secondary_group_adjustments(group: list[int], adjustments: dict[int, float]) -> None:
    """
    Apply position adjustments for a group of overlapping secondary/transit points.

    Used specifically for secondary points (transit, synastry, return charts).
    These adjustments use tighter spacing values that are appropriate for the
    outer ring where transit planets are displayed.

    Note: These values differ from _apply_group_adjustments to maintain
    backward compatibility with the original chart rendering behavior.

    Args:
        group: List of point indices that form an overlapping group.
        adjustments: Dictionary to store the calculated adjustment values.
    """
    size = len(group)
    if size == 2:
        # Tighter spacing for secondary points: -1.0/+1.0 instead of -1.5/+1.5
        adjustments[group[0]] = -1.0
        adjustments[group[1]] = 1.0
    elif size == 3:
        # Tighter spacing: -1.5/0/+1.5 instead of -2.0/0/+2.0
        adjustments[group[0]] = -1.5
        adjustments[group[1]] = 0.0
        adjustments[group[2]] = 1.5
    elif size == 4:
        # Tighter spacing: -2.0/-1.0/+1.0/+2.0 instead of -3.0/-1.0/+1.0/+3.0
        adjustments[group[0]] = -2.0
        adjustments[group[1]] = -1.0
        adjustments[group[2]] = 1.0
        adjustments[group[3]] = 2.0
    # Note: Groups of 5+ are not handled for secondary points in original code


def _calculate_secondary_indicator_adjustments(
    points_abs_positions: Sequence[Any],
    points_settings: Sequence[Mapping[str, Any]],
    chart_type: str = "",
    exclude_points: Optional[list[str]] = None,
) -> dict[int, float]:
    """
    Calculate position adjustments for secondary/transit point indicators.

    This is similar to _calculate_indicator_adjustments but uses tighter spacing
    values appropriate for the outer transit ring. The adjustment values match
    the original implementation's behavior for transit/synastry/return charts.

    Args:
        points_abs_positions: Absolute positions of all points.
        points_settings: Settings for all points.
        chart_type: Type of chart (used for filtering).
        exclude_points: Point names to exclude from processing.

    Returns:
        Dictionary mapping point index to adjustment value.
    """
    position_adjustments: dict[int, float] = {i: 0.0 for i in range(len(points_settings))}
    exclude_points = exclude_points or []

    # Build position-to-index mapping (excluding filtered points)
    position_index_map = {}
    for i in range(len(points_settings)):
        if chart_type == "Transit" and points_settings[i]["name"] in exclude_points:
            continue
        position_index_map[points_abs_positions[i]] = i

    sorted_positions = sorted(position_index_map.keys())

    # Identify groups of close points
    point_groups: List[List[int]] = []
    in_group = False

    for pos_idx, abs_position in enumerate(sorted_positions):
        point_a_idx = position_index_map[abs_position]
        point_b_idx = position_index_map[
            sorted_positions[0] if pos_idx == len(sorted_positions) - 1 else sorted_positions[pos_idx + 1]
        ]

        distance = degreeDiff(points_abs_positions[point_a_idx], points_abs_positions[point_b_idx])

        if distance <= INDICATOR_GROUPING_THRESHOLD:
            if in_group:
                point_groups[-1].append(point_b_idx)
            else:
                point_groups.append([point_a_idx, point_b_idx])
                in_group = True
        else:
            in_group = False

    # Apply secondary-specific adjustments (tighter spacing)
    for group in point_groups:
        _apply_secondary_group_adjustments(group, position_adjustments)

    return position_adjustments


def _calculate_text_rotation(
    first_house_degree: float,
    point_abs_position: float,
) -> Tuple[float, str]:
    """
    Calculate text rotation angle and anchor for degree labels.

    The text is rotated to follow the radial direction and flipped
    when on the left side of the chart to ensure readability.

    Args:
        first_house_degree: Degree of the first house (Ascendant).
        point_abs_position: Absolute position of the point.

    Returns:
        Tuple of (rotation_angle, text_anchor).
    """
    rotation = first_house_degree - point_abs_position
    text_anchor = "end"

    # Normalize rotation to [-180, 180] range
    while rotation > 180:
        rotation -= 360
    while rotation < -180:
        rotation += 360

    # Flip text on left side of chart for readability
    if rotation < -90 or rotation > 90:
        rotation += 180 if rotation < 0 else -180
        text_anchor = "start"

    return rotation, text_anchor


# =============================================================================
# SVG RENDERING FUNCTIONS
# =============================================================================


def _generate_point_svg(
    point_details: KerykeionPointModel,
    x: float,
    y: float,
    scale: float,
    point_name: str,
) -> str:
    """
    Generate SVG markup for a celestial point.

    Creates a group element containing the point symbol with proper
    positioning, scaling, and metadata attributes.

    Args:
        point_details: Model containing point data.
        x: X-coordinate for the point.
        y: Y-coordinate for the point.
        scale: Scale factor for the symbol.
        point_name: Name used for the SVG symbol reference.

    Returns:
        SVG markup string for the celestial point.
    """
    svg = f'<g kr:node="ChartPoint" kr:house="{point_details["house"]}" '
    svg += f'kr:sign="{point_details["sign"]}" kr:absoluteposition="{point_details["abs_pos"]}" '
    svg += f'kr:signposition="{point_details["position"]}" kr:slug="{point_details["name"]}" '
    svg += f'transform="translate(-{12 * scale},-{12 * scale}) scale({scale})">'
    svg += f'<use x="{x * (1 / scale)}" y="{y * (1 / scale)}" xlink:href="#{point_name}" />'
    svg += "</g>"
    return svg


def _draw_external_natal_lines(
    output: str,
    radius: Union[int, float],
    third_circle_radius: Union[int, float],
    point_radius: Union[int, float],
    true_offset: Union[int, float],
    adjusted_offset: Union[int, float],
    color: str,
) -> str:
    """
    Draw connecting lines for external view mode.

    Creates two line segments: one from the chart circle to the true
    position, and another from there to the adjusted (visual) position.

    Args:
        output: Current SVG output to append to.
        radius: Chart radius.
        third_circle_radius: Inner circle radius.
        point_radius: Point placement radius.
        true_offset: True angular position.
        adjusted_offset: Visually adjusted position.
        color: Line color.

    Returns:
        Updated SVG output with added lines.
    """
    # First line: from chart edge to intermediate position
    x1 = sliceToX(0, radius - third_circle_radius, true_offset) + third_circle_radius
    y1 = sliceToY(0, radius - third_circle_radius, true_offset) + third_circle_radius
    x2 = sliceToX(0, radius - point_radius - 30, true_offset) + point_radius + 30
    y2 = sliceToY(0, radius - point_radius - 30, true_offset) + point_radius + 30
    output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
    output += f'style="stroke-width:1px;stroke:{color};stroke-opacity:.3;"/>\n'

    # Second line: from intermediate to final adjusted position
    x1, y1 = x2, y2
    x2 = sliceToX(0, radius - point_radius - 10, adjusted_offset) + point_radius + 10
    y2 = sliceToY(0, radius - point_radius - 10, adjusted_offset) + point_radius + 10
    output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
    output += f'style="stroke-width:1px;stroke:{color};stroke-opacity:.5;"/>\n'

    return output


# =============================================================================
# DEGREE INDICATOR FUNCTIONS
# =============================================================================


def _draw_primary_point_indicators(
    output: str,
    radius: Union[int, float],
    first_circle_radius: Union[int, float],
    third_circle_radius: Union[int, float],
    first_house_degree: Union[int, float],
    seventh_house_degree: Union[int, float],
    points_abs_positions: list[Union[int, float]],
    points_rel_positions: list[Union[int, float]],
    points_settings: Sequence[Mapping[str, Any]],
) -> str:
    """
    Draw degree indicators for primary points in single-subject charts.

    Each indicator consists of a radial line at the point's position
    and a rotated text label showing the degree within the sign.

    Args:
        output: Current SVG output to append to.
        radius: Chart radius.
        first_circle_radius: Outer zodiac ring radius.
        third_circle_radius: Inner boundary radius.
        first_house_degree: Ascendant degree.
        seventh_house_degree: Descendant degree.
        points_abs_positions: Absolute positions of points.
        points_rel_positions: Positions within signs.
        points_settings: Display settings for points.

    Returns:
        Updated SVG output with added indicators.
    """
    # Calculate adjustments for overlapping indicators
    position_adjustments = _calculate_indicator_adjustments(points_abs_positions, points_settings)
    zero_point = 360 - seventh_house_degree

    for point_idx in range(len(points_settings)):
        point_offset = zero_point + points_abs_positions[point_idx]
        if point_offset > 360:
            point_offset -= 360

        # Draw radial indicator line
        x1 = sliceToX(0, radius - first_circle_radius + 4, point_offset) + first_circle_radius - 4
        y1 = sliceToY(0, radius - first_circle_radius + 4, point_offset) + first_circle_radius - 4
        x2 = sliceToX(0, radius - first_circle_radius - 4, point_offset) + first_circle_radius + 4
        y2 = sliceToY(0, radius - first_circle_radius - 4, point_offset) + first_circle_radius + 4

        point_color = points_settings[point_idx]["color"]
        output += f'<line class="planet-degree-line" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        output += f'style="stroke: {point_color}; stroke-width: 1px; stroke-opacity:.8;"/>'

        # Draw rotated degree text
        rotation, text_anchor = _calculate_text_rotation(first_house_degree, points_abs_positions[point_idx])
        x_offset = 1 if text_anchor == "end" else -1
        adjusted_point_offset = point_offset + position_adjustments[point_idx]
        text_radius = first_circle_radius - 5.0

        deg_x = sliceToX(0, radius - text_radius, adjusted_point_offset + x_offset) + text_radius
        deg_y = sliceToY(0, radius - text_radius, adjusted_point_offset + x_offset) + text_radius

        degree_text = convert_decimal_to_degree_string(points_rel_positions[point_idx], format_type="1")
        output += f'<g transform="translate({deg_x},{deg_y})">'
        output += f'<text transform="rotate({rotation})" text-anchor="{text_anchor}" '
        output += f'style="fill: {point_color}; font-size: 10px;">{degree_text}</text></g>'

    return output


def _draw_inner_point_indicators(
    output: str,
    radius: Union[int, float],
    third_circle_radius: Union[int, float],
    first_house_degree: Union[int, float],
    seventh_house_degree: Union[int, float],
    points_abs_positions: list[Union[int, float]],
    points_rel_positions: list[Union[int, float]],
    points_settings: Sequence[Mapping[str, Any]],
) -> str:
    """
    Draw degree indicators for inner/natal points in dual-subject charts.

    Similar to primary indicators but positioned on the inner boundary
    between the natal planet ring and the zodiac signs.

    Args:
        output: Current SVG output.
        radius: Chart radius.
        third_circle_radius: Inner boundary radius.
        first_house_degree: Ascendant degree.
        seventh_house_degree: Descendant degree.
        points_abs_positions: Absolute positions.
        points_rel_positions: Sign positions.
        points_settings: Display settings.

    Returns:
        Updated SVG output with indicators.
    """
    position_adjustments = _calculate_indicator_adjustments(points_abs_positions, points_settings)
    zero_point = 360 - seventh_house_degree

    for point_idx in range(len(points_settings)):
        point_offset = zero_point + points_abs_positions[point_idx]
        if point_offset > 360:
            point_offset -= 360

        # Draw radial line at inner boundary
        x1 = sliceToX(0, radius - NATAL_INDICATOR_OFFSET + 4, point_offset) + NATAL_INDICATOR_OFFSET - 4
        y1 = sliceToY(0, radius - NATAL_INDICATOR_OFFSET + 4, point_offset) + NATAL_INDICATOR_OFFSET - 4
        x2 = sliceToX(0, radius - NATAL_INDICATOR_OFFSET - 4, point_offset) + NATAL_INDICATOR_OFFSET + 4
        y2 = sliceToY(0, radius - NATAL_INDICATOR_OFFSET - 4, point_offset) + NATAL_INDICATOR_OFFSET + 4

        point_color = points_settings[point_idx]["color"]
        output += f'<line class="planet-degree-line-inner" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        output += f'style="stroke: {point_color}; stroke-width: 1px; stroke-opacity:.8;"/>'

        # Draw degree text (positioned toward center)
        rotation, text_anchor = _calculate_text_rotation(first_house_degree, points_abs_positions[point_idx])
        # Inner text uses opposite anchor
        text_anchor = "start" if text_anchor == "end" else "end"

        adjusted_point_offset = point_offset + position_adjustments[point_idx]
        text_radius = NATAL_INDICATOR_OFFSET + 5.0

        deg_x = sliceToX(0, radius - text_radius, adjusted_point_offset) + text_radius
        deg_y = sliceToY(0, radius - text_radius, adjusted_point_offset) + text_radius

        degree_text = convert_decimal_to_degree_string(points_rel_positions[point_idx], format_type="1")
        output += f'<g transform="translate({deg_x},{deg_y})">'
        output += f'<text transform="rotate({rotation})" text-anchor="{text_anchor}" '
        output += f'style="fill: {point_color}; font-size: 8px; dominant-baseline: middle;">{degree_text}</text></g>'

    return output


def _draw_secondary_points(
    output: str,
    radius: Union[int, float],
    first_house_degree: Union[int, float],
    seventh_house_degree: Union[int, float],
    points_abs_positions: list[Union[int, float]],
    points_rel_positions: list[Union[int, float]],
    points_settings: Sequence[Mapping[str, Any]],
    chart_type: str,
    exclude_points: list[str],
    main_offset: float,
) -> str:
    """
    Draw secondary celestial points for transit/synastry charts.

    Renders the outer ring of planets (transit positions) with symbols,
    connecting lines, and degree indicators.

    Args:
        output: Current SVG output.
        radius: Chart radius.
        first_house_degree: Ascendant degree.
        seventh_house_degree: Descendant degree.
        points_abs_positions: Absolute positions of secondary points.
        points_rel_positions: Positions within signs.
        points_settings: Display settings.
        chart_type: Type of chart.
        exclude_points: Points to exclude from rendering.
        main_offset: Offset for connecting line drawing.

    Returns:
        Updated SVG output with secondary points.
    """
    # Calculate position adjustments using secondary-specific spacing values
    # This differs from _calculate_indicator_adjustments which uses wider spacing
    position_adjustments = _calculate_secondary_indicator_adjustments(
        points_abs_positions, points_settings, chart_type, exclude_points
    )

    # Build position map (excluding houses for Transit)
    position_index_map = {}
    for i in range(len(points_settings)):
        if chart_type == "Transit" and points_settings[i]["name"] in exclude_points:
            continue
        position_index_map[points_abs_positions[i]] = i

    sorted_positions = sorted(position_index_map.keys())
    zero_point = 360 - seventh_house_degree
    alternate_position = False
    point_idx = 0

    # Draw each secondary point
    for abs_position in sorted_positions:
        point_idx = position_index_map[abs_position]

        if chart_type == "Transit" and points_settings[point_idx]["name"] in exclude_points:
            continue

        # Determine point radius (alternating for visual separation)
        is_chart_angle = CHART_ANGLE_MIN_INDEX < point_idx < CHART_ANGLE_MAX_INDEX
        if is_chart_angle:
            point_radius = 9
        elif alternate_position:
            point_radius = 18
            alternate_position = False
        else:
            point_radius = 26
            alternate_position = True

        # Calculate position
        point_offset = zero_point + points_abs_positions[point_idx]
        if point_offset > 360:
            point_offset -= 360

        # Draw point symbol
        point_x = sliceToX(0, radius - point_radius, point_offset) + point_radius
        point_y = sliceToY(0, radius - point_radius, point_offset) + point_radius
        output += '<g class="transit-planet-name" transform="translate(-6,-6)"><g transform="scale(0.5)">'
        output += (
            f'<use x="{point_x * 2}" y="{point_y * 2}" xlink:href="#{points_settings[point_idx]["name"]}" /></g></g>'
        )

        # Draw indicator line
        x1 = sliceToX(0, radius + 3, point_offset) - 3
        y1 = sliceToY(0, radius + 3, point_offset) - 3
        x2 = sliceToX(0, radius - 3, point_offset) + 3
        y2 = sliceToY(0, radius - 3, point_offset) + 3
        point_color = points_settings[point_idx]["color"]
        output += f'<line class="transit-planet-line" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        output += f'style="stroke: {point_color}; stroke-width: 1px; stroke-opacity:.8;"/>'

        # Draw degree text
        rotation, text_anchor = _calculate_text_rotation(first_house_degree, points_abs_positions[point_idx])
        x_offset = 1 if text_anchor == "end" else -1
        adjusted_point_offset = point_offset + position_adjustments[point_idx]
        text_radius = -3.0

        deg_x = sliceToX(0, radius - text_radius, adjusted_point_offset + x_offset) + text_radius
        deg_y = sliceToY(0, radius - text_radius, adjusted_point_offset + x_offset) + text_radius

        degree_text = convert_decimal_to_degree_string(points_rel_positions[point_idx], format_type="1")
        output += f'<g transform="translate({deg_x},{deg_y})">'
        output += f'<text transform="rotate({rotation})" text-anchor="{text_anchor}" '
        output += f'style="fill: {point_color}; font-size: 10px;">{degree_text}</text></g>'

    # Draw connecting lines for the main reference point
    dropin = 36 if chart_type in DUAL_CHART_TYPES else 0
    x1 = sliceToX(0, radius - (dropin + 3), main_offset) + (dropin + 3)
    y1 = sliceToY(0, radius - (dropin + 3), main_offset) + (dropin + 3)
    x2 = sliceToX(0, radius - (dropin - 3), main_offset) + (dropin - 3)
    y2 = sliceToY(0, radius - (dropin - 3), main_offset) + (dropin - 3)
    point_color = points_settings[point_idx]["color"]
    output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
    output += f'style="stroke: {point_color}; stroke-width: 2px; stroke-opacity:.6;"/>'

    # Second connecting line segment
    dropin = 160 if chart_type in DUAL_CHART_TYPES else 120
    x1 = sliceToX(0, radius - dropin, main_offset) + dropin
    y1 = sliceToY(0, radius - dropin, main_offset) + dropin
    x2 = sliceToX(0, radius - (dropin - 3), main_offset) + (dropin - 3)
    y2 = sliceToY(0, radius - (dropin - 3), main_offset) + (dropin - 3)
    output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
    output += f'style="stroke: {point_color}; stroke-width: 2px; stroke-opacity:.6;"/>'

    return output
