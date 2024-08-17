# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""


import logging
from typing import get_args

from kerykeion.settings.kerykeion_settings import get_settings
from kerykeion.aspects.synastry_aspects import SynastryAspects
from kerykeion.aspects.natal_aspects import NatalAspects
from kerykeion.astrological_subject import AstrologicalSubject
from kerykeion.kr_types import KerykeionException, ChartType, KerykeionPointModel, Sign
from kerykeion.kr_types import ChartTemplateDictionary
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel
from kerykeion.kr_types.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.charts.charts_utils import (
    draw_zodiac_slice, 
    convert_latitude_coordinate_to_string, 
    convert_longitude_coordinate_to_string,
    draw_aspect_line,
    draw_elements_percentages,
    draw_transit_ring_degree_steps,
    draw_degree_ring,
    draw_transit_ring,
    draw_first_circle,
    draw_second_circle,
    draw_third_circle,
    draw_aspect_grid,
    draw_houses_cusps_and_text_number,
    draw_aspect_transit_grid,
    draw_moon_phase,
    draw_house_grid,
    draw_planet_grid,
)
from kerykeion.charts.draw_planets import draw_planets # type: ignore
from kerykeion.utilities import get_houses_list
from kerykeion.charts.color_style_tags import DEFAULT_COLOR_STYLE_TAG
from pathlib import Path
from scour.scour import scourString
from string import Template
from typing import Union, List
from datetime import datetime



class KerykeionChartSVG:
    """
    Creates the instance that can generate the chart with the
    function makeSVG().

    Parameters:
        - first_obj: First kerykeion object
        - chart_type: Natal, ExternalNatal, Transit, Synastry (Default: Type="Natal").
        - second_obj: Second kerykeion object (Not required if type is Natal)
        - new_output_directory: Set the output directory (default: home directory).
        - new_settings_file: Set the settings file (default: kr.config.json).
            In the settings file you can set the language, colors, planets, aspects, etc.
    """
    
    # Constants
    _DEFAULT_HEIGHT = 546.0
    _DEFAULT_FULL_WIDTH = 1200
    _DEFAULT_NATAL_WIDTH = 772.2

    # Set at init
    first_obj: Union[AstrologicalSubject, AstrologicalSubjectModel]
    second_obj: Union[AstrologicalSubject, AstrologicalSubjectModel, None]
    chart_type: ChartType
    new_output_directory: Union[Path, None]
    new_settings_file: Union[Path, None]
    output_directory: Path

    # Internal properties
    fire: float
    earth: float
    air: float
    water: float
    main_radius: float
    first_circle_radius: float
    second_circle_radius: float
    third_circle_radius: float
    homedir: Path
    width: Union[float, int]
    language_settings: dict
    chart_colors_settings: dict
    planets_settings: dict
    aspects_settings: dict
    planet_in_zodiac_extra_points: int
    chart_settings: dict
    user: Union[AstrologicalSubject, AstrologicalSubjectModel]
    available_planets_setting: List[KerykeionSettingsCelestialPointModel]
    height: float
    location: str
    geolat: float
    geolon: float
    template: str

    def __init__(
        self,
        first_obj: Union[AstrologicalSubject, AstrologicalSubjectModel],
        chart_type: ChartType = "Natal",
        second_obj: Union[AstrologicalSubject, AstrologicalSubjectModel, None] = None,
        new_output_directory: Union[str, None] = None,
        new_settings_file: Union[Path, None] = None,
        color_style_tag: str = DEFAULT_COLOR_STYLE_TAG
    ):
        # Directories:
        self.homedir = Path.home()
        self.new_settings_file = new_settings_file

        if new_output_directory:
            self.output_directory = Path(new_output_directory)
        else:
            self.output_directory = self.homedir

        self.parse_json_settings(new_settings_file)
        self.chart_type = chart_type

        # Kerykeion instance
        self.user = first_obj

        self.available_planets_setting = []
        for body in self.planets_settings:
            if body['is_active'] == False:
                continue

            self.available_planets_setting.append(body)

        # Available bodies
        available_celestial_points_names = []
        for body in self.available_planets_setting:
            available_celestial_points_names.append(body["name"].lower())

        self.available_kerykeion_celestial_points: list[KerykeionPointModel] = []
        for body in available_celestial_points_names:
            self.available_kerykeion_celestial_points.append(self.user.get(body))

        # Makes the sign number list.
        if self.chart_type == "Natal" or self.chart_type == "ExternalNatal":
            natal_aspects_instance = NatalAspects(self.user, new_settings_file=self.new_settings_file)
            self.aspects_list = natal_aspects_instance.relevant_aspects

        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            if not second_obj:
                raise KerykeionException("Second object is required for Transit or Synastry charts.")

            # Kerykeion instance
            self.t_user = second_obj

            # Aspects
            self.aspects_list = SynastryAspects(self.user, self.t_user, new_settings_file=self.new_settings_file).relevant_aspects

            self.t_available_kerykeion_celestial_points = []
            for body in available_celestial_points_names:
                self.t_available_kerykeion_celestial_points.append(self.t_user.get(body))

        # screen size
        self.height = self._DEFAULT_HEIGHT
        if self.chart_type == "Synastry" or self.chart_type == "Transit":
            self.width = self._DEFAULT_FULL_WIDTH
        else:
            self.width = self._DEFAULT_NATAL_WIDTH

        # default location
        self.location = self.user.city
        self.geolat = self.user.lat
        self.geolon =  self.user.lng
        
        if self.chart_type == "Transit":
            self.t_name = self.language_settings["transit_name"]

        # Default radius for the chart
        self.main_radius = 240

        # Set circle radii based on chart type
        if self.chart_type == "ExternalNatal":
            self.first_circle_radius, self.second_circle_radius, self.third_circle_radius = 56, 92, 112
        else:
            self.first_circle_radius, self.second_circle_radius, self.third_circle_radius = 0, 36, 120

        # Initialize element points
        self.fire = 0.0
        self.earth = 0.0
        self.air = 0.0
        self.water = 0.0

        # Color style tag
        self.color_style_tag = color_style_tag

        # Calculate element points from planets
        self._calculate_elements_points_from_planets()

    def set_output_directory(self, dir_path: Path) -> None:
        """
        Sets the output direcotry and returns it's path.
        """
        self.output_directory = dir_path
        logging.info(f"Output direcotry set to: {self.output_directory}")

    def parse_json_settings(self, settings_file):
        """
        Parse the settings file.
        """
        settings = get_settings(settings_file)

        language = settings["general_settings"]["language"]
        self.language_settings = settings["language_settings"].get(language, "EN")
        self.chart_colors_settings = settings["chart_colors"]
        self.planets_settings = settings["celestial_points"]
        self.aspects_settings = settings["aspects"]
        self.planet_in_zodiac_extra_points = settings["general_settings"]["planet_in_zodiac_extra_points"]
        self.chart_settings = settings["chart_settings"]

    def _draw_zodiac_circle_slices(self, r):
        """
        Generate the SVG string representing the zodiac circle
        with the 12 slices for each zodiac sign.

        Args:
            r (float): The radius of the zodiac slices.

        Returns:
            str: The SVG string representing the zodiac circle.
        """
        sings = get_args(Sign)
        output = ""
        for i, sing in enumerate(sings):
            output += draw_zodiac_slice(
                c1=self.first_circle_radius,
                chart_type=self.chart_type,
                seventh_house_degree_ut=self.user.seventh_house.abs_pos,
                num=i,
                r=r,
                style=f'fill:{self.chart_colors_settings[f"zodiac_bg_{i}"]}; fill-opacity: 0.5;',
                type=sing,
            )

        return output

    def _calculate_elements_points_from_planets(self):
        """
        Calculate chart element points from a planet.
        TODO: Refactor this method.
        Should be completely rewritten. Maybe even part of the AstrologicalSubject class.
        The points should include just the standard way of calculating the elements points.
        """

        zodiac = (
            {"name": "Ari", "element": "fire"},
            {"name": "Tau", "element": "earth"},
            {"name": "Gem", "element": "air"},
            {"name": "Can", "element": "water"},
            {"name": "Leo", "element": "fire"},
            {"name": "Vir", "element": "earth"},
            {"name": "Lib", "element": "air"},
            {"name": "Sco", "element": "water"},
            {"name": "Sag", "element": "fire"},
            {"name": "Cap", "element": "earth"},
            {"name": "Aqu", "element": "air"},
            {"name": "Pis", "element": "water"},
        )
        
        # Available bodies
        available_celestial_points_names = []
        for body in self.available_planets_setting:
            available_celestial_points_names.append(body["name"].lower())

        # Make list of the points sign
        points_sign = []
        for planet in available_celestial_points_names:
            points_sign.append(self.user.get(planet).sign_num)

        for i in range(len(self.available_planets_setting)):
            # element: get extra points if planet is in own zodiac sign.
            related_zodiac_signs = self.available_planets_setting[i]["related_zodiac_signs"]
            cz = points_sign[i]
            extra_points = 0
            if related_zodiac_signs != []:
                for e in range(len(related_zodiac_signs)):
                    if int(related_zodiac_signs[e]) == int(cz):
                        extra_points = self.planet_in_zodiac_extra_points

            ele = zodiac[points_sign[i]]["element"]
            if ele == "fire":
                self.fire = self.fire + self.available_planets_setting[i]["element_points"] + extra_points

            elif ele == "earth":
                self.earth = self.earth + self.available_planets_setting[i]["element_points"] + extra_points

            elif ele == "air":
                self.air = self.air + self.available_planets_setting[i]["element_points"] + extra_points

            elif ele == "water":
                self.water = self.water + self.available_planets_setting[i]["element_points"] + extra_points

    def _draw_all_aspects_lines(self, r, ar):
        out = ""
        for aspect in self.aspects_list:
            out += draw_aspect_line(
                r=r,
                ar=ar,
                aspect=aspect,
                color=self.aspects_settings[aspect["aid"]]["color"],
                seventh_house_degree_ut=self.user.seventh_house.abs_pos
            )

        return out

    def _draw_all_transit_aspects_lines(self, r, ar):
        out = ""
        for aspect in self.aspects_list:
            out += draw_aspect_line(
                r=r,
                ar=ar,
                aspect=aspect,
                color=self.aspects_settings[aspect["aid"]]["color"],
                seventh_house_degree_ut=self.user.seventh_house.abs_pos
            )
        return out

    def _create_template_dictionary(self) -> ChartTemplateDictionary:
        """
        Create a dictionary containing the template data for generating an astrological chart.

        Returns:
            ChartTemplateDictionary: A dictionary with template data for the chart.
        """
        # Initialize template dictionary
        template_dict: ChartTemplateDictionary = dict()  # type: ignore

        # Set the color style tag
        template_dict["color_style_tag"] = self.color_style_tag

        # Set chart dimensions
        template_dict["chart_height"] = self.height
        template_dict["chart_width"] = self.width

        # Set chart name
        template_dict["stringName"] = f"{self.user.name}:" if self.chart_type in ["Synastry", "Transit"] else f'{self.language_settings["info"]}:'

        # Set viewbox based on chart type
        template_dict['viewbox'] = self.chart_settings["basic_chart_viewBox"] if self.chart_type in ["Natal", "ExternalNatal"] else self.chart_settings["wide_chart_viewBox"]

        # Generate rings and circles based on chart type
        if self.chart_type in ["Transit", "Synastry"]:
            template_dict["transitRing"] = draw_transit_ring(self.main_radius, self.chart_colors_settings["paper_1"], self.chart_colors_settings["zodiac_transit_ring_3"])
            template_dict["degreeRing"] = draw_transit_ring_degree_steps(self.main_radius, self.user.seventh_house.abs_pos)
            template_dict["first_circle"] = draw_first_circle(self.main_radius, self.chart_colors_settings["zodiac_transit_ring_2"], self.chart_type)
            template_dict["second_circle"] = draw_second_circle(self.main_radius, self.chart_colors_settings['zodiac_transit_ring_1'], self.chart_colors_settings['paper_1'], self.chart_type)
            template_dict['third_circle'] = draw_third_circle(self.main_radius, self.chart_colors_settings['zodiac_transit_ring_0'], self.chart_colors_settings['paper_1'], self.chart_type, self.third_circle_radius)
            template_dict["makeAspectGrid"] = draw_aspect_transit_grid(self.language_settings["aspects"], self.aspects_list, self.planets_settings, self.aspects_settings)

            template_dict["makeAspects"] = self._draw_all_transit_aspects_lines(self.main_radius, self.main_radius - 160)
        else:
            template_dict["transitRing"] = ""
            template_dict["degreeRing"] = draw_degree_ring(self.main_radius, self.first_circle_radius, self.user.seventh_house.abs_pos, self.chart_colors_settings["paper_0"])
            template_dict['first_circle'] = draw_first_circle(self.main_radius, self.chart_colors_settings["zodiac_radix_ring_2"], self.chart_type, self.first_circle_radius)
            template_dict["second_circle"] = draw_second_circle(self.main_radius, self.chart_colors_settings["zodiac_radix_ring_1"], self.chart_colors_settings["paper_1"], self.chart_type, self.second_circle_radius)
            template_dict['third_circle'] = draw_third_circle(self.main_radius, self.chart_colors_settings["zodiac_radix_ring_0"], self.chart_colors_settings["paper_1"], self.chart_type, self.third_circle_radius)
            template_dict["makeAspectGrid"] = draw_aspect_grid(self.chart_colors_settings['paper_0'], self.available_planets_setting, self.aspects_list)

            template_dict["makeAspects"] = self._draw_all_aspects_lines(self.main_radius, self.main_radius - self.third_circle_radius)

        # Set chart title
        if self.chart_type == "Synastry":
            template_dict["stringTitle"] = f"{self.user.name} {self.language_settings['and_word']} {self.t_user.name}"
        elif self.chart_type == "Transit":
            template_dict["stringTitle"] = f"{self.language_settings['transits']} {self.t_user.day}/{self.t_user.month}/{self.t_user.year}"
        else:
            template_dict["stringTitle"] = self.user.name

        # Set bottom left corner information
        template_dict["bottomLeft0"] = f"{self.user.zodiac_type if self.user.zodiac_type == 'Tropic' else str(self.user.zodiac_type) + ' ' + str(self.user.sidereal_mode)}"
        template_dict["bottomLeft1"] = f"{self.user.houses_system_name}"
        if self.chart_type in ["Natal", "ExternalNatal", "Synastry"]:
            template_dict["bottomLeft2"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.language_settings.get("day", "Day")} {self.user.lunar_phase.get("moon_phase", "")}'
            template_dict["bottomLeft3"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.user.lunar_phase.moon_phase_name}'
            template_dict["bottomLeft4"] = f'{self.user.perspective_type}'
        else:
            template_dict["bottomLeft2"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.language_settings.get("day", "Day")} {self.t_user.lunar_phase.get("moon_phase", "")}'
            template_dict["bottomLeft3"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.t_user.lunar_phase.moon_phase_name}'
            template_dict["bottomLeft4"] = f'{self.t_user.perspective_type}'

        # Draw moon phase
        template_dict['moon_phase'] = draw_moon_phase(
            self.user.lunar_phase["degrees_between_s_m"], 
            self.geolat
        )

        # Set location string
        if len(self.location) > 35:
            split_location = self.location.split(",")
            if len(split_location) > 1:
                template_dict["stringLocation"] = split_location[0] + ", " + split_location[-1]
                if len(template_dict["stringLocation"]) > 35:
                    template_dict["stringLocation"] = template_dict["stringLocation"][:35] + "..."
            else:
                template_dict["stringLocation"] = self.location[:35] + "..."
        else:
            template_dict["stringLocation"] = self.location

        # Set additional information for Synastry chart type
        if self.chart_type == "Synastry":
            template_dict["stringLat"] = f"{self.t_user.name}: "
            template_dict["stringLon"] = self.t_user.city
            template_dict["stringPosition"] = f"{self.t_user.year}-{self.t_user.month}-{self.t_user.day} {self.t_user.hour:02d}:{self.t_user.minute:02d}"
        else:
            latitude_string = convert_latitude_coordinate_to_string(self.geolat, self.language_settings['north'], self.language_settings['south'])
            longitude_string = convert_longitude_coordinate_to_string(self.geolon, self.language_settings['east'], self.language_settings['west'])
            template_dict["stringLat"] = f"{self.language_settings['latitude']}: {latitude_string}"
            template_dict["stringLon"] = f"{self.language_settings['longitude']}: {longitude_string}"
            template_dict["stringPosition"] = f"{self.language_settings['type']}: {self.chart_type}"

        # Set paper colors
        template_dict["paper_color_0"] = self.chart_colors_settings["paper_0"]
        template_dict["paper_color_1"] = self.chart_colors_settings["paper_1"]

        # Set planet colors
        for planet in self.planets_settings:
            planet_id = planet["id"]
            template_dict[f"planets_color_{planet_id}"] = planet["color"] # type: ignore

        # Set zodiac colors
        for i in range(12):
            template_dict[f"zodiac_color_{i}"] = self.chart_colors_settings[f"zodiac_icon_{i}"] # type: ignore

        # Set orb colors
        for aspect in self.aspects_settings:
            template_dict[f"orb_color_{aspect['degree']}"] = aspect['color'] # type: ignore

        # Drawing functions
        template_dict["makeZodiac"] = self._draw_zodiac_circle_slices(self.main_radius)

        first_subject_houses_list = get_houses_list(self.user)

        # Draw houses grid and cusps
        if self.chart_type in ["Transit", "Synastry"]:
            second_subject_houses_list = get_houses_list(self.t_user)

            template_dict["makeHousesGrid"] = draw_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                secondary_subject_houses_list=second_subject_houses_list,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self.language_settings["cusp"]
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

        else:
            template_dict["makeHousesGrid"] = draw_house_grid(
                main_subject_houses_list=first_subject_houses_list,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self.language_settings["cusp"]
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

        # Draw planets
        if self.chart_type in ["Transit", "Synastry"]:
            template_dict["makePlanets"] = draw_planets(
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points, 
                available_planets_setting=self.available_planets_setting,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
                radius=self.main_radius, 
                main_subject_first_house_degree_ut=self.user.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.user.seventh_house.abs_pos,
                chart_type=self.chart_type, 
                third_circle_radius=self.third_circle_radius,
            )
        else:
            template_dict["makePlanets"] = draw_planets(
                available_planets_setting=self.available_planets_setting,
                chart_type=self.chart_type,
                radius=self.main_radius, 
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                third_circle_radius=self.third_circle_radius,
                main_subject_first_house_degree_ut=self.user.first_house.abs_pos,
                main_subject_seventh_house_degree_ut=self.user.seventh_house.abs_pos
            )

        # Draw elements percentages
        template_dict["elements_percentages"] = draw_elements_percentages(
            self.language_settings['fire'],
            self.fire,
            self.language_settings['earth'],
            self.earth,
            self.language_settings['air'],
            self.air,
            self.language_settings['water'],
            self.water,
        )

        # Draw planet grid
        if self.chart_type in ["Transit", "Synastry"]:
            if self.chart_type == "Transit":
                second_subject_table_name = self.language_settings["transit_name"]
            else:
                second_subject_table_name = self.t_user.name
            template_dict["makePlanetGrid"] = draw_planet_grid(
                planets_and_houses_grid_title=self.language_settings["planets_and_house"],
                subject_name=self.user.name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self.language_settings["celestial_points"],
                second_subject_name=second_subject_table_name,
                second_subject_available_kerykeion_celestial_points=self.t_available_kerykeion_celestial_points,
            )
        else:
            template_dict["makePlanetGrid"] = draw_planet_grid(
                planets_and_houses_grid_title=self.language_settings["planets_and_house"],
                subject_name=self.user.name,
                available_kerykeion_celestial_points=self.available_kerykeion_celestial_points,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                celestial_point_language=self.language_settings["celestial_points"],
            )

        # Set date time string
        dt = datetime.fromisoformat(self.user.iso_formatted_local_datetime)
        custom_format = dt.strftime('%Y-%-m-%-d %H:%M [%z]')  # Note the use of '-' to remove leading zeros
        custom_format = custom_format[:-3] + ':' + custom_format[-3:]
        template_dict["stringDateTime"] = f"{custom_format}"

        return template_dict

    def makeTemplate(self, minify: bool = False) -> str:
        """Creates the template for the SVG file"""
        td = self._create_template_dictionary()

        DATA_DIR = Path(__file__).parent
        xml_svg = DATA_DIR / "templates/chart.xml"
        
        # read template
        with open(xml_svg, "r", encoding="utf-8", errors="ignore") as f:
            template = Template(f.read()).substitute(td)

        # return filename

        logging.debug(f"Template dictionary keys: {td.keys()}")

        self._create_template_dictionary()

        if minify:
            template = scourString(template).replace('"', "'").replace("\n", "").replace("\t","").replace("    ", "").replace("  ", "")

        else:
            template = template.replace('"', "'")

        return template

    def makeSVG(self, minify: bool = False):
        """Prints out the SVG file in the specifide folder"""

        if not hasattr(self, "template"):
            self.template = self.makeTemplate(minify)

        self.chartname = self.output_directory / f"{self.user.name} - {self.chart_type} Chart.svg"

        with open(self.chartname, "w", encoding="utf-8", errors="ignore") as output_file:
            output_file.write(self.template)

        logging.info(f"SVG Generated Correctly in: {self.chartname}")


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    setup_logging(level="debug")

    first = AstrologicalSubject("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
    second = AstrologicalSubject("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

    # Internal Natal Chart
    internal_natal_chart = KerykeionChartSVG(first)
    internal_natal_chart.makeSVG()

    # External Natal Chart
    external_natal_chart = KerykeionChartSVG(first, "ExternalNatal", second)
    external_natal_chart.makeSVG()

    # Synastry Chart
    synastry_chart = KerykeionChartSVG(first, "Synastry", second)
    synastry_chart.makeSVG()

    # Transits Chart
    transits_chart = KerykeionChartSVG(first, "Transit", second)
    transits_chart.makeSVG()
    
    # Sidereal Birth Chart (Lahiri)
    sidereal_subject = AstrologicalSubject("John Lennon Lahiri", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
    sidereal_chart = KerykeionChartSVG(sidereal_subject)
    sidereal_chart.makeSVG()

    # Sidereal Birth Chart (Fagan-Bradley)
    sidereal_subject = AstrologicalSubject("John Lennon Fagan-Bradley", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY")
    sidereal_chart = KerykeionChartSVG(sidereal_subject)
    sidereal_chart.makeSVG()

    # Sidereal Birth Chart (DeLuce)
    sidereal_subject = AstrologicalSubject("John Lennon DeLuce", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="DELUCE")
    sidereal_chart = KerykeionChartSVG(sidereal_subject)
    sidereal_chart.makeSVG()

    # Sidereal Birth Chart (J2000)
    sidereal_subject = AstrologicalSubject("John Lennon J2000", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="J2000")
    sidereal_chart = KerykeionChartSVG(sidereal_subject)
    sidereal_chart.makeSVG()

    # House System Morinus
    morinus_house_subject = AstrologicalSubject("John Lennon - House System Morinus", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system_identifier="M")
    morinus_house_chart = KerykeionChartSVG(morinus_house_subject)
    morinus_house_chart.makeSVG()

    ## To check all the available house systems uncomment the following code:
    # from kerykeion.kr_types import HousesSystemIdentifier
    # from typing import get_args
    # for i in get_args(HousesSystemIdentifier):
    #     alternatives_house_subject = AstrologicalSubject(f"John Lennon - House System {i}", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system=i)
    #     alternatives_house_chart = KerykeionChartSVG(alternatives_house_subject)
    #     alternatives_house_chart.makeSVG()

    # With True Geocentric Perspective
    true_geocentric_subject = AstrologicalSubject("John Lennon - True Geocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", perspective_type="True Geocentric")
    true_geocentric_chart = KerykeionChartSVG(true_geocentric_subject)
    true_geocentric_chart.makeSVG()

    # With Heliocentric Perspective
    heliocentric_subject = AstrologicalSubject("John Lennon - Heliocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", perspective_type="Heliocentric")
    heliocentric_chart = KerykeionChartSVG(heliocentric_subject)
    heliocentric_chart.makeSVG()

    # With Topocentric Perspective
    topocentric_subject = AstrologicalSubject("John Lennon - Topocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", perspective_type="Topocentric")
    topocentric_chart = KerykeionChartSVG(topocentric_subject)
    topocentric_chart.makeSVG()


