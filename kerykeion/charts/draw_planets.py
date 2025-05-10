# type: ignore
# TODO: Legacy original method extracted as function. The V2 is a heavy refactor of this code. If it's safe, delete this.

from kerykeion.charts.charts_utils import degreeDiff, sliceToX, sliceToY, convert_decimal_to_degree_string
from kerykeion.kr_types import KerykeionException, ChartType, KerykeionPointModel
from kerykeion.kr_types.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.kr_types.kr_literals import Houses
import logging
from typing import Union, get_args



def draw_planets(
    radius: Union[int, float],
    available_kerykeion_celestial_points: list[KerykeionPointModel],
    available_planets_setting: list[KerykeionSettingsCelestialPointModel],
    third_circle_radius: Union[int, float],
    main_subject_first_house_degree_ut: Union[int, float],
    main_subject_seventh_house_degree_ut: Union[int, float],
    chart_type: ChartType,
    second_subject_available_kerykeion_celestial_points: Union[list[KerykeionPointModel], None] = None,
):
    """
    Draws the planets on a chart based on the provided parameters.

    Args:
        radius (int): The radius of the chart.
        available_kerykeion_celestial_points (list[KerykeionPointModel]): List of celestial points for the main subject.
        available_planets_setting (list[KerykeionSettingsCelestialPointModel]): Settings for the celestial points.
        third_circle_radius (Union[int, float]): Radius of the third circle.
        main_subject_first_house_degree_ut (Union[int, float]): Degree of the first house for the main subject.
        main_subject_seventh_house_degree_ut (Union[int, float]): Degree of the seventh house for the main subject.
        chart_type (ChartType): Type of the chart (e.g., "Transit", "Synastry").
        second_subject_available_kerykeion_celestial_points (Union[list[KerykeionPointModel], None], optional):
            List of celestial points for the second subject, required for "Transit" or "Synastry" charts. Defaults to None.

    Raises:
        KerykeionException: If the second subject is required but not provided.

    Returns:
        str: SVG output for the chart with the planets drawn.
    """
    TRANSIT_RING_EXCLUDE_POINTS_NAMES = get_args(Houses)

    if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
        if second_subject_available_kerykeion_celestial_points is None:
            raise KerykeionException("Second subject is required for Transit or Synastry charts")

    # Make a list for the absolute degrees of the points of the graphic.
    points_deg_ut = []
    for planet in available_kerykeion_celestial_points:
        points_deg_ut.append(planet.abs_pos)

    # Make a list of the relative degrees of the points in the graphic.
    points_deg = []
    for planet in available_kerykeion_celestial_points:
        points_deg.append(planet.position)

    if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
        # Make a list for the absolute degrees of the points of the graphic.
        t_points_deg_ut = []
        for planet in second_subject_available_kerykeion_celestial_points:
            t_points_deg_ut.append(planet.abs_pos)

        # Make a list of the relative degrees of the points in the graphic.
        t_points_deg = []
        for planet in second_subject_available_kerykeion_celestial_points:
            t_points_deg.append(planet.position)

    planets_degut = {}
    diff = range(len(available_planets_setting))

    for i in range(len(available_planets_setting)):
        # list of planets sorted by degree
        logging.debug(f"planet: {i}, degree: {points_deg_ut[i]}")
        planets_degut[points_deg_ut[i]] = i

    """
    FIXME: The planets_degut is a dictionary like:
    {planet_degree: planet_index}
    It should be replaced bu points_deg_ut
    print(points_deg_ut)
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
            prev = points_deg_ut[planets_degut[keys[-1]]]
            next = points_deg_ut[planets_degut[keys[1]]]
        elif e == (len(keys) - 1):
            prev = points_deg_ut[planets_degut[keys[e - 1]]]
            next = points_deg_ut[planets_degut[keys[0]]]
        else:
            prev = points_deg_ut[planets_degut[keys[e - 1]]]
            next = points_deg_ut[planets_degut[keys[e + 1]]]
        diffa = degreeDiff(prev, points_deg_ut[i])
        diffb = degreeDiff(next, points_deg_ut[i])
        planets_by_pos[e] = [i, diffa, diffb]

        logging.debug(f'{available_planets_setting[i]["label"]}, {diffa}, {diffb}')

        if diffb < planet_drange:
            if group_open:
                groups[-1].append([e, diffa, diffb, available_planets_setting[planets_degut[keys[e]]]["label"]])
            else:
                group_open = True
                groups.append([])
                groups[-1].append([e, diffa, diffb, available_planets_setting[planets_degut[keys[e]]]["label"]])
        else:
            if group_open:
                groups[-1].append([e, diffa, diffb, available_planets_setting[planets_degut[keys[e]]]["label"]])
            group_open = False

    def zero(x):
        return 0

    planets_delta = list(map(zero, range(len(available_planets_setting))))

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
            elif (planets_by_pos[next_to_a][1] > (2.4 * planet_drange)) & (
                planets_by_pos[next_to_b][2] > (2.4 * planet_drange)
            ):
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
                    planets_delta[groups[a][(f + 1)][0]] = (
                        1.2 * planet_drange + planets_delta[groups[a][f][0]] - groups[a][f][2]
                    )

    for e in range(len(keys)):
        i = planets_degut[keys[e]]

        # coordinates
        if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
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
            if chart_type == "ExternalNatal":
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

        offset = (int(main_subject_seventh_house_degree_ut) / -1) + int(points_deg_ut[i] + planets_delta[e])
        trueoffset = (int(main_subject_seventh_house_degree_ut) / -1) + int(points_deg_ut[i])

        planet_x = sliceToX(0, (radius - rplanet), offset) + rplanet
        planet_y = sliceToY(0, (radius - rplanet), offset) + rplanet
        if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
            scale = 0.8

        elif chart_type == "ExternalNatal":
            scale = 0.8
            # line1
            x1 = sliceToX(0, (radius - third_circle_radius), trueoffset) + third_circle_radius
            y1 = sliceToY(0, (radius - third_circle_radius), trueoffset) + third_circle_radius
            x2 = sliceToX(0, (radius - rplanet - 30), trueoffset) + rplanet + 30
            y2 = sliceToY(0, (radius - rplanet - 30), trueoffset) + rplanet + 30
            color = available_planets_setting[i]["color"]
            output += (
                '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke-width:1px;stroke:%s;stroke-opacity:.3;"/>\n'
                % (x1, y1, x2, y2, color)
            )
            # line2
            x1 = sliceToX(0, (radius - rplanet - 30), trueoffset) + rplanet + 30
            y1 = sliceToY(0, (radius - rplanet - 30), trueoffset) + rplanet + 30
            x2 = sliceToX(0, (radius - rplanet - 10), offset) + rplanet + 10
            y2 = sliceToY(0, (radius - rplanet - 10), offset) + rplanet + 10
            output += (
                '<line x1="%s" y1="%s" x2="%s" y2="%s" style="stroke-width:1px;stroke:%s;stroke-opacity:.5;"/>\n'
                % (x1, y1, x2, y2, color)
            )

        else:
            scale = 1

        planet_details = available_kerykeion_celestial_points[i]

        output += f'<g kr:node="ChartPoint" kr:house="{planet_details["house"]}" kr:sign="{planet_details["sign"]}" kr:slug="{planet_details["name"]}" transform="translate(-{12 * scale},-{12 * scale}) scale({scale})">'
        output += f'<use x="{planet_x * (1/scale)}" y="{planet_y * (1/scale)}" xlink:href="#{available_planets_setting[i]["name"]}" />'
        output += f"</g>"

    # make transit degut and display planets
    if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
        group_offset = {}
        t_planets_degut = {}
        list_range = len(available_planets_setting)

        for i in range(list_range):
            if chart_type == "Transit" and available_planets_setting[i]["name"] in TRANSIT_RING_EXCLUDE_POINTS_NAMES:
                continue

            group_offset[i] = 0
            t_planets_degut[t_points_deg_ut[i]] = i

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

            a = t_points_deg_ut[i_a]
            b = t_points_deg_ut[i_b]
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
            if chart_type == "Transit" and available_planets_setting[e]["name"] in TRANSIT_RING_EXCLUDE_POINTS_NAMES:
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
            zeropoint = 360 - main_subject_seventh_house_degree_ut
            t_offset = zeropoint + t_points_deg_ut[i]
            if t_offset > 360:
                t_offset = t_offset - 360
            planet_x = sliceToX(0, (radius - rplanet), t_offset) + rplanet
            planet_y = sliceToY(0, (radius - rplanet), t_offset) + rplanet
            output += f'<g class="transit-planet-name" transform="translate(-6,-6)"><g transform="scale(0.5)"><use x="{planet_x*2}" y="{planet_y*2}" xlink:href="#{available_planets_setting[i]["name"]}" /></g></g>'

            # Transit planet line
            x1 = sliceToX(0, radius + 3, t_offset) - 3
            y1 = sliceToY(0, radius + 3, t_offset) - 3
            x2 = sliceToX(0, radius - 3, t_offset) + 3
            y2 = sliceToY(0, radius - 3, t_offset) + 3
            output += f'<line class="transit-planet-line" x1="{str(x1)}" y1="{str(y1)}" x2="{str(x2)}" y2="{str(y2)}" style="stroke: {available_planets_setting[i]["color"]}; stroke-width: 1px; stroke-opacity:.8;"/>'

            # transit planet degree text
            rotate = main_subject_first_house_degree_ut - t_points_deg_ut[i]
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
            deg_x = sliceToX(0, (radius - rtext), t_offset + xo) + rtext
            deg_y = sliceToY(0, (radius - rtext), t_offset + xo) + rtext
            degree = int(t_offset)
            output += f'<g transform="translate({deg_x},{deg_y})">'
            output += f'<text transform="rotate({rotate})" text-anchor="{textanchor}'
            output += f'" style="fill: {available_planets_setting[i]["color"]}; font-size: 10px;">{convert_decimal_to_degree_string(t_points_deg[i], format_type="1")}'
            output += "</text></g>"

        # check transit
        if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
            dropin = 36
        else:
            dropin = 0

        # planet line
        x1 = sliceToX(0, radius - (dropin + 3), offset) + (dropin + 3)
        y1 = sliceToY(0, radius - (dropin + 3), offset) + (dropin + 3)
        x2 = sliceToX(0, (radius - (dropin - 3)), offset) + (dropin - 3)
        y2 = sliceToY(0, (radius - (dropin - 3)), offset) + (dropin - 3)

        output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {available_planets_setting[i]["color"]}; stroke-width: 2px; stroke-opacity:.6;"/>'

        # check transit
        if chart_type == "Transit" or chart_type == "Synastry" or chart_type == "Return":
            dropin = 160
        else:
            dropin = 120

        x1 = sliceToX(0, radius - dropin, offset) + dropin
        y1 = sliceToY(0, radius - dropin, offset) + dropin
        x2 = sliceToX(0, (radius - (dropin - 3)), offset) + (dropin - 3)
        y2 = sliceToY(0, (radius - (dropin - 3)), offset) + (dropin - 3)
        output += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" style="stroke: {available_planets_setting[i]["color"]}; stroke-width: 2px; stroke-opacity:.6;"/>'

    return output
