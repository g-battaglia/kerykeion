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
from typing import Collection, Mapping, Union, Optional, Literal, cast, get_args

from kerykeion.aspects import AspectsFactory
from kerykeion.house_comparison.factory import HouseComparisonFactory
from kerykeion.relationship_score.factory import RelationshipScoreFactory
from kerykeion.schemas import KerykeionException, ChartType, ActiveAspect
from kerykeion.schemas.models import (
    AngularityModel,
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
    StelliumModel,
)
from kerykeion.schemas.settings_models import KerykeionSettingsCelestialPointModel
from kerykeion.schemas.literals import (
    AstrologicalPoint,
)
from kerykeion.utilities.core import find_common_active_points, distribute_percentages_to_100, has_terrestrial_frame
from kerykeion.settings.config_constants import (
    DEFAULT_ACTIVE_ASPECTS,
    PREDICTIVE_ACTIVE_ASPECTS,
    DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS,
    NO_POINT_ORB_ADJUSTMENTS,
)
from kerykeion.aspects.orb_utils import OrbAdjustmentStrategy, PointOrbAdjustment
from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS
from kerykeion.charts.utils import (
    DOUBLE_CHART_TYPES,
    ElementQualityDistributionMethod,
    calculate_element_points,
    calculate_quality_points,
    calculate_synastry_element_points,
    calculate_synastry_quality_points,
)


# --- Angularity & stellium analysis -----------------------------------------
# Classical seven planets against the four chart angles. The 8-degree orb and
# the three-planet stellium threshold are the common conventions for these
# summary indicators; they are analysis defaults, not the user's aspect orbs.
ANGULARITY_ORB_DEGREES = 8.0
STELLIUM_MIN_POINTS = 3

_CLASSICAL_PLANET_FIELDS = ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn")
_ANGLE_FIELDS = ("ascendant", "medium_coeli", "descendant", "imum_coeli")
_HOUSE_NAME_TO_NUMBER = {
    "First_House": 1, "Second_House": 2, "Third_House": 3, "Fourth_House": 4,
    "Fifth_House": 5, "Sixth_House": 6, "Seventh_House": 7, "Eighth_House": 8,
    "Ninth_House": 9, "Tenth_House": 10, "Eleventh_House": 11, "Twelfth_House": 12,
}


def _angular_distance(a: float, b: float) -> float:
    """Shortest arc between two ecliptic longitudes (0-180)."""
    d = abs(a - b) % 360.0
    return 360.0 - d if d > 180.0 else d


def _subject_point_filter(subject: object, active_points: Optional[Collection[str]]) -> Optional[set[str]]:
    """Effective point-name filter for a subject's analyses.

    Mirrors the distribution semantics: the subject's own ``active_points``
    intersected with the caller's explicit filter (when given). ``None``
    means "no restriction known" (a subject without the field).
    """
    own = getattr(subject, "active_points", None)
    if own is None and active_points is None:
        return None
    effective = set(str(p) for p in own) if own is not None else None
    if active_points is not None:
        caller = set(str(p) for p in active_points)
        effective = caller if effective is None else (effective & caller)
    return effective


def _compute_angularities(
    subject: object,
    orb: float = ANGULARITY_ORB_DEGREES,
    active_points: Optional[set[str]] = None,
) -> list[AngularityModel]:
    """Every (classical planet, angle) pair within ``orb``, closest first.

    ALL pairs inside the orb are reported — not just each planet's nearest
    angle — so a consumer that only cares about specific angles (e.g. an
    ASC/MC-only ruleset) can filter without losing a planet whose nearest
    angle happened to be another one. ``active_points`` restricts the planets
    to the chart's effective selection: an excluded planet must never appear
    in the analysis of a chart that excluded it. Non-terrestrial perspectives
    yield no angularities: their longitudes and the angles live in different
    frames.
    """
    if not has_terrestrial_frame(subject):
        return []
    results: list[AngularityModel] = []
    for planet_field in _CLASSICAL_PLANET_FIELDS:
        planet = getattr(subject, planet_field, None)
        if planet is None or planet.abs_pos is None:
            continue
        if active_points is not None and str(planet.name) not in active_points:
            continue
        for angle_field in _ANGLE_FIELDS:
            angle = getattr(subject, angle_field, None)
            if angle is None or angle.abs_pos is None:
                continue
            distance = _angular_distance(planet.abs_pos, angle.abs_pos)
            if distance <= orb:
                results.append(
                    AngularityModel(point=str(planet.name), angle=str(angle.name), distance=round(distance, 4))
                )
    results.sort(key=lambda entry: entry.distance)
    return results


def _compute_stelliums(
    subject: object,
    min_points: int = STELLIUM_MIN_POINTS,
    active_points: Optional[set[str]] = None,
) -> list[StelliumModel]:
    """Houses gathering at least ``min_points`` classical planets, biggest first.

    ``active_points`` restricts the planets to the chart's effective
    selection, keeping the analysis consistent with the serialized
    ``active_points`` list. Non-terrestrial perspectives yield no stelliums:
    grouping their longitudes into terrestrial houses would be meaningless.
    """
    if not has_terrestrial_frame(subject):
        return []
    buckets: dict[int, list[str]] = {}
    for planet_field in _CLASSICAL_PLANET_FIELDS:
        planet = getattr(subject, planet_field, None)
        if planet is None or planet.house is None:
            continue
        if active_points is not None and str(planet.name) not in active_points:
            continue
        house_number = _HOUSE_NAME_TO_NUMBER.get(str(planet.house))
        if house_number is None:
            continue
        buckets.setdefault(house_number, []).append(str(planet.name))
    stelliums = [
        StelliumModel(house=house, points=points)
        for house, points in buckets.items()
        if len(points) >= min_points
    ]
    stelliums.sort(key=lambda entry: (-len(entry.points), entry.house))
    return stelliums


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
        >>> # Create synastry chart data (relationship_score is opt-in on
        >>> # create_chart_data; create_synastry_chart_data enables it by default)
        >>> jane = AstrologicalSubjectFactory.from_birth_data("Jane", 1992, 6, 15, 14, 30, "Paris", "FR")
        >>> synastry_data = ChartDataFactory.create_chart_data(
        ...     "Synastry", john, jane, include_relationship_score=True
        ... )
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
        point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]] = None,
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
                An entry can also vary by aspect:
                ``{"Sun": {"*": 1.5, "conjunction": 3.0}}`` applies 3.0° to Sun
                conjunctions and 1.5° to every other Sun aspect (``"*"`` is the
                default for unlisted aspects; without it the point is
                unconfigured for those aspects).
            point_orb_adjustment_strategy: How to combine the two points'
                adjustments (default ``"max_explicit"``)
            distribution_method: Strategy for element/modality weighting ("pure_count" or "weighted")
            custom_distribution_weights: Optional overrides for the distribution weights

        Returns:
            ChartDataModel: Comprehensive chart data model

        Raises:
            KerykeionException: If ``chart_type`` is not a valid ``ChartType``,
                or if chart type requirements are not met (e.g. a missing
                second subject for dual charts)
        """
        # An unknown chart_type must fail here with the valid options; letting
        # it fall through produces misleading errors ("Second subject is
        # required for NatalFoo charts") or a late pydantic ValidationError
        # after the full dual pipeline has already run.
        _valid_chart_types = get_args(ChartType)
        if chart_type not in _valid_chart_types:
            raise KerykeionException(
                f"Unknown chart_type {chart_type!r}. Valid chart types: "
                f"{', '.join(_valid_chart_types)}."
            )

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
        # Source the serialized metadata from the aspects model, not from the raw
        # inputs: aspects_model.active_points includes the catalog fixed stars
        # actually aspected (effective_active_points omits them), and
        # aspects_model.active_aspects has had unsupported declination names
        # dropped — so the metadata describes the real calculation.
        if chart_type in ["Natal", "Composite", "SingleReturnChart"]:
            # Single chart data model - cast types since they're already validated
            single_model = cast(SingleChartAspectsModel, aspects_model)
            return SingleChartDataModel(
                chart_type=cast(Literal["Natal", "Composite", "SingleReturnChart"], chart_type),
                subject=first_subject,
                aspects=single_model.aspects,
                element_distribution=element_distribution,
                quality_distribution=quality_distribution,
                angularities=_compute_angularities(
                    first_subject, active_points=_subject_point_filter(first_subject, active_points)
                ),
                stelliums=_compute_stelliums(
                    first_subject, active_points=_subject_point_filter(first_subject, active_points)
                ),
                active_points=list(single_model.active_points),
                active_aspects=list(single_model.active_aspects),
            )
        else:
            # Dual chart data model - cast types since they're already validated
            if second_subject is None:
                raise KerykeionException(f"Second subject is required for {chart_type} charts.")
            dual_model = cast(DualChartAspectsModel, aspects_model)
            # Synastry is symmetric: its distributions and its serialized
            # active_points both describe the COMMON point set, so the
            # per-subject analyses must honour it too — a Sun-only partner
            # must not surface the other partner's Venus stellium under a
            # contract that declares only the Sun active. Transit-like charts
            # keep each subject's own set instead, mirroring their
            # distribution convention (the natal analysis is never truncated
            # by the moving chart's tracking set).
            if chart_type == "Synastry":
                first_analysis_filter: Optional[set[str]] = {str(p) for p in effective_active_points}
                second_analysis_filter = first_analysis_filter
            else:
                first_analysis_filter = _subject_point_filter(first_subject, active_points)
                second_analysis_filter = _subject_point_filter(second_subject, active_points)
            return DualChartDataModel(
                chart_type=cast(Literal["Transit", "Synastry", "DualReturnChart", "Progression"], chart_type),
                first_subject=first_subject,
                second_subject=second_subject,
                aspects=dual_model.aspects,
                house_comparison=house_comparison,
                relationship_score=relationship_score,
                element_distribution=element_distribution,
                quality_distribution=quality_distribution,
                first_subject_angularities=_compute_angularities(
                    first_subject, active_points=first_analysis_filter
                ),
                first_subject_stelliums=_compute_stelliums(
                    first_subject, active_points=first_analysis_filter
                ),
                second_subject_angularities=_compute_angularities(
                    second_subject, active_points=second_analysis_filter
                ),
                second_subject_stelliums=_compute_stelliums(
                    second_subject, active_points=second_analysis_filter
                ),
                active_points=list(dual_model.active_points),
                active_aspects=list(dual_model.active_aspects),
            )

    @staticmethod
    def create_natal_chart_data(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points: Optional[list[AstrologicalPoint]] = None,
        active_aspects: Optional[list[ActiveAspect]] = None,
        *,
        axis_orb_limit: Optional[float] = None,
        point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]] = None,
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
        point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]] = None,
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
        point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]] = None,
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
        point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]] = None,
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
        point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]] = None,
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
        point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]] = None,
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
        point_orb_adjustments: Optional[Mapping[str, PointOrbAdjustment]] = None,
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
    from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory

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
