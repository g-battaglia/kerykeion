---
title: 'Sun Times Factory'
description: 'Compute sunrise, sunset, twilight, solar noon, and day length for a civil date and location.'
category: 'Forecasting'
tags: ['docs', 'sunrise', 'sunset', 'twilight', 'sun times', 'kerykeion']
order: 57
---

# Sun Times Factory

`SunTimesFactory` computes apparent upper-limb sunrise and sunset (including
atmospheric refraction), solar noon, day length, and civil/nautical/astronomical
twilight. The civil date is interpreted in the supplied IANA timezone; returned
instants are timezone-aware UTC datetimes.

## Basic Usage

```python
from kerykeion import SunTimesFactory

sun = SunTimesFactory.from_date(
    2026, 5, 28,
    latitude=41.9028,
    longitude=12.4964,
    tz_str="Europe/Rome",
)
print(sun.sunrise, sun.sunset, sun.day_length)
print(sun.civil_dawn, sun.civil_dusk)
```

## `from_date`

`SunTimesFactory.from_date(year, month, day, *, latitude, longitude, tz_str) -> SunTimesModel`

| Parameter | Type | Description |
| :-- | :-- | :-- |
| `year`, `month`, `day` | int | Gregorian civil date in `tz_str`. |
| `latitude` | float | North-positive latitude, from -90 to 90. |
| `longitude` | float | East-positive longitude, from -180 to 180. |
| `tz_str` | str | IANA timezone identifier. |

Invalid coordinates, timezone names, and civil dates raise
`KerykeionException`.

## `SunTimesModel`

All instants are timezone-aware UTC `datetime` objects; `day_length` is a
`timedelta`.

| Field | Type | Description |
| :-- | :-- | :-- |
| `date` | str | Civil date (`YYYY-MM-DD`) in the requested timezone. |
| `timezone` | str | IANA timezone identifier the date is anchored to. |
| `latitude` | float | Observer latitude in degrees, north positive. |
| `longitude` | float | Observer longitude in degrees, east positive. |
| `sunrise` | datetime or None | Sunrise (upper limb, atmospheric refraction applied). |
| `sunset` | datetime or None | Sunset (upper limb, atmospheric refraction applied). |
| `solar_noon` | datetime or None | Meridian transit -- true local noon, not the midpoint of the rise/set pair. |
| `day_length` | timedelta or None | Sunset minus sunrise. |
| `is_polar_day` | bool | The Sun stays above the horizon for the whole civil date. |
| `is_polar_night` | bool | The Sun stays below the horizon for the whole civil date. |
| `civil_dawn`, `civil_dusk` | datetime or None | Sun 6° below the horizon. |
| `nautical_dawn`, `nautical_dusk` | datetime or None | Sun 12° below the horizon. |
| `astronomical_dawn`, `astronomical_dusk` | datetime or None | Sun 18° below the horizon. |

At high latitudes a date may have no complete sunrise-to-sunset pair. The
missing events and `day_length` are then `None` and the applicable polar flag is
set, but `solar_noon` is still reported -- the Sun culminates on a day it never
rises -- and is `None` only when the backend cannot find the transit at all. On
transition dates sunrise and sunset may be present independently, and a paired
sunset may fall on the following civil date, so `day_length` can exceed 24
hours when daylight spans local midnight.
