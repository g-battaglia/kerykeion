# -*- coding: utf-8 -*-
"""Chart commands: ``natal``, ``synastry``, ``transit`` and the rest.

Each function here is a plain callable annotated with the shared ``Annotated``
option aliases from :mod:`kerykeion.cli.options`; :mod:`kerykeion.cli.app`
registers them as top-level commands. Keeping them decorator-free means the
functions are callable directly from tests without going through Click.

Every chart command follows the same shape: build a subject (or pair) from a
profile and/or inline flags, ask the library for the result, and funnel it
through :func:`kerykeion.cli.rendering.emit`. Error classification and clean
exit codes live in :mod:`kerykeion.cli.errors` and apply centrally, not here.
"""

from __future__ import annotations

from kerykeion.cli import subject_resolver, warnings
from kerykeion.cli.options import (
    FixedStarsFlag,
    FormatOpt,
    HousesSystemOpt,
    OfflineFlag,
    OnlineFlag,
    OutputOpt,
    PerspectiveOpt,
    PointsFlag,
    SetFlags,
    SiderealModeOpt,
    SubjectAltitude,
    SubjectCity,
    SubjectDate,
    SubjectIsoUtc,
    SubjectLat,
    SubjectLng,
    SubjectName,
    SubjectNation,
    SubjectProfile,
    SubjectSeconds,
    SubjectTime,
    SubjectTz,
    WithFlags,
    WithoutFlags,
    ZodiacTypeOpt,
)
from kerykeion.cli.rendering import formats


def natal(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    name: SubjectName = None,  # type: ignore[assignment]
    date: SubjectDate = None,  # type: ignore[assignment]
    time: SubjectTime = None,  # type: ignore[assignment]
    seconds: SubjectSeconds = None,  # type: ignore[assignment]
    iso_utc: SubjectIsoUtc = None,  # type: ignore[assignment]
    lat: SubjectLat = None,  # type: ignore[assignment]
    lng: SubjectLng = None,  # type: ignore[assignment]
    tz: SubjectTz = None,  # type: ignore[assignment]
    city: SubjectCity = None,  # type: ignore[assignment]
    nation: SubjectNation = None,  # type: ignore[assignment]
    online: OnlineFlag = None,  # type: ignore[assignment]
    offline: OfflineFlag = None,  # type: ignore[assignment]
    altitude: SubjectAltitude = None,  # type: ignore[assignment]
    zodiac: ZodiacTypeOpt = None,  # type: ignore[assignment]
    sidereal_mode: SiderealModeOpt = None,  # type: ignore[assignment]
    houses: HousesSystemOpt = None,  # type: ignore[assignment]
    perspective: PerspectiveOpt = None,  # type: ignore[assignment]
    points: PointsFlag = None,  # type: ignore[assignment]
    fixed_stars: FixedStarsFlag = None,  # type: ignore[assignment]
    with_flags: WithFlags = None,  # type: ignore[assignment]
    without_flags: WithoutFlags = None,  # type: ignore[assignment]
    set_flags: SetFlags = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Natal chart for a subject: report (text), JSON, XML or SVG."""
    flags = subject_resolver.build_flags(
        name=name, date=date, time=time, seconds=seconds, iso_utc=iso_utc, lat=lat,
        lng=lng, tz=tz, city=city, nation=nation, online=online, offline=offline,
        altitude=altitude, zodiac=zodiac, sidereal_mode=sidereal_mode, houses=houses,
        perspective=perspective, points=points, fixed_stars=fixed_stars,
        with_flags=with_flags, without_flags=without_flags, set_flags=set_flags,
    )
    model = subject_resolver.resolve_subject(flags, profile)
    resolved = formats.resolve_format(fmt, output)
    warnings.output_with_warnings(model, resolved, output)
