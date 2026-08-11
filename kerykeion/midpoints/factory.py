# -*- coding: utf-8 -*-
"""
Midpoint analysis factory.

A *midpoint* between two zodiacal points is the longitude that lies exactly
half-way between them on the shorter arc — for example, the midpoint of
Sun at 10° Aries (10°) and Moon at 20° Gemini (80°) is 45° = 15° Taurus.
Cosmobiology and Uranian/Hamburg-school astrology treat midpoints as
sensitive *axes*: when a third point crosses one, the energies of the
defining pair are activated.

This module computes:

- The midpoint of every unordered pair of active points.
- The 90°-modulus position of each midpoint (for cosmobiology dial work).
- Optional *aspects to midpoint* — i.e. which other active points form
  a configured aspect with the midpoint within the configured orb.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from typing import List, Optional, Sequence, cast

from pydantic import Field
from kerykeion.schemas.models import SubscriptableBaseModel

from kerykeion.aspects.utils import get_aspect_from_two_points
from kerykeion.schemas.literals import SIGN_CODES, SignNumbers
from kerykeion.schemas.models import AstrologicalSubjectModel, KerykeionPointModel
from kerykeion._predictive_utils import gather_active_points, build_aspect_settings
from kerykeion.utilities import _ZODIAC_SIGNS, circular_mean, get_planet_house, HOUSE_FIELD_NAMES


class MidpointAspectModel(SubscriptableBaseModel):
    """An aspect formed between a midpoint and a third active point."""

    point_name: str = Field(description="Name of the third point that aspects the midpoint.")
    point_abs_pos: float = Field(description="Absolute zodiacal longitude of the third point (0-360).")
    aspect: str = Field(description="Aspect name (conjunction, trine, square, ...).")
    aspect_degrees: int = Field(description="Exact aspect angle in degrees.")
    orb: float = Field(description="Orb (deviation from exact aspect) in degrees.")


class MidpointModel(SubscriptableBaseModel):
    """The midpoint of two zodiacal points plus optional aspect activations."""

    point_a: str = Field(description="Name of the first point.")
    point_b: str = Field(description="Name of the second point.")
    point_a_abs_pos: float = Field(description="Absolute longitude of point A (0-360).")
    point_b_abs_pos: float = Field(description="Absolute longitude of point B (0-360).")
    midpoint_abs_pos: float = Field(description="Midpoint longitude on the shorter arc (0-360).")
    midpoint_sign: str = Field(description="Three-letter zodiac sign code (Ari, Tau, ...).")
    midpoint_position: float = Field(description="Position within the sign in degrees (0-30).")
    midpoint_modulus_90: float = Field(
        description="90° dial position (longitude % 90), used by cosmobiology and Uranian astrology.",
    )
    aspects_to_midpoint: List[MidpointAspectModel] = Field(
        default_factory=list,
        description="Active points that form a configured aspect with this midpoint.",
    )


class MidpointFactory:
    """Compute the full midpoint table of an :class:`AstrologicalSubjectModel`.

    Example::

        from kerykeion import AstrologicalSubjectFactory, MidpointFactory

        subject = AstrologicalSubjectFactory.from_birth_data(
            "John", 1990, 6, 15, 14, 30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
        )
        midpoints = MidpointFactory.compute(subject)
        for m in midpoints:
            print(f"{m.point_a}/{m.point_b}: {m.midpoint_position:.2f}° {m.midpoint_sign}"
                  f" (90° dial: {m.midpoint_modulus_90:.2f}°)")
            for a in m.aspects_to_midpoint:
                print(f"   activated by {a.point_name} ({a.aspect}, orb {a.orb:.2f}°)")
    """

    @staticmethod
    def _shorter_arc_midpoint(a: float, b: float) -> float:
        """Return the midpoint of the *shorter* great-circle arc between
        two zodiacal longitudes (0-360°) — the convention used by all
        serious midpoint literature (Ebertin, Witte, et al.).

        Delegates to :func:`kerykeion.utilities.circular_mean`, which
        implements the same convention (including the antipodal tie-break).
        """
        return circular_mean(a, b)

    @staticmethod
    def _sign_and_position(longitude: float) -> tuple[str, float]:
        """Return ``(sign_code, position_within_sign)`` for a longitude in 0-360°."""
        normalised = longitude % 360.0
        sign_index = int(normalised // 30) % 12
        position = normalised - (sign_index * 30.0)
        return SIGN_CODES[sign_index], position

    @staticmethod
    def compute(
        subject: AstrologicalSubjectModel,
        *,
        active_points: Optional[Sequence[str]] = None,
        compute_aspects: bool = True,
        aspect_orb: float = 1.0,
        aspects: Optional[Sequence[str]] = None,
    ) -> List[MidpointModel]:
        """Compute every pairwise midpoint and (optionally) its aspect activations.

        Args:
            subject: The natal / event chart to analyse.
            active_points: Names of the points to use as midpoint constituents.
                Defaults to :data:`DEFAULT_PREDICTIVE_POINTS`.
            compute_aspects: If ``True`` (default) also compute the list of
                third points that aspect each midpoint within ``aspect_orb``.
            aspect_orb: Orb in degrees for aspect-to-midpoint detection.
            aspects: Optional whitelist of aspect names to consider. If
                ``None``, every aspect in
                ``DEFAULT_CHART_ASPECTS_SETTINGS`` is allowed.

        Returns:
            A list of :class:`MidpointModel` covering every unordered pair of
            requested points. The order is deterministic: the input order of
            ``active_points`` (or the default tuple) drives the iteration.
        """
        gathered = gather_active_points(subject, active_points)
        if len(gathered) < 2:
            return []

        aspect_settings = build_aspect_settings(orb=aspect_orb, aspect_filter=aspects) if compute_aspects else None

        results: List[MidpointModel] = []
        for i in range(len(gathered)):
            for j in range(i + 1, len(gathered)):
                name_a, pos_a = gathered[i]
                name_b, pos_b = gathered[j]
                midpoint_long = MidpointFactory._shorter_arc_midpoint(pos_a, pos_b)
                sign, pos_in_sign = MidpointFactory._sign_and_position(midpoint_long)

                aspects_to_midpoint: List[MidpointAspectModel] = []
                if compute_aspects:
                    for name_other, pos_other in gathered:
                        if name_other in (name_a, name_b):
                            continue
                        outcome = get_aspect_from_two_points(
                            # aspect_settings is always built when compute_aspects is true
                            aspects_settings=cast(List[dict], aspect_settings),
                            point_one=midpoint_long,
                            point_two=pos_other,
                        )
                        if outcome.get("verdict"):
                            aspects_to_midpoint.append(
                                MidpointAspectModel(
                                    point_name=name_other,
                                    point_abs_pos=pos_other,
                                    aspect=outcome["name"],
                                    aspect_degrees=outcome["aspect_degrees"],
                                    orb=outcome["orbit"],
                                )
                            )

                results.append(
                    MidpointModel(
                        point_a=name_a,
                        point_b=name_b,
                        point_a_abs_pos=pos_a,
                        point_b_abs_pos=pos_b,
                        midpoint_abs_pos=midpoint_long,
                        midpoint_sign=sign,
                        midpoint_position=pos_in_sign,
                        midpoint_modulus_90=midpoint_long % 90.0,
                        aspects_to_midpoint=aspects_to_midpoint,
                    )
                )
        return results

    @staticmethod
    def compute_active_midpoint_points(
        subject: AstrologicalSubjectModel,
        pair_names: Sequence[str],
    ) -> List[KerykeionPointModel]:
        """Materialize midpoints requested by name as :class:`KerykeionPointModel`
        entries so the chart drawer can render them like ordinary active points.

        Args:
            subject: The natal subject the midpoints are computed against.
            pair_names: Pair identifiers in the ``"A_B"`` form, where ``A`` and
                ``B`` are canonical active-point names (e.g. ``"Sun_Moon"``,
                ``"Mercury_Venus"``, ``"Sun_True_North_Lunar_Node"``).

        Returns:
            One :class:`KerykeionPointModel` per resolved pair, with
            ``name='A_B_Midpoint'``, ``point_type='Midpoint'`` and sign/element/
            quality/house derived from the midpoint longitude on the shorter
            arc. Unknown pairs are silently skipped.
        """
        if not pair_names:
            return []

        # Resolve point names → absolute longitudes using the subject's own
        # active_points so the lookup stays consistent with the chart.
        gathered = dict(gather_active_points(subject, subject.active_points))

        # Build the natal house cusp list once for house assignment.
        houses_degree_ut: list[float] = []
        for field in HOUSE_FIELD_NAMES:
            cusp = getattr(subject, field, None)
            if cusp is not None:
                houses_degree_ut.append(cusp.abs_pos)

        points: List[KerykeionPointModel] = []
        emitted_pairs: set[frozenset[str]] = set()
        import logging
        logger = logging.getLogger(__name__)

        for raw in pair_names:
            # The pair key is "<name_a>_<name_b>", but the canonical point
            # names themselves can contain underscores (e.g.
            # "True_North_Lunar_Node"). Split greedily on every "_" and try
            # the resulting (prefix, suffix) splits until both sides resolve.
            tokens = raw.split("_")
            name_a: str | None = None
            name_b: str | None = None
            for split in range(1, len(tokens)):
                candidate_a = "_".join(tokens[:split])
                candidate_b = "_".join(tokens[split:])
                if candidate_a in gathered and candidate_b in gathered:
                    name_a, name_b = candidate_a, candidate_b
                    break
            if name_a is None or name_b is None:
                # Most common cause: one constituent point isn't in
                # ``subject.active_points``. Log so operators can spot the
                # typo / config drift in production.
                logger.warning(
                    "Skipping midpoint pair %r: could not split it into two "
                    "point names that both resolve in subject.active_points "
                    "(%s available)",
                    raw, len(gathered),
                )
                continue

            # Canonicalize on the unordered pair so an exact duplicate or a
            # reversed "B_A" twin doesn't materialize a second point at the
            # same longitude (the drawer dedups by name only, so duplicates
            # would render as overlapping glyphs). First occurrence wins.
            pair_key = frozenset((name_a, name_b))
            if pair_key in emitted_pairs:
                logger.debug("Skipping duplicate midpoint pair %r: already emitted", raw)
                continue
            emitted_pairs.add(pair_key)

            midpoint_long = MidpointFactory._shorter_arc_midpoint(gathered[name_a], gathered[name_b])
            sign_idx = int(midpoint_long // 30) % 12
            zodiac = _ZODIAC_SIGNS[sign_idx]

            house = None
            if len(houses_degree_ut) == 12:
                try:
                    house = get_planet_house(midpoint_long, houses_degree_ut)
                except ValueError:
                    house = None

            points.append(
                KerykeionPointModel(
                    name=f"{name_a}_{name_b}_Midpoint",
                    quality=zodiac.quality,
                    element=zodiac.element,
                    sign=zodiac.sign,
                    sign_num=cast(SignNumbers, sign_idx),  # int(...) % 12 is always 0-11
                    position=midpoint_long - sign_idx * 30.0,
                    abs_pos=midpoint_long,
                    emoji=zodiac.emoji,
                    point_type="Midpoint",
                    house=house,
                    retrograde=False,
                )
            )
        return points
