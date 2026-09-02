# -*- coding: utf-8 -*-
"""Chart commands: ``natal``, ``now``, ``synastry``, ``transit``, ``composite``, ``return``, ``progression``.

The relationship and predictive charts take the base subject as ``-s <profile>``
only — save it once, reuse it. ``natal`` and ``now`` spell the inline flag set,
because a one-off natal is the common interactive use. SVG always goes through
``ChartDrawer.generate_svg_string``, never ``save_svg`` (which writes into the
home directory and prints to stdout).
"""

from __future__ import annotations

from typing import Any, Optional

from kerykeion.extra.cli import subject_resolver
from kerykeion.extra.cli.commands._shared import _emit, _stored_subject, _subject_from, with_render_flags
from kerykeion.extra.cli.options import (
    DayOpt,
    FixedStarsFlag,
    FormatOpt,
    HousesSystemOpt,
    MonthOpt,
    OfflineFlag,
    OnlineFlag,
    OutputOpt,
    PerspectiveOpt,
    PointsFlag,
    ReturnTypeOpt,
    SetFlags,
    SiderealModeOpt,
    Subject2Profile,
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
    TargetYearOpt,
    ToDateOpt,
    ToTimeOpt,
    WithFlags,
    WithoutFlags,
    YearOpt,
    ZodiacTypeOpt,
)
from kerykeion.extra.cli.rendering import formats

_RETURN_TYPES = ("Solar", "Lunar")
# The natal frame a transit wheel must share, as SubjectFlags field → model attribute.
# The custom-ayanamsa pair is part of it: a natal cast with --sidereal-mode USER
# needs its two numbers on every rebuild.
_FRAME = {
    "zodiac": "zodiac_type",
    "sidereal_mode": "sidereal_mode",
    "houses": "houses_system_identifier",
    "perspective": "perspective_type",
    "custom_ayanamsa_t0": "custom_ayanamsa_t0",
    "custom_ayanamsa_ayan_t0": "custom_ayanamsa_ayan_t0",
}


def _emit_subject_or_chart(subject: object, fmt: Optional[str], output: Optional[str], opts: object = None) -> None:
    """Subject for text/json/xml; a natal chart-data wrapper for SVG."""
    resolved = formats.resolve_format(fmt, output)
    if resolved == "svg":
        from kerykeion import ChartDataFactory

        subject = ChartDataFactory.create_natal_chart_data(subject)  # type: ignore[arg-type]
    _emit(subject, resolved, output, opts)


def _relocation(
    lat: Optional[float],
    lng: Optional[float],
    tz: Optional[str],
    city: Optional[str],
    online: Optional[bool],
    offline: Optional[bool],
    cmd: str,
) -> bool:
    """Validate the relocated-place flags ``transit`` and ``return`` share; True when coordinates were given.

    Coordinates come as a whole group: the natal timezone standing in for a new
    latitude/longitude would localise the moment in the wrong zone — a
    multi-hour error in the houses, with no warning. A city geocodes, so it
    excludes coordinates and cannot be honoured offline.
    """
    given = [value for value in (lat, lng, tz) if value is not None]
    if 0 < len(given) < 3:
        raise ValueError(
            f"a relocated {cmd} needs --lat, --lng and --tz together (or none, to use the natal birthplace); "
            "the natal timezone does not match new coordinates."
        )
    if city is not None and given:
        raise ValueError(
            "pass either --city or --lat/--lng/--tz, not both: mixing them silently picks one place and drops the other."
        )
    if city is not None and (offline is True or online is False):
        raise ValueError(
            "--city cannot be resolved with --offline; drop it (geocoding needs the network) or pass "
            f"--lat/--lng/--tz for an offline relocated {cmd}."
        )
    return bool(given)


@with_render_flags
def natal(
    profile: SubjectProfile = None,
    name: SubjectName = None,
    date: SubjectDate = None,
    time: SubjectTime = None,
    seconds: SubjectSeconds = None,
    iso_utc: SubjectIsoUtc = None,
    lat: SubjectLat = None,
    lng: SubjectLng = None,
    tz: SubjectTz = None,
    city: SubjectCity = None,
    nation: SubjectNation = None,
    online: OnlineFlag = None,
    offline: OfflineFlag = None,
    altitude: SubjectAltitude = None,
    zodiac: ZodiacTypeOpt = None,
    sidereal_mode: SiderealModeOpt = None,
    houses: HousesSystemOpt = None,
    perspective: PerspectiveOpt = None,
    points: PointsFlag = None,
    fixed_stars: FixedStarsFlag = None,
    with_flags: WithFlags = None,
    without_flags: WithoutFlags = None,
    set_flags: SetFlags = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
    *,
    opts: object = None,
) -> None:
    """Natal chart: text report, JSON, XML or SVG."""
    model = subject_resolver.resolve_subject(_subject_from(locals()), profile)
    _emit_subject_or_chart(model, fmt, output, opts)


@with_render_flags
def now(
    name: SubjectName = None,
    lat: SubjectLat = None,
    lng: SubjectLng = None,
    tz: SubjectTz = None,
    city: SubjectCity = None,
    nation: SubjectNation = None,
    online: OnlineFlag = None,
    offline: OfflineFlag = None,
    altitude: SubjectAltitude = None,
    zodiac: ZodiacTypeOpt = None,
    sidereal_mode: SiderealModeOpt = None,
    houses: HousesSystemOpt = None,
    perspective: PerspectiveOpt = None,
    points: PointsFlag = None,
    fixed_stars: FixedStarsFlag = None,
    with_flags: WithFlags = None,
    without_flags: WithoutFlags = None,
    set_flags: SetFlags = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
    *,
    opts: object = None,
) -> None:
    """Chart of the current moment at a place."""
    flags = _subject_from(locals(), date=None, time=None, seconds=None, iso_utc=None, mode_override="current")
    _emit_subject_or_chart(subject_resolver.resolve_subject(flags, None), fmt, output, opts)


@with_render_flags
def synastry(
    profile: SubjectProfile = None,
    subject2: Subject2Profile = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
    *,
    opts: object = None,
) -> None:
    """Synastry of two stored subjects (dual wheel)."""
    from kerykeion import ChartDataFactory

    first = _stored_subject(profile, "synastry")
    second = _stored_subject(subject2, "synastry", "-S")
    _emit(ChartDataFactory.create_synastry_chart_data(first, second), fmt, output, opts)


@with_render_flags
def transit(
    profile: SubjectProfile = None,
    lat: SubjectLat = None,
    lng: SubjectLng = None,
    tz: SubjectTz = None,
    city: SubjectCity = None,
    nation: SubjectNation = None,
    online: OnlineFlag = None,
    offline: OfflineFlag = None,
    altitude: SubjectAltitude = None,
    to_date: ToDateOpt = None,
    to_time: ToTimeOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
    *,
    opts: object = None,
) -> None:
    """Natal chart against a transit moment (dual wheel).

    The moment defaults to now at the natal birthplace (offline). Pass
    ``--lat/--lng/--tz`` for a relocated transit, or ``--city`` to geocode; pass
    ``--to-date`` and ``--to-time`` together for a specific moment.
    """
    if (to_time is None) != (to_date is None):
        raise ValueError("--to-date and --to-time go together (omit both to transit the current moment).")
    relocated = _relocation(lat, lng, tz, city, online, offline, "transit")
    from kerykeion import ChartDataFactory

    natal = _stored_subject(profile, "transit", online=online, offline=offline)
    # A city geocodes its own place; otherwise the natal birthplace stands unless relocated.
    place: dict[str, Any] = {}
    if relocated:
        place = {"lat": lat, "lng": lng, "tz": tz}
    elif city is None:
        place = {"lat": natal.lat, "lng": natal.lng, "tz": natal.tz_str}
    frame: dict[str, Any] = {flag: getattr(natal, attr, None) for flag, attr in _FRAME.items()}
    # ``create_transit_chart_data`` passes both subjects verbatim, so the transit
    # moment must share the natal frame or the two rings would disagree.
    transit_flags = subject_resolver.SubjectFlags(
        name="Transit",
        date=to_date,
        time=to_time,
        city=city,
        nation=nation,
        online=online,
        offline=offline,
        altitude=altitude,
        mode_override=None if to_date else "current",
        **place,
        **frame,
    )
    transit_subject = subject_resolver.resolve_subject(transit_flags, None)
    _emit(ChartDataFactory.create_transit_chart_data(natal, transit_subject), fmt, output, opts)


@with_render_flags
def composite(
    profile: SubjectProfile = None,
    subject2: Subject2Profile = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
    *,
    opts: object = None,
) -> None:
    """Midpoint composite of two stored subjects."""
    from kerykeion import ChartDataFactory, CompositeSubjectFactory

    first = _stored_subject(profile, "composite")
    second = _stored_subject(subject2, "composite", "-S")
    composite_subject = CompositeSubjectFactory(first, second).get_midpoint_composite_subject_model()
    _emit(ChartDataFactory.create_composite_chart_data(composite_subject), fmt, output, opts)


@with_render_flags
def return_chart(
    profile: SubjectProfile = None,
    return_type: ReturnTypeOpt = None,
    year: YearOpt = None,
    month: MonthOpt = 1,
    day: DayOpt = 1,
    lat: SubjectLat = None,
    lng: SubjectLng = None,
    tz: SubjectTz = None,
    city: SubjectCity = None,
    nation: SubjectNation = None,
    online: OnlineFlag = None,
    offline: OfflineFlag = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
    *,
    opts: object = None,
) -> None:
    """Solar or lunar return for a year (dual wheel).

    Cast for the natal birthplace by default (offline). Relocate with
    ``--lat/--lng/--tz`` or with ``--city --nation`` (geocoded), never both.
    """
    if year is None:
        raise ValueError("return needs --year")
    rtype = {t.lower(): t for t in _RETURN_TYPES}.get(str(return_type or "Solar").strip().lower())
    if rtype is None:
        raise ValueError(f"--type must be {' or '.join(_RETURN_TYPES)}, got {return_type!r}")
    relocated = _relocation(lat, lng, tz, city, online, offline, "return")
    from kerykeion import ChartDataFactory, PlanetaryReturnFactory

    natal = _stored_subject(profile, "return", online=online, offline=offline)
    # PlanetaryReturnFactory geocodes on its own, so it takes the place directly.
    if city is not None:
        factory = PlanetaryReturnFactory(natal, city=city, nation=nation, online=True)
    else:
        place = (lat, lng, tz) if relocated else (natal.lat, natal.lng, natal.tz_str)
        if any(value is None for value in place):
            raise ValueError(
                "return needs the return-chart location: pass --lat/--lng/--tz (or -s a profile with coordinates), "
                "or --city (geocoded)."
            )
        factory = PlanetaryReturnFactory(natal, lat=place[0], lng=place[1], tz_str=place[2], online=False)
    return_subject = factory.next_return_from_date(year, month, day, return_type=rtype)  # type: ignore[arg-type]
    _emit(ChartDataFactory.create_return_chart_data(natal, return_subject), fmt, output, opts)


@with_render_flags
def progression(
    profile: SubjectProfile = None,
    target_year: TargetYearOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
    *,
    opts: object = None,
) -> None:
    """Secondary progression to a target year (dual wheel)."""
    if target_year is None:
        raise ValueError("progression needs --target-year")
    from kerykeion import ChartDataFactory, SecondaryProgressionFactory

    natal = _stored_subject(profile, "progression")
    progressed = SecondaryProgressionFactory.compute(natal, target_year=target_year)
    _emit(ChartDataFactory.create_progression_chart_data(natal, progressed), fmt, output, opts)
