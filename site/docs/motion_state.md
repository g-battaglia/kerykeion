---
title: 'Motion State'
description: 'Per-point motion classification — fast, average, slow, retrograde and stationary states from ecliptic speed.'
category: 'Analysis'
tags: ['docs', 'motion', 'retrograde', 'station', 'kerykeion']
order: 43
---

# Motion State

Every computed point carries its instantaneous ecliptic `speed` (degrees/day),
a `retrograde` flag and a `motion_state` classified in `kerykeion/motion` by
`classify_motion_state()` against the body's mean daily motion: stationary
(inside a band around zero), retrograde (negative speed), slow (below 80%),
fast (above 120%) or average.

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Jane", 1990, 7, 15, 10, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)

print(subject.mars.motion_state, subject.mars.speed, subject.mars.retrograde)
```

A station is reported as `stationary_retrograde` (turning backwards) or
`stationary_direct` (resuming forward motion) whenever a second speed sample
can establish the trend; without it the generic `stationary` is returned rather
than a guess. Classification uses geocentric mean motions, so it is attached
for Earth-centred perspectives only — heliocentric speeds have no retrograde.

Related: [Schemas](/content/docs/schemas),
[Retrograde Stations](/content/docs/retrograde_station_factory).
