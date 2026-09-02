# -*- coding: utf-8 -*-
"""The ``Annotated[T, Opt(...)]`` aliases every command composes its signature from.

One spelling per flag, shared by every command that takes it. Almost every alias
is ``Optional`` with a ``None`` default: ``None`` means "not given", so the
resolver can tell it apart from "given as this value". The aliases stay written
out as ``Annotated[...]``: a factory returning the whole alias would be shorter,
but pyright then sees a variable, not a type alias, and rejects every use.
"""

from __future__ import annotations

from typing import Annotated, Callable, Optional

from kerykeion_cli.parser import Opt

Str = Optional[str]
Int = Optional[int]
Float = Optional[float]
Bool = Optional[bool]
Strs = Optional[list[str]]


def _panel(group: Optional[str]) -> Callable[..., Opt]:
    """An ``Opt`` factory bound to one help section: ``subject("--name", help=...)``."""
    return lambda *names, help: Opt(names, help, group)


subject, advanced, render = _panel("Subject"), _panel("Subject (advanced)"), _panel(None)
second, technique, analysis, sky, series = (
    _panel("Second subject"),
    _panel("Technique"),
    _panel("Analysis"),
    _panel("Sky"),
    _panel("Series"),
)
chart, report, call = _panel("Chart (SVG)"), _panel("Report"), _panel("Call")

# ── Subject identity, birth data, place ──────────────────────────────────────
SubjectProfile = Annotated[Str, subject("-s", "--subject", help="Profile name (e.g. -s ada) or file path.")]
SubjectName = Annotated[Str, subject("--name", help="Subject display name.")]
SubjectDate = Annotated[Str, subject("--date", help="Calendar date YYYY-MM-DD (negative year = BCE).")]
SubjectTime = Annotated[Str, subject("--time", help="Clock time HH:MM or HH:MM:SS.")]
SubjectSeconds = Annotated[Int, subject("--seconds", help="Seconds component of the birth time.")]
SubjectIsoUtc = Annotated[Str, subject("--iso-utc", help="ISO-8601 UTC timestamp instead of --date/--time.")]
SubjectLat = Annotated[Float, subject("--lat", help="Birth latitude in decimal degrees.")]
SubjectLng = Annotated[Float, subject("--lng", help="Birth longitude in decimal degrees.")]
SubjectTz = Annotated[Str, subject("--tz", "--tz-str", help="IANA timezone, e.g. Europe/Rome.")]
SubjectCity = Annotated[Str, subject("--city", help="City name (display, and GeoNames when online).")]
SubjectNation = Annotated[Str, subject("--nation", help="ISO country code or name.")]
SubjectAltitude = Annotated[Float, subject("--altitude", help="Birth altitude in metres.")]
OnlineFlag = Annotated[
    Bool,
    subject(
        "--online/--no-online",
        help="Resolve city/timezone through GeoNames. Default: off when lat+lng+tz are all known. "
        "--no-online overrides a profile saved online.",
    ),
]
OfflineFlag = Annotated[Bool, subject("--offline", help="Never call GeoNames (the safer default for pipelines).")]

# ── Zodiac, houses, points, calculation toggles ──────────────────────────────
ZodiacTypeOpt = Annotated[Str, advanced("--zodiac", help="Tropical | Sidereal.")]
SiderealModeOpt = Annotated[
    Str, advanced("--sidereal-mode", help="Ayanamsa for sidereal charts (FAGAN_BRADLEY, LAHIRI…).")
]
HousesSystemOpt = Annotated[
    Str,
    advanced("--houses", help="House system: a letter (P, K, W, C, R, A, M…) or a name (placidus, koch, whole-sign…)."),
]
PerspectiveOpt = Annotated[
    Str, advanced("--perspective", help="Apparent Geocentric | True Geocentric | Heliocentric | Topocentric.")
]
PointsFlag = Annotated[
    Str,
    advanced(
        "--points",
        help="Point set: default | all | traditional | v5 | uranian | main | nodes | axes, or a comma list of names.",
    ),
]
FixedStarsFlag = Annotated[
    Str, advanced("--fixed-stars", help="Fixed-star preset: royal | behenian | default-stars, or a comma list.")
]
WithFlags = Annotated[
    Strs,
    advanced(
        "--with",
        help="Enable a calculate_* feature (repeatable): lunar_phase, dignities, nakshatra, gauquelin, nutation, local_space.",
    ),
]
WithoutFlags = Annotated[
    Strs, advanced("--without", help="Disable a calculate_* feature (repeatable); same names as --with.")
]
SetFlags = Annotated[
    Strs,
    advanced(
        "--set",
        help="Advanced profile field as key=value (repeatable); checked against the profile recipe, no private keys.",
    ),
]

# ── Output ───────────────────────────────────────────────────────────────────
FormatOpt = Annotated[
    Str,
    render("-f", "--format", help="Output format: text | json | xml | svg. Default: text on a TTY, JSON when piped."),
]
OutputOpt = Annotated[
    Str, render("-o", "--output", help="Write to a file. Format is inferred from the suffix unless -f is also given.")
]

# ── Second subject, return, progression, transit ─────────────────────────────
Subject2Profile = Annotated[
    Str, second("-S", "--subject2", help="Second subject (synastry, composite): profile name or file path.")
]
ReturnTypeOpt = Annotated[Str, _panel("Return")("--type", help="Return type: Solar | Lunar. Default Solar.")]
YearOpt = Annotated[Int, _panel("Return")("--year", help="Year for the return.")]
MonthOpt = Annotated[int, _panel("Return")("--month", help="Month to search from (default 1).")]
DayOpt = Annotated[int, _panel("Return")("--day", help="Day to search from (default 1).")]
TargetYearOpt = Annotated[
    Int, _panel("Progression")("--target-year", help="Target year for the secondary progression.")
]
ToDateOpt = Annotated[
    Str, _panel("Transit")("--to-date", help="Transit date YYYY-MM-DD. Give with --to-time; omit both for now.")
]
ToTimeOpt = Annotated[Str, _panel("Transit")("--to-time", help="Transit time HH:MM[:SS]. Used with --to-date.")]

# ── Techniques ───────────────────────────────────────────────────────────────
TargetDateOpt = Annotated[
    Str,
    technique(
        "--target-date",
        help="ISO date YYYY-MM-DD the technique is evaluated for (profections, firdaria, zodiacal releasing). "
        "Defaults to the subject's local now.",
    ),
]
LotOpt = Annotated[Str, technique("--lot", help="Lot for zodiacal releasing: fortune | spirit (default fortune).")]
LotLevelsOpt = Annotated[Int, technique("--levels", help="Releasing levels to compute (1–4, default 2).")]
LifeCapOpt = Annotated[
    Int, technique("--life-cap-years", help="Upper age bound for the technique (firdaria 120, zodiacal releasing 100).")
]
YearsBeforeOpt = Annotated[Int, technique("--years-before", help="Past profected years to show (default 3).")]
YearsAfterOpt = Annotated[Int, technique("--years-after", help="Future profected years to show (default 4).")]
RateKeyOpt = Annotated[Str, technique("--rate", help="Primary-direction rate: ptolemy | naibod (default ptolemy).")]
MaxYearsOpt = Annotated[
    Float,
    technique(
        "--max-years", help="Hard ceiling on direction arcs, in years of life (primary directions, default 100)."
    ),
]
IsMoonVoidOpt = Annotated[
    Bool, technique("--moon-void/--no-moon-void", help="Horary: force the Moon's void state rather than compute it.")
]
MethodOpt = Annotated[Str, technique("--method", help="Node method: mean | osculating (default mean).")]
PlanetsOpt = Annotated[
    Strs, technique("--planets", help="Planet names to restrict to (repeatable or CSV). Default is technique-specific.")
]
MidpointOrbOpt = Annotated[Float, technique("--orb", help="Orb for midpoint aspects, in degrees (default 1.0).")]
StarOrbOpt = Annotated[Float, technique("--orb", help="Orb, in degrees, for a star to count as prominent.")]
AcgStepOpt = Annotated[
    Float, technique("--step", help="Latitude scanning step in degrees for astro-cartography (default 1.0).")
]
AcgLatRangeOpt = Annotated[
    Str, technique("--lat-range", help="Latitude band 'min,max' for astro-cartography (default -66,66).")
]
RelocateCityOpt = Annotated[
    Str, technique("--new-city", help="City label for the relocated chart (default 'Relocated').")
]
RelocateNationOpt = Annotated[Str, technique("--new-nation", help="Nation for the relocated chart.")]
RelocateTzOpt = Annotated[Str, technique("--new-tz", help="Timezone for the relocated chart (default: original).")]
RelocateLatOpt = Annotated[Float, technique("--new-lat", help="Latitude of the relocation (required).")]
RelocateLngOpt = Annotated[Float, technique("--new-lng", help="Longitude of the relocation (required).")]
TargetIsoOpt = Annotated[
    Str, technique("--target-iso", help="Target moment as an ISO UTC datetime (alternative to --target-year).")
]
# Not "--aspects": that flag names *which* aspects; one flag with two meanings is a bug magnet.
ComputeAspectsFlag = Annotated[
    Bool, technique("--compute-aspects/--no-compute-aspects", help="Compute the directed aspects (default: on).")
]
AspectOrbOpt = Annotated[Float, technique("--aspect-orb", help="Orb for the directed aspects.")]

# ── Analyses ─────────────────────────────────────────────────────────────────
AspectsOpt = Annotated[
    Strs,
    analysis(
        "--aspects",
        help="Aspects to use, repeatable or CSV: a name (`trine`) or name:orb (`trine:6`) where the command "
        "supports per-aspect orbs. `kerykeion info literals AspectName` lists the names.",
    ),
]
DeclinationsFlag = Annotated[
    Bool,
    analysis(
        "--declinations", help="Use the declination aspects (parallel / contra-parallel) instead of the ecliptic ones."
    ),
]
DeclinationOrbOpt = Annotated[Float, analysis("--orb", help="Orb for declination aspects (used with --declinations).")]
AxisOrbLimitOpt = Annotated[
    Float, analysis("--axis-orb-limit", help="Cap the orb used for the axes (Asc/MC and their opposites).")
]
DominantMethodOpt = Annotated[
    Str, analysis("--method", help="Dominants strategy. `kerykeion info methods` lists what is available.")
]
DistributionMethodOpt = Annotated[
    Str, analysis("--distribution-method", help="How element/quality distributions are weighted.")
]
CustomWeightsOpt = Annotated[
    Str, analysis("--custom-weights", help="JSON object of per-point weights, e.g. '{\"Sun\": 1.5}'.")
]
AccidentalDignitiesFlag = Annotated[
    Bool, analysis("--accidental-dignities", help="Include accidental dignities in the dominants scoring.")
]
ScoreBreakdownFlag = Annotated[Bool, analysis("--score-breakdown", help="Include the per-point score breakdown.")]
AllAspectsFlag = Annotated[Bool, analysis("--all-aspects", help="Score every aspect, not only the major ones.")]
UsingDefaultLocationFlag = Annotated[
    Bool, analysis("--using-default-location", help="Use the library's default location rather than the subject's.")
]
LocationPrecisionOpt = Annotated[
    Int, analysis("--location-precision", help="Rounding applied to the location before the lookup.")
]

# ── Sky ──────────────────────────────────────────────────────────────────────
FromOpt = Annotated[
    Str,
    _panel("Range")(
        "--from",
        help="Range start (YYYY-MM-DD or YYYY-MM-DDThh:mm). For sun-times/hours/eclipses: a single moment or start year.",
    ),
]
ToOpt = Annotated[Str, _panel("Range")("--to", help="Range end (ISO date or datetime).")]
StartYearOpt = Annotated[Int, sky("--start-year", help="First year to search (eclipses). Default: current UTC year.")]
CountOpt = Annotated[Int, sky("--count", help="How many events to return (eclipses default 5/10, heliacal default 5).")]
PhaseOpt = Annotated[
    Strs,
    sky(
        "--phase",
        help="Lunation phase to include (repeatable): new | first_quarter | full | last_quarter. Default: all.",
    ),
]
PeriodsFlag = Annotated[
    Bool,
    sky(
        "--periods",
        help="Report the spans instead of the events: sign stays (ingresses) or retrograde spans (stations), "
        "clipped to the range.",
    ),
]
ZodiacSkyOpt = Annotated[Str, sky("--zodiac", help="Tropical | Sidereal (sky searches).")]
SiderealSkyOpt = Annotated[Str, sky("--sidereal-mode", help="Ayanamsa for sidereal sky searches.")]
PlanetIdOpt = Annotated[
    Str,
    sky(
        "--planet",
        help="The body occulted by the Moon, by name or Swiss Ephemeris id (required; calculated points cannot be occulted).",
    ),
]

# ── Time series ──────────────────────────────────────────────────────────────
StepTypeOpt = Annotated[Str, series("--step-type", help="Sampling granularity: days | hours | minutes (default days).")]
SeriesStepOpt = Annotated[Int, series("--step", help="Sample every N units (default 1). Must be positive.")]
NoLimitFlag = Annotated[
    Bool,
    series(
        "--no-limit",
        help="Lift the sampling ceiling (730 days / 8760 hours / 525600 minutes). Use carefully.",
    ),
]
EventsFlag = Annotated[
    Bool,
    series(
        "--events", help="For `transits`: discrete events (applying→exact→separating) instead of per-sample aspects."
    ),
]
RefineFlag = Annotated[
    Bool,
    series("--refine", help="For `transits --events`: refine exact moments to sub-step precision (geocentric only)."),
]

# ── `kerykeion call` ─────────────────────────────────────────────────────────
ListFlag = Annotated[Bool, render("--list", help="List the call targets available (Factory.method / function).")]
JsonListFlag = Annotated[
    Bool, render("--json", help="With --list: a JSON array. With --explain: a JSON array of parameters.")
]
ExplainFlag = Annotated[
    Bool,
    render(
        "--explain", help="Describe every parameter of the target (cli | subject | json-only | unsupported) and exit."
    ),
]
ParamOpt = Annotated[
    Strs,
    call(
        "--param",
        help="A method parameter as key=value (repeatable), coerced to the parameter's type; JSON for structural types.",
    ),
]
CallSubject2Opt = Annotated[
    Str, call("-S", "--subject2", help="Second subject (profile): bound to the target's second subject parameter.")
]

# ── Report (text) and payload shape ──────────────────────────────────────────
NoAspectsFlag = Annotated[Bool, report("--no-aspects", help="Omit the aspects section from the text report.")]
MaxAspectsOpt = Annotated[
    Int, report("--max-aspects", help="Keep at most N aspects in the text report (the tightest first).")
]
EnvelopeFlag = Annotated[
    Bool, report("--envelope", help="Wrap the payload with provenance and the warnings, in-band (JSON only).")
]

# ── Chart appearance (svg) ───────────────────────────────────────────────────
# A knob the library defaults to True is declared in the paired --x/--no-x form,
# otherwise "not given" could never mean False and the negative would be unreachable.
ThemeOpt = Annotated[
    Str,
    chart(
        "--theme", help="Chart theme: classic, dark, black-and-white (`kerykeion info methods` lists the current set)."
    ),
]
ChartLanguageOpt = Annotated[
    Str, chart("--chart-language", help="Language of the chart labels: EN, FR, PT, IT, CN, ES, RU, TR, DE, HI.")
]
ChartStyleOpt = Annotated[Str, chart("--style", help="Chart style: classic or modern.")]
CustomTitleOpt = Annotated[Str, chart("--custom-title", help="Replace the chart's title line.")]
PaddingOpt = Annotated[Int, chart("--padding", help="Outer padding in SVG units.")]
ExternalViewFlag = Annotated[
    Bool,
    chart(
        "--external-view",
        help="Draw the external (outer-ring) layout. Classic style only; modern ignores it and says so.",
    ),
]
TransparentBackgroundFlag = Annotated[
    Bool, chart("--transparent-background", help="Omit the background rectangle (for compositing).")
]
CuspComparisonFlag = Annotated[
    Bool, chart("--cusp-position-comparison", help="Show the cusp-position comparison (dual wheels).")
]
AutoSizeFlag = Annotated[
    Bool, chart("--auto-size/--no-auto-size", help="Size the viewBox to the content (default: on).")
]
DegreeIndicatorsFlag = Annotated[
    Bool,
    chart(
        "--degree-indicators/--no-degree-indicators",
        help="Draw the degree ticks (default: on). Classic style only; modern ignores it and says so.",
    ),
]
AspectIconsFlag = Annotated[
    Bool,
    chart(
        "--aspect-icons/--no-aspect-icons",
        help="Draw aspect glyphs in the grid (default: on). Classic style only; modern ignores it and says so.",
    ),
]
ZodiacRingFlag = Annotated[
    Bool, chart("--zodiac-ring/--no-zodiac-ring", help="Draw the zodiac background ring (default: on).")
]
DiurnalityFlag = Annotated[Bool, chart("--diurnality/--no-diurnality", help="Mark day/night sect (default: on).")]
HousePositionComparisonFlag = Annotated[
    Bool,
    chart(
        "--house-position-comparison/--no-house-position-comparison",
        help="Show the house-position comparison (default: on). Dual wheels only.",
    ),
]
AspectGridTypeOpt = Annotated[Str, chart("--aspect-grid-type", help="Dual-chart aspect grid: list or table.")]
SvgVariantOpt = Annotated[
    Str,
    chart("--svg-variant", help="Which SVG to render: full (default), wheel (wheel only), aspect-grid (grid only)."),
]
ChartSettingsOpt = Annotated[
    Str,
    chart(
        "--chart-settings",
        help="JSON file with any of: colors_settings, celestial_points_settings, aspects_settings, language_pack.",
    ),
]
