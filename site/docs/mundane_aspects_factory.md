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

ISO inputs are treated as UTC; a date-only end includes the entire final day.

### `from_julian_day`

`from_julian_day(start_jd, end_jd, points=None, aspects=None, zodiac_type="Tropical", sidereal_mode=None) -> MundaneAspectsCollectionModel`

Both Julian bounds must be finite. Unknown point/aspect names and over-large
ranges raise `ValueError`; zodiac configuration and backend failures raise
`KerykeionException`.

By default the factory scans Sun through Pluto (Moon excluded) and the five
Ptolemaic aspects. Pass the Moon explicitly for lunar aspectarian events. An
explicit empty `points` or `aspects` list returns an empty collection.

## Models

`MundaneAspectsCollectionModel` contains `start_jd`, `end_jd`, and chronological
`aspects`. Each `MundaneAspectModel` contains `point_a`, `point_b`, `aspect`,
`aspect_degrees`, `julian_day`, `iso_utc`, both bodies' longitude/sign, and both
retrograde flags. Body ordering is canonical and independent of caller order.
