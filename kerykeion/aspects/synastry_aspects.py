# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import logging
from pathlib import Path
from typing import Union, List, Optional

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.settings.kerykeion_settings import get_settings
from kerykeion.aspects.aspects_utils import get_aspect_from_two_points, get_active_points_list
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel, AspectModel, ActiveAspect, CompositeSubjectModel, PlanetReturnModel, SynastryAspectsModel
from kerykeion.kr_types.settings_models import KerykeionSettingsModel
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_ASPECTS, DEFAULT_AXIS_ORBIT
from kerykeion.settings.legacy.legacy_celestial_points_settings import DEFAULT_CELESTIAL_POINTS_SETTINGS
from kerykeion.settings.legacy.legacy_chart_aspects_settings import DEFAULT_CHART_ASPECTS_SETTINGS
from kerykeion.kr_types.kr_literals import AstrologicalPoint
from kerykeion.utilities import find_common_active_points


# Axes constants for orb filtering
AXES_LIST = [
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
]


class SynastryAspectsFactory:
    """
    Factory class for creating synastry aspects analysis between two subjects.

    This factory calculates all aspects between two charts and provides both
    comprehensive and filtered aspect lists based on orb settings and relevance.
    """

    @staticmethod
    def from_subjects(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        new_settings_file: Union[Path, KerykeionSettingsModel, dict, None] = None,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: Optional[List[ActiveAspect]] = None,
    ) -> SynastryAspectsModel:
        """
        Create synastry aspects analysis from two existing astrological subjects.

        Args:
            first_subject: The first astrological subject
            second_subject: The second astrological subject
            new_settings_file: Custom settings file or settings model
            active_points: List of points to include in calculations
            active_aspects: List of aspects with their orb settings

        Returns:
            SynastryAspectsModel containing all calculated aspects data
        """
        # Initialize settings and configurations
        settings = get_settings(new_settings_file)
        celestial_points = DEFAULT_CELESTIAL_POINTS_SETTINGS
        aspects_settings = DEFAULT_CHART_ASPECTS_SETTINGS
        axes_orbit_settings = DEFAULT_AXIS_ORBIT

        # Set active aspects with default fallback
        active_aspects_resolved = active_aspects if active_aspects is not None else DEFAULT_ACTIVE_ASPECTS

        # Determine active points to use - find common points between both subjects
        if active_points is None:
            active_points_resolved = first_subject.active_points
        else:
            active_points_resolved = find_common_active_points(
                first_subject.active_points,
                active_points,
            )

        # Further filter with second subject's active points
        active_points_resolved = find_common_active_points(
            second_subject.active_points,
            active_points_resolved,
        )

        return SynastryAspectsFactory._create_synastry_aspects_model(
            first_subject, second_subject, active_points_resolved, active_aspects_resolved,
            aspects_settings, axes_orbit_settings, celestial_points
        )

    @staticmethod
    def _create_synastry_aspects_model(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points_resolved: List[AstrologicalPoint],
        active_aspects_resolved: List[ActiveAspect],
        aspects_settings: List[dict],
        axes_orbit_settings: float,
        celestial_points: List[dict]
    ) -> SynastryAspectsModel:
        """
        Create the complete synastry aspects model with all calculations.

        Returns:
            SynastryAspectsModel containing all aspects data
        """
        all_aspects = SynastryAspectsFactory._calculate_all_aspects(
            first_subject, second_subject, active_points_resolved, active_aspects_resolved,
            aspects_settings, celestial_points
        )
        relevant_aspects = SynastryAspectsFactory._filter_relevant_aspects(all_aspects, axes_orbit_settings)

        return SynastryAspectsModel(
            first_subject=first_subject,
            second_subject=second_subject,
            all_aspects=all_aspects,
            relevant_aspects=relevant_aspects,
            active_points=active_points_resolved,
            active_aspects=active_aspects_resolved,
        )

    @staticmethod
    def _calculate_all_aspects(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points: List[AstrologicalPoint],
        active_aspects: List[ActiveAspect],
        aspects_settings: List[dict],
        celestial_points: List[dict]
    ) -> List[AspectModel]:
        """
        Calculate all synastry aspects between two subjects.

        This method handles all aspect calculations including settings updates
        and planet ID resolution in a single comprehensive method.

        Returns:
            List of all calculated AspectModel instances
        """
        # Get active points lists for both subjects
        first_active_points_list = get_active_points_list(first_subject, active_points)
        second_active_points_list = get_active_points_list(second_subject, active_points)

        # Update aspects settings with active aspects orbs
        filtered_settings = []
        for aspect_setting in aspects_settings:
            for active_aspect in active_aspects:
                if aspect_setting["name"] == active_aspect["name"]:
                    aspect_setting = aspect_setting.copy()  # Don't modify original
                    aspect_setting["orb"] = active_aspect["orb"]
                    filtered_settings.append(aspect_setting)
                    break

        all_aspects_list = []
        for first in range(len(first_active_points_list)):
            # Generate aspects list between all points of first and second subjects
            for second in range(len(second_active_points_list)):
                aspect = get_aspect_from_two_points(
                    filtered_settings,
                    first_active_points_list[first]["abs_pos"],
                    second_active_points_list[second]["abs_pos"],
                )

                if aspect["verdict"]:
                    # Get planet IDs directly from celestial points settings
                    first_planet_id = 0
                    second_planet_id = 0

                    first_name = first_active_points_list[first]["name"]
                    second_name = second_active_points_list[second]["name"]

                    for planet in celestial_points:
                        if planet["name"] == first_name:
                            first_planet_id = planet["id"]
                        if planet["name"] == second_name:
                            second_planet_id = planet["id"]

                    aspect_model = AspectModel(
                        p1_name=first_name,
                        p1_owner=first_subject.name,
                        p1_abs_pos=first_active_points_list[first]["abs_pos"],
                        p2_name=second_name,
                        p2_owner=second_subject.name,
                        p2_abs_pos=second_active_points_list[second]["abs_pos"],
                        aspect=aspect["name"],
                        orbit=aspect["orbit"],
                        aspect_degrees=aspect["aspect_degrees"],
                        diff=aspect["diff"],
                        p1=first_planet_id,
                        p2=second_planet_id,
                    )
                    all_aspects_list.append(aspect_model)

        return all_aspects_list

    @staticmethod
    def _filter_relevant_aspects(all_aspects: List[AspectModel], axes_orbit_settings: float) -> List[AspectModel]:
        """
        Filter aspects based on orb thresholds for axes and comprehensive criteria.

        This method consolidates all filtering logic including axes checks and orb thresholds
        for synastry aspects in a single comprehensive filtering method.

        Args:
            all_aspects: Complete list of calculated aspects
            axes_orbit_settings: Orb threshold for axes aspects

        Returns:
            Filtered list of relevant aspects
        """
        logging.debug("Calculating relevant synastry aspects by filtering orbs...")

        relevant_aspects = []

        for aspect in all_aspects:
            # Check if aspect involves any of the chart axes and apply stricter orb limits
            aspect_involves_axes = (aspect.p1_name in AXES_LIST or aspect.p2_name in AXES_LIST)

            if aspect_involves_axes and abs(aspect.orbit) >= axes_orbit_settings:
                continue

            relevant_aspects.append(aspect)

        return relevant_aspects


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging

    setup_logging(level="debug")

    john = AstrologicalSubjectFactory.from_birth_data("John", 1940, 10, 9, 10, 30, "Liverpool", "GB")
    yoko = AstrologicalSubjectFactory.from_birth_data("Yoko", 1933, 2, 18, 10, 30, "Tokyo", "JP")

    # Create synastry aspects analysis using the factory
    synastry_aspects_model = SynastryAspectsFactory.from_subjects(john, yoko)
    print(f"All synastry aspects: {len(synastry_aspects_model.all_aspects)}")
    print(f"Relevant synastry aspects: {len(synastry_aspects_model.relevant_aspects)}")
