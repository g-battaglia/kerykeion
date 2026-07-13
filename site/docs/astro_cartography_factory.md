---
title: 'Astro-Cartography Factory'
description: 'Compute astro-cartography (ACG) planetary lines showing where each planet is angular across the globe.'
category: 'Advanced Calculations'
tags: ['docs', 'astro-cartography', 'acg', 'relocation', 'kerykeion']
order: 45
---

# Astro-Cartography Factory

The `AstroCartographyFactory` computes **Astro-Cartography (ACG) lines** -- geographic coordinates where each planet's angular lines (Ascendant, Descendant, MC, IC) fall across the globe for a given birth moment. The output can be plotted on a map.

## How It Works

For a fixed Julian Day, each planet's true equatorial coordinates (right ascension and declination) are computed once. MC/IC lines are derived analytically: the body culminates on the meridian at geographic longitude `RA - GST` (MC), and anti-culminates on the antimeridian (IC). ASC/DSC lines are obtained by solving the horizon equation `cos H = -tan(lat) * tan(declination)` at each sampled latitude -- latitudes where the body is circumpolar (or never rises) have no line point. Lines are computed in mundo, so they are identical for tropical and sidereal charts of the same instant.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, AstroCartographyFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)

lines = AstroCartographyFactory.compute(subject, step=2)

for line in lines:
    print(f"{line.planet} {line.line_type}: {len(line.points)} points")
```

## Methods

### `compute(subject, *, step, tolerance, lat_range, planets)`

Compute ACG lines for a natal chart.

| Parameter   | Type                     | Default    | Description                                              |
| :---------- | :----------------------- | :--------- | :------------------------------------------------------- |
| `subject`   | AstrologicalSubjectModel | --         | A natal chart subject with a finite Julian Day            |
| `step`      | float                    | 1.0        | Finite positive latitude sampling step; the projected grid is capped at 250,000 line points |
| `tolerance` | float or None            | None       | Unused since v6 (horizon equation is solved exactly); kept for backward compatibility |
| `lat_range` | tuple[float, float]      | (-66, 66)  | Finite ordered bounds within -90..+90 degrees            |
| `planets`   | list[str] or tuple[str, ...] or None | None | Supported planet names (defaults to Sun through Pluto); malformed or unknown entries raise `KerykeionException` |

**Returns:** `List[ACGLineModel]` -- one per planet per line type.

## Data Models

### `ACGLineModel`

| Field       | Type                                  | Description                              |
| :---------- | :------------------------------------ | :--------------------------------------- |
| `planet`    | str                                   | Planet name                              |
| `line_type` | Literal["ASC", "DSC", "MC", "IC"]     | Angular line type                        |
| `points`    | List[ACGLinePointModel]                    | Geographic coordinates of the line       |

### `ACGLinePointModel`

| Field       | Type  | Description                              |
| :---------- | :---- | :--------------------------------------- |
| `longitude` | float | Geographic longitude (-180 to +180)      |
| `latitude`  | float | Geographic latitude (-90 to +90)         |

## Customization

### Higher Resolution

```python
lines = AstroCartographyFactory.compute(subject, step=0.5)
```

### Specific Planets

```python
lines = AstroCartographyFactory.compute(
    subject,
    planets=["Sun", "Moon", "Jupiter", "Saturn"]
)
```

### Extended Latitude Range

```python
lines = AstroCartographyFactory.compute(
    subject,
    lat_range=(-80, 80)
)
```

## Line Types

- **ASC (Ascendant)**: where the planet rises -- themes of self-expression and new beginnings
- **DSC (Descendant)**: where the planet sets -- themes of relationships and partnerships
- **MC (Medium Coeli)**: where the planet culminates -- themes of career and public life
- **IC (Imum Coeli)**: where the planet is at the nadir -- themes of home and inner life

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
