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

# Offline mode: explicit coordinates, no GeoNames lookup
subject = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

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
| `life_cap_years` | int                        | 100          | How far the L1 timeline extends, in years of life (`DEFAULT_LIFE_CAP_YEARS`).             |

When `target_date` falls beyond `life_cap_years`, the L1 timeline is extended to
cover the target date plus a ten-year margin, so the current path is always
resolvable. A shorter cap is never applied in that case.

**Returns:** `ZodiacalReleasingModel`

**Raises:** `KerykeionException` for an unknown `lot`; an unresolvable Lot
(missing birth time, so no Ascendant/Sun/Moon); an unparseable `target_date`; a
timezone-aware `target_date` (pass a bare ISO date such as `"2026-06-04"`); or a
subject with no single moment in time to anchor the timeline — a midpoint
composite. Returns and Davison charts are accepted: they resolve through their
ISO timestamp.

## Data Models

### `ZodiacalReleasingModel`

| Field        | Type                  | Description                                            |
| :----------- | :-------------------- | :---------------------------------------------------- |
| `lot`          | str                   | The Lot released from (`"fortune"` / `"spirit"`).   |
| `lot_sign`     | str                   | Sign of the Lot (the L1 starting sign).             |
| `lot_degree`   | float                 | Absolute longitude of the Lot in the subject's zodiac. |
| `periods`      | list[`ZRPeriodModel`] | The top-level (L1) periods, each with nested levels. |
| `current_path` | list[`ZRPeriodModel`] | The chain of active periods (L1→Ln) at `target_date`, when one was supplied. |

### `ZRPeriodModel`

One period at a given level of subdivision. Periods nest: an L1 (years) period
contains L2 (months) sub-periods, and so on.

| Field                 | Type                  | Description                                            |
| :-------------------- | :-------------------- | :---------------------------------------------------- |
| `sign`                | str                   | Three-letter code of the sign ruling the period (`"Ari"` … `"Pis"`). |
| `ruler`               | str or None           | Traditional (domicile) ruler of that sign.          |
| `level`               | int                   | Subdivision level (1 = years, 2 = months, 3 = days, …). |
| `start`               | str                   | Start date (ISO `YYYY-MM-DD`).                      |
| `end`                 | str                   | End date (ISO `YYYY-MM-DD`).                        |
| `years`               | float                 | Nominal length in years at this level (the sign's general years divided by `12 ** (level - 1)`). |
| `is_angular`          | bool                  | `True` for a peak period: the sign is angular (1st/4th/7th/10th) from the natal Lot of Fortune, the reference used for every released lot. |
| `is_loosing_the_bond` | bool                  | `True` when the period begins after a "loosing of the bond" jump to the opposite sign. |
| `subperiods`          | list[`ZRPeriodModel`] | Nested sub-periods one level deeper (possibly empty). |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
