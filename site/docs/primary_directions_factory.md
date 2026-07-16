---
title: 'Primary Directions'
description: 'Compute Placidus semi-arc primary directions for classical predictive astrology.'
category: 'Forecasting'
tags: ['docs', 'primary-directions', 'placidus', 'predictive', 'kerykeion']
order: 43
---

# Primary Directions

The `PrimaryDirectionsFactory` implements **Placidus semi-arc primary directions** -- the most widely used method in classical/traditional astrology for predicting life events.

## Algorithm

1. Convert each planet's ecliptic position to equatorial (RA, Dec)
2. Compute the semi-arc (diurnal or nocturnal) for each planet
3. Compute the meridian distance (RA - RAMC)
4. Compute the pole of the significator (Placidus house latitude)
5. Compute oblique ascension of promissor under the significator's pole
6. The arc of direction = OA(promissor under sig's pole) - OA(significator)
7. Convert arc to years using the rate key

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, PrimaryDirectionsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1940, 10, 9, 18, 30,
    lng=-2.9833, lat=53.4, tz_str="Europe/London", online=False,
)

directions = PrimaryDirectionsFactory.compute(subject, max_years=80)

for d in directions[:10]:
    print(f"Year {d.direction_years:.1f}: {d.promissor} {d.aspect} {d.significator}")
```

## Methods

### `compute(subject, *, max_years, rate_key, aspects)`

Compute primary directions for a natal chart.

| Parameter   | Type                      | Default    | Description                                             |
| :---------- | :------------------------ | :--------- | :------------------------------------------------------ |
| `subject`   | AstrologicalSubjectModel  | --         | The natal chart subject                                 |
| `max_years` | float                     | 100        | Finite, non-negative maximum number of years to compute directions for |
| `rate_key`  | "ptolemy" or "naibod"     | "ptolemy"  | Conversion rate (ptolemy: 1 deg = 1 yr, naibod: 0.98564 deg = 1 yr); other values raise `KerykeionException` |
| `aspects`   | List[str] or None         | None       | Unique supported aspect names; non-strings, unknown names, and malformed entries raise `KerykeionException` |

**Returns:** `List[PrimaryDirectionModel]` sorted by `direction_years`.

### `compute_speculum(subject)`

Compute the Placidian coordinate table independently of the direction list:

```python
speculum = PrimaryDirectionsFactory.compute_speculum(subject)
for entry in speculum:
    print(entry.name, entry.right_ascension, entry.declination, entry.semi_arc)
```

**Returns:** `List[SpeculumEntryModel]`. The subject must represent one real
instant with valid chart geometry; midpoint composites are not supported.
Equatorial coordinates follow the subject's configured perspective:
planetocentric charts use that center body's frame, and Topocentric charts use
the observer coordinates including `subject.altitude` (sea level when `None`).

### Rate Keys

- **Ptolemy**: 1 degree of arc = 1 year of life (the classical rate)
- **Naibod**: 0.98564 degrees = 1 year (the mean daily motion of the Sun)

## Data Models

### `PrimaryDirectionModel`

| Field             | Type  | Description                                       |
| :---------------- | :---- | :------------------------------------------------ |
| `promissor`       | str   | The directed planet (moving point)                |
| `significator`    | str   | The receiving point (fixed target)                |
| `aspect`          | str   | Aspect type (conjunction, trine, square, etc.)    |
| `arc`             | float | Arc of direction in degrees of RA                 |
| `direction_years` | float | Equivalent years using the selected rate key      |
| `rate_key`        | str   | Rate key used (ptolemy or naibod)                 |
| `is_converse`     | bool  | `True` for converse directions (see note below)   |

> **Note:** `compute()` returns both **direct** (`is_converse=False`) and
> **converse** (`is_converse=True`) entries interleaved, so the same
> promissor/significator pair appears twice at different arcs. The converse
> arc is an explicit sign-flip approximation of the classical technique —
> filter on `is_converse` if you only want the traditional direct directions.

### `SpeculumEntryModel`

The speculum (coordinate table) for each point can be retrieved separately:

| Field                | Type  | Description                                    |
| :------------------- | :---- | :--------------------------------------------- |
| `name`               | str   | Planet name                                    |
| `ecliptic_longitude` | float | Ecliptic longitude (0-360)                     |
| `right_ascension`    | float | Right Ascension in degrees                     |
| `declination`        | float | Declination in degrees (-90 to +90)            |
| `meridian_distance`  | float | Angular distance from MC in RA degrees         |
| `semi_arc`           | float | Semi-arc (diurnal or nocturnal) in degrees     |
| `is_above_horizon`   | bool  | True if planet is above the horizon            |
| `pole`               | float | Pole of the house position (Placidus)          |
| `oblique_ascension`  | float | Oblique ascension under own pole               |

## Direction Points

By default, the factory computes directions between: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Ascendant, Medium Coeli.

## Aspect Types

Default major aspects: conjunction, sextile, square, trine, opposition.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
