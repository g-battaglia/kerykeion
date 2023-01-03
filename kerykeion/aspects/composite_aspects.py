"""
    This is part of Kerykeion (C) 2023 Giacomo Battaglia
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kerykeion import KrInstance
from pathlib import Path
from typing import Union

from kerykeion.aspects.natal_aspects import NatalAspects


class CompositeAspects(NatalAspects):
    """
    Generates an object with all the aspects between two persons.
    """

    def __init__(
        self,
        kr_object_one: KrInstance,
        kr_object_two: KrInstance,
        new_settings_file: Union[str, Path, None] = None,
    ):
        self.first_user = kr_object_one
        self.second_user = kr_object_two

        self.new_settings_file = new_settings_file
        self._parse_json_settings()

        if not hasattr(self.first_user, "sun"):
            self.first_user.__get_all()

        if not hasattr(self.second_user, "sun"):
            self.second_user.__get_all()

        self.first_init_point_list = (
            self.first_user.planets_list + self.first_user.houses_list
        )
        self.second_init_point_list = (
            self.second_user.planets_list + self.second_user.houses_list
        )

    def get_all_aspects(self):
        """
        Return all the aspects of the points in the natal chart in a dictionary,
        first all the individual aspects of each planet, second the aspects
        whitout repetitions.
        """

        f_1 = self.filter_by_settings(self.first_init_point_list)
        f_2 = self.filter_by_settings(self.second_init_point_list)

        self.all_aspects_list = []

        for first in range(len(f_1)):
            # Generates the aspects list whitout repetitions
            for second in range(len(f_2)):
                verdict, name, orbit, aspect_degrees, color, aid, diff = self.asp_calc(
                    f_1[first]["abs_pos"], f_2[second]["abs_pos"]
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
                        "p1": self.p_id_decoder(f_1[first]["name"]),
                        "p2": self.p_id_decoder(
                            f_2[second]["name"],
                        ),
                    }

                    self.all_aspects_list.append(d_asp)

        return self.all_aspects_list


if __name__ == "__main__":
    john = KrInstance("John", 1940, 10, 9, 10, 30, "Liverpool")
    yoko = KrInstance("Yoko", 1933, 2, 18, 10, 30, "Tokyo")

    composite_aspects = CompositeAspects(john, yoko)

    print(composite_aspects.get_all_aspects())