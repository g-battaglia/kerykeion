---
title: 'Solar Arc Directions'
description: 'Compute solar arc directed charts and directed-to-natal aspects for predictive timing.'
category: 'Forecasting'
tags: ['docs', 'solar-arc', 'directions', 'predictive', 'kerykeion']
order: 42
---

# Solar Arc Directions

The `SolarArcFactory` computes **solar arc directions** -- a predictive technique that applies the Sun's progressed arc uniformly to every natal point. Every directed point advances at roughly 1 degree per year, preserving the natal chart's inter-point geometry while revealing yearly themes through contacts to natal positions.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, SolarArcFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)

result = SolarArcFactory.compute(
    natal,
    target_iso_utc_datetime="2026-04-25T00:00:00Z",
)

print(f"Solar arc: {result.solar_arc:.2f} degrees")

for dp in result.directed_points:
    print(f"{dp.name}: {dp.natal_sign} -> {dp.directed_sign} ({dp.directed_position:.2f})")
    if dp.sign_changed:
        print(f"  ** Sign change!")

for asp in result.directed_to_natal_aspects:
    print(f"D.{asp.directed_point} {asp.aspect} N.{asp.natal_point} (orb: {asp.orb:.2f})")
```

## Methods

### `compute(natal_subject, *, ...)`

Returns a `SolarArcSubjectModel` with the solar arc, directed points, and directed-to-natal aspects.

| Parameter                  | Type              | Default         | Description                                    |
| :------------------------- | :---------------- | :-------------- | :--------------------------------------------- |
| `natal_subject`            | AstrologicalSubjectModel | —       | The natal chart                                |
| `target_iso_utc_datetime`  | str or None       | None            | Target moment in ISO UTC format                |
| `target_year`              | int or None       | None            | Shorthand: direct to January 1 of this year    |
| `active_points`            | Sequence[str] or None | None        | Points to include in the directed picture      |
| `compute_aspects`          | bool              | True            | Whether to compute directed-to-natal aspects   |
| `aspect_orb`               | float             | 3.0             | Orb in degrees for aspect detection            |
| `aspects`                  | Sequence[str] or None | None        | Whitelist of aspect names                      |

### `compute_directed_subject(natal_subject, *, target_iso_utc_datetime=None, target_year=None)`

Returns a copy of `natal_subject` with every directable point advanced by the solar arc -- including the four angles (Asc/MC/Desc/IC), which are directed like the planets -- while only the house cusps stay on the natal frame. This is the form you want for a **biwheel** rendering: inner ring = natal, outer ring = directed.

```python
directed = SolarArcFactory.compute_directed_subject(natal_subject, target_year=2030)
print(directed.name)            # "<name> (directed)"
print(directed.sun.sign, f"{directed.sun.abs_pos:.2f}°")
```

| Parameter                  | Type                     | Default | Description                                  |
| :------------------------- | :----------------------- | :------ | :------------------------------------------- |
| `natal_subject`            | AstrologicalSubjectModel | —       | The natal chart                              |
| `target_iso_utc_datetime`  | str or None              | None    | Target moment in ISO UTC format             |
| `target_year`              | int or None              | None    | Shorthand: direct to January 1 of this year |

**Returns:** `AstrologicalSubjectModel` (the directed chart, named `"<name> (directed)"`).

## Data Models

### `SolarArcSubjectModel`

| Field                       | Type                          | Description                             |
| :-------------------------- | :---------------------------- | :-------------------------------------- |
| `natal_name`                | str                           | Name of the natal subject               |
| `target_iso_utc_datetime`   | str                           | The target real-world date              |
| `solar_arc`                 | float                         | Solar arc in degrees (0-360)            |
| `directed_points`           | List[SolarArcDirectedPointModel]   | All directed positions                  |
| `directed_to_natal_aspects` | List[SolarArcDirectedAspectModel]  | Active directed-to-natal aspects        |

### `SolarArcDirectedPointModel`

| Field              | Type  | Description                                          |
| :----------------- | :---- | :--------------------------------------------------- |
| `name`             | str   | Name of the natal point                              |
| `natal_abs_pos`    | float | Natal longitude (0-360)                              |
| `directed_abs_pos` | float | Directed longitude after applying the solar arc      |
| `natal_sign`       | str   | Natal sign code                                      |
| `directed_sign`    | str   | Directed sign code                                   |
| `directed_position`| float | Position within the directed sign (0-30)             |
| `sign_changed`     | bool  | True if the directed position is in a different sign |

### `SolarArcDirectedAspectModel`

| Field              | Type  | Description                                |
| :----------------- | :---- | :----------------------------------------- |
| `directed_point`   | str   | Name of the directed (moving) point        |
| `natal_point`      | str   | Name of the natal (receiving) point        |
| `directed_abs_pos` | float | Directed absolute longitude                |
| `natal_abs_pos`    | float | Natal absolute longitude                   |
| `aspect`           | str   | Aspect name                                |
| `aspect_degrees`   | int   | Exact aspect angle in degrees              |
| `orb`              | float | Orb in degrees                             |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
