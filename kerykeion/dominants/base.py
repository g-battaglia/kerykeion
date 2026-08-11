# -*- coding: utf-8 -*-
"""
Strategy contract and shared machinery for the dominants calculator.
====================================================================

This module defines the seam that makes the calculator extensible:

- :class:`DominantStrategy` — a structural ``typing.Protocol``. Anything with a
  ``name`` and a ``compute(subject, config)`` method that returns a
  :class:`DominantsModel` is a valid strategy, so users can plug in their own
  school without subclassing anything (mirrors the project's existing
  ``ChartRendererProtocol`` idiom).
- :class:`BaseDominantStrategy` — an optional convenience base implementing the
  *Template Method* pattern: it owns the boring, shared work (ranking a category,
  normalizing percentages, choosing winners, assembling the public model) so a
  concrete school only has to produce raw per-category scores.
- :class:`DominantsConfig` — the single, growable bag of options the factory
  injects into a strategy, keeping ``compute``'s signature stable over time.

The intermediate value objects (:class:`Category`, :class:`BreakdownItem`) are
plain dataclasses so strategies never touch Pydantic directly; the base class is
the one place that builds the public :class:`DominantsModel`.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional, Protocol, cast, runtime_checkable

from kerykeion.dominants.data import DOMINANT_PLANET_COUNT
from kerykeion.schemas.literals import DominantMethod, Element, Houses, Quality, Sign
from kerykeion.schemas.models import (
    AstrologicalSubjectModel,
    DominantBreakdownItemModel,
    DominantScoreModel,
    DominantsModel,
)
from kerykeion.utilities import distribute_percentages_to_100

#: Allowed distribution methods for the element/quality tally (mirrors
#: ``charts_utils.ElementQualityDistributionMethod`` without importing the
#: rendering package).
DistributionMethod = Literal["pure_count", "weighted"]

#: The fixed set of categories every result exposes, in display order. The base
#: class always emits all of them so the public model shape is stable.
CATEGORY_NAMES: tuple[str, ...] = (
    "planets",
    "signs",
    "elements",
    "qualities",
    "houses",
    "polarities",
    "hemispheres",
    "quadrants",
)


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class DominantsConfig:
    """Tunable options passed by the factory into a strategy's ``compute``.

    Bundling the knobs in one object keeps the strategy contract stable as
    options are added (open/closed principle): new fields here never change the
    ``compute`` signature.

    Attributes:
        active_points: Optional explicit subset of point names to consider. When
            ``None``, each school uses its natural default set.
        distribution_method: ``"weighted"`` (default) or ``"pure_count"`` for the
            element/modality tally.
        custom_weights: Optional per-point weight overrides for the element/
            modality tally (case-insensitive point names).
        include_accidental_dignities: When ``True``, the Almuten Figuris adds its
            optional accidental-dignity layer (house placement, day ruler).
        include_score_breakdown: When ``True``, strategies populate the model's
            ``score_breakdown`` with a per-rule audit trail.
        dominant_planet_count: How many top planets are flagged as dominant.
    """

    active_points: Optional[List[str]] = None
    distribution_method: DistributionMethod = "weighted"
    custom_weights: Optional[Dict[str, float]] = None
    include_accidental_dignities: bool = False
    include_score_breakdown: bool = False
    dominant_planet_count: int = DOMINANT_PLANET_COUNT


# =============================================================================
# INTERNAL VALUE OBJECTS (no Pydantic — strategies stay model-agnostic)
# =============================================================================


@dataclass
class Category:
    """Raw scores for one dominant category, before ranking.

    Attributes:
        scores: Mapping of item name to raw score (e.g. ``{"Sun": 12.4}``).
        dominant: The subset of names a school flags as dominant for this
            category (e.g. the top-N planets, or elements above a threshold).
        tiebreak_order: Optional priority order for breaking equal-score ties in
            the ranked output. When set, ties are broken by position in this
            sequence instead of alphabetically, so the ranked list's rank 1
            agrees with a school that picks its winner by the same order (e.g.
            the Almuten Figuris' traditional Saturn->Moon order). Names absent
            from the sequence sort after those present, then alphabetically.
    """

    scores: Dict[str, float] = field(default_factory=dict)
    dominant: set[str] = field(default_factory=set)
    tiebreak_order: Optional[tuple] = None


@dataclass
class BreakdownItem:
    """A single audit line for ``score_breakdown`` (see the public model)."""

    category: str
    target: str
    rule: str
    points: float
    detail: Optional[str] = None


# =============================================================================
# STRATEGY PROTOCOL
# =============================================================================


@runtime_checkable
class DominantStrategy(Protocol):
    """Structural contract for a dominant-calculation school.

    Any object exposing a ``name`` attribute and a ``compute`` method with the
    signature below satisfies the protocol — no inheritance required. This is
    the extension point for user-defined schools.

    Attributes:
        name: Human-readable identifier of the school, copied into
            :attr:`DominantsModel.strategy_name`.
    """

    name: str

    def compute(self, subject: AstrologicalSubjectModel, config: DominantsConfig) -> DominantsModel:
        """Compute the dominants of ``subject`` under ``config``.

        Args:
            subject: The (already calculated) natal/event chart.
            config: Options bundle (see :class:`DominantsConfig`).

        Returns:
            A fully populated :class:`DominantsModel`.
        """
        ...


# =============================================================================
# OPTIONAL BASE CLASS (Template Method)
# =============================================================================


class BaseDominantStrategy:
    """Convenience base that centralizes ranking, normalization and assembly.

    A concrete school subclasses this, sets :attr:`name` (and optionally
    :attr:`method`), and produces raw :class:`Category` scores; the inherited
    :meth:`build_model` turns those into the ranked, percentage-normalized public
    model. Subclassing is optional — see :class:`DominantStrategy`.

    Attributes:
        name: Identifier of the school (overridden by subclasses).
        method: The built-in :data:`DominantMethod` this school implements, or
            ``None`` for a custom strategy.
    """

    name: str = "base"
    method: Optional[DominantMethod] = None

    def compute(self, subject: AstrologicalSubjectModel, config: DominantsConfig) -> DominantsModel:
        """Compute the dominants. Must be overridden by concrete schools."""
        raise NotImplementedError(f"{type(self).__name__} must implement compute(subject, config).")

    # -- shared helpers -----------------------------------------------------

    @staticmethod
    def _rank_category(category: Category) -> List[DominantScoreModel]:
        """Rank one category's raw scores into ordered :class:`DominantScoreModel`.

        Entries are sorted by descending score with a deterministic name-based
        tie-break. Percentages are computed over the non-negative part of the
        scores (negative scores, e.g. dignity penalties, would otherwise distort
        a share-of-total) and reuse the library's largest-remainder rounding.

        Args:
            category: The raw scores and dominant flags for the category.

        Returns:
            Ranked score models (rank 1 = strongest); empty if no scores.
        """
        scores = category.scores
        if not scores:
            return []

        order = category.tiebreak_order
        if order:
            rank_of = {name: i for i, name in enumerate(order)}
            ordered = sorted(
                scores.items(),
                key=lambda kv: (-kv[1], rank_of.get(kv[0], len(order)), kv[0]),
            )
        else:
            ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
        percentages = distribute_percentages_to_100({name: max(0.0, value) for name, value in scores.items()})

        return [
            DominantScoreModel(
                name=name,
                score=round(value, 4),
                percentage=float(percentages.get(name, 0)),
                rank=rank,
                is_dominant=name in category.dominant,
            )
            for rank, (name, value) in enumerate(ordered, start=1)
        ]

    @staticmethod
    def _winner(items: List[DominantScoreModel]) -> Optional[str]:
        """Return the name of the category winner.

        The winner is the highest-ranked entry flagged dominant; if a school
        flags none, the top-ranked entry is used. ``None`` for an empty category.
        """
        for item in items:
            if item.is_dominant:
                return item.name
        return items[0].name if items else None

    def build_model(
        self,
        *,
        categories: Dict[str, Category],
        breakdown: Optional[List[BreakdownItem]] = None,
    ) -> DominantsModel:
        """Assemble the public :class:`DominantsModel` from raw categories.

        Args:
            categories: Raw scores keyed by category name (see
                :data:`CATEGORY_NAMES`). Missing categories become empty lists.
            breakdown: Optional audit trail; included verbatim in the model.

        Returns:
            The ranked, percentage-normalized, winner-annotated model.
        """
        ranked: Dict[str, List[DominantScoreModel]] = {
            name: self._rank_category(categories.get(name, Category())) for name in CATEGORY_NAMES
        }

        breakdown_models = [
            DominantBreakdownItemModel(
                category=item.category,
                target=item.target,
                rule=item.rule,
                points=round(item.points, 4),
                detail=item.detail,
            )
            for item in (breakdown or [])
        ]

        return DominantsModel(
            strategy_name=self.name,
            method=self.method,
            planets=ranked["planets"],
            signs=ranked["signs"],
            elements=ranked["elements"],
            qualities=ranked["qualities"],
            houses=ranked["houses"],
            polarities=ranked["polarities"],
            hemispheres=ranked["hemispheres"],
            quadrants=ranked["quadrants"],
            dominant_planet=self._winner(ranked["planets"]),
            # _winner returns the winning entry's plain-str name; for the
            # literal-typed fields the names are by construction members of the
            # literal (and Pydantic re-validates them at model construction).
            dominant_sign=cast(Optional[Sign], self._winner(ranked["signs"])),
            dominant_element=cast(Optional[Element], self._winner(ranked["elements"])),
            dominant_quality=cast(Optional[Quality], self._winner(ranked["qualities"])),
            dominant_house=cast(Optional[Houses], self._winner(ranked["houses"])),
            score_breakdown=breakdown_models,
        )
