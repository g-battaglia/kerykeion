---
title: 'Utilities Module'
description: 'Explore Kerykeions helper functions for coordinate conversions, house management, moon phases, and Julian date calculations.'
category: 'Reference'
tags: ['docs', 'utilities', 'math', 'kerykeion']
order: 16
---

# Utilities Module

The `utilities` module provides essential helper functions for astrological calculations, coordinate conversions, and data management.

## Coordinate & Position Helpers

Functions for handling circular degrees and zodiac positions.

| Function                                           | Description                                               |
| :------------------------------------------------- | :-------------------------------------------------------- |
| `get_number_from_name(name)`                       | Converts point name (e.g., "Sun") to Swiss Ephemeris ID.  |
| `get_kerykeion_point_from_degree(deg, name, point_type, speed=None, declination=None, magnitude=None, ecliptic_latitude=None)` | Creates a full `KerykeionPointModel` from a degree. |
| `circular_mean(pos1, pos2)`                        | Calculates mean of two angles, handling 0°/360° crossing. |
| `is_point_between(start, end, point, *, allow_reflex=False)` | Checks if a degree lies on the arc from `start` to `end`. The arc is the short way round unless `allow_reflex=True`. |
| `normalize_longitude(lng)`                         | A longitude into the `[-180, 180)` range the ephemeris backend expects. |
| `wrap_180(angle)`                                  | An angle into the signed range `[-180, 180)`. |
| `circular_sort(degrees)`                           | Sorts degrees clockwise starting from the first element.  |

```python
from kerykeion.utilities import circular_mean, get_kerykeion_point_from_degree

# Mean of 350° and 10° is 0° (not 180°)
mean = circular_mean(350, 10)

# Create object from degree
sun = get_kerykeion_point_from_degree(120.5, "Sun", "AstrologicalPoint")
print(f"{sun.sign} {sun.position:.2f}°") # Leo 0.50°
```

## House Management

Functions for working with astrological houses.

| Function                                     | Description                                                    |
| :------------------------------------------- | :------------------------------------------------------------- |
| `get_planet_house(planet_pos, active_cusps)` | Determines which house a planet falls into (returns a house name like `"First_House"`). Direction-aware: six house systems return descending cusps above roughly 67°, and the horizon system does it on the equator. |
| `house_spans(cusps)` | The twelve house widths and which of them run against the frame they were given. Use it to ask which way a chart's houses run before measuring anything across them. |
| `normalize_degree(angle)` | An angle into `[0, 360)`. Use it instead of `% 360`, which answers exactly `360.0` for a hair-negative input — outside the range every caller assumes. Propagates `NaN` rather than inventing `0`. |
| `get_house_name(number)`                     | Converts `1` to `"First_House"`.                               |
| `get_house_number(name)`                     | Converts `"First_House"` to `1`.                               |
| `get_houses_list(subject)`                   | Returns list of all 12 house objects from a subject.           |
| `validate_latitude(lat)`                     | Returns a finite latitude in [-90, 90] unchanged; otherwise raises `KerykeionException`. |
| `validate_longitude(lng)`                    | Returns a finite longitude in [-180, 180] unchanged; otherwise raises `KerykeionException`. |
| `check_and_adjust_polar_latitude(lat)`       | Clamps a latitude to the ±66° limit. Narrow use only — see below. |
| `angle_house_identities(cusps, asc, mc)`     | Which house each angle opens, for the angles this chart puts on a cusp. |
| `coincident_cusp_groups(cusps)`              | The sets of house numbers whose cusps stand on the same longitude. |
| `HOUSE_FIELD_NAMES`                          | The twelve subject attribute names, in order: `("first_house", ..., "twelfth_house")`. |

`check_and_adjust_polar_latitude` is **not** the general answer to a house system undefined inside the polar circle. A chart cast there keeps its real latitude and substitutes a house system that is defined everywhere; moving the observer instead would report cusps for a place the subject was not born in. The only remaining caller is `kerykeion/ephemeris_backend/backend.py`, inside the `clamp_latitude` branch, which serves Gauquelin sectors alone: their 36-sector division has no 12-cusp substitute, so retrying just inside the limit is the only way to produce that shape at all. Use `validate_latitude` for plain range checks.

```python
from kerykeion.utilities import get_planet_house, get_house_number

# Find the house containing a planet at 15° (cusps: 0° and 30°)
cusps = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
house_name = get_planet_house(15, cusps) # Returns "First_House"
house_num = get_house_number(house_name) # Returns 1
```

## Time & Dates

Functions for temporal conversions.

| Function                 | Description                                      |
| :----------------------- | :----------------------------------------------- |
| `datetime_to_julian(dt)` | Converts Python `datetime` to Julian Day number. |
| `julian_to_datetime(jd)` | Converts Julian Day number to Python `datetime`. |
| `civil_jd(year, month, day, hour=0.0)` | Julian Day of a civil moment in the engine's calendar convention. BCE-safe. |
| `civil_leap_year(year)`  | The leap rule in that same convention. |
| `jd_to_iso_date(jd)`     | ISO date of a Julian Day, BCE-safe. |
| `jd_to_iso_datetime(jd)` | ISO datetime (second resolution) of a Julian Day, BCE-safe. |
| `parse_astronomical_iso_moment(value)` | Parses a naive ISO date/datetime into `(year, month, day, decimal_hour)`, astronomical years included. |

### Timezones

| Function | Description |
| :------- | :---------- |
| `safe_timezone(tz_str)` | Resolves an IANA name to a `ZoneInfo`, raising `KerykeionException` if it is not one. |
| `is_nonexistent(naive, tz)` | Whether a naive wall time never occurred (spring-forward gap). |
| `is_ambiguous(naive, tz)` | Whether a naive wall time occurred twice (fall-back fold). |
| `localize_naive(naive, tz, *, is_dst=None)` | Attaches `tz` to a naive wall time, resolving a gap or fold explicitly rather than guessing. |

### Formatting

| Function | Description |
| :------- | :---------- |
| `format_ancient_iso(year, month, day, decimal_hour, utc_offset_hours)` | An ISO 8601 extended-year string for a possibly negative year. |
| `format_astronomical_iso_date(year, month, day)` | `YYYY-MM-DD` with astronomical year numbering (0 = 1 BCE, -1 = 2 BCE). |
| `format_iso_display(iso, fmt="%Y-%m-%d %H:%M")` | Formats an ISO datetime string for display, BCE included. |
| `extract_year_from_iso(iso)` | The year as an `int`, BCE dates included. |
| `format_degrees_below_bound(value, upper_bound, decimals=2)` | Formats a degree so the *rounded* string stays below `upper_bound` — a position of 29.999° never prints as `30.00`. |
| `format_timedelta_hhmm(td)` | Renders a duration as `H:MM`, rounded to whole minutes. |

### Subject Frames and Anchors

Helpers that read a subject-like model without caring which model it is.

| Function | Description |
| :------- | :---------- |
| `has_terrestrial_frame(subject)` | Whether the subject's planet longitudes share the angles' Earth frame. |
| `require_same_frame(first, second)` | Raises when two subjects' reference frames differ — the guard a dual chart needs before comparing them. |
| `TERRESTRIAL_PERSPECTIVES` | The `frozenset` those two test against: `Apparent Geocentric`, `True Geocentric`, `Topocentric`. |
| `resolve_sect_is_diurnal(subject)` | Sect (day/night), defaulting to day. |
| `resolve_subject_birth_datetime(subject)` | Local (naive) birth or anchor datetime. |
| `resolve_subject_local_moment(subject)` | The same moment as `(year, month, day, decimal_hour)`. |
| `resolve_subject_local_now(subject)` | Current wall-clock time in the subject's own timezone, naive. |

```python
from kerykeion.utilities import datetime_to_julian
from datetime import datetime

jd = datetime_to_julian(datetime(2000, 1, 1, 12, 0, 0))
# Returns 2451545.0
```

## Lunar Data

Helper function to calculate accurate lunar phases.

| Function                                  | Description                                                        |
| :---------------------------------------- | :----------------------------------------------------------------- |
| `calculate_moon_phase(moon_deg, sun_deg)` | Returns `LunarPhaseModel` with the Sun-Moon angle, the lunation day (1-28), the phase name and emoji, the nearest major phase, and the waxing/waning stage. |

```python
from kerykeion.utilities import calculate_moon_phase

phase = calculate_moon_phase(180, 0) # Full Moon
print(f"{phase.moon_emoji} {phase.moon_phase_name}")
```

The name and the emoji come from windows **centred on the syzygies**: New and Full span ±6.4286° of the exact aspect, the two quarters ±19.2857°, and the four crescent/gibbous names fill the rest. The name therefore tracks the event rather than a bin boundary. The `moon_phase` index (1-28) is unchanged.

## Data Utilities

General purpose tools for list management, logging, and SVG optimization.

| Function                                          | Description                                           |
| :------------------------------------------------ | :---------------------------------------------------- |
| `get_available_astrological_points_list(subject)` | Returns list of all active points in a subject.       |
| `find_common_active_points(list_a, list_b)`       | Returns intersection of two point lists.              |
| `setup_logging(level)`                            | Configures Kerykeion's internal logger.               |
| `inline_css_variables_in_svg(svg_content)`        | Replaces CSS variables with static values for export. |
| `normalize_zodiac_type(str)`                      | Normalizes string to "Tropical" or "Sidereal".        |
| `distribute_percentages_to_100(values)`           | Rounds percentages ensuring they sum exactly to 100%. |
| `strip_illegal_control_chars(value)`              | Drops XML-1.0-illegal and terminal-control characters from a stringified value, so user text cannot break the SVG or the terminal. |

## Lunar Helpers

Additional moon phase formatting utilities.

| Function                                     | Description                        |
| :------------------------------------------- | :--------------------------------- |
| `lunar_phase_name_from_degrees(degrees)`     | Returns `(name, emoji)` for a Sun-Moon separation. This is where a chart's phase name comes from. |
| `lunar_major_phase_from_degrees(degrees)`    | Returns the nearest of the four major phases. |
| `lunar_stage_from_degrees(degrees)`          | Returns `"waxing"` or `"waning"`.  |
| `get_moon_emoji_from_phase_int(phase)`       | Returns emoji for a lunation day (1-28). Approximate — see below. |
| `get_moon_phase_name_from_phase_int(phase)`  | Returns name for a lunation day (1-28). Approximate — see below.  |

The name windows are centred on the events they name: half a bin either side of the two syzygies, one and a half bins either side of the quarters. The two `*_from_phase_int` helpers read the 1-28 lunation day instead, whose bins are offset from the events — bin 1 begins at the conjunction rather than straddling it — so near an event they can answer with the neighbouring name. They are kept for callers that hold the integer and nothing else; anything holding the degrees should call `lunar_phase_name_from_degrees`.

```python
from kerykeion.utilities import lunar_phase_name_from_degrees

print(lunar_phase_name_from_degrees(180.5))  # ('Full Moon', '🌕')
```

Both take only the 1-28 index, so they cannot use the centred windows described above: they are the older 28-bin approximation, kept for callers that hold an index and nothing else, and they disagree with `LunarPhaseModel.moon_phase_name` near a boundary. Read the fields off the model when you have it.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
