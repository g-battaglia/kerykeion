---
title: 'Eclipse Factory'
description: 'Search for upcoming solar and lunar eclipses, globally or from a specific location, using the eclipse algorithms of the ephemeris backend (libephemeris by default).'
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

### `search_from_location(lat, lng, start_year=None, count=5, zodiac_type="Tropical", sidereal_mode=None)`

Finds eclipses visible from a specific geographic location.

| Parameter       | Type                   | Default      | Description                          |
| :-------------- | :--------------------- | :----------- | :----------------------------------- |
| `lat`           | float                  | —            | Geographic latitude (north positive) |
| `lng`           | float                  | —            | Geographic longitude (east positive) |
| `start_year`    | Optional[int]          | None         | Year to start searching from; `None` = current UTC year |
| `count`         | int                    | 5            | Number of each type to find          |
| `zodiac_type`   | `ZodiacType`           | `"Tropical"` | `"Tropical"` or `"Sidereal"`; affects reported eclipse positions, not maximum times. |
| `sidereal_mode` | `SiderealMode` or None | None         | Required ayanamsha when `zodiac_type="Sidereal"`. |

**Returns:** `EclipseSearchResultModel`

### `search_global(start_year=None, count=10, zodiac_type="Tropical", sidereal_mode=None)`

Finds eclipses regardless of observer position.

| Parameter       | Type                   | Default      | Description                  |
| :-------------- | :--------------------- | :----------- | :--------------------------- |
| `start_year`    | Optional[int]          | None         | Year to start searching from; `None` = current UTC year |
| `count`         | int                    | 10           | Number of each type to find  |
| `zodiac_type`   | `ZodiacType`           | `"Tropical"` | `"Tropical"` or `"Sidereal"`; affects reported eclipse positions, not maximum times. |
| `sidereal_mode` | `SiderealMode` or None | None         | Required ayanamsha when `zodiac_type="Sidereal"`. |

**Returns:** `EclipseSearchResultModel`

For both search methods, `count` must be between 0 and 1,000 inclusive;
invalid counts raise `ValueError` before any backend call.

## Global Search

```python
# Find eclipses anywhere on Earth
global_results = EclipseFactory.search_global(start_year=2025, count=10)

print(f"Found {len(global_results.solar_eclipses)} solar eclipses")
print(f"Found {len(global_results.lunar_eclipses)} lunar eclipses")
```

Eclipse maximum times are determined by shadow geometry and therefore do not
change with the zodiac. To report the eclipse longitude/sign in a sidereal
frame, request an ayanamsha:

```python
sidereal_results = EclipseFactory.search_global(
    start_year=2025,
    count=3,
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI",
)
```

## Data Models

### `SolarEclipseModel`

| Field          | Type           | Description                                |
| :------------- | :------------- | :----------------------------------------- |
| `type`         | str            | Eclipse type: total, annular, partial, annular-total |
| `maximum_jd`   | float          | Julian Day of maximum eclipse              |
| `datestamp`     | str            | ISO 8601 formatted datetime of maximum     |
| `magnitude`    | float or None          | Fraction of solar diameter covered          |
| `obscuration`  | float or None          | Fraction of solar disk area covered         |
| `sun_altitude` | float or None  | Sun altitude at maximum (degrees)          |
| `ecliptic_longitude` | float or None | Eclipse longitude at maximum in the requested zodiac (0–360). |
| `sign`         | str or None    | Zodiac sign at maximum in the requested zodiac. |
| `sign_num`     | int or None    | Zodiac sign index (0=Aries). |
| `degree`       | float or None  | Degree within the sign (0–30). |
| `saros`        | int or None    | Saros series number when the active backend/catalog provides one. |
| `inex`         | int or None    | Reserved Inex series number; currently `None` because available nearest-series results are not trustworthy. |
| `gamma`        | float or None  | Shadow-axis distance from Earth's centre, in Earth radii, when supported by the backend. |
| `duration_minutes` | float or None | Central total/annular phase duration at the point of greatest eclipse; `None` for partial eclipses or unsupported backends. |

### `LunarEclipseModel`

| Field                | Type          | Description                         |
| :------------------- | :------------ | :---------------------------------- |
| `type`               | str           | Eclipse type: total, partial, penumbral |
| `maximum_jd`         | float         | Julian Day of maximum eclipse       |
| `datestamp`           | str           | ISO 8601 formatted datetime         |
| `magnitude_umbral`   | float or None | Umbral magnitude                    |
| `magnitude_penumbral`| float or None | Penumbral magnitude                 |
| `ecliptic_longitude` | float or None | Eclipse longitude at maximum in the requested zodiac (0–360). |
| `sign`                | str or None   | Zodiac sign at maximum in the requested zodiac. |
| `sign_num`            | int or None   | Zodiac sign index (0=Aries). |
| `degree`              | float or None | Degree within the sign (0–30). |
| `saros`               | int or None   | Saros series number when the active backend/catalog provides one. |
| `inex`                | int or None   | Reserved Inex series number; currently `None` because available nearest-series results are not trustworthy. |

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
