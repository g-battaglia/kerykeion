---
title: 'Zodiacal Releasing (Aphesis)'
description: 'Compute the Hellenistic time-lord technique of zodiacal releasing (aphesis) from the Lot of Fortune or Spirit.'
category: 'Forecasting'
tags: ['docs', 'zodiacal releasing', 'aphesis', 'hellenistic', 'time-lord', 'kerykeion']
order: 53
---

# Zodiacal Releasing (Aphesis)

The `ZodiacalReleasingFactory` computes **zodiacal releasing** (aphesis), a Hellenistic time-lord technique (Vettius Valens). Periods unfold from a Lot's sign in zodiacal order: each sign rules for its "general years", subdividing into months, days and finer levels, with the **"loosing of the bond"** jump applied as the sequence circles back. Peak (angular) periods are marked relative to the Lot of Fortune.

A known birth time is required (the technique is built from the Ascendant and the Lots).

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, ZodiacalReleasingFactory

subject = AstrologicalSubjectFactory.from_birth_data("Jane", 1990, 6, 15, 12, 0, "Rome", "IT")

zr = ZodiacalReleasingFactory.from_subject(subject, lot="fortune", levels=2, target_date="2026-06-04")
print(zr.lot_sign, len(zr.periods), "top-level periods")

for period in zr.periods:
    print(period)
```

## Methods

### `from_subject(subject, *, lot="fortune", levels=2, target_date=None, life_cap_years=...)`

Build the zodiacal-releasing periods for a subject.

| Parameter        | Type                       | Default      | Description                                                                              |
| :--------------- | :------------------------- | :----------- | :--------------------------------------------------------------------------------------- |
| `subject`        | `AstrologicalSubjectModel` | --           | The natal chart (requires a known birth time / Ascendant).                               |
| `lot`            | `"fortune"` / `"spirit"`   | `"fortune"`  | Which Lot to release from.                                                                |
| `levels`         | int                        | 2            | Subdivision levels to compute (1–4). L1/L2 are built in full; deeper levels only along the target-date path. |
| `target_date`    | str (ISO `YYYY-MM-DD`) or None | None     | Date used to mark the current period chain. When omitted, only full levels (≤ 2) are built. |
| `life_cap_years` | int                        | (default)    | How far the L1 timeline extends, in years of life.                                       |

**Returns:** `ZodiacalReleasingModel`

**Raises:** `KerykeionException` for an unknown `lot`, an unresolvable Lot (missing birth time), or an unparseable `target_date`.

## Data Models

### `ZodiacalReleasingModel`

| Field        | Type                  | Description                                            |
| :----------- | :-------------------- | :---------------------------------------------------- |
| `lot`        | str                   | The Lot released from (`"fortune"` / `"spirit"`).     |
| `lot_sign`   | str                   | Sign of the Lot (the L1 starting sign).               |
| `periods`    | list[`ZRPeriodModel`] | The top-level (L1) periods, each with nested levels.  |

### `ZRPeriodModel`

Each period carries its ruling `sign`, `level` (L1–L4), start/end dates, sub-periods, and flags such as the "loosing of the bond" jump and peak/angular markers.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
