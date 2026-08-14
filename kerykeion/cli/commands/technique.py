# -*- coding: utf-8 -*-
"""``kerykeion technique <sub>`` — analytical techniques on a stored subject.

Every subcommand takes ``-s <profile>`` and emits the technique's model in the
chosen format. The functions are decorator-free (registered by
:mod:`kerykeion.cli.app`) so they remain directly callable from tests. Only the
parameters the CLI actually wants to expose are wired; the rest ride the
library defaults — we pass ``None`` through only when the user gave a value.
"""

from __future__ import annotations

from typing import Any, Optional

from kerykeion.cli import subject_resolver
from kerykeion.cli.commands._shared import (
    _aspect_names,
    _choose,
    _emit,
    _parse_aspects,
    _render_from,
    _split_csv,
)
from kerykeion.cli.commands.charts import _emit_subject_or_chart
from kerykeion.cli.options import (
    AcgLatRangeOpt,
    AcgStepOpt,
    AspectGridTypeOpt,
    AspectIconsFlag,
    AspectOrbOpt,
    AspectsOpt,
    AutoSizeFlag,
    ComputeAspectsFlag,
    ChartLanguageOpt,
    ChartSettingsOpt,
    ChartStyleOpt,
    CountOpt,
    CuspComparisonFlag,
    CustomTitleOpt,
    DegreeIndicatorsFlag,
    DiurnalityFlag,
    EnvelopeFlag,
    ExternalViewFlag,
    FormatOpt,
    HousePositionComparisonFlag,
    IsMoonVoidOpt,
    LifeCapOpt,
    LotLevelsOpt,
    LotOpt,
    MaxAspectsOpt,
    MaxYearsOpt,
    MethodOpt,
    MidpointOrbOpt,
    NoAspectsFlag,
    OutputOpt,
    PaddingOpt,
    PlanetsOpt,
    RateKeyOpt,
    RelocateCityOpt,
    RelocateLatOpt,
    RelocateLngOpt,
    RelocateNationOpt,
    RelocateTzOpt,
    StarOrbOpt,
    Subject2Profile,
    SubjectProfile,
    SvgVariantOpt,
    TargetDateOpt,
    TargetIsoOpt,
    TargetYearOpt,
    ThemeOpt,
    TransparentBackgroundFlag,
    YearsAfterOpt,
    YearsBeforeOpt,
    ZodiacRingFlag,
)
from kerykeion.cli.typer_app import KerykeionTyper

technique_app = KerykeionTyper(
    name="technique",
    help="Analytical techniques on a stored subject (-s <profile>).",
    no_args_is_help=True,
    add_completion=False,
)


def _need_subject(profile: Optional[str], cmd: str) -> object:
    if not profile:
        raise ValueError(f"{cmd} needs -s <profile>")
    return subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile)


@technique_app.command("profections")
def profections(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    target_date: TargetDateOpt = None,  # type: ignore[assignment]
    years_before: YearsBeforeOpt = None,  # type: ignore[assignment]
    years_after: YearsAfterOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Annual profections: the profected year and surrounding years."""
    from kerykeion import ProfectionsFactory

    subject = _need_subject(profile, "profections")
    kwargs: dict[str, Any] = {}
    if target_date is not None:
        kwargs["target_date"] = target_date
    if years_before is not None:
        kwargs["years_before"] = years_before
    if years_after is not None:
        kwargs["years_after"] = years_after
    _emit(ProfectionsFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("firdaria")
def firdaria(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    target_date: TargetDateOpt = None,  # type: ignore[assignment]
    life_cap_years: LifeCapOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Firdaria (medieval time-lords) for the subject."""
    from kerykeion import FirdariaFactory

    subject = _need_subject(profile, "firdaria")
    kwargs: dict[str, Any] = {}
    if target_date is not None:
        kwargs["target_date"] = target_date
    if life_cap_years is not None:
        kwargs["life_cap_years"] = life_cap_years
    _emit(FirdariaFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("zr")
def zr(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    lot: LotOpt = None,  # type: ignore[assignment]
    levels: LotLevelsOpt = None,  # type: ignore[assignment]
    target_date: TargetDateOpt = None,  # type: ignore[assignment]
    life_cap_years: LifeCapOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Zodiacal releasing from the Lot of Fortune (or Spirit)."""
    from kerykeion import ZodiacalReleasingFactory

    subject = _need_subject(profile, "zr")
    kwargs: dict[str, Any] = {}
    chosen_lot = _choose(lot, ("fortune", "spirit"), "lot")
    if chosen_lot is not None:
        kwargs["lot"] = chosen_lot
    if levels is not None:
        if not 1 <= levels <= 4:
            raise ValueError("--levels must be between 1 and 4")
        kwargs["levels"] = levels
    if target_date is not None:
        kwargs["target_date"] = target_date
    if life_cap_years is not None:
        kwargs["life_cap_years"] = life_cap_years
    _emit(ZodiacalReleasingFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("receptions")
def receptions(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Mutual receptions by domicile and exaltation."""
    from kerykeion import MutualReceptionsFactory

    subject = _need_subject(profile, "receptions")
    _emit(MutualReceptionsFactory.from_subject(subject), fmt, output)  # type: ignore[arg-type]


@technique_app.command("horary")
def horary(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    is_moon_void: IsMoonVoidOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Horary chart indicators and considerations before judgement."""
    from kerykeion import HoraryIndicatorsFactory

    subject = _need_subject(profile, "horary")
    kwargs: dict[str, Any] = {}
    if is_moon_void is not None:
        kwargs["is_moon_void"] = is_moon_void
    _emit(HoraryIndicatorsFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("midpoints")
def midpoints(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    orb: MidpointOrbOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Midpoints and midpoint aspects."""
    from kerykeion import MidpointFactory

    subject = _need_subject(profile, "midpoints")
    kwargs: dict[str, Any] = {}
    active = _split_csv(planets)
    if active is not None:
        kwargs["active_points"] = active
    if orb is not None:
        kwargs["aspect_orb"] = orb
    _emit(MidpointFactory.compute(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("directions")
def directions(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    max_years: MaxYearsOpt = None,  # type: ignore[assignment]
    rate: RateKeyOpt = None,  # type: ignore[assignment]
    aspects: AspectsOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Primary directions under the Ptolemy or Naibod rate."""
    from kerykeion import PrimaryDirectionsFactory

    subject = _need_subject(profile, "directions")
    kwargs: dict[str, Any] = {}
    if max_years is not None:
        kwargs["max_years"] = max_years
    chosen_rate = _choose(rate, ("ptolemy", "naibod"), "rate")
    if chosen_rate is not None:
        kwargs["rate_key"] = chosen_rate
    # ``aspects`` here is the set of aspect ANGLES (conjunction, sextile, …),
    # not planets: PrimaryDirectionsFactory.compute validates it against
    # ASPECT_ANGLES and has no planet filter. Binding ``--planets`` to it (as the
    # sibling techniques do for their real planet filters) made the documented
    # flag always crash; the flag is now named for what it actually controls.
    # Shared --aspects syntax; primary directions have no per-aspect orb, so a
    # ':orb' suffix is refused by name rather than silently dropped.
    chosen_aspects = _aspect_names(_parse_aspects(aspects), "primary directions")
    if chosen_aspects is not None:
        valid = set(PrimaryDirectionsFactory.ASPECT_ANGLES)
        invalid = [a for a in chosen_aspects if a not in valid]
        if invalid:
            raise ValueError(
                f"--aspects must be one of {', '.join(sorted(valid))}; got {invalid}."
            )
        kwargs["aspects"] = chosen_aspects
    _emit(PrimaryDirectionsFactory.compute(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("acg")
def acg(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    step: AcgStepOpt = None,  # type: ignore[assignment]
    lat_range: AcgLatRangeOpt = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Astro-cartography: where each planet rises, sets, culminates."""
    from kerykeion import AstroCartographyFactory

    subject = _need_subject(profile, "acg")
    kwargs: dict[str, Any] = {}
    if step is not None:
        kwargs["step"] = step
    if lat_range is not None:
        try:
            lo, hi = (float(p) for p in lat_range.split(","))
        except ValueError as exc:
            raise ValueError(f"--lat-range needs 'min,max', got {lat_range!r}") from exc
        kwargs["lat_range"] = (lo, hi)
    active = _split_csv(planets)
    if active is not None:
        kwargs["planets"] = active
    _emit(AstroCartographyFactory.compute(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("stars")
def stars(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    count: CountOpt = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Heliacal risings/settings of the visible planets at the birthplace."""
    from kerykeion import HeliacalFactory

    subject = _need_subject(profile, "stars")
    julian_day = getattr(subject, "julian_day", None)
    if julian_day is None:
        raise ValueError("the subject has no julian_day to search heliacal events from")
    lat = getattr(subject, "lat", None)
    lng = getattr(subject, "lng", None)
    altitude = getattr(subject, "altitude", 0.0) or 0.0
    if lat is None or lng is None:
        raise ValueError("heliacal search needs the subject's lat/lng")
    kwargs: dict[str, Any] = dict(lat=lat, lng=lng, altitude=altitude)
    if count is not None:
        kwargs["count"] = count
    active = _split_csv(planets)
    if active is not None:
        kwargs["planets"] = active
    factory = HeliacalFactory()
    _emit(factory.search_events(julian_day, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("relocate")
def relocate(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    new_lat: RelocateLatOpt = None,  # type: ignore[assignment]
    new_lng: RelocateLngOpt = None,  # type: ignore[assignment]
    new_city: RelocateCityOpt = None,  # type: ignore[assignment]
    new_nation: RelocateNationOpt = None,  # type: ignore[assignment]
    new_tz: RelocateTzOpt = None,  # type: ignore[assignment]
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
    """Recast houses/angles for the same birth moment at a new location."""
    from kerykeion import RelocatedChartFactory

    subject = _need_subject(profile, "relocate")
    if new_lat is None or new_lng is None:
        raise ValueError("relocate needs --new-lat and --new-lng")
    relocated = RelocatedChartFactory.relocate(
        subject,  # type: ignore[arg-type]
        new_lat,
        new_lng,
        new_city=new_city or "Relocated",
        new_nation=new_nation or "",
        new_tz_str=new_tz,
    )
    # A relocated chart is a subject; emit it like `natal` (subject for text/json,
    # natal chart wrapper for svg).
    _emit_subject_or_chart(relocated, fmt, output, _render_from(locals()))


@technique_app.command("nodes")
def nodes(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    method: MethodOpt = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Planetary nodes (ascending/descending, perihelion/aphelion)."""
    from kerykeion import PlanetaryNodesFactory

    subject = _need_subject(profile, "nodes")
    kwargs: dict[str, Any] = {}
    chosen = _choose(method, ("mean", "osculating"), "method")
    if chosen is not None:
        kwargs["method"] = chosen
    active = _split_csv(planets)
    if active is not None:
        kwargs["planets"] = active
    _emit(PlanetaryNodesFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("house-comparison")
def house_comparison(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    subject2: Subject2Profile = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Where each of one subject's points falls in the other's houses."""
    from kerykeion import HouseComparisonFactory

    if not profile:
        raise ValueError("house-comparison needs -s <profile> for the first subject")
    if not subject2:
        raise ValueError("house-comparison needs -S <profile> for the second subject")
    first = _need_subject(profile, "house-comparison")
    second = _need_subject(subject2, "house-comparison")
    kwargs: dict[str, Any] = {}
    active = _split_csv(planets)
    if active is not None:
        kwargs["active_points"] = active
    factory = HouseComparisonFactory(first, second, **kwargs)  # type: ignore[arg-type]
    _emit(factory.get_house_comparison(), fmt, output)


@technique_app.command("solar-arc")
def solar_arc(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    target_year: TargetYearOpt = None,  # type: ignore[assignment]
    target_iso: TargetIsoOpt = None,  # type: ignore[assignment]
    planets: PlanetsOpt = None,  # type: ignore[assignment]
    compute_aspects: ComputeAspectsFlag = None,  # type: ignore[assignment]
    aspect_orb: AspectOrbOpt = None,  # type: ignore[assignment]
    aspects: AspectsOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Solar-arc directions to a target year or moment.

    The sibling of ``progression``: both move a natal chart forward, one by the
    Sun's arc and one by the secondary-progression day-for-a-year rule.
    """
    from kerykeion import SolarArcFactory

    subject = _need_subject(profile, "solar-arc")
    if target_year is None and target_iso is None:
        raise ValueError("solar-arc needs --target-year or --target-iso")
    kwargs: dict[str, Any] = {}
    if target_year is not None:
        kwargs["target_year"] = target_year
    if target_iso is not None:
        kwargs["target_iso_utc_datetime"] = target_iso
    active = _split_csv(planets)
    if active is not None:
        kwargs["active_points"] = active
    if compute_aspects is not None:
        kwargs["compute_aspects"] = compute_aspects
    if aspect_orb is not None:
        kwargs["aspect_orb"] = aspect_orb
    # Solar arc takes one orb for all aspects (--aspect-orb), so a per-aspect
    # ':orb' has nowhere to go and is refused rather than dropped.
    chosen = _aspect_names(_parse_aspects(aspects), "solar arc")
    if chosen is not None:
        kwargs["aspects"] = chosen
    _emit(SolarArcFactory.compute(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


@technique_app.command("fixed-stars")
def fixed_stars(
    profile: SubjectProfile = None,  # type: ignore[assignment]
    orb: StarOrbOpt = None,  # type: ignore[assignment]
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Fixed stars conjunct the subject's points, within an orb."""
    from kerykeion import FixedStarDiscoveryFactory

    subject = _need_subject(profile, "fixed-stars")
    kwargs: dict[str, Any] = {}
    if orb is not None:
        kwargs["orb"] = orb
    _emit(
        FixedStarDiscoveryFactory.find_prominent_stars(subject, **kwargs),  # type: ignore[arg-type]
        fmt,
        output,
    )
