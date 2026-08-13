# -*- coding: utf-8 -*-
"""``kerykeion subject`` — create, inspect and verify stored subject profiles.

A profile is the editable "recipe" (JSON, 0600) that rebuilds an
:class:`AstrologicalSubjectModel`. This group persists recipes (``save``),
shows them (``show``/``list``/``path``) and round-trips a recipe through the
factory to confirm it materialises (``verify``). The chart commands (``natal``,
``synastry``, …) take a ``-s`` profile name and reuse the same resolver.
"""

from __future__ import annotations

from typing import Optional

import typer

from kerykeion.cli import config, profiles, subject_resolver, warnings
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
    SubjectSeconds,
    SubjectTime,
    SubjectTz,
    WithFlags,
    WithoutFlags,
    ZodiacTypeOpt,
)
from kerykeion.cli.rendering import formats

from kerykeion.cli.typer_app import KerykeionTyper

subject_app = KerykeionTyper(
    name="subject",
    help="Store and inspect subject profiles (birth-data recipes).",
    no_args_is_help=True,
    add_completion=False,
)


@subject_app.command("save")
def save(
    store_name: str = typer.Argument(..., help="Name under which the profile is stored."),
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
) -> None:
    """Build a recipe from the flags and persist it as a profile (0600)."""
    flags = subject_resolver.build_flags(
        name=name, date=date, time=time, seconds=seconds, iso_utc=iso_utc, lat=lat,
        lng=lng, tz=tz, city=city, nation=nation, online=online, offline=offline,
        altitude=altitude, zodiac=zodiac, sidereal_mode=sidereal_mode, houses=houses,
        perspective=perspective, points=points, fixed_stars=fixed_stars,
        with_flags=with_flags, without_flags=without_flags, set_flags=set_flags,
    )
    # The display name falls back to the store name when --name is absent.
    if not flags.name:
        flags.name = store_name

    recipe = subject_resolver.merge_inputs(flags)
    profile = profiles.Profile(
        name=flags.name, input=profiles.ProfileInput(**recipe), meta=profiles.make_meta()
    )
    path = config.profile_path(store_name)
    profiles.save(path, profile)
    # The path goes to stdout (scriptable: ``$(kerykeion subject save ada …)``);
    # the human line goes to stderr so it never pollutes a pipeline.
    typer.echo(str(path))
    typer.echo(f"Saved profile {store_name!r} ({path}).", err=True)


@subject_app.command("show")
def show(
    profile_spec: str = typer.Argument(..., help="Profile name or file path."),
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Print a stored profile (recipe + provenance)."""
    path = profiles.resolve_path(profile_spec)
    profile = profiles.load(path)
    resolved = formats.resolve_format(fmt, output)
    # Route through the warnings funnel for parity with the compute commands
    # (a recipe carries no ephemeris warnings, so this is a no-op for warnings,
    # but it keeps --warnings-as-errors uniformly honoured across subcommands).
    warnings.output_with_warnings(profile, resolved, output)


@subject_app.command("list")
def list_cmd(
    fmt: FormatOpt = None,  # type: ignore[assignment]
) -> None:
    """List profile names in the store (text: one per line; pipe: JSON array)."""
    names = profiles.list_profiles()
    resolved = formats.resolve_format(fmt, None)
    warnings.output_with_warnings(names, resolved, None)


@subject_app.command("path")
def path_cmd(
    profile_spec: str = typer.Argument(..., help="Profile name or file path."),
) -> None:
    """Print the resolved on-disk path of a profile."""
    typer.echo(str(profiles.resolve_path(profile_spec)))


@subject_app.command("verify")
def verify(
    profile_spec: str = typer.Argument(..., help="Profile name or file path."),
    fmt: FormatOpt = None,  # type: ignore[assignment]
    output: OutputOpt = None,  # type: ignore[assignment]
) -> None:
    """Materialise the recipe into a subject and print a compact summary.

    Round-trips the recipe through the factory (so a malformed recipe, a bad
    timezone, or an ephemeris gap surface here, not in the middle of a chart).
    """
    model = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile_spec)
    summary = _subject_summary(model)
    resolved = formats.resolve_format(fmt, output)
    # The compact summary carries no warnings, but the materialised subject it
    # was built from may (an ephemeris gap, a polar-house fallback). Collect from
    # the subject so --warnings-as-errors engages here too, like the charts.
    warnings.output_with_warnings(summary, resolved, output, warning_source=model)


def _subject_summary(model: object) -> dict[str, object]:
    """A compact, robust summary of a materialised subject.

    Every field is read defensively: ``verify`` must never crash on a model
    shape it does not expect, only report what it can find.
    """

    def sign(attr: str) -> Optional[str]:
        point = getattr(model, attr, None)
        return getattr(point, "sign", None) if point is not None else None

    return {
        "ok": True,
        "name": getattr(model, "name", None),
        "zodiac_type": getattr(model, "zodiac_type", None),
        "sun": sign("sun"),
        "moon": sign("moon"),
        "ascendant": sign("first_house") or sign("ascendant"),
    }
