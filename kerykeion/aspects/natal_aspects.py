# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from pathlib import Path
from kerykeion import AstrologicalSubject
from kerykeion.kr_types import CompositeSubjectModel
import logging
from typing import Union, List
from kerykeion.settings.kerykeion_settings import get_settings
from dataclasses import dataclass, field
from functools import cached_property
from kerykeion.aspects.aspects_utils import planet_id_decoder, get_aspect_from_two_points, get_active_points_list
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel, AspectModel, ActiveAspect
from kerykeion.kr_types.kr_literals import AxialCusps, Planet
from kerykeion.kr_types.settings_models import KerykeionSettingsModel
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, DEFAULT_ACTIVE_ASPECTS



AXES_LIST = [
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
]


@dataclass
class NatalAspects:
    """
    Generates an object with all the aspects of a birthcart.
    """

    user: Union[AstrologicalSubject, AstrologicalSubjectModel, CompositeSubjectModel]
    new_settings_file: Union[Path, KerykeionSettingsModel, dict, None] = None
    active_points: List[Union[AxialCusps, Planet]] = field(default_factory=lambda: DEFAULT_ACTIVE_POINTS)
    active_aspects: List[ActiveAspect] = field(default_factory=lambda: DEFAULT_ACTIVE_ASPECTS)

    def __post_init__(self):
        self.settings = get_settings(self.new_settings_file)

        self.celestial_points = self.settings.celestial_points
        self.aspects_settings = self.settings.aspects
        self.axes_orbit_settings = self.settings.general_settings.axes_orbit
        self.active_points = self.active_points

    @cached_property
    def all_aspects(self):
        """
        Return all the aspects of the points in the natal chart in a dictionary,
        first all the individual aspects of each planet, second the aspects
        without repetitions.
        """

        active_points_list = get_active_points_list(self.user, self.settings, self.active_points)

        # ---> TODO: Clean this up
        filtered_settings = []
        for a in self.aspects_settings:
            for aspect in self.active_aspects:
                if a["name"] == aspect["name"]:
                    a["orb"] = aspect["orb"]  # Assign the aspect's orb
                    filtered_settings.append(a)
                    break  # Exit the inner loop once a match is found
        self.aspects_settings = filtered_settings
        # <--- TODO: Clean this up

        self.all_aspects_list = []
        for first in range(len(active_points_list)):
            # Generates the aspects list without repetitions
            for second in range(first + 1, len(active_points_list)):
                # AC/DC, MC/IC and North/South nodes are always in opposition
                opposite_pairs = {
                    ("Ascendant", "Descendant"),
                    ("Descendant", "Ascendant"),
                    ("Medium_Coeli", "Imum_Coeli"),
                    ("Imum_Coeli", "Medium_Coeli"),
                    ("True_Node", "True_South_Node"),
                    ("Mean_Node", "Mean_South_Node"),
                    ("True_South_Node", "True_Node"),
                    ("Mean_South_Node", "Mean_Node"),
                }
                if (active_points_list[first]["name"], active_points_list[second]["name"]) in opposite_pairs:
                    continue

                aspect = get_aspect_from_two_points(
                    self.aspects_settings,
                    active_points_list[first]["abs_pos"],
                    active_points_list[second]["abs_pos"]
                )

                verdict = aspect["verdict"]
                name = aspect["name"]
                orbit = aspect["orbit"]
                aspect_degrees = aspect["aspect_degrees"]
                diff = aspect["diff"]

                if verdict == True:
                    aspect_model = AspectModel(
                        p1_name=active_points_list[first]["name"],
                        p1_owner=self.user.name,
                        p1_abs_pos=active_points_list[first]["abs_pos"],
                        p2_name=active_points_list[second]["name"],
                        p2_owner=self.user.name,
                        p2_abs_pos=active_points_list[second]["abs_pos"],
                        aspect=name,
                        orbit=orbit,
                        aspect_degrees=aspect_degrees,
                        diff=diff,
                        p1=planet_id_decoder(self.celestial_points, active_points_list[first]["name"]),
                        p2=planet_id_decoder(self.celestial_points, active_points_list[second]["name"]),
                    )
                    self.all_aspects_list.append(aspect_model)

        return self.all_aspects_list

    @cached_property
    def relevant_aspects(self):
        """
        Filters the aspects list with the desired points, in this case
        the most important are hardcoded.
        Set the list with set_points and creating a list with the names
        or the numbers of the houses.
        The relevant aspects are the ones that are set as looping in the available_aspects list.
        """

        logging.debug("Relevant aspects not already calculated, calculating now...")
        self.all_aspects

        axes_list = AXES_LIST
        counter = 0

        # Remove aspects where the orbits exceed the maximum orb thresholds specified in the settings
        # (specified usually in kr.config.json file)
        aspects_filtered = self.all_aspects
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

    # All aspects as a list of dictionaries
    aspects = NatalAspects(johnny)
    #print([a.model_dump() for a in aspects.all_aspects])

    print("\n")

    # Relevant aspects as a list of dictionaries
    aspects = NatalAspects(johnny)
    print([a.model_dump() for a in aspects.relevant_aspects])
