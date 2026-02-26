---
title: 'Moon Phase Details Factory'
description: 'Generate rich lunar phase context including illumination, upcoming phases, eclipses, sunrise/sunset, and solar position from any astrological subject.'
category: 'Forecasting'
tags: ['docs', 'moon', 'lunar', 'phases', 'eclipses', 'kerykeion']
order: 12
---

# Moon Phase Details Factory

The `MoonPhaseDetailsFactory` builds a complete `MoonPhaseOverviewModel` from an existing `AstrologicalSubjectModel`. While the basic `LunarPhaseModel` attached to every subject provides the Sun-Moon angle, phase name, and emoji, this factory enriches that data into a full lunar context suitable for UI display, API responses, or detailed reports.

## What It Provides

| Section | Data |
| :--- | :--- |
| **Moon Summary** | Phase name, emoji, major phase label, waxing/waning stage, illumination percentage, age in days, lunar cycle progress, Sun and Moon zodiac signs |
| **Illumination Details** | Numeric percentage, visible fraction (0-1), phase angle in degrees |
| **Upcoming Phases** | Last and next occurrence of New Moon, First Quarter, Full Moon, Last Quarter (precise Swiss Ephemeris timing) |
| **Next Lunar Eclipse** | Date, timestamp, eclipse type (Total, Partial, Penumbral) |
| **Sun Info** | Sunrise, sunset, solar noon, day length, apparent altitude and azimuth |
| **Next Solar Eclipse** | Date, timestamp, eclipse type (Total, Annular, Partial, Hybrid) |
| **Location** | Latitude, longitude, default-location flag |

## Usage

```python
from kerykeion import AstrologicalSubjectFactory, MoonPhaseDetailsFactory

# 1. Create an astrological subject
subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    online=False,
)

# 2. Generate the moon phase overview
overview = MoonPhaseDetailsFactory.from_subject(subject)

# 3. Access the data
print(f"Phase: {overview.moon.phase_name} {overview.moon.emoji}")
print(f"Illumination: {overview.moon.illumination}")
print(f"Stage: {overview.moon.stage}")
print(f"Major Phase: {overview.moon.major_phase}")
print(f"Age: {overview.moon.age_days} days")
```

**Expected Output:**

```text
Phase: Waxing Crescent 🌒
Illumination: 2%
Stage: waxing
Major Phase: New Moon
Age: 1 days
```

## API Reference

### `MoonPhaseDetailsFactory.from_subject(...)`

```python
@classmethod
def from_subject(
    cls,
    subject: AstrologicalSubjectModel,
    *,
    using_default_location: bool = False,
    location_precision: int = 0,
) -> MoonPhaseOverviewModel
```

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `subject` | `AstrologicalSubjectModel` | **Required** | An astrological subject with Sun, Moon, and time/location data. |
| `using_default_location` | `bool` | `False` | Whether the location comes from a default configuration (metadata for API consumers). |
| `location_precision` | `int` | `0` | Optional precision indicator for the location coordinates. |

**Returns:** `MoonPhaseOverviewModel` with all sections populated.

## Accessing Nested Data

The returned `MoonPhaseOverviewModel` provides structured access to all data:

```python
overview = MoonPhaseDetailsFactory.from_subject(subject)

# Moon summary
moon = overview.moon
if moon.zodiac:
    print(f"Zodiac: Sun in {moon.zodiac.sun_sign}, Moon in {moon.zodiac.moon_sign}")

# Illumination details
if moon.detailed and moon.detailed.illumination_details:
    illum = moon.detailed.illumination_details
    print(f"Visible fraction: {illum.visible_fraction:.4f}")
    print(f"Phase angle: {illum.phase_angle:.2f}°")

# Upcoming phases
if moon.detailed and moon.detailed.upcoming_phases:
    phases = moon.detailed.upcoming_phases
    if phases.full_moon and phases.full_moon.next:
        print(f"Next Full Moon: {phases.full_moon.next.datestamp}")
    if phases.new_moon and phases.new_moon.last:
        print(f"Last New Moon: {phases.new_moon.last.datestamp}")

# Eclipses
if moon.next_lunar_eclipse:
    print(f"Next Lunar Eclipse: {moon.next_lunar_eclipse.datestamp}")
    print(f"Type: {moon.next_lunar_eclipse.type}")

# Sun info
if overview.sun:
    sun = overview.sun
    print(f"Sunrise: {sun.sunrise_timestamp}")
    print(f"Sunset: {sun.sunset_timestamp}")
    print(f"Day length: {sun.day_length}")
    if sun.position:
        print(f"Sun altitude: {sun.position.altitude:.2f}°")

    if sun.next_solar_eclipse:
        print(f"Next Solar Eclipse: {sun.next_solar_eclipse.datestamp}")
```

## JSON Serialization

The overview model is fully serializable via Pydantic:

```python
# Full JSON (excluding None fields for compact output)
print(overview.model_dump_json(exclude_none=True, indent=2))

# Python dict
data = overview.model_dump(exclude_none=True)
```

## Generating a Report

The `ReportGenerator` accepts `MoonPhaseOverviewModel` directly:

```python
from kerykeion import ReportGenerator

report = ReportGenerator(overview)
report.print_report()
```

This produces a formatted ASCII table report with sections for Moon Summary, Illumination Details, Upcoming Phases, Eclipses, Sun Info, and Location. See the [Report Module](/content/docs/report) documentation for details.

## Precision and Accuracy

- **Phase timings**: Binary search with Swiss Ephemeris converges to ~1 second precision for all major phase events.
- **Illumination formula**: Standard `k = 0.5 * (1 - cos(angle))` applied to the Sun-Moon ecliptic separation.
- **Lunar age**: Computed from the actual last New Moon timestamp (not a synodic-month approximation).
- **Eclipse search**: Uses `swe.sol_eclipse_when_glob` and `swe.lun_eclipse_when` for the next global eclipse of each type.
- **Sunrise/sunset**: Computed via `swe.rise_trans` with standard atmospheric refraction corrections.

## Edge Cases

- **Polar regions**: When the Sun does not rise or set (polar day/night), sunrise and sunset fields will be `None`.
- **Missing lunar phase**: If the subject was created with `calculate_lunar_phase=False`, the moon summary will contain only `None` fields.
- **No coordinates**: If the subject has no `lat`/`lng`, sun times and position will be `None`, and location fields will be empty.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
