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
    KerykeionSettingsCelestialPointModel,
    KerykeionLanguageModel,
)
from kerykeion.schemas.kr_literals import (
    KerykeionChartTheme,
    KerykeionChartLanguage,
    AstrologicalPoint,
)
from kerykeion.schemas.kr_models import ChartDataModel
from kerykeion.settings import LANGUAGE_SETTINGS
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
    makeLunarPhase,
    draw_main_house_grid,
    draw_secondary_house_grid,
    draw_main_planet_grid,
    draw_secondary_planet_grid,
    format_location_string,
    format_datetime_with_timezone
)
from kerykeion.charts.draw_planets import draw_planets
from kerykeion.utilities import get_houses_list, inline_css_variables_in_svg, distribute_percentages_to_100
from kerykeion.settings.chart_defaults import (
    DEFAULT_CHART_COLORS,
    DEFAULT_CELESTIAL_POINTS_SETTINGS,
    DEFAULT_CHART_ASPECTS_SETTINGS,
)
from typing import List, Literal


logger = logging.getLogger(__name__)


class ChartDrawer:
    """
    ChartDrawer generates astrological chart visualizations as SVG files from pre-computed chart data.

    This class is designed for pure visualization and requires chart data to be pre-computed using
    ChartDataFactory. This separation ensures clean architecture where ChartDataFactory handles
    all calculations (aspects, element/quality distributions, subjects) while ChartDrawer focuses
    solely on rendering SVG visualizations.

    ChartDrawer supports creating full chart SVGs, wheel-only SVGs, and aspect-grid-only SVGs
    for various chart types including Natal, Transit, Synastry, and Composite.
    Charts are rendered using XML templates and drawing utilities, with customizable themes,
    language, and visual settings.

    The generated SVG files are optimized for web use and can be saved to any specified
    destination path using the save_svg method.

    NOTE:
        The generated SVG files are optimized for web use, opening in browsers. If you want to
        use them in other applications, you might need to adjust the SVG settings or styles.

    Args:
        chart_data (ChartDataModel):
            Pre-computed chart data from ChartDataFactory containing all subjects, aspects,
            element/quality distributions, and other analytical data. This is the ONLY source
            of chart information - no calculations are performed by ChartDrawer.
        theme (KerykeionChartTheme, optional):
            CSS theme for the chart. If None, no default styles are applied. Defaults to 'classic'.
        double_chart_aspect_grid_type (Literal['list', 'table'], optional):
            Specifies rendering style for double-chart aspect grids. Defaults to 'list'.
        chart_language (KerykeionChartLanguage, optional):
            Language code for chart labels. Defaults to 'EN'.
        language_pack (dict | None, optional):
            Additional translations merged over the bundled defaults for the
            selected language. Useful to introduce new languages or override
            existing labels.
        transparent_background (bool, optional):
            Whether to use a transparent background instead of the theme color. Defaults to False.

    Public Methods:
        makeTemplate(minify=False, remove_css_variables=False) -> str:
            Render the full chart SVG as a string without writing to disk. Use `minify=True`
            to remove whitespace and quotes, and `remove_css_variables=True` to embed CSS vars.

        save_svg(output_path=None, filename=None, minify=False, remove_css_variables=False) -> None:
            Generate and write the full chart SVG file to the specified path.
            If output_path is None, saves to the user's home directory.
            If filename is None, uses default pattern: '{subject.name} - {chart_type} Chart.svg'.

        makeWheelOnlyTemplate(minify=False, remove_css_variables=False) -> str:
            Render only the chart wheel (no aspect grid) as an SVG string.

        save_wheel_only_svg_file(output_path=None, filename=None, minify=False, remove_css_variables=False) -> None:
            Generate and write the wheel-only SVG file to the specified path.
            If output_path is None, saves to the user's home directory.
            If filename is None, uses default pattern: '{subject.name} - {chart_type} Chart - Wheel Only.svg'.

        makeAspectGridOnlyTemplate(minify=False, remove_css_variables=False) -> str:
            Render only the aspect grid as an SVG string.

        save_aspect_grid_only_svg_file(output_path=None, filename=None, minify=False, remove_css_variables=False) -> None:
            Generate and write the aspect-grid-only SVG file to the specified path.
            If output_path is None, saves to the user's home directory.
            If filename is None, uses default pattern: '{subject.name} - {chart_type} Chart - Aspect Grid Only.svg'.

    Example:
        >>> from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
        >>> from kerykeion.chart_data_factory import ChartDataFactory
        >>> from kerykeion.charts.chart_drawer import ChartDrawer
        >>>
        >>> # Step 1: Create subject
        >>> subject = AstrologicalSubjectFactory.from_birth_data("John", 1990, 1, 1, 12, 0, "London", "GB")
        >>>
        >>> # Step 2: Pre-compute chart data
        >>> chart_data = ChartDataFactory.create_natal_chart_data(subject)
        >>>
        >>> # Step 3: Create visualization
        >>> chart_drawer = ChartDrawer(chart_data=chart_data, theme="classic")
        >>> chart_drawer.save_svg()  # Saves to home directory with default filename
        >>> # Or specify custom path and filename:
        >>> chart_drawer.save_svg("/path/to/output/directory", "my_custom_chart")
    """

    # Constants

    _DEFAULT_HEIGHT = 550
    _DEFAULT_FULL_WIDTH = 1250
    _DEFAULT_SYNASTRY_WIDTH = 1570
    _DEFAULT_NATAL_WIDTH = 870
    _DEFAULT_FULL_WIDTH_WITH_TABLE = 1250
    _DEFAULT_ULTRA_WIDE_WIDTH = 1320

    _VERTICAL_PADDING_TOP = 15
    _VERTICAL_PADDING_BOTTOM = 15
    _TITLE_SPACING = 8

    _ASPECT_LIST_ASPECTS_PER_COLUMN = 14
    _ASPECT_LIST_COLUMN_WIDTH = 105

    _BASE_VERTICAL_OFFSETS = {
        "wheel": 50,
        "grid": 0,
        "aspect_grid": 50,
        "aspect_list": 50,
        "title": 0,
        "elements": 0,
        "qualities": 0,
        "lunar_phase": 518,
        "bottom_left": 0,
    }
    _MAX_TOP_SHIFT = 80
    _TOP_SHIFT_FACTOR = 2
    _ROW_HEIGHT = 8

    _BASIC_CHART_VIEWBOX = f"0 0 {_DEFAULT_NATAL_WIDTH} {_DEFAULT_HEIGHT}"
    _WIDE_CHART_VIEWBOX = f"0 0 {_DEFAULT_FULL_WIDTH} 546.0"
    _ULTRA_WIDE_CHART_VIEWBOX = f"0 0 {_DEFAULT_ULTRA_WIDE_WIDTH} 546.0"
    _TRANSIT_CHART_WITH_TABLE_VIWBOX = f"0 0 {_DEFAULT_FULL_WIDTH_WITH_TABLE} 546.0"

    # Set at init
    first_obj: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel]
    second_obj: Union[AstrologicalSubjectModel, PlanetReturnModel, None]
    chart_type: ChartType
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
    available_planets_setting: List[KerykeionSettingsCelestialPointModel]
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
        celestial_points_settings: list[dict] = DEFAULT_CELESTIAL_POINTS_SETTINGS,
        aspects_settings: list[dict] = DEFAULT_CHART_ASPECTS_SETTINGS,
        custom_title: Union[str, None] = None,
        show_house_position_comparison: bool = True,
        auto_size: bool = True,
        padding: int = 20,
    ):
        """
        Initialize the chart visualizer with pre-computed chart data.

        Args:
            chart_data (ChartDataModel):
                Pre-computed chart data from ChartDataFactory containing all subjects,
                aspects, element/quality distributions, and other analytical data.
            theme (KerykeionChartTheme or None, optional):
                CSS theme to apply; None for default styling.
            double_chart_aspect_grid_type (Literal['list','table'], optional):
                Layout style for double-chart aspect grids ('list' or 'table').
            chart_language (KerykeionChartLanguage, optional):
                Language code for chart labels (e.g., 'EN', 'IT').
            language_pack (dict | None, optional):
                Additional translations merged over the bundled defaults for the
                selected language. Useful to introduce new languages or override
                existing labels.
            external_view (bool, optional):
                Whether to use external visualization (planets on outer ring) for single-subject charts. Defaults to False.
            transparent_background (bool, optional):
                Whether to use a transparent background instead of the theme color. Defaults to False.
            custom_title (str or None, optional):
                Custom title for the chart. If None, the default title will be used based on chart type. Defaults to None.
            show_house_position_comparison (bool, optional):
                Whether to render the house position comparison grid (when supported by the chart type).
                Defaults to True. Set to False to hide the table and reclaim horizontal space.
        """
        # --------------------
        # COMMON INITIALIZATION
        # --------------------
        self.chart_language = chart_language
        self.double_chart_aspect_grid_type = double_chart_aspect_grid_type
        self.transparent_background = transparent_background
        self.external_view = external_view
        self.chart_colors_settings = deepcopy(colors_settings)
        self.planets_settings = [dict(body) for body in celestial_points_settings]
        self.aspects_settings = [dict(aspect) for aspect in aspects_settings]
        self.custom_title = custom_title
        self.show_house_position_comparison = show_house_position_comparison
        self.auto_size = auto_size
        self._padding = padding
        self._vertical_offsets: dict[str, int] = self._BASE_VERTICAL_OFFSETS.copy()

        # Extract data from ChartDataModel
        self.chart_data = chart_data
        self.chart_type = chart_data.chart_type
        self.active_points = chart_data.active_points
        self.active_aspects = chart_data.active_aspects

        # Extract subjects based on chart type
        if chart_data.chart_type in ["Natal", "Composite", "SingleReturnChart"]:
            # SingleChartDataModel
            self.first_obj = getattr(chart_data, 'subject')
            self.second_obj = None

        else:  # DualChartDataModel for Transit, Synastry, DualReturnChart
            self.first_obj = getattr(chart_data, 'first_subject')
            self.second_obj = getattr(chart_data, 'second_subject')

        # Load settings
        self._load_language_settings(language_pack)

        # Default radius for all charts
        self.main_radius = 240

        # Configure available planets from chart data
        self.available_planets_setting = []
        for body in self.planets_settings:
            if body["name"] in self.active_points:
                body["is_active"] = True
                self.available_planets_setting.append(body)  # type: ignore[arg-type]

        active_points_count = len(self.available_planets_setting)
        if active_points_count > 24:
            logger.warning(
                "ChartDrawer detected %s active celestial points; rendering may look crowded beyond 24.",
                active_points_count,
            )

        # Set available celestial points
        available_celestial_points_names = [body["name"].lower() for body in self.available_planets_setting]
        self.available_kerykeion_celestial_points = self._collect_subject_points(
            self.first_obj,
            available_celestial_points_names,
        )

        # Collect secondary subject points for dual charts using the same active set
        self.t_available_kerykeion_celestial_points: list[KerykeionPointModel] = []
        if self.second_obj is not None:
            self.t_available_kerykeion_celestial_points = self._collect_subject_points(
                self.second_obj,
                available_celestial_points_names,
            )

        # ------------------------
        # CHART TYPE SPECIFIC SETUP FROM CHART DATA
        # ------------------------

        if self.chart_type == "Natal":
            # --- NATAL CHART SETUP ---

            # Extract aspects from pre-computed chart data
            self.aspects_list = chart_data.aspects

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            self.width = self._DEFAULT_NATAL_WIDTH

            # Get location and coordinates
            self.location, self.geolat, self.geolon = self._get_location_info()

            # Circle radii - depends on external_view
            if self.external_view:
                self.first_circle_radius = 56
                self.second_circle_radius = 92
                self.third_circle_radius = 112
            else:
                self.first_circle_radius = 0
                self.second_circle_radius = 36
                self.third_circle_radius = 120

        elif self.chart_type == "Composite":
            # --- COMPOSITE CHART SETUP ---

            # Extract aspects from pre-computed chart data
            self.aspects_list = chart_data.aspects

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            self.width = self._DEFAULT_NATAL_WIDTH

            # Get location and coordinates
            self.location, self.geolat, self.geolon = self._get_location_info()

            # Circle radii
            self.first_circle_radius = 0
            self.second_circle_radius = 36
            self.third_circle_radius = 120

        elif self.chart_type == "Transit":
            # --- TRANSIT CHART SETUP ---

            # Extract aspects from pre-computed chart data
            self.aspects_list = chart_data.aspects

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            if self.double_chart_aspect_grid_type == "table":
                self.width = self._DEFAULT_FULL_WIDTH_WITH_TABLE
            else:
                self.width = self._DEFAULT_FULL_WIDTH

            # Get location and coordinates
            self.location, self.geolat, self.geolon = self._get_location_info()

            # Circle radii
            self.first_circle_radius = 0
            self.second_circle_radius = 36
            self.third_circle_radius = 120

        elif self.chart_type == "Synastry":
            # --- SYNASTRY CHART SETUP ---

            # Extract aspects from pre-computed chart data
            self.aspects_list = chart_data.aspects

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            self.width = self._DEFAULT_SYNASTRY_WIDTH

            # Get location and coordinates
            self.location, self.geolat, self.geolon = self._get_location_info()

            # Circle radii
            self.first_circle_radius = 0
            self.second_circle_radius = 36
            self.third_circle_radius = 120

        elif self.chart_type == "DualReturnChart":
            # --- RETURN CHART SETUP ---

            # Extract aspects from pre-computed chart data
            self.aspects_list = chart_data.aspects

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            self.width = self._DEFAULT_ULTRA_WIDE_WIDTH

            # Get location and coordinates
            self.location, self.geolat, self.geolon = self._get_location_info()

            # Circle radii
            self.first_circle_radius = 0
            self.second_circle_radius = 36
            self.third_circle_radius = 120

        elif self.chart_type == "SingleReturnChart":
            # --- SINGLE WHEEL RETURN CHART SETUP ---

            # Extract aspects from pre-computed chart data
            self.aspects_list = chart_data.aspects

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            self.width = self._DEFAULT_NATAL_WIDTH

            # Get location and coordinates
            self.location, self.geolat, self.geolon = self._get_location_info()

            # Circle radii
            self.first_circle_radius = 0
            self.second_circle_radius = 36
            self.third_circle_radius = 120

        self._apply_house_comparison_width_override()

        # --------------------
        # FINAL COMMON SETUP FROM CHART DATA
        # --------------------

        # Extract pre-computed element and quality distributions
        self.fire = chart_data.element_distribution.fire
        self.earth = chart_data.element_distribution.earth
        self.air = chart_data.element_distribution.air
        self.water = chart_data.element_distribution.water

        self.cardinal = chart_data.quality_distribution.cardinal
        self.fixed = chart_data.quality_distribution.fixed
        self.mutable = chart_data.quality_distribution.mutable

        # Set up theme
        if theme not in get_args(KerykeionChartTheme) and theme is not None:
            raise KerykeionException(f"Theme {theme} is not available. Set None for default theme.")

        self.set_up_theme(theme)

        self._apply_dynamic_height_adjustment()
        self._adjust_height_for_extended_aspect_columns()
        # Reconcile width with the updated layout once height adjustments are known.
        if self.auto_size:
            self._update_width_to_content()

    def _count_active_planets(self) -> int:
        """Return number of active celestial points in the current chart."""
        return len([p for p in self.available_planets_setting if p.get("is_active")])

    def _apply_dynamic_height_adjustment(self) -> None:
        """Adjust chart height and vertical offsets based on active points."""
        active_points_count = self._count_active_planets()

        offsets = self._BASE_VERTICAL_OFFSETS.copy()

        minimum_height = self._DEFAULT_HEIGHT

        if self.chart_type == "Synastry":
            self._apply_synastry_height_adjustment(
                active_points_count=active_points_count,
                offsets=offsets,
                minimum_height=minimum_height,
            )
            return

        if active_points_count <= 20:
            self.height = max(self.height, minimum_height)
            self._vertical_offsets = offsets
            return

        extra_points = active_points_count - 20
        extra_height = extra_points * self._ROW_HEIGHT

        self.height = max(self.height, minimum_height + extra_height)

        delta_height = max(self.height - minimum_height, 0)

        # Anchor wheel, aspect grid/list, and lunar phase to the bottom
        offsets["wheel"] += delta_height
        offsets["aspect_grid"] += delta_height
        offsets["aspect_list"] += delta_height
        offsets["lunar_phase"] += delta_height
        offsets["bottom_left"] += delta_height

        # Smooth top offsets to keep breathing room near the title and grids
        shift = min(extra_points * self._TOP_SHIFT_FACTOR, self._MAX_TOP_SHIFT)
        top_shift = shift // 2

        offsets["grid"] += shift
        offsets["title"] += top_shift
        offsets["elements"] += top_shift
        offsets["qualities"] += top_shift

        self._vertical_offsets = offsets

    def _adjust_height_for_extended_aspect_columns(self) -> None:
        """Ensure tall aspect columns fit within the SVG for double-chart lists."""
        if self.double_chart_aspect_grid_type != "list":
            return

        if self.chart_type not in ("Synastry", "Transit", "DualReturnChart"):
            return

        total_aspects = len(self.aspects_list) if hasattr(self, "aspects_list") else 0
        if total_aspects == 0:
            return

        aspects_per_column = 14
        extended_column_start = 11  # Zero-based column index where tall columns begin
        base_capacity = aspects_per_column * extended_column_start

        if total_aspects <= base_capacity:
            return

        translate_y = 273
        bottom_padding = 40
        title_clearance = 18
        line_height = 14
        baseline_index = aspects_per_column - 1
        top_limit_index = ceil((-translate_y + title_clearance) / line_height)
        max_capacity_by_top = baseline_index - top_limit_index + 1

        if max_capacity_by_top <= aspects_per_column:
            return

        target_capacity = max_capacity_by_top
        required_available_height = target_capacity * line_height
        required_height = translate_y + bottom_padding + required_available_height

        if required_height <= self.height:
            return

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
        offsets: dict[str, int],
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
        if self.show_house_position_comparison:
            return

        if self.chart_type == "Synastry":
            self.width = self._DEFAULT_FULL_WIDTH
        elif self.chart_type == "DualReturnChart":
            self.width = self._DEFAULT_FULL_WIDTH_WITH_TABLE if self.double_chart_aspect_grid_type == "table" else self._DEFAULT_FULL_WIDTH
        elif self.chart_type == "Transit":
            # Transit charts already use the compact width unless the aspect grid table is requested.
            self.width = self._DEFAULT_FULL_WIDTH_WITH_TABLE if self.double_chart_aspect_grid_type == "table" else self._DEFAULT_FULL_WIDTH

    def _dynamic_viewbox(self) -> str:
        """Return the viewBox string based on current width/height with vertical padding."""
        min_y = -self._VERTICAL_PADDING_TOP
        viewbox_height = int(self.height) + self._VERTICAL_PADDING_TOP + self._VERTICAL_PADDING_BOTTOM
        return f"0 {min_y} {int(self.width)} {viewbox_height}"

    def _wheel_only_viewbox(self, margin: int = 20) -> str:
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
        extents = [wheel_right]

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
                if self.show_house_position_comparison and self.second_obj is not None:
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

            if self.chart_type == "Transit":
                # House comparison grid at x ~ 1030
                if self.show_house_position_comparison:
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
                    extents.append(house_comparison_grid_right)

            if self.chart_type == "DualReturnChart":
                # House comparison grid translated to x ~ 1100
                if self.show_house_position_comparison:
                    dual_return_columns = [
                        self._translate("return_point", "Return Point"),
                        self._translate("Return", "DualReturnChart"),
                        self._translate("Natal", "Natal"),
                    ]
                    dual_return_grid_width = self._estimate_house_comparison_grid_width(
                        column_labels=dual_return_columns,
                        include_radix_column=True,
                        include_title=True,
                    )
                    house_comparison_grid_right = 1100 + dual_return_grid_width
                    extents.append(house_comparison_grid_right)

        # Conservative safety padding
        return int(max(extents) + self._padding)

    def _calculate_double_chart_aspect_columns(
        self,
        total_aspects: int,
        chart_height: Optional[int],
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
        chart_height: Optional[int],
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

    @staticmethod
    def _estimate_text_width(text: str, font_size: int) -> float:
        """Very rough text width estimation in pixels based on font size."""
        if not text:
            return 0.0
        average_char_width = float(font_size)
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
        languages = load_language_settings(overrides)

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
                style=f'fill:{self.chart_colors_settings[f"zodiac_bg_{i}"]}; fill-opacity: 0.5;',
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
                )
        return out

    def _draw_all_transit_aspects_lines(self, r, ar):
        """
        Render SVG lines for all transit aspects in the chart.

        Args:
            r (float): Radius at which transit aspect lines originate.
            ar (float): Radius at which transit aspect lines terminate.

        Returns:
            str: SVG markup for all transit aspect lines.
        """
        out = ""
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
                )
        return out

    def _truncate_name(self, name: str, max_length: int = 50, ellipsis_symbol: str = "…", truncate_at_space: bool = False) -> str:
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

        return name[:max_length-1] + ellipsis_symbol

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
            return f'{truncated_name} - {natal_label}'

        elif self.chart_type == "Composite":
            composite_label = self._translate("composite_chart", "Composite")
            and_word = self._translate("and_word", "&")
            name1 = self._truncate_name(self.first_obj.first_subject.name) # type: ignore
            name2 = self._truncate_name(self.first_obj.second_subject.name) # type: ignore
            return f"{composite_label}: {name1} {and_word} {name2}"

        elif self.chart_type == "Transit":
            transit_label = self._translate("transits", "Transits")
            date_obj = datetime.fromisoformat(self.second_obj.iso_formatted_local_datetime) # type: ignore
            date_str = date_obj.strftime("%d/%m/%y")
            truncated_name = self._truncate_name(self.first_obj.name)
            return f"{truncated_name} - {transit_label} {date_str}"

        elif self.chart_type == "Synastry":
            synastry_label = self._translate("synastry_chart", "Synastry")
            and_word = self._translate("and_word", "&")
            name1 = self._truncate_name(self.first_obj.name)
            name2 = self._truncate_name(self.second_obj.name) # type: ignore
            return f"{synastry_label}: {name1} {and_word} {name2}"

        elif self.chart_type == "DualReturnChart":
            return_datetime = datetime.fromisoformat(self.second_obj.iso_formatted_local_datetime) # type: ignore
            year = return_datetime.year
            month_year = return_datetime.strftime("%m/%Y")
            truncated_name = self._truncate_name(self.first_obj.name)
            if self.second_obj is not None and isinstance(self.second_obj, PlanetReturnModel) and self.second_obj.return_type == "Solar":
                solar_label = self._translate("solar_return", "Solar")
                return f"{truncated_name} - {solar_label} {year}"
            else:
                lunar_label = self._translate("lunar_return", "Lunar")
                return f"{truncated_name} - {lunar_label} {month_year}"

        elif self.chart_type == "SingleReturnChart":
            return_datetime = datetime.fromisoformat(self.first_obj.iso_formatted_local_datetime) # type: ignore
            year = return_datetime.year
            month_year = return_datetime.strftime("%m/%Y")
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

        # Set the color style tag and basic dimensions
        template_dict["color_style_tag"] = self.color_style_tag
        template_dict["chart_height"] = self.height
        template_dict["chart_width"] = self.width

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

        # Set paper colors
        template_dict["paper_color_0"] = self.chart_colors_settings["paper_0"]

        # Set background color based on transparent_background setting
        if self.transparent_background:
            template_dict["background_color"] = "transparent"
        else:
            template_dict["background_color"] = self.chart_colors_settings["paper_1"]

        # Set planet colors - initialize all possible colors first with defaults
        default_color = "#000000"  # Default black color for unused planets
        for i in range(42):  # Support all 42 celestial points (0-41)
            template_dict[f"planets_color_{i}"] = default_color

        # Override with actual colors from settings
        for planet in self.planets_settings:
            planet_id = planet["id"]
            template_dict[f"planets_color_{planet_id}"] = planet["color"]

        # Set zodiac colors
        for i in range(12):
            template_dict[f"zodiac_color_{i}"] = self.chart_colors_settings[f"zodiac_icon_{i}"]

        # Set orb colors
        for aspect in self.aspects_settings:
            template_dict[f"orb_color_{aspect['degree']}"] = aspect["color"]

        # Draw zodiac circle slices
        template_dict["makeZodiac"] = self._draw_zodiac_circle_slices(self.main_radius)

        # Calculate element percentages
        total_elements = self.fire + self.water + self.earth + self.air
        element_values = {"fire": self.fire, "earth": self.earth, "air": self.air, "water": self.water}
        element_percentages = distribute_percentages_to_100(element_values) if total_elements > 0 else {"fire": 0, "earth": 0, "air": 0, "water": 0}
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
        quality_percentages = distribute_percentages_to_100(quality_values) if total_qualities > 0 else {"cardinal": 0, "fixed": 0, "mutable": 0}
        cardinal_percentage = quality_percentages["cardinal"]
        fixed_percentage = quality_percentages["fixed"]
        mutable_percentage = quality_percentages["mutable"]

        template_dict["qualities_string"] = f"{self._translate('qualities', 'Qualities')}:"
        template_dict["cardinal_string"] = f"{self._translate('cardinal', 'Cardinal')} {cardinal_percentage}%"
        template_dict["fixed_string"] = f"{self._translate('fixed', 'Fixed')} {fixed_percentage}%"
        template_dict["mutable_string"] = f"{self._translate('mutable', 'Mutable')} {mutable_percentage}%"

        # Get houses list for main subject
        first_subject_houses_list = get_houses_list(self.first_obj)

        # Chart title
        template_dict["stringTitle"] = self._get_chart_title(custom_title_override=custom_title)

        # ------------------------------- #
        #  CHART TYPE SPECIFIC SETTINGS   #
        # ------------------------------- #

        if self.chart_type == "Natal":
            # Set viewbox dynamically
            template_dict["viewbox"] = self._dynamic_viewbox()

            # Rings and circles
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

            # Aspects
            template_dict["makeDoubleChartAspectList"] = ""
            template_dict["makeAspectGrid"] = draw_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self.available_planets_setting,
                self.aspects_list,
            )
            template_dict["makeAspects"] = self._draw_all_aspects_lines(self.main_radius, self.main_radius - self.third_circle_radius)

            # Top left section
            latitude_string = convert_latitude_coordinate_to_string(
                self.geolat,
                self._translate("north", "North"),
                self._translate("south", "South"),
            )
            longitude_string = convert_longitude_coordinate_to_string(
                self.geolon,
                self._translate("east", "East"),
                self._translate("west", "West"),
            )

            template_dict["top_left_0"] = f'{self._translate("location", "Location")}:'
            template_dict["top_left_1"] = f"{self.first_obj.city}, {self.first_obj.nation}"
            template_dict["top_left_2"] = f"{self._translate('latitude', 'Latitude')}: {latitude_string}"
            template_dict["top_left_3"] = f"{self._translate('longitude', 'Longitude')}: {longitude_string}"
            template_dict["top_left_4"] = format_datetime_with_timezone(self.first_obj.iso_formatted_local_datetime) # type: ignore
            localized_weekday = self._translate(
                f"weekdays.{self.first_obj.day_of_week}",
                self.first_obj.day_of_week,  # type: ignore[arg-type]
            )
            template_dict["top_left_5"] = f"{self._translate('day_of_week', 'Day of Week')}: {localized_weekday}" # type: ignore

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropical":
                zodiac_info = f"{self._translate('zodiac', 'Zodiac')}: {self._translate('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self._translate('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = zodiac_info
            template_dict["bottom_left_1"] = (
                f"{self._translate('domification', 'Domification')}: "
                f"{self._translate('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)}"
            )

            # Lunar phase information (optional)
            if self.first_obj.lunar_phase is not None:
                template_dict["bottom_left_2"] = (
                    f'{self._translate("lunation_day", "Lunation Day")}: '
                    f'{self.first_obj.lunar_phase.get("moon_phase", "")}'
                )
                template_dict["bottom_left_3"] = (
                    f'{self._translate("lunar_phase", "Lunar Phase")}: '
                    f'{self._translate(self.first_obj.lunar_phase.moon_phase_name.lower().replace(" ", "_"), self.first_obj.lunar_phase.moon_phase_name)}'
                )
            else:
                template_dict["bottom_left_2"] = ""
                template_dict["bottom_left_3"] = ""

            template_dict["bottom_left_4"] = (
                f'{self._translate("perspective_type", "Perspective")}: '
                f'{self._translate(self.first_obj.perspective_type.lower().replace(" ", "_"), self.first_obj.perspective_type)}'
            )

            # Moon phase section calculations
            if self.first_obj.lunar_phase is not None:
                template_dict["makeLunarPhase"] = makeLunarPhase(self.first_obj.lunar_phase["degrees_between_s_m"], self.geolat)
            else:
                template_dict["makeLunarPhase"] = ""

            # Houses and planet drawing
            template_dict["makeMainHousesGrid"] = draw_main_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
            )
            template_dict["makeSecondaryHousesGrid"] = ""

            template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
                r=self.main_radius,
                first_subject_houses_list=first_subject_houses_list,
                standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
                first_house_color=self.planets_settings[12]["color"],
                tenth_house_color=self.planets_settings[13]["color"],
                seventh_house_color=self.planets_settings[14]["color"],
                fourth_house_color=self.planets_settings[15]["color"],
                c1=self.first_circle_radius,
                c3=self.third_circle_radius,
                chart_type=self.chart_type,
                external_view=self.external_view,
            )

            template_dict["makePlanets"] = draw_planets(
                available_planets_setting=self.available_planets_setting,
                chart_type=self.chart_type,
                radius=self.main_radius,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                third_circle_radius=self.third_circle_radius,
                main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                external_view=self.external_view,
            )

            template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
                planets_and_houses_grid_title=self._translate("planets_and_house", "Points for"),
                subject_name=self.first_obj.name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
            )
            template_dict["makeSecondaryPlanetGrid"] = ""
            template_dict["makeHouseComparisonGrid"] = ""

        elif self.chart_type == "Composite":
            # Set viewbox dynamically
            template_dict["viewbox"] = self._dynamic_viewbox()

            # Rings and circles
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

            # Aspects
            template_dict["makeDoubleChartAspectList"] = ""
            template_dict["makeAspectGrid"] = draw_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self.available_planets_setting,
                self.aspects_list,
            )
            template_dict["makeAspects"] = self._draw_all_aspects_lines(self.main_radius, self.main_radius - self.third_circle_radius)

            # Top left section
            # First subject
            latitude = convert_latitude_coordinate_to_string(
                self.first_obj.first_subject.lat, # type: ignore
                self._translate("north_letter", "N"),
                self._translate("south_letter", "S"),
            )
            longitude = convert_longitude_coordinate_to_string(
                self.first_obj.first_subject.lng, # type: ignore
                self._translate("east_letter", "E"),
                self._translate("west_letter", "W"),
            )

            # Second subject
            latitude_string = convert_latitude_coordinate_to_string(
                self.first_obj.second_subject.lat, # type: ignore
                self._translate("north_letter", "N"),
                self._translate("south_letter", "S"),
            )
            longitude_string = convert_longitude_coordinate_to_string(
                self.first_obj.second_subject.lng, # type: ignore
                self._translate("east_letter", "E"),
                self._translate("west_letter", "W"),
            )

            template_dict["top_left_0"] = f"{self.first_obj.first_subject.name}" # type: ignore
            template_dict["top_left_1"] = f"{datetime.fromisoformat(self.first_obj.first_subject.iso_formatted_local_datetime).strftime('%Y-%m-%d %H:%M')}" # type: ignore
            template_dict["top_left_2"] = f"{latitude} {longitude}"
            template_dict["top_left_3"] = self.first_obj.second_subject.name # type: ignore
            template_dict["top_left_4"] = f"{datetime.fromisoformat(self.first_obj.second_subject.iso_formatted_local_datetime).strftime('%Y-%m-%d %H:%M')}" # type: ignore
            template_dict["top_left_5"] = f"{latitude_string} / {longitude_string}"

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropical":
                zodiac_info = f"{self._translate('zodiac', 'Zodiac')}: {self._translate('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self._translate('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = zodiac_info
            template_dict["bottom_left_1"] = f"{self._translate('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)} {self._translate('houses', 'Houses')}"
            template_dict["bottom_left_2"] = f'{self._translate("perspective_type", "Perspective")}: {self.first_obj.first_subject.perspective_type}' # type: ignore
            template_dict["bottom_left_3"] = f'{self._translate("composite_chart", "Composite Chart")} - {self._translate("midpoints", "Midpoints")}'
            template_dict["bottom_left_4"] = ""

            # Moon phase section calculations
            if self.first_obj.lunar_phase is not None:
                template_dict["makeLunarPhase"] = makeLunarPhase(self.first_obj.lunar_phase["degrees_between_s_m"], self.geolat)
            else:
                template_dict["makeLunarPhase"] = ""

            # Houses and planet drawing
            template_dict["makeMainHousesGrid"] = draw_main_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
            )
            template_dict["makeSecondaryHousesGrid"] = ""

            template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
                r=self.main_radius,
                first_subject_houses_list=first_subject_houses_list,
                standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
                first_house_color=self.planets_settings[12]["color"],
                tenth_house_color=self.planets_settings[13]["color"],
                seventh_house_color=self.planets_settings[14]["color"],
                fourth_house_color=self.planets_settings[15]["color"],
                c1=self.first_circle_radius,
                c3=self.third_circle_radius,
                chart_type=self.chart_type,
                external_view=self.external_view,
            )

            template_dict["makePlanets"] = draw_planets(
                available_planets_setting=self.available_planets_setting,
                chart_type=self.chart_type,
                radius=self.main_radius,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                third_circle_radius=self.third_circle_radius,
                main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                external_view=self.external_view,
            )

            subject_name = (
                f"{self.first_obj.first_subject.name}"
                f" {self._translate('and_word', '&')} "
                f"{self.first_obj.second_subject.name}"
            )  # type: ignore

            template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
                planets_and_houses_grid_title=self._translate("planets_and_house", "Points for"),
                subject_name=subject_name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
            )
            template_dict["makeSecondaryPlanetGrid"] = ""
            template_dict["makeHouseComparisonGrid"] = ""

        elif self.chart_type == "Transit":

            # Transit has no Element Percentages
            template_dict["elements_string"] = ""
            template_dict["fire_string"] = ""
            template_dict["earth_string"] = ""
            template_dict["air_string"] = ""
            template_dict["water_string"] = ""

            # Transit has no Qualities Percentages
            template_dict["qualities_string"] = ""
            template_dict["cardinal_string"] = ""
            template_dict["fixed_string"] = ""
            template_dict["mutable_string"] = ""

            # Set viewbox dynamically
            template_dict["viewbox"] = self._dynamic_viewbox()

            # Get houses list for secondary subject
            second_subject_houses_list = get_houses_list(self.second_obj) # type: ignore

            # Rings and circles
            template_dict["transitRing"] = draw_transit_ring(
                self.main_radius,
                self.chart_colors_settings["paper_1"],
                self.chart_colors_settings["zodiac_transit_ring_3"],
            )
            template_dict["degreeRing"] = draw_transit_ring_degree_steps(self.main_radius, self.first_obj.seventh_house.abs_pos)
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

            # Aspects
            if self.double_chart_aspect_grid_type == "list":
                title = f'{self.first_obj.name} - {self._translate("transit_aspects", "Transit Aspects")}'
                template_dict["makeAspectGrid"] = ""
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                    title,
                    self.aspects_list,
                    self.planets_settings,
                    self.aspects_settings,
                    chart_height=self.height,
                )  # type: ignore[arg-type]
            else:
                template_dict["makeAspectGrid"] = ""
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                    self.chart_colors_settings["paper_0"],
                    self.available_planets_setting,
                    self.aspects_list,
                    600,
                    520,
                )

            template_dict["makeAspects"] = self._draw_all_transit_aspects_lines(self.main_radius, self.main_radius - 160)

            # Top left section (clear separation of Natal vs Transit details)
            natal_latitude_string = (
                convert_latitude_coordinate_to_string(
                    self.first_obj.lat,  # type: ignore[arg-type]
                    self._translate("north_letter", "N"),
                    self._translate("south_letter", "S"),
                )
                if getattr(self.first_obj, "lat", None) is not None
                else ""
            )
            natal_longitude_string = (
                convert_longitude_coordinate_to_string(
                    self.first_obj.lng,  # type: ignore[arg-type]
                    self._translate("east_letter", "E"),
                    self._translate("west_letter", "W"),
                )
                if getattr(self.first_obj, "lng", None) is not None
                else ""
            )

            transit_latitude_string = ""
            transit_longitude_string = ""
            if self.second_obj is not None:
                if getattr(self.second_obj, "lat", None) is not None:
                    transit_latitude_string = convert_latitude_coordinate_to_string(
                        self.second_obj.lat,  # type: ignore[arg-type]
                        self._translate("north_letter", "N"),
                        self._translate("south_letter", "S"),
                    )
                if getattr(self.second_obj, "lng", None) is not None:
                    transit_longitude_string = convert_longitude_coordinate_to_string(
                        self.second_obj.lng,  # type: ignore[arg-type]
                        self._translate("east_letter", "E"),
                        self._translate("west_letter", "W"),
                    )

            natal_dt = format_datetime_with_timezone(self.first_obj.iso_formatted_local_datetime)  # type: ignore[arg-type]
            natal_place = f"{format_location_string(self.first_obj.city)}, {self.first_obj.nation}"  # type: ignore[arg-type]
            transit_dt = (
                format_datetime_with_timezone(self.second_obj.iso_formatted_local_datetime)  # type: ignore[arg-type]
                if self.second_obj is not None and getattr(self.second_obj, "iso_formatted_local_datetime", None) is not None
                else ""
            )
            transit_place = (
                f"{format_location_string(self.second_obj.city)}, {self.second_obj.nation}"  # type: ignore[arg-type]
                if self.second_obj is not None
                else ""
            )

            template_dict["top_left_0"] = f"{self._translate('chart_info_natal_label', 'Natal')}: {natal_dt}"
            template_dict["top_left_1"] = natal_place
            template_dict["top_left_2"] = f"{natal_latitude_string}  ·  {natal_longitude_string}"
            template_dict["top_left_3"] = f"{self._translate('chart_info_transit_label', 'Transit')}: {transit_dt}"
            template_dict["top_left_4"] = transit_place
            template_dict["top_left_5"] = f"{transit_latitude_string}  ·  {transit_longitude_string}"

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropical":
                zodiac_info = f"{self._translate('zodiac', 'Zodiac')}: {self._translate('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self._translate('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = zodiac_info
            template_dict["bottom_left_1"] = f"{self._translate('domification', 'Domification')}: {self._translate('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)}"

            # Lunar phase information from second object (Transit) (optional)
            if self.second_obj is not None and hasattr(self.second_obj, 'lunar_phase') and self.second_obj.lunar_phase is not None:
                template_dict["bottom_left_3"] = (
                    f"{self._translate('Transit', 'Transit')} "
                    f"{self._translate('lunation_day', 'Lunation Day')}: "
                    f"{self.second_obj.lunar_phase.get('moon_phase', '')}"
                )  # type: ignore
                template_dict["bottom_left_4"] = (
                    f"{self._translate('Transit', 'Transit')} "
                    f"{self._translate('lunar_phase', 'Lunar Phase')}: "
                    f"{self._translate(self.second_obj.lunar_phase.moon_phase_name.lower().replace(' ', '_'), self.second_obj.lunar_phase.moon_phase_name)}"
                )
            else:
                template_dict["bottom_left_3"] = ""
                template_dict["bottom_left_4"] = ""

            template_dict["bottom_left_2"] = f'{self._translate("perspective_type", "Perspective")}: {self._translate(self.second_obj.perspective_type.lower().replace(" ", "_"), self.second_obj.perspective_type)}' # type: ignore

            # Moon phase section calculations - use transit subject data only
            if self.second_obj is not None and getattr(self.second_obj, "lunar_phase", None):
                template_dict["makeLunarPhase"] = makeLunarPhase(self.second_obj.lunar_phase["degrees_between_s_m"], self.geolat)
            else:
                template_dict["makeLunarPhase"] = ""

            # Houses and planet drawing
            template_dict["makeMainHousesGrid"] = draw_main_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
            )
            # template_dict["makeSecondaryHousesGrid"] = draw_secondary_house_grid(
            #     secondary_subject_houses_list=second_subject_houses_list,
            #     text_color=self.chart_colors_settings["paper_0"],
            #     house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
            # )
            template_dict["makeSecondaryHousesGrid"] = ""

            template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
                r=self.main_radius,
                first_subject_houses_list=first_subject_houses_list,
                standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
                first_house_color=self.planets_settings[12]["color"],
                tenth_house_color=self.planets_settings[13]["color"],
                seventh_house_color=self.planets_settings[14]["color"],
                fourth_house_color=self.planets_settings[15]["color"],
                c1=self.first_circle_radius,
                c3=self.third_circle_radius,
                chart_type=self.chart_type,
                external_view=self.external_view,
                second_subject_houses_list=second_subject_houses_list,
                transit_house_cusp_color=self.chart_colors_settings["houses_transit_line"],
            )

            template_dict["makePlanets"] = draw_planets(
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                available_planets_setting=self.available_planets_setting,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
                radius=self.main_radius,
                main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                chart_type=self.chart_type,
                third_circle_radius=self.third_circle_radius,
                external_view=self.external_view,
            )

            # Planet grids
            first_name_label = self._truncate_name(self.first_obj.name)
            transit_label = self._translate("transit", "Transit")
            first_return_grid_title = f"{first_name_label} ({self._translate('inner_wheel', 'Inner Wheel')})"
            second_return_grid_title = f"{transit_label} ({self._translate('outer_wheel', 'Outer Wheel')})"
            template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
                planets_and_houses_grid_title="",
                subject_name=first_return_grid_title,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
            )

            template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
                planets_and_houses_grid_title="",
                second_subject_name=second_return_grid_title,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
            )

            # House comparison grid
            if self.show_house_position_comparison:
                house_comparison_factory = HouseComparisonFactory(
                    first_subject=self.first_obj,  # type: ignore[arg-type]
                    second_subject=self.second_obj,  # type: ignore[arg-type]
                    active_points=self.active_points,
                )
                house_comparison = house_comparison_factory.get_house_comparison()

                template_dict["makeHouseComparisonGrid"] = draw_single_house_comparison_grid(
                    house_comparison,
                    celestial_point_language=self._language_model.celestial_points,
                    active_points=self.active_points,
                    points_owner_subject_number=2, # The second subject is the Transit
                    house_position_comparison_label=self._translate("house_position_comparison", "House Position Comparison"),
                    return_point_label=self._translate("transit_point", "Transit Point"),
                    natal_house_label=self._translate("house_position", "Natal House"),
                    x_position=980,
                )
            else:
                template_dict["makeHouseComparisonGrid"] = ""

        elif self.chart_type == "Synastry":
            # Set viewbox dynamically
            template_dict["viewbox"] = self._dynamic_viewbox()

            # Get houses list for secondary subject
            second_subject_houses_list = get_houses_list(self.second_obj) # type: ignore

            # Rings and circles
            template_dict["transitRing"] = draw_transit_ring(
                self.main_radius,
                self.chart_colors_settings["paper_1"],
                self.chart_colors_settings["zodiac_transit_ring_3"],
            )
            template_dict["degreeRing"] = draw_transit_ring_degree_steps(self.main_radius, self.first_obj.seventh_house.abs_pos)
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

            # Aspects
            if self.double_chart_aspect_grid_type == "list":
                template_dict["makeAspectGrid"] = ""
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                    f"{self.first_obj.name} - {self.second_obj.name} {self._translate('synastry_aspects', 'Synastry Aspects')}",  # type: ignore[union-attr]
                    self.aspects_list,
                    self.planets_settings,  # type: ignore[arg-type]
                    self.aspects_settings,  # type: ignore[arg-type]
                    chart_height=self.height,
                )
            else:
                template_dict["makeAspectGrid"] = ""
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                    self.chart_colors_settings["paper_0"],
                    self.available_planets_setting,
                    self.aspects_list,
                    550,
                    450,
                )

            template_dict["makeAspects"] = self._draw_all_transit_aspects_lines(self.main_radius, self.main_radius - 160)

            # Top left section
            template_dict["top_left_0"] = f"{self.first_obj.name}:"
            template_dict["top_left_1"] = f"{self.first_obj.city}, {self.first_obj.nation}" # type: ignore
            template_dict["top_left_2"] = format_datetime_with_timezone(self.first_obj.iso_formatted_local_datetime) # type: ignore
            template_dict["top_left_3"] = f"{self.second_obj.name}: " # type: ignore
            template_dict["top_left_4"] = f"{self.second_obj.city}, {self.second_obj.nation}" # type: ignore
            template_dict["top_left_5"] = format_datetime_with_timezone(self.second_obj.iso_formatted_local_datetime) # type: ignore

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropical":
                zodiac_info = f"{self._translate('zodiac', 'Zodiac')}: {self._translate('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self._translate('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = ""
            # FIXME!
            template_dict["bottom_left_1"] = "" # f"Compatibility Score: {16}/44" # type: ignore
            template_dict["bottom_left_2"] = zodiac_info
            template_dict["bottom_left_3"] = f"{self._translate('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)} {self._translate('houses', 'Houses')}"
            template_dict["bottom_left_4"] = f'{self._translate("perspective_type", "Perspective")}: {self._translate(self.first_obj.perspective_type.lower().replace(" ", "_"), self.first_obj.perspective_type)}'

            # Moon phase section calculations
            template_dict["makeLunarPhase"] = ""

            # Houses and planet drawing
            template_dict["makeMainHousesGrid"] = draw_main_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
            )

            template_dict["makeSecondaryHousesGrid"] = draw_secondary_house_grid(
                secondary_subject_houses_list=second_subject_houses_list,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
            )

            template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
                r=self.main_radius,
                first_subject_houses_list=first_subject_houses_list,
                standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
                first_house_color=self.planets_settings[12]["color"],
                tenth_house_color=self.planets_settings[13]["color"],
                seventh_house_color=self.planets_settings[14]["color"],
                fourth_house_color=self.planets_settings[15]["color"],
                c1=self.first_circle_radius,
                c3=self.third_circle_radius,
                chart_type=self.chart_type,
                external_view=self.external_view,
                second_subject_houses_list=second_subject_houses_list,
                transit_house_cusp_color=self.chart_colors_settings["houses_transit_line"],
            )

            template_dict["makePlanets"] = draw_planets(
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                available_planets_setting=self.available_planets_setting,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
                radius=self.main_radius,
                main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                chart_type=self.chart_type,
                third_circle_radius=self.third_circle_radius,
                external_view=self.external_view,
            )

            # Planet grid
            first_name_label = self._truncate_name(self.first_obj.name, 18, "…")  # type: ignore[union-attr]
            second_name_label = self._truncate_name(self.second_obj.name, 18, "…")  # type: ignore[union-attr]
            template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
                planets_and_houses_grid_title="",
                subject_name=f"{first_name_label} ({self._translate('inner_wheel', 'Inner Wheel')})",
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
            )
            template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
                planets_and_houses_grid_title="",
                second_subject_name= f"{second_name_label} ({self._translate('outer_wheel', 'Outer Wheel')})", # type: ignore
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
            )
            if self.show_house_position_comparison:
                house_comparison_factory = HouseComparisonFactory(
                    first_subject=self.first_obj,  # type: ignore[arg-type]
                    second_subject=self.second_obj,  # type: ignore[arg-type]
                    active_points=self.active_points,
                )
                house_comparison = house_comparison_factory.get_house_comparison()

                first_subject_label = self._truncate_name(self.first_obj.name, 8, "…", True)  # type: ignore[union-attr]
                second_subject_label = self._truncate_name(self.second_obj.name, 8, "…", True)  # type: ignore[union-attr]
                point_column_label = self._translate("point", "Point")
                comparison_label = self._translate("house_position_comparison", "House Position Comparison")

                first_subject_grid = draw_house_comparison_grid(
                    house_comparison,
                    celestial_point_language=self._language_model.celestial_points,
                    active_points=self.active_points,
                    points_owner_subject_number=1,
                    house_position_comparison_label=comparison_label,
                    return_point_label=first_subject_label + " " + point_column_label,
                    return_label=first_subject_label,
                    radix_label=second_subject_label,
                    x_position=1090,
                    y_position=0,
                )

                second_subject_grid = draw_house_comparison_grid(
                    house_comparison,
                    celestial_point_language=self._language_model.celestial_points,
                    active_points=self.active_points,
                    points_owner_subject_number=2,
                    house_position_comparison_label="",
                    return_point_label=second_subject_label + " " + point_column_label,
                    return_label=second_subject_label,
                    radix_label=first_subject_label,
                    x_position=1290,
                    y_position=0,
                )

                template_dict["makeHouseComparisonGrid"] = first_subject_grid + second_subject_grid
            else:
                template_dict["makeHouseComparisonGrid"] = ""

        elif self.chart_type == "DualReturnChart":
            # Set viewbox dynamically
            template_dict["viewbox"] = self._dynamic_viewbox()

            # Get houses list for secondary subject
            second_subject_houses_list = get_houses_list(self.second_obj) # type: ignore

            # Rings and circles
            template_dict["transitRing"] = draw_transit_ring(
                self.main_radius,
                self.chart_colors_settings["paper_1"],
                self.chart_colors_settings["zodiac_transit_ring_3"],
            )
            template_dict["degreeRing"] = draw_transit_ring_degree_steps(self.main_radius, self.first_obj.seventh_house.abs_pos)
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

            # Aspects
            if self.double_chart_aspect_grid_type == "list":
                title = self._translate("return_aspects", "Natal to Return Aspects")
                template_dict["makeAspectGrid"] = ""
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_list(
                    title,
                    self.aspects_list,
                    self.planets_settings,
                    self.aspects_settings,
                    max_columns=7,
                    chart_height=self.height,
                )  # type: ignore[arg-type]
            else:
                template_dict["makeAspectGrid"] = ""
                template_dict["makeDoubleChartAspectList"] = draw_transit_aspect_grid(
                    self.chart_colors_settings["paper_0"],
                    self.available_planets_setting,
                    self.aspects_list,
                    550,
                    450,
                )

            template_dict["makeAspects"] = self._draw_all_transit_aspects_lines(self.main_radius, self.main_radius - 160)


            # Top left section
            # Subject
            latitude_string = convert_latitude_coordinate_to_string(self.first_obj.lat, self._translate("north", "North"), self._translate("south", "South")) # type: ignore
            longitude_string = convert_longitude_coordinate_to_string(self.first_obj.lng, self._translate("east", "East"), self._translate("west", "West")) # type: ignore

            # Return
            return_latitude_string = convert_latitude_coordinate_to_string(self.second_obj.lat, self._translate("north", "North"), self._translate("south", "South")) # type: ignore
            return_longitude_string = convert_longitude_coordinate_to_string(self.second_obj.lng, self._translate("east", "East"), self._translate("west", "West")) # type: ignore

            if self.second_obj is not None and hasattr(self.second_obj, 'return_type') and self.second_obj.return_type == "Solar":
                template_dict["top_left_0"] = f"{self._translate('solar_return', 'Solar Return')}:"
            else:
                template_dict["top_left_0"] = f"{self._translate('lunar_return', 'Lunar Return')}:"
            template_dict["top_left_1"] = format_datetime_with_timezone(self.second_obj.iso_formatted_local_datetime) # type: ignore
            template_dict["top_left_2"] = f"{return_latitude_string} / {return_longitude_string}"
            template_dict["top_left_3"] = f"{self.first_obj.name}"
            template_dict["top_left_4"] = format_datetime_with_timezone(self.first_obj.iso_formatted_local_datetime) # type: ignore
            template_dict["top_left_5"] = f"{latitude_string} / {longitude_string}"

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropical":
                zodiac_info = f"{self._translate('zodiac', 'Zodiac')}: {self._translate('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self._translate('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = zodiac_info
            template_dict["bottom_left_1"] = f"{self._translate('domification', 'Domification')}: {self._translate('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)}"

            # Lunar phase information (optional)
            if self.first_obj.lunar_phase is not None:
                template_dict["bottom_left_2"] = f'{self._translate("lunation_day", "Lunation Day")}: {self.first_obj.lunar_phase.get("moon_phase", "")}'
                template_dict["bottom_left_3"] = f'{self._translate("lunar_phase", "Lunar Phase")}: {self._translate(self.first_obj.lunar_phase.moon_phase_name.lower().replace(" ", "_"), self.first_obj.lunar_phase.moon_phase_name)}'
            else:
                template_dict["bottom_left_2"] = ""
                template_dict["bottom_left_3"] = ""

            template_dict["bottom_left_4"] = f'{self._translate("perspective_type", "Perspective")}: {self._translate(self.first_obj.perspective_type.lower().replace(" ", "_"), self.first_obj.perspective_type)}'

            # Moon phase section calculations
            if self.first_obj.lunar_phase is not None:
                template_dict["makeLunarPhase"] = makeLunarPhase(self.first_obj.lunar_phase["degrees_between_s_m"], self.geolat)
            else:
                template_dict["makeLunarPhase"] = ""

            # Houses and planet drawing
            template_dict["makeMainHousesGrid"] = draw_main_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
            )

            template_dict["makeSecondaryHousesGrid"] = draw_secondary_house_grid(
                secondary_subject_houses_list=second_subject_houses_list,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
            )

            template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
                r=self.main_radius,
                first_subject_houses_list=first_subject_houses_list,
                standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
                first_house_color=self.planets_settings[12]["color"],
                tenth_house_color=self.planets_settings[13]["color"],
                seventh_house_color=self.planets_settings[14]["color"],
                fourth_house_color=self.planets_settings[15]["color"],
                c1=self.first_circle_radius,
                c3=self.third_circle_radius,
                chart_type=self.chart_type,
                external_view=self.external_view,
                second_subject_houses_list=second_subject_houses_list,
                transit_house_cusp_color=self.chart_colors_settings["houses_transit_line"],
            )

            template_dict["makePlanets"] = draw_planets(
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                available_planets_setting=self.available_planets_setting,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
                radius=self.main_radius,
                main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                chart_type=self.chart_type,
                third_circle_radius=self.third_circle_radius,
                external_view=self.external_view,
            )

            # Planet grid
            first_name_label = self._truncate_name(self.first_obj.name)
            if self.second_obj is not None and hasattr(self.second_obj, 'return_type') and self.second_obj.return_type == "Solar":
                first_return_grid_title = f"{first_name_label} ({self._translate('inner_wheel', 'Inner Wheel')})"
                second_return_grid_title = f"{self._translate('solar_return', 'Solar Return')} ({self._translate('outer_wheel', 'Outer Wheel')})"
            else:
                first_return_grid_title = f"{first_name_label} ({self._translate('inner_wheel', 'Inner Wheel')})"
                second_return_grid_title = f'{self._translate("lunar_return", "Lunar Return")} ({self._translate("outer_wheel", "Outer Wheel")})'
            template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
                planets_and_houses_grid_title="",
                subject_name=first_return_grid_title,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
            )
            template_dict["makeSecondaryPlanetGrid"] = draw_secondary_planet_grid(
                planets_and_houses_grid_title="",
                second_subject_name=second_return_grid_title,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
            )

            if self.show_house_position_comparison:
                house_comparison_factory = HouseComparisonFactory(
                    first_subject=self.first_obj,  # type: ignore[arg-type]
                    second_subject=self.second_obj,  # type: ignore[arg-type]
                    active_points=self.active_points,
                )
                house_comparison = house_comparison_factory.get_house_comparison()

                template_dict["makeHouseComparisonGrid"] = draw_house_comparison_grid(
                    house_comparison,
                    celestial_point_language=self._language_model.celestial_points,
                    active_points=self.active_points,
                    points_owner_subject_number=2, # The second subject is the Solar Return
                    house_position_comparison_label=self._translate("house_position_comparison", "House Position Comparison"),
                    return_point_label=self._translate("return_point", "Return Point"),
                    return_label=self._translate("Return", "DualReturnChart"),
                    radix_label=self._translate("Natal", "Natal"),
                )
            else:
                template_dict["makeHouseComparisonGrid"] = ""

        elif self.chart_type == "SingleReturnChart":
            # Set viewbox dynamically
            template_dict["viewbox"] = self._dynamic_viewbox()

            # Rings and circles
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

            # Aspects
            template_dict["makeDoubleChartAspectList"] = ""
            template_dict["makeAspectGrid"] = draw_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self.available_planets_setting,
                self.aspects_list,
            )
            template_dict["makeAspects"] = self._draw_all_aspects_lines(self.main_radius, self.main_radius - self.third_circle_radius)

            # Top left section
            latitude_string = convert_latitude_coordinate_to_string(self.geolat, self._translate("north", "North"), self._translate("south", "South"))
            longitude_string = convert_longitude_coordinate_to_string(self.geolon, self._translate("east", "East"), self._translate("west", "West"))

            template_dict["top_left_0"] = f'{self._translate("info", "Info")}:'
            template_dict["top_left_1"] = format_datetime_with_timezone(self.first_obj.iso_formatted_local_datetime) # type: ignore
            template_dict["top_left_2"] = f"{self.first_obj.city}, {self.first_obj.nation}"
            template_dict["top_left_3"] = f"{self._translate('latitude', 'Latitude')}: {latitude_string}"
            template_dict["top_left_4"] = f"{self._translate('longitude', 'Longitude')}: {longitude_string}"

            if hasattr(self.first_obj, 'return_type') and self.first_obj.return_type == "Solar":
                template_dict["top_left_5"] = f"{self._translate('type', 'Type')}: {self._translate('solar_return', 'Solar Return')}"
            else:
                template_dict["top_left_5"] = f"{self._translate('type', 'Type')}: {self._translate('lunar_return', 'Lunar Return')}"

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropical":
                zodiac_info = f"{self._translate('zodiac', 'Zodiac')}: {self._translate('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self._translate('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = zodiac_info
            template_dict["bottom_left_1"] = f"{self._translate('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)} {self._translate('houses', 'Houses')}"

            # Lunar phase information (optional)
            if self.first_obj.lunar_phase is not None:
                template_dict["bottom_left_2"] = f'{self._translate("lunation_day", "Lunation Day")}: {self.first_obj.lunar_phase.get("moon_phase", "")}'
                template_dict["bottom_left_3"] = f'{self._translate("lunar_phase", "Lunar Phase")}: {self._translate(self.first_obj.lunar_phase.moon_phase_name.lower().replace(" ", "_"), self.first_obj.lunar_phase.moon_phase_name)}'
            else:
                template_dict["bottom_left_2"] = ""
                template_dict["bottom_left_3"] = ""

            template_dict["bottom_left_4"] = f'{self._translate("perspective_type", "Perspective")}: {self._translate(self.first_obj.perspective_type.lower().replace(" ", "_"), self.first_obj.perspective_type)}'

            # Moon phase section calculations
            if self.first_obj.lunar_phase is not None:
                template_dict["makeLunarPhase"] = makeLunarPhase(self.first_obj.lunar_phase["degrees_between_s_m"], self.geolat)
            else:
                template_dict["makeLunarPhase"] = ""

            # Houses and planet drawing
            template_dict["makeMainHousesGrid"] = draw_main_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self._translate("cusp", "Cusp"),
            )
            template_dict["makeSecondaryHousesGrid"] = ""

            template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
                r=self.main_radius,
                first_subject_houses_list=first_subject_houses_list,
                standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
                first_house_color=self.planets_settings[12]["color"],
                tenth_house_color=self.planets_settings[13]["color"],
                seventh_house_color=self.planets_settings[14]["color"],
                fourth_house_color=self.planets_settings[15]["color"],
                c1=self.first_circle_radius,
                c3=self.third_circle_radius,
                chart_type=self.chart_type,
                external_view=self.external_view,
            )

            template_dict["makePlanets"] = draw_planets(
                available_planets_setting=self.available_planets_setting,
                chart_type=self.chart_type,
                radius=self.main_radius,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                third_circle_radius=self.third_circle_radius,
                main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
                external_view=self.external_view,
            )

            template_dict["makeMainPlanetGrid"] = draw_main_planet_grid(
                planets_and_houses_grid_title=self._translate("planets_and_house", "Points for"),
                subject_name=self.first_obj.name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self._language_model.celestial_points,
            )
            template_dict["makeSecondaryPlanetGrid"] = ""
            template_dict["makeHouseComparisonGrid"] = ""

        return ChartTemplateModel(**template_dict)

    def generate_svg_string(self, minify: bool = False, remove_css_variables=False, *, custom_title: Union[str, None] = None) -> str:
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

        if remove_css_variables:
            template = inline_css_variables_in_svg(template)

        if minify:
            template = scourString(template).replace('"', "'").replace("\n", "").replace("\t", "").replace("    ", "").replace("  ", "")

        else:
            template = template.replace('"', "'")

        return template

    def save_svg(self, output_path: Union[str, Path, None] = None, filename: Union[str, None] = None, minify: bool = False, remove_css_variables=False, *, custom_title: Union[str, None] = None):
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

        # Convert output_path to Path object, default to home directory
        output_directory = Path(output_path) if output_path is not None else Path.home()

        # Determine filename
        if filename is not None:
            chartname = output_directory / f"{filename}.svg"
        else:
            # Use default filename pattern
            chart_type_for_filename = self.chart_type

            if self.chart_type == "DualReturnChart" and self.second_obj is not None and hasattr(self.second_obj, 'return_type') and self.second_obj.return_type == "Lunar":
                chartname = output_directory / f"{self.first_obj.name} - {chart_type_for_filename} Chart - Lunar Return.svg"
            elif self.chart_type == "DualReturnChart" and self.second_obj is not None and hasattr(self.second_obj, 'return_type') and self.second_obj.return_type == "Solar":
                chartname = output_directory / f"{self.first_obj.name} - {chart_type_for_filename} Chart - Solar Return.svg"
            else:
                chartname = output_directory / f"{self.first_obj.name} - {chart_type_for_filename} Chart.svg"

        with open(chartname, "w", encoding="utf-8", errors="ignore") as output_file:
            output_file.write(self.template)

        print(f"SVG Generated Correctly in: {chartname}")

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

        if remove_css_variables:
            template = inline_css_variables_in_svg(template)

        if minify:
            template = scourString(template).replace('"', "'").replace("\n", "").replace("\t", "").replace("    ", "").replace("  ", "")

        else:
            template = template.replace('"', "'")

        return template

    def save_wheel_only_svg_file(self, output_path: Union[str, Path, None] = None, filename: Union[str, None] = None, minify: bool = False, remove_css_variables=False):
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

        # Convert output_path to Path object, default to home directory
        output_directory = Path(output_path) if output_path is not None else Path.home()

        # Determine filename
        if filename is not None:
            chartname = output_directory / f"{filename}.svg"
        else:
            # Use default filename pattern
            chart_type_for_filename = "ExternalNatal" if self.external_view and self.chart_type == "Natal" else self.chart_type
            chartname = output_directory / f"{self.first_obj.name} - {chart_type_for_filename} Chart - Wheel Only.svg"

        with open(chartname, "w", encoding="utf-8", errors="ignore") as output_file:
            output_file.write(template)

        print(f"SVG Generated Correctly in: {chartname}")

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

        template = Template(template).substitute({**template_dict.model_dump(), "makeAspectGrid": aspects_grid, "viewbox": viewbox_override})

        if remove_css_variables:
            template = inline_css_variables_in_svg(template)

        if minify:
            template = scourString(template).replace('"', "'").replace("\n", "").replace("\t", "").replace("    ", "").replace("  ", "")

        else:
            template = template.replace('"', "'")

        return template

    def save_aspect_grid_only_svg_file(self, output_path: Union[str, Path, None] = None, filename: Union[str, None] = None, minify: bool = False, remove_css_variables=False):
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

        # Convert output_path to Path object, default to home directory
        output_directory = Path(output_path) if output_path is not None else Path.home()

        # Determine filename
        if filename is not None:
            chartname = output_directory / f"{filename}.svg"
        else:
            # Use default filename pattern
            chart_type_for_filename = "ExternalNatal" if self.external_view and self.chart_type == "Natal" else self.chart_type
            chartname = output_directory / f"{self.first_obj.name} - {chart_type_for_filename} Chart - Aspect Grid Only.svg"

        with open(chartname, "w", encoding="utf-8", errors="ignore") as output_file:
            output_file.write(template)

        print(f"SVG Generated Correctly in: {chartname}")

if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    from kerykeion.planetary_return_factory import PlanetaryReturnFactory
    from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
    from kerykeion.chart_data_factory import ChartDataFactory
    from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

    ACTIVE_PLANETS: list[AstrologicalPoint] = DEFAULT_ACTIVE_POINTS
    # ACTIVE_PLANETS: list[AstrologicalPoint] = ALL_ACTIVE_POINTS
    setup_logging(level="info")

    subject = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", active_points=ACTIVE_PLANETS)

    return_factory = PlanetaryReturnFactory(
        subject,
        city="Los Angeles",
        nation="US",
        lng=-118.2437,
        lat=34.0522,
        tz_str="America/Los_Angeles",
        altitude=0
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
    birth_chart.save_svg() # minify=True, remove_css_variables=True)

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

    solar_return_chart.save_svg() # minify=True, remove_css_variables=True)

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

    single_wheel_return_chart.save_svg() # minify=True, remove_css_variables=True)

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
    lunar_return_chart.save_svg() # minify=True, remove_css_variables=True)

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
    transit_chart.save_svg() # minify=True, remove_css_variables=True)

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
    synastry_chart.save_svg() # minify=True, remove_css_variables=True)

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
        double_chart_aspect_grid_type="table"
    )
    transit_chart_with_grid.save_svg() # minify=True, remove_css_variables=True)
    transit_chart_with_grid.save_aspect_grid_only_svg_file()
    transit_chart_with_grid.save_wheel_only_svg_file()

    print("✅ All chart examples completed using ChartDataFactory + ChartDrawer architecture!")
