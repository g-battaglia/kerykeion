# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2023 Giacomo Battaglia
"""


import pytz

from datetime import datetime
from kerykeion.settings.kerykeion_settings import get_settings_dict
from kerykeion.aspects.synastry_aspects import SynastryAspects
from kerykeion.aspects.natal_aspects import NatalAspects
from kerykeion.astrological_subject import AstrologicalSubject
from kerykeion.kr_types import KerykeionException, ChartType
from kerykeion.kr_types.chart_types import ChartTemplateModel
from kerykeion.charts.charts_utils import decHourJoin, degreeDiff, offsetToTz, sliceToX, sliceToY
from logging import getLogger, basicConfig
from pathlib import Path
from string import Template
from typing import Union


logger = getLogger(__name__)
basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level="INFO"
)


class KerykeionChartSVG:
    """
    Creates the instance that can generate the chart with the
    function makeSVG().

    Parameters:
        - first_obj: First kerykeion object
        - chart_type: Natal, ExternalNatal, Transit, Synastry (Default: Type="Natal").
        - second_obj: Second kerykeion object (Not required if type is Natal)
        - new_output_directory: Set the output directory (default: output_directory)
        - lang: language settings (default: "EN")
        - new_settings_file: Set the settings file (default: kr.config.json)
    """

    first_obj: AstrologicalSubject
    second_obj: Union[AstrologicalSubject, None]
    chart_type: ChartType
    new_output_directory: Union[Path, None]
    new_settings_file: Union[Path, None]
    output_directory: Path

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

        # SVG Width
        self.natal_width = 772.2
        self.full_width = 1200

        self.parse_json_settings(new_settings_file)
        self.chart_type = chart_type

        # Kerykeion instance
        self.user = first_obj

        # Make a list for the absolute degrees of the points of the graphic.
        self.points_deg_ut = self.user.planets_degrees_ut + [
            self.user.houses_degree_ut[0],
            self.user.houses_degree_ut[9],
            self.user.houses_degree_ut[6],
            self.user.houses_degree_ut[3],
        ]

        # Make a list of the relative degrees of the points in the graphic.
        self.points_deg = []
        for planet in self.user.planets_list:
            self.points_deg.append(planet["position"])

        self.points_deg = self.points_deg + [
            self.user.houses_list[0]["position"],
            self.user.houses_list[9]["position"],
            self.user.houses_list[6]["position"],
            self.user.houses_list[3]["position"],
        ]

        # Make list of the points sign
        self.points_sign = []

        for planet in self.user.planets_list:
            self.points_sign.append(planet["sign_num"])

        self.points_sign = self.points_sign + [
            self.user.houses_list[0]["sign_num"],
            self.user.houses_list[9]["sign_num"],
            self.user.houses_list[6]["sign_num"],
            self.user.houses_list[3]["sign_num"],
        ]

        # Make a list of points if they are retrograde or not.
        self.points_retrograde = []

        for planet in self.user.planets_list:
            self.points_retrograde.append(planet["retrograde"])

        self.points_retrograde = self.points_retrograde + [False, False, False, False]

        # Makes the sign number list.

        self.houses_sign_graph = []
        for h in self.user.houses_list:
            self.houses_sign_graph.append(h["sign_num"])

        if self.chart_type == "Natal" or self.chart_type == "ExternalNatal":
            natal_aspects_instance = NatalAspects(self.user, new_settings_file=self.new_settings_file)
            self.aspects_list = natal_aspects_instance.get_relevant_aspects()

        # TODO: If not second should exit
        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            if not second_obj:
                raise KerykeionException("Second object is required for Transit or Synastry charts.")

            # Kerykeion instance
            self.t_user = second_obj

            # Make a list for the absolute degrees of the points of the graphic.

            self.t_points_deg_ut = self.t_user.planets_degrees_ut + [
                self.t_user.houses_degree_ut[0],
                self.t_user.houses_degree_ut[9],
                self.t_user.houses_degree_ut[6],
                self.t_user.houses_degree_ut[3],
            ]

            # Make a list of the relative degrees of the points in the graphic.

            self.t_points_deg = []
            for planet in self.t_user.planets_list:
                self.t_points_deg.append(planet["position"])

            self.t_points_deg = self.t_points_deg + [
                self.t_user.houses_list[0]["position"],
                self.t_user.houses_list[9]["position"],
                self.t_user.houses_list[6]["position"],
                self.t_user.houses_list[3]["position"],
            ]

            # Make list of the poits sign.

            self.t_points_sign = []

            for planet in self.t_user.planets_list:
                self.t_points_sign.append(planet["sign_num"])

            self.t_points_sign = self.t_points_sign + [
                self.t_user.houses_list[0]["sign_num"],
                self.t_user.houses_list[9]["sign_num"],
                self.t_user.houses_list[6]["sign_num"],
                self.t_user.houses_list[3]["sign_num"],
            ]

            # Make a list of poits if they are retrograde or not.

            self.t_points_retrograde = []

            for planet in self.t_user.planets_list:
                self.t_points_retrograde.append(planet["retrograde"])

            self.t_points_retrograde = self.t_points_retrograde + [False, False, False, False]

            self.t_houses_sign_graph = []
            for h in self.t_user.houses_list:
                self.t_houses_sign_graph.append(h["sign_num"])

        # screen size
        if self.chart_type == "Natal":
            self.screen_width = 772.2
        else:
            self.screen_width = 1200
        self.screen_height = 772.2

        # check for home
        self.home_location = self.user.city
        self.home_geolat = self.user.lat
        self.home_geolon = self.user.lng
        self.home_countrycode = self.user.nation
        self.home_timezonestr = self.user.tz_str

        print(f"{self.user.name} birth location: {self.home_location}, {self.home_geolat}, {self.home_geolon}")

        # default location
        self.location = self.home_location
        self.geolat = float(self.home_geolat)
        self.geolon = float(self.home_geolon)
        self.countrycode = self.home_countrycode
        self.timezonestr = self.home_timezonestr

        # current datetime
        now = datetime.now()

        # aware datetime object
        dt_input = datetime(now.year, now.month, now.day, now.hour, now.minute, now.second)
        dt = pytz.timezone(self.timezonestr).localize(dt_input)

        # naive utc datetime object
        dt_utc = dt.replace(tzinfo=None) - dt.utcoffset()  # type: ignore

        # Default
        self.name = self.user.name
        self.charttype = self.chart_type
        self.year = self.user.utc.year
        self.month = self.user.utc.month
        self.day = self.user.utc.day
        self.hour = self.user.utc.hour + self.user.utc.minute / 100
        self.timezone = offsetToTz(dt.utcoffset())
        self.altitude = 25
        self.geonameid = None

        # Transit

        if self.chart_type == "Transit":
            self.t_geolon = self.geolon
            self.t_geolat = self.geolat
            self.t_altitude = self.altitude
            self.t_name = self.language_settings["transit_name"]
            self.t_year = dt_utc.year
            self.t_month = dt_utc.month
            self.t_day = dt_utc.day
            self.t_hour = decHourJoin(dt_utc.hour, dt_utc.minute, dt_utc.second)
            self.t_timezone = offsetToTz(dt.utcoffset())
            self.t_altitude = 25
            self.t_geonameid = None

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

        # Immediately generate template.
        self.template = self.makeTemplate()

    def set_output_directory(self, dir_path: Path) -> None:
        """
        Sets the output direcotry and returns it's path.
        """
        self.output_directory = dir_path
        dir_string = f"Output direcotry set to: {self.output_directory}"
        return print(dir_string)

    def parse_json_settings(self, settings_file):
        """
        Parse the settings file.
        """
        settings = get_settings_dict(settings_file)

        language = settings["general_settings"]["language"]
        self.language_settings = settings["language_settings"].get(language, "EN")
        self.chart_colors_settings = settings["chart_colors"]
        self.planets_settings = settings["celestial_points"]
        self.aspects_settings = settings["aspects"]
        self.planet_in_zodiac_extra_points = settings["general_settings"]["planet_in_zodiac_extra_points"]

    def _transitRing(self, r) -> str:
        """
        Draws the transit ring.
        """
        radius_offset = 18

        out = f'<circle cx="{r}" cy="{r}" r="{r - radius_offset}" style="fill: none; stroke: {self.chart_colors_settings["paper_1"]}; stroke-width: 36px; stroke-opacity: .4;"/>'
        out += f'<circle cx="{r}" cy="{r}" r="{r}" style="fill: none; stroke: {self.chart_colors_settings["zodiac_transit_ring_3"]}; stroke-width: 1px; stroke-opacity: .6;"/>'

        return out

    def _degreeRing(self, r) -> str:
        """
        Draws the degree ring.
        """
        out = ""
        for i in range(72):
            offset = float(i * 5) - self.user.houses_degree_ut[6]
            if offset < 0:
                offset = offset + 360.0
            elif offset > 360:
                offset = offset - 360.0
            x1 = sliceToX(0, r - self.c1, offset) + self.c1
            y1 = sliceToY(0, r - self.c1, offset) + self.c1
            x2 = sliceToX(0, r + 2 - self.c1, offset) - 2 + self.c1
            y2 = sliceToY(0, r + 2 - self.c1, offset) - 2 + self.c1

            out += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {self.chart_colors_settings["paper_0"]}; stroke-width: 1px; stroke-opacity:.9;"/>'

        return out

    def _degreeTransitRing(self, r):
        out = ""
        for i in range(72):
            offset = float(i * 5) - self.user.houses_degree_ut[6]
            if offset < 0:
                offset = offset + 360.0
            elif offset > 360:
                offset = offset - 360.0
            x1 = sliceToX(0, r, offset)
            y1 = sliceToY(0, r, offset)
            x2 = sliceToX(0, r + 2, offset) - 2
            y2 = sliceToY(0, r + 2, offset) - 2
            out += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: #F00; stroke-width: 1px; stroke-opacity:.9;"/>'

        return out

    def _lat2str(self, coord):
        """Converts a floating point latitude to string with
        degree, minutes and seconds and the appropriate sign
        (north or south). Eg. 52.1234567 -> 52°7'25" N

        Args:
            coord (float): latitude in floating point format
        Returns:
            str: latitude in string format with degree, minutes,
             seconds and sign (N/S)
        """

        sign = self.language_settings["north"]
        if coord < 0.0:
            sign = self.language_settings["south"]
            coord = abs(coord)
        deg = int(coord)
        min = int((float(coord) - deg) * 60)
        sec = int(round(float(((float(coord) - deg) * 60) - min) * 60.0))
        return f"{deg}°{min}'{sec}\" {sign}"

    def _lon2str(self, coord):
        """Converts a floating point longitude to string with
        degree, minutes and seconds and the appropriate sign
        (east or west). Eg. 52.1234567 -> 52°7'25" E

        Args:
            coord (float): longitude in floating point format
        Returns:
            str: longitude in string format with degree, minutes,
                seconds and sign (E/W)
        """

        sign = self.language_settings["east"]
        if coord < 0.0:
            sign = self.language_settings["west"]
            coord = abs(coord)
        deg = int(coord)
        min = int((float(coord) - deg) * 60)
        sec = int(round(float(((float(coord) - deg) * 60) - min) * 60.0))
        return f"{deg}°{min}'{sec}\" {sign}"

    def _dec2deg(self, dec, type="3"):
        """Coverts decimal float to degrees in format
        a°b'c".
        """

        dec = float(dec)
        a = int(dec)
        a_new = (dec - float(a)) * 60.0
        b_rounded = int(round(a_new))
        b = int(a_new)
        c = int(round((a_new - float(b)) * 60.0))
        if type == "3":
            out = f"{a:02d}&#176;{b:02d}&#39;{c:02d}&#34;"
        elif type == "2":
            out = f"{a:02d}&#176;{b_rounded:02d}&#39;"
        elif type == "1":
            out = f"{a:02d}&#176;"
        else:
            raise KerykeionException(f"Wrong type: {type}, it must be 1, 2 or 3.")
        return str(out)

    def _drawAspect(self, r, ar, degA, degB, color):
        """
        Draws svg aspects: ring, aspect ring, degreeA degreeB
        """
        offset = (int(self.user.houses_degree_ut[6]) / -1) + int(degA)
        x1 = sliceToX(0, ar, offset) + (r - ar)
        y1 = sliceToY(0, ar, offset) + (r - ar)
        offset = (int(self.user.houses_degree_ut[6]) / -1) + int(degB)
        x2 = sliceToX(0, ar, offset) + (r - ar)
        y2 = sliceToY(0, ar, offset) + (r - ar)
        out = f'            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {color}; stroke-width: 1; stroke-opacity: .9;"/>'

        return out

    def _zodiacSlice(self, num, r, style, type):
        # pie slices
        offset = 360 - self.user.houses_degree_ut[6]
        # check transit
        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            dropin = 0
        else:
            dropin = self.c1
        slice = f'<path d="M{str(r)},{str(r)} L{str(dropin + sliceToX(num, r - dropin, offset))},{str(dropin + sliceToY(num, r - dropin, offset))} A{str(r - dropin)},{str(r - dropin)} 0 0,0 {str(dropin + sliceToX(num + 1, r - dropin, offset))},{str(dropin + sliceToY(num + 1, r - dropin, offset))} z" style="{style}"/>'

        # symbols
        offset = offset + 15
        # check transit
        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            dropin = 54
        else:
            dropin = 18 + self.c1
        sign = f'<g transform="translate(-16,-16)"><use x="{str(dropin + sliceToX(num, r - dropin, offset))}" y="{str(dropin + sliceToY(num, r - dropin, offset))}" xlink:href="#{type}" /></g>'

        return slice + "" + sign

    def _makeZodiac(self, r):
        output = ""
        for i in range(len(self.zodiac)):
            output = (
                output
                + self._zodiacSlice(
                    i,
                    r,
                    f'fill:{self.chart_colors_settings[f"zodiac_bg_{i}"]}; fill-opacity: 0.5;',
                    self.zodiac[i]["name"],
                )
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

    def _value_element_from_planet(self, i):
        """
        Calculate chart element points from a planet.
        """

        # element: get extra points if planet is in own zodiac sign.
        related_zodiac_signs = self.planets_settings[i]["related_zodiac_signs"]
        cz = self.points_sign[i]
        extra_points = 0
        if related_zodiac_signs != []:
            for e in range(len(related_zodiac_signs)):
                if int(related_zodiac_signs[e]) == int(cz):
                    extra_points = self.planet_in_zodiac_extra_points

        ele = self.zodiac[self.points_sign[i]]["element"]
        if ele == "fire":
            self.fire = self.fire + self.planets_settings[i]["element_points"] + extra_points

        elif ele == "earth":
            self.earth = self.earth + self.planets_settings[i]["element_points"] + extra_points

        elif ele == "air":
            self.air = self.air + self.planets_settings[i]["element_points"] + extra_points

        elif ele == "water":
            self.water = self.water + self.planets_settings[i]["element_points"] + extra_points

    def _make_planets(self, r):
        planets_degut = {}
        diff = range(len(self.planets_settings))

        for i in range(len(self.planets_settings)):
            if self.planets_settings[i]["is_active"] == 1:
                # list of planets sorted by degree
                logger.debug(f"planet: {i}, degree: {self.points_deg_ut[i]}")
                planets_degut[self.points_deg_ut[i]] = i

            self._value_element_from_planet(i)

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

            logger.debug(f'{self.planets_settings[i]["label"]}, {diffa}, {diffb}')

            if diffb < planet_drange:
                if group_open:
                    groups[-1].append([e, diffa, diffb, self.planets_settings[planets_degut[keys[e]]]["label"]])
                else:
                    group_open = True
                    groups.append([])
                    groups[-1].append([e, diffa, diffb, self.planets_settings[planets_degut[keys[e]]]["label"]])
            else:
                if group_open:
                    groups[-1].append([e, diffa, diffb, self.planets_settings[planets_degut[keys[e]]]["label"]])
                group_open = False

        def zero(x):
            return 0

        planets_delta = list(map(zero, range(len(self.planets_settings))))

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
                color = self.planets_settings[i]["color"]
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
            output += f'<g transform="translate(-{12 * scale},-{12 * scale})"><g transform="scale({scale})"><use x="{planet_x * (1/scale)}" y="{planet_y * (1/scale)}" xlink:href="#{self.planets_settings[i]["name"]}" /></g></g>'

        # make transit degut and display planets
        if self.chart_type == "Transit" or self.chart_type == "Synastry":
            group_offset = {}
            t_planets_degut = {}
            if self.chart_type == "Transit":
                list_range = len(self.planets_settings) - 4
            else:
                list_range = len(self.planets_settings)
            for i in range(list_range):
                group_offset[i] = 0
                if self.planets_settings[i]["is_active"] == 1:
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
            for e in range(len(t_keys)):
                i = t_planets_degut[t_keys[e]]

                if 22 < i < 27:
                    rplanet = 9
                elif switch == 1:
                    rplanet = 18
                    switch = 0
                else:
                    rplanet = 26
                    switch = 1

                zeropoint = 360 - self.user.houses_degree_ut[6]
                t_offset = zeropoint + self.t_points_deg_ut[i]
                if t_offset > 360:
                    t_offset = t_offset - 360
                planet_x = sliceToX(0, (r - rplanet), t_offset) + rplanet
                planet_y = sliceToY(0, (r - rplanet), t_offset) + rplanet
                output += f'<g transform="translate(-6,-6)"><g transform="scale(0.5)"><use x="{planet_x*2}" y="{planet_y*2}" xlink:href="#{self.planets_settings[i]["name"]}" /></g></g>'

                # transit planet line
                x1 = sliceToX(0, r + 3, t_offset) - 3
                y1 = sliceToY(0, r + 3, t_offset) - 3
                x2 = sliceToX(0, r - 3, t_offset) + 3
                y2 = sliceToY(0, r - 3, t_offset) + 3
                output += f'<line x1="{str(x1)}" y1="{str(y1)}" x2="{str(x2)}" y2="{str(y2)}" style="stroke: {self.planets_settings[i]["color"]}; stroke-width: 1px; stroke-opacity:.8;"/>'

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
                output += f'" style="fill: {self.planets_settings[i]["color"]}; font-size: 10px;">{self._dec2deg(self.t_points_deg[i], type="1")}'
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

            output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {self.planets_settings[i]["color"]}; stroke-width: 2px; stroke-opacity:.6;"/>'

            # check transit
            if self.chart_type == "Transit" or self.chart_type == "Synastry":
                dropin = 160
            else:
                dropin = 120

            x1 = sliceToX(0, r - dropin, offset) + dropin
            y1 = sliceToY(0, r - dropin, offset) + dropin
            x2 = sliceToX(0, (r - (dropin - 3)), offset) + (dropin - 3)
            y2 = sliceToY(0, (r - (dropin - 3)), offset) + (dropin - 3)
            output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {self.planets_settings[i]["color"]}; stroke-width: 2px; stroke-opacity:.6;"/>'

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
        for i in range(len(self.planets_settings)):
            a = self.points_deg_ut[i]
            qc[i] = {}
            sext[i] = {}
            opp[i] = {}
            sq[i] = {}
            tr[i] = {}
            conj[i] = {}
            # skip some points
            n = self.planets_settings[i]["name"]
            if n == "earth" or n == "True_Node" or n == "osc. apogee" or n == "intp. apogee" or n == "intp. perigee":
                continue
            if n == "Dsc" or n == "Ic":
                continue
            for j in range(len(self.planets_settings)):
                # skip some points
                n = self.planets_settings[j]["name"]
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
                            logger.debug(f"Got tsquare {a} {k} {l}")
                            if k > l:
                                tsquare[f"{a},{l},{k}"] = f"{self.planets_settings[a]['label']} => {self.planets_settings[l]['label']}, {self.planets_settings[k]['label']}"

                            else:
                                tsquare[f"{a},{k},{l}"] = f"{self.planets_settings[a]['label']} => {self.planets_settings[k]['label']}, {self.planets_settings[l]['label']}"

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
                                                self.planets_settings[l[0]]["label"],
                                                self.planets_settings[l[1]]["label"],
                                                self.planets_settings[l[2]]["label"],
                                                self.planets_settings[l[3]]["label"],
                                            )
        # print yots
        out = '<g transform="translate(-30,380)">'
        if len(yot) >= 1:
            y = 0
            for k, v in yot.items():
                out += f'<text y="{y}" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 12px;">{"Yot"}</text>'

                # first planet symbol
                out += f'<g transform="translate(20,{y})">'
                out += f'<use transform="scale(0.4)" x="0" y="-20" xlink:href="#{self.planets_settings[yot[k][0]]["name"]}" /></g>'

                # second planet symbol
                out += f'<g transform="translate(30,{y})">'
                out += f'<use transform="scale(0.4)" x="0" y="-20" xlink:href="#{self.planets_settings[yot[k][1]]["name"]}" /></g>'

                # third planet symbol
                out += f'<g transform="translate(40,{y})">'
                out += f'<use transform="scale(0.4)" x="0" y="-20" xlink:href="#{self.planets_settings[yot[k][2]]["name"]}" /></g>'

                y = y + 14
        # finalize
        out += "</g>"
        # return out
        return ""

    # Aspect and aspect grid functions for natal type charts.
    def _makeAspects(self, r, ar):
        out = ""
        for element in self.aspects_list:
            out += self._drawAspect(
                r,
                ar,
                element["p1_abs_pos"],
                element["p2_abs_pos"],
                self.aspects_settings[element["aid"]]["color"],
            )

        return out

    def _makeAspectGrid(self, r):
        out = ""
        style = "stroke:%s; stroke-width: 1px; stroke-opacity:.6; fill:none" % (self.chart_colors_settings["paper_0"])
        xindent = 380
        yindent = 468
        box = 14
        revr = list(range(len(self.planets_settings)))
        revr.reverse()
        counter = 0
        for a in revr:
            counter += 1
            if self.planets_settings[a]["is_active"] == 1:
                out += f'<rect x="{xindent}" y="{yindent}" width="{box}" height="{box}" style="{style}"/>'
                out += f'<use transform="scale(0.4)" x="{(xindent+2)*2.5}" y="{(yindent+1)*2.5}" xlink:href="#{self.planets_settings[a]["name"]}" />'

                xindent = xindent + box
                yindent = yindent - box
                revr2 = list(range(a))
                revr2.reverse()
                xorb = xindent
                yorb = yindent + box
                for b in revr2:
                    if self.planets_settings[b]["is_active"] == 1:
                        out += f'<rect x="{xorb}" y="{yorb}" width="{box}" height="{box}" style="{style}"/>'

                        xorb = xorb + box
                        for element in self.aspects_list:
                            if (element["p1"] == a and element["p2"] == b) or (element["p1"] == b and element["p2"] == a):
                                out += f'<use  x="{xorb-box+1}" y="{yorb+1}" xlink:href="#orb{element["aspect_degrees"]}" />'

        return out

    # Aspect and aspect grid functions for transit type charts.

    def _makeAspectsTransit(self, r, ar):
        out = ""

        self.aspects_list = SynastryAspects(self.user, self.t_user, new_settings_file=self.new_settings_file).get_relevant_aspects()

        for element in self.aspects_list:
            print(element)
            out += self._drawAspect(
                r,
                ar,
                element["p1_abs_pos"],
                element["p2_abs_pos"],
                self.aspects_settings[element["aid"]]["color"],
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
                # if len(self.aspects_list) > 24:
                #     line = -1 * ( len(self.aspects_list) - 24) * 14
                # else:
                #     line = 0

                # temporary:
                line = 0

            if i == 24:
                nl = 200
                # if len(self.aspects_list) > 36:
                #     line = -1 * ( len(self.aspects_list) - 36) * 14
                # else:
                #     line = 0
                line = 0

            if i == 36:
                nl = 300
                if len(self.aspects_list) > 48:
                    line = -1 * (len(self.aspects_list) - 48) * 14
                else:
                    line = 0
            out += f'<g transform="translate({nl},{line})">'
            # first planet symbol

            # TODO: (next((item for item in self.planets_settings if item["id"] == self.aspects_list[i]["p1"]))) It preventes the use ot numeric ID, but it is not working.
            out += f'<use transform="scale(0.4)" x="0" y="3" xlink:href="#{self.planets_settings[self.aspects_list[i]["p1"]]["name"]}" />'
            
            # aspect symbol
            out += f'<use  x="15" y="0" xlink:href="#orb{self.aspects_settings[self.aspects_list[i]["aid"]]["degree"]}" />'
            # second planet symbol
            out += '<g transform="translate(30,0)">'
            
            # TODO: (next((item for item in self.planets_settings if item["id"] == self.aspects_list[i]["p3"])))
            out += '<use transform="scale(0.4)" x="0" y="3" xlink:href="#%s" />' % (self.planets_settings[self.aspects_list[i]["p2"]]["name"]) 
            
            out += "</g>"
            # difference in degrees
            out += f'<text y="8" x="45" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self._dec2deg(self.aspects_list[i]["orbit"])}</text>'
            # line
            out += "</g>"
            line = line + 14
        out += "</g>"
        return out

    def _makeElements(self, r):
        total = self.fire + self.earth + self.air + self.water
        pf = int(round(100 * self.fire / total))
        pe = int(round(100 * self.earth / total))
        pa = int(round(100 * self.air / total))
        pw = int(round(100 * self.water / total))

        out = '<g transform="translate(-30,79)">'
        out += f'<text y="0" style="fill:#ff6600; font-size: 10px;">{self.language_settings["fire"]}  {str(pf)}%</text>'
        out += f'<text y="12" style="fill:#6a2d04; font-size: 10px;">{self.language_settings["earth"]} {str(pe)}%</text>'
        out += f'<text y="24" style="fill:#6f76d1; font-size: 10px;">{self.language_settings["air"]}   {str(pa)}%</text>'
        out += f'<text y="36" style="fill:#630e73; font-size: 10px;">{self.language_settings["water"]} {str(pw)}%</text>'
        out += "</g>"

        return out

    def _makePlanetGrid(self):
        li = 10
        offset = 0

        out = '<g transform="translate(500,-20)">'
        out += '<g transform="translate(140, -15)">'
        out += f'<text text-anchor="end" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 14px;">{self.language_settings["planets_and_house"]} {self.name}:</text>'
        out += "</g>"

        end_of_line = None
        for i in range(len(self.planets_settings)):
            offset_between_lines = 14
            end_of_line = "</g>"

            # Guarda qui !!
            if i == 27:
                li = 10
                offset = -120

            if self.planets_settings[i]["is_active"] == 1:
                # start of line
                out += f'<g transform="translate({offset},{li})">'

                # planet text
                out += f'<text text-anchor="end" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self.language_settings["celestial_points"][self.planets_settings[i]["label"]]}</text>'

                # planet symbol
                out += f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{self.planets_settings[i]["name"]}" /></g>'

                # planet degree
                out += f'<text text-anchor="start" x="19" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self._dec2deg(self.points_deg[i])}</text>'

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

            for i in range(len(self.planets_settings)):
                if i == 27:
                    t_li = 10
                    t_offset = -120

                if self.planets_settings[i]["is_active"] == 1:
                    # start of line
                    out += f'<g transform="translate({t_offset},{t_li})">'

                    # planet text
                    out += f'<text text-anchor="end" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self.language_settings["celestial_points"][self.planets_settings[i]["label"]]}</text>'
                    # planet symbol
                    out += f'<g transform="translate(5,-8)"><use transform="scale(0.4)" xlink:href="#{self.planets_settings[i]["name"]}" /></g>'
                    # planet degree
                    out += f'<text text-anchor="start" x="19" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self._dec2deg(self.t_points_deg[i])}</text>'
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

    def _makeHousesGrid(self):
        out = '<g transform="translate(600,-20)">'

        li = 10
        for i in range(12):
            if i < 9:
                cusp = "&#160;&#160;" + str(i + 1)
            else:
                cusp = str(i + 1)
            out += f'<g transform="translate(0,{li})">'
            out += f'<text text-anchor="end" x="40" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self.language_settings["cusp"]} {cusp}:</text>'
            out += f'<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#{self.zodiac[self.houses_sign_graph[i]]["name"]}" /></g>'
            out += f'<text x="53" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;"> {self._dec2deg(self.user.houses_list[i]["position"])}</text>'
            out += "</g>"
            li = li + 14

        out += "</g>"

        if self.chart_type == "Synastry":
            out += '<g transform="translate(840, -20)">'
            li = 10
            for i in range(12):
                if i < 9:
                    cusp = "&#160;&#160;" + str(i + 1)
                else:
                    cusp = str(i + 1)
                out += '<g transform="translate(0,' + str(li) + ')">'
                out += f'<text text-anchor="end" x="40" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;">{self.language_settings["cusp"]} {cusp}:</text>'
                out += f'<g transform="translate(40,-8)"><use transform="scale(0.3)" xlink:href="#{self.zodiac[self.t_houses_sign_graph[i]]["name"]}" /></g>'
                out += f'<text x="53" style="fill:{self.chart_colors_settings["paper_0"]}; font-size: 10px;"> {self._dec2deg(self.t_user.houses_list[i]["position"])}</text>'
                out += "</g>"
                li = li + 14
            out += "</g>"

        return out

    def _createTemplateDictionary(self):
        # self.chart_type = "Transit"
        # empty element points
        self.fire = 0.0
        self.earth = 0.0
        self.air = 0.0
        self.water = 0.0

        # width and height from screen
        ratio = float(self.screen_width) / float(self.screen_height)
        if ratio < 1.3:  # 1280x1024
            wm_off = 130
        else:  # 1024x768, 800x600, 1280x800, 1680x1050
            wm_off = 100

        # Viewbox and sizing
        svgHeight = "100%"  # self.screen_height-wm_off
        svgWidth = "100%"  #  self.screen_width-5.0
        # svgHeight=self.screen_height-wm_off
        # svgWidth=(770.0*svgHeight)/540.0
        # svgWidth=float(self.screen_width)-25.0
        rotate = "0"
        translate = "0"
        # Defoult:
        # viewbox = '0 0 772.2 546.0' #297mm * 2.6 + 210mm * 2.6
        if self.chart_type == "Natal":
            viewbox = "0 0 772.2 546.0"  # 297mm * 2.6 + 210mm * 2.6
        else:
            viewbox = "0 0 1000 546.0"

        # template dictionary
        td: ChartTemplateModel = dict()
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
            td["transitRing"] = self._transitRing(r)
            td["degreeRing"] = self._degreeTransitRing(r)

            # circles
            td["c1"] = f'cx="{r}" cy="{r}" r="{r - 36}"'
            td["c1style"] = f'fill: none; stroke: {self.chart_colors_settings["zodiac_transit_ring_2"]}; stroke-width: 1px; stroke-opacity:.4;'
            td["c2"] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r - 72) + '"'
            td["c2style"] = f"fill: {self.chart_colors_settings['paper_1']}; fill-opacity:.4; stroke: {self.chart_colors_settings['zodiac_transit_ring_1']}; stroke-opacity:.4; stroke-width: 1px"

            td["c3"] = 'cx="' + str(r) + '" cy="' + str(r) + '" r="' + str(r - 160) + '"'
            td["c3style"] = f"fill: {self.chart_colors_settings['paper_1']}; fill-opacity:.8; stroke: {self.chart_colors_settings['zodiac_transit_ring_0']}; stroke-width: 1px"

            td["makeAspects"] = self._makeAspectsTransit(r, (r - 160))
            td["makeAspectGrid"] = self._makeAspectTransitGrid(r)
            td["makePatterns"] = ""
            td["chart_width"] = self.full_width
        else:
            td["transitRing"] = ""
            td["degreeRing"] = self._degreeRing(r)

            # circles
            td["c1"] = f'cx="{r}" cy="{r}" r="{r - self.c1}"'
            td["c1style"] = f'fill: none; stroke: {self.chart_colors_settings["zodiac_radix_ring_2"]}; stroke-width: 1px; '
            td["c2"] = f'cx="{r}" cy="{r}" r="{r - self.c2}"'
            td["c2style"] = f'fill: {self.chart_colors_settings["paper_1"]}; fill-opacity:.2; stroke: {self.chart_colors_settings["zodiac_radix_ring_1"]}; stroke-opacity:.4; stroke-width: 1px'
            td["c3"] = f'cx="{r}" cy="{r}" r="{r - self.c3}"'
            td["c3style"] = f'fill: {self.chart_colors_settings["paper_1"]}; fill-opacity:.8; stroke: {self.chart_colors_settings["zodiac_radix_ring_0"]}; stroke-width: 1px'
            td["makeAspects"] = self._makeAspects(r, (r - self.c3))
            td["makeAspectGrid"] = self._makeAspectGrid(r)
            td["makePatterns"] = self._makePatterns()
            td["chart_width"] = self.natal_width

        td["circleX"] = str(0)
        td["circleY"] = str(0)
        td["svgWidth"] = str(svgWidth)
        td["svgHeight"] = str(svgHeight)
        td["viewbox"] = viewbox

        if self.chart_type == "Synastry":
            td["stringTitle"] = f"{self.name} {self.language_settings['and_word']} {self.t_user.name}"

        elif self.chart_type == "Transit":
            td["stringTitle"] = f"{self.language_settings['transits']} {self.t_user.day}/{self.t_user.month}/{self.t_user.year}"

        else:
            td["stringTitle"] = self.name

        # Tipo di carta
        if self.chart_type == "Synastry" or self.name == "Transit":
            td["stringName"] = f"{self.name}:"
        else:
            td["stringName"] = f'{self.language_settings["info"]}:'

        # bottom left
        td["bottomLeft1"] = ""
        td["bottomLeft2"] = ""
        td["bottomLeft3"] = f'{self.language_settings.get("lunar_phase", "Lunar Phase")}: {self.language_settings.get("day", "Day")} {self.user.lunar_phase.get("moon_phase", "")}'
        td["bottomLeft4"] = ""

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

        td["stringDateTime"] = f"{self.user.year}-{self.user.month}-{self.user.day} {self.user.hour:02d}:{self.user.minute:02d}"

        if self.chart_type == "Synastry":
            td["stringLat"] = f"{self.t_user.name}: "
            td["stringLon"] = self.t_user.city
            td["stringPosition"] = f"{self.t_user.year}-{self.t_user.month}-{self.t_user.day} {self.t_user.hour:02d}:{self.t_user.minute:02d}"

        else:
            td["stringLat"] = f"{self.language_settings['latitude']}: {self._lat2str(self.geolat)}"
            td["stringLon"] = f"{self.language_settings['longitude']}: {self._lon2str(self.geolon)}"
            td["stringPosition"] = f"{self.language_settings['type']}: {self.charttype}"

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
        td["cfgTranslate"] = translate

        # functions
        td["makeZodiac"] = self._makeZodiac(r)
        td["makeHouses"] = self._makeHouses(r)
        td["makePlanets"] = self._make_planets(r)
        td["makeElements"] = self._makeElements(r)
        td["makePlanetGrid"] = self._makePlanetGrid()
        td["makeHousesGrid"] = self._makeHousesGrid()

        return td

    def makeTemplate(self):
        """Creates the template for the SVG file"""
        td = self._createTemplateDictionary()

        # read template
        with open(self.xml_svg, "r", encoding="utf-8", errors="ignore") as output_file:
            f = open(self.xml_svg)
            template = Template(f.read()).substitute(td)

        # return filename

        logger.debug(f"Template dictionary keys: {td.keys()}")

        self._createTemplateDictionary()
        return template.replace('"', "'")

    def makeSVG(self):
        """Prints out the SVG file in the specifide folder"""

        if not (self.template):
            self.template = self.makeTemplate()

        self.chartname = self.output_directory / f"{self.name}{self.chart_type}Chart.svg"

        with open(self.chartname, "w", encoding="utf-8", errors="ignore") as output_file:
            output_file.write(self.template)

        return print(f"SVG Generated Correctly in: {self.chartname}")


if __name__ == "__main__":
    basicConfig(level="DEBUG")

    first = AstrologicalSubject("John Lennon", 1940, 10, 9, 10, 30, "Liverpool", "GB")
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
