---
title: 'Heliacal Risings & Settings'
description: 'Find heliacal events -- when planets first become visible at dawn or last visible at dusk.'
category: 'Advanced Calculations'
tags: ['docs', 'heliacal', 'visibility', 'rising', 'setting', 'kerykeion']
order: 48
---

# Heliacal Risings & Settings

The `HeliacalFactory` calculates **heliacal events** -- the first/last visibility of planets and stars relative to the Sun. A heliacal rising is the first morning a planet becomes visible above the eastern horizon just before sunrise after a period of invisibility. A heliacal setting is the last evening it is visible above the western horizon just after sunset.

## Event Types

| Constant           | Description                                        |
| :----------------- | :------------------------------------------------- |
| `HELIACAL_RISING`  | Morning first: planet first visible before sunrise |
| `HELIACAL_SETTING` | Evening last: planet last visible after sunset     |
| `EVENING_FIRST`    | Evening first (Mercury/Venus only)                 |
| `MORNING_LAST`     | Morning last (Mercury/Venus only)                  |

These constants are exported from the `kerykeion.heliacal` subpackage, not from
the top-level `kerykeion` namespace:

```python
from kerykeion.heliacal import (
    HELIACAL_RISING,
    HELIACAL_SETTING,
    EVENING_FIRST,
    MORNING_LAST,
)
```

## Basic Usage

```python
from kerykeion import HeliacalFactory
from kerykeion.ephemeris_backend import ephe

factory = HeliacalFactory()

# Find the next heliacal rising of Venus from Rome
jd_start = ephe.julday(2025, 1, 1, 0.0)
event = factory.next_heliacal_rising(
    julian_day=jd_start,
    planet_name_or_star="Venus",
    lat=41.9028,
    lng=12.4964,
    altitude=50,
)

print(f"Venus heliacal rising: {event.datestamp}")
```

## Methods

### `HeliacalFactory(ephe_path=None)`

Build a factory. The instance is stateless apart from the ephemeris path.

| Parameter   | Type          | Default | Description                                                 |
| :---------- | :------------ | :------ | :---------------------------------------------------------- |
| `ephe_path` | str or None   | None    | Path to the ephemeris data directory. `None` falls back to the path configured via `KERYKEION_EPHE_PATH` (or the empty string). |

The path is applied per calculation, inside the ephemeris session each method
opens, rather than mutating global backend state at construction time.

### `next_heliacal_rising(julian_day, planet_name_or_star, geopos=None, atmo=None, observer=None, *, lat=None, lng=None, altitude=None)`

Find the next heliacal rising after the given Julian Day.

| Parameter              | Type                                   | Default      | Description                                              |
| :--------------------- | :------------------------------------- | :----------- | :------------------------------------------------------- |
| `julian_day`           | float                                  | **Required** | Finite starting Julian Day (UT).                         |
| `planet_name_or_star`  | str                                    | **Required** | Planet name (e.g. `"Venus"`) or fixed-star name.         |
| `geopos`               | Tuple[float, float, float] or None     | None         | Observer `(longitude, latitude, altitude_m)`; mutually exclusive with the coordinate keywords. |
| `atmo`                 | Tuple[float, float, float, float] or None | None       | Four finite values: `(pressure, temperature, humidity, extinction)`. |
| `observer`             | Tuple of 6 floats or None              | None         | Six finite observer parameters (age, Snellen ratio, etc.). |
| `lat`                  | float or None                          | None         | Observer latitude in [-90, 90] (keyword-only); must be paired with `lng`. |
| `lng`                  | float or None                          | None         | Observer longitude in [-180, 180] (keyword-only); must be paired with `lat`. |
| `altitude`             | float or None                          | None         | Finite observer altitude in metres; defaults to `0` with `lat`/`lng`. |

**Returns:** `HeliacalEventModel`

**Raises:** `KerykeionException` when no rising is found after `julian_day`,
when the body is not a supported planet or a recognized fixed-star name, or
when the search date falls outside the available ephemeris range. The first two
cases share one message: the backend reports them identically, so the exception
names both possibilities and suggests widening the window.

### `search_events(julian_day, geopos=None, count=5, planets=None, event_types=None, atmo=None, observer=None, *, lat=None, lng=None, altitude=None)`

Find the next N heliacal events across multiple planets, sorted chronologically.

| Parameter     | Type                       | Default      | Description                                         |
| :------------ | :------------------------- | :----------- | :-------------------------------------------------- |
| `julian_day`  | float                      | **Required** | Finite starting Julian Day (UT).                    |
| `geopos`      | Tuple[float,float,float] or None | None    | Observer `(longitude, latitude, altitude_m)`; mutually exclusive with coordinate keywords. |
| `count`       | int                        | 5            | Non-negative maximum number of events to return (maximum 200). |
| `planets`     | Sequence[str] or None      | None         | Planet names (defaults to Mercury through Saturn).  |
| `event_types` | Sequence[int] or None      | None         | Valid event type constants from the table above (defaults to rising/setting). |
| `atmo`        | Tuple or None              | None         | Exactly four finite atmospheric parameters.         |
| `observer`    | Tuple or None              | None         | Exactly six finite observer parameters.             |
| `lat`         | float or None              | None         | Observer latitude in [-90, 90] (keyword-only); must be paired with `lng`. |
| `lng`         | float or None              | None         | Observer longitude in [-180, 180] (keyword-only); must be paired with `lat`. |
| `altitude`    | float or None              | None         | Finite observer altitude in metres; defaults to `0` with `lat`/`lng`. |

The keyword coordinate form is recommended because it makes latitude and
longitude order explicit. Do not combine it with `geopos`; passing both forms,
or passing only one of `lat`/`lng`, raises `KerykeionException`.

**Returns:** `List[HeliacalEventModel]`

```python
# doc-snippet: no-run — multi-planet visibility search runs for minutes
events = factory.search_events(
    julian_day=ephe.julday(2025, 1, 1, 0.0),
    lat=41.9028,
    lng=12.4964,
    altitude=50,
    count=10,
)

for e in events:
    print(f"{e.planet_name}: {e.event_type} on {e.datestamp}")
```

## Supported Planets

Mercury, Venus, Mars, Jupiter, Saturn.

Inner planets (Mercury, Venus) support all four event types; outer planets only support heliacal rising and setting.

## Data Models

### `HeliacalEventModel`

| Field         | Type  | Description                                        |
| :------------ | :---- | :------------------------------------------------- |
| `event_type`  | str   | Human-readable event type (e.g. "heliacal_rising") |
| `julian_day`  | float | Julian Day (UT) of the visibility event            |
| `planet_name` | str   | Name of the planet or star                         |
| `datestamp`    | str   | ISO-style date string (YYYY-MM-DD)                 |

## Atmospheric & Observer Parameters

Default atmospheric parameters: pressure 1013.25 hPa, temperature 15 C, humidity 40%, extinction coefficient 0.2.

Default observer: 36 years old, normal vision (Snellen 1.0), naked eye.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
