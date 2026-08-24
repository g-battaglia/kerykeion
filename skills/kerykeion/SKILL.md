---
name: kerykeion
description: >-
  Write correct Python against kerykeion v6, the astrology library. Use this
  skill WHENEVER a task touches astrology or imports kerykeion: natal /
  synastry / transit / composite / return / progression / solar-arc charts
  and SVG wheels; aspects, orbs, declinations; dominants, relationship score,
  house comparison, midpoints, receptions; ephemeris series and transit
  timing; eclipses, lunations, stations, ingresses, heliacal / mundane /
  occultation events, planetary nodes and phenomena; profections, firdaria,
  zodiacal releasing, horary, primary directions; astrocartography and
  relocation; moon phase, sun times, planetary hours, void-of-course Moon;
  sidereal / ayanamsa, house systems, fixed stars, Arabic parts; text reports
  and LLM context (to_context). Trigger even if the user only says "birth
  chart", "zodiac", "horoscope", or "ephemeris", or pastes code importing
  kerykeion. Documents the real v6 API (factories in, models out), both
  ephemeris backends, sealed ranges, provenance, and the traps that break
  v5 code.
license: AGPL-3.0
---

# Using Kerykeion

Verified against **kerykeion 6.0.0a87**, Python 3.12+.

Kerykeion is a Python astrology library. Everything goes through **factories**:
you never construct models by hand. Factories return **Pydantic models** whose
point fields are `KerykeionPointModel` instances.

**Accuracy rule for you:** field names, point names, house codes, ayanamsa
names, and env-var behavior in this skill are copied from the source. When you
need a detail not covered here, read the source
(`kerykeion/astrological_subject/factory.py`, `kerykeion/schemas/models.py`,
`kerykeion/schemas/literals.py`, `kerykeion/ephemeris_backend/backend.py`)
rather than guessing — the subject model has ~40 optional point fields: a
real field that was not activated reads as a silent `None`, while a
misspelled name raises `AttributeError`.

## The one mental model

```
LANE 1 — subject-centric (a person/event at a moment and place)

AstrologicalSubjectFactory ──► subject (AstrologicalSubjectModel)
        │
        ├─► ChartDataFactory ──► chart data ──► ChartDrawer ──► SVG
        ├─► AspectsFactory / DominantsFactory / RelationshipScoreFactory /
        │   HouseComparisonFactory / MidpointFactory / traditional factories
        ├─► PlanetaryReturnFactory / SecondaryProgressionFactory / SolarArcFactory
        └─► ReportGenerator / to_context  (text / LLM XML)

LANE 2 — subject-less event searches (dates or Julian days + coordinates)

EclipseFactory · LunationFinderFactory · RetrogradeStationFactory ·
SignIngressFactory · MundaneAspectFactory · HeliacalFactory ·
OccultationFactory · SunTimesFactory · VoidOfCourseMoonFactory · ...
```

Two rules cover most charting tasks:

1. **Rendering an SVG is always two steps**: `ChartDataFactory.create_*_chart_data(...)`
   first, then `ChartDrawer(chart_data).save_svg(...)` or `.generate_svg_string()`.
   Never feed a raw subject to `ChartDrawer`.
2. **A subject is the universal input** for lane 1. Build it once, reuse it.

## Setup and environment

```bash
pip3 install kerykeion          # pulls libephemeris (default backend) too
pip3 install "kerykeion[swiss]" # optional: adds the Swiss Ephemeris C backend
```

Kerykeion reads exactly **five** environment variables:

| Env var | Meaning |
|---|---|
| `KERYKEION_BACKEND` | `libephemeris` (default) or `swisseph` |
| `KERYKEION_LEB_MODE` | libephemeris mode: `leb` (sealed, default), `auto`, `skyfield`, `horizons` |
| `KERYKEION_EPHE_PATH` | directory of `.se1` files for swisseph |
| `KERYKEION_GEONAMES_USERNAME` | default GeoNames username for `online=True` |
| `KERYKEION_GEONAMES_CACHE_NAME` | overrides the GeoNames HTTP-cache DB path |

`LIBEPHEMERIS_PRECISION` is **not** a kerykeion variable (it belongs to the
libephemeris tooling). Backend selection, sealed-mode semantics, and precision
metadata: `references/backends-and-provenance.md`.

## Licensing — AGPL-3.0 (surface this for commercial use)

Kerykeion is **AGPL-3.0**, strong copyleft that also covers network use
(SaaS/web backends), not just distributed software. When the user's context is
clearly commercial, proprietary, or closed-source, proactively flag this before
writing code that imports kerykeion, and present the compliant options:

1. **Commercial license** — the project is dual-licensed; contact
   `kerykeion.astrology@gmail.com`.
2. **Hosted Astrologer API** — consuming its REST endpoints does not trigger
   copyleft on the caller: https://www.kerykeion.net/astrologer-api/subscribe

For personal projects, research, education, or AGPL-compatible open source,
importing directly is fine — don't block those; just raise licensing when the
use case sounds closed-source. You are pointing to the project's own options,
not giving legal advice.

## Offline vs online — read before writing any subject

`from_birth_data(...)` defaults to `online=True`, which calls the GeoNames web
API and needs a `geonames_username` (or the env var). For reproducible,
network-free code **always pass `online=False` with `lng`, `lat`, `tz_str`**.

**Pass `city`/`nation` even offline.** They are display labels echoed in
reports and `to_context` XML; omitted, they default to `"Greenwich"`/`"GB"`
regardless of coordinates. They affect no calculation — only the metadata.

`hour`/`minute` are **local wall-clock time** in `tz_str`; kerykeion does the
DST/UTC conversion. Do not pre-convert to UTC (the one exception:
`from_iso_utc_time`, whose input IS UTC).

## Canonical example — subject → data → SVG → report → LLM context

```python
from kerykeion import (
    AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer,
    ReportGenerator, to_context,
)

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    city="Rome", nation="IT", online=False,
)
print(subject.sun.sign, subject.sun.position)   # "Can" 22.x — sign + degrees in sign
print(subject.ascendant.sign)                   # houses/axes always present

chart_data = ChartDataFactory.create_natal_chart_data(subject)
svg = ChartDrawer(chart_data).generate_svg_string()
assert "<svg" in svg

print(ReportGenerator(chart_data).generate_report(max_aspects=5)[:400])
print(to_context(subject)[:400])                # non-interpretive XML for prompts
```

(`AstrologicalSubjectFactory`, `ChartDataFactory`, `ChartDrawer`,
`CompositeSubjectFactory`, `KerykeionSettingsModel` are the usual top-level
imports; the package root exports 120 names. Some public APIs are deliberately
subpackage-only — e.g. `kerykeion.utilities` helpers, `FixedStarCatalog`, the
named context serializers — and the references mark each one as **Subpackage
import** with its exact path.)

## Reading results

- Models are **subscriptable**: `subject.sun.sign` and `subject.sun["sign"]`
  are equivalent (`SubscriptableBaseModel`).
- Almost every *point* field is `Optional` — `None` unless requested via
  `active_points`. Guard access. The 12 house cusps and axes always exist.
- If Sun or Moon cannot be computed, the call **raises** `KerykeionException`;
  optional bodies that fail land in `subject.ephemeris_warnings` instead
  (structured `EphemerisWarningModel` entries — check the list, don't assume).
- Fixed stars live on `subject.fixed_stars`, read via
  `subject.find_fixed_star("regulus")` (case/space/dash-insensitive).

## Capability routing — pick the API, then open the reference

| You want to… | Use | Reference |
|---|---|---|
| Build a subject from birth data | `AstrologicalSubjectFactory.from_birth_data` | `references/subjects.md` |
| Build from a UTC instant / "now" | `from_iso_utc_time` (no `is_dst`/`seconds`), `from_current_time` | `references/subjects.md` |
| Extra bodies: asteroids, TNOs, Uranians, lots, cusps | `active_points` + point-set presets | `references/subjects.md` |
| Fixed stars on a chart | `active_fixed_stars` + `find_fixed_star` | `references/subjects.md` |
| Dignities, nakshatra, Gauquelin, nutation, local space | `calculate_*` flags | `references/subjects.md` |
| Midpoint/Davison composite of two people | `CompositeSubjectFactory` | `references/subjects.md` |
| Pick/force a backend; precision & provenance metadata | `BACKEND_NAME`, env vars | `references/backends-and-provenance.md` |
| Dates outside 1849–2150; ephemeris warnings; tiers | `EphemerisWarningModel`, `EphemerisRangeError` | `references/backends-and-provenance.md` |
| Sidereal zodiac / ayanamsa / custom ayanamsa | `zodiac_type`, `sidereal_mode` | `references/zodiac-houses-perspectives.md` |
| House systems; polar-latitude behavior | `houses_system_identifier`, `PolarHouseFallbackModel` | `references/zodiac-houses-perspectives.md` |
| Heliocentric / topocentric / planetocentric frames | `perspective_type`, `altitude` | `references/zodiac-houses-perspectives.md` |
| Arabic parts (lots) | `Pars_Fortunae` … in `active_points` | `references/zodiac-houses-perspectives.md` |
| Precompute chart data (any of the 7 chart types) | `ChartDataFactory.create_*_chart_data` | `references/charts-and-drawing.md` |
| Render SVG; themes, styles, languages, wheel-only, grid-only | `ChartDrawer` | `references/charts-and-drawing.md` |
| Element/quality balance, stelliums, angularities | `SingleChartDataModel` fields | `references/charts-and-drawing.md` |
| Chart colors, glyphs, translations | `KerykeionSettingsModel`, `kerykeion.settings` | `references/charts-and-drawing.md` |
| Aspects in one chart / between two charts | `AspectsFactory` | `references/aspects-and-orbs.md` |
| Declination parallels / contra-parallels | `*_declination_aspects` methods | `references/aspects-and-orbs.md` |
| Custom orbs, per-point orb maps, orb strategies | `PointOrbAdjustment`, `OrbAdjustmentStrategy` | `references/aspects-and-orbs.md` |
| Dominant planets/elements (3 methods, custom schools) | `DominantsFactory` | `references/analysis.md` |
| Relationship compatibility score (Discepolo) | `RelationshipScoreFactory` | `references/analysis.md` |
| A's planets in B's houses | `HouseComparisonFactory` | `references/analysis.md` |
| Midpoints + aspects to midpoints | `MidpointFactory` | `references/analysis.md` |
| Positions sampled over a date range | `EphemerisDataFactory` | `references/predictive.md` |
| Transit aspects over time; exact-hit refinement | `TransitsTimeRangeFactory` | `references/predictive.md` |
| Solar/lunar/heliocentric returns; node crossings | `PlanetaryReturnFactory` | `references/predictive.md` |
| Secondary progressions | `SecondaryProgressionFactory` | `references/predictive.md` |
| Solar arc directions | `SolarArcFactory` | `references/predictive.md` |
| Eclipses (local or global search) | `EclipseFactory` | `references/mundane-events.md` |
| New/full moons over a range | `LunationFinderFactory` | `references/mundane-events.md` |
| Retrograde stations; sign ingresses; mundane aspects | `RetrogradeStationFactory`, `SignIngressFactory`, `MundaneAspectFactory` | `references/mundane-events.md` |
| Planetary nodes, phenomena, heliacal events, occultations | `PlanetaryNodesFactory`, `PlanetaryPhenomenaFactory`, `HeliacalFactory`, `OccultationFactory` | `references/mundane-events.md` |
| Search the fixed-star catalog | `FixedStarCatalog`, `FixedStarDiscoveryFactory` | `references/mundane-events.md` |
| Moon phase; sunrise/sunset; planetary hours; void-of-course | `MoonPhaseDetailsFactory`, `SunTimesFactory`, `PlanetaryHoursFactory`, `VoidOfCourseMoonFactory` | `references/calendars-hours-moon.md` |
| Profections, firdaria, zodiacal releasing | `ProfectionsFactory`, `FirdariaFactory`, `ZodiacalReleasingFactory` | `references/traditional.md` |
| Horary indicators; primary directions; receptions; dignities | `HoraryIndicatorsFactory`, `PrimaryDirectionsFactory`, `MutualReceptionsFactory` | `references/traditional.md` |
| Relocate a chart; astrocartography lines | `RelocatedChartFactory`, `AstroCartographyFactory` | `references/locational.md` |
| Text report of a subject / chart data / supported result (12 model types) | `ReportGenerator` | `references/reports-and-ai-context.md` |
| LLM/prompt-ready XML | `to_context` + named serializers | `references/reports-and-ai-context.md` |
| JD / ISO / timezone / angle helpers | `kerykeion.utilities` | `references/utilities.md` |
| v5 code breaks; ImportError; DeprecationWarning | removed-name map | `references/migration-and-deprecations.md` |
| "Where is X documented?" | full name → file index | `references/api-index.md` |

If a name is marked **Subpackage import** in a reference, it is NOT importable
from bare `kerykeion` — use the exact import path shown there.

## Top traps

1. **v5 names raise `ImportError`.** `AstrologicalSubject`, `KerykeionChartSVG`,
   `NatalAspects`, `SynastryAspects` are gone; the error message includes the
   replacement AND the v6 default changes that alter results. `hasattr()` /
   `getattr(..., default)` also raise for these — feature-detect with
   `try/except ImportError`. See `references/migration-and-deprecations.md`.
2. **Offline needs `lng`/`lat`/`tz_str`** — and pass `city`/`nation` anyway or
   reports/`to_context` will say Greenwich.
3. **Stars ≠ points.** Fixed stars go in `active_fixed_stars`, come back on
   `subject.fixed_stars`. Star names inside `active_points` are redirected with
   a warning; an all-stars `active_points` raises.
4. **`active_points=[]` raises.** Pass `None` for the defaults. Unknown point
   names raise too (typos fail loudly).
5. **Optional points are `None` unless requested**; houses always exist;
   Sun/Moon failure raises; other omissions land in `ephemeris_warnings`.
6. **Sealed ephemeris range.** A fresh install covers **1849–2150**; outside it
   kerykeion **raises** (`EphemerisRangeError` / `KerykeionException`) instead
   of silently degrading. Widen with `libephemeris.download_leb_for_tier(...)`.
7. **Provenance populates on libephemeris only**, and `source="Keplerian"` is
   normal for default points on old dates (e.g. Chiron). Never match
   exhaustively on `source` values; house-geometry points have provenance
   `None` by design, and fixed stars carry `source`/`precision_class` but keep
   their coverage and review fields `None`.
8. **`ChartDrawer`: `theme` defaults to `"classic"` but `style` defaults to
   `"modern"`** — two orthogonal knobs. Default filenames carry the style
   suffix (`" - Modern.svg"` / `" - Classic.svg"`). `external_view`,
   `show_degree_indicators`, `show_aspect_icons` are classic-only.
9. **Time is local wall-clock** + `tz_str`; never pre-convert to UTC except
   with `from_iso_utc_time` (which is UTC by contract).
10. **Sidereal coherence.** The subject factories default a missing
    `sidereal_mode` to `FAGAN_BRADLEY`, but the subject-less event factories
    (and direct model construction) require it explicitly with
    `zodiac_type="Sidereal"`. `sidereal_mode` with Tropical raises; `USER`
    mode needs both `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0`.

Also: `ephemeris_session()` rejects same-thread nesting (`RuntimeError`) — never
build a subject inside an open session (`references/backends-and-provenance.md`);
an empty list passed to `to_context` raises `TypeError`
(`references/reports-and-ai-context.md`).

## Defaults worth knowing

- **Zodiac** Tropical · **houses** Placidus `"P"` · **perspective** Apparent
  Geocentric · **chart style** `modern` · **chart theme** `classic`.
- **Active points (14)**: Sun–Pluto, `True_North_Lunar_Node`, `Chiron`,
  `Ascendant`, `Medium_Coeli`. (v5 had 18 — `kerykeion.settings.
  V5_DEFAULT_ACTIVE_POINTS` restores them.)
- **Active aspects**: conjunction/opposition/trine/square at 6°, sextile at 5°.
  Predictive factories use a flat 3° set (`PREDICTIVE_ACTIVE_ASPECTS`).
- Point-set and aspect-set presets, and where to import each:
  `references/subjects.md` and `references/aspects-and-orbs.md`.

## Reference index

| File | Read when the task involves |
|---|---|
| `references/api-index.md` | finding which file documents a given name |
| `references/subjects.md` | building/reading subjects, points, composites |
| `references/backends-and-provenance.md` | backends, env vars, sealed ranges, provenance |
| `references/zodiac-houses-perspectives.md` | sidereal, houses, perspectives, lots |
| `references/charts-and-drawing.md` | chart data, SVG drawing, themes, settings |
| `references/aspects-and-orbs.md` | aspects, orbs, declinations |
| `references/analysis.md` | dominants, compatibility, house comparison, midpoints |
| `references/predictive.md` | ephemeris series, transits, returns, progressions, solar arc |
| `references/mundane-events.md` | eclipses, lunations, stations, ingresses, star catalog |
| `references/calendars-hours-moon.md` | moon phase, sun times, planetary hours, VoC |
| `references/traditional.md` | profections, firdaria, ZR, horary, directions, dignities |
| `references/locational.md` | relocation, astrocartography |
| `references/reports-and-ai-context.md` | `ReportGenerator`, `to_context` |
| `references/utilities.md` | JD/ISO/timezone/angle helpers |
| `references/migration-and-deprecations.md` | v5→v6 migration, deprecations |

Scripts (run them, don't just read them):

- `scripts/quickstart.py` — offline end-to-end sanity check (`--svg DIR` optional).
- `scripts/env_report.py` — backend / env / ephemeris-coverage diagnostic; run it
  when dates raise or the active backend is unclear.
