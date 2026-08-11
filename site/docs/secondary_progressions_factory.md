---
title: 'Secondary Progressions'
description: 'Compute day-for-a-year secondary progressions and progressed-to-natal aspects for predictive astrology.'
category: 'Forecasting'
tags: ['docs', 'progressions', 'predictive', 'kerykeion']
order: 41
---

# Secondary Progressions

The `SecondaryProgressionFactory` computes **secondary progressions** -- the most widely used predictive technique in Western astrology. Its symbolism is "a day for a year": the chart calculated for the natal location N real days after birth represents the N-th year of the native's life.

The Sun progresses ~1 degree per year, the Moon ~12 degrees per year. The factory also calculates **progressed-to-natal aspects** for predictive timing.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, SecondaryProgressionFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)

# Simple: get the progressed subject model
progressed = SecondaryProgressionFactory.compute(
    natal,
    target_iso_utc_datetime="2026-04-25T00:00:00Z",
)

print(f"Progressed Sun: {progressed.sun.sign} at {progressed.sun.position:.2f}")
print(f"Progressed Moon: {progressed.moon.sign} at {progressed.moon.position:.2f}")
```

## Methods

### `compute(natal_subject, *, target_iso_utc_datetime, target_year, progressed_subject_name)`

Returns a progressed `AstrologicalSubjectModel` that works transparently with all downstream tools (aspects, charts, reports).

| Parameter                  | Type         | Default | Description                                    |
| :------------------------- | :----------- | :------ | :--------------------------------------------- |
| `natal_subject`            | AstrologicalSubjectModel | — | The natal chart                       |
| `target_iso_utc_datetime`  | str or None  | None    | Target moment in ISO UTC format                |
| `target_year`              | int or None  | None    | Shorthand: progress to January 1 of this year  |
| `progressed_subject_name`  | str or None  | None    | Custom name for the progressed subject         |

Provide either `target_iso_utc_datetime` or `target_year`, not both.

### `compute_full(natal_subject, *, ...)`

Returns a `SecondaryProgressionsResultModel` with the progressed subject **plus** progressed-to-natal aspects.

| Parameter                      | Type              | Default         | Description                                        |
| :----------------------------- | :---------------- | :-------------- | :------------------------------------------------- |
| `natal_subject`                | AstrologicalSubjectModel | —       | The natal chart                                    |
| `target_iso_utc_datetime`      | str or None       | None            | Target moment in ISO UTC format                    |
| `target_year`                  | int or None       | None            | Shorthand: progress to January 1 of this year      |
| `progressed_subject_name`      | str or None       | None            | Custom name for the progressed subject             |
| `active_points`                | Sequence[str] or None | None        | Points to include in aspect calculations           |
| `compute_aspects`              | bool              | True            | Whether to compute progressed-to-natal aspects     |
| `aspect_orb`                   | float             | 3.0             | Orb in degrees for aspect detection                |
| `aspects`                      | Sequence[str] or None | None        | Whitelist of aspect names (defaults to the 5 Ptolemaic majors: conjunction, opposition, trine, square, sextile) |
| `point_orb_adjustments`         | Mapping[str, float or Mapping[str, float]] or None | None   | Finite additive per-point orb adjustments; entries may be aspect-keyed with a `"*"` default |
| `point_orb_adjustment_strategy`| str               | "max_explicit" | `max_explicit`, `min_explicit`, `sum`, or `none`   |

```python
result = SecondaryProgressionFactory.compute_full(
    natal,
    target_iso_utc_datetime="2026-04-25T00:00:00Z",
    aspect_orb=1.5,
)

print(f"Ephemeris date: {result.ephemeris_iso_utc_datetime}")

for asp in result.progressed_to_natal_aspects:
    print(f"P.{asp.progressed_point} {asp.aspect} N.{asp.natal_point} (orb: {asp.orb:.2f})")
```

## Data Models

### `SecondaryProgressionsResultModel`

| Field                          | Type                          | Description                                  |
| :----------------------------- | :---------------------------- | :------------------------------------------- |
| `natal_name`                   | str                           | Name of the natal subject                    |
| `target_iso_utc_datetime`      | str                           | The real-world date requested                |
| `ephemeris_iso_utc_datetime`   | str                           | The actual ephemeris date looked up           |
| `progressed_subject`           | AstrologicalSubjectModel      | The full progressed chart                    |
| `progressed_to_natal_aspects`  | List[ProgressedToNatalAspectModel] | Cross-chart aspects                          |
| `progressed_points`            | List[ProgressedPointModel]        | Per-point natal-vs-progressed comparison     |

### `ProgressedPointModel`

| Field              | Type   | Description                                           |
| :----------------- | :----- | :---------------------------------------------------- |
| `name`             | str    | Planet name.                                          |
| `natal_abs_pos`    | float  | Natal absolute longitude.                             |
| `progressed_abs_pos` | float | Progressed absolute longitude.                       |
| `natal_sign`       | str    | Sign of the natal placement.                          |
| `progressed_sign`  | str    | Sign of the progressed placement.                     |
| `sign_changed`     | bool   | Whether the planet changed signs from natal to progressed. |

### `ProgressedToNatalAspectModel`

| Field              | Type  | Description                                |
| :----------------- | :---- | :----------------------------------------- |
| `progressed_point` | str   | Name of the progressed (moving) point      |
| `natal_point`      | str   | Name of the natal (receiving) point        |
| `progressed_abs_pos` | float | Progressed absolute longitude            |
| `natal_abs_pos`    | float | Natal absolute longitude                   |
| `aspect`           | str   | Aspect name (conjunction, trine, etc.)     |
| `aspect_degrees`   | int   | Exact aspect angle in degrees              |
| `orb`              | float | Orb (deviation from exact) in degrees      |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
