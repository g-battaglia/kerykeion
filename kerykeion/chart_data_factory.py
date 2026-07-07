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

import logging
from typing import Mapping, Union, Optional, Literal, cast

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
from kerykeion.settings.config_constants import (
    DEFAULT_ACTIVE_ASPECTS,
    PREDICTIVE_ACTIVE_ASPECTS,
    DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS,
    NO_POINT_ORB_ADJUSTMENTS,
)
from kerykeion.aspects.orb_utils import OrbAdjustmentStrategy
from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS
from kerykeion.charts.charts_utils import (
    DOUBLE_CHART_TYPES,
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

    # Chart types analysed like a natal chart — they get the wider natal
    # aspect orbs and the luminary orb bonus. Every other chart type
    # (transit, progression, returns) is predictive: tight flat orbs, no
    # luminary bonus. Single source of truth for the per-chart-type defaults.
    _NATAL_FAMILY_CHART_TYPES = frozenset({"Natal", "Synastry", "Composite"})

    @staticmethod
    def create_chart_data(
        chart_type: ChartType,
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Optional[Union[AstrologicalSubjectModel, PlanetReturnModel]] = None,
        active_points: Optional[list[AstrologicalPoint]] = None,
        active_aspects: Optional[list[ActiveAspect]] = None,
        include_house_comparison: bool = True,
        include_relationship_score: bool = False,
        *,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
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
            active_aspects: Aspect types and orbs to use. When ``None``, the
                per-chart-type default applies — natal/synastry/composite use
                ``DEFAULT_ACTIVE_ASPECTS``, every other type uses the tight
                ``PREDICTIVE_ACTIVE_ASPECTS``.
            include_house_comparison: Whether to include house comparison for dual charts
            include_relationship_score: Whether to include relationship scoring for synastry
            axis_orb_limit: Optional orb threshold for chart axes (Ascendant,
                Medium_Coeli, Descendant, Imum_Coeli). When set, aspects involving
                an axis are kept only if their orb is below this limit; the tighter
                orb is applied uniformly to both single-chart and dual-chart
                (synastry/transit) aspects. ``None`` (default) disables it.
            point_orb_adjustments: Optional per-point orb adjustment table (e.g.
                ``{"Sun": 1.5, "Moon": 1.5}``). When ``None``, the per-chart-type
                default applies — natal/synastry/composite use
                ``DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS``, every other type uses none.
            point_orb_adjustment_strategy: How to combine the two points'
                adjustments (default ``"max_explicit"``)
            distribution_method: Strategy for element/modality weighting ("pure_count" or "weighted")
            custom_distribution_weights: Optional overrides for the distribution weights

        Returns:
            ChartDataModel: Comprehensive chart data model

        Raises:
            KerykeionException: If chart type requirements are not met
        """
        # Resolve per-chart-type defaults when the caller did not specify them.
        is_natal_family = chart_type in ChartDataFactory._NATAL_FAMILY_CHART_TYPES
        if active_aspects is None:
            active_aspects = DEFAULT_ACTIVE_ASPECTS if is_natal_family else PREDICTIVE_ACTIVE_ASPECTS
        if point_orb_adjustments is None:
            point_orb_adjustments = (
                DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS if is_natal_family else NO_POINT_ORB_ADJUSTMENTS
            )

        # Validate chart type requirements
        if chart_type in DOUBLE_CHART_TYPES and not second_subject:
            raise KerykeionException(f"Second subject is required for {chart_type} charts.")

        if chart_type == "Composite" and not isinstance(first_subject, CompositeSubjectModel):
            raise KerykeionException("First subject must be a CompositeSubjectModel for Composite charts.")

        if chart_type == "DualReturnChart" and not isinstance(second_subject, PlanetReturnModel):
            raise KerykeionException(
                "Second subject must be a PlanetReturnModel for DualReturnChart charts. "
                "Build it with PlanetaryReturnFactory (e.g. next_return_from_date)."
            )

        if chart_type == "SingleReturnChart" and not isinstance(first_subject, PlanetReturnModel):
            raise KerykeionException("First subject must be a PlanetReturnModel for SingleReturnChart charts.")

        if chart_type == "Progression":
            if not isinstance(first_subject, AstrologicalSubjectModel):
                raise KerykeionException("First subject must be an AstrologicalSubjectModel for Progression charts.")
            if not isinstance(second_subject, AstrologicalSubjectModel):
                raise KerykeionException("Second subject must be an AstrologicalSubjectModel for Progression charts.")

        # Determine active points. None is the documented "use the subject's
        # own points" sentinel; an explicitly-passed empty list is a real
        # (empty) filter, not a request for everything.
        if active_points is None:
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
                active_points=list(effective_active_points),
                active_aspects=active_aspects,
                axis_orb_limit=axis_orb_limit,
                point_orb_adjustments=point_orb_adjustments,
                point_orb_adjustment_strategy=point_orb_adjustment_strategy,
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
            elif chart_type == "Progression":
                first_subject_is_fixed = True  # Natal chart is fixed
                second_subject_is_fixed = False  # Progressed chart is moving

            aspects_model = AspectsFactory.dual_chart_aspects(
                first_subject,
                second_subject,
                active_points=list(effective_active_points),
                active_aspects=active_aspects,
                axis_orb_limit=axis_orb_limit,
                first_subject_is_fixed=first_subject_is_fixed,
                second_subject_is_fixed=second_subject_is_fixed,
                point_orb_adjustments=point_orb_adjustments,
                point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            )

        # Calculate house comparison for dual charts
        house_comparison = None
        if second_subject and include_house_comparison and chart_type in DOUBLE_CHART_TYPES:
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
                # The relationship score is a geocentric technique: it weights
                # the natal Sun (and other bodies) of both partners. A chart
                # whose perspective excludes the Sun as its center body
                # (heliocentric: Sun is the center; selenocentric: Moon is) has
                # no natal Sun to score on, so the score is not applicable —
                # skip it (with a warning) rather than raise and block an
                # otherwise valid synastry (aspects/positions are perspective-
                # independent in the way the chart draws them).
                if first_subject.sun is not None and second_subject.sun is not None:
                    relationship_score_factory = RelationshipScoreFactory(
                        first_subject,
                        second_subject,
                        axis_orb_limit=axis_orb_limit,
                    )
                    relationship_score = relationship_score_factory.get_relationship_score()
                else:
                    logging.warning(
                        "Skipping relationship_score: a partner subject has no "
                        "Sun (a non-geocentric perspective excludes the center "
                        "body). The score is a geocentric technique."
                    )

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
                # Raw combined point totals (not percentages): the model's
                # fire/earth/... fields are documented "points total" and every
                # other chart type stores raw totals here; the percentages are
                # derived below via distribute_percentages_to_100.
                element_totals = calculate_synastry_element_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    second_subject,
                    method=distribution_method,
                    custom_weights=custom_distribution_weights,
                    include_fixed_stars=True,
                    as_percentages=False,
                )
                quality_totals = calculate_synastry_quality_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    second_subject,
                    method=distribution_method,
                    custom_weights=custom_distribution_weights,
                    include_fixed_stars=True,
                    as_percentages=False,
                )
            else:
                # Fallback to single chart calculation for incompatible types
                element_totals = calculate_element_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    method=distribution_method,
                    custom_weights=custom_distribution_weights,
                    include_fixed_stars=True,
                )
                quality_totals = calculate_quality_points(
                    available_planets_setting,
                    celestial_points_names,
                    first_subject,
                    method=distribution_method,
                    custom_weights=custom_distribution_weights,
                    include_fixed_stars=True,
                )
        else:
            # Single-subject distribution (Natal, and the FIRST subject of
            # Transit/DualReturnChart/Progression). Compute it over the FIRST
            # subject's OWN active_points, intersected with the caller's explicit
            # active_points filter (when given). This keeps the caller's filter
            # honored (a chart requested with active_points=['Sun','Moon'] has a
            # Sun+Moon distribution, consistent with its aspect list) WITHOUT
            # letting the SECOND subject's point count truncate it (a transit
            # tracking 7 bodies must not drop the natal's Uranus/Neptune/Pluto).
            first_points = set(first_subject.active_points)
            if active_points is not None:
                first_points &= set(active_points)
            first_subject_setting = [
                KerykeionSettingsCelestialPointModel(**{**dict(body), "is_active": True})  # type: ignore[arg-type]
                for body in DEFAULT_CELESTIAL_POINTS_SETTINGS
                if body["name"] in first_points
            ]
            first_subject_names = [b.name.lower() for b in first_subject_setting]
            element_totals = calculate_element_points(
                first_subject_setting,
                first_subject_names,
                first_subject,
                method=distribution_method,
                custom_weights=custom_distribution_weights,
                include_fixed_stars=True,
            )
            quality_totals = calculate_quality_points(
                first_subject_setting,
                first_subject_names,
                first_subject,
                method=distribution_method,
                custom_weights=custom_distribution_weights,
                include_fixed_stars=True,
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
                active_points=list(effective_active_points),
                active_aspects=active_aspects,
            )
        else:
            # Dual chart data model - cast types since they're already validated
            if second_subject is None:
                raise KerykeionException(f"Second subject is required for {chart_type} charts.")
            return DualChartDataModel(
                chart_type=cast(Literal["Transit", "Synastry", "DualReturnChart", "Progression"], chart_type),
                first_subject=first_subject,
                second_subject=second_subject,
                aspects=cast(DualChartAspectsModel, aspects_model).aspects,
                house_comparison=house_comparison,
                relationship_score=relationship_score,
                element_distribution=element_distribution,
                quality_distribution=quality_distribution,
                active_points=list(effective_active_points),
                active_aspects=active_aspects,
            )

    @staticmethod
    def create_natal_chart_data(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points: Optional[list[AstrologicalPoint]] = None,
        active_aspects: Optional[list[ActiveAspect]] = None,
        *,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating natal chart data.

        Args:
            subject: Astrological subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            axis_orb_limit: Optional orb threshold for chart axes (Ascendant,
                Medium_Coeli, Descendant, Imum_Coeli). ``None`` (default) disables it.
            point_orb_adjustments: Per-point orb adjustment table. ``None`` uses
                the natal default (Sun/Moon +1.5°, the luminary-widening rule);
                pass ``{}`` to disable.
            point_orb_adjustment_strategy: How to combine the two points' adjustments
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
            axis_orb_limit=axis_orb_limit,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_synastry_chart_data(
        first_subject: AstrologicalSubjectModel,
        second_subject: AstrologicalSubjectModel,
        active_points: Optional[list[AstrologicalPoint]] = None,
        active_aspects: Optional[list[ActiveAspect]] = None,
        include_house_comparison: bool = True,
        include_relationship_score: bool = True,
        *,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
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
            axis_orb_limit: Optional orb threshold for chart axes (Ascendant,
                Medium_Coeli, Descendant, Imum_Coeli). Applied to dual-chart
                aspects and the relationship score. ``None`` (default) disables it.
            point_orb_adjustments: Per-point orb adjustment table. ``None`` uses
                the natal default (Sun/Moon +1.5°); pass ``{}`` to disable.
            point_orb_adjustment_strategy: How to combine the two points' adjustments
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
            axis_orb_limit=axis_orb_limit,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_transit_chart_data(
        natal_subject: AstrologicalSubjectModel,
        transit_subject: AstrologicalSubjectModel,
        active_points: Optional[list[AstrologicalPoint]] = None,
        active_aspects: Optional[list[ActiveAspect]] = None,
        include_house_comparison: bool = True,
        *,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
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
            axis_orb_limit: Optional orb threshold for chart axes (Ascendant,
                Medium_Coeli, Descendant, Imum_Coeli). ``None`` (default) disables it.
            point_orb_adjustments: Per-point orb adjustment table. ``None`` means
                no adjustment — transits use a flat tight orb by convention.
            point_orb_adjustment_strategy: How to combine the two points' adjustments
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
            axis_orb_limit=axis_orb_limit,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_composite_chart_data(
        composite_subject: CompositeSubjectModel,
        active_points: Optional[list[AstrologicalPoint]] = None,
        active_aspects: Optional[list[ActiveAspect]] = None,
        *,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating composite chart data.

        Args:
            composite_subject: Composite astrological subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use
            axis_orb_limit: Optional orb threshold for chart axes (Ascendant,
                Medium_Coeli, Descendant, Imum_Coeli). ``None`` (default) disables it.
            point_orb_adjustments: Per-point orb adjustment table. ``None`` uses
                the natal default (Sun/Moon +1.5°); pass ``{}`` to disable.
            point_orb_adjustment_strategy: How to combine the two points' adjustments
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
            axis_orb_limit=axis_orb_limit,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_return_chart_data(
        natal_subject: AstrologicalSubjectModel,
        return_subject: PlanetReturnModel,
        active_points: Optional[list[AstrologicalPoint]] = None,
        active_aspects: Optional[list[ActiveAspect]] = None,
        include_house_comparison: bool = True,
        *,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating planetary return chart data.

        Args:
            natal_subject: Natal astrological subject
            return_subject: Planetary return subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use. Defaults to the
                predictive set (3° orb) — the conventional return-chart default.
            include_house_comparison: Whether to include house comparison
            axis_orb_limit: Optional orb threshold for chart axes (Ascendant,
                Medium_Coeli, Descendant, Imum_Coeli). ``None`` (default) disables it.
            point_orb_adjustments: Per-point orb adjustment table. ``None`` means
                no adjustment — returns use a flat tight orb by convention.
            point_orb_adjustment_strategy: How to combine the two points' adjustments
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
            axis_orb_limit=axis_orb_limit,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_single_wheel_return_chart_data(
        return_subject: PlanetReturnModel,
        active_points: Optional[list[AstrologicalPoint]] = None,
        active_aspects: Optional[list[ActiveAspect]] = None,
        *,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating single wheel planetary return chart data.

        Args:
            return_subject: Planetary return subject
            active_points: Points to include in calculations
            active_aspects: Aspect types and orbs to use. Defaults to the
                predictive set (3° orb) — the conventional return-chart default.
            axis_orb_limit: Optional orb threshold for chart axes (Ascendant,
                Medium_Coeli, Descendant, Imum_Coeli). ``None`` (default) disables it.
            point_orb_adjustments: Per-point orb adjustment table. ``None`` means
                no adjustment — returns use a flat tight orb by convention.
            point_orb_adjustment_strategy: How to combine the two points' adjustments
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
            axis_orb_limit=axis_orb_limit,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            distribution_method=distribution_method,
            custom_distribution_weights=custom_distribution_weights,
        )

    @staticmethod
    def create_progression_chart_data(
        natal_subject: AstrologicalSubjectModel,
        progressed_subject: AstrologicalSubjectModel,
        active_points: Optional[list[AstrologicalPoint]] = None,
        active_aspects: Optional[list[ActiveAspect]] = None,
        include_house_comparison: bool = True,
        *,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
        distribution_method: ElementQualityDistributionMethod = "weighted",
        custom_distribution_weights: Optional[Mapping[str, float]] = None,
    ) -> ChartDataModel:
        """
        Convenience method for creating secondary progression chart data.

        Produces a dual-wheel chart with the natal chart as the inner ring
        and the day-for-a-year progressed chart as the outer ring.

        Args:
            natal_subject: The natal AstrologicalSubjectModel (inner ring).
            progressed_subject: The progressed AstrologicalSubjectModel (outer ring),
                typically from ``SecondaryProgressionFactory.compute()``.
            active_points: Points to include in calculations.
            active_aspects: Aspect types and orbs to use.
            include_house_comparison: Whether to include house overlay analysis.
            axis_orb_limit: Optional orb limit for axis aspects.
            point_orb_adjustments: Per-point orb adjustment table. ``None`` means
                no adjustment — progressions use a flat tight orb.
            point_orb_adjustment_strategy: How to combine the two points' adjustments
            distribution_method: Strategy for element/modality weighting.
            custom_distribution_weights: Optional overrides for distribution weights.

        Returns:
            ChartDataModel: Dual-wheel progression chart data.
        """
        return ChartDataFactory.create_chart_data(
            first_subject=natal_subject,
            second_subject=progressed_subject,
            chart_type="Progression",
            active_points=active_points,
            active_aspects=active_aspects,
            include_house_comparison=include_house_comparison,
            axis_orb_limit=axis_orb_limit,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
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
