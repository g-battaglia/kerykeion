# -*- coding: utf-8 -*-
"""Reusable ``Annotated[T, typer.Option(...)]`` aliases for CLI parameters.

Kept in one place so the subject-building flags are spelled identically across
``subject save``, ``natal``, ``synastry`` and every other command that resolves
a subject — and so the help panels stay consistent. Commands compose these
aliases as parameter annotations; typer reads the ``Option`` metadata from the
``Annotated`` wrapper. Only this style is used (not ``x: T = typer.Option(...)``)
because pyright in basic mode flags the assignment form.

Every alias is ``Optional`` with a ``None`` default so the resolver can tell
"not given on the command line" apart from "given as this value" via
:func:`kerykeion.cli.context.was_given`.
"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

# ── Subject identity & birth data ────────────────────────────────────────────
SubjectProfile = Annotated[
    Optional[str],
    typer.Option(
        "-s",
        "--subject",
        help="Profile name (e.g. -s ada) or file path. Omit to build the subject "
        "fully from the inline flags below.",
        rich_help_panel="Subject",
    ),
]
SubjectName = Annotated[
    Optional[str],
    typer.Option("--name", help="Subject display name.", rich_help_panel="Subject"),
]
SubjectDate = Annotated[
    Optional[str],
    typer.Option(
        "--date",
        help="Calendar date as YYYY-MM-DD. Negative years are BCE. Never parsed with "
        "date.fromisoformat (which rejects year < 1).",
        rich_help_panel="Subject",
    ),
]
SubjectTime = Annotated[
    Optional[str],
    typer.Option("--time", help="Clock time as HH:MM or HH:MM:SS.", rich_help_panel="Subject"),
]
SubjectSeconds = Annotated[
    Optional[int],
    typer.Option("--seconds", help="Seconds component of the birth time.", rich_help_panel="Subject"),
]
SubjectIsoUtc = Annotated[
    Optional[str],
    typer.Option(
        "--iso-utc",
        help="Build from an ISO-8601 UTC timestamp instead of --date/--time.",
        rich_help_panel="Subject",
    ),
]
SubjectLat = Annotated[
    Optional[float],
    typer.Option("--lat", help="Birth latitude in decimal degrees.", rich_help_panel="Subject"),
]
SubjectLng = Annotated[
    Optional[float],
    typer.Option("--lng", help="Birth longitude in decimal degrees.", rich_help_panel="Subject"),
]
SubjectTz = Annotated[
    Optional[str],
    typer.Option("--tz", "--tz-str", help="IANA timezone, e.g. Europe/Rome.", rich_help_panel="Subject"),
]
SubjectCity = Annotated[
    Optional[str],
    typer.Option(
        "--city", help="City name (used for display and GeoNames when online).", rich_help_panel="Subject"
    ),
]
SubjectNation = Annotated[
    Optional[str],
    typer.Option("--nation", help="ISO country code or name.", rich_help_panel="Subject"),
]
SubjectAltitude = Annotated[
    Optional[float],
    typer.Option("--altitude", help="Birth altitude in metres.", rich_help_panel="Subject"),
]

# ── Online / offline ─────────────────────────────────────────────────────────
OnlineFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--online",
        help="Call the GeoNames API to resolve city/timezone. Default depends on whether "
        "lat+lng+tz are all known.",
        rich_help_panel="Subject",
    ),
]
OfflineFlag = Annotated[
    Optional[bool],
    typer.Option("--offline", help="Never call GeoNames (the safer default for pipelines).", rich_help_panel="Subject"),
]

# ── Zodiac / houses / perspective ────────────────────────────────────────────
ZodiacTypeOpt = Annotated[
    Optional[str],
    typer.Option("--zodiac", help="Tropical | Sidereal.", rich_help_panel="Subject (advanced)"),
]
SiderealModeOpt = Annotated[
    Optional[str],
    typer.Option(
        "--sidereal-mode",
        help="Ayanamsa for sidereal charts (e.g. FAGAN_BRADLEY, LAHIRI).",
        rich_help_panel="Subject (advanced)",
    ),
]
HousesSystemOpt = Annotated[
    Optional[str],
    typer.Option(
        "--houses",
        help="House system: a letter (P, K, W, C, R, A, M, …) or a name (placidus, koch, "
        "whole-sign, campanus, regiomontanus, equal, morinus).",
        rich_help_panel="Subject (advanced)",
    ),
]
PerspectiveOpt = Annotated[
    Optional[str],
    typer.Option("--perspective", help="Apparent Geocentric | True Geocentric | Heliocentric | Topocentric.", rich_help_panel="Subject (advanced)"),
]

# ── Point set & calculation toggles ──────────────────────────────────────────
PointsFlag = Annotated[
    Optional[str],
    typer.Option(
        "--points",
        help="Point set alias: default | all | traditional | v5 | uranian | main | nodes | axes; "
        "or a comma-separated list of point names.",
        rich_help_panel="Subject (advanced)",
    ),
]
FixedStarsFlag = Annotated[
    Optional[str],
    typer.Option(
        "--fixed-stars",
        help="Fixed-star preset: royal | behenian | default-stars; or a comma-separated list.",
        rich_help_panel="Subject (advanced)",
    ),
]
WithFlags = Annotated[
    Optional[list[str]],
    typer.Option(
        "--with",
        help="Enable a calculate_* feature (repeatable): lunar_phase, dignities, nakshatra, "
        "gauquelin, nutation, local_space.",
        rich_help_panel="Subject (advanced)",
    ),
]
WithoutFlags = Annotated[
    Optional[list[str]],
    typer.Option(
        "--without",
        help="Disable a calculate_* feature (repeatable); same vocabulary as --with.",
        rich_help_panel="Subject (advanced)",
    ),
]
SetFlags = Annotated[
    Optional[list[str]],
    typer.Option(
        "--set",
        help="Pass an advanced factory parameter as key=value (repeatable). Whitelisted against "
        "from_birth_data's signature; keys with a leading underscore are refused.",
        rich_help_panel="Subject (advanced)",
    ),
]

# ── Rendering ────────────────────────────────────────────────────────────────
FormatOpt = Annotated[
    Optional[str],
    typer.Option(
        "-f",
        "--format",
        help="Output format: text | json | xml | svg. Default: text on a TTY, JSON when piped.",
    ),
]
OutputOpt = Annotated[
    Optional[str],
    typer.Option(
        "-o",
        "--output",
        help="Write to a file. Format is inferred from the suffix unless -f is also given.",
    ),
]

# ── Second subject & technique-specific flags ────────────────────────────────
Subject2Profile = Annotated[
    Optional[str],
    typer.Option(
        "-S",
        "--subject2",
        help="Second subject (synastry, composite): profile name or file path.",
        rich_help_panel="Second subject",
    ),
]
ReturnTypeOpt = Annotated[
    Optional[str],
    typer.Option(
        "--type",
        help="Return type: Solar | Lunar (planetary returns). Default Solar.",
        rich_help_panel="Return",
    ),
]
YearOpt = Annotated[
    Optional[int],
    typer.Option("--year", help="Year for the return.", rich_help_panel="Return"),
]
MonthOpt = Annotated[
    int,
    typer.Option("--month", help="Month to search from (default 1).", rich_help_panel="Return"),
]
DayOpt = Annotated[
    int,
    typer.Option("--day", help="Day to search from (default 1).", rich_help_panel="Return"),
]
TargetYearOpt = Annotated[
    Optional[int],
    typer.Option(
        "--target-year",
        help="Target year for the secondary progression.",
        rich_help_panel="Progression",
    ),
]
ToDateOpt = Annotated[
    Optional[str],
    typer.Option(
        "--to-date",
        help="Transit date YYYY-MM-DD. Omit (with --now) for the current moment.",
        rich_help_panel="Transit",
    ),
]
ToTimeOpt = Annotated[
    Optional[str],
    typer.Option(
        "--to-time",
        help="Transit time HH:MM[:SS]. Used with --to-date.",
        rich_help_panel="Transit",
    ),
]
