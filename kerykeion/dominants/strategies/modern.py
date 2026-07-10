# -*- coding: utf-8 -*-
"""
Modern weighted dominants (Astrotheme-style).
==============================================

The popular modern method: each planet accumulates a strength score from four
parameters, and the chart's dominant signs, houses, elements, modes, polarity,
hemispheres and quadrants are then derived from those planetary scores.

A planet's score = angularity + aspect activity + essential dignity + rulership:

1. **Angularity** — proximity to the four angles (Asc > MC > Desc > IC), within a
   15° orb, the contribution fading linearly to zero at the edge of the orb.
2. **Aspect activity** — every aspect the planet makes, weighted by aspect type,
   by orb exactitude (tighter = stronger), and by a static "speed tier" so a
   slow Neptune-Pluto aspect counts far less than a fast Moon-Mars one; aspects
   to an angle are emphasised.
3. **Essential dignity** — a deliberately mild bonus for the planet's highest
   dignity, with detriment/fall penalties applied additively so a minor
   dignity (term, face, triplicity) never masks a debility (kept small so it
   never distorts the result).
4. **Rulership** — a bonus for ruling the Ascendant (largest), the MC, the Sun
   sign and the Moon sign.

Speed and retrogradation are deliberately **excluded** from the scoring, as in
Astrotheme's documented method. The exact point values Astrotheme uses are
proprietary; the constants in :mod:`kerykeion.dominants.data` are a transparent,
tunable approximation of the documented behaviour.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import Dict, List, Optional, cast

from kerykeion.dignities.dignity_data import DETRIMENT_RULERS, FALL_TABLE
from kerykeion.dignities.dignity_factory import calculate_essential_dignity
from kerykeion.dominants.base import BaseDominantStrategy, BreakdownItem, Category, DominantsConfig
from kerykeion.dominants.data import (
    ANGLE_WEIGHTS,
    ANGULARITY_MAX_POINTS,
    ANGULARITY_ORB,
    ASC_SIGN_BONUS,
    ASPECT_BASE_POINTS,
    ASPECT_ORB_BY_NAME,
    ASPECT_STRENGTH,
    ASPECT_TO_ANGLE_MULTIPLIER,
    DIGNITY_BONUS,
    DOMINANT_HOUSE_COUNT,
    DOMINANT_SIGN_COUNT,
    DOMINANT_ASPECTS,
    MODERN_RULERS,
    PLANET_SPEED_TIER,
    PLANET_SPEED_TIER_DEFAULT,
    POLARITY_BY_ELEMENT,
    RULER_BONUS_ASC,
    RULER_BONUS_MC,
    RULER_BONUS_MOON_SIGN,
    RULER_BONUS_SUN_SIGN,
)
from kerykeion.dominants.utils import angle_degrees, rulers_inverse, scoring_planets
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, DominantsModel, KerykeionPointModel
from kerykeion.utilities import get_house_number, resolve_sect_is_diurnal

#: The four chart angles, in the order the engine references them.
_ANGLE_NAMES: tuple[str, ...] = ("Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli")

#: Subject attributes for the twelve house cusps, in order 1..12.
_HOUSE_ATTRS: tuple[str, ...] = (
    "first_house",
    "second_house",
    "third_house",
    "fourth_house",
    "fifth_house",
    "sixth_house",
    "seventh_house",
    "eighth_house",
    "ninth_house",
    "tenth_house",
    "eleventh_house",
    "twelfth_house",
)

#: House numbers in the eastern half of the chart (Ascendant side).
_EASTERN_HOUSES = frozenset({10, 11, 12, 1, 2, 3})

#: Quadrant name by 1-based quadrant index.
_QUADRANT_NAMES = ("First_Quadrant", "Second_Quadrant", "Third_Quadrant", "Fourth_Quadrant")


def _angular_separation(a: float, b: float) -> float:
    """Smallest separation between two ecliptic longitudes (0-180°)."""
    diff = abs(a - b) % 360.0
    return min(diff, 360.0 - diff)


class ModernDominantStrategy(BaseDominantStrategy):
    """Modern weighted dominants for every category Astrotheme reports.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, DominantsFactory
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "John Lennon", 1940, 10, 9, 18, 30,
        ...     lat=53.4084, lng=-2.9916, tz_str="Europe/London", online=False)
        >>> result = DominantsFactory.from_subject(subject, strategy="modern")
        >>> result.dominant_planet, result.dominant_sign  # doctest: +SKIP
        ('Mars', 'Tau')
    """

    name = "modern"
    method = "modern"

    def compute(self, subject: AstrologicalSubjectModel, config: DominantsConfig) -> DominantsModel:
        """Score the planets, then derive every dominant category from them.

        Args:
            subject: The chart to analyse.
            config: Options; honours ``dominant_planet_count`` and
                ``include_score_breakdown``.

        Returns:
            A fully populated :class:`DominantsModel`.
        """
        planets = scoring_planets(subject)
        planet_names = [point.name for point in planets]
        angles = angle_degrees(subject)
        include_breakdown = config.include_score_breakdown
        breakdown: List[BreakdownItem] = []

        # --- planetary strength = four additive parameters ------------------
        angularity = self._angularity_scores(planets, angles, breakdown, include_breakdown)
        activity = self._aspect_scores(subject, planet_names, breakdown, include_breakdown)
        dignity = self._dignity_scores(subject, planets, breakdown, include_breakdown)
        rulership = self._rulership_scores(subject, planet_names, breakdown, include_breakdown)

        totals: Dict[str, float] = {
            name: angularity.get(name, 0.0)
            + activity.get(name, 0.0)
            + dignity.get(name, 0.0)
            + rulership.get(name, 0.0)
            for name in planet_names
        }
        dominant_planets = _top_keys(totals, config.dominant_planet_count)

        # --- derive the remaining categories from the planetary scores ------
        categories = {
            "planets": Category(scores=totals, dominant=dominant_planets),
            "signs": self._sign_category(subject, planets, totals, dominant_planets),
            "houses": self._house_category(subject, planets, totals, dominant_planets),
            "elements": self._element_category(planets, totals),
            "qualities": self._quality_category(planets, totals),
            "polarities": self._polarity_category(planets, totals),
            "hemispheres": self._hemisphere_category(planets, totals),
            "quadrants": self._quadrant_category(planets, totals),
        }

        return self.build_model(categories=categories, breakdown=breakdown)

    # -- parameter 1: angularity -------------------------------------------

    @staticmethod
    def _angularity_scores(
        planets: List[KerykeionPointModel],
        angles: Dict[str, Optional[float]],
        breakdown: List[BreakdownItem],
        include_breakdown: bool,
    ) -> Dict[str, float]:
        """Score each planet by its proximity to the four angles.

        The contribution from an angle is ``ANGULARITY_MAX_POINTS`` scaled by the
        angle's weight and by a linear orb falloff (full strength at exact
        conjunction, zero at ``ANGULARITY_ORB``). Contributions from all angles
        are summed.
        """
        scores: Dict[str, float] = {}
        for point in planets:
            total = 0.0
            for angle_name, angle_degree in angles.items():
                if angle_degree is None:
                    continue
                separation = _angular_separation(point.abs_pos, angle_degree)
                if separation > ANGULARITY_ORB:
                    continue
                falloff = (ANGULARITY_ORB - separation) / ANGULARITY_ORB
                contribution = ANGULARITY_MAX_POINTS * ANGLE_WEIGHTS[angle_name] * falloff
                total += contribution
                if include_breakdown and contribution > 0:
                    breakdown.append(
                        BreakdownItem(
                            "angularity", point.name, f"near {angle_name}", contribution, f"orb {separation:.1f}°"
                        )
                    )
            scores[point.name] = total
        return scores

    # -- parameter 2: aspect activity --------------------------------------

    @staticmethod
    def _aspect_scores(
        subject: AstrologicalSubjectModel,
        planet_names: List[str],
        breakdown: List[BreakdownItem],
        include_breakdown: bool,
    ) -> Dict[str, float]:
        """Score each planet by the weighted activity of the aspects it makes.

        A single pass over the chart's aspects feeds both endpoints: each scoring
        planet gains points for every aspect it is part of, weighted by aspect
        type, orb exactitude, the speed tiers of the two bodies, and an angle
        bonus when the partner is one of the four angles.
        """
        # Local import keeps the dominants package free of an import-time
        # dependency on the (heavier) aspects/subject machinery.
        from kerykeion.aspects.aspects_factory import AspectsFactory

        scores: Dict[str, float] = {name: 0.0 for name in planet_names}
        planet_set = set(planet_names)
        angle_set = set(_ANGLE_NAMES)

        # The names come from the subject's own points plus the four angles,
        # so they are valid AstrologicalPoint literals at runtime.
        requested_points = cast(List[AstrologicalPoint], planet_names + list(_ANGLE_NAMES))
        # single_chart_aspects intersects the requested points with
        # subject.active_points, which by default excludes Descendant and
        # Imum_Coeli. The angularity channel reads all four angles straight
        # from the model, so without this widening the dominants ranking
        # would depend on the subject's active_points configuration rather
        # than on the birth data alone.
        aspect_subject = subject.model_copy(
            update={"active_points": list(dict.fromkeys([*subject.active_points, *requested_points]))}
        )
        aspects_model = AspectsFactory.single_chart_aspects(
            aspect_subject,
            active_points=requested_points,
            active_aspects=DOMINANT_ASPECTS,
        )

        for aspect in aspects_model.aspects:
            type_weight = ASPECT_STRENGTH.get(aspect.aspect_degrees, 0.0)
            orb_limit = ASPECT_ORB_BY_NAME.get(aspect.aspect)
            if type_weight <= 0.0 or not orb_limit:
                continue
            orb_weight = max(0.0, 1.0 - abs(aspect.orbit) / orb_limit)
            if orb_weight <= 0.0:
                continue

            # Feed both endpoints: each scoring planet sees the other as partner.
            for primary, partner in ((aspect.p1_name, aspect.p2_name), (aspect.p2_name, aspect.p1_name)):
                if primary not in planet_set:
                    continue
                pair_weight = (
                    PLANET_SPEED_TIER.get(primary, PLANET_SPEED_TIER_DEFAULT)
                    + PLANET_SPEED_TIER.get(partner, PLANET_SPEED_TIER_DEFAULT)
                ) / 2.0
                angle_weight = ASPECT_TO_ANGLE_MULTIPLIER if partner in angle_set else 1.0
                contribution = ASPECT_BASE_POINTS * type_weight * orb_weight * pair_weight * angle_weight
                scores[primary] += contribution
                if include_breakdown and contribution > 0:
                    breakdown.append(
                        BreakdownItem(
                            "aspect",
                            primary,
                            f"{aspect.aspect} {partner}",
                            contribution,
                            f"orb {abs(aspect.orbit):.1f}°",
                        )
                    )
        return scores

    # -- parameter 3: essential dignity (mild) -----------------------------

    @staticmethod
    def _dignity_scores(
        subject: AstrologicalSubjectModel,
        planets: List[KerykeionPointModel],
        breakdown: List[BreakdownItem],
        include_breakdown: bool,
    ) -> Dict[str, float]:
        """Apply a small bonus/penalty for each planet's essential dignity.

        The planet's *highest* dignity supplies the bonus, and the detriment/
        fall penalties are applied additively on top (straight from the
        dignity tables). Dignities and debilities are independent, so a minor
        dignity must never mask a debility: Mars at 28° Libra sits in its own
        Egyptian term AND in detriment, scoring 0.25 - 1.00 = -0.75 — not the
        bare +0.25 the "Term" label alone would suggest.
        """
        is_diurnal = resolve_sect_is_diurnal(subject)
        scores: Dict[str, float] = {}
        for point in planets:
            result = calculate_essential_dignity(point.name, point.sign, point.element, point.position, is_diurnal)
            label = result.get("essential_dignity")
            if label is None:  # non-classical body: no essential dignity
                scores[point.name] = 0.0
                continue
            # Bonus of the highest dignity. The dignity factory relabels a
            # dignity-less debilitated planet as Detriment/Fall — skip those
            # labels here, the additive penalties below already cover them.
            components: List[tuple[str, float]] = []
            if label not in ("Detriment", "Fall"):
                label_bonus = DIGNITY_BONUS.get(label, 0.0)
                if label_bonus:
                    components.append((label, label_bonus))
            if point.name in DETRIMENT_RULERS.get(point.sign, []):
                components.append(("Detriment", DIGNITY_BONUS["Detriment"]))
            if FALL_TABLE.get(point.sign) == point.name:
                components.append(("Fall", DIGNITY_BONUS["Fall"]))
            scores[point.name] = sum(value for _, value in components)
            if include_breakdown:
                for component_label, value in components:
                    breakdown.append(BreakdownItem("dignity", point.name, component_label, value, point.sign))
        return scores

    # -- parameter 4: rulership --------------------------------------------

    @staticmethod
    def _rulership_scores(
        subject: AstrologicalSubjectModel,
        planet_names: List[str],
        breakdown: List[BreakdownItem],
        include_breakdown: bool,
    ) -> Dict[str, float]:
        """Bonus the rulers of the Ascendant, MC, Sun sign and Moon sign.

        The Ascendant ruler gets the largest bonus, then the MC ruler, then the
        rulers of the Sun and Moon signs (modern rulerships).
        """
        scores: Dict[str, float] = {name: 0.0 for name in planet_names}
        planet_set = set(planet_names)

        key_signs = (
            (subject.ascendant, RULER_BONUS_ASC, "ruler of Ascendant"),
            (subject.medium_coeli, RULER_BONUS_MC, "ruler of MC"),
            (subject.sun, RULER_BONUS_SUN_SIGN, "ruler of Sun sign"),
            (subject.moon, RULER_BONUS_MOON_SIGN, "ruler of Moon sign"),
        )
        for point, bonus, rule in key_signs:
            if point is None:
                continue
            for ruler in MODERN_RULERS.get(point.sign, []):
                if ruler in planet_set:
                    scores[ruler] += bonus
                    if include_breakdown:
                        breakdown.append(BreakdownItem("rulership", ruler, rule, bonus, point.sign))
        return scores

    # -- derivations --------------------------------------------------------

    @staticmethod
    def _sign_category(
        subject: AstrologicalSubjectModel,
        planets: List[KerykeionPointModel],
        totals: Dict[str, float],
        dominant_planets: set[str],
    ) -> Category:
        """Derive dominant signs from occupancy, the Ascendant, and rulership.

        A sign accrues weight from (a) the scores of the planets occupying it,
        (b) a flat bonus for the rising sign, and (c) the scores of the dominant
        planets that rule it (modern rulerships).
        """
        scores: Dict[str, float] = {}
        for point in planets:
            value = totals[point.name]
            if value > 0:
                scores[point.sign] = scores.get(point.sign, 0.0) + value

        if subject.ascendant is not None:
            scores[subject.ascendant.sign] = scores.get(subject.ascendant.sign, 0.0) + ASC_SIGN_BONUS

        ruled_by = rulers_inverse(MODERN_RULERS)
        for planet in dominant_planets:
            for sign in ruled_by.get(planet, []):
                scores[sign] = scores.get(sign, 0.0) + totals[planet]

        return Category(scores=scores, dominant=_top_keys(scores, DOMINANT_SIGN_COUNT))

    @staticmethod
    def _house_category(
        subject: AstrologicalSubjectModel,
        planets: List[KerykeionPointModel],
        totals: Dict[str, float],
        dominant_planets: set[str],
    ) -> Category:
        """Derive dominant houses from occupancy plus dominant-ruler emphasis.

        Each house accrues the scores of the planets it contains; additionally a
        house whose cusp sign is ruled by a dominant planet gains half that
        planet's score. Houses are skipped entirely for charts without a known
        birth time (no house placements).
        """
        scores: Dict[str, float] = {}
        for point in planets:
            if point.house is None:
                continue
            scores[point.house] = scores.get(point.house, 0.0) + totals[point.name]

        # Emphasise houses whose cusp is ruled by a dominant planet.
        for attr in _HOUSE_ATTRS:
            cusp = getattr(subject, attr, None)
            if cusp is None:
                continue
            for ruler in MODERN_RULERS.get(cusp.sign, []):
                if ruler in dominant_planets:
                    scores[cusp.name] = scores.get(cusp.name, 0.0) + totals[ruler] * 0.5

        return Category(scores=scores, dominant=_top_keys(scores, DOMINANT_HOUSE_COUNT))

    @staticmethod
    def _element_category(planets: List[KerykeionPointModel], totals: Dict[str, float]) -> Category:
        """Score-weighted element tally (each planet's element gains its score)."""
        scores: Dict[str, float] = {}
        for point in planets:
            scores[point.element] = scores.get(point.element, 0.0) + totals[point.name]
        return Category(scores=scores, dominant=_top_keys(scores, 1))

    @staticmethod
    def _quality_category(planets: List[KerykeionPointModel], totals: Dict[str, float]) -> Category:
        """Score-weighted modality tally (each planet's modality gains its score)."""
        scores: Dict[str, float] = {}
        for point in planets:
            scores[point.quality] = scores.get(point.quality, 0.0) + totals[point.name]
        return Category(scores=scores, dominant=_top_keys(scores, 1))

    @staticmethod
    def _polarity_category(planets: List[KerykeionPointModel], totals: Dict[str, float]) -> Category:
        """Yang (Fire+Air) vs Yin (Earth+Water), score-weighted."""
        scores: Dict[str, float] = {"Yang": 0.0, "Yin": 0.0}
        for point in planets:
            scores[POLARITY_BY_ELEMENT[point.element]] += totals[point.name]
        return Category(scores=scores, dominant=_top_keys(scores, 1))

    @staticmethod
    def _hemisphere_category(planets: List[KerykeionPointModel], totals: Dict[str, float]) -> Category:
        """North/South (below/above horizon) and East/West, score-weighted.

        Uses each planet's house: houses 1-6 are the Northern (below-horizon)
        hemisphere and 7-12 the Southern; houses 10-3 are the Eastern
        (Ascendant-side) hemisphere and 4-9 the Western.
        """
        scores: Dict[str, float] = {"North": 0.0, "South": 0.0, "East": 0.0, "West": 0.0}
        for point in planets:
            if point.house is None:
                continue
            house_number = get_house_number(point.house)
            value = totals[point.name]
            scores["North" if house_number <= 6 else "South"] += value
            scores["East" if house_number in _EASTERN_HOUSES else "West"] += value

        # Flag the winner of each independent axis as dominant.
        dominant = {
            max(("North", "South"), key=lambda key: scores[key]),
            max(("East", "West"), key=lambda key: scores[key]),
        }
        return Category(scores=scores, dominant=dominant)

    @staticmethod
    def _quadrant_category(planets: List[KerykeionPointModel], totals: Dict[str, float]) -> Category:
        """Score-weighted distribution across the four quadrants (houses 1-3, …)."""
        scores: Dict[str, float] = {name: 0.0 for name in _QUADRANT_NAMES}
        for point in planets:
            if point.house is None:
                continue
            quadrant_index = (get_house_number(point.house) - 1) // 3
            scores[_QUADRANT_NAMES[quadrant_index]] += totals[point.name]
        return Category(scores=scores, dominant=_top_keys(scores, 1))


def _top_keys(scores: Dict[str, float], count: int) -> set[str]:
    """Return the ``count`` highest-scoring keys (deterministic tie-break by name).

    Keys with a non-positive score are never flagged dominant, so an empty or
    all-zero category yields no dominants.
    """
    positive = {name: value for name, value in scores.items() if value > 0}
    ordered = sorted(positive.items(), key=lambda kv: (-kv[1], kv[0]))
    return {name for name, _ in ordered[:count]}
