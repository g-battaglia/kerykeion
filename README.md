<h1 align="center">Kerykeion</h1>

<div align="center">
  <a href="https://github.com/g-battaglia/kerykeion"><img src="https://img.shields.io/github/stars/g-battaglia/kerykeion.svg?logo=github" alt="GitHub stars"></a>
  <a href="https://github.com/g-battaglia/kerykeion"><img src="https://img.shields.io/github/forks/g-battaglia/kerykeion.svg?logo=github" alt="GitHub forks"></a>
  <a href="https://pypi.org/project/kerykeion/"><img src="https://img.shields.io/pypi/v/kerykeion?label=PyPI" alt="PyPI version"></a>
  <a href="https://pypi.org/project/kerykeion/"><img src="https://img.shields.io/pypi/pyversions/kerykeion.svg" alt="Supported Python versions"></a>
  <a href="https://pepy.tech/project/kerykeion"><img src="https://static.pepy.tech/badge/kerykeion/month" alt="Monthly downloads"></a>
</div>

<p align="center">
  <img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/v6/docs/charts/modern_default_natal.svg" width="540" alt="Kerykeion modern natal chart">
</p>

Kerykeion is a Python library for astrology. It computes planetary and house positions, detects aspects, and generates SVG charts, including birth, synastry, transit, and composite charts. You can also customize which planets to include in your calculations.

The main goal of this project is to provide high-precision astrological calculations through a clean, data-driven approach, making them accessible and programmable.

Kerykeion also serves as the engine behind the hosted Astrologer API, and it integrates seamlessly with LLM and AI applications.

## Hosted API

If you are building a commercial application, a SaaS, or prefer to keep the codebase closed-source, consider the hosted **Astrologer API** on RapidAPI.

Your app consumes Kerykeion as an external service rather than importing the AGPL library directly — no server setup, no copyleft concerns. Subscribing directly supports the ongoing development of this open-source project.

<p align="center">
  <strong><a href="https://rapidapi.com/gbattaglia/api/astrologer/pricing">Get Started on RapidAPI</a></strong>
  &nbsp;·&nbsp;
  <strong><a href="https://www.kerykeion.net/content/astrologer-api/">Full API Documentation</a></strong>
</p>

The hosted API provides JSON calculations, ready-to-display SVG charts, and AI-ready context endpoints. It is a practical fit for web, mobile, frontend-only, and production applications that should not operate their own Python and ephemeris infrastructure.

| | Kerykeion library | Hosted Astrologer API |
|---|---|---|
| Deployment | You install and operate Python | Cloud-hosted service |
| License model | AGPL-3.0 | External API consumption |
| Closed-source app | Review AGPL or commercial-license requirements | Designed for this use case |
| Updates and ephemeris infrastructure | Managed by your team | Managed by the service |
| Offline operation | Yes | No |
| Customizing library internals | Full access | Stable HTTP contract |

## Table of Contents

- [Hosted API](#hosted-api)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [How Kerykeion Is Organized](#how-kerykeion-is-organized)
- [Feature Overview](#feature-overview)
  - [Subjects and Chart Types](#subjects-and-chart-types)
  - [Zodiacs, Houses, Perspectives, and Points](#zodiacs-houses-perspectives-and-points)
  - [Aspects and Chart Analysis](#aspects-and-chart-analysis)
  - [Predictive and Locational Techniques](#predictive-and-locational-techniques)
  - [Sky Events and Time Calculations](#sky-events-and-time-calculations)
  - [Traditional Techniques](#traditional-techniques)
  - [Rendering, Data, Reports, and AI](#rendering-data-reports-and-ai)
- [Core Workflows](#core-workflows)
  - [Build and Inspect a Subject](#build-and-inspect-a-subject)
  - [Generate an SVG Chart](#generate-an-svg-chart)
  - [Synastry and Transits](#synastry-and-transits)
  - [Solar and Lunar Returns](#solar-and-lunar-returns)
  - [Composite and Davison Charts](#composite-and-davison-charts)
  - [Aspects and Chart Analysis](#aspects-and-chart-analysis-1)
  - [Reports and AI Context](#reports-and-ai-context)
- [Calculation Configuration](#calculation-configuration)
  - [Active Points](#active-points)
  - [Fixed Stars](#fixed-stars)
  - [Sidereal Modes and Custom Ayanamsa](#sidereal-modes-and-custom-ayanamsa)
  - [House Systems and Polar Latitudes](#house-systems-and-polar-latitudes)
  - [Observer Perspectives](#observer-perspectives)
  - [Timezones, LMT, and Calendars](#timezones-lmt-and-calendars)
  - [Precision, Coverage, and Provenance](#precision-coverage-and-provenance)
- [Chart Rendering](#chart-rendering)
- [Command-Line Interface](#command-line-interface)
- [Documentation](#documentation)
- [Swiss Ephemeris Backend](#swiss-ephemeris-backend)
- [AI Agent Skill](#ai-agent-skill)
- [Development](#development)
- [License and Commercial Use](#license-and-commercial-use)
- [Contributing and Citation](#contributing-and-citation)

## Installation

Kerykeion requires **Python 3.12 or newer**.

This branch documents **6.0.0rc1**, the first v6 release candidate. Select the prerelease explicitly:

```bash
# Library only
pip install --upgrade "kerykeion==6.0.0rc1"

# Library plus the command-line interface
pip install --upgrade --pre "kerykeion[cli]==6.0.0rc1"

# Library, CLI, and optional Swiss Ephemeris backend
pip install --upgrade --pre "kerykeion[all]==6.0.0rc1"
```

An unqualified `pip install kerykeion` selects the latest stable release. Before upgrading from v4 or v5, read the [v6 release notes](https://github.com/g-battaglia/kerykeion/blob/v6/release_notes/v6.0.0rc1.md) and the [migration guide](https://www.kerykeion.net/content/docs/migration).

A plain library installation intentionally provides no shell command. The `kerykeion` command belongs to the separate `kerykeion-cli` distribution, installed by the `cli` extra.

### Supported date ranges

The default reviewed ephemeris tier uses JPL DE440s and covers **1850–2150**. The upper bound is exclusive. Dates outside the active kernel raise `KerykeionException` rather than silently changing source.

Install a wider reviewed core through libephemeris:

```python
# doc-snippet: no-run — downloads ephemeris kernels
import libephemeris

libephemeris.download_leb_for_tier("medium")    # 1550–2650
libephemeris.download_leb_for_tier("extended")  # DE441, including BCE dates
```

The core tier controls the date range of the core bodies. Asteroids, exotics, and lunar apsides use separate data groups or runtime models and can have different coverage. See [Ephemeris Backend](https://www.kerykeion.net/content/docs/ephemeris_backend) and [Backend Precision Comparison](https://www.kerykeion.net/content/docs/backend_precision_comparison).

## Quick Start

This offline example creates a subject, derives chart data, and saves a natal SVG:

```python
from pathlib import Path

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person",
    year=1990,
    month=7,
    day=15,
    hour=10,
    minute=30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
drawer.save_svg(output_path=output_dir, filename="example-natal")

print(subject.sun.sign, subject.sun.position)
print((output_dir / "example-natal.svg").resolve())
```

The recommended offline contract is explicit: set `online=False` and provide longitude, latitude, and an IANA timezone. For automatic location lookup, set `online=True`, provide `city` and `nation`, and configure a GeoNames username through `geonames_username` or `KERYKEION_GEONAMES_USERNAME`.

- [Getting Started](https://www.kerykeion.net/content/docs/)
- [Birth Data](https://www.kerykeion.net/content/examples/birth-data)
- [Astrological Subject Factory](https://www.kerykeion.net/content/docs/astrological_subject_factory)
- [Birth Chart Example](https://www.kerykeion.net/content/examples/birth-chart)

## How Kerykeion Is Organized

Kerykeion separates calculations from presentation:

```text
Birth/event data
      |
      v
AstrologicalSubjectFactory  ->  AstrologicalSubjectModel
      |
      v
ChartDataFactory            ->  ChartDataModel
      |
      +--> ChartDrawer       ->  SVG
      +--> ReportGenerator   ->  text
      +--> to_context        ->  XML for LLMs
      +--> model_dump_json   ->  JSON
```

- `AstrologicalSubjectFactory` computes the sky, houses, points, configuration, and provenance through `from_birth_data()`, `from_iso_utc_time()`, or `from_current_time()`.
- `ChartDataFactory` adds aspects, distributions, angularities, stelliums, relationship scores, and house comparisons where appropriate.
- `ChartDrawer` only renders already-computed chart data.
- Every public result is a Pydantic model with attribute access, dictionary-style compatibility, and JSON serialization.

This design lets applications use the calculations without SVG, replace the presentation layer, or send structured results directly to another service.

## Feature Overview

Every public calculation factory is named below. Features that share a factory or are configured as point families, rendering options, or output formats are listed separately so the README remains a complete map of the library.

### Subjects and Chart Types

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Natal and event subjects | `AstrologicalSubjectFactory` | Planetary positions, houses, axes, lunar phase, configuration, and provenance for a local or UTC moment | [Subject Factory](https://www.kerykeion.net/content/docs/astrological_subject_factory) |
| Structured chart data | `ChartDataFactory` | Typed data for natal, synastry, transit, return, composite, and progression charts | [Chart Data](https://www.kerykeion.net/content/docs/chart_data_factory) |
| Natal charts | `ChartDataFactory.create_natal_chart_data` | Single-subject aspects, distributions, angularities, and stelliums | [Birth Chart](https://www.kerykeion.net/content/examples/birth-chart) |
| Synastry charts | `ChartDataFactory.create_synastry_chart_data` | Cross-chart aspects, reciprocal house placement, and compatibility scoring | [Synastry](https://www.kerykeion.net/content/examples/synastry-chart) |
| Transit charts | `ChartDataFactory.create_transit_chart_data` | Natal-to-transit aspects and projected house positions | [Transit Chart](https://www.kerykeion.net/content/examples/transit-chart) |
| Solar and Lunar return charts | `PlanetaryReturnFactory` | Exact return moments and single- or dual-wheel return subjects | [Planetary Returns](https://www.kerykeion.net/content/docs/planetary_return_factory) · [Example](https://www.kerykeion.net/content/examples/dual-return-chart) |
| Heliocentric returns | `PlanetaryReturnFactory.next_heliocentric_return` | Returns of a planet to its natal heliocentric longitude | [Planetary Returns](https://www.kerykeion.net/content/docs/planetary_return_factory) |
| Lunar-node crossings | `PlanetaryReturnFactory.next_lunar_node_crossing` | Exact moments when the Moon crosses its orbital node | [Planetary Returns](https://www.kerykeion.net/content/docs/planetary_return_factory) |
| Midpoint composite charts | `CompositeSubjectFactory.get_midpoint_composite_subject_model` | Circular midpoint positions with explicit house-frame metadata | [Composite Subjects](https://www.kerykeion.net/content/docs/composite_subject_factory) · [Example](https://www.kerykeion.net/content/examples/composite-chart) |
| Davison charts | `CompositeSubjectFactory.get_davison_composite_subject_model` | The time-space midpoint recast as a real chart | [Composite Subjects](https://www.kerykeion.net/content/docs/composite_subject_factory) |
| Relocated charts | `RelocatedChartFactory` | Natal planetary positions with houses, axes, sect, Vertex, and Lots recalculated for another location | [Relocated Charts](https://www.kerykeion.net/content/docs/relocated_chart_factory) |
| Secondary-progressed charts | `SecondaryProgressionFactory` | Day-for-a-year progressed subjects and progressed-to-natal contacts | [Secondary Progressions](https://www.kerykeion.net/content/docs/secondary_progressions_factory) |
| Solar-arc-directed charts | `SolarArcFactory` | A uniform progressed-Sun arc applied to natal points and angles | [Solar Arc](https://www.kerykeion.net/content/docs/solar_arc_factory) |

### Zodiacs, Houses, Perspectives, and Points

| Feature | Configuration/API | Description | Documentation |
|---|---|---|---|
| Tropical zodiac | `zodiac_type="Tropical"` | Default zodiac frame | [Subject Factory](https://www.kerykeion.net/content/docs/astrological_subject_factory) |
| Sidereal zodiac | `zodiac_type="Sidereal"`, `sidereal_mode` | 47 named modes plus the custom `USER` mode | [Sidereal Modes](https://www.kerykeion.net/content/examples/sidereal-modes) |
| Custom ayanamsa | `sidereal_mode="USER"`, `custom_ayanamsa_t0`, `custom_ayanamsa_ayan_t0` | User-defined reference epoch and offset | [Schemas](https://www.kerykeion.net/content/docs/schemas#siderealmode) |
| Fixed reference frames | J2000, J1900, B1950, and related modes | Backend-supported sidereal reference-frame choices | [Ephemeris Backend](https://www.kerykeion.net/content/docs/ephemeris_backend) |
| House systems | `houses_system_identifier` | Placidus by default and all systems supported by the active backend | [House Systems](https://www.kerykeion.net/content/examples/houses-systems) |
| Polar house handling | `polar_house_fallbacks`, `coincident_house_cusps` | Machine-readable substitutions and zero-width cusp groups | [FAQ](https://www.kerykeion.net/content/docs/faq) |
| Apparent and true geocentric | `perspective_type` | Standard apparent positions or true geometric positions | [Perspective Types](https://www.kerykeion.net/content/examples/perspective-type) |
| Topocentric | `perspective_type="Topocentric"`, `altitude` | Observer-parallax positions at a specific location and elevation | [Perspective Types](https://www.kerykeion.net/content/examples/perspective-type) |
| Heliocentric and barycentric | `perspective_type` | Sun-centered or Solar System barycenter positions | [Perspective Types](https://www.kerykeion.net/content/examples/perspective-type) |
| Planetocentric perspectives | Selenocentric through Saturncentric | Positions observed from another supported planet | [Perspective Types](https://www.kerykeion.net/content/examples/perspective-type) |
| Configurable point set | `active_points` | Compute only the planets, axes, nodes, Lots, and optional bodies required by the application | [Active Points](https://www.kerykeion.net/content/docs/active_points) |
| Lunar nodes | True/Mean North and South nodes | Rahu/Ketu pairs with exact derived opposites | [Active Points](https://www.kerykeion.net/content/docs/active_points) |
| Lilith, Priapus, and White Moon | Mean/True/Interpolated variants | Lunar apogee/perigee families and native Selena support where available | [Active Points](https://www.kerykeion.net/content/docs/active_points) |
| Arabic Parts / Lots | Fortune, Spirit, Eros, and Faith | Sect-aware points with prerequisites calculated automatically | [Active Points](https://www.kerykeion.net/content/docs/active_points) |
| Asteroids and centaurs | Chiron, Ceres, Pallas, Juno, Vesta, Pholus | Optional minor-body positions | [Active Points](https://www.kerykeion.net/content/docs/active_points) |
| Trans-Neptunian objects | Eris, Sedna, Haumea, Makemake, Ixion, Orcus, Quaoar | Optional TNO positions with source/coverage metadata | [Active Points](https://www.kerykeion.net/content/docs/active_points) |
| Uranian / Hamburg points | Cupido through Poseidon | Eight hypothetical points from runtime analytical models | [Active Points](https://www.kerykeion.net/content/docs/active_points) |
| Fixed stars | `active_fixed_stars`, `subject.fixed_stars` | Opt-in catalog stars with longitude, latitude, speed, declination, and magnitude | [Active Points](https://www.kerykeion.net/content/docs/active_points) |
| Dynamic star discovery | `FixedStarDiscoveryFactory` | Search the catalog and find prominent stars near subject positions | [Fixed Star Discovery](https://www.kerykeion.net/content/docs/fixed_star_discovery_factory) |
| Online location resolution | GeoNames integration | Cached city, coordinate, and timezone lookup | [GeoNames](https://www.kerykeion.net/content/docs/fetch_geonames) |

### Aspects and Chart Analysis

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Single- and dual-chart aspects | `AspectsFactory` | Longitudinal aspects within one chart or between two charts | [Aspects](https://www.kerykeion.net/content/docs/aspects) |
| Declination aspects | `single_chart_declination_aspects`, `dual_chart_declination_aspects` | Parallels and contra-parallels | [Aspects](https://www.kerykeion.net/content/docs/aspects) |
| Applying/separating motion | `AspectModel.aspect_movement` | Aspect movement derived from relative speed | [Aspects](https://www.kerykeion.net/content/docs/aspects) |
| Custom orbs | `active_aspects`, `point_orb_adjustments` | Per-aspect, per-point, and aspect-specific orb policies | [Aspects](https://www.kerykeion.net/content/docs/aspects) |
| House comparison | `HouseComparisonFactory` | Reciprocal placement of each subject's points in the other's houses | [House Comparison](https://www.kerykeion.net/content/docs/house_comparison) · [Example](https://www.kerykeion.net/content/examples/house-comparison) |
| Relationship score | `RelationshipScoreFactory` | Ciro Discepolo compatibility score with contributing aspects | [Relationship Score](https://www.kerykeion.net/content/docs/relationship_score_factory) · [Example](https://www.kerykeion.net/content/examples/relationship-score) |
| Element and quality distributions | `ChartDataFactory` | Pure count or configurable weighted analysis | [Element and Quality](https://www.kerykeion.net/content/docs/element_quality_distribution) |
| Angularities and stelliums | `ChartDataModel.angularities`, `.stelliums` | Planets near axes and concentrations by house | [Chart Data](https://www.kerykeion.net/content/docs/chart_data_factory) |
| Essential dignities | `calculate_dignities=True` | Domicile, exaltation, detriment, fall, triplicity, terms, and scores | [Subject Factory](https://www.kerykeion.net/content/docs/astrological_subject_factory) |
| Vedic nakshatras | `calculate_nakshatra=True` | Nakshatra, pada, and Vimshottari lord with an explicit ayanamsa | [Subject Factory](https://www.kerykeion.net/content/docs/astrological_subject_factory) |
| Motion state | point `speed`, `retrograde`, `motion_state` | Fast, average, slow, retrograde, and named station states | [Schemas](https://www.kerykeion.net/content/docs/schemas) |
| Declination and out-of-bounds | point `declination`, `is_out_of_bounds` | OOB detection against the epoch's true obliquity | [Schemas](https://www.kerykeion.net/content/docs/schemas) |
| Gauquelin sectors | `calculate_gauquelin=True` | 36-sector cusps and per-point sector values | [Subject Factory](https://www.kerykeion.net/content/docs/astrological_subject_factory) |
| Local Space | `calculate_local_space=True` | Azimuth and altitude above the observer's horizon | [Subject Factory](https://www.kerykeion.net/content/docs/astrological_subject_factory) |
| Nutation and obliquity | `calculate_nutation=True` | True/mean obliquity and nutation components | [Schemas](https://www.kerykeion.net/content/docs/schemas) |
| Midpoint analysis | `MidpointFactory` | Pairwise midpoints, 90° dial positions, and third-point activations | [Midpoints](https://www.kerykeion.net/content/docs/midpoint_factory) |
| Chart dominants | `DominantsFactory` | Modern, Almuten Figuris, elemental, or custom `DominantStrategy` scoring | [Dominants](https://www.kerykeion.net/content/docs/dominants_factory) |

### Predictive and Locational Techniques

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Ephemeris time series | `EphemerisDataFactory` | Daily, hourly, or minutely samples as dictionaries, models, or full subjects | [Ephemeris Data](https://www.kerykeion.net/content/docs/ephemeris_data_factory) · [Example](https://www.kerykeion.net/content/examples/ephemeris-data) |
| Transit snapshots | `TransitsTimeRangeFactory.get_transit_moments` | Aspects at every supplied ephemeris sample, optionally including the full subject | [Transit Ranges](https://www.kerykeion.net/content/docs/transits_time_range_factory) |
| Transit events | `TransitsTimeRangeFactory.get_transit_events` | Applying/exact/separating runs, retrograde multi-passes, and optional exact-moment refinement | [Transit Ranges](https://www.kerykeion.net/content/docs/transits_time_range_factory) · [Example](https://www.kerykeion.net/content/examples/transits-time-range) |
| Solar and Lunar returns | `PlanetaryReturnFactory` | Exact return searches in the natal zodiac/perspective, cast for the requested return location | [Planetary Returns](https://www.kerykeion.net/content/docs/planetary_return_factory) |
| Secondary progressions | `SecondaryProgressionFactory` | Day-for-a-year subjects and contacts | [Secondary Progressions](https://www.kerykeion.net/content/docs/secondary_progressions_factory) |
| Solar arc | `SolarArcFactory` | Directed points and directed-to-natal aspects | [Solar Arc](https://www.kerykeion.net/content/docs/solar_arc_factory) |
| Primary directions | `PrimaryDirectionsFactory` | Placidus semi-arc directions with Ptolemy and Naibod rate keys | [Primary Directions](https://www.kerykeion.net/content/docs/primary_directions_factory) |
| Astrocartography | `AstroCartographyFactory` | MC, IC, ASC, and DSC lines represented as world-coordinate sequences | [Astrocartography](https://www.kerykeion.net/content/docs/astro_cartography_factory) |
| Relocation | `RelocatedChartFactory` | House and angle changes for a destination while natal planetary longitudes stay fixed | [Relocated Charts](https://www.kerykeion.net/content/docs/relocated_chart_factory) |

Secondary-progressed houses follow the **Q2 / daily houses** convention: they are the real angles at the progressed ephemeris instant, not solar-arc-directed angles. Planetary progressions are unaffected by this choice. See [Secondary Progressions](https://www.kerykeion.net/content/docs/secondary_progressions_factory).

### Sky Events and Time Calculations

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Detailed Moon phase | `MoonPhaseDetailsFactory` | Illumination, phase windows, rise/set, Sun data, upcoming phases, and eclipse context | [Moon Phase Details](https://www.kerykeion.net/content/docs/moon_phase_details_factory) · [Example](https://www.kerykeion.net/content/examples/moon-phase-details) |
| Exact lunations | `LunationFinderFactory` | New, first-quarter, full, and last-quarter moments across a range | [Lunations](https://www.kerykeion.net/content/docs/lunation_factory) |
| Sunrise, sunset, and twilight | `SunTimesFactory` | Upper-limb rise/set, solar noon, day length, twilight, and polar day/night | [Sun Times](https://www.kerykeion.net/content/docs/sun_times_factory) |
| Planetary hours | `PlanetaryHoursFactory` | Twelve unequal day and night hours with Chaldean rulers | [Planetary Hours](https://www.kerykeion.net/content/docs/planetary_hours_factory) |
| Void-of-course Moon | `VoidOfCourseMoonFactory` | Current void state and complete VoC windows before ingress | [Void of Course](https://www.kerykeion.net/content/docs/void_of_course_moon_factory) |
| Retrograde stations and periods | `RetrogradeStationFactory` | Exact SR/SD events and clipped retrograde spans | [Retrograde Stations](https://www.kerykeion.net/content/docs/retrograde_station_factory) |
| Sign ingresses and stays | `SignIngressFactory` | Exact ingress moments and contiguous sign periods | [Sign Ingresses](https://www.kerykeion.net/content/docs/sign_ingress_factory) |
| Mundane aspects | `MundaneAspectFactory` | Exact moving-body-to-moving-body aspects for aspectarians | [Mundane Aspects](https://www.kerykeion.net/content/docs/mundane_aspects_factory) |
| Solar and Lunar eclipses | `EclipseFactory` | Global and local eclipse searches with structured circumstances | [Eclipses](https://www.kerykeion.net/content/docs/eclipse_factory) |
| Planetary phenomena | `PlanetaryPhenomenaFactory` | Elongation, phase angle, magnitude, morning/evening status, and solar phase | [Planetary Phenomena](https://www.kerykeion.net/content/docs/planetary_phenomena_factory) |
| Planetary nodes and apsides | `PlanetaryNodesFactory` | Ascending/descending nodes and periapsis/apoapsis | [Planetary Nodes](https://www.kerykeion.net/content/docs/planetary_nodes_factory) |
| Heliacal events | `HeliacalFactory` | Heliacal risings and settings from observer and atmospheric inputs | [Heliacal Events](https://www.kerykeion.net/content/docs/heliacal_factory) |
| Lunar occultations | `OccultationFactory` | Global or local occultation searches for supported bodies | [Occultations](https://www.kerykeion.net/content/docs/occultation_factory) |

Sunrise and `subject.is_diurnal` intentionally answer different questions. Sunrise uses the apparent upper limb and standard refraction; diurnality uses the Sun's geometric center against the true horizon. See [Sun Times](https://www.kerykeion.net/content/docs/sun_times_factory).

### Traditional Techniques

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Zodiacal releasing | `ZodiacalReleasingFactory` | L1–L4 aphesis periods from Fortune or Spirit, with loosing-of-the-bond and peak markers | [Zodiacal Releasing](https://www.kerykeion.net/content/docs/zodiacal_releasing_factory) |
| Annual profections | `ProfectionsFactory` | Activated house/sign, Lord of the Year, and age cycle | [Profections](https://www.kerykeion.net/content/docs/profections_factory) |
| Firdaria | `FirdariaFactory` | Sect-dependent Persian major and sub-period sequences | [Firdaria](https://www.kerykeion.net/content/docs/firdaria_factory) |
| Mutual receptions | `MutualReceptionsFactory` | Domicile and exaltation receptions among classical planets | [Mutual Receptions](https://www.kerykeion.net/content/docs/receptions_factory) |
| Horary indicators | `HoraryIndicatorsFactory` | Querent/quesited rulers, considerations before judgment, VoC state, and receptions | [Horary](https://www.kerykeion.net/content/docs/horary_factory) |

### Rendering, Data, Reports, and AI

| Feature | Main API/configuration | Description | Documentation |
|---|---|---|---|
| SVG rendering | `ChartDrawer` | Natal, synastry, transit, return, composite, and progression charts | [Charts](https://www.kerykeion.net/content/docs/charts) |
| Modern and classic styles | `style="modern"` / `"classic"` | Concentric modern layout or traditional classic wheel | [Modern Charts](https://www.kerykeion.net/content/examples/modern-charts) |
| Themes | `theme` | Classic/light, dark, black-and-white, or unthemed CSS variables | [Theming](https://www.kerykeion.net/content/examples/theming) |
| Ten chart languages | `chart_language`, `language_pack` | EN, FR, PT, ES, TR, RU, IT, CN, DE, HI, plus custom labels | [Chart Language](https://www.kerykeion.net/content/examples/chart-language) |
| Glyph sizing and spreading | `glyph_size`, automatic decluttering | Small, medium, or large clusters with collision-aware placement | [Glyph Sizes](https://www.kerykeion.net/content/examples/glyph-sizes) · [Glyph Reference](https://www.kerykeion.net/content/docs/chart-glyphs) |
| Optional visual marks | `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`, `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note` | Opt-in facts already carried by chart data | [Chart Marks](https://www.kerykeion.net/content/examples/chart-marks) |
| Minimal SVG outputs | wheel-only and grid-only methods | Reusable wheel or aspect table without the full chart page | [Minimalist Charts](https://www.kerykeion.net/content/examples/minimalist-charts-and-aspect-table) |
| External natal view | `external_view=True`, classic style | Classic natal wheel with planets outside the zodiac ring | [Birth Chart](https://www.kerykeion.net/content/examples/birth-chart) |
| SVG portability controls | `minify`, `remove_css_variables`, `transparent_background`, `auto_size`, `custom_title` | Compact, standalone, embeddable, and custom-sized output | [Charts](https://www.kerykeion.net/content/docs/charts) |
| Machine-readable SVG metadata | `kr:` attributes | Stable point, owner, house, projected-house, and ring identifiers | [Chart Internals](https://www.kerykeion.net/content/docs/chart_internals) |
| Pydantic and JSON | `.model_dump()`, `.model_dump_json()` | Typed validation and structured serialization | [Schemas](https://www.kerykeion.net/content/docs/schemas) |
| Text reports | `ReportGenerator` | Reports for subjects, chart data, Moon context, and traditional techniques | [Reports](https://www.kerykeion.net/content/docs/report) · [Example](https://www.kerykeion.net/content/examples/report) |
| LLM context | `to_context` | Escaped, non-qualitative XML for prompts and agents | [Context Serializer](https://www.kerykeion.net/content/docs/context_serializer) |
| Command-line interface | `kerykeion-cli` | Charts, analysis, techniques, events, profiles, JSON, SVG, and guarded factory dispatch | [CLI](https://www.kerykeion.net/content/docs/cli) |
| AI Agent Skill | `skills/kerykeion`, `kerykeion/llms.txt` | API-grounded instructions for coding agents | [AI Agent Skill](#ai-agent-skill) |
| Selectable backend | `BACKEND_NAME`, environment variables | Default libephemeris or optional Swiss Ephemeris | [Ephemeris Backend](https://www.kerykeion.net/content/docs/ephemeris_backend) |
| Hosted service | Astrologer API | External access to calculations, SVG, and AI context for commercial products | [RapidAPI](https://rapidapi.com/gbattaglia/api/astrologer/pricing) · [API Docs](https://www.kerykeion.net/content/astrologer-api/) |

## Core Workflows

### Build and Inspect a Subject

```python
from kerykeion import AstrologicalSubjectFactory

john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon",
    1940,
    10,
    9,
    18,
    30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

print(john.sun.sign, john.sun.position, john.sun.house)
print(john["moon"]["abs_pos"])
print(john.is_diurnal)
print(john.model_dump_json(indent=2))
```

Each `KerykeionPointModel` can carry sign, absolute and within-sign longitude, speed, retrograde state, motion state, house, declination, ecliptic latitude, source, precision class, and optional enrichment data. Fields that do not apply remain `None` rather than receiving fabricated values.

### Generate an SVG Chart

```python
from pathlib import Path

from kerykeion import ChartDataFactory, ChartDrawer

natal_data = ChartDataFactory.create_natal_chart_data(john)
natal_drawer = ChartDrawer(natal_data)

chart_dir = Path("charts_output")
chart_dir.mkdir(exist_ok=True)
natal_drawer.save_svg(
    output_path=chart_dir,
    filename="john-lennon-natal",
    style="modern",
)
```

Use `generate_svg_string()` when the SVG should stay in memory. Wheel-only and aspect-grid-only methods are available for custom layouts. See [Charts](https://www.kerykeion.net/content/docs/charts).

### Synastry and Transits

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

paul = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney",
    1942,
    6,
    18,
    15,
    30,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)

synastry_data = ChartDataFactory.create_synastry_chart_data(john, paul)
print(len(synastry_data.aspects))
print(synastry_data.relationship_score.score_value)

transit_data = ChartDataFactory.create_transit_chart_data(john, paul)
print(transit_data.chart_type)
```

A transit chart accepts any event subject as its moving side. For sampled transit timelines and refined exact events, use `EphemerisDataFactory` with `TransitsTimeRangeFactory`.

### Solar and Lunar Returns

```python
from kerykeion import ChartDataFactory, PlanetaryReturnFactory

return_factory = PlanetaryReturnFactory(
    john,
    lng=-2.9833,
    lat=53.4,
    tz_str="Europe/London",
    online=False,
)
solar_return = return_factory.next_return_from_date(
    2026,
    1,
    1,
    return_type="Solar",
)

single_return_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
dual_return_data = ChartDataFactory.create_return_chart_data(john, solar_return)

print(solar_return.iso_formatted_utc_datetime)
print(single_return_data.chart_type, dual_return_data.chart_type)
```

Return instants are reported to the whole second. Feeding a reported instant back to the ISO entry point advances to the following return; `backwards=True` finds the preceding one. Topocentric returns use the requested return location and altitude consistently for both the crossing search and the returned chart.

### Composite and Davison Charts

```python
from kerykeion import CompositeSubjectFactory

composite_factory = CompositeSubjectFactory(john, paul, house_anchor="auto")
midpoint_composite = composite_factory.get_midpoint_composite_subject_model()
davison_composite = composite_factory.get_davison_composite_subject_model()

print(midpoint_composite.house_frame)
print(davison_composite.sun.abs_pos)
```

The midpoint composite is a symbolic midpoint model. The Davison result is a real ephemeris chart cast at the pair's midpoint time and place. See [Composite Subject Factory](https://www.kerykeion.net/content/docs/composite_subject_factory).

### Aspects and Chart Analysis

```python
from kerykeion import AspectsFactory, ChartDataFactory

aspect_result = AspectsFactory.single_chart_aspects(
    john,
    point_orb_adjustments={"Sun": 1.5, "Moon": 1.5},
)
analysis = ChartDataFactory.create_natal_chart_data(
    john,
    distribution_method="weighted",
)

for aspect in aspect_result.aspects[:5]:
    print(aspect.p1_name, aspect.aspect, aspect.p2_name, aspect.orbit)

print(analysis.element_distribution)
print(analysis.angularities[:2])
print(analysis.stelliums)
```

Use `single_chart_declination_aspects()` or `dual_chart_declination_aspects()` for parallels and contra-parallels. See [Aspects](https://www.kerykeion.net/content/docs/aspects).

### Reports and AI Context

```python
from kerykeion import ReportGenerator, to_context

report = ReportGenerator(natal_data).generate_report(max_aspects=10)
xml_context = to_context(natal_data)

print(report[:500])
print(xml_context[:500])
```

`ReportGenerator` creates human-readable text. `to_context()` creates neutral XML intended as factual input to an LLM; it does not generate an astrological interpretation. See [Reports](https://www.kerykeion.net/content/docs/report) and [Context Serializer](https://www.kerykeion.net/content/docs/context_serializer).

## Calculation Configuration

### Active Points

`active_points` is a calculation choice, not only a drawing filter. Request optional points when the subject is created. `ChartDataFactory` can filter points that already exist, but it does not go back and calculate omitted bodies.

This example correctly includes both Mean and True lunar nodes and their opposites:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

requested_nodes = [
    "Mean_North_Lunar_Node",
    "Mean_South_Lunar_Node",
    "True_North_Lunar_Node",
    "True_South_Lunar_Node",
]
all_requested_points = list(dict.fromkeys([*DEFAULT_ACTIVE_POINTS, *requested_nodes]))

node_subject = AstrologicalSubjectFactory.from_birth_data(
    "Node Example",
    1990,
    7,
    15,
    10,
    30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
    active_points=all_requested_points,
)
node_data = ChartDataFactory.create_natal_chart_data(node_subject)

assert node_subject.mean_north_lunar_node is not None
assert node_subject.mean_south_lunar_node is not None
assert set(requested_nodes) <= set(node_data.active_points)
```

Presets for core, all, Uranian, and other point groups are documented in [Active Points](https://www.kerykeion.net/content/docs/active_points) and [Active Points Examples](https://www.kerykeion.net/content/examples/active-points).

### Fixed Stars

Fixed stars use a separate open-name channel because they come from a catalog rather than the closed chart-point vocabulary:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

star_subject = AstrologicalSubjectFactory.from_birth_data(
    "Star Example",
    1990,
    7,
    15,
    10,
    30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
    active_fixed_stars=["Sirius", "Regulus", "Aldebaran", "Antares", "Fomalhaut"],
)

sirius = star_subject.find_fixed_star("Sirius")
assert sirius is not None
print(sirius.abs_pos, sirius.declination, sirius.magnitude)

star_chart_data = ChartDataFactory.create_natal_chart_data(star_subject)
```

Requested stars participate automatically in chart rendering and aspects. Discover catalog names through `FixedStarCatalog` or `FixedStarDiscoveryFactory`. See [Fixed Star Discovery](https://www.kerykeion.net/content/docs/fixed_star_discovery_factory).

### Sidereal Modes and Custom Ayanamsa

```python
from kerykeion import AstrologicalSubjectFactory

sidereal_subject = AstrologicalSubjectFactory.from_birth_data(
    "Sidereal Example",
    1990,
    7,
    15,
    10,
    30,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    online=False,
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
)
print(sidereal_subject.ayanamsa_value)
```

For a custom ayanamsa, use `sidereal_mode="USER"` and provide both `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0`. Nakshatras on a tropical chart use `nakshatra_ayanamsa="LAHIRI"` by default for the lunar-mansion division only; the chart's tropical longitudes remain unchanged.

See [Sidereal Modes](https://www.kerykeion.net/content/examples/sidereal-modes) and [Schemas](https://www.kerykeion.net/content/docs/schemas#siderealmode).

### House Systems and Polar Latitudes

Pass a one-character `houses_system_identifier`; Placidus (`"P"`) is the default. See [House Systems](https://www.kerykeion.net/content/examples/houses-systems) for the supported list.

Some quadrant systems are mathematically undefined inside the polar circle. Kerykeion records any substitution in `subject.polar_house_fallbacks`; `houses_system_identifier` remains what was requested and `effective_houses_system_identifier` states what produced the cusps. Systems that legitimately place several cusps at one longitude expose those zero-width groups through `coincident_house_cusps`.

`ChartDrawer(..., show_polar_fallback_note=True)` can print the substitution on the chart.

### Observer Perspectives

The default is `"Apparent Geocentric"`. Available alternatives include `"True Geocentric"`, `"Topocentric"`, `"Heliocentric"`, `"Barycentric"`, `"Selenocentric"`, and supported planetocentric frames.

Frame-specific rules matter:

- a center body has no position as seen from itself and is excluded;
- lunar nodes and lunar apogee variants are geocentric-only;
- Local Space, Gauquelin sectors, and OOB classification are only populated in frames where they are meaningful;
- two-chart operations require compatible frames;
- a Topocentric subject cannot be relocated by keeping its original planetary positions, because their parallax belongs to the original observer.

See [Perspective Types](https://www.kerykeion.net/content/examples/perspective-type).

### Timezones, LMT, and Calendars

- Use an IANA zone such as `Europe/Rome`; a modern fixed UTC offset cannot reproduce historical or DST rules.
- If a modern wall time is repeated or skipped by a transition, `is_dst=True` selects the larger UTC offset and `is_dst=False` the smaller one. Leaving it unset raises instead of guessing.
- Before a zone has a recorded civil clock, a synthetic IANA `LMT` record is replaced by Local Mean Time at the supplied longitude. Named historical records such as RMT, BMT, KMT, and MMT remain authoritative.
- Naive daily `EphemerisDataFactory` inputs advance by local calendar days. Hourly and minutely series advance uniformly in UTC.
- CE birth-data components use the proleptic Gregorian calendar. BCE birth input uses astronomical year numbering (`0` = 1 BCE) and the Julian-calendar birth path.
- ISO event timestamps use the proleptic Gregorian calendar required by ISO 8601.

See [Astrological Subject Factory](https://www.kerykeion.net/content/docs/astrological_subject_factory), [Ephemeris Data](https://www.kerykeion.net/content/docs/ephemeris_data_factory), and [Utilities](https://www.kerykeion.net/content/docs/utilities).

### Precision, Coverage, and Provenance

High precision depends on body, date, active data tier, and source. A successful chart can contain points from different producers; applications should inspect the public metadata instead of assuming every optional body came from the core JPL kernel:

- `subject.ephemeris_warnings` lists optional points that no permitted source could produce;
- `point.source` identifies sources such as `LEB`, `Derived`, `Analytical`, or `Keplerian`;
- `point.precision_class` states the backend's classification;
- `point.ephemeris_coverage_start_jd` and `point.ephemeris_coverage_end_jd` expose the applicable window;
- `point.source_reviewed` reports whether that coverage record is reviewed.

`source="Keplerian"` is an approximation and is not ephemeris-grade. Geometrically derived points say `source="Derived"`. Uranian points are runtime analytical models and say `source="Analytical"`; they are not LEB data.

Sun or Moon calculation failure raises because a subject without either luminary is not a usable chart. Optional-body failures can return a valid subject with a machine-readable warning. See [Backend Precision Comparison](https://www.kerykeion.net/content/docs/backend_precision_comparison).

## Chart Rendering

The modern concentric-ring renderer is the default; the classic wheel remains fully supported. All chart types can use the three built-in themes—`"classic"`, `"dark"`, and `"black-and-white"`—or `theme=None` for unthemed CSS variables.

```python
from pathlib import Path

from kerykeion import ChartDrawer

styled_drawer = ChartDrawer(
    natal_data,
    theme="dark",
    chart_language="IT",
    glyph_size="large",
    show_motion_state=True,
    show_out_of_bounds=True,
    show_aspect_movement=True,
)
styled_drawer.save_svg(
    output_path=Path("charts_output"),
    filename="john-dark-marked",
    minify=True,
)
```

<p align="center">
  <img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/v6/docs/charts/modern_classic_natal.svg" width="230" alt="Modern classic theme">
  <img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/v6/docs/charts/modern_dark_natal.svg" width="230" alt="Modern dark theme">
  <img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/v6/docs/charts/modern_black_and_white_natal.svg" width="230" alt="Modern black-and-white theme">
</p>

### Output controls

| Option | Purpose |
|---|---|
| `style="modern"` / `"classic"` | Select the wheel renderer |
| `theme` | Choose a built-in palette or leave CSS variables unthemed |
| `chart_language` / `language_pack` | Use one of ten languages or supply custom labels |
| `colors_settings`, `celestial_points_settings`, `aspects_settings` | Customize palette, glyphs, and aspect appearance |
| `glyph_size` | Select small, medium, or large point clusters on modern wheels |
| `show_zodiac_background_ring` | Toggle the colored zodiac annulus on modern wheels |
| `transparent_background=True` | Leave the SVG page unpainted |
| `auto_size=True` and `padding` | Fit the page to rendered content |
| `custom_title` | Replace the generated chart title |
| `minify=True` | Minify a saved SVG |
| `remove_css_variables=True` | Inline styles for SVG consumers without CSS-variable support |
| `external_view=True` | Use the external classic natal layout |
| `show_degree_indicators`, `show_aspect_icons` | Toggle classic-wheel degree and aspect symbols |
| `double_chart_aspect_grid_type` | Choose the `"list"` or `"table"` dual-chart aspect layout |
| `show_house_position_comparison` | Include point-to-house comparison tables on supported dual charts |
| `show_cusp_position_comparison` | Include reciprocal cusp placement tables |
| `show_diurnality` | Show or hide applicable diurnal/nocturnal labels |

Optional marks—`show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`, `show_relationship_score`, `show_ayanamsa_value`, and `show_polar_fallback_note`—default to `False`. A mark is silent when its source data has no applicable value.

See [Charts](https://www.kerykeion.net/content/docs/charts), [Theming](https://www.kerykeion.net/content/examples/theming), [Chart Language](https://www.kerykeion.net/content/examples/chart-language), [Glyph Sizes](https://www.kerykeion.net/content/examples/glyph-sizes), [Chart Marks](https://www.kerykeion.net/content/examples/chart-marks), and [Minimalist Charts](https://www.kerykeion.net/content/examples/minimalist-charts-and-aspect-table).

## Command-Line Interface

The CLI is a separate distribution, `kerykeion-cli`. It uses only the Python standard library beyond Kerykeion itself.

```bash
pip install --pre "kerykeion[cli]==6.0.0rc1"
# Or install it as an isolated tool:
uv tool install --prerelease=allow "kerykeion-cli==6.0.0rc1"
```

Save a subject profile and reuse it:

```console
$ kerykeion subject save john --name "John Lennon" --date 1940-10-09 --time 18:30 \
      --lat 53.4 --lng -2.9833 --tz Europe/London --offline
$ kerykeion natal -s john
$ kerykeion natal -s john -f svg -o /tmp/john.svg --theme dark
```

A terminal defaults to a text report. A pipeline defaults to JSON:

```console
$ kerykeion natal -s john | jq -r .sun.sign
Lib
```

The command tree covers charts, aspects, dominants, Moon context, relationship scores, predictive and traditional techniques, astronomical events, ephemeris data, transit timelines, stored subject profiles, and a guarded dispatcher for public factories:

```console
$ kerykeion call ProfectionsFactory.from_subject -s john -f json
$ kerykeion call --list
$ kerykeion info literals SiderealMode
$ kerykeion status --check
```

`call` dispatches only to names exported by `kerykeion.__all__`; arbitrary Python names are refused. See the [complete CLI reference](https://www.kerykeion.net/content/docs/cli).

For a commercial product that should not install Python, manage ephemeris data, or import the AGPL library, use the [hosted Astrologer API](https://rapidapi.com/gbattaglia/api/astrologer/pricing) instead.

## Documentation

- **Getting Started:** [kerykeion.net/content/docs](https://www.kerykeion.net/content/docs/)
- **Examples Gallery:** [kerykeion.net/content/examples](https://www.kerykeion.net/content/examples/)
- **Python API Reference:** [kerykeion.net/pydocs](https://www.kerykeion.net/pydocs/)
- **Migration Guide:** [v4/v5 to v6](https://www.kerykeion.net/content/docs/migration)
- **Cookbook:** [Practical recipes](https://www.kerykeion.net/content/docs/cookbook)
- **Schemas:** [Models and literals](https://www.kerykeion.net/content/docs/schemas)
- **FAQ:** [Troubleshooting and conventions](https://www.kerykeion.net/content/docs/faq)
- **Hosted API:** [Full API Documentation](https://www.kerykeion.net/content/astrologer-api/)

## Swiss Ephemeris Backend

Kerykeion uses **libephemeris 3.2.1** by default. To use the optional Swiss Ephemeris backend:

```bash
pip install --pre "kerykeion[swiss]==6.0.0rc1"
python -m kerykeion.swisseph_setup
export KERYKEION_BACKEND=swisseph
export KERYKEION_EPHE_PATH=~/.kerykeion/sweph
```

Swiss Ephemeris needs its `.se1` data files for full precision and `sefstars.txt` for fixed-star features. Without complete files, body and date availability can be narrower. See [Swiss Ephemeris Configuration](https://www.kerykeion.net/content/docs/swisseph_configuration).

Backend selection happens once at import. `KERYKEION_BACKEND` selects the engine, `KERYKEION_LEB_MODE` controls the libephemeris calculation mode, and `LIBEPHEMERIS_PRECISION` selects the active data tier. See [Ephemeris Backend](https://www.kerykeion.net/content/docs/ephemeris_backend).

## AI Agent Skill

Kerykeion includes a cross-platform [Agent Skill](https://agentskills.io/) that teaches coding agents the real v6 factories, models, configuration, and examples. During the v6 prerelease cycle, copy it from the current `v6` branch:

```bash
git clone --branch v6 --depth 1 https://github.com/g-battaglia/kerykeion.git
cd kerykeion

# Claude Code
cp -r skills/kerykeion /path/to/project/.claude/skills/kerykeion

# Codex
cp -r skills/kerykeion /path/to/project/.agents/skills/kerykeion

# Generic agentskills.io layout
cp -r skills/kerykeion /path/to/project/skills/kerykeion
```

Once v6 is the default branch, skills-aware tools can install it with:

```bash
npx skills add g-battaglia/kerykeion
```

The library wheel also includes `kerykeion/llms.txt`, a self-contained API guide. For runtime chart context, use `to_context()`.

## Development

Kerykeion uses `uv`, pytest, Ruff, MyPy, Pyright, and poethepoet. All project gates run locally; the repository intentionally has no GitHub Actions workflows.

```bash
git clone --branch v6 https://github.com/g-battaglia/kerykeion.git
cd kerykeion
uv sync --dev

uv run poe test:core
uv run poe check
uv run poe docs:check
uv run poe docs:snippets
uv run poe build:smoke
```

Test tiers correspond to installed ephemeris coverage. To run the full-range suite, install the extended kernel and select it explicitly:

```bash
LIBEPHEMERIS_PRECISION=extended uv run poe test:extended
```

- [Development Guide](https://github.com/g-battaglia/kerykeion/blob/v6/DEVELOPMENT.md)
- [Test Guide](https://github.com/g-battaglia/kerykeion/blob/v6/TEST.md)
- [Contributing Guide](https://github.com/g-battaglia/kerykeion/blob/v6/CONTRIBUTING.md)
- [Changelog](https://github.com/g-battaglia/kerykeion/blob/v6/CHANGELOG.md)

## License and Commercial Use

Kerykeion and the default libephemeris backend are distributed under **AGPL-3.0**. If your software imports or operates the library, review the AGPL's requirements for distribution and network use. See [LICENSE](https://github.com/g-battaglia/kerykeion/blob/v6/LICENSE) and [LICENSING.md](https://github.com/g-battaglia/kerykeion/blob/v6/LICENSING.md).

For commercial applications, SaaS products, mobile apps, or closed-source codebases, the recommended route is the hosted **Astrologer API**:

- **[Subscribe on RapidAPI](https://rapidapi.com/gbattaglia/api/astrologer/pricing)**
- **[Read the Full API Documentation](https://www.kerykeion.net/content/astrologer-api/)**

Your product calls an external service rather than importing Kerykeion directly. Subscription revenue directly funds the maintenance and continued development of this repository.

A direct commercial license for embedding Kerykeion can also be discussed with the copyright holder. The intended model is described in [COMMERCIAL-LICENSE.md](https://github.com/g-battaglia/kerykeion/blob/v6/COMMERCIAL-LICENSE.md); that document is currently marked as a draft. Contact [kerykeion.astrology@gmail.com](mailto:kerykeion.astrology@gmail.com?subject=Kerykeion%20Commercial%20License).

This section is a practical project summary, not legal advice. Consult qualified counsel for your specific use case.

## Contributing and Citation

Contributions are welcome. Open an issue or discussion before substantial work and follow the local gates in [CONTRIBUTING.md](https://github.com/g-battaglia/kerykeion/blob/v6/CONTRIBUTING.md). Contributions are accepted under the copyright-assignment terms documented there; authorship remains visible in project history and release notes.

[AstrologerStudio](https://www.astrologerstudio.com/) is a cloud astrology application built with Kerykeion and the Astrologer API.

For academic or published work, cite:

```text
Battaglia, G. (2025). Kerykeion: A Python Library for Astrological Calculations and Chart Generation.
https://github.com/g-battaglia/kerykeion
```

Questions and integration requests: [kerykeion.astrology@gmail.com](mailto:kerykeion.astrology@gmail.com?subject=Kerykeion).
