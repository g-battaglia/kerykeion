---
title: 'Kerykeion Documentation'
description: 'Kerykeion is a Python library for astrology. Compute planetary positions, detect aspects, generate SVG charts, calculate synastry scores, and integrate with AI/LLMs. Powered by libephemeris (with optional Swiss Ephemeris backend).'
category: 'Getting Started'
tags: ['docs', 'kerykeion', 'python', 'astrology', 'getting-started']
order: 1
---

# Kerykeion Documentation

**Kerykeion** is a production-grade Python library for computational astrology. It provides high-precision planetary and house position calculations (via libephemeris, with optional Swiss Ephemeris backend), aspect detection, relationship scoring, transit forecasting, and professional SVG chart generation -- all with a clean, factory-based API and Pydantic models.

### What you can do with Kerykeion

- **Calculate** positions for 63+ celestial points (planets, asteroids, TNOs, fixed stars, Arabic parts)
- **Generate** professional SVG charts in 6 themes, 2 styles, and 10 languages
- **Analyze** aspects, element/quality distributions, and relationship compatibility
- **Forecast** with solar/lunar returns, transits over time ranges, and ephemeris data
- **Integrate** with AI/LLMs via structured XML context serialization
- **Export** everything as JSON via Pydantic models

> **Building a production app?** Skip the server setup with [**Astrologer API**](https://www.kerykeion.net/astrologer-api/subscribe) -- get charts, calculations, and AI interpretations via REST API. [Learn more](/content/docs/astrologer-api)

## Installation

```bash
pip install kerykeion
```

Requires **Python 3.12** or higher.

## Quick Start

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Create an astrological subject (offline mode with explicit coordinates)
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Doe", 1990, 7, 15, 10, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    online=False
)

# Access planetary positions
print(f"Sun: {subject.sun.sign} at {subject.sun.position:.2f}°")  # position = 0-30° within sign
print(f"Moon: {subject.moon.sign} at {subject.moon.position:.2f}°")
print(f"Ascendant: {subject.first_house.sign}")
print(f"Sun absolute position: {subject.sun.abs_pos:.2f}°")  # abs_pos = 0-360° on zodiac

# Generate an SVG chart
chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data)
svg_string = drawer.generate_svg_string()
```

**Output:**
```
Sun: Can at 22.61°
Moon: Ari at 21.21°
Ascendant: Vir
Sun absolute position: 112.61°
```

> **`position` vs `abs_pos`**: Every celestial point has two position fields. `position` is the degree within its sign (0-30°), while `abs_pos` is the absolute ecliptic longitude (0-360°). Use `position` for display and `abs_pos` for calculations.

For more examples, see the [Examples Gallery](/content/examples/).

---

## Getting Started

-   **[Complete Tutorial](/content/docs/tutorial)**: Build a full astrology application from scratch (recommended starting point).
-   **[Astrologer API](/content/docs/astrologer-api)**: Production-ready REST API for commercial projects.
-   **[Migration Guide (v4/v5 to v6)](/content/docs/migration)**: Step-by-step migration instructions for existing users.
-   **[Troubleshooting & FAQ](/content/docs/faq)**: Common issues and solutions.
-   **[Glossary](/content/docs/glossary)**: Astrological terms explained for developers.

## Core

-   **[Astrological Subject Factory](/content/docs/astrological_subject_factory)**: Creating astrological subjects from birth data, ISO timestamps, or current time.
-   **[Chart Data Factory](/content/docs/chart_data_factory)**: Calculating structured chart data for natal, synastry, transit, composite, and return charts.
-   **[Charts Module](/content/docs/charts)**: Rendering professional SVG charts with `ChartDrawer`.
-   **[Chart Glyphs](/content/docs/chart-glyphs)**: Visual reference for every glyph rendered in charts (planets, points, signs, aspects).
-   **[Report Module](/content/docs/report)**: Generating human-readable text reports.

## Analysis

-   **[Aspects](/content/docs/aspects)**: Calculating angular relationships between planets (11 ecliptic aspect types plus declination parallels, configurable orbs).
-   **[Composite Subject Factory](/content/docs/composite_subject_factory)**: Creating midpoint composite charts for relationships.
-   **[Relationship Score Factory](/content/docs/relationship_score_factory)**: Quantitative compatibility scoring (Ciro Discepolo method).
-   **[House Comparison](/content/docs/house_comparison)**: Bidirectional synastry house overlay analysis.
-   **[Element & Quality Distribution](/content/docs/element_quality_distribution)**: Analyzing element (Fire/Earth/Air/Water) and quality (Cardinal/Fixed/Mutable) balance.
-   **[Chart Dominants](/content/docs/dominants_factory)**: Dominant planet/sign/element/quality via modern, Almuten Figuris, or elemental schools.

## Forecasting

-   **[Planetary Return Factory](/content/docs/planetary_return_factory)**: Calculating solar and lunar returns with relocation support.
-   **[Moon Phase Details Factory](/content/docs/moon_phase_details_factory)**: Rich lunar phase context with illumination, upcoming phases, eclipses, and sun info.
-   **[Transits Time Range Factory](/content/docs/transits_time_range_factory)**: Tracking transit aspects over a date range.
-   **[Ephemeris Data Factory](/content/docs/ephemeris_data_factory)**: Generating time-series planetary position data.
-   **[Secondary Progressions](/content/docs/secondary_progressions_factory)**: Day-for-a-year progressions via `SecondaryProgressionFactory`.
-   **[Solar Arc Directions](/content/docs/solar_arc_factory)**: Solar arc directed charts via `SolarArcFactory`.
-   **[Primary Directions](/content/docs/primary_directions_factory)**: Placidus semi-arc method via `PrimaryDirectionsFactory`.
-   **[Zodiacal Releasing](/content/docs/zodiacal_releasing_factory)**: Hellenistic aphesis time-lord periods from the Lot of Fortune or Spirit.
-   **[Lunation Finder](/content/docs/lunation_factory)**: New/First-Quarter/Full/Last-Quarter Moons over a date range.
-   **[Retrograde Stations](/content/docs/retrograde_station_factory)**: Planetary retrograde/direct stations over a date range.
-   **[Sign Ingresses](/content/docs/sign_ingress_factory)**: Planet sign-change moments over a date range.
-   **[Mundane Aspects](/content/docs/mundane_aspects_factory)**: Exact transiting-to-transiting aspects for calendar aspectarians.
-   **[Void-of-Course Moon](/content/docs/void_of_course_moon_factory)**: Current void state and complete void windows over a range.
-   **[Sun Times](/content/docs/sun_times_factory)**: Sunrise, sunset, twilight, solar noon, and day length.
-   **[Planetary Hours](/content/docs/planetary_hours_factory)**: The 24 unequal Chaldean hours for a civil moment.

## Advanced Calculations

-   **[Eclipse Factory](/content/docs/eclipse_factory)**: Solar and lunar eclipse search (global or location-specific).
-   **[Planetary Phenomena](/content/docs/planetary_phenomena_factory)**: Elongation, phase, magnitude, morning/evening star status.
-   **[Planetary Nodes & Apsides](/content/docs/planetary_nodes_factory)**: Ascending/descending nodes and perihelion/aphelion.
-   **[Heliacal Risings & Settings](/content/docs/heliacal_factory)**: First/last visibility of planets relative to the Sun.
-   **[Occultation Factory](/content/docs/occultation_factory)**: Lunar occultation search (global or location-specific).
-   **[Relocated Charts](/content/docs/relocated_chart_factory)**: Chart relocation preserving planetary positions.
-   **[Fixed Star Discovery](/content/docs/fixed_star_discovery_factory)**: Dynamic fixed star conjunction detection.
-   **[Astro-Cartography](/content/docs/astro_cartography_factory)**: ACG planetary angular lines across the globe.
-   **[Midpoints](/content/docs/midpoint_factory)**: Cosmobiology 90° dial midpoint analysis with aspect activations.

## Reference

-   **[Types & Schemas](/content/docs/schemas)**: Complete Pydantic model and type reference.
-   **[Active Points](/content/docs/active_points)**: Reference for all 53+ celestial points and preset configurations.
-   **[Cookbook](/content/docs/cookbook)**: Practical recipes and code snippets for common tasks.
-   **[Constants](/content/docs/constants)**: Exhaustive lists of points, aspects, and preset constants.
-   **[Utilities](/content/docs/utilities)**: Helper functions for zodiac math, Julian Day, and SVG processing.
-   **[Settings](/content/docs/settings)**: Global configuration, translation utilities, and presets.
-   **[Chart Internals](/content/docs/chart_internals)**: Low-level SVG rendering functions (advanced).
-   **[Fetch Geonames](/content/docs/fetch_geonames)**: GeoNames API integration for location resolution.
-   **[Ephemeris Backend](/content/docs/ephemeris_backend)**: Backend configuration (libephemeris vs Swiss Ephemeris).
-   **[Swiss Ephemeris Configuration](/content/docs/swisseph_configuration)**: Optional Swiss Ephemeris backend setup, fixed-star catalog, and precision notes.
-   **[Legacy API](/content/docs/legacy)**: Migration info for v4/v5 users (removed in v6).

## Integration

-   **[AI Context Serializer](/content/docs/context_serializer)**: Serializing chart data to non-qualitative XML for LLM/AI consumption.
