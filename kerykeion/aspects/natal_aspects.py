# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2023 Giacomo Battaglia
"""

from pathlib import Path
from kerykeion import AstrologicalSubject
from logging import getLogger, basicConfig
from typing import Union
from kerykeion.settings.kerykeion_settings import get_settings
from dataclasses import dataclass
from kerykeion.aspects.aspects_utils import filter_by_settings, planet_id_decoder, get_aspect_from_two_points

logger = getLogger(__name__)
basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level="INFO")


@dataclass
class NatalAspects:
    """
    Generates an object with all the aspects of a birthcart.
    """

    user: AstrologicalSubject
    new_settings_file: Union[Path, None] = None
    _all_aspects: Union[list, None] = None
    _relevant_aspects: Union[list, None] = None

    def __post_init__(self):
        settings = get_settings(self.new_settings_file)

        self.init_point_list = self.user.planets_list + self.user.houses_list

        self.planets_settings = settings["celestial_points"]
        self.aspects_settings = settings["aspects"]
        self.axes_orbit_settings = settings["general_settings"]["axes_orbit"]

    @property
    def all_aspects(self):
        """
        Return all the aspects of the points in the natal chart in a dictionary,
        first all the individual aspects of each planet, second the aspects
        without repetitions.
        """

        if self._all_aspects is not None:
            return self._all_aspects

        point_list = filter_by_settings(self.planets_settings, self.init_point_list)

        self.all_aspects_list = []

        for first in range(len(point_list)):
            # Generates the aspects list without repetitions
            for second in range(first + 1, len(point_list)):
                verdict, name, orbit, aspect_degrees, color, aid, diff = get_aspect_from_two_points(
                    self.aspects_settings, point_list[first]["abs_pos"], point_list[second]["abs_pos"]
                )

                if verdict == True:
                    d_asp = {
                        "p1_name": point_list[first]["name"],
                        "p1_abs_pos": point_list[first]["abs_pos"],
                        "p2_name": point_list[second]["name"],
                        "p2_abs_pos": point_list[second]["abs_pos"],
                        "aspect": name,
                        "orbit": orbit,
                        "aspect_degrees": aspect_degrees,
                        "color": color,
                        "aid": aid,
                        "diff": diff,
                        "p1": planet_id_decoder(self.planets_settings, point_list[first]["name"]),
                        "p2": planet_id_decoder(
                            self.planets_settings,
                            point_list[second]["name"],
                        ),
                    }

                    self.all_aspects_list.append(d_asp)

        return self.all_aspects_list

    @property
    def relevant_aspects(self):
        """
        Filters the aspects list with the desired points, in this case
        the most important are hardcoded.
        Set the list with set_points and creating a list with the names
        or the numbers of the houses.
        """

        if self._relevant_aspects is not None:
            logger.debug("Relevant aspects already calculated, returning cached value")
            return self._relevant_aspects

        logger.debug("Relevant aspects not already calculated, calculating now...")
        self.all_aspects

        aspects_filtered = []
        for a in self.all_aspects_list:
            if self.aspects_settings[a["aid"]]["is_active"] == True:
                aspects_filtered.append(a)

        axes_list = [
            "First_House",
            "Tenth_House",
            "Seventh_House",
            "Fourth_House",
        ]
        counter = 0

        aspects_list_subtract = []
        for a in aspects_filtered:
            counter += 1
            name_p1 = str(a["p1_name"])
            name_p2 = str(a["p2_name"])

            if name_p1 in axes_list:
                if abs(a["orbit"]) >= self.axes_orbit_settings:
                    aspects_list_subtract.append(a)

            elif name_p2 in axes_list:
                if abs(a["orbit"]) >= self.axes_orbit_settings:
                    aspects_list_subtract.append(a)

        self.aspects = [item for item in aspects_filtered if item not in aspects_list_subtract]

        return self.aspects


if __name__ == "__main__":
    basicConfig(level="DEBUG", force=True)
    johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US")

    # All aspects
    aspects = NatalAspects(johnny)
    print(aspects.all_aspects)

    print("\n")

    # Relevant aspects
    aspects = NatalAspects(johnny)
    print(aspects.relevant_aspects)
