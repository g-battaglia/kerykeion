# -*- coding: utf-8 -*-
"""
Chart Data Factory Module

This module provides factory classes for creating comprehensive chart data models that include
all the pure data from astrological charts, including subjects, aspects, house comparisons,
and other analytical data without the visual rendering components.

This is designed to be the "pure data" counterpart to ChartDrawer, providing structured
access to all chart information for API consumption, data analysis, or other programmatic uses.

Key Features:
    - Comprehensive chart data including subjects and aspects
    - House comparison analysis for dual charts
    - Element and quality distributions
    - Relationship scoring for synastry charts
    - Flexible point and aspect filtering
    - Support for all chart types (Natal, Transit, Synastry, Composite, Return)

Classes:
    ElementDistributionModel: Model for element distribution analysis
    QualityDistributionModel: Model for quality distribution analysis
    SingleChartDataModel: Model for single-subject chart data
    DualChartDataModel: Model for dual-subject chart data
    ChartDataFactory: Factory for creating chart data models

Author: Giacomo Battaglia
Copyright: (C) 2025 Kerykeion Project
License: AGPL-3.0
"""

from typing import Mapping, Union, Optional, List, Literal, cast

from kerykeion.aspects import AspectsFactory
from kerykeion.house_comparison.house_comparison_factory import HouseComparisonFactory
from kerykeion.relationship_score_factory import RelationshipScoreFactory
from kerykeion.schemas import KerykeionException, ChartType, ActiveAspect
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    PlanetReturnModel,
    SingleChartAspectsModel,
    DualChartAspectsModel,
    ElementDistributionModel,
    QualityDistributionModel,
    SingleChartDataModel,
    DualChartDataModel,
    ChartDataModel,
)
from kerykeion.schemas.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.schemas.kr_literals import (
    AstrologicalPoint,
)
from kerykeion.utilities import find_common_active_points, distribute_percentages_to_100
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_ASPECTS
from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS
from kerykeion.charts.charts_utils import (
    ElementQualityDistributionMethod,
    calculate_element_points,
    calculate_quality_points,
    calculate_synastry_element_points,
    calculate_synastry_quality_points,
)


class ChartDataFactory:
    """
    Factory class for creating comprehensive chart data models.

    This factory creates ChartDataModel instances containing all the pure data
    from astrological charts, including subjects, aspects, house comparisons,
    and analytical metrics. It provides the structured data equivalent of
    ChartDrawer's visual output.

    The factory handles all chart types and automatically includes relevant
    analyses based on chart type (e.g., house comparison for dual charts,
    relationship scoring for synastry charts).

    Example:
        >>> # Create natal chart data
        >>> john = AstrologicalSubjectFactory.from_birth_data("John", 1990, 1, 1, 12, 0, "London", "GB")
        >>> natal_data = ChartDataFactory.create_chart_data("Natal", john)
        >>> print(f"Elements: Fire {natal_data.element_distribution.fire_percentage}%")
        >>>
        >>> # Create synastry chart data
        >>> jane = AstrologicalSubjectFactory.from_birth_data("Jane", 1992, 6, 15, 14, 30, "Paris", "FR")
        >>> synastry_data = ChartDataFactory.create_chart_data("Synastry", john, jane)
        >>> print(f"Relationship score: {synastry_data.relationship_score.score_value}")
    """

    @staticmethod
    def create_chart_data(
        chart_type: ChartType,
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Optional[Union[AstrologicalSubjectModel, PlanetReturnModel]] = None,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        include_house_comparison: bool = True,
        include_relationship_score: bool = False,
        *,
        axis_orb_limit: Optional[float] = None,
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Create comprehensive chart data for the specified chart type.

        Args:
            chart_type: Type of chart to create data for
            first_subject: Primary astrological subject
            second_subject: Secondary subject (required for dual charts)
            active_points: Points to include in calculations (defaults to first_subject.active_points)
            active_aspects: Aspect types and orbs to use
            include_house_comparison: Whether to include house comparison for dual charts
            include_relationship_score: Whether to include relationship scoring for synastry
            axis_orb_limit: Optional orb threshold for chart axes (applies only to single chart aspects)
            distribution_method: Strategy for element/modality weighting ("pure_count" or "weighted")
            custom_distribution_weights: Optional overrides for the distribution weights

        Returns:
            ChartDataModel: Comprehensive chart data model

        Raises:
            KerykeionException: If chart type requirements are not met
        """

        # Validate chart type requirements
        if chart_type in ["Transit", "Synastry", "DualReturnChart"] and not second_subject:
            raise KerykeionException(f"Second subject is required for {chart_type} charts.")

        if chart_type == "Composite" and not isinstance(first_subject, CompositeSubjectModel):
            raise KerykeionException("First subject must be a CompositeSubjectModel for Composite charts.")

        if chart_type == "Return" and not isinstance(second_subject, PlanetReturnModel):
            raise KerykeionException("Second subject must be a PlanetReturnModel for Return charts.")

        if chart_type == "SingleReturnChart" and not isinstance(first_subject, PlanetReturnModel):
            raise KerykeionException("First subject must be a PlanetReturnModel for SingleReturnChart charts.")

        # Determine active points
        if not active_points:
            effective_active_points = first_subject.active_points
        else:
            effective_active_points = find_common_active_points(active_points, first_subject.active_points)

        # For dual charts, further filter by second subject's active points
        if second_subject:
            effective_active_points = find_common_active_points(effective_active_points, second_subject.active_points)

        # Calculate aspects based on chart type
        aspects_model: Union[SingleChartAspectsModel, DualChartAspectsModel]
        if chart_type in ["Natal", "Composite", "SingleReturnChart"]:
            # Single chart aspects
            aspects_model = AspectsFactory.single_chart_aspects(
                first_subject,
                active_points=effective_active_points,
                active_aspects=active_aspects,
                axis_orb_limit=axis_orb_limit,
            )
        else:
            # Dual chart aspects - second_subject is guaranteed to exist here due to validation above
            if second_subject is None:
                raise KerykeionException(f"Second subject is required for {chart_type} charts.")

            # Determine if subjects are fixed based on chart type
            first_subject_is_fixed = False
            second_subject_is_fixed = False

            if chart_type == "Synastry":
                first_subject_is_fixed = True
                second_subject_is_fixed = True
            elif chart_type == "Transit":
                first_subject_is_fixed = True  # Natal chart is fixed
                second_subject_is_fixed = False  # Transit chart is moving
            elif chart_type == "DualReturnChart":
                first_subject_is_fixed = True  # Natal chart is fixed
                second_subject_is_fixed = False  # Return chart is moving (like transits)

            aspects_model = AspectsFactory.dual_chart_aspects(
                first_subject,
                second_subject,
                active_points=effective_active_points,
                active_aspects=active_aspects,
                axis_orb_limit=axis_orb_limit,
                first_subject_is_fixed=first_subject_is_fixed,
                second_subject_is_fixed=second_subject_is_fixed,
            )

        # Calculate house comparison for dual charts
        house_comparison = None
        if second_subject and include_house_comparison and chart_type in ["Transit", "Synastry", "DualReturnChart"]:
            if isinstance(first_subject, AstrologicalSubjectModel) and isinstance(
                second_subject, (AstrologicalSubjectModel, PlanetReturnModel)
            ):
                house_comparison_factory = HouseComparisonFactory(
                    first_subject, second_subject, active_points=effective_active_points
                )
                house_comparison = house_comparison_factory.get_house_comparison()

        # Calculate relationship score for synastry
        relationship_score = None
        if chart_type == "Synastry" and include_relationship_score and second_subject:
            if isinstance(first_subject, AstrologicalSubjectModel) and isinstance(
                second_subject, AstrologicalSubjectModel
            ):
                relationship_score_factory = RelationshipScoreFactory(
                    first_subject,
                    second_subject,
                    axis_orb_limit=axis_orb_limit,
                )
                relationship_score = relationship_score_factory.get_relationship_score()

        # Calculate element and quality distributions
        available_planets_setting_dicts: list[dict[str, object]] = []
        for body in DEFAULT_CELESTIAL_POINTS_SETTINGS:
            if body["name"] in effective_active_points:
                body_dict = dict(body)
                body_dict["is_active"] = True
                available_planets_setting_dicts.append(body_dict)

        # Convert to models for type safety
        available_planets_setting: list[KerykeionSettingsCelestialPointModel] = [
            KerykeionSettingsCelestialPointModel(**body)  # type: ignore[arg-type]
            for body in available_planets_setting_dicts
        ]

        celestial_points_names = [body.name.lower() for body in available_planets_setting]

        if chart_type == "Synastry" and second_subject:
            # Calculate combined element/quality points for synastry
            # Type narrowing: ensure both subjects are AstrologicalSubjectModel for synastry
            if isinstance(first_subject, AstrologicalSubjectModel) and isinstance(
                second_subject, AstrologicalSubjectModel
            ):
                element_totals = calculate_synastry_element_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    second_subject,
                    method=distribution_method,
                    custom_weights=custom_distribution_weights,
                )
                quality_totals = calculate_synastry_quality_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    second_subject,
                    method=distribution_method,
                    custom_weights=custom_distribution_weights,
                )
            else:
                # Fallback to single chart calculation for incompatible types
                element_totals = calculate_element_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    method=distribution_method,
                    custom_weights=custom_distribution_weights,
                )
                quality_totals = calculate_quality_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    method=distribution_method,
                    custom_weights=custom_distribution_weights,
                )
        else:
            # Calculate element/quality points for single chart
            element_totals = calculate_element_points(
                available_planets_setting,
                celestial_points_names,
                first_subject,
                method=distribution_method,
                custom_weights=custom_distribution_weights,
            )
            quality_totals = calculate_quality_points(
                available_planets_setting,
                celestial_points_names,
                first_subject,
                method=distribution_method,
                custom_weights=custom_distribution_weights,
            )

        # Calculate percentages
        total_elements = (
            element_totals["fire"] + element_totals["water"] + element_totals["earth"] + element_totals["air"]
        )
        element_percentages = (
            distribute_percentages_to_100(element_totals)
            if total_elements > 0
            else {"fire": 0, "earth": 0, "air": 0, "water": 0}
        )
        element_distribution = ElementDistributionModel(
            fire=element_totals["fire"],
            earth=element_totals["earth"],
            air=element_totals["air"],
            water=element_totals["water"],
            fire_percentage=element_percentages["fire"],
            earth_percentage=element_percentages["earth"],
            air_percentage=element_percentages["air"],
            water_percentage=element_percentages["water"],
        )

        total_qualities = quality_totals["cardinal"] + quality_totals["fixed"] + quality_totals["mutable"]
        quality_percentages = (
            distribute_percentages_to_100(quality_totals)
            if total_qualities > 0
            else {"cardinal": 0, "fixed": 0, "mutable": 0}
        )
        quality_distribution = QualityDistributionModel(
            cardinal=quality_totals["cardinal"],
            fixed=quality_totals["fixed"],
            mutable=quality_totals["mutable"],
            cardinal_percentage=quality_percentages["cardinal"],
            fixed_percentage=quality_percentages["fixed"],
            mutable_percentage=quality_percentages["mutable"],
        )

        # Create and return the appropriate chart data model
        if chart_type in ["Natal", "Composite", "SingleReturnChart"]:
            # Single chart data model - cast types since they're already validated
            return SingleChartDataModel(
                chart_type=cast(Literal["Natal", "Composite", "SingleReturnChart"], chart_type),
                subject=first_subject,
                aspects=cast(SingleChartAspectsModel, aspects_model).aspects,
                element_distribution=element_distribution,
                quality_distribution=quality_distribution,
                active_points=effective_active_points,
                active_aspects=active_aspects,
            )
        else:
            # Dual chart data model - cast types since they're already validated
            if second_subject is None:
                raise KerykeionException(f"Second subject is required for {chart_type} charts.")
            return DualChartDataModel(
                chart_type=cast(Literal["Transit", "Synastry", "DualReturnChart"], chart_type),
                first_subject=first_subject,
                second_subject=second_subject,
                aspects=cast(DualChartAspectsModel, aspects_model).aspects,
                house_comparison=house_comparison,
                relationship_score=relationship_score,
                element_distribution=element_distribution,
                quality_distribution=quality_distribution,
                active_points=effective_active_points,
                active_aspects=active_aspects,
            )

    @staticmethod
    def create_natal_chart_data(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        *,
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating natal chart data.

        Args:
            subject: Astrological subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            distribution_method: Strategy for element/modality weighting
            custom_distribution_weights: Optional overrides for distribution weights

        Returns:
            ChartDataModel: Natal chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=subject,
            chart_type="Natal",
            active_points=active_points,
            active_aspects=active_aspects,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_synastry_chart_data(
        first_subject: AstrologicalSubjectModel,
        second_subject: AstrologicalSubjectModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        include_house_comparison: bool = True,
        include_relationship_score: bool = True,
        *,
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating synastry chart data.

        Args:
            first_subject: First astrological subject
            second_subject: Second astrological subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            include_house_comparison: Whether to include house comparison
            include_relationship_score: Whether to include relationship scoring
            distribution_method: Strategy for element/modality weighting
            custom_distribution_weights: Optional overrides for distribution weights

        Returns:
            ChartDataModel: Synastry chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=first_subject,
            chart_type="Synastry",
            second_subject=second_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            include_house_comparison=include_house_comparison,
            include_relationship_score=include_relationship_score,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_transit_chart_data(
        natal_subject: AstrologicalSubjectModel,
        transit_subject: AstrologicalSubjectModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        include_house_comparison: bool = True,
        *,
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating transit chart data.

        Args:
            natal_subject: Natal astrological subject
            transit_subject: Transit astrological subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            include_house_comparison: Whether to include house comparison
            distribution_method: Strategy for element/modality weighting
            custom_distribution_weights: Optional overrides for distribution weights

        Returns:
            ChartDataModel: Transit chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=natal_subject,
            chart_type="Transit",
            second_subject=transit_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            include_house_comparison=include_house_comparison,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_composite_chart_data(
        composite_subject: CompositeSubjectModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        *,
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating composite chart data.

        Args:
            composite_subject: Composite astrological subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            distribution_method: Strategy for element/modality weighting
            custom_distribution_weights: Optional overrides for distribution weights

        Returns:
            ChartDataModel: Composite chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=composite_subject,
            chart_type="Composite",
            active_points=active_points,
            active_aspects=active_aspects,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_return_chart_data(
        natal_subject: AstrologicalSubjectModel,
        return_subject: PlanetReturnModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        include_house_comparison: bool = True,
        *,
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating planetary return chart data.

        Args:
            natal_subject: Natal astrological subject
            return_subject: Planetary return subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            include_house_comparison: Whether to include house comparison
            distribution_method: Strategy for element/modality weighting
            custom_distribution_weights: Optional overrides for distribution weights

        Returns:
            ChartDataModel: Return chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=natal_subject,
            chart_type="DualReturnChart",
            second_subject=return_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            include_house_comparison=include_house_comparison,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_single_wheel_return_chart_data(
        return_subject: PlanetReturnModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        *,
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating single wheel planetary return chart data.

        Args:
            return_subject: Planetary return subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            distribution_method: Strategy for element/modality weighting
            custom_distribution_weights: Optional overrides for distribution weights

        Returns:
            ChartDataModel: Single wheel return chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=return_subject,
            chart_type="SingleReturnChart",
            active_points=active_points,
            active_aspects=active_aspects,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )


if __name__ == "__main__":
    # Example usage
    from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

    # Create a natal chart data
    subject = AstrologicalSubjectFactory.from_current_time(name="Test Subject")
    natal_data = ChartDataFactory.create_natal_chart_data(subject)

    print(f"Chart Type: {natal_data.chart_type}")
    print(f"Active Points: {len(natal_data.active_points)}")
    print(f"Aspects: {len(natal_data.aspects)}")
    print(f"Fire: {natal_data.element_distribution.fire_percentage}%")
    print(f"Earth: {natal_data.element_distribution.earth_percentage}%")
    print(f"Air: {natal_data.element_distribution.air_percentage}%")
    print(f"Water: {natal_data.element_distribution.water_percentage}%")

    print("\n---\n")
    print(natal_data.model_dump_json(indent=4))
