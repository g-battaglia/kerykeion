<h1 align="center">Kerykeion</h1>
<div align="center">
  <a href="https://github.com/g-battaglia/kerykeion" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/github/stars/g-battaglia/kerykeion.svg?logo=github" alt="GitHub stars"></a>
  <a href="https://github.com/g-battaglia/kerykeion" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/github/forks/g-battaglia/kerykeion.svg?logo=github" alt="GitHub forks"></a>
</div>
<div align="center">
  <a href="https://pepy.tech/project/kerykeion" target="_blank" rel="noopener noreferrer"><img src="https://static.pepy.tech/badge/kerykeion/month" alt="Monthly downloads"></a>
  <a href="https://pepy.tech/project/kerykeion" target="_blank" rel="noopener noreferrer"><img src="https://static.pepy.tech/badge/kerykeion/week" alt="Weekly downloads"></a>
  <a href="https://pepy.tech/project/kerykeion" target="_blank" rel="noopener noreferrer"><img src="https://static.pepy.tech/personalized-badge/kerykeion?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads/total" alt="Total downloads"></a>
</div>
<div align="center">
  <a href="https://pypi.org/project/kerykeion/" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/pypi/v/kerykeion?label=pypi%20package" alt="Package version"></a>
  <a href="https://pypi.org/project/kerykeion/" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/pypi/pyversions/kerykeion.svg" alt="Supported Python versions"></a>
  <a href="https://github.com/g-battaglia/kerykeion/blob/main/LICENSE" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/License-AGPL--3.0-blue.svg" alt="License: AGPL-3.0"></a>
  <a href="https://www.kerykeion.net/content/docs/" target="_blank" rel="noopener noreferrer"><img src="https://img.shields.io/badge/docs-kerykeion.net-blue.svg" alt="Documentation"></a>
</div>
<p align="center">⭐ Like this project? Star it on GitHub and help it grow! ⭐</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/docs/charts/modern_default_natal.svg" width="540" alt="Kerykeion modern natal chart">
</p>

Kerykeion is a Python library for astrological calculations and SVG charts. It calculates planetary positions, houses, aspects, returns, progressions, and other techniques listed in the [feature overview](#feature-overview).

The defaults use the tropical zodiac, Placidus houses, and apparent geocentric positions. Results are Pydantic models that you can inspect in Python, export as JSON, or serialize as XML for LLM context.

## Hosted API

**For every commercial project, including SaaS products, mobile apps, paid services, and closed-source software, use the hosted Astrologer API instead of integrating the local library or CLI.** Your app calls Kerykeion as an external service, with no Python or ephemeris infrastructure and no AGPL library in your codebase.

The API returns JSON calculations, SVG charts, and context for LLMs. For integration with coding agents, the <a href="https://github.com/g-battaglia/Astrologer-API/tree/v5/skills/astrologer-api" target="_blank" rel="noopener noreferrer">Astrologer API Agent Skill</a> documents authentication, endpoints, schemas, and examples. CLI access through Astrologer API is planned.

<p align="center">
  <strong><a href="https://rapidapi.com/gbattaglia/api/astrologer/pricing" target="_blank" rel="noopener noreferrer">Get API access on RapidAPI</a></strong>
  &nbsp;·&nbsp;
  <a href="https://www.kerykeion.net/content/astrologer-api/" target="_blank" rel="noopener noreferrer">Read the API docs</a>
</p>

Subscriptions directly support Kerykeion's continued development.

## Chart styles and themes

Kerykeion has two SVG chart styles, Modern and Classic, and three built-in themes. Click a preview to open the full-size PNG:

<table>
  <tr>
    <th></th>
    <th align="center">Classic theme</th>
    <th align="center">Dark theme</th>
    <th align="center">Black &amp; white</th>
  </tr>
  <tr>
    <th>Modern style</th>
    <td><a href="https://github.com/g-battaglia/kerykeion/blob/main/docs/charts/modern_classic_natal.png"><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/docs/charts/modern_classic_natal.png" width="250" alt="Modern chart with the classic theme"></a></td>
    <td><a href="https://github.com/g-battaglia/kerykeion/blob/main/docs/charts/modern_dark_natal.png"><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/docs/charts/modern_dark_natal.png" width="250" alt="Modern chart with the dark theme"></a></td>
    <td><a href="https://github.com/g-battaglia/kerykeion/blob/main/docs/charts/modern_black_and_white_natal.png"><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/docs/charts/modern_black_and_white_natal.png" width="250" alt="Modern chart with the black-and-white theme"></a></td>
  </tr>
  <tr>
    <th>Classic style</th>
    <td><a href="https://github.com/g-battaglia/kerykeion/blob/main/docs/charts/classic_default_natal.png"><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/docs/charts/classic_default_natal.png" width="250" alt="Classic chart with the classic theme"></a></td>
    <td><a href="https://github.com/g-battaglia/kerykeion/blob/main/docs/charts/classic_dark_natal.png"><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/docs/charts/classic_dark_natal.png" width="250" alt="Classic chart with the dark theme"></a></td>
    <td><a href="https://github.com/g-battaglia/kerykeion/blob/main/docs/charts/classic_black_and_white_natal.png"><img src="https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/main/docs/charts/classic_black_and_white_natal.png" width="250" alt="Classic chart with the black-and-white theme"></a></td>
  </tr>
</table>

Choose a style with `style="modern"` or `style="classic"`, and a theme with `theme="classic"`, `theme="dark"`, or `theme="black-and-white"`. See [Chart Rendering](#chart-rendering), <a href="https://www.kerykeion.net/content/examples/modern-charts" target="_blank" rel="noopener noreferrer">Modern Charts</a>, and <a href="https://www.kerykeion.net/content/examples/theming" target="_blank" rel="noopener noreferrer">Theming</a>.

## Table of contents

- [Hosted API](#hosted-api)
- [Chart styles and themes](#chart-styles-and-themes)
- [Installation](#installation)
- [Quick start](#quick-start)
- [How Kerykeion is organized](#how-kerykeion-is-organized)
- [Feature overview](#feature-overview)
  - [Subjects and chart types](#subjects-and-chart-types)
  - [Zodiacs, houses, perspectives, and points](#zodiacs-houses-perspectives-and-points)
  - [Aspects and chart analysis](#aspects-and-chart-analysis)
  - [Predictive and locational techniques](#predictive-and-locational-techniques)
  - [Sky events and time calculations](#sky-events-and-time-calculations)
  - [Traditional techniques](#traditional-techniques)
  - [Rendering, data, reports, and AI](#rendering-data-reports-and-ai)
- [Core workflows](#core-workflows)
  - [Build and inspect a subject](#build-and-inspect-a-subject)
  - [Generate an SVG chart](#generate-an-svg-chart)
  - [Synastry and transits](#synastry-and-transits)
  - [Solar and lunar returns](#solar-and-lunar-returns)
  - [Composite and Davison charts](#composite-and-davison-charts)
  - [Aspects and chart analysis](#aspects-and-chart-analysis-1)
  - [Reports and AI context](#reports-and-ai-context)
- [Calculation configuration](#calculation-configuration)
  - [Active points](#active-points)
  - [Fixed stars](#fixed-stars)
  - [Sidereal modes and custom ayanamsa](#sidereal-modes-and-custom-ayanamsa)
  - [House systems and polar latitudes](#house-systems-and-polar-latitudes)
  - [Observer perspectives](#observer-perspectives)
  - [Timezones, LMT, and calendars](#timezones-lmt-and-calendars)
  - [Precision, coverage, and provenance](#precision-coverage-and-provenance)
- [Chart rendering](#chart-rendering)
- [Command-line interface](#command-line-interface)
- [Documentation](#documentation)
  - [Troubleshooting](#troubleshooting)
- [Swiss Ephemeris backend](#swiss-ephemeris-backend)
- [AI agent skill](#ai-agent-skill)
- [Development](#development)
- [License and commercial use](#license-and-commercial-use)
- [Astrologer Studio](#astrologer-studio)
- [Contributing and citation](#contributing-and-citation)

## Installation

Kerykeion requires **Python 3.12 or newer**.

Install the current stable release:

```bash
pip install --upgrade "kerykeion"
```

This installs the Python library only. It does not install a shell command. The optional CLI is a separate distribution described in the [Command-Line Interface](#command-line-interface) section.

Before upgrading from v4 or v5, read the <a href="https://github.com/g-battaglia/kerykeion/blob/main/release_notes/v6.0.0.md" target="_blank" rel="noopener noreferrer">v6 release notes</a> and the <a href="https://www.kerykeion.net/content/docs/migration" target="_blank" rel="noopener noreferrer">migration guide</a>.

### Supported date ranges

The default reviewed ephemeris tier uses JPL DE440s and covers **1850–2150**. The upper bound is exclusive. Dates outside the active kernel raise `KerykeionException` rather than silently changing source.

Install a wider reviewed core through libephemeris:

```python
# doc-snippet: no-run - downloads ephemeris kernels
import libephemeris

libephemeris.download_leb_for_tier("medium")    # 1550–2650
libephemeris.download_leb_for_tier("extended")  # DE441, including BCE dates
```

The core tier controls the date range of the core bodies. Asteroids, exotics, and lunar apsides use separate data groups or runtime models and can have different coverage. See <a href="https://www.kerykeion.net/content/docs/ephemeris_backend" target="_blank" rel="noopener noreferrer">Ephemeris Backend</a> and <a href="https://www.kerykeion.net/content/docs/backend_precision_comparison" target="_blank" rel="noopener noreferrer">Backend Precision Comparison</a>.

## Quick start

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

Expected output (longitude abbreviated):

```text
Can 22.607...
.../charts_output/example-natal.svg
```

The second line is an absolute path based on your current working directory. Open the generated SVG in a browser to view the chart.

For offline calculations, set `online=False` and provide longitude, latitude, and an IANA timezone. For automatic location lookup, set `online=True`, provide `city` and `nation`, and configure a GeoNames username through `geonames_username` or `KERYKEION_GEONAMES_USERNAME`.

- <a href="https://www.kerykeion.net/content/docs/" target="_blank" rel="noopener noreferrer">Getting Started</a>
- <a href="https://www.kerykeion.net/content/examples/birth-data" target="_blank" rel="noopener noreferrer">Birth Data</a>
- <a href="https://www.kerykeion.net/content/docs/astrological_subject_factory" target="_blank" rel="noopener noreferrer">Astrological Subject Factory</a>
- <a href="https://www.kerykeion.net/content/examples/birth-chart" target="_blank" rel="noopener noreferrer">Birth Chart Example</a>

## How Kerykeion is organized

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

## Feature overview

The tables below list the calculation factories, configuration options, and output formats, with links to their documentation.

### Subjects and chart types

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Natal and event subjects | `AstrologicalSubjectFactory` | Planetary positions, houses, axes, lunar phase, configuration, and provenance for a local or UTC moment | <a href="https://www.kerykeion.net/content/docs/astrological_subject_factory" target="_blank" rel="noopener noreferrer">Subject Factory</a> |
| Structured chart data | `ChartDataFactory` | Typed data for natal, synastry, transit, return, composite, and progression charts | <a href="https://www.kerykeion.net/content/docs/chart_data_factory" target="_blank" rel="noopener noreferrer">Chart Data</a> |
| Natal charts | `ChartDataFactory.create_natal_chart_data` | Single-subject aspects, distributions, angularities, and stelliums | <a href="https://www.kerykeion.net/content/examples/birth-chart" target="_blank" rel="noopener noreferrer">Birth Chart</a> |
| Synastry charts | `ChartDataFactory.create_synastry_chart_data` | Cross-chart aspects, reciprocal house placement, and compatibility scoring | <a href="https://www.kerykeion.net/content/examples/synastry-chart" target="_blank" rel="noopener noreferrer">Synastry</a> |
| Transit charts | `ChartDataFactory.create_transit_chart_data` | Natal-to-transit aspects and projected house positions | <a href="https://www.kerykeion.net/content/examples/transit-chart" target="_blank" rel="noopener noreferrer">Transit Chart</a> |
| Solar and Lunar return charts | `PlanetaryReturnFactory` | Exact return moments and single- or dual-wheel return subjects | <a href="https://www.kerykeion.net/content/docs/planetary_return_factory" target="_blank" rel="noopener noreferrer">Planetary Returns</a> · <a href="https://www.kerykeion.net/content/examples/dual-return-chart" target="_blank" rel="noopener noreferrer">Example</a> |
| Heliocentric returns | `PlanetaryReturnFactory.next_heliocentric_return` | Returns of a planet to its natal heliocentric longitude | <a href="https://www.kerykeion.net/content/docs/planetary_return_factory" target="_blank" rel="noopener noreferrer">Planetary Returns</a> |
| Lunar-node crossings | `PlanetaryReturnFactory.next_lunar_node_crossing` | Exact moments when the Moon crosses its orbital node | <a href="https://www.kerykeion.net/content/docs/planetary_return_factory" target="_blank" rel="noopener noreferrer">Planetary Returns</a> |
| Midpoint composite charts | `CompositeSubjectFactory.get_midpoint_composite_subject_model` | Circular midpoint positions with explicit house-frame metadata | <a href="https://www.kerykeion.net/content/docs/composite_subject_factory" target="_blank" rel="noopener noreferrer">Composite Subjects</a> · <a href="https://www.kerykeion.net/content/examples/composite-chart" target="_blank" rel="noopener noreferrer">Example</a> |
| Davison charts | `CompositeSubjectFactory.get_davison_composite_subject_model` | The time-space midpoint recast as a real chart | <a href="https://www.kerykeion.net/content/docs/composite_subject_factory" target="_blank" rel="noopener noreferrer">Composite Subjects</a> |
| Relocated charts | `RelocatedChartFactory` | Natal planetary positions with houses, axes, sect, Vertex, and Lots recalculated for another location | <a href="https://www.kerykeion.net/content/docs/relocated_chart_factory" target="_blank" rel="noopener noreferrer">Relocated Charts</a> |
| Secondary-progressed charts | `SecondaryProgressionFactory` | Day-for-a-year progressed subjects and progressed-to-natal contacts | <a href="https://www.kerykeion.net/content/docs/secondary_progressions_factory" target="_blank" rel="noopener noreferrer">Secondary Progressions</a> |
| Solar-arc-directed charts | `SolarArcFactory` | A uniform progressed-Sun arc applied to natal points and angles | <a href="https://www.kerykeion.net/content/docs/solar_arc_factory" target="_blank" rel="noopener noreferrer">Solar Arc</a> |

### Zodiacs, houses, perspectives, and points

| Feature | Configuration/API | Description | Documentation |
|---|---|---|---|
| Tropical zodiac | `zodiac_type="Tropical"` | Default zodiac frame | <a href="https://www.kerykeion.net/content/docs/astrological_subject_factory" target="_blank" rel="noopener noreferrer">Subject Factory</a> |
| Sidereal zodiac | `zodiac_type="Sidereal"`, `sidereal_mode` | 47 named modes plus the custom `USER` mode | <a href="https://www.kerykeion.net/content/examples/sidereal-modes" target="_blank" rel="noopener noreferrer">Sidereal Modes</a> |
| Custom ayanamsa | `sidereal_mode="USER"`, `custom_ayanamsa_t0`, `custom_ayanamsa_ayan_t0` | User-defined reference epoch and offset | <a href="https://www.kerykeion.net/content/docs/schemas#siderealmode" target="_blank" rel="noopener noreferrer">Schemas</a> |
| Fixed reference frames | J2000, J1900, B1950, and related modes | Backend-supported sidereal reference-frame choices | <a href="https://www.kerykeion.net/content/docs/ephemeris_backend" target="_blank" rel="noopener noreferrer">Ephemeris Backend</a> |
| House systems | `houses_system_identifier` | Placidus by default and all systems supported by the active backend | <a href="https://www.kerykeion.net/content/examples/houses-systems" target="_blank" rel="noopener noreferrer">House Systems</a> |
| Polar house handling | `polar_house_fallbacks`, `coincident_house_cusps` | Machine-readable substitutions and zero-width cusp groups | <a href="https://www.kerykeion.net/content/docs/faq" target="_blank" rel="noopener noreferrer">FAQ</a> |
| Apparent and true geocentric | `perspective_type` | Standard apparent positions or true geometric positions | <a href="https://www.kerykeion.net/content/examples/perspective-type" target="_blank" rel="noopener noreferrer">Perspective Types</a> |
| Topocentric | `perspective_type="Topocentric"`, `altitude` | Observer-parallax positions at a specific location and elevation | <a href="https://www.kerykeion.net/content/examples/perspective-type" target="_blank" rel="noopener noreferrer">Perspective Types</a> |
| Heliocentric and barycentric | `perspective_type` | Sun-centered or Solar System barycenter positions | <a href="https://www.kerykeion.net/content/examples/perspective-type" target="_blank" rel="noopener noreferrer">Perspective Types</a> |
| Planetocentric perspectives | Selenocentric through Saturncentric | Positions observed from another supported planet | <a href="https://www.kerykeion.net/content/examples/perspective-type" target="_blank" rel="noopener noreferrer">Perspective Types</a> |
| Configurable point set | `active_points` | Compute only the planets, axes, nodes, Lots, and optional bodies required by the application | <a href="https://www.kerykeion.net/content/docs/active_points" target="_blank" rel="noopener noreferrer">Active Points</a> |
| Lunar nodes | True/Mean North and South nodes | Rahu/Ketu pairs with exact derived opposites | <a href="https://www.kerykeion.net/content/docs/active_points" target="_blank" rel="noopener noreferrer">Active Points</a> |
| Lilith, Priapus, and White Moon | Mean/True/Interpolated variants | Lunar apogee/perigee families and native Selena support where available | <a href="https://www.kerykeion.net/content/docs/active_points" target="_blank" rel="noopener noreferrer">Active Points</a> |
| Arabic Parts / Lots | Fortune, Spirit, Eros, and Faith | Sect-aware points with prerequisites calculated automatically | <a href="https://www.kerykeion.net/content/docs/active_points" target="_blank" rel="noopener noreferrer">Active Points</a> |
| Asteroids and centaurs | Chiron, Ceres, Pallas, Juno, Vesta, Pholus | Optional minor-body positions | <a href="https://www.kerykeion.net/content/docs/active_points" target="_blank" rel="noopener noreferrer">Active Points</a> |
| Trans-Neptunian objects | Eris, Sedna, Haumea, Makemake, Ixion, Orcus, Quaoar | Optional TNO positions with source/coverage metadata | <a href="https://www.kerykeion.net/content/docs/active_points" target="_blank" rel="noopener noreferrer">Active Points</a> |
| Uranian / Hamburg points | Cupido through Poseidon | Eight hypothetical points from runtime analytical models | <a href="https://www.kerykeion.net/content/docs/active_points" target="_blank" rel="noopener noreferrer">Active Points</a> |
| Fixed stars | `active_fixed_stars`, `subject.fixed_stars` | Opt-in catalog stars with longitude, latitude, speed, declination, and magnitude | <a href="https://www.kerykeion.net/content/docs/active_points" target="_blank" rel="noopener noreferrer">Active Points</a> |
| Dynamic star discovery | `FixedStarDiscoveryFactory` | Search the catalog and find prominent stars near subject positions | <a href="https://www.kerykeion.net/content/docs/fixed_star_discovery_factory" target="_blank" rel="noopener noreferrer">Fixed Star Discovery</a> |
| Online location resolution | GeoNames integration | Cached city, coordinate, and timezone lookup | <a href="https://www.kerykeion.net/content/docs/fetch_geonames" target="_blank" rel="noopener noreferrer">GeoNames</a> |

### Aspects and chart analysis

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Single- and dual-chart aspects | `AspectsFactory` | Longitudinal aspects within one chart or between two charts | <a href="https://www.kerykeion.net/content/docs/aspects" target="_blank" rel="noopener noreferrer">Aspects</a> |
| Declination aspects | `single_chart_declination_aspects`, `dual_chart_declination_aspects` | Parallels and contra-parallels | <a href="https://www.kerykeion.net/content/docs/aspects" target="_blank" rel="noopener noreferrer">Aspects</a> |
| Applying/separating motion | `AspectModel.aspect_movement` | Aspect movement derived from relative speed | <a href="https://www.kerykeion.net/content/docs/aspects" target="_blank" rel="noopener noreferrer">Aspects</a> |
| Custom orbs | `active_aspects`, `point_orb_adjustments` | Per-aspect, per-point, and aspect-specific orb policies | <a href="https://www.kerykeion.net/content/docs/aspects" target="_blank" rel="noopener noreferrer">Aspects</a> |
| House comparison | `HouseComparisonFactory` | Reciprocal placement of each subject's points in the other's houses | <a href="https://www.kerykeion.net/content/docs/house_comparison" target="_blank" rel="noopener noreferrer">House Comparison</a> · <a href="https://www.kerykeion.net/content/examples/house-comparison" target="_blank" rel="noopener noreferrer">Example</a> |
| Relationship score | `RelationshipScoreFactory` | Ciro Discepolo compatibility score with contributing aspects | <a href="https://www.kerykeion.net/content/docs/relationship_score_factory" target="_blank" rel="noopener noreferrer">Relationship Score</a> · <a href="https://www.kerykeion.net/content/examples/relationship-score" target="_blank" rel="noopener noreferrer">Example</a> |
| Element and quality distributions | `ChartDataFactory` | Pure count or configurable weighted analysis | <a href="https://www.kerykeion.net/content/docs/element_quality_distribution" target="_blank" rel="noopener noreferrer">Element and Quality</a> |
| Angularities and stelliums | `ChartDataModel.angularities`, `.stelliums` | Planets near axes and concentrations by house | <a href="https://www.kerykeion.net/content/docs/chart_data_factory" target="_blank" rel="noopener noreferrer">Chart Data</a> |
| Essential dignities | `calculate_dignities=True` | Domicile, exaltation, detriment, fall, triplicity, terms, and scores | <a href="https://www.kerykeion.net/content/docs/astrological_subject_factory" target="_blank" rel="noopener noreferrer">Subject Factory</a> |
| Vedic nakshatras | `calculate_nakshatra=True` | Nakshatra, pada, and Vimshottari lord with an explicit ayanamsa | <a href="https://www.kerykeion.net/content/docs/astrological_subject_factory" target="_blank" rel="noopener noreferrer">Subject Factory</a> |
| Motion state | point `speed`, `retrograde`, `motion_state` | Fast, average, slow, retrograde, and named station states | <a href="https://www.kerykeion.net/content/docs/schemas" target="_blank" rel="noopener noreferrer">Schemas</a> |
| Declination and out-of-bounds | point `declination`, `is_out_of_bounds` | OOB detection against the epoch's true obliquity | <a href="https://www.kerykeion.net/content/docs/schemas" target="_blank" rel="noopener noreferrer">Schemas</a> |
| Gauquelin sectors | `calculate_gauquelin=True` | 36-sector cusps and per-point sector values | <a href="https://www.kerykeion.net/content/docs/astrological_subject_factory" target="_blank" rel="noopener noreferrer">Subject Factory</a> |
| Local Space | `calculate_local_space=True` | Azimuth and altitude above the observer's horizon | <a href="https://www.kerykeion.net/content/docs/astrological_subject_factory" target="_blank" rel="noopener noreferrer">Subject Factory</a> |
| Nutation and obliquity | `calculate_nutation=True` | True/mean obliquity and nutation components | <a href="https://www.kerykeion.net/content/docs/schemas" target="_blank" rel="noopener noreferrer">Schemas</a> |
| Midpoint analysis | `MidpointFactory` | Pairwise midpoints, 90° dial positions, and third-point activations | <a href="https://www.kerykeion.net/content/docs/midpoint_factory" target="_blank" rel="noopener noreferrer">Midpoints</a> |
| Chart dominants | `DominantsFactory` | Modern, Almuten Figuris, elemental, or custom `DominantStrategy` scoring | <a href="https://www.kerykeion.net/content/docs/dominants_factory" target="_blank" rel="noopener noreferrer">Dominants</a> |

### Predictive and locational techniques

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Ephemeris time series | `EphemerisDataFactory` | Daily, hourly, or minutely samples as dictionaries, models, or full subjects | <a href="https://www.kerykeion.net/content/docs/ephemeris_data_factory" target="_blank" rel="noopener noreferrer">Ephemeris Data</a> · <a href="https://www.kerykeion.net/content/examples/ephemeris-data" target="_blank" rel="noopener noreferrer">Example</a> |
| Transit snapshots | `TransitsTimeRangeFactory.get_transit_moments` | Aspects at every supplied ephemeris sample, optionally including the full subject | <a href="https://www.kerykeion.net/content/docs/transits_time_range_factory" target="_blank" rel="noopener noreferrer">Transit Ranges</a> |
| Transit events | `TransitsTimeRangeFactory.get_transit_events` | Applying/exact/separating runs, retrograde multi-passes, and optional exact-moment refinement | <a href="https://www.kerykeion.net/content/docs/transits_time_range_factory" target="_blank" rel="noopener noreferrer">Transit Ranges</a> · <a href="https://www.kerykeion.net/content/examples/transits-time-range" target="_blank" rel="noopener noreferrer">Example</a> |
| Solar and Lunar returns | `PlanetaryReturnFactory` | Exact return searches in the natal zodiac/perspective, cast for the requested return location | <a href="https://www.kerykeion.net/content/docs/planetary_return_factory" target="_blank" rel="noopener noreferrer">Planetary Returns</a> |
| Secondary progressions | `SecondaryProgressionFactory` | Day-for-a-year subjects and contacts | <a href="https://www.kerykeion.net/content/docs/secondary_progressions_factory" target="_blank" rel="noopener noreferrer">Secondary Progressions</a> |
| Solar arc | `SolarArcFactory` | Directed points and directed-to-natal aspects | <a href="https://www.kerykeion.net/content/docs/solar_arc_factory" target="_blank" rel="noopener noreferrer">Solar Arc</a> |
| Primary directions | `PrimaryDirectionsFactory` | Placidus semi-arc directions with Ptolemy and Naibod rate keys | <a href="https://www.kerykeion.net/content/docs/primary_directions_factory" target="_blank" rel="noopener noreferrer">Primary Directions</a> |
| Astrocartography | `AstroCartographyFactory` | MC, IC, ASC, and DSC lines represented as world-coordinate sequences | <a href="https://www.kerykeion.net/content/docs/astro_cartography_factory" target="_blank" rel="noopener noreferrer">Astrocartography</a> |
| Relocation | `RelocatedChartFactory` | House and angle changes for a destination while natal planetary longitudes stay fixed | <a href="https://www.kerykeion.net/content/docs/relocated_chart_factory" target="_blank" rel="noopener noreferrer">Relocated Charts</a> |

Secondary-progressed houses follow the **Q2 / daily houses** convention: they are the real angles at the progressed ephemeris instant, not solar-arc-directed angles. Planetary progressions are unaffected by this choice. See <a href="https://www.kerykeion.net/content/docs/secondary_progressions_factory" target="_blank" rel="noopener noreferrer">Secondary Progressions</a>.

### Sky events and time calculations

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Detailed Moon phase | `MoonPhaseDetailsFactory` | Illumination, phase windows, rise/set, Sun data, upcoming phases, and eclipse context | <a href="https://www.kerykeion.net/content/docs/moon_phase_details_factory" target="_blank" rel="noopener noreferrer">Moon Phase Details</a> · <a href="https://www.kerykeion.net/content/examples/moon-phase-details" target="_blank" rel="noopener noreferrer">Example</a> |
| Exact lunations | `LunationFinderFactory` | New, first-quarter, full, and last-quarter moments across a range | <a href="https://www.kerykeion.net/content/docs/lunation_factory" target="_blank" rel="noopener noreferrer">Lunations</a> |
| Sunrise, sunset, and twilight | `SunTimesFactory` | Upper-limb rise/set, solar noon, day length, twilight, and polar day/night | <a href="https://www.kerykeion.net/content/docs/sun_times_factory" target="_blank" rel="noopener noreferrer">Sun Times</a> |
| Planetary hours | `PlanetaryHoursFactory` | Twelve unequal day and night hours with Chaldean rulers | <a href="https://www.kerykeion.net/content/docs/planetary_hours_factory" target="_blank" rel="noopener noreferrer">Planetary Hours</a> |
| Void-of-course Moon | `VoidOfCourseMoonFactory` | Current void state and complete VoC windows before ingress | <a href="https://www.kerykeion.net/content/docs/void_of_course_moon_factory" target="_blank" rel="noopener noreferrer">Void of Course</a> |
| Retrograde stations and periods | `RetrogradeStationFactory` | Exact SR/SD events and clipped retrograde spans | <a href="https://www.kerykeion.net/content/docs/retrograde_station_factory" target="_blank" rel="noopener noreferrer">Retrograde Stations</a> |
| Sign ingresses and stays | `SignIngressFactory` | Exact ingress moments and contiguous sign periods | <a href="https://www.kerykeion.net/content/docs/sign_ingress_factory" target="_blank" rel="noopener noreferrer">Sign Ingresses</a> |
| Mundane aspects | `MundaneAspectFactory` | Exact moving-body-to-moving-body aspects for aspectarians | <a href="https://www.kerykeion.net/content/docs/mundane_aspects_factory" target="_blank" rel="noopener noreferrer">Mundane Aspects</a> |
| Solar and Lunar eclipses | `EclipseFactory` | Global and local eclipse searches with structured circumstances | <a href="https://www.kerykeion.net/content/docs/eclipse_factory" target="_blank" rel="noopener noreferrer">Eclipses</a> |
| Planetary phenomena | `PlanetaryPhenomenaFactory` | Elongation, phase angle, magnitude, morning/evening status, and solar phase | <a href="https://www.kerykeion.net/content/docs/planetary_phenomena_factory" target="_blank" rel="noopener noreferrer">Planetary Phenomena</a> |
| Planetary nodes and apsides | `PlanetaryNodesFactory` | Ascending/descending nodes and periapsis/apoapsis | <a href="https://www.kerykeion.net/content/docs/planetary_nodes_factory" target="_blank" rel="noopener noreferrer">Planetary Nodes</a> |
| Heliacal events | `HeliacalFactory` | Heliacal risings and settings from observer and atmospheric inputs | <a href="https://www.kerykeion.net/content/docs/heliacal_factory" target="_blank" rel="noopener noreferrer">Heliacal Events</a> |
| Lunar occultations | `OccultationFactory` | Global or local occultation searches for supported bodies | <a href="https://www.kerykeion.net/content/docs/occultation_factory" target="_blank" rel="noopener noreferrer">Occultations</a> |

Sunrise and `subject.is_diurnal` intentionally answer different questions. Sunrise uses the apparent upper limb and standard refraction; diurnality uses the Sun's geometric center against the true horizon. See <a href="https://www.kerykeion.net/content/docs/sun_times_factory" target="_blank" rel="noopener noreferrer">Sun Times</a>.

### Traditional techniques

| Feature | Main API | Description | Documentation |
|---|---|---|---|
| Zodiacal releasing | `ZodiacalReleasingFactory` | L1–L4 aphesis periods from Fortune or Spirit, with loosing-of-the-bond and peak markers | <a href="https://www.kerykeion.net/content/docs/zodiacal_releasing_factory" target="_blank" rel="noopener noreferrer">Zodiacal Releasing</a> |
| Annual profections | `ProfectionsFactory` | Activated house/sign, Lord of the Year, and age cycle | <a href="https://www.kerykeion.net/content/docs/profections_factory" target="_blank" rel="noopener noreferrer">Profections</a> |
| Firdaria | `FirdariaFactory` | Sect-dependent Persian major and sub-period sequences | <a href="https://www.kerykeion.net/content/docs/firdaria_factory" target="_blank" rel="noopener noreferrer">Firdaria</a> |
| Mutual receptions | `MutualReceptionsFactory` | Domicile and exaltation receptions among classical planets | <a href="https://www.kerykeion.net/content/docs/receptions_factory" target="_blank" rel="noopener noreferrer">Mutual Receptions</a> |
| Horary indicators | `HoraryIndicatorsFactory` | Querent/quesited rulers, considerations before judgment, VoC state, and receptions | <a href="https://www.kerykeion.net/content/docs/horary_factory" target="_blank" rel="noopener noreferrer">Horary</a> |

### Rendering, data, reports, and AI

| Feature | Main API/configuration | Description | Documentation |
|---|---|---|---|
| SVG rendering | `ChartDrawer` | Natal, synastry, transit, return, composite, and progression charts | <a href="https://www.kerykeion.net/content/docs/charts" target="_blank" rel="noopener noreferrer">Charts</a> |
| Modern and classic styles | `style="modern"` / `"classic"` | Concentric modern layout or traditional classic wheel | <a href="https://www.kerykeion.net/content/examples/modern-charts" target="_blank" rel="noopener noreferrer">Modern Charts</a> |
| Themes | `theme` | Classic/light, dark, black-and-white, or unthemed CSS variables | <a href="https://www.kerykeion.net/content/examples/theming" target="_blank" rel="noopener noreferrer">Theming</a> |
| Ten chart languages | `chart_language`, `language_pack` | EN, FR, PT, ES, TR, RU, IT, CN, DE, HI, plus custom labels | <a href="https://www.kerykeion.net/content/examples/chart-language" target="_blank" rel="noopener noreferrer">Chart Language</a> |
| Glyph sizing and spreading | `glyph_size`, automatic decluttering | Small, medium, or large clusters with collision-aware placement | <a href="https://www.kerykeion.net/content/examples/glyph-sizes" target="_blank" rel="noopener noreferrer">Glyph Sizes</a> · <a href="https://www.kerykeion.net/content/docs/chart-glyphs" target="_blank" rel="noopener noreferrer">Glyph Reference</a> |
| Optional visual marks | `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`, `show_relationship_score`, `show_ayanamsa_value`, `show_polar_fallback_note` | Opt-in facts already carried by chart data | <a href="https://www.kerykeion.net/content/examples/chart-marks" target="_blank" rel="noopener noreferrer">Chart Marks</a> |
| Minimal SVG outputs | wheel-only and grid-only methods | Reusable wheel or aspect table without the full chart page | <a href="https://www.kerykeion.net/content/examples/minimalist-charts-and-aspect-table" target="_blank" rel="noopener noreferrer">Minimalist Charts</a> |
| External natal view | `external_view=True`, classic style | Classic natal wheel with planets outside the zodiac ring | <a href="https://www.kerykeion.net/content/examples/birth-chart" target="_blank" rel="noopener noreferrer">Birth Chart</a> |
| SVG portability controls | `minify`, `remove_css_variables`, `transparent_background`, `auto_size`, `custom_title` | Compact, standalone, embeddable, and custom-sized output | <a href="https://www.kerykeion.net/content/docs/charts" target="_blank" rel="noopener noreferrer">Charts</a> |
| Machine-readable SVG metadata | `kr:` attributes | Stable point, owner, house, projected-house, and ring identifiers | <a href="https://www.kerykeion.net/content/docs/chart_internals" target="_blank" rel="noopener noreferrer">Chart Internals</a> |
| Pydantic and JSON | `.model_dump()`, `.model_dump_json()` | Typed validation and structured serialization | <a href="https://www.kerykeion.net/content/docs/schemas" target="_blank" rel="noopener noreferrer">Schemas</a> |
| Text reports | `ReportGenerator` | Reports for subjects, chart data, Moon context, and traditional techniques | <a href="https://www.kerykeion.net/content/docs/report" target="_blank" rel="noopener noreferrer">Reports</a> · <a href="https://www.kerykeion.net/content/examples/report" target="_blank" rel="noopener noreferrer">Example</a> |
| LLM context | `to_context` | Escaped, non-qualitative XML for prompts and agents | <a href="https://www.kerykeion.net/content/docs/context_serializer" target="_blank" rel="noopener noreferrer">Context Serializer</a> |
| AI Agent Skill | `skills/kerykeion`, `kerykeion/llms.txt` | API-grounded instructions for coding agents | [AI Agent Skill](#ai-agent-skill) |
| Selectable backend | `BACKEND_NAME`, environment variables | Default libephemeris or optional Swiss Ephemeris | <a href="https://www.kerykeion.net/content/docs/ephemeris_backend" target="_blank" rel="noopener noreferrer">Ephemeris Backend</a> |

## Core workflows

The examples in this section build on each other. Run them in order to reuse `john`, `paul`, and `natal_data`.

### Build and inspect a subject

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

### Generate an SVG chart

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

Use `generate_svg_string()` when the SVG should stay in memory. Wheel-only and aspect-grid-only methods are available for custom layouts. See <a href="https://www.kerykeion.net/content/docs/charts" target="_blank" rel="noopener noreferrer">Charts</a>.

### Synastry and transits

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

### Solar and lunar returns

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

### Composite and Davison charts

```python
from kerykeion import CompositeSubjectFactory

composite_factory = CompositeSubjectFactory(john, paul, house_anchor="auto")
midpoint_composite = composite_factory.get_midpoint_composite_subject_model()
davison_composite = composite_factory.get_davison_composite_subject_model()

print(midpoint_composite.house_frame)
print(davison_composite.sun.abs_pos)
```

The midpoint composite is a symbolic midpoint model. The Davison result is a real ephemeris chart cast at the pair's midpoint time and place. See <a href="https://www.kerykeion.net/content/docs/composite_subject_factory" target="_blank" rel="noopener noreferrer">Composite Subject Factory</a>.

### Aspects and chart analysis

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

Use `single_chart_declination_aspects()` or `dual_chart_declination_aspects()` for parallels and contra-parallels. See <a href="https://www.kerykeion.net/content/docs/aspects" target="_blank" rel="noopener noreferrer">Aspects</a>.

### Reports and AI context

```python
from kerykeion import ReportGenerator, to_context

report = ReportGenerator(natal_data).generate_report(max_aspects=10)
xml_context = to_context(natal_data)

print(report[:500])
print(xml_context[:500])
```

`ReportGenerator` creates human-readable text. `to_context()` creates neutral XML intended as factual input to an LLM; it does not generate an astrological interpretation. See <a href="https://www.kerykeion.net/content/docs/report" target="_blank" rel="noopener noreferrer">Reports</a> and <a href="https://www.kerykeion.net/content/docs/context_serializer" target="_blank" rel="noopener noreferrer">Context Serializer</a>.

## Calculation configuration

### Active points

`active_points` is a calculation choice, not only a drawing filter. Request optional points when the subject is created. `ChartDataFactory` can filter points that already exist, but it does not go back and calculate omitted bodies.

This example requests both Mean and True lunar nodes and their opposites:

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

Presets for core, all, Uranian, and other point groups are documented in <a href="https://www.kerykeion.net/content/docs/active_points" target="_blank" rel="noopener noreferrer">Active Points</a> and <a href="https://www.kerykeion.net/content/examples/active-points" target="_blank" rel="noopener noreferrer">Active Points Examples</a>.

### Fixed stars

Request catalog stars by name with `active_fixed_stars`, separately from `active_points`:

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

Requested stars participate automatically in chart rendering and aspects. Discover catalog names through `FixedStarCatalog` or `FixedStarDiscoveryFactory`. See <a href="https://www.kerykeion.net/content/docs/fixed_star_discovery_factory" target="_blank" rel="noopener noreferrer">Fixed Star Discovery</a>.

### Sidereal modes and custom ayanamsa

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

See <a href="https://www.kerykeion.net/content/examples/sidereal-modes" target="_blank" rel="noopener noreferrer">Sidereal Modes</a> and <a href="https://www.kerykeion.net/content/docs/schemas#siderealmode" target="_blank" rel="noopener noreferrer">Schemas</a>.

### House systems and polar latitudes

Pass a one-character `houses_system_identifier`; Placidus (`"P"`) is the default. See <a href="https://www.kerykeion.net/content/examples/houses-systems" target="_blank" rel="noopener noreferrer">House Systems</a> for the supported list.

Some quadrant systems are mathematically undefined inside the polar circle. Kerykeion records any substitution in `subject.polar_house_fallbacks`; `houses_system_identifier` remains what was requested and `effective_houses_system_identifier` states what produced the cusps. Systems that legitimately place several cusps at one longitude expose those zero-width groups through `coincident_house_cusps`.

`ChartDrawer(..., show_polar_fallback_note=True)` can print the substitution on the chart.

### Observer perspectives

The default is `"Apparent Geocentric"`. Available alternatives include `"True Geocentric"`, `"Topocentric"`, `"Heliocentric"`, `"Barycentric"`, `"Selenocentric"`, and supported planetocentric frames.

Frame-specific rules matter:

- a center body has no position as seen from itself and is excluded;
- lunar nodes and lunar apogee variants are geocentric-only;
- Local Space, Gauquelin sectors, and OOB classification are only populated in frames where they are meaningful;
- two-chart operations require compatible frames;
- a Topocentric subject cannot be relocated by keeping its original planetary positions, because their parallax belongs to the original observer.

See <a href="https://www.kerykeion.net/content/examples/perspective-type" target="_blank" rel="noopener noreferrer">Perspective Types</a>.

### Timezones, LMT, and calendars

- Use an IANA zone such as `Europe/Rome`; a modern fixed UTC offset cannot reproduce historical or DST rules.
- If a modern wall time is repeated or skipped by a transition, `is_dst=True` selects the larger UTC offset and `is_dst=False` the smaller one. Leaving it unset raises instead of guessing.
- Before a zone has a recorded civil clock, a synthetic IANA `LMT` record is replaced by Local Mean Time at the supplied longitude. Named historical records such as RMT, BMT, KMT, and MMT remain authoritative.
- Naive daily `EphemerisDataFactory` inputs advance by local calendar days. Hourly and minutely series advance uniformly in UTC.
- CE birth-data components use the proleptic Gregorian calendar. BCE birth input uses astronomical year numbering (`0` = 1 BCE) and the Julian-calendar birth path.
- ISO event timestamps use the proleptic Gregorian calendar required by ISO 8601.

See <a href="https://www.kerykeion.net/content/docs/astrological_subject_factory" target="_blank" rel="noopener noreferrer">Astrological Subject Factory</a>, <a href="https://www.kerykeion.net/content/docs/ephemeris_data_factory" target="_blank" rel="noopener noreferrer">Ephemeris Data</a>, and <a href="https://www.kerykeion.net/content/docs/utilities" target="_blank" rel="noopener noreferrer">Utilities</a>.

### Precision, coverage, and provenance

High precision depends on body, date, active data tier, and source. A successful chart can contain points from different producers; applications should inspect the public metadata instead of assuming every optional body came from the core JPL kernel:

- `subject.ephemeris_warnings` lists optional points that no permitted source could produce;
- `point.source` identifies sources such as `LEB`, `Derived`, `Analytical`, or `Keplerian`;
- `point.precision_class` states the backend's classification;
- `point.ephemeris_coverage_start_jd` and `point.ephemeris_coverage_end_jd` expose the applicable window;
- `point.source_reviewed` reports whether that coverage record is reviewed.

`source="Keplerian"` is an approximation and is not ephemeris-grade. Geometrically derived points say `source="Derived"`. Uranian points are runtime analytical models and say `source="Analytical"`; they are not LEB data.

Sun or Moon calculation failure raises because a subject without either luminary is not a usable chart. Optional-body failures can return a valid subject with a machine-readable warning. See <a href="https://www.kerykeion.net/content/docs/backend_precision_comparison" target="_blank" rel="noopener noreferrer">Backend Precision Comparison</a>.

## Chart rendering

The modern concentric-ring renderer is the default. Use `style="classic"` for the classic wheel. All chart types support `theme="classic"`, `"dark"`, or `"black-and-white"`. Use `theme=None` to leave CSS variables unthemed.

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

The complete visual comparison is shown in [Chart Styles and Themes](#chart-styles-and-themes) near the top of this README.

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

The optional marks `show_motion_state`, `show_out_of_bounds`, `show_aspect_movement`, `show_relationship_score`, `show_ayanamsa_value`, and `show_polar_fallback_note` default to `False`. The renderer omits a mark when its source data has no applicable value.

See <a href="https://www.kerykeion.net/content/docs/charts" target="_blank" rel="noopener noreferrer">Charts</a>, <a href="https://www.kerykeion.net/content/examples/theming" target="_blank" rel="noopener noreferrer">Theming</a>, <a href="https://www.kerykeion.net/content/examples/chart-language" target="_blank" rel="noopener noreferrer">Chart Language</a>, <a href="https://www.kerykeion.net/content/examples/glyph-sizes" target="_blank" rel="noopener noreferrer">Glyph Sizes</a>, <a href="https://www.kerykeion.net/content/examples/chart-marks" target="_blank" rel="noopener noreferrer">Chart Marks</a>, and <a href="https://www.kerykeion.net/content/examples/minimalist-charts-and-aspect-table" target="_blank" rel="noopener noreferrer">Minimalist Charts</a>.

## Command-line interface

The core Kerykeion package is a Python library and does not install a shell command. Install the optional `kerykeion-cli` package for terminal use or automation. It has the same version as the library.

### Install the CLI

```bash
# Library and CLI in the current environment
pip install "kerykeion[cli]"

# Or install the CLI as an isolated tool
uv tool install "kerykeion-cli"
```

### CLI overview

The CLI exposes natal, synastry, transit, return, progression and midpoint-composite charts, together with aspects, traditional and predictive techniques, sky events, ephemeris series, transit timelines and saved subject profiles. It supports text, JSON, XML and SVG output. Davison charts remain a library feature (`CompositeSubjectFactory.get_davison_composite_subject_model`) and are reachable from the terminal through `kerykeion call`.

For automation, the CLI provides structured output and stable exit codes, with diagnostics separate from the output data. Scripts and coding agents can discover commands, reuse saved profiles, call public factories, and check the environment with `status --check`.

```console
$ kerykeion subject save john --name "John Lennon" --date 1940-10-09 --time 18:30 \
      --lat 53.4 --lng -2.9833 --tz Europe/London --offline
$ kerykeion natal -s john -f svg -o /tmp/john.svg --theme dark
$ kerykeion call ProfectionsFactory.from_subject -s john -f json
$ kerykeion status --check
```

For installation details, command coverage, output behavior and examples, read the <a href="https://github.com/g-battaglia/kerykeion/blob/main/cli/README.md" target="_blank" rel="noopener noreferrer">kerykeion-cli README</a>. The <a href="https://www.kerykeion.net/content/docs/cli" target="_blank" rel="noopener noreferrer">CLI documentation</a> provides the complete reference, while the <a href="https://github.com/g-battaglia/kerykeion/tree/main/skills/kerykeion-cli" target="_blank" rel="noopener noreferrer">CLI Agent Skill</a> contains tested instructions and recipes for coding agents.

For every commercial CLI workflow, use the <a href="https://rapidapi.com/gbattaglia/api/astrologer/pricing" target="_blank" rel="noopener noreferrer">hosted Astrologer API</a>. CLI access through Astrologer API is planned.

## Documentation

- **Getting Started:** <a href="https://www.kerykeion.net/content/docs/" target="_blank" rel="noopener noreferrer">kerykeion.net/content/docs</a>
- **Examples Gallery:** <a href="https://www.kerykeion.net/content/examples/" target="_blank" rel="noopener noreferrer">kerykeion.net/content/examples</a>
- **Python API Reference:** <a href="https://www.kerykeion.net/pydocs/" target="_blank" rel="noopener noreferrer">kerykeion.net/pydocs</a>
- **Migration Guide:** <a href="https://www.kerykeion.net/content/docs/migration" target="_blank" rel="noopener noreferrer">v4/v5 to v6</a>
- **Cookbook:** <a href="https://www.kerykeion.net/content/docs/cookbook" target="_blank" rel="noopener noreferrer">Practical recipes</a>
- **Schemas:** <a href="https://www.kerykeion.net/content/docs/schemas" target="_blank" rel="noopener noreferrer">Models and literals</a>
- **FAQ:** <a href="https://www.kerykeion.net/content/docs/faq" target="_blank" rel="noopener noreferrer">Troubleshooting and conventions</a>
- **Hosted API:** <a href="https://www.kerykeion.net/content/astrologer-api/" target="_blank" rel="noopener noreferrer">Full API Documentation</a>
- **Changelog:** <a href="https://github.com/g-battaglia/kerykeion/blob/main/CHANGELOG.md" target="_blank" rel="noopener noreferrer">CHANGELOG.md</a> and <a href="https://github.com/g-battaglia/kerykeion/blob/main/release_notes/v6.0.0.md" target="_blank" rel="noopener noreferrer">v6 release notes</a>

### Troubleshooting

Common first-run issues:

- `KerykeionException` for dates outside the active kernel (default tier covers **1850–2150**, upper bound exclusive). Install a wider tier or narrow the range; see [Supported date ranges](#supported-date-ranges).
- Ambiguous or nonexistent local times during timezone transitions need an explicit `is_dst` choice or a known UTC instant supplied through `from_iso_utc_time()`. The factory refuses to guess; see the <a href="https://www.kerykeion.net/content/docs/faq" target="_blank" rel="noopener noreferrer">FAQ</a> for offset-selection semantics.
- `online=True` without a GeoNames username fails. Either stay offline with explicit `lng`/`lat`/`tz_str` and `online=False`, or configure `geonames_username` / `KERYKEION_GEONAMES_USERNAME`. See the <a href="https://www.kerykeion.net/content/docs/faq" target="_blank" rel="noopener noreferrer">FAQ</a>.

## Swiss Ephemeris backend

Kerykeion uses **libephemeris 3.2.1** by default. To use the optional Swiss Ephemeris backend:

```bash
pip install "kerykeion[swiss]"
python -m kerykeion.swisseph_setup
export KERYKEION_BACKEND=swisseph
export KERYKEION_EPHE_PATH=~/.kerykeion/sweph
```

Swiss Ephemeris needs its `.se1` data files for full precision and `sefstars.txt` for fixed-star features. Without complete files, body and date availability can be narrower. See <a href="https://www.kerykeion.net/content/docs/swisseph_configuration" target="_blank" rel="noopener noreferrer">Swiss Ephemeris Configuration</a>.

Backend selection happens once at import. `KERYKEION_BACKEND` selects the engine, `KERYKEION_LEB_MODE` controls the libephemeris calculation mode, and `LIBEPHEMERIS_PRECISION` selects the active data tier. See <a href="https://www.kerykeion.net/content/docs/ephemeris_backend" target="_blank" rel="noopener noreferrer">Ephemeris Backend</a>.

## AI agent skill

The library includes a cross-platform <a href="https://agentskills.io/" target="_blank" rel="noopener noreferrer">Agent Skill</a> for the Kerykeion Python API. It covers v6 factories, models, configuration and examples, and is checked against the current release with executable documentation tests.

```bash
git clone --branch main --depth 1 https://github.com/g-battaglia/kerykeion.git
cd kerykeion

# Claude Code
cp -r skills/kerykeion /path/to/project/.claude/skills/kerykeion

# Codex
cp -r skills/kerykeion /path/to/project/.agents/skills/kerykeion

# Generic agentskills.io layout
cp -r skills/kerykeion /path/to/project/skills/kerykeion
```

Skills-aware tools can install the repository skill with:

```bash
npx skills add g-battaglia/kerykeion
```

The library wheel also includes `kerykeion/llms.txt`, a self-contained API guide. For runtime chart context, use `to_context()`. The separate CLI Agent Skill is documented in the [Command-Line Interface](#command-line-interface) section.

## Development

Kerykeion uses `uv`, pytest, Ruff, MyPy, Pyright, and poethepoet. All project gates run locally; the repository intentionally has no GitHub Actions workflows.

```bash
git clone --branch main https://github.com/g-battaglia/kerykeion.git
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

- <a href="https://github.com/g-battaglia/kerykeion/blob/main/DEVELOPMENT.md" target="_blank" rel="noopener noreferrer">Development Guide</a>
- <a href="https://github.com/g-battaglia/kerykeion/blob/main/TEST.md" target="_blank" rel="noopener noreferrer">Test Guide</a>
- <a href="https://github.com/g-battaglia/kerykeion/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener noreferrer">Contributing Guide</a>
- <a href="https://github.com/g-battaglia/kerykeion/blob/main/CHANGELOG.md" target="_blank" rel="noopener noreferrer">Changelog</a>

## License and commercial use

Kerykeion and the default libephemeris backend are distributed under **AGPL-3.0**. If your software imports or operates the library, review the AGPL's requirements for distribution and network use. See <a href="https://github.com/g-battaglia/kerykeion/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">LICENSE</a> and <a href="https://github.com/g-battaglia/kerykeion/blob/main/LICENSING.md" target="_blank" rel="noopener noreferrer">LICENSING.md</a>.

For every commercial application, SaaS product, mobile app, paid service, or closed-source codebase, use the hosted **Astrologer API**:

- **<a href="https://rapidapi.com/gbattaglia/api/astrologer/pricing" target="_blank" rel="noopener noreferrer">Subscribe on RapidAPI</a>**
- **<a href="https://www.kerykeion.net/content/astrologer-api/" target="_blank" rel="noopener noreferrer">Read the Full API Documentation</a>**

Your product calls an external service rather than importing Kerykeion directly. Subscription revenue directly funds the maintenance and continued development of this repository.

CLI access through Astrologer API is planned.

This section is a practical project summary, not legal advice. Consult qualified counsel for your specific use case.

## Astrologer Studio

<a href="https://www.astrologerstudio.com/" target="_blank" rel="noopener noreferrer">Astrologer Studio</a> is a browser application that uses Kerykeion and the hosted Astrologer API for astrological calculations and charts. It requires no local Python installation or ephemeris setup.

<p align="center">
  <strong><a href="https://www.astrologerstudio.com/" target="_blank" rel="noopener noreferrer">Open Astrologer Studio</a></strong>
</p>

## Contributing and citation

Contributions are welcome. Open an issue or discussion before substantial work and follow the local gates in <a href="https://github.com/g-battaglia/kerykeion/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener noreferrer">CONTRIBUTING.md</a>. Contributions are accepted under the copyright-assignment terms documented there; authorship remains visible in project history and release notes.

For academic or published work, cite:

```text
Battaglia, G. (2026). Kerykeion: A Python Library for Astrological Calculations and Chart Generation.
https://github.com/g-battaglia/kerykeion
```

Questions and integration requests: <a href="mailto:kerykeion.astrology@gmail.com?subject=Kerykeion" target="_blank" rel="noopener noreferrer">kerykeion.astrology@gmail.com</a>.
