# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
    
    ⚠️  DEPRECATION NOTICE ⚠️
    
    This module is deprecated and maintained for backward compatibility only.
    
    The functionality has been moved to the unified AspectsFactory in aspects_factory.py.
    Please use:
    
    from kerykeion.aspects import AspectsFactory
    
    # Instead of:
    # synastry_aspects = SynastryAspectsFactory.from_subjects(first_subject, second_subject)
    
    # Use:
    # synastry_aspects = AspectsFactory.synastry_aspects(first_subject, second_subject)
    
    This module will be removed in a future version.
"""

import logging
from typing import Union, List, Optional

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_utils import get_aspect_from_two_points, get_active_points_list
from kerykeion.kr_types.kr_models import AstrologicalSubjectModel, AspectModel, ActiveAspect, CompositeSubjectModel, PlanetReturnModel, SynastryAspectsModel
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
    Factory class for creating synastry aspects analysis between two astrological subjects.

    This factory calculates all astrological aspects (angular relationships) between 
    planets and points in two different charts. It's primarily used for relationship 
    compatibility analysis, transit calculations, and comparative astrology.

    The factory provides both comprehensive aspect lists and filtered relevant aspects
    based on orb settings and chart axes considerations.

    Key Features:
        - Calculates all aspects between two subjects
        - Filters aspects based on orb thresholds
        - Applies stricter orb limits for chart axes (ASC, MC, DSC, IC)
        - Supports multiple subject types (natal, composite, planetary returns)

    Example:
        >>> john = AstrologicalSubjectFactory.from_birth_data("John", 1990, 1, 1, 12, 0, "London", "GB")
        >>> jane = AstrologicalSubjectFactory.from_birth_data("Jane", 1992, 6, 15, 14, 30, "Paris", "FR")
        >>> synastry = SynastryAspectsFactory.from_subjects(john, jane)
        >>> print(f"Found {len(synastry.relevant_aspects)} relevant aspects")
    """

    @staticmethod
    def from_subjects(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        *,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: Optional[List[ActiveAspect]] = None,
    ) -> SynastryAspectsModel:
        """
        Create synastry aspects analysis between two astrological subjects.

        This method calculates all astrological aspects (angular relationships)
        between planets and points in two different birth charts, commonly used
        for relationship compatibility analysis.

        Args:
            first_subject: The first astrological subject (person, composite chart, or planetary return)
            second_subject: The second astrological subject to compare with the first
            active_points: Optional list of celestial points to include in calculations.
                          If None, uses common points between both subjects.
            active_aspects: Optional list of aspect types with their orb settings.
                           If None, uses default aspect configuration.

        Returns:
            SynastryAspectsModel: Complete model containing all calculated aspects data,
                                 including both comprehensive and filtered relevant aspects.

        Example:
            >>> john = AstrologicalSubjectFactory.from_birth_data("John", 1990, 1, 1, 12, 0, "London", "GB")
            >>> jane = AstrologicalSubjectFactory.from_birth_data("Jane", 1992, 6, 15, 14, 30, "Paris", "FR")
            >>> synastry = SynastryAspectsFactory.from_subjects(john, jane)
            >>> print(f"Found {len(synastry.relevant_aspects)} relevant aspects")
        """
        # Initialize settings and configurations
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

        Args:
            first_subject: First astrological subject
            second_subject: Second astrological subject  
            active_points_resolved: Resolved list of active celestial points
            active_aspects_resolved: Resolved list of active aspects with orbs
            aspects_settings: Chart aspect configuration settings
            axes_orbit_settings: Orb threshold for chart axes
            celestial_points: Celestial points configuration

        Returns:
            SynastryAspectsModel: Complete model containing all aspects data
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

        This method performs comprehensive aspect calculations between all active points
        of both subjects, applying the specified orb settings and creating detailed
        aspect models with planet IDs and positional information.

        Args:
            first_subject: First astrological subject
            second_subject: Second astrological subject
            active_points: List of celestial points to include in calculations
            active_aspects: List of aspect types with their orb settings
            aspects_settings: Base aspect configuration settings
            celestial_points: Celestial points configuration with IDs

        Returns:
            List[AspectModel]: Complete list of all calculated aspect instances
        """
        # Get active points lists for both subjects
        first_active_points_list = get_active_points_list(first_subject, active_points)
        second_active_points_list = get_active_points_list(second_subject, active_points)

        # Create a lookup dictionary for planet IDs to optimize performance
        planet_id_lookup = {planet["name"]: planet["id"] for planet in celestial_points}

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
                    first_name = first_active_points_list[first]["name"]
                    second_name = second_active_points_list[second]["name"]
                    
                    # Get planet IDs using lookup dictionary for better performance
                    first_planet_id = planet_id_lookup.get(first_name, 0)
                    second_planet_id = planet_id_lookup.get(second_name, 0)

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
