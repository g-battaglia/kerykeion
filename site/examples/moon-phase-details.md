---
title: 'Moon Phase Details'
tags: ['examples', 'moon', 'lunar', 'phases', 'eclipses', 'kerykeion']
order: 15
---

# Moon Phase Details

The `MoonPhaseDetailsFactory` generates a rich lunar context from any astrological subject. This page shows practical examples covering common use cases.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, MoonPhaseDetailsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 2025, 4, 1, 7, 51,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
)

overview = MoonPhaseDetailsFactory.from_subject(subject)

print(f"Phase:        {overview.moon.phase_name} {overview.moon.emoji}")
print(f"Illumination: {overview.moon.illumination}")
print(f"Stage:        {overview.moon.stage}")
print(f"Major Phase:  {overview.moon.major_phase}")
print(f"Age:          {overview.moon.age_days} days")
print(f"Cycle:        {overview.moon.lunar_cycle}")
```

**Output:**

```text
Phase:        Waxing Crescent 🌒
Illumination: 5%
Stage:        waxing
Major Phase:  New Moon
Age:          2 days
Cycle:        6.836%
```

## Upcoming Phases

Find the last and next occurrence of each major phase:

```python
if overview.moon.detailed and overview.moon.detailed.upcoming_phases:
    phases = overview.moon.detailed.upcoming_phases

    for label, window in [
        ("New Moon",      phases.new_moon),
        ("First Quarter", phases.first_quarter),
        ("Full Moon",     phases.full_moon),
        ("Last Quarter",  phases.last_quarter),
    ]:
        if window is None:
            continue
        last = window.last.datestamp if window.last else "N/A"
        nxt  = window.next.datestamp if window.next else "N/A"
        print(f"{label:15s}  Last: {last}")
        print(f"{'':15s}  Next: {nxt}")
        print()
```

**Output:**

```text
New Moon          Last: Sun, 30 Mar 2025 ...
                  Next: Mon, 28 Apr 2025 ...

First Quarter     Last: ...
                  Next: ...
...
```

## Eclipse Information

```python
# Next Lunar Eclipse
if overview.moon.next_lunar_eclipse:
    ecl = overview.moon.next_lunar_eclipse
    print(f"Next Lunar Eclipse: {ecl.datestamp}")
    print(f"Type: {ecl.type}")

# Next Solar Eclipse
if overview.sun and overview.sun.next_solar_eclipse:
    ecl = overview.sun.next_solar_eclipse
    print(f"Next Solar Eclipse: {ecl.datestamp}")
    print(f"Type: {ecl.type}")
```

## Sun Times and Position

```python
if overview.sun:
    sun = overview.sun

    print(f"Sunrise:    {sun.sunrise_timestamp}")
    print(f"Sunset:     {sun.sunset_timestamp}")
    print(f"Solar Noon: {sun.solar_noon}")
    print(f"Day Length: {sun.day_length}")

    if sun.position:
        print(f"Altitude:   {sun.position.altitude:.2f}°")
        print(f"Azimuth:    {sun.position.azimuth:.2f}°")
```

## Generating a Text Report

Pass the overview directly to `ReportGenerator` for a formatted ASCII report:

```python
from kerykeion import ReportGenerator

ReportGenerator(overview).print_report()
```

**Output:**

```text
=====================================================
Moon Phase Overview — Tue, 01 Apr 2025 06:51:00 +0000
=====================================================

+Moon Summary--+-------------------+
| Field        | Value             |
+--------------+-------------------+
| Phase Name   | Waxing Crescent 🌒|
| Major Phase  | New Moon          |
| Stage        | Waxing            |
| Illumination | 5%                |
| Age (days)   | 2                 |
| ...          | ...               |
+--------------+-------------------+

+Illumination Details--------+
| Field            | Value   |
+------------------+---------+
| Percentage       | 5.0%    |
| Visible Fraction | 0.0476  |
| Phase Angle      | 24.61°  |
+------------------+---------+

...
```

## JSON Serialization

```python
import json

# Compact JSON (no None fields)
json_str = overview.model_dump_json(exclude_none=True, indent=2)
print(json_str)

# Or as a Python dict
data = overview.model_dump(exclude_none=True)
```

## Zodiac Signs

```python
if overview.moon.zodiac:
    print(f"Sun Sign:  {overview.moon.zodiac.sun_sign}")
    print(f"Moon Sign: {overview.moon.zodiac.moon_sign}")
```

## Location Metadata

The factory can annotate whether a default location was used (useful for API consumers):

```python
overview = MoonPhaseDetailsFactory.from_subject(
    subject,
    using_default_location=True,
    location_precision=2,
)

loc = overview.location
print(f"Lat: {loc.latitude}, Lng: {loc.longitude}")
print(f"Default location: {loc.using_default_location}")
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
