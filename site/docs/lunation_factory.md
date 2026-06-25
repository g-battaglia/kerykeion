---
title: 'Lunation Finder'
description: 'Find New, First-Quarter, Full and Last-Quarter Moons within a date range.'
category: 'Forecasting'
tags: ['docs', 'lunation', 'moon', 'new moon', 'full moon', 'kerykeion']
order: 54
---

# Lunation Finder

The `LunationFinderFactory` finds **lunations** -- the New, First-Quarter, Full and Last-Quarter Moons -- within a date range. It is geocentric (no observer location needed) and returns results in chronological order. Dates are ISO strings treated as UTC.

## Basic Usage

```python
from kerykeion import LunationFinderFactory

result = LunationFinderFactory.from_iso_range("2026-01-01", "2026-12-31")
for lunation in result.lunations:
    print(lunation.iso_utc, lunation.phase)  # phase: new / first_quarter / full / last_quarter
```

Restrict to specific phases:

```python
fulls = LunationFinderFactory.from_iso_range("2026-01-01", "2026-12-31", phases=["full"])
```

## Methods

### `from_iso_range(start_date, end_date, phases=None)`

| Parameter    | Type                | Default | Description                                                            |
| :----------- | :------------------ | :------ | :-------------------------------------------------------------------- |
| `start_date` | str (ISO)           | --      | Range start, e.g. `"2026-01-01"` (a date-only value starts at 00:00 UTC). |
| `end_date`   | str (ISO)           | --      | Range end (a date-only value is widened through the end of that UTC day). |
| `phases`     | list[str] or None   | None    | Subset of `new` / `first_quarter` / `full` / `last_quarter`. Defaults to all four. |

**Returns:** `LunationsCollectionModel`

### `from_julian_day(start_jd, end_jd, phases=None)`

Same as above but with Julian Day (UT) bounds. **Raises** `KerykeionException` if the ephemeris backend fails mid-scan (e.g. a date outside the available range) and `ValueError` for an unknown phase name or an over-large range.

## Data Models

### `LunationsCollectionModel`

| Field        | Type   | Description                        |
| :----------- | :----- | :-------------------------------- |
| `lunations`  | list   | Chronologically ordered lunations. |

Each lunation item has:

| Field        | Type  | Description                                             |
| :----------- | :---- | :----------------------------------------------------- |
| `phase`      | str   | `new` / `first_quarter` / `full` / `last_quarter`.    |
| `iso_utc`    | str   | ISO 8601 UTC datetime of the exact phase.             |
| `julian_day` | float | Julian Day (UT) of the exact phase.                   |
| `sun`        | object | Sun position (sign + longitude) at the lunation.     |
| `moon`       | object | Moon position (sign + longitude) at the lunation.    |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
