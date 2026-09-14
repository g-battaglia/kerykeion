# -*- coding: utf-8 -*-
"""``kerykeion subject`` — create, inspect and verify stored subject profiles.

A profile is the editable recipe (JSON, 0600) that rebuilds a subject: ``save``
persists it, ``show``/``list``/``path`` read it, ``verify`` rebuilds it through
the factory. The chart commands take it as ``-s <name>``.
"""

from __future__ import annotations

from typing import Annotated, Optional

import sys
from kerykeion_cli import profiles, subject_resolver, warnings
from kerykeion_cli.commands._shared import _emit, _subject_from
from kerykeion_cli.parser import Arg
from kerykeion_cli.options import (
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
from kerykeion_cli import rendering



def save(
    store_name: Annotated[str, Arg(help="Name under which the profile is stored.")],
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
) -> None:
    """Save a subject under a name, for -s <name> everywhere."""
    if store_name.endswith(".json"):  # the store adds .json, and -s reads a .json spec as a file path
        raise ValueError(
            "profile names cannot end in '.json': -s resolves a .json spec as a file path, so the stored profile "
            "would never load back. Drop the suffix (the store adds its own)."
        )
    flags = _subject_from(locals())
    flags.name = flags.name or store_name
    recipe = subject_resolver.merge_inputs(flags)
    profile = profiles.Profile(name=flags.name, input=profiles.ProfileInput(**recipe), meta=profiles.make_meta())
    path = profiles.profile_path(store_name)
    profiles.save(path, profile)
    print(path)  # stdout is scriptable; the human line goes to stderr
    print(f"Saved profile {store_name!r} ({path}).", file=sys.stderr)


def show(
    profile_spec: Annotated[str, Arg(help="Profile name or file path.")],
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Print a stored profile."""
    _emit(profiles.load(profiles.resolve_path(profile_spec)), fmt, output)


def list_cmd(fmt: FormatOpt = None) -> None:
    """List the stored profile names."""
    _emit(profiles.list_profiles(), fmt, None)


def path_cmd(profile_spec: Annotated[str, Arg(help="Profile name or file path.")]) -> None:
    """Print a profile's file path."""
    print(profiles.resolve_path(profile_spec))


def verify(
    profile_spec: Annotated[str, Arg(help="Profile name or file path.")],
    fmt: FormatOpt = None,
    output: OutputOpt = None,
) -> None:
    """Rebuild a profile and print a short summary.

    The cheap pre-flight for a batch: a malformed recipe, a bad timezone or an
    ephemeris gap surfaces here, before a long run starts.
    """
    model = subject_resolver.resolve_subject(subject_resolver.SubjectFlags(), profile_spec)

    def sign(attr: str) -> Optional[str]:
        return getattr(getattr(model, attr, None), "sign", None)

    summary = {
        "ok": True,
        "name": getattr(model, "name", None),
        "zodiac_type": getattr(model, "zodiac_type", None),
        "sun": sign("sun"),
        "moon": sign("moon"),
        "ascendant": sign("first_house") or sign("ascendant"),
    }
    # The summary carries no warnings; the subject it came from may — collect from that one.
    warnings.output_with_warnings(summary, rendering.resolve_format(fmt, output), output, warning_source=model)


COMMANDS = [
    ("save", save),
    ("show", show),
    ("list", list_cmd),
    ("path", path_cmd),
    ("verify", verify),
]
