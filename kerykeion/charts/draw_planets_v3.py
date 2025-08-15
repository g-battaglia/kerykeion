"""
TODO: Not stable at all, check it very well before using it!
"""

from dataclasses import dataclass
from enum import Enum
from typing import Union, Optional, List, Dict, Tuple, get_args
import logging

from kerykeion.charts.charts_utils import degreeDiff, sliceToX, sliceToY, convert_decimal_to_degree_string
from kerykeion.kr_types import KerykeionException, ChartType, KerykeionPointModel
from kerykeion.kr_types.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.kr_types.kr_literals import Houses


class ChartRadius(Enum):
    """Standard radius values for different chart elements."""
    ANGLE_TRANSIT = 76
    ANGLE_NATAL = 40
    ANGLE_EXTERNAL_NATAL = 30
    PLANET_PRIMARY = 94
    PLANET_ALTERNATE = 74
    PLANET_TRANSIT_PRIMARY = 130
    PLANET_TRANSIT_ALTERNATE = 110
    PLANET_EXTERNAL_PRIMARY = 84
    PLANET_EXTERNAL_ALTERNATE = 64


class ChartConstants:
    """Configuration constants for chart drawing."""
    PLANET_GROUPING_THRESHOLD = 3.4
    SECONDARY_GROUPING_THRESHOLD = 2.5
    ANGLE_INDEX_RANGE = (22, 27)  # ASC, MC, DSC, IC indices
    SYMBOL_SCALE_FACTOR = 0.8
    SYMBOL_SIZE = 12
    MAX_DEGREE_DISTANCE = 360.0

    # Line styling
    LINE_OPACITY_PRIMARY = 0.3
    LINE_OPACITY_SECONDARY = 0.5
    LINE_WIDTH_THIN = 1
    LINE_WIDTH_THICK = 2

    # Text styling
    TEXT_SIZE = 10


@dataclass
class PointPosition:
    """Represents a celestial point's position and distance information."""
    index: int
    position_index: int
    distance_to_prev: float
    distance_to_next: float
    label: str


@dataclass
class ChartConfiguration:
    """Configuration for chart drawing parameters."""
    radius: float
    third_circle_radius: float
    first_house_degree: float
    seventh_house_degree: float
    chart_type: ChartType
    scale_factor: float = 1.0

    def __post_init__(self):
        """Set scale factor based on chart type."""
        if self.chart_type in ["Transit", "Synastry", "Return", "ExternalNatal"]:
            self.scale_factor = ChartConstants.SYMBOL_SCALE_FACTOR


class CelestialPointGrouper:
    """Handles grouping of celestial points that are close together."""

    def __init__(self, threshold: float = ChartConstants.PLANET_GROUPING_THRESHOLD):
        """
        Initialize the celestial point grouper.
        
        Args:
            threshold: Distance threshold below which points are considered grouped together.
        """
        self.threshold = threshold

    def create_position_mapping(
        self,
        celestial_points: List[KerykeionPointModel],
        settings: List[KerykeionSettingsCelestialPointModel]
    ) -> Tuple[Dict[float, int], List[float]]:
        """Create mapping from absolute positions to point indices."""
        position_index_map = {}
        for i, point in enumerate(celestial_points):
            position_index_map[point.abs_pos] = i
            logging.debug(f"Point {settings[i]['label']}: index {i}, degree {point.abs_pos}")

        return position_index_map, sorted(position_index_map.keys())

    def calculate_distances(
        self,
        sorted_positions: List[float],
        position_index_map: Dict[float, int],
        abs_positions: List[float]
    ) -> List[PointPosition]:
        """Calculate distances between adjacent points."""
        point_positions = []

        for position_idx, abs_position in enumerate(sorted_positions):
            point_idx = position_index_map[abs_position]

            if len(sorted_positions) == 1:
                # Single point case
                distance_to_prev = distance_to_next = ChartConstants.MAX_DEGREE_DISTANCE
            else:
                prev_idx, next_idx = self._get_adjacent_indices(
                    position_idx, sorted_positions, position_index_map
                )
                distance_to_prev = degreeDiff(abs_positions[prev_idx], abs_positions[point_idx])
                distance_to_next = degreeDiff(abs_positions[next_idx], abs_positions[point_idx])

            point_positions.append(PointPosition(
                index=point_idx,
                position_index=position_idx,
                distance_to_prev=distance_to_prev,
                distance_to_next=distance_to_next,
                label=f"point_{point_idx}"  # Will be updated by caller
            ))

        return point_positions

    def _get_adjacent_indices(
        self,
        position_idx: int,
        sorted_positions: List[float],
        position_index_map: Dict[float, int]
    ) -> Tuple[int, int]:
        """Get indices of previous and next points."""
        total_positions = len(sorted_positions)

        if position_idx == 0:
            prev_position = sorted_positions[-1]
            next_position = sorted_positions[1]
        elif position_idx == total_positions - 1:
            prev_position = sorted_positions[position_idx - 1]
            next_position = sorted_positions[0]
        else:
            prev_position = sorted_positions[position_idx - 1]
            next_position = sorted_positions[position_idx + 1]

        return position_index_map[prev_position], position_index_map[next_position]

    def identify_groups(self, point_positions: List[PointPosition]) -> List[List[PointPosition]]:
        """Identify groups of points that are close together."""
        groups = []
        current_group = []

        for point_pos in point_positions:
            if point_pos.distance_to_next < self.threshold:
                current_group.append(point_pos)
            else:
                if current_group:
                    current_group.append(point_pos)
                    groups.append(current_group)
                    current_group = []

        # Handle case where last group wraps around
        if current_group and groups and point_positions[0] in groups[0]:
            groups[0] = current_group + groups[0]
        elif current_group:
            groups.append(current_group)

        return groups


class PositionAdjuster:
    """Calculates position adjustments to prevent overlapping points."""

    def __init__(self, threshold: float = ChartConstants.PLANET_GROUPING_THRESHOLD):
        """
        Initialize the position adjuster.
        
        Args:
            threshold: Distance threshold for grouping adjustment calculations.
        """
        self.threshold = threshold

    def calculate_adjustments(
        self,
        groups: List[List[PointPosition]],
        total_points: int
    ) -> List[float]:
        """Calculate position adjustments for all points."""
        adjustments = [0.0] * total_points

        for group in groups:
            if len(group) == 2:
                self._handle_two_point_group(group, adjustments)
            elif len(group) >= 3:
                self._handle_multi_point_group(group, adjustments)

        return adjustments

    def _handle_two_point_group(
        self,
        group: List[PointPosition],
        adjustments: List[float]
    ) -> None:
        """Handle positioning for a group of two points."""
        point_a, point_b = group[0], group[1]

        # Check available space around the group
        if (point_a.distance_to_prev > 2 * self.threshold and
            point_b.distance_to_next > 2 * self.threshold):
            # Both points have room
            offset = (self.threshold - point_a.distance_to_next) / 2
            adjustments[point_a.position_index] = -offset
            adjustments[point_b.position_index] = +offset
        elif point_a.distance_to_prev > 2 * self.threshold:
            # Only first point has room
            adjustments[point_a.position_index] = -self.threshold
        elif point_b.distance_to_next > 2 * self.threshold:
            # Only second point has room
            adjustments[point_b.position_index] = +self.threshold

    def _handle_multi_point_group(
        self,
        group: List[PointPosition],
        adjustments: List[float]
    ) -> None:
        """Handle positioning for groups of three or more points."""
        group_size = len(group)

        # Calculate available and needed space
        available_space = group[0].distance_to_prev
        for point in group:
            available_space += point.distance_to_next

        needed_space = 3 * self.threshold + 1.2 * (group_size - 1) * self.threshold

        if available_space > needed_space:
            # Distribute points evenly
            spacing = 1.2 * self.threshold
            start_offset = (available_space - needed_space) / 2

            for i, point in enumerate(group):
                adjustments[point.position_index] = start_offset + i * spacing - group[0].distance_to_prev


class RadiusCalculator:
    """Calculates appropriate radius for different point types and chart types."""

    @staticmethod
    def get_point_radius(
        point_idx: int,
        chart_type: ChartType,
        is_alternate: bool = False
    ) -> int:
        """Get radius for a celestial point based on its type and chart context."""
        is_angle = ChartConstants.ANGLE_INDEX_RANGE[0] < point_idx < ChartConstants.ANGLE_INDEX_RANGE[1]

        if chart_type in ["Transit", "Synastry", "Return"]:
            if is_angle:
                return ChartRadius.ANGLE_TRANSIT.value
            return (ChartRadius.PLANET_TRANSIT_ALTERNATE.value if is_alternate
                   else ChartRadius.PLANET_TRANSIT_PRIMARY.value)

        elif chart_type == "ExternalNatal":
            if is_angle:
                return ChartRadius.ANGLE_EXTERNAL_NATAL.value
            return (ChartRadius.PLANET_EXTERNAL_ALTERNATE.value if is_alternate
                   else ChartRadius.PLANET_EXTERNAL_PRIMARY.value)

        else:  # Natal chart
            if is_angle:
                return ChartRadius.ANGLE_NATAL.value
            return (ChartRadius.PLANET_ALTERNATE.value if is_alternate
                   else ChartRadius.PLANET_PRIMARY.value)


class SVGRenderer:
    """Handles SVG generation for celestial points."""

    def __init__(self, config: ChartConfiguration):
        """
        Initialize the SVG renderer with chart configuration.
        
        Args:
            config: Chart configuration containing radius, scale factors, and chart type.
        """
        self.config = config

    def calculate_offset(self, point_degree: float, adjustment: float = 0) -> float:
        """Calculate the angular offset for positioning a point."""
        return (-self.config.seventh_house_degree) + point_degree + adjustment

    def generate_point_svg(
        self,
        point: KerykeionPointModel,
        x: float,
        y: float,
        point_name: str
    ) -> str:
        """Generate SVG element for a celestial point."""
        scale = self.config.scale_factor
        transform_offset = ChartConstants.SYMBOL_SIZE * scale

        svg_parts = [
            f'<g kr:node="ChartPoint" kr:house="{point.house}" kr:sign="{point.sign}" ',
            f'kr:slug="{point.name}" transform="translate(-{transform_offset},-{transform_offset}) scale({scale})">',
            f'<use x="{x / scale}" y="{y / scale}" xlink:href="#{point_name}" />',
            '</g>'
        ]

        return ''.join(svg_parts)

    def draw_external_natal_lines(
        self,
        point_radius: float,
        true_offset: float,
        adjusted_offset: float,
        color: str
    ) -> str:
        """Draw connecting lines for ExternalNatal chart type."""
        lines = []

        # First line segment
        x1 = sliceToX(0, self.config.radius - self.config.third_circle_radius, true_offset) + self.config.third_circle_radius
        y1 = sliceToY(0, self.config.radius - self.config.third_circle_radius, true_offset) + self.config.third_circle_radius
        x2 = sliceToX(0, self.config.radius - point_radius - 30, true_offset) + point_radius + 30
        y2 = sliceToY(0, self.config.radius - point_radius - 30, true_offset) + point_radius + 30

        lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                    f'style="stroke-width:{ChartConstants.LINE_WIDTH_THIN}px;stroke:{color};'
                    f'stroke-opacity:{ChartConstants.LINE_OPACITY_PRIMARY};"/>')

        # Second line segment
        x3 = sliceToX(0, self.config.radius - point_radius - 10, adjusted_offset) + point_radius + 10
        y3 = sliceToY(0, self.config.radius - point_radius - 10, adjusted_offset) + point_radius + 10

        lines.append(f'<line x1="{x2}" y1="{y2}" x2="{x3}" y2="{y3}" '
                    f'style="stroke-width:{ChartConstants.LINE_WIDTH_THIN}px;stroke:{color};'
                    f'stroke-opacity:{ChartConstants.LINE_OPACITY_SECONDARY};"/>')

        return '\n'.join(lines) + '\n'


class SecondaryPointsRenderer:
    """Handles rendering of secondary points (transit, synastry, return)."""

    def __init__(self, config: ChartConfiguration):
        """
        Initialize the secondary points renderer.
        
        Args:
            config: Chart configuration for rendering parameters.
        """
        self.config = config
        self.grouper = CelestialPointGrouper(ChartConstants.SECONDARY_GROUPING_THRESHOLD)

    def draw_secondary_points(
        self,
        points_abs_positions: List[float],
        points_rel_positions: List[float],
        points_settings: List[KerykeionSettingsCelestialPointModel],
        exclude_points: List[str]
    ) -> str:
        """Draw all secondary celestial points."""
        if not points_abs_positions:
            return ""

        # Filter out excluded points
        filtered_indices = [
            i for i, setting in enumerate(points_settings)
            if self.config.chart_type != "Transit" or setting["name"] not in exclude_points
        ]

        if not filtered_indices:
            return ""

        # Calculate position adjustments for grouping
        adjustments = self._calculate_secondary_adjustments(
            filtered_indices, points_abs_positions, points_settings
        )

        # Render each secondary point
        output_parts = []
        alternate_position = False

        for idx in filtered_indices:
            point_svg = self._render_single_secondary_point(
                idx, points_abs_positions, points_rel_positions,
                points_settings, adjustments, alternate_position
            )
            output_parts.append(point_svg)
            alternate_position = not alternate_position

        return ''.join(output_parts)

    def _calculate_secondary_adjustments(
        self,
        indices: List[int],
        positions: List[float],
        settings: List[KerykeionSettingsCelestialPointModel]
    ) -> Dict[int, float]:
        """Calculate position adjustments for secondary points."""
        # Create position mapping for filtered indices
        position_map = {positions[i]: i for i in indices}
        sorted_positions = sorted(position_map.keys())

        # Find groups
        groups = []
        current_group = []

        for i, pos in enumerate(sorted_positions):
            point_idx = position_map[pos]
            next_pos = sorted_positions[(i + 1) % len(sorted_positions)]
            next_idx = position_map[next_pos]

            distance = degreeDiff(positions[point_idx], positions[next_idx])

            if distance <= self.grouper.threshold:
                if not current_group:
                    current_group = [point_idx]
                current_group.append(next_idx)
            else:
                if current_group:
                    groups.append(current_group)
                    current_group = []

        if current_group:
            groups.append(current_group)

        # Calculate adjustments
        adjustments = {i: 0.0 for i in indices}

        for group in groups:
            if len(group) == 2:
                adjustments[group[0]] = -1.0
                adjustments[group[1]] = 1.0
            elif len(group) == 3:
                adjustments[group[0]] = -1.5
                adjustments[group[1]] = 0.0
                adjustments[group[2]] = 1.5
            elif len(group) >= 4:
                for j, point_idx in enumerate(group):
                    adjustments[point_idx] = -2.0 + j * (4.0 / (len(group) - 1))

        return adjustments

    def _render_single_secondary_point(
        self,
        point_idx: int,
        abs_positions: List[float],
        rel_positions: List[float],
        settings: List[KerykeionSettingsCelestialPointModel],
        adjustments: Dict[int, float],
        is_alternate: bool
    ) -> str:
        """Render a single secondary point with symbol, line, and degree text."""
        # Determine radius
        is_angle = ChartConstants.ANGLE_INDEX_RANGE[0] < point_idx < ChartConstants.ANGLE_INDEX_RANGE[1]
        point_radius = 9 if is_angle else (18 if is_alternate else 26)

        # Calculate position
        point_offset = self._calculate_secondary_offset(abs_positions[point_idx])

        # Generate SVG components
        symbol_svg = self._generate_secondary_symbol(point_idx, point_radius, point_offset, settings)
        line_svg = self._generate_secondary_line(point_idx, point_offset, settings)
        text_svg = self._generate_secondary_text(
            point_idx, abs_positions, rel_positions, settings, adjustments, point_offset
        )

        return symbol_svg + line_svg + text_svg

    def _calculate_secondary_offset(self, abs_position: float) -> float:
        """Calculate offset for secondary point positioning."""
        zero_point = 360 - self.config.seventh_house_degree
        offset = zero_point + abs_position
        return offset - 360 if offset > 360 else offset

    def _generate_secondary_symbol(
        self, point_idx: int, radius: int, offset: float,
        settings: List[KerykeionSettingsCelestialPointModel]
    ) -> str:
        """Generate SVG for secondary point symbol."""
        x = sliceToX(0, self.config.radius - radius, offset) + radius
        y = sliceToY(0, self.config.radius - radius, offset) + radius

        return (f'<g class="transit-planet-name" transform="translate(-6,-6)">'
                f'<g transform="scale(0.5)">'
                f'<use x="{x*2}" y="{y*2}" xlink:href="#{settings[point_idx]["name"]}" />'
                f'</g></g>')

    def _generate_secondary_line(
        self, point_idx: int, offset: float,
        settings: List[KerykeionSettingsCelestialPointModel]
    ) -> str:
        """Generate connecting line for secondary point."""
        x1 = sliceToX(0, self.config.radius + 3, offset) - 3
        y1 = sliceToY(0, self.config.radius + 3, offset) - 3
        x2 = sliceToX(0, self.config.radius - 3, offset) + 3
        y2 = sliceToY(0, self.config.radius - 3, offset) + 3

        color = settings[point_idx]["color"]
        return (f'<line class="transit-planet-line" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                f'style="stroke: {color}; stroke-width: {ChartConstants.LINE_WIDTH_THIN}px; '
                f'stroke-opacity:.8;"/>')

    def _generate_secondary_text(
        self,
        point_idx: int,
        abs_positions: List[float],
        rel_positions: List[float],
        settings: List[KerykeionSettingsCelestialPointModel],
        adjustments: Dict[int, float],
        point_offset: float
    ) -> str:
        """Generate degree text for secondary point."""
        # Calculate rotation and text anchor
        rotation = self.config.first_house_degree - abs_positions[point_idx]
        text_anchor = "end"

        # Adjust for readability
        if -270 < rotation < -90:
            rotation += 180.0
            text_anchor = "start"
        elif 90 < rotation < 270:
            rotation -= 180.0
            text_anchor = "start"

        # Position text
        x_offset = 1 if text_anchor == "end" else -1
        adjusted_offset = point_offset + adjustments[point_idx]
        text_radius = -3.0

        deg_x = sliceToX(0, self.config.radius - text_radius, adjusted_offset + x_offset) + text_radius
        deg_y = sliceToY(0, self.config.radius - text_radius, adjusted_offset + x_offset) + text_radius

        # Format degree text
        degree_text = convert_decimal_to_degree_string(rel_positions[point_idx], format_type="1")
        color = settings[point_idx]["color"]

        return (f'<g transform="translate({deg_x},{deg_y})">'
                f'<text transform="rotate({rotation})" text-anchor="{text_anchor}" '
                f'style="fill: {color}; font-size: {ChartConstants.TEXT_SIZE}px;">{degree_text}</text>'
                f'</g>')


def _validate_chart_inputs(
    chart_type: ChartType,
    secondary_points: Optional[List[KerykeionPointModel]]
) -> None:
    """Validate that required secondary points are provided for chart types that need them."""
    if _requires_secondary_points(chart_type) and secondary_points is None:
        raise KerykeionException(f"Secondary celestial points are required for {chart_type} charts")


def _requires_secondary_points(chart_type: ChartType) -> bool:
    """Check if chart type requires secondary celestial points."""
    return chart_type in ["Transit", "Synastry", "Return"]


def _draw_main_points(
    celestial_points: List[KerykeionPointModel],
    settings: List[KerykeionSettingsCelestialPointModel],
    config: ChartConfiguration,
    grouper: CelestialPointGrouper,
    adjuster: PositionAdjuster,
    renderer: SVGRenderer
) -> str:
    """Draw the main celestial points with proper grouping and positioning."""
    # Create position mapping and calculate distances
    position_map, sorted_positions = grouper.create_position_mapping(celestial_points, settings)
    abs_positions = [p.abs_pos for p in celestial_points]

    point_positions = grouper.calculate_distances(sorted_positions, position_map, abs_positions)

    # Update labels
    for point_pos in point_positions:
        point_pos.label = settings[point_pos.index]["label"]

    # Identify groups and calculate adjustments
    groups = grouper.identify_groups(point_positions)
    adjustments = adjuster.calculate_adjustments(groups, len(settings))

    # Draw each point
    output_parts = []

    for position_idx, abs_position in enumerate(sorted_positions):
        point_idx = position_map[abs_position]

        # Calculate positioning
        point_radius = RadiusCalculator.get_point_radius(
            point_idx, config.chart_type, bool(position_idx % 2)
        )

        adjusted_offset = renderer.calculate_offset(
            abs_positions[point_idx], adjustments[position_idx]
        )

        # Calculate coordinates
        point_x = sliceToX(0, config.radius - point_radius, adjusted_offset) + point_radius
        point_y = sliceToY(0, config.radius - point_radius, adjusted_offset) + point_radius

        # Draw external natal lines if needed
        if config.chart_type == "ExternalNatal":
            true_offset = renderer.calculate_offset(abs_positions[point_idx])
            line_svg = renderer.draw_external_natal_lines(
                point_radius, true_offset, adjusted_offset, settings[point_idx]["color"]
            )
            output_parts.append(line_svg)

        # Generate point SVG
        point_svg = renderer.generate_point_svg(
            celestial_points[point_idx], point_x, point_y, settings[point_idx]["name"]
        )
        output_parts.append(point_svg)

    return ''.join(output_parts)


def draw_planets_v2(
    radius: Union[int, float],
    available_kerykeion_celestial_points: List[KerykeionPointModel],
    available_planets_setting: List[KerykeionSettingsCelestialPointModel],
    third_circle_radius: Union[int, float],
    main_subject_first_house_degree_ut: Union[int, float],
    main_subject_seventh_house_degree_ut: Union[int, float],
    chart_type: ChartType,
    second_subject_available_kerykeion_celestial_points: Optional[List[KerykeionPointModel]] = None,
) -> str:
    """
    Draw celestial points on an astrological chart.

    This is the main entry point for drawing planets and other celestial points
    on astrological charts. It handles positioning, grouping, and overlap resolution.

    Args:
        radius: Chart radius in pixels
        available_kerykeion_celestial_points: Main subject's celestial points
        available_planets_setting: Settings for celestial points
        third_circle_radius: Radius of the third circle
        main_subject_first_house_degree_ut: First house degree
        main_subject_seventh_house_degree_ut: Seventh house degree
        chart_type: Type of chart being drawn
        second_subject_available_kerykeion_celestial_points: Secondary subject's points

    Returns:
        SVG string for the celestial points

    Raises:
        KerykeionException: If secondary points are required but not provided
    """
    # Validate inputs
    _validate_chart_inputs(chart_type, second_subject_available_kerykeion_celestial_points)

    # Create configuration
    config = ChartConfiguration(
        radius=float(radius),
        third_circle_radius=float(third_circle_radius),
        first_house_degree=float(main_subject_first_house_degree_ut),
        seventh_house_degree=float(main_subject_seventh_house_degree_ut),
        chart_type=chart_type
    )

    # Initialize components
    grouper = CelestialPointGrouper()
    adjuster = PositionAdjuster()
    renderer = SVGRenderer(config)

    # Process main celestial points
    output_parts = []

    if available_kerykeion_celestial_points:
        main_svg = _draw_main_points(
            available_kerykeion_celestial_points,
            available_planets_setting,
            config,
            grouper,
            adjuster,
            renderer
        )
        output_parts.append(main_svg)

    # Process secondary points if needed
    if _requires_secondary_points(chart_type) and second_subject_available_kerykeion_celestial_points:
        secondary_renderer = SecondaryPointsRenderer(config)

        secondary_abs_positions = [p.abs_pos for p in second_subject_available_kerykeion_celestial_points]
        secondary_rel_positions = [p.position for p in second_subject_available_kerykeion_celestial_points]
        exclude_points = list(get_args(Houses)) if chart_type == "Transit" else []

        secondary_svg = secondary_renderer.draw_secondary_points(
            secondary_abs_positions,
            secondary_rel_positions,
            available_planets_setting,
            exclude_points
        )
        output_parts.append(secondary_svg)

    return ''.join(output_parts)

