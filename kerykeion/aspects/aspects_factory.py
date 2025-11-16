# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import logging
from typing import Union, List, Optional

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.aspects.aspects_utils import get_aspect_from_two_points, get_active_points_list, calculate_aspect_movement
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    AspectModel,
    ActiveAspect,
    CompositeSubjectModel,
    PlanetReturnModel,
    SingleChartAspectsModel,
    DualChartAspectsModel,
    # Legacy aliases for backward compatibility
    NatalAspectsModel,
    SynastryAspectsModel
)
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_ASPECTS
from kerykeion.settings.chart_defaults import (
    DEFAULT_CELESTIAL_POINTS_SETTINGS,
    DEFAULT_CHART_ASPECTS_SETTINGS,
)
from kerykeion.utilities import find_common_active_points

# Axes constants for orb filtering
AXES_LIST = [
    "Ascendant",
    "Medium_Coeli",
    "Descendant",
    "Imum_Coeli",
]


class AspectsFactory:
    """
    Unified factory class for creating both single chart and dual chart aspects analysis.

    This factory provides methods to calculate all aspects within a single chart or
    between two charts. It consolidates the common functionality between different
    types of aspect calculations while providing specialized methods for each type.

    The factory provides both comprehensive and filtered aspect lists based on orb settings
    and relevance criteria.

    Key Features:
        - Calculates aspects within a single chart (natal, returns, composite, etc.)
        - Calculates aspects between two charts (synastry, transits, comparisons, etc.)
        - Filters aspects based on orb thresholds
        - Applies stricter orb limits for chart axes (ASC, MC, DSC, IC)
        - Supports multiple subject types (natal, composite, planetary returns)

    Example:
        >>> # For single chart aspects (natal, returns, etc.)
        >>> johnny = AstrologicalSubjectFactory.from_birth_data("Johnny", 1963, 6, 9, 0, 0, "Owensboro", "US")
        >>> single_chart_aspects = AspectsFactory.single_chart_aspects(johnny)
        >>>
        >>> # For dual chart aspects (synastry, comparisons, etc.)
        >>> john = AstrologicalSubjectFactory.from_birth_data("John", 1990, 1, 1, 12, 0, "London", "GB")
        >>> jane = AstrologicalSubjectFactory.from_birth_data("Jane", 1992, 6, 15, 14, 30, "Paris", "FR")
        >>> dual_chart_aspects = AspectsFactory.dual_chart_aspects(john, jane)
    """

    @staticmethod
    def single_chart_aspects(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        *,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: Optional[List[ActiveAspect]] = None,
        axis_orb_limit: Optional[float] = None,
    ) -> SingleChartAspectsModel:
        """
        Create aspects analysis for a single astrological chart.

        This method calculates all astrological aspects (angular relationships)
        within a single chart. Can be used for any type of chart including:
        - Natal charts
        - Planetary return charts
        - Composite charts
        - Any other single chart type

        Args:
            subject: The astrological subject for aspect calculation

        Kwargs:
            active_points: List of points to include in calculations
            active_aspects: List of aspects with their orb settings
            axis_orb_limit: Optional orb threshold applied to chart axes; when None, no special axis filter

        Returns:
            SingleChartAspectsModel containing all calculated aspects data

        Example:
            >>> johnny = AstrologicalSubjectFactory.from_birth_data("Johnny", 1963, 6, 9, 0, 0, "Owensboro", "US")
            >>> chart_aspects = AspectsFactory.single_chart_aspects(johnny)
            >>> print(f"Found {len(chart_aspects.aspects)} aspects")
        """
        # Initialize settings and configurations
        celestial_points = DEFAULT_CELESTIAL_POINTS_SETTINGS
        aspects_settings = DEFAULT_CHART_ASPECTS_SETTINGS
        # Set active aspects with default fallback
        active_aspects_resolved = active_aspects if active_aspects is not None else DEFAULT_ACTIVE_ASPECTS

        # Determine active points to use
        if active_points is None:
            active_points_resolved = subject.active_points
        else:
            active_points_resolved = find_common_active_points(
                subject.active_points,
                active_points,
            )

        return AspectsFactory._create_single_chart_aspects_model(
            subject,
            active_points_resolved,
            active_aspects_resolved,
            aspects_settings,
            axis_orb_limit,
            celestial_points,
        )

    @staticmethod
    def dual_chart_aspects(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        *,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: Optional[List[ActiveAspect]] = None,
        axis_orb_limit: Optional[float] = None,
    ) -> DualChartAspectsModel:
        """
        Create aspects analysis between two astrological charts.

        This method calculates all astrological aspects (angular relationships)
        between planets and points in two different charts. Can be used for:
        - Synastry (relationship compatibility)
        - Transit comparisons
        - Composite vs natal comparisons
        - Any other dual chart analysis

        Args:
            first_subject: The first astrological subject
            second_subject: The second astrological subject to compare with the first

        Kwargs:
            active_points: Optional list of celestial points to include in calculations.
                          If None, uses common points between both subjects.
            active_aspects: Optional list of aspect types with their orb settings.
                           If None, uses default aspect configuration.
            axis_orb_limit: Optional orb threshold for chart axes (applied to single chart calculations only)

        Returns:
            DualChartAspectsModel: Complete model containing all calculated aspects data,
                                  including both comprehensive and filtered relevant aspects.

        Example:
            >>> john = AstrologicalSubjectFactory.from_birth_data("John", 1990, 1, 1, 12, 0, "London", "GB")
            >>> jane = AstrologicalSubjectFactory.from_birth_data("Jane", 1992, 6, 15, 14, 30, "Paris", "FR")
            >>> synastry = AspectsFactory.dual_chart_aspects(john, jane)
            >>> print(f"Found {len(synastry.aspects)} aspects")
        """
        # Initialize settings and configurations
        celestial_points = DEFAULT_CELESTIAL_POINTS_SETTINGS
        aspects_settings = DEFAULT_CHART_ASPECTS_SETTINGS
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

        return AspectsFactory._create_dual_chart_aspects_model(
            first_subject,
            second_subject,
            active_points_resolved,
            active_aspects_resolved,
            aspects_settings,
            axis_orb_limit,
            celestial_points,
        )

    @staticmethod
    def _create_single_chart_aspects_model(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points_resolved: List[AstrologicalPoint],
        active_aspects_resolved: List[ActiveAspect],
        aspects_settings: List[dict],
        axis_orb_limit: Optional[float],
        celestial_points: List[dict]
    ) -> SingleChartAspectsModel:
        """
        Create the complete single chart aspects model with all calculations.

        Returns:
            SingleChartAspectsModel containing filtered aspects data
        """
        all_aspects = AspectsFactory._calculate_single_chart_aspects(
            subject, active_points_resolved, active_aspects_resolved, aspects_settings, celestial_points
        )
        filtered_aspects = AspectsFactory._filter_relevant_aspects(
            all_aspects,
            axis_orb_limit,
            apply_axis_orb_filter=axis_orb_limit is not None,
        )

        return SingleChartAspectsModel(
            subject=subject,
            aspects=filtered_aspects,
            active_points=active_points_resolved,
            active_aspects=active_aspects_resolved,
        )

    @staticmethod
    def _create_dual_chart_aspects_model(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points_resolved: List[AstrologicalPoint],
        active_aspects_resolved: List[ActiveAspect],
        aspects_settings: List[dict],
        axis_orb_limit: Optional[float],
        celestial_points: List[dict]
    ) -> DualChartAspectsModel:
        """
        Create the complete dual chart aspects model with all calculations.

        Args:
            first_subject: First astrological subject
            second_subject: Second astrological subject
            active_points_resolved: Resolved list of active celestial points
            active_aspects_resolved: Resolved list of active aspects with orbs
            aspects_settings: Chart aspect configuration settings
            axis_orb_limit: Orb threshold for chart axes
            celestial_points: Celestial points configuration

        Returns:
            DualChartAspectsModel: Complete model containing filtered aspects data
        """
        all_aspects = AspectsFactory._calculate_dual_chart_aspects(
            first_subject, second_subject, active_points_resolved, active_aspects_resolved,
            aspects_settings, celestial_points
        )
        filtered_aspects = AspectsFactory._filter_relevant_aspects(
            all_aspects,
            axis_orb_limit,
            apply_axis_orb_filter=False,
        )

        return DualChartAspectsModel(
            first_subject=first_subject,
            second_subject=second_subject,
            aspects=filtered_aspects,
            active_points=active_points_resolved,
            active_aspects=active_aspects_resolved,
        )

    @staticmethod
    def _calculate_single_chart_aspects(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points: List[AstrologicalPoint],
        active_aspects: List[ActiveAspect],
        aspects_settings: List[dict],
        celestial_points: List[dict]
    ) -> List[AspectModel]:
        """
        Calculate all aspects within a single chart.

        This method handles all aspect calculations including settings updates,
        opposite pair filtering, and planet ID resolution for single charts.
        Works with any chart type (natal, return, composite, etc.).

        Returns:
            List of all calculated AspectModel instances
        """
        active_points_list = get_active_points_list(subject, active_points)

        # Update aspects settings with active aspects orbs
        filtered_settings = AspectsFactory._update_aspect_settings(aspects_settings, active_aspects)

        # Create a lookup dictionary for planet IDs to optimize performance
        planet_id_lookup = {planet["name"]: planet["id"] for planet in celestial_points}

        # Define opposite pairs that should be skipped for single chart aspects
        opposite_pairs = {
            ("Ascendant", "Descendant"),
            ("Descendant", "Ascendant"),
            ("Medium_Coeli", "Imum_Coeli"),
            ("Imum_Coeli", "Medium_Coeli"),
            ("True_North_Lunar_Node", "True_South_Lunar_Node"),
            ("Mean_North_Lunar_Node", "Mean_South_Lunar_Node"),
            ("True_South_Lunar_Node", "True_North_Lunar_Node"),
            ("Mean_South_Lunar_Node", "Mean_North_Lunar_Node"),
        }

        all_aspects_list = []

        for first in range(len(active_points_list)):
            # Generate aspects list without repetitions (single chart - same chart)
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
                    # Get planet IDs using lookup dictionary for better performance
                    first_planet_id = planet_id_lookup.get(first_name, 0)
                    second_planet_id = planet_id_lookup.get(second_name, 0)

                    # Determine aspect movement.
                    # If both points are chart axes, there is no meaningful
                    # dynamic movement between them, so we mark the aspect as
                    # "Fixed" regardless of any synthetic speeds.
                    if first_name in AXES_LIST and second_name in AXES_LIST:
                        aspect_movement = "Fixed"
                    else:
                        # Get speeds, fall back to 0.0 only if missing/None
                        first_speed = active_points_list[first].get("speed") or 0.0
                        second_speed = active_points_list[second].get("speed") or 0.0

                        # Calculate aspect movement (applying/separating/fixed)
                        aspect_movement = calculate_aspect_movement(
                            active_points_list[first]["abs_pos"],
                            active_points_list[second]["abs_pos"],
                            aspect["aspect_degrees"],
                            first_speed,
                            second_speed
                        )

                    aspect_model = AspectModel(
                        p1_name=first_name,
                        p1_owner=subject.name,
                        p1_abs_pos=active_points_list[first]["abs_pos"],
                        p2_name=second_name,
                        p2_owner=subject.name,
                        p2_abs_pos=active_points_list[second]["abs_pos"],
                        aspect=aspect["name"],
                        orbit=aspect["orbit"],
                        aspect_degrees=aspect["aspect_degrees"],
                        diff=aspect["diff"],
                        p1=first_planet_id,
                        p2=second_planet_id,
                        aspect_movement=aspect_movement,
                    )
                    all_aspects_list.append(aspect_model)

        return all_aspects_list

    @staticmethod
    def _calculate_dual_chart_aspects(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points: List[AstrologicalPoint],
        active_aspects: List[ActiveAspect],
        aspects_settings: List[dict],
        celestial_points: List[dict]
    ) -> List[AspectModel]:
        """
        Calculate all aspects between two charts.

        This method performs comprehensive aspect calculations between all active points
        of both subjects, applying the specified orb settings and creating detailed
        aspect models with planet IDs and positional information.
        Works with any chart types (synastry, transits, comparisons, etc.).

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
        filtered_settings = AspectsFactory._update_aspect_settings(aspects_settings, active_aspects)

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

                    # For aspects between axes (ASC, MC, DSC, IC) in different charts
                    # there is no meaningful dynamic movement between two house systems,
                    # so we mark the movement as "Fixed".
                    if first_name in AXES_LIST and second_name in AXES_LIST:
                        aspect_movement = "Fixed"
                    else:
                        # Get speeds, fall back to 0.0 only if missing/None
                        first_speed = first_active_points_list[first].get("speed") or 0.0
                        second_speed = second_active_points_list[second].get("speed") or 0.0

                        # Calculate aspect movement (applying/separating/fixed)
                        aspect_movement = calculate_aspect_movement(
                            first_active_points_list[first]["abs_pos"],
                            second_active_points_list[second]["abs_pos"],
                            aspect["aspect_degrees"],
                            first_speed,
                            second_speed
                        )

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
                        aspect_movement=aspect_movement,
                    )
                    all_aspects_list.append(aspect_model)

        return all_aspects_list

    @staticmethod
    def _update_aspect_settings(
        aspects_settings: List[dict],
        active_aspects: List[ActiveAspect]
    ) -> List[dict]:
        """
        Update aspects settings with active aspects orbs.

        This is a common utility method used by both single chart and dual chart calculations.

        Args:
            aspects_settings: Base aspect settings
            active_aspects: Active aspects with their orb configurations

        Returns:
            List of filtered and updated aspect settings
        """
        filtered_settings = []
        for aspect_setting in aspects_settings:
            for active_aspect in active_aspects:
                if aspect_setting["name"] == active_aspect["name"]:
                    aspect_setting = aspect_setting.copy()  # Don't modify original
                    aspect_setting["orb"] = active_aspect["orb"]
                    filtered_settings.append(aspect_setting)
                    break
        return filtered_settings

    @staticmethod
    def _filter_relevant_aspects(
        all_aspects: List[AspectModel],
        axis_orb_limit: Optional[float],
        *,
        apply_axis_orb_filter: bool,
    ) -> List[AspectModel]:
        """
        Filter aspects based on orb thresholds for axes and comprehensive criteria.

        This method consolidates all filtering logic including axes checks and orb thresholds
        for both single chart and dual chart aspects in a single comprehensive filtering method.

        Args:
            all_aspects: Complete list of calculated aspects
            axis_orb_limit: Optional orb threshold for axes aspects
            apply_axis_orb_filter: Whether to apply the axis-specific orb filtering logic

        Returns:
            Filtered list of relevant aspects
        """
        logging.debug("Calculating relevant aspects by filtering orbs...")

        relevant_aspects = []

        if not apply_axis_orb_filter or axis_orb_limit is None:
            return list(all_aspects)

        for aspect in all_aspects:
            # Check if aspect involves any of the chart axes and apply stricter orb limits
            aspect_involves_axes = (aspect.p1_name in AXES_LIST or aspect.p2_name in AXES_LIST)

            if aspect_involves_axes and abs(aspect.orbit) >= axis_orb_limit:
                continue

            relevant_aspects.append(aspect)

        return relevant_aspects

    # Legacy methods for temporary backward compatibility
    @staticmethod
    def natal_aspects(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        *,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: Optional[List[ActiveAspect]] = None,
        axis_orb_limit: Optional[float] = None,
    ) -> NatalAspectsModel:
        """
        Legacy method - use single_chart_aspects() instead.

        ⚠️  DEPRECATION WARNING ⚠️
        This method is deprecated. Use AspectsFactory.single_chart_aspects() instead.
        """
        return AspectsFactory.single_chart_aspects(
            subject,
            active_points=active_points,
            active_aspects=active_aspects,
            axis_orb_limit=axis_orb_limit,
        )

    @staticmethod
    def synastry_aspects(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        *,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: Optional[List[ActiveAspect]] = None,
        axis_orb_limit: Optional[float] = None,
    ) -> SynastryAspectsModel:
        """
        Legacy method - use dual_chart_aspects() instead.

        ⚠️  DEPRECATION WARNING ⚠️
        This method is deprecated. Use AspectsFactory.dual_chart_aspects() instead.
        """
        return AspectsFactory.dual_chart_aspects(
            first_subject,
            second_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            axis_orb_limit=axis_orb_limit,
        )


if __name__ == "__main__":
    from kerykeion.utilities import setup_logging

    setup_logging(level="debug")

    # Test single chart aspects (replaces natal aspects)
    johnny = AstrologicalSubjectFactory.from_birth_data("Johnny Depp", 1963, 6, 9, 0, 0, city="Owensboro", nation="US")
    single_chart_aspects = AspectsFactory.single_chart_aspects(johnny)
    print(f"Single chart aspects: {len(single_chart_aspects.aspects)}")

    # Test dual chart aspects (replaces synastry aspects)
    john = AstrologicalSubjectFactory.from_birth_data("John", 1940, 10, 9, 10, 30, "Liverpool", "GB")
    yoko = AstrologicalSubjectFactory.from_birth_data("Yoko", 1933, 2, 18, 10, 30, "Tokyo", "JP")
    dual_chart_aspects = AspectsFactory.dual_chart_aspects(john, yoko)
    print(f"Dual chart aspects: {len(dual_chart_aspects.aspects)}")
