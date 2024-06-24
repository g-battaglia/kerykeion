# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""

from pathlib import Path
from kerykeion import AstrologicalSubject
import logging
from typing import Union
from kerykeion.settings.kerykeion_settings import get_settings
from dataclasses import dataclass
from functools import cached_property
from kerykeion.aspects.aspects_utils import planet_id_decoder, get_aspect_from_two_points, get_active_points_list


AXES_LIST = [
    "First_House",
    "Tenth_House",
    "Seventh_House",
    "Fourth_House",
]


@dataclass
class NatalAspects:
    """
    Generates an object with all the aspects of a birthcart.
    """

    user: AstrologicalSubject
    new_settings_file: Union[Path, None] = None

    def __post_init__(self):
        self.settings = get_settings(self.new_settings_file)

        self.celestial_points = self.settings["celestial_points"]
        self.aspects_settings = self.settings["aspects"]
        self.axes_orbit_settings = self.settings["general_settings"]["axes_orbit"]

    @cached_property
    def all_aspects(self):
        """
        Return all the aspects of the points in the natal chart in a dictionary,
        first all the individual aspects of each planet, second the aspects
        without repetitions.
        """

        active_points_list = get_active_points_list(self.user, self.settings)

        self.all_aspects_list = []

        for first in range(len(active_points_list)):
            # Generates the aspects list without repetitions
            for second in range(first + 1, len(active_points_list)):
                verdict, name, orbit, aspect_degrees, aid, diff = get_aspect_from_two_points(
                    self.aspects_settings, active_points_list[first]["abs_pos"], active_points_list[second]["abs_pos"]
                )

                if verdict == True:
                    d_asp = {
                        "p1_name": active_points_list[first]["name"],
                        "p1_abs_pos": active_points_list[first]["abs_pos"],
                        "p2_name": active_points_list[second]["name"],
                        "p2_abs_pos": active_points_list[second]["abs_pos"],
                        "aspect": name,
                        "orbit": orbit,
                        "aspect_degrees": aspect_degrees,
                        "aid": aid,
                        "diff": diff,
                        "p1": planet_id_decoder(self.celestial_points, active_points_list[first]["name"]),
                        "p2": planet_id_decoder(
                            self.celestial_points,
                            active_points_list[second]["name"],
                        ),
                    }

                    self.all_aspects_list.append(d_asp)

        return self.all_aspects_list

    @cached_property
    def relevant_aspects(self):
        """
        Filters the aspects list with the desired points, in this case
        the most important are hardcoded.
        Set the list with set_points and creating a list with the names
        or the numbers of the houses.
        """

        logging.debug("Relevant aspects not already calculated, calculating now...")
        self.all_aspects

        aspects_filtered = []
        for a in self.all_aspects_list:
            if self.aspects_settings[a["aid"]]["is_active"] == True:
                aspects_filtered.append(a)

        axes_list = AXES_LIST
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
    from kerykeion.utilities import setup_logging
    setup_logging(level="debug")

    johnny = AstrologicalSubject("Johnny Depp", 1963, 6, 9, 0, 0, "Owensboro", "US")

    # All aspects
    aspects = NatalAspects(johnny)
    print(aspects.all_aspects)

    print("\n")

    # Relevant aspects
    aspects = NatalAspects(johnny)
    print(aspects.relevant_aspects)
