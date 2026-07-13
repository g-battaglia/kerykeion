---
title: 'Void-of-Course Moon Factory'
description: 'Resolve the current void-of-course Moon or enumerate complete void windows over a UTC range.'
category: 'Forecasting'
tags: ['docs', 'void of course', 'moon', 'ingress', 'aspects', 'kerykeion']
order: 59
---

# Void-of-Course Moon Factory

`VoidOfCourseMoonFactory` uses the classical definition: the Moon is void after
its last exact Ptolemaic aspect to the Sun, Mercury, Venus, Mars, Jupiter, or
Saturn in its current sign, until the next sign ingress. The shared
`PTOLEMAIC_ASPECTS` constant names the five aspect families. This calculation
is geocentric and needs no observer coordinates.

## Current State

```python
from kerykeion import VoidOfCourseMoonFactory

state = VoidOfCourseMoonFactory.from_datetime(
    2026, 6, 1, 9, 0,
    tz_str="Europe/Rome",
)
print(state.is_void_of_course, state.moon_sign, state.next_sign)
print(state.void_start, state.void_end, state.last_aspect, state.next_aspect)
```

`from_datetime(year, month, day, hour, minute=0, *, tz_str, zodiac_type="Tropical", sidereal_mode=None) -> VoidOfCourseMoonModel`

For `zodiac_type="Sidereal"`, `sidereal_mode` is required; sign boundaries and
therefore void windows shift with the ayanamsha.

## Range Search

`from_iso_range(start_date, end_date, *, zodiac_type="Tropical", sidereal_mode=None) -> VoidOfCourseWindowsCollectionModel`

ISO inputs are treated as UTC. A date-only end includes that entire UTC day.
Returned windows are not clipped: the first can begin before `start_date` and
the last can end after `end_date` when they intersect the requested range.

## Models

- `VoidOfCourseMoonModel`: current boolean state, `moon_sign`, `next_sign`,
  `ingress`, `void_start`, `void_end`, `last_aspect`, and `next_aspect`.
- `VoidOfCourseWindowModel`: one full window, its signs, start/end,
  `duration_minutes`, and opening `last_aspect`.
- `VoidOfCourseWindowsCollectionModel`: requested `start_jd`/`end_jd` and the
  chronological `windows` list.
- `VoidOfCourseAspectModel`: target `planet`, `aspect`, exact angle, and
  timezone-aware UTC `exact_time`.

