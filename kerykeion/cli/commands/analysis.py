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
from typing import Any

from kerykeion.cli.commands._shared import (
    _active_aspects,
    _emit,
    _given,
    _parse_aspects,
    _split_csv,
    _stored_subject,
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


def aspects(
    profile: SubjectProfile = None,
    subject2: Subject2Profile = None,
    declinations: DeclinationsFlag = None,
    planets: PlanetsOpt = None,
    aspect_list: AspectsOpt = None,
    axis_orb_limit: AxisOrbLimitOpt = None,
    orb: DeclinationOrbOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
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

    first = _stored_subject(profile, "aspects")
    second = _stored_subject(subject2, "aspects", "-S") if subject2 else None
    kwargs: dict[str, Any] = _given(active_points=_split_csv(planets))

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
        kwargs.update(_given(orb=orb))
        model = (
            AspectsFactory.dual_chart_declination_aspects(first, second, **kwargs)  # type: ignore[arg-type]
            if second is not None
            else AspectsFactory.single_chart_declination_aspects(first, **kwargs)  # type: ignore[arg-type]
        )
    else:
        if orb is not None:
            raise ValueError(
                "--orb applies to --declinations; for ecliptic aspects give the orb per aspect, e.g. --aspects trine:6."
            )
        # A bad flag value is rejected here (exit 4, invalid input) rather than
        # inside the factory, which would raise a kerykeion-level error (exit 5):
        # pipeline branching relies on telling those two apart.
        if axis_orb_limit is not None and axis_orb_limit <= 0:
            raise ValueError("--axis-orb-limit must be a positive number.")
        kwargs.update(
            _given(
                active_aspects=_active_aspects(_parse_aspects(aspect_list)),
                axis_orb_limit=axis_orb_limit,
            )
        )
        model = (
            AspectsFactory.dual_chart_aspects(first, second, **kwargs)  # type: ignore[arg-type]
            if second is not None
            else AspectsFactory.single_chart_aspects(first, **kwargs)  # type: ignore[arg-type]
        )
    _emit(model, fmt, output)


def dominants(
    profile: SubjectProfile = None,
    method: DominantMethodOpt = None,
    planets: PlanetsOpt = None,
    distribution_method: DistributionMethodOpt = None,
    custom_weights: CustomWeightsOpt = None,
    accidental_dignities: AccidentalDignitiesFlag = None,
    score_breakdown: ScoreBreakdownFlag = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Dominant signs, elements, qualities and planets for a subject."""
    from kerykeion import DominantsFactory

    subject = _stored_subject(profile, "dominants")
    kwargs: dict[str, Any] = {}
    if method is not None:
        # Validated against what the library reports, not a copied list, so a
        # newly added strategy works here the day it ships.
        available = list(DominantsFactory.available_methods())
        canonical = {name.lower(): name for name in available}
        chosen = canonical.get(method.strip().lower())
        if chosen is None:
            raise ValueError(f"--method must be one of {', '.join(available)}, got {method!r}")
        kwargs["strategy"] = chosen
    kwargs.update(
        _given(
            active_points=_split_csv(planets),
            distribution_method=distribution_method,
            include_accidental_dignities=accidental_dignities,
            include_score_breakdown=score_breakdown,
        )
    )
    if custom_weights is not None:
        try:
            weights = json.loads(custom_weights)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"--custom-weights is not valid JSON ({exc.msg}); expected an object like '{{\"Sun\": 1.5}}'."
            ) from None
        if not isinstance(weights, dict):
            raise ValueError("--custom-weights must be a JSON object, e.g. '{\"Sun\": 1.5}'.")
        kwargs["custom_weights"] = weights
    _emit(DominantsFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def moon(
    profile: SubjectProfile = None,
    using_default_location: UsingDefaultLocationFlag = None,
    location_precision: LocationPrecisionOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Moon phase details for the subject's moment and place."""
    from kerykeion import MoonPhaseDetailsFactory

    subject = _stored_subject(profile, "moon")
    kwargs = _given(
        using_default_location=using_default_location,
        location_precision=location_precision,
    )
    _emit(MoonPhaseDetailsFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def relationship_score(
    profile: SubjectProfile = None,
    subject2: Subject2Profile = None,
    all_aspects: MajorAspectsOnlyFlag = None,
    axis_orb_limit: AxisOrbLimitOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Ciro Discepolo's relationship score between two stored subjects."""
    from kerykeion import RelationshipScoreFactory

    first = _stored_subject(profile, "relationship-score")
    second = _stored_subject(subject2, "relationship-score", "-S")
    kwargs = _given(
        use_only_major_aspects=None if all_aspects is None else not all_aspects,
        axis_orb_limit=axis_orb_limit,
    )
    factory = RelationshipScoreFactory(first, second, **kwargs)  # type: ignore[arg-type]
    _emit(factory.get_relationship_score(), fmt, output)
