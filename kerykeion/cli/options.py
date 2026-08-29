# -*- coding: utf-8 -*-
"""Reusable ``Annotated[T, typer.Option(...)]`` aliases for CLI parameters.

Kept in one place so the subject-building flags are spelled identically across
``subject save``, ``natal``, ``synastry`` and every other command that resolves
a subject — and so the help panels stay consistent. Commands compose these
aliases as parameter annotations; typer reads the ``Option`` metadata from the
``Annotated`` wrapper.

Almost every alias is ``Optional`` with a ``None`` default: ``None`` means the
flag was not supplied, so the resolver can tell "not given" apart from "given as
this value". The two that are not (``--month``, ``--day``) carry a real default.

:func:`flag` is only shorthand for ``typer.Option(..., rich_help_panel=...)``.
The aliases stay written out as ``Annotated[...]`` on purpose: a factory that
returned the whole alias would read shorter, but pyright then sees a variable
rather than a type alias and rejects every use of it (``reportInvalidTypeForm``,
an error in this project's config).
"""

from __future__ import annotations

from typing import Annotated, Any, Optional

import typer


def flag(*names: str, help: str, panel: Optional[str] = None) -> Any:
    """A ``typer.Option`` for *names*, on the ``panel`` help group."""
    return typer.Option(*names, help=help, rich_help_panel=panel)


# ── Subject identity & birth data ────────────────────────────────────────────
SubjectProfile = Annotated[
    Optional[str],
    flag(
        "-s",
        "--subject",
        help="Profile name (e.g. -s ada) or file path. Omit to build the subject fully from the inline flags below.",
        panel="Subject",
    ),
]
SubjectName = Annotated[Optional[str], flag("--name", help="Subject display name.", panel="Subject")]
SubjectDate = Annotated[
    Optional[str],
    flag(
        "--date",
        help="Calendar date as YYYY-MM-DD. Negative years are BCE. Never parsed with date.fromisoformat (which rejects year < 1).",
        panel="Subject",
    ),
]
SubjectTime = Annotated[Optional[str], flag("--time", help="Clock time as HH:MM or HH:MM:SS.", panel="Subject")]
SubjectSeconds = Annotated[
    Optional[int], flag("--seconds", help="Seconds component of the birth time.", panel="Subject")
]
SubjectIsoUtc = Annotated[
    Optional[str],
    flag("--iso-utc", help="Build from an ISO-8601 UTC timestamp instead of --date/--time.", panel="Subject"),
]
SubjectLat = Annotated[Optional[float], flag("--lat", help="Birth latitude in decimal degrees.", panel="Subject")]
SubjectLng = Annotated[Optional[float], flag("--lng", help="Birth longitude in decimal degrees.", panel="Subject")]
SubjectTz = Annotated[Optional[str], flag("--tz", "--tz-str", help="IANA timezone, e.g. Europe/Rome.", panel="Subject")]
SubjectCity = Annotated[
    Optional[str], flag("--city", help="City name (used for display and GeoNames when online).", panel="Subject")
]
SubjectNation = Annotated[Optional[str], flag("--nation", help="ISO country code or name.", panel="Subject")]
SubjectAltitude = Annotated[Optional[float], flag("--altitude", help="Birth altitude in metres.", panel="Subject")]

# ── Online / offline ─────────────────────────────────────────────────────────
OnlineFlag = Annotated[
    Optional[bool],
    flag(
        "--online/--no-online",
        help="Call the GeoNames API to resolve city/timezone. Default depends on whether lat+lng+tz are all known. ``--no-online`` overrides a profile saved online.",
        panel="Subject",
    ),
]
OfflineFlag = Annotated[
    Optional[bool], flag("--offline", help="Never call GeoNames (the safer default for pipelines).", panel="Subject")
]

# ── Zodiac / houses / perspective ────────────────────────────────────────────
ZodiacTypeOpt = Annotated[Optional[str], flag("--zodiac", help="Tropical | Sidereal.", panel="Subject (advanced)")]
SiderealModeOpt = Annotated[
    Optional[str],
    flag(
        "--sidereal-mode", help="Ayanamsa for sidereal charts (e.g. FAGAN_BRADLEY, LAHIRI).", panel="Subject (advanced)"
    ),
]
HousesSystemOpt = Annotated[
    Optional[str],
    flag(
        "--houses",
        help="House system: a letter (P, K, W, C, R, A, M, …) or a name (placidus, koch, whole-sign, campanus, regiomontanus, equal, morinus).",
        panel="Subject (advanced)",
    ),
]
PerspectiveOpt = Annotated[
    Optional[str],
    flag(
        "--perspective",
        help="Apparent Geocentric | True Geocentric | Heliocentric | Topocentric.",
        panel="Subject (advanced)",
    ),
]

# ── Point set & calculation toggles ──────────────────────────────────────────
PointsFlag = Annotated[
    Optional[str],
    flag(
        "--points",
        help="Point set alias: default | all | traditional | v5 | uranian | main | nodes | axes; or a comma-separated list of point names.",
        panel="Subject (advanced)",
    ),
]
FixedStarsFlag = Annotated[
    Optional[str],
    flag(
        "--fixed-stars",
        help="Fixed-star preset: royal | behenian | default-stars; or a comma-separated list.",
        panel="Subject (advanced)",
    ),
]
WithFlags = Annotated[
    Optional[list[str]],
    flag(
        "--with",
        help="Enable a calculate_* feature (repeatable): lunar_phase, dignities, nakshatra, gauquelin, nutation, local_space.",
        panel="Subject (advanced)",
    ),
]
WithoutFlags = Annotated[
    Optional[list[str]],
    flag(
        "--without",
        help="Disable a calculate_* feature (repeatable); same vocabulary as --with.",
        panel="Subject (advanced)",
    ),
]
SetFlags = Annotated[
    Optional[list[str]],
    flag(
        "--set",
        help="Pass an advanced factory parameter as key=value (repeatable). Whitelisted against from_birth_data's signature; keys with a leading underscore are refused.",
        panel="Subject (advanced)",
    ),
]

# ── Rendering ────────────────────────────────────────────────────────────────
FormatOpt = Annotated[
    Optional[str],
    flag("-f", "--format", help="Output format: text | json | xml | svg. Default: text on a TTY, JSON when piped."),
]
OutputOpt = Annotated[
    Optional[str],
    flag("-o", "--output", help="Write to a file. Format is inferred from the suffix unless -f is also given."),
]

# ── Second subject & technique-specific flags ────────────────────────────────
Subject2Profile = Annotated[
    Optional[str],
    flag(
        "-S",
        "--subject2",
        help="Second subject (synastry, composite): profile name or file path.",
        panel="Second subject",
    ),
]
ReturnTypeOpt = Annotated[
    Optional[str], flag("--type", help="Return type: Solar | Lunar (planetary returns). Default Solar.", panel="Return")
]
YearOpt = Annotated[Optional[int], flag("--year", help="Year for the return.", panel="Return")]
MonthOpt = Annotated[int, flag("--month", help="Month to search from (default 1).", panel="Return")]
DayOpt = Annotated[int, flag("--day", help="Day to search from (default 1).", panel="Return")]
TargetYearOpt = Annotated[
    Optional[int], flag("--target-year", help="Target year for the secondary progression.", panel="Progression")
]
ToDateOpt = Annotated[
    Optional[str],
    flag(
        "--to-date",
        help="Transit date YYYY-MM-DD. Give with --to-time; omit both for the current moment.",
        panel="Transit",
    ),
]
ToTimeOpt = Annotated[
    Optional[str], flag("--to-time", help="Transit time HH:MM[:SS]. Used with --to-date.", panel="Transit")
]

# ── Technique-specific flags ─────────────────────────────────────────────────
TargetDateOpt = Annotated[
    Optional[str],
    flag(
        "--target-date",
        help="ISO date YYYY-MM-DD the technique is evaluated for (profections, firdaria, zodiacal releasing). Defaults to the subject's local now.",
        panel="Technique",
    ),
]
LotOpt = Annotated[
    Optional[str],
    flag("--lot", help="Lot for zodiacal releasing: fortune | spirit (default fortune).", panel="Technique"),
]
LotLevelsOpt = Annotated[
    Optional[int], flag("--levels", help="Number of releasing levels to compute (1–4, default 2).", panel="Technique")
]
LifeCapOpt = Annotated[
    Optional[int],
    flag(
        "--life-cap-years",
        help="Upper age bound for the technique span (firdaria 120, zodiacal releasing 100).",
        panel="Technique",
    ),
]
YearsBeforeOpt = Annotated[
    Optional[int], flag("--years-before", help="Past profected years to show (default 3).", panel="Technique")
]
YearsAfterOpt = Annotated[
    Optional[int], flag("--years-after", help="Future profected years to show (default 4).", panel="Technique")
]
RateKeyOpt = Annotated[
    Optional[str], flag("--rate", help="Primary-direction rate: ptolemy | naibod (default ptolemy).", panel="Technique")
]
MaxYearsOpt = Annotated[
    Optional[float],
    flag(
        "--max-years",
        help="Hard ceiling on direction arcs, in years of life (primary directions, default 100).",
        panel="Technique",
    ),
]
IsMoonVoidOpt = Annotated[
    Optional[bool],
    flag(
        "--moon-void/--no-moon-void",
        help="For the horary considerations: force the Moon's void state rather than compute it.",
        panel="Technique",
    ),
]
MethodOpt = Annotated[
    Optional[str],
    flag("--method", help="Node method: mean | osculating (planetary nodes, default mean).", panel="Technique"),
]
PlanetsOpt = Annotated[
    Optional[list[str]],
    flag(
        "--planets",
        help="Comma list of planet names to restrict to (repeatable or CSV). Default is technique-specific.",
        panel="Technique",
    ),
]
AspectsOpt = Annotated[
    Optional[list[str]],
    flag(
        "--aspects",
        help="Aspects to use, repeatable or CSV: a name (`trine`) or a name with an orb (`trine:6`) where the command supports per-aspect orbs. `kerykeion info literals AspectName` lists the names.",
        panel="Analysis",
    ),
]
MidpointOrbOpt = Annotated[
    Optional[float], flag("--orb", help="Orb for midpoint aspects, in degrees (default 1.0).", panel="Technique")
]
AcgStepOpt = Annotated[
    Optional[float],
    flag("--step", help="Latitude scanning step in degrees for astro-cartography (default 1.0).", panel="Technique"),
]
AcgLatRangeOpt = Annotated[
    Optional[str],
    flag("--lat-range", help="Latitude band 'min,max' for astro-cartography (default -66,66).", panel="Technique"),
]
RelocateCityOpt = Annotated[
    Optional[str],
    flag("--new-city", help="City label for the relocated chart (default 'Relocated').", panel="Technique"),
]
RelocateNationOpt = Annotated[
    Optional[str], flag("--new-nation", help="Nation for the relocated chart.", panel="Technique")
]
RelocateTzOpt = Annotated[
    Optional[str], flag("--new-tz", help="Timezone for the relocated chart (default: original).", panel="Technique")
]
RelocateLatOpt = Annotated[
    Optional[float], flag("--new-lat", help="Latitude of the relocation (required).", panel="Technique")
]
RelocateLngOpt = Annotated[
    Optional[float], flag("--new-lng", help="Longitude of the relocation (required).", panel="Technique")
]

# ── Sky-specific flags ───────────────────────────────────────────────────────
FromOpt = Annotated[
    Optional[str],
    flag(
        "--from",
        help="Range start (ISO date or datetime: YYYY-MM-DD or YYYY-MM-DDThh:mm). For sun-times/hours/eclipses this is a single moment or start year.",
        panel="Range",
    ),
]
ToOpt = Annotated[Optional[str], flag("--to", help="Range end (ISO date or datetime).", panel="Range")]
StartYearOpt = Annotated[
    Optional[int], flag("--start-year", help="First year to search (eclipses). Default: current UTC year.", panel="Sky")
]
CountOpt = Annotated[
    Optional[int],
    flag("--count", help="How many events to return (eclipses default 5/10, heliacal default 5).", panel="Sky"),
]
PhaseOpt = Annotated[
    Optional[list[str]],
    flag(
        "--phase",
        help="Lunation phase to include (repeatable): new | first_quarter | full | last_quarter. Default: all four.",
        panel="Sky",
    ),
]
ZodiacSkyOpt = Annotated[Optional[str], flag("--zodiac", help="Tropical | Sidereal (sky searches).", panel="Sky")]
SiderealSkyOpt = Annotated[
    Optional[str], flag("--sidereal-mode", help="Ayanamsa for sidereal sky searches.", panel="Sky")
]

# ── Series (ephemeris / transits) flags ──────────────────────────────────────
StepTypeOpt = Annotated[
    Optional[str],
    flag("--step-type", help="Sampling granularity: days | hours | minutes (default days).", panel="Series"),
]
SeriesStepOpt = Annotated[
    Optional[int], flag("--step", help="Sample every N units (default 1). Must be positive.", panel="Series")
]
NoLimitFlag = Annotated[
    Optional[bool],
    flag(
        "--no-limit",
        help="Disable the ephemeris sampling ceiling (730 days / 8760 hours / 525600 minutes). The pre-flight check is skipped and max_*=None is passed through. Use carefully.",
        panel="Series",
    ),
]
EventsFlag = Annotated[
    Optional[bool],
    flag(
        "--events",
        help="For `transits`: return discrete events (applying→exact→separating) instead of per-sample aspect lists.",
        panel="Series",
    ),
]
RefineFlag = Annotated[
    Optional[bool],
    flag(
        "--refine",
        help="For `transits --events`: refine exact moments to sub-step precision (geocentric only).",
        panel="Series",
    ),
]

# ── Dispatcher (`kerykeion call`) flags ──────────────────────────────────────
ListFlag = Annotated[
    Optional[bool], flag("--list", help="List the call targets available (Factory.method / function).")
]
JsonListFlag = Annotated[
    Optional[bool], flag("--json", help="With --list: emit a JSON array. With --explain: a JSON array of parameters.")
]
ExplainFlag = Annotated[
    Optional[bool],
    flag(
        "--explain", help="Describe every parameter of the target (cli | subject | json-only | unsupported) and exit."
    ),
]
ParamOpt = Annotated[
    Optional[list[str]],
    flag(
        "--param",
        help="A method parameter as key=value (repeatable). Value is coerced to the parameter's type; use --param key='{...}' JSON for structural types.",
        panel="Call",
    ),
]
CallSubject2Opt = Annotated[
    Optional[str],
    flag(
        "-S",
        "--subject2",
        help="Second subject (profile): bound to the target's second subject parameter.",
        panel="Call",
    ),
]

# ── Analysis commands (aspects, dominants, moon, relationship-score) ─────────
DeclinationsFlag = Annotated[
    Optional[bool],
    flag(
        "--declinations",
        help="Use the declination aspects (parallel / contra-parallel) instead of the ecliptic ones.",
        panel="Analysis",
    ),
]
DeclinationOrbOpt = Annotated[
    Optional[float], flag("--orb", help="Orb for declination aspects (used with --declinations).", panel="Analysis")
]
AxisOrbLimitOpt = Annotated[
    Optional[float],
    flag("--axis-orb-limit", help="Cap the orb used for the axes (Asc/MC and their opposites).", panel="Analysis"),
]
DominantMethodOpt = Annotated[
    Optional[str],
    flag("--method", help="Dominants strategy. `kerykeion info methods` lists what is available.", panel="Analysis"),
]
DistributionMethodOpt = Annotated[
    Optional[str],
    flag("--distribution-method", help="How element/quality distributions are weighted.", panel="Analysis"),
]
CustomWeightsOpt = Annotated[
    Optional[str],
    flag("--custom-weights", help="JSON object of per-point weights, e.g. '{\"Sun\": 1.5}'.", panel="Analysis"),
]
AccidentalDignitiesFlag = Annotated[
    Optional[bool],
    flag("--accidental-dignities", help="Include accidental dignities in the dominants scoring.", panel="Analysis"),
]
ScoreBreakdownFlag = Annotated[
    Optional[bool], flag("--score-breakdown", help="Include the per-point score breakdown.", panel="Analysis")
]
MajorAspectsOnlyFlag = Annotated[
    Optional[bool],
    flag(
        "--all-aspects/--major-aspects-only",
        help="Score every aspect, or only the major ones (default: major only).",
        panel="Analysis",
    ),
]
UsingDefaultLocationFlag = Annotated[
    Optional[bool],
    flag(
        "--using-default-location",
        help="Use the library's default location rather than the subject's.",
        panel="Analysis",
    ),
]
LocationPrecisionOpt = Annotated[
    Optional[int],
    flag("--location-precision", help="Rounding applied to the location before the lookup.", panel="Analysis"),
]
StarOrbOpt = Annotated[
    Optional[float], flag("--orb", help="Orb, in degrees, for a star to count as prominent.", panel="Technique")
]
TargetIsoOpt = Annotated[
    Optional[str],
    flag(
        "--target-iso", help="Target moment as an ISO UTC datetime (alternative to --target-year).", panel="Technique"
    ),
]
# Deliberately not "--aspects": that flag names *which* aspects, and one
# flag with two meanings is what these reviews keep having to undo.
ComputeAspectsFlag = Annotated[
    Optional[bool],
    flag(
        "--compute-aspects/--no-compute-aspects", help="Compute the directed aspects (default: on).", panel="Technique"
    ),
]
AspectOrbOpt = Annotated[Optional[float], flag("--aspect-orb", help="Orb for the directed aspects.", panel="Technique")]
PlanetIdOpt = Annotated[
    Optional[str],
    flag(
        "--planet",
        help="The body occulted by the Moon, by name or Swiss Ephemeris id (required; calculated points such as the nodes cannot be occulted).",
        panel="Sky",
    ),
]
SnapshotFlag = Annotated[
    Optional[bool],
    flag(
        "--snapshot",
        help="Also store the computed subject in the profile, so later reads reuse it instead of recomputing. Ignored automatically if the kerykeion version or ephemeris backend changes.",
        panel="Subject",
    ),
]

# ── Report shaping (--format text) ───────────────────────────────────────────
NoAspectsFlag = Annotated[
    Optional[bool], flag("--no-aspects", help="Omit the aspects section from the text report.", panel="Report")
]
MaxAspectsOpt = Annotated[
    Optional[int],
    flag("--max-aspects", help="Keep at most N aspects in the text report (the tightest ones first).", panel="Report"),
]
EnvelopeFlag = Annotated[
    Optional[bool],
    flag(
        "--envelope",
        help="Wrap the payload with provenance and the warnings, in-band (JSON only) — for a pipeline that cannot read stderr.",
        panel="Report",
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
    flag(
        "--theme",
        help="Chart theme: light, dark, dark-high-contrast, classic, strawberry, black-and-white.",
        panel="Chart (SVG)",
    ),
]
ChartLanguageOpt = Annotated[
    Optional[str],
    flag(
        "--chart-language",
        help="Language of the chart labels: EN, FR, PT, IT, CN, ES, RU, TR, DE, HI.",
        panel="Chart (SVG)",
    ),
]
ChartStyleOpt = Annotated[Optional[str], flag("--style", help="Chart style: classic or modern.", panel="Chart (SVG)")]
CustomTitleOpt = Annotated[
    Optional[str], flag("--custom-title", help="Replace the chart's title line.", panel="Chart (SVG)")
]
PaddingOpt = Annotated[Optional[int], flag("--padding", help="Outer padding in SVG units.", panel="Chart (SVG)")]
ExternalViewFlag = Annotated[
    Optional[bool],
    flag(
        "--external-view",
        help="Draw the external (outer-ring) layout. Classic style only — with the default --style modern the library ignores it and says so on stderr.",
        panel="Chart (SVG)",
    ),
]
TransparentBackgroundFlag = Annotated[
    Optional[bool],
    flag("--transparent-background", help="Omit the background rectangle (for compositing).", panel="Chart (SVG)"),
]
CuspComparisonFlag = Annotated[
    Optional[bool],
    flag("--cusp-position-comparison", help="Show the cusp-position comparison (dual wheels).", panel="Chart (SVG)"),
]
AutoSizeFlag = Annotated[
    Optional[bool],
    flag("--auto-size/--no-auto-size", help="Size the viewBox to the content (default: on).", panel="Chart (SVG)"),
]
DegreeIndicatorsFlag = Annotated[
    Optional[bool],
    flag(
        "--degree-indicators/--no-degree-indicators",
        help="Draw the degree ticks (default: on). Classic style only — with the default --style modern the library ignores it and says so on stderr.",
        panel="Chart (SVG)",
    ),
]
AspectIconsFlag = Annotated[
    Optional[bool],
    flag(
        "--aspect-icons/--no-aspect-icons",
        help="Draw aspect glyphs in the grid (default: on). Classic style only — with the default --style modern the library ignores it and says so on stderr.",
        panel="Chart (SVG)",
    ),
]
ZodiacRingFlag = Annotated[
    Optional[bool],
    flag("--zodiac-ring/--no-zodiac-ring", help="Draw the zodiac background ring (default: on).", panel="Chart (SVG)"),
]
DiurnalityFlag = Annotated[
    Optional[bool], flag("--diurnality/--no-diurnality", help="Mark day/night sect (default: on).", panel="Chart (SVG)")
]
HousePositionComparisonFlag = Annotated[
    Optional[bool],
    flag(
        "--house-position-comparison/--no-house-position-comparison",
        help="Show the house-position comparison (default: on). Dual wheels only (synastry, transit, return, progression).",
        panel="Chart (SVG)",
    ),
]
AspectGridTypeOpt = Annotated[
    Optional[str], flag("--aspect-grid-type", help="Dual-chart aspect grid: list or table.", panel="Chart (SVG)")
]
SvgVariantOpt = Annotated[
    Optional[str],
    flag(
        "--svg-variant",
        help="Which SVG to render: full (default), wheel (wheel only), aspect-grid (grid only).",
        panel="Chart (SVG)",
    ),
]
ChartSettingsOpt = Annotated[
    Optional[str],
    flag(
        "--chart-settings",
        help="JSON file with any of: colors_settings, celestial_points_settings, aspects_settings, language_pack. Structural settings that are too big for a flag.",
        panel="Chart (SVG)",
    ),
]
