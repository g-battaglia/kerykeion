# -*- coding: utf-8 -*-
"""Time-series commands: ``ephemeris`` and ``transits``.

Both drive ``EphemerisDataFactory``; ``transits`` feeds the sampled subjects
into ``TransitsTimeRangeFactory`` against a natal chart. The sample ceiling is
checked *before* any computation (exit 8), unless ``--no-limit`` disables both
the pre-check and the library's own guard.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, cast, get_args

from kerykeion.cli.commands._shared import _emit, _given, _parse_dt, _stored_subject
from kerykeion.cli.options import (
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
from kerykeion.cli.sampling import StepType, check_ephemeris_sampling, validate_range

_STEP_TYPES: tuple[StepType, ...] = get_args(StepType)


def _series(
    cmd: str, from_: Optional[str], to: Optional[str], step_type: Optional[str], step: Optional[int]
) -> tuple[datetime, datetime, StepType, int]:
    """The validated range and sampling; range order and awareness are checked even under ``--no-limit``."""
    if from_ is None or to is None:
        raise ValueError(f"{cmd} needs --from and --to")
    start, end = _parse_dt(from_), _parse_dt(to)
    validate_range(start, end)
    stype = step_type or "days"
    if stype not in _STEP_TYPES:
        raise ValueError(f"--step-type must be {' or '.join(_STEP_TYPES)}, got {stype!r}")
    count = 1 if step is None else step  # `step or 1` would silently rewrite --step 0
    if count <= 0:
        raise ValueError("--step must be a positive integer.")
    return start, end, cast(StepType, stype), count


def _sampling_kwargs(stype: StepType, step: int, no_limit: Optional[bool]) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"step_type": stype, "step": step}
    if no_limit:  # the library's own guard goes too
        kwargs.update(max_days=None, max_hours=None, max_minutes=None)
    return kwargs


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
    """A time series of planet positions and house cusps."""
    from kerykeion import EphemerisDataFactory
    from kerykeion.cli.subject_resolver import resolve_house_system

    start, end, stype, step_n = _series("ephemeris", from_, to, step_type, step)
    if not no_limit:
        check_ephemeris_sampling(start, end, stype, step_n, tz_str=tz)
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
    _emit(EphemerisDataFactory(start, end, **kwargs).get_ephemeris_data(as_model=True), fmt, output)


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
    """Natal chart vs a time series of transits: per-sample aspects, or events with ``--events`` (``--refine`` sharpens them)."""
    from kerykeion import EphemerisDataFactory, TransitsTimeRangeFactory

    if refine and not events:  # get_transit_moments() takes no refine argument: never drop it silently
        raise ValueError("--refine sharpens exact moments and requires --events.")
    start, end, stype, step_n = _series("transits", from_, to, step_type, step)
    # The natal is materialised first so its *resolved* timezone (a city profile
    # keeps tz_str=None in the recipe) drives the DST-aware sample count.
    natal = _stored_subject(profile, "transits")
    if not no_limit:
        check_ephemeris_sampling(start, end, stype, step_n, tz_str=getattr(natal, "tz_str", None))
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
    points = EphemerisDataFactory(start, end, **kwargs).get_ephemeris_data_as_astrological_subjects()
    factory = TransitsTimeRangeFactory(natal, points)  # type: ignore[arg-type]
    model = factory.get_transit_events(refine_exact_moments=bool(refine)) if events else factory.get_transit_moments()
    _emit(model, fmt, output)
