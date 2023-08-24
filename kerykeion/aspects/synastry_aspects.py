# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2023 Giacomo Battaglia
"""

from kerykeion import AstrologicalSubject
from pathlib import Path
from typing import Union

from kerykeion.aspects.natal_aspects import NatalAspects
from kerykeion.settings.kerykeion_settings import get_settings
from kerykeion.aspects.aspects_utils import filter_by_settings, planet_id_decoder, get_aspect_from_two_points


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
        self.first_user = kr_object_one
        self.second_user = kr_object_two

        self.new_settings_file = new_settings_file

        self.first_init_point_list = self.first_user.planets_list + self.first_user.houses_list
        self.second_init_point_list = self.second_user.planets_list + self.second_user.houses_list

        self._all_aspects: Union[list, None] = None
        self._relevant_aspects: Union[list, None] = None

        settings = get_settings(self.new_settings_file)

        self.planets_settings = settings["celestial_points"]
        self.aspects_settings = settings["aspects"]
        self.axes_orbit_settings = settings["general_settings"]["axes_orbit"]

    @property
    def all_aspects(self):
        """
        Return all the aspects of the points in the natal chart in a dictionary,
        first all the individual aspects of each planet, second the aspects
        whiteout repetitions.
        """

        if self._all_aspects is not None:
            return self._all_aspects

        f_1 = filter_by_settings(self.planets_settings, self.first_init_point_list)

        f_2 = filter_by_settings(self.planets_settings, self.second_init_point_list)

        self.all_aspects_list = []

        for first in range(len(f_1)):
            # Generates the aspects list whitout repetitions
            for second in range(len(f_2)):
                verdict, name, orbit, aspect_degrees, color, aid, diff = get_aspect_from_two_points(
                    self.aspects_settings, f_1[first]["abs_pos"], f_2[second]["abs_pos"]
                )

                if verdict == True:
                    d_asp = {
                        "p1_name": f_1[first]["name"],
                        "p1_abs_pos": f_1[first]["abs_pos"],
                        "p2_name": f_2[second]["name"],
                        "p2_abs_pos": f_2[second]["abs_pos"],
                        "aspect": name,
                        "orbit": orbit,
                        "aspect_degrees": aspect_degrees,
                        "color": color,
                        "aid": aid,
                        "diff": diff,
                        "p1": planet_id_decoder(self.planets_settings, f_1[first]["name"]),
                        "p2": planet_id_decoder(
                            self.planets_settings,
                            f_2[second]["name"],
                        ),
                    }

                    self.all_aspects_list.append(d_asp)

        return self.all_aspects_list


if __name__ == "__main__":
    john = AstrologicalSubject("John", 1940, 10, 9, 10, 30, "Liverpool")
    yoko = AstrologicalSubject("Yoko", 1933, 2, 18, 10, 30, "Tokyo")

    synastry_aspects = SynastryAspects(john, yoko)

    # All aspects
    print(synastry_aspects.all_aspects)

    # Relevant aspects
    print(synastry_aspects.relevant_aspects)
