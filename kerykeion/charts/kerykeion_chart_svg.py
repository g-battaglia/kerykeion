# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""


import logging

from kerykeion.settings.kerykeion_settings import get_settings
from kerykeion.aspects.synastry_aspects import SynastryAspects
from kerykeion.aspects.natal_aspects import NatalAspects
from kerykeion.astrological_subject import AstrologicalSubject
from kerykeion.kr_types import KerykeionException, ChartType
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
    draw_second_circle
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
    points_sign: list
    points_retrograde: list
    houses_sign_graph: list
    t_points_deg_ut: list
    t_points_deg: list
    t_points_sign: list
    t_points_retrograde: list
    t_houses_sign_graph: list
    height: float
    location: str
    geolat: float
    geolon: float
    zoom: int
    zodiac: tuple
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
        available_celestial_points = []
        for body in self.available_planets_setting:
            available_celestial_points.append(body["name"].lower())
        
        # Make a list for the absolute degrees of the points of the graphic.
        self.points_deg_ut = []
        for planet in available_celestial_points:
            self.points_deg_ut.append(self.user.get(planet).abs_pos)

        # Make a list of the relative degrees of the points in the graphic.
        self.points_deg = []
        for planet in available_celestial_points:
            self.points_deg.append(self.user.get(planet).position)

        # Make list of the points sign
        self.points_sign = []
        for planet in available_celestial_points:
            self.points_sign.append(self.user.get(planet).sign_num)

        # Make a list of points if they are retrograde or not.
        self.points_retrograde = []
        for planet in available_celestial_points:
            self.points_retrograde.append(self.user.get(planet).retrograde)

        # Makes the sign number list.

        self.houses_sign_graph = []
        for h in self.user.houses_list:
            self.houses_sign_graph.append(h["sign_num"])

        if self.chart_type == "Natal" or self.chart_type == "ExternalNatal":
            natal_aspects_instance = NatalAspects(self.user, new_settings_file=self.new_settings_file)
            self.aspects_list = natal_aspects_instance.relevant_aspects

        # TODO: If not second should exit
        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            if not second_obj:
                raise KerykeionException("Second object is required for Transit or Synastry charts.")

            # Kerykeion instance
            self.t_user = second_obj

            # Make a list for the absolute degrees of the points of the graphic.
            self.t_points_deg_ut = []
            for planet in available_celestial_points:            
                self.t_points_deg_ut.append(self.t_user.get(planet).abs_pos)

            # Make a list of the relative degrees of the points in the graphic.
            self.t_points_deg = []
            for planet in available_celestial_points:
                self.t_points_deg.append(self.t_user.get(planet).position)

            # Make list of the poits sign.
            self.t_points_sign = []
            for planet in available_celestial_points:
                self.t_points_sign.append(self.t_user.get(planet).sign_num)

            # Make a list of poits if they are retrograde or not.
            self.t_points_retrograde = []
            for planet in available_celestial_points:
                self.t_points_retrograde.append(self.t_user.get(planet).retrograde)

            self.t_houses_sign_graph = []
            for h in self.t_user.houses_list:
                self.t_houses_sign_graph.append(h["sign_num"])

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

        # configuration
        # ZOOM 1 = 100%
        self.zoom = 1

        self.zodiac = (
            {"name": "aries", "element": "fire"},
            {"name": "taurus", "element": "earth"},
            {"name": "gemini", "element": "air"},
            {"name": "cancer", "element": "water"},
            {"name": "leo", "element": "fire"},
            {"name": "virgo", "element": "earth"},
            {"name": "libra", "element": "air"},
            {"name": "scorpio", "element": "water"},
            {"name": "sagittarius", "element": "fire"},
            {"name": "capricorn", "element": "earth"},
            {"name": "aquarius", "element": "air"},
            {"name": "pisces", "element": "water"},
        )

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

        output = ""
        for i, zodiac_element in enumerate(self.zodiac):
            output += draw_zodiac_slice(
                c1=self.c1,
                chart_type=self.chart_type,
                seventh_house_degree_ut=self.user.houses_degree_ut[6],
                num=i,
                r=r,
                style=f'fill:{self.chart_colors_settings[f"zodiac_bg_{i}"]}; fill-opacity: 0.5;',
                type=zodiac_element["name"],
            )

        return output

    def _makeHouses(self, r):
        path = ""

        xr = 12
        for i in range(xr):
            # check transit
            if self.chart_type == "Transit" or self.chart_type == "Synastry":
                dropin = 160
                roff = 72
                t_roff = 36
            else:
                dropin = self.c3
                roff = self.c1

            # offset is negative desc houses_degree_ut[6]
            offset = (int(self.user.houses_degree_ut[int(xr / 2)]) / -1) + int(self.user.houses_degree_ut[i])
            x1 = sliceToX(0, (r - dropin), offset) + dropin
            y1 = sliceToY(0, (r - dropin), offset) + dropin
            x2 = sliceToX(0, r - roff, offset) + roff
            y2 = sliceToY(0, r - roff, offset) + roff

            if i < (xr - 1):
                text_offset = offset + int(degreeDiff(self.user.houses_degree_ut[(i + 1)], self.user.houses_degree_ut[i]) / 2)
            else:
                text_offset = offset + int(degreeDiff(self.user.houses_degree_ut[0], self.user.houses_degree_ut[(xr - 1)]) / 2)

            # mc, asc, dsc, ic
            if i == 0:
                linecolor = self.planets_settings[12]["color"]
            elif i == 9:
                linecolor = self.planets_settings[13]["color"]
            elif i == 6:
                linecolor = self.planets_settings[14]["color"]
            elif i == 3:
                linecolor = self.planets_settings[15]["color"]
            else:
                linecolor = self.chart_colors_settings["houses_radix_line"]

            # Transit houses lines.
            if self.chart_type == "Transit" or self.chart_type == "Synastry":
                # Degrees for point zero.

                zeropoint = 360 - self.user.houses_degree_ut[6]
                t_offset = zeropoint + self.t_user.houses_degree_ut[i]
                if t_offset > 360:
                    t_offset = t_offset - 360
                t_x1 = sliceToX(0, (r - t_roff), t_offset) + t_roff
                t_y1 = sliceToY(0, (r - t_roff), t_offset) + t_roff
                t_x2 = sliceToX(0, r, t_offset)
                t_y2 = sliceToY(0, r, t_offset)
                if i < 11:
                    t_text_offset = t_offset + int(degreeDiff(self.t_user.houses_degree_ut[(i + 1)], self.t_user.houses_degree_ut[i]) / 2)
                else:
                    t_text_offset = t_offset + int(degreeDiff(self.t_user.houses_degree_ut[0], self.t_user.houses_degree_ut[11]) / 2)
                # linecolor
                if i == 0 or i == 9 or i == 6 or i == 3:
                    t_linecolor = linecolor
                else:
                    t_linecolor = self.chart_colors_settings["houses_transit_line"]
                xtext = sliceToX(0, (r - 8), t_text_offset) + 8
                ytext = sliceToY(0, (r - 8), t_text_offset) + 8

                if self.chart_type == "Transit":
                    path = path + '<text style="fill: #00f; fill-opacity: 0; font-size: 14px"><tspan x="' + str(xtext - 3) + '" y="' + str(ytext + 3) + '">' + str(i + 1) + "</tspan></text>"
                    path = f"{path}<line x1='{str(t_x1)}' y1='{str(t_y1)}' x2='{str(t_x2)}' y2='{str(t_y2)}' style='stroke: {t_linecolor}; stroke-width: 2px; stroke-opacity:0;'/>"

                else:
                    path = path + '<text style="fill: #00f; fill-opacity: .4; font-size: 14px"><tspan x="' + str(xtext - 3) + '" y="' + str(ytext + 3) + '">' + str(i + 1) + "</tspan></text>"
                    path = f"{path}<line x1='{str(t_x1)}' y1='{str(t_y1)}' x2='{str(t_x2)}' y2='{str(t_y2)}' style='stroke: {t_linecolor}; stroke-width: 2px; stroke-opacity:.3;'/>"


            # if transit
            if self.chart_type == "Transit" or self.chart_type == "Synastry":
                dropin = 84
            elif self.chart_type == "ExternalNatal":
                dropin = 100
            # Natal
            else:
                dropin = 48

            xtext = sliceToX(0, (r - dropin), text_offset) + dropin  # was 132
            ytext = sliceToY(0, (r - dropin), text_offset) + dropin  # was 132
            path = f'{path}<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {linecolor}; stroke-width: 2px; stroke-dasharray:3,2; stroke-opacity:.4;"/>'
            path = path + '<text style="fill: #f00; fill-opacity: .6; font-size: 14px"><tspan x="' + str(xtext - 3) + '" y="' + str(ytext + 3) + '">' + str(i + 1) + "</tspan></text>"

        return path

    def _calculate_elements_points_from_planets(self):
        """
        Calculate chart element points from a planet.
        """
        
        for i in range(len(self.available_planets_setting)):
            # element: get extra points if planet is in own zodiac sign.
            related_zodiac_signs = self.available_planets_setting[i]["related_zodiac_signs"]
            cz = self.points_sign[i]
            extra_points = 0
            if related_zodiac_signs != []:
                for e in range(len(related_zodiac_signs)):
                    if int(related_zodiac_signs[e]) == int(cz):
                        extra_points = self.planet_in_zodiac_extra_points

            ele = self.zodiac[self.points_sign[i]]["element"]
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
            # output planet
            output += f'<g transform="translate(-{12 * scale},-{12 * scale})"><g transform="scale({scale})"><use x="{planet_x * (1/scale)}" y="{planet_y * (1/scale)}" xlink:href="#{self.available_planets_setting[i]["name"]}" /></g></g>'

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

    def _makePatterns(self):
        """
        * Stellium: At least four planets linked together in a series of continuous conjunctions.
        * Grand trine: Three trine aspects together.
        * Grand cross: Two pairs of opposing planets squared to each other.
        * T-Square: Two planets in opposition squared to a third.
        * Yod: Two qunicunxes together joined by a sextile.
        """
        conj = {}  # 0
        opp = {}  # 10
        sq = {}  # 5
        tr = {}  # 6
        qc = {}  # 9
        sext = {}  # 3
        for i in range(len(self.available_planets_setting)):
            a = self.points_deg_ut[i]
            qc[i] = {}
            sext[i] = {}
            opp[i] = {}
            sq[i] = {}
            tr[i] = {}
            conj[i] = {}
            # skip some points
            n = self.available_planets_setting[i]["name"]
            if n == "earth" or n == "True_Node" or n == "osc. apogee" or n == "intp. apogee" or n == "intp. perigee":
                continue
            if n == "Dsc" or n == "Ic":
                continue
            for j in range(len(self.available_planets_setting)):
                # skip some points
                n = self.available_planets_setting[j]["name"]
                if n == "earth" or n == "True_Node" or n == "osc. apogee" or n == "intp. apogee" or n == "intp. perigee":
                    continue
                if n == "Dsc" or n == "Ic":
                    continue
                b = self.points_deg_ut[j]
                delta = float(degreeDiff(a, b))
                # check for opposition
                xa = float(self.aspects_settings[10]["degree"]) - float(self.aspects_settings[10]["orb"])
                xb = float(self.aspects_settings[10]["degree"]) + float(self.aspects_settings[10]["orb"])
                if xa <= delta <= xb:
                    opp[i][j] = True
                # check for conjunction
                xa = float(self.aspects_settings[0]["degree"]) - float(self.aspects_settings[0]["orb"])
                xb = float(self.aspects_settings[0]["degree"]) + float(self.aspects_settings[0]["orb"])
                if xa <= delta <= xb:
                    conj[i][j] = True
                # check for squares
                xa = float(self.aspects_settings[5]["degree"]) - float(self.aspects_settings[5]["orb"])
                xb = float(self.aspects_settings[5]["degree"]) + float(self.aspects_settings[5]["orb"])
                if xa <= delta <= xb:
                    sq[i][j] = True
                # check for qunicunxes
                xa = float(self.aspects_settings[9]["degree"]) - float(self.aspects_settings[9]["orb"])
                xb = float(self.aspects_settings[9]["degree"]) + float(self.aspects_settings[9]["orb"])
                if xa <= delta <= xb:
                    qc[i][j] = True
                # check for sextiles
                xa = float(self.aspects_settings[3]["degree"]) - float(self.aspects_settings[3]["orb"])
                xb = float(self.aspects_settings[3]["degree"]) + float(self.aspects_settings[3]["orb"])
                if xa <= delta <= xb:
                    sext[i][j] = True

        yot = {}
        # check for double qunicunxes
        for k, v in qc.items():
            if len(qc[k]) >= 2:
                # check for sextile
                for l, w in qc[k].items():
                    for m, x in qc[k].items():
                        if m in sext[l]:
                            if l > m:
                                yot["%s,%s,%s" % (k, m, l)] = [k, m, l]
                            else:
                                yot["%s,%s,%s" % (k, l, m)] = [k, l, m]
        tsquare = {}
        # check for opposition
        for k, v in opp.items():
            if len(opp[k]) >= 1:
                # check for square
                for l, w in opp[k].items():
                    for a, b in sq.items():
                        if k in sq[a] and l in sq[a]:
                            logging.debug(f"Got tsquare {a} {k} {l}")
                            if k > l:
                                tsquare[f"{a},{l},{k}"] = f"{self.available_planets_setting[a]['label']} => {self.available_planets_setting[l]['label']}, {self.available_planets_setting[k]['label']}"

                            else:
                                tsquare[f"{a},{k},{l}"] = f"{self.available_planets_setting[a]['label']} => {self.available_planets_setting[k]['label']}, {self.available_planets_setting[l]['label']}"

        stellium = {}
        # check for 4 continuous conjunctions
        for k, v in conj.items():
            if len(conj[k]) >= 1:
                # first conjunction
                for l, m in conj[k].items():
                    if len(conj[l]) >= 1:
                        for n, o in conj[l].items():
                            # skip 1st conj
                            if n == k:
                                continue
                            if len(conj[n]) >= 1:
                                # third conjunction
                                for p, q in conj[n].items():
                                    # skip first and second conj
                                    if p == k or p == n:
                                        continue
                                    if len(conj[p]) >= 1:
                                        # fourth conjunction
                                        for r, s in conj[p].items():
                                            # skip conj 1,2,3
                                            if r == k or r == n or r == p:
                                                continue

                                            l = [k, n, p, r]
                                            l.sort()
                                            stellium["%s %s %s %s" % (l[0], l[1], l[2], l[3])] = "%s %s %s %s" % (
                                                self.available_planets_setting[l[0]]["label"],
                                                self.available_planets_setting[l[1]]["label"],
                                                self.available_planets_setting[l[2]]["label"],
                                                self.available_planets_setting[l[3]]["label"],
                                            )
        # print yots
        out = '<g transform="translate(-30,380)">'
        if len(yot) >= 1:
            y = 0
            for k, v in yot.items():
                out += f'<text y="{y}" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 12px;">{"Yot"}</text>'

                # first planet symbol
                out += f'<g transform="translate(20,{y})">'
                out += f'<use transform="scale(0.4)" x="0" y="-20" xlink:href="#{self.available_planets_setting[yot[k][0]]["name"]}" /></g>'

                # second planet symbol
                out += f'<g transform="translate(30,{y})">'
                out += f'<use transform="scale(0.4)" x="0" y="-20" xlink:href="#{self.available_planets_setting[yot[k][1]]["name"]}" /></g>'

                # third planet symbol
                out += f'<g transform="translate(40,{y})">'
                out += f'<use transform="scale(0.4)" x="0" y="-20" xlink:href="#{self.available_planets_setting[yot[k][2]]["name"]}" /></g>'

                y = y + 14
        # finalize
        out += "</g>"
        # return out
        return ""

    # Aspect and aspect grid functions for natal type charts.
    def _makeAspects(self, r, ar):
        out = ""
        for element in self.aspects_list:
            out += draw_aspect_line(
                r=r,
                ar=ar,
                degA=element["p1_abs_pos"],
                degB=element["p2_abs_pos"],
                color=self.aspects_settings[element["aid"]]["color"],
                seventh_house_degree_ut=self.user.seventh_house.abs_pos
            )

        return out

    def _makeAspectGrid(self, r):
        out = ""
        style = "stroke:%s; stroke-width: 1px; stroke-opacity:.6; fill:none" % (self.chart_colors_settings["paper_0"])
        xindent = 380
        yindent = 468
        box = 14
        revr = list(range(len(self.available_planets_setting)))
        revr.reverse()
        counter = 0
        for a in revr:
            counter += 1
            out += f'<rect x="{xindent}" y="{yindent}" width="{box}" height="{box}" style="{style}"/>'
            out += f'<use transform="scale(0.4)" x="{(xindent+2)*2.5}" y="{(yindent+1)*2.5}" xlink:href="#{self.available_planets_setting[a]["name"]}" />'

            xindent = xindent + box
            yindent = yindent - box
            revr2 = list(range(a))
            revr2.reverse()
            xorb = xindent
            yorb = yindent + box
            for b in revr2:
                out += f'<rect x="{xorb}" y="{yorb}" width="{box}" height="{box}" style="{style}"/>'

                xorb = xorb + box
                for element in self.aspects_list:
                    if (element["p1"] == a and element["p2"] == b) or (element["p1"] == b and element["p2"] == a):
                        out += f'<use  x="{xorb-box+1}" y="{yorb+1}" xlink:href="#orb{element["aspect_degrees"]}" />'

        return out

    # Aspect and aspect grid functions for transit type charts
    def _makeAspectsTransit(self, r, ar):
        out = ""

        self.aspects_list = SynastryAspects(self.user, self.t_user, new_settings_file=self.new_settings_file).relevant_aspects

        for element in self.aspects_list:
            out += draw_aspect_line(
                r=r,
                ar=ar,
                degA=element["p1_abs_pos"],
                degB=element["p2_abs_pos"],
                color=self.aspects_settings[element["aid"]]["color"],
                seventh_house_degree_ut=self.user.seventh_house.abs_pos
            )

        return out

    def _makeAspectTransitGrid(self, r):
        out = '<g transform="translate(500,310)">'
        out += f'<text y="-15" x="0" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 14px;">{self.language_settings["aspects"]}:</text>'

        line = 0
        nl = 0

        for i in range(len(self.aspects_list)):
            if i == 12:
                nl = 100
                
                line = 0

            elif i == 24:
                nl = 200

                line = 0

            elif i == 36:
                nl = 300
                
                line = 0
                    
            elif i == 48:
                nl = 400

                # When there are more than 60 aspects, the text is moved up
                if len(self.aspects_list) > 60:
                    line = -1 * (len(self.aspects_list) - 60) * 14
                else:
                    line = 0

            out += f'<g transform="translate({nl},{line})">'
            
            # first planet symbol
            out += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{self.planets_settings[self.aspects_list[i]["p1"]]["name"]}" />'
            
            # aspect symbol
            out += f'<use  x="15" y="0" xlink:href="#orb{self.aspects_settings[self.aspects_list[i]["aid"]]["degree"]}" />'
            
            # second planet symbol
            out += '<g transform="translate(30,0)">'
            out += '<use transform="scale(0.4)" x="0" y="3" xlink:href="#%s" />' % (self.planets_settings[self.aspects_list[i]["p2"]]["name"]) 
            
            out += "</g>"
            # difference in degrees
            out += f'<text y="8" x="45" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{convert_decimal_to_degree_string(self.aspects_list[i]["orbit"])}</text>'
            # line
            out += "</g>"
            line = line + 14
        out += "</g>"
        return out

    def _makePlanetGrid(self):
        li = 10
        offset = 0

        out = '<g transform="translate(510,-20)">'
        out += '<g transform="translate(140, -15)">'
        out += f'<text text-anchor="end" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 14px;">{self.language_settings["planets_and_house"]} {self.user.name}:</text>'
        out += "</g>"

        end_of_line = None
        for i in range(len(self.available_planets_setting)):
            offset_between_lines = 14
            end_of_line = "</g>"

            # Guarda qui !!
            if i == 27:
                li = 10
                offset = -120

            # start of line
            out += f'<g transform="translate({offset},{li})">'

            # planet text
            out += f'<text text-anchor="end" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self.language_settings["celestial_points"][self.available_planets_setting[i]["label"]]}</text>'

            # planet symbol
            out += f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{self.available_planets_setting[i]["name"]}" /></g>'

            # planet degree
            out += f'<text text-anchor="start" x="19" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{convert_decimal_to_degree_string(self.points_deg[i])}</text>'

            # zodiac
            out += f'<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#{self.zodiac[self.points_sign[i]]["name"]}" /></g>'

            # planet retrograde
            if self.points_retrograde[i]:
                out += '<g transform="translate(74,-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'

            # end of line
            out += end_of_line

            li = li + offset_between_lines

        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            if self.chart_type == "Transit":
                out += '<g transform="translate(320, -15)">'
                out += f'<text text-anchor="end" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 14px;">{self.t_name}:</text>'
            else:
                out += '<g transform="translate(380, -15)">'
                out += f'<text text-anchor="end" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 14px;">{self.language_settings["planets_and_house"]} {self.t_user.name}:</text>'

            out += end_of_line

            t_li = 10
            t_offset = 250

            for i in range(len(self.available_planets_setting)):
                if i == 27:
                    t_li = 10
                    t_offset = -120

                # start of line
                out += f'<g transform="translate({t_offset},{t_li})">'

                # planet text
                out += f'<text text-anchor="end" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self.language_settings["celestial_points"][self.available_planets_setting[i]["label"]]}</text>'
                # planet symbol
                out += f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{self.available_planets_setting[i]["name"]}" /></g>'
                # planet degree
                out += f'<text text-anchor="start" x="19" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{convert_decimal_to_degree_string(self.t_points_deg[i])}</text>'
                # zodiac
                out += f'<g transform="translate(60,-8)"><use transform="scale(0.3)" xlink:href="#{self.zodiac[self.t_points_sign[i]]["name"]}" /></g>'

                # planet retrograde
                if self.t_points_retrograde[i]:
                    out += '<g transform="translate(74,-6)"><use transform="scale(.5)" xlink:href="#retrograde" /></g>'

                # end of line
                out += end_of_line

                t_li = t_li + offset_between_lines

        if end_of_line is None:
            raise KerykeionException("End of line not found")

        out += end_of_line
        return out

    def _draw_house_grid(self):
        """
        Generate SVG code for a grid of astrological houses.

        Returns:
            str: The SVG code for the grid of houses.
        """
        out = '<g transform="translate(610,-20)">'

        li = 10
        for i in range(12):
            if i < 9:
                cusp = "&#160;&#160;" + str(i + 1)
            else:
                cusp = str(i + 1)
            out += f'<g transform="translate(0,{li})">'
            out += f'<text text-anchor="end" x="40" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self.language_settings["cusp"]} {cusp}:</text>'
            out += f'<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#{self.zodiac[self.houses_sign_graph[i]]["name"]}" /></g>'
            out += f'<text x="53" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;"> {convert_decimal_to_degree_string(self.user.houses_list[i]["position"])}</text>'
            out += "</g>"
            li = li + 14

        out += "</g>"

        if self.chart_type == "Synastry":
            out += '<!-- Synastry Houses -->'
            out += '<g transform="translate(850, -20)">'
            li = 10

            for i in range(12):
                if i < 9:
                    cusp = "&#160;&#160;" + str(i + 1)
                else:
                    cusp = str(i + 1)
                out += '<g transform="translate(0,' + str(li) + ')">'
                out += f'<text text-anchor="end" x="40" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self.language_settings["cusp"]} {cusp}:</text>'
                out += f'<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#{self.zodiac[self.t_houses_sign_graph[i]]["name"]}" /></g>'
                out += f'<text x="53" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;"> {convert_decimal_to_degree_string(self.t_user.houses_list[i]["position"])}</text>'
                out += "</g>"
                li = li + 14
            out += "</g>"

        return out

    def _createTemplateDictionary(self) -> ChartTemplateDictionary:
        # self.chart_type = "Transit"
        # empty element points
        self.fire = 0.0
        self.earth = 0.0
        self.air = 0.0
        self.water = 0.0

        # Calculate the elements points
        self._calculate_elements_points_from_planets()

        # Viewbox and sizing
        svgHeight = "100%"
        svgWidth = "100%"
        rotate = "0"
        
        # To increase the size of the chart, change the viewbox
        if self.chart_type == "Natal" or self.chart_type == "ExternalNatal":
            viewbox = self.chart_settings["basic_chart_viewBox"]
        else:
            viewbox = self.chart_settings["wide_chart_viewBox"]

        # template dictionary
        td: ChartTemplateDictionary = dict() # type: ignore
        r = 240

        if self.chart_type == "ExternalNatal":
            self.c1 = 56
            self.c2 = 92
            self.c3 = 112
        else:
            self.c1 = 0
            self.c2 = 36
            self.c3 = 120

        # transit
        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            td["transitRing"] = draw_transit_ring(r, self.chart_colors_settings["paper_1"], self.chart_colors_settings["zodiac_transit_ring_3"])
            td["degreeRing"] = draw_transit_ring_degree_steps(r, self.user.seventh_house.abs_pos)

            # circles
            td["first_circle"] = draw_first_circle(r, self.chart_colors_settings["zodiac_transit_ring_2"], self.chart_type)
            td["second_circle"] = draw_second_circle(r, self.chart_colors_settings['zodiac_transit_ring_1'], self.chart_colors_settings['paper_1'], self.chart_type)

            td["c3"] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r - 160) + '"'
            td["c3style"] = f"fill: {self.chart_colors_settings['paper_1']}; fill-opacity:.8; stroke: {self.chart_colors_settings['zodiac_transit_ring_0']}; stroke-width: 1px"

            td["makeAspects"] = self._makeAspectsTransit(r, (r - 160))
            td["makeAspectGrid"] = self._makeAspectTransitGrid(r)
            td["makePatterns"] = ""
        else:
            td["transitRing"] = ""
            td["degreeRing"] = draw_degree_ring(r, self.c1, self.user.seventh_house.abs_pos, self.chart_colors_settings["paper_0"])

            td['first_circle'] = draw_first_circle(r, self.chart_colors_settings["zodiac_radix_ring_2"], self.chart_type, self.c1)

            td["second_circle"] = draw_second_circle(r, self.chart_colors_settings["zodiac_radix_ring_1"], self.chart_colors_settings["paper_1"], self.chart_type, self.c2)
            
            td["c3"] = f'cx="{r}" cy="{r}" r="{r - self.c3}"'
            td["c3style"] = f'fill: {self.chart_colors_settings["paper_1"]}; fill-opacity:.8; stroke: {self.chart_colors_settings["zodiac_radix_ring_0"]}; stroke-width: 1px'
            
            td["makeAspects"] = self._makeAspects(r, (r - self.c3))
            td["makeAspectGrid"] = self._makeAspectGrid(r)
            td["makePatterns"] = self._makePatterns()
        
        td["chart_height"] = self.height
        td["chart_width"] = self.width
        td["circleX"] = str(0)
        td["circleY"] = str(0)
        td["svgWidth"] = str(svgWidth)
        td["svgHeight"] = str(svgHeight)
        td["viewbox"] = viewbox

        # Chart Title
        if self.chart_type == "Synastry":
            td["stringTitle"] = f"{self.user.name} {self.language_settings['and_word']} {self.t_user.name}"

        elif self.chart_type == "Transit":
            td["stringTitle"] = f"{self.language_settings['transits']} {self.t_user.day}/{self.t_user.month}/{self.t_user.year}"

        else:
            td["stringTitle"] = self.user.name

        # Chart Name
        if self.chart_type == "Synastry" or self.chart_type == "Transit":
            td["stringName"] = f"{self.user.name}:"
        else:
            td["stringName"] = f'{self.language_settings["info"]}:'

        # Bottom Left Corner
        if self.chart_type == "Natal" or self.chart_type == "ExternalNatal" or self.chart_type == "Synastry":
            td["bottomLeft0"] = f"{self.user.zodiac_type if self.user.zodiac_type == 'Tropic' else self.user.zodiac_type + ' ' + self.user.sidereal_mode}"
            td["bottomLeft1"] = f"{self.user.houses_system_name}"
            td["bottomLeft2"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.language_settings.get("day", "Day")} {self.user.lunar_phase.get("moon_phase", "")}'
            td["bottomLeft3"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.user.lunar_phase.moon_phase_name}'
            td["bottomLeft4"] = f'{self.user.perspective_type}'

        else:
            td["bottomLeft0"] = f"{self.user.zodiac_type if self.user.zodiac_type == 'Tropic' else self.user.zodiac_type + ' ' + self.user.sidereal_mode}"
            td["bottomLeft1"] = f"{self.user.houses_system_name}"
            td["bottomLeft2"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.language_settings.get("day", "Day")} {self.t_user.lunar_phase.get("moon_phase", "")}'
            td["bottomLeft3"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.t_user.lunar_phase.moon_phase_name}'
            td["bottomLeft4"] = f'{self.t_user.perspective_type}'

        # lunar phase
        deg = self.user.lunar_phase["degrees_between_s_m"]

        lffg = None
        lfbg = None
        lfcx = None
        lfr = None

        if deg < 90.0:
            maxr = deg
            if deg > 80.0:
                maxr = maxr * maxr
            lfcx = 20.0 + (deg / 90.0) * (maxr + 10.0)
            lfr = 10.0 + (deg / 90.0) * maxr
            lffg = self.chart_colors_settings["lunar_phase_0"]
            lfbg = self.chart_colors_settings["lunar_phase_1"]

        elif deg < 180.0:
            maxr = 180.0 - deg
            if deg < 100.0:
                maxr = maxr * maxr
            lfcx = 20.0 + ((deg - 90.0) / 90.0 * (maxr + 10.0)) - (maxr + 10.0)
            lfr = 10.0 + maxr - ((deg - 90.0) / 90.0 * maxr)
            lffg = self.chart_colors_settings["lunar_phase_1"]
            lfbg = self.chart_colors_settings["lunar_phase_0"]

        elif deg < 270.0:
            maxr = deg - 180.0
            if deg > 260.0:
                maxr = maxr * maxr
            lfcx = 20.0 + ((deg - 180.0) / 90.0 * (maxr + 10.0))
            lfr = 10.0 + ((deg - 180.0) / 90.0 * maxr)
            lffg, lfbg = self.chart_colors_settings["lunar_phase_1"], self.chart_colors_settings["lunar_phase_0"]

        elif deg < 361:
            maxr = 360.0 - deg
            if deg < 280.0:
                maxr = maxr * maxr
            lfcx = 20.0 + ((deg - 270.0) / 90.0 * (maxr + 10.0)) - (maxr + 10.0)
            lfr = 10.0 + maxr - ((deg - 270.0) / 90.0 * maxr)
            lffg, lfbg = self.chart_colors_settings["lunar_phase_0"], self.chart_colors_settings["lunar_phase_1"]

        if lffg is None or lfbg is None or lfcx is None or lfr is None:
            raise KerykeionException("Lunar phase error")

        td["lunar_phase_fg"] = lffg
        td["lunar_phase_bg"] = lfbg
        td["lunar_phase_cx"] = lfcx
        td["lunar_phase_r"] = lfr
        td["lunar_phase_outline"] = self.chart_colors_settings["lunar_phase_2"]

        # rotation based on latitude
        td["lunar_phase_rotate"] = -90.0 - self.geolat

        # stringlocation
        if len(self.location) > 35:
            split = self.location.split(",")
            if len(split) > 1:
                td["stringLocation"] = split[0] + ", " + split[-1]
                if len(td["stringLocation"]) > 35:
                    td["stringLocation"] = td["stringLocation"][:35] + "..."
            else:
                td["stringLocation"] = self.location[:35] + "..."
        else:
            td["stringLocation"] = self.location

        if self.chart_type == "Synastry":
            td["stringLat"] = f"{self.t_user.name}: "
            td["stringLon"] = self.t_user.city
            td["stringPosition"] = f"{self.t_user.year}-{self.t_user.month}-{self.t_user.day} {self.t_user.hour:02d}:{self.t_user.minute:02d}"

        else:
            latitude_string = convert_latitude_coordinate_to_string(
                self.geolat, 
                self.language_settings['north'], 
                self.language_settings['south']
            )
            longitude_string = convert_longitude_coordinate_to_string(
                self.geolon, 
                self.language_settings['east'], 
                self.language_settings['west']
            )

            td["stringLat"] = f"{self.language_settings['latitude']}: {latitude_string}"
            td["stringLon"] = f"{self.language_settings['longitude']}: {longitude_string}"
            td["stringPosition"] = f"{self.language_settings['type']}: {self.chart_type}"

        # paper_color_X
        td["paper_color_0"] = self.chart_colors_settings["paper_0"]
        td["paper_color_1"] = self.chart_colors_settings["paper_1"]

        # planets_color_X
        for i in range(len(self.planets_settings)):
            planet_id = self.planets_settings[i]["id"]
            td[f"planets_color_{planet_id}"] = self.planets_settings[i]["color"]

        # zodiac_color_X
        for i in range(12):
            td[f"zodiac_color_{i}"] = self.chart_colors_settings[f"zodiac_icon_{i}"]

        # orb_color_X
        for i in range(len(self.aspects_settings)):
            td[f"orb_color_{self.aspects_settings[i]['degree']}"] = self.aspects_settings[i]['color']

        # config
        td["cfgZoom"] = str(self.zoom)
        td["cfgRotate"] = rotate

        # ---
        # Drawing Functions
        #--- 

        td["makeZodiac"] = self._draw_zodiac_circle_slices(r)
        td["makeHousesGrid"] = self._draw_house_grid()
        # TODO: Add the rest of the functions
        td["makeHouses"] = self._makeHouses(r)
        td["makePlanets"] = self._make_planets(r)
        td["elements_percentages"] = draw_elements_percentages(
            self.language_settings['fire'],
            self.fire,
            self.language_settings['earth'],
            self.earth,
            self.language_settings['air'],
            self.air,
            self.language_settings['water'],
            self.water,
        )
        td["makePlanetGrid"] = self._makePlanetGrid()

        # Date time String
        dt = datetime.fromisoformat(self.user.iso_formatted_local_datetime)
        custom_format = dt.strftime('%Y-%-m-%-d %H:%M [%z]')  # Note the use of '-' to remove leading zeros
        custom_format = custom_format[:-3] + ':' + custom_format[-3:]
        td["stringDateTime"] = f"{custom_format}"

        return td

    def makeTemplate(self, minify: bool = False) -> str:
        """Creates the template for the SVG file"""
        td = self._createTemplateDictionary()

        # read template
        with open(self.xml_svg, "r", encoding="utf-8", errors="ignore") as f:
            template = Template(f.read()).substitute(td)

        # return filename

        logging.debug(f"Template dictionary keys: {td.keys()}")

        self._createTemplateDictionary()

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