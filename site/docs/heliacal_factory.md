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

## Basic Usage

```python
from kerykeion import HeliacalFactory
from kerykeion.ephemeris_backend import swe

factory = HeliacalFactory()

# Find the next heliacal rising of Venus from Rome
jd_start = swe.julday(2025, 1, 1, 0.0)
event = factory.next_heliacal_rising(
    julian_day=jd_start,
    planet_name_or_star="Venus",
    geopos=(12.4964, 41.9028, 50),  # (longitude, latitude, altitude_m)
)

print(f"Venus heliacal rising: {event.datestamp}")
```

## Methods

### `next_heliacal_rising(julian_day, planet_name_or_star, geopos, atmo, observer)`

Find the next heliacal rising after the given Julian Day.

| Parameter              | Type                               | Default  | Description                                              |
| :--------------------- | :--------------------------------- | :------- | :------------------------------------------------------- |
| `julian_day`           | float                              | --       | Starting Julian Day (UT)                                 |
| `planet_name_or_star`  | str                                | --       | Planet name (e.g. `"Venus"`) or fixed-star name          |
| `geopos`               | Tuple[float, float, float]         | --       | (longitude, latitude, altitude_m) of the observer        |
| `atmo`                 | Tuple[float,float,float,float] or None | None | (pressure, temperature, humidity, extinction)            |
| `observer`             | Tuple of 6 floats or None          | None     | Observer parameters (age, Snellen ratio, etc.)           |

**Returns:** `HeliacalEventModel`

### `search_events(julian_day, geopos, count, planets, event_types, atmo, observer)`

Find the next N heliacal events across multiple planets, sorted chronologically.

| Parameter     | Type                       | Default | Description                                         |
| :------------ | :------------------------- | :------ | :-------------------------------------------------- |
| `julian_day`  | float                      | --      | Starting Julian Day (UT)                            |
| `geopos`      | Tuple[float,float,float]   | --      | Observer position                                   |
| `count`       | int                        | 5       | Maximum number of events to return                  |
| `planets`     | Sequence[str] or None      | None    | Planet names (defaults to Mercury through Saturn)   |
| `event_types` | Sequence[int] or None      | None    | Event type constants (defaults to rising/setting)   |
| `atmo`        | Tuple or None              | None    | Atmospheric parameters                              |
| `observer`    | Tuple or None              | None    | Observer parameters                                 |

**Returns:** `List[HeliacalEventModel]`

```python
events = factory.search_events(
    julian_day=swe.julday(2025, 1, 1, 0.0),
    geopos=(12.4964, 41.9028, 50),
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
