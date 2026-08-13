# -*- coding: utf-8 -*-
"""Top-level time-series commands: ``ephemeris`` and ``transits``.

Both drive :class:`EphemerisDataFactory` for the underlying planet positions;
``transits`` then feeds the resulting subjects into
:class:`TransitsTimeRangeFactory` against a natal chart. The sample ceiling is
enforced *before* any computation via :mod:`kerykeion.cli.sampling` (exit 8),
unless ``--no-limit`` disables both the pre-check and the library's own guard.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from kerykeion.cli import subject_resolver, warnings
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
from kerykeion.cli.rendering import formats
from kerykeion.cli.sampling import StepType, check_ephemeris_sampling

_STEP_TYPES = ("days", "hours", "minutes")


def _emit(model: object, fmt: Optional[str], output: Optional[str]) -> None:
    warnings.output_with_warnings(model, formats.resolve_format(fmt, output), output)


def _parse_dt(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"expected an ISO date or datetime (YYYY-MM-DD[Thh:mm]), got {value!r}"
        ) from exc


def _resolve_range(from_: Optional[str], to: Optional[str], cmd: str) -> tuple[datetime, datetime]:
    if from_ is None or to is None:
        raise ValueError(f"{cmd} needs --from and --to")
    start = _parse_dt(from_)
    end = _parse_dt(to)
    return start, end


def ephemeris(
    lat: SubjectLat = None,  # type: ignore[assignment]
    lng: SubjectLng = None,  # type: ignore[assignment]
    tz: SubjectTz = None,  # type: ignore[assignment]
    from_: FromOpt = None,  # type: ignore[assignment]
    to: ToOpt = None,  # type: ignore[assignment]
    step_type: StepTypeOpt = None,  # type: ignore[assignment]
    step: SeriesStepOpt = None,  # type: ignore[assignment]
    zodiac: ZodiacTypeOpt = None,  # type: ignore[assignment]
    sidereal_mode: SiderealModeOpt = None,  # type: ignore[assignment]
    houses: HousesSystemOpt = None,  # type: ignore[assignment]
    no_limit: NoLimitFlag = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """A time series of planet positions and house cusps."""
    from kerykeion import EphemerisDataFactory
    from kerykeion.cli.subject_resolver import resolve_house_system

    start, end = _resolve_range(from_, to, "ephemeris")
    stype: StepType = (step_type or "days")  # type: ignore[assignment]
    if stype not in _STEP_TYPES:
        raise ValueError(f"--step-type must be {' or '.join(_STEP_TYPES)}, got {stype!r}")
    # `step or 1` would silently rewrite `--step 0` to 1 (falsy-zero); use
    # `is None` and reject non-positive explicitly so 0 is an error, not step 1.
    step_n = step if step is not None else 1
    if step_n <= 0:
        raise ValueError("--step must be a positive integer.")
    if not no_limit:
        check_ephemeris_sampling(start, end, stype, step_n, tz_str=tz)

    kwargs: dict[str, Any] = dict(
        step_type=stype, step=step_n, max_days=None, max_hours=None, max_minutes=None
    ) if no_limit else dict(step_type=stype, step=step_n)
    if lat is not None:
        kwargs["lat"] = lat
    if lng is not None:
        kwargs["lng"] = lng
    if tz is not None:
        kwargs["tz_str"] = tz
    if zodiac is not None:
        kwargs["zodiac_type"] = zodiac
    if sidereal_mode is not None:
        kwargs["sidereal_mode"] = sidereal_mode
    resolved_houses = resolve_house_system(houses) if houses else None
    if resolved_houses is not None:
        kwargs["houses_system_identifier"] = resolved_houses

    factory = EphemerisDataFactory(start, end, **kwargs)
    data = factory.get_ephemeris_data(as_model=True)
    _emit(data, fmt, output)


def transits(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    from_: FromOpt = None,  # type: ignore[assignment]
    to: ToOpt = None,  # type: ignore[assignment]
    step_type: StepTypeOpt = None,  # type: ignore[assignment]
    step: SeriesStepOpt = None,  # type: ignore[assignment]
    no_limit: NoLimitFlag = None,  # type: ignore[assignment]
    events: EventsFlag = None,  # type: ignore[assignment]
    refine: RefineFlag = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Natal chart vs a time series of transits: per-sample aspects or events.

    The transit series is sampled at the natal chart's own coordinates and frame
    (zodiac, sidereal mode, houses, perspective) so the dual-wheel geometry is
    consistent. ``--events`` collapses the series into discrete
    applying→exact→separating events; ``--refine`` sharpens the exact moment
    (geocentric frames only).
    """
    from kerykeion import EphemerisDataFactory, TransitsTimeRangeFactory

    if not profile:
        raise ValueError("transits needs -s <profile> for the natal subject")
    # ``--refine`` sharpens the exact moment of a transit event, so it only
    # applies to the ``--events`` collapse. On the plain moments path
    # ``get_transit_moments()`` takes no refine argument, so accepting ``--refine``
    # there would silently drop the user's request. Fail loudly instead.
    if refine and not events:
        raise ValueError("--refine sharpens exact moments and requires --events.")
    start, end = _resolve_range(from_, to, "transits")
    stype: StepType = (step_type or "days")  # type: ignore[assignment]
    if stype not in _STEP_TYPES:
        raise ValueError(f"--step-type must be {' or '.join(_STEP_TYPES)}, got {stype!r}")
    step_n = step if step is not None else 1
    if step_n <= 0:
        raise ValueError("--step must be a positive integer.")
    # Read the natal tz from the profile recipe so the pre-flight sample count
    # is DST-aware (the library counts in the natal timezone); the heavy natal
    # materialization only runs once the check has passed. Let a missing or
    # unreadable profile surface now (clear exit 4) rather than swallowing the
    # error and falling through to an unrelated sampling-limit message.
    from kerykeion.cli import profiles as _profiles

    natal_tz: Optional[str] = _profiles.load(_profiles.resolve_path(profile)).input.tz_str
    if not no_limit:
        check_ephemeris_sampling(start, end, stype, step_n, tz_str=natal_tz)

    natal = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
    # Inherit the natal frame so the transit wheel matches the natal one.
    eph_kwargs: dict[str, Any] = dict(step_type=stype, step=step_n)
    if no_limit:
        eph_kwargs.update(max_days=None, max_hours=None, max_minutes=None)
    for src, dst in (
        ("lat", "lat"), ("lng", "lng"), ("tz_str", "tz_str"),
        ("zodiac_type", "zodiac_type"), ("sidereal_mode", "sidereal_mode"),
        ("houses_system_identifier", "houses_system_identifier"),
        ("perspective_type", "perspective_type"),
    ):
        value = getattr(natal, src, None)
        if value is not None:
            eph_kwargs[dst] = value

    points = EphemerisDataFactory(start, end, **eph_kwargs).get_ephemeris_data_as_astrological_subjects()
    tr_factory = TransitsTimeRangeFactory(natal, points)  # type: ignore[arg-type]
    model: object
    if events:
        model = tr_factory.get_transit_events(refine_exact_moments=bool(refine))
    else:
        model = tr_factory.get_transit_moments()
    _emit(model, fmt, output)
