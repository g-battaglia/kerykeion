# -*- coding: utf-8 -*-
"""
Almuten Figuris — the traditional "Lord of the Geniture".
=========================================================

A medieval/Renaissance technique for the single planet that most rules a chart.
For each of the five *hylegiacal places* — the degrees of the Sun, the Moon, the
Ascendant, the Part of Fortune and the prenatal Syzygy — every classical planet
earns points for the essential dignities it holds over that degree:

    Domicile 5 · Exaltation 4 · Triplicity 3 (by sect) · Term 2 · Face 1

The planet with the highest total across all places is the Almuten Figuris. An
optional accidental-dignity layer (house placement, weekday ruler) can be added
on request; the essential tally is the firm core and the default.

Reference: kerykeion.net "The Almuten Figuris". The dignity tables themselves are
reused verbatim from :mod:`kerykeion.dignities.dignity_data`, so this school is
consistent with the rest of the library's traditional astrology.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from kerykeion.dignities.dignity_data import DOMICILE_RULERS, EXALTATION_TABLE, TRIPLICITY_RULERS

# The term/face lookups are non-trivial (Egyptian bounds, Chaldean decans); we
# reuse the dignity engine's helpers rather than duplicate those tables.
from kerykeion.dignities.dignity_factory import _get_decan, _get_decan_ruler, _get_term_ruler
from kerykeion.dominants.base import BaseDominantStrategy, BreakdownItem, Category, DominantsConfig
from kerykeion.dominants.data import (
    ALMUTEN_DAY_RULER_BONUS,
    ALMUTEN_HOUSE_PLACEMENT_POINTS,
    ALMUTEN_TIEBREAK_ORDER,
    CLASSICAL_PLANETS,
    ESSENTIAL_DIGNITY_POINTS,
    WEEKDAY_RULERS,
)
from kerykeion.dominants.utils import ZodiacPosition, part_of_fortune_degree, prenatal_syzygy, zodiac_breakdown
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, DominantsModel
from kerykeion.utilities import get_house_number


class AlmutenFigurisStrategy(BaseDominantStrategy):
    """Compute the Almuten Figuris (traditional Lord of the Geniture).

    Populates the ``planets`` category (all seven classical planets, ranked by
    dignity total) and, for convenience, fills the winner's sign / element /
    modality / house into the matching single-entry categories. Modern points
    and the polarity/hemisphere/quadrant categories are not part of this
    technique and stay empty.

    Note:
        The technique is traditionally **tropical**. For a sidereal subject the
        dignities are tallied on the sidereal signs the points fall in: this is
        internally consistent and deterministic, but departs from classical
        (tropical) practice, so a sidereal Almuten should be read with that in
        mind.

    Example:
        >>> from kerykeion import AstrologicalSubjectFactory, DominantsFactory
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "John Lennon", 1940, 10, 9, 18, 30,
        ...     lat=53.4084, lng=-2.9916, tz_str="Europe/London", online=False)
        >>> result = DominantsFactory.from_subject(subject, strategy="almuten_figuris")
        >>> result.dominant_planet  # the Almuten Figuris  # doctest: +SKIP
        'Saturn'
    """

    name = "almuten_figuris"
    method = "almuten_figuris"

    def compute(self, subject: AstrologicalSubjectModel, config: DominantsConfig) -> DominantsModel:
        """Tally essential (and optionally accidental) dignities and rank planets.

        Args:
            subject: The chart to analyse.
            config: Options; honours ``include_accidental_dignities`` and
                ``include_score_breakdown``.

        Returns:
            A :class:`DominantsModel` whose ``dominant_planet`` is the Almuten.
        """
        sect = "day" if bool(getattr(subject, "is_diurnal", True)) else "night"
        places = self._collect_places(subject)

        essential: Dict[str, float] = {planet: 0.0 for planet in CLASSICAL_PLANETS}
        major_count: Dict[str, int] = {planet: 0 for planet in CLASSICAL_PLANETS}
        accidental: Dict[str, float] = {planet: 0.0 for planet in CLASSICAL_PLANETS}
        breakdown: List[BreakdownItem] = []

        # --- essential dignities over each hylegiacal place ------------------
        for place_name, position in places:
            holders = self._dignity_holders(position, sect)
            for dignity, planets in holders.items():
                points = ESSENTIAL_DIGNITY_POINTS[dignity]
                for planet in planets:
                    if planet is None:
                        continue
                    essential[planet] += points
                    if dignity in ("Domicile", "Exaltation"):
                        major_count[planet] += 1
                    if config.include_score_breakdown:
                        breakdown.append(
                            BreakdownItem(
                                category="place",
                                target=planet,
                                rule=dignity,
                                points=float(points),
                                detail=f"{place_name} @ {position.sign} {position.position:.1f}°",
                            )
                        )

        # --- optional accidental dignities -----------------------------------
        if config.include_accidental_dignities:
            self._add_accidental_dignities(subject, accidental, breakdown)

        totals: Dict[str, float] = {planet: essential[planet] + accidental[planet] for planet in CLASSICAL_PLANETS}
        winner = self._resolve_winner(totals, essential, major_count)

        categories = {"planets": Category(scores=totals, dominant={winner})}
        self._fill_winner_placement(subject, winner, totals[winner], categories)

        return self.build_model(categories=categories, breakdown=breakdown)

    # -- helpers ------------------------------------------------------------

    @staticmethod
    def _collect_places(subject: AstrologicalSubjectModel) -> List[Tuple[str, ZodiacPosition]]:
        """Return the available hylegiacal places as (name, zodiac position).

        Places whose point is absent (e.g. no Ascendant for an unknown birth
        time, or no resolvable prenatal syzygy) are simply omitted, so the tally
        runs over whatever is available.
        """
        places: List[Tuple[str, ZodiacPosition]] = []

        def add(name: str, degree: Optional[float]) -> None:
            if degree is not None:
                places.append((name, zodiac_breakdown(degree)))

        add("Sun", subject.sun.abs_pos if subject.sun else None)
        add("Moon", subject.moon.abs_pos if subject.moon else None)
        add("Ascendant", subject.ascendant.abs_pos if subject.ascendant else None)
        add("Pars_Fortunae", part_of_fortune_degree(subject))

        syzygy = prenatal_syzygy(subject)
        add("Syzygy", syzygy.degree if syzygy else None)

        return places

    @staticmethod
    def _dignity_holders(position: ZodiacPosition, sect: str) -> Dict[str, List[Optional[str]]]:
        """Return, for one degree, which planet holds each essential dignity.

        Args:
            position: The zodiacal breakdown of the place's degree.
            sect: ``"day"`` or ``"night"`` (selects the triplicity ruler).

        Returns:
            Mapping of dignity name to the planet(s) that hold it at this degree.
        """
        triplicity = TRIPLICITY_RULERS.get(position.element, {}).get(sect)
        exaltation = EXALTATION_TABLE.get(position.sign, (None, None))[0]
        return {
            "Domicile": list(DOMICILE_RULERS.get(position.sign, [])),
            "Exaltation": [exaltation],
            "Triplicity": [triplicity],
            "Term": [_get_term_ruler(position.sign, position.position)],
            "Face": [_get_decan_ruler(position.sign, _get_decan(position.position))],
        }

    @staticmethod
    def _add_accidental_dignities(
        subject: AstrologicalSubjectModel,
        accidental: Dict[str, float],
        breakdown: List[BreakdownItem],
    ) -> None:
        """Add the optional accidental-dignity layer in place.

        Two contributions are applied: points for the house each classical planet
        occupies, and a bonus for the planet ruling the weekday of birth. (The
        planetary-hour ruler is intentionally not included; it would require the
        full sunrise-based planetary-hours computation.)
        """
        # House placement.
        for planet in CLASSICAL_PLANETS:
            point = getattr(subject, planet.lower(), None)
            if point is None or point.house is None:
                continue
            house_points = ALMUTEN_HOUSE_PLACEMENT_POINTS.get(get_house_number(point.house))
            if house_points:
                accidental[planet] += house_points
                breakdown.append(
                    BreakdownItem("accidental", planet, "house placement", float(house_points), point.house)
                )

        # Weekday (day) ruler. Weekday index: 0 = Sunday … 6 = Saturday.
        julian_day = getattr(subject, "julian_day", None)
        if julian_day is not None:
            weekday_index = (int(julian_day + 0.5) + 1) % 7
            day_ruler = WEEKDAY_RULERS[weekday_index]
            accidental[day_ruler] += ALMUTEN_DAY_RULER_BONUS
            breakdown.append(BreakdownItem("accidental", day_ruler, "day ruler", ALMUTEN_DAY_RULER_BONUS))

    @staticmethod
    def _resolve_winner(
        totals: Dict[str, float],
        essential: Dict[str, float],
        major_count: Dict[str, int],
    ) -> str:
        """Pick the Almuten, breaking ties deterministically.

        Tie-break order: higher total, then higher essential-only subtotal, then
        more rulership-grade dignities (domicile/exaltation), then the
        traditional planetary order (Saturn → Moon) via
        :data:`ALMUTEN_TIEBREAK_ORDER`.
        """
        return min(
            CLASSICAL_PLANETS,
            key=lambda planet: (
                -totals[planet],
                -essential[planet],
                -major_count[planet],
                ALMUTEN_TIEBREAK_ORDER.index(planet),
            ),
        )

    @staticmethod
    def _fill_winner_placement(
        subject: AstrologicalSubjectModel,
        winner: str,
        winner_score: float,
        categories: Dict[str, Category],
    ) -> None:
        """Populate sign/element/quality/house categories from the winner's point.

        This lets the convenience ``dominant_sign`` / ``dominant_element`` /
        ``dominant_quality`` / ``dominant_house`` fields reflect where the Almuten
        sits, without claiming a full sign/house ranking the technique does not
        produce.
        """
        point = getattr(subject, winner.lower(), None)
        if point is None:
            return
        categories["signs"] = Category(scores={point.sign: winner_score}, dominant={point.sign})
        categories["elements"] = Category(scores={point.element: winner_score}, dominant={point.element})
        categories["qualities"] = Category(scores={point.quality: winner_score}, dominant={point.quality})
        if point.house is not None:
            categories["houses"] = Category(scores={point.house: winner_score}, dominant={point.house})
