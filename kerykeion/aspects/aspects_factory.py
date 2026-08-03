# -*- coding: utf-8 -*-
"""
This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import logging
import math
from typing import Any, Callable, Mapping, Sequence, Union, List, Optional, cast

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory, OPPOSITE_PAIRS
from kerykeion.aspects.aspects_utils import (
    get_aspect_from_two_points,
    get_active_points_list,
    calculate_aspect_movement,
)
from kerykeion.aspects.orb_utils import (
    OrbAdjustmentStrategy,
    resolve_pair_orb_adjustment,
    validate_point_orb_adjustments,
)
from kerykeion.schemas.kr_models import (
    AstrologicalSubjectModel,
    AspectModel,
    ActiveAspect,
    CompositeSubjectModel,
    PlanetReturnModel,
    SingleChartAspectsModel,
    DualChartAspectsModel,
)
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import AstrologicalPoint, AspectMovementType
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_ASPECTS, AXIAL_POINTS
from kerykeion.settings.chart_defaults import (
    DEFAULT_CELESTIAL_POINTS_SETTINGS,
    DEFAULT_CHART_ASPECTS_SETTINGS,
    _CelestialPointSetting,
)
from kerykeion.utilities import find_common_active_points, require_same_frame

logger = logging.getLogger(__name__)

# Axes used for orb filtering. Alias the codebase-wide single source of truth
# (AXIAL_POINTS) so the axis set can never drift from the rest of the package.
AXES_LIST = AXIAL_POINTS

# Geometrically locked opposite pairs, derived from the subject factory's
# OPPOSITE_PAIRS mapping (each derived point is rigidly primary + 180°).
# Within a single chart, any longitudinal aspect between such a pair is an
# artifact (a permanent 0.0-orb opposition), and their shared/mirrored
# declinations likewise produce a permanent parallel or contra-parallel —
# so both calculation paths skip these pairs. Cross-chart pairs (synastry,
# transits, ...) remain meaningful and are NOT skipped.
GEOMETRIC_OPPOSITE_PAIRS: frozenset = frozenset(
    frozenset((derived, config["primary"])) for derived, config in OPPOSITE_PAIRS.items()
)

# Mean/true variants of the same lunar node never separate by more than ~1.75°:
# within a single chart every mean×true node pair reports a permanent
# conjunction (same end) or opposition (opposite ends) — configuration
# artifacts, exactly like the rigid pairs above. Cross-chart pairs (synastry,
# transits) remain meaningful and are NOT skipped.
MEAN_TRUE_NODE_ARTIFACT_PAIRS: frozenset = frozenset(
    (
        frozenset(("Mean_North_Lunar_Node", "True_North_Lunar_Node")),
        frozenset(("Mean_South_Lunar_Node", "True_South_Lunar_Node")),
        frozenset(("Mean_North_Lunar_Node", "True_South_Lunar_Node")),
        frozenset(("True_North_Lunar_Node", "Mean_South_Lunar_Node")),
    )
)

# Full set of same-chart artifact pairs skipped by the single-chart paths.
SINGLE_CHART_ARTIFACT_PAIRS: frozenset = GEOMETRIC_OPPOSITE_PAIRS | MEAN_TRUE_NODE_ARTIFACT_PAIRS

# `find_common_active_points` is annotated for AstrologicalPoint literals only,
# but the v6 fixed-star channel mixes plain catalog star names (str) into the
# active-point lists handled here. View the helper through a str-widened
# signature; runtime behavior is unchanged (pure set intersection + sort).
_find_common_point_names = cast(
    Callable[[Sequence[str], Sequence[str]], List[Union[AstrologicalPoint, str]]],
    find_common_active_points,
)


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
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
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
            point_orb_adjustments: Optional per-point orb adjustment table (e.g.
                ``{"Sun": 1.5, "Moon": 1.5}``); widens/tightens the base orb when
                a configured point is involved in the aspect
            point_orb_adjustment_strategy: How to combine the two points'
                adjustments (default ``"max_explicit"``)

        Returns:
            SingleChartAspectsModel containing all calculated aspects data

        Raises:
            ValueError: If ``point_orb_adjustments`` contains a non-string key
                or a non-finite adjustment value.
            KerykeionException: If ``axis_orb_limit`` is provided but not a
                finite positive number.

        Note:
            Luminary orbs differ between entry points: this method applies NO
            per-point orb widening by default (``point_orb_adjustments=None``),
            while ``ChartDataFactory`` natal-family charts (natal, synastry,
            composite) default to ``DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS``
            (Sun/Moon +1.5°). The same chart can therefore yield different
            aspect lists depending on the entry point. To reproduce
            ``ChartDataFactory`` output, pass
            ``point_orb_adjustments=DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS``
            (from ``kerykeion.settings.config_constants``).

        Example:
            >>> johnny = AstrologicalSubjectFactory.from_birth_data("Johnny", 1963, 6, 9, 0, 0, "Owensboro", "US")
            >>> chart_aspects = AspectsFactory.single_chart_aspects(johnny)
            >>> print(f"Found {len(chart_aspects.aspects)} aspects")
        """
        validate_point_orb_adjustments(point_orb_adjustments)

        # Initialize settings and configurations
        # v6: extend celestial_points with synthetic settings for any dynamic
        # catalog fixed star carried on subject.fixed_stars, so aspects engine
        # can iterate them just like planets.
        from kerykeion.settings.chart_defaults import build_dynamic_fixed_star_settings

        celestial_points = list(DEFAULT_CELESTIAL_POINTS_SETTINGS)
        raw_star_names = [getattr(s, "name", None) for s in getattr(subject, "fixed_stars", None) or []]
        dynamic_star_names: List[str] = [n for n in raw_star_names if n]
        if dynamic_star_names:
            celestial_points = celestial_points + build_dynamic_fixed_star_settings(
                dynamic_star_names, existing_settings=celestial_points
            )
        aspects_settings = DEFAULT_CHART_ASPECTS_SETTINGS
        # Set active aspects with default fallback
        active_aspects_resolved = active_aspects if active_aspects is not None else DEFAULT_ACTIVE_ASPECTS

        # Determine active points to use. v6: extend with star names so the
        # aspects loop iterates them; subject.fixed_stars stars are not in
        # subject.active_points by design.
        subject_active: List[Union[AstrologicalPoint, str]] = list(subject.active_points) + [
            n for n in dynamic_star_names if n not in subject.active_points
        ]
        if active_points is None:
            # Default: catalog fixed stars carried on the subject participate
            # automatically (subject_active already includes them above).
            active_points_resolved = subject_active
        else:
            # The caller's restriction governs the regular points channel.
            # Stars are a separate channel — opted into per-subject via
            # active_fixed_stars at construction — so the subject's own stars
            # always participate; star–star pairs are skipped downstream.
            active_points_resolved = _find_common_point_names(
                subject_active,
                list(active_points) + [n for n in dynamic_star_names if n not in active_points],
            )

        return AspectsFactory._create_single_chart_aspects_model(
            subject,
            active_points_resolved,
            active_aspects_resolved,
            aspects_settings,
            axis_orb_limit,
            celestial_points,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            star_names=frozenset(dynamic_star_names),
        )

    @staticmethod
    def dual_chart_aspects(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        *,
        active_points: Optional[List[AstrologicalPoint]] = None,
        active_aspects: Optional[List[ActiveAspect]] = None,
        axis_orb_limit: Optional[float] = None,
        first_subject_is_fixed: bool = False,
        second_subject_is_fixed: bool = False,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
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
            axis_orb_limit: Optional orb threshold for chart axes (Ascendant,
                Medium_Coeli, Descendant, Imum_Coeli). When set, aspects involving
                an axis are kept only if their orb is below this limit. The angles
                are time-sensitive points, so the tighter orb is applied uniformly
                to both single-chart and dual-chart (synastry/transit) aspects.
                When ``None`` (default) no axis-specific filtering is performed.
            point_orb_adjustments: Optional per-point orb adjustment table
            point_orb_adjustment_strategy: How to combine the two points'
                adjustments (default ``"max_explicit"``)

        Returns:
            DualChartAspectsModel: Complete model containing all calculated aspects data,
                                  including both comprehensive and filtered relevant aspects.

        Raises:
            ValueError: If ``point_orb_adjustments`` contains a non-string key
                or a non-finite adjustment value.
            KerykeionException: If the two subjects use different reference
                frames, or ``axis_orb_limit`` is provided but not a finite
                positive number.

        Note:
            Luminary orbs differ between entry points: this method applies NO
            per-point orb widening by default (``point_orb_adjustments=None``),
            while ``ChartDataFactory`` natal-family charts (natal, synastry,
            composite) default to ``DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS``
            (Sun/Moon +1.5°). The same chart pair can therefore yield different
            aspect lists depending on the entry point. To reproduce
            ``ChartDataFactory`` output, pass
            ``point_orb_adjustments=DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS``
            (from ``kerykeion.settings.config_constants``).

        Example:
            >>> john = AstrologicalSubjectFactory.from_birth_data("John", 1990, 1, 1, 12, 0, "London", "GB")
            >>> jane = AstrologicalSubjectFactory.from_birth_data("Jane", 1992, 6, 15, 14, 30, "Paris", "FR")
            >>> synastry = AspectsFactory.dual_chart_aspects(john, jane)
            >>> print(f"Found {len(synastry.aspects)} aspects")
        """
        validate_point_orb_adjustments(point_orb_adjustments)

        # Aspects between two charts are only meaningful when both are cast in the
        # same reference frame. Reject mixed frames (e.g. Tropical × Sidereal)
        # instead of returning astronomically-meaningless aspects — mirrors the
        # check CompositeSubjectFactory already performs.
        require_same_frame(first_subject, second_subject)

        # Initialize settings and configurations (v6: include dynamic star settings)
        from kerykeion.settings.chart_defaults import build_dynamic_fixed_star_settings

        celestial_points = list(DEFAULT_CELESTIAL_POINTS_SETTINGS)
        dynamic_star_names: list[str] = []
        for subj in (first_subject, second_subject):
            for s in getattr(subj, "fixed_stars", None) or []:
                star_name = getattr(s, "name", None)
                if star_name and star_name not in dynamic_star_names:
                    dynamic_star_names.append(star_name)
        if dynamic_star_names:
            celestial_points = celestial_points + build_dynamic_fixed_star_settings(
                dynamic_star_names, existing_settings=celestial_points
            )
        aspects_settings = DEFAULT_CHART_ASPECTS_SETTINGS
        # Set active aspects with default fallback
        active_aspects_resolved = active_aspects if active_aspects is not None else DEFAULT_ACTIVE_ASPECTS

        # v6: extend each subject's active_points with its fixed_stars names so
        # the dual-chart aspects engine iterates them as first-class points.
        first_subject_raw = list(first_subject.active_points) + [
            getattr(s, "name", None) for s in getattr(first_subject, "fixed_stars", None) or []
        ]
        first_subject_active: List[Union[AstrologicalPoint, str]] = [n for n in first_subject_raw if n]
        second_subject_raw = list(second_subject.active_points) + [
            getattr(s, "name", None) for s in getattr(second_subject, "fixed_stars", None) or []
        ]
        second_subject_active: List[Union[AstrologicalPoint, str]] = [n for n in second_subject_raw if n]

        # Determine active points to use - find common points between both subjects
        if active_points is None:
            active_points_resolved = first_subject_active
        else:
            active_points_resolved = _find_common_point_names(
                first_subject_active,
                active_points,
            )

        # Further filter with second subject's active points
        active_points_resolved = _find_common_point_names(
            second_subject_active,
            active_points_resolved,
        )

        # v6: catalog fixed stars from either subject participate regardless of
        # the active_points restriction (re-append the union after the
        # intersections). Stars are a separate channel — opted into per-subject
        # via active_fixed_stars at construction — and star–star pairs are
        # skipped downstream, so only star–planet aspects emerge.
        for name in dynamic_star_names:
            if name not in active_points_resolved:
                active_points_resolved.append(name)

        return AspectsFactory._create_dual_chart_aspects_model(
            first_subject,
            second_subject,
            active_points_resolved,
            active_aspects_resolved,
            aspects_settings,
            axis_orb_limit,
            celestial_points,
            first_subject_is_fixed=first_subject_is_fixed,
            second_subject_is_fixed=second_subject_is_fixed,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            star_names=frozenset(dynamic_star_names),
        )

    @staticmethod
    def _create_single_chart_aspects_model(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points_resolved: List[Union[AstrologicalPoint, str]],
        active_aspects_resolved: List[ActiveAspect],
        aspects_settings: Sequence[Mapping[str, Any]],
        axis_orb_limit: Optional[float],
        celestial_points: List[_CelestialPointSetting],
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
        star_names: frozenset = frozenset(),
    ) -> SingleChartAspectsModel:
        """
        Create the complete single chart aspects model with all calculations.

        Returns:
            SingleChartAspectsModel containing filtered aspects data
        """
        all_aspects = AspectsFactory._calculate_single_chart_aspects(
            subject,
            active_points_resolved,
            active_aspects_resolved,
            aspects_settings,
            celestial_points,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            star_names=star_names,
        )
        filtered_aspects = AspectsFactory._filter_relevant_aspects(
            all_aspects,
            axis_orb_limit,
        )

        return SingleChartAspectsModel(
            subject=subject,
            aspects=filtered_aspects,
            active_points=active_points_resolved,
            active_aspects=AspectsFactory._computed_active_aspects(active_aspects_resolved, aspects_settings),
        )

    @staticmethod
    def _create_dual_chart_aspects_model(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points_resolved: List[Union[AstrologicalPoint, str]],
        active_aspects_resolved: List[ActiveAspect],
        aspects_settings: Sequence[Mapping[str, Any]],
        axis_orb_limit: Optional[float],
        celestial_points: List[_CelestialPointSetting],
        first_subject_is_fixed: bool,
        second_subject_is_fixed: bool,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
        star_names: frozenset = frozenset(),
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
            star_names: Names of catalog fixed stars (star-star pairs are skipped)

        Returns:
            DualChartAspectsModel: Complete model containing filtered aspects data
        """
        all_aspects = AspectsFactory._calculate_dual_chart_aspects(
            first_subject,
            second_subject,
            active_points_resolved,
            active_aspects_resolved,
            aspects_settings,
            celestial_points,
            first_subject_is_fixed=first_subject_is_fixed,
            second_subject_is_fixed=second_subject_is_fixed,
            point_orb_adjustments=point_orb_adjustments,
            point_orb_adjustment_strategy=point_orb_adjustment_strategy,
            star_names=star_names,
        )
        filtered_aspects = AspectsFactory._filter_relevant_aspects(
            all_aspects,
            axis_orb_limit,
        )

        return DualChartAspectsModel(
            first_subject=first_subject,
            second_subject=second_subject,
            aspects=filtered_aspects,
            active_points=active_points_resolved,
            active_aspects=AspectsFactory._computed_active_aspects(active_aspects_resolved, aspects_settings),
        )

    @staticmethod
    def _computed_active_aspects(
        active_aspects: List[ActiveAspect], aspects_settings: Sequence[Mapping[str, Any]]
    ) -> List[ActiveAspect]:
        """Return only the active aspects the longitudinal engine actually computes.

        Declination aspects (``parallel``/``contra-parallel``) and any name
        without a settings entry are silently ignored by the calculation (see the
        warning in ``_update_aspect_settings``); dropping them here keeps the
        serialized ``active_aspects`` an honest description of the result — a JSON
        consumer must not believe a parallel was computed when it was not.
        """
        known_names = {setting["name"] for setting in aspects_settings}
        return [aspect for aspect in active_aspects if aspect["name"] in known_names]

    @staticmethod
    def _calculate_single_chart_aspects(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points: List[Union[AstrologicalPoint, str]],
        active_aspects: List[ActiveAspect],
        aspects_settings: Sequence[Mapping[str, Any]],
        celestial_points: List[_CelestialPointSetting],
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
        star_names: frozenset = frozenset(),
    ) -> List[AspectModel]:
        """
        Calculate all aspects within a single chart.

        This method handles all aspect calculations including settings updates,
        opposite pair filtering, and planet ID resolution for single charts.
        Works with any chart type (natal, return, composite, etc.).

        Returns:
            List of all calculated AspectModel instances
        """
        # v6: pass the (already-extended) celestial_points so that catalog
        # fixed stars on subject.fixed_stars are reachable by the lookup loop
        # in get_active_points_list; without this, they fall back to the
        # DEFAULT_CELESTIAL_POINTS_SETTINGS and never get iterated.
        active_points_list = get_active_points_list(subject, active_points, celestial_points=celestial_points)

        # Update aspects settings with active aspects orbs
        filtered_settings = AspectsFactory._update_aspect_settings(aspects_settings, active_aspects)

        # Create a lookup dictionary for planet IDs to optimize performance
        planet_id_lookup = {planet["name"]: planet["id"] for planet in celestial_points}

        all_aspects_list = []
        n_points = len(active_points_list)

        for first_idx, first_point in enumerate(active_points_list):
            first_name = first_point["name"]
            first_abs_pos = first_point["abs_pos"]
            first_speed = first_point.get("speed") or 0.0
            first_in_axes = first_name in AXES_LIST
            first_is_star = first_name in star_names
            # Generate aspects list without repetitions (single chart - same chart)
            for second_idx in range(first_idx + 1, n_points):
                second_point = active_points_list[second_idx]
                second_name = second_point["name"]

                # Skip same-chart artifact pairs: geometrically locked
                # opposites (AC/DC, MC/IC, N/S nodes, Vertex/Anti-Vertex,
                # Lilith/Priapus — the derived point sits at primary + 180° by
                # construction, a fake 0.0-orb opposition) and mean×true lunar
                # node combinations (a permanent ≤1.75°-orb conjunction or
                # opposition when both variants are active).
                if frozenset((first_name, second_name)) in SINGLE_CHART_ARTIFACT_PAIRS:
                    continue

                # Skip star-star pairs: fixed stars are mutually static, so
                # any aspect between two stars is identical in every chart.
                if first_is_star and second_name in star_names:
                    continue

                second_abs_pos = second_point["abs_pos"]
                extra_orb = resolve_pair_orb_adjustment(
                    first_name,
                    second_name,
                    point_orb_adjustments,
                    point_orb_adjustment_strategy,
                )
                aspect = get_aspect_from_two_points(
                    filtered_settings, first_abs_pos, second_abs_pos, extra_orb=extra_orb
                )

                if aspect["verdict"]:
                    # Get planet IDs using lookup dictionary for better performance
                    first_planet_id = planet_id_lookup.get(first_name, 0)
                    second_planet_id = planet_id_lookup.get(second_name, 0)

                    second_speed = second_point.get("speed") or 0.0

                    # Determine aspect movement.
                    # If both points are chart axes, there is no meaningful
                    # dynamic movement between them, so we mark the aspect as
                    # "Static" regardless of any synthetic speeds.
                    aspect_movement: AspectMovementType
                    if first_in_axes and second_name in AXES_LIST:
                        aspect_movement = "Static"
                    else:
                        # Calculate aspect movement (applying/separating/fixed)
                        aspect_movement = calculate_aspect_movement(
                            first_abs_pos,
                            second_abs_pos,
                            aspect["aspect_degrees"],
                            first_speed,
                            second_speed,
                        )

                    aspect_model = AspectModel(
                        p1_name=first_name,
                        p1_owner=subject.name,
                        p1_abs_pos=first_abs_pos,
                        p2_name=second_name,
                        p2_owner=subject.name,
                        p2_abs_pos=second_abs_pos,
                        aspect=aspect["name"],
                        orbit=aspect["orbit"],
                        aspect_degrees=aspect["aspect_degrees"],
                        diff=aspect["diff"],
                        p1=first_planet_id,
                        p2=second_planet_id,
                        aspect_movement=aspect_movement,
                        p1_speed=first_speed,
                        p2_speed=second_speed,
                    )
                    all_aspects_list.append(aspect_model)

        return all_aspects_list

    @staticmethod
    def _calculate_dual_chart_aspects(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        active_points: List[Union[AstrologicalPoint, str]],
        active_aspects: List[ActiveAspect],
        aspects_settings: Sequence[Mapping[str, Any]],
        celestial_points: List[_CelestialPointSetting],
        first_subject_is_fixed: bool,
        second_subject_is_fixed: bool,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
        star_names: frozenset = frozenset(),
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
            star_names: Names of catalog fixed stars (star-star pairs are skipped)

        Returns:
            List[AspectModel]: Complete list of all calculated aspect instances
        """
        # Get active points lists for both subjects
        # v6: see single_chart_aspects note — pass extended celestial_points.
        first_active_points_list = get_active_points_list(
            first_subject, active_points, celestial_points=celestial_points
        )
        second_active_points_list = get_active_points_list(
            second_subject, active_points, celestial_points=celestial_points
        )

        # Create a lookup dictionary for planet IDs to optimize performance
        planet_id_lookup = {planet["name"]: planet["id"] for planet in celestial_points}

        # Update aspects settings with active aspects orbs
        filtered_settings = AspectsFactory._update_aspect_settings(aspects_settings, active_aspects)

        all_aspects_list = []
        for first in range(len(first_active_points_list)):
            # Read the point name before the inner loop so the orb resolver
            # can use it (the name was previously read only after the verdict).
            first_name = first_active_points_list[first]["name"]
            first_is_star = first_name in star_names
            # Generate aspects list between all points of first and second subjects
            for second in range(len(second_active_points_list)):
                second_name = second_active_points_list[second]["name"]

                # Skip star-star pairs: fixed stars are mutually static, so a
                # cross-chart star-star aspect carries no information (the
                # worst case being same-name pairs like Regulus-Regulus at
                # precession-drift orb in every synastry/transit chart).
                if first_is_star and second_name in star_names:
                    continue

                extra_orb = resolve_pair_orb_adjustment(
                    first_name,
                    second_name,
                    point_orb_adjustments,
                    point_orb_adjustment_strategy,
                )
                aspect = get_aspect_from_two_points(
                    filtered_settings,
                    first_active_points_list[first]["abs_pos"],
                    second_active_points_list[second]["abs_pos"],
                    extra_orb=extra_orb,
                )

                if aspect["verdict"]:
                    # Get planet IDs using lookup dictionary for better performance
                    first_planet_id = planet_id_lookup.get(first_name, 0)
                    second_planet_id = planet_id_lookup.get(second_name, 0)

                    # Get speeds first, fall back to 0.0 only if missing/None
                    first_speed = first_active_points_list[first].get("speed") or 0.0
                    second_speed = second_active_points_list[second].get("speed") or 0.0

                    # Override speeds if subjects are fixed — BEFORE the
                    # axis-axis branch, so axis-axis pairs of a fixed chart
                    # don't persist synthetic cusp speeds (~360°/day) in the
                    # model while every other pair reports 0.0.
                    if first_subject_is_fixed:
                        first_speed = 0.0
                    if second_subject_is_fixed:
                        second_speed = 0.0

                    # For aspects between axes (ASC, MC, DSC, IC) in different charts
                    # there is no meaningful dynamic movement between two house systems,
                    # so we mark the movement as "Static".
                    aspect_movement: AspectMovementType
                    if first_name in AXES_LIST and second_name in AXES_LIST:
                        aspect_movement = "Static"
                    else:
                        # Calculate aspect movement (applying/separating/fixed)
                        aspect_movement = calculate_aspect_movement(
                            first_active_points_list[first]["abs_pos"],
                            second_active_points_list[second]["abs_pos"],
                            aspect["aspect_degrees"],
                            first_speed,
                            second_speed,
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
                        p1_speed=first_speed,
                        p2_speed=second_speed,
                    )
                    all_aspects_list.append(aspect_model)

        return all_aspects_list

    @staticmethod
    def _update_aspect_settings(
        aspects_settings: Sequence[Mapping[str, Any]], active_aspects: List[ActiveAspect]
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
        active_orbs: dict[str, float] = {}
        for a in active_aspects:
            active_orbs.setdefault(a["name"], a["orb"])
        filtered_settings = []
        for aspect_setting in aspects_settings:
            orb = active_orbs.get(aspect_setting["name"])
            if orb is not None:
                aspect_setting_copy = dict(aspect_setting)  # Don't modify original
                aspect_setting_copy["orb"] = orb
                filtered_settings.append(aspect_setting_copy)

        # Warn about active aspect names that have no matching settings entry:
        # they would otherwise be silently dropped from the calculation.
        known_names = {aspect_setting["name"] for aspect_setting in aspects_settings}
        unknown_names = [name for name in active_orbs if name not in known_names]
        if unknown_names:
            declination_names = [n for n in unknown_names if n in ("parallel", "contra-parallel")]
            if declination_names:
                logger.warning(
                    "Declination aspects %s are not handled by the longitudinal aspect "
                    "methods and were ignored; use single_chart_declination_aspects() / "
                    "dual_chart_declination_aspects() instead.",
                    declination_names,
                )
            other_names = [n for n in unknown_names if n not in declination_names]
            if other_names:
                logger.warning(
                    "Unknown active aspect names %s are not present in the chart aspect settings and were ignored.",
                    other_names,
                )
        return filtered_settings

    @staticmethod
    def _filter_relevant_aspects(
        all_aspects: List[AspectModel],
        axis_orb_limit: Optional[float],
    ) -> List[AspectModel]:
        """
        Filter aspects based on orb thresholds for axes and comprehensive criteria.

        This method consolidates all filtering logic including axes checks and orb thresholds
        for both single chart and dual chart aspects in a single comprehensive filtering method.

        Args:
            all_aspects: Complete list of calculated aspects
            axis_orb_limit: Optional orb threshold for axes aspects; when None, no
                axis-specific filtering is applied and all aspects are returned.

        Returns:
            Filtered list of relevant aspects
        """
        logger.debug("Calculating relevant aspects by filtering orbs...")

        relevant_aspects = []

        if axis_orb_limit is None:
            return list(all_aspects)

        if not math.isfinite(axis_orb_limit) or axis_orb_limit <= 0:
            raise KerykeionException("axis_orb_limit must be a positive number when provided")

        for aspect in all_aspects:
            # Check if aspect involves any of the chart axes and apply stricter orb limits
            aspect_involves_axes = aspect.p1_name in AXES_LIST or aspect.p2_name in AXES_LIST

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
    ) -> SingleChartAspectsModel:
        """
        Legacy method - use single_chart_aspects() instead.

        .. deprecated::
            Use :meth:`single_chart_aspects` instead. This alias emits a
            DeprecationWarning and will be removed in kerykeion 7.0.0.
        """
        import warnings

        warnings.warn(
            "natal_aspects is deprecated and will be removed in kerykeion 7.0.0; "
            "use AspectsFactory.single_chart_aspects instead",
            DeprecationWarning,
            stacklevel=2,
        )
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
    ) -> DualChartAspectsModel:
        """
        Legacy method - use dual_chart_aspects() instead.

        .. deprecated::
            Use :meth:`dual_chart_aspects` instead. This alias emits a
            DeprecationWarning and will be removed in kerykeion 7.0.0.
        """
        import warnings

        warnings.warn(
            "synastry_aspects is deprecated and will be removed in kerykeion 7.0.0; "
            "use AspectsFactory.dual_chart_aspects instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return AspectsFactory.dual_chart_aspects(
            first_subject,
            second_subject,
            active_points=active_points,
            active_aspects=active_aspects,
            axis_orb_limit=axis_orb_limit,
        )

    # =========================================================================
    # DECLINATION ASPECTS (Parallels / Contra-Parallels) — v6.0
    # =========================================================================

    @staticmethod
    def single_chart_declination_aspects(
        subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        *,
        active_points: Optional[List[AstrologicalPoint]] = None,
        orb: float = 1.0,
    ) -> List[AspectModel]:
        """
        Calculate declination-based aspects within a single chart.

        Two points form a **parallel** when their declinations are within *orb*
        degrees of each other (both north or both south of the equator).
        A **contra-parallel** occurs when their declinations are equal in
        magnitude but opposite in sign (one north, one south).

        Args:
            subject: The astrological subject.
            orb: Maximum orb in degrees (default 1.0, standard for declination aspects).
                Must be finite and non-negative.
            active_points: Optional list of points to include. As in the
                longitudinal twin (``single_chart_aspects``), the restriction is
                intersected with ``subject.active_points``.

        Returns:
            List of AspectModel with aspect="parallel" or aspect="contra-parallel".
        """
        if not math.isfinite(orb) or orb < 0:
            raise KerykeionException("orb must be a finite non-negative number")

        # v6: extend points_to_use and celestial_points with subject.fixed_stars
        # so catalog stars participate in parallel/contra-parallel aspects too.
        # As in the longitudinal methods, stars are a separate channel and
        # always participate (the active_points restriction governs only the
        # regular points); star–star pairs are skipped downstream.
        from kerykeion.settings.chart_defaults import build_dynamic_fixed_star_settings

        # Same active-points contract as single_chart_aspects: the caller's
        # restriction is intersected with subject.active_points instead of
        # replacing it, so the longitude and declination channels see the same
        # point set for the same arguments.
        subject_active_points = cast("List[Union[AstrologicalPoint, str]]", list(subject.active_points))
        points_to_use: List[Union[AstrologicalPoint, str]] = (
            _find_common_point_names(subject_active_points, list(active_points))
            if active_points is not None
            else subject_active_points
        )
        raw_star_names = [getattr(s, "name", None) for s in getattr(subject, "fixed_stars", None) or []]
        dynamic_star_names: List[str] = [n for n in raw_star_names if n]
        celestial_points = list(DEFAULT_CELESTIAL_POINTS_SETTINGS)
        if dynamic_star_names:
            celestial_points = celestial_points + build_dynamic_fixed_star_settings(
                dynamic_star_names, existing_settings=celestial_points
            )
            # Stars are a separate channel (per-subject opt-in via
            # active_fixed_stars); they participate regardless of the
            # active_points restriction. Star–star pairs are skipped in
            # _compute_declination_aspects.
            points_to_use = list(points_to_use) + [n for n in dynamic_star_names if n not in points_to_use]
        points_list = get_active_points_list(subject, points_to_use, celestial_points=celestial_points)

        return AspectsFactory._compute_declination_aspects(
            points_list,
            points_list,
            subject.name,
            subject.name,
            orb,
            single_chart=True,
            celestial_points=celestial_points,
            star_names=frozenset(dynamic_star_names),
        )

    @staticmethod
    def dual_chart_declination_aspects(
        first_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        second_subject: Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel],
        *,
        active_points: Optional[List[AstrologicalPoint]] = None,
        orb: float = 1.0,
    ) -> List[AspectModel]:
        """
        Calculate declination-based aspects between two charts.

        Args:
            first_subject: First astrological subject.
            second_subject: Second astrological subject.
            orb: Maximum orb in degrees (default 1.0). Must be finite and non-negative.
            active_points: Optional list of points to include. As in the
                longitudinal twin (``dual_chart_aspects``), the restriction is
                intersected with each subject's ``active_points``.

        Returns:
            List of AspectModel with aspect="parallel" or aspect="contra-parallel".
        """
        if not math.isfinite(orb) or orb < 0:
            raise KerykeionException("orb must be a finite non-negative number")

        # v6: extend points + celestial_points with both subjects' fixed_stars
        # so catalog stars participate in parallel/contra-parallel aspects.
        from kerykeion.settings.chart_defaults import build_dynamic_fixed_star_settings

        # Same active-points contract as dual_chart_aspects: the caller's
        # restriction is intersected with each subject's own active_points.
        first_active = cast("List[Union[AstrologicalPoint, str]]", list(first_subject.active_points))
        second_active = cast("List[Union[AstrologicalPoint, str]]", list(second_subject.active_points))
        pts1: List[Union[AstrologicalPoint, str]] = (
            _find_common_point_names(first_active, list(active_points)) if active_points is not None else first_active
        )
        pts2: List[Union[AstrologicalPoint, str]] = (
            _find_common_point_names(second_active, list(active_points)) if active_points is not None else second_active
        )
        dynamic_star_names: list[str] = []
        for subj in (first_subject, second_subject):
            for s in getattr(subj, "fixed_stars", None) or []:
                star_name = getattr(s, "name", None)
                if star_name and star_name not in dynamic_star_names:
                    dynamic_star_names.append(star_name)
        celestial_points = list(DEFAULT_CELESTIAL_POINTS_SETTINGS)
        if dynamic_star_names:
            celestial_points = celestial_points + build_dynamic_fixed_star_settings(
                dynamic_star_names, existing_settings=celestial_points
            )
            pts1 = list(pts1) + [n for n in dynamic_star_names if n not in pts1]
            pts2 = list(pts2) + [n for n in dynamic_star_names if n not in pts2]
        list1 = get_active_points_list(first_subject, pts1, celestial_points=celestial_points)
        list2 = get_active_points_list(second_subject, pts2, celestial_points=celestial_points)

        return AspectsFactory._compute_declination_aspects(
            list1,
            list2,
            first_subject.name,
            second_subject.name,
            orb,
            single_chart=False,
            celestial_points=celestial_points,
            star_names=frozenset(dynamic_star_names),
        )

    @staticmethod
    def _compute_declination_aspects(
        points_a: list,
        points_b: list,
        owner_a: str,
        owner_b: str,
        orb: float,
        *,
        single_chart: bool,
        celestial_points: Optional[list] = None,
        star_names: frozenset = frozenset(),
    ) -> List[AspectModel]:
        """
        Core declination aspect computation shared by single and dual chart methods.

        Args:
            celestial_points: Extended settings list (including dynamic fixed-star
                entries) used for p1/p2 id lookup; defaults to the static settings.
            star_names: Names of catalog fixed stars. Star–star pairs are skipped:
                stars are mutually static, so any star–star parallel is identical
                in every chart and carries no information.
        """
        aspects: List[AspectModel] = []
        id_source = celestial_points if celestial_points is not None else DEFAULT_CELESTIAL_POINTS_SETTINGS
        planet_id_lookup = {p["name"]: p["id"] for p in id_source}

        for i, pa in enumerate(points_a):
            start_j = i + 1 if single_chart else 0
            for j in range(start_j, len(points_b)):
                pb = points_b[j]
                dec_a = pa.get("declination") if hasattr(pa, "get") else getattr(pa, "declination", None)
                dec_b = pb.get("declination") if hasattr(pb, "get") else getattr(pb, "declination", None)

                if dec_a is None or dec_b is None:
                    continue

                name_a = pa["name"] if isinstance(pa, dict) else pa.name
                name_b = pb["name"] if isinstance(pb, dict) else pb.name

                # Geometrically derived opposite pairs (Vertex/Anti-Vertex,
                # node axes, Lilith/Priapus) have rigidly mirrored declinations
                # (their contra-parallel is a construction artifact, not an
                # aspect), and mean×true lunar node combinations share nearly
                # identical declinations (a permanent parallel/contra-parallel).
                # Same-chart only — cross-chart pairs (synastry, transits) are
                # independent points and remain meaningful.
                if single_chart and frozenset((name_a, name_b)) in SINGLE_CHART_ARTIFACT_PAIRS:
                    continue

                # Star–star pairs: fixed stars barely move relative to each
                # other, so these "aspects" are constants across all charts.
                if name_a in star_names and name_b in star_names:
                    continue

                abs_pos_a = pa["abs_pos"] if isinstance(pa, dict) else pa.abs_pos
                abs_pos_b = pb["abs_pos"] if isinstance(pb, dict) else pb.abs_pos

                # Parallel: both declinations same sign AND close in magnitude
                # Contra-parallel: declinations opposite sign AND close in magnitude
                # Use if/elif to prevent reporting BOTH for the same pair
                # (near-zero declinations could match both conditions)
                same_sign = (dec_a >= 0) == (dec_b >= 0)
                parallel_diff = abs(dec_a - dec_b)
                contra_diff = abs(dec_a + dec_b)

                if same_sign and parallel_diff <= orb:
                    aspects.append(
                        AspectModel(
                            p1_name=name_a,
                            p1_owner=owner_a,
                            p1_abs_pos=abs_pos_a,
                            p2_name=name_b,
                            p2_owner=owner_b,
                            p2_abs_pos=abs_pos_b,
                            aspect="parallel",
                            orbit=round(parallel_diff, 6),
                            aspect_degrees=0,
                            diff=round(parallel_diff, 6),
                            p1=planet_id_lookup.get(name_a, 0),
                            p2=planet_id_lookup.get(name_b, 0),
                            aspect_movement="Static",
                            p1_speed=0.0,
                            p2_speed=0.0,
                        )
                    )
                elif not same_sign and contra_diff <= orb:
                    aspects.append(
                        AspectModel(
                            p1_name=name_a,
                            p1_owner=owner_a,
                            p1_abs_pos=abs_pos_a,
                            p2_name=name_b,
                            p2_owner=owner_b,
                            p2_abs_pos=abs_pos_b,
                            aspect="contra-parallel",
                            orbit=round(contra_diff, 6),
                            aspect_degrees=0,
                            diff=round(contra_diff, 6),
                            p1=planet_id_lookup.get(name_a, 0),
                            p2=planet_id_lookup.get(name_b, 0),
                            aspect_movement="Static",
                            p1_speed=0.0,
                            p2_speed=0.0,
                        )
                    )

        return aspects


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
