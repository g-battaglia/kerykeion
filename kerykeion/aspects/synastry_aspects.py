# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2024 Giacomo Battaglia
"""

from kerykeion import AstrologicalSubject
from pathlib import Path
from typing import Union
from functools import cached_property

from kerykeion.aspects.natal_aspects import NatalAspects
from kerykeion.settings.kerykeion_settings import get_settings
from kerykeion.aspects.aspects_utils import planet_id_decoder, get_aspect_from_two_points, get_active_points_list


class SynastryAspects(NatalAspects):
    """
    Generates an object with all the aspects between two persons.
    """

    def __init__(
        self,
        kr_object_one: AstrologicalSubject,
        kr_object_two: AstrologicalSubject,
        new_settings_file: Union[Path, None] = None,
    ):
        # Subjects
        self.first_user = kr_object_one
        self.second_user = kr_object_two

        # Settings
        self.new_settings_file = new_settings_file
        self.settings = get_settings(self.new_settings_file)

        self.celestial_points = self.settings["celestial_points"]
        self.aspects_settings = self.settings["aspects"]
        self.axes_orbit_settings = self.settings["general_settings"]["axes_orbit"]

        # Private variables of the aspects
        self._all_aspects: Union[list, None] = None
        self._relevant_aspects: Union[list, None] = None

    @cached_property
    def all_aspects(self):
        """
        Return all the aspects of the points in the natal chart in a dictionary,
        first all the individual aspects of each planet, second the aspects
        whiteout repetitions.
        """

        if self._all_aspects is not None:
            return self._all_aspects

        # Celestial Points Lists
        first_active_points_list = get_active_points_list(self.first_user, self.settings)
        second_active_points_list = get_active_points_list(self.second_user, self.settings)

        self.all_aspects_list = []

        for first in range(len(first_active_points_list)):
            # Generates the aspects list whitout repetitions
            for second in range(len(second_active_points_list)):
                verdict, name, orbit, aspect_degrees, aid, diff = get_aspect_from_two_points(
                    self.aspects_settings,
                    first_active_points_list[first]["abs_pos"],
                    second_active_points_list[second]["abs_pos"],
                )

                if verdict == True:
                    d_asp = {
                        "p1_name": first_active_points_list[first]["name"],
                        "p1_abs_pos": first_active_points_list[first]["abs_pos"],
                        "p2_name": second_active_points_list[second]["name"],
                        "p2_abs_pos": second_active_points_list[second]["abs_pos"],
                        "aspect": name,
                        "orbit": orbit,
                        "aspect_degrees": aspect_degrees,
                        "aid": aid,
                        "diff": diff,
                        "p1": planet_id_decoder(
                            self.settings.celestial_points, first_active_points_list[first]["name"]
                        ),
                        "p2": planet_id_decoder(
                            self.settings.celestial_points,
                            second_active_points_list[second]["name"],
                        ),
                    }

                    self.all_aspects_list.append(d_asp)

        return self.all_aspects_list


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging
    setup_logging(level="debug")

    john = AstrologicalSubject("John", 1940, 10, 9, 18, 30, "Liverpool")
    yoko = AstrologicalSubject("Yoko", 1933, 2, 18, 18, 30, "Tokyo")

    synastry_aspects = SynastryAspects(john, yoko)

    # All aspects
    print(synastry_aspects.all_aspects)

    # Relevant aspects
    print(synastry_aspects.relevant_aspects)
