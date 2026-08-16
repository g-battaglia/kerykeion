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
from kerykeion.cli.commands._shared import _emit, _render_from
from kerykeion.cli.options import (
    AspectGridTypeOpt,
    AspectIconsFlag,
    AutoSizeFlag,
    ChartLanguageOpt,
    ChartSettingsOpt,
    ChartStyleOpt,
    CuspComparisonFlag,
    CustomTitleOpt,
    DayOpt,
    DegreeIndicatorsFlag,
    DiurnalityFlag,
    EnvelopeFlag,
    ExternalViewFlag,
    FixedStarsFlag,
    FormatOpt,
    HousePositionComparisonFlag,
    HousesSystemOpt,
    MaxAspectsOpt,
    MonthOpt,
    NoAspectsFlag,
    OfflineFlag,
    OnlineFlag,
    OutputOpt,
    PaddingOpt,
    PerspectiveOpt,
    PointsFlag,
    ReturnTypeOpt,
    SetFlags,
    SiderealModeOpt,
    SvgVariantOpt,
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
    ThemeOpt,
    ToDateOpt,
    ToTimeOpt,
    TransparentBackgroundFlag,
    WithFlags,
    WithoutFlags,
    YearOpt,
    ZodiacRingFlag,
    ZodiacTypeOpt,
)
from kerykeion.cli.rendering import formats

_RETURN_TYPES = ("Solar", "Lunar")


def _natal_chart(subject: object) -> object:
    from kerykeion import ChartDataFactory

    # ``subject`` is the AstrologicalSubjectModel returned by resolve_subject;
    # typed ``object`` here because the resolver is intentionally untyped.
    return ChartDataFactory.create_natal_chart_data(subject)  # type: ignore[arg-type]


def _emit_subject_or_chart(
    subject: object, fmt: Optional[str], output: Optional[str], opts: object = None
) -> None:
    """Subject for text/json/xml; a natal chart-data wrapper for SVG."""
    resolved = formats.resolve_format(fmt, output)
    if resolved == "svg":
        warnings.output_with_warnings(_natal_chart(subject), resolved, output, opts=opts)
    else:
        warnings.output_with_warnings(subject, resolved, output, opts=opts)


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
    no_aspects: NoAspectsFlag = None,  # type: ignore[assignment]
    max_aspects: MaxAspectsOpt = None,  # type: ignore[assignment]
    envelope: EnvelopeFlag = None,  # type: ignore[assignment]
    theme: ThemeOpt = None,  # type: ignore[assignment]
    chart_language: ChartLanguageOpt = None,  # type: ignore[assignment]
    style: ChartStyleOpt = None,  # type: ignore[assignment]
    custom_title: CustomTitleOpt = None,  # type: ignore[assignment]
    padding: PaddingOpt = None,  # type: ignore[assignment]
    external_view: ExternalViewFlag = None,  # type: ignore[assignment]
    transparent_background: TransparentBackgroundFlag = None,  # type: ignore[assignment]
    cusp_position_comparison: CuspComparisonFlag = None,  # type: ignore[assignment]
    auto_size: AutoSizeFlag = None,  # type: ignore[assignment]
    degree_indicators: DegreeIndicatorsFlag = None,  # type: ignore[assignment]
    aspect_icons: AspectIconsFlag = None,  # type: ignore[assignment]
    zodiac_ring: ZodiacRingFlag = None,  # type: ignore[assignment]
    diurnality: DiurnalityFlag = None,  # type: ignore[assignment]
    house_position_comparison: HousePositionComparisonFlag = None,  # type: ignore[assignment]
    aspect_grid_type: AspectGridTypeOpt = None,  # type: ignore[assignment]
    svg_variant: SvgVariantOpt = None,  # type: ignore[assignment]
    chart_settings: ChartSettingsOpt = None,  # type: ignore[assignment]
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
    _emit_subject_or_chart(model, fmt, output, _render_from(locals()))


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
    no_aspects: NoAspectsFlag = None,  # type: ignore[assignment]
    max_aspects: MaxAspectsOpt = None,  # type: ignore[assignment]
    envelope: EnvelopeFlag = None,  # type: ignore[assignment]
    theme: ThemeOpt = None,  # type: ignore[assignment]
    chart_language: ChartLanguageOpt = None,  # type: ignore[assignment]
    style: ChartStyleOpt = None,  # type: ignore[assignment]
    custom_title: CustomTitleOpt = None,  # type: ignore[assignment]
    padding: PaddingOpt = None,  # type: ignore[assignment]
    external_view: ExternalViewFlag = None,  # type: ignore[assignment]
    transparent_background: TransparentBackgroundFlag = None,  # type: ignore[assignment]
    cusp_position_comparison: CuspComparisonFlag = None,  # type: ignore[assignment]
    auto_size: AutoSizeFlag = None,  # type: ignore[assignment]
    degree_indicators: DegreeIndicatorsFlag = None,  # type: ignore[assignment]
    aspect_icons: AspectIconsFlag = None,  # type: ignore[assignment]
    zodiac_ring: ZodiacRingFlag = None,  # type: ignore[assignment]
    diurnality: DiurnalityFlag = None,  # type: ignore[assignment]
    house_position_comparison: HousePositionComparisonFlag = None,  # type: ignore[assignment]
    aspect_grid_type: AspectGridTypeOpt = None,  # type: ignore[assignment]
    svg_variant: SvgVariantOpt = None,  # type: ignore[assignment]
    chart_settings: ChartSettingsOpt = None,  # type: ignore[assignment]
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
    _emit_subject_or_chart(model, fmt, output, _render_from(locals()))


def synastry(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    subject2: Subject2Profile = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
    no_aspects: NoAspectsFlag = None,  # type: ignore[assignment]
    max_aspects: MaxAspectsOpt = None,  # type: ignore[assignment]
    envelope: EnvelopeFlag = None,  # type: ignore[assignment]
    theme: ThemeOpt = None,  # type: ignore[assignment]
    chart_language: ChartLanguageOpt = None,  # type: ignore[assignment]
    style: ChartStyleOpt = None,  # type: ignore[assignment]
    custom_title: CustomTitleOpt = None,  # type: ignore[assignment]
    padding: PaddingOpt = None,  # type: ignore[assignment]
    external_view: ExternalViewFlag = None,  # type: ignore[assignment]
    transparent_background: TransparentBackgroundFlag = None,  # type: ignore[assignment]
    cusp_position_comparison: CuspComparisonFlag = None,  # type: ignore[assignment]
    auto_size: AutoSizeFlag = None,  # type: ignore[assignment]
    degree_indicators: DegreeIndicatorsFlag = None,  # type: ignore[assignment]
    aspect_icons: AspectIconsFlag = None,  # type: ignore[assignment]
    zodiac_ring: ZodiacRingFlag = None,  # type: ignore[assignment]
    diurnality: DiurnalityFlag = None,  # type: ignore[assignment]
    house_position_comparison: HousePositionComparisonFlag = None,  # type: ignore[assignment]
    aspect_grid_type: AspectGridTypeOpt = None,  # type: ignore[assignment]
    svg_variant: SvgVariantOpt = None,  # type: ignore[assignment]
    chart_settings: ChartSettingsOpt = None,  # type: ignore[assignment]
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
    _emit(chart, fmt, output, _render_from(locals()))


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
    no_aspects: NoAspectsFlag = None,  # type: ignore[assignment]
    max_aspects: MaxAspectsOpt = None,  # type: ignore[assignment]
    envelope: EnvelopeFlag = None,  # type: ignore[assignment]
    theme: ThemeOpt = None,  # type: ignore[assignment]
    chart_language: ChartLanguageOpt = None,  # type: ignore[assignment]
    style: ChartStyleOpt = None,  # type: ignore[assignment]
    custom_title: CustomTitleOpt = None,  # type: ignore[assignment]
    padding: PaddingOpt = None,  # type: ignore[assignment]
    external_view: ExternalViewFlag = None,  # type: ignore[assignment]
    transparent_background: TransparentBackgroundFlag = None,  # type: ignore[assignment]
    cusp_position_comparison: CuspComparisonFlag = None,  # type: ignore[assignment]
    auto_size: AutoSizeFlag = None,  # type: ignore[assignment]
    degree_indicators: DegreeIndicatorsFlag = None,  # type: ignore[assignment]
    aspect_icons: AspectIconsFlag = None,  # type: ignore[assignment]
    zodiac_ring: ZodiacRingFlag = None,  # type: ignore[assignment]
    diurnality: DiurnalityFlag = None,  # type: ignore[assignment]
    house_position_comparison: HousePositionComparisonFlag = None,  # type: ignore[assignment]
    aspect_grid_type: AspectGridTypeOpt = None,  # type: ignore[assignment]
    svg_variant: SvgVariantOpt = None,  # type: ignore[assignment]
    chart_settings: ChartSettingsOpt = None,  # type: ignore[assignment]
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
    # A relocated transit needs matching coordinates AND timezone. Letting the
    # natal tz_str stand in when only --lat/--lng are overridden would localise
    # the transit moment in the natal zone (e.g. Rome) at the new coordinates
    # (e.g. New York) — a multi-hour UTC error in the houses/Ascendant, with no
    # warning. Require the whole inline group, or none (use the natal place).
    _geo_provided = [v for v in (lat, lng, tz) if v is not None]
    if 0 < len(_geo_provided) < 3:
        raise ValueError(
            "a relocated transit needs --lat, --lng and --tz together (or none, "
            "to use the natal birthplace); the natal timezone does not match new "
            "coordinates."
        )
    # ``--city`` relocates by geocoding, so the natal coordinates must NOT be
    # inherited: the factory only geocodes when coordinates are missing, and
    # inherited ones satisfied that gate — the wheel stayed cast for the natal
    # birthplace while the requested city appeared as a display label. Geocoding
    # needs the network, so an explicit --offline alongside a bare --city has
    # no honest resolution.
    if city is not None and not _geo_provided:
        if offline is True or online is False:
            raise ValueError(
                "--city cannot be resolved with --offline; drop it (geocoding "
                "needs the network) or pass --lat/--lng/--tz for an offline "
                "relocation."
            )
    _inherit_geo = city is None
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
    # two rings disagree. ``series transits`` does the same inheritance. The
    # custom-ayanamsa pair is part of that frame: without it a natal cast with
    # ``--sidereal-mode USER`` crashes the transit resolution (the mode needs
    # its two numbers on every rebuild).
    transit_flags = subject_resolver.SubjectFlags(
        name="Transit",
        date=to_date,
        time=to_time,
        lat=lat if lat is not None else (getattr(natal, "lat", None) if _inherit_geo else None),
        lng=lng if lng is not None else (getattr(natal, "lng", None) if _inherit_geo else None),
        tz=tz if tz is not None else (getattr(natal, "tz_str", None) if _inherit_geo else None),
        city=city,
        nation=nation,
        online=online,
        offline=offline,
        altitude=altitude,
        zodiac=getattr(natal, "zodiac_type", None),
        sidereal_mode=getattr(natal, "sidereal_mode", None),
        houses=getattr(natal, "houses_system_identifier", None),
        perspective=getattr(natal, "perspective_type", None),
        custom_ayanamsa_t0=getattr(natal, "custom_ayanamsa_t0", None),
        custom_ayanamsa_ayan_t0=getattr(natal, "custom_ayanamsa_ayan_t0", None),
        # Default to "now" when no --to-date is given.
        mode_override=None if to_date else "current",
    )
    transit_subject = subject_resolver.resolve_subject(transit_flags, None)
    chart = ChartDataFactory.create_transit_chart_data(natal, transit_subject)
    _emit(chart, fmt, output, _render_from(locals()))


def composite(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    subject2: Subject2Profile = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
    no_aspects: NoAspectsFlag = None,  # type: ignore[assignment]
    max_aspects: MaxAspectsOpt = None,  # type: ignore[assignment]
    envelope: EnvelopeFlag = None,  # type: ignore[assignment]
    theme: ThemeOpt = None,  # type: ignore[assignment]
    chart_language: ChartLanguageOpt = None,  # type: ignore[assignment]
    style: ChartStyleOpt = None,  # type: ignore[assignment]
    custom_title: CustomTitleOpt = None,  # type: ignore[assignment]
    padding: PaddingOpt = None,  # type: ignore[assignment]
    external_view: ExternalViewFlag = None,  # type: ignore[assignment]
    transparent_background: TransparentBackgroundFlag = None,  # type: ignore[assignment]
    cusp_position_comparison: CuspComparisonFlag = None,  # type: ignore[assignment]
    auto_size: AutoSizeFlag = None,  # type: ignore[assignment]
    degree_indicators: DegreeIndicatorsFlag = None,  # type: ignore[assignment]
    aspect_icons: AspectIconsFlag = None,  # type: ignore[assignment]
    zodiac_ring: ZodiacRingFlag = None,  # type: ignore[assignment]
    diurnality: DiurnalityFlag = None,  # type: ignore[assignment]
    house_position_comparison: HousePositionComparisonFlag = None,  # type: ignore[assignment]
    aspect_grid_type: AspectGridTypeOpt = None,  # type: ignore[assignment]
    svg_variant: SvgVariantOpt = None,  # type: ignore[assignment]
    chart_settings: ChartSettingsOpt = None,  # type: ignore[assignment]
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
    _emit(chart, fmt, output, _render_from(locals()))


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
    no_aspects: NoAspectsFlag = None,  # type: ignore[assignment]
    max_aspects: MaxAspectsOpt = None,  # type: ignore[assignment]
    envelope: EnvelopeFlag = None,  # type: ignore[assignment]
    theme: ThemeOpt = None,  # type: ignore[assignment]
    chart_language: ChartLanguageOpt = None,  # type: ignore[assignment]
    style: ChartStyleOpt = None,  # type: ignore[assignment]
    custom_title: CustomTitleOpt = None,  # type: ignore[assignment]
    padding: PaddingOpt = None,  # type: ignore[assignment]
    external_view: ExternalViewFlag = None,  # type: ignore[assignment]
    transparent_background: TransparentBackgroundFlag = None,  # type: ignore[assignment]
    cusp_position_comparison: CuspComparisonFlag = None,  # type: ignore[assignment]
    auto_size: AutoSizeFlag = None,  # type: ignore[assignment]
    degree_indicators: DegreeIndicatorsFlag = None,  # type: ignore[assignment]
    aspect_icons: AspectIconsFlag = None,  # type: ignore[assignment]
    zodiac_ring: ZodiacRingFlag = None,  # type: ignore[assignment]
    diurnality: DiurnalityFlag = None,  # type: ignore[assignment]
    house_position_comparison: HousePositionComparisonFlag = None,  # type: ignore[assignment]
    aspect_grid_type: AspectGridTypeOpt = None,  # type: ignore[assignment]
    svg_variant: SvgVariantOpt = None,  # type: ignore[assignment]
    chart_settings: ChartSettingsOpt = None,  # type: ignore[assignment]
) -> None:
    """Planetary return (Solar/Lunar) as a dual wheel: natal + return chart.

    The return is cast for the natal birthplace by default (offline, no network).
    Override the location for a relocated return with ``--lat/--lng/--tz`` or
    with ``--city --nation`` (geocoded; never mix the two — exit 4, one command
    one place).
    """
    if not profile:
        raise ValueError("return needs -s <profile> for the natal subject")
    if year is None:
        raise ValueError("return needs --year")
    # Case-insensitive like every other enum-style flag (`--lot`, `--rate`,
    # `--zodiac`): `--type solar` must not fail where `--zodiac tropical` works.
    rtype = {t.lower(): t for t in _RETURN_TYPES}.get(str(return_type or "Solar").strip().lower())
    if rtype is None:
        raise ValueError(f"--type must be {' or '.join(_RETURN_TYPES)}, got {return_type!r}")
    # Same relocated-location invariant as `transit`: --lat/--lng/--tz must be
    # given together, otherwise the natal timezone would silently localise the
    # return at the new coordinates (wrong houses/Ascendant).
    _geo_provided = [v for v in (lat, lng, tz) if v is not None]
    if 0 < len(_geo_provided) < 3:
        raise ValueError(
            "a relocated return needs --lat, --lng and --tz together (or none, "
            "to use the natal birthplace); the natal timezone does not match new "
            "coordinates."
        )
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
    if city is not None and any(v is not None for v in (lat, lng, tz)):
        # A city and explicit coordinates are two answers to the same question:
        # whichever the factory honoured, the other would be silently dropped.
        raise ValueError(
            "pass either --city or --lat/--lng/--tz, not both: mixing them "
            "silently picks one place and drops the other."
        )
    if city is not None:
        # The city decides the return place, geocoded like `transit` — no
        # explicit --online needed (the geocode runs offline through the default
        # local database when no GeoNames username is configured). It used to be
        # honoured only under --online and silently ignored otherwise, recasting
        # the return at the natal birthplace with the city as a label.
        if offline is True or online is False:
            raise ValueError(
                "--city cannot be resolved with --offline; drop it (geocoding "
                "needs the network) or pass --lat/--lng/--tz for an offline "
                "relocated return."
            )
        factory = PlanetaryReturnFactory(natal, city=city, nation=nation, online=True)
    elif coords:
        # Complete coordinates (inline or inherited from the natal) decide the
        # place even under --online: the location is already specified and
        # geocoding has nothing to add. Requiring --city first used to reject
        # `--lat/--lng/--tz --online` — a fully specified relocated return.
        factory = PlanetaryReturnFactory(natal, lat=r_lat, lng=r_lng, tz_str=r_tz, online=False)
    else:
        raise ValueError(
            "return needs the return-chart location: pass --lat/--lng/--tz "
            "(or -s a profile with coordinates), or --city (geocoded)."
        )
    return_subject = factory.next_return_from_date(
        year, month, day, return_type=rtype  # type: ignore[arg-type]  # validated above
    )
    chart = ChartDataFactory.create_return_chart_data(natal, return_subject)
    _emit(chart, fmt, output, _render_from(locals()))


def progression(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    target_year: TargetYearOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
    no_aspects: NoAspectsFlag = None,  # type: ignore[assignment]
    max_aspects: MaxAspectsOpt = None,  # type: ignore[assignment]
    envelope: EnvelopeFlag = None,  # type: ignore[assignment]
    theme: ThemeOpt = None,  # type: ignore[assignment]
    chart_language: ChartLanguageOpt = None,  # type: ignore[assignment]
    style: ChartStyleOpt = None,  # type: ignore[assignment]
    custom_title: CustomTitleOpt = None,  # type: ignore[assignment]
    padding: PaddingOpt = None,  # type: ignore[assignment]
    external_view: ExternalViewFlag = None,  # type: ignore[assignment]
    transparent_background: TransparentBackgroundFlag = None,  # type: ignore[assignment]
    cusp_position_comparison: CuspComparisonFlag = None,  # type: ignore[assignment]
    auto_size: AutoSizeFlag = None,  # type: ignore[assignment]
    degree_indicators: DegreeIndicatorsFlag = None,  # type: ignore[assignment]
    aspect_icons: AspectIconsFlag = None,  # type: ignore[assignment]
    zodiac_ring: ZodiacRingFlag = None,  # type: ignore[assignment]
    diurnality: DiurnalityFlag = None,  # type: ignore[assignment]
    house_position_comparison: HousePositionComparisonFlag = None,  # type: ignore[assignment]
    aspect_grid_type: AspectGridTypeOpt = None,  # type: ignore[assignment]
    svg_variant: SvgVariantOpt = None,  # type: ignore[assignment]
    chart_settings: ChartSettingsOpt = None,  # type: ignore[assignment]
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
    _emit(chart, fmt, output, _render_from(locals()))
