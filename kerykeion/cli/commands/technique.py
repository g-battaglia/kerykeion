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

import typer

from kerykeion.cli import subject_resolver, warnings
from kerykeion.cli.commands.charts import _emit_subject_or_chart
from kerykeion.cli.options import (
    AcgLatRangeOpt,
    AcgStepOpt,
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
    SubjectProfile,
    TargetDateOpt,
    YearsAfterOpt,
    YearsBeforeOpt,
)
from kerykeion.cli.rendering import formats
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


def _emit(model: object, fmt: Optional[str], output: Optional[str]) -> None:
    warnings.output_with_warnings(model, formats.resolve_format(fmt, output), output)


def _split_csv(values: Optional[list[str]]) -> Optional[list[str]]:
    """Flatten a repeatable option that may also carry comma-separated tokens."""
    if values is None:
        return None
    out: list[str] = []
    for item in values:
        out.extend(part.strip() for part in item.split(",") if part.strip())
    return out or None


def _choose(value: Any, allowed: tuple[str, ...], label: str) -> Any:
    if value is None:
        return None
    v = str(value).strip()
    if v not in allowed:
        raise ValueError(f"--{label} must be {' or '.join(allowed)}, got {value!r}")
    return v


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
    planets: PlanetsOpt = None,  # type: ignore[assignment]
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
    aspects = _split_csv(planets)
    if aspects is not None:
        kwargs["aspects"] = aspects
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
    count: Optional[int] = typer.Option(None, "--count", help="Number of events (default 5)."),
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
    _emit_subject_or_chart(relocated, fmt, output)


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
