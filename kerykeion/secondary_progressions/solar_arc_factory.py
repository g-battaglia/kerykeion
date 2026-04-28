# -*- coding: utf-8 -*-
"""
Solar arc directions factory.

The *solar arc* technique is a sibling of secondary progressions: it
takes the difference between the progressed Sun and the natal Sun
("solar arc") and applies that *single* arc — uniformly — to every
natal point. As a result every directed point advances at roughly
1° / year (the Sun's mean rate), and the inter-point geometry of the
natal chart is preserved while contacts to natal positions reveal
yearly themes.

This module returns a structured model rather than an
:class:`AstrologicalSubjectModel`, because the directed positions are
*not* a real ephemeris snapshot — they're a symbolic shift applied to
the natal chart. House cusps and angles in the natal subject stay
untouched; the directed points are the angular images of the natal
points after a uniform forward rotation by the solar arc.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Sequence

from pydantic import BaseModel, Field

from kerykeion.aspects.aspects_utils import get_aspect_from_two_points
from kerykeion.schemas import KerykeionException
from kerykeion.schemas.kr_literals import SIGN_CODES
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion._predictive_utils import gather_active_points, build_aspect_settings

from .secondary_progression_factory import SecondaryProgressionFactory


def _parse_target_utc(
    target_iso_utc_datetime: Optional[str],
    target_year: Optional[int],
) -> Optional[datetime]:
    """Parse target input into a UTC datetime, or return None if neither is given."""
    if target_iso_utc_datetime is not None and target_year is not None:
        raise KerykeionException(
            "Pass exactly one of `target_iso_utc_datetime` or `target_year`."
        )
    if target_year is not None:
        try:
            return datetime(target_year, 1, 1, tzinfo=timezone.utc)
        except (ValueError, OverflowError) as exc:
            raise KerykeionException(
                f"Invalid `target_year`: {target_year!r}"
            ) from exc
    if target_iso_utc_datetime:
        try:
            iso = target_iso_utc_datetime.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso)
        except ValueError as exc:
            raise KerykeionException(
                f"Invalid `target_iso_utc_datetime`: {target_iso_utc_datetime!r}"
            ) from exc
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return None


def _normalise_long(longitude: float) -> float:
    return longitude % 360.0


def _forward_arc_diff(target: float, source: float) -> float:
    """Return the forward zodiacal difference ``target - source`` in the
    range ``[0, 360)`` degrees.
    """
    return (target - source) % 360.0


def _is_near_zero_arc(arc: float, orb: float) -> bool:
    """Return ``True`` when a forward arc is within ``orb`` of 0°/360°."""
    return min(arc, 360.0 - arc) < orb


class SolarArcDirectedPoint(BaseModel):
    """A natal point after applying the solar-arc shift."""

    name: str = Field(description="Name of the natal point (Sun, Moon, Mercury, ...).")
    natal_abs_pos: float = Field(description="Natal longitude (0-360).")
    directed_abs_pos: float = Field(description="Directed longitude (0-360) after applying the solar arc.")
    natal_sign: str
    directed_sign: str
    directed_position: float = Field(description="Position within the directed sign (0-30).")
    sign_changed: bool = Field(description="True if the directed position is in a different sign than the natal one.")


class SolarArcDirectedAspect(BaseModel):
    """A directed-to-natal aspect — the actionable timing signal."""

    directed_point: str = Field(description="Name of the directed (moving) point.")
    natal_point: str = Field(description="Name of the natal (receiving) point.")
    directed_abs_pos: float
    natal_abs_pos: float
    aspect: str
    aspect_degrees: int
    orb: float


class SolarArcSubjectModel(BaseModel):
    """The full solar-arc result: arc, directed points, directed-to-natal hits."""

    natal_name: str
    target_iso_utc_datetime: str
    solar_arc: float = Field(description="Solar arc in degrees (forward, range [0, 360)).")
    directed_points: List[SolarArcDirectedPoint] = Field(default_factory=list)
    directed_to_natal_aspects: List[SolarArcDirectedAspect] = Field(default_factory=list)


class SolarArcFactory:
    """Compute the solar arc and the directed-to-natal aspect picture
    for an :class:`AstrologicalSubjectModel` at a target moment.

    Example::

        from kerykeion import AstrologicalSubjectFactory, SolarArcFactory

        natal = AstrologicalSubjectFactory.from_birth_data(
            "John", 1990, 6, 15, 14, 30,
            lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
        )
        result = SolarArcFactory.compute(
            natal,
            target_iso_utc_datetime="2026-04-25T00:00:00Z",
        )
        print(f"Solar arc: {result.solar_arc:.4f}°")
        for hit in result.directed_to_natal_aspects:
            print(
                f"  {hit.directed_point} ({hit.directed_abs_pos:.2f}°) "
                f"{hit.aspect} natal {hit.natal_point} (orb {hit.orb:.2f}°)"
            )
    """

    @staticmethod
    def compute(
        natal_subject: AstrologicalSubjectModel,
        *,
        target_iso_utc_datetime: Optional[str] = None,
        target_year: Optional[int] = None,
        active_points: Optional[Sequence[str]] = None,
        compute_aspects: bool = True,
        aspect_orb: float = 1.0,
        aspects: Optional[Sequence[str]] = None,
    ) -> SolarArcSubjectModel:
        """Compute the solar arc and directed-to-natal aspect picture.

        Args:
            natal_subject: Fully-built natal :class:`AstrologicalSubjectModel`.
            target_iso_utc_datetime: ISO-8601 UTC timestamp of the target.
                Mutually exclusive with ``target_year``.
            target_year: Convenience: target year (Jan 1 at 00:00 UTC).
                Mutually exclusive with ``target_iso_utc_datetime``.
            active_points: Names of the natal points to direct. Defaults
                to :data:`DEFAULT_PREDICTIVE_POINTS`.
            compute_aspects: If ``True`` (default), also compute the list
                of directed-to-natal aspect contacts.
            aspect_orb: Orb in degrees for aspect detection.
            aspects: Optional whitelist of aspect names to detect.

        Returns:
            A :class:`SolarArcSubjectModel` describing the arc and every
            directed point + directed-to-natal aspect found.
        """
        if natal_subject.sun is None:
            raise KerykeionException("Natal subject is missing the Sun — cannot compute solar arc.")

        target_utc = _parse_target_utc(target_iso_utc_datetime, target_year)

        progressed = SecondaryProgressionFactory.compute(
            natal_subject,
            target_iso_utc_datetime=target_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z") if target_utc else None,
        )
        if progressed.sun is None:
            raise KerykeionException("Progressed subject is missing the Sun — cannot compute solar arc.")

        solar_arc = _forward_arc_diff(progressed.sun.abs_pos, natal_subject.sun.abs_pos)

        gathered = gather_active_points(natal_subject, active_points)

        directed_points: List[SolarArcDirectedPoint] = []
        for name, natal_pos in gathered:
            directed_pos = _normalise_long(natal_pos + solar_arc)
            natal_sign_idx = int(natal_pos // 30) % 12
            directed_sign_idx = int(directed_pos // 30) % 12
            directed_points.append(
                SolarArcDirectedPoint(
                    name=name,
                    natal_abs_pos=natal_pos,
                    directed_abs_pos=directed_pos,
                    natal_sign=SIGN_CODES[natal_sign_idx],
                    directed_sign=SIGN_CODES[directed_sign_idx],
                    directed_position=directed_pos - directed_sign_idx * 30.0,
                    sign_changed=natal_sign_idx != directed_sign_idx,
                )
            )

        directed_to_natal: List[SolarArcDirectedAspect] = []
        if compute_aspects:
            aspect_settings = build_aspect_settings(aspect_orb, aspects)
            for d in directed_points:
                for natal_name, natal_pos in gathered:
                    if natal_name == d.name and _is_near_zero_arc(solar_arc, aspect_orb):
                        continue
                    outcome = get_aspect_from_two_points(
                        aspects_settings=aspect_settings,
                        point_one=d.directed_abs_pos,
                        point_two=natal_pos,
                    )
                    if outcome.get("verdict"):
                        directed_to_natal.append(
                            SolarArcDirectedAspect(
                                directed_point=d.name,
                                natal_point=natal_name,
                                directed_abs_pos=d.directed_abs_pos,
                                natal_abs_pos=natal_pos,
                                aspect=outcome["name"],
                                aspect_degrees=outcome["aspect_degrees"],
                                orb=outcome["orbit"],
                            )
                        )

        result_target_iso = target_utc.strftime("%Y-%m-%dT%H:%M:%S.000Z") if target_utc else ""

        return SolarArcSubjectModel(
            natal_name=natal_subject.name,
            target_iso_utc_datetime=result_target_iso,
            solar_arc=solar_arc,
            directed_points=directed_points,
            directed_to_natal_aspects=directed_to_natal,
        )
