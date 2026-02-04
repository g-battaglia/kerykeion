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
| `get_kerykeion_point_from_degree(deg, name, type)` | Creates a full `KerykeionPointModel` from a degree.       |
| `circular_mean(pos1, pos2)`                        | Calculates mean of two angles, handling 0°/360° crossing. |
| `is_point_between(start, end, point)`              | Checks if a degree lies between two others on a circle.   |
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
| `get_planet_house(planet_pos, active_cusps)` | Determines which house a planet falls into.                    |
| `get_house_name(number)`                     | Converts `1` to `"First_House"`.                               |
| `get_house_number(name)`                     | Converts `"First_House"` to `1`.                               |
| `get_houses_list(subject)`                   | Returns list of all 12 house objects from a subject.           |
| `check_and_adjust_polar_latitude(lat)`       | Adjusts extreme latitudes to prevent house calculation errors. |

```python
from kerykeion.utilities import get_planet_house

# Check if a planet at 15° is in the first house (cusps: 0° and 30°)
cusps = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
house_num = get_planet_house(15, cusps) # Returns 1
```

## Time & Dates

Functions for temporal conversions.

| Function                 | Description                                      |
| :----------------------- | :----------------------------------------------- |
| `datetime_to_julian(dt)` | Converts Python `datetime` to Julian Day number. |
| `julian_to_datetime(jd)` | Converts Julian Day number to Python `datetime`. |

```python
from kerykeion.utilities import datetime_to_julian
from datetime import datetime

jd = datetime_to_julian(datetime(2000, 1, 1, 12, 0, 0))
# Returns 2451545.0
```

## Lunar Data

Helper function to calculate accurate lunar phases and illumination.

| Function                                  | Description                                                        |
| :---------------------------------------- | :----------------------------------------------------------------- |
| `calculate_moon_phase(moon_deg, sun_deg)` | Returns `MoonPhaseModel` with phase name, emoji, and illumination. |

```python
from kerykeion.utilities import calculate_moon_phase

phase = calculate_moon_phase(180, 0) # Full Moon
print(f"{phase.moon_emoji} {phase.moon_phase_name}")
```

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

## Lunar Helpers

Additional moon phase formatting utilities.

| Function                                    | Description                        |
| :------------------------------------------ | :--------------------------------- |
| `get_moon_emoji_from_phase_int(phase)`      | Returns emoji for 0-7 phase index. |
| `get_moon_phase_name_from_phase_int(phase)` | Returns name for 0-7 phase index.  |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
