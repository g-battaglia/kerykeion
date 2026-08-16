# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import logging
import math
import re
from functools import lru_cache
from math import ceil
from pathlib import Path
from string import Template
from typing import Any, Mapping, Optional, Sequence, Union, cast, get_args

# Sentinel object used to distinguish "parameter not passed" from an explicit value
# in render methods (generate_svg_string, save_svg, etc.).  When the user omits
# style= or show_zodiac_background_ring= at render time, the instance-level
# default set in __init__ is used instead.
_UNSET: Any = object()

# Module directory for resolving template/theme paths
_MODULE_DIR = Path(__file__).parent

from kerykeion.ephemeris_backend.backend import ephe
from svg_polish import optimize as _svg_polish_optimize

from kerykeion.house_comparison.factory import HouseComparisonFactory
from kerykeion.schemas import (
    KerykeionException,
    ChartType,
    Sign,
    ActiveAspect,
    KerykeionPointModel,
)
from kerykeion.schemas import ChartTemplateModel
from kerykeion.schemas.models import (
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    PlanetReturnModel,
    SingleChartDataModel,
    DualChartDataModel,
)
from kerykeion.schemas.settings_models import (
    KerykeionLanguageModel,
)
from kerykeion.schemas.literals import (
    KerykeionChartTheme,
    KerykeionChartStyle,
    KerykeionChartLanguage,
    AstrologicalPoint,
)
from kerykeion.settings.config_constants import (
    AXIAL_POINTS,
    DEFAULT_ACTIVE_POINTS,
    has_visible_text,
    return_label_keys,
    subject_states_a_diurnality,
)
from kerykeion.settings.translations import get_translations, load_language_pair
from kerykeion.charts.glyph_metrics import estimate_text_width
from kerykeion.charts.utils import (
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
    make_lunar_phase,
    draw_main_house_grid,
    draw_secondary_house_grid,
    draw_main_planet_grid,
    draw_secondary_planet_grid,
    escape_svg_text,
    format_location_string,
    format_datetime_with_timezone,
    draw_house_sectors,
    convert_decimal_to_degree_string,
    gauquelin_column_width,
    planet_grid_column_width,
    get_decoded_kerykeion_celestial_point_name,
    CHART_TEXT_FONT_FAMILY,
)
from kerykeion.charts.draw_planets import draw_planets
from kerykeion.charts.draw_modern import (
    draw_modern_dual_horoscope,
    draw_modern_horoscope,
)
from kerykeion.utilities.core import (
    get_houses_list,
    get_planet_house,
    inline_css_variables_in_svg,
    distribute_percentages_to_100,
    format_iso_display,
    extract_year_from_iso,
)
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


@lru_cache(maxsize=8)
def _load_cached_file(path: str) -> str:
    """Read a file from disk and cache the result for subsequent calls.

    These are trusted in-package templates/themes (valid UTF-8); read strictly
    so a truncated or corrupt install surfaces a clear decode error instead of
    silently yielding malformed SVG (``errors="ignore"`` would drop bad bytes).
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Template fields that hold user-controlled plain text (subject names, cities,
# custom titles). They are XML-escaped in _create_template_dictionary before
# substitution; all other fields are either numeric or trusted SVG fragments.
_PLAIN_TEXT_TEMPLATE_FIELDS = (
    "stringTitle",
    # Built from the title plus the subject's city and nation, so it carries the
    # same user-controlled text and needs the same escaping.
    "stringDescription",
    "top_left_0",
    "top_left_1",
    "top_left_2",
    "top_left_3",
    "top_left_4",
    "top_left_5",
    "bottom_left_0",
    "bottom_left_1",
    "bottom_left_2",
    "bottom_left_3",
    "bottom_left_4",
    # The diurnality line embeds subject names on synastry wheels, so it is
    # plain user-controlled text and must be escaped like the rest.
    "bottom_left_5",
    # Element/quality labels are language-pack text (translated names +
    # percentages). Escape them too so a custom or translated pack containing
    # markup-significant characters cannot break the XML.
    "elements_string",
    "fire_string",
    "earth_string",
    "air_string",
    "water_string",
    "qualities_string",
    "cardinal_string",
    "fixed_string",
    "mutable_string",
)


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


# The diurnality line is a sixth bottom-left row, drawn at y=522. The rows sit
# inside the wheel's chord, and because all of them are *below* its centre
# (340, 290, r=240) the lower a row is the MORE clear width it has: row 0 gets
# 143px, row 5 gets 259px. So the new row needs no room made for it — it lands in
# the widest band of the six.
#
# The one thing in its way is the moon glyph, which occupies x 20-40, y 518-538
# and would sit on top of it. So the glyph drops instead, keeping the same 10px
# gap below the last row of text that it has always had. An earlier revision
# lifted the whole block by 22px instead, on the mistaken belief that lower rows
# were tighter; that stole 18 to 38px from the five existing rows and pushed
# "Progression Lunar phase: Waxing Gibbous" under the wheel in the default
# language. When the line is not drawn, nothing moves at all.
DIURNALITY_GLYPH_DROP: int = 14

# The geometry the paragraph above describes, as numbers the code can use.
_WHEEL_CENTRE_X: float = 340.0
_WHEEL_CENTRE_Y: float = 290.0
_WHEEL_RADIUS: float = 240.0
_INFO_ROW_FIRST_Y: float = 452.0
_INFO_ROW_STEP: float = 14.0
_INFO_ROW_TEXT_X: float = 20.0
_INFO_ROW_TEXT_RISE: float = 10.0
_INFO_ROW_COUNT: int = 6
#: Baseline the moon glyph's default offset was chosen against — the fifth row,
#: i.e. the last one before the diurnality line existed.
_INFO_ROW_LEGACY_LAST_Y: float = 508.0

# How much clear width row 5 really has, and it is not the 258.6px the chord
# gives at the baseline: the chord narrows going *upward*, and text rises above
# its baseline. Ideographs fill the em box, so the binding measurement is the
# chord at y = 522 - 10px = 512 — centre (340, 290), r=240, so the graphics start
# at x=248.8 and 228.8px is clear from the text's x=20. Taking the baseline
# figure overstates the room by 13% and is what let a row overrun. The constant
# sits a little under the geometry, since the estimator below is close to the
# truth rather than wildly conservative and the last pixel is not worth having.
DIURNALITY_ROW_CLEAR_WIDTH: float = 228.0


def info_row_clear_width(row_index: int) -> float:
    """Clear width in px available to bottom-left row *row_index*, at 10px text.

    Derived from the geometry described above rather than tabulated, so the two
    cannot drift: the rows sit inside the wheel's chord, the chord narrows going
    upward, and text rises about 10px above its baseline — so the binding
    measurement for a row drawn at ``y`` is the chord at ``y - 10``.

    The spread is wide enough to matter. Row 5 has 229px and row 0 only 134,
    which is why a line that fits at the bottom of the panel can run under the
    wheel at the top of it. Anything written into these rows should be measured
    against its own row, never against the roomiest one.
    """
    baseline_y = _INFO_ROW_FIRST_Y + _INFO_ROW_STEP * row_index
    measured_y = baseline_y - _INFO_ROW_TEXT_RISE
    half_chord = math.sqrt(_WHEEL_RADIUS**2 - (measured_y - _WHEEL_CENTRE_Y) ** 2)
    return (_WHEEL_CENTRE_X - half_chord) - _INFO_ROW_TEXT_X


def truncate_to_width(text: str, budget: float, ellipsis_symbol: str = "…", font_size: float = 10.0) -> str:
    """Shorten *text* until :func:`estimate_text_width` fits *budget*.

    Keeps at least one character of a non-empty *text*, even when that overshoots:
    returning nothing would leave the value on the diurnality row with no owner,
    the very ambiguity the wheel names are there to remove. The overshoot is
    bounded by one glyph plus the ellipsis and is only reachable when the row's
    fixed text has already eaten the budget, which no shipped translation does —
    see the guard in :meth:`InfoSectionBuilder.build_dual_diurnality_info`.

    Empty text stays empty rather than becoming a bare ellipsis.

    *budget* is in pixels at *font_size*. Both default to the info panel's 10px,
    which is the only caller in this module — but a caller measuring 16px text
    against a pixel budget got a 53% overrun when the size was hardcoded here,
    so it is a parameter.

    Cuts by code point, not by grapheme cluster: a Devanagari conjunct or an
    emoji ZWJ sequence can lose its tail and leave a dangling virama or joiner
    before the ellipsis. It never overruns the budget — the pieces are charged
    individually — so this is a quality limit rather than a layout one.
    """
    if not text:
        return ""
    if estimate_text_width(text, font_size) <= budget:
        return text

    ellipsis_width = estimate_text_width(ellipsis_symbol, font_size)
    kept = ""
    for char in text:
        if kept and estimate_text_width(kept + char, font_size) + ellipsis_width > budget:
            break
        kept += char
    return kept + ellipsis_symbol


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

from kerykeion.schemas.models import ChartDataModel

if TYPE_CHECKING:
    from kerykeion.charts.drawer import ChartDrawer  # type: ignore[attr-defined]  # noqa: F811


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

    def _return_label(self, subject) -> str:
        """The display name for a return chart's own wheel.

        See :func:`return_label_keys`.
        """
        key, default = return_label_keys(subject)
        return self._translate(key, default)

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
    # SIZING METHODS (override to customize width/height per chart type)
    # -------------------------------------------------------------------------

    def get_initial_width(self) -> float:
        """Return the default chart width for this chart type."""
        return self.drawer._DEFAULT_NATAL_WIDTH

    def get_minimum_width(self, wheel_right: float) -> int:
        """Return the baseline minimum width to prevent compression."""
        return max(int(wheel_right), self.drawer._DEFAULT_NATAL_WIDTH)

    def is_dual_wheel(self) -> bool:
        """Whether this chart type uses dual-wheel (biwheel) layout."""
        return False

    def get_comparison_point_label(self) -> str:
        """Label for the outer-wheel points in house comparison grids."""
        return ""

    def get_comparison_cusp_label(self) -> str:
        """Label for the outer-wheel cusps in cusp comparison grids."""
        return ""

    def get_width_without_comparison(self) -> float:
        """Width to use when house comparison grids are hidden. Defaults to initial width."""
        return self.get_initial_width()

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

    def _translated_house_system(self, subject, terse: bool = False) -> str:
        """Translate the effective house system of one wheel.

        Near the poles the requested system can be undefined, and the subject
        factory quietly stands another one in its place. The chart has always
        printed the system actually used; with ``show_polar_fallback_note`` it
        also admits that a substitution happened, which is the difference
        between a reader trusting the line and a reader being misled by it.
        """
        house_key = "houses_system_" + subject.effective_houses_system_identifier
        name = self._translate(house_key, subject.effective_houses_system_name)
        if self.drawer.show_polar_fallback_note and subject._main_house_fallback() is not None:
            name += "*" if terse else f"* ({self._translate('polar_fallback', 'polar fallback')})"
        return name

    def _translated_house_systems(self, subject, second_subject=None, terse: bool = False) -> str:
        """Translate one system, or both when the two wheels do not tell the same story.

        Landing on the same system is not the same as having asked for it. One
        wheel can use Porphyry natively while the other asked for Placidus and
        was given Porphyry at a polar latitude — identical effective
        identifiers, different facts. Collapsing on the identifier alone would
        print one unqualified name and hide the substitution entirely, so the
        rendered names are what decide: they already carry the fallback mark.
        """
        first_system = self._translated_house_system(subject, terse=terse)
        if second_subject is None:
            return first_system
        second_system = self._translated_house_system(second_subject, terse=terse)
        if second_system != first_system:
            return f"{first_system} / {second_system}"
        return first_system

    def _marks_a_polar_fallback(self, subject, second_subject=None) -> bool:
        """Whether this row is about to gain a fallback mark from either wheel."""
        if not self.drawer.show_polar_fallback_note:
            return False
        subjects = [subject] + ([second_subject] if second_subject is not None else [])
        return any(s is not None and s._main_house_fallback() is not None for s in subjects)

    def _fit_house_row(self, compose, subject, second_subject, row_index: int) -> str:
        """Compose a house-system row, shedding the fallback wording before the words break.

        The spelled-out note is worth the room when there is room: at row 1 the
        wheel leaves ~147px and "Domification: Porphyry* (polar fallback)" wants
        180. Cutting that mid-word would leave "(pol…", which reads as damage
        rather than as a deliberate mark, so the row drops to the bare asterisk
        instead — keeping the one thing it must not lose, that a substitution
        happened. The truncation below is a floor no shipped translation reaches.

        The measuring only happens when a mark is actually being added. A dual
        wheel naming two different systems already ran a few pixels past this
        row before the option existed, and it is not this feature's place to
        start truncating that: with nothing to mark, the row is returned exactly
        as it was.
        """
        verbose = compose(False)
        if not self._marks_a_polar_fallback(subject, second_subject):
            return verbose

        budget = info_row_clear_width(row_index)
        if estimate_text_width(verbose) <= budget:
            return verbose
        terse = compose(True)
        if estimate_text_width(terse) <= budget:
            return terse
        return truncate_to_width(terse, budget)

    def build_domification_info(self, second_subject=None, row_index: int = 1) -> str:
        """Build the domification string, including both differing dual-wheel systems."""
        label = self._translate("domification", "Domification")
        first = self.drawer.first_obj
        return self._fit_house_row(
            lambda terse: f"{label}: {self._translated_house_systems(first, second_subject, terse=terse)}",
            first,
            second_subject,
            row_index,
        )

    def build_perspective_info(self, subject) -> str:
        """Build the perspective type string."""
        return self.drawer._get_perspective_string(subject)

    def build_houses_system_info(self, subject, second_subject=None, row_index: int = 1) -> str:
        """Build compact house-system text, including a differing second wheel."""
        # The system the cusps came from, not the one requested: the compact
        # renderers label dual wheels and returns, where a polar chart would
        # otherwise read as the system it could not actually be cast in.
        houses = self._translate("houses", "Houses")
        return self._fit_house_row(
            lambda terse: f"{self._translated_house_systems(subject, second_subject, terse=terse)} {houses}",
            subject,
            second_subject,
            row_index,
        )

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

    def _diurnality_value(self, subject) -> str:
        """The bare "Diurnal"/"Nocturnal" value, or ``""`` when it does not apply.

        Three cases yield nothing, and only the first is a user preference — the
        other two are absences of meaning rather than absences of data:

        - **``show_diurnality=False``.** The caller opted out of the line.
        - **Any perspective not cast from the Earth.** Not for want of a horizon:
          such a chart still carries an Ascendant and houses, and this very panel
          prints its domification one row above. The objection is the Sun. On a
          heliocentric chart it is the centre body and is excluded from the
          points, so the statement has nothing in the drawing to refer to; on a
          Marscentric or Selenocentric one it is worse, because a Sun *is* drawn
          and it is not the Sun that was measured — ``is_diurnal`` comes from a
          tropical geocentric Sun, and on a Liverpool chart that is 196° while
          the Marscentric wheel draws 354°. Seven of the eleven perspectives are
          in that position.
        - **``is_diurnal is None``.** Midpoint composites represent no single
          sky, so there is no moment for the Sun to be above or below.

        Note the deliberate explicit ``is None`` check rather than
        :func:`resolve_sect_is_diurnal`: that helper defaults a missing value to
        day, which is right for calculations that must pick a branch, but here it
        would label a composite that never had a sky as diurnal.
        """
        if not self.drawer.show_diurnality or not subject_states_a_diurnality(subject):
            return ""
        return (
            self._translate("diurnal", "Diurnal") if subject.is_diurnal else self._translate("nocturnal", "Nocturnal")
        )

    def build_diurnality_info(self, subject) -> str:
        """Build the diurnality line for a single-wheel chart.

        Whether the Sun stood above or below the horizon is an observable fact
        shared by every tradition, so the wording stays descriptive
        ("Diurnality: Nocturnal") and leaves any one school's vocabulary for what
        follows from it out of the neutral info panel.

        Args:
            subject: Subject exposing ``is_diurnal`` and ``perspective_type``.

        Returns:
            The formatted line, or ``""`` when diurnality does not apply.
        """
        value = self._diurnality_value(subject)
        if not value:
            return ""
        return f"{self._translate('diurnality', 'Diurnality')}: {value}"

    def build_relationship_score_info(self) -> tuple[str, str]:
        """Build the synastry relationship-score rows: the value, then its band.

        Returns two empty strings unless the option is on AND the chart data
        actually carries a score: ``create_synastry_chart_data`` computes one by
        default, but the generic factory does not, and a chart drawn from the
        generic path must print nothing rather than a zero it never measured.

        Two rows rather than one because of where they sit. The score is a count
        of weighted contacts, so the number means nothing without the band it
        falls in — but a synastry panel's first row has only ~134px of clear
        width before the wheel, and "Relationship Score: 12 (Important)" needs
        156 even in English. A synastry leaves rows 0 and 1 both empty, so the
        pair fits with room to spare in every shipped language instead of one
        row being truncated in most of them.
        """
        if not self.drawer.show_relationship_score:
            return "", ""
        score = getattr(self.drawer.chart_data, "relationship_score", None)
        if score is None:
            return "", ""

        label = self._translate("relationship_score", "Relationship Score")
        description_key = "relationship_score_" + str(score.score_description).lower().replace(" ", "_")
        description = self._translate(description_key, str(score.score_description))
        return (
            truncate_to_width(f"{label}: {score.score_value}", info_row_clear_width(0)),
            truncate_to_width(str(description), info_row_clear_width(1)),
        )

    @staticmethod
    def _is_symbolic_direction(first, second) -> bool:
        """True when *second*'s points were moved by an arc from *first*, not recast.

        A solar arc directed chart keeps the nativity's instant and shifts every
        point forward by the Sun's arc, so its ``is_diurnal`` answers for the
        birth and not for the wheel drawn from it: on a Rome 1950 nativity
        directed to 2020 the value says the Sun is up while the directed Sun sits
        in the third house, below the horizon. A secondary progressed chart is
        cast for a real later moment and its value does describe its own wheel.

        Both arrive through the same renderer and the same model, with the same
        ``chart_type``, so the flag has to come from somewhere. It comes from the
        instant: sharing the natal one is what "symbolic" means here. Astrologer
        Studio reaches the same conclusion by asking its caller, having no better
        signal on its side of the wire.

        Only the progression renderer consults this. Two subjects can share an
        instant without one being derived from the other — twins in a synastry,
        or two charts cast for the same event — and there the shared instant
        means nothing.
        """
        first_utc = getattr(first, "iso_formatted_utc_datetime", None)
        second_utc = getattr(second, "iso_formatted_utc_datetime", None)
        return first is not second and first_utc is not None and first_utc == second_utc

    def build_dual_diurnality_info(self, first: tuple, second: tuple, second_may_be_directed: bool = False) -> str:
        """Build one diurnality line covering both wheels of a dual chart.

        Diurnality belongs to a single chart: the same placement reads
        differently depending on the diurnality of the chart it sits in, so a
        two-wheel chart needs both values or neither is interpretable. They share
        one line, each behind the name of its own wheel, so a bare "Nocturnal"
        can never be read as a statement about the wrong chart.

        Everything on this row is fighting for about 228px — see
        :data:`DIURNALITY_ROW_CLEAR_WIDTH` — so two of its choices are about
        space rather than style. The separator is a single-spaced "·" rather
        than the wide one used elsewhere in this panel, and there is no
        "Diurnality:" label; the wheel names carry the meaning perfectly well on
        their own, since "Natal Nocturnal" needs no heading to be understood.

        The values and separators are shipped text and fixed, so the wheel names
        absorb whatever is left, cut to :func:`estimate_text_width` rather than to
        a character count. That distinction is the whole point: eight ideographs
        are twice the width of eight Latin letters, and a character cap sent a
        Chinese-named synastry clean under the wheel while its test stayed green.

        Args:
            first: ``(subject, wheel_name)`` for the first wheel.
            second: ``(subject, wheel_name)`` for the second wheel.

        Returns:
            The joined line, or ``""`` when neither wheel has an applicable value.
        """
        if second_may_be_directed and self._is_symbolic_direction(first[0], second[0]):
            # See _is_symbolic_direction. Neither wheel gets a value: the natal
            # one would be true and the directed one false, side by side, and a
            # reader has no way to tell which is which.
            return ""

        labelled = []
        for subject, wheel_name in (first, second):
            if subject is None:
                continue
            value = self._diurnality_value(subject)
            if not value:
                continue
            if not has_visible_text(wheel_name):
                # A value with no owner is worse than no line — it is precisely
                # the ambiguity the wheel names were added to prevent. One name
                # with no visible glyph blanks the whole row rather than leaving
                # the other value to be read as belonging to both. Reachable: the
                # name is a plain string with no normalisation upstream.
                return ""
            labelled.append((wheel_name, value))
        if not labelled:
            return ""

        separator = " · "
        # The values and separators are shipped text and cannot be shortened, so
        # they come off the budget first and the wheel names get what is left.
        fixed = estimate_text_width(separator) * (len(labelled) - 1) + sum(
            estimate_text_width(f" {value}") for _, value in labelled
        )
        # What the names cost even when cut as far as they go. `truncate_to_width`
        # keeps one character plus an ellipsis rather than returning nothing, so
        # the row has a floor and `fixed` alone is not what has to fit — an
        # earlier version of this guard compared `fixed` and let a language pack
        # with wide values render 260px into a 228px row.
        floor = sum(estimate_text_width(truncate_to_width(name, 0.0)) for name, _ in labelled)
        if fixed + floor > DIURNALITY_ROW_CLEAR_WIDTH:
            # No shipped translation gets here — the widest pair of values is a
            # third of the row — but a caller's language pack can. Drop the line:
            # two bare values on a dual chart are ambiguous, so it is worth less
            # than the graphics it would otherwise sit on.
            return ""
        names_budget = DIURNALITY_ROW_CLEAR_WIDTH - fixed

        # Water-filling: a name that wants less than its equal share hands the
        # remainder to the one that wants more, so "Natal" beside a long name
        # does not get cut to make room it was never going to use.
        natural = [estimate_text_width(name) for name, _ in labelled]
        share = names_budget / len(labelled)
        spare = sum(share - width for width in natural if width < share)
        over = [width for width in natural if width > share]
        share_for_long = share + (spare / len(over) if over else 0.0)

        parts = [
            f"{truncate_to_width(name, share if width <= share else share_for_long)} {value}"
            for (name, value), width in zip(labelled, natural)
        ]
        row = separator.join(parts)

        # Re-measure what was actually built. Water-filling can hand a long name
        # less than its own one-glyph floor while the other name takes its full
        # share, so the pre-allocation guard above is necessary but not
        # sufficient: constructed adversarially (a language pack of wide values
        # plus a name of ǅ-digraphs) the row came out 5px over. No shipped
        # translation reaches it, but the module claims it may only ever
        # over-estimate, and an invariant with a known hole is not one.
        return "" if estimate_text_width(row) > DIURNALITY_ROW_CLEAR_WIDTH else row

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
        template_dict["bottom_left_5"] = builder.build_diurnality_info(d.first_obj)

        # Lunar phase visualization
        d._setup_lunar_phase(template_dict, d.first_obj, d.geolat)

    def setup_grids(self, template_dict: dict) -> None:
        """Set up planet and house grids for single subject."""
        d = self.drawer
        houses_list = self._get_houses_list(d.first_obj)

        d._setup_main_houses_grid(template_dict, houses_list)
        template_dict["makeSecondaryHousesGrid"] = ""
        d._setup_single_wheel_houses(template_dict, houses_list)
        d._setup_house_sectors(template_dict, houses_list)
        d._setup_gauquelin_sectors(template_dict)
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
        template_dict["top_left_1"] = format_iso_display(
            d.first_obj.first_subject.iso_formatted_local_datetime  # type: ignore[union-attr]
        )
        template_dict["top_left_2"] = f"{first_lat} {first_lng}"
        template_dict["top_left_3"] = d.first_obj.second_subject.name  # type: ignore[union-attr]
        template_dict["top_left_4"] = format_iso_display(
            d.first_obj.second_subject.iso_formatted_local_datetime  # type: ignore[union-attr]
        )
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
        # Empty for a midpoint composite (is_diurnal is None — no single sky);
        # populated for a Davison composite, which does represent a real moment.
        # It goes in row 4, the slot this renderer already left blank, rather than
        # row 5: appending below an empty row would open a visible gap above it.
        template_dict["bottom_left_4"] = builder.build_diurnality_info(d.first_obj)
        template_dict["bottom_left_5"] = ""

        # Lunar phase
        d._setup_lunar_phase(template_dict, d.first_obj, d.geolat)

    def setup_grids(self, template_dict: dict) -> None:
        """Set up grids with combined subject name."""
        d = self.drawer
        houses_list = self._get_houses_list(d.first_obj)

        d._setup_main_houses_grid(template_dict, houses_list)
        template_dict["makeSecondaryHousesGrid"] = ""
        d._setup_single_wheel_houses(template_dict, houses_list)
        d._setup_house_sectors(template_dict, houses_list)
        d._setup_gauquelin_sectors(template_dict)
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

    def get_initial_width(self) -> float:
        d = self.drawer
        if d.double_chart_aspect_grid_type == "table":
            return d._DEFAULT_FULL_WIDTH_WITH_TABLE
        return d._DEFAULT_FULL_WIDTH

    def get_minimum_width(self, wheel_right: float) -> int:
        return max(int(wheel_right), 450)

    def is_dual_wheel(self) -> bool:
        return True

    def get_comparison_point_label(self) -> str:
        return self._translate("transit_point", "Transit Point")

    def get_comparison_cusp_label(self) -> str:
        return self._comparison_cusp_label()

    def setup_circles(self, template_dict: dict) -> None:
        """Set up transit-style circles with outer ring."""
        self.drawer._setup_transit_circles(template_dict)

    def _aspect_list_title(self) -> str:
        """Title for the aspect list panel. Override in subclasses for custom labels."""
        return f"{self.drawer.first_obj.name} - {self._translate('transit_aspects', 'Transit Aspects')}"

    def _outer_wheel_label(self) -> str:
        """Label for the outer wheel in planet grids. Override for custom labels."""
        return self._translate("transit", "Transit")

    def _comparison_return_point_label(self) -> str:
        """Label for the outer-wheel points in house comparison grids."""
        return self._translate("transit_point", "Transit Point")

    def _comparison_cusp_label(self) -> str:
        """Label for the outer-wheel cusps in cusp comparison grids."""
        return self._translate("transit_cusp", "Transit Cusp")

    def setup_aspects(self, template_dict: dict) -> None:
        """Set up aspect list or grid for dual-wheel chart."""
        d = self.drawer

        if d.double_chart_aspect_grid_type == "list":
            title = self._aspect_list_title()
            template_dict["makeAspectGrid"] = ""

            if d._is_right_panel_mode():
                rp = d._get_right_panel_aspect_params()
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                    title,
                    d.aspects_list,
                    d.planets_settings,
                    d.aspects_settings,
                    aspects_per_column=rp["aspects_per_column"],
                    column_width=rp["column_width"],
                    line_height=rp["line_height"],
                    chart_height=d.height,
                    x_offset=rp["x_offset"],
                    y_offset=rp["y_offset"],
                )
            else:
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                    title,
                    d.aspects_list,
                    d.planets_settings,
                    d.aspects_settings,
                    chart_height=d.height,
                )
        else:
            template_dict["makeAspectGrid"] = ""
            if d._is_right_panel_mode():
                rp = d._get_right_panel_aspect_params()
                grid_x = rp["x_offset"]
                n_active = max(d._count_aspect_grid_planets(), 1)
                grid_size = 14 * n_active
                grid_y = int(rp["y_offset"] + grid_size + 30)
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                    d.chart_colors_settings["paper_0"],
                    d._get_aspect_grid_planets_setting(),
                    d.aspects_list,
                    grid_x,
                    grid_y,
                    aspects_settings=d.aspects_settings,
                )
            else:
                # Same anchor as Synastry/DualReturn (550, 450): the previous
                # hardcoded (600, 520) pushed the glyph header row past the
                # 565-unit viewBox bottom, clipping it on every table-mode
                # Transit chart.
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                    d.chart_colors_settings["paper_0"],
                    d._get_aspect_grid_planets_setting(),
                    d.aspects_list,
                    d._TRANSIT_ASPECT_GRID_X,
                    d._TRANSIT_ASPECT_GRID_Y,
                    aspects_settings=d.aspects_settings,
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
        template_dict["bottom_left_1"] = builder.build_domification_info(d.second_obj)

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
        template_dict["bottom_left_5"] = builder.build_dual_diurnality_info(
            (d.first_obj, self._translate("chart_info_natal_label", "Natal")),
            (d.second_obj, self._translate("chart_info_transit_label", "Transit")),
        )

        # Moon phase visualization from transit subject
        if d.second_obj is not None and getattr(d.second_obj, "lunar_phase", None):
            template_dict["makeLunarPhase"] = make_lunar_phase(
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
        d._setup_house_sectors(template_dict, first_houses, second_houses)
        template_dict["makeGauquelinSectors"] = ""  # Not rendered for dual-wheel charts
        d._setup_dual_wheel_planets(template_dict)

        # Planet grids with wheel labels
        first_label = d._truncate_name(d.first_obj.name)
        first_grid_title = f"{first_label} ({self._translate('inner_wheel', 'Inner Wheel')})"
        second_grid_title = f"{self._outer_wheel_label()} ({self._translate('outer_wheel', 'Outer Wheel')})"

        template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
            planets_and_houses_grid_title="",
            subject_name=first_grid_title,
            available_kerykeion_celestial_points=d.available_kerykeion_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
            show_out_of_bounds=d.show_out_of_bounds,
        )
        template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
            planets_and_houses_grid_title="",
            second_subject_name=second_grid_title,
            second_subject_available_kerykeion_celestial_points=d.second_subject_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
            show_out_of_bounds=d.show_out_of_bounds,
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
                return_point_label=self._comparison_return_point_label(),
                natal_house_label=self._translate("house_position", "House Position"),
                x_position=d._TRANSIT_HOUSE_COMPARISON_X,
            )

        if d.show_cusp_position_comparison:
            cusp_x = 1180 if d.show_house_position_comparison else 980

            cusp_grid = draw_single_cusp_comparison_grid(
                house_comparison,
                celestial_point_language=d._language_model.celestial_points,
                cusps_owner_subject_number=2,
                cusp_position_comparison_label=self._translate("cusp_position_comparison", "Cusp Position Comparison"),
                owner_cusp_label=self._comparison_cusp_label(),
                projected_house_label=self._translate("natal_house", "Natal House"),
                x_position=cusp_x,
                y_position=0,
            )
            house_comparison_svg += cusp_grid

        template_dict["makeHouseComparisonGrid"] = house_comparison_svg


class ProgressionChartRenderer(TransitChartRenderer):
    """Renderer for Secondary Progression charts.

    Reuses the Transit dual-wheel layout (natal inner, progressed outer)
    via label hooks — no duplicated rendering logic.
    """

    def __init__(self, drawer: "ChartDrawer"):
        super().__init__(drawer)
        if not isinstance(drawer.first_obj, AstrologicalSubjectModel) or not isinstance(
            drawer.second_obj, AstrologicalSubjectModel
        ):
            raise KerykeionException("Progression charts require AstrologicalSubjectModel subjects.")

    def get_comparison_point_label(self) -> str:
        return self._translate("progressed_point", "Progressed Point")

    def _aspect_list_title(self) -> str:
        return f"{self.drawer.first_obj.name} - {self._translate('progression_aspects', 'Progression Aspects')}"

    def _outer_wheel_label(self) -> str:
        return self._translate("progression", "Progression")

    def _comparison_return_point_label(self) -> str:
        return self._translate("progressed_point", "Progressed Point")

    def _comparison_cusp_label(self) -> str:
        return self._translate("progressed_cusp", "Progressed Cusp")

    def setup_info_sections(self, template_dict: dict) -> None:
        super().setup_info_sections(template_dict)
        d = self.drawer
        if d.second_obj is not None:
            prog_dt = ""
            if getattr(d.second_obj, "iso_formatted_local_datetime", None) is not None:
                prog_dt = format_datetime_with_timezone(d.second_obj.iso_formatted_local_datetime)
            template_dict["top_left_3"] = f"{self._translate('chart_info_progression_label', 'Progression')}: {prog_dt}"
            # The transit renderer labelled the second wheel "Transit"; here it is
            # the progressed chart, so relabel rather than inherit a wrong name.
            template_dict["bottom_left_5"] = InfoSectionBuilder(d).build_dual_diurnality_info(
                (d.first_obj, self._translate("chart_info_natal_label", "Natal")),
                (d.second_obj, self._translate("chart_info_progression_label", "Progression")),
                # This renderer draws both secondary progressions and solar arc
                # directions, and only the second is symbolic.
                second_may_be_directed=True,
            )
            if hasattr(d.second_obj, "lunar_phase") and d.second_obj.lunar_phase is not None:
                builder = InfoSectionBuilder(d)
                builder.build_lunar_phase_info(
                    template_dict,
                    d.second_obj,
                    prefix=f"{self._translate('progression', 'Progression')} ",
                    key_lunation="bottom_left_3",
                    key_phase="bottom_left_4",
                )


class SynastryChartRenderer(BaseChartRenderer):
    """Renderer for Synastry charts.

    Dual-wheel chart comparing two birth charts.
    """

    def get_initial_width(self) -> float:
        return self.drawer._DEFAULT_SYNASTRY_WIDTH

    def get_minimum_width(self, wheel_right: float) -> int:
        return max(int(wheel_right), self.drawer._DEFAULT_SYNASTRY_WIDTH // 2)

    def is_dual_wheel(self) -> bool:
        return True

    def get_comparison_point_label(self) -> str:
        return ""

    def get_width_without_comparison(self) -> float:
        return self.drawer._DEFAULT_FULL_WIDTH

    def setup_circles(self, template_dict: dict) -> None:
        """Set up transit-style circles for dual-wheel display."""
        self.drawer._setup_transit_circles(template_dict)

    def setup_aspects(self, template_dict: dict) -> None:
        """Set up aspect list or grid for synastry."""
        d = self.drawer

        if d.double_chart_aspect_grid_type == "list":
            template_dict["makeAspectGrid"] = ""

            if d._is_right_panel_mode():
                rp = d._get_right_panel_aspect_params()
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                    f"{d.first_obj.name} - {d.second_obj.name} {self._translate('synastry_aspects', 'Synastry Aspects')}",
                    d.aspects_list,
                    d.planets_settings,
                    d.aspects_settings,
                    aspects_per_column=rp["aspects_per_column"],
                    column_width=rp["column_width"],
                    line_height=rp["line_height"],
                    chart_height=d.height,
                    x_offset=rp["x_offset"],
                    y_offset=rp["y_offset"],
                )
            else:
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                    f"{d.first_obj.name} - {d.second_obj.name} {self._translate('synastry_aspects', 'Synastry Aspects')}",
                    d.aspects_list,
                    d.planets_settings,
                    d.aspects_settings,
                    chart_height=d.height,
                )
        else:
            template_dict["makeAspectGrid"] = ""
            if d._is_right_panel_mode():
                # Position the grid to the right of left content.
                # draw_transit_aspect_grid uses y_indent as the BOTTOM of the
                # grid (the header row); data cells grow UPWARD from there.
                rp = d._get_right_panel_aspect_params()
                grid_x = rp["x_offset"]
                n_active = max(d._count_aspect_grid_planets(), 1)
                box_size = 14
                grid_total_h = (n_active + 1) * box_size
                # Place grid so its top aligns near the chart title
                aspect_list_y = d._vertical_offsets["aspect_list"]
                chart_title_y = d._vertical_offsets.get("title", 0.0)
                target_top = chart_title_y + 20  # small margin below title
                grid_y = int(target_top - aspect_list_y + grid_total_h)
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                    d.chart_colors_settings["paper_0"],
                    d._get_aspect_grid_planets_setting(),
                    d.aspects_list,
                    grid_x,
                    grid_y,
                    aspects_settings=d.aspects_settings,
                )
            else:
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                    d.chart_colors_settings["paper_0"],
                    d._get_aspect_grid_planets_setting(),
                    d.aspects_list,
                    550,
                    450,
                    aspects_settings=d.aspects_settings,
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

        # Bottom left section. Rows 0 and 1 are the synastry panel's spare ones,
        # and the score takes both: the value on the first, its band on the
        # second. Nothing else moves.
        template_dict["bottom_left_0"], template_dict["bottom_left_1"] = builder.build_relationship_score_info()
        template_dict["bottom_left_2"] = builder.build_zodiac_info()
        template_dict["bottom_left_3"] = builder.build_houses_system_info(d.first_obj, d.second_obj, row_index=3)
        template_dict["bottom_left_4"] = builder.build_perspective_info(d.first_obj)
        # Both natals keep their own sect: a placement that is in sect for one
        # partner can be out of sect for the other, which is precisely what a
        # synastry reading needs to see.
        # Only the first word of each name, as the comparison grids above do to
        # the same two names. No character cap here: these are the only
        # user-controlled strings on the row, and the builder cuts them to the
        # width actually left by the wheel's chord — a cap in characters cannot,
        # since eight ideographs are twice the width of eight Latin letters and
        # ran clean under the graphics.
        template_dict["bottom_left_5"] = builder.build_dual_diurnality_info(
            (d.first_obj, d._truncate_name(d.first_obj.name, truncate_at_space=True)),
            (d.second_obj, d._truncate_name(d.second_obj.name, truncate_at_space=True)),
        )

        template_dict["makeLunarPhase"] = ""

    def setup_grids(self, template_dict: dict) -> None:
        """Set up dual-wheel grids for both subjects."""
        d = self.drawer
        first_houses = self._get_houses_list(d.first_obj)
        second_houses = self._get_houses_list(d.second_obj)

        d._setup_main_houses_grid(template_dict, first_houses)
        d._setup_secondary_houses_grid(template_dict, second_houses)
        d._setup_dual_wheel_houses(template_dict, first_houses, second_houses)
        d._setup_house_sectors(template_dict, first_houses, second_houses)
        template_dict["makeGauquelinSectors"] = ""
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
            show_out_of_bounds=d.show_out_of_bounds,
        )
        template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
            planets_and_houses_grid_title="",
            second_subject_name=f"{second_label} ({self._translate('outer_wheel', 'Outer Wheel')})",
            second_subject_available_kerykeion_celestial_points=d.second_subject_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
            show_out_of_bounds=d.show_out_of_bounds,
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

        template_dict["top_left_5"] = f"{self._translate('type', 'Type')}: {self._return_label(d.first_obj)}"

        # Bottom left section
        template_dict["bottom_left_0"] = builder.build_zodiac_info()
        template_dict["bottom_left_1"] = builder.build_houses_system_info(d.first_obj)
        builder.build_lunar_phase_info(template_dict, d.first_obj)
        template_dict["bottom_left_4"] = builder.build_perspective_info(d.first_obj)
        # A single-wheel return stands on its own, so it carries its own sect —
        # the sect of the return moment, not of the nativity behind it.
        template_dict["bottom_left_5"] = builder.build_diurnality_info(d.first_obj)

        # Lunar phase visualization
        d._setup_lunar_phase(template_dict, d.first_obj, d.geolat)

    def setup_grids(self, template_dict: dict) -> None:
        """Set up grids for single return chart."""
        d = self.drawer
        houses_list = self._get_houses_list(d.first_obj)

        d._setup_main_houses_grid(template_dict, houses_list)
        template_dict["makeSecondaryHousesGrid"] = ""
        d._setup_single_wheel_houses(template_dict, houses_list)
        d._setup_house_sectors(template_dict, houses_list)
        d._setup_gauquelin_sectors(template_dict)
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

    def get_initial_width(self) -> float:
        return self.drawer._DEFAULT_ULTRA_WIDE_WIDTH

    def get_minimum_width(self, wheel_right: float) -> int:
        return max(int(wheel_right), self.drawer._DEFAULT_ULTRA_WIDE_WIDTH // 2)

    def is_dual_wheel(self) -> bool:
        return True

    def get_comparison_point_label(self) -> str:
        return ""

    def get_width_without_comparison(self) -> float:
        d = self.drawer
        if d.double_chart_aspect_grid_type == "table":
            return d._DEFAULT_FULL_WIDTH_WITH_TABLE
        return d._DEFAULT_FULL_WIDTH

    def setup_circles(self, template_dict: dict) -> None:
        """Set up transit-style circles for dual-wheel display."""
        self.drawer._setup_transit_circles(template_dict)

    def setup_aspects(self, template_dict: dict) -> None:
        """Set up aspect list or grid for return chart."""
        d = self.drawer

        if d.double_chart_aspect_grid_type == "list":
            title = self._translate("return_aspects", "Natal to Return Aspects")
            template_dict["makeAspectGrid"] = ""

            if d._is_right_panel_mode():
                rp = d._get_right_panel_aspect_params()
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                    title,
                    d.aspects_list,
                    d.planets_settings,
                    d.aspects_settings,
                    max_columns=7,
                    aspects_per_column=rp["aspects_per_column"],
                    column_width=rp["column_width"],
                    line_height=rp["line_height"],
                    chart_height=d.height,
                    x_offset=rp["x_offset"],
                    y_offset=rp["y_offset"],
                )
            else:
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
            if d._is_right_panel_mode():
                rp = d._get_right_panel_aspect_params()
                grid_x = rp["x_offset"]
                n_active = max(d._count_aspect_grid_planets(), 1)
                box_size = 14
                grid_total_h = (n_active + 1) * box_size
                aspect_list_y = d._vertical_offsets["aspect_list"]
                chart_title_y = d._vertical_offsets.get("title", 0.0)
                target_top = chart_title_y + 20
                grid_y = int(target_top - aspect_list_y + grid_total_h)
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                    d.chart_colors_settings["paper_0"],
                    d._get_aspect_grid_planets_setting(),
                    d.aspects_list,
                    grid_x,
                    grid_y,
                    aspects_settings=d.aspects_settings,
                )
            else:
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                    d.chart_colors_settings["paper_0"],
                    d._get_aspect_grid_planets_setting(),
                    d.aspects_list,
                    550,
                    450,
                    aspects_settings=d.aspects_settings,
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

        template_dict["top_left_0"] = f"{self._return_label(d.second_obj)}:"

        template_dict["top_left_1"] = format_datetime_with_timezone(d.second_obj.iso_formatted_local_datetime)
        template_dict["top_left_2"] = f"{return_lat} / {return_lon}"
        template_dict["top_left_3"] = f"{d.first_obj.name}"
        template_dict["top_left_4"] = format_datetime_with_timezone(d.first_obj.iso_formatted_local_datetime)
        template_dict["top_left_5"] = f"{lat_str} / {lon_str}"

        # Bottom left section
        template_dict["bottom_left_0"] = builder.build_zodiac_info()
        template_dict["bottom_left_1"] = builder.build_domification_info(d.second_obj)
        builder.build_lunar_phase_info(template_dict, d.first_obj)
        template_dict["bottom_left_4"] = builder.build_perspective_info(d.first_obj)

        template_dict["bottom_left_5"] = builder.build_dual_diurnality_info(
            (d.first_obj, self._translate("chart_info_natal_label", "Natal")),
            (d.second_obj, self._return_label(d.second_obj)),
        )

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
        d._setup_house_sectors(template_dict, first_houses, second_houses)
        template_dict["makeGauquelinSectors"] = ""
        d._setup_dual_wheel_planets(template_dict)

        # Planet grid labels
        first_label = d._truncate_name(d.first_obj.name)
        first_grid_title = f"{first_label} ({self._translate('inner_wheel', 'Inner Wheel')})"
        second_grid_title = f"{self._return_label(d.second_obj)} ({self._translate('outer_wheel', 'Outer Wheel')})"

        template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
            planets_and_houses_grid_title="",
            subject_name=first_grid_title,
            available_kerykeion_celestial_points=d.available_kerykeion_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
            show_out_of_bounds=d.show_out_of_bounds,
        )
        template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
            planets_and_houses_grid_title="",
            second_subject_name=second_grid_title,
            second_subject_available_kerykeion_celestial_points=d.second_subject_celestial_points,
            chart_type=d.chart_type,
            text_color=d.chart_colors_settings["paper_0"],
            celestial_point_language=d._language_model.celestial_points,
            show_out_of_bounds=d.show_out_of_bounds,
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
    "Progression": ProgressionChartRenderer,
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
            CSS theme for the chart. Available: 'classic', 'dark', 'dark-high-contrast',
            'light', 'strawberry', 'black-and-white'. If None, no styles applied.
            Defaults to 'classic'.
        double_chart_aspect_grid_type (Literal['list', 'table'], optional):
            Specifies rendering style for double-chart aspect grids. Defaults to 'list'.
        chart_language (KerykeionChartLanguage, optional):
            Language code for chart labels. Defaults to 'EN'.
        language_pack (dict | None, optional):
            Additional translations. For one of the bundled languages the pack
            is merged over that language's defaults (partial packs override
            individual labels). For a NEW language code the pack itself is the
            language: it must be complete (clone the EN block and edit), or
            model validation fails listing the missing fields.
        external_view (bool, optional):
            For Natal charts only: place planets outside the zodiac ring
            (classic style only). Defaults to False.
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
            Show degree indicators on planets (classic style only). Defaults to True.
        show_aspect_icons (bool, optional):
            Show aspect icons on aspect lines (classic style only). Defaults to True.
        style (KerykeionChartStyle, optional):
            Chart wheel style — 'modern' (concentric rings) or 'classic'
            (traditional circles). Defaults to 'modern'.

    Public Methods:
        generate_svg_string(minify=False, remove_css_variables=False) -> str:
            Render the full chart SVG as a string without writing to disk.

        save_svg(output_path=None, filename=None, minify=False, remove_css_variables=False) -> None:
            Generate and write the full chart SVG file to the specified path.
            If output_path is None, saves to the user's home directory.
            If filename is None, uses default pattern:
            '{subject.name} - {chart_type} Chart - {Modern|Classic}.svg'.

        generate_wheel_only_svg_string(minify=False, remove_css_variables=False) -> str:
            Render only the chart wheel (no aspect grid) as an SVG string.

        save_wheel_only_svg_file(output_path=None, filename=None, ...) -> None:
            Generate and write the wheel-only SVG file to the specified path.

        generate_aspect_grid_only_svg_string(minify=False, remove_css_variables=False) -> str:
            Render only the aspect grid as an SVG string.

        save_aspect_grid_only_svg_file(output_path=None, filename=None, ...) -> None:
            Generate and write the aspect-grid-only SVG file to the specified path.

    Example:
        >>> from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory
        >>> from kerykeion.chart_data.factory import ChartDataFactory
        >>> from kerykeion.charts.drawer import ChartDrawer
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
    _TRANSIT_CHART_WITH_TABLE_VIEWBOX = f"0 0 {DEFAULT_DIMENSIONS.full_width_with_table} 546.0"

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

    # Right-panel layout: when more than this many points are active, the
    # aspect list/grid is placed in a full-height right-side panel instead of
    # below the wheel.  This prevents the SVG from becoming excessively wide.
    _RIGHT_PANEL_POINTS_THRESHOLD = 24

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
    active_points: List[Union[AstrologicalPoint, str]]
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
    all_available_planets_setting: List[dict[Any, Any]]
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
        style: "KerykeionChartStyle" = "modern",
        show_zodiac_background_ring: bool = True,
        show_diurnality: bool = True,
        show_motion_state: bool = False,
        show_out_of_bounds: bool = False,
        show_aspect_movement: bool = False,
        show_relationship_score: bool = False,
        show_ayanamsa_value: bool = False,
        show_polar_fallback_note: bool = False,
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
                Additional translations. For one of the bundled languages the
                pack is merged over that language's defaults (partial packs
                override individual labels). For a NEW language code the pack
                itself is the language: it must be complete (clone the EN
                block and edit), or model validation fails listing the
                missing fields.
            external_view (bool, optional):
                Whether to use external visualization (planets on outer ring) for
                single-subject charts. Only applies to Natal charts, and only in
                the classic style — the modern style ignores it and warns.
                Defaults to False.
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
                Whether to show degree indicators on planets (classic style only).
                Defaults to True.
            show_aspect_icons (bool, optional):
                Whether to show aspect icons on aspect lines (classic style only).
                Defaults to True.
            style (KerykeionChartStyle, optional):
                Default chart wheel style — "modern" (concentric rings) or "classic"
                (traditional circles).  This default is used by generate_svg_string(),
                save_svg(), generate_wheel_only_svg_string(), and save_wheel_only_svg_file()
                unless overridden with an explicit ``style=`` argument at render time.
                Defaults to "modern".
            show_zodiac_background_ring (bool, optional):
                Default for whether to draw colored zodiac wedges (modern style only).
                Can be overridden at render time.  Defaults to True.
            show_diurnality (bool, optional):
                Whether to print the chart's diurnality (whether the Sun stood
                above or below the horizon) in the bottom-left info panel.
                Set to False to omit the line; the panel then keeps exactly the
                spacing it had before the line existed. Defaults to True.
            show_motion_state (bool, optional):
                Mark planets at a station on the wheel — "SR" where the
                retrograde phase opens, "SD" where it closes. Defaults to False.
            show_out_of_bounds (bool, optional):
                Badge out-of-bounds planets in the point tables. The badge
                appears only in a table that has at least one such planet.
                Defaults to False.
            show_aspect_movement (bool, optional):
                Dash the aspect lines that are separating, leaving applying
                aspects solid. Defaults to False.
            show_relationship_score (bool, optional):
                Print the synastry relationship score in the info panel. The
                line needs a score on the chart data, which
                ``create_synastry_chart_data`` computes unless asked not to.
                Defaults to False.
            show_ayanamsa_value (bool, optional):
                Append the ayanamsa offset in degrees to the zodiac line of a
                sidereal chart. Defaults to False.
            show_polar_fallback_note (bool, optional):
                Mark the domification line when the requested house system
                could not be used at this latitude and another one stood in
                for it. Defaults to False.

            Every option in this last group is off by default: each one adds
            marks a reader has not asked for, and a chart that gains them
            without being asked is a chart whose look changed under its owner.

        Raises:
            KerykeionException: If ``theme`` is not a valid KerykeionChartTheme
                (and not None), if ``chart_language`` is not a valid
                KerykeionChartLanguage (unless a ``language_pack`` supplies the
                custom language), or if ``double_chart_aspect_grid_type`` is
                not 'list' or 'table'.
        """
        # =====================================================================
        # STEP 1: Store basic configuration parameters
        # =====================================================================
        # Validate the open string parameters up front, mirroring the theme
        # contract below: an unknown language would otherwise silently fall
        # back to EN and an unknown grid type would silently render as
        # "table" — plausible-looking output hiding the caller's mistake.
        # A language_pack legitimizes ANY code: it is the documented way to
        # introduce new languages (e.g. chart_language="JP" + a JP pack).
        if chart_language not in get_args(KerykeionChartLanguage) and language_pack is None:
            raise KerykeionException(
                f"chart_language {chart_language!r} is not available. "
                f"Valid languages: {', '.join(get_args(KerykeionChartLanguage))} — "
                "or supply a language_pack to introduce a custom language."
            )
        if double_chart_aspect_grid_type not in ("list", "table"):
            raise KerykeionException(
                f"double_chart_aspect_grid_type {double_chart_aspect_grid_type!r} is not valid. Use 'list' or 'table'."
            )
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
            style=style,
            show_zodiac_background_ring=show_zodiac_background_ring,
            show_diurnality=show_diurnality,
            show_motion_state=show_motion_state,
            show_out_of_bounds=show_out_of_bounds,
            show_aspect_movement=show_aspect_movement,
            show_relationship_score=show_relationship_score,
            show_ayanamsa_value=show_ayanamsa_value,
            show_polar_fallback_note=show_polar_fallback_note,
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
        # STEP 4b: Create renderer (needed by sizing methods)
        # =====================================================================
        self._renderer = get_chart_renderer(self.chart_type, self)

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
        style: "KerykeionChartStyle",
        show_zodiac_background_ring: bool,
        show_diurnality: bool,
        show_motion_state: bool,
        show_out_of_bounds: bool,
        show_aspect_movement: bool,
        show_relationship_score: bool,
        show_ayanamsa_value: bool,
        show_polar_fallback_note: bool,
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

        # Color and rendering settings (shallow copy — values are immutable strings)
        self.chart_colors_settings = dict(colors_settings)
        self.planets_settings = [dict(body) for body in celestial_points_settings]
        self.aspects_settings = [dict(aspect) for aspect in aspects_settings]

        # Display options
        self.custom_title = custom_title
        self.show_house_position_comparison = show_house_position_comparison
        self.show_cusp_position_comparison = show_cusp_position_comparison
        self.show_degree_indicators = show_degree_indicators
        self.show_aspect_icons = show_aspect_icons
        self.show_diurnality = show_diurnality
        self.auto_size = auto_size
        self._padding = padding

        # Opt-in marks. Every one of these adds something to the chart that the
        # reader did not ask for, so each stays off until it is asked for.
        self.show_motion_state = show_motion_state
        self.show_out_of_bounds = show_out_of_bounds
        self.show_aspect_movement = show_aspect_movement
        self.show_relationship_score = show_relationship_score
        self.show_ayanamsa_value = show_ayanamsa_value
        self.show_polar_fallback_note = show_polar_fallback_note

        # Chart style defaults (can be overridden per-render call)
        self._validate_chart_style(style)
        self._style: "KerykeionChartStyle" = style
        self._show_zodiac_background_ring: bool = show_zodiac_background_ring
        # Classic-only options already reported by _warn_classic_only_options,
        # so a reused drawer warns once per option rather than once per render.
        self._warned_classic_only: set[str] = set()

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
        if not isinstance(chart_data, (SingleChartDataModel, DualChartDataModel)):
            received = type(chart_data).__name__
            hint = ""
            if isinstance(chart_data, (AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel)):
                hint = (
                    " In v5, KerykeionChartSVG was built directly from a subject; in v6, compute the chart data first."
                )
            raise KerykeionException(
                f"ChartDrawer expects chart data from ChartDataFactory "
                f"(SingleChartDataModel or DualChartDataModel), got {received}.{hint}\n"
                "Example:\n"
                "    chart_data = ChartDataFactory.create_natal_chart_data(subject)\n"
                "    svg = ChartDrawer(chart_data).generate_svg_string()\n"
                "Migration guide: https://www.kerykeion.net/content/docs/migration"
            )

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

        # v6: extend settings with dynamic catalog fixed stars from subject.fixed_stars.
        # These stars are NOT in active_points (active_points only carries
        # planets/asteroids/angular points/etc); they live as KerykeionPointModel
        # entries inside subject.fixed_stars and must always render when present.
        from kerykeion.settings.chart_defaults import build_dynamic_fixed_star_settings

        dynamic_star_names: list[str] = []
        for subj in (self.first_obj, self.second_obj):
            if subj is None:
                continue
            for star in getattr(subj, "fixed_stars", None) or []:
                star_name = getattr(star, "name", None)
                if star_name and star_name not in dynamic_star_names:
                    dynamic_star_names.append(star_name)

        if dynamic_star_names:
            # Catalog stars without a static setting → generated on the fly
            # with glyph_id="FixedStar" (build_dynamic_fixed_star_settings skips
            # names that already have a dedicated entry, so the hardcoded 23
            # keep their dedicated colors).
            # The dynamic entries are plain dicts at runtime (TypedDict); widen
            # them to match the list[dict] settings containers they extend.
            extra_star_settings = cast(
                "list[dict[Any, Any]]",
                build_dynamic_fixed_star_settings(
                    dynamic_star_names,
                    existing_settings=self.planets_settings,
                ),
            )
            for setting in extra_star_settings:
                setting["is_active"] = True
            self.planets_settings.extend(extra_star_settings)
            self.available_planets_setting.extend(extra_star_settings)

            # Stars with an existing static setting (e.g. Regulus, Sirius) are
            # not in active_points (the v6 channel is separate) but must still
            # render. Activate them here so the wheel iterates them.
            extra_names_set = {s["name"] for s in extra_star_settings}
            already_active_names = {s["name"] for s in self.available_planets_setting}
            for star_name in dynamic_star_names:
                if star_name in extra_names_set or star_name in already_active_names:
                    continue
                for body in self.planets_settings:
                    if body["name"] == star_name:
                        body["is_active"] = True
                        self.available_planets_setting.append(body)
                        break

        # User-selected midpoints share the dynamic-channel mechanism
        # with fixed_stars: they live in subject.active_midpoints and the
        # drawer materialises a synthetic celestial-point setting for each.
        from kerykeion.settings.chart_defaults import build_dynamic_midpoint_settings

        _seen_midpoints: dict[str, None] = {}
        for subj in (self.first_obj, self.second_obj):
            if subj is None:
                continue
            for mp in getattr(subj, "active_midpoints", None) or []:
                mp_name = getattr(mp, "name", None)
                if mp_name:
                    _seen_midpoints[mp_name] = None
        dynamic_midpoint_names: list[str] = list(_seen_midpoints)

        if dynamic_midpoint_names:
            # Same runtime dict widening as for the dynamic fixed stars above.
            extra_midpoint_settings = cast(
                "list[dict[Any, Any]]",
                build_dynamic_midpoint_settings(
                    dynamic_midpoint_names,
                    existing_settings=self.planets_settings,
                ),
            )
            for setting in extra_midpoint_settings:
                setting["is_active"] = True
            self.planets_settings.extend(extra_midpoint_settings)
            self.available_planets_setting.extend(extra_midpoint_settings)

            extra_names = {s["name"] for s in extra_midpoint_settings}
            active_names = {s["name"] for s in self.available_planets_setting}
            for mp_name in dynamic_midpoint_names:
                if mp_name in extra_names or mp_name in active_names:
                    continue
                for body in self.planets_settings:
                    if body["name"] == mp_name:
                        body["is_active"] = True
                        self.available_planets_setting.append(body)
                        break

        # This list is the union of renderable settings across both subjects.
        # Keep it available for lookups, but scope the per-subject settings below
        # to the points actually collected for that subject; dual charts may have
        # dynamic stars or midpoints on only one side.
        all_available_planets_setting = list(self.available_planets_setting)

        # Collect KerykeionPointModel objects for the primary subject
        available_celestial_points_names = [body["name"].lower() for body in all_available_planets_setting]
        self.available_kerykeion_celestial_points = self._collect_subject_points(
            self.first_obj,
            available_celestial_points_names,
        )
        first_collected_names = {p.name for p in self.available_kerykeion_celestial_points if p is not None}
        self.available_planets_setting = [
            body for body in all_available_planets_setting if body["name"] in first_collected_names
        ]
        self.all_available_planets_setting = all_available_planets_setting

        # Warn about potential crowding with many active points (planets only;
        # fixed stars are excluded from the crowding heuristic since they have
        # their own visibility filter).
        active_dynamic_star_names = {
            body["name"] for body in self.available_planets_setting if body["name"] in dynamic_star_names
        }
        active_points_count = len(self.available_planets_setting) - len(active_dynamic_star_names)
        if active_points_count > 24:
            logger.warning(
                "ChartDrawer detected %s active celestial points; rendering may look crowded beyond 24.",
                active_points_count,
            )

        # Collect points for secondary subject (dual-wheel charts only)
        # These appear on the outer wheel in Transit, Synastry, and DualReturnChart
        self.second_subject_celestial_points: list[KerykeionPointModel] = []
        self.second_subject_available_planets_setting: list[dict[Any, Any]] = []
        if self.second_obj is not None:
            self.second_subject_celestial_points = self._collect_subject_points(
                self.second_obj,
                available_celestial_points_names,
            )
            # v6: align the secondary settings list to the points that the
            # second subject actually populated. If the natal subject has all
            # 9 active_points but the return subject only computed 7 of them
            # (e.g. an angle could not be derived for the new location), the
            # downstream drawing code would iterate len(settings)=9 against
            # positions=7 and IndexError. Filtering the settings here keeps
            # the two lists symmetric.
            second_collected_names = {p.name for p in self.second_subject_celestial_points if p is not None}
            self.second_subject_available_planets_setting = [
                body for body in all_available_planets_setting if body["name"] in second_collected_names
            ]

    def _configure_dimensions_and_geometry(self, chart_data: "ChartDataModel") -> None:
        """
        Configure chart dimensions and wheel geometry.

        This method sets up:
        - Aspects list from chart data
        - Initial height (may be adjusted later)
        - Location information (city, lat/lon)
        - Chart width based on chart type
        - Circle radii based on chart type and view mode
        - Grid shift for multi-column planet grids
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

        # Calculate horizontal shift for planet/house grids when multi-column
        # layout would overlap the chart wheel.
        # Only apply in auto_size mode; fixed-width charts use preset dimensions.
        self._grid_x_shift = self._calculate_grid_x_shift() if self.auto_size else 0

        # Adjust width if house comparison grid is hidden
        self._apply_house_comparison_width_override()

    def _calculate_grid_x_shift(self) -> int:
        """Calculate horizontal shift to prevent multi-column planet grids from overlapping the wheel.

        When many celestial points are active (> 20), the planet grid splits into
        multiple columns that grow leftward from the default x position. If the
        leftmost column would overlap the chart wheel, the entire grid block
        (planet grid + house grid) is shifted rightward.

        This only applies to single-wheel chart types (Natal, Composite, SingleReturn).
        Double-wheel charts use a single-column layout and are not affected.

        Returns:
            Number of pixels to shift grids rightward (0 if no shift needed).
        """
        if self._renderer.is_dual_wheel():
            return 0

        from kerykeion.charts.utils import (
            _GAUQUELIN_MAX_ROWS,
            _SECOND_COLUMN_THRESHOLD,
            _gauquelin_grid_thresholds,
            _select_planet_grid_thresholds,
        )

        # Check if Gauquelin mode is active
        has_gauquelin = any(
            hasattr(p, "gauquelin_sector") and p.gauquelin_sector is not None
            for p in self.available_kerykeion_celestial_points
        )

        if has_gauquelin:
            n_gauq = sum(
                1
                for p in self.available_kerykeion_celestial_points
                if hasattr(p, "gauquelin_sector") and p.gauquelin_sector is not None
            )
            if n_gauq <= _GAUQUELIN_MAX_ROWS:
                return 0
            col_width = gauquelin_column_width(self._gauquelin_grid_carries_oob_badges())
            thresholds = _gauquelin_grid_thresholds(n_gauq)
            n = n_gauq
        else:
            n = self._count_active_planets()
            if n <= _SECOND_COLUMN_THRESHOLD:
                return 0
            # The grid sizes its own columns from the names it prints, so the
            # estimator has to ask the same question — reserving the fixed
            # stride while the grid draws a wider one clips the last column.
            col_width = planet_grid_column_width(
                [
                    get_decoded_kerykeion_celestial_point_name(
                        point["name"], self._language_model.celestial_points
                    )
                    for point in self.available_kerykeion_celestial_points
                ],
                self.show_out_of_bounds,
            )
            thresholds = _select_planet_grid_thresholds(self.chart_type, n)

        # Determine how many columns will be used
        if n <= thresholds[0]:
            num_cols = 1
        elif n <= thresholds[1]:
            num_cols = 2
        elif n <= thresholds[2]:
            num_cols = 3
        else:
            num_cols = 4

        if num_cols <= 1:
            return 0

        # Wheel right edge + gap
        wheel_right = 100 + (2 * self.main_radius)  # 100 (translate-x) + diameter
        gap = 20  # Minimum gap between wheel and leftmost column

        # Leftmost column position without shift
        leftmost_x = self._MAIN_PLANET_GRID_X - (num_cols - 1) * col_width

        overlap = (wheel_right + gap) - leftmost_x
        return max(0, int(overlap))

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
        primary = sum(1 for p in self.available_planets_setting if p.get("is_active"))
        if self.second_obj is None:
            return primary
        secondary = sum(1 for p in self.second_subject_available_planets_setting if p.get("is_active"))
        return max(primary, secondary)

    def _get_aspect_grid_planets_setting(self) -> list[dict[Any, Any]]:
        """Return the settings list used to draw aspect grids."""
        if self._renderer.is_dual_wheel():
            return self.all_available_planets_setting
        return self.available_planets_setting

    def _count_aspect_grid_planets(self) -> int:
        """Return number of active points that need rows/columns in an aspect grid."""
        return sum(1 for p in self._get_aspect_grid_planets_setting() if p.get("is_active"))

    def _is_right_panel_mode(self) -> bool:
        """Whether the aspect list/grid should be placed in a right-side panel.

        Activates only for dual-wheel chart types with many active points.
        Charts with <= _RIGHT_PANEL_POINTS_THRESHOLD points keep the standard
        bottom-anchored layout so that default charts remain unchanged.
        """
        if not self._renderer.is_dual_wheel():
            return False
        # "table" draws an NxN grid sized on the union of both subjects, so the
        # decision uses the union count. "list" anchors against the taller of the
        # two per-subject columns, so max(primary, secondary) is the right metric.
        if self.double_chart_aspect_grid_type == "table":
            return self._count_aspect_grid_planets() > self._RIGHT_PANEL_POINTS_THRESHOLD
        return self._count_active_planets() > self._RIGHT_PANEL_POINTS_THRESHOLD

    def _estimate_left_content_right_edge(self) -> float:
        """Estimate the rightmost X extent of all content EXCEPT the aspect list.

        Used to determine where the right-panel aspect list should start.
        Returns the X coordinate in the SVG coordinate system (before viewBox halving).
        """
        grid_shift = getattr(self, "_grid_x_shift", 0)

        extents: list[float] = []

        # Wheel footprint: translate(100, ...) + diameter
        wheel_right = 100 + (2 * self.main_radius)
        extents.append(wheel_right)

        # Main planet grid
        extents.append(645 + grid_shift + 80)
        # Main houses grid
        extents.append(750 + grid_shift + 120)

        if self._renderer.is_dual_wheel():
            # Secondary planet grid
            extents.append(910 + 80)

        if self.chart_type in ("Synastry", "DualReturnChart"):
            # Secondary houses grid
            extents.append(1015 + 120)

        if self.chart_type == "Synastry":
            if self.show_house_position_comparison or self.show_cusp_position_comparison:
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

                extents.append(1090 + first_grid_width)
                extents.append(1290 + second_grid_width)

                if self.show_cusp_position_comparison:
                    max_house_right = max(1090 + first_grid_width, 1290 + second_grid_width)
                    cusp_block_width = 160.0 * 2.0
                    extents.append(max_house_right + 50.0 + cusp_block_width + 45.0)

        comparison_point_label = self._renderer.get_comparison_point_label()
        comparison_cusp_label = self._renderer.get_comparison_cusp_label()
        comparison_label = max(filter(None, [comparison_point_label, comparison_cusp_label]), key=len, default="")
        if comparison_label:
            if self.show_house_position_comparison or self.show_cusp_position_comparison:
                transit_columns = [
                    comparison_label,
                    self._translate("house_position", "House Position"),
                ]
                transit_grid_width = self._estimate_house_comparison_grid_width(
                    column_labels=transit_columns,
                    include_radix_column=False,
                    include_title=True,
                    minimum_width=170.0,
                )
                house_right = 980 + transit_grid_width
                if self.show_house_position_comparison:
                    extents.append(house_right)
                if self.show_cusp_position_comparison:
                    if self.show_house_position_comparison:
                        extents.append(house_right + 40.0 + 260.0)
                    else:
                        extents.append(house_right)

        if self.chart_type == "DualReturnChart":
            if self.show_house_position_comparison or self.show_cusp_position_comparison:
                first_subject_label = self._translate("Natal", "Natal")
                key, default = return_label_keys(self.second_obj)
                second_subject_label = self._translate(key, default)
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

                extents.append(1090 + first_grid_width)
                extents.append(1290 + second_grid_width)

                if self.show_cusp_position_comparison:
                    max_house_right = max(1090 + first_grid_width, 1290 + second_grid_width)
                    cusp_block_width = 160.0 * 2.0
                    extents.append(max_house_right + 50.0 + cusp_block_width + 45.0)

        return max(extents)

    def _get_right_panel_aspect_params(self) -> dict:
        """Compute layout parameters for the right-panel aspect list.

        When many celestial points are active, the aspect list is placed in a
        full-height panel on the right side of the chart instead of being
        bottom-anchored below the wheel.

        Returns a dict with keys:
            x_offset:  horizontal origin for the aspect list group
            y_offset:  vertical origin for the aspect list group
            aspects_per_column:  number of rows per column (uses full height)
        """
        # The Aspect_List SVG group is translated by:
        #   translate(50, $aspect_list_translate_y)
        # where aspect_list_translate_y = self._vertical_offsets["aspect_list"]
        #
        # Content inside draw_transit_aspect_list is wrapped in:
        #   <g transform="translate(x_offset, y_offset)">
        #
        # So the absolute SVG position of the first aspect row is:
        #   abs_x = 50 + x_offset
        #   abs_y = aspect_list_translate_y + y_offset
        #
        # We want the list to start near the top of the SVG and extend to
        # the bottom, positioned to the right of all other content.

        aspect_list_translate_y = self._vertical_offsets["aspect_list"]

        # Where the left content ends (in absolute SVG coords)
        left_edge = self._estimate_left_content_right_edge()

        # The Aspect_List group already has translate(50, ...) from the template
        parent_group_x = 50.0
        gap = 30.0  # gap between left content and aspect list

        x_offset = int(left_edge - parent_group_x + gap)

        # Align the aspect list title with the chart title.
        # The title text inside draw_transit_aspect_list is rendered at
        # (y_offset - 15) relative to the Aspect_List group origin.
        # Absolute title position = aspect_list_translate_y + y_offset - 15
        # We want this to match the chart title offset.
        chart_title_y = self._vertical_offsets.get("title", 0.0)
        # Add a small offset so the aspect title sits just below the chart title
        target_title_y = chart_title_y + 18.0
        # y_offset such that aspect_list_translate_y + y_offset - 15 = target_title_y
        y_offset = int(target_title_y + 15 - aspect_list_translate_y)
        top_margin = target_title_y

        # For shorter charts (Transit, DualReturn at ~876px) use compact spacing
        # to avoid an excessively wide aspect list.
        if self.height < 1000:
            line_height = 12
            column_width = 85
        else:
            line_height = 14
            column_width = 100

        # Calculate how many rows fit in the full height
        bottom_margin = 40
        usable_height = self.height - bottom_margin - top_margin
        aspects_per_column = max(14, int(usable_height / line_height))

        return {
            "x_offset": x_offset,
            "y_offset": y_offset,
            "aspects_per_column": aspects_per_column,
            "line_height": line_height,
            "column_width": column_width,
        }

    def _get_chart_width(self) -> float:
        """Determine the appropriate chart width based on chart type and display options.

        Returns:
            float: The width in pixels for the SVG canvas.
        """
        return self._renderer.get_initial_width()

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

        # Double-wheel charts (Synastry, Transit, DualReturnChart) use single-column
        # planet grids that grow vertically at ~15px per row. They share the same
        # height/offset logic which accounts for right-panel mode and the taller
        # row spacing. Single-wheel charts fall through to the generic logic below.
        if self._renderer.is_dual_wheel():
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

        # Calculate extra height needed for additional points.
        # Even with balanced multi-column planet grids, the triangular aspect
        # grid (single-wheel charts) still scales with total active points,
        # so height must accommodate the full point count.
        #
        # The triangular aspect grid uses 14px boxes and grows upward from y=468.
        # Its absolute top is: (default_aspect_offset + delta_height) + (468 - 14*n).
        # Ensure this stays within the viewbox (>= -VERTICAL_PADDING_TOP).
        extra_points = active_points_count - 20
        row_based_height = extra_points * self._ROW_HEIGHT  # 8px per additional point
        aspect_grid_min_delta = max(0, 14 * active_points_count - 468 - 50 - self._VERTICAL_PADDING_TOP)
        extra_height = max(row_based_height, aspect_grid_min_delta)

        self.height = max(self.height, minimum_height + extra_height)

        delta_height = max(self.height - minimum_height, 0)

        # Top elements get a partial shift to maintain visual balance
        # The shift is capped at _MAX_TOP_SHIFT (80px) to prevent excessive spacing
        shift = min(extra_points * self._TOP_SHIFT_FACTOR, self._MAX_TOP_SHIFT)
        top_shift = shift // 2  # Title shifts less than grids

        offsets["grid"] += shift
        offsets["title"] += top_shift
        offsets["elements"] += top_shift
        offsets["qualities"] += top_shift

        # Bottom-anchored elements shift down by the full delta
        # This keeps them "pinned" to the bottom of the SVG
        offsets["wheel"] += delta_height
        offsets["aspect_grid"] += delta_height
        offsets["lunar_phase"] += delta_height
        offsets["bottom_left"] += delta_height

        # In right-panel mode the aspect list is positioned at the top of the
        # SVG (full-height right side), so it must NOT be pushed down.
        if not self._is_right_panel_mode():
            offsets["aspect_list"] += delta_height

        self._vertical_offsets = offsets

    def _adjust_height_for_extended_aspect_columns(self) -> None:
        """Ensure tall aspect columns fit within the SVG for double-chart lists.

        When displaying many aspects in list mode for dual-wheel charts,
        columns beyond the 11th one extend upward beyond the normal bounds.
        This method calculates the required height to accommodate these
        extended columns without clipping.

        In right-panel mode the aspect list uses full chart height from the
        top, so no additional height adjustment is necessary.

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

        if not self._renderer.is_dual_wheel():
            return

        # In right-panel mode the aspect list starts near the top of the SVG
        # and uses all the available height, so no extension adjustment needed.
        if self._is_right_panel_mode():
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

        In right-panel mode the wheel (x:100-580) and grids (x:645+) occupy
        different horizontal ranges, so they can overlap vertically.  This
        produces a significantly shorter chart.
        """
        base_rows = 14  # Up to 16 active points fit without extra height
        extra_rows = max(active_points_count - base_rows, 0)

        synastry_row_height = 15
        comparison_padding_per_row = 4  # Keeps house comparison grids within view.

        # Move title up for synastry charts
        offsets["title"] = -10

        # -----------------------------------------------------------------
        # Compute grid / title position shifts (identical for all modes)
        # -----------------------------------------------------------------
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

        # -----------------------------------------------------------------
        # Right-panel mode: allow wheel / grid vertical overlap
        # -----------------------------------------------------------------
        if self._is_right_panel_mode():
            # Grid content bottom (tallest grid = house comparison)
            grid_content_bottom = offsets["grid"] + active_points_count * synastry_row_height + 50

            # Wheel needs approximately 2 * radius + 30px for degree labels
            wheel_diameter = 2 * self.main_radius + 30

            # Position wheel so its bottom aligns with grid content bottom
            wheel_offset = max(50.0, grid_content_bottom - wheel_diameter)
            offsets["wheel"] = wheel_offset
            offsets["aspect_grid"] = wheel_offset

            # Height = tallest content + bottom margin
            content_bottom = max(grid_content_bottom, wheel_offset + wheel_diameter)
            self.height = max(self.height, int(content_bottom + 40))

            # Position bottom-anchored elements relative to the new height
            delta = max(self.height - minimum_height, 0)
            offsets["lunar_phase"] = 518.0 + delta
            offsets["bottom_left"] = delta

            self._vertical_offsets = offsets
            return

        # -----------------------------------------------------------------
        # Standard mode: stack wheel below grids
        # -----------------------------------------------------------------
        extra_height = extra_rows * (synastry_row_height + comparison_padding_per_row)
        self.height = max(self.height, minimum_height + extra_height)
        delta_height = max(self.height - minimum_height, 0)

        offsets["wheel"] += delta_height
        offsets["aspect_grid"] += delta_height
        offsets["lunar_phase"] += delta_height
        offsets["bottom_left"] += delta_height
        offsets["aspect_list"] += delta_height

        self._vertical_offsets = offsets

    def _collect_subject_points(
        self,
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        point_attribute_names: list[str],
    ) -> list[KerykeionPointModel]:
        """Collect ordered active celestial points for a subject.

        Looks up points by attribute name first; for fixed stars (v6 unified
        array, not subject attributes) falls back to ``subject.fixed_stars``
        lookup by case/separator-insensitive name match.
        """

        # Build a quick lookup over subject.fixed_stars by normalized slug
        star_lookup: dict[str, KerykeionPointModel] = {}
        for star in getattr(subject, "fixed_stars", None) or []:
            star_name = getattr(star, "name", None)
            if not star_name:
                continue
            slug = star_name.strip().lower().replace(" ", "_").replace("-", "_")
            star_lookup[slug] = star

        # Same idea for active midpoints (live as a separate array, not as
        # attributes on the subject).
        midpoint_lookup: dict[str, KerykeionPointModel] = {}
        for mp in getattr(subject, "active_midpoints", None) or []:
            mp_name = getattr(mp, "name", None)
            if not mp_name:
                continue
            slug = mp_name.strip().lower().replace(" ", "_").replace("-", "_")
            midpoint_lookup[slug] = mp

        collected: list[KerykeionPointModel] = []

        for raw_name in point_attribute_names:
            attr_name = raw_name if hasattr(subject, raw_name) else raw_name.lower()
            point = getattr(subject, attr_name, None)
            if point is None:
                slug = raw_name.strip().lower().replace(" ", "_").replace("-", "_")
                point = star_lookup.get(slug) or midpoint_lookup.get(slug)
            if point is None:
                continue
            collected.append(point)

        return collected

    def _apply_house_comparison_width_override(self) -> None:
        """Shrink chart width when the optional house comparison grid is hidden."""
        if self.show_house_position_comparison or self.show_cusp_position_comparison:
            return

        if self._renderer.is_dual_wheel():
            self.width = self._renderer.get_width_without_comparison()

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

        n = max(self._count_aspect_grid_planets(), 1)

        if self._renderer.is_dual_wheel():
            # Full NxN grid
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

        n_active = max(self._count_aspect_grid_planets(), 1)

        # Common grids present on many chart types
        # Apply grid shift when multi-column layout would overlap the wheel
        grid_shift = getattr(self, "_grid_x_shift", 0)

        has_gauquelin = any(
            hasattr(p, "gauquelin_sector") and p.gauquelin_sector is not None
            for p in self.available_kerykeion_celestial_points
        )

        if has_gauquelin:
            # Unified Gauquelin grid replaces both planet and house grids
            main_grid_right = 645 + grid_shift + gauquelin_column_width(
                self._gauquelin_grid_carries_oob_badges()
            )
            extents.append(main_grid_right)
        else:
            main_planet_grid_right = 645 + grid_shift + 80
            main_houses_grid_right = 750 + grid_shift + 120
            extents.extend([main_planet_grid_right, main_houses_grid_right])

        if self.chart_type in ("Natal", "Composite", "SingleReturnChart"):
            # Triangular aspect grid at x_start=510+grid_shift (inside translate(35,...))
            aspect_grid_right = 560 + grid_shift + 14 * n_active
            extents.append(aspect_grid_right)

        if self._renderer.is_dual_wheel():
            # Double-chart aspects placement
            if self._is_right_panel_mode():
                # Right-panel mode: aspect list/grid starts after left content
                rp = self._get_right_panel_aspect_params()
                parent_group_x = 50.0  # Aspect_List group translate(50, ...)
                if self.double_chart_aspect_grid_type == "list":
                    total_aspects = len(self.aspects_list) if hasattr(self, "aspects_list") else 0
                    per_col = max(rp["aspects_per_column"], 1)
                    columns = max(1, ceil(total_aspects / per_col))
                    aspect_right = parent_group_x + rp["x_offset"] + (columns * rp["column_width"])
                    extents.append(aspect_right)
                else:
                    # Grid table: NxN grid at the right-panel position
                    grid_width = 14 * (n_active + 1)
                    aspect_right = parent_group_x + rp["x_offset"] + grid_width
                    extents.append(aspect_right)
            else:
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

            if self.chart_type in ("Synastry", "DualReturnChart"):
                # Secondary houses grid default x ~ 1015
                secondary_houses_grid_right = 1015 + 120
                extents.append(secondary_houses_grid_right)

            if self.chart_type == "Synastry":
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

            comparison_point_label = self._renderer.get_comparison_point_label()
            comparison_cusp_label = self._renderer.get_comparison_cusp_label()
            comparison_label = max(filter(None, [comparison_point_label, comparison_cusp_label]), key=len, default="")
            if comparison_label:
                if self.show_house_position_comparison or self.show_cusp_position_comparison:
                    transit_columns = [
                        comparison_label,
                        self._translate("house_position", "House Position"),
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
                    key, default = return_label_keys(self.second_obj)
                    second_subject_label = self._translate(key, default)
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
        """Very rough text width estimation in pixels based on font size.

        KNOWN DIVERGENCE, deliberately left: this is *not*
        :func:`estimate_text_width`, the per-character table used to fit the info
        panel's diurnality row. This one sizes the planet grid, the legend and
        the auto-size canvas, and its 0.7-of-the-em average under-reports
        ideographs by about 30% while over-reporting narrow Latin.

        Pointing it at the measured table is the right fix and was tried here —
        it is a **layout change**, not a cleanup: 32 baselines moved, one canvas
        from 1244px to 1177px. That belongs in a change about grid geometry,
        where the narrowing can be reviewed against the fact that neither
        ``chart.xml`` nor the themes declare a font-family, so a viewer with a
        wider default has only this estimate's generosity as its margin.
        """
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
        wheel_right = 100 + (2 * self.main_radius) + self._padding
        return self._renderer.get_minimum_width(wheel_right)

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
        elif self.chart_type in ("Transit", "DualReturnChart", "Progression") and self.second_obj:
            # Use location from the second subject (transit/return/progressed)
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

        theme_dir = _MODULE_DIR / "themes"

        self.color_style_tag = _load_cached_file(str(theme_dir / f"{theme}.css"))

    def _load_language_settings(
        self,
        language_pack: Optional[Mapping[str, Any]],
    ) -> None:
        """Resolve language models for the requested chart language."""
        overrides = {self.chart_language: dict(language_pack)} if language_pack else None
        # Materialize only the selected language + English fallback, not the whole
        # ~10-language table (load_language_pair avoids the full-table deepcopy).
        base_data, fallback_data = load_language_pair(self.chart_language, overrides)  # type: ignore[arg-type]

        if not fallback_data:
            raise KerykeionException("English translations are missing from LANGUAGE_SETTINGS.")

        selected_model = KerykeionLanguageModel(**base_data)
        if base_data is fallback_data:
            # The common EN / unknown-language case: load_language_pair returns the
            # same English dict for both selected and fallback. Build the model and
            # dump it once instead of twice — get_translations consults the shared
            # dict for both primary and fallback, so reusing the object is safe.
            fallback_model = selected_model
            selected_dump = selected_model.model_dump()
            fallback_dump = selected_dump
        else:
            fallback_model = KerykeionLanguageModel(**fallback_data)
            selected_dump = selected_model.model_dump()
            fallback_dump = fallback_model.model_dump()

        self._fallback_language_model = fallback_model
        self._language_model = selected_model
        self._fallback_language_dict = fallback_dump
        self._language_dict = selected_dump
        self.language_settings = self._language_dict  # Backward compatibility

    def _translate(self, key: str, default: Any) -> Any:
        # Resolve against the selected language, then the (English) fallback model
        # dump, in a single pass — get_translations consults fallback_dict before
        # its built-in English defaults, preserving the previous two-call precedence
        # while avoiding the redundant second call and dotted-key split per label.
        return get_translations(
            key,
            default,
            language_dict=self._language_dict,
            fallback_dict=self._fallback_language_dict,
        )

    def _get_zodiac_info(self) -> str:
        """
        Generate the zodiac/ayanamsa info string for display in bottom_left section.

        Returns:
            str: Localized zodiac type description (Tropical or Ayanamsa mode).
        """
        if self.first_obj.zodiac_type == "Tropical":
            return f"{self._translate('zodiac', 'Zodiac')}: {self._translate('tropical', 'Tropical')}"
        else:
            # A sidereal subject always carries a concrete sidereal_mode (enforced by
            # the AstrologicalBaseModel validator), so the displayed ayanamsa reflects
            # the mode actually used for the positions — no fallback needed.
            mode_const = "SIDM_" + self.first_obj.sidereal_mode  # type: ignore[operator]
            mode_name = ephe.get_ayanamsa_name(getattr(ephe, mode_const))
            line = f"{self._translate('ayanamsa', 'Ayanamsa')}: {mode_name}"
            # The mode names the convention; the offset says where it actually
            # put the zodiac for this date, which is what differs between two
            # charts drawn under the same ayanamsa centuries apart.
            #
            # That difference is exactly why a dual wheel cannot always show
            # one: this line has no ring label, so printing the first subject's
            # offset on a chart whose second subject has another one states
            # something false about the outer wheel. The rendered strings are
            # what is compared rather than the floats — two offsets that round
            # to the same degrees and minutes are the same claim on this line,
            # and hiding the value for a difference no reader could see would
            # be its own kind of dishonesty.
            value = getattr(self.first_obj, "ayanamsa_value", None)
            if self.show_ayanamsa_value and value is not None and self.second_obj is not None:
                second_value = getattr(self.second_obj, "ayanamsa_value", None)
                if second_value is None or convert_decimal_to_degree_string(
                    second_value, "2"
                ) != convert_decimal_to_degree_string(value, "2"):
                    return line
            if self.show_ayanamsa_value and value is not None:
                # Degrees and minutes, not seconds: the info panel escapes its
                # own text, and the seconds symbol is already an entity — it
                # would reach the reader as a literal &quot;.
                line += f" ({convert_decimal_to_degree_string(value, '2')})"
            return line

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
        # Shift the aspect grid rightward by the same amount as the planet/house
        # grids so multi-column Gauquelin layouts don't overlap it.
        aspect_x = 510 + self._grid_x_shift
        template_dict["makeAspectGrid"] = draw_aspect_grid(
            self.chart_colors_settings["paper_0"],
            self.available_planets_setting,
            self.aspects_list,
            x_start=aspect_x,
            aspects_settings=self.aspects_settings,
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
            # Same anchor as Synastry/DualReturn (550, 450): (600, 520) would
            # push the glyph header row past the 565-unit viewBox bottom.
            template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self._get_aspect_grid_planets_setting(),
                self.aspects_list,
                self._TRANSIT_ASPECT_GRID_X,
                self._TRANSIT_ASPECT_GRID_Y,
                aspects_settings=self.aspects_settings,
            )
        template_dict["makeAspects"] = self._draw_all_aspects_lines(self.main_radius, self.main_radius - 160)

    def _axis_cusp_colors(self) -> tuple[str, str, str, str]:
        """Resolve the (ASC, MC, DSC, IC) cusp colors by point name.

        Looks the axis colors up by name in ``planets_settings`` rather than by
        fixed position, so custom ``celestial_points_settings`` (different order
        or length) cannot raise ``IndexError`` or assign the wrong color. Falls
        back to the standard radix cusp color when an axis is missing.
        """
        fallback = self.chart_colors_settings["houses_radix_line"]
        # ``AXIAL_POINTS`` (config_constants) is the codebase-wide single source
        # of truth for the four angles, in ASC/MC/DSC/IC order — reuse it for
        # both the filter and the returned order. Collect only the four axis
        # colors by name (not the whole ~40-entry planets_settings list) — this
        # runs once per chart render. Use `or fallback` (not get's default) so an
        # entry that explicitly carries color=None (or "") still resolves to the
        # standard cusp color instead of emitting an invalid `stroke:None` into
        # the SVG.
        color_by_name = {
            name: (p.get("color") or fallback) for p in self.planets_settings if (name := p.get("name")) in AXIAL_POINTS
        }
        return tuple(color_by_name.get(name, fallback) for name in AXIAL_POINTS)  # type: ignore[return-value]

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
        asc_color, mc_color, dsc_color, ic_color = self._axis_cusp_colors()
        template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
            r=self.main_radius,
            first_subject_houses_list=houses_list,
            standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
            first_house_color=asc_color,  # ASC color
            tenth_house_color=mc_color,  # MC color
            seventh_house_color=dsc_color,  # DSC color
            fourth_house_color=ic_color,  # IC color
            c1=self.first_circle_radius,  # Outer boundary for cusp lines
            c3=self.third_circle_radius,  # Inner boundary for cusp lines
            chart_type=self.chart_type,
            external_view=self.external_view,
        )

    def _setup_house_sectors(
        self, template_dict: dict, houses_list: list, second_houses_list: list | None = None
    ) -> None:
        """Populate template_dict with transparent house sector wedges for interactive highlighting.

        For dual charts, when second_houses_list is provided, renders two sets of sectors:
        - Subject 1 (horoscope="0"): inner area (r-72 to r-160)
        - Subject 2 (horoscope="1"): outer area (r-36 to r-72), oriented using Subject 1's wheel
        """
        is_dual = second_houses_list is not None and self._renderer.is_dual_wheel()
        sectors = draw_house_sectors(
            r=self.main_radius,
            houses_list=houses_list,
            c1=self.first_circle_radius,
            c3=self.third_circle_radius,
            chart_type=self.chart_type,
            external_view=self.external_view,
            horoscope_id="0" if is_dual else None,
        )
        if is_dual and second_houses_list is not None:
            sectors += draw_house_sectors(
                r=self.main_radius,
                houses_list=second_houses_list,
                c1=self.first_circle_radius,
                c3=self.third_circle_radius,
                chart_type=self.chart_type,
                external_view=self.external_view,
                horoscope_id="1",
                seventh_house_abs_override=houses_list[6].abs_pos,
                outer_r_offset=36,
                inner_r_offset=72,
            )
        template_dict["makeHouseSectors"] = sectors

    def _setup_gauquelin_sectors(self, template_dict: dict) -> None:
        """Replace house lines with 36 Gauquelin sectors when active.

        When any planet has a gauquelin_sector value, the standard 12-house
        cusp lines in ``makeHouses`` are replaced by 36 sector divisions.
        The sectors use the same radii as houses so they occupy the same
        visual ring.
        """
        has_gauquelin = False
        for point in self.available_kerykeion_celestial_points:
            if hasattr(point, "gauquelin_sector") and point.gauquelin_sector is not None:
                has_gauquelin = True
                break

        if has_gauquelin:
            from kerykeion.charts.utils import (
                draw_gauquelin_sector_hit_areas,
                draw_gauquelin_sectors,
            )

            gauq_cusps = getattr(self.first_obj, "gauquelin_sector_cusps", None)

            # Replace houses with Gauquelin sectors
            template_dict["makeHouses"] = draw_gauquelin_sectors(
                r=self.main_radius,
                inner_r=self.first_circle_radius,
                outer_r=self.third_circle_radius,
                seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                color=self.chart_colors_settings["houses_radix_line"],
                gauquelin_cusps=gauq_cusps,
            )
            # Clear the 12-house invisible hit-area wedges: in Gauquelin mode the
            # visible ring is 36 sectors, so the 12-wedge geometry would mislead
            # any frontend using makeHouseSectors for click/hover targeting.
            template_dict["makeHouseSectors"] = ""
            # Emit 36 transparent clickable wedges so the frontend can focus
            # individual Gauquelin sectors (mirrors the HouseSector convention).
            template_dict["makeGauquelinSectors"] = draw_gauquelin_sector_hit_areas(
                r=self.main_radius,
                c1=self.first_circle_radius,
                c3=self.third_circle_radius,
                seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                gauquelin_cusps=gauq_cusps,
            )
        else:
            template_dict["makeGauquelinSectors"] = ""

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
        asc_color, mc_color, dsc_color, ic_color = self._axis_cusp_colors()
        template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
            r=self.main_radius,
            first_subject_houses_list=first_houses_list,
            standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
            first_house_color=asc_color,  # ASC color
            tenth_house_color=mc_color,  # MC color
            seventh_house_color=dsc_color,  # DSC color
            fourth_house_color=ic_color,  # IC color
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
            show_motion_state=self.show_motion_state,
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
            second_subject_available_planets_setting=self.second_subject_available_planets_setting,
            radius=self.main_radius,
            main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
            main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
            chart_type=self.chart_type,
            third_circle_radius=self.third_circle_radius,
            external_view=self.external_view,
            second_circle_radius=self.second_circle_radius,
            show_degree_indicators=self.show_degree_indicators,
            show_motion_state=self.show_motion_state,
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
            template_dict["makeLunarPhase"] = make_lunar_phase(subject.lunar_phase["degrees_between_s_m"], latitude)
        else:
            template_dict["makeLunarPhase"] = ""

    def _setup_main_houses_grid(self, template_dict: dict, houses_list: list) -> None:
        """
        Populate template_dict with the main houses grid table.

        Creates the tabular display of house cusps for the primary subject.
        When Gauquelin sectors are active, replaces the 12-cusp table with
        a sector table showing each planet's Gauquelin sector number (1-36).

        Args:
            template_dict: Dictionary to populate with grid SVG elements.
            houses_list: List of house data from the subject.
        """
        # Check if Gauquelin sectors are active
        has_gauquelin = any(
            hasattr(p, "gauquelin_sector") and p.gauquelin_sector is not None
            for p in self.available_kerykeion_celestial_points
        )

        if has_gauquelin:
            # Gauquelin data is shown in the unified planet grid — no separate house grid
            template_dict["makeMainHousesGrid"] = ""
        else:
            template_dict["makeMainHousesGrid"] = draw_main_house_grid(
                main_subject_houses_list=houses_list,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
                x_position=self._MAIN_HOUSES_GRID_X + self._grid_x_shift,
            )

    def _setup_main_planet_grid(self, template_dict: dict, subject_name: str, title: str = "") -> None:
        """
        Populate template_dict with the main planet grid table.

        Creates the tabular display of planet positions for the primary subject.
        When Gauquelin sectors are active, produces a unified table with
        Planet | Longitude | Declination | Sector that replaces both the
        planet grid and the house cusp grid.

        Args:
            template_dict: Dictionary to populate with grid SVG elements.
            subject_name: Name to display in the grid header.
            title: Optional title prefix (e.g., "Points for").
        """
        # Check for Gauquelin mode
        has_gauquelin = any(
            hasattr(p, "gauquelin_sector") and p.gauquelin_sector is not None
            for p in self.available_kerykeion_celestial_points
        )

        if has_gauquelin:
            from kerykeion.charts.utils import draw_gauquelin_unified_grid

            # Shift the Gauquelin grid 30px left for better symmetry: the unified
            # grid (220px) replaces both planet grid (80px) + house grid (120px),
            # and centering it in the same footprint requires a leftward nudge.
            gauquelin_x_nudge = -30
            template_dict["makeMainPlanetGrid"] = draw_gauquelin_unified_grid(
                celestial_points=self.available_kerykeion_celestial_points,
                text_color=self.chart_colors_settings["paper_0"],
                x_position=self._MAIN_PLANET_GRID_X + self._grid_x_shift + gauquelin_x_nudge,
                celestial_point_language=self._language_model.celestial_points,
                show_out_of_bounds=self.show_out_of_bounds,
            )
        else:
            template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
                planets_and_houses_grid_title=title,
                subject_name=subject_name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
                x_position=self._MAIN_PLANET_GRID_X + self._grid_x_shift,
                show_out_of_bounds=self.show_out_of_bounds,
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
            show_out_of_bounds=self.show_out_of_bounds,
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
        # The system the cusps CAME FROM, not the one requested: inside the polar
        # circle those differ, and the legend describes what is drawn.
        house_key = "houses_system_" + self.first_obj.effective_houses_system_identifier
        return (
            f"{self._translate('domification', 'Domification')}: "
            f"{self._translate(house_key, self.first_obj.effective_houses_system_name)}"
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
        # The system the cusps came from, not the one requested: the compact
        # renderers label dual wheels and returns, where a polar chart would
        # otherwise read as the system it could not actually be cast in.
        house_key = "houses_system_" + subject.effective_houses_system_identifier
        return (
            f"{self._translate(house_key, subject.effective_houses_system_name)} {self._translate('houses', 'Houses')}"
        )

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
            try:
                template = _svg_polish_optimize(template)
            except Exception as exc:
                # svg_polish handles the scour-inherited var()/calc() crashes
                # on complex SVG structures, but keep the fallback for truly
                # malformed XML and other unexpected failures.
                logging.warning(
                    "svg_polish failed on SVG minification, falling back to string-based minification: %s",
                    exc,
                )

                template = template.replace('"', "'")
                template = re.sub(r"\s+", " ", template)
                template = re.sub(r">\s+<", "><", template)
                template = template.strip()
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
        signs = get_args(Sign)
        return "".join(
            draw_zodiac_slice(
                c1=self.first_circle_radius,
                chart_type=self.chart_type,
                seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                num=i,
                r=r,
                style=f"fill:{self.chart_colors_settings[f'zodiac_bg_{i}']}; fill-opacity: 0.5;",
                type=sign,
            )
            for i, sign in enumerate(signs)
        )

    def _draw_all_aspects_lines(self, r: float, ar: float) -> str:
        """
        Render SVG lines for all aspects in the chart.

        Args:
            r (float): Radius at which aspect lines originate.
            ar (float): Radius at which aspect lines terminate.

        Returns:
            str: SVG markup for all aspect lines.
        """
        parts: list[str] = []
        # Track rendered icon positions (x, y, aspect_degrees) to avoid overlapping symbols of same type
        rendered_icon_positions: list[tuple[float, float, int]] = []
        for aspect in self.aspects_list:
            aspect_name = aspect["aspect"]
            aspect_color = next((a["color"] for a in self.aspects_settings if a["name"] == aspect_name), None)
            if aspect_color:
                parts.append(
                    draw_aspect_line(
                        r=r,
                        ar=ar,
                        aspect=aspect,
                        color=aspect_color,
                        seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                        show_aspect_icon=self.show_aspect_icons,
                        rendered_icon_positions=rendered_icon_positions,
                        show_aspect_movement=self.show_aspect_movement,
                    )
                )
        return "".join(parts)

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
            # Strip first: names are not normalised upstream, and a leading space
            # made the first "word" the empty string. On the diurnality row that
            # produced a bare value with no owner — exactly the ambiguity the
            # labels exist to prevent. Fall back to the whole name if stripping
            # leaves no first word at all.
            stripped = name.strip()
            name = stripped.split(" ")[0] or stripped

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
            date_str = format_iso_display(self.second_obj.iso_formatted_local_datetime, "%Y-%m-%d")  # type: ignore
            truncated_name = self._truncate_name(self.first_obj.name)
            return f"{truncated_name} - {transit_label} {date_str}"

        elif self.chart_type == "Synastry":
            synastry_label = self._translate("synastry_chart", "Synastry")
            and_word = self._translate("and_word", "&")
            name1 = self._truncate_name(self.first_obj.name)
            name2 = self._truncate_name(self.second_obj.name)  # type: ignore
            return f"{synastry_label}: {name1} {and_word} {name2}"

        elif self.chart_type == "DualReturnChart":
            year = extract_year_from_iso(self.second_obj.iso_formatted_local_datetime)  # type: ignore
            month_year = format_iso_display(self.second_obj.iso_formatted_local_datetime, "%Y-%m")  # type: ignore
            truncated_name = self._truncate_name(self.first_obj.name)
            key, default = return_label_keys(self.second_obj)
            label = self._translate(key, default)
            # A solar return recurs yearly, the others within a year, so only the
            # solar title is unambiguous with the year alone.
            is_solar = isinstance(self.second_obj, PlanetReturnModel) and self.second_obj.return_type == "Solar"
            return f"{truncated_name} - {label} {year if is_solar else month_year}"

        elif self.chart_type == "SingleReturnChart":
            year = extract_year_from_iso(self.first_obj.iso_formatted_local_datetime)  # type: ignore
            month_year = format_iso_display(self.first_obj.iso_formatted_local_datetime, "%Y-%m")  # type: ignore
            truncated_name = self._truncate_name(self.first_obj.name)
            key, default = return_label_keys(self.first_obj)
            label = self._translate(key, default)
            is_solar = isinstance(self.first_obj, PlanetReturnModel) and self.first_obj.return_type == "Solar"
            return f"{truncated_name} - {label} {year if is_solar else month_year}"

        elif self.chart_type == "Progression":
            prog_label = self._translate("progression", "Progression")
            name1 = self._truncate_name(self.first_obj.name)
            name2 = self._truncate_name(self.second_obj.name) if self.second_obj else ""  # type: ignore
            return f"{prog_label}: {name1} — {name2}"

        # Fallback for unknown chart types
        return self._truncate_name(self.first_obj.name)

    def _get_chart_description(self, title: str) -> str:
        """One sentence for a reader who cannot see the wheel.

        The title alone ("John Lennon - Natal") says whose chart it is and
        nothing about what was drawn. A screen reader announcing a chart should
        also be told the kind of drawing, the moment and place it was cast for,
        the house system, and how much is on it — the same facts a sighted
        reader takes from the corners of the sheet in a glance.

        Everything here already exists on the subject; nothing is computed.
        """
        parts = [title]

        moment = getattr(self.first_obj, "iso_formatted_local_datetime", None)
        if moment:
            parts.append(format_iso_display(moment, "%Y-%m-%d %H:%M"))

        where = ", ".join(
            str(x) for x in (getattr(self.first_obj, "city", None),
                             getattr(self.first_obj, "nation", None)) if x
        )
        if where:
            parts.append(where)

        system_id = getattr(self.first_obj, "effective_houses_system_identifier", None)
        if system_id:
            parts.append(self._translate(
                f"houses_system_{system_id}",
                getattr(self.first_obj, "effective_houses_system_name", system_id),
            ))

        points = len(getattr(self, "available_planets_setting", []) or [])
        aspects = len(getattr(self, "aspects_list", []) or [])
        counted = self._translate(
            "chart_contents",
            "{points} points, {aspects} aspects",
        )
        try:
            parts.append(counted.format(points=points, aspects=aspects))
        except (KeyError, IndexError):  # a language pack with a broken pattern
            parts.append(f"{points} points, {aspects} aspects")

        return ". ".join(p for p in parts if p) + "."

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
        template_dict["makeGauquelinSectors"] = ""  # Default empty, populated if Gauquelin sectors present
        template_dict["makeHouseSectors"] = ""  # Default empty, populated by _setup_house_sectors

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
        # lunar_phase / bottom_left are written after the renderer runs — see the
        # note further down, next to DIURNALITY_GLYPH_DROP.

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
        # COLORS: Planet colors for all 71 possible celestial points
        # ---------------------------------------------------------------------
        # Initialize all slots with default black, then override with settings.
        # This ensures template substitution never fails on missing colors.
        default_color = "#000000"
        # Seed the model-declared range (ChartTemplateModel requires
        # planets_color_0..61) PLUS every id in the default catalog, which now
        # extends past 61 (e.g. Vulkanus 72, White_Moon 75) — the old
        # hardcoded range(71) silently drifted out of sync with the catalog.
        for i in range(62):
            template_dict[f"planets_color_{i}"] = default_color
        for planet_setting in DEFAULT_CELESTIAL_POINTS_SETTINGS:
            template_dict[f"planets_color_{planet_setting['id']}"] = default_color

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
        # Seed every degree from the defaults first: ChartTemplateModel
        # declares all orb_color_* fields as required, so a caller-reduced
        # aspects_settings (documented constructor option) would otherwise
        # fail template validation on every render.
        for default_aspect in DEFAULT_CHART_ASPECTS_SETTINGS:
            template_dict[f"orb_color_{default_aspect['degree']}"] = default_aspect["color"]
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

        # Chart title, and the sentence a screen reader gets with it
        template_dict["stringTitle"] = self._get_chart_title(custom_title_override=custom_title)
        template_dict["stringDescription"] = self._get_chart_description(template_dict["stringTitle"])

        # Set viewbox dynamically for all chart types
        template_dict["viewbox"] = self._dynamic_viewbox()

        # ------------------------------- #
        #  CHART TYPE SPECIFIC SETTINGS   #
        # ------------------------------- #
        # Delegate to the appropriate renderer based on chart type.
        # This uses the Strategy Pattern to separate chart-specific logic.
        self._renderer.render(template_dict)

        # ---------------------------------------------------------------------
        # LAYOUT: bottom-left block and moon glyph
        # ---------------------------------------------------------------------
        # Written here, after the renderer: this is the single point every height
        # branch converges on, right-panel synastry included.
        #
        # The six rows have fixed baselines and every renderer fills all six,
        # blanks included, so a row with nothing to say used to leave a hole and
        # the block stopped looking like a block — a heliocentric chart printed
        # two lines, two gaps, one line, a gap. The rows are packed to the bottom
        # instead. Downwards and not upwards: the rows sit under the wheel's
        # centre so the chord widens as it descends (row 0 clears 134px, row 5
        # clears 229), which makes moving a line down always safe and moving one
        # up the mistake documented above DIURNALITY_GLYPH_DROP.
        #
        # All six nodes stay in the markup — the empties simply migrate to the
        # top — because the baseline-freshness guard counts them.
        filled = [template_dict.get(f"bottom_left_{i}", "") for i in range(_INFO_ROW_COUNT)]
        filled = [row for row in filled if row]
        for index in range(_INFO_ROW_COUNT):
            slot = index - (_INFO_ROW_COUNT - len(filled))
            template_dict[f"bottom_left_{index}"] = filled[slot] if slot >= 0 else ""

        # The glyph keeps the 10px gap below the last line it has always had.
        # Expressed against the last *filled* row rather than against row 5
        # specifically: with the rows packed down, "is row 5 filled" is true
        # whenever anything is written at all, and the old test of it would drop
        # the glyph on every chart.
        lunar_phase_y = offsets["lunar_phase"]
        if filled:
            last_row_y = _INFO_ROW_FIRST_Y + _INFO_ROW_STEP * (_INFO_ROW_COUNT - 1)
            lunar_phase_y = offsets["lunar_phase"] + (last_row_y - _INFO_ROW_LEGACY_LAST_Y)
        # The template field is ``int``; the offsets are floats on a dataclass a
        # caller can supply, so coerce here rather than lean on pydantic's lax
        # coercion. ``round`` rather than ``int``: the shipped defaults are whole,
        # but a caller passing 518.5 should not silently lose half a pixel to
        # truncation.
        template_dict["lunar_phase_translate_y"] = round(lunar_phase_y)
        template_dict["bottom_left_translate_y"] = round(offsets["bottom_left"])
        template_dict["chart_font_family"] = CHART_TEXT_FONT_FAMILY

        # ---------------------------------------------------------------------
        # SECURITY: Escape user-controlled plain-text fields
        # ---------------------------------------------------------------------
        # These fields carry user-supplied strings (subject names, cities,
        # custom titles) and are substituted into the SVG template as text
        # content. Escape them here — at the single point where they enter the
        # template model — so markup in a name cannot break the XML or inject
        # script. SVG fragment fields (makePlanets, grids, ...) are NOT escaped:
        # they contain legitimate markup and escape user text at draw time.
        for text_field in _PLAIN_TEXT_TEMPLATE_FIELDS:
            if text_field in template_dict:
                template_dict[text_field] = escape_svg_text(template_dict[text_field])

        return ChartTemplateModel(**template_dict)

    def _generate_modern_content(
        self,
        show_zodiac_background_ring: bool = True,
    ) -> str:
        """Generate raw modern wheel SVG content in the 100x100 coordinate space.

        Automatically dispatches to single or dual horoscope based on chart type.

        Args:
            show_zodiac_background_ring: Draw colored zodiac wedges.

        Returns:
            str: Raw SVG group content for the modern wheel.
        """
        houses_list = get_houses_list(self.first_obj)
        aspects_dicts = [a.model_dump() if hasattr(a, "model_dump") else dict(a) for a in self.aspects_list]

        if self.second_obj is not None and self._renderer.is_dual_wheel():
            return draw_modern_dual_horoscope(
                planets_1=self.available_kerykeion_celestial_points,
                houses_1=houses_list,
                planets_2=self.second_subject_celestial_points,
                aspects_list=aspects_dicts,
                seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                planets_settings=self.all_available_planets_setting,
                aspects_settings=self.aspects_settings,
                chart_type=self.chart_type,
                show_zodiac_background_ring=show_zodiac_background_ring,
                show_motion_state=self.show_motion_state,
                show_aspect_movement=self.show_aspect_movement,
            )
        else:
            has_gauquelin = any(
                hasattr(p, "gauquelin_sector") and p.gauquelin_sector is not None
                for p in self.available_kerykeion_celestial_points
            )
            gauq_cusps = getattr(self.first_obj, "gauquelin_sector_cusps", None)
            return draw_modern_horoscope(
                planets=self.available_kerykeion_celestial_points,
                houses=houses_list,
                aspects_list=aspects_dicts,
                seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                planets_settings=self.available_planets_setting,
                aspects_settings=self.aspects_settings,
                show_zodiac_background_ring=show_zodiac_background_ring,
                gauquelin_sectors=has_gauquelin,
                gauquelin_cusps=gauq_cusps,
                show_motion_state=self.show_motion_state,
                show_aspect_movement=self.show_aspect_movement,
            )

    _GLYPH_CENTER_ATTR_RE = re.compile(r'kr:(cx|cy)="([^"]+)"')
    _CHART_POINT_TAG_RE = re.compile(r'<g\b(?=[^>]*\bkr:node=(["\'])ChartPoint\1)[^>]*>')
    _CHART_POINT_ID_ATTR_RE = re.compile(r'\bkr:(horoscope|absoluteposition)=(["\'])(.*?)\2')
    _CHART_POINT_ANALYSIS_ATTR_RE = re.compile(r'\bkr:(horoscope|slug)=(["\'])(.*?)\2')

    @classmethod
    def _rebase_glyph_centers(cls, svg: str, scale: float, tx: float, ty: float) -> str:
        """Rewrite every kr:cx / kr:cy attribute from wheel-local to SVG-root user space.

        The three ChartPoint emitters (classic draw_planets, modern draw_modern)
        write glyph centers in their own wheel-local frame at draw time — they
        cannot know which template will consume the fragment. Each output path
        (full chart vs wheel-only, classic vs modern) wraps the wheel in a known
        affine map (scale + Full_Wheel translate), so the final values are
        normalized here to honor the documented contract: kr:cx / kr:cy are in
        chart SVG root coordinates. kr:cx/kr:cy occur only on ChartPoint nodes,
        so a global rewrite is safe.
        """
        if scale == 1.0 and tx == 0.0 and ty == 0.0:
            return svg

        def _sub(match: "re.Match[str]") -> str:
            axis = match.group(1)
            value = float(match.group(2))
            offset = tx if axis == "cx" else ty
            return f'kr:{axis}="{value * scale + offset}"'

        return cls._GLYPH_CENTER_ATTR_RE.sub(_sub, svg)

    def _inject_projected_house_metadata(self, svg: str) -> str:
        """Add reciprocal-house metadata to every point in a dual wheel.

        ``kr:house`` remains the house in the point owner's own horoscope. The
        additive ``kr:projectedhouse`` attribute is the house containing that
        point in the other horoscope, while ``kr:projectedhoroscope`` identifies
        that target ring. Computing this from the two subjects keeps the SVG
        contract available even when optional chart-data house comparisons were
        disabled.
        """
        if self.second_obj is None or not self._renderer.is_dual_wheel():
            return svg

        first_cusps = [house.abs_pos for house in get_houses_list(self.first_obj)]
        second_cusps = [house.abs_pos for house in get_houses_list(self.second_obj)]
        projected_by_position: dict[tuple[str, str], tuple[str, str]] = {}

        for owner_ring, target_ring, points, target_cusps in (
            ("0", "1", self.available_kerykeion_celestial_points, second_cusps),
            ("1", "0", self.second_subject_celestial_points, first_cusps),
        ):
            for point in points:
                try:
                    projected_house = get_planet_house(point.abs_pos, target_cusps)
                except ValueError:
                    continue
                projected_by_position[(owner_ring, str(point.abs_pos))] = (projected_house, target_ring)

        def _annotate(match: "re.Match[str]") -> str:
            tag = match.group(0)
            identity = {name: value for name, _, value in self._CHART_POINT_ID_ATTR_RE.findall(tag)}
            key = (identity.get("horoscope", "0"), identity.get("absoluteposition", ""))
            projection = projected_by_position.get(key)
            if projection is None:
                return tag

            projected_house, target_ring = projection
            return f'{tag[:-1]} kr:projectedhouse="{projected_house}" kr:projectedhoroscope="{target_ring}">'

        return self._CHART_POINT_TAG_RE.sub(_annotate, svg)

    def _inject_analysis_metadata(self, svg: str) -> str:
        """Tag each point with the chart-level analyses it takes part in.

        Angularity and stelliums are properties of the chart, not of the point:
        they live on the chart data, keyed by point name, and the three point
        serializers never see them. Annotating the finished markup — the same
        route ``_inject_projected_house_metadata`` takes — keeps that data out
        of every draw signature while still delivering it to consumers that
        read the SVG rather than the model.

        ``kr:angularity`` lists the angles the point stands on, each with its
        arc, as ``Angle:distance`` pairs separated by a space and ordered
        closest first: ``kr:angularity="Ascendant:0.8991 Medium_Coeli:4.3156"``.
        One attribute rather than two, and a list rather than a single value,
        because the analysis is genuinely one-to-many — near the poles the
        Ascendant and the Midheaven close on each other, and a planet can sit
        within orb of both. Two attributes repeated per pair would be duplicate
        attribute names, which is not valid XML; keeping only the closest pair
        would silently drop what ``_compute_angularities`` deliberately reports.

        ``kr:stellium`` carries the house of the crowd the point belongs to.
        Both are absent for a point that takes part in neither.
        """
        chart_data = self.chart_data
        rings: tuple[tuple[str, list, list], ...]
        if self._renderer.is_dual_wheel():
            rings = (
                (
                    "0",
                    list(getattr(chart_data, "first_subject_angularities", []) or []),
                    list(getattr(chart_data, "first_subject_stelliums", []) or []),
                ),
                (
                    "1",
                    list(getattr(chart_data, "second_subject_angularities", []) or []),
                    list(getattr(chart_data, "second_subject_stelliums", []) or []),
                ),
            )
        else:
            rings = (
                (
                    "0",
                    list(getattr(chart_data, "angularities", []) or []),
                    list(getattr(chart_data, "stelliums", []) or []),
                ),
            )

        # Collected per point before being rendered, so a point standing on two
        # angles produces one attribute holding two pairs rather than the
        # attribute twice.
        angles_by_point: dict[tuple[str, str], list[str]] = {}
        analysis_by_point: dict[tuple[str, str], list[str]] = {}
        for ring, angularities, stelliums in rings:
            for angularity in angularities:
                angles_by_point.setdefault((ring, str(angularity.point)), []).append(
                    f"{escape_svg_text(str(angularity.angle))}:{round(angularity.distance, 4)}"
                )
            for stellium in stelliums:
                for name in stellium.points:
                    analysis_by_point.setdefault((ring, str(name)), []).append(f'kr:stellium="{stellium.house}"')

        for key, pairs in angles_by_point.items():
            analysis_by_point.setdefault(key, []).insert(0, f'kr:angularity="{" ".join(pairs)}"')

        if not analysis_by_point:
            return svg

        def _annotate(match: "re.Match[str]") -> str:
            tag = match.group(0)
            identity = {name: value for name, _, value in self._CHART_POINT_ANALYSIS_ATTR_RE.findall(tag)}
            key = (identity.get("horoscope", "0"), identity.get("slug", ""))
            attributes = analysis_by_point.get(key)
            if not attributes:
                return tag
            return f'{tag[:-1]} {" ".join(attributes)}>'

        return self._CHART_POINT_TAG_RE.sub(_annotate, svg)

    def _gauquelin_grid_carries_oob_badges(self) -> bool:
        """Whether the Gauquelin table will be widened for out-of-bounds badges.

        The grid widens itself only when a body actually needs the badge, so
        the estimator has to ask the same question rather than reserving on the
        option alone: reserving more would move the sector column on charts
        that draw no badge, and reserving less would clip the one that does.
        """
        if not self.show_out_of_bounds:
            return False
        return any(getattr(p, "is_out_of_bounds", None) for p in self.available_kerykeion_celestial_points)

    def _validate_chart_style(self, style: KerykeionChartStyle) -> None:
        """Validate that the given style is a supported chart style.

        Args:
            style: The chart style to validate.

        Raises:
            KerykeionException: If the style is not in the allowed values.
        """
        allowed_styles = get_args(KerykeionChartStyle)
        if style not in allowed_styles:
            raise KerykeionException(f"Style {style!r} is not available. Allowed values: {', '.join(allowed_styles)}.")

    def _warn_classic_only_options(self, effective_style: "KerykeionChartStyle") -> None:
        """Warn when classic-only options are active but the modern style renders.

        With "modern" as the default style, a caller that sets ``external_view``,
        ``show_degree_indicators=False`` or ``show_aspect_icons=False`` without
        also asking for ``style="classic"`` would silently lose the option: the
        modern renderer ignores all three. The render still succeeds — the warning
        only makes the silence audible. ``show_degree_indicators`` and
        ``show_aspect_icons`` default to True, so only a non-default False value
        can be recognised as an explicit request.

        Each option warns once per drawer. The condition is a property of the
        instance, not of the call, so repeating it on every render would turn a
        batch job — a year of transits off one drawer — into hundreds of
        identical lines, which is how a warning stops being read.

        Args:
            effective_style: The style actually used for this render.
        """
        if effective_style != "modern":
            return

        classic_only = (
            ("external_view", self.external_view, "to keep the external layout"),
            ("show_degree_indicators", not self.show_degree_indicators, "for it to take effect"),
            ("show_aspect_icons", not self.show_aspect_icons, "for it to take effect"),
        )
        for name, is_set, remedy in classic_only:
            if is_set and name not in self._warned_classic_only:
                self._warned_classic_only.add(name)
                logger.warning(
                    f"{name} is a classic-style option and the modern style ignores it; "
                    f'pass style="classic" {remedy}.'
                )

    def generate_svg_string(
        self,
        minify: bool = False,
        remove_css_variables=False,
        *,
        custom_title: Union[str, None] = None,
        style: "Union[KerykeionChartStyle, object]" = _UNSET,
        show_zodiac_background_ring: "Union[bool, object]" = _UNSET,
    ) -> str:
        """
        Render the full chart SVG as a string.

        Reads the XML template, substitutes variables, and optionally inlines CSS
        variables and minifies the output.

        Args:
            minify (bool): Remove whitespace and quotes for compactness.
            remove_css_variables (bool): Embed CSS variable definitions.
            custom_title (str or None): Optional override for the SVG title.
            style (KerykeionChartStyle): Chart wheel style — "classic" or "modern".
                If not provided, uses the default set in the constructor.
            show_zodiac_background_ring (bool): Draw colored zodiac wedges (modern only).
                If not provided, uses the default set in the constructor.

        Returns:
        """
        # ``is not _UNSET`` cannot narrow the ``object``-typed kwargs, so explicit
        # values are cast to the documented parameter types (the style value is
        # re-validated by _validate_chart_style right below).
        effective_style = cast("KerykeionChartStyle", style) if style is not _UNSET else self._style
        effective_ring = (
            cast(bool, show_zodiac_background_ring)
            if show_zodiac_background_ring is not _UNSET
            else self._show_zodiac_background_ring
        )

        self._validate_chart_style(effective_style)
        self._warn_classic_only_options(effective_style)
        td = self._create_template_dictionary(custom_title=custom_title)

        DATA_DIR = _MODULE_DIR
        raw_template = _load_cached_file(str(DATA_DIR / "templates" / "chart.xml"))

        template_data = td.model_dump()

        if effective_style == "modern":
            modern_content = self._generate_modern_content(
                show_zodiac_background_ring=effective_ring,
            )
            # Scale from 100x100 modern space into the ~480x480 classic wheel space.
            # The wheel group in chart.xml is at translate(100, $full_wheel_translate_y),
            # and the classic wheel has diameter 2*main_radius ≈ 480.
            scale = (2 * self.main_radius) / 100
            wrapped = f'<g transform="scale({scale:.4f})">\n{modern_content}\n</g>'

            overrides = dict(template_data)
            # Inject modern wheel into the background circle placeholder;
            # blank out all other classic wheel sub-groups.
            overrides["background_circle"] = wrapped
            overrides["makeZodiac"] = ""
            overrides["first_circle"] = ""
            overrides["second_circle"] = ""
            overrides["third_circle"] = ""
            overrides["transitRing"] = ""
            overrides["degreeRing"] = ""
            overrides["makeHouses"] = ""
            overrides["makePlanets"] = ""
            overrides["makeAspects"] = ""
            # Blank the classic transparent hit-area overlays too: otherwise the
            # classic house-sector / Gauquelin click wedges (populated in
            # template_data) leak on top of the injected modern wheel with
            # mismatched classic-wheel geometry, duplicating the modern wheel's
            # own click regions. The modern wheel renders its own sectors.
            overrides["makeHouseSectors"] = ""
            overrides["makeGauquelinSectors"] = ""
            template = Template(raw_template).substitute(overrides)
            # Modern wheel-local (100x100) -> scale wrapper -> Full_Wheel translate.
            template = self._rebase_glyph_centers(template, scale, 100.0, self._vertical_offsets["wheel"])
        else:
            template = Template(raw_template).substitute(template_data)
            # Classic values are Full_Wheel-local; add the template's translate.
            template = self._rebase_glyph_centers(template, 1.0, 100.0, self._vertical_offsets["wheel"])

        template = self._inject_projected_house_metadata(template)
        template = self._inject_analysis_metadata(template)

        logger.debug("Template dictionary includes %s fields", len(template_data))

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
            # The English label, not the translated one: this is a filename and
            # has to be stable across the caller's chart_language. Naming only
            # Solar and Lunar meant a heliocentric and a node-crossing return for
            # the same subject both fell through to the bare chart-type name, and
            # the second silently overwrote the first.
            _, english_label = return_label_keys(self.second_obj)
            return f"{self.first_obj.name} - {self.chart_type} Chart - {english_label}{suffix}"

        # Handle ExternalNatal renaming for wheel and grid exports.
        #
        # The modern wheel is deliberately NOT in this set: it ignores
        # external_view (see _warn_classic_only_options), so naming its file
        # "ExternalNatal" would have the filename claim a layout the drawing
        # does not have — and with modern the default style, that mislabelled
        # file is what a caller who merely set external_view=True now gets.
        external_alias_suffixes = {" - Classic Wheel Only", " - Aspect Grid Only"}
        if suffix in external_alias_suffixes and self.external_view and self.chart_type == "Natal":
            chart_type_name = "ExternalNatal"
        else:
            chart_type_name = self.chart_type

        return f"{self.first_obj.name} - {chart_type_name} Chart{suffix}"

    @staticmethod
    def _sanitize_output_basename(name: str) -> str:
        """
        Sanitize a filename (without extension) for safe use as a basename.

        Subject names and custom filenames are user-controlled and may contain
        path separators or traversal sequences. This replaces path separators,
        null bytes, ".." sequences and leading dots with underscores so the
        resulting name cannot escape the output directory or hide the file.

        Args:
            name (str): The raw filename without extension.

        Returns:
            str: The sanitized basename.
        """
        sanitized = name.replace("\x00", "_").replace("/", "_").replace("\\", "_")
        while ".." in sanitized:
            sanitized = sanitized.replace("..", "_")
        # Replace leading dots (hidden files / relative tricks) with underscores
        sanitized = re.sub(r"^\.+", lambda match: "_" * len(match.group()), sanitized)
        return sanitized or "_"

    def _write_svg_to_disk(
        self,
        content: str,
        output_path: Union[str, Path, None],
        filename: Union[str, None],
        default_suffix: str = "",
    ) -> Path:
        """
        Write SVG content to disk and return the path.

        The basename is sanitized and the final path is verified to stay inside
        the output directory, so user-controlled names cannot traverse paths.

        Args:
            content (str): The SVG content to write.
            output_path (str, Path, or None): Directory path. Defaults to home directory.
            filename (str or None): Custom filename without extension. If None, uses default.
            default_suffix (str): Suffix for default filename (e.g., " - Wheel Only").

        Returns:
            Path: The path where the file was saved.

        Raises:
            KerykeionException: If the resolved path escapes the output
                directory, or if the SVG cannot be written (missing/read-only
                directory, un-encodable content).
        """
        output_directory = Path(output_path) if output_path is not None else Path.home()

        if filename is not None:
            base_name = filename
        else:
            base_name = self._get_default_filename_suffix(default_suffix)

        chartname = output_directory / f"{self._sanitize_output_basename(str(base_name))}.svg"

        # Defense in depth: ensure the resolved target stays inside the
        # resolved output directory (covers symlinks and exotic inputs).
        resolved_directory = output_directory.resolve()
        resolved_chartname = chartname.resolve()
        try:
            resolved_chartname.relative_to(resolved_directory)
        except ValueError:
            raise KerykeionException(
                f"Refusing to write SVG outside the output directory: {resolved_chartname} is not inside {resolved_directory}."
            ) from None

        # Encode FIRST (before opening the file): a lone surrogate would
        # otherwise raise mid-write, after open() already truncated/created the
        # file, leaving a stale 0-byte .svg behind. Encoding up front means an
        # un-encodable character fails before any file is touched. WITHOUT
        # errors="ignore" (which silently dropped such characters, producing a
        # file that no longer matched generate_svg_string()). Both raw stdlib
        # errors are wrapped in the library's own exception.
        try:
            encoded = content.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise KerykeionException(
                f"The SVG content contains a character that cannot be encoded ({exc}). "
                "Check the subject name / city / custom title for invalid characters."
            ) from exc
        try:
            with open(chartname, "wb") as output_file:
                output_file.write(encoded)
        except OSError as exc:
            raise KerykeionException(
                f"Could not write the SVG to {chartname}: {exc}. Check the output directory exists and is writable."
            ) from exc

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
        style: "Union[KerykeionChartStyle, object]" = _UNSET,
        show_zodiac_background_ring: "Union[bool, object]" = _UNSET,
    ):
        """
        Generate and save the full chart SVG to disk.

        Calls generate_svg_string to render the SVG, then writes a file named
        "{subject.name} - {chart_type} Chart - Modern.svg" (or "... - Classic.svg"
        when the effective style is "classic") in the specified output directory.

        Args:
            output_path (str, Path, or None): Directory path where the SVG file will be saved.
                If None, defaults to the user's home directory.
            filename (str or None): Custom filename for the SVG file (without extension).
                If None, uses the default pattern:
                "{subject.name} - {chart_type} Chart - {Modern|Classic}".
            minify (bool): Pass-through to generate_svg_string for compact output.
            remove_css_variables (bool): Pass-through to generate_svg_string to embed CSS variables.
            custom_title (str or None): Optional override for the SVG title.
            style (KerykeionChartStyle): Chart wheel style — "classic" or "modern".
                If not provided, uses the default set in the constructor.
            show_zodiac_background_ring (bool): Draw colored zodiac wedges (modern only).
                If not provided, uses the default set in the constructor.

        Returns:
            None
        """
        effective_style = style if style is not _UNSET else self._style
        suffix = " - Modern" if effective_style == "modern" else " - Classic"
        self.template = self.generate_svg_string(
            minify,
            remove_css_variables,
            custom_title=custom_title,
            style=style,
            show_zodiac_background_ring=show_zodiac_background_ring,
        )
        self._write_svg_to_disk(self.template, output_path, filename, default_suffix=suffix)

    def generate_wheel_only_svg_string(
        self,
        minify: bool = False,
        remove_css_variables=False,
        *,
        style: "Union[KerykeionChartStyle, object]" = _UNSET,
        show_zodiac_background_ring: "Union[bool, object]" = _UNSET,
    ):
        """
        Render the wheel-only chart SVG as a string.

        Reads the wheel-only XML template, substitutes chart data, and applies optional
        CSS inlining and minification.

        Args:
            minify (bool): Remove whitespace and quotes for compactness.
            remove_css_variables (bool): Embed CSS variable definitions.
            style (KerykeionChartStyle): Chart wheel style — "classic" or "modern".
                If not provided, uses the default set in the constructor.
            show_zodiac_background_ring (bool): Draw colored zodiac wedges (modern only).
                If not provided, uses the default set in the constructor.

        Returns:
            str: SVG markup for the chart wheel only.
        """
        # ``is not _UNSET`` cannot narrow the ``object``-typed kwargs, so explicit
        # values are cast to the documented parameter types (the style value is
        # re-validated by _validate_chart_style right below).
        effective_style = cast("KerykeionChartStyle", style) if style is not _UNSET else self._style
        effective_ring = (
            cast(bool, show_zodiac_background_ring)
            if show_zodiac_background_ring is not _UNSET
            else self._show_zodiac_background_ring
        )

        self._validate_chart_style(effective_style)
        self._warn_classic_only_options(effective_style)

        if effective_style == "modern":
            raw_template = _load_cached_file(str(_MODULE_DIR / "templates" / "modern_wheel.xml"))

            template_dict = self._create_template_dictionary()
            modern_content = self._generate_modern_content(
                show_zodiac_background_ring=effective_ring,
            )
            template = Template(raw_template).substitute(
                {
                    **template_dict.model_dump(),
                    "makeModernHoroscope": modern_content,
                    "viewbox": "0 0 100 100",
                }
            )
        else:
            raw_template = _load_cached_file(str(_MODULE_DIR / "templates" / "wheel_only.xml"))

            template_dict = self._create_template_dictionary()
            wheel_viewbox = self._wheel_only_viewbox()
            template = Template(raw_template).substitute({**template_dict.model_dump(), "viewbox": wheel_viewbox})
            # Classic values are Full_Wheel-local; wheel_only.xml pins the wheel
            # at translate(100, 50). (The modern branch is already root-space:
            # its wheel-local 100x100 frame IS the wheel-only viewBox.)
            template = self._rebase_glyph_centers(template, 1.0, 100.0, 50.0)

        template = self._inject_projected_house_metadata(template)
        template = self._inject_analysis_metadata(template)

        return self._apply_svg_post_processing(template, minify, remove_css_variables)

    def save_wheel_only_svg_file(
        self,
        output_path: Union[str, Path, None] = None,
        filename: Union[str, None] = None,
        minify: bool = False,
        remove_css_variables=False,
        *,
        style: "Union[KerykeionChartStyle, object]" = _UNSET,
        show_zodiac_background_ring: "Union[bool, object]" = _UNSET,
    ):
        """
        Generate and save wheel-only chart SVG to disk.

        Calls generate_wheel_only_svg_string and writes a file named
        "{subject.name} - {chart_type} Chart - Modern Wheel Only.svg" (or
        "... - Classic Wheel Only.svg" when the effective style is "classic")
        in the specified output directory.

        Args:
            output_path (str, Path, or None): Directory path where the SVG file will be saved.
                If None, defaults to the user's home directory.
            filename (str or None): Custom filename for the SVG file (without extension).
                If None, uses the default pattern:
                "{subject.name} - {chart_type} Chart - {Modern|Classic} Wheel Only".
            minify (bool): Pass-through to generate_wheel_only_svg_string for compact output.
            remove_css_variables (bool): Pass-through to generate_wheel_only_svg_string to embed CSS variables.
            style (KerykeionChartStyle): Chart wheel style — "classic" or "modern".
                If not provided, uses the default set in the constructor.
            show_zodiac_background_ring (bool): Draw colored zodiac wedges (modern only).
                If not provided, uses the default set in the constructor.

        Returns:
            None
        """
        effective_style = style if style is not _UNSET else self._style
        suffix = " - Modern Wheel Only" if effective_style == "modern" else " - Classic Wheel Only"
        template = self.generate_wheel_only_svg_string(
            minify,
            remove_css_variables,
            style=style,
            show_zodiac_background_ring=show_zodiac_background_ring,
        )
        self._write_svg_to_disk(template, output_path, filename, default_suffix=suffix)

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

        template = _load_cached_file(str(_MODULE_DIR / "templates" / "aspect_grid_only.xml"))

        template_dict = self._create_template_dictionary()

        if self._renderer.is_dual_wheel():
            aspects_grid = draw_transit_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self._get_aspect_grid_planets_setting(),
                self.aspects_list,
                aspects_settings=self.aspects_settings,
            )
        else:
            aspects_grid = draw_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self.available_planets_setting,
                self.aspects_list,
                x_start=50,
                y_start=250,
                aspects_settings=self.aspects_settings,
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
    from kerykeion.utilities.core import setup_logging
    from kerykeion.planetary_returns.factory import PlanetaryReturnFactory
    from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory
    from kerykeion.chart_data.factory import ChartDataFactory

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
