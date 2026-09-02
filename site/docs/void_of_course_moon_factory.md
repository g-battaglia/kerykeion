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
Saturn in its current sign, until the next sign ingress. The five aspects
considered are conjunction, sextile, square, trine and opposition; the scan
reads them from its own `PTOLEMAIC_ASPECTS` name/degree tuple in
`kerykeion.void_of_course_moon.utils`, not from the top-level
`kerykeion.PTOLEMAIC_ASPECTS` used by the predictive modules. This calculation
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

**Raises** `KerykeionException` for an invalid timezone, an invalid zodiac
configuration, or a date outside the available ephemeris range.

## Range Search

`from_iso_range(start_date, end_date, *, zodiac_type="Tropical", sidereal_mode=None) -> VoidOfCourseWindowsCollectionModel`

Naive ISO inputs are treated as UTC; an offset-aware input is converted to UTC.
A date-only end includes that entire UTC day. Returned windows are not clipped:
the first can begin before `start_date` and the last can end after `end_date`
when they intersect the requested range.

**Raises** `KerykeionException` for a malformed ISO input, an invalid zodiac
configuration, or an ephemeris-range failure mid-scan.

## Models

All instants are timezone-aware UTC datetimes.

### `VoidOfCourseMoonModel`

| Field               | Type                     | Description                                                              |
| :------------------ | :----------------------- | :----------------------------------------------------------------------- |
| `is_void_of_course` | bool                     | `True` if the queried moment lies inside the void window.                 |
| `moon_sign`         | Sign                     | Sign the Moon currently occupies.                                         |
| `next_sign`         | Sign                     | Sign the Moon ingresses into next.                                        |
| `ingress`           | datetime                 | Moment the Moon enters `next_sign`; equals `void_end`.                    |
| `void_start`        | datetime                 | Last in-sign aspect, or the sign-entry moment for a whole-sign void.      |
| `void_end`          | datetime                 | End of the void window, equal to `ingress`.                               |
| `last_aspect`       | VoidOfCourseAspectModel or None | Last exact aspect before ingress; `None` for a whole-sign void.    |
| `next_aspect`       | VoidOfCourseAspectModel or None | First exact aspect after the ingress, which ends the lull.          |

### `VoidOfCourseWindowModel`

| Field              | Type                     | Description                                                        |
| :----------------- | :----------------------- | :------------------------------------------------------------------ |
| `moon_sign`        | Sign                     | Sign the Moon is leaving (where the void happens).                   |
| `next_sign`        | Sign                     | Sign the Moon ingresses into, ending the void.                       |
| `void_start`       | datetime                 | Start of the window — last in-sign aspect, or the sign-entry moment. |
| `void_end`         | datetime                 | End of the window, i.e. the ingress instant.                         |
| `duration_minutes` | float                    | Window length in minutes.                                            |
| `last_aspect`      | VoidOfCourseAspectModel or None | Aspect that opened the void; `None` for a whole-sign void.     |

### `VoidOfCourseWindowsCollectionModel`

| Field      | Type                           | Description                            |
| :--------- | :----------------------------- | :------------------------------------- |
| `start_jd` | float                          | Requested Julian Day (UT) range start. |
| `end_jd`   | float                          | Requested Julian Day (UT) range end.   |
| `windows`  | list[VoidOfCourseWindowModel]  | Chronological, non-overlapping windows. |

### `VoidOfCourseAspectModel`

| Field            | Type     | Description                                                        |
| :--------------- | :------- | :------------------------------------------------------------------ |
| `planet`         | str      | Body the Moon aspects (Sun, Mercury, Venus, Mars, Jupiter, Saturn). |
| `aspect`         | str      | Aspect name (conjunction, sextile, square, trine, opposition).      |
| `aspect_degrees` | float    | The aspect's exact angle in degrees (0, 60, 90, 120, 180).          |
| `exact_time`     | datetime | Moment the aspect perfects.                                          |
