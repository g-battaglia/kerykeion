---
title: 'Firdaria (Planetary Periods)'
description: 'Compute the firdaria — Persian planetary time-lord periods based on the chart sect.'
category: 'Forecasting'
tags: ['docs', 'firdaria', 'time-lord', 'persian', 'traditional', 'kerykeion']
order: 61
---

# Firdaria (Planetary Periods)

**`FirdariaFactory`** computes the **firdaria**, a Persian time-lord technique that divides life into a fixed sequence of planetary periods. The sequence depends on the chart's sect: diurnal charts begin with the Sun (10 years), nocturnal charts begin with the Moon (9 years). The full 75-year cycle runs through the seven classical planets and the two lunar nodes.

Each major period (except the nodes) is subdivided into seven sub-periods, one per classical planet, beginning from the major lord itself and cycling through the Chaldean order.

All date arithmetic runs on Julian Days over the subject's local wall-clock anchor, so deep-BCE births are fully supported. A firdaria "year" is the Julian year of 365.25 days.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, FirdariaFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)

firdaria = FirdariaFactory.from_subject(subject, target_date="2026-06-04")
print(f"Sect: {'Day' if firdaria.is_diurnal else 'Night'}")
if firdaria.current:
    print(f"Current lord: {firdaria.current.lord} ({firdaria.current.years} years)")
if firdaria.current_sub:
    print(f"Current sub-lord: {firdaria.current_sub.lord}")
```

## Methods

### `from_subject(subject, *, target_date=None, life_cap_years=120)`

Build the firdaria timeline for a subject.

| Parameter        | Type                       | Default | Description                                                                                     |
| :--------------- | :------------------------- | :------ | :---------------------------------------------------------------------------------------------- |
| `subject`        | `AstrologicalSubjectModel` | --      | The natal chart. Requires a real sect (`is_diurnal` must be a boolean). Midpoint composites are rejected. |
| `target_date`    | str (ISO date/datetime) or None | None | Date the current period is resolved against. Astronomical year numbering accepted. When omitted, now in the subject's timezone. |
| `life_cap_years` | int                        | 120     | How far the timeline extends, in years of life.                                                 |

**Returns:** `FirdariaModel`

**Raises:** `KerykeionException` when the sect is unresolvable, the birth moment is missing, or `target_date` is unparseable.

## Data Models

### `FirdariaModel`

| Field         | Type                             | Description                                                      |
| :------------ | :------------------------------- | :--------------------------------------------------------------- |
| `is_diurnal`  | `bool`                           | Sect the sequence was chosen from.                               |
| `periods`     | `list[FirdariaPeriodModel]`      | Major periods from birth up to the life cap, in order.           |
| `current`     | `FirdariaPeriodModel \| None`    | The major period containing the target date, if any.             |
| `current_sub` | `FirdariaSubPeriodModel \| None` | The sub-period containing the target date, if any.               |

### `FirdariaPeriodModel`

| Field         | Type                              | Description                                                                  |
| :------------ | :-------------------------------- | :--------------------------------------------------------------------------- |
| `lord`        | `str`                             | Ruler of the period (classical planet or `North_Node` / `South_Node`).       |
| `years`       | `int`                             | Length of the period in firdaria years.                                       |
| `age_start`   | `int`                             | Age at which the period begins.                                              |
| `age_end`     | `int`                             | Age at which the period ends.                                                |
| `start`       | `str`                             | Local ISO datetime (`YYYY-MM-DDTHH:MM:SS`) the period begins.               |
| `end`         | `str`                             | Local ISO datetime the period ends.                                          |
| `sub_periods` | `list[FirdariaSubPeriodModel]`    | Seven sub-lord periods (empty for the nodes, which are not subdivided).      |

### `FirdariaSubPeriodModel`

| Field   | Type              | Description                                              |
| :------ | :---------------- | :------------------------------------------------------- |
| `lord`  | `ClassicalPlanet` | Planet ruling the sub-period.                            |
| `start` | `str`             | Local ISO datetime the sub-period begins.                |
| `end`   | `str`             | Local ISO datetime the sub-period ends.                  |

### Period Sequences

| Sect     | Sequence (lord, years)                                                                    |
| :------- | :---------------------------------------------------------------------------------------- |
| Diurnal  | Sun 10 → Venus 8 → Mercury 13 → Moon 9 → Saturn 11 → Jupiter 12 → Mars 7 → NN 3 → SN 2 |
| Nocturnal| Moon 9 → Saturn 11 → Jupiter 12 → Mars 7 → Sun 10 → Venus 8 → Mercury 13 → NN 3 → SN 2 |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
