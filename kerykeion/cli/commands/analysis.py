# -*- coding: utf-8 -*-
"""Top-level analysis commands: ``aspects``, ``dominants``, ``moon``, ``relationship-score``.

These read a stored subject (or two) and report a derived analysis rather than a
chart. They were reachable through ``kerykeion call`` from the start — the
dispatcher covers every public factory — but only by naming the factory and its
method, which is a poor trade for the four most common questions asked of a
chart. Curated commands cost one file and give each a real ``--help``.

The functions are decorator-free; :mod:`kerykeion.cli.app` registers them.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from kerykeion.cli.commands._shared import (
    _active_aspects,
    _emit,
    _parse_aspects,
    _split_csv,
)
from kerykeion.cli.options import (
    AccidentalDignitiesFlag,
    AspectsOpt,
    AxisOrbLimitOpt,
    CustomWeightsOpt,
    DeclinationOrbOpt,
    DeclinationsFlag,
    DistributionMethodOpt,
    DominantMethodOpt,
    FormatOpt,
    LocationPrecisionOpt,
    MajorAspectsOnlyFlag,
    OutputOpt,
    PlanetsOpt,
    ScoreBreakdownFlag,
    Subject2Profile,
    SubjectProfile,
    UsingDefaultLocationFlag,
)


def _subject(profile: Optional[str], cmd: str) -> object:
    from kerykeion.cli import subject_resolver

    if not profile:
        raise ValueError(f"{cmd} needs -s <profile>")
    return subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)


def aspects(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    subject2: Subject2Profile = None,  # type: ignore[assignment]
    declinations: DeclinationsFlag = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    aspect_list: AspectsOpt = None,  # type: ignore[assignment]
    axis_orb_limit: AxisOrbLimitOpt = None,  # type: ignore[assignment]
    orb: DeclinationOrbOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Aspects within one chart, or between two (-S) — ecliptic or declination.

    One command covers the factory's four entry points: ``-S`` selects the dual
    form, ``--declinations`` the parallel/contra-parallel pair.

    The two families do not take the same options. Declination aspects are
    computed against a single ``--orb`` and have no per-aspect table and no axis
    rule, so ``--aspects`` and ``--axis-orb-limit`` are rejected there instead of
    being forwarded into a ``TypeError`` from the factory.
    """
    from kerykeion import AspectsFactory

    first = _subject(profile, "aspects")
    second = _subject(subject2, "aspects") if subject2 else None
    active = _split_csv(planets)
    kwargs: dict[str, Any] = {}
    if active is not None:
        kwargs["active_points"] = active

    model: object
    if declinations:
        rejected = [
            flag
            for flag, value in (("--aspects", aspect_list), ("--axis-orb-limit", axis_orb_limit))
            if value is not None
        ]
        if rejected:
            raise ValueError(
                f"{rejected[0]} does not apply to declination aspects; they use a "
                "single --orb and have no per-aspect table."
            )
        if orb is not None:
            kwargs["orb"] = orb
        model = (
            AspectsFactory.dual_chart_declination_aspects(first, second, **kwargs)  # type: ignore[arg-type]
            if second is not None
            else AspectsFactory.single_chart_declination_aspects(first, **kwargs)  # type: ignore[arg-type]
        )
    else:
        if orb is not None:
            raise ValueError(
                "--orb applies to --declinations; for ecliptic aspects give the orb "
                "per aspect, e.g. --aspects trine:6."
            )
        chosen = _active_aspects(_parse_aspects(aspect_list))
        if chosen is not None:
            kwargs["active_aspects"] = chosen
        if axis_orb_limit is not None:
            # Reject it here (exit 4, invalid input) rather than letting the
            # factory raise a kerykeion-level error (exit 5): a bad flag value
            # is not a library failure, and pipeline branching relies on that
            # distinction.
            if axis_orb_limit <= 0:
                raise ValueError("--axis-orb-limit must be a positive number.")
            kwargs["axis_orb_limit"] = axis_orb_limit
        model = (
            AspectsFactory.dual_chart_aspects(first, second, **kwargs)  # type: ignore[arg-type]
            if second is not None
            else AspectsFactory.single_chart_aspects(first, **kwargs)  # type: ignore[arg-type]
        )
    _emit(model, fmt, output)


def dominants(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    method: DominantMethodOpt = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    distribution_method: DistributionMethodOpt = None,  # type: ignore[assignment]
    custom_weights: CustomWeightsOpt = None,  # type: ignore[assignment]
    accidental_dignities: AccidentalDignitiesFlag = None,  # type: ignore[assignment]
    score_breakdown: ScoreBreakdownFlag = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Dominant signs, elements, qualities and planets for a subject."""
    from kerykeion import DominantsFactory

    subject = _subject(profile, "dominants")
    kwargs: dict[str, Any] = {}
    if method is not None:
        # Validated against what the library reports, not a copied list, so a
        # newly added strategy works here the day it ships.
        available = list(DominantsFactory.available_methods())
        canonical = {name.lower(): name for name in available}
        chosen = canonical.get(method.strip().lower())
        if chosen is None:
            raise ValueError(
                f"--method must be one of {', '.join(available)}, got {method!r}"
            )
        kwargs["strategy"] = chosen
    active = _split_csv(planets)
    if active is not None:
        kwargs["active_points"] = active
    if distribution_method is not None:
        kwargs["distribution_method"] = distribution_method
    if custom_weights is not None:
        try:
            weights = json.loads(custom_weights)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"--custom-weights is not valid JSON ({exc.msg}); expected an object "
                'like \'{"Sun": 1.5}\'.'
            ) from None
        if not isinstance(weights, dict):
            raise ValueError('--custom-weights must be a JSON object, e.g. \'{"Sun": 1.5}\'.')
        kwargs["custom_weights"] = weights
    if accidental_dignities is not None:
        kwargs["include_accidental_dignities"] = accidental_dignities
    if score_breakdown is not None:
        kwargs["include_score_breakdown"] = score_breakdown
    _emit(DominantsFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def moon(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    using_default_location: UsingDefaultLocationFlag = None,  # type: ignore[assignment]
    location_precision: LocationPrecisionOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Moon phase details for the subject's moment and place."""
    from kerykeion import MoonPhaseDetailsFactory

    subject = _subject(profile, "moon")
    kwargs: dict[str, Any] = {}
    if using_default_location is not None:
        kwargs["using_default_location"] = using_default_location
    if location_precision is not None:
        kwargs["location_precision"] = location_precision
    _emit(MoonPhaseDetailsFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def relationship_score(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    subject2: Subject2Profile = None,  # type: ignore[assignment]
    all_aspects: MajorAspectsOnlyFlag = None,  # type: ignore[assignment]
    axis_orb_limit: AxisOrbLimitOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Ciro Discepolo's relationship score between two stored subjects."""
    from kerykeion import RelationshipScoreFactory

    if not profile:
        raise ValueError("relationship-score needs -s <profile> for the first subject")
    if not subject2:
        raise ValueError("relationship-score needs -S <profile> for the second subject")
    first = _subject(profile, "relationship-score")
    second = _subject(subject2, "relationship-score")
    kwargs: dict[str, Any] = {}
    if all_aspects is not None:
        kwargs["use_only_major_aspects"] = not all_aspects
    if axis_orb_limit is not None:
        kwargs["axis_orb_limit"] = axis_orb_limit
    factory = RelationshipScoreFactory(first, second, **kwargs)  # type: ignore[arg-type]
    _emit(factory.get_relationship_score(), fmt, output)
