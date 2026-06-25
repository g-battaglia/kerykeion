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
from kerykeion.ephemeris_backend import swe

factory = OccultationFactory()

# Find next 3 global occultations of Venus
jd_start = swe.julday(2025, 1, 1, 0.0)
events = factory.search_global(jd_start, swe.VENUS, count=3)

for occ in events:
    print(f"{occ.planet_name}: {occ.type} on {occ.datestamp}")
```

## Methods

### `search_global(julian_day, planet_id, count)`

Find occultations visible from anywhere on Earth.

| Parameter    | Type  | Default | Description                                      |
| :----------- | :---- | :------ | :----------------------------------------------- |
| `julian_day` | float | --      | Starting Julian Day (UT) for the search          |
| `planet_id`  | int   | --      | Planet identifier (swe-style constant, e.g. `swe.VENUS`) |
| `count`      | int   | 5       | Number of events to return                       |

**Returns:** `List[OccultationModel]`

### `search_local(julian_day, planet_id, lat, lng, count)`

Find occultations visible from a specific location.

| Parameter    | Type  | Default | Description                                      |
| :----------- | :---- | :------ | :----------------------------------------------- |
| `julian_day` | float | --      | Starting Julian Day (UT) for the search          |
| `planet_id`  | int   | --      | Planet identifier (swe-style constant)           |
| `lat`        | float | --      | Geographic latitude (north positive)             |
| `lng`        | float | --      | Geographic longitude (east positive)             |
| `count`      | int   | 5       | Number of events to return                       |

**Returns:** `List[OccultationModel]`

```python
# Find occultations visible from Rome
events = factory.search_local(
    julian_day=swe.julday(2025, 1, 1, 0.0),
    planet_id=swe.SATURN,
    lat=41.9028,
    lng=12.4964,
    count=5,
)
```

## Planet Identifiers

Use `swe` constants for the `planet_id` parameter:

| Planet  | Constant       |
| :------ | :------------- |
| Mercury | `swe.MERCURY`  |
| Venus   | `swe.VENUS`    |
| Mars    | `swe.MARS`     |
| Jupiter | `swe.JUPITER`  |
| Saturn  | `swe.SATURN`   |

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
