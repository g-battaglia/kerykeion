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
from typing import Any, Optional, cast, get_args

from kerykeion.cli import subject_resolver
from kerykeion.cli.commands._shared import _emit, _given, _parse_dt
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


def _resolve_range(from_: Optional[str], to: Optional[str], cmd: str) -> tuple[datetime, datetime]:
    if from_ is None or to is None:
        raise ValueError(f"{cmd} needs --from and --to")
    return _parse_dt(from_), _parse_dt(to)


def _resolve_sampling(step_type: Optional[str], step: Optional[int]) -> tuple[StepType, int]:
    """Validate ``--step-type``/``--step`` into the pair the factory wants."""
    stype = step_type or "days"
    if stype not in _STEP_TYPES:
        raise ValueError(f"--step-type must be {' or '.join(_STEP_TYPES)}, got {stype!r}")
    # `step or 1` would silently rewrite `--step 0` to 1 (falsy-zero); use
    # `is None` and reject non-positive explicitly so 0 is an error, not step 1.
    count = step if step is not None else 1
    if count <= 0:
        raise ValueError("--step must be a positive integer.")
    return cast(StepType, stype), count


def _ceiling_off() -> dict[str, None]:
    """The ``--no-limit`` overrides: the library's own guard, disabled too."""
    return {"max_days": None, "max_hours": None, "max_minutes": None}


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

    start, end = _resolve_range(from_, to, "ephemeris")
    stype, step_n = _resolve_sampling(step_type, step)
    # Range validation runs unconditionally: --no-limit bypasses the sample
    # ceiling, not an inverted or mixed-awareness range, which would otherwise
    # surface as the library's generic 'No dates found' error.
    validate_range(start, end)
    if not no_limit:
        check_ephemeris_sampling(start, end, stype, step_n, tz_str=tz)

    kwargs: dict[str, Any] = {
        "step_type": stype,
        "step": step_n,
        **(_ceiling_off() if no_limit else {}),
        **_given(
            lat=lat,
            lng=lng,
            tz_str=tz,
            zodiac_type=zodiac,
            sidereal_mode=sidereal_mode,
            houses_system_identifier=resolve_house_system(houses) if houses else None,
        ),
    }
    factory = EphemerisDataFactory(start, end, **kwargs)
    data = factory.get_ephemeris_data(as_model=True)
    _emit(data, fmt, output)


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
    stype, step_n = _resolve_sampling(step_type, step)
    # Range validation runs unconditionally even with --no-limit (see ephemeris).
    validate_range(start, end)
    # Materialise the natal before the pre-flight so its *resolved* timezone
    # (not the stored recipe value) drives the DST-aware sample count: an
    # online/city profile keeps tz_str=None in the recipe (the zone is resolved
    # by GeoNames only at materialisation), so reading the recipe would run the
    # count DST-unaware and diverge from the library. The materialisation is one
    # subject build — negligible next to the series it guards.
    natal = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
    natal_tz = getattr(natal, "tz_str", None)
    if not no_limit:
        check_ephemeris_sampling(start, end, stype, step_n, tz_str=natal_tz)
    # Inherit the natal frame so the transit wheel matches the natal one.
    # The custom-ayanamsa pair is part of that frame: without it a natal cast
    # with ``--sidereal-mode USER`` crashes here (the mode needs its two
    # numbers on every rebuild, and EphemerisDataFactory accepts both).
    inherited = (
        "lat",
        "lng",
        "tz_str",
        "zodiac_type",
        "sidereal_mode",
        "houses_system_identifier",
        "perspective_type",
        "custom_ayanamsa_t0",
        "custom_ayanamsa_ayan_t0",
    )
    eph_kwargs: dict[str, Any] = {
        "step_type": stype,
        "step": step_n,
        **(_ceiling_off() if no_limit else {}),
        **_given(**{name: getattr(natal, name, None) for name in inherited}),
    }

    points = EphemerisDataFactory(start, end, **eph_kwargs).get_ephemeris_data_as_astrological_subjects()
    tr_factory = TransitsTimeRangeFactory(natal, points)  # type: ignore[arg-type]
    model: object
    if events:
        model = tr_factory.get_transit_events(refine_exact_moments=bool(refine))
    else:
        model = tr_factory.get_transit_moments()
    _emit(model, fmt, output)
