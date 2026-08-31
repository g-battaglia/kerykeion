---
title: 'Ephemeris Data'
tags: ['examples', 'ephemeris', 'time-series', 'planetary positions', 'kerykeion']
order: 17
---

# Ephemeris Data

The `EphemerisDataFactory` generates time-series planetary position data across date ranges. It is useful for tracking planetary movements, ingresses, and building ephemeris tables.

## Basic Usage

Generate daily planetary positions for a one-month period:

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory

factory = EphemerisDataFactory(
    start_datetime=datetime(2025, 1, 1),
    end_datetime=datetime(2025, 1, 31),
    step_type="days",
    step=1,
    lat=41.9028,
    lng=12.4964,
    tz_str="Europe/Rome",
)

data = factory.get_ephemeris_data()

# Each entry contains date, planets, and houses
for entry in data[:3]:
    print(f"Date: {entry['date']}")
    for planet in entry["planets"][:3]:
        print(f"  {planet['name']}: {planet['sign']} at {planet['position']:.2f}°")
    print()
```

## Hourly Data

Track faster-moving bodies with hourly resolution:

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory

factory = EphemerisDataFactory(
    start_datetime=datetime(2025, 3, 20, 0, 0),
    end_datetime=datetime(2025, 3, 21, 0, 0),
    step_type="hours",
    step=1,
    lat=51.5074,
    lng=-0.1278,
    tz_str="Europe/London",
)

data = factory.get_ephemeris_data()
print(f"Generated {len(data)} hourly data points")

# Track the Moon's movement through the day
for entry in data:
    moon = next(p for p in entry["planets"] if p["name"] == "Moon")
    print(f"{entry['date']}: Moon at {moon['position']:.4f}° {moon['sign']}")
```

## Getting Full Subject Models

Use `get_ephemeris_data_as_astrological_subjects()` to get full `AstrologicalSubjectModel` instances, giving access to all Kerykeion features for each time point:

```python
from datetime import datetime
from kerykeion import EphemerisDataFactory

factory = EphemerisDataFactory(
    start_datetime=datetime(2025, 1, 1),
    end_datetime=datetime(2025, 1, 7),
    step_type="days",
    step=1,
    lat=41.9028,
    lng=12.4964,
    tz_str="Europe/Rome",
)

subjects = factory.get_ephemeris_data_as_astrological_subjects()

for subject in subjects:
    # subject.name is "Now" for every sample — the date is on the model itself
    print(f"{subject.iso_formatted_local_datetime[:10]}: "
          f"Sun in {subject.sun.sign}, Moon in {subject.moon.sign}")
```

## Constructor Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `start_datetime` | `datetime` | **Required** | Start of the date range |
| `end_datetime` | `datetime` | **Required** | End of the date range |
| `step_type` | `"days"`, `"hours"`, `"minutes"` | `"days"` | Time interval unit |
| `step` | `int` | `1` | Number of units per step |
| `lat` | `float` | `51.4769` | Latitude for house calculations |
| `lng` | `float` | `0.0005` | Longitude for house calculations |
| `tz_str` | `str` | `"Etc/UTC"` | Timezone string |
| `is_dst` | `bool` | `False` | How to resolve a wall time that falls in a DST fold |
| `zodiac_type` | `ZodiacType` | `"Tropical"` | Tropical or Sidereal zodiac |
| `sidereal_mode` | `SiderealMode` | `None` | Ayanamsa for sidereal mode |
| `custom_ayanamsa_t0` | `float \| None` | `None` | Reference Julian Day for `sidereal_mode="USER"` |
| `custom_ayanamsa_ayan_t0` | `float \| None` | `None` | Ayanamsa value at `custom_ayanamsa_t0` |
| `houses_system_identifier` | `str` | `"P"` | House system (Placidus default) |
| `perspective_type` | `PerspectiveType` | `"Apparent Geocentric"` | Observation perspective |
| `active_points` | `list[AstrologicalPoint] \| None` | `None` | Points each sample computes; `None` uses the default 14 |
| `active_fixed_stars` | `list[str] \| None` | `None` | Fixed stars each sample computes |
| `altitude` | `float \| None` | `None` | Observer altitude in metres, for topocentric work |
| `max_days` | `int` | `730` | Safety limit for day ranges |
| `max_hours` | `int` | `8760` | Safety limit for hour ranges |
| `max_minutes` | `int` | `525600` | Safety limit for minute ranges |

## Methods

| Method | Returns | Description |
| :--- | :--- | :--- |
| `get_ephemeris_data()` | `list[dict]` | Raw dicts with `date`, `planets`, `houses` |
| `get_ephemeris_data_as_astrological_subjects()` | `list[AstrologicalSubjectModel]` | Full subject models for each time point |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
