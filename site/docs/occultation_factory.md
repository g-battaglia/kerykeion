---
title: 'Occultation Factory'
description: 'Search for lunar occultation events -- when the Moon passes in front of a planet as seen from Earth.'
category: 'Advanced Calculations'
tags: ['docs', 'occultations', 'lunar', 'kerykeion']
order: 49
---

# Occultation Factory

The `OccultationFactory` searches for **lunar occultations** -- events where the Moon passes in front of a planet or star as seen from Earth. It wraps the ephemeris backend's occultation functions (libephemeris by default) for both global and location-specific searches.

## Basic Usage

```python
from kerykeion import OccultationFactory
from kerykeion.ephemeris_backend import ephe

factory = OccultationFactory()

# Find next 3 global occultations of Venus
jd_start = ephe.julday(2025, 1, 1, 0.0)
events = factory.search_global(jd_start, ephe.VENUS, count=3)

for occ in events:
    print(f"{occ.planet_name}: {occ.type} on {occ.datestamp}")
```

## Methods

### `search_global(julian_day, planet_id, count)`

Find occultations visible from anywhere on Earth.

| Parameter    | Type  | Default | Description                                      |
| :----------- | :---- | :------ | :----------------------------------------------- |
| `julian_day` | float | --      | Finite starting Julian Day (UT) for the search   |
| `planet_id`  | int or str | -- | Body identifier: an ephe-style constant (e.g. `ephe.VENUS`) or a planet name (e.g. `"Venus"`) |
| `count`      | int   | 5       | Number of events to return                       |

**Returns:** `List[OccultationModel]`

### `search_local(julian_day, planet_id, lat, lng, count)`

Find occultations visible from a specific location.

| Parameter    | Type  | Default | Description                                      |
| :----------- | :---- | :------ | :----------------------------------------------- |
| `julian_day` | float | --      | Finite starting Julian Day (UT) for the search   |
| `planet_id`  | int or str | -- | Body identifier: an ephe-style constant or a planet name |
| `lat`        | float | --      | Geographic latitude in [-90, 90] (north positive) |
| `lng`        | float | --      | Geographic longitude in [-180, 180] (east positive) |
| `count`      | int   | 5       | Number of events to return                       |

**Returns:** `List[OccultationModel]`

For both search methods, `count` must be between 0 and 1,000 inclusive;
invalid counts raise `ValueError` before any backend call. A `planet_id` that
is neither an `int` nor a `str` raises `TypeError`, and a body outside the
occultable set (see [Planet Identifiers](#planet-identifiers)) raises
`KerykeionException`.

```python
# Find occultations visible from Rome
events = factory.search_local(
    julian_day=ephe.julday(2025, 1, 1, 0.0),
    planet_id=ephe.SATURN,
    lat=41.9028,
    lng=12.4964,
    count=5,
)
```

## Planet Identifiers

`planet_id` accepts either an `ephe` constant or the body's name as a string:

| Planet  | Constant       | Name        |
| :------ | :------------- | :---------- |
| Mercury | `ephe.MERCURY`  | `"Mercury"` |
| Venus   | `ephe.VENUS`    | `"Venus"`   |
| Mars    | `ephe.MARS`     | `"Mars"`    |
| Jupiter | `ephe.JUPITER`  | `"Jupiter"` |
| Saturn  | `ephe.SATURN`   | `"Saturn"`  |

A name is resolved through the project-wide name-to-ID map, so
`factory.search_global(jd, "Venus")` and `factory.search_global(jd, ephe.VENUS)`
are equivalent.

### Accepted Bodies

Only physically real bodies can be occulted by the Moon, so both forms are
restricted to: **Sun, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune,
Pluto, Chiron, Pholus, Ceres, Pallas, Juno, Vesta**.

Anything else raises:

- `KerykeionException` — an unknown planet name, or a known name/ID outside the
  set above: the calculated points (lunar nodes, Lilith and apogee variants, the
  Uranian hypotheticals) have no disk to be covered, and the Moon and the Earth
  are not occultable either.
- `TypeError` — a `planet_id` that is neither an `int` nor a `str` (booleans
  included).

## Data Models

### `OccultationModel`

| Field         | Type  | Description                                       |
| :------------ | :---- | :------------------------------------------------ |
| `planet_name` | str   | Name of the occulted body (e.g. "Venus")          |
| `type`        | str   | Occultation type: Total, Partial, Annular, Unknown |
| `maximum_jd`  | float | Julian Day of maximum occultation                 |
| `datestamp`    | str   | ISO-8601 UTC datestamp of maximum                 |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more ->](/content/docs/astrologer-api)
