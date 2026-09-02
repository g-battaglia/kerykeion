# -*- coding: utf-8 -*-
"""``kerykeion technique <sub>`` — analytical techniques on a stored subject.

Every subcommand takes ``-s <profile>`` and emits the technique's model in the
chosen format. Only the flags actually given reach the factory; the rest ride
the library defaults.
"""

from __future__ import annotations

from typing import Any

from kerykeion.extra.cli.commands._shared import (
    _aspect_names,
    _choose,
    _emit,
    _given,
    _parse_aspects,
    _split_csv,
    _stored_subject,
    with_render_flags,
)
from kerykeion.extra.cli.commands.charts import _emit_subject_or_chart
from kerykeion.extra.cli.options import (
    AcgLatRangeOpt,
    AcgStepOpt,
    AspectOrbOpt,
    AspectsOpt,
    ComputeAspectsFlag,
    CountOpt,
    FormatOpt,
    IsMoonVoidOpt,
    LifeCapOpt,
    LotLevelsOpt,
    LotOpt,
    MaxYearsOpt,
    MethodOpt,
    MidpointOrbOpt,
    OutputOpt,
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
    TargetDateOpt,
    TargetIsoOpt,
    TargetYearOpt,
    YearsAfterOpt,
    YearsBeforeOpt,
)



def profections(
    profile: SubjectProfile = None,
    target_date: TargetDateOpt = None,
    years_before: YearsBeforeOpt = None,
    years_after: YearsAfterOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Annual profections around a target date."""
    from kerykeion import ProfectionsFactory

    subject = _stored_subject(profile, "profections")
    kwargs = _given(target_date=target_date, years_before=years_before, years_after=years_after)
    _emit(ProfectionsFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def firdaria(
    profile: SubjectProfile = None,
    target_date: TargetDateOpt = None,
    life_cap_years: LifeCapOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Firdaria, the Persian time lords."""
    from kerykeion import FirdariaFactory

    subject = _stored_subject(profile, "firdaria")
    kwargs = _given(target_date=target_date, life_cap_years=life_cap_years)
    _emit(FirdariaFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def zr(
    profile: SubjectProfile = None,
    lot: LotOpt = None,
    levels: LotLevelsOpt = None,
    target_date: TargetDateOpt = None,
    life_cap_years: LifeCapOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Zodiacal releasing from the Lot of Fortune (or Spirit)."""
    from kerykeion import ZodiacalReleasingFactory

    subject = _stored_subject(profile, "zr")
    if levels is not None and not 1 <= levels <= 4:
        raise ValueError("--levels must be between 1 and 4")
    kwargs = _given(
        lot=_choose(lot, ("fortune", "spirit"), "lot"),
        levels=levels,
        target_date=target_date,
        life_cap_years=life_cap_years,
    )
    _emit(ZodiacalReleasingFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def receptions(profile: SubjectProfile = None, fmt: FormatOpt = None, output: OutputOpt = None) -> None:
    """Mutual receptions by domicile and exaltation."""
    from kerykeion import MutualReceptionsFactory

    subject = _stored_subject(profile, "receptions")
    _emit(MutualReceptionsFactory.from_subject(subject), fmt, output)  # type: ignore[arg-type]


def horary(
    profile: SubjectProfile = None,
    is_moon_void: IsMoonVoidOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Horary indicators and considerations before judgement."""
    from kerykeion import HoraryIndicatorsFactory

    subject = _stored_subject(profile, "horary")
    _emit(HoraryIndicatorsFactory.from_subject(subject, **_given(is_moon_void=is_moon_void)), fmt, output)  # type: ignore[arg-type]


def midpoints(
    profile: SubjectProfile = None,
    planets: PlanetsOpt = None,
    orb: MidpointOrbOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Midpoints and midpoint aspects."""
    from kerykeion import MidpointFactory

    subject = _stored_subject(profile, "midpoints")
    kwargs = _given(active_points=_split_csv(planets), aspect_orb=orb)
    _emit(MidpointFactory.compute(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def directions(
    profile: SubjectProfile = None,
    max_years: MaxYearsOpt = None,
    rate: RateKeyOpt = None,
    aspects: AspectsOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Primary directions (Ptolemy or Naibod rate)."""
    from kerykeion import PrimaryDirectionsFactory

    subject = _stored_subject(profile, "directions")
    # ``aspects`` are the aspect ANGLES the factory validates against ASPECT_ANGLES
    # (it has no planet filter); no per-aspect orb, so ':orb' is refused by name.
    chosen = _aspect_names(_parse_aspects(aspects), "primary directions")
    if chosen is not None:
        valid = set(PrimaryDirectionsFactory.ASPECT_ANGLES)
        invalid = [a for a in chosen if a not in valid]
        if invalid:
            raise ValueError(f"--aspects must be one of {', '.join(sorted(valid))}; got {invalid}.")
    kwargs = _given(max_years=max_years, rate_key=_choose(rate, ("ptolemy", "naibod"), "rate"), aspects=chosen)
    _emit(PrimaryDirectionsFactory.compute(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def acg(
    profile: SubjectProfile = None,
    step: AcgStepOpt = None,
    lat_range: AcgLatRangeOpt = None,
    planets: PlanetsOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Astrocartography: where each planet rises, sets and culminates."""
    from kerykeion import AstroCartographyFactory

    subject = _stored_subject(profile, "acg")
    band = None
    if lat_range is not None:
        try:
            lo, hi = (float(edge) for edge in lat_range.split(","))
        except ValueError as exc:
            raise ValueError(f"--lat-range needs 'min,max', got {lat_range!r}") from exc
        band = (lo, hi)
    kwargs = _given(step=step, lat_range=band, planets=_split_csv(planets))
    _emit(AstroCartographyFactory.compute(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def heliacal(
    profile: SubjectProfile = None,
    count: CountOpt = None,
    planets: PlanetsOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Heliacal risings and settings at the birthplace."""
    from kerykeion import HeliacalFactory

    subject = _stored_subject(profile, "heliacal")
    julian_day, lat, lng = (getattr(subject, name, None) for name in ("julian_day", "lat", "lng"))
    if julian_day is None:
        raise ValueError("the subject has no julian_day to search heliacal events from")
    if lat is None or lng is None:
        raise ValueError("heliacal search needs the subject's lat/lng")
    kwargs: dict[str, Any] = {
        "lat": lat,
        "lng": lng,
        "altitude": getattr(subject, "altitude", 0.0) or 0.0,
        **_given(count=count, planets=_split_csv(planets)),
    }
    _emit(HeliacalFactory().search_events(julian_day, **kwargs), fmt, output)  # type: ignore[arg-type]


@with_render_flags
def relocate(
    profile: SubjectProfile = None,
    new_lat: RelocateLatOpt = None,
    new_lng: RelocateLngOpt = None,
    new_city: RelocateCityOpt = None,
    new_nation: RelocateNationOpt = None,
    new_tz: RelocateTzOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
    *,
    opts: object = None,
) -> None:
    """The same birth moment recast at another place."""
    from kerykeion import RelocatedChartFactory

    subject = _stored_subject(profile, "relocate")
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
    _emit_subject_or_chart(relocated, fmt, output, opts)  # a relocated chart is a subject: emitted like `natal`


def nodes(
    profile: SubjectProfile = None,
    method: MethodOpt = None,
    planets: PlanetsOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Planetary nodes and apsides (perigee and apogee for the Moon)."""
    from kerykeion import PlanetaryNodesFactory

    subject = _stored_subject(profile, "nodes")
    kwargs = _given(method=_choose(method, ("mean", "osculating"), "method"), planets=_split_csv(planets))
    _emit(PlanetaryNodesFactory.from_subject(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def house_comparison(
    profile: SubjectProfile = None,
    subject2: Subject2Profile = None,
    planets: PlanetsOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Each subject's points in the other's houses."""
    from kerykeion import HouseComparisonFactory

    first = _stored_subject(profile, "house-comparison")
    second = _stored_subject(subject2, "house-comparison", "-S")
    factory = HouseComparisonFactory(first, second, **_given(active_points=_split_csv(planets)))  # type: ignore[arg-type]
    _emit(factory.get_house_comparison(), fmt, output)


def solar_arc(
    profile: SubjectProfile = None,
    target_year: TargetYearOpt = None,
    target_iso: TargetIsoOpt = None,
    planets: PlanetsOpt = None,
    compute_aspects: ComputeAspectsFlag = None,
    aspect_orb: AspectOrbOpt = None,
    aspects: AspectsOpt = None,
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Solar-arc directions to a target year or moment."""
    from kerykeion import SolarArcFactory

    subject = _stored_subject(profile, "solar-arc")
    if target_year is None and target_iso is None:
        raise ValueError("solar-arc needs --target-year or --target-iso")
    kwargs = _given(
        target_year=target_year,
        target_iso_utc_datetime=target_iso,
        active_points=_split_csv(planets),
        compute_aspects=compute_aspects,
        aspect_orb=aspect_orb,
        aspects=_aspect_names(_parse_aspects(aspects), "solar arc"),  # one orb for all (--aspect-orb): no ':orb'
    )
    _emit(SolarArcFactory.compute(subject, **kwargs), fmt, output)  # type: ignore[arg-type]


def fixed_stars(
    profile: SubjectProfile = None, orb: StarOrbOpt = None, fmt: FormatOpt = None, output: OutputOpt = None
) -> None:
    """Fixed stars conjunct the subject's points."""
    from kerykeion import FixedStarDiscoveryFactory

    subject = _stored_subject(profile, "fixed-stars")
    _emit(FixedStarDiscoveryFactory.find_prominent_stars(subject, **_given(orb=orb)), fmt, output)  # type: ignore[arg-type]


COMMANDS = [
    ("profections", profections),
    ("firdaria", firdaria),
    ("zr", zr),
    ("receptions", receptions),
    ("horary", horary),
    ("midpoints", midpoints),
    ("directions", directions),
    ("acg", acg),
    ("heliacal", heliacal),
    ("relocate", relocate),
    ("nodes", nodes),
    ("house-comparison", house_comparison),
    ("solar-arc", solar_arc),
    ("fixed-stars", fixed_stars),
]
