# -*- coding: utf-8 -*-
"""Reusable ``Annotated[T, typer.Option(...)]`` aliases for CLI parameters.

Kept in one place so the subject-building flags are spelled identically across
``subject save``, ``natal``, ``synastry`` and every other command that resolves
a subject — and so the help panels stay consistent. Commands compose these
aliases as parameter annotations; typer reads the ``Option`` metadata from the
``Annotated`` wrapper. Only this style is used (not ``x: T = typer.Option(...)``)
because pyright in basic mode flags the assignment form.

Every alias is ``Optional`` with a ``None`` default: a ``None`` value means the
flag was not supplied on the command line, so the resolver can tell "not given"
apart from "given as this value".
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
        "--online/--no-online",
        help="Call the GeoNames API to resolve city/timezone. Default depends on whether "
        "lat+lng+tz are all known. ``--no-online`` overrides a profile saved online.",
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
        help="Transit date YYYY-MM-DD. Give with --to-time; omit both for the current moment.",
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

# ── Technique-specific flags ─────────────────────────────────────────────────
TargetDateOpt = Annotated[
    Optional[str],
    typer.Option(
        "--target-date",
        help="ISO date YYYY-MM-DD the technique is evaluated for (profections, "
        "firdaria, zodiacal releasing). Defaults to the subject's local now.",
        rich_help_panel="Technique",
    ),
]
LotOpt = Annotated[
    Optional[str],
    typer.Option(
        "--lot",
        help="Lot for zodiacal releasing: fortune | spirit (default fortune).",
        rich_help_panel="Technique",
    ),
]
LotLevelsOpt = Annotated[
    Optional[int],
    typer.Option(
        "--levels",
        help="Number of releasing levels to compute (1–4, default 2).",
        rich_help_panel="Technique",
    ),
]
LifeCapOpt = Annotated[
    Optional[int],
    typer.Option(
        "--life-cap-years",
        help="Upper age bound for the technique span (firdaria 120, zodiacal releasing 100).",
        rich_help_panel="Technique",
    ),
]
YearsBeforeOpt = Annotated[
    Optional[int],
    typer.Option(
        "--years-before", help="Past profected years to show (default 3).", rich_help_panel="Technique"
    ),
]
YearsAfterOpt = Annotated[
    Optional[int],
    typer.Option(
        "--years-after", help="Future profected years to show (default 4).", rich_help_panel="Technique"
    ),
]
RateKeyOpt = Annotated[
    Optional[str],
    typer.Option(
        "--rate",
        help="Primary-direction rate: ptolemy | naibod (default ptolemy).",
        rich_help_panel="Technique",
    ),
]
MaxYearsOpt = Annotated[
    Optional[float],
    typer.Option(
        "--max-years",
        help="Hard ceiling on direction arcs, in years of life (primary directions, default 100).",
        rich_help_panel="Technique",
    ),
]
IsMoonVoidOpt = Annotated[
    Optional[bool],
    typer.Option(
        "--moon-void/--no-moon-void",
        help="For the horary considerations: force the Moon's void state rather than compute it.",
        rich_help_panel="Technique",
    ),
]
MethodOpt = Annotated[
    Optional[str],
    typer.Option(
        "--method",
        help="Node method: mean | osculating (planetary nodes, default mean).",
        rich_help_panel="Technique",
    ),
]
PlanetsOpt = Annotated[
    Optional[list[str]],
    typer.Option(
        "--planets",
        help="Comma list of planet names to restrict to (repeatable or CSV). "
        "Default is technique-specific.",
        rich_help_panel="Technique",
    ),
]
AspectsOpt = Annotated[
    Optional[list[str]],
    typer.Option(
        "--aspects",
        help="Aspects to use, repeatable or CSV: a name (`trine`) or a name with an "
        "orb (`trine:6`) where the command supports per-aspect orbs. "
        "`kerykeion info literals AspectName` lists the names.",
        rich_help_panel="Analysis",
    ),
]
MidpointOrbOpt = Annotated[
    Optional[float],
    typer.Option(
        "--orb", help="Orb for midpoint aspects, in degrees (default 1.0).", rich_help_panel="Technique"
    ),
]
AcgStepOpt = Annotated[
    Optional[float],
    typer.Option(
        "--step",
        help="Latitude scanning step in degrees for astro-cartography (default 1.0).",
        rich_help_panel="Technique",
    ),
]
AcgLatRangeOpt = Annotated[
    Optional[str],
    typer.Option(
        "--lat-range",
        help="Latitude band 'min,max' for astro-cartography (default -66,66).",
        rich_help_panel="Technique",
    ),
]
RelocateCityOpt = Annotated[
    Optional[str],
    typer.Option(
        "--new-city", help="City label for the relocated chart (default 'Relocated').",
        rich_help_panel="Technique",
    ),
]
RelocateNationOpt = Annotated[
    Optional[str],
    typer.Option("--new-nation", help="Nation for the relocated chart.", rich_help_panel="Technique"),
]
RelocateTzOpt = Annotated[
    Optional[str],
    typer.Option(
        "--new-tz", help="Timezone for the relocated chart (default: original).",
        rich_help_panel="Technique",
    ),
]
RelocateLatOpt = Annotated[
    Optional[float],
    typer.Option("--new-lat", help="Latitude of the relocation (required).", rich_help_panel="Technique"),
]
RelocateLngOpt = Annotated[
    Optional[float],
    typer.Option("--new-lng", help="Longitude of the relocation (required).", rich_help_panel="Technique"),
]

# ── Sky-specific flags ───────────────────────────────────────────────────────
FromOpt = Annotated[
    Optional[str],
    typer.Option(
        "--from",
        help="Range start (ISO date or datetime: YYYY-MM-DD or YYYY-MM-DDThh:mm). "
        "For sun-times/hours/eclipses this is a single moment or start year.",
        rich_help_panel="Range",
    ),
]
ToOpt = Annotated[
    Optional[str],
    typer.Option("--to", help="Range end (ISO date or datetime).", rich_help_panel="Range"),
]
StartYearOpt = Annotated[
    Optional[int],
    typer.Option(
        "--start-year", help="First year to search (eclipses). Default: current UTC year.",
        rich_help_panel="Sky",
    ),
]
CountOpt = Annotated[
    Optional[int],
    typer.Option(
        "--count", help="How many events to return (eclipses default 5/10, heliacal default 5).",
        rich_help_panel="Sky",
    ),
]
PhaseOpt = Annotated[
    Optional[list[str]],
    typer.Option(
        "--phase",
        help="Lunation phase to include (repeatable): new | first_quarter | full | last_quarter. "
        "Default: all four.",
        rich_help_panel="Sky",
    ),
]
ZodiacSkyOpt = Annotated[
    Optional[str],
    typer.Option(
        "--zodiac", help="Tropical | Sidereal (sky searches).", rich_help_panel="Sky"
    ),
]
SiderealSkyOpt = Annotated[
    Optional[str],
    typer.Option(
        "--sidereal-mode", help="Ayanamsa for sidereal sky searches.", rich_help_panel="Sky"
    ),
]

# ── Series (ephemeris / transits) flags ──────────────────────────────────────
StepTypeOpt = Annotated[
    Optional[str],
    typer.Option(
        "--step-type",
        help="Sampling granularity: days | hours | minutes (default days).",
        rich_help_panel="Series",
    ),
]
SeriesStepOpt = Annotated[
    Optional[int],
    typer.Option(
        "--step", help="Sample every N units (default 1). Must be positive.", rich_help_panel="Series"
    ),
]
NoLimitFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--no-limit",
        help="Disable the ephemeris sampling ceiling (730 days / 8760 hours / 525600 minutes). "
        "The pre-flight check is skipped and max_*=None is passed through. Use carefully.",
        rich_help_panel="Series",
    ),
]
EventsFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--events",
        help="For `transits`: return discrete events (applying→exact→separating) instead of "
        "per-sample aspect lists.",
        rich_help_panel="Series",
    ),
]
RefineFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--refine",
        help="For `transits --events`: refine exact moments to sub-step precision (geocentric only).",
        rich_help_panel="Series",
    ),
]

# ── Dispatcher (`kerykeion call`) flags ──────────────────────────────────────
ListFlag = Annotated[
    Optional[bool],
    typer.Option("--list", help="List the call targets available (Factory.method / function)."),
]
JsonListFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--json",
        help="With --list: emit a JSON array. With --explain: a JSON array of parameters.",
    ),
]
ExplainFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--explain",
        help="Describe every parameter of the target (cli | subject | json-only | unsupported) and exit.",
    ),
]
ParamOpt = Annotated[
    Optional[list[str]],
    typer.Option(
        "--param",
        help="A method parameter as key=value (repeatable). Value is coerced to the "
        "parameter's type; use --param key='{...}' JSON for structural types.",
        rich_help_panel="Call",
    ),
]
CallSubject2Opt = Annotated[
    Optional[str],
    typer.Option(
        "-S",
        "--subject2",
        help="Second subject (profile): bound to the target's second subject parameter.",
        rich_help_panel="Call",
    ),
]

# ── Analysis commands (aspects, dominants, moon, relationship-score) ─────────
DeclinationsFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--declinations",
        help="Use the declination aspects (parallel / contra-parallel) instead of "
        "the ecliptic ones.",
        rich_help_panel="Analysis",
    ),
]
DeclinationOrbOpt = Annotated[
    Optional[float],
    typer.Option(
        "--orb",
        help="Orb for declination aspects (used with --declinations).",
        rich_help_panel="Analysis",
    ),
]
AxisOrbLimitOpt = Annotated[
    Optional[float],
    typer.Option(
        "--axis-orb-limit",
        help="Cap the orb used for the axes (Asc/MC and their opposites).",
        rich_help_panel="Analysis",
    ),
]
DominantMethodOpt = Annotated[
    Optional[str],
    typer.Option(
        "--method",
        help="Dominants strategy. `kerykeion info methods` lists what is available.",
        rich_help_panel="Analysis",
    ),
]
DistributionMethodOpt = Annotated[
    Optional[str],
    typer.Option(
        "--distribution-method",
        help="How element/quality distributions are weighted.",
        rich_help_panel="Analysis",
    ),
]
CustomWeightsOpt = Annotated[
    Optional[str],
    typer.Option(
        "--custom-weights",
        help='JSON object of per-point weights, e.g. \'{"Sun": 1.5}\'.',
        rich_help_panel="Analysis",
    ),
]
AccidentalDignitiesFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--accidental-dignities",
        help="Include accidental dignities in the dominants scoring.",
        rich_help_panel="Analysis",
    ),
]
ScoreBreakdownFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--score-breakdown",
        help="Include the per-point score breakdown.",
        rich_help_panel="Analysis",
    ),
]
MajorAspectsOnlyFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--all-aspects/--major-aspects-only",
        help="Score every aspect, or only the major ones (default: major only).",
        rich_help_panel="Analysis",
    ),
]
UsingDefaultLocationFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--using-default-location",
        help="Use the library's default location rather than the subject's.",
        rich_help_panel="Analysis",
    ),
]
LocationPrecisionOpt = Annotated[
    Optional[int],
    typer.Option(
        "--location-precision",
        help="Rounding applied to the location before the lookup.",
        rich_help_panel="Analysis",
    ),
]
StarOrbOpt = Annotated[
    Optional[float],
    typer.Option(
        "--orb", help="Orb, in degrees, for a star to count as prominent.",
        rich_help_panel="Technique",
    ),
]
TargetIsoOpt = Annotated[
    Optional[str],
    typer.Option(
        "--target-iso",
        help="Target moment as an ISO UTC datetime (alternative to --target-year).",
        rich_help_panel="Technique",
    ),
]
ComputeAspectsFlag = Annotated[
    Optional[bool],
    typer.Option(
        # Deliberately not "--aspects": that flag names *which* aspects, and one
        # flag with two meanings is what these reviews keep having to undo.
        "--compute-aspects/--no-compute-aspects",
        help="Compute the directed aspects (default: on).",
        rich_help_panel="Technique",
    ),
]
AspectOrbOpt = Annotated[
    Optional[float],
    typer.Option(
        "--aspect-orb", help="Orb for the directed aspects.", rich_help_panel="Technique"
    ),
]
PlanetIdOpt = Annotated[
    Optional[str],
    typer.Option(
        "--planet",
        help="The body occulted by the Moon, by name or Swiss Ephemeris id "
        "(required; calculated points such as the nodes cannot be occulted).",
        rich_help_panel="Sky",
    ),
]

SnapshotFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--snapshot",
        help="Also store the computed subject in the profile, so later reads reuse "
        "it instead of recomputing. Ignored automatically if the kerykeion version "
        "or ephemeris backend changes.",
        rich_help_panel="Subject",
    ),
]

# ── Report shaping (--format text) ───────────────────────────────────────────
NoAspectsFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--no-aspects",
        help="Omit the aspects section from the text report.",
        rich_help_panel="Report",
    ),
]
MaxAspectsOpt = Annotated[
    Optional[int],
    typer.Option(
        "--max-aspects",
        help="Keep at most N aspects in the text report (the tightest ones first).",
        rich_help_panel="Report",
    ),
]
EnvelopeFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--envelope",
        help="Wrap the payload with provenance and the warnings, in-band (JSON only) "
        "— for a pipeline that cannot read stderr.",
        rich_help_panel="Report",
    ),
]

# ── Chart appearance (--format svg) ──────────────────────────────────────────
# Boolean convention, and the reason it is asymmetric: a flag whose library
# default is False needs no negative form ("not given" already means False), but
# a flag whose default is True is *useless* without one — that is exactly the
# bug that made the documented `--no-online` unreachable. So every knob the
# library defaults to True is declared in the paired `--x/--no-x` form.
ThemeOpt = Annotated[
    Optional[str],
    typer.Option(
        "--theme",
        help="Chart theme: light, dark, dark-high-contrast, classic, strawberry, "
        "black-and-white.",
        rich_help_panel="Chart (SVG)",
    ),
]
ChartLanguageOpt = Annotated[
    Optional[str],
    typer.Option(
        "--chart-language",
        help="Language of the chart labels: EN, FR, PT, IT, CN, ES, RU, TR, DE, HI.",
        rich_help_panel="Chart (SVG)",
    ),
]
ChartStyleOpt = Annotated[
    Optional[str],
    typer.Option(
        "--style", help="Chart style: classic or modern.", rich_help_panel="Chart (SVG)"
    ),
]
CustomTitleOpt = Annotated[
    Optional[str],
    typer.Option(
        "--custom-title",
        help="Replace the chart's title line.",
        rich_help_panel="Chart (SVG)",
    ),
]
PaddingOpt = Annotated[
    Optional[int],
    typer.Option(
        "--padding", help="Outer padding in SVG units.", rich_help_panel="Chart (SVG)"
    ),
]
ExternalViewFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--external-view",
        help="Draw the external (outer-ring) layout. Classic style only — with the "
        "default --style modern the library ignores it and says so on stderr.",
        rich_help_panel="Chart (SVG)",
    ),
]
TransparentBackgroundFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--transparent-background",
        help="Omit the background rectangle (for compositing).",
        rich_help_panel="Chart (SVG)",
    ),
]
CuspComparisonFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--cusp-position-comparison",
        help="Show the cusp-position comparison (dual wheels).",
        rich_help_panel="Chart (SVG)",
    ),
]
AutoSizeFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--auto-size/--no-auto-size",
        help="Size the viewBox to the content (default: on).",
        rich_help_panel="Chart (SVG)",
    ),
]
DegreeIndicatorsFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--degree-indicators/--no-degree-indicators",
        help="Draw the degree ticks (default: on). Classic style only — with the "
        "default --style modern the library ignores it and says so on stderr.",
        rich_help_panel="Chart (SVG)",
    ),
]
AspectIconsFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--aspect-icons/--no-aspect-icons",
        help="Draw aspect glyphs in the grid (default: on). Classic style only — with "
        "the default --style modern the library ignores it and says so on stderr.",
        rich_help_panel="Chart (SVG)",
    ),
]
ZodiacRingFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--zodiac-ring/--no-zodiac-ring",
        help="Draw the zodiac background ring (default: on).",
        rich_help_panel="Chart (SVG)",
    ),
]
DiurnalityFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--diurnality/--no-diurnality",
        help="Mark day/night sect (default: on).",
        rich_help_panel="Chart (SVG)",
    ),
]
HousePositionComparisonFlag = Annotated[
    Optional[bool],
    typer.Option(
        "--house-position-comparison/--no-house-position-comparison",
        help="Show the house-position comparison (default: on). Dual wheels only "
        "(synastry, transit, return, progression).",
        rich_help_panel="Chart (SVG)",
    ),
]
AspectGridTypeOpt = Annotated[
    Optional[str],
    typer.Option(
        "--aspect-grid-type",
        help="Dual-chart aspect grid: list or table.",
        rich_help_panel="Chart (SVG)",
    ),
]
SvgVariantOpt = Annotated[
    Optional[str],
    typer.Option(
        "--svg-variant",
        help="Which SVG to render: full (default), wheel (wheel only), "
        "aspect-grid (grid only).",
        rich_help_panel="Chart (SVG)",
    ),
]
ChartSettingsOpt = Annotated[
    Optional[str],
    typer.Option(
        "--chart-settings",
        help="JSON file with any of: colors_settings, celestial_points_settings, "
        "aspects_settings, language_pack. Structural settings that are too big "
        "for a flag.",
        rich_help_panel="Chart (SVG)",
    ),
]
