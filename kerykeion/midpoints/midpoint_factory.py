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

from typing import List, Optional, Sequence

from pydantic import BaseModel, Field

from kerykeion.aspects.aspects_utils import get_aspect_from_two_points
from kerykeion.schemas.kr_literals import SIGN_CODES
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion._predictive_utils import gather_active_points, build_aspect_settings


class MidpointAspectModel(BaseModel):
    """An aspect formed between a midpoint and a third active point."""

    point_name: str = Field(description="Name of the third point that aspects the midpoint.")
    point_abs_pos: float = Field(description="Absolute zodiacal longitude of the third point (0-360).")
    aspect: str = Field(description="Aspect name (conjunction, trine, square, ...).")
    aspect_degrees: int = Field(description="Exact aspect angle in degrees.")
    orb: float = Field(description="Orb (deviation from exact aspect) in degrees.")


class MidpointModel(BaseModel):
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
        two zodiacal longitudes (0-360°).

        For pairs separated by less than 180° the midpoint is simply
        ``(a + b) / 2``. For pairs separated by more than 180° the
        ``(a + b) / 2`` formula returns the *longer* arc midpoint — we
        rotate it by 180° to land on the shorter arc instead, which is
        the convention used by all serious midpoint literature
        (Ebertin, Witte, et al.).
        """
        a_n = a % 360.0
        b_n = b % 360.0
        diff = abs(a_n - b_n)
        midpoint = (a_n + b_n) / 2.0
        if diff > 180.0:
            midpoint = (midpoint + 180.0) % 360.0
        return midpoint % 360.0

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

        aspect_settings = build_aspect_settings(orb=aspect_orb, aspect_filter=aspects)

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
                            aspects_settings=aspect_settings,
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
