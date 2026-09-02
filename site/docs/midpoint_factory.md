---
title: 'Midpoint Factory'
description: 'Compute cosmobiology midpoints and 90-degree dial positions with aspect activations.'
category: 'Advanced Calculations'
tags: ['docs', 'midpoints', 'cosmobiology', 'uranian', 'kerykeion']
order: 44
---

# Midpoint Factory

The `MidpointFactory` computes the **midpoint** of every unordered pair of active points in a chart. Midpoints are central to **cosmobiology** (Ebertin) and **Uranian/Hamburg-school** astrology, where they are treated as sensitive axes: when a third point crosses one, the energies of the defining pair are activated.

## What It Computes

- The midpoint of every pair of active points (shorter arc convention)
- The 90-degree modulus position for cosmobiology dial work
- Optional aspect activations: which third points form aspects with each midpoint

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, MidpointFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)

midpoints = MidpointFactory.compute(subject)

for m in midpoints:
    print(f"{m.point_a}/{m.point_b}: {m.midpoint_position:.2f} {m.midpoint_sign}"
          f" (90 dial: {m.midpoint_modulus_90:.2f})")
    for a in m.aspects_to_midpoint:
        print(f"   activated by {a.point_name} ({a.aspect}, orb {a.orb:.2f})")
```

## Methods

### `compute(subject, *, active_points, compute_aspects, aspect_orb, aspects)`

Compute every pairwise midpoint and (optionally) aspect activations.

| Parameter        | Type              | Default | Description                                           |
| :--------------- | :---------------- | :------ | :---------------------------------------------------- |
| `subject`        | AstrologicalSubjectModel | --  | The natal/event chart to analyse                      |
| `active_points`  | Sequence[str] or None | None | Points to use as midpoint constituents. Defaults to `DEFAULT_PREDICTIVE_POINTS`: Sun through Pluto, True North Lunar Node, Chiron, Ascendant and Medium Coeli. Names the subject does not carry are skipped, and fewer than two resolved points give an empty list |
| `compute_aspects`| bool              | True    | Also compute third-point aspect activations           |
| `aspect_orb`     | float             | 1.0     | Orb in degrees for aspect-to-midpoint detection       |
| `aspects`        | Sequence[str] or None | None | Whitelist of aspect names (defaults to all configured) |

**Returns:** `List[MidpointModel]`

### `compute_active_midpoint_points(subject, pair_names)`

Materialize midpoints as `KerykeionPointModel` entries so the chart drawer can render them like ordinary active points.

| Parameter    | Type           | Description                                              |
| :----------- | :------------- | :------------------------------------------------------- |
| `subject`    | AstrologicalSubjectModel | The natal subject                          |
| `pair_names` | Sequence[str]  | Pair identifiers in `"A_B"` form (e.g. `"Sun_Moon"`)    |

**Returns:** `List[KerykeionPointModel]`, one per resolved pair, named
`"A_B_Midpoint"` with `point_type="Midpoint"` and sign, element, quality and
house derived from the midpoint longitude on the shorter arc. Both sides of a
pair must resolve in the subject's own `active_points`: a pair that does not
is skipped and logged as a warning. A repeated pair, or the reversed `"B_A"`
twin of one already emitted, is skipped too — the first occurrence wins.

## Data Models

### `MidpointModel`

| Field                 | Type                      | Description                                           |
| :-------------------- | :------------------------ | :---------------------------------------------------- |
| `point_a`             | str                       | Name of the first point                               |
| `point_b`             | str                       | Name of the second point                              |
| `point_a_abs_pos`     | float                     | Absolute longitude of point A (0-360)                 |
| `point_b_abs_pos`     | float                     | Absolute longitude of point B (0-360)                 |
| `midpoint_abs_pos`    | float                     | Midpoint longitude on the shorter arc (0-360)         |
| `midpoint_sign`       | str                       | Three-letter zodiac sign code (Ari, Tau, ...)         |
| `midpoint_position`   | float                     | Position within the sign in degrees (0-30)            |
| `midpoint_modulus_90` | float                     | 90-degree dial position (longitude % 90)              |
| `aspects_to_midpoint` | List[MidpointAspectModel] | Third points that aspect this midpoint                |

### `MidpointAspectModel`

| Field            | Type  | Description                                           |
| :--------------- | :---- | :---------------------------------------------------- |
| `point_name`     | str   | Name of the third point that aspects the midpoint     |
| `point_abs_pos`  | float | Absolute zodiacal longitude of the third point        |
| `aspect`         | str   | Aspect name (conjunction, trine, square, ...)         |
| `aspect_degrees` | int   | Exact aspect angle in degrees                         |
| `orb`            | float | Orb (deviation from exact aspect) in degrees          |

## 90-Degree Dial

The `midpoint_modulus_90` field converts the midpoint longitude to the 90-degree dial used in cosmobiology. This reduces the full 360-degree circle to a 90-degree range, making it easier to spot hard aspects (conjunction, square, opposition) as conjunctions on the dial.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
