---
title: 'Planetary Hours Factory'
description: 'Compute the 24 unequal Chaldean planetary hours containing a local civil moment.'
category: 'Forecasting'
tags: ['docs', 'planetary hours', 'chaldean order', 'sunrise', 'kerykeion']
order: 58
---

# Planetary Hours Factory

`PlanetaryHoursFactory` divides sunrise-to-sunset into twelve equal day hours
and sunset-to-next-sunrise into twelve equal night hours. The first hour is
ruled by the weekday ruler; subsequent hours follow the Chaldean order. A civil
moment before sunrise belongs to the previous planetary day automatically.

## Basic Usage

```python
from kerykeion import PlanetaryHoursFactory

result = PlanetaryHoursFactory.from_datetime(
    2026, 5, 28, 11, 30,
    latitude=41.9028,
    longitude=12.4964,
    tz_str="Europe/Rome",
)
print(result.day_ruler, result.current_index, result.current_ruler)
for planetary_hour in result.hours:
    print(planetary_hour.index, planetary_hour.ruler, planetary_hour.start, planetary_hour.end)
```

## `from_datetime`

`PlanetaryHoursFactory.from_datetime(year, month, day, hour, minute=0, *, latitude, longitude, tz_str) -> PlanetaryHoursModel`

The date and clock time are interpreted in `tz_str`. Latitude is north-positive
(-90 to 90); longitude is east-positive (-180 to 180). Invalid input raises
`KerykeionException`. Planetary hours are undefined when a bounding sunrise or
sunset is absent (polar day/night), which also raises `KerykeionException`.

A planetary day runs from one sunrise to the next, so both ends of the
representable calendar are refused with `KerykeionException`: an evening of
9999-12-31 would need the sunrise of 10000-01-01, and a morning of 0001-01-01
before sunrise would need the sunset of the day before year 1.

## Models

### `PlanetaryHoursModel`

| Field           | Type                     | Description                                                     |
| :-------------- | :----------------------- | :-------------------------------------------------------------- |
| `date`          | str                      | Civil date (ISO) of the planetary day's sunrise, in `timezone`. |
| `timezone`      | str                      | IANA timezone identifier.                                        |
| `latitude`      | float                    | Observer latitude in degrees.                                    |
| `longitude`     | float                    | Observer longitude in degrees.                                   |
| `day_ruler`     | ClassicalPlanet          | Planet ruling the whole planetary day (from the weekday).        |
| `current_index` | int                      | 1-based index of the hour containing the requested moment.       |
| `current_ruler` | ClassicalPlanet          | Ruler of the hour containing the requested moment.               |
| `sunrise`       | datetime                 | Sunrise opening the day hours.                                   |
| `sunset`        | datetime                 | Sunset dividing day and night hours.                             |
| `next_sunrise`  | datetime                 | Sunrise closing the night hours.                                 |
| `hours`         | list[PlanetaryHourModel] | All 24 planetary hours, in chronological order.                  |

### `PlanetaryHourModel`

| Field        | Type            | Description                                                          |
| :----------- | :-------------- | :------------------------------------------------------------------- |
| `index`      | int             | 1-based position in the sequence (1-24).                             |
| `ruler`      | ClassicalPlanet | Classical planet ruling the hour.                                    |
| `is_diurnal` | bool            | `True` for the 12 day hours, `False` for the 12 night hours.         |
| `start`      | datetime        | Hour start.                                                          |
| `end`        | datetime        | Hour end.                                                            |

All event instants are timezone-aware UTC datetimes.
