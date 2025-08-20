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

from typing import Union, Optional, List, Literal, cast

from kerykeion.aspects import AspectsFactory
from kerykeion.house_comparison.house_comparison_factory import HouseComparisonFactory
from kerykeion.relationship_score_factory import RelationshipScoreFactory
from kerykeion.schemas import (
    KerykeionException,
    ChartType,
    ActiveAspect,
    SubscriptableBaseModel
)
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    CompositeSubjectModel,
    PlanetReturnModel,
    SingleChartAspectsModel,
    DualChartAspectsModel,
    RelationshipScoreModel
)
from kerykeion.schemas.kr_literals import (
    AstrologicalPoint,
)
from kerykeion.house_comparison.house_comparison_models import HouseComparisonModel
from kerykeion.utilities import find_common_active_points, distribute_percentages_to_100
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_ASPECTS
from kerykeion.settings.legacy.legacy_celestial_points_settings import DEFAULT_CELESTIAL_POINTS_SETTINGS
from kerykeion.charts.charts_utils import (
    calculate_element_points,
    calculate_quality_points,
    calculate_synastry_element_points,
    calculate_synastry_quality_points,
)


class ElementDistributionModel(SubscriptableBaseModel):
    """
    Model representing element distribution in a chart.

    Attributes:
        fire: Fire element points total
        earth: Earth element points total
        air: Air element points total
        water: Water element points total
        fire_percentage: Fire element percentage
        earth_percentage: Earth element percentage
        air_percentage: Air element percentage
        water_percentage: Water element percentage
    """
    fire: float
    earth: float
    air: float
    water: float
    fire_percentage: int
    earth_percentage: int
    air_percentage: int
    water_percentage: int


class QualityDistributionModel(SubscriptableBaseModel):
    """
    Model representing quality distribution in a chart.

    Attributes:
        cardinal: Cardinal quality points total
        fixed: Fixed quality points total
        mutable: Mutable quality points total
        cardinal_percentage: Cardinal quality percentage
        fixed_percentage: Fixed quality percentage
        mutable_percentage: Mutable quality percentage
    """
    cardinal: float
    fixed: float
    mutable: float
    cardinal_percentage: int
    fixed_percentage: int
    mutable_percentage: int


class SingleChartDataModel(SubscriptableBaseModel):
    """
    Chart data model for single-subject astrological charts.

    This model contains all pure data from single-subject charts including planetary
    positions, internal aspects, element/quality distributions, and location data.
    Used for chart types that analyze a single astrological subject.

    Supported chart types:
    - Natal: Birth chart with internal planetary aspects
    - Composite: Midpoint relationship chart with internal aspects
    - SingleWheelReturn: Single planetary return with internal aspects

    Attributes:
        chart_type: Type of single chart (Natal, Composite, SingleWheelReturn)
        subject: The astrological subject being analyzed
        aspects: Internal aspects within the chart
        element_distribution: Distribution of elemental energies
        quality_distribution: Distribution of modal qualities
        active_points: Celestial points included in calculations
        active_aspects: Aspect types and orb settings used
    """

    # Chart identification
    chart_type: Literal["Natal", "Composite", "SingleWheelReturn"]

    # Single chart subject
    subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel]

    # Internal aspects analysis
    aspects: SingleChartAspectsModel

    # Element and quality distributions
    element_distribution: ElementDistributionModel
    quality_distribution: QualityDistributionModel

    # Configuration and metadata
    active_points: List[AstrologicalPoint]
    active_aspects: List[ActiveAspect]


class DualChartDataModel(SubscriptableBaseModel):
    """
    Chart data model for dual-subject astrological charts.

    This model contains all pure data from dual-subject charts including both subjects,
    inter-chart aspects, house comparisons, relationship analysis, and combined
    element/quality distributions. Used for chart types that compare or overlay
    two astrological subjects.

    Supported chart types:
    - Transit: Natal chart with current planetary transits
    - Synastry: Relationship compatibility between two people
    - Return: Natal chart with planetary return comparison

    Attributes:
        chart_type: Type of dual chart (Transit, Synastry, Return)
        first_subject: Primary astrological subject (natal, base chart)
        second_subject: Secondary astrological subject (transit, partner, return)
        aspects: Inter-chart aspects between the two subjects
        house_comparison: House overlay analysis between subjects
        relationship_score: Compatibility scoring (synastry only)
        element_distribution: Combined elemental distribution
        quality_distribution: Combined modal distribution
        active_points: Celestial points included in calculations
        active_aspects: Aspect types and orb settings used
    """

    # Chart identification
    chart_type: Literal["Transit", "Synastry", "Return"]

    # Dual chart subjects
    first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel]
    second_subject: Union[AstrologicalSubjectModel, PlanetReturnModel]

    # Inter-chart aspects analysis
    aspects: DualChartAspectsModel

    # House comparison analysis
    house_comparison: Optional[HouseComparisonModel] = None

    # Relationship analysis (synastry only)
    relationship_score: Optional[RelationshipScoreModel] = None

    # Combined element and quality distributions
    element_distribution: ElementDistributionModel
    quality_distribution: QualityDistributionModel

    # Configuration and metadata
    active_points: List[AstrologicalPoint]
    active_aspects: List[ActiveAspect]


# Union type for all chart data models
ChartDataModel = Union[SingleChartDataModel, DualChartDataModel]


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
        include_relationship_score: bool = True,
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

        Returns:
            ChartDataModel: Comprehensive chart data model

        Raises:
            KerykeionException: If chart type requirements are not met
        """

        # Validate chart type requirements
        if chart_type in ["Transit", "Synastry", "Return"] and not second_subject:
            raise KerykeionException(f"Second subject is required for {chart_type} charts.")

        if chart_type == "Composite" and not isinstance(first_subject, CompositeSubjectModel):
            raise KerykeionException("First subject must be a CompositeSubjectModel for Composite charts.")

        if chart_type == "Return" and not isinstance(second_subject, PlanetReturnModel):
            raise KerykeionException("Second subject must be a PlanetReturnModel for Return charts.")

        if chart_type == "SingleWheelReturn" and not isinstance(first_subject, PlanetReturnModel):
            raise KerykeionException("First subject must be a PlanetReturnModel for SingleWheelReturn charts.")

        # Determine active points
        if not active_points:
            effective_active_points = first_subject.active_points
        else:
            effective_active_points = find_common_active_points(
                active_points,
                first_subject.active_points
            )

        # For dual charts, further filter by second subject's active points
        if second_subject:
            effective_active_points = find_common_active_points(
                effective_active_points,
                second_subject.active_points
            )

        # Calculate aspects based on chart type
        if chart_type in ["Natal", "Composite", "SingleWheelReturn"]:
            # Single chart aspects
            aspects = AspectsFactory.single_chart_aspects(
                first_subject,
                active_points=effective_active_points,
                active_aspects=active_aspects,
            )
        else:
            # Dual chart aspects - second_subject is guaranteed to exist here due to validation above
            if second_subject is None:
                raise KerykeionException(f"Second subject is required for {chart_type} charts.")
            aspects = AspectsFactory.dual_chart_aspects(
                first_subject,
                second_subject,
                active_points=effective_active_points,
                active_aspects=active_aspects,
            )

        # Calculate house comparison for dual charts
        house_comparison = None
        if second_subject and include_house_comparison and chart_type in ["Transit", "Synastry", "Return"]:
            if isinstance(first_subject, AstrologicalSubjectModel) and isinstance(second_subject, (AstrologicalSubjectModel, PlanetReturnModel)):
                house_comparison_factory = HouseComparisonFactory(
                    first_subject,
                    second_subject,
                    active_points=effective_active_points
                )
                house_comparison = house_comparison_factory.get_house_comparison()

        # Calculate relationship score for synastry
        relationship_score = None
        if chart_type == "Synastry" and include_relationship_score and second_subject:
            if isinstance(first_subject, AstrologicalSubjectModel) and isinstance(second_subject, AstrologicalSubjectModel):
                relationship_score_factory = RelationshipScoreFactory(
                    first_subject,
                    second_subject
                )
                relationship_score = relationship_score_factory.get_relationship_score()

        # Calculate element and quality distributions
        celestial_points_settings = DEFAULT_CELESTIAL_POINTS_SETTINGS
        available_planets_setting = []
        for body in celestial_points_settings:
            if body["name"] in effective_active_points:
                body["is_active"] = True
                available_planets_setting.append(body)

        celestial_points_names = [body["name"].lower() for body in available_planets_setting]

        if chart_type == "Synastry" and second_subject:
            # Calculate combined element/quality points for synastry
            # Type narrowing: ensure both subjects are AstrologicalSubjectModel for synastry
            if isinstance(first_subject, AstrologicalSubjectModel) and isinstance(second_subject, AstrologicalSubjectModel):
                element_totals = calculate_synastry_element_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    second_subject,
                )
                quality_totals = calculate_synastry_quality_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    second_subject,
                )
            else:
                # Fallback to single chart calculation for incompatible types
                element_totals = calculate_element_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                )
                quality_totals = calculate_quality_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                )
        else:
            # Calculate element/quality points for single chart
            element_totals = calculate_element_points(
                available_planets_setting,
                celestial_points_names,
                first_subject,
            )
            quality_totals = calculate_quality_points(
                available_planets_setting,
                celestial_points_names,
                first_subject,
            )

        # Calculate percentages
        total_elements = element_totals["fire"] + element_totals["water"] + element_totals["earth"] + element_totals["air"]
        element_percentages = distribute_percentages_to_100(element_totals) if total_elements > 0 else {"fire": 0, "earth": 0, "air": 0, "water": 0}
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
        quality_percentages = distribute_percentages_to_100(quality_totals) if total_qualities > 0 else {"cardinal": 0, "fixed": 0, "mutable": 0}
        quality_distribution = QualityDistributionModel(
            cardinal=quality_totals["cardinal"],
            fixed=quality_totals["fixed"],
            mutable=quality_totals["mutable"],
            cardinal_percentage=quality_percentages["cardinal"],
            fixed_percentage=quality_percentages["fixed"],
            mutable_percentage=quality_percentages["mutable"],
        )

        # Create and return the appropriate chart data model
        if chart_type in ["Natal", "Composite", "SingleWheelReturn"]:
            # Single chart data model - cast types since they're already validated
            return SingleChartDataModel(
                chart_type=cast(Literal["Natal", "Composite", "SingleWheelReturn"], chart_type),
                subject=first_subject,
                aspects=cast(SingleChartAspectsModel, aspects),
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
                chart_type=cast(Literal["Transit", "Synastry", "Return"], chart_type),
                first_subject=first_subject,
                second_subject=second_subject,
                aspects=cast(DualChartAspectsModel, aspects),
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
    ) -> ChartDataModel:
        """
        Convenience method for creating natal chart data.

        Args:
            subject: Astrological subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use

        Returns:
            ChartDataModel: Natal chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=subject,
            chart_type="Natal",
            active_points=active_points,
            active_aspects=active_aspects,
        )

    @staticmethod
    def create_synastry_chart_data(
        first_subject: AstrologicalSubjectModel,
        second_subject: AstrologicalSubjectModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        include_house_comparison: bool = True,
        include_relationship_score: bool = True,
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
        )

    @staticmethod
    def create_transit_chart_data(
        natal_subject: AstrologicalSubjectModel,
        transit_subject: AstrologicalSubjectModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        include_house_comparison: bool = True,
    ) -> ChartDataModel:
        """
        Convenience method for creating transit chart data.

        Args:
            natal_subject: Natal astrological subject
            transit_subject: Transit astrological subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            include_house_comparison: Whether to include house comparison

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
        )

    @staticmethod
    def create_composite_chart_data(
        composite_subject: CompositeSubjectModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
    ) -> ChartDataModel:
        """
        Convenience method for creating composite chart data.

        Args:
            composite_subject: Composite astrological subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use

        Returns:
            ChartDataModel: Composite chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=composite_subject,
            chart_type="Composite",
            active_points=active_points,
            active_aspects=active_aspects,
        )

    @staticmethod
    def create_return_chart_data(
        natal_subject: AstrologicalSubjectModel,
        return_subject: PlanetReturnModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
        include_house_comparison: bool = True,
    ) -> ChartDataModel:
        """
        Convenience method for creating planetary return chart data.

        Args:
            natal_subject: Natal astrological subject
            return_subject: Planetary return subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            include_house_comparison: Whether to include house comparison

        Returns:
            ChartDataModel: Return chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=natal_subject,
            chart_type="Return",
            second_subject=return_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            include_house_comparison=include_house_comparison,
        )

    @staticmethod
    def create_single_wheel_return_chart_data(
        return_subject: PlanetReturnModel,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: List[ActiveAspect] = DEFAULT_ACTIVE_ASPECTS,
    ) -> ChartDataModel:
        """
        Convenience method for creating single wheel planetary return chart data.

        Args:
            return_subject: Planetary return subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use

        Returns:
            ChartDataModel: Single wheel return chart data
        """
        return ChartDataFactory.create_chart_data(
            first_subject=return_subject,
            chart_type="SingleWheelReturn",
            active_points=active_points,
            active_aspects=active_aspects,
        )


if __name__ == "__main__":
    # Example usage
    from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

    # Create a natal chart data
    subject = AstrologicalSubjectFactory.from_current_time(name="Test Subject")
    natal_data = ChartDataFactory.create_natal_chart_data(subject)

    print(f"Chart Type: {natal_data.chart_type}")
    print(f"Active Points: {len(natal_data.active_points)}")
    print(f"Aspects: {len(natal_data.aspects.relevant_aspects)}")
    print(f"Fire: {natal_data.element_distribution.fire_percentage}%")
    print(f"Earth: {natal_data.element_distribution.earth_percentage}%")
    print(f"Air: {natal_data.element_distribution.air_percentage}%")
    print(f"Water: {natal_data.element_distribution.water_percentage}%")
