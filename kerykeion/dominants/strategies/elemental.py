# -*- coding: utf-8 -*-
"""
Elemental & modal balance — the simplest dominant school.
=========================================================

This school answers the everyday question "is this an Air chart? a Fixed
chart?" by tallying the chart's points per element (Fire/Earth/Air/Water) and
per modality (Cardinal/Fixed/Mutable), then taking the heaviest of each. It is
intentionally thin: it delegates the actual counting to the library's existing
``calculate_element_points`` / ``calculate_quality_points`` so the numbers match
the element/quality distributions shown elsewhere (charts, reports), including
the ``"weighted"`` vs ``"pure_count"`` methods and per-point weight overrides.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, cast

from kerykeion.dominants.base import BaseDominantStrategy, BreakdownItem, Category, DominantsConfig
from kerykeion.dominants.data import (
    ELEMENT_LOWER_TO_TITLE,
    POLARITY_BY_ELEMENT,
    QUALITY_LOWER_TO_TITLE,
)
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, DominantsModel

if TYPE_CHECKING:
    from typing import Sequence

    from kerykeion.schemas.kr_literals import Element
    from kerykeion.schemas.settings_models import KerykeionSettingsCelestialPointModel


class ElementalBalanceStrategy(BaseDominantStrategy):
    """Dominant element and modality by weighted (or pure) count.

    Populates the ``elements``, ``qualities`` and ``polarities`` categories; the
    planet/sign/house/hemisphere/quadrant categories are left empty (this school
    does not score them). The dominant of each populated category is its single
    heaviest entry.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, DominantsFactory
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "John Lennon", 1940, 10, 9, 18, 30,
        ...     lat=53.4084, lng=-2.9916, tz_str="Europe/London", online=False)
        >>> result = DominantsFactory.from_subject(subject, strategy="elemental")
        >>> result.dominant_element, result.dominant_quality  # doctest: +SKIP
        ('Air', 'Cardinal')
    """

    name = "elemental"
    method = "elemental"

    def compute(self, subject: AstrologicalSubjectModel, config: DominantsConfig) -> DominantsModel:
        """Tally elements and modalities and pick the heaviest of each.

        Args:
            subject: The chart to analyse.
            config: Options; honours ``distribution_method``, ``custom_weights``
                and ``active_points``.

        Returns:
            A :class:`DominantsModel` with the element, quality and polarity
            categories populated.
        """
        # Local import: the element/quality helpers live in the (heavier) charts
        # package; importing lazily keeps the dominants package import-light and
        # free of any import-time coupling to the rendering code.
        from kerykeion.charts.charts_utils import calculate_element_points, calculate_quality_points
        from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS

        point_names: List[str] = list(config.active_points) if config.active_points else list(subject.active_points)

        # ``planets_settings`` is kept by the helpers for API compatibility only
        # (unused), so the TypedDict-based defaults are safe to pass here.
        planets_settings = cast("Sequence[KerykeionSettingsCelestialPointModel]", DEFAULT_CELESTIAL_POINTS_SETTINGS)

        # Raw totals come back keyed lowercase (e.g. "fire"); we relabel them to
        # the Title-case Element/Quality literals the public model expects.
        element_totals = calculate_element_points(
            planets_settings,
            point_names,
            subject,
            method=config.distribution_method,
            custom_weights=config.custom_weights,
        )
        quality_totals = calculate_quality_points(
            planets_settings,
            point_names,
            subject,
            method=config.distribution_method,
            custom_weights=config.custom_weights,
        )

        elements: Dict[str, float] = {ELEMENT_LOWER_TO_TITLE[key]: value for key, value in element_totals.items()}
        qualities: Dict[str, float] = {QUALITY_LOWER_TO_TITLE[key]: value for key, value in quality_totals.items()}

        # Polarity: Fire+Air = Yang, Earth+Water = Yin. The keys of ``elements``
        # are exactly the Title-case Element literals built just above.
        polarities: Dict[str, float] = {"Yang": 0.0, "Yin": 0.0}
        for element, value in elements.items():
            polarities[POLARITY_BY_ELEMENT[cast("Element", element)]] += value

        categories = {
            "elements": Category(scores=elements, dominant=_top_keys(elements, 1)),
            "qualities": Category(scores=qualities, dominant=_top_keys(qualities, 1)),
            "polarities": Category(scores=polarities, dominant=_top_keys(polarities, 1)),
        }

        breakdown: List[BreakdownItem] = []
        if config.include_score_breakdown:
            for element, value in elements.items():
                breakdown.append(BreakdownItem("element", element, config.distribution_method, value))
            for quality, value in qualities.items():
                breakdown.append(BreakdownItem("quality", quality, config.distribution_method, value))

        return self.build_model(categories=categories, breakdown=breakdown)


def _top_keys(scores: Dict[str, float], count: int) -> set[str]:
    """Return the ``count`` highest-scoring keys (deterministic tie-break by name).

    Args:
        scores: Mapping of name to score.
        count: How many top keys to return.

    Returns:
        The set of the highest-scoring keys.
    """
    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    return {name for name, _ in ordered[:count]}
