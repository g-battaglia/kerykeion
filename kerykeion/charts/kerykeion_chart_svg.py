# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""


import logging
import swisseph as swe
from typing import get_args

from kerykeion.settings.kerykeion_settings import get_settings
from kerykeion.aspects.synastry_aspects import SynastryAspects
from kerykeion.aspects.natal_aspects import NatalAspects
from kerykeion.astrological_subject import AstrologicalSubject
from kerykeion.kr_types import (
    KerykeionException,
    ChartType,
    KerykeionPointModel,
    Sign,
    ActiveAspect,
)
from kerykeion.kr_types import ChartTemplateDictionary
from kerykeion.kr_types.kr_models import (
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    PlanetReturnModel,
)
from kerykeion.kr_types.settings_models import (
    KerykeionSettingsCelestialPointModel,
    KerykeionSettingsModel,
)
from kerykeion.kr_types.kr_literals import (
    KerykeionChartTheme,
    KerykeionChartLanguage,
    AxialCusps,
    Planet,
)
from kerykeion.charts.charts_utils import (
    draw_zodiac_slice,
    convert_latitude_coordinate_to_string,
    convert_longitude_coordinate_to_string,
    draw_aspect_line,
    draw_transit_ring_degree_steps,
    draw_degree_ring,
    draw_transit_ring,
    draw_first_circle,
    draw_second_circle,
    draw_third_circle,
    draw_aspect_grid,
    draw_houses_cusps_and_text_number,
    draw_transit_aspect_list,
    draw_transit_aspect_grid,
    calculate_moon_phase_chart_params,
    draw_house_grid,
    draw_planet_grid,
    format_location_string,
    format_datetime_with_timezone,
    calculate_element_points,
)
from kerykeion.charts.draw_planets_v2 import draw_planets_v2 as draw_planets
from kerykeion.utilities import get_houses_list, inline_css_variables_in_svg
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS
from pathlib import Path
from scour.scour import scourString
from string import Template
from typing import Union, List, Literal
from datetime import datetime


class KerykeionChartSVG:
    """
    KerykeionChartSVG generates astrological chart visualizations as SVG files.

    This class supports creating full chart SVGs, wheel-only SVGs, and aspect-grid-only SVGs
    for various chart types including Natal, ExternalNatal, Transit, Synastry, and Composite.
    Charts are rendered using XML templates and drawing utilities, with customizable themes,
    language, active points, and aspects.
    The rendered SVGs can be saved to a specified output directory or, by default, to the user's home directory.

    NOTE:
        The generated SVG files are optimized for web use, opening in browsers. If you want to
        use them in other applications, you might need to adjust the SVG settings or styles.

    Args:
        first_obj (AstrologicalSubject | AstrologicalSubjectModel | CompositeSubjectModel):
            The primary astrological subject for the chart.
        chart_type (ChartType, optional):
            The type of chart to generate ('Natal', 'ExternalNatal', 'Transit', 'Synastry', 'Composite').
            Defaults to 'Natal'.
        second_obj (AstrologicalSubject | AstrologicalSubjectModel, optional):
            The secondary subject for Transit or Synastry charts. Not required for Natal or Composite.
        new_output_directory (str | Path, optional):
            Directory to write generated SVG files. Defaults to the user's home directory.
        new_settings_file (Path | dict | KerykeionSettingsModel, optional):
            Path or settings object to override default chart configuration (colors, fonts, aspects).
        theme (KerykeionChartTheme, optional):
            CSS theme for the chart. If None, no default styles are applied. Defaults to 'classic'.
        double_chart_aspect_grid_type (Literal['list', 'table'], optional):
            Specifies rendering style for double-chart aspect grids. Defaults to 'list'.
        chart_language (KerykeionChartLanguage, optional):
            Language code for chart labels. Defaults to 'EN'.
        active_points (list[Planet | AxialCusps], optional):
            List of celestial points and angles to include. Defaults to DEFAULT_ACTIVE_POINTS.
            Example:
            ["Sun", "Moon", "Mercury", "Venus"]

        active_aspects (list[ActiveAspect], optional):
            List of aspects (name and orb) to calculate. Defaults to DEFAULT_ACTIVE_ASPECTS.
            Example:
            [
                {"name": "conjunction", "orb": 10},
                {"name": "opposition", "orb": 10},
                {"name": "trine", "orb": 8},
                {"name": "sextile", "orb": 6},
                {"name": "square", "orb": 5},
                {"name": "quintile", "orb": 1},
            ]

    Public Methods:
        makeTemplate(minify=False, remove_css_variables=False) -> str:
            Render the full chart SVG as a string without writing to disk. Use `minify=True`
            to remove whitespace and quotes, and `remove_css_variables=True` to embed CSS vars.

        makeSVG(minify=False, remove_css_variables=False) -> None:
            Generate and write the full chart SVG file to the output directory.
            Filenames follow the pattern:
            '{subject.name} - {chart_type} Chart.svg'.

        makeWheelOnlyTemplate(minify=False, remove_css_variables=False) -> str:
            Render only the chart wheel (no aspect grid) as an SVG string.

        makeWheelOnlySVG(minify=False, remove_css_variables=False) -> None:
            Generate and write the wheel-only SVG file:
            '{subject.name} - {chart_type} Chart - Wheel Only.svg'.

        makeAspectGridOnlyTemplate(minify=False, remove_css_variables=False) -> str:
            Render only the aspect grid as an SVG string.

        makeAspectGridOnlySVG(minify=False, remove_css_variables=False) -> None:
            Generate and write the aspect-grid-only SVG file:
            '{subject.name} - {chart_type} Chart - Aspect Grid Only.svg'.
    """

    # Constants
    _BASIC_CHART_VIEWBOX = "0 0 820 550.0"
    _WIDE_CHART_VIEWBOX = "0 0 1200 546.0"
    _ULTRA_WIDE_CHART_VIEWBOX = "0 0 1300 546.0"
    _TRANSIT_CHART_WITH_TABLE_VIWBOX = "0 0 960 546.0"

    _DEFAULT_HEIGHT = 550
    _DEFAULT_FULL_WIDTH = 1200
    _DEFAULT_NATAL_WIDTH = 820
    _DEFAULT_FULL_WIDTH_WITH_TABLE = 1200
    _DEFAULT_ULTRA_WIDE_WIDTH = 1300
    _PLANET_IN_ZODIAC_EXTRA_POINTS = 10

    # Set at init
    first_obj: Union[AstrologicalSubject, AstrologicalSubjectModel, CompositeSubjectModel]
    second_obj: Union[AstrologicalSubject, AstrologicalSubjectModel, PlanetReturnModel, None]
    chart_type: ChartType
    new_output_directory: Union[Path, None]
    new_settings_file: Union[Path, None, KerykeionSettingsModel, dict]
    output_directory: Path
    new_settings_file: Union[Path, None, KerykeionSettingsModel, dict]
    theme: Union[KerykeionChartTheme, None]
    double_chart_aspect_grid_type: Literal["list", "table"]
    chart_language: KerykeionChartLanguage
    active_points: List[Union[Planet, AxialCusps]]
    active_aspects: List[ActiveAspect]

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
    planets_settings: dict
    aspects_settings: dict
    available_planets_setting: List[KerykeionSettingsCelestialPointModel]
    height: float
    location: str
    geolat: float
    geolon: float
    template: str

    def __init__(
        self,
        first_obj: Union[AstrologicalSubject, AstrologicalSubjectModel, CompositeSubjectModel],
        chart_type: ChartType = "Natal",
        second_obj: Union[AstrologicalSubject, AstrologicalSubjectModel, PlanetReturnModel, None] = None,
        new_output_directory: Union[str, None] = None,
        new_settings_file: Union[Path, None, KerykeionSettingsModel, dict] = None,
        theme: Union[KerykeionChartTheme, None] = "classic",
        double_chart_aspect_grid_type: Literal["list", "table"] = "list",
        chart_language: KerykeionChartLanguage = "EN",
        active_points: List[Union[Planet, AxialCusps]] = DEFAULT_ACTIVE_POINTS,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
    ):
        """
        Initialize the chart generator with subject data and configuration options.

        Args:
            first_obj (AstrologicalSubject, AstrologicalSubjectModel, or CompositeSubjectModel):
                Primary astrological subject instance.
            chart_type (ChartType, optional):
                Type of chart to generate (e.g., 'Natal', 'Transit').
            second_obj (AstrologicalSubject or AstrologicalSubjectModel, optional):
                Secondary subject for Transit or Synastry charts.
            new_output_directory (str or Path, optional):
                Base directory to save generated SVG files.
            new_settings_file (Path, dict, or KerykeionSettingsModel, optional):
                Custom settings source for chart colors, fonts, and aspects.
            theme (KerykeionChartTheme or None, optional):
                CSS theme to apply; None for default styling.
            double_chart_aspect_grid_type (Literal['list','table'], optional):
                Layout style for double-chart aspect grids ('list' or 'table').
            chart_language (KerykeionChartLanguage, optional):
                Language code for chart labels (e.g., 'EN', 'IT').
            active_points (List[Planet or AxialCusps], optional):
                Celestial points to include in the chart visualization.
            active_aspects (List[ActiveAspect], optional):
                Aspects to calculate, each defined by name and orb.
        """
        # --------------------
        # COMMON INITIALIZATION
        # --------------------
        home_directory = Path.home()
        self.new_settings_file = new_settings_file
        self.chart_language = chart_language
        self.active_points = active_points
        self.active_aspects = active_aspects
        self.chart_type = chart_type
        self.double_chart_aspect_grid_type = double_chart_aspect_grid_type

        # Set output directory
        if new_output_directory:
            self.output_directory = Path(new_output_directory)
        else:
            self.output_directory = home_directory

        # Load settings
        self.parse_json_settings(new_settings_file)

        # Primary subject
        self.first_obj = first_obj

        # Default radius for all charts
        self.main_radius = 240

        # Configure available planets
        self.available_planets_setting = []
        for body in self.planets_settings:
            if body["name"] in active_points:
                body["is_active"] = True
                self.available_planets_setting.append(body)

        # Set available celestial points
        available_celestial_points_names = [body["name"].lower() for body in self.available_planets_setting]
        self.available_kerykeion_celestial_points = []
        for body in available_celestial_points_names:
            self.available_kerykeion_celestial_points.append(self.first_obj.get(body))

        # ------------------------
        # CHART TYPE SPECIFIC SETUP
        # ------------------------

        if self.chart_type in ["Natal", "ExternalNatal"]:
            # --- NATAL / EXTERNAL NATAL CHART SETUP ---

            # Validate Subject
            if not isinstance(self.first_obj, AstrologicalSubjectModel) and not isinstance(self.first_obj, AstrologicalSubject):
                raise KerykeionException("First object must be an AstrologicalSubjectModel or AstrologicalSubject instance.")

            # Calculate aspects
            natal_aspects_instance = NatalAspects(
                self.first_obj,
                new_settings_file=self.new_settings_file,
                active_points=active_points,
                active_aspects=active_aspects,
            )
            self.aspects_list = natal_aspects_instance.relevant_aspects

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            self.width = self._DEFAULT_NATAL_WIDTH

            # Location and coordinates
            self.location = self.first_obj.city
            self.geolat = self.first_obj.lat
            self.geolon = self.first_obj.lng

            # Circle radii
            if self.chart_type == "ExternalNatal":
                self.first_circle_radius = 56
                self.second_circle_radius = 92
                self.third_circle_radius = 112
            else:
                self.first_circle_radius = 0
                self.second_circle_radius = 36
                self.third_circle_radius = 120

        elif self.chart_type == "Composite":
            # --- COMPOSITE CHART SETUP ---

            # Validate Subject
            if not isinstance(self.first_obj, CompositeSubjectModel):
                raise KerykeionException("First object must be a CompositeSubjectModel instance.")

            # Calculate aspects
            self.aspects_list = NatalAspects(self.first_obj, new_settings_file=self.new_settings_file, active_points=active_points).relevant_aspects

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            self.width = self._DEFAULT_NATAL_WIDTH

            # Location and coordinates (average of both subjects)
            self.location = ""
            self.geolat = (self.first_obj.first_subject.lat + self.first_obj.second_subject.lat) / 2
            self.geolon = (self.first_obj.first_subject.lng + self.first_obj.second_subject.lng) / 2

            # Circle radii
            self.first_circle_radius = 0
            self.second_circle_radius = 36
            self.third_circle_radius = 120

        elif self.chart_type == "Transit":
            # --- TRANSIT CHART SETUP ---

            # Validate Subjects
            if not second_obj:
                raise KerykeionException("Second object is required for Transit charts.")
            if not isinstance(self.first_obj, AstrologicalSubjectModel) and not isinstance(self.first_obj, AstrologicalSubject):
                raise KerykeionException("First object must be an AstrologicalSubjectModel or AstrologicalSubject instance.")
            if not isinstance(second_obj, AstrologicalSubjectModel) and not isinstance(second_obj, AstrologicalSubject):
                raise KerykeionException("Second object must be an AstrologicalSubjectModel or AstrologicalSubject instance.")

            # Secondary subject setup
            self.second_obj = second_obj

            # Calculate aspects (transit to natal)
            synastry_aspects_instance = SynastryAspects(
                self.second_obj,
                self.first_obj,
                new_settings_file=self.new_settings_file,
                active_points=active_points,
                active_aspects=active_aspects,
            )
            self.aspects_list = synastry_aspects_instance.relevant_aspects

            # Secondary subject available points
            self.t_available_kerykeion_celestial_points = []
            for body in available_celestial_points_names:
                self.t_available_kerykeion_celestial_points.append(self.second_obj.get(body))

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            if self.double_chart_aspect_grid_type == "table":
                self.width = self._DEFAULT_FULL_WIDTH_WITH_TABLE
            else:
                self.width = self._DEFAULT_FULL_WIDTH

            # Location and coordinates (from transit subject)
            self.location = self.second_obj.city
            self.geolat = self.second_obj.lat
            self.geolon = self.second_obj.lng
            self.t_name = self.language_settings["transit_name"]

            # Circle radii
            self.first_circle_radius = 0
            self.second_circle_radius = 36
            self.third_circle_radius = 120

        elif self.chart_type == "Synastry":
            # --- SYNASTRY CHART SETUP ---

            # Validate Subjects
            if not second_obj:
                raise KerykeionException("Second object is required for Synastry charts.")
            if not isinstance(self.first_obj, AstrologicalSubjectModel) and not isinstance(self.first_obj, AstrologicalSubject):
                raise KerykeionException("First object must be an AstrologicalSubjectModel or AstrologicalSubject instance.")
            if not isinstance(second_obj, AstrologicalSubjectModel) and not isinstance(second_obj, AstrologicalSubject):
                raise KerykeionException("Second object must be an AstrologicalSubjectModel or AstrologicalSubject instance.")

            # Secondary subject setup
            self.second_obj = second_obj

            # Calculate aspects (natal to partner)
            synastry_aspects_instance = SynastryAspects(
                self.first_obj,
                self.second_obj,
                new_settings_file=self.new_settings_file,
                active_points=active_points,
                active_aspects=active_aspects,
            )
            self.aspects_list = synastry_aspects_instance.relevant_aspects

            # Secondary subject available points
            self.t_available_kerykeion_celestial_points = []
            for body in available_celestial_points_names:
                self.t_available_kerykeion_celestial_points.append(self.second_obj.get(body))

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            self.width = self._DEFAULT_FULL_WIDTH

            # Location and coordinates (from primary subject)
            self.location = self.first_obj.city
            self.geolat = self.first_obj.lat
            self.geolon = self.first_obj.lng

            # Circle radii
            self.first_circle_radius = 0
            self.second_circle_radius = 36
            self.third_circle_radius = 120

        elif self.chart_type == "Return":
            # --- RETURN CHART SETUP ---

            # Validate Subjects
            if not second_obj:
                raise KerykeionException("Second object is required for Return charts.")
            if not isinstance(self.first_obj, AstrologicalSubjectModel) and not isinstance(self.first_obj, AstrologicalSubject):
                raise KerykeionException("First object must be an AstrologicalSubjectModel or AstrologicalSubject instance.")
            if not isinstance(second_obj, PlanetReturnModel):
                raise KerykeionException("Second object must be a PlanetReturnModel instance.")

            # Secondary subject setup
            self.second_obj = second_obj

            # Calculate aspects (natal to return)
            synastry_aspects_instance = SynastryAspects(
                self.first_obj,
                self.second_obj,
                new_settings_file=self.new_settings_file,
                active_points=active_points,
                active_aspects=active_aspects,
            )
            self.aspects_list = synastry_aspects_instance.relevant_aspects

            # Secondary subject available points
            self.t_available_kerykeion_celestial_points = []
            for body in available_celestial_points_names:
                self.t_available_kerykeion_celestial_points.append(self.second_obj.get(body))

            # Screen size
            self.height = self._DEFAULT_HEIGHT
            self.width = self._DEFAULT_ULTRA_WIDE_WIDTH

            # Location and coordinates (from natal subject)
            self.location = self.first_obj.city
            self.geolat = self.first_obj.lat
            self.geolon = self.first_obj.lng

            # Circle radii
            self.first_circle_radius = 0
            self.second_circle_radius = 36
            self.third_circle_radius = 120

        # --------------------
        # FINAL COMMON SETUP
        # --------------------

        # Calculate element points
        celestial_points_names = [body["name"].lower() for body in self.available_planets_setting]
        element_totals = calculate_element_points(
            self.available_planets_setting,
            celestial_points_names,
            self.first_obj,
            self._PLANET_IN_ZODIAC_EXTRA_POINTS,
        )

        self.fire = element_totals["fire"]
        self.earth = element_totals["earth"]
        self.air = element_totals["air"]
        self.water = element_totals["water"]

        # Set up theme
        if theme not in get_args(KerykeionChartTheme) and theme is not None:
            raise KerykeionException(f"Theme {theme} is not available. Set None for default theme.")

        self.set_up_theme(theme)

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

    def set_output_directory(self, dir_path: Path) -> None:
        """
        Set the directory where generated SVG files will be saved.

        Args:
            dir_path (Path): Target directory for SVG output.
        """
        self.output_directory = dir_path
        logging.info(f"Output directory set to: {self.output_directory}")

    def parse_json_settings(self, settings_file_or_dict: Union[Path, dict, KerykeionSettingsModel, None]) -> None:
        """
        Load and parse chart configuration settings.

        Args:
            settings_file_or_dict (Path, dict, or KerykeionSettingsModel):
                Source for custom chart settings.
        """
        settings = get_settings(settings_file_or_dict)

        self.language_settings = settings["language_settings"][self.chart_language]
        self.chart_colors_settings = settings["chart_colors"]
        self.planets_settings = settings["celestial_points"]
        self.aspects_settings = settings["aspects"]

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

    def _create_template_dictionary(self) -> ChartTemplateDictionary:
        """
        Assemble chart data and rendering instructions into a template dictionary.

        Gathers styling, dimensions, and SVG fragments for chart components based on
        chart type and subjects.

        Returns:
            ChartTemplateDictionary: Populated structure of template variables.
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

        # Set paper colors
        template_dict["paper_color_0"] = self.chart_colors_settings["paper_0"]
        template_dict["paper_color_1"] = self.chart_colors_settings["paper_1"]

        # Set planet colors
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
        total = self.fire + self.water + self.earth + self.air
        fire_percentage = int(round(100 * self.fire / total))
        earth_percentage = int(round(100 * self.earth / total))
        air_percentage = int(round(100 * self.air / total))
        water_percentage = int(round(100 * self.water / total))

        template_dict["fire_string"] = f"{self.language_settings['fire']} {fire_percentage}%"
        template_dict["earth_string"] = f"{self.language_settings['earth']} {earth_percentage}%"
        template_dict["air_string"] = f"{self.language_settings['air']} {air_percentage}%"
        template_dict["water_string"] = f"{self.language_settings['water']} {water_percentage}%"

        # Moon phase section calculations
        moon_phase_dict = calculate_moon_phase_chart_params(self.first_obj.lunar_phase["degrees_between_s_m"], self.geolat)
        template_dict["lunar_phase_rotate"] = moon_phase_dict["lunar_phase_rotate"]
        template_dict["lunar_phase_circle_center_x"] = moon_phase_dict["circle_center_x"]
        template_dict["lunar_phase_circle_radius"] = moon_phase_dict["circle_radius"]

        # Get houses list for main subject
        first_subject_houses_list = get_houses_list(self.first_obj)

        # ------------------------------- #
        #  CHART TYPE SPECIFIC SETTINGS   #
        # ------------------------------- #

        if self.chart_type in ["Natal", "ExternalNatal"]:
            # Set viewbox
            template_dict["viewbox"] = self._BASIC_CHART_VIEWBOX

            # Rings and circles
            template_dict["transitRing"] = ""
            template_dict["degreeRing"] = draw_degree_ring(
                self.main_radius,
                self.first_circle_radius,
                self.first_obj.seventh_house.abs_pos,
                self.chart_colors_settings["paper_0"],
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
            template_dict["makeAspectGrid"] = draw_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self.available_planets_setting,
                self.aspects_list,
            )
            template_dict["makeAspects"] = self._draw_all_aspects_lines(self.main_radius, self.main_radius - self.third_circle_radius)

            # Chart title
            template_dict["stringTitle"] = self.first_obj.name

            # Top left section
            latitude_string = convert_latitude_coordinate_to_string(self.geolat, self.language_settings["north"], self.language_settings["south"])
            longitude_string = convert_longitude_coordinate_to_string(self.geolon, self.language_settings["east"], self.language_settings["west"])

            template_dict["top_left_0"] = f'{self.language_settings["info"]}:'
            template_dict["top_left_1"] = format_location_string(self.location)
            template_dict["top_left_2"] = format_datetime_with_timezone(self.first_obj.iso_formatted_local_datetime) # type: ignore
            template_dict["top_left_3"] = f"{self.language_settings['latitude']}: {latitude_string}"
            template_dict["top_left_4"] = f"{self.language_settings['longitude']}: {longitude_string}"
            template_dict["top_left_5"] = f"{self.language_settings['type']}: {self.language_settings.get(self.chart_type, self.chart_type)}"

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropic":
                zodiac_info = f"{self.language_settings.get('zodiac', 'Zodiac')}: {self.language_settings.get('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self.language_settings.get('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = f"{self.language_settings.get('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)} {self.language_settings.get('houses', 'Houses')}"
            template_dict["bottom_left_1"] = zodiac_info
            template_dict["bottom_left_2"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")} {self.language_settings.get("day", "Day").lower()}: {self.first_obj.lunar_phase.get("moon_phase", "")}'
            template_dict["bottom_left_3"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.language_settings.get(self.first_obj.lunar_phase.moon_phase_name.lower().replace(" ", "_"), self.first_obj.lunar_phase.moon_phase_name)}'
            template_dict["bottom_left_4"] = f'{self.language_settings.get(self.first_obj.perspective_type.lower().replace(" ", "_"), self.first_obj.perspective_type)}'

            # Houses and planet drawing
            template_dict["makeHousesGrid"] = draw_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self.language_settings["cusp"],
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
            )

            template_dict["makePlanets"] = draw_planets(
                available_planets_setting=self.available_planets_setting,
                chart_type=self.chart_type,
                radius=self.main_radius,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                third_circle_radius=self.third_circle_radius,
                main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
            )

            template_dict["makePlanetGrid"] = draw_planet_grid(
                planets_and_houses_grid_title=self.language_settings["planets_and_house"],
                subject_name=self.first_obj.name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self.language_settings["celestial_points"],
            )

        elif self.chart_type == "Composite":
            # Set viewbox
            template_dict["viewbox"] = self._BASIC_CHART_VIEWBOX

            # Rings and circles
            template_dict["transitRing"] = ""
            template_dict["degreeRing"] = draw_degree_ring(
                self.main_radius,
                self.first_circle_radius,
                self.first_obj.seventh_house.abs_pos,
                self.chart_colors_settings["paper_0"],
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
            template_dict["makeAspectGrid"] = draw_aspect_grid(
                self.chart_colors_settings["paper_0"],
                self.available_planets_setting,
                self.aspects_list,
            )
            template_dict["makeAspects"] = self._draw_all_aspects_lines(self.main_radius, self.main_radius - self.third_circle_radius)

            # Chart title
            template_dict["stringTitle"] = f"{self.first_obj.first_subject.name} {self.language_settings['and_word']} {self.first_obj.second_subject.name}" # type: ignore

            # Top left section
            # First subject
            latitude = convert_latitude_coordinate_to_string(
                self.first_obj.first_subject.lat, # type: ignore
                self.language_settings["north_letter"],
                self.language_settings["south_letter"],
            )
            longitude = convert_longitude_coordinate_to_string(
                self.first_obj.first_subject.lng, # type: ignore
                self.language_settings["east_letter"],
                self.language_settings["west_letter"],
            )

            # Second subject
            latitude_string = convert_latitude_coordinate_to_string(
                self.first_obj.second_subject.lat, # type: ignore
                self.language_settings["north_letter"],
                self.language_settings["south_letter"],
            )
            longitude_string = convert_longitude_coordinate_to_string(
                self.first_obj.second_subject.lng, # type: ignore
                self.language_settings["east_letter"],
                self.language_settings["west_letter"],
            )

            template_dict["top_left_0"] = f"{self.first_obj.first_subject.name}" # type: ignore
            template_dict["top_left_1"] = f"{datetime.fromisoformat(self.first_obj.first_subject.iso_formatted_local_datetime).strftime('%Y-%m-%d %H:%M')}" # type: ignore
            template_dict["top_left_2"] = f"{latitude} {longitude}"
            template_dict["top_left_3"] = self.first_obj.second_subject.name # type: ignore
            template_dict["top_left_4"] = f"{datetime.fromisoformat(self.first_obj.second_subject.iso_formatted_local_datetime).strftime('%Y-%m-%d %H:%M')}" # type: ignore
            template_dict["top_left_5"] = f"{latitude_string} / {longitude_string}"

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropic":
                zodiac_info = f"{self.language_settings.get('zodiac', 'Zodiac')}: {self.language_settings.get('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self.language_settings.get('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = f"{self.language_settings.get('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)} {self.language_settings.get('houses', 'Houses')}"
            template_dict["bottom_left_1"] = zodiac_info
            template_dict["bottom_left_2"] = f"{self.first_obj.first_subject.perspective_type}" # type: ignore
            template_dict["bottom_left_3"] = f'{self.language_settings.get("composite_chart", "Composite Chart")} - {self.language_settings.get("midpoints", "Midpoints")}'
            template_dict["bottom_left_4"] = ""

            # Houses and planet drawing
            template_dict["makeHousesGrid"] = draw_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self.language_settings["cusp"],
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
            )

            template_dict["makePlanets"] = draw_planets(
                available_planets_setting=self.available_planets_setting,
                chart_type=self.chart_type,
                radius=self.main_radius,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                third_circle_radius=self.third_circle_radius,
                main_subject_first_house_degree_ut=self.first_obj.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.first_obj.seventh_house.abs_pos,
            )

            subject_name = f"{self.first_obj.first_subject.name} {self.language_settings['and_word']} {self.first_obj.second_subject.name}" # type: ignore

            template_dict["makePlanetGrid"] = draw_planet_grid(
                planets_and_houses_grid_title=self.language_settings["planets_and_house"],
                subject_name=subject_name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self.language_settings["celestial_points"],
            )

        elif self.chart_type == "Transit":
            # Set viewbox
            if self.double_chart_aspect_grid_type == "table":
                template_dict["viewbox"] = self._TRANSIT_CHART_WITH_TABLE_VIWBOX
            else:
                template_dict["viewbox"] = self._WIDE_CHART_VIEWBOX

            # Get houses list for secondary subject
            second_subject_houses_list = get_houses_list(self.second_obj) # type: ignore

            # Rings and circles
            template_dict["transitRing"] = draw_transit_ring(
                self.main_radius,
                self.chart_colors_settings["paper_1"],
                self.chart_colors_settings["zodiac_transit_ring_3"],
            )
            template_dict["degreeRing"] = draw_transit_ring_degree_steps(self.main_radius, self.first_obj.seventh_house.abs_pos)
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
                title = self.language_settings.get("transit_aspects", "Transit Aspects")
                template_dict["makeAspectGrid"] = draw_transit_aspect_list(title, self.aspects_list, self.planets_settings, self.aspects_settings)
            else:
                template_dict["makeAspectGrid"] = draw_transit_aspect_grid(
                    self.chart_colors_settings["paper_0"],
                    self.available_planets_setting,
                    self.aspects_list,
                    550,
                    450,
                )

            template_dict["makeAspects"] = self._draw_all_transit_aspects_lines(self.main_radius, self.main_radius - 160)

            # Chart title
            template_dict["stringTitle"] = f"{self.language_settings['transits']} {self.second_obj.day}/{self.second_obj.month}/{self.second_obj.year}" # type: ignore

            # Top left section
            latitude_string = convert_latitude_coordinate_to_string(self.geolat, self.language_settings["north"], self.language_settings["south"])
            longitude_string = convert_longitude_coordinate_to_string(self.geolon, self.language_settings["east"], self.language_settings["west"])

            template_dict["top_left_0"] = f"{self.first_obj.name}:"
            template_dict["top_left_1"] = format_location_string(self.location)
            template_dict["top_left_2"] = format_datetime_with_timezone(self.first_obj.iso_formatted_local_datetime) # type: ignore
            template_dict["top_left_3"] = f"{self.language_settings['latitude']}: {latitude_string}"
            template_dict["top_left_4"] = f"{self.language_settings['longitude']}: {longitude_string}"
            template_dict["top_left_5"] = f"{self.language_settings['type']}: {self.language_settings.get(self.chart_type, self.chart_type)}"

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropic":
                zodiac_info = f"{self.language_settings.get('zodiac', 'Zodiac')}: {self.language_settings.get('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self.language_settings.get('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = f"{self.language_settings.get('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)} {self.language_settings.get('houses', 'Houses')}"
            template_dict["bottom_left_1"] = zodiac_info
            template_dict["bottom_left_2"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.language_settings.get("day", "Day")} {self.second_obj.lunar_phase.get("moon_phase", "")}' # type: ignore
            template_dict["bottom_left_3"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.second_obj.lunar_phase.moon_phase_name}' # type: ignore
            template_dict["bottom_left_4"] = f'{self.language_settings.get(self.second_obj.perspective_type.lower().replace(" ", "_"), self.second_obj.perspective_type)}' # type: ignore

            # Houses and planet drawing
            template_dict["makeHousesGrid"] = draw_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                secondary_subject_houses_list=second_subject_houses_list,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self.language_settings["cusp"],
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
            )

            # Planet grid
            second_subject_table_name = self.language_settings["transit_name"]
            template_dict["makePlanetGrid"] = draw_planet_grid(
                planets_and_houses_grid_title=self.language_settings["planets_and_house"],
                subject_name=self.first_obj.name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self.language_settings["celestial_points"],
                second_subject_name=second_subject_table_name,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
            )

        elif self.chart_type == "Synastry":
            # Set viewbox
            template_dict["viewbox"] = self._WIDE_CHART_VIEWBOX

            # Get houses list for secondary subject
            second_subject_houses_list = get_houses_list(self.second_obj) # type: ignore

            # Rings and circles
            template_dict["transitRing"] = draw_transit_ring(
                self.main_radius,
                self.chart_colors_settings["paper_1"],
                self.chart_colors_settings["zodiac_transit_ring_3"],
            )
            template_dict["degreeRing"] = draw_transit_ring_degree_steps(self.main_radius, self.first_obj.seventh_house.abs_pos)
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
                title = self.language_settings.get("couple_aspects", "Couple Aspects")
                template_dict["makeAspectGrid"] = draw_transit_aspect_list(title, self.aspects_list, self.planets_settings, self.aspects_settings)
            else:
                template_dict["makeAspectGrid"] = draw_transit_aspect_grid(
                    self.chart_colors_settings["paper_0"],
                    self.available_planets_setting,
                    self.aspects_list,
                    550,
                    450,
                )

            template_dict["makeAspects"] = self._draw_all_transit_aspects_lines(self.main_radius, self.main_radius - 160)

            # Chart title
            template_dict["stringTitle"] = f"{self.first_obj.name} {self.language_settings['and_word']} {self.second_obj.name}" # type: ignore

            # Top left section
            template_dict["top_left_0"] = f"{self.first_obj.name}:"
            template_dict["top_left_1"] = format_location_string(self.location)
            template_dict["top_left_2"] = format_datetime_with_timezone(self.first_obj.iso_formatted_local_datetime) # type: ignore
            template_dict["top_left_3"] = f"{self.second_obj.name}: " # type: ignore
            template_dict["top_left_4"] = self.second_obj.city # type: ignore
            template_dict["top_left_5"] = f"{self.second_obj.year}-{self.second_obj.month}-{self.second_obj.day} {self.second_obj.hour:02d}:{self.second_obj.minute:02d}" # type: ignore

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropic":
                zodiac_info = f"{self.language_settings.get('zodiac', 'Zodiac')}: {self.language_settings.get('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self.language_settings.get('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = f"{self.language_settings.get('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)} {self.language_settings.get('houses', 'Houses')}"
            template_dict["bottom_left_1"] = zodiac_info
            template_dict["bottom_left_2"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")} {self.language_settings.get("day", "Day").lower()}: {self.first_obj.lunar_phase.get("moon_phase", "")}'
            template_dict["bottom_left_3"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.language_settings.get(self.first_obj.lunar_phase.moon_phase_name.lower().replace(" ", "_"), self.first_obj.lunar_phase.moon_phase_name)}'
            template_dict["bottom_left_4"] = f'{self.language_settings.get(self.first_obj.perspective_type.lower().replace(" ", "_"), self.first_obj.perspective_type)}'

            # Houses and planet drawing
            template_dict["makeHousesGrid"] = draw_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                secondary_subject_houses_list=second_subject_houses_list,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self.language_settings["cusp"],
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
            )

            # Planet grid
            second_subject_table_name = self.second_obj.name # type: ignore
            template_dict["makePlanetGrid"] = draw_planet_grid(
                planets_and_houses_grid_title=self.language_settings["planets_and_house"],
                subject_name=self.first_obj.name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self.language_settings["celestial_points"],
                second_subject_name=second_subject_table_name,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
            )

        elif self.chart_type == "Return":
            # Set viewbox
            template_dict["viewbox"] = self._ULTRA_WIDE_CHART_VIEWBOX

            # Get houses list for secondary subject
            second_subject_houses_list = get_houses_list(self.second_obj) # type: ignore

            # Rings and circles
            template_dict["transitRing"] = draw_transit_ring(
                self.main_radius,
                self.chart_colors_settings["paper_1"],
                self.chart_colors_settings["zodiac_transit_ring_3"],
            )
            template_dict["degreeRing"] = draw_transit_ring_degree_steps(self.main_radius, self.first_obj.seventh_house.abs_pos)
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
                title = self.language_settings.get("return_aspects", "Natal to Return Aspects")
                template_dict["makeAspectGrid"] = draw_transit_aspect_list(title, self.aspects_list, self.planets_settings, self.aspects_settings, max_columns=7)
            else:
                template_dict["makeAspectGrid"] = draw_transit_aspect_grid(
                    self.chart_colors_settings["paper_0"],
                    self.available_planets_setting,
                    self.aspects_list,
                    550,
                    450,
                )

            template_dict["makeAspects"] = self._draw_all_transit_aspects_lines(self.main_radius, self.main_radius - 160)

            # Chart title
            template_dict["stringTitle"] = f"{self.first_obj.name} {self.second_obj.return_type} {self.language_settings['Return']}" # type: ignore

            # Top left section
            # Subject
            latitude_string = convert_latitude_coordinate_to_string(self.first_obj.lat, self.language_settings["north"], self.language_settings["south"]) # type: ignore
            longitude_string = convert_longitude_coordinate_to_string(self.first_obj.lng, self.language_settings["east"], self.language_settings["west"]) # type: ignore

            # Return
            return_latitude_string = convert_latitude_coordinate_to_string(self.second_obj.lat, self.language_settings["north"], self.language_settings["south"]) # type: ignore
            return_longitude_string = convert_longitude_coordinate_to_string(self.second_obj.lng, self.language_settings["east"], self.language_settings["west"]) # type: ignore

            template_dict["top_left_0"] = f"{self.language_settings['Return']}"
            template_dict["top_left_1"] = f"{return_latitude_string} / {return_longitude_string}"
            template_dict["top_left_2"] = format_datetime_with_timezone(self.second_obj.iso_formatted_local_datetime) # type: ignore
            template_dict["top_left_3"] = f"{self.first_obj.name}"
            template_dict["top_left_4"] = f"{latitude_string} / {longitude_string}"
            template_dict["top_left_5"] = format_datetime_with_timezone(self.first_obj.iso_formatted_local_datetime) # type: ignore

            # Bottom left section
            if self.first_obj.zodiac_type == "Tropic":
                zodiac_info = f"{self.language_settings.get('zodiac', 'Zodiac')}: {self.language_settings.get('tropical', 'Tropical')}"
            else:
                mode_const = "SIDM_" + self.first_obj.sidereal_mode # type: ignore
                mode_name = swe.get_ayanamsa_name(getattr(swe, mode_const))
                zodiac_info = f"{self.language_settings.get('ayanamsa', 'Ayanamsa')}: {mode_name}"

            template_dict["bottom_left_0"] = f"{self.language_settings.get('houses_system_' + self.first_obj.houses_system_identifier, self.first_obj.houses_system_name)} {self.language_settings.get('houses', 'Houses')}"
            template_dict["bottom_left_1"] = zodiac_info
            template_dict["bottom_left_2"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")} {self.language_settings.get("day", "Day").lower()}: {self.first_obj.lunar_phase.get("moon_phase", "")}'
            template_dict["bottom_left_3"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.language_settings.get(self.first_obj.lunar_phase.moon_phase_name.lower().replace(" ", "_"), self.first_obj.lunar_phase.moon_phase_name)}'
            template_dict["bottom_left_4"] = f'{self.language_settings.get(self.first_obj.perspective_type.lower().replace(" ", "_"), self.first_obj.perspective_type)}'

            # Houses and planet drawing
            template_dict["makeHousesGrid"] = draw_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                secondary_subject_houses_list=second_subject_houses_list,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self.language_settings["cusp"],
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
            )

            # Planet grid
            second_subject_table_name = self.second_obj.name # type: ignore
            template_dict["makePlanetGrid"] = draw_planet_grid(
                planets_and_houses_grid_title=self.language_settings["planets_and_house"],
                subject_name=self.first_obj.name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self.language_settings["celestial_points"],
                second_subject_name=second_subject_table_name,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
            )

        return ChartTemplateDictionary(**template_dict)

    def makeTemplate(self, minify: bool = False, remove_css_variables=False) -> str:
        """
        Render the full chart SVG as a string.

        Reads the XML template, substitutes variables, and optionally inlines CSS
        variables and minifies the output.

        Args:
            minify (bool): Remove whitespace and quotes for compactness.
            remove_css_variables (bool): Embed CSS variable definitions.

        Returns:
            str: SVG markup as a string.
        """
        td = self._create_template_dictionary()

        DATA_DIR = Path(__file__).parent
        xml_svg = DATA_DIR / "templates" / "chart.xml"

        # read template
        with open(xml_svg, "r", encoding="utf-8", errors="ignore") as f:
            template = Template(f.read()).substitute(td)

        # return filename

        logging.debug(f"Template dictionary keys: {td.keys()}")

        self._create_template_dictionary()

        if remove_css_variables:
            template = inline_css_variables_in_svg(template)

        if minify:
            template = scourString(template).replace('"', "'").replace("\n", "").replace("\t", "").replace("    ", "").replace("  ", "")

        else:
            template = template.replace('"', "'")

        return template

    def makeSVG(self, minify: bool = False, remove_css_variables=False):
        """
        Generate and save the full chart SVG to disk.

        Calls makeTemplate to render the SVG, then writes a file named
        "{subject.name} - {chart_type} Chart.svg" in the output directory.

        Args:
            minify (bool): Pass-through to makeTemplate for compact output.
            remove_css_variables (bool): Pass-through to makeTemplate to embed CSS variables.

        Returns:
            None
        """

        self.template = self.makeTemplate(minify, remove_css_variables)

        chartname = self.output_directory / f"{self.first_obj.name} - {self.chart_type} Chart.svg"

        with open(chartname, "w", encoding="utf-8", errors="ignore") as output_file:
            output_file.write(self.template)

        print(f"SVG Generated Correctly in: {chartname}")

    def makeWheelOnlyTemplate(self, minify: bool = False, remove_css_variables=False):
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
        template = Template(template).substitute(template_dict)

        if remove_css_variables:
            template = inline_css_variables_in_svg(template)

        if minify:
            template = scourString(template).replace('"', "'").replace("\n", "").replace("\t", "").replace("    ", "").replace("  ", "")

        else:
            template = template.replace('"', "'")

        return template

    def makeWheelOnlySVG(self, minify: bool = False, remove_css_variables=False):
        """
        Generate and save wheel-only chart SVG to disk.

        Calls makeWheelOnlyTemplate and writes a file named
        "{subject.name} - {chart_type} Chart - Wheel Only.svg" in the output directory.

        Args:
            minify (bool): Pass-through to makeWheelOnlyTemplate for compact output.
            remove_css_variables (bool): Pass-through to makeWheelOnlyTemplate to embed CSS variables.

        Returns:
            None
        """

        template = self.makeWheelOnlyTemplate(minify, remove_css_variables)
        chartname = self.output_directory / f"{self.first_obj.name} - {self.chart_type} Chart - Wheel Only.svg"

        with open(chartname, "w", encoding="utf-8", errors="ignore") as output_file:
            output_file.write(template)

        print(f"SVG Generated Correctly in: {chartname}")

    def makeAspectGridOnlyTemplate(self, minify: bool = False, remove_css_variables=False):
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

        if self.chart_type in ["Transit", "Synastry", "Return"]:
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

        template = Template(template).substitute({**template_dict, "makeAspectGrid": aspects_grid})

        if remove_css_variables:
            template = inline_css_variables_in_svg(template)

        if minify:
            template = scourString(template).replace('"', "'").replace("\n", "").replace("\t", "").replace("    ", "").replace("  ", "")

        else:
            template = template.replace('"', "'")

        return template

    def makeAspectGridOnlySVG(self, minify: bool = False, remove_css_variables=False):
        """
        Generate and save aspect-grid-only chart SVG to disk.

        Calls makeAspectGridOnlyTemplate and writes a file named
        "{subject.name} - {chart_type} Chart - Aspect Grid Only.svg" in the output directory.

        Args:
            minify (bool): Pass-through to makeAspectGridOnlyTemplate for compact output.
            remove_css_variables (bool): Pass-through to makeAspectGridOnlyTemplate to embed CSS variables.

        Returns:
            None
        """

        template = self.makeAspectGridOnlyTemplate(minify, remove_css_variables)
        chartname = self.output_directory / f"{self.first_obj.name} - {self.chart_type} Chart - Aspect Grid Only.svg"

        with open(chartname, "w", encoding="utf-8", errors="ignore") as output_file:
            output_file.write(template)

        print(f"SVG Generated Correctly in: {chartname}")


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    from kerykeion.planetary_return_factory import PlanetaryReturnFactory

    setup_logging(level="info")

    subject = AstrologicalSubject("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")

    return_factory = PlanetaryReturnFactory(
        subject,
        city="Los Angeles",
        nation="US",
        lng=-118.2437,
        lat=34.0522,
        tz_str="America/Los_Angeles",
        altitude=0,
    )
    solar_return = return_factory.next_return_from_iso_formatted_time(
        "2026-10-09T18:30:00+01:00",  # UTC+1
        return_type="Solar",
    )
    solar_return_chart = KerykeionChartSVG(first_obj=subject, chart_type="Return", second_obj=solar_return, chart_language="IT")

    solar_return_chart.makeSVG(minify=True, remove_css_variables=True)
