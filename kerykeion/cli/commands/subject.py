# -*- coding: utf-8 -*-
"""``kerykeion subject`` — create, inspect and verify stored subject profiles.

A profile is the editable recipe (JSON, 0600) that rebuilds a subject: ``save``
persists it, ``show``/``list``/``path`` read it, ``verify`` round-trips it
through the factory. The chart commands take it as ``-s <name>``.
"""

from __future__ import annotations

from typing import Optional

import typer

from kerykeion.cli import config, profiles, subject_resolver, warnings
from kerykeion.cli.commands._shared import _emit, _subject_from
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
    SnapshotFlag,
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
    snapshot: SnapshotFlag = None,
) -> None:
    """Build a recipe from the flags and persist it as a profile (0600)."""
    if store_name.endswith(".json"):  # the store adds .json, and -s reads a .json spec as a file path
        raise ValueError(
            "profile names cannot end in '.json': -s resolves a .json spec as a file path, so the stored profile "
            "would never load back. Drop the suffix (the store adds its own)."
        )
    flags = _subject_from(locals())
    flags.name = flags.name or store_name
    recipe = subject_resolver.merge_inputs(flags)
    # With --snapshot the recipe is materialised now, so a broken one fails at `save`, not at the first read.
    stored = subject_resolver.materialize(recipe).model_dump(mode="json") if snapshot else None
    profile = profiles.Profile(
        name=flags.name, input=profiles.ProfileInput(**recipe), snapshot=stored, meta=profiles.make_meta()
    )
    path = config.profile_path(store_name)
    profiles.save(path, profile)
    typer.echo(str(path))  # stdout is scriptable; the human line goes to stderr
    typer.echo(f"Saved profile {store_name!r} ({path}).", err=True)


@subject_app.command("show")
def show(
    profile_spec: str = typer.Argument(..., help="Profile name or file path."),
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Print a stored profile (recipe + provenance)."""
    _emit(profiles.load(profiles.resolve_path(profile_spec)), fmt, output)


@subject_app.command("list")
def list_cmd(fmt: FormatOpt = None) -> None:
    """List profile names in the store (text: one per line; pipe: JSON array)."""
    _emit(profiles.list_profiles(), fmt, None)


@subject_app.command("path")
def path_cmd(profile_spec: str = typer.Argument(..., help="Profile name or file path.")) -> None:
    """Print the resolved on-disk path of a profile."""
    typer.echo(str(profiles.resolve_path(profile_spec)))


@subject_app.command("verify")
def verify(
    profile_spec: str = typer.Argument(..., help="Profile name or file path."),
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Materialise the recipe into a subject and print a compact summary.

    Always recomputes (a snapshot reading back fine is not what ``verify``
    claims) and reports how the stored snapshot compares: ``absent``, ``stale``
    (other version/backend), ``matches``, or ``drifted`` (re-save it).
    """
    model = subject_resolver.materialize(subject_resolver.merge_inputs(subject_resolver.SubjectFlags(), profile_spec))

    def sign(attr: str) -> Optional[str]:
        return getattr(getattr(model, attr, None), "sign", None)

    profile = profiles.load(profiles.resolve_path(profile_spec))
    if not profile.snapshot:
        state = "absent"
    elif subject_resolver.snapshot_is_usable(profile.meta) is not None:
        state = "stale"
    else:
        state = "matches" if model.model_dump(mode="json") == profile.snapshot else "drifted"
    summary = {
        "ok": True,
        "name": getattr(model, "name", None),
        "zodiac_type": getattr(model, "zodiac_type", None),
        "sun": sign("sun"),
        "moon": sign("moon"),
        "ascendant": sign("first_house") or sign("ascendant"),
        "snapshot": state,
    }
    # The summary carries no warnings; the subject it came from may — collect from that one.
    warnings.output_with_warnings(summary, formats.resolve_format(fmt, output), output, warning_source=model)
