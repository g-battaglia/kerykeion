---
title: 'Eclipse Factory'
description: 'Search for upcoming solar and lunar eclipses, globally or from a specific location, using the ephemeris backend's eclipse algorithms (libephemeris by default).'
category: 'Advanced Calculations'
tags: ['docs', 'eclipses', 'solar', 'lunar', 'kerykeion']
order: 40
---

# Eclipse Factory

The `EclipseFactory` searches for upcoming solar and lunar eclipses using the ephemeris backend's eclipse algorithms (libephemeris by default). It supports both **global** searches (eclipses visible from anywhere on Earth) and **location-specific** searches (eclipses visible from given coordinates).

## Basic Usage

```python
from kerykeion import EclipseFactory

# Find eclipses visible from Rome
results = EclipseFactory.search_from_location(
    lat=41.9028,
    lng=12.4964,
    start_year=2025,
    count=5
)

for eclipse in results.solar_eclipses:
    print(f"Solar: {eclipse.type} on {eclipse.datestamp} (mag: {eclipse.magnitude:.4f})")

for eclipse in results.lunar_eclipses:
    print(f"Lunar: {eclipse.type} on {eclipse.datestamp}")
```

## Methods

### `search_from_location(lat, lng, start_year, count)`

Finds eclipses visible from a specific geographic location.

| Parameter    | Type  | Default | Description                          |
| :----------- | :---- | :------ | :----------------------------------- |
| `lat`        | float | —       | Geographic latitude (north positive) |
| `lng`        | float | —       | Geographic longitude (east positive) |
| `start_year` | Optional[int] | None | Year to start searching from; `None` = current UTC year |
| `count`      | int   | 5       | Number of each type to find          |

**Returns:** `EclipseSearchResultModel`

### `search_global(start_year, count)`

Finds eclipses regardless of observer position.

| Parameter    | Type | Default | Description                  |
| :----------- | :--- | :------ | :--------------------------- |
| `start_year` | int  | 2025    | Year to start searching from |
| `count`      | int  | 10      | Number of each type to find  |

**Returns:** `EclipseSearchResultModel`

## Global Search

```python
# Find eclipses anywhere on Earth
global_results = EclipseFactory.search_global(start_year=2025, count=10)

print(f"Found {len(global_results.solar_eclipses)} solar eclipses")
print(f"Found {len(global_results.lunar_eclipses)} lunar eclipses")
```

## Data Models

### `SolarEclipseModel`

| Field          | Type           | Description                                |
| :------------- | :------------- | :----------------------------------------- |
| `type`         | str            | Eclipse type: total, annular, partial, annular-total |
| `maximum_jd`   | float          | Julian Day of maximum eclipse              |
| `datestamp`     | str            | ISO 8601 formatted datetime of maximum     |
| `magnitude`    | float          | Fraction of solar diameter covered          |
| `obscuration`  | float          | Fraction of solar disk area covered         |
| `sun_altitude` | float or None  | Sun altitude at maximum (degrees)          |

### `LunarEclipseModel`

| Field                | Type          | Description                         |
| :------------------- | :------------ | :---------------------------------- |
| `type`               | str           | Eclipse type: total, partial, penumbral |
| `maximum_jd`         | float         | Julian Day of maximum eclipse       |
| `datestamp`           | str           | ISO 8601 formatted datetime         |
| `magnitude_umbral`   | float or None | Umbral magnitude                    |
| `magnitude_penumbral`| float or None | Penumbral magnitude                 |

### `EclipseSearchResultModel`

| Field             | Type                    | Description                              |
| :---------------- | :---------------------- | :--------------------------------------- |
| `solar_eclipses`  | List[SolarEclipseModel] | Solar eclipses found                     |
| `lunar_eclipses`  | List[LunarEclipseModel] | Lunar eclipses found                     |
| `latitude`        | float or None           | Search latitude (None for global search) |
| `longitude`       | float or None           | Search longitude (None for global)       |

## JSON Export

All models support Pydantic serialization:

```python
results = EclipseFactory.search_global(start_year=2025, count=3)
print(results.model_dump_json(indent=2))
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
