---
title: 'Kerykeion Documentation'
description: 'Kerykeion is a Python library for astrology. Compute planetary positions, detect aspects, generate SVG charts, calculate synastry scores, and integrate with AI/LLMs. Powered by the Swiss Ephemeris.'
category: 'Getting Started'
tags: ['docs', 'kerykeion', 'python', 'astrology', 'getting-started']
order: 1
---

# Kerykeion Documentation

**Kerykeion** is a production-grade Python library for computational astrology. It provides high-precision planetary and house position calculations (via the Swiss Ephemeris), aspect detection, relationship scoring, transit forecasting, and professional SVG chart generation -- all with a clean, factory-based API and Pydantic models.

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

Requires **Python 3.9** or higher.

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
Sun: Can at 22.54°
Moon: Sco at 15.32°
Ascendant: Vir
Sun absolute position: 112.54°
```

> **`position` vs `abs_pos`**: Every celestial point has two position fields. `position` is the degree within its sign (0-30°), while `abs_pos` is the absolute ecliptic longitude (0-360°). Use `position` for display and `abs_pos` for calculations.

For more examples, see the [Examples Gallery](/content/examples/).

---

## Getting Started

-   **[Complete Tutorial](/content/docs/tutorial)**: Build a full astrology application from scratch (recommended starting point).
-   **[Astrologer API](/content/docs/astrologer-api)**: Production-ready REST API for commercial projects.
-   **[Migration Guide (v4 to v5)](/content/docs/migration)**: Step-by-step migration instructions for existing users.
-   **[Troubleshooting & FAQ](/content/docs/faq)**: Common issues and solutions.
-   **[Glossary](/content/docs/glossary)**: Astrological terms explained for developers.

## Core

-   **[Astrological Subject Factory](/content/docs/astrological_subject_factory)**: Creating astrological subjects from birth data, ISO timestamps, or current time.
-   **[Chart Data Factory](/content/docs/chart_data_factory)**: Calculating structured chart data for natal, synastry, transit, composite, and return charts.
-   **[Charts Module](/content/docs/charts)**: Rendering professional SVG charts with `ChartDrawer`.
-   **[Report Module](/content/docs/report)**: Generating human-readable text reports.

## Analysis

-   **[Aspects](/content/docs/aspects)**: Calculating angular relationships between planets (11 aspect types, configurable orbs).
-   **[Composite Subject Factory](/content/docs/composite_subject_factory)**: Creating midpoint composite charts for relationships.
-   **[Relationship Score Factory](/content/docs/relationship_score_factory)**: Quantitative compatibility scoring (Ciro Discepolo method).
-   **[House Comparison](/content/docs/house_comparison)**: Bidirectional synastry house overlay analysis.
-   **[Element & Quality Distribution](/content/docs/element_quality_distribution)**: Analyzing element (Fire/Earth/Air/Water) and quality (Cardinal/Fixed/Mutable) balance.

## Forecasting

-   **[Planetary Return Factory](/content/docs/planetary_return_factory)**: Calculating solar and lunar returns with relocation support.
-   **[Moon Phase Details Factory](/content/docs/moon_phase_details_factory)**: Rich lunar phase context with illumination, upcoming phases, eclipses, and sun info.
-   **[Transits Time Range Factory](/content/docs/transits_time_range_factory)**: Tracking transit aspects over a date range.
-   **[Ephemeris Data Factory](/content/docs/ephemeris_data_factory)**: Generating time-series planetary position data.

## Reference

-   **[Types & Schemas](/content/docs/schemas)**: Complete Pydantic model and type reference.
-   **[Active Points](/content/docs/active_points)**: Reference for all 63 celestial points and preset configurations.
-   **[Cookbook](/content/docs/cookbook)**: Practical recipes and code snippets for common tasks.
-   **[Constants](/content/docs/constants)**: Exhaustive lists of points, aspects, and preset constants.
-   **[Utilities](/content/docs/utilities)**: Helper functions for zodiac math, Julian Day, and SVG processing.
-   **[Settings](/content/docs/settings)**: Global configuration, translation utilities, and presets.
-   **[Chart Internals](/content/docs/chart_internals)**: Low-level SVG rendering functions (advanced).
-   **[Fetch Geonames](/content/docs/fetch_geonames)**: GeoNames API integration for location resolution.
-   **[Legacy API](/content/docs/legacy)**: Backward compatibility layer for v4 users.

## Integration

-   **[AI Context Serializer](/content/docs/context_serializer)**: Serializing chart data to non-qualitative XML for LLM/AI consumption.
