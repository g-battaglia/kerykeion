# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import logging
from typing import Union, List, Optional

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_utils import get_aspect_from_two_points, get_active_points_list
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel, AspectModel, ActiveAspect, CompositeSubjectModel, PlanetReturnModel, NatalAspectsModel
from kerykeion.kr_types.kr_literals import AstrologicalPoint
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_ASPECTS, DEFAULT_AXIS_ORBIT
from kerykeion.settings.legacy.legacy_celestial_points_settings import DEFAULT_CELESTIAL_POINTS_SETTINGS
from kerykeion.settings.legacy.legacy_chart_aspects_settings import DEFAULT_CHART_ASPECTS_SETTINGS
from kerykeion.utilities import find_common_active_points

# Axes constants for orb filtering
AXES_LIST = [
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
]


class NatalAspectsFactory:
    """
    Factory class for creating natal aspects analysis.

    This factory calculates all aspects in a birth chart and provides both
    comprehensive and filtered aspect lists based on orb settings and relevance.
    """

    @staticmethod
    def from_subject(
        user: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        *,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: Optional[List[ActiveAspect]] = None,
    ) -> NatalAspectsModel:
        """
        Create natal aspects analysis from an existing astrological subject.

        Args:
            user: The astrological subject for aspect calculation

        Kwargs:
            active_points: List of points to include in calculations
            active_aspects: List of aspects with their orb settings

        Returns:
            NatalAspectsModel containing all calculated aspects data
        """
        # Initialize settings and configurations
        celestial_points = DEFAULT_CELESTIAL_POINTS_SETTINGS
        aspects_settings = DEFAULT_CHART_ASPECTS_SETTINGS
        axes_orbit_settings = DEFAULT_AXIS_ORBIT

        # Set active aspects with default fallback
        active_aspects_resolved = active_aspects if active_aspects is not None else DEFAULT_ACTIVE_ASPECTS

        # Determine active points to use
        if active_points is None:
            active_points_resolved = user.active_points
        else:
            active_points_resolved = find_common_active_points(
                user.active_points,
                active_points,
            )

        return NatalAspectsFactory._create_natal_aspects_model(
            user, active_points_resolved, active_aspects_resolved,
            aspects_settings, axes_orbit_settings, celestial_points
        )

    @staticmethod
    def _create_natal_aspects_model(
        user: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points_resolved: List[AstrologicalPoint],
        active_aspects_resolved: List[ActiveAspect],
        aspects_settings: List[dict],
        axes_orbit_settings: float,
        celestial_points: List[dict]
    ) -> NatalAspectsModel:
        """
        Create the complete natal aspects model with all calculations.

        Returns:
            NatalAspectsModel containing all aspects data
        """
        all_aspects = NatalAspectsFactory._calculate_all_aspects(
            user, active_points_resolved, active_aspects_resolved, aspects_settings, celestial_points
        )
        relevant_aspects = NatalAspectsFactory._filter_relevant_aspects(all_aspects, axes_orbit_settings)

        return NatalAspectsModel(
            subject=user,
            all_aspects=all_aspects,
            relevant_aspects=relevant_aspects,
            active_points=active_points_resolved,
            active_aspects=active_aspects_resolved,
        )

    @staticmethod
    def _calculate_all_aspects(
        user: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points: List[AstrologicalPoint],
        active_aspects: List[ActiveAspect],
        aspects_settings: List[dict],
        celestial_points: List[dict]
    ) -> List[AspectModel]:
        """
        Calculate all aspects between active points in the natal chart.

        This method handles all aspect calculations including settings updates,
        opposite pair filtering, and planet ID resolution in a single comprehensive method.

        Returns:
            List of all calculated AspectModel instances
        """
        active_points_list = get_active_points_list(user, active_points)

        # Update aspects settings with active aspects orbs
        filtered_settings = []
        for aspect_setting in aspects_settings:
            for active_aspect in active_aspects:
                if aspect_setting["name"] == active_aspect["name"]:
                    aspect_setting = aspect_setting.copy()  # Don't modify original
                    aspect_setting["orb"] = active_aspect["orb"]
                    filtered_settings.append(aspect_setting)
                    break

        # Define opposite pairs that should be skipped
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

        all_aspects_list = []

        for first in range(len(active_points_list)):
            # Generate aspects list without repetitions
            for second in range(first + 1, len(active_points_list)):
                # Skip predefined opposite pairs (AC/DC, MC/IC, North/South nodes)
                first_name = active_points_list[first]["name"]
                second_name = active_points_list[second]["name"]

                if (first_name, second_name) in opposite_pairs:
                    continue

                aspect = get_aspect_from_two_points(
                    filtered_settings,
                    active_points_list[first]["abs_pos"],
                    active_points_list[second]["abs_pos"]
                )

                if aspect["verdict"]:
                    # Get planet IDs directly from celestial points settings
                    first_planet_id = 0
                    second_planet_id = 0

                    for planet in celestial_points:
                        if planet["name"] == first_name:
                            first_planet_id = planet["id"]
                        if planet["name"] == second_name:
                            second_planet_id = planet["id"]

                    aspect_model = AspectModel(
                        p1_name=first_name,
                        p1_owner=user.name,
                        p1_abs_pos=active_points_list[first]["abs_pos"],
                        p2_name=second_name,
                        p2_owner=user.name,
                        p2_abs_pos=active_points_list[second]["abs_pos"],
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
        Filter aspects based on orb thresholds for axes and other comprehensive criteria.

        This method consolidates all filtering logic including axes checks and orb thresholds
        into a single comprehensive filtering method.

        Args:
            all_aspects: Complete list of calculated aspects
            axes_orbit_settings: Orb threshold for axes aspects

        Returns:
            Filtered list of relevant aspects
        """
        logging.debug("Calculating relevant aspects by filtering orbs...")

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

    # Create subject using AstrologicalSubjectFactory
    johnny = AstrologicalSubjectFactory.from_birth_data("Johnny Depp", 1963, 6, 9, 0, 0, city="Owensboro", nation="US")

    # Create aspects analysis from subject
    natal_aspects = NatalAspectsFactory.from_subject(johnny)
    print(f"All aspects count: {len(natal_aspects.all_aspects)}")
    print(f"Relevant aspects count: {len(natal_aspects.relevant_aspects)}")
