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

The result contains `date`, `timezone`, `latitude`, `longitude`, `sunrise`,
`sunset`, `solar_noon`, `day_length`, `is_polar_day`, `is_polar_night`,
`civil_dawn`, `civil_dusk`, `nautical_dawn`, `nautical_dusk`,
`astronomical_dawn`, and `astronomical_dusk`.

At high latitudes a date may have no complete sunrise-to-sunset pair. Missing
events, `solar_noon`, or `day_length` are then `None`, and the applicable polar
flag is set. On transition dates sunrise and sunset may be present independently.

