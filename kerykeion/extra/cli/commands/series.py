# -*- coding: utf-8 -*-
"""Time-series commands: ``ephemeris`` and ``transits``.

Both drive ``EphemerisDataFactory``; ``transits`` feeds the sampled subjects
into ``TransitsTimeRangeFactory`` against a natal chart. The factory counts
the samples before building anything and refuses a series over its ceiling;
the CLI reports that refusal as exit 8 with the flags to change, and
``--no-limit`` lifts the ceiling.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal, Optional, cast, get_args

from kerykeion.extra.cli.commands._shared import _emit, _given, _parse_dt, _stored_subject
from kerykeion.extra.cli.errors import SamplingLimitError
from kerykeion.extra.cli.options import (
    EventsFlag,
    FormatOpt,
    FromOpt,
    HousesSystemOpt,
    NoLimitFlag,
    OutputOpt,
    RefineFlag,
    SeriesStepOpt,
    SiderealModeOpt,
    StepTypeOpt,
    SubjectLat,
    SubjectLng,
    SubjectProfile,
    SubjectTz,
    ToOpt,
    ZodiacTypeOpt,
)

StepType = Literal["days", "hours", "minutes"]
_STEP_TYPES: tuple[StepType, ...] = get_args(StepType)
_CEILING_MESSAGE = re.compile(r"Too many (\w+): (\d+) > (\d+)")


def _series(
    cmd: str, from_: Optional[str], to: Optional[str], step_type: Optional[str], step: Optional[int]
) -> tuple[datetime, datetime, StepType, int]:
    """The validated range and sampling; range order and awareness are checked even under ``--no-limit``."""
    if from_ is None or to is None:
        raise ValueError(f"{cmd} needs --from and --to")
    start, end = _parse_dt(from_), _parse_dt(to)
    if (start.tzinfo is None) != (end.tzinfo is None):
        raise ValueError(
            "--from and --to must use the same ISO form (both offset-aware or both naive); "
            f"got {start.isoformat()!r} and {end.isoformat()!r}."
        )
    if end < start:
        raise ValueError("--to must not precede --from.")
    stype = step_type or "days"
    if stype not in _STEP_TYPES:
        raise ValueError(f"--step-type must be {' or '.join(_STEP_TYPES)}, got {stype!r}")
    count = 1 if step is None else step  # `step or 1` would silently rewrite --step 0
    if count <= 0:
        raise ValueError("--step must be a positive integer.")
    return start, end, cast(StepType, stype), count


def _sampling_kwargs(stype: StepType, step: int, no_limit: Optional[bool]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"step_type": stype, "step": step}
    if no_limit:
        kwargs.update(max_days=None, max_hours=None, max_minutes=None)
    return kwargs


def _sampled(start: datetime, end: datetime, **kwargs: Any):
    """``EphemerisDataFactory`` for the range; its ceiling refusal becomes exit 8, worded for the flags."""
    from kerykeion import EphemerisDataFactory

    try:
        return EphemerisDataFactory(start, end, **kwargs)
    except ValueError as exc:
        over = _CEILING_MESSAGE.match(str(exc))
        if over is None:
            raise
        unit, requested, ceiling = over.groups()
        raise SamplingLimitError(
            f"the series would hold {int(requested):,} {unit} of ephemeris data; the ceiling is {int(ceiling):,}. "
            "Narrow the date range, increase --step, or pass --no-limit to override (at your own risk)."
        ) from None


def ephemeris(
    lat: SubjectLat = None,
    lng: SubjectLng = None,
    tz: SubjectTz = None,
    from_: FromOpt = None,
    to: ToOpt = None,
    step_type: StepTypeOpt = None,
    step: SeriesStepOpt = None,
    zodiac: ZodiacTypeOpt = None,
    sidereal_mode: SiderealModeOpt = None,
    houses: HousesSystemOpt = None,
    no_limit: NoLimitFlag = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Planet positions and house cusps over a date range."""
    from kerykeion.extra.cli.subject_resolver import resolve_house_system

    start, end, stype, step_n = _series("ephemeris", from_, to, step_type, step)
    kwargs = {
        **_sampling_kwargs(stype, step_n, no_limit),
        **_given(
            lat=lat,
            lng=lng,
            tz_str=tz,
            zodiac_type=zodiac,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=resolve_house_system(houses),
        ),
    }
    _emit(_sampled(start, end, **kwargs).get_ephemeris_data(as_model=True), fmt, output)


def transits(
    profile: SubjectProfile = None,
    from_: FromOpt = None,
    to: ToOpt = None,
    step_type: StepTypeOpt = None,
    step: SeriesStepOpt = None,
    no_limit: NoLimitFlag = None,
    events: EventsFlag = None,
    refine: RefineFlag = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Transits to a natal chart over a date range.

    Per-sample aspects by default; --events collapses them into applying,
    exact and separating events, and --refine sharpens the exact moments.
    """
    from kerykeion import TransitsTimeRangeFactory

    if refine and not events:  # get_transit_moments() takes no refine argument: never drop it silently
        raise ValueError("--refine sharpens exact moments and requires --events.")
    start, end, stype, step_n = _series("transits", from_, to, step_type, step)
    natal = _stored_subject(profile, "transits")
    # The series samples in the natal frame (place, zodiac, houses, perspective,
    # custom ayanamsa) so the dual-wheel geometry is consistent.
    inherited = (
        "lat", "lng", "tz_str", "zodiac_type", "sidereal_mode", "houses_system_identifier",
        "perspective_type", "custom_ayanamsa_t0", "custom_ayanamsa_ayan_t0",
    )  # fmt: skip
    kwargs = {
        **_sampling_kwargs(stype, step_n, no_limit),
        **_given(**{name: getattr(natal, name, None) for name in inherited}),
    }
    points = _sampled(start, end, **kwargs).get_ephemeris_data_as_astrological_subjects()
    factory = TransitsTimeRangeFactory(natal, points)  # type: ignore[arg-type]
    model = factory.get_transit_events(refine_exact_moments=bool(refine)) if events else factory.get_transit_moments()
    _emit(model, fmt, output)
