---
title: 'Index'
description: 'Welcome to the Kerykeion documentation'
category: 'Getting Started'
order: 1
---

# Kerykeion Documentation

Welcome to the Kerykeion documentation. Kerykeion is a Python library for astrology that computes planetary and house positions, detects aspects, and generates SVG charts.

> **Building a production app?** Skip the server setup with [**Astrologer API**](https://www.kerykeion.net/astrologer-api/subscribe) - get charts, calculations, and AI interpretations via REST API. [Learn more →](/content/docs/astrologer-api)

## Installation

```bash
pip install kerykeion
```

Requires **Python 3.9** or higher.

## Quick Start

```python
from kerykeion import AstrologicalSubjectFactory

# Create an astrological subject (offline mode with explicit coordinates)
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Doe", 1990, 7, 15, 10, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    online=False
)

# Access planetary positions
print(f"Sun: {subject.sun.sign} at {subject.sun.position:.2f}°")
print(f"Moon: {subject.moon.sign} at {subject.moon.position:.2f}°")
print(f"Ascendant: {subject.first_house.sign}")
```

**Output:**
```
Sun: Can at 22.54°
Moon: Sco at 15.32°
Ascendant: Vir
```

For more examples, see the [Examples Gallery](/content/examples/).

---

## Getting Started

-   **[Astrologer API](/content/docs/astrologer-api)**: Production-ready REST API for commercial projects.
-   **[Migration Guide (v4 to v5)](/content/docs/migration)**: Step-by-step migration instructions for existing users.
-   **[Complete Tutorial](/content/docs/tutorial)**: Build a full astrology application from scratch.
-   **[Troubleshooting & FAQ](/content/docs/faq)**: Common issues and solutions.
-   **[Glossary](/content/docs/glossary)**: Astrological terms explained.

## Core

-   **[Astrological Subject Factory](/content/docs/astrological_subject_factory)**: Creating astrological subjects from birth data or time.
-   **[Chart Data Factory](/content/docs/chart_data_factory)**: Calculating chart data for various chart types.
-   **[Charts Module](/content/docs/charts)**: Visualizing charts using `ChartDrawer`.
-   **[Report Module](/content/docs/report)**: Generating astrological reports.

## Analysis

-   **[Aspects](/content/docs/aspects)**: Understanding astrological aspects.
-   **[Composite Subject Factory](/content/docs/composite_subject_factory)**: Creating composite charts for relationships.
-   **[Relationship Score Factory](/content/docs/relationship_score_factory)**: Evaluating compatibility scores.
-   **[House Comparison](/content/docs/house_comparison)**: Comparing house placements between charts.
-   **[Element & Quality Distribution](/content/docs/element_quality_distribution)**: Analyzing element and quality balance.

## Forecasting

-   **[Planetary Return Factory](/content/docs/planetary_return_factory)**: Calculating solar and lunar returns.
-   **[Transits Time Range Factory](/content/docs/transits_time_range_factory)**: Analyzing transits over a specific time range.
-   **[Ephemeris Data Factory](/content/docs/ephemeris_data_factory)**: Generating ephemeris data.

## Reference

-   **[Types & Schemas](/content/docs/schemas)**: Core data models and type definitions.
-   **[Constants](/content/docs/constants)**: Constants for planets, signs, and aspects.
-   **[Utilities](/content/docs/utilities)**: General utility functions.
-   **[Settings](/content/docs/settings)**: Global configuration.
-   **[Fetch Geonames](/content/docs/fetch_geonames)**: Fetching location data from GeoNames.
-   **[Legacy API](/content/docs/legacy)**: Backward compatibility layer for v4 users.

## Integration

-   **[AI Context Serializer](/content/docs/context_serializer)**: Serializing chart context for AI/LLM integration.
