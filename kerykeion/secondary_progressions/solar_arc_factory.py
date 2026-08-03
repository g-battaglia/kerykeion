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

from typing import List, Mapping, Optional, Sequence

from pydantic import BaseModel, Field  # noqa: F401  (BaseModel kept for back-compat imports)

from kerykeion.schemas.kr_models import SubscriptableBaseModel

from kerykeion.aspects.aspects_utils import get_aspect_from_two_points
from kerykeion.aspects.orb_utils import OrbAdjustmentStrategy, resolve_pair_orb_adjustment
from kerykeion.schemas import KerykeionException
from kerykeion.schemas.kr_literals import SIGN_CODES
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion._predictive_utils import gather_active_points, build_aspect_settings, PTOLEMAIC_ASPECTS
from kerykeion.utilities import _ZODIAC_SIGNS, get_planet_house, HOUSE_FIELD_NAMES

from .secondary_progression_factory import SecondaryProgressionFactory


def _normalise_long(longitude: float) -> float:
    return longitude % 360.0


def _forward_arc_diff(target: float, source: float) -> float:
    """Return the forward zodiacal difference ``target - source`` in the
    range ``[0, 360)`` degrees.
    """
    return (target - source) % 360.0


def _is_near_zero_arc(arc: float, orb: float) -> bool:
    """Return ``True`` when a forward arc is within ``orb`` of 0°/360°."""
    return min(arc, 360.0 - arc) <= orb


def _midpoint_name_to_pair_key(name: str) -> str:
    """Recover the ``A_B`` pair identifier from a synthetic midpoint name.

    Midpoint points carry ``name='A_B_Midpoint'``; the pair-key consumed by
    ``MidpointFactory.compute_active_midpoint_points`` is the same string
    minus the ``_Midpoint`` suffix.
    """
    return name[: -len("_Midpoint")] if name.endswith("_Midpoint") else name


class SolarArcDirectedPointModel(SubscriptableBaseModel):
    """A natal point after applying the solar-arc shift."""

    name: str = Field(description="Name of the natal point (Sun, Moon, Mercury, ...).")
    natal_abs_pos: float = Field(description="Natal longitude (0-360).")
    directed_abs_pos: float = Field(description="Directed longitude (0-360) after applying the solar arc.")
    natal_sign: str
    directed_sign: str
    directed_position: float = Field(description="Position within the directed sign (0-30).")
    sign_changed: bool = Field(description="True if the directed position is in a different sign than the natal one.")


class SolarArcDirectedAspectModel(SubscriptableBaseModel):
    """A directed-to-natal aspect — the actionable timing signal."""

    directed_point: str = Field(description="Name of the directed (moving) point.")
    natal_point: str = Field(description="Name of the natal (receiving) point.")
    directed_abs_pos: float
    natal_abs_pos: float
    aspect: str
    aspect_degrees: int
    orb: float


class SolarArcSubjectModel(SubscriptableBaseModel):
    """The full solar-arc result: arc, directed points, directed-to-natal hits."""

    natal_name: str
    target_iso_utc_datetime: str
    solar_arc: float = Field(description="Solar arc in degrees (forward, range [0, 360)).")
    directed_points: List[SolarArcDirectedPointModel] = Field(default_factory=list)
    directed_to_natal_aspects: List[SolarArcDirectedAspectModel] = Field(default_factory=list)


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
        aspect_orb: float = 3.0,
        aspects: Optional[Sequence[str]] = None,
        point_orb_adjustments: Optional[Mapping[str, float]] = None,
        point_orb_adjustment_strategy: OrbAdjustmentStrategy = "max_explicit",
    ) -> SolarArcSubjectModel:
        """Compute the solar arc and directed-to-natal aspect picture.

        Args:
            natal_subject: Fully-built natal :class:`AstrologicalSubjectModel`.
            target_iso_utc_datetime: ISO-8601 UTC timestamp of the target.
                Mutually exclusive with ``target_year``.
            target_year: Convenience: target year (Jan 1 at 00:00 UTC).
                Mutually exclusive with ``target_iso_utc_datetime``.
            active_points: Names of the natal points to direct (the
                "moving" side). Aspect detection checks these directed
                points against the natal subject's own ``active_points``.
                Defaults to :data:`DEFAULT_PREDICTIVE_POINTS`.
            compute_aspects: If ``True`` (default), also compute the list
                of directed-to-natal aspect contacts.
            aspect_orb: Orb in degrees for aspect detection.
            aspects: Optional whitelist of aspect names to detect.
            point_orb_adjustments: Optional per-point orb adjustment table.
                ``None`` (default) means no adjustment — solar arc uses a
                flat, tight orb regardless of which point is involved.
            point_orb_adjustment_strategy: How to combine the two points'
                adjustments when a table is supplied (default ``"max_explicit"``).

        Returns:
            A :class:`SolarArcSubjectModel` describing the arc and every
            directed point + directed-to-natal aspect found.
        """
        if natal_subject.sun is None:
            raise KerykeionException("Natal subject is missing the Sun — cannot compute solar arc.")
        if (target_iso_utc_datetime is None) == (target_year is None):
            raise KerykeionException("Pass exactly one of `target_iso_utc_datetime` or `target_year`.")

        target_jd = SecondaryProgressionFactory._target_to_jd(target_iso_utc_datetime, target_year)

        progressed = SecondaryProgressionFactory.compute(
            natal_subject,
            target_iso_utc_datetime=target_iso_utc_datetime,
            target_year=target_year,
        )
        if progressed.sun is None:
            raise KerykeionException("Progressed subject is missing the Sun — cannot compute solar arc.")

        solar_arc = _forward_arc_diff(progressed.sun.abs_pos, natal_subject.sun.abs_pos)

        directed_sources = gather_active_points(natal_subject, active_points)
        natal_targets = gather_active_points(natal_subject, natal_subject.active_points)

        directed_points: List[SolarArcDirectedPointModel] = []
        for name, natal_pos in directed_sources:
            directed_pos = _normalise_long(natal_pos + solar_arc)
            natal_sign_idx = int(natal_pos // 30) % 12
            directed_sign_idx = int(directed_pos // 30) % 12
            directed_points.append(
                SolarArcDirectedPointModel(
                    name=name,
                    natal_abs_pos=natal_pos,
                    directed_abs_pos=directed_pos,
                    natal_sign=SIGN_CODES[natal_sign_idx],
                    directed_sign=SIGN_CODES[directed_sign_idx],
                    directed_position=directed_pos - directed_sign_idx * 30.0,
                    sign_changed=natal_sign_idx != directed_sign_idx,
                )
            )

        directed_to_natal: List[SolarArcDirectedAspectModel] = []
        if compute_aspects:
            effective_aspects = aspects if aspects is not None else PTOLEMAIC_ASPECTS
            aspect_settings = build_aspect_settings(aspect_orb, effective_aspects)
            for d in directed_points:
                for natal_name, natal_pos in natal_targets:
                    extra_orb = resolve_pair_orb_adjustment(
                        d.name,
                        natal_name,
                        point_orb_adjustments,
                        point_orb_adjustment_strategy,
                    )
                    # Skip the tautological self-conjunction (a directed point
                    # with its own natal position) using the SAME effective orb
                    # the detection below uses — otherwise a per-pair widening
                    # (extra_orb) lets the self-conjunction slip past a guard
                    # sized only to the base orb.
                    if natal_name == d.name and _is_near_zero_arc(solar_arc, aspect_orb + max(0.0, extra_orb)):
                        continue
                    outcome = get_aspect_from_two_points(
                        aspects_settings=aspect_settings,
                        point_one=d.directed_abs_pos,
                        point_two=natal_pos,
                        extra_orb=extra_orb,
                    )
                    if outcome.get("verdict"):
                        directed_to_natal.append(
                            SolarArcDirectedAspectModel(
                                directed_point=d.name,
                                natal_point=natal_name,
                                directed_abs_pos=d.directed_abs_pos,
                                natal_abs_pos=natal_pos,
                                aspect=outcome["name"],
                                aspect_degrees=outcome["aspect_degrees"],
                                orb=outcome["orbit"],
                            )
                        )

        result_target_iso = SecondaryProgressionFactory._jd_to_utc_iso(target_jd)

        return SolarArcSubjectModel(
            natal_name=natal_subject.name,
            target_iso_utc_datetime=result_target_iso,
            solar_arc=solar_arc,
            directed_points=directed_points,
            directed_to_natal_aspects=directed_to_natal,
        )

    # Names of point fields whose abs_pos must be shifted by the solar arc
    # when building a directed AstrologicalSubjectModel. The four angles
    # (Asc/MC/Desc/IC) ARE directed — solar-arc-directed angles are a standard
    # technique and compute()'s aspect list (which uses DEFAULT_PREDICTIVE_POINTS,
    # including Ascendant/Medium_Coeli) reports directed-angle contacts, so the
    # directed subject must place the angles where those aspects point. Only the
    # house CUSPS stay on the natal frame (they define the biwheel's house grid).
    _DIRECTABLE_FIELDS = (
        "sun",
        "moon",
        "mercury",
        "venus",
        "mars",
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
        "chiron",
        "earth",
        "pholus",
        "mean_lilith",
        "true_lilith",
        "interpolated_lilith",
        "mean_priapus",
        "true_priapus",
        "interpolated_perigee",
        "white_moon",
        "ceres",
        "pallas",
        "juno",
        "vesta",
        "eris",
        "sedna",
        "haumea",
        "makemake",
        "ixion",
        "orcus",
        "quaoar",
        "cupido",
        "hades",
        "zeus",
        "kronos",
        "apollon",
        "admetos",
        "vulkanus",
        "poseidon",
        "mean_north_lunar_node",
        "true_north_lunar_node",
        "mean_south_lunar_node",
        "true_south_lunar_node",
        "pars_fortunae",
        "pars_spiritus",
        "pars_amoris",
        "pars_fidei",
        "vertex",
        "anti_vertex",
        "ascendant",
        "medium_coeli",
        "descendant",
        "imum_coeli",
    )

    @staticmethod
    def compute_directed_subject(
        natal_subject: AstrologicalSubjectModel,
        *,
        target_iso_utc_datetime: Optional[str] = None,
        target_year: Optional[int] = None,
    ) -> AstrologicalSubjectModel:
        """Return a copy of ``natal_subject`` with every directable point
        shifted forward by the solar arc.

        The four angles (Asc/MC/Desc/IC) ARE directed, consistent with
        :meth:`compute`, whose aspect list reports directed-angle contacts.
        Only the house CUSPS stay on the natal frame (they define the biwheel's
        house grid): inner ring = natal, outer ring = directed, houses fixed.
        """
        result = SolarArcFactory.compute(
            natal_subject,
            target_iso_utc_datetime=target_iso_utc_datetime,
            target_year=target_year,
            compute_aspects=False,
        )
        arc = result.solar_arc

        directed = natal_subject.model_copy(deep=True)
        directed.name = f"{natal_subject.name} (directed)"

        # House cusps stay on the natal frame — used to recompute house
        # placement for each directed point.
        houses_degree_ut: list[float] = []
        for house_field in HOUSE_FIELD_NAMES:
            cusp = getattr(directed, house_field, None)
            if cusp is not None:
                houses_degree_ut.append(cusp.abs_pos)

        for field_name in SolarArcFactory._DIRECTABLE_FIELDS:
            point = getattr(directed, field_name, None)
            if point is None:
                continue
            new_abs = _normalise_long(point.abs_pos + arc)
            sign_idx = int(new_abs // 30) % 12
            zodiac = _ZODIAC_SIGNS[sign_idx]

            point.abs_pos = new_abs
            point.sign = SIGN_CODES[sign_idx]
            point.sign_num = sign_idx
            point.position = new_abs - sign_idx * 30.0
            # Recompute sign-derived metadata so downstream consumers
            # (ChartDrawer, AI prompts, PDF exports) stay consistent
            # when a directed point crosses signs.
            point.quality = zodiac.quality
            point.element = zodiac.element
            point.emoji = zodiac.emoji
            # Clear the OTHER position-derived enrichments: after the arc shift
            # the natal essential_dignity / dignity_score / decan / term /
            # nakshatra no longer describe the directed position, and a stale
            # value is more misleading than None. (These are opt-in fields,
            # populated only when the natal requested them.)
            point.essential_dignity = None
            point.dignity_score = None
            point.decan_number = None
            point.decan_ruler = None
            point.term_ruler = None
            point.nakshatra = None
            point.nakshatra_number = None
            point.nakshatra_pada = None
            point.nakshatra_lord = None
            # Also null the location/diurnal-dependent enrichments: after the arc
            # shift the natal azimuth/altitude (local-space horizon position) and
            # gauquelin_sector (diurnal sector) describe a longitude the point no
            # longer occupies. Same triple, same reason, as relocate() nulls when
            # it moves a chart to a new location.
            point.azimuth = None
            point.altitude_above_horizon = None
            point.gauquelin_sector = None
            if len(houses_degree_ut) == 12:
                try:
                    point.house = get_planet_house(new_abs, houses_degree_ut)
                except ValueError:
                    # Leave the natal house value rather than crash
                    pass

        # Active midpoints were deep-copied from the natal subject and now
        # point at natal positions. Recompute them against the directed
        # planets so the biwheel outer ring renders directed midpoint glyphs
        # rather than stale natal ones.
        if directed.active_midpoints:
            from kerykeion.midpoints.midpoint_factory import MidpointFactory

            pair_names = [_midpoint_name_to_pair_key(mp.name) for mp in directed.active_midpoints]
            pair_names = [n for n in pair_names if n]
            directed.active_midpoints = MidpointFactory.compute_active_midpoint_points(directed, pair_names)

        return directed
