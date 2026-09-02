---
title: 'Mundane Aspect Factory'
description: 'Find exact transiting-to-transiting aspect perfections over a UTC date range.'
category: 'Forecasting'
tags: ['docs', 'mundane aspects', 'aspectarian', 'transits', 'calendar', 'kerykeion']
order: 60
---

# Mundane Aspect Factory

`MundaneAspectFactory` produces an aspectarian: exact aspects between two
moving bodies over a range. Aspect times are zodiac-independent because the
same ayanamsha shifts both longitudes; reported longitudes and signs use the
requested tropical or sidereal zodiac.

## Basic Usage

```python
from kerykeion import MundaneAspectFactory

result = MundaneAspectFactory.from_iso_range(
    "2020-12-01", "2020-12-31",
    points=["Jupiter", "Saturn"],
    aspects=["conjunction"],
)
for event in result.aspects:
    print(event.iso_utc, event.point_a, event.aspect, event.point_b)
```

## Methods

### `from_iso_range`

`from_iso_range(start_date, end_date, points=None, aspects=None, zodiac_type="Tropical", sidereal_mode=None) -> MundaneAspectsCollectionModel`

Naive ISO inputs are treated as UTC; an offset-aware input is converted to UTC
before the scan. A date-only end includes the entire final day. A malformed ISO
string raises `KerykeionException`.

### `from_julian_day`

`from_julian_day(start_jd, end_jd, points=None, aspects=None, zodiac_type="Tropical", sidereal_mode=None) -> MundaneAspectsCollectionModel`

Both Julian bounds must be finite. Unknown point/aspect names and over-large
ranges raise `ValueError`; zodiac configuration and backend failures raise
`KerykeionException`.

By default the factory scans Sun through Pluto (Moon excluded) and the five
Ptolemaic aspects. Pass the Moon explicitly for lunar aspectarian events. An
explicit empty `points` or `aspects` list returns an empty collection.

## Accepted Names

`points` accepts these bodies, listed here in the canonical fast-to-slow order
that also fixes which member of a pair becomes `point_a`:

`Moon`, `Mercury`, `Venus`, `Sun`, `Mars`, `Jupiter`, `Saturn`, `Chiron`,
`Uranus`, `Neptune`, `Pluto`, `Mean_North_Lunar_Node`, `True_North_Lunar_Node`.

`aspects` accepts the longitude aspects of `DEFAULT_CHART_ASPECTS_SETTINGS`:
`conjunction`, `semi-sextile`, `semi-square`, `sextile`, `quintile`, `square`,
`trine`, `sesquiquadrate`, `biquintile`, `quincunx`, `opposition`. Declination
aspects (`parallel`, `contra-parallel`) are not longitude events and are
rejected with `ValueError`, as is any other unknown name.

## Models

### `MundaneAspectsCollectionModel`

| Field      | Type                      | Description                            |
| :--------- | :------------------------ | :------------------------------------- |
| `start_jd` | float                     | Requested Julian Day (UT) range start. |
| `end_jd`   | float                     | Requested Julian Day (UT) range end.   |
| `aspects`  | list[MundaneAspectModel]  | Chronologically ordered exact aspects. |

### `MundaneAspectModel`

Body ordering is canonical and independent of caller order.

| Field                | Type  | Description                                                   |
| :------------------- | :---- | :------------------------------------------------------------ |
| `point_a`            | str   | First body (canonical fast-to-slow order).                     |
| `point_b`            | str   | Second body.                                                   |
| `aspect`             | str   | Aspect name, e.g. `"square"`.                                  |
| `aspect_degrees`     | float | The aspect's exact angle in degrees.                           |
| `julian_day`         | float | Julian Day (UT) of the exact perfection.                       |
| `iso_utc`            | str   | ISO 8601 UTC datetime of the exact perfection.                 |
| `point_a_longitude`  | float | Ecliptic longitude of `point_a` at the event (requested zodiac). |
| `point_b_longitude`  | float | Ecliptic longitude of `point_b` at the event (requested zodiac). |
| `point_a_sign`       | Sign  | Sign of `point_a` at the event.                                |
| `point_b_sign`       | Sign  | Sign of `point_b` at the event.                                |
| `point_a_retrograde` | bool  | `True` if `point_a` is retrograde at the event.                |
| `point_b_retrograde` | bool  | `True` if `point_b` is retrograde at the event.                |
