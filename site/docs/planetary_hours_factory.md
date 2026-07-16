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

## Models

`PlanetaryHoursModel` contains the planetary-day `date`, timezone and
coordinates, `day_ruler`, `current_index`, `current_ruler`, the bounding
`sunrise`, `sunset`, `next_sunrise`, and all 24 `hours`.

Each `PlanetaryHourModel` has a 1-based `index`, `ruler`, `is_diurnal`, `start`,
and `end`. All event instants are timezone-aware UTC datetimes.
