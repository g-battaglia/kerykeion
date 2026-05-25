---
title: 'Relocated Chart Factory'
description: 'Relocate a natal chart to a different geographic location, recalculating houses and angles while preserving planetary positions.'
category: 'Advanced Calculations'
tags: ['docs', 'relocation', 'houses', 'angles', 'kerykeion']
order: 50
---

# Relocated Chart Factory

The `RelocatedChartFactory` creates a **relocated chart** from an existing natal chart. A relocated chart keeps all planetary positions identical to the natal chart but recalculates houses and angles (ASC, MC, DSC, IC) for a different geographic location.

This is equivalent to asking: "If I had been born at the same Universal Time but in a different city, which houses would my planets fall in?"

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, RelocatedChartFactory

# Create the original natal chart
natal = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)

# Relocate to New York
relocated = RelocatedChartFactory.relocate(
    natal,
    new_lat=40.7128,
    new_lng=-74.006,
    new_city="New York",
    new_nation="US",
)

print(f"Original Ascendant: {natal.first_house.sign}")
print(f"Relocated Ascendant: {relocated.first_house.sign}")

# Planetary positions are identical
print(f"Original Sun: {natal.sun.abs_pos:.4f}")
print(f"Relocated Sun: {relocated.sun.abs_pos:.4f}")  # Same value
```

## Methods

### `relocate(subject, new_lat, new_lng, new_city, new_nation, new_tz_str)`

Relocate a natal chart to a new geographic location.

| Parameter    | Type         | Default     | Description                              |
| :----------- | :----------- | :---------- | :--------------------------------------- |
| `subject`    | AstrologicalSubjectModel | -- | Original natal chart                |
| `new_lat`    | float        | --          | New latitude (north positive)            |
| `new_lng`    | float        | --          | New longitude (east positive)            |
| `new_city`   | str          | "Relocated" | City name for the relocated chart        |
| `new_nation` | str          | ""          | Country code                             |
| `new_tz_str` | str or None  | None        | Timezone (defaults to original)          |

**Returns:** `AstrologicalSubjectModel` with relocated houses and angles.

## What Changes

| Unchanged              | Recalculated                    |
| :--------------------- | :------------------------------ |
| All planetary positions | Ascendant (1st house cusp)     |
| Planetary speeds        | Medium Coeli (10th house cusp) |
| Aspects between planets | All 12 house cusps             |
| Fixed star positions    | Descendant, Imum Coeli         |
|                        | Planet-in-house assignments     |

## Use Cases

- **Relocation astrology**: understand how moving to a new city changes the emphasis of your chart
- **Travel planning**: check which houses are activated in a destination
- **Astro-cartography companion**: verify specific locations from ACG lines

## Combining with Charts

The relocated subject works with all downstream tools:

```python
from kerykeion import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from pathlib import Path

chart_data = ChartDataFactory.create_natal_chart_data(relocated)
drawer = ChartDrawer(chart_data=chart_data)
drawer.save_svg(output_path=Path("charts_output"), filename="relocated-new-york")
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
