# -*- coding: utf-8 -*-
"""Chart commands: ``natal``, ``synastry``, ``transit`` and the rest.

Each function here is a plain callable annotated with the shared ``Annotated``
option aliases from :mod:`kerykeion.cli.options`; :mod:`kerykeion.cli.app`
registers them as top-level commands. Keeping them decorator-free means the
functions are callable directly from tests without going through Click.

Design choice: the relationship/predictive charts (``synastry``, ``transit``,
``composite``, ``return``, ``progression``) take the base subject as
``-s <profile>`` only — you ``subject save`` a profile once, then reuse it. Only
``natal`` and ``now`` spell the full inline flag set, because a one-off natal is
the most common interactive use. SVG always goes through
:meth:`ChartDrawer.generate_svg_string` (never ``save_svg``).
"""

from __future__ import annotations

from typing import Optional

from kerykeion.cli import subject_resolver, warnings
from kerykeion.cli.options import (
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
from kerykeion.cli.rendering import formats

_RETURN_TYPES = ("Solar", "Lunar")


def _natal_chart(subject: object) -> object:
    from kerykeion import ChartDataFactory

    # ``subject`` is the AstrologicalSubjectModel returned by resolve_subject;
    # typed ``object`` here because the resolver is intentionally untyped.
    return ChartDataFactory.create_natal_chart_data(subject)  # type: ignore[arg-type]


def _emit_chart(chart: object, fmt: Optional[str], output: Optional[str]) -> None:
    warnings.output_with_warnings(chart, formats.resolve_format(fmt, output), output)


def _emit_subject_or_chart(subject: object, fmt: Optional[str], output: Optional[str]) -> None:
    """Subject for text/json/xml; a natal chart-data wrapper for SVG."""
    resolved = formats.resolve_format(fmt, output)
    if resolved == "svg":
        warnings.output_with_warnings(_natal_chart(subject), resolved, output)
    else:
        warnings.output_with_warnings(subject, resolved, output)


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
    _emit_subject_or_chart(model, fmt, output)


def now(
    name: SubjectName = None,  # type: ignore[assignment]
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
    """Subject for the current moment (transit-style snapshot)."""
    flags = subject_resolver.build_flags(
        name=name, date=None, time=None, seconds=None, iso_utc=None, lat=lat, lng=lng,
        tz=tz, city=city, nation=nation, online=online, offline=offline,
        altitude=altitude, zodiac=zodiac, sidereal_mode=sidereal_mode, houses=houses,
        perspective=perspective, points=points, fixed_stars=fixed_stars,
        with_flags=with_flags, without_flags=without_flags, set_flags=set_flags,
        mode_override="current",
    )
    model = subject_resolver.resolve_subject(flags, None)
    _emit_subject_or_chart(model, fmt, output)


def synastry(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    subject2: Subject2Profile = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Synastry (dual wheel) between two stored subjects."""
    if not profile:
        raise ValueError("synastry needs -s <profile> for the first subject")
    if not subject2:
        raise ValueError("synastry needs -S <profile> for the second subject")
    from kerykeion import ChartDataFactory

    first = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
    second = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), subject2)
    chart = ChartDataFactory.create_synastry_chart_data(first, second)
    _emit_chart(chart, fmt, output)


def transit(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    lat: SubjectLat = None,  # type: ignore[assignment]
    lng: SubjectLng = None,  # type: ignore[assignment]
    tz: SubjectTz = None,  # type: ignore[assignment]
    city: SubjectCity = None,  # type: ignore[assignment]
    nation: SubjectNation = None,  # type: ignore[assignment]
    online: OnlineFlag = None,  # type: ignore[assignment]
    offline: OfflineFlag = None,  # type: ignore[assignment]
    altitude: SubjectAltitude = None,  # type: ignore[assignment]
    to_date: ToDateOpt = None,  # type: ignore[assignment]
    to_time: ToTimeOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Transit dual wheel: natal (inner) vs a transit moment (outer).

    The transit moment defaults to now at the natal birthplace (offline), so
    ``transit -s ada`` works without re-typing coordinates. Pass ``--lat``/
    ``--lng``/``--tz`` for a relocated transit, or ``--city --online`` to
    geocode. For a specific moment, pass ``--to-date`` and ``--to-time``
    together; omit both for the current moment.
    """
    if not profile:
        raise ValueError("transit needs -s <profile> for the natal subject")
    if to_time is not None and to_date is None:
        raise ValueError(
            "--to-time requires --to-date (omit both to transit the current moment)."
        )
    if to_date is not None and to_time is None:
        raise ValueError(
            "--to-date also requires --to-time (omit both to transit the current moment)."
        )
    from kerykeion import ChartDataFactory

    natal = subject_resolver.resolve_subject(
        subject_resolver.SubjectFlags(online=online, offline=offline), profile
    )
    # The transit moment is a minimal subject: just a place and a moment, but it
    # MUST share the natal frame (zodiac, sidereal mode, houses, perspective) —
    # ``create_transit_chart_data`` passes both subjects verbatim to
    # ``create_chart_data``; it does not re-frame the transit wheel. Without
    # inheriting these the outer ring would always be Tropical/Placidus/
    # Apparent-Geocentric regardless of the natal, producing a dual wheel whose
    # two rings disagree. ``series transits`` does the same inheritance.
    transit_flags = subject_resolver.SubjectFlags(
        name="Transit",
        date=to_date,
        time=to_time,
        lat=lat if lat is not None else getattr(natal, "lat", None),
        lng=lng if lng is not None else getattr(natal, "lng", None),
        tz=tz if tz is not None else getattr(natal, "tz_str", None),
        city=city,
        nation=nation,
        online=online,
        offline=offline,
        altitude=altitude,
        zodiac=getattr(natal, "zodiac_type", None),
        sidereal_mode=getattr(natal, "sidereal_mode", None),
        houses=getattr(natal, "houses_system_identifier", None),
        perspective=getattr(natal, "perspective_type", None),
        # Default to "now" when no --to-date is given.
        mode_override=None if to_date else "current",
    )
    transit_subject = subject_resolver.resolve_subject(transit_flags, None)
    chart = ChartDataFactory.create_transit_chart_data(natal, transit_subject)
    _emit_chart(chart, fmt, output)


def composite(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    subject2: Subject2Profile = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Composite chart (midpoint) of two stored subjects."""
    if not profile:
        raise ValueError("composite needs -s <profile> for the first subject")
    if not subject2:
        raise ValueError("composite needs -S <profile> for the second subject")
    from kerykeion import ChartDataFactory, CompositeSubjectFactory

    first = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
    second = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), subject2)
    composite_subject = CompositeSubjectFactory(first, second).get_midpoint_composite_subject_model()
    chart = ChartDataFactory.create_composite_chart_data(composite_subject)
    _emit_chart(chart, fmt, output)


def return_chart(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    return_type: ReturnTypeOpt = None,  # type: ignore[assignment]
    year: YearOpt = None,  # type: ignore[assignment]
    month: MonthOpt = 1,  # type: ignore[assignment]
    day: DayOpt = 1,  # type: ignore[assignment]
    lat: SubjectLat = None,  # type: ignore[assignment]
    lng: SubjectLng = None,  # type: ignore[assignment]
    tz: SubjectTz = None,  # type: ignore[assignment]
    city: SubjectCity = None,  # type: ignore[assignment]
    nation: SubjectNation = None,  # type: ignore[assignment]
    online: OnlineFlag = None,  # type: ignore[assignment]
    offline: OfflineFlag = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Planetary return (Solar/Lunar) as a dual wheel: natal + return chart.

    The return is cast for the natal birthplace by default (offline, no network).
    Override the location for a relocated return with ``--lat/--lng/--tz`` (or
    ``--city --nation --online``).
    """
    if not profile:
        raise ValueError("return needs -s <profile> for the natal subject")
    if year is None:
        raise ValueError("return needs --year")
    rtype = return_type or "Solar"
    if rtype not in _RETURN_TYPES:
        raise ValueError(f"--type must be {' or '.join(_RETURN_TYPES)}, got {rtype!r}")
    from kerykeion import ChartDataFactory, PlanetaryReturnFactory

    natal = subject_resolver.resolve_subject(
        subject_resolver.SubjectFlags(online=online, offline=offline), profile
    )
    # PlanetaryReturnFactory does its own geocoding (unlike the other chart
    # factories): it needs a return-chart location. Default to the natal
    # birthplace (offline); explicit flags relocate the return.
    r_lat = lat if lat is not None else getattr(natal, "lat", None)
    r_lng = lng if lng is not None else getattr(natal, "lng", None)
    r_tz = tz if tz is not None else getattr(natal, "tz_str", None)
    coords = r_lat is not None and r_lng is not None and r_tz is not None
    if online is True:
        if not city:
            raise ValueError("--online return needs --city (and ideally --nation)")
        factory = PlanetaryReturnFactory(natal, city=city, nation=nation, online=True)
    elif offline is True or coords:
        if not coords:
            raise ValueError(
                "return needs the return-chart location: pass --lat/--lng/--tz "
                "(or -s a profile with coordinates), or use --city --online."
            )
        factory = PlanetaryReturnFactory(natal, lat=r_lat, lng=r_lng, tz_str=r_tz, online=False)
    else:
        raise ValueError(
            "return needs the return-chart location: pass --lat/--lng/--tz "
            "(or -s a profile with coordinates), or use --city --online."
        )
    return_subject = factory.next_return_from_date(
        year, month, day, return_type=rtype  # type: ignore[arg-type]  # validated above
    )
    chart = ChartDataFactory.create_return_chart_data(natal, return_subject)
    _emit_chart(chart, fmt, output)


def progression(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    target_year: TargetYearOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Secondary progression dual wheel for a target year.

    Progressed angles follow the Q2 / daily-houses convention (MC ~360 deg/year),
    not astro.com's solar-arc default.
    """
    if not profile:
        raise ValueError("progression needs -s <profile> for the natal subject")
    if target_year is None:
        raise ValueError("progression needs --target-year")
    from kerykeion import ChartDataFactory, SecondaryProgressionFactory

    natal = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)
    progressed = SecondaryProgressionFactory.compute(natal, target_year=target_year)
    chart = ChartDataFactory.create_progression_chart_data(natal, progressed)
    _emit_chart(chart, fmt, output)
