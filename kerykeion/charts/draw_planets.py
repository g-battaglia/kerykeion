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

from kerykeion.charts.charts_utils import (
    DOUBLE_CHART_TYPES,
    degree_difference,
    escape_svg_text,
    wheel_x,
    wheel_y,
    convert_decimal_to_degree_string,
)
from kerykeion.schemas import KerykeionException, ChartType, KerykeionPointModel
from kerykeion.schemas.literals import Houses
from kerykeion.settings.chart_defaults import resolve_glyph_id
import logging
from typing import Union, get_args, Optional, Sequence, Mapping, Any

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

# Grouping thresholds (in degrees)
PLANET_GROUPING_THRESHOLD = 3.4  # Distance to consider planets as grouped
INDICATOR_GROUPING_THRESHOLD = 2.5  # Distance for indicator overlap detection

# Chart angle indices (ASC, MC, DSC, IC are between these indices)
# The four chart angles are classified by NAME: the historical index window
# (22 < idx < 27, inherited from the fixed OpenAstro point ordering) pointed at
# Ceres/Pallas/Juno/Vesta in the v6 catalog and shifted with any active-points
# filtering.
CHART_ANGLE_NAMES: tuple[str, ...] = ("Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli")

# Radius offsets for different chart elements
NATAL_INDICATOR_OFFSET = 72  # Offset for inner chart degree indicators
DUAL_CHART_ANGLE_RADIUS = 76  # Radius for chart angles in dual charts
DUAL_CHART_PLANET_RADIUS_A = 110  # Alternate planet radius in dual charts
DUAL_CHART_PLANET_RADIUS_B = 130  # Default planet radius in dual charts

# Chart types that can display two subjects. Every dual type requires
# secondary points — keeping the two names aliased means a future dual chart
# type cannot be added to one list and silently render without its outer wheel.
DUAL_CHART_TYPES = DOUBLE_CHART_TYPES
REQUIRED_SECONDARY_CHART_TYPES: tuple[ChartType, ...] = DOUBLE_CHART_TYPES


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
    second_subject_available_planets_setting: Union[Sequence[Mapping[str, Any]], None] = None,
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
            (required for Transit, Synastry, Progression charts).
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
    transit_ring_exclude_points: list[str] = list(get_args(Houses))
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
    # 3. Build position/index pairs and sort for ordered processing
    # -------------------------------------------------------------------------
    # A list of (abs_pos, index) tuples is used instead of a {abs_pos: index}
    # dict so that two points sharing the exact same absolute position (e.g.
    # an exact conjunction) are both kept and rendered.
    # Bound to the shorter of the two lists so a settings list longer than the
    # collected points (e.g. a return subject with fewer points than settings)
    # can't IndexError — the same length guard the sibling indicator helpers use.
    sorted_position_entries = sorted(
        (main_points_abs_positions[i], i)
        for i in range(min(len(available_planets_setting), len(main_points_abs_positions)))
    )
    sorted_positions = [entry[0] for entry in sorted_position_entries]
    sorted_point_indices = [entry[1] for entry in sorted_position_entries]

    # -------------------------------------------------------------------------
    # 4. Calculate position adjustments to prevent overlapping
    # -------------------------------------------------------------------------
    position_adjustments = _calculate_planet_adjustments(
        main_points_abs_positions,
        available_planets_setting,
        sorted_point_indices,
        sorted_positions,
    )

    # -------------------------------------------------------------------------
    # 5. Draw main celestial points
    # -------------------------------------------------------------------------
    adjusted_offset = 0.0
    for position_idx, abs_position in enumerate(sorted_positions):
        point_idx = sorted_point_indices[position_idx]

        # Determine radius based on chart type and point type
        point_radius = _determine_point_radius(
            available_planets_setting[point_idx]["name"], chart_type, bool(position_idx % 2), external_view
        )

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
        point_x = wheel_x(0, radius - point_radius, adjusted_offset) + point_radius
        point_y = wheel_y(0, radius - point_radius, adjusted_offset) + point_radius

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
                available_planets_setting[point_idx]["name"],
                abs_pos=main_points_abs_positions[point_idx],
            )

        # Draw the celestial point SVG element
        point_details = available_kerykeion_celestial_points[point_idx]
        # In dual charts, main subject is horoscope "0"
        h_id = "0" if chart_type in DUAL_CHART_TYPES else None
        # v6: dynamic catalog fixed stars carry a ``glyph_id`` setting pointing
        # to a generic ``#FixedStar`` symbol (their per-star <symbol> doesn't
        # exist in the template). Other points fall back to their own slug.
        glyph_id = available_planets_setting[point_idx].get("glyph_id")
        output += _generate_point_svg(
            point_details,
            point_x,
            point_y,
            scale_factor,
            available_planets_setting[point_idx]["name"],
            horoscope_id=h_id,
            glyph_id=glyph_id,
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
        # Dual charts: the secondary/outer points (transit or partner planets)
        # are ALWAYS drawn — their glyphs are chart content, not an indicator.
        # ``show_degree_indicators`` only gates tick lines and degree labels.
        if secondary_points_abs_positions and secondary_points_rel_positions:
            # v6: use the per-second-subject settings list if provided so
            # the iteration aligns with the actual collected points. Falls
            # back to the shared ``available_planets_setting`` to keep
            # legacy callers working (single-subject + transit charts where
            # the second subject mirrors the primary settings).
            secondary_settings = (
                second_subject_available_planets_setting
                if second_subject_available_planets_setting is not None
                else available_planets_setting
            )
            output = _draw_secondary_points(
                output,
                radius,
                main_subject_first_house_degree_ut,
                main_subject_seventh_house_degree_ut,
                secondary_points_abs_positions,
                secondary_points_rel_positions,
                secondary_settings,
                chart_type,
                transit_ring_exclude_points,
                second_subject_available_kerykeion_celestial_points,
                show_degree_indicators=show_degree_indicators,
            )
        # Primary/inner points (natal planets): pure degree indicators, so the
        # flag gates the whole call (their glyphs are drawn in section 5).
        if show_degree_indicators:
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
    if chart_type in REQUIRED_SECONDARY_CHART_TYPES and secondary_points is None:
        raise KerykeionException(f"Secondary celestial points are required for {chart_type} charts")


# =============================================================================
# POSITION CALCULATION HELPERS
# =============================================================================


def _calculate_planet_adjustments(
    points_abs_positions: Sequence[Any],
    points_settings: Sequence[Mapping[str, Any]],
    sorted_point_indices: Sequence[int],
    sorted_positions: Sequence[Any],
) -> list[float]:
    """
    Calculate position adjustments for planets to prevent visual overlapping.

    This function identifies groups of planets that are too close together
    and calculates offset adjustments to spread them apart visually.

    Args:
        points_abs_positions: Absolute positions of all points.
        points_settings: Settings for all points.
        sorted_point_indices: Point indices aligned with ``sorted_positions``.
        sorted_positions: Positions sorted in ascending order.

    Returns:
        List of adjustment values (in degrees) for each position.
    """
    planets_by_position: list[Optional[list[Union[int, float]]]] = [None] * len(sorted_point_indices)
    point_groups: list[list[list[Union[int, float, str]]]] = []
    position_adjustments: list[float] = [0.0] * len(points_settings)
    is_group_open = False

    # First pass: compute adjacent distances for every position
    for position_idx, abs_position in enumerate(sorted_positions):
        point_idx = sorted_point_indices[position_idx]

        # Calculate distances to adjacent points
        if len(sorted_positions) == 1:
            # Single planet: no adjacent planets to consider
            distance_to_prev = 360.0
            distance_to_next = 360.0
        else:
            prev_pos, next_pos = _get_adjacent_positions(
                position_idx, sorted_positions, sorted_point_indices, points_abs_positions
            )
            distance_to_prev = degree_difference(prev_pos, points_abs_positions[point_idx])
            distance_to_next = degree_difference(next_pos, points_abs_positions[point_idx])

        planets_by_position[position_idx] = [point_idx, distance_to_prev, distance_to_next]

    # Second pass: identify groups scanning the ring circularly, starting just
    # after the widest gap. Starting at index 0 would split a run that
    # straddles 0°/360° (e.g. 29°58' Pisces + 0°10' Aries) into two fragments,
    # leaving the wrap pair without any anti-collision adjustment.
    total_positions = len(sorted_positions)
    scan_start = (
        max(range(total_positions), key=lambda idx: planets_by_position[idx][1])  # type: ignore[index]
        if total_positions
        else 0
    )
    for scan_step in range(total_positions):
        position_idx = (scan_start + scan_step) % total_positions
        point_idx, distance_to_prev, distance_to_next = planets_by_position[position_idx]  # type: ignore[misc, assignment]
        label = points_settings[int(point_idx)]["label"]

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

    if point_groups and logger.isEnabledFor(logging.DEBUG):
        logger.debug("Layout overlap groups")
        for group_idx, group in enumerate(point_groups, start=1):
            group_entries: list[str] = []
            for point_data in group:
                position_idx = int(point_data[0])
                label = str(point_data[3])
                abs_position = float(sorted_positions[position_idx])
                group_entries.append(f"{label}({abs_position:.2f})")
            logger.debug("  group %d: %s", group_idx, " ".join(group_entries))

    return position_adjustments


def _get_adjacent_positions(
    position_idx: int,
    sorted_positions: Sequence[Any],
    sorted_point_indices: Sequence[int],
    points_abs_positions: Sequence[Any],
) -> tuple[float, float]:
    """Get the absolute positions of adjacent points (with wraparound)."""
    total = len(sorted_positions)
    if position_idx == 0:
        prev_idx = sorted_point_indices[-1]
        next_idx = sorted_point_indices[1]
    elif position_idx == total - 1:
        prev_idx = sorted_point_indices[position_idx - 1]
        next_idx = sorted_point_indices[0]
    else:
        prev_idx = sorted_point_indices[position_idx - 1]
        next_idx = sorted_point_indices[position_idx + 1]

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
        # Guard the divisor: a group of >=3 points at the exact same absolute
        # position gives space_before_first == space_after_last == 0 (0/0). Fall
        # back to centering the group instead of raising ZeroDivisionError.
        edge_space = space_before_first + space_after_last
        start_position = (
            (leftover_space / edge_space) * space_before_first if edge_space else space_before_first
        )

    # Apply positions if there's enough space
    if available_space > needed_space:
        position_adjustments[group[0][0]] = start_position - group[0][1] + (1.5 * threshold)
        for i in range(group_size - 1):
            position_adjustments[group[i + 1][0]] = 1.2 * threshold + position_adjustments[group[i][0]] - group[i][2]
    else:
        # Not enough room for the full spread: distribute the points evenly
        # across whatever space is available instead of giving up entirely —
        # dense stelliums would otherwise render fully stacked, mitigated only
        # by the alternating point radii.
        step = available_space / (group_size + 1)
        position_adjustments[group[0][0]] = step - group[0][1]
        for i in range(group_size - 1):
            position_adjustments[group[i + 1][0]] = step + position_adjustments[group[i][0]] - group[i][2]


def _calculate_point_offset(
    seventh_house_degree: Union[int, float],
    point_degree: Union[int, float],
    adjustment: Union[int, float],
) -> float:
    """Calculate the angular offset for placing a celestial point on the chart."""
    return -int(seventh_house_degree) + int(point_degree + adjustment)


def _determine_point_radius(
    point_name: str,
    chart_type: str,
    is_alternate_position: bool,
    external_view: bool = False,
) -> int:
    """
    Determine the radial distance for placing a celestial point.

    Different radii are used to create visual separation between points
    and to distinguish between chart angles and regular planets.

    Args:
        point_name: Name of the celestial point (angles get a dedicated radius).
        chart_type: Type of the chart.
        is_alternate_position: Whether to use alternate positioning for visual separation.
        external_view: Whether external view mode is enabled.

    Returns:
        Radius value for the point placement.
    """
    is_chart_angle = point_name in CHART_ANGLE_NAMES

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
        return 10

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

    # Build sorted (position, index) pairs (excluding filtered points). A list
    # of tuples is used instead of a {abs_pos: index} dict so points sharing
    # the exact same absolute position are all kept.
    # v6 safety net: bound to the shorter of the two lists so an upstream
    # mismatch (e.g. a return subject with fewer collected points than
    # active_points settings) can't trigger an IndexError. Callers are
    # expected to pass aligned lists; this guard is purely defensive.
    n = min(len(points_settings), len(points_abs_positions))
    sorted_point_indices = [
        index
        for _, index in sorted(
            (points_abs_positions[i], i)
            for i in range(n)
            if not (chart_type == "Transit" and points_settings[i]["name"] in exclude_points)
        )
    ]

    # Identify groups of close points (circular-aware: a run straddling the
    # list start is one group, not two overwriting each other).
    point_groups = _group_close_indicators(sorted_point_indices, points_abs_positions)

    # Apply adjustments based on group size
    for group in point_groups:
        _apply_group_adjustments(group, position_adjustments)

    return position_adjustments


def _group_close_indicators(
    sorted_point_indices: list[int],
    points_abs_positions: Sequence[Any],
) -> list[list[int]]:
    """Group circularly-adjacent indicators closer than the grouping threshold.

    The positions live on a circle: the run detection must treat the
    last->first pair like any other, and a run straddling the list start must
    stay ONE group — building it as a separate group would overwrite the first
    group's adjustments and leave labels overlapping.
    """
    m = len(sorted_point_indices)
    if m < 2:
        return []

    close_to_next = [
        degree_difference(
            points_abs_positions[sorted_point_indices[k]],
            points_abs_positions[sorted_point_indices[(k + 1) % m]],
        )
        <= INDICATOR_GROUPING_THRESHOLD
        for k in range(m)
    ]

    if all(close_to_next):
        # Every neighbor pair is close: one single circular group.
        return [list(sorted_point_indices)]

    # Rotate to a run boundary so each maximal run is scanned contiguously.
    start = next(k for k in range(m) if not close_to_next[(k - 1) % m])
    groups: list[list[int]] = []
    current = [sorted_point_indices[start]]
    for step in range(m):
        k = (start + step) % m
        if close_to_next[k]:
            current.append(sorted_point_indices[(k + 1) % m])
        else:
            if len(current) > 1:
                groups.append(current)
            current = [sorted_point_indices[(k + 1) % m]]
    return groups


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
    elif size >= 5:
        # Spread a 5+ transit stellium symmetrically about its center, mirroring
        # the primary path (whose size>=5 branch uses spread 1.5). Secondary
        # spacing is tighter (2/3 of primary, matching the 2/3/4 ratios above),
        # so a 5+ outer stellium's degree labels no longer stack and overlap.
        spread = 1.0
        mid = (size - 1) / 2
        for i, idx in enumerate(group):
            adjustments[idx] = (i - mid) * spread


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

    # Build sorted (position, index) pairs (excluding filtered points). A list
    # of tuples is used instead of a {abs_pos: index} dict so points sharing
    # the exact same absolute position are all kept.
    # v6 safety net: bound to the shorter of the two lists so an upstream
    # mismatch (e.g. a return subject with fewer collected points than
    # active_points settings) can't trigger an IndexError. Callers are
    # expected to pass aligned lists; this guard is purely defensive.
    n = min(len(points_settings), len(points_abs_positions))
    sorted_point_indices = [
        index
        for _, index in sorted(
            (points_abs_positions[i], i)
            for i in range(n)
            if not (chart_type == "Transit" and points_settings[i]["name"] in exclude_points)
        )
    ]

    # Identify groups of close points (circular-aware: a run straddling the
    # list start is one group, not two overwriting each other).
    point_groups = _group_close_indicators(sorted_point_indices, points_abs_positions)

    # Apply secondary-specific adjustments (tighter spacing)
    for group in point_groups:
        _apply_secondary_group_adjustments(group, position_adjustments)

    return position_adjustments


def _calculate_text_rotation(
    first_house_degree: float,
    point_abs_position: float,
) -> tuple[float, str]:
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
    horoscope_id: Union[str, None] = None,
    glyph_id: Union[str, None] = None,
) -> str:
    """
    Generate SVG markup for a celestial point.

    Creates a group element containing the point symbol with proper
    positioning, scaling, and metadata attributes. If the point is
    retrograde, a small retrograde symbol (℞) is rendered next to the glyph.

    Args:
        point_details: Model containing point data.
        x: X-coordinate for the point.
        y: Y-coordinate for the point.
        scale: Scale factor for the symbol.
        point_name: Name used for the SVG symbol reference.

    Returns:
        SVG markup string for the celestial point.
    """
    is_retrograde = point_details["retrograde"] is True
    retro_attr = ' kr:retrograde="true"' if is_retrograde else ""
    horoscope_attr = f' kr:horoscope="{horoscope_id}"' if horoscope_id else ""
    gauq = getattr(point_details, "gauquelin_sector", None)
    gauq_attr = f' kr:gauquelinsector="{gauq}"' if gauq is not None else ""

    # kr:cx / kr:cy — the rendered glyph center, emitted so frontend hit-
    # detection can use an exact center without having to measure the symbol's
    # <use> (whose bbox depends on the referenced <symbol>, which has no
    # intrinsic viewBox). `x` and `y` passed into this function are the glyph
    # center in the FULL_WHEEL-LOCAL frame — the translate(-12*scale, -12*scale)
    # on the wrapping <g> cancels the half-offset that the symbol's own
    # coordinate system imposes. chart_drawer._rebase_glyph_centers then adds
    # each template's Full_Wheel translate so the final SVG carries true
    # root-space values.
    glyph_ref = glyph_id or (
        point_name if point_details.point_type == "House" else resolve_glyph_id(point_name)
    )
    parts: list[str] = [
        f'<g kr:node="ChartPoint" kr:house="{point_details["house"]}" ',
        f'kr:sign="{point_details["sign"]}" kr:absoluteposition="{point_details["abs_pos"]}" ',
        f'kr:signposition="{point_details["position"]}" kr:slug="{escape_svg_text(point_details["name"])}"{retro_attr}{horoscope_attr}{gauq_attr} ',
        f'kr:cx="{x}" kr:cy="{y}" ',
        f'transform="translate(-{12 * scale},-{12 * scale}) scale({scale})">',
        f'<use x="{x * (1 / scale)}" y="{y * (1 / scale)}" xlink:href="#{glyph_ref}" />',
    ]

    if is_retrograde:
        # Position the retrograde symbol at the bottom-right foot of the planet glyph.
        # Planet glyphs occupy ~24x24 units; x=+22 sits just past the right edge,
        # y=+18 aligns the symbol with the glyph's baseline (foot).
        retro_x = x * (1 / scale) + 22
        retro_y = y * (1 / scale) + 18
        parts.append(f'<g transform="translate({retro_x},{retro_y}) scale(0.55)">')
        parts.append('<use xlink:href="#retrograde" />')
        parts.append("</g>")

    parts.append("</g>")
    return "".join(parts)


def _draw_external_natal_lines(
    output: str,
    radius: Union[int, float],
    third_circle_radius: Union[int, float],
    point_radius: Union[int, float],
    true_offset: Union[int, float],
    adjusted_offset: Union[int, float],
    color: str,
    point_name: str = "",
    abs_pos: Optional[Union[int, float]] = None,
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
        point_name: Name of the celestial point (for kr:slug metadata).
        abs_pos: The owning ChartPoint's absolute position — the same float the
            ChartPoint tag interpolates, so kr:absoluteposition strings match.

    Returns:
        Updated SVG output with added lines.
    """
    # First line: from chart edge to intermediate position
    x1 = wheel_x(0, radius - third_circle_radius, true_offset) + third_circle_radius
    y1 = wheel_y(0, radius - third_circle_radius, true_offset) + third_circle_radius
    x2 = wheel_x(0, radius - point_radius - 30, true_offset) + point_radius + 30
    y2 = wheel_y(0, radius - point_radius - 30, true_offset) + point_radius + 30

    # Second line: from intermediate to final adjusted position
    x3 = wheel_x(0, radius - point_radius - 10, adjusted_offset) + point_radius + 10
    y3 = wheel_y(0, radius - point_radius - 10, adjusted_offset) + point_radius + 10

    pos_attr = f' kr:absoluteposition="{abs_pos}"' if abs_pos is not None else ""
    return (
        output
        + f'<g kr:node="ConnectingLine" kr:slug="{escape_svg_text(point_name)}"{pos_attr}>'
        + f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        + f'style="stroke-width:1px;stroke:{color};stroke-opacity:.3;"/>\n'
        + f'<line x1="{x2}" y1="{y2}" x2="{x3}" y2="{y3}" '
        + f'style="stroke-width:1px;stroke:{color};stroke-opacity:.5;"/>\n'
        + "</g>"
    )


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

    parts: list[str] = [output]

    # Bound by the shortest list, as every sibling helper does (see
    # _calculate_indicator_adjustments and _draw_secondary_points). A settings
    # list longer than the collected points would otherwise raise IndexError.
    n = min(len(points_settings), len(points_abs_positions), len(points_rel_positions))
    for point_idx in range(n):
        point_offset = zero_point + points_abs_positions[point_idx]
        if point_offset > 360:
            point_offset -= 360

        # Draw radial indicator line
        x1 = wheel_x(0, radius - first_circle_radius + 4, point_offset) + first_circle_radius - 4
        y1 = wheel_y(0, radius - first_circle_radius + 4, point_offset) + first_circle_radius - 4
        x2 = wheel_x(0, radius - first_circle_radius - 4, point_offset) + first_circle_radius + 4
        y2 = wheel_y(0, radius - first_circle_radius - 4, point_offset) + first_circle_radius + 4

        point_color = points_settings[point_idx]["color"]

        # Draw degree text (always horizontal for readability)
        adjusted_point_offset = point_offset + position_adjustments[point_idx]
        text_radius = first_circle_radius - 10.0

        deg_x = wheel_x(0, radius - text_radius, adjusted_point_offset) + text_radius
        deg_y = wheel_y(0, radius - text_radius, adjusted_point_offset) + text_radius

        degree_text = convert_decimal_to_degree_string(points_rel_positions[point_idx], format_type="1")
        point_slug = points_settings[point_idx]["name"]
        # kr:absoluteposition reuses the same float as the ChartPoint tag so the
        # two attribute strings are identical (focus code matches by string).
        parts.append(
            f'<g kr:node="Indicator" kr:slug="{escape_svg_text(point_slug)}" '
            f'kr:absoluteposition="{points_abs_positions[point_idx]}">'
            f'<line class="planet-degree-line" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'style="stroke: {point_color}; stroke-width: 1px; stroke-opacity:.8;"/>'
            f'<g transform="translate({deg_x},{deg_y})">'
            f'<text text-anchor="middle" dominant-baseline="middle" '
            f'style="fill: {point_color}; font-size: 10px;">{degree_text}</text></g>'
            "</g>"
        )

    return "".join(parts)


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
    parts: list[str] = [output]

    # Bound by the shortest list, as every sibling helper does (see
    # _calculate_indicator_adjustments and _draw_secondary_points). A settings
    # list longer than the collected points would otherwise raise IndexError.
    n = min(len(points_settings), len(points_abs_positions), len(points_rel_positions))
    for point_idx in range(n):
        point_offset = zero_point + points_abs_positions[point_idx]
        if point_offset > 360:
            point_offset -= 360

        # Draw radial line at inner boundary
        x1 = wheel_x(0, radius - NATAL_INDICATOR_OFFSET + 4, point_offset) + NATAL_INDICATOR_OFFSET - 4
        y1 = wheel_y(0, radius - NATAL_INDICATOR_OFFSET + 4, point_offset) + NATAL_INDICATOR_OFFSET - 4
        x2 = wheel_x(0, radius - NATAL_INDICATOR_OFFSET - 4, point_offset) + NATAL_INDICATOR_OFFSET + 4
        y2 = wheel_y(0, radius - NATAL_INDICATOR_OFFSET - 4, point_offset) + NATAL_INDICATOR_OFFSET + 4

        point_color = points_settings[point_idx]["color"]

        # Draw degree text (always horizontal, positioned toward center)
        adjusted_point_offset = point_offset + position_adjustments[point_idx]
        text_radius = NATAL_INDICATOR_OFFSET + 5.0

        deg_x = wheel_x(0, radius - text_radius, adjusted_point_offset) + text_radius
        deg_y = wheel_y(0, radius - text_radius, adjusted_point_offset) + text_radius

        degree_text = convert_decimal_to_degree_string(points_rel_positions[point_idx], format_type="1")
        point_slug = points_settings[point_idx]["name"]
        # Subject 1's ring in dual charts: kr:horoscope="0" + the same abs-pos
        # float as the ChartPoint tag (string-identical for focus matching).
        parts.append(
            f'<g kr:node="Indicator" kr:slug="{escape_svg_text(point_slug)}" '
            f'kr:absoluteposition="{points_abs_positions[point_idx]}" kr:horoscope="0">'
            f'<line class="planet-degree-line-inner" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'style="stroke: {point_color}; stroke-width: 1px; stroke-opacity:.8;"/>'
            f'<g transform="translate({deg_x},{deg_y})">'
            f'<text text-anchor="middle" dominant-baseline="middle" '
            f'style="fill: {point_color}; font-size: 8px;">{degree_text}</text></g>'
            "</g>"
        )

    return "".join(parts)


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
    celestial_points: Union[list[KerykeionPointModel], None] = None,
    show_degree_indicators: bool = True,
) -> str:
    """
    Draw secondary celestial points for transit/synastry charts.

    Renders the outer ring of planets (transit positions) with symbols,
    connecting lines, and degree indicators. If a point is retrograde,
    a small retrograde symbol (℞) is rendered next to the glyph.
    The glyphs are always rendered; ``show_degree_indicators`` only controls
    the tick lines and the degree labels next to them.

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
        celestial_points: Celestial point models (used for retrograde detection).

    Returns:
        Updated SVG output with secondary points.
    """
    # Calculate position adjustments using secondary-specific spacing values
    # This differs from _calculate_indicator_adjustments which uses wider spacing
    position_adjustments = _calculate_secondary_indicator_adjustments(
        points_abs_positions, points_settings, chart_type, exclude_points
    )

    # Build sorted (position, index) pairs (excluding houses for Transit).
    # A list of tuples is used instead of a {abs_pos: index} dict so points
    # sharing the exact same absolute position are all rendered.
    # Bound the scan to the shortest of the three parallel lists: every index
    # in sorted_point_indices is later used to look up all three, so an index
    # valid for points_settings but not for the positions lists would raise.
    n = min(len(points_settings), len(points_abs_positions), len(points_rel_positions))
    sorted_point_indices = [
        index
        for _, index in sorted(
            (points_abs_positions[i], i)
            for i in range(n)
            if not (chart_type == "Transit" and points_settings[i]["name"] in exclude_points)
        )
    ]

    zero_point = 360 - seventh_house_degree
    alternate_position = False

    # Draw each secondary point
    for point_idx in sorted_point_indices:
        if chart_type == "Transit" and points_settings[point_idx]["name"] in exclude_points:
            continue

        # Determine point radius (alternating for visual separation)
        is_chart_angle = points_settings[point_idx]["name"] in CHART_ANGLE_NAMES
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
        point_x = wheel_x(0, radius - point_radius, point_offset) + point_radius
        point_y = wheel_y(0, radius - point_radius, point_offset) + point_radius
        is_retrograde = (
            celestial_points is not None
            and point_idx < len(celestial_points)
            and celestial_points[point_idx].retrograde is True
        )
        retro_attr = ' kr:retrograde="true"' if is_retrograde else ""
        point_color = points_settings[point_idx]["color"]

        # Build point symbol with kr: metadata (matching _generate_point_svg attributes)
        point_name = points_settings[point_idx]["name"]
        # v6: dynamic points fall back to their shared generic symbols.
        point_glyph = points_settings[point_idx].get("glyph_id")
        if not point_glyph:
            point_details = (
                celestial_points[point_idx]
                if celestial_points is not None and point_idx < len(celestial_points)
                else None
            )
            point_glyph = (
                point_name
                if point_details is not None and point_details.point_type == "House"
                else resolve_glyph_id(point_name)
            )
        kr_attrs = f'kr:node="ChartPoint" kr:slug="{escape_svg_text(point_name)}" kr:horoscope="1"'
        if celestial_points is not None and point_idx < len(celestial_points):
            cp = celestial_points[point_idx]
            kr_attrs += f' kr:house="{cp.house}" kr:sign="{cp.sign}" kr:absoluteposition="{cp.abs_pos}" kr:signposition="{cp.position}"'
        # kr:cx / kr:cy — glyph center in the FULL_WHEEL-LOCAL frame, matching
        # _generate_point_svg. The outer translate(-6,-6) plus inner scale(0.5)
        # and pre-doubled use x/y place the symbol center exactly at
        # (point_x, point_y) in that frame; chart_drawer._rebase_glyph_centers
        # adds the template's Full_Wheel translate for true root-space values.
        kr_attrs += f' kr:cx="{point_x}" kr:cy="{point_y}"'
        point_svg = (
            f'<g {kr_attrs}{retro_attr} class="transit-planet-name" transform="translate(-6,-6)"><g transform="scale(0.5)">'
            f'<use x="{point_x * 2}" y="{point_y * 2}" xlink:href="#{point_glyph}" />'
        )
        if is_retrograde:
            # Same offset logic as _generate_point_svg: bottom-right foot of the glyph.
            # Inner coordinate space is 2x due to scale(0.5) wrapper.
            retro_x = point_x * 2 + 22
            retro_y = point_y * 2 + 18
            point_svg += (
                f'<g transform="translate({retro_x},{retro_y}) scale(0.55)"><use xlink:href="#retrograde" /></g>'
            )
        point_svg += "</g></g>"

        output += point_svg

        if show_degree_indicators:
            # Draw indicator line
            x1 = wheel_x(0, radius + 3, point_offset) - 3
            y1 = wheel_y(0, radius + 3, point_offset) - 3
            x2 = wheel_x(0, radius - 3, point_offset) + 3
            y2 = wheel_y(0, radius - 3, point_offset) + 3

            # Draw degree text (always horizontal for readability)
            adjusted_point_offset = point_offset + position_adjustments[point_idx]
            text_radius = -9.0

            deg_x = wheel_x(0, radius - text_radius, adjusted_point_offset) + text_radius
            deg_y = wheel_y(0, radius - text_radius, adjusted_point_offset) + text_radius

            degree_text = convert_decimal_to_degree_string(points_rel_positions[point_idx], format_type="1")
            # Wrap tick + degree text in an Indicator node (kr:absoluteposition is
            # the same float as the ChartPoint tag, so the strings are identical
            # and downstream focus code can tie this tick to the outer ring).
            output += (
                f'<g kr:node="Indicator" kr:slug="{escape_svg_text(point_name)}" '
                + f'kr:absoluteposition="{points_abs_positions[point_idx]}" kr:horoscope="1">'
                + f'<line class="transit-planet-line" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                + f'style="stroke: {point_color}; stroke-width: 1px; stroke-opacity:.8;"/>'
                + f'<g transform="translate({deg_x},{deg_y})">'
                + '<text text-anchor="middle" dominant-baseline="middle" '
                + f'style="fill: {point_color}; font-size: 10px;">{degree_text}</text></g>'
                + "</g>"
            )

    return output
