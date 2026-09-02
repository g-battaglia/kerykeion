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

**Raises:** `KerykeionException` if the subject uses the `"Topocentric"`
perspective -- its planetary positions embed the parallax of the natal
observer, so they cannot be kept while the observer moves coherently. Re-create
the subject with the new coordinates instead. Also `KerykeionException` for a
geometrically impossible `|new_lat| > 90`;
`new_lng` is not rejected but wrapped into `[-180, 180)`, so `370` is read as
`10` east.

## What Changes

| Unchanged               | Recalculated                                                |
| :---------------------- | :---------------------------------------------------------- |
| All planetary positions | Ascendant, Medium Coeli, Descendant, Imum Coeli             |
| Planetary speeds        | All 12 house cusps                                          |
| Aspects between planets | Vertex and Anti-Vertex                                      |
| Fixed star longitudes   | Planet-in-house assignments, fixed stars and midpoints included |
| Midpoint longitudes     | `is_diurnal`, and the essential dignities that depend on sect |
|                         | The Ascendant-derived Arabic parts, with the re-selected sect |
|                         | `polar_house_fallbacks` and `coincident_house_cusps`         |
|                         | The local ISO datetime, when `new_tz_str` is given           |

Three per-point enrichments describe the natal horizon and cannot survive the
move, so they are reset to `None` rather than carried over stale: `azimuth`,
`altitude_above_horizon` and `gauquelin_sector` on every point (fixed stars
included), along with `gauquelin_sector_cusps` on the subject.

For a sidereal subject the house ring is computed tropically and then shifted
by the natal `ayanamsa_value`, the same value the natal cusps used, so the
relocated cusps land in the subject's own sidereal zodiac.

## Use Cases

- **Relocation astrology**: understand how moving to a new city changes the emphasis of your chart
- **Travel planning**: check which houses are activated in a destination
- **Astro-cartography companion**: verify specific locations from ACG lines

## Combining with Charts

The relocated subject works with all downstream tools:

```python
from kerykeion import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer
from pathlib import Path

chart_data = ChartDataFactory.create_natal_chart_data(relocated)
drawer = ChartDrawer(chart_data=chart_data)
drawer.save_svg(output_path=Path("charts_output"), filename="relocated-new-york")
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
