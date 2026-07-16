---
title: 'Planetary Phenomena Factory'
description: 'Calculate observational planetary phenomena: elongation, illumination, phase angle, apparent magnitude, and morning/evening star status.'
category: 'Advanced Calculations'
tags: ['docs', 'phenomena', 'elongation', 'magnitude', 'kerykeion']
order: 46
---

# Planetary Phenomena Factory

The `PlanetaryPhenomenaFactory` calculates **observational phenomena** for planets using the ephemeris backend's `ephe.pheno_ut()` function (libephemeris by default). It computes elongation, illumination fraction, phase angle, apparent diameter/magnitude, and morning/evening star status.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, PlanetaryPhenomenaFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 2025, 4, 1, 12, 0,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)

results = PlanetaryPhenomenaFactory.from_subject(subject)

for p in results.phenomena:
    print(f"{p.name}: elongation={p.elongation:.1f}, mag={p.apparent_magnitude:.1f}")
    if p.is_morning_star:
        print(f"  Morning star")
    elif p.is_evening_star:
        print(f"  Evening star")
```

## Methods

### `from_subject(subject, planets)`

Calculate phenomena from an existing astrological subject.

| Parameter | Type                     | Default | Description                      |
| :-------- | :----------------------- | :------ | :------------------------------- |
| `subject` | AstrologicalSubjectModel | --      | An astrological subject          |
| `planets` | List[str] or None        | None    | Planet names (defaults to all)   |

**Returns:** `PlanetaryPhenomenaCollectionModel`

### `from_julian_day(julian_day, planets)`

Calculate phenomena from a Julian Day number.

| Parameter    | Type              | Default | Description                    |
| :----------- | :---------------- | :------ | :----------------------------- |
| `julian_day` | float             | --      | Finite Julian Day number       |
| `planets`    | List[str] or None | None    | Planet names (defaults to all) |

**Returns:** `PlanetaryPhenomenaCollectionModel`

## Supported Planets

Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto.

Morning/evening star status is calculated only for the inferior planets (Mercury, Venus).

## Data Models

### `PlanetaryPhenomenaModel`

| Field                | Type          | Description                                       |
| :------------------- | :------------ | :------------------------------------------------ |
| `name`               | str           | Planet name                                       |
| `phase_angle`        | float         | Phase angle in degrees                            |
| `phase`              | float         | Illuminated fraction (0.0 to 1.0)                 |
| `elongation`         | float         | Angular distance from the Sun in degrees          |
| `apparent_diameter`  | float         | Apparent diameter in degrees                      |
| `apparent_magnitude` | float         | Apparent visual magnitude                         |
| `is_morning_star`    | Optional[bool] | True if visible before sunrise; `None` for planets other than Mercury/Venus |
| `is_evening_star`    | Optional[bool] | True if visible after sunset; `None` for planets other than Mercury/Venus   |

### `PlanetaryPhenomenaCollectionModel`

| Field          | Type                            | Description                |
| :------------- | :------------------------------ | :------------------------- |
| `iso_datetime` | str                             | ISO datetime of moment     |
| `julian_day`   | float                           | Julian Day number          |
| `phenomena`    | List[PlanetaryPhenomenaModel]   | Phenomena for each planet  |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
