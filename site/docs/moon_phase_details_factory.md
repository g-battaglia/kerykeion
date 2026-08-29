---
title: 'Moon Phase Details Factory'
description: 'Generate rich lunar phase context including illumination, upcoming phases, eclipses, sunrise/sunset, moonrise/moonset, and solar position from any astrological subject.'
category: 'Forecasting'
tags: ['docs', 'moon', 'lunar', 'phases', 'eclipses', 'kerykeion']
order: 12
---

# Moon Phase Details Factory

The `MoonPhaseDetailsFactory` builds a complete `MoonPhaseOverviewModel` from an existing `AstrologicalSubjectModel`. While the basic `LunarPhaseModel` attached to every subject provides the Sun-Moon angle, phase name, and emoji, this factory enriches that data into a full lunar context suitable for UI display, API responses, or detailed reports.

## What It Provides

| Section | Data |
| :--- | :--- |
| **Moon Summary** | Phase name, emoji, major phase label, waxing/waning stage, illumination percentage, age in days, precise age in days (`age_days_precise`), lunar cycle progress, Sun and Moon zodiac signs |
| **Moonrise / Moonset** | The two horizon crossings for the subject's civil day, as local ISO-8601 strings and Unix timestamps |
| **Illumination Details** | Numeric percentage, visible fraction (0-1), phase angle in degrees |
| **Upcoming Phases** | Last and next occurrence of New Moon, First Quarter, Full Moon, Last Quarter (precise ephemeris timing) |
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
Phase: Last Quarter 🌗
Illumination: 59%
Stage: waning
Major Phase: Last Quarter
Age: 22 days
```

## API Reference

### `MoonPhaseDetailsFactory.from_subject(...)`

```python
# doc-snippet: no-run — API signature reference
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

# Moonrise and moonset — local ISO strings, plus the same instants as Unix seconds.
# Either can be None: the Moon rises about 50 minutes later each day, so roughly
# one civil day in thirty has no moonrise and another has no moonset.
print(f"Moonrise: {moon.moonrise}")
print(f"Moonset: {moon.moonset}")
print(moon.moonrise_timestamp, moon.moonset_timestamp)

# Eclipses
if moon.next_lunar_eclipse:
    print(f"Next Lunar Eclipse: {moon.next_lunar_eclipse.datestamp}")
    print(f"Type: {moon.next_lunar_eclipse.type}")

# Sun info
if overview.sun:
    sun = overview.sun
    # sunrise/sunset are timezone-aware datetime objects; day_length is a timedelta
    print(f"Sunrise: {sun.sunrise:%H:%M}")
    print(f"Sunset: {sun.sunset:%H:%M}")
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

- **Phase timings**: Binary search on the ephemeris backend converges to ~1 second precision for all major phase events.
- **Illumination formula**: Standard `k = 0.5 * (1 - cos(angle))` applied to the Sun-Moon ecliptic separation.
- **Lunar age**: Computed from the actual last New Moon timestamp (not a synodic-month approximation).
- **Eclipse search**: Uses `ephe.sol_eclipse_when_glob` and `ephe.lun_eclipse_when` for the next global eclipse of each type.
- **Sunrise/sunset**: Computed via `ephe.rise_trans` with standard atmospheric refraction corrections.
- **Moonrise/moonset**: The same `rise_trans` call pointed at the Moon — same refracted upper limb, same standard atmosphere, plus the topocentric horizontal parallax the backend adds for it, which is what makes the answer the one an almanac prints. The civil day's two midnights are each resolved in the subject's zone rather than by adding 24 hours, and by the same rule, so a DST transition neither clips an event out of the day nor lets tomorrow's in. Where a zone changes offset AT 00:00 that rule has to choose: inside a fall-back fold the day opens at the FIRST of the two midnights (the repeated hour is already the new day), and across a spring-forward gap at the first instant past it — a 25-hour and a 23-hour day, each enclosing exactly its own hours. Both fields are timestamps in the subject's **local** zone, matching `sun.sunrise`.
- **`moonrise` is a `str`, `sunrise` is a `datetime`**: deliberate, and not going to change. The moon block mirrors the shape of the web APIs it was modelled on, where every field is a string or a number; the sun block is a native model and keeps native types. In `model_dump(mode="json")` the two agree in every zone but UTC, where the `datetime` serialises with a trailing `Z` and the string keeps the `+00:00` it was formatted with. Read `moonrise_timestamp` / `moonset_timestamp` (Unix seconds, UTC) when an instant rather than a rendering is what is wanted. Changing the field type would break every consumer already parsing the string.

## Edge Cases

- **Polar regions**: When the Sun does not rise or set (polar day/night), sunrise and sunset fields will be `None`.
- **Days without a moonrise or a moonset**: The Moon rises about 50 minutes later each day, so roughly one civil day in thirty has no moonrise at all, and another has no moonset. The backend always answers with the *next* event, which on those days belongs to tomorrow; anything falling outside the subject's own civil day is reported as `None` rather than passed off as today's.
- **Missing lunar phase**: If the subject was created with `calculate_lunar_phase=False`, the moon summary will contain only `None` fields — except `moonrise` / `moonset`, which are computed regardless, since a horizon crossing is a fact about the place and the day rather than about the phase.
- **No coordinates**: If the subject has no `lat`/`lng`, sun times and position will be `None`, and location fields will be empty.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
