---
title: 'Profections (Annual)'
description: 'Compute annual profections — a traditional timing technique that activates one house per year of life.'
category: 'Forecasting'
tags: ['docs', 'profections', 'annual profections', 'time-lord', 'traditional', 'kerykeion']
order: 60
---

# Profections (Annual)

**`ProfectionsFactory`** computes annual profections, a traditional timing technique that activates one house per year of life. Starting from the 1st house at birth, the profected house advances one house each birthday, cycling every 12 years. The sign on the activated cusp determines the **Lord of the Year** — the traditional domicile ruler of that sign.

The profection timeline follows the subject's own house system: a whole-sign chart profects through whole signs by construction, while a Placidus chart profects through Placidus cusps.

BCE births are fully supported (astronomical year numbering), and birthday anniversaries on February 29 correctly roll to March 1 in common years.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, ProfectionsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False
)

profections = ProfectionsFactory.from_subject(subject, target_date="2026-06-04")
print(f"Age {profections.current.age}: {profections.current.house}th house")
print(f"Sign: {profections.current.sign}, Lord: {profections.current.lord}")
```

## Methods

### `from_subject(subject, *, target_date=None, years_before=3, years_after=4)`

Build the profection years around a target date.

| Parameter      | Type                       | Default  | Description                                                                                       |
| :------------- | :------------------------- | :------- | :------------------------------------------------------------------------------------------------ |
| `subject`      | `AstrologicalSubjectModel` | --       | The natal chart. Requires the twelve house cusps. BCE births are supported.                        |
| `target_date`  | str (ISO `YYYY-MM-DD`) or None | None | Date the "current" year is resolved against. Astronomical year numbering accepted (e.g. `'-0550-10-07'`). When omitted, today in the subject's timezone. |
| `years_before` | int                        | 3        | Past years to include in the table.                                                               |
| `years_after`  | int                        | 4        | Future years to include in the table.                                                             |

**Returns:** `ProfectionsModel`

**Raises:** `KerykeionException` when cusps are missing, the target date is unparseable, or the target date precedes the birth date.

## Data Models

### `ProfectionsModel`

| Field     | Type                         | Description                                                          |
| :-------- | :--------------------------- | :------------------------------------------------------------------- |
| `current` | `ProfectionYearModel`        | The profection year containing the target date.                      |
| `years`   | `list[ProfectionYearModel]`  | Window of profection years (past and future around the current one). |

### `ProfectionYearModel`

| Field        | Type              | Description                                                                   |
| :----------- | :---------------- | :---------------------------------------------------------------------------- |
| `age`        | `int`             | Completed age the profection year begins at (0 = birth).                      |
| `house`      | `int`             | Profected house number (1-12), cycling every 12 years.                        |
| `sign`       | `Sign`            | Sign on the cusp of the profected house, in the subject's house system.       |
| `lord`       | `ClassicalPlanet` | Traditional (domicile) ruler of that sign — the Lord of the Year.             |
| `year_start` | `str`             | ISO date (`YYYY-MM-DD`) the profection year begins (the birthday anniversary).|
| `year_end`   | `str`             | ISO date the profection year ends (the next anniversary).                     |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
