# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import logging
from copy import deepcopy
from math import ceil
from datetime import datetime
from pathlib import Path
from string import Template
from typing import Any, Mapping, Optional, Sequence, Union, get_args

import swisseph as swe
from scour.scour import scourString

from kerykeion.house_comparison.house_comparison_factory import HouseComparisonFactory
from kerykeion.schemas import (
    KerykeionException,
    ChartType,
    Sign,
    ActiveAspect,
    KerykeionPointModel,
)
from kerykeion.schemas import ChartTemplateModel
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    PlanetReturnModel,
)
from kerykeion.schemas.settings_models import (
    KerykeionLanguageModel,
)
from kerykeion.schemas.kr_literals import (
    KerykeionChartTheme,
    KerykeionChartLanguage,
    AstrologicalPoint,
)
from kerykeion.schemas.kr_models import ChartDataModel
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS
from kerykeion.settings.translations import get_translations, load_language_settings
from kerykeion.charts.charts_utils import (
    draw_zodiac_slice,
    convert_latitude_coordinate_to_string,
    convert_longitude_coordinate_to_string,
    draw_aspect_line,
    draw_transit_ring_degree_steps,
    draw_degree_ring,
    draw_transit_ring,
    draw_background_circle,
    draw_first_circle,
    draw_house_comparison_grid,
    draw_second_circle,
    draw_third_circle,
    draw_aspect_grid,
    draw_houses_cusps_and_text_number,
    draw_transit_aspect_list,
    draw_transit_aspect_grid,
    draw_single_house_comparison_grid,
    draw_cusp_comparison_grid,
    draw_single_cusp_comparison_grid,
    makeLunarPhase,
    draw_main_house_grid,
    draw_secondary_house_grid,
    draw_main_planet_grid,
    draw_secondary_planet_grid,
    format_location_string,
    format_datetime_with_timezone,
)
from kerykeion.charts.draw_planets import draw_planets
from kerykeion.utilities import get_houses_list, inline_css_variables_in_svg, distribute_percentages_to_100
from kerykeion.settings.chart_defaults import (
    DEFAULT_CHART_COLORS,
    DEFAULT_CELESTIAL_POINTS_SETTINGS,
    DEFAULT_CHART_ASPECTS_SETTINGS,
    _CelestialPointSetting,
    _ChartAspectSetting,
)
from typing import List, Literal
from dataclasses import dataclass


logger = logging.getLogger(__name__)


# =============================================================================
# TYPE ALIASES
# =============================================================================
# These type aliases improve code readability by providing semantic meaning
# to complex Union types used throughout the ChartDrawer class.
# =============================================================================

# Type for subjects that can be the primary (first) subject in any chart type.
# - AstrologicalSubjectModel: Standard birth chart subject
# - CompositeSubjectModel: Midpoint composite of two subjects
# - PlanetReturnModel: Solar/Lunar return chart subject
FirstSubjectType = Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel]

# Type for subjects that can be the secondary (second) subject in dual-wheel charts.
# Used in Transit, Synastry, and DualReturnChart types.
# - AstrologicalSubjectModel: For Transit and Synastry charts
# - PlanetReturnModel: For DualReturnChart (Solar/Lunar returns)
SecondSubjectType = Union[AstrologicalSubjectModel, PlanetReturnModel, None]


# =============================================================================
# CONFIGURATION DATACLASSES
# =============================================================================
# These dataclasses encapsulate configuration values that were previously
# scattered as class constants. They provide:
# - Type safety and IDE autocompletion
# - Immutability (frozen=True) where appropriate
# - Clear documentation of related configuration groups
# =============================================================================


@dataclass(frozen=True)
class ChartDimensionsConfig:
    """
    Immutable configuration for SVG canvas dimensions.

    These dimensions define the default width and height for different chart types.
    Width varies based on the number of grids and elements displayed alongside
    the main wheel.

    Attributes:
        default_height: Standard height for all chart types (550px)
        natal_width: Single-wheel charts (Natal, Composite, SingleReturn)
        full_width: Dual-wheel charts with aspect list
        full_width_with_table: Dual-wheel charts with aspect table grid
        synastry_width: Synastry with house comparison grids
        ultra_wide_width: DualReturnChart with extended grids
    """

    default_height: int = 550
    natal_width: int = 870
    full_width: int = 1250
    full_width_with_table: int = 1250
    synastry_width: int = 1570
    ultra_wide_width: int = 1320


@dataclass(frozen=True)
class CircleRadiiConfig:
    """
    Immutable configuration for concentric circle radii.

    The astrological wheel is composed of concentric circles:
    - main_radius: Distance from center to outermost wheel edge
    - first_circle: Outer boundary (0 for internal view, >0 for external)
    - second_circle: Zodiac sign ring boundary
    - third_circle: Inner boundary for aspect lines

    Two layouts are supported:
    1. Internal view (default): Planets drawn inside the zodiac ring
    2. External view: Planets drawn outside the zodiac ring (Natal only)

    Attributes:
        main_radius: Main wheel radius (240px from center)
        single_wheel_first: First circle for internal/single-wheel layout
        single_wheel_second: Second circle for internal/single-wheel layout
        single_wheel_third: Third circle for internal/single-wheel layout
        external_view_first: First circle for external view layout
        external_view_second: Second circle for external view layout
        external_view_third: Third circle for external view layout
    """

    main_radius: int = 240
    # Single-wheel and dual-wheel internal layout (planets inside zodiac ring)
    single_wheel_first: int = 0
    single_wheel_second: int = 36
    single_wheel_third: int = 120
    # External view layout (planets outside zodiac ring, Natal only)
    external_view_first: int = 56
    external_view_second: int = 92
    external_view_third: int = 112


@dataclass
class VerticalOffsetsConfig:
    """
    Mutable configuration for vertical positioning of chart elements.

    These offsets control the Y-translation of different SVG groups within
    the chart. They are adjusted dynamically based on the number of active
    celestial points to prevent content overflow.

    The chart layout has two anchor strategies:
    1. Bottom-anchored elements (wheel, aspect_grid, lunar_phase): Stay pinned
       to the bottom of the SVG canvas.
    2. Top elements (title, elements, qualities): Shift partially to maintain
       visual balance.

    Attributes:
        wheel: Vertical offset for the main wheel group
        grid: Vertical offset for planet/house data grids
        aspect_grid: Vertical offset for aspect grid (table mode)
        aspect_list: Vertical offset for aspect list (list mode)
        title: Vertical offset for chart title
        elements: Vertical offset for element percentages display
        qualities: Vertical offset for quality percentages display
        lunar_phase: Vertical offset for lunar phase icon
        bottom_left: Vertical offset for bottom-left info section
    """

    wheel: float = 50.0
    grid: float = 0.0
    aspect_grid: float = 50.0
    aspect_list: float = 50.0
    title: float = 0.0
    elements: float = 0.0
    qualities: float = 0.0
    lunar_phase: float = 518.0
    bottom_left: float = 0.0

    def shift_bottom_anchored_elements(self, delta: float) -> None:
        """
        Shift all bottom-anchored elements by the specified delta.

        This method is used when the chart height increases due to additional
        active celestial points. Bottom-anchored elements need to move down
        by the full height increase to stay "pinned" to the SVG bottom.

        Args:
            delta: The number of pixels to shift elements down.
        """
        self.wheel += delta
        self.aspect_grid += delta
        self.aspect_list += delta
        self.lunar_phase += delta
        self.bottom_left += delta

    def shift_top_elements(self, shift: float) -> None:
        """
        Shift top elements (title, elements, qualities) by the specified amount.

        Top elements receive a partial shift to maintain visual balance when
        the chart height increases. This prevents excessive spacing while
        keeping content readable.

        Args:
            shift: The number of pixels to shift elements down.
        """
        top_shift = shift / 2  # Title shifts less than grids
        self.grid += shift
        self.title += top_shift
        self.elements += top_shift
        self.qualities += top_shift

    def to_dict(self) -> dict[str, float]:
        """
        Convert offsets to a dictionary for template substitution.

        Returns:
            Dictionary mapping offset names to their float values.
        """
        return {
            "wheel": self.wheel,
            "grid": self.grid,
            "aspect_grid": self.aspect_grid,
            "aspect_list": self.aspect_list,
            "title": self.title,
            "elements": self.elements,
            "qualities": self.qualities,
            "lunar_phase": self.lunar_phase,
            "bottom_left": self.bottom_left,
        }


@dataclass(frozen=True)
class GridPositionsConfig:
    """
    Immutable configuration for horizontal grid positions.

    These X-coordinates define where each data grid starts on the SVG canvas.
    Grids are positioned right of the main wheel, with secondary grids
    (for dual-wheel charts) placed further right.

    Attributes:
        main_planet_x: X position for primary subject planets table
        main_houses_x: X position for primary subject houses table
        secondary_planet_x: X position for secondary subject planets table
        secondary_houses_x: X position for secondary subject houses table
        house_comparison_first_x: First comparison grid (Synastry/DualReturn)
        house_comparison_second_x: Second comparison grid (Synastry/DualReturn)
        transit_house_comparison_x: Transit house comparison position
        transit_aspect_grid_x: Aspect grid X position (table mode)
        transit_aspect_grid_y: Aspect grid Y position (table mode)
    """

    main_planet_x: int = 645
    main_houses_x: int = 750
    secondary_planet_x: int = 910
    secondary_houses_x: int = 1015
    house_comparison_first_x: int = 1090
    house_comparison_second_x: int = 1290
    transit_house_comparison_x: int = 980
    transit_aspect_grid_x: int = 550
    transit_aspect_grid_y: int = 450


# Default configuration instances
# These are used as fallback values and can be overridden per-instance
DEFAULT_DIMENSIONS = ChartDimensionsConfig()
DEFAULT_RADII = CircleRadiiConfig()
DEFAULT_GRID_POSITIONS = GridPositionsConfig()


# =============================================================================
# CHART RENDERER PROTOCOL AND BASE CLASS
# =============================================================================
# The Strategy Pattern is used to separate chart-type-specific rendering logic
# from the main ChartDrawer class. Each chart type (Natal, Transit, Synastry,
# etc.) has its own renderer class that implements the ChartRendererProtocol.
# =============================================================================

from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from kerykeion.charts.chart_drawer import ChartDrawer  # type: ignore[attr-defined]  # noqa: F811


class ChartRendererProtocol(Protocol):
    """Protocol defining the interface for chart type-specific renderers.

    Each chart type (Natal, Transit, Synastry, etc.) implements this protocol
    to provide specialized rendering logic while sharing common infrastructure
    from ChartDrawer.
    """

    def setup_circles(self, template_dict: dict) -> None:
        """Configure concentric circle SVG elements for the wheel."""
        ...

    def setup_aspects(self, template_dict: dict) -> None:
        """Configure aspect lines and grid/list display."""
        ...

    def setup_info_sections(self, template_dict: dict) -> None:
        """Configure top_left and bottom_left informational text."""
        ...

    def setup_grids(self, template_dict: dict) -> None:
        """Configure planet and house grid tables."""
        ...

    def setup_house_comparison(self, template_dict: dict) -> None:
        """Configure house comparison grid (dual-wheel charts only)."""
        ...

    def render(self, template_dict: dict) -> None:
        """Execute all setup methods in order to populate template_dict."""
        ...


class BaseChartRenderer:
    """Base class providing common functionality for chart renderers.

    Subclasses override specific setup methods to customize rendering
    for their chart type while inheriting shared infrastructure.

    Attributes:
        drawer: Reference to the parent ChartDrawer instance.
    """

    def __init__(self, drawer: "ChartDrawer"):
        """Initialize the renderer with a reference to the parent drawer.

        Args:
            drawer: The ChartDrawer instance that owns this renderer.
        """
        self.drawer = drawer

    def render(self, template_dict: dict) -> None:
        """Execute all setup methods to populate the template dictionary.

        This is a Template Method that calls setup methods in a defined order.
        Subclasses override individual setup methods to customize behavior.

        Args:
            template_dict: Dictionary to populate with SVG template values.
        """
        self.setup_circles(template_dict)
        self.setup_aspects(template_dict)
        self.setup_info_sections(template_dict)
        self.setup_grids(template_dict)
        self.setup_house_comparison(template_dict)

    def setup_circles(self, template_dict: dict) -> None:
        """Configure circle elements. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement setup_circles")

    def setup_aspects(self, template_dict: dict) -> None:
        """Configure aspect elements. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement setup_aspects")

    def setup_info_sections(self, template_dict: dict) -> None:
        """Configure info sections. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement setup_info_sections")

    def setup_grids(self, template_dict: dict) -> None:
        """Configure grid elements. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement setup_grids")

    def setup_house_comparison(self, template_dict: dict) -> None:
        """Configure house comparison. Default: no comparison grid."""
        template_dict["makeHouseComparisonGrid"] = ""

    # -------------------------------------------------------------------------
    # SHARED HELPER METHODS
    # -------------------------------------------------------------------------
    # These methods provide common functionality used by multiple renderers.
    # -------------------------------------------------------------------------

    def _translate(self, key: str, default: Any) -> Any:
        """Convenience method to access drawer's translation function."""
        return self.drawer._translate(key, default)

    def _format_latitude(self, latitude: float, use_abbreviations: bool = False) -> str:
        """Format latitude using drawer's method."""
        return self.drawer._format_latitude_string(latitude, use_abbreviations)

    def _format_longitude(self, longitude: float, use_abbreviations: bool = False) -> str:
        """Format longitude using drawer's method."""
        return self.drawer._format_longitude_string(longitude, use_abbreviations)

    def _get_houses_list(self, subject) -> list:
        """Get houses list for a subject."""
        return get_houses_list(subject)


# =============================================================================
# INFO SECTION BUILDER
# =============================================================================
# Encapsulates the logic for building top_left and bottom_left info sections.
# Reduces code duplication across chart types.
# =============================================================================


class InfoSectionBuilder:
    """Builder for top_left and bottom_left informational sections.

    This class extracts common patterns for building the info sections
    displayed in chart corners, reducing duplication across chart types.
    """

    def __init__(self, drawer: "ChartDrawer"):
        """Initialize the builder with a drawer reference.

        Args:
            drawer: The ChartDrawer instance to build info sections for.
        """
        self.drawer = drawer

    def _translate(self, key: str, default: Any) -> Any:
        """Convenience method to access drawer's translation function."""
        return self.drawer._translate(key, default)

    def build_zodiac_info(self) -> str:
        """Build the zodiac/ayanamsa info string."""
        return self.drawer._get_zodiac_info()

    def build_domification_info(self) -> str:
        """Build the domification/house system string."""
        return self.drawer._get_domification_string()

    def build_perspective_info(self, subject) -> str:
        """Build the perspective type string."""
        return self.drawer._get_perspective_string(subject)

    def build_houses_system_info(self, subject) -> str:
        """Build compact house system string (without 'Domification:' label)."""
        house_key = "houses_system_" + subject.houses_system_identifier
        return f"{self._translate(house_key, subject.houses_system_name)} {self._translate('houses', 'Houses')}"

    def build_lunar_phase_info(
        self,
        template_dict: dict,
        subject,
        prefix: str = "",
        key_lunation: str = "bottom_left_2",
        key_phase: str = "bottom_left_3",
    ) -> None:
        """Populate template_dict with lunar phase info if available.

        Args:
            template_dict: Dictionary to populate.
            subject: Subject with potential lunar_phase data.
            prefix: Optional prefix for labels (e.g., "Transit ").
            key_lunation: Template key for lunation day.
            key_phase: Template key for phase name.
        """
        if subject.lunar_phase is None:
            template_dict[key_lunation] = ""
            template_dict[key_phase] = ""
            return

        lunation_label = self._translate("lunation_day", "Lunation Day")
        phase_label = self._translate("lunar_phase", "Lunar Phase")
        phase_name = subject.lunar_phase.moon_phase_name
        phase_key = phase_name.lower().replace(" ", "_")

        template_dict[key_lunation] = f"{prefix}{lunation_label}: {subject.lunar_phase.get('moon_phase', '')}"
        template_dict[key_phase] = f"{prefix}{phase_label}: {self._translate(phase_key, phase_name)}"

    def build_location_coordinates(
        self,
        latitude: float,
        longitude: float,
        use_abbreviations: bool = False,
    ) -> tuple[str, str]:
        """Build formatted latitude and longitude strings.

        Args:
            latitude: Geographic latitude.
            longitude: Geographic longitude.
            use_abbreviations: Use N/S/E/W instead of full words.

        Returns:
            Tuple of (latitude_string, longitude_string).
        """
        lat_str = self.drawer._format_latitude_string(latitude, use_abbreviations)
        lon_str = self.drawer._format_longitude_string(longitude, use_abbreviations)
        return lat_str, lon_str


# =============================================================================
# CHART TYPE-SPECIFIC RENDERERS
# =============================================================================
# Each renderer implements the ChartRendererProtocol for a specific chart type.
# This separates chart-specific logic from the main ChartDrawer class.
# =============================================================================


class NatalChartRenderer(BaseChartRenderer):
    """Renderer for Natal (birth) charts.

    Single-wheel chart showing birth positions with triangular aspect grid.
    """

    def setup_circles(self, template_dict: dict) -> None:
        """Set up radix-style circles for single-wheel display."""
        self.drawer._setup_radix_circles(template_dict)

    def setup_aspects(self, template_dict: dict) -> None:
        """Set up triangular aspect grid for single-chart aspects."""
        self.drawer._setup_single_chart_aspects(template_dict)

    def setup_info_sections(self, template_dict: dict) -> None:
        """Set up location, birth info, and technical details."""
        d = self.drawer
        builder = InfoSectionBuilder(d)

        # Top left section - Location and birth info
        lat_str, lon_str = builder.build_location_coordinates(d.geolat, d.geolon)

        template_dict["top_left_0"] = f"{self._translate('location', 'Location')}:"
        template_dict["top_left_1"] = f"{d.first_obj.city}, {d.first_obj.nation}"
        template_dict["top_left_2"] = f"{self._translate('latitude', 'Latitude')}: {lat_str}"
        template_dict["top_left_3"] = f"{self._translate('longitude', 'Longitude')}: {lon_str}"
        template_dict["top_left_4"] = format_datetime_with_timezone(d.first_obj.iso_formatted_local_datetime)

        localized_weekday = self._translate(f"weekdays.{d.first_obj.day_of_week}", d.first_obj.day_of_week)
        template_dict["top_left_5"] = f"{self._translate('day_of_week', 'Day of Week')}: {localized_weekday}"

        # Bottom left section - Technical info
        template_dict["bottom_left_0"] = builder.build_zodiac_info()
        template_dict["bottom_left_1"] = builder.build_domification_info()
        builder.build_lunar_phase_info(template_dict, d.first_obj)
        template_dict["bottom_left_4"] = builder.build_perspective_info(d.first_obj)

        # Lunar phase visualization
        d._setup_lunar_phase(template_dict, d.first_obj, d.geolat)

    def setup_grids(self, template_dict: dict) -> None:
        """Set up planet and house grids for single subject."""
        d = self.drawer
        houses_list = self._get_houses_list(d.first_obj)

        d._setup_main_houses_grid(template_dict, houses_list)
        template_dict["makeSecondaryHousesGrid"] = ""
        d._setup_single_wheel_houses(template_dict, houses_list)
        d._setup_single_wheel_planets(template_dict)
        d._setup_main_planet_grid(
            template_dict,
            d.first_obj.name,
            self._translate("planets_and_house", "Points for"),
        )
        template_dict["makeSecondaryPlanetGrid"] = ""


class CompositeChartRenderer(BaseChartRenderer):
    """Renderer for Composite charts.

    Single-wheel chart showing midpoints between two subjects.
    """

    def setup_circles(self, template_dict: dict) -> None:
        """Set up radix-style circles."""
        self.drawer._setup_radix_circles(template_dict)

    def setup_aspects(self, template_dict: dict) -> None:
        """Set up triangular aspect grid."""
        self.drawer._setup_single_chart_aspects(template_dict)

    def setup_info_sections(self, template_dict: dict) -> None:
        """Set up info for both composite subjects."""
        d = self.drawer
        builder = InfoSectionBuilder(d)

        # First subject coordinates
        first_lat, first_lng = builder.build_location_coordinates(
            d.first_obj.first_subject.lat,  # type: ignore[union-attr]
            d.first_obj.first_subject.lng,  # type: ignore[union-attr]
            use_abbreviations=True,
        )
        # Second subject coordinates
        second_lat, second_lng = builder.build_location_coordinates(
            d.first_obj.second_subject.lat,  # type: ignore[union-attr]
            d.first_obj.second_subject.lng,  # type: ignore[union-attr]
            use_abbreviations=True,
        )

        template_dict["top_left_0"] = f"{d.first_obj.first_subject.name}"  # type: ignore[union-attr]
        template_dict["top_left_1"] = datetime.fromisoformat(
            d.first_obj.first_subject.iso_formatted_local_datetime  # type: ignore[union-attr]
        ).strftime("%Y-%m-%d %H:%M")
        template_dict["top_left_2"] = f"{first_lat} {first_lng}"
        template_dict["top_left_3"] = d.first_obj.second_subject.name  # type: ignore[union-attr]
        template_dict["top_left_4"] = datetime.fromisoformat(
            d.first_obj.second_subject.iso_formatted_local_datetime  # type: ignore[union-attr]
        ).strftime("%Y-%m-%d %H:%M")
        template_dict["top_left_5"] = f"{second_lat} / {second_lng}"

        # Bottom left section
        template_dict["bottom_left_0"] = builder.build_zodiac_info()
        template_dict["bottom_left_1"] = builder.build_houses_system_info(d.first_obj)
        template_dict["bottom_left_2"] = (
            f"{self._translate('perspective_type', 'Perspective')}: {d.first_obj.first_subject.perspective_type}"  # type: ignore[union-attr]
        )
        template_dict["bottom_left_3"] = (
            f"{self._translate('composite_chart', 'Composite Chart')} - {self._translate('midpoints', 'Midpoints')}"
        )
        template_dict["bottom_left_4"] = ""

        # Lunar phase
        d._setup_lunar_phase(template_dict, d.first_obj, d.geolat)

    def setup_grids(self, template_dict: dict) -> None:
        """Set up grids with combined subject name."""
        d = self.drawer
        houses_list = self._get_houses_list(d.first_obj)

        d._setup_main_houses_grid(template_dict, houses_list)
        template_dict["makeSecondaryHousesGrid"] = ""
        d._setup_single_wheel_houses(template_dict, houses_list)
        d._setup_single_wheel_planets(template_dict)

        # Combined subject name
        subject_name = (
            f"{d.first_obj.first_subject.name} {self._translate('and_word', '&')} {d.first_obj.second_subject.name}"  # type: ignore[union-attr]
        )
        d._setup_main_planet_grid(
            template_dict,
            subject_name,
            self._translate("planets_and_house", "Points for"),
        )
        template_dict["makeSecondaryPlanetGrid"] = ""


class TransitChartRenderer(BaseChartRenderer):
    """Renderer for Transit charts.

    Dual-wheel chart showing natal (inner) vs transit (outer) positions.
    """

    def setup_circles(self, template_dict: dict) -> None:
        """Set up transit-style circles with outer ring."""
        self.drawer._setup_transit_circles(template_dict)

    def setup_aspects(self, template_dict: dict) -> None:
        """Set up aspect list or grid for dual-wheel chart."""
        d = self.drawer

        if d.double_chart_aspect_grid_type == "list":
            title = f"{d.first_obj.name} - {self._translate('transit_aspects', 'Transit Aspects')}"
            template_dict["makeAspectGrid"] = ""
            template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                title,
                d.aspects_list,
                d.planets_settings,
                d.aspects_settings,
                chart_height=d.height,
            )
        else:
            template_dict["makeAspectGrid"] = ""
            template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                d.chart_colors_settings["paper_0"],
                d.available_planets_setting,
                d.aspects_list,
                600,
                520,
            )

        template_dict["makeAspects"] = d._draw_all_aspects_lines(d.main_radius, d.main_radius - 160)

    def setup_info_sections(self, template_dict: dict) -> None:
        """Set up natal and transit info sections."""
        d = self.drawer
        builder = InfoSectionBuilder(d)

        # Clear element/quality percentages (Transit doesn't show these)
        d._clear_element_quality_strings(template_dict)

        # Natal coordinates
        natal_lat = ""
        natal_lon = ""
        if getattr(d.first_obj, "lat", None) is not None:
            natal_lat, natal_lon = builder.build_location_coordinates(
                d.first_obj.lat, d.first_obj.lng, use_abbreviations=True
            )

        # Transit coordinates
        transit_lat = ""
        transit_lon = ""
        if d.second_obj is not None:
            if getattr(d.second_obj, "lat", None) is not None:
                transit_lat, transit_lon = builder.build_location_coordinates(
                    d.second_obj.lat, d.second_obj.lng, use_abbreviations=True
                )

        natal_dt = format_datetime_with_timezone(d.first_obj.iso_formatted_local_datetime)
        natal_place = f"{format_location_string(d.first_obj.city)}, {d.first_obj.nation}"

        transit_dt = ""
        transit_place = ""
        if d.second_obj is not None:
            if getattr(d.second_obj, "iso_formatted_local_datetime", None) is not None:
                transit_dt = format_datetime_with_timezone(d.second_obj.iso_formatted_local_datetime)
            transit_place = f"{format_location_string(d.second_obj.city)}, {d.second_obj.nation}"

        template_dict["top_left_0"] = f"{self._translate('chart_info_natal_label', 'Natal')}: {natal_dt}"
        template_dict["top_left_1"] = natal_place
        template_dict["top_left_2"] = f"{natal_lat}  ·  {natal_lon}"
        template_dict["top_left_3"] = f"{self._translate('chart_info_transit_label', 'Transit')}: {transit_dt}"
        template_dict["top_left_4"] = transit_place
        template_dict["top_left_5"] = f"{transit_lat}  ·  {transit_lon}"

        # Bottom left section
        template_dict["bottom_left_0"] = builder.build_zodiac_info()
        template_dict["bottom_left_1"] = builder.build_domification_info()

        # Lunar phase from transit subject
        if d.second_obj is not None and hasattr(d.second_obj, "lunar_phase") and d.second_obj.lunar_phase is not None:
            builder.build_lunar_phase_info(
                template_dict,
                d.second_obj,
                prefix=f"{self._translate('Transit', 'Transit')} ",
                key_lunation="bottom_left_3",
                key_phase="bottom_left_4",
            )
        else:
            template_dict["bottom_left_3"] = ""
            template_dict["bottom_left_4"] = ""

        template_dict["bottom_left_2"] = builder.build_perspective_info(d.second_obj)

        # Moon phase visualization from transit subject
        if d.second_obj is not None and getattr(d.second_obj, "lunar_phase", None):
            template_dict["makeLunarPhase"] = makeLunarPhase(
                d.second_obj.lunar_phase["degrees_between_s_m"],  # type: ignore[index]
                d.geolat,
            )
        else:
            template_dict["makeLunarPhase"] = ""

    def setup_grids(self, template_dict: dict) -> None:
        """Set up dual-wheel planet and house grids."""
        d = self.drawer
        first_houses = self._get_houses_list(d.first_obj)
        second_houses = self._get_houses_list(d.second_obj)

        d._setup_main_houses_grid(template_dict, first_houses)
        template_dict["makeSecondaryHousesGrid"] = ""  # Transit doesn't show transit houses grid
        d._setup_dual_wheel_houses(template_dict, first_houses, second_houses)
        d._setup_dual_wheel_planets(template_dict)

        # Planet grids with wheel labels
        first_label = d._truncate_name(d.first_obj.name)
        transit_label = self._translate("transit", "Transit")
        first_grid_title = f"{first_label} ({self._translate('inner_wheel', 'Inner Wheel')})"
        second_grid_title = f"{transit_label} ({self._translate('outer_wheel', 'Outer Wheel')})"

        template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
            planets_and_houses_grid_title="",
            subject_name=first_grid_title,
            available_kerykeion_celestial_points=d.available_kerykeion_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
        )
        template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
            planets_and_houses_grid_title="",
            second_subject_name=second_grid_title,
            second_subject_available_kerykeion_celestial_points=d.second_subject_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
        )

    def setup_house_comparison(self, template_dict: dict) -> None:
        """Set up single house comparison grid for Transit."""
        d = self.drawer

        if not (d.show_house_position_comparison or d.show_cusp_position_comparison):
            template_dict["makeHouseComparisonGrid"] = ""
            return

        house_comparison_factory = HouseComparisonFactory(
            first_subject=d.first_obj,
            second_subject=d.second_obj,
            active_points=d.active_points,
        )
        house_comparison = house_comparison_factory.get_house_comparison()

        house_comparison_svg = ""

        if d.show_house_position_comparison:
            house_comparison_svg = draw_single_house_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                active_points=d.active_points,
                points_owner_subject_number=2,
                house_position_comparison_label=self._translate(
                    "house_position_comparison", "House Position Comparison"
                ),
                return_point_label=self._translate("transit_point", "Transit Point"),
                natal_house_label=self._translate("house_position", "Natal House"),
                x_position=d._TRANSIT_HOUSE_COMPARISON_X,
            )

        if d.show_cusp_position_comparison:
            cusp_x = 1180 if d.show_house_position_comparison else 980

            cusp_grid = draw_single_cusp_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                cusps_owner_subject_number=2,
                cusp_position_comparison_label=self._translate("cusp_position_comparison", "Cusp Position Comparison"),
                owner_cusp_label=self._translate("transit_cusp", "Transit Cusp"),
                projected_house_label=self._translate("natal_house", "Natal House"),
                x_position=cusp_x,
                y_position=0,
            )
            house_comparison_svg += cusp_grid

        template_dict["makeHouseComparisonGrid"] = house_comparison_svg


class SynastryChartRenderer(BaseChartRenderer):
    """Renderer for Synastry charts.

    Dual-wheel chart comparing two birth charts.
    """

    def setup_circles(self, template_dict: dict) -> None:
        """Set up transit-style circles for dual-wheel display."""
        self.drawer._setup_transit_circles(template_dict)

    def setup_aspects(self, template_dict: dict) -> None:
        """Set up aspect list or grid for synastry."""
        d = self.drawer

        if d.double_chart_aspect_grid_type == "list":
            template_dict["makeAspectGrid"] = ""
            template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                f"{d.first_obj.name} - {d.second_obj.name} {self._translate('synastry_aspects', 'Synastry Aspects')}",
                d.aspects_list,
                d.planets_settings,
                d.aspects_settings,
                chart_height=d.height,
            )
        else:
            template_dict["makeAspectGrid"] = ""
            template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                d.chart_colors_settings["paper_0"],
                d.available_planets_setting,
                d.aspects_list,
                550,
                450,
            )

        template_dict["makeAspects"] = d._draw_all_aspects_lines(d.main_radius, d.main_radius - 160)

    def setup_info_sections(self, template_dict: dict) -> None:
        """Set up info for both synastry subjects."""
        d = self.drawer
        builder = InfoSectionBuilder(d)

        template_dict["top_left_0"] = f"{d.first_obj.name}:"
        template_dict["top_left_1"] = f"{d.first_obj.city}, {d.first_obj.nation}"
        template_dict["top_left_2"] = format_datetime_with_timezone(d.first_obj.iso_formatted_local_datetime)
        template_dict["top_left_3"] = f"{d.second_obj.name}: "
        template_dict["top_left_4"] = f"{d.second_obj.city}, {d.second_obj.nation}"
        template_dict["top_left_5"] = format_datetime_with_timezone(d.second_obj.iso_formatted_local_datetime)

        # Bottom left section
        template_dict["bottom_left_0"] = ""
        template_dict["bottom_left_1"] = ""
        template_dict["bottom_left_2"] = builder.build_zodiac_info()
        template_dict["bottom_left_3"] = builder.build_houses_system_info(d.first_obj)
        template_dict["bottom_left_4"] = builder.build_perspective_info(d.first_obj)

        template_dict["makeLunarPhase"] = ""

    def setup_grids(self, template_dict: dict) -> None:
        """Set up dual-wheel grids for both subjects."""
        d = self.drawer
        first_houses = self._get_houses_list(d.first_obj)
        second_houses = self._get_houses_list(d.second_obj)

        d._setup_main_houses_grid(template_dict, first_houses)
        d._setup_secondary_houses_grid(template_dict, second_houses)
        d._setup_dual_wheel_houses(template_dict, first_houses, second_houses)
        d._setup_dual_wheel_planets(template_dict)

        # Planet grids
        first_label = d._truncate_name(d.first_obj.name, 18, "…")
        second_label = d._truncate_name(d.second_obj.name, 18, "…")

        template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
            planets_and_houses_grid_title="",
            subject_name=f"{first_label} ({self._translate('inner_wheel', 'Inner Wheel')})",
            available_kerykeion_celestial_points=d.available_kerykeion_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
        )
        template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
            planets_and_houses_grid_title="",
            second_subject_name=f"{second_label} ({self._translate('outer_wheel', 'Outer Wheel')})",
            second_subject_available_kerykeion_celestial_points=d.second_subject_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
        )

    def setup_house_comparison(self, template_dict: dict) -> None:
        """Set up dual house comparison grids for Synastry."""
        d = self.drawer

        if not (d.show_house_position_comparison or d.show_cusp_position_comparison):
            template_dict["makeHouseComparisonGrid"] = ""
            return

        house_comparison_factory = HouseComparisonFactory(
            first_subject=d.first_obj,
            second_subject=d.second_obj,
            active_points=d.active_points,
        )
        house_comparison = house_comparison_factory.get_house_comparison()

        first_subject_label = d._truncate_name(d.first_obj.name, 8, "…", True)
        second_subject_label = d._truncate_name(d.second_obj.name, 8, "…", True)
        point_column_label = self._translate("point", "Point")
        comparison_label = self._translate("house_position_comparison", "House Position Comparison")

        house_comparison_svg = ""

        if d.show_house_position_comparison:
            first_grid = draw_house_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                active_points=d.active_points,
                points_owner_subject_number=1,
                house_position_comparison_label=comparison_label,
                return_point_label=first_subject_label + " " + point_column_label,
                return_label=first_subject_label,
                radix_label=second_subject_label,
                x_position=d._HOUSE_COMPARISON_GRID_X_FIRST,
                y_position=0,
            )

            second_grid = draw_house_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                active_points=d.active_points,
                points_owner_subject_number=2,
                house_position_comparison_label="",
                return_point_label=second_subject_label + " " + point_column_label,
                return_label=second_subject_label,
                radix_label=first_subject_label,
                x_position=d._HOUSE_COMPARISON_GRID_X_SECOND,
                y_position=0,
            )

            house_comparison_svg = first_grid + second_grid

        if d.show_cusp_position_comparison:
            if d.show_house_position_comparison:
                first_columns = [
                    f"{first_subject_label} {point_column_label}",
                    first_subject_label,
                    second_subject_label,
                ]
                second_columns = [
                    f"{second_subject_label} {point_column_label}",
                    second_subject_label,
                    first_subject_label,
                ]

                first_grid_width = d._estimate_house_comparison_grid_width(
                    column_labels=first_columns,
                    include_radix_column=True,
                    include_title=True,
                )
                second_grid_width = d._estimate_house_comparison_grid_width(
                    column_labels=second_columns,
                    include_radix_column=True,
                    include_title=False,
                )

                max_right = max(1000 + first_grid_width, 1190 + second_grid_width)
                cusp_x = int(max_right + 50.0)
                first_cusp_x = cusp_x
                second_cusp_x = cusp_x + 160
            else:
                first_cusp_x = 1090
                second_cusp_x = 1290

            first_cusp = draw_cusp_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                cusps_owner_subject_number=1,
                cusp_position_comparison_label=self._translate("cusp_position_comparison", "Cusp Position Comparison"),
                owner_cusp_label=first_subject_label + " " + self._translate("cusp", "Cusp"),
                projected_house_label=second_subject_label + " " + self._translate("house", "House"),
                x_position=first_cusp_x,
                y_position=0,
            )

            second_cusp = draw_cusp_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                cusps_owner_subject_number=2,
                cusp_position_comparison_label="",
                owner_cusp_label=second_subject_label + " " + self._translate("cusp", "Cusp"),
                projected_house_label=first_subject_label + " " + self._translate("house", "House"),
                x_position=second_cusp_x,
                y_position=0,
            )

            house_comparison_svg += first_cusp + second_cusp

        template_dict["makeHouseComparisonGrid"] = house_comparison_svg


class SingleReturnChartRenderer(BaseChartRenderer):
    """Renderer for SingleReturnChart (Solar/Lunar Return without natal comparison).

    Single-wheel chart for the return moment only.
    """

    def setup_circles(self, template_dict: dict) -> None:
        """Set up radix-style circles."""
        self.drawer._setup_radix_circles(template_dict)

    def setup_aspects(self, template_dict: dict) -> None:
        """Set up triangular aspect grid."""
        self.drawer._setup_single_chart_aspects(template_dict)

    def setup_info_sections(self, template_dict: dict) -> None:
        """Set up return info section."""
        d = self.drawer
        builder = InfoSectionBuilder(d)

        lat_str, lon_str = builder.build_location_coordinates(d.geolat, d.geolon)

        template_dict["top_left_0"] = f"{self._translate('info', 'Info')}:"
        template_dict["top_left_1"] = format_datetime_with_timezone(d.first_obj.iso_formatted_local_datetime)
        template_dict["top_left_2"] = f"{d.first_obj.city}, {d.first_obj.nation}"
        template_dict["top_left_3"] = f"{self._translate('latitude', 'Latitude')}: {lat_str}"
        template_dict["top_left_4"] = f"{self._translate('longitude', 'Longitude')}: {lon_str}"

        if isinstance(d.first_obj, PlanetReturnModel) and d.first_obj.return_type == "Solar":
            template_dict["top_left_5"] = (
                f"{self._translate('type', 'Type')}: {self._translate('solar_return', 'Solar Return')}"
            )
        else:
            template_dict["top_left_5"] = (
                f"{self._translate('type', 'Type')}: {self._translate('lunar_return', 'Lunar Return')}"
            )

        # Bottom left section
        template_dict["bottom_left_0"] = builder.build_zodiac_info()
        template_dict["bottom_left_1"] = builder.build_houses_system_info(d.first_obj)
        builder.build_lunar_phase_info(template_dict, d.first_obj)
        template_dict["bottom_left_4"] = builder.build_perspective_info(d.first_obj)

        # Lunar phase visualization
        d._setup_lunar_phase(template_dict, d.first_obj, d.geolat)

    def setup_grids(self, template_dict: dict) -> None:
        """Set up grids for single return chart."""
        d = self.drawer
        houses_list = self._get_houses_list(d.first_obj)

        d._setup_main_houses_grid(template_dict, houses_list)
        template_dict["makeSecondaryHousesGrid"] = ""
        d._setup_single_wheel_houses(template_dict, houses_list)
        d._setup_single_wheel_planets(template_dict)
        d._setup_main_planet_grid(
            template_dict,
            d.first_obj.name,
            self._translate("planets_and_house", "Points for"),
        )
        template_dict["makeSecondaryPlanetGrid"] = ""


class DualReturnChartRenderer(BaseChartRenderer):
    """Renderer for DualReturnChart.

    Dual-wheel chart showing natal (inner) vs return (outer) positions.
    """

    def setup_circles(self, template_dict: dict) -> None:
        """Set up transit-style circles for dual-wheel display."""
        self.drawer._setup_transit_circles(template_dict)

    def setup_aspects(self, template_dict: dict) -> None:
        """Set up aspect list or grid for return chart."""
        d = self.drawer

        if d.double_chart_aspect_grid_type == "list":
            title = self._translate("return_aspects", "Natal to Return Aspects")
            template_dict["makeAspectGrid"] = ""
            template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                title,
                d.aspects_list,
                d.planets_settings,
                d.aspects_settings,
                max_columns=7,
                chart_height=d.height,
            )
        else:
            template_dict["makeAspectGrid"] = ""
            template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                d.chart_colors_settings["paper_0"],
                d.available_planets_setting,
                d.aspects_list,
                550,
                450,
            )

        template_dict["makeAspects"] = d._draw_all_aspects_lines(d.main_radius, d.main_radius - 160)

    def setup_info_sections(self, template_dict: dict) -> None:
        """Set up natal and return info sections."""
        d = self.drawer
        builder = InfoSectionBuilder(d)

        # Subject (natal) coordinates
        lat_str, lon_str = builder.build_location_coordinates(d.first_obj.lat, d.first_obj.lng)

        # Return coordinates
        return_lat, return_lon = builder.build_location_coordinates(d.second_obj.lat, d.second_obj.lng)

        if isinstance(d.second_obj, PlanetReturnModel) and d.second_obj.return_type == "Solar":
            template_dict["top_left_0"] = f"{self._translate('solar_return', 'Solar Return')}:"
        else:
            template_dict["top_left_0"] = f"{self._translate('lunar_return', 'Lunar Return')}:"

        template_dict["top_left_1"] = format_datetime_with_timezone(d.second_obj.iso_formatted_local_datetime)
        template_dict["top_left_2"] = f"{return_lat} / {return_lon}"
        template_dict["top_left_3"] = f"{d.first_obj.name}"
        template_dict["top_left_4"] = format_datetime_with_timezone(d.first_obj.iso_formatted_local_datetime)
        template_dict["top_left_5"] = f"{lat_str} / {lon_str}"

        # Bottom left section
        template_dict["bottom_left_0"] = builder.build_zodiac_info()
        template_dict["bottom_left_1"] = builder.build_domification_info()
        builder.build_lunar_phase_info(template_dict, d.first_obj)
        template_dict["bottom_left_4"] = builder.build_perspective_info(d.first_obj)

        # Lunar phase visualization
        d._setup_lunar_phase(template_dict, d.first_obj, d.geolat)

    def setup_grids(self, template_dict: dict) -> None:
        """Set up dual-wheel grids for natal and return."""
        d = self.drawer
        first_houses = self._get_houses_list(d.first_obj)
        second_houses = self._get_houses_list(d.second_obj)

        d._setup_main_houses_grid(template_dict, first_houses)
        d._setup_secondary_houses_grid(template_dict, second_houses)
        d._setup_dual_wheel_houses(template_dict, first_houses, second_houses)
        d._setup_dual_wheel_planets(template_dict)

        # Planet grid labels
        first_label = d._truncate_name(d.first_obj.name)
        if isinstance(d.second_obj, PlanetReturnModel) and d.second_obj.return_type == "Solar":
            first_grid_title = f"{first_label} ({self._translate('inner_wheel', 'Inner Wheel')})"
            second_grid_title = (
                f"{self._translate('solar_return', 'Solar Return')} ({self._translate('outer_wheel', 'Outer Wheel')})"
            )
        else:
            first_grid_title = f"{first_label} ({self._translate('inner_wheel', 'Inner Wheel')})"
            second_grid_title = (
                f"{self._translate('lunar_return', 'Lunar Return')} ({self._translate('outer_wheel', 'Outer Wheel')})"
            )

        template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
            planets_and_houses_grid_title="",
            subject_name=first_grid_title,
            available_kerykeion_celestial_points=d.available_kerykeion_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
        )
        template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
            planets_and_houses_grid_title="",
            second_subject_name=second_grid_title,
            second_subject_available_kerykeion_celestial_points=d.second_subject_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
        )

    def setup_house_comparison(self, template_dict: dict) -> None:
        """Set up dual house comparison grids for DualReturnChart."""
        d = self.drawer

        if not (d.show_house_position_comparison or d.show_cusp_position_comparison):
            template_dict["makeHouseComparisonGrid"] = ""
            return

        house_comparison_factory = HouseComparisonFactory(
            first_subject=d.first_obj,
            second_subject=d.second_obj,
            active_points=d.active_points,
        )
        house_comparison = house_comparison_factory.get_house_comparison()

        natal_label = self._translate("Natal", "Natal")
        return_label_text = self._translate("Return", "Return")
        point_column_label = self._translate("point", "Point")

        house_comparison_svg = ""

        if d.show_house_position_comparison:
            first_grid = draw_house_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                active_points=d.active_points,
                points_owner_subject_number=1,
                house_position_comparison_label=self._translate(
                    "house_position_comparison", "House Position Comparison"
                ),
                return_point_label=f"{natal_label} {point_column_label}",
                return_label=natal_label,
                radix_label=return_label_text,
                x_position=d._HOUSE_COMPARISON_GRID_X_FIRST,
                y_position=0,
            )

            second_grid = draw_house_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                active_points=d.active_points,
                points_owner_subject_number=2,
                house_position_comparison_label="",
                return_point_label=point_column_label,
                return_label=return_label_text,
                radix_label=natal_label,
                x_position=d._HOUSE_COMPARISON_GRID_X_SECOND,
                y_position=0,
            )

            house_comparison_svg = first_grid + second_grid

        if d.show_cusp_position_comparison:
            if d.show_house_position_comparison:
                first_columns = [f"{natal_label} {point_column_label}", natal_label, return_label_text]
                second_columns = [f"{return_label_text} {point_column_label}", return_label_text, natal_label]

                first_grid_width = d._estimate_house_comparison_grid_width(
                    column_labels=first_columns,
                    include_radix_column=True,
                    include_title=True,
                )
                second_grid_width = d._estimate_house_comparison_grid_width(
                    column_labels=second_columns,
                    include_radix_column=True,
                    include_title=False,
                )

                max_right = max(1000 + first_grid_width, 1190 + second_grid_width)
                cusp_x = int(max_right + 50.0)
                first_cusp_x = cusp_x
                second_cusp_x = cusp_x + 160
            else:
                first_cusp_x = 1090
                second_cusp_x = 1290

            first_cusp = draw_cusp_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                cusps_owner_subject_number=1,
                cusp_position_comparison_label=self._translate("cusp_position_comparison", "Cusp Position Comparison"),
                owner_cusp_label=f"{natal_label} " + self._translate("cusp", "Cusp"),
                projected_house_label=self._translate("Return", "Return") + " " + self._translate("house", "House"),
                x_position=first_cusp_x,
                y_position=0,
            )

            second_cusp = draw_cusp_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                cusps_owner_subject_number=2,
                cusp_position_comparison_label="",
                owner_cusp_label=self._translate("return_cusp", "Return Cusp"),
                projected_house_label=f"{natal_label} " + self._translate("house", "House"),
                x_position=second_cusp_x,
                y_position=0,
            )

            house_comparison_svg += first_cusp + second_cusp

        template_dict["makeHouseComparisonGrid"] = house_comparison_svg


# =============================================================================
# RENDERER REGISTRY
# =============================================================================
# Maps chart type names to their corresponding renderer classes.
# =============================================================================

CHART_RENDERERS: dict[str, type[BaseChartRenderer]] = {
    "Natal": NatalChartRenderer,
    "Composite": CompositeChartRenderer,
    "Transit": TransitChartRenderer,
    "Synastry": SynastryChartRenderer,
    "SingleReturnChart": SingleReturnChartRenderer,
    "DualReturnChart": DualReturnChartRenderer,
}


def get_chart_renderer(chart_type: str, drawer: "ChartDrawer") -> BaseChartRenderer:
    """Factory function to create the appropriate renderer for a chart type.

    Args:
        chart_type: The type of chart (e.g., "Natal", "Transit").
        drawer: The ChartDrawer instance to render for.

    Returns:
        An instance of the appropriate renderer class.

    Raises:
        ValueError: If chart_type is not recognized.
    """
    renderer_class = CHART_RENDERERS.get(chart_type)
    if renderer_class is None:
        raise ValueError(f"Unknown chart type: {chart_type}")
    return renderer_class(drawer)


class ChartDrawer:  # type: ignore[no-redef]
    """
    ChartDrawer generates astrological chart visualizations as SVG files from pre-computed chart data.

    This class is designed for pure visualization and requires chart data to be pre-computed using
    ChartDataFactory. This separation ensures clean architecture where ChartDataFactory handles
    all calculations (aspects, element/quality distributions, subjects) while ChartDrawer focuses
    solely on rendering SVG visualizations.

    Architecture Overview:
    ----------------------
    The class is organized into several logical sections:

    1. **Configuration (Dataclasses)**: Immutable configuration for dimensions, radii, and
       positions is managed through dataclasses defined at module level:
       - ChartDimensionsConfig: SVG canvas dimensions
       - CircleRadiiConfig: Concentric circle radii for the wheel
       - VerticalOffsetsConfig: Vertical positioning of chart elements
       - GridPositionsConfig: Horizontal grid positions

    2. **Initialization**: The __init__ method is organized into discrete steps, each
       delegated to a helper method for clarity:
       - _store_basic_configuration(): Store constructor parameters
       - _extract_chart_data(): Parse ChartDataModel
       - _load_language_settings(): Initialize translations
       - _configure_active_celestial_points(): Set up active planets
       - _configure_dimensions_and_geometry(): Set width, height, radii
       - _extract_element_quality_distributions(): Store element/quality data

    3. **Template Generation**: The _create_template_dictionary() method assembles all
       chart data into a dictionary that is substituted into XML templates. Chart-type
       specific logic is handled through explicit if/elif branches for maximum clarity.

    4. **SVG Output**: Multiple output methods support different use cases:
       - generate_svg_string() / save_svg(): Full chart with all elements
       - generate_wheel_only_svg_string() / save_wheel_only_svg_file(): Just the wheel
       - generate_aspect_grid_only_svg_string() / save_aspect_grid_only_svg_file(): Just aspects

    Supported Chart Types:
    ----------------------
    - **Natal**: Single-wheel birth chart with triangular aspect grid
    - **Composite**: Single-wheel midpoint chart of two subjects
    - **Transit**: Dual-wheel with natal (inner) and transit (outer) positions
    - **Synastry**: Dual-wheel comparing two birth charts
    - **SingleReturnChart**: Single-wheel Solar/Lunar return chart
    - **DualReturnChart**: Dual-wheel with natal and return positions

    NOTE:
        The generated SVG files are optimized for web use, opening in browsers. If you want to
        use them in other applications, you might need to adjust the SVG settings or styles.

    Args:
        chart_data (ChartDataModel):
            Pre-computed chart data from ChartDataFactory containing all subjects, aspects,
            element/quality distributions, and other analytical data. This is the ONLY source
            of chart information - no calculations are performed by ChartDrawer.
        theme (KerykeionChartTheme, optional):
            CSS theme for the chart. Available: 'classic', 'dark', 'dark_high_contrast',
            'light', 'light_high_contrast', 'strawberry'. If None, no styles applied.
            Defaults to 'classic'.
        double_chart_aspect_grid_type (Literal['list', 'table'], optional):
            Specifies rendering style for double-chart aspect grids. Defaults to 'list'.
        chart_language (KerykeionChartLanguage, optional):
            Language code for chart labels. Defaults to 'EN'.
        language_pack (dict | None, optional):
            Additional translations merged over the bundled defaults for the
            selected language. Useful to introduce new languages or override
            existing labels.
        external_view (bool, optional):
            For Natal charts only: place planets outside the zodiac ring.
            Defaults to False.
        transparent_background (bool, optional):
            Whether to use a transparent background instead of the theme color.
            Defaults to False.
        colors_settings (dict, optional):
            Custom color settings. Defaults to DEFAULT_CHART_COLORS.
        celestial_points_settings (Sequence, optional):
            Custom celestial point settings. Defaults to DEFAULT_CELESTIAL_POINTS_SETTINGS.
        aspects_settings (Sequence, optional):
            Custom aspect settings. Defaults to DEFAULT_CHART_ASPECTS_SETTINGS.
        custom_title (str | None, optional):
            Override the auto-generated chart title.
        show_house_position_comparison (bool, optional):
            Show house comparison grid for supported chart types. Defaults to True.
        show_cusp_position_comparison (bool, optional):
            Show cusp comparison grid. Defaults to False.
        auto_size (bool, optional):
            Automatically adjust dimensions to fit content. Defaults to True.
        padding (int, optional):
            Padding in pixels around chart elements. Defaults to 20.
        show_degree_indicators (bool, optional):
            Show degree indicators on planets. Defaults to True.
        show_aspect_icons (bool, optional):
            Show aspect icons on aspect lines. Defaults to True.

    Public Methods:
        generate_svg_string(minify=False, remove_css_variables=False) -> str:
            Render the full chart SVG as a string without writing to disk.

        save_svg(output_path=None, filename=None, minify=False, remove_css_variables=False) -> None:
            Generate and write the full chart SVG file to the specified path.
            If output_path is None, saves to the user's home directory.
            If filename is None, uses default pattern: '{subject.name} - {chart_type} Chart.svg'.

        generate_wheel_only_svg_string(minify=False, remove_css_variables=False) -> str:
            Render only the chart wheel (no aspect grid) as an SVG string.

        save_wheel_only_svg_file(output_path=None, filename=None, ...) -> None:
            Generate and write the wheel-only SVG file to the specified path.

        generate_aspect_grid_only_svg_string(minify=False, remove_css_variables=False) -> str:
            Render only the aspect grid as an SVG string.

        save_aspect_grid_only_svg_file(output_path=None, filename=None, ...) -> None:
            Generate and write the aspect-grid-only SVG file to the specified path.

    Example:
        >>> from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
        >>> from kerykeion.chart_data_factory import ChartDataFactory
        >>> from kerykeion.charts.chart_drawer import ChartDrawer
        >>>
        >>> # Step 1: Create subject
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "John", 1990, 1, 1, 12, 0, "London", "GB"
        ... )
        >>>
        >>> # Step 2: Pre-compute chart data
        >>> chart_data = ChartDataFactory.create_natal_chart_data(subject)
        >>>
        >>> # Step 3: Create visualization
        >>> chart_drawer = ChartDrawer(chart_data=chart_data, theme="classic")
        >>> chart_drawer.save_svg()  # Saves to home directory with default filename
        >>>
        >>> # Or specify custom path and filename:
        >>> chart_drawer.save_svg("/path/to/output/directory", "my_custom_chart")
    """

    # =========================================================================
    # CLASS CONSTANTS
    # =========================================================================
    # Configuration values are now managed through dataclasses defined above:
    # - ChartDimensionsConfig: SVG canvas dimensions
    # - CircleRadiiConfig: Concentric circle radii
    # - VerticalOffsetsConfig: Vertical positioning of chart elements
    # - GridPositionsConfig: Horizontal grid positions
    #
    # The following class constants reference the default dataclass instances
    # for backward compatibility and convenience.
    # =========================================================================

    # -------------------------------------------------------------------------
    # CHART DIMENSIONS (from ChartDimensionsConfig)
    # -------------------------------------------------------------------------
    _DEFAULT_HEIGHT = DEFAULT_DIMENSIONS.default_height
    _DEFAULT_NATAL_WIDTH = DEFAULT_DIMENSIONS.natal_width
    _DEFAULT_FULL_WIDTH = DEFAULT_DIMENSIONS.full_width
    _DEFAULT_FULL_WIDTH_WITH_TABLE = DEFAULT_DIMENSIONS.full_width_with_table
    _DEFAULT_SYNASTRY_WIDTH = DEFAULT_DIMENSIONS.synastry_width
    _DEFAULT_ULTRA_WIDE_WIDTH = DEFAULT_DIMENSIONS.ultra_wide_width

    # -------------------------------------------------------------------------
    # WHEEL GEOMETRY - RADII (from CircleRadiiConfig)
    # -------------------------------------------------------------------------
    # The wheel is drawn as concentric circles. See CircleRadiiConfig docstring
    # for detailed explanation of the circle layout.
    #
    # For SINGLE-WHEEL charts (Natal internal view, Composite, SingleReturn):
    #   first_circle_radius = 0    (no outer planet ring)
    #   second_circle_radius = 36  (zodiac boundary)
    #   third_circle_radius = 120  (inner aspect area)
    #
    # For DUAL-WHEEL charts (Transit, Synastry, DualReturn):
    #   Same radii, but outer ring used for second subject planets
    #
    # For EXTERNAL VIEW Natal charts:
    #   first_circle_radius = 56   (outer planet ring)
    #   second_circle_radius = 92  (zodiac boundary shifted inward)
    #   third_circle_radius = 112  (inner aspect area shifted inward)
    _MAIN_RADIUS = DEFAULT_RADII.main_radius

    # Single-wheel internal layout (planets inside zodiac ring)
    _SINGLE_WHEEL_FIRST_CIRCLE = DEFAULT_RADII.single_wheel_first
    _SINGLE_WHEEL_SECOND_CIRCLE = DEFAULT_RADII.single_wheel_second
    _SINGLE_WHEEL_THIRD_CIRCLE = DEFAULT_RADII.single_wheel_third

    # Dual-wheel layout (same as single-wheel, outer ring for 2nd subject)
    _DUAL_WHEEL_FIRST_CIRCLE = DEFAULT_RADII.single_wheel_first
    _DUAL_WHEEL_SECOND_CIRCLE = DEFAULT_RADII.single_wheel_second
    _DUAL_WHEEL_THIRD_CIRCLE = DEFAULT_RADII.single_wheel_third

    # External view layout (planets outside zodiac ring)
    _EXTERNAL_VIEW_FIRST_CIRCLE = DEFAULT_RADII.external_view_first
    _EXTERNAL_VIEW_SECOND_CIRCLE = DEFAULT_RADII.external_view_second
    _EXTERNAL_VIEW_THIRD_CIRCLE = DEFAULT_RADII.external_view_third

    # -------------------------------------------------------------------------
    # LAYOUT SPACING AND POSITIONING
    # -------------------------------------------------------------------------
    _VERTICAL_PADDING_TOP = 15
    _VERTICAL_PADDING_BOTTOM = 15
    _TITLE_SPACING = 8

    _ASPECT_LIST_ASPECTS_PER_COLUMN = 14
    _ASPECT_LIST_COLUMN_WIDTH = 105

    # Dynamic height adjustment parameters
    _MAX_TOP_SHIFT = 80  # Maximum pixels to shift top elements down
    _TOP_SHIFT_FACTOR = 2  # Pixels per extra point for top shift calculation
    _ROW_HEIGHT = 8  # Pixels per row in planet/house grids

    # -------------------------------------------------------------------------
    # VIEWBOX PRESETS (computed from dimensions config)
    # -------------------------------------------------------------------------
    _BASIC_CHART_VIEWBOX = f"0 0 {DEFAULT_DIMENSIONS.natal_width} {DEFAULT_DIMENSIONS.default_height}"
    _WIDE_CHART_VIEWBOX = f"0 0 {DEFAULT_DIMENSIONS.full_width} 546.0"
    _ULTRA_WIDE_CHART_VIEWBOX = f"0 0 {DEFAULT_DIMENSIONS.ultra_wide_width} 546.0"
    _TRANSIT_CHART_WITH_TABLE_VIWBOX = f"0 0 {DEFAULT_DIMENSIONS.full_width_with_table} 546.0"

    # -------------------------------------------------------------------------
    # GRID X-POSITIONS (from GridPositionsConfig)
    # -------------------------------------------------------------------------
    _MAIN_PLANET_GRID_X = DEFAULT_GRID_POSITIONS.main_planet_x
    _MAIN_HOUSES_GRID_X = DEFAULT_GRID_POSITIONS.main_houses_x
    _SECONDARY_PLANET_GRID_X = DEFAULT_GRID_POSITIONS.secondary_planet_x
    _SECONDARY_HOUSES_GRID_X = DEFAULT_GRID_POSITIONS.secondary_houses_x
    _HOUSE_COMPARISON_GRID_X_FIRST = DEFAULT_GRID_POSITIONS.house_comparison_first_x
    _HOUSE_COMPARISON_GRID_X_SECOND = DEFAULT_GRID_POSITIONS.house_comparison_second_x
    _TRANSIT_HOUSE_COMPARISON_X = DEFAULT_GRID_POSITIONS.transit_house_comparison_x
    _TRANSIT_ASPECT_GRID_X = DEFAULT_GRID_POSITIONS.transit_aspect_grid_x
    _TRANSIT_ASPECT_GRID_Y = DEFAULT_GRID_POSITIONS.transit_aspect_grid_y

    # -------------------------------------------------------------------------
    # INSTANCE ATTRIBUTES (type hints)
    # -------------------------------------------------------------------------
    # These are set during __init__ and define the chart's runtime state.

    # Subject data - the primary and optional secondary astrological subjects
    first_obj: FirstSubjectType
    second_obj: SecondSubjectType
    chart_type: ChartType

    # Visual configuration
    theme: Union[KerykeionChartTheme, None]
    double_chart_aspect_grid_type: Literal["list", "table"]
    chart_language: KerykeionChartLanguage
    active_points: List[AstrologicalPoint]
    active_aspects: List[ActiveAspect]
    transparent_background: bool
    external_view: bool
    show_house_position_comparison: bool
    custom_title: Union[str, None]
    _language_model: KerykeionLanguageModel
    _fallback_language_model: KerykeionLanguageModel

    # Internal properties
    fire: float
    earth: float
    air: float
    water: float
    first_circle_radius: float
    second_circle_radius: float
    third_circle_radius: float
    width: Union[float, int]
    language_settings: dict
    chart_colors_settings: dict
    planets_settings: list[dict[Any, Any]]
    aspects_settings: list[dict[Any, Any]]
    available_planets_setting: List[dict[Any, Any]]
    height: float
    location: str
    geolat: float
    geolon: float
    template: str

    def __init__(
        self,
        chart_data: "ChartDataModel",
        *,
        theme: Union[KerykeionChartTheme, None] = "classic",
        double_chart_aspect_grid_type: Literal["list", "table"] = "list",
        chart_language: KerykeionChartLanguage = "EN",
        language_pack: Optional[Mapping[str, Any]] = None,
        external_view: bool = False,
        transparent_background: bool = False,
        colors_settings: dict = DEFAULT_CHART_COLORS,
        celestial_points_settings: Sequence[_CelestialPointSetting] = DEFAULT_CELESTIAL_POINTS_SETTINGS,
        aspects_settings: Sequence[_ChartAspectSetting] = DEFAULT_CHART_ASPECTS_SETTINGS,
        custom_title: Union[str, None] = None,
        show_house_position_comparison: bool = True,
        show_cusp_position_comparison: bool = False,
        auto_size: bool = True,
        padding: int = 20,
        show_degree_indicators: bool = True,
        show_aspect_icons: bool = True,
    ):
        """
        Initialize the chart visualizer with pre-computed chart data.

        This constructor orchestrates the setup of all chart components through
        a series of well-defined initialization steps. Each step is delegated
        to a private helper method for clarity and maintainability.

        Args:
            chart_data (ChartDataModel):
                Pre-computed chart data from ChartDataFactory containing all subjects,
                aspects, element/quality distributions, and other analytical data.
            theme (KerykeionChartTheme or None, optional):
                CSS theme to apply; None for default styling. Defaults to 'classic'.
            double_chart_aspect_grid_type (Literal['list','table'], optional):
                Layout style for double-chart aspect grids. Defaults to 'list'.
            chart_language (KerykeionChartLanguage, optional):
                Language code for chart labels (e.g., 'EN', 'IT'). Defaults to 'EN'.
            language_pack (dict | None, optional):
                Additional translations merged over the bundled defaults for the
                selected language. Useful to introduce new languages or override
                existing labels.
            external_view (bool, optional):
                Whether to use external visualization (planets on outer ring) for
                single-subject charts. Only applies to Natal charts. Defaults to False.
            transparent_background (bool, optional):
                Whether to use a transparent background instead of the theme color.
                Defaults to False.
            colors_settings (dict, optional):
                Custom color settings for chart elements. Defaults to DEFAULT_CHART_COLORS.
            celestial_points_settings (Sequence, optional):
                Custom celestial point settings. Defaults to DEFAULT_CELESTIAL_POINTS_SETTINGS.
            aspects_settings (Sequence, optional):
                Custom aspect settings. Defaults to DEFAULT_CHART_ASPECTS_SETTINGS.
            custom_title (str or None, optional):
                Custom title for the chart. If None, uses default based on chart type.
            show_house_position_comparison (bool, optional):
                Whether to render the house position comparison grid (when supported).
                Defaults to True. Set to False to hide and reclaim horizontal space.
            show_cusp_position_comparison (bool, optional):
                Whether to render the cusp position comparison grid alongside the house
                comparison. Defaults to False.
            auto_size (bool, optional):
                Whether to automatically adjust chart dimensions based on content.
                Defaults to True.
            padding (int, optional):
                Padding in pixels around chart elements. Defaults to 20.
            show_degree_indicators (bool, optional):
                Whether to show degree indicators on planets. Defaults to True.
            show_aspect_icons (bool, optional):
                Whether to show aspect icons on aspect lines. Defaults to True.
        """
        # =====================================================================
        # STEP 1: Store basic configuration parameters
        # =====================================================================
        # These are direct assignments of constructor parameters to instance
        # attributes. They form the foundation for all subsequent setup.
        self._store_basic_configuration(
            chart_language=chart_language,
            double_chart_aspect_grid_type=double_chart_aspect_grid_type,
            transparent_background=transparent_background,
            external_view=external_view,
            colors_settings=colors_settings,
            celestial_points_settings=celestial_points_settings,
            aspects_settings=aspects_settings,
            custom_title=custom_title,
            show_house_position_comparison=show_house_position_comparison,
            show_cusp_position_comparison=show_cusp_position_comparison,
            show_degree_indicators=show_degree_indicators,
            show_aspect_icons=show_aspect_icons,
            auto_size=auto_size,
            padding=padding,
        )

        # =====================================================================
        # STEP 2: Extract and store chart data
        # =====================================================================
        # Parse the ChartDataModel to extract subjects, aspects, and other
        # computed data. This includes determining if we have a single or
        # dual-wheel chart configuration.
        self._extract_chart_data(chart_data)

        # =====================================================================
        # STEP 3: Load language settings
        # =====================================================================
        # Initialize the translation system with the requested language and
        # any custom language pack overrides.
        self._load_language_settings(language_pack)

        # =====================================================================
        # STEP 4: Configure active celestial points
        # =====================================================================
        # Set up the list of celestial points that will be displayed in the
        # chart, based on what's active in the chart data.
        self._configure_active_celestial_points()

        # =====================================================================
        # STEP 5: Configure chart dimensions and geometry
        # =====================================================================
        # Set up width, height, circle radii, and other geometric properties
        # based on the chart type and display options.
        self._configure_dimensions_and_geometry(chart_data)

        # =====================================================================
        # STEP 6: Extract element and quality distributions
        # =====================================================================
        # Store the pre-computed element (fire, earth, air, water) and quality
        # (cardinal, fixed, mutable) distributions for display.
        self._extract_element_quality_distributions(chart_data)

        # =====================================================================
        # STEP 7: Validate and set up theme
        # =====================================================================
        # Verify the theme is valid and load the corresponding CSS.
        if theme not in get_args(KerykeionChartTheme) and theme is not None:
            raise KerykeionException(f"Theme {theme} is not available. Set None for default theme.")
        self.set_up_theme(theme)

        # =====================================================================
        # STEP 8: Apply dynamic layout adjustments
        # =====================================================================
        # Adjust chart dimensions based on the number of active celestial
        # points and other dynamic factors.
        self._apply_dynamic_height_adjustment()
        self._adjust_height_for_extended_aspect_columns()

        # Reconcile width with the updated layout once height adjustments are known
        if self.auto_size:
            self._update_width_to_content()

    # =========================================================================
    # INITIALIZATION HELPER METHODS
    # =========================================================================
    # These methods are called by __init__ to break down the initialization
    # into logical, testable units. They are ordered by their call sequence.
    # =========================================================================

    def _store_basic_configuration(
        self,
        *,
        chart_language: KerykeionChartLanguage,
        double_chart_aspect_grid_type: Literal["list", "table"],
        transparent_background: bool,
        external_view: bool,
        colors_settings: dict,
        celestial_points_settings: Sequence[_CelestialPointSetting],
        aspects_settings: Sequence[_ChartAspectSetting],
        custom_title: Union[str, None],
        show_house_position_comparison: bool,
        show_cusp_position_comparison: bool,
        show_degree_indicators: bool,
        show_aspect_icons: bool,
        auto_size: bool,
        padding: int,
    ) -> None:
        """
        Store basic configuration parameters as instance attributes.

        This method handles the first step of initialization: storing all
        constructor parameters that don't require any processing or validation.

        Args:
            See __init__ docstring for parameter descriptions.
        """
        # Language and display settings
        self.chart_language = chart_language
        self.double_chart_aspect_grid_type = double_chart_aspect_grid_type
        self.transparent_background = transparent_background
        self.external_view = external_view

        # Color and rendering settings (deep copy to avoid mutation)
        self.chart_colors_settings = deepcopy(colors_settings)
        self.planets_settings = [dict(body) for body in celestial_points_settings]
        self.aspects_settings = [dict(aspect) for aspect in aspects_settings]

        # Display options
        self.custom_title = custom_title
        self.show_house_position_comparison = show_house_position_comparison
        self.show_cusp_position_comparison = show_cusp_position_comparison
        self.show_degree_indicators = show_degree_indicators
        self.show_aspect_icons = show_aspect_icons
        self.auto_size = auto_size
        self._padding = padding

        # Initialize vertical offsets using the dataclass, then convert to dict
        self._vertical_offsets_config = VerticalOffsetsConfig()
        self._vertical_offsets: dict[str, float] = self._vertical_offsets_config.to_dict()

    def _extract_chart_data(self, chart_data: "ChartDataModel") -> None:
        """
        Extract and store data from the ChartDataModel.

        This method parses the chart data model to extract:
        - Chart type (Natal, Transit, Synastry, etc.)
        - Active celestial points and aspects
        - Primary and secondary subjects (for dual-wheel charts)

        Args:
            chart_data: Pre-computed chart data from ChartDataFactory.
        """
        # Store reference to the full chart data
        self.chart_data = chart_data
        self.chart_type = chart_data.chart_type
        self.active_points = chart_data.active_points
        self.active_aspects = chart_data.active_aspects

        # Extract subjects based on chart type
        # Single-wheel charts have only one subject, dual-wheel charts have two
        if chart_data.chart_type in ["Natal", "Composite", "SingleReturnChart"]:
            # SingleChartDataModel - only one subject
            self.first_obj = getattr(chart_data, "subject")
            self.second_obj = None
        else:
            # DualChartDataModel - two subjects (Transit, Synastry, DualReturnChart)
            self.first_obj = getattr(chart_data, "first_subject")
            self.second_obj = getattr(chart_data, "second_subject")

    def _configure_active_celestial_points(self) -> None:
        """
        Configure the list of active celestial points for rendering.

        This method:
        1. Filters planets_settings to only include active points
        2. Marks each active point with is_active=True
        3. Collects KerykeionPointModel objects for both subjects
        4. Warns if more than 24 points are active (may cause crowding)
        """
        # Main radius for all chart wheels (distance from center to outer edge)
        self.main_radius = self._MAIN_RADIUS

        # Filter and mark active planets from settings
        self.available_planets_setting = []
        for body in self.planets_settings:
            if body["name"] in self.active_points:
                body["is_active"] = True
                self.available_planets_setting.append(body)

        # Warn about potential crowding with many active points
        active_points_count = len(self.available_planets_setting)
        if active_points_count > 24:
            logger.warning(
                "ChartDrawer detected %s active celestial points; rendering may look crowded beyond 24.",
                active_points_count,
            )

        # Collect KerykeionPointModel objects for the primary subject
        available_celestial_points_names = [body["name"].lower() for body in self.available_planets_setting]
        self.available_kerykeion_celestial_points = self._collect_subject_points(
            self.first_obj,
            available_celestial_points_names,
        )

        # Collect points for secondary subject (dual-wheel charts only)
        # These appear on the outer wheel in Transit, Synastry, and DualReturnChart
        self.second_subject_celestial_points: list[KerykeionPointModel] = []
        if self.second_obj is not None:
            self.second_subject_celestial_points = self._collect_subject_points(
                self.second_obj,
                available_celestial_points_names,
            )

    def _configure_dimensions_and_geometry(self, chart_data: "ChartDataModel") -> None:
        """
        Configure chart dimensions and wheel geometry.

        This method sets up:
        - Aspects list from chart data
        - Initial height (may be adjusted later)
        - Location information (city, lat/lon)
        - Chart width based on chart type
        - Circle radii based on chart type and view mode
        - Width adjustments for house comparison visibility

        Args:
            chart_data: Pre-computed chart data containing aspects.
        """
        # Store aspects list for rendering
        self.aspects_list = chart_data.aspects

        # Set initial height (may be increased for many active points)
        self.height = self._DEFAULT_HEIGHT

        # Extract location information for display
        self.location, self.geolat, self.geolon = self._get_location_info()

        # Determine width based on chart type and display options
        self.width = self._get_chart_width()

        # Set circle radii based on chart type and view mode
        self._setup_circle_radii()

        # Adjust width if house comparison grid is hidden
        self._apply_house_comparison_width_override()

    def _extract_element_quality_distributions(self, chart_data: "ChartDataModel") -> None:
        """
        Extract pre-computed element and quality distributions from chart data.

        These distributions show the balance of elements (Fire, Earth, Air, Water)
        and qualities (Cardinal, Fixed, Mutable) in the chart, typically displayed
        as percentages in the chart header.

        Args:
            chart_data: Pre-computed chart data containing distributions.
        """
        # Element distribution (Fire, Earth, Air, Water)
        self.fire = chart_data.element_distribution.fire
        self.earth = chart_data.element_distribution.earth
        self.air = chart_data.element_distribution.air
        self.water = chart_data.element_distribution.water

        # Quality distribution (Cardinal, Fixed, Mutable)
        self.cardinal = chart_data.quality_distribution.cardinal
        self.fixed = chart_data.quality_distribution.fixed
        self.mutable = chart_data.quality_distribution.mutable

    def _count_active_planets(self) -> int:
        """Return number of active celestial points in the current chart."""
        return len([p for p in self.available_planets_setting if p.get("is_active")])

    def _get_chart_width(self) -> float:
        """Determine the appropriate chart width based on chart type and display options.

        Returns:
            float: The width in pixels for the SVG canvas.
        """
        width_map = {
            "Natal": self._DEFAULT_NATAL_WIDTH,
            "Composite": self._DEFAULT_NATAL_WIDTH,
            "SingleReturnChart": self._DEFAULT_NATAL_WIDTH,
            "Synastry": self._DEFAULT_SYNASTRY_WIDTH,
            "DualReturnChart": self._DEFAULT_ULTRA_WIDE_WIDTH,
        }

        if self.chart_type == "Transit":
            # Transit width depends on aspect grid display type
            if self.double_chart_aspect_grid_type == "table":
                return self._DEFAULT_FULL_WIDTH_WITH_TABLE
            return self._DEFAULT_FULL_WIDTH

        return width_map.get(self.chart_type, self._DEFAULT_FULL_WIDTH)

    def _setup_circle_radii(self) -> None:
        """Configure the three concentric circle radii based on chart type and view mode.

        The wheel consists of three circles:
        - first_circle_radius: Outer boundary (0 for internal view, > 0 for external view)
        - second_circle_radius: Zodiac sign ring boundary
        - third_circle_radius: Inner boundary for aspect lines

        For Natal charts with external_view=True, planets appear outside the zodiac ring.
        All other configurations place planets inside the zodiac ring.
        """
        # Only Natal charts with external_view use the external layout
        if self.chart_type == "Natal" and self.external_view:
            self.first_circle_radius = self._EXTERNAL_VIEW_FIRST_CIRCLE
            self.second_circle_radius = self._EXTERNAL_VIEW_SECOND_CIRCLE
            self.third_circle_radius = self._EXTERNAL_VIEW_THIRD_CIRCLE
        else:
            # All other chart types use the standard internal/dual-wheel layout
            self.first_circle_radius = self._SINGLE_WHEEL_FIRST_CIRCLE
            self.second_circle_radius = self._SINGLE_WHEEL_SECOND_CIRCLE
            self.third_circle_radius = self._SINGLE_WHEEL_THIRD_CIRCLE

    def _apply_dynamic_height_adjustment(self) -> None:
        """Adjust chart height and vertical offsets based on active celestial points.

        When more than 20 celestial points are active, the planet/house grids
        extend vertically. This method increases the SVG height proportionally
        and adjusts the vertical offsets of all chart elements to maintain
        proper layout.

        The adjustment strategy:
        1. Bottom-anchored elements (wheel, aspect grid, lunar phase) shift down
           by the full height increase to stay at the bottom.
        2. Top elements (title, element/quality percentages) shift down partially
           to maintain visual balance and breathing room.
        3. The planet/house grid shifts down more to create space between the
           title section and the data grids.

        For Synastry charts, a specialized adjustment is used due to the
        multiple side-by-side grids that all grow vertically together.
        """
        active_points_count = self._count_active_planets()

        # Create fresh offsets from the default configuration
        offsets = VerticalOffsetsConfig().to_dict()

        minimum_height = self._DEFAULT_HEIGHT

        # Synastry has its own height logic due to dual comparison grids
        if self.chart_type == "Synastry":
            self._apply_synastry_height_adjustment(
                active_points_count=active_points_count,
                offsets=offsets,
                minimum_height=minimum_height,
            )
            return

        # Up to 20 active points fit in the default height
        if active_points_count <= 20:
            self.height = max(self.height, minimum_height)
            self._vertical_offsets = offsets
            return

        # Calculate extra height needed for additional points
        extra_points = active_points_count - 20
        extra_height = extra_points * self._ROW_HEIGHT  # 8px per additional point

        self.height = max(self.height, minimum_height + extra_height)

        delta_height = max(self.height - minimum_height, 0)

        # Bottom-anchored elements shift down by the full delta
        # This keeps them "pinned" to the bottom of the SVG
        offsets["wheel"] += delta_height
        offsets["aspect_grid"] += delta_height
        offsets["aspect_list"] += delta_height
        offsets["lunar_phase"] += delta_height
        offsets["bottom_left"] += delta_height

        # Top elements get a partial shift to maintain visual balance
        # The shift is capped at _MAX_TOP_SHIFT (80px) to prevent excessive spacing
        shift = min(extra_points * self._TOP_SHIFT_FACTOR, self._MAX_TOP_SHIFT)
        top_shift = shift // 2  # Title shifts less than grids

        offsets["grid"] += shift
        offsets["title"] += top_shift
        offsets["elements"] += top_shift
        offsets["qualities"] += top_shift

        self._vertical_offsets = offsets

    def _adjust_height_for_extended_aspect_columns(self) -> None:
        """Ensure tall aspect columns fit within the SVG for double-chart lists.

        When displaying many aspects in list mode for dual-wheel charts,
        columns beyond the 11th one extend upward beyond the normal bounds.
        This method calculates the required height to accommodate these
        extended columns without clipping.

        Layout constants explained:
        - aspects_per_column (14): Standard number of aspects per column
        - extended_column_start (11): Column index where upward extension begins
        - translate_y (273): Y-translation of the aspect list SVG group
        - bottom_padding (40): Space between last aspect and SVG bottom
        - title_clearance (18): Space reserved above for column headers
        - line_height (14): Vertical spacing between aspect entries
        """
        if self.double_chart_aspect_grid_type != "list":
            return

        if self.chart_type not in ("Synastry", "Transit", "DualReturnChart"):
            return

        total_aspects = len(self.aspects_list) if hasattr(self, "aspects_list") else 0
        if total_aspects == 0:
            return

        # Layout parameters for aspect list rendering
        aspects_per_column = 14  # Max aspects per column before overflow
        extended_column_start = 11  # Columns 0-10 fit normally; 11+ extend upward
        base_capacity = aspects_per_column * extended_column_start

        # If all aspects fit in the base columns, no height adjustment needed
        if total_aspects <= base_capacity:
            return

        # Calculate how much extra height is needed for extended columns
        translate_y = 273  # SVG group translation (aspect list starts at y=273)
        bottom_padding = 40  # Bottom margin
        title_clearance = 18  # Header/title space
        line_height = 14  # Pixels per aspect row

        # Calculate the maximum capacity when extending upward
        baseline_index = aspects_per_column - 1
        top_limit_index = ceil((-translate_y + title_clearance) / line_height)
        max_capacity_by_top = baseline_index - top_limit_index + 1

        if max_capacity_by_top <= aspects_per_column:
            return

        # Calculate required SVG height to fit all extended content
        target_capacity = max_capacity_by_top
        required_available_height = target_capacity * line_height
        required_height = translate_y + bottom_padding + required_available_height

        if required_height <= self.height:
            return

        # Increase height and shift bottom-anchored elements accordingly
        delta = required_height - self.height
        self.height = required_height

        offsets = self._vertical_offsets
        # Keep bottom-anchored groups aligned after changing the overall height.
        offsets["wheel"] += delta
        offsets["aspect_grid"] += delta
        offsets["aspect_list"] += delta
        offsets["lunar_phase"] += delta
        offsets["bottom_left"] += delta
        self._vertical_offsets = offsets

    def _apply_synastry_height_adjustment(
        self,
        *,
        active_points_count: int,
        offsets: dict[str, float],
        minimum_height: int,
    ) -> None:
        """Specialised dynamic height handling for Synastry charts.

        With the planet grids locked to a single column, every additional active
        point extends multiple tables vertically (planets, houses, comparisons).
        We therefore scale the height using the actual line spacing used by those
        tables (≈14px) and keep the bottom anchored elements aligned.
        """
        base_rows = 14  # Up to 16 active points fit without extra height
        extra_rows = max(active_points_count - base_rows, 0)

        synastry_row_height = 15
        comparison_padding_per_row = 4  # Keeps house comparison grids within view.
        extra_height = extra_rows * (synastry_row_height + comparison_padding_per_row)

        self.height = max(self.height, minimum_height + extra_height)

        delta_height = max(self.height - minimum_height, 0)

        # Move title up for synastry charts
        offsets["title"] = -10

        offsets["wheel"] += delta_height
        offsets["aspect_grid"] += delta_height
        offsets["aspect_list"] += delta_height
        offsets["lunar_phase"] += delta_height
        offsets["bottom_left"] += delta_height

        row_height_ratio = synastry_row_height / max(self._ROW_HEIGHT, 1)
        synastry_top_shift_factor = max(
            self._TOP_SHIFT_FACTOR,
            int(ceil(self._TOP_SHIFT_FACTOR * row_height_ratio)),
        )
        shift = min(extra_rows * synastry_top_shift_factor, self._MAX_TOP_SHIFT)

        base_grid_padding = 36
        grid_padding_per_row = 6
        base_header_padding = 12
        header_padding_per_row = 4
        min_title_to_grid_gap = 36

        grid_shift = shift + base_grid_padding + (extra_rows * grid_padding_per_row)
        grid_shift = min(grid_shift, shift + self._MAX_TOP_SHIFT)

        top_shift = (shift // 2) + base_header_padding + (extra_rows * header_padding_per_row)

        max_allowed_shift = shift + self._MAX_TOP_SHIFT
        missing_gap = min_title_to_grid_gap - (grid_shift - top_shift)
        grid_shift = min(grid_shift + missing_gap, max_allowed_shift)
        if grid_shift - top_shift < min_title_to_grid_gap:
            top_shift = max(0, grid_shift - min_title_to_grid_gap)

        offsets["grid"] += grid_shift
        offsets["title"] += top_shift
        offsets["elements"] += top_shift
        offsets["qualities"] += top_shift

        self._vertical_offsets = offsets

    def _collect_subject_points(
        self,
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        point_attribute_names: list[str],
    ) -> list[KerykeionPointModel]:
        """Collect ordered active celestial points for a subject."""

        collected: list[KerykeionPointModel] = []

        for raw_name in point_attribute_names:
            attr_name = raw_name if hasattr(subject, raw_name) else raw_name.lower()
            point = getattr(subject, attr_name, None)
            if point is None:
                continue
            collected.append(point)

        return collected

    def _apply_house_comparison_width_override(self) -> None:
        """Shrink chart width when the optional house comparison grid is hidden."""
        if self.show_house_position_comparison or self.show_cusp_position_comparison:
            return

        if self.chart_type == "Synastry":
            self.width = self._DEFAULT_FULL_WIDTH
        elif self.chart_type == "DualReturnChart":
            self.width = (
                self._DEFAULT_FULL_WIDTH_WITH_TABLE
                if self.double_chart_aspect_grid_type == "table"
                else self._DEFAULT_FULL_WIDTH
            )
        elif self.chart_type == "Transit":
            # Transit charts already use the compact width unless the aspect grid table is requested.
            self.width = (
                self._DEFAULT_FULL_WIDTH_WITH_TABLE
                if self.double_chart_aspect_grid_type == "table"
                else self._DEFAULT_FULL_WIDTH
            )

    def _dynamic_viewbox(self) -> str:
        """Return the viewBox string based on current width/height with vertical padding."""
        min_y = -self._VERTICAL_PADDING_TOP
        viewbox_height = int(self.height) + self._VERTICAL_PADDING_TOP + self._VERTICAL_PADDING_BOTTOM
        return f"0 {min_y} {int(self.width)} {viewbox_height}"

    def _wheel_only_viewbox(self, margin: int = 25) -> str:
        """Return a tight viewBox for the wheel-only template.

        The wheel is drawn inside a group translated by (100, 50) and has
        diameter 2 * main_radius. We add a small margin around it.
        """
        left = 100 - margin
        top = 50 - margin
        width = (2 * self.main_radius) + (2 * margin)
        height = (2 * self.main_radius) + (2 * margin)
        return f"{left} {top} {width} {height}"

    def _grid_only_viewbox(self, margin: int = 10) -> str:
        """Compute a tight viewBox for the Aspect Grid Only SVG.

        The grid is rendered using fixed origins and box size:
        - For Transit/Synastry/DualReturn charts, `draw_transit_aspect_grid`
          uses `x_indent=50`, `y_indent=250`, `box_size=14` and draws:
            • a header row to the right of `x_indent`
            • a left header column at `x_indent - box_size`
            • an NxN grid of cells above `y_indent`

        - For Natal/Composite/SingleReturn charts, `draw_aspect_grid` uses
          `x_start=50`, `y_start=250`, `box_size=14` and draws a triangular grid
          that extends to the right (x) and upwards (y).

        This function mirrors that geometry to return a snug viewBox around the
        content, with a small configurable `margin`.

        Args:
            margin: Extra pixels to add on each side of the computed bounds.

        Returns:
            A string "minX minY width height" suitable for the SVG `viewBox`.
        """
        # Must match defaults used in the renderers
        x0 = 50
        y0 = 250
        box = 14

        n = max(len([p for p in self.available_planets_setting if p.get("is_active")]), 1)

        if self.chart_type in ("Transit", "Synastry", "DualReturnChart"):
            # Full N×N grid
            left = (x0 - box) - margin
            top = (y0 - box * n) - margin
            right = (x0 + box * n) + margin
            bottom = (y0 + box) + margin
        else:
            # Triangular grid (no extra left column)
            left = x0 - margin
            top = (y0 - box * n) - margin
            right = (x0 + box * n) + margin
            bottom = (y0 + box) + margin

        width = max(1, int(right - left))
        height = max(1, int(bottom - top))

        return f"{int(left)} {int(top)} {width} {height}"

    def _estimate_required_width_full(self) -> int:
        """Estimate minimal width to contain all rendered groups for the full chart.

        The calculation is heuristic and mirrors the default x positions used in
        the SVG templates and drawing utilities. We keep a conservative padding.
        """
        # Wheel footprint (translate(100,50) + diameter of 2*radius)
        wheel_right = 100 + (2 * self.main_radius)
        extents: list[float] = [wheel_right]

        n_active = max(self._count_active_planets(), 1)

        # Common grids present on many chart types
        main_planet_grid_right = 645 + 80
        main_houses_grid_right = 750 + 120
        extents.extend([main_planet_grid_right, main_houses_grid_right])

        if self.chart_type in ("Natal", "Composite", "SingleReturnChart"):
            # Triangular aspect grid at x_start=540, width ~ 14 * n_active
            aspect_grid_right = 560 + 14 * n_active
            extents.append(aspect_grid_right)

        if self.chart_type in ("Transit", "Synastry", "DualReturnChart"):
            # Double-chart aspects placement
            if self.double_chart_aspect_grid_type == "list":
                total_aspects = len(self.aspects_list) if hasattr(self, "aspects_list") else 0
                columns = self._calculate_double_chart_aspect_columns(total_aspects, self.height)
                columns = max(columns, 1)
                aspect_list_right = 565 + (columns * self._ASPECT_LIST_COLUMN_WIDTH)
                extents.append(aspect_list_right)
            else:
                # Grid table placed with x_indent ~550, width ~ 14px per cell across n_active+1
                aspect_grid_table_right = 550 + (14 * (n_active + 1))
                extents.append(aspect_grid_table_right)

            # Secondary grids
            secondary_planet_grid_right = 910 + 80
            extents.append(secondary_planet_grid_right)

            if self.chart_type == "Synastry":
                # Secondary houses grid default x ~ 1015
                secondary_houses_grid_right = 1015 + 120
                extents.append(secondary_houses_grid_right)
                if (
                    self.show_house_position_comparison or self.show_cusp_position_comparison
                ) and self.second_obj is not None:
                    point_column_label = self._translate("point", "Point")
                    first_subject_label = self._truncate_name(self.first_obj.name, 8, "…", True)  # type: ignore[union-attr]
                    second_subject_label = self._truncate_name(self.second_obj.name, 8, "…", True)  # type: ignore[union-attr]

                    first_columns = [
                        f"{first_subject_label} {point_column_label}",
                        first_subject_label,
                        second_subject_label,
                    ]
                    second_columns = [
                        f"{second_subject_label} {point_column_label}",
                        second_subject_label,
                        first_subject_label,
                    ]

                    first_grid_width = self._estimate_house_comparison_grid_width(
                        column_labels=first_columns,
                        include_radix_column=True,
                        include_title=True,
                    )
                    second_grid_width = self._estimate_house_comparison_grid_width(
                        column_labels=second_columns,
                        include_radix_column=True,
                        include_title=False,
                    )

                    first_house_comparison_grid_right = 1090 + first_grid_width
                    second_house_comparison_grid_right = 1290 + second_grid_width
                    extents.extend([first_house_comparison_grid_right, second_house_comparison_grid_right])

                    if self.show_cusp_position_comparison:
                        # Cusp comparison block positioned to the right of both point grids.
                        # In Synastry we render two cusp grids side by side; reserve
                        # enough horizontal space for both tables plus a small gap.
                        max_house_comparison_right = max(
                            first_house_comparison_grid_right,
                            second_house_comparison_grid_right,
                        )
                        cusp_grid_width = 160.0
                        inter_cusp_gap = 0.0
                        cusp_block_width = (cusp_grid_width * 2.0) + inter_cusp_gap
                        # Place cusp block slightly to the right of the house comparison tables
                        # and ensure the overall SVG width comfortably contains it, including
                        # the rightmost text of the second cusp table.
                        extra_cusp_margin = 45.0
                        cusp_block_right = max_house_comparison_right + 50.0 + cusp_block_width + extra_cusp_margin
                        extents.append(cusp_block_right)

            if self.chart_type == "Transit":
                # House comparison grid at x ~ 1030
                if self.show_house_position_comparison or self.show_cusp_position_comparison:
                    transit_columns = [
                        self._translate("transit_point", "Transit Point"),
                        self._translate("house_position", "Natal House"),
                    ]
                    transit_grid_width = self._estimate_house_comparison_grid_width(
                        column_labels=transit_columns,
                        include_radix_column=False,
                        include_title=True,
                        minimum_width=170.0,
                    )
                    house_comparison_grid_right = 980 + transit_grid_width

                    if self.show_house_position_comparison:
                        # Classic layout: house comparison grid at x=980
                        extents.append(house_comparison_grid_right)

                    if self.show_cusp_position_comparison:
                        if self.show_house_position_comparison:
                            # Both grids visible: cusp table rendered to the right
                            cusp_block_width = 260.0
                            cusp_block_right = house_comparison_grid_right + 40.0 + cusp_block_width
                            extents.append(cusp_block_right)
                        else:
                            # Cusp-only: cusp table occupies the house grid slot at x=980
                            cusp_only_right = house_comparison_grid_right
                            extents.append(cusp_only_right)

            if self.chart_type == "DualReturnChart":
                # House and cusp comparison grids laid out similarly to Synastry.
                if self.show_house_position_comparison or self.show_cusp_position_comparison:
                    # Use localized labels for the natal subject and the return.
                    first_subject_label = self._translate("Natal", "Natal")
                    if isinstance(self.second_obj, PlanetReturnModel) and self.second_obj.return_type == "Solar":
                        second_subject_label = self._translate("solar_return", "Solar Return")
                    else:
                        second_subject_label = self._translate("lunar_return", "Lunar Return")
                    point_column_label = self._translate("point", "Point")

                    first_columns = [
                        f"{first_subject_label} {point_column_label}",
                        first_subject_label,
                        second_subject_label,
                    ]
                    second_columns = [
                        f"{second_subject_label} {point_column_label}",
                        second_subject_label,
                        first_subject_label,
                    ]

                    first_grid_width = self._estimate_house_comparison_grid_width(
                        column_labels=first_columns,
                        include_radix_column=True,
                        include_title=True,
                    )
                    second_grid_width = self._estimate_house_comparison_grid_width(
                        column_labels=second_columns,
                        include_radix_column=True,
                        include_title=False,
                    )

                    first_house_comparison_grid_right = 1090 + first_grid_width
                    second_house_comparison_grid_right = 1290 + second_grid_width
                    extents.extend([first_house_comparison_grid_right, second_house_comparison_grid_right])

                    if self.show_cusp_position_comparison:
                        # Cusp comparison block positioned to the right of both house grids.
                        max_house_comparison_right = max(
                            first_house_comparison_grid_right,
                            second_house_comparison_grid_right,
                        )
                        cusp_grid_width = 160.0
                        inter_cusp_gap = 0.0
                        cusp_block_width = (cusp_grid_width * 2.0) + inter_cusp_gap
                        extra_cusp_margin = 45.0
                        cusp_block_right = max_house_comparison_right + 50.0 + cusp_block_width + extra_cusp_margin
                        extents.append(cusp_block_right)

        # Conservative safety padding
        return int(max(extents) + self._padding)

    def _calculate_double_chart_aspect_columns(
        self,
        total_aspects: int,
        chart_height: Optional[Union[int, float]],
    ) -> int:
        """Return how many columns the double-chart aspect list needs.

        The first 11 columns follow the legacy 14-rows layout. Starting from the
        12th column we can fit more rows thanks to the taller chart height that
        gets computed earlier, so we re-use the same capacity as the SVG builder.
        """
        if total_aspects <= 0:
            return 0

        per_column = self._ASPECT_LIST_ASPECTS_PER_COLUMN
        extended_start = 10  # 0-based index where tall columns begin
        base_capacity = per_column * extended_start

        full_height_capacity = self._calculate_full_height_column_capacity(chart_height)

        if total_aspects <= base_capacity:
            return ceil(total_aspects / per_column)

        remaining = max(total_aspects - base_capacity, 0)
        extra_columns = ceil(remaining / full_height_capacity) if remaining > 0 else 0
        return extended_start + extra_columns

    def _calculate_full_height_column_capacity(
        self,
        chart_height: Optional[Union[int, float]],
    ) -> int:
        """Compute the row capacity for columns that use the tall layout."""
        per_column = self._ASPECT_LIST_ASPECTS_PER_COLUMN

        if chart_height is None:
            return per_column

        translate_y = 273
        bottom_padding = 40
        title_clearance = 18
        line_height = 14
        baseline_index = per_column - 1
        top_limit_index = ceil((-translate_y + title_clearance) / line_height)
        max_capacity_by_top = baseline_index - top_limit_index + 1

        available_height = max(chart_height - translate_y - bottom_padding, line_height)
        allowed_capacity = max(per_column, int(available_height // line_height))

        # Respect both the physical height of the SVG and the visual limit
        # imposed by the title area.
        return max(per_column, min(allowed_capacity, max_capacity_by_top))

    def _estimate_text_width(self, text: str, font_size: float = 12) -> float:
        """Very rough text width estimation in pixels based on font size."""
        if not text:
            return 0.0
        average_char_width = float(font_size) * 0.7
        return max(float(font_size), len(text) * average_char_width)

    def _get_active_point_display_names(self) -> list[str]:
        """Return localized labels for the currently active celestial points."""
        language_map = {}
        fallback_map = {}

        if hasattr(self, "_language_model"):
            language_map = self._language_model.celestial_points.model_dump()
        if hasattr(self, "_fallback_language_model"):
            fallback_map = self._fallback_language_model.celestial_points.model_dump()

        display_names: list[str] = []
        for point in self.active_points:
            key = str(point)
            label = language_map.get(key) or fallback_map.get(key) or key
            display_names.append(str(label))
        return display_names

    def _estimate_house_comparison_grid_width(
        self,
        *,
        column_labels: Sequence[str],
        include_radix_column: bool,
        include_title: bool,
        minimum_width: float = 250.0,
    ) -> int:
        """
        Approximate the rendered width for a house comparison grid in the current locale.

        Args:
            column_labels: Ordered labels for the header row.
            include_radix_column: Whether a third numeric column is rendered.
            include_title: Include the localized title in the width estimation.
            minimum_width: Absolute lower bound to prevent extreme shrinking.
        """
        font_size_body = 10
        font_size_title = 14
        minimum_grid_width = float(minimum_width)

        active_names = self._get_active_point_display_names()
        max_name_width = max(
            (self._estimate_text_width(name, font_size_body) for name in active_names),
            default=self._estimate_text_width("Sun", font_size_body),
        )
        width_candidates: list[float] = []

        name_start = 15
        width_candidates.append(name_start + max_name_width)

        value_offsets = [90]
        if include_radix_column:
            value_offsets.append(140)
        value_samples = ("12", "-", "0")
        max_value_width = max((self._estimate_text_width(sample, font_size_body) for sample in value_samples))
        for offset in value_offsets:
            width_candidates.append(offset + max_value_width)

        header_offsets = [0, 77]
        if include_radix_column:
            header_offsets.append(132)
        for idx, offset in enumerate(header_offsets):
            label = column_labels[idx] if idx < len(column_labels) else ""
            if not label:
                continue
            width_candidates.append(offset + self._estimate_text_width(label, font_size_body))

        if include_title:
            title_label = self._translate("house_position_comparison", "House Position Comparison")
            width_candidates.append(self._estimate_text_width(title_label, font_size_title))

        grid_width = max(width_candidates, default=minimum_grid_width)
        return int(max(grid_width, minimum_grid_width))

    def _minimum_width_for_chart_type(self) -> int:
        """Baseline width to avoid compressing core groups too tightly."""
        wheel_right = 100 + (2 * self.main_radius)
        baseline = wheel_right + self._padding

        if self.chart_type in ("Natal", "Composite", "SingleReturnChart"):
            return max(int(baseline), self._DEFAULT_NATAL_WIDTH)
        if self.chart_type == "Synastry":
            return max(int(baseline), self._DEFAULT_SYNASTRY_WIDTH // 2)
        if self.chart_type == "DualReturnChart":
            return max(int(baseline), self._DEFAULT_ULTRA_WIDE_WIDTH // 2)
        if self.chart_type == "Transit":
            return max(int(baseline), 450)
        return max(int(baseline), self._DEFAULT_NATAL_WIDTH)

    def _update_width_to_content(self) -> None:
        """Resize the chart width so the farthest element fits comfortably."""
        try:
            required_width = self._estimate_required_width_full()
        except Exception as e:
            logger.debug("Auto-size width calculation failed: %s", e)
            return

        minimum_width = self._minimum_width_for_chart_type()
        self.width = max(required_width, minimum_width)

    def _get_location_info(self) -> tuple[str, float, float]:
        """
        Determine location information based on chart type and subjects.

        Returns:
            tuple: (location_name, latitude, longitude)
        """
        if self.chart_type == "Composite":
            # For composite charts, use average location of the two composite subjects
            if isinstance(self.first_obj, CompositeSubjectModel):
                location_name = ""
                latitude = (self.first_obj.first_subject.lat + self.first_obj.second_subject.lat) / 2
                longitude = (self.first_obj.first_subject.lng + self.first_obj.second_subject.lng) / 2
            else:
                # Fallback to first subject location
                location_name = self.first_obj.city or "Unknown"
                latitude = self.first_obj.lat or 0.0
                longitude = self.first_obj.lng or 0.0
        elif self.chart_type in ["Transit", "DualReturnChart"] and self.second_obj:
            # Use location from the second subject (transit/return)
            location_name = self.second_obj.city or "Unknown"
            latitude = self.second_obj.lat or 0.0
            longitude = self.second_obj.lng or 0.0
        else:
            # Use location from the first subject
            location_name = self.first_obj.city or "Unknown"
            latitude = self.first_obj.lat or 0.0
            longitude = self.first_obj.lng or 0.0

        return location_name, latitude, longitude

    def set_up_theme(self, theme: Union[KerykeionChartTheme, None] = None) -> None:
        """
        Load and apply a CSS theme for the chart visualization.

        Args:
            theme (KerykeionChartTheme or None): Name of the theme to apply. If None, no CSS is applied.
        """
        if theme is None:
            self.color_style_tag = ""
            return

        theme_dir = Path(__file__).parent / "themes"

        with open(theme_dir / f"{theme}.css", "r") as f:
            self.color_style_tag = f.read()

    def _load_language_settings(
        self,
        language_pack: Optional[Mapping[str, Any]],
    ) -> None:
        """Resolve language models for the requested chart language."""
        overrides = {self.chart_language: dict(language_pack)} if language_pack else None
        languages = load_language_settings(overrides)  # type: ignore[arg-type]

        fallback_data = languages.get("EN")
        if fallback_data is None:
            raise KerykeionException("English translations are missing from LANGUAGE_SETTINGS.")

        base_data = languages.get(self.chart_language, fallback_data)
        selected_model = KerykeionLanguageModel(**base_data)
        fallback_model = KerykeionLanguageModel(**fallback_data)

        self._fallback_language_model = fallback_model
        self._language_model = selected_model
        self._fallback_language_dict = fallback_model.model_dump()
        self._language_dict = selected_model.model_dump()
        self.language_settings = self._language_dict  # Backward compatibility

    def _translate(self, key: str, default: Any) -> Any:
        fallback_value = get_translations(key, default, language_dict=self._fallback_language_dict)
        return get_translations(key, fallback_value, language_dict=self._language_dict)

    def _get_zodiac_info(self) -> str:
        """
        Generate the zodiac/ayanamsa info string for display in bottom_left section.

        Returns:
            str: Localized zodiac type description (Tropical or Ayanamsa mode).
        """
        if self.first_obj.zodiac_type == "Tropical":
            return f"{self._translate('zodiac', 'Zodiac')}: {self._translate('tropical', 'Tropical')}"
        else:
            mode_const = "SIDM_" + self.first_obj.sidereal_mode  # type: ignore
            mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
            return f"{self._translate('ayanamsa', 'Ayanamsa')}: {mode_name}"

    # =========================================================================
    # TEMPLATE HELPER METHODS
    # =========================================================================
    # These methods populate specific sections of the template_dict.
    # They are designed to reduce code duplication while maintaining
    # clear separation between chart types.
    # =========================================================================

    def _setup_radix_circles(self, template_dict: dict) -> None:
        """
        Populate template_dict with radix-style circle elements.

        Used by single-wheel charts (Natal, Composite, SingleReturnChart) that display
        planets inside the zodiac wheel without a transit ring.

        The radix layout uses:
        - No transit ring (empty string)
        - Degree ring with 1-degree tick marks
        - Three concentric circles for zodiac signs, houses, and aspects

        Args:
            template_dict: Dictionary to populate with circle SVG elements.
        """
        template_dict["transitRing"] = ""
        template_dict["degreeRing"] = draw_degree_ring(
            self.main_radius,
            self.first_circle_radius,
            self.first_obj.seventh_house.abs_pos,
            self.chart_colors_settings["paper_0"],
        )
        template_dict["background_circle"] = draw_background_circle(
            self.main_radius,
            self.chart_colors_settings["paper_1"],
            self.chart_colors_settings["paper_1"],
        )
        template_dict["first_circle"] = draw_first_circle(
            self.main_radius,
            self.chart_colors_settings["zodiac_radix_ring_2"],
            self.chart_type,
            self.first_circle_radius,
        )
        template_dict["second_circle"] = draw_second_circle(
            self.main_radius,
            self.chart_colors_settings["zodiac_radix_ring_1"],
            self.chart_colors_settings["paper_1"],
            self.chart_type,
            self.second_circle_radius,
        )
        template_dict["third_circle"] = draw_third_circle(
            self.main_radius,
            self.chart_colors_settings["zodiac_radix_ring_0"],
            self.chart_colors_settings["paper_1"],
            self.chart_type,
            self.third_circle_radius,
        )

    def _setup_transit_circles(self, template_dict: dict) -> None:
        """
        Populate template_dict with transit-style circle elements.

        Used by dual-wheel charts (Transit, Synastry, DualReturnChart) that display
        two sets of planets with a transit ring for the outer wheel.

        The transit layout uses:
        - Outer transit ring for secondary subject planets
        - Degree steps ring with tick marks
        - Three concentric circles with transit color scheme

        Args:
            template_dict: Dictionary to populate with circle SVG elements.
        """
        template_dict["transitRing"] = draw_transit_ring(
            self.main_radius,
            self.chart_colors_settings["paper_1"],
            self.chart_colors_settings["zodiac_transit_ring_3"],
        )
        template_dict["degreeRing"] = draw_transit_ring_degree_steps(
            self.main_radius, self.first_obj.seventh_house.abs_pos
        )
        template_dict["background_circle"] = draw_background_circle(
            self.main_radius,
            self.chart_colors_settings["paper_1"],
            self.chart_colors_settings["paper_1"],
        )
        template_dict["first_circle"] = draw_first_circle(
            self.main_radius,
            self.chart_colors_settings["zodiac_transit_ring_2"],
            self.chart_type,
        )
        template_dict["second_circle"] = draw_second_circle(
            self.main_radius,
            self.chart_colors_settings["zodiac_transit_ring_1"],
            self.chart_colors_settings["paper_1"],
            self.chart_type,
        )
        template_dict["third_circle"] = draw_third_circle(
            self.main_radius,
            self.chart_colors_settings["zodiac_transit_ring_0"],
            self.chart_colors_settings["paper_1"],
            self.chart_type,
            self.third_circle_radius,
        )

    def _setup_single_chart_aspects(self, template_dict: dict) -> None:
        """
        Populate template_dict with aspect elements for single-wheel charts.

        Generates the triangular aspect grid and aspect lines for charts with
        only one subject (Natal, Composite, SingleReturnChart).

        Args:
            template_dict: Dictionary to populate with aspect SVG elements.
        """
        template_dict["makeDoubleChartAspectList"] = ""
        template_dict["makeAspectGrid"] = draw_aspect_grid(
            self.chart_colors_settings["paper_0"],
            self.available_planets_setting,
            self.aspects_list,
        )
        template_dict["makeAspects"] = self._draw_all_aspects_lines(
            self.main_radius, self.main_radius - self.third_circle_radius
        )

    def _setup_dual_chart_aspects(self, template_dict: dict, aspect_title: str) -> None:
        """
        Populate template_dict with aspect elements for dual-wheel charts.

        Generates either an aspect list or aspect grid based on configuration,
        plus aspect lines for charts with two subjects (Transit, Synastry, DualReturnChart).

        Args:
            template_dict: Dictionary to populate with aspect SVG elements.
            aspect_title: Title text to display above the aspect list.
        """
        if self.double_chart_aspect_grid_type == "list":
            template_dict["makeAspectGrid"] = ""
            template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                aspect_title,
                self.aspects_list,
                self.planets_settings,
                self.aspects_settings,
                chart_height=self.height,
            )
        else:
            template_dict["makeAspectGrid"] = ""
            template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self.available_planets_setting,
                self.aspects_list,
                600,
                520,
            )
        template_dict["makeAspects"] = self._draw_all_aspects_lines(self.main_radius, self.main_radius - 160)

    def _setup_single_wheel_houses(self, template_dict: dict, houses_list: list) -> None:
        """
        Populate template_dict with house cusp drawing for single-wheel charts.

        Draws house cusps and numbers for charts with only one subject.
        Uses the radix house cusp color scheme.

        The c1/c3 parameters control where house cusp lines start and end:
        - c1 (first_circle_radius): outer boundary offset from edge
        - c3 (third_circle_radius): inner boundary offset from edge

        Args:
            template_dict: Dictionary to populate with house SVG elements.
            houses_list: List of house data from the subject.
        """
        template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
            r=self.main_radius,
            first_subject_houses_list=houses_list,
            standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
            first_house_color=self.planets_settings[12]["color"],  # ASC color
            tenth_house_color=self.planets_settings[13]["color"],  # MC color
            seventh_house_color=self.planets_settings[14]["color"],  # DSC color
            fourth_house_color=self.planets_settings[15]["color"],  # IC color
            c1=self.first_circle_radius,  # Outer boundary for cusp lines
            c3=self.third_circle_radius,  # Inner boundary for cusp lines
            chart_type=self.chart_type,
            external_view=self.external_view,
        )

    def _setup_dual_wheel_houses(self, template_dict: dict, first_houses_list: list, second_houses_list: list) -> None:
        """
        Populate template_dict with house cusp drawing for dual-wheel charts.

        Draws house cusps for both subjects with radix and transit color schemes.

        The c1/c3 parameters control where house cusp lines start and end:
        - c1 (first_circle_radius): outer boundary offset from edge
        - c3 (third_circle_radius): inner boundary offset from edge

        Args:
            template_dict: Dictionary to populate with house SVG elements.
            first_houses_list: List of house data from the primary subject.
            second_houses_list: List of house data from the secondary subject.
        """
        template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
            r=self.main_radius,
            first_subject_houses_list=first_houses_list,
            standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
            first_house_color=self.planets_settings[12]["color"],  # ASC color
            tenth_house_color=self.planets_settings[13]["color"],  # MC color
            seventh_house_color=self.planets_settings[14]["color"],  # DSC color
            fourth_house_color=self.planets_settings[15]["color"],  # IC color
            c1=self.first_circle_radius,  # Outer boundary for cusp lines
            c3=self.third_circle_radius,  # Inner boundary for cusp lines
            chart_type=self.chart_type,
            external_view=self.external_view,
            second_subject_houses_list=second_houses_list,
            transit_house_cusp_color=self.chart_colors_settings["houses_transit_line"],
        )

    def _setup_single_wheel_planets(self, template_dict: dict) -> None:
        """
        Populate template_dict with planet drawing for single-wheel charts.

        Draws planet symbols and degree indicators for charts with only one subject.

        Args:
            template_dict: Dictionary to populate with planet SVG elements.
        """
        template_dict["makePlanets"] = draw_planets(
            available_planets_setting=self.available_planets_setting,
            chart_type=self.chart_type,
            radius=self.main_radius,
            available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
            third_circle_radius=self.third_circle_radius,
            main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
            main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
            external_view=self.external_view,
            first_circle_radius=self.first_circle_radius,
            show_degree_indicators=self.show_degree_indicators,
        )

    def _setup_dual_wheel_planets(self, template_dict: dict) -> None:
        """
        Populate template_dict with planet drawing for dual-wheel charts.

        Draws planet symbols for both subjects (inner and outer wheel).

        Args:
            template_dict: Dictionary to populate with planet SVG elements.
        """
        template_dict["makePlanets"] = draw_planets(
            available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
            available_planets_setting=self.available_planets_setting,
            second_subject_available_kerykeion_celestial_points=self.second_subject_celestial_points,
            radius=self.main_radius,
            main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
            main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
            chart_type=self.chart_type,
            third_circle_radius=self.third_circle_radius,
            external_view=self.external_view,
            second_circle_radius=self.second_circle_radius,
            show_degree_indicators=self.show_degree_indicators,
        )

    def _setup_lunar_phase(self, template_dict: dict, subject, latitude: float) -> None:
        """
        Populate template_dict with lunar phase visualization if available.

        Draws the moon phase icon when lunar phase data is present on the subject.

        Args:
            template_dict: Dictionary to populate with lunar phase SVG elements.
            subject: The subject object that may contain lunar_phase data.
            latitude: Geographic latitude for moon phase calculation.
        """
        if subject.lunar_phase is not None:
            template_dict["makeLunarPhase"] = makeLunarPhase(subject.lunar_phase["degrees_between_s_m"], latitude)
        else:
            template_dict["makeLunarPhase"] = ""

    def _setup_main_houses_grid(self, template_dict: dict, houses_list: list) -> None:
        """
        Populate template_dict with the main houses grid table.

        Creates the tabular display of house cusps for the primary subject.

        Args:
            template_dict: Dictionary to populate with grid SVG elements.
            houses_list: List of house data from the subject.
        """
        template_dict["makeMainHousesGrid"] = draw_main_house_grid(
            main_subject_houses_list=houses_list,
            text_color=self.chart_colors_settings["paper_0"],
            house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
        )

    def _setup_main_planet_grid(self, template_dict: dict, subject_name: str, title: str = "") -> None:
        """
        Populate template_dict with the main planet grid table.

        Creates the tabular display of planet positions for the primary subject.

        Args:
            template_dict: Dictionary to populate with grid SVG elements.
            subject_name: Name to display in the grid header.
            title: Optional title prefix (e.g., "Points for").
        """
        template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
            planets_and_houses_grid_title=title,
            subject_name=subject_name,
            available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
            chart_type=self.chart_type,
            text_color=self.chart_colors_settings["paper_0"],
            celestial_point_language=self._language_model.celestial_points,
        )

    def _setup_secondary_planet_grid(self, template_dict: dict, subject_name: str, title: str = "") -> None:
        """
        Populate template_dict with the secondary planet grid table.

        Creates the tabular display of planet positions for the secondary subject
        in dual-wheel charts.

        Args:
            template_dict: Dictionary to populate with grid SVG elements.
            subject_name: Name to display in the grid header.
            title: Optional title prefix.
        """
        template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
            planets_and_houses_grid_title=title,
            second_subject_name=subject_name,
            second_subject_available_kerykeion_celestial_points=self.second_subject_celestial_points,
            chart_type=self.chart_type,
            text_color=self.chart_colors_settings["paper_0"],
            celestial_point_language=self._language_model.celestial_points,
        )

    def _setup_secondary_houses_grid(self, template_dict: dict, houses_list: list) -> None:
        """
        Populate template_dict with the secondary houses grid table.

        Creates the tabular display of house cusps for the secondary subject
        in dual-wheel charts.

        Args:
            template_dict: Dictionary to populate with grid SVG elements.
            houses_list: List of house data from the secondary subject.
        """
        template_dict["makeSecondaryHousesGrid"] = draw_secondary_house_grid(
            secondary_subject_houses_list=houses_list,
            text_color=self.chart_colors_settings["paper_0"],
            house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
        )

    def _clear_element_quality_strings(self, template_dict: dict) -> None:
        """
        Clear element and quality percentage strings from template_dict.

        Used by Transit charts which don't display element/quality distributions.

        Args:
            template_dict: Dictionary to clear element/quality strings from.
        """
        template_dict["elements_string"] = ""
        template_dict["fire_string"] = ""
        template_dict["earth_string"] = ""
        template_dict["air_string"] = ""
        template_dict["water_string"] = ""
        template_dict["qualities_string"] = ""
        template_dict["cardinal_string"] = ""
        template_dict["fixed_string"] = ""
        template_dict["mutable_string"] = ""

    def _get_perspective_string(self, subject) -> str:
        """
        Generate the localized perspective type string for a subject.

        Args:
            subject: The subject containing perspective_type attribute.

        Returns:
            str: Formatted perspective string (e.g., "Perspective: Geocentric").
        """
        perspective_key = subject.perspective_type.lower().replace(" ", "_")
        return (
            f"{self._translate('perspective_type', 'Perspective')}: "
            f"{self._translate(perspective_key, subject.perspective_type)}"
        )

    def _get_domification_string(self) -> str:
        """
        Generate the localized domification/house system string.

        Returns:
            str: Formatted domification string (e.g., "Domification: Placidus").
        """
        house_key = "houses_system_" + self.first_obj.houses_system_identifier
        return (
            f"{self._translate('domification', 'Domification')}: "
            f"{self._translate(house_key, self.first_obj.houses_system_name)}"
        )

    # =========================================================================
    # INFO SECTION HELPER METHODS
    # =========================================================================
    # These methods generate formatted strings for the top_left and bottom_left
    # info sections of the chart. They encapsulate common formatting patterns
    # and handle translation of labels.
    # =========================================================================

    def _format_latitude_string(
        self,
        latitude: float,
        use_abbreviations: bool = False,
    ) -> str:
        """
        Format a latitude value as a human-readable string with direction.

        Args:
            latitude: The latitude value in degrees.
            use_abbreviations: If True, use "N"/"S" instead of "North"/"South".

        Returns:
            Formatted string like "41° 52' 12\" North" or "41° 52' 12\" N".
        """
        if use_abbreviations:
            north = self._translate("north_letter", "N")
            south = self._translate("south_letter", "S")
        else:
            north = self._translate("north", "North")
            south = self._translate("south", "South")
        return convert_latitude_coordinate_to_string(latitude, north, south)

    def _format_longitude_string(
        self,
        longitude: float,
        use_abbreviations: bool = False,
    ) -> str:
        """
        Format a longitude value as a human-readable string with direction.

        Args:
            longitude: The longitude value in degrees.
            use_abbreviations: If True, use "E"/"W" instead of "East"/"West".

        Returns:
            Formatted string like "12° 29' 36\" East" or "12° 29' 36\" E".
        """
        if use_abbreviations:
            east = self._translate("east_letter", "E")
            west = self._translate("west_letter", "W")
        else:
            east = self._translate("east", "East")
            west = self._translate("west", "West")
        return convert_longitude_coordinate_to_string(longitude, east, west)

    def _format_lunation_day_string(self, subject: FirstSubjectType) -> str:
        """
        Format the lunation day string for display in bottom_left section.

        Args:
            subject: The subject containing lunar_phase data.

        Returns:
            Formatted string like "Lunation Day: 15" or empty string if no lunar phase.
        """
        if subject.lunar_phase is None:
            return ""
        return f"{self._translate('lunation_day', 'Lunation Day')}: {subject.lunar_phase.get('moon_phase', '')}"

    def _format_lunar_phase_name_string(self, subject: FirstSubjectType) -> str:
        """
        Format the lunar phase name string for display in bottom_left section.

        Args:
            subject: The subject containing lunar_phase data.

        Returns:
            Formatted string like "Lunar Phase: Full Moon" or empty string if no lunar phase.
        """
        if subject.lunar_phase is None:
            return ""
        phase_name = subject.lunar_phase.moon_phase_name
        phase_key = phase_name.lower().replace(" ", "_")
        return f"{self._translate('lunar_phase', 'Lunar Phase')}: {self._translate(phase_key, phase_name)}"

    def _format_houses_system_string(self, subject: FirstSubjectType) -> str:
        """
        Format the house system string for display (compact version without "Domification:" label).

        Args:
            subject: The subject containing house system information.

        Returns:
            Formatted string like "Placidus Houses".
        """
        house_key = "houses_system_" + subject.houses_system_identifier
        return f"{self._translate(house_key, subject.houses_system_name)} {self._translate('houses', 'Houses')}"

    def _apply_svg_post_processing(self, template: str, minify: bool, remove_css_variables: bool) -> str:
        """
        Apply CSS inlining and minification to SVG template.

        Args:
            template (str): The raw SVG template string.
            minify (bool): Remove whitespace and quotes for compactness.
            remove_css_variables (bool): Embed CSS variable definitions inline.

        Returns:
            str: The processed SVG template.
        """
        if remove_css_variables:
            template = inline_css_variables_in_svg(template)

        if minify:
            template = (
                scourString(template)
                .replace('"', "'")
                .replace("\n", "")
                .replace("\t", "")
                .replace("    ", "")
                .replace("  ", "")
            )
        else:
            template = template.replace('"', "'")

        return template

    def _draw_zodiac_circle_slices(self, r):
        """
        Draw zodiac circle slices for each sign.

        Args:
            r (float): Outer radius of the zodiac ring.

        Returns:
            str: Concatenated SVG elements for zodiac slices.
        """
        sings = get_args(Sign)
        output = ""
        for i, sing in enumerate(sings):
            output += draw_zodiac_slice(
                c1=self.first_circle_radius,
                chart_type=self.chart_type,
                seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                num=i,
                r=r,
                style=f"fill:{self.chart_colors_settings[f'zodiac_bg_{i}']}; fill-opacity: 0.5;",
                type=sing,
            )

        return output

    def _draw_all_aspects_lines(self, r, ar):
        """
        Render SVG lines for all aspects in the chart.

        Args:
            r (float): Radius at which aspect lines originate.
            ar (float): Radius at which aspect lines terminate.

        Returns:
            str: SVG markup for all aspect lines.
        """
        out = ""
        # Track rendered icon positions (x, y, aspect_degrees) to avoid overlapping symbols of same type
        rendered_icon_positions: list[tuple[float, float, int]] = []
        for aspect in self.aspects_list:
            aspect_name = aspect["aspect"]
            aspect_color = next((a["color"] for a in self.aspects_settings if a["name"] == aspect_name), None)
            if aspect_color:
                out += draw_aspect_line(
                    r=r,
                    ar=ar,
                    aspect=aspect,
                    color=aspect_color,
                    seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                    show_aspect_icon=self.show_aspect_icons,
                    rendered_icon_positions=rendered_icon_positions,
                )
        return out

    def _truncate_name(
        self, name: str, max_length: int = 50, ellipsis_symbol: str = "…", truncate_at_space: bool = False
    ) -> str:
        """
        Truncate a name if it's too long, preserving readability.

        Args:
            name (str): The name to truncate
            max_length (int): Maximum allowed length

        Returns:
            str: Truncated name with ellipsis if needed
        """
        if truncate_at_space:
            name = name.split(" ")[0]

        if len(name) <= max_length:
            return name

        return name[: max_length - 1] + ellipsis_symbol

    def _get_chart_title(self, custom_title_override: Union[str, None] = None) -> str:
        """
        Generate the chart title based on chart type and custom title settings.

        If a custom title is provided, it will be used. Otherwise, generates the
        appropriate default title based on the chart type and subjects.

        Args:
            custom_title_override (str | None): Explicit override supplied at render time.

        Returns:
            str: The chart title to display (max ~40 characters).
        """
        # If a kwarg override is provided, use it
        if custom_title_override is not None:
            return custom_title_override

        # If custom title is provided at initialization, use it
        if self.custom_title is not None:
            return self.custom_title

        # Generate default title based on chart type
        if self.chart_type == "Natal":
            natal_label = self._translate("birth_chart", "Natal")
            truncated_name = self._truncate_name(self.first_obj.name)
            return f"{truncated_name} - {natal_label}"

        elif self.chart_type == "Composite":
            composite_label = self._translate("composite_chart", "Composite")
            and_word = self._translate("and_word", "&")
            name1 = self._truncate_name(self.first_obj.first_subject.name)  # type: ignore
            name2 = self._truncate_name(self.first_obj.second_subject.name)  # type: ignore
            return f"{composite_label}: {name1} {and_word} {name2}"

        elif self.chart_type == "Transit":
            transit_label = self._translate("transits", "Transits")
            date_obj = datetime.fromisoformat(self.second_obj.iso_formatted_local_datetime)  # type: ignore
            date_str = date_obj.strftime("%Y-%m-%d")
            truncated_name = self._truncate_name(self.first_obj.name)
            return f"{truncated_name} - {transit_label} {date_str}"

        elif self.chart_type == "Synastry":
            synastry_label = self._translate("synastry_chart", "Synastry")
            and_word = self._translate("and_word", "&")
            name1 = self._truncate_name(self.first_obj.name)
            name2 = self._truncate_name(self.second_obj.name)  # type: ignore
            return f"{synastry_label}: {name1} {and_word} {name2}"

        elif self.chart_type == "DualReturnChart":
            return_datetime = datetime.fromisoformat(self.second_obj.iso_formatted_local_datetime)  # type: ignore
            year = return_datetime.year
            month_year = return_datetime.strftime("%Y-%m")
            truncated_name = self._truncate_name(self.first_obj.name)
            if (
                self.second_obj is not None
                and isinstance(self.second_obj, PlanetReturnModel)
                and self.second_obj.return_type == "Solar"
            ):
                solar_label = self._translate("solar_return", "Solar")
                return f"{truncated_name} - {solar_label} {year}"
            else:
                lunar_label = self._translate("lunar_return", "Lunar")
                return f"{truncated_name} - {lunar_label} {month_year}"

        elif self.chart_type == "SingleReturnChart":
            return_datetime = datetime.fromisoformat(self.first_obj.iso_formatted_local_datetime)  # type: ignore
            year = return_datetime.year
            month_year = return_datetime.strftime("%Y-%m")
            truncated_name = self._truncate_name(self.first_obj.name)
            if isinstance(self.first_obj, PlanetReturnModel) and self.first_obj.return_type == "Solar":
                solar_label = self._translate("solar_return", "Solar")
                return f"{truncated_name} - {solar_label} {year}"
            else:
                lunar_label = self._translate("lunar_return", "Lunar")
                return f"{truncated_name} - {lunar_label} {month_year}"

        # Fallback for unknown chart types
        return self._truncate_name(self.first_obj.name)

    def _create_template_dictionary(self, *, custom_title: Union[str, None] = None) -> ChartTemplateModel:
        """
        Assemble chart data and rendering instructions into a template dictionary.

        Gathers styling, dimensions, and SVG fragments for chart components based on
        chart type and subjects.

        Args:
            custom_title (str | None): Optional runtime override for the chart title.

        Returns:
            ChartTemplateModel: Populated structure of template variables.
        """
        # Initialize template dictionary
        template_dict: dict = {}

        # -------------------------------------#
        #  COMMON SETTINGS FOR ALL CHART TYPES #
        # -------------------------------------#

        # ---------------------------------------------------------------------
        # STYLING: Theme CSS and basic canvas dimensions
        # ---------------------------------------------------------------------
        # The color_style_tag contains CSS that defines all color variables
        # used by the SVG elements. Chart dimensions set the viewBox.
        template_dict["color_style_tag"] = self.color_style_tag
        template_dict["chart_height"] = self.height
        template_dict["chart_width"] = self.width

        # ---------------------------------------------------------------------
        # LAYOUT: Vertical offsets for SVG group translations
        # ---------------------------------------------------------------------
        # These offsets are applied as transform="translate(x, y)" on SVG groups.
        # They are dynamically adjusted based on active celestial points count.
        offsets = self._vertical_offsets
        template_dict["full_wheel_translate_y"] = offsets["wheel"]
        template_dict["houses_and_planets_translate_y"] = offsets["grid"]
        template_dict["aspect_grid_translate_y"] = offsets["aspect_grid"]
        template_dict["aspect_list_translate_y"] = offsets["aspect_list"]
        template_dict["title_translate_y"] = offsets["title"]
        template_dict["elements_translate_y"] = offsets["elements"]
        template_dict["qualities_translate_y"] = offsets["qualities"]
        template_dict["lunar_phase_translate_y"] = offsets["lunar_phase"]
        template_dict["bottom_left_translate_y"] = offsets["bottom_left"]

        # ---------------------------------------------------------------------
        # COLORS: Paper, background, and transparency settings
        # ---------------------------------------------------------------------
        template_dict["paper_color_0"] = self.chart_colors_settings["paper_0"]

        # Background can be transparent for overlay/embedding use cases
        if self.transparent_background:
            template_dict["background_color"] = "transparent"
        else:
            template_dict["background_color"] = self.chart_colors_settings["paper_1"]

        # ---------------------------------------------------------------------
        # COLORS: Planet colors for all 42 possible celestial points
        # ---------------------------------------------------------------------
        # Initialize all slots with default black, then override with settings.
        # This ensures template substitution never fails on missing colors.
        default_color = "#000000"
        for i in range(42):  # Support all 42 celestial points (0-41)
            template_dict[f"planets_color_{i}"] = default_color

        for planet in self.planets_settings:
            planet_id = planet["id"]
            template_dict[f"planets_color_{planet_id}"] = planet["color"]

        # ---------------------------------------------------------------------
        # COLORS: Zodiac sign colors (12 signs)
        # ---------------------------------------------------------------------
        for i in range(12):
            template_dict[f"zodiac_color_{i}"] = self.chart_colors_settings[f"zodiac_icon_{i}"]

        # ---------------------------------------------------------------------
        # COLORS: Aspect orb colors (keyed by degree)
        # ---------------------------------------------------------------------
        for aspect in self.aspects_settings:
            template_dict[f"orb_color_{aspect['degree']}"] = aspect["color"]

        # ---------------------------------------------------------------------
        # SVG ELEMENTS: Zodiac circle slices (the colored background arcs)
        # ---------------------------------------------------------------------
        template_dict["makeZodiac"] = self._draw_zodiac_circle_slices(self.main_radius)

        # ---------------------------------------------------------------------
        # STATISTICS: Element distribution percentages
        # ---------------------------------------------------------------------
        # Elements represent the four classical elements: Fire, Earth, Air, Water.
        # Values are normalized to sum to 100% for display.
        total_elements = self.fire + self.water + self.earth + self.air
        element_values = {"fire": self.fire, "earth": self.earth, "air": self.air, "water": self.water}
        element_percentages = (
            distribute_percentages_to_100(element_values)
            if total_elements > 0
            else {"fire": 0, "earth": 0, "air": 0, "water": 0}
        )
        fire_percentage = element_percentages["fire"]
        earth_percentage = element_percentages["earth"]
        air_percentage = element_percentages["air"]
        water_percentage = element_percentages["water"]

        # Element Percentages
        template_dict["elements_string"] = f"{self._translate('elements', 'Elements')}:"
        template_dict["fire_string"] = f"{self._translate('fire', 'Fire')} {fire_percentage}%"
        template_dict["earth_string"] = f"{self._translate('earth', 'Earth')} {earth_percentage}%"
        template_dict["air_string"] = f"{self._translate('air', 'Air')} {air_percentage}%"
        template_dict["water_string"] = f"{self._translate('water', 'Water')} {water_percentage}%"

        # Qualities Percentages
        total_qualities = self.cardinal + self.fixed + self.mutable
        quality_values = {"cardinal": self.cardinal, "fixed": self.fixed, "mutable": self.mutable}
        quality_percentages = (
            distribute_percentages_to_100(quality_values)
            if total_qualities > 0
            else {"cardinal": 0, "fixed": 0, "mutable": 0}
        )
        cardinal_percentage = quality_percentages["cardinal"]
        fixed_percentage = quality_percentages["fixed"]
        mutable_percentage = quality_percentages["mutable"]

        template_dict["qualities_string"] = f"{self._translate('qualities', 'Qualities')}:"
        template_dict["cardinal_string"] = f"{self._translate('cardinal', 'Cardinal')} {cardinal_percentage}%"
        template_dict["fixed_string"] = f"{self._translate('fixed', 'Fixed')} {fixed_percentage}%"
        template_dict["mutable_string"] = f"{self._translate('mutable', 'Mutable')} {mutable_percentage}%"

        # Chart title
        template_dict["stringTitle"] = self._get_chart_title(custom_title_override=custom_title)

        # Set viewbox dynamically for all chart types
        template_dict["viewbox"] = self._dynamic_viewbox()

        # ------------------------------- #
        #  CHART TYPE SPECIFIC SETTINGS   #
        # ------------------------------- #
        # Delegate to the appropriate renderer based on chart type.
        # This uses the Strategy Pattern to separate chart-specific logic.
        renderer = get_chart_renderer(self.chart_type, self)
        renderer.render(template_dict)

        return ChartTemplateModel(**template_dict)

    def generate_svg_string(
        self, minify: bool = False, remove_css_variables=False, *, custom_title: Union[str, None] = None
    ) -> str:
        """
        Render the full chart SVG as a string.

        Reads the XML template, substitutes variables, and optionally inlines CSS
        variables and minifies the output.

        Args:
            minify (bool): Remove whitespace and quotes for compactness.
            remove_css_variables (bool): Embed CSS variable definitions.
            custom_title (str or None): Optional override for the SVG title.

        Returns:
            str: SVG markup as a string.
        """
        td = self._create_template_dictionary(custom_title=custom_title)

        DATA_DIR = Path(__file__).parent
        xml_svg = DATA_DIR / "templates" / "chart.xml"

        # read template
        with open(xml_svg, "r", encoding="utf-8", errors="ignore") as f:
            template = Template(f.read()).substitute(td.model_dump())

        # return filename

        logger.debug("Template dictionary includes %s fields", len(td.model_dump()))

        return self._apply_svg_post_processing(template, minify, remove_css_variables)

    def _get_default_filename_suffix(self, suffix: str = "") -> str:
        """
        Generate the default filename for SVG output based on chart type.

        Args:
            suffix (str): Optional suffix to append (e.g., " - Wheel Only", " - Aspect Grid Only").

        Returns:
            str: The default filename without extension.
        """
        # Handle special case for DualReturnChart with return type suffix
        if self.chart_type == "DualReturnChart" and isinstance(self.second_obj, PlanetReturnModel):
            if self.second_obj.return_type == "Lunar":
                return f"{self.first_obj.name} - {self.chart_type} Chart - Lunar Return{suffix}"
            elif self.second_obj.return_type == "Solar":
                return f"{self.first_obj.name} - {self.chart_type} Chart - Solar Return{suffix}"

        # Handle ExternalNatal renaming for wheel and grid exports
        if suffix and self.external_view and self.chart_type == "Natal":
            chart_type_name = "ExternalNatal"
        else:
            chart_type_name = self.chart_type

        return f"{self.first_obj.name} - {chart_type_name} Chart{suffix}"

    def _write_svg_to_disk(
        self,
        content: str,
        output_path: Union[str, Path, None],
        filename: Union[str, None],
        default_suffix: str = "",
    ) -> Path:
        """
        Write SVG content to disk and return the path.

        Args:
            content (str): The SVG content to write.
            output_path (str, Path, or None): Directory path. Defaults to home directory.
            filename (str or None): Custom filename without extension. If None, uses default.
            default_suffix (str): Suffix for default filename (e.g., " - Wheel Only").

        Returns:
            Path: The path where the file was saved.
        """
        output_directory = Path(output_path) if output_path is not None else Path.home()

        if filename is not None:
            chartname = output_directory / f"{filename}.svg"
        else:
            default_name = self._get_default_filename_suffix(default_suffix)
            chartname = output_directory / f"{default_name}.svg"

        with open(chartname, "w", encoding="utf-8", errors="ignore") as output_file:
            output_file.write(content)

        print(f"SVG Generated Correctly in: {chartname}")
        return chartname

    def save_svg(
        self,
        output_path: Union[str, Path, None] = None,
        filename: Union[str, None] = None,
        minify: bool = False,
        remove_css_variables=False,
        *,
        custom_title: Union[str, None] = None,
    ):
        """
        Generate and save the full chart SVG to disk.

        Calls generate_svg_string to render the SVG, then writes a file named
        "{subject.name} - {chart_type} Chart.svg" in the specified output directory.

        Args:
            output_path (str, Path, or None): Directory path where the SVG file will be saved.
                If None, defaults to the user's home directory.
            filename (str or None): Custom filename for the SVG file (without extension).
                If None, uses the default pattern: "{subject.name} - {chart_type} Chart".
            minify (bool): Pass-through to generate_svg_string for compact output.
            remove_css_variables (bool): Pass-through to generate_svg_string to embed CSS variables.
            custom_title (str or None): Optional override for the SVG title.

        Returns:
            None
        """

        self.template = self.generate_svg_string(minify, remove_css_variables, custom_title=custom_title)
        self._write_svg_to_disk(self.template, output_path, filename, default_suffix="")

    def generate_wheel_only_svg_string(self, minify: bool = False, remove_css_variables=False):
        """
        Render the wheel-only chart SVG as a string.

        Reads the wheel-only XML template, substitutes chart data, and applies optional
        CSS inlining and minification.

        Args:
            minify (bool): Remove whitespace and quotes for compactness.
            remove_css_variables (bool): Embed CSS variable definitions.

        Returns:
            str: SVG markup for the chart wheel only.
        """

        with open(
            Path(__file__).parent / "templates" / "wheel_only.xml",
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as f:
            template = f.read()

        template_dict = self._create_template_dictionary()
        # Use a compact viewBox specific for the wheel-only rendering
        wheel_viewbox = self._wheel_only_viewbox()
        template = Template(template).substitute({**template_dict.model_dump(), "viewbox": wheel_viewbox})

        return self._apply_svg_post_processing(template, minify, remove_css_variables)

    def save_wheel_only_svg_file(
        self,
        output_path: Union[str, Path, None] = None,
        filename: Union[str, None] = None,
        minify: bool = False,
        remove_css_variables=False,
    ):
        """
        Generate and save wheel-only chart SVG to disk.

        Calls generate_wheel_only_svg_string and writes a file named
        "{subject.name} - {chart_type} Chart - Wheel Only.svg" in the specified output directory.

        Args:
            output_path (str, Path, or None): Directory path where the SVG file will be saved.
                If None, defaults to the user's home directory.
            filename (str or None): Custom filename for the SVG file (without extension).
                If None, uses the default pattern: "{subject.name} - {chart_type} Chart - Wheel Only".
            minify (bool): Pass-through to generate_wheel_only_svg_string for compact output.
            remove_css_variables (bool): Pass-through to generate_wheel_only_svg_string to embed CSS variables.

        Returns:
            None
        """

        template = self.generate_wheel_only_svg_string(minify, remove_css_variables)
        self._write_svg_to_disk(template, output_path, filename, default_suffix=" - Wheel Only")

    def generate_aspect_grid_only_svg_string(self, minify: bool = False, remove_css_variables=False):
        """
        Render the aspect-grid-only chart SVG as a string.

        Reads the aspect-grid XML template, generates the aspect grid based on chart type,
        and applies optional CSS inlining and minification.

        Args:
            minify (bool): Remove whitespace and quotes for compactness.
            remove_css_variables (bool): Embed CSS variable definitions.

        Returns:
            str: SVG markup for the aspect grid only.
        """

        with open(
            Path(__file__).parent / "templates" / "aspect_grid_only.xml",
            "r",
            encoding="utf-8",
            errors="ignore",
        ) as f:
            template = f.read()

        template_dict = self._create_template_dictionary()

        if self.chart_type in ["Transit", "Synastry", "DualReturnChart"]:
            aspects_grid = draw_transit_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self.available_planets_setting,
                self.aspects_list,
            )
        else:
            aspects_grid = draw_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self.available_planets_setting,
                self.aspects_list,
                x_start=50,
                y_start=250,
            )

        # Use a compact, known-good viewBox that frames the grid
        viewbox_override = self._grid_only_viewbox()

        template = Template(template).substitute(
            {**template_dict.model_dump(), "makeAspectGrid": aspects_grid, "viewbox": viewbox_override}
        )

        return self._apply_svg_post_processing(template, minify, remove_css_variables)

    def save_aspect_grid_only_svg_file(
        self,
        output_path: Union[str, Path, None] = None,
        filename: Union[str, None] = None,
        minify: bool = False,
        remove_css_variables=False,
    ):
        """
        Generate and save aspect-grid-only chart SVG to disk.

        Calls generate_aspect_grid_only_svg_string and writes a file named
        "{subject.name} - {chart_type} Chart - Aspect Grid Only.svg" in the specified output directory.

        Args:
            output_path (str, Path, or None): Directory path where the SVG file will be saved.
                If None, defaults to the user's home directory.
            filename (str or None): Custom filename for the SVG file (without extension).
                If None, uses the default pattern: "{subject.name} - {chart_type} Chart - Aspect Grid Only".
            minify (bool): Pass-through to generate_aspect_grid_only_svg_string for compact output.
            remove_css_variables (bool): Pass-through to generate_aspect_grid_only_svg_string to embed CSS variables.

        Returns:
            None
        """

        template = self.generate_aspect_grid_only_svg_string(minify, remove_css_variables)
        self._write_svg_to_disk(template, output_path, filename, default_suffix=" - Aspect Grid Only")


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    from kerykeion.planetary_return_factory import PlanetaryReturnFactory
    from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
    from kerykeion.chart_data_factory import ChartDataFactory

    ACTIVE_PLANETS: list[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS
    # ACTIVE_PLANETS: list[AstrologicalPoint] = ALL_ACTIVE_POINTS
    setup_logging(level="info")

    subject = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", active_points=ACTIVE_PLANETS
    )

    return_factory = PlanetaryReturnFactory(
        subject, city="Los Angeles", nation="US", lng=-118.2437, lat=34.0522, tz_str="America/Los_Angeles", altitude=0
    )

    ###
    ## Birth Chart - NEW APPROACH with ChartDataFactory
    birth_chart_data = ChartDataFactory.create_natal_chart_data(
        subject,
        active_points=ACTIVE_PLANETS,
    )
    birth_chart = ChartDrawer(
        chart_data=birth_chart_data,
        chart_language="IT",
        theme="strawberry",
    )
    birth_chart.save_svg()  # minify=True, remove_css_variables=True)

    ###
    ## Solar Return Chart - NEW APPROACH with ChartDataFactory
    solar_return = return_factory.next_return_from_iso_formatted_time(
        "2025-01-09T18:30:00+01:00",  # UTC+1
        return_type="Solar",
    )
    solar_return_chart_data = ChartDataFactory.create_return_chart_data(
        subject,
        solar_return,
        active_points=ACTIVE_PLANETS,
    )
    solar_return_chart = ChartDrawer(
        chart_data=solar_return_chart_data,
        chart_language="IT",
        theme="classic",
    )

    solar_return_chart.save_svg()  # minify=True, remove_css_variables=True)

    ###
    ## Single wheel return - NEW APPROACH with ChartDataFactory
    single_wheel_return_chart_data = ChartDataFactory.create_single_wheel_return_chart_data(
        solar_return,
        active_points=ACTIVE_PLANETS,
    )
    single_wheel_return_chart = ChartDrawer(
        chart_data=single_wheel_return_chart_data,
        chart_language="IT",
        theme="dark",
    )

    single_wheel_return_chart.save_svg()  # minify=True, remove_css_variables=True)

    ###
    ## Lunar return - NEW APPROACH with ChartDataFactory
    lunar_return = return_factory.next_return_from_iso_formatted_time(
        "2025-01-09T18:30:00+01:00",  # UTC+1
        return_type="Lunar",
    )
    lunar_return_chart_data = ChartDataFactory.create_return_chart_data(
        subject,
        lunar_return,
        active_points=ACTIVE_PLANETS,
    )
    lunar_return_chart = ChartDrawer(
        chart_data=lunar_return_chart_data,
        chart_language="IT",
        theme="dark",
    )
    lunar_return_chart.save_svg()  # minify=True, remove_css_variables=True)

    ###
    ## Transit Chart - NEW APPROACH with ChartDataFactory
    transit = AstrologicalSubjectFactory.from_iso_utc_time(
        "Transit",
        "2021-10-04T18:30:00+01:00",
    )
    transit_chart_data = ChartDataFactory.create_transit_chart_data(
        subject,
        transit,
        active_points=ACTIVE_PLANETS,
    )
    transit_chart = ChartDrawer(
        chart_data=transit_chart_data,
        chart_language="IT",
        theme="dark",
    )
    transit_chart.save_svg()  # minify=True, remove_css_variables=True)

    ###
    ## Synastry Chart - NEW APPROACH with ChartDataFactory
    second_subject = AstrologicalSubjectFactory.from_birth_data("Yoko Ono", 1933, 2, 18, 18, 30, "Tokyo", "JP")
    synastry_chart_data = ChartDataFactory.create_synastry_chart_data(
        subject,
        second_subject,
        active_points=ACTIVE_PLANETS,
    )
    synastry_chart = ChartDrawer(
        chart_data=synastry_chart_data,
        chart_language="IT",
        theme="dark",
    )
    synastry_chart.save_svg()  # minify=True, remove_css_variables=True)

    ##
    # Transit Chart with Grid - NEW APPROACH with ChartDataFactory
    subject.name = "Grid"
    transit_chart_with_grid_data = ChartDataFactory.create_transit_chart_data(
        subject,
        transit,
        active_points=ACTIVE_PLANETS,
    )
    transit_chart_with_grid = ChartDrawer(
        chart_data=transit_chart_with_grid_data,
        chart_language="IT",
        theme="dark",
        double_chart_aspect_grid_type="table",
    )
    transit_chart_with_grid.save_svg()  # minify=True, remove_css_variables=True)
    transit_chart_with_grid.save_aspect_grid_only_svg_file()
    transit_chart_with_grid.save_wheel_only_svg_file()

    print("✅ All chart examples completed using ChartDataFactory + ChartDrawer architecture!")
