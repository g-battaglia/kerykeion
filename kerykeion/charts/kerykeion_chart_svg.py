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
from kerykeion.kr_types.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.charts.charts_utils import (
    degreeDiff, 
    sliceToX, 
    sliceToY, 
    draw_zodiac_slice, 
    convert_latitude_coordinate_to_string, 
    convert_longitude_coordinate_to_string,
    draw_aspect_line,
    draw_elements_percentages,
    convert_decimal_to_degree_string,
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
    draw_planet_grid
)
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
    first_obj: AstrologicalSubject
    second_obj: Union[AstrologicalSubject, None]
    chart_type: ChartType
    new_output_directory: Union[Path, None]
    new_settings_file: Union[Path, None]
    output_directory: Path

    # Internal properties
    fire: float
    earth: float
    air: float
    water: float
    c1: float
    c2: float
    c3: float
    homedir: Path
    xml_svg: Path
    width: Union[float, int]
    language_settings: dict
    chart_colors_settings: dict
    planets_settings: dict
    aspects_settings: dict
    planet_in_zodiac_extra_points: int
    chart_settings: dict
    user: AstrologicalSubject
    available_planets_setting: List[KerykeionSettingsCelestialPointModel]
    transit_ring_exclude_points_names: List[str]
    points_deg_ut: list
    points_deg: list
    points_retrograde: list
    t_points_deg_ut: list
    t_points_deg: list
    t_points_retrograde: list
    height: float
    location: str
    geolat: float
    geolon: float
    template: str

    def __init__(
        self,
        first_obj: AstrologicalSubject,
        chart_type: ChartType = "Natal",
        second_obj: Union[AstrologicalSubject, None] = None,
        new_output_directory: Union[str, None] = None,
        new_settings_file: Union[Path, None] = None,
    ):
        # Directories:
        DATA_DIR = Path(__file__).parent
        self.homedir = Path.home()
        self.new_settings_file = new_settings_file

        if new_output_directory:
            self.output_directory = Path(new_output_directory)
        else:
            self.output_directory = self.homedir

        self.xml_svg = DATA_DIR / "templates/chart.xml"

        self.parse_json_settings(new_settings_file)
        self.chart_type = chart_type

        # Kerykeion instance
        self.user = first_obj

        self.available_planets_setting = []
        for body in self.planets_settings:
            if body['is_active'] == False:
                continue

            self.available_planets_setting.append(body)

        # House cusp points are excluded from the transit ring.
        self.transit_ring_exclude_points_names = [
            "First_House",
            "Second_House",
            "Third_House",
            "Fourth_House",
            "Fifth_House",
            "Sixth_House",
            "Seventh_House",
            "Eighth_House",
            "Ninth_House",
            "Tenth_House",
            "Eleventh_House",
            "Twelfth_House"
        ]

        # Available bodies
        available_celestial_points_names = []
        for body in self.available_planets_setting:
            available_celestial_points_names.append(body["name"].lower())

        self.available_kerykeion_celestial_points = []
        for body in available_celestial_points_names:
            self.available_kerykeion_celestial_points.append(self.user.get(body))

        # Make a list for the absolute degrees of the points of the graphic.
        self.points_deg_ut = []
        for planet in available_celestial_points_names:
            self.points_deg_ut.append(self.user.get(planet).abs_pos)

        # Make a list of the relative degrees of the points in the graphic.
        self.points_deg = []
        for planet in available_celestial_points_names:
            self.points_deg.append(self.user.get(planet).position)

        # Makes the sign number list.
        if self.chart_type == "Natal" or self.chart_type == "ExternalNatal":
            natal_aspects_instance = NatalAspects(self.user, new_settings_file=self.new_settings_file)
            self.aspects_list = natal_aspects_instance.relevant_aspects

        # TODO: If not second should exit
        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            if not second_obj:
                raise KerykeionException("Second object is required for Transit or Synastry charts.")

            # Kerykeion instance
            self.t_user = second_obj

            self.t_available_kerykeion_celestial_points = []
            for body in available_celestial_points_names:
                self.t_available_kerykeion_celestial_points.append(self.t_user.get(body))

            # Make a list for the absolute degrees of the points of the graphic.
            self.t_points_deg_ut = []
            for planet in available_celestial_points_names:
                self.t_points_deg_ut.append(self.t_user.get(planet).abs_pos)

            # Make a list of the relative degrees of the points in the graphic.
            self.t_points_deg = []
            for planet in available_celestial_points_names:
                self.t_points_deg.append(self.t_user.get(planet).position)

            # Make a list of poits if they are retrograde or not.
            self.t_points_retrograde = []
            for planet in available_celestial_points_names:
                self.t_points_retrograde.append(self.t_user.get(planet).retrograde)

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
        
        logging.info(f"{self.user.name} birth location: {self.location}, {self.geolat}, {self.geolon}")

        if self.chart_type == "Transit":
            self.t_name = self.language_settings["transit_name"]

        self.template = None

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
                c1=self.c1,
                chart_type=self.chart_type,
                seventh_house_degree_ut=self.user.houses_degree_ut[6],
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

    def _make_planets(self, r):
        planets_degut = {}
        diff = range(len(self.available_planets_setting))

        for i in range(len(self.available_planets_setting)):
            # list of planets sorted by degree
            logging.debug(f"planet: {i}, degree: {self.points_deg_ut[i]}")
            planets_degut[self.points_deg_ut[i]] = i

        """
        FIXME: The planets_degut is a dictionary like:
        {planet_degree: planet_index}
        It should be replaced bu points_deg_ut
        print(self.points_deg_ut)
        print(planets_degut)
        """

        output = ""
        keys = list(planets_degut.keys())
        keys.sort()
        switch = 0

        planets_degrouped = {}
        groups = []
        planets_by_pos = list(range(len(planets_degut)))
        planet_drange = 3.4
        # get groups closely together
        group_open = False
        for e in range(len(keys)):
            i = planets_degut[keys[e]]
            # get distances between planets
            if e == 0:
                prev = self.points_deg_ut[planets_degut[keys[-1]]]
                next = self.points_deg_ut[planets_degut[keys[1]]]
            elif e == (len(keys) - 1):
                prev = self.points_deg_ut[planets_degut[keys[e - 1]]]
                next = self.points_deg_ut[planets_degut[keys[0]]]
            else:
                prev = self.points_deg_ut[planets_degut[keys[e - 1]]]
                next = self.points_deg_ut[planets_degut[keys[e + 1]]]
            diffa = degreeDiff(prev, self.points_deg_ut[i])
            diffb = degreeDiff(next, self.points_deg_ut[i])
            planets_by_pos[e] = [i, diffa, diffb]

            logging.debug(f'{self.available_planets_setting[i]["label"]}, {diffa}, {diffb}')

            if diffb < planet_drange:
                if group_open:
                    groups[-1].append([e, diffa, diffb, self.available_planets_setting[planets_degut[keys[e]]]["label"]])
                else:
                    group_open = True
                    groups.append([])
                    groups[-1].append([e, diffa, diffb, self.available_planets_setting[planets_degut[keys[e]]]["label"]])
            else:
                if group_open:
                    groups[-1].append([e, diffa, diffb, self.available_planets_setting[planets_degut[keys[e]]]["label"]])
                group_open = False

        def zero(x):
            return 0

        planets_delta = list(map(zero, range(len(self.available_planets_setting))))

        # print groups
        # print planets_by_pos
        for a in range(len(groups)):
            # Two grouped planets
            if len(groups[a]) == 2:
                next_to_a = groups[a][0][0] - 1
                if groups[a][1][0] == (len(planets_by_pos) - 1):
                    next_to_b = 0
                else:
                    next_to_b = groups[a][1][0] + 1
                # if both planets have room
                if (groups[a][0][1] > (2 * planet_drange)) & (groups[a][1][2] > (2 * planet_drange)):
                    planets_delta[groups[a][0][0]] = -(planet_drange - groups[a][0][2]) / 2
                    planets_delta[groups[a][1][0]] = +(planet_drange - groups[a][0][2]) / 2
                # if planet a has room
                elif groups[a][0][1] > (2 * planet_drange):
                    planets_delta[groups[a][0][0]] = -planet_drange
                # if planet b has room
                elif groups[a][1][2] > (2 * planet_drange):
                    planets_delta[groups[a][1][0]] = +planet_drange

                # if planets next to a and b have room move them
                elif (planets_by_pos[next_to_a][1] > (2.4 * planet_drange)) & (planets_by_pos[next_to_b][2] > (2.4 * planet_drange)):
                    planets_delta[(next_to_a)] = groups[a][0][1] - planet_drange * 2
                    planets_delta[groups[a][0][0]] = -planet_drange * 0.5
                    planets_delta[next_to_b] = -(groups[a][1][2] - planet_drange * 2)
                    planets_delta[groups[a][1][0]] = +planet_drange * 0.5

                # if planet next to a has room move them
                elif planets_by_pos[next_to_a][1] > (2 * planet_drange):
                    planets_delta[(next_to_a)] = groups[a][0][1] - planet_drange * 2.5
                    planets_delta[groups[a][0][0]] = -planet_drange * 1.2

                # if planet next to b has room move them
                elif planets_by_pos[next_to_b][2] > (2 * planet_drange):
                    planets_delta[next_to_b] = -(groups[a][1][2] - planet_drange * 2.5)
                    planets_delta[groups[a][1][0]] = +planet_drange * 1.2

            # Three grouped planets or more
            xl = len(groups[a])
            if xl >= 3:
                available = groups[a][0][1]
                for f in range(xl):
                    available += groups[a][f][2]
                need = (3 * planet_drange) + (1.2 * (xl - 1) * planet_drange)
                leftover = available - need
                xa = groups[a][0][1]
                xb = groups[a][(xl - 1)][2]

                # center
                if (xa > (need * 0.5)) & (xb > (need * 0.5)):
                    startA = xa - (need * 0.5)
                # position relative to next planets
                else:
                    startA = (leftover / (xa + xb)) * xa
                    startB = (leftover / (xa + xb)) * xb

                if available > need:
                    planets_delta[groups[a][0][0]] = startA - groups[a][0][1] + (1.5 * planet_drange)
                    for f in range(xl - 1):
                        planets_delta[groups[a][(f + 1)][0]] = 1.2 * planet_drange + planets_delta[groups[a][f][0]] - groups[a][f][2]

        for e in range(len(keys)):
            i = planets_degut[keys[e]]

            # coordinates
            if self.chart_type == "Transit" or self.chart_type == "Synastry":
                if 22 < i < 27:
                    rplanet = 76
                elif switch == 1:
                    rplanet = 110
                    switch = 0
                else:
                    rplanet = 130
                    switch = 1
            else:
                # if 22 < i < 27 it is asc,mc,dsc,ic (angles of chart)
                # put on special line (rplanet is range from outer ring)
                amin, bmin, cmin = 0, 0, 0
                if self.chart_type == "ExternalNatal":
                    amin = 74 - 10
                    bmin = 94 - 10
                    cmin = 40 - 10

                if 22 < i < 27:
                    rplanet = 40 - cmin
                elif switch == 1:
                    rplanet = 74 - amin
                    switch = 0
                else:
                    rplanet = 94 - bmin
                    switch = 1

            rtext = 45

            offset = (int(self.user.houses_degree_ut[6]) / -1) + int(self.points_deg_ut[i] + planets_delta[e])
            trueoffset = (int(self.user.houses_degree_ut[6]) / -1) + int(self.points_deg_ut[i])

            planet_x = sliceToX(0, (r - rplanet), offset) + rplanet
            planet_y = sliceToY(0, (r - rplanet), offset) + rplanet
            if self.chart_type == "Transit" or self.chart_type == "Synastry":
                scale = 0.8
                
            elif self.chart_type == "ExternalNatal":
                scale = 0.8
                # line1
                x1 = sliceToX(0, (r - self.c3), trueoffset) + self.c3
                y1 = sliceToY(0, (r - self.c3), trueoffset) + self.c3
                x2 = sliceToX(0, (r - rplanet - 30), trueoffset) + rplanet + 30
                y2 = sliceToY(0, (r - rplanet - 30), trueoffset) + rplanet + 30
                color = self.available_planets_setting[i]["color"]
                output += (
                    '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke-width:1px;stroke:%s;stroke-opacity:.3;"/>\n'
                    % (x1, y1, x2, y2, color)
                )
                # line2
                x1 = sliceToX(0, (r - rplanet - 30), trueoffset) + rplanet + 30
                y1 = sliceToY(0, (r - rplanet - 30), trueoffset) + rplanet + 30
                x2 = sliceToX(0, (r - rplanet - 10), offset) + rplanet + 10
                y2 = sliceToY(0, (r - rplanet - 10), offset) + rplanet + 10
                output += (
                    '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke-width:1px;stroke:%s;stroke-opacity:.5;"/>\n'
                    % (x1, y1, x2, y2, color)
                )
                
            else:
                scale = 1

            planet_details = self.user[self.available_planets_setting[i]["name"].lower()]

            output += f'<g kr:node="ChartPoint" kr:house="{planet_details["house"]}" kr:sign="{planet_details["sign"]}" kr:slug="{planet_details["name"]}" transform="translate(-{12 * scale},-{12 * scale}) scale({scale})">'
            output += f'<use x="{planet_x * (1/scale)}" y="{planet_y * (1/scale)}" xlink:href="#{self.available_planets_setting[i]["name"]}" />'
            output += f'</g>'

        # make transit degut and display planets
        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            group_offset = {}
            t_planets_degut = {}
            list_range = len(self.available_planets_setting)

            for i in range(list_range):
                if self.chart_type == "Transit" and self.available_planets_setting[i]['name'] in self.transit_ring_exclude_points_names:
                    continue
                
                group_offset[i] = 0
                t_planets_degut[self.t_points_deg_ut[i]] = i
        
            t_keys = list(t_planets_degut.keys())
            t_keys.sort()

            # grab closely grouped planets
            groups = []
            in_group = False
            for e in range(len(t_keys)):
                i_a = t_planets_degut[t_keys[e]]
                if e == (len(t_keys) - 1):
                    i_b = t_planets_degut[t_keys[0]]
                else:
                    i_b = t_planets_degut[t_keys[e + 1]]

                a = self.t_points_deg_ut[i_a]
                b = self.t_points_deg_ut[i_b]
                diff = degreeDiff(a, b)
                if diff <= 2.5:
                    if in_group:
                        groups[-1].append(i_b)
                    else:
                        groups.append([i_a])
                        groups[-1].append(i_b)
                        in_group = True
                else:
                    in_group = False
            # loop groups and set degrees display adjustment
            for i in range(len(groups)):
                if len(groups[i]) == 2:
                    group_offset[groups[i][0]] = -1.0
                    group_offset[groups[i][1]] = 1.0
                elif len(groups[i]) == 3:
                    group_offset[groups[i][0]] = -1.5
                    group_offset[groups[i][1]] = 0
                    group_offset[groups[i][2]] = 1.5
                elif len(groups[i]) == 4:
                    group_offset[groups[i][0]] = -2.0
                    group_offset[groups[i][1]] = -1.0
                    group_offset[groups[i][2]] = 1.0
                    group_offset[groups[i][3]] = 2.0

            switch = 0
            
            # Transit planets loop
            for e in range(len(t_keys)):
                if self.chart_type == "Transit" and self.available_planets_setting[e]["name"] in self.transit_ring_exclude_points_names:
                    continue

                i = t_planets_degut[t_keys[e]]

                if 22 < i < 27:
                    rplanet = 9
                elif switch == 1:
                    rplanet = 18
                    switch = 0
                else:
                    rplanet = 26
                    switch = 1

                # Transit planet name
                zeropoint = 360 - self.user.houses_degree_ut[6]
                t_offset = zeropoint + self.t_points_deg_ut[i]
                if t_offset > 360:
                    t_offset = t_offset - 360
                planet_x = sliceToX(0, (r - rplanet), t_offset) + rplanet
                planet_y = sliceToY(0, (r - rplanet), t_offset) + rplanet
                output += f'<g class="transit-planet-name" transform="translate(-6,-6)"><g transform="scale(0.5)"><use x="{planet_x*2}" y="{planet_y*2}" xlink:href="#{self.available_planets_setting[i]["name"]}" /></g></g>'

                # Transit planet line
                x1 = sliceToX(0, r + 3, t_offset) - 3
                y1 = sliceToY(0, r + 3, t_offset) - 3
                x2 = sliceToX(0, r - 3, t_offset) + 3
                y2 = sliceToY(0, r - 3, t_offset) + 3
                output += f'<line class="transit-planet-line" x1="{str(x1)}" y1="{str(y1)}" x2="{str(x2)}" y2="{str(y2)}" style="stroke: {self.available_planets_setting[i]["color"]}; stroke-width: 1px; stroke-opacity:.8;"/>'

                # transit planet degree text
                rotate = self.user.houses_degree_ut[0] - self.t_points_deg_ut[i]
                textanchor = "end"
                t_offset += group_offset[i]
                rtext = -3.0

                if -90 > rotate > -270:
                    rotate = rotate + 180.0
                    textanchor = "start"
                if 270 > rotate > 90:
                    rotate = rotate - 180.0
                    textanchor = "start"

                if textanchor == "end":
                    xo = 1
                else:
                    xo = -1
                deg_x = sliceToX(0, (r - rtext), t_offset + xo) + rtext
                deg_y = sliceToY(0, (r - rtext), t_offset + xo) + rtext
                degree = int(t_offset)
                output += f'<g transform="translate({deg_x},{deg_y})">'
                output += f'<text transform="rotate({rotate})" text-anchor="{textanchor}'
                output += f'" style="fill: {self.available_planets_setting[i]["color"]}; font-size: 10px;">{convert_decimal_to_degree_string(self.t_points_deg[i], type="1")}'
                output += "</text></g>"

            # check transit
            if self.chart_type == "Transit" or self.chart_type == "Synastry":
                dropin = 36
            else:
                dropin = 0

            # planet line
            x1 = sliceToX(0, r - (dropin + 3), offset) + (dropin + 3)
            y1 = sliceToY(0, r - (dropin + 3), offset) + (dropin + 3)
            x2 = sliceToX(0, (r - (dropin - 3)), offset) + (dropin - 3)
            y2 = sliceToY(0, (r - (dropin - 3)), offset) + (dropin - 3)

            output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {self.available_planets_setting[i]["color"]}; stroke-width: 2px; stroke-opacity:.6;"/>'

            # check transit
            if self.chart_type == "Transit" or self.chart_type == "Synastry":
                dropin = 160
            else:
                dropin = 120

            x1 = sliceToX(0, r - dropin, offset) + dropin
            y1 = sliceToY(0, r - dropin, offset) + dropin
            x2 = sliceToX(0, (r - (dropin - 3)), offset) + (dropin - 3)
            y2 = sliceToY(0, (r - (dropin - 3)), offset) + (dropin - 3)
            output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {self.available_planets_setting[i]["color"]}; stroke-width: 2px; stroke-opacity:.6;"/>'

        return output

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

        self.aspects_list = SynastryAspects(self.user, self.t_user, new_settings_file=self.new_settings_file).relevant_aspects

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
        # Initialize element points
        self.fire = 0.0
        self.earth = 0.0
        self.air = 0.0
        self.water = 0.0

        # Calculate element points from planets
        self._calculate_elements_points_from_planets()

        # Default rotation
        rotation = "0"

        # Initialize template dictionary
        template_dict: ChartTemplateDictionary = dict()  # type: ignore
        radius = 240

        # Set viewbox based on chart type
        template_dict['viewbox'] = self.chart_settings["basic_chart_viewBox"] if self.chart_type in ["Natal", "ExternalNatal"] else self.chart_settings["wide_chart_viewBox"]

        # Set circle radii based on chart type
        if self.chart_type == "ExternalNatal":
            self.c1, self.c2, self.c3 = 56, 92, 112
        else:
            self.c1, self.c2, self.c3 = 0, 36, 120

        # Generate rings and circles based on chart type
        if self.chart_type in ["Transit", "Synastry"]:
            template_dict["transitRing"] = draw_transit_ring(radius, self.chart_colors_settings["paper_1"], self.chart_colors_settings["zodiac_transit_ring_3"])
            template_dict["degreeRing"] = draw_transit_ring_degree_steps(radius, self.user.seventh_house.abs_pos)
            template_dict["first_circle"] = draw_first_circle(radius, self.chart_colors_settings["zodiac_transit_ring_2"], self.chart_type)
            template_dict["second_circle"] = draw_second_circle(radius, self.chart_colors_settings['zodiac_transit_ring_1'], self.chart_colors_settings['paper_1'], self.chart_type)
            template_dict['third_circle'] = draw_third_circle(radius, self.chart_colors_settings['zodiac_transit_ring_0'], self.chart_colors_settings['paper_1'], self.chart_type)
            template_dict["makeAspects"] = self._draw_all_transit_aspects_lines(radius, radius - 160)
            template_dict["makeAspectGrid"] = draw_aspect_transit_grid(self.language_settings["aspects"], self.aspects_list, self.planets_settings, self.aspects_settings)
        else:
            template_dict["transitRing"] = ""
            template_dict["degreeRing"] = draw_degree_ring(radius, self.c1, self.user.seventh_house.abs_pos, self.chart_colors_settings["paper_0"])
            template_dict['first_circle'] = draw_first_circle(radius, self.chart_colors_settings["zodiac_radix_ring_2"], self.chart_type, self.c1)
            template_dict["second_circle"] = draw_second_circle(radius, self.chart_colors_settings["zodiac_radix_ring_1"], self.chart_colors_settings["paper_1"], self.chart_type, self.c2)
            template_dict['third_circle'] = draw_third_circle(radius, self.chart_colors_settings["zodiac_radix_ring_0"], self.chart_colors_settings["paper_1"], self.chart_type, self.c3)
            template_dict["makeAspects"] = self._draw_all_aspects_lines(radius, radius - self.c3)
            template_dict["makeAspectGrid"] = draw_aspect_grid(self.chart_colors_settings['paper_0'], self.available_planets_setting, self.aspects_list)

        # Set chart dimensions
        template_dict["chart_height"] = self.height
        template_dict["chart_width"] = self.width

        # Set chart title
        if self.chart_type == "Synastry":
            template_dict["stringTitle"] = f"{self.user.name} {self.language_settings['and_word']} {self.t_user.name}"
        elif self.chart_type == "Transit":
            template_dict["stringTitle"] = f"{self.language_settings['transits']} {self.t_user.day}/{self.t_user.month}/{self.t_user.year}"
        else:
            template_dict["stringTitle"] = self.user.name

        # Set chart name
        template_dict["stringName"] = f"{self.user.name}:" if self.chart_type in ["Synastry", "Transit"] else f'{self.language_settings["info"]}:'

        # Set bottom left corner information
        template_dict["bottomLeft0"] = f"{self.user.zodiac_type if self.user.zodiac_type == 'Tropic' else self.user.zodiac_type + ' ' + self.user.sidereal_mode}"
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
        template_dict['moon_phase'] = draw_moon_phase(self.user.lunar_phase["degrees_between_s_m"], self.geolat)

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
            template_dict[f"planets_color_{planet_id}"] = planet["color"]

        # Set zodiac colors
        for i in range(12):
            template_dict[f"zodiac_color_{i}"] = self.chart_colors_settings[f"zodiac_icon_{i}"]

        # Set orb colors
        for aspect in self.aspects_settings:
            template_dict[f"orb_color_{aspect['degree']}"] = aspect['color']

        # Set configuration rotation
        template_dict["cfgRotate"] = rotation

        # Drawing functions
        template_dict["makeZodiac"] = self._draw_zodiac_circle_slices(radius)

        # Draw houses grid and cusps
        if self.chart_type in ["Transit", "Synastry"]:
            template_dict["makeHousesGrid"] = draw_house_grid(
                main_subject_houses_list=self.user.houses_list,
                secondary_subject_houses_list=self.t_user.houses_list,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self.language_settings["cusp"]
            )

            template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
                r=radius,
                first_subject_houses_list_ut=self.user.houses_degree_ut,
                standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
                first_house_color=self.planets_settings[12]["color"],
                tenth_house_color=self.planets_settings[13]["color"],
                seventh_house_color=self.planets_settings[14]["color"],
                fourth_house_color=self.planets_settings[15]["color"],
                c1=self.c1,
                c3=self.c3,
                chart_type=self.chart_type,
                second_subject_houses_list_ut=self.t_user.houses_degree_ut,
                transit_house_cusp_color=self.chart_colors_settings["houses_transit_line"],
            )

        else:
            template_dict["makeHousesGrid"] = draw_house_grid(
                main_subject_houses_list=self.user.houses_list,
                chart_type=self.chart_type,
                text_color=self.chart_colors_settings["paper_0"],
                house_cusp_generale_name_label=self.language_settings["cusp"]
            )

            template_dict["makeHouses"] = draw_houses_cusps_and_text_number(
                r=radius,
                first_subject_houses_list_ut=self.user.houses_degree_ut,
                standard_house_cusp_color=self.chart_colors_settings["houses_radix_line"],
                first_house_color=self.planets_settings[12]["color"],
                tenth_house_color=self.planets_settings[13]["color"],
                seventh_house_color=self.planets_settings[14]["color"],
                fourth_house_color=self.planets_settings[15]["color"],
                c1=self.c1,
                c3=self.c3,
                chart_type=self.chart_type,
            )

        # Draw planets
        template_dict["makePlanets"] = self._make_planets(radius)

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

        # read template
        with open(self.xml_svg, "r", encoding="utf-8", errors="ignore") as f:
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

        if not (self.template):
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


