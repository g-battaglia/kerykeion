---
title: 'Ephemeris Data Factory'
description: 'Generate time-series astrological data with the Ephemeris Data Factory. Perfect for creating planetary positions for any date range and interval.'
category: 'Forecasting'
tags: ['docs', 'ephemeris', 'data', 'kerykeion']
order: 14
---

# Ephemeris Data Factory

The `EphemerisDataFactory` generates time-series astrological data (ephemerides) for a specified date range and interval.

## Basic Usage

Initialize the factory with a start and end date to generate a list of planetary positions.

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory

# 1. Define Range
start = datetime(2024, 1, 1)
end = datetime(2024, 1, 31)

# 2. Initialize Factory
factory = EphemerisDataFactory(
    start,
    end,
    step_type="days", # "days", "hours", or "minutes"
    step=1, # Interval size
    lat=51.5074,
    lng=-0.1278,
    tz_str="Europe/London"
)

# 3. Get Data (List of Dictionaries)
data = factory.get_ephemeris_data()
print(f"Sun 1st Day: {data[0]['planets'][0]['abs_pos']:.2f}°")
```

## Methods

### `get_ephemeris_data()`

Returns a list of dictionaries. Fast and lightweight. Best for raw data processing.

**Output Structure:**

```json
[
  {
    "date": "2024-01-01T00:00:00",
    "planets": [
      { "name": "Sun", "abs_pos": 280.23, "sign": "Cap", ... },
      ...
    ]
  },
  ...
]
```

### `get_ephemeris_data_as_astrological_subjects()`

Returns a list of full `AstrologicalSubjectModel` objects. Slower but provides full analysis capabilities (aspects, houses, etc.).

```python
subjects = factory.get_ephemeris_data_as_astrological_subjects()
print(subjects[0].sun.sign)
```

## Configuration

### Time Parameters

| Parameter     | Description                  | Options                          |
| :------------ | :--------------------------- | :------------------------------- |
| `step_type`   | Unit of time step            | `"days"`, `"hours"`, `"minutes"` |
| `step`        | Multiplier for step type     | Integer (e.g. `1`, `7`)          |
| `max_days`    | Safety limit for daily data  | Default: 730                     |
| `max_hours`   | Safety limit for hourly data | Default: 8760                    |
| `max_minutes` | Safety limit for minute data | Default: 525600                  |

### Location Parameters

| Parameter | Description               | Default            |
| :-------- | :------------------------ | :----------------- |
| `lat`     | Latitude for house cusps  | `51.4769` (London) |
| `lng`     | Longitude for house cusps | `0.0005`           |
| `tz_str`  | Timezone string           | `"Etc/UTC"`        |
| `is_dst`  | Daylight saving time flag | `False`            |

### Calculation Parameters

| Parameter                  | Description                 | Default                 |
| :------------------------- | :-------------------------- | :---------------------- |
| `zodiac_type`              | Tropical or Sidereal        | `"Tropical"`            |
| `sidereal_mode`            | Ayanamsa mode (if Sidereal) | `None`                  |
| `houses_system_identifier` | House system code           | `"P"` (Placidus)        |
| `perspective_type`         | Calculation perspective     | `"Apparent Geocentric"` |

_Note: You can override safety limits by passing `None` if you need large datasets._

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
