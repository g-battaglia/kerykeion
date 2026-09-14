---
title: 'Composite Chart'
tags: ['examples', 'composite', 'davison', 'relationships', 'charts', 'kerykeion']
order: 20
---

# Composite Chart

A composite chart is a single chart standing for the relationship itself, rather
than a comparison of two charts the way synastry is. `CompositeSubjectFactory`
builds one two ways from the same pair of subjects.

| Method | What it does |
| :--- | :--- |
| `get_midpoint_composite_subject_model()` | Averages the two charts: every position is the midpoint of the two. |
| `get_davison_composite_subject_model()` | Averages the two birth **moments** and **places**, then casts a real chart for that derived date and location. |

## Midpoint composite

```python
from pathlib import Path

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    CompositeSubjectFactory,
)

angelina = AstrologicalSubjectFactory.from_birth_data(
    "Angelina Jolie", 1975, 6, 4, 9, 9,
    city="Los Angeles", nation="US",
    lng=-118.15, lat=34.03, tz_str="America/Los_Angeles",
    online=False,
)
brad = AstrologicalSubjectFactory.from_birth_data(
    "Brad Pitt", 1963, 12, 18, 6, 31,
    city="Shawnee", nation="US",
    lng=-96.56, lat=35.20, tz_str="America/Chicago",
    online=False,
)

factory = CompositeSubjectFactory(angelina, brad)
composite = factory.get_midpoint_composite_subject_model()

print(composite.name)
print(composite.composite_chart_type)
print(f"Sun: {composite.sun.sign} {composite.sun.abs_pos:.2f}°")
print(f"Moon: {composite.moon.sign} {composite.moon.abs_pos:.2f}°")
print(f"Ascendant: {composite.first_house.sign} {composite.first_house.abs_pos:.2f}°")
```

**Output:**
```
Angelina Jolie and Brad Pitt Composite Chart
Midpoint
Sun: Pis 349.64°
Moon: Pis 332.96°
Ascendant: Lib 185.62°
```

The result is a `CompositeSubjectModel`, which `ChartDataFactory` draws like any
other subject:

```python
chart_data = ChartDataFactory.create_composite_chart_data(composite)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
ChartDrawer(chart_data).save_svg(
    output_path=output_dir,
    filename="jolie-pitt-composite",
)
```

![Midpoint composite chart](https://raw.githubusercontent.com/g-battaglia/kerykeion/refs/heads/alpha/v6/tests/data/svg/Angelina%20Jolie%20and%20Brad%20Pitt%20Composite%20Chart%20-%20Composite%20Chart%20-%20Modern.svg)

## Davison composite

The Davison chart is a real chart: its positions actually occurred, at a moment
and a place halfway between the two births.

```python
davison = factory.get_davison_composite_subject_model()

print(davison.composite_chart_type)
print(davison.iso_formatted_utc_datetime)
print(f"{davison.lat:.3f}, {davison.lng:.3f}")
print(f"Sun: {davison.sun.sign} {davison.sun.abs_pos:.2f}°")
```

**Output:**
```
Davison
1969-09-10T14:20:00+00:00
34.615, -107.355
Sun: Vir 167.69°
```

The two methods give different charts on purpose: the midpoint composite is an
average of two skies, the Davison is one sky that existed.

## `house_anchor`

Between two points on a circle there are two midpoints, half a turn apart.
Taking the nearer one for each of the twelve cusps independently breaks down
when the two charts' angles are nearly opposed — the choice flips partway round
the ring, and the twelve arcs come to 1080° instead of 360°. About one pair in
sixteen is affected.

`house_anchor` decides which angle is held at its near midpoint while the others
move, which is how the field repairs it:

| Value | Behaviour |
| :--- | :--- |
| `"auto"` (default) | Whichever of the Ascendant and the Midheaven has its two base cusps closer together. |
| `"ascendant"` | Hold the Ascendant. |
| `"midheaven"` | Hold the Midheaven. |

Anything else raises `KerykeionException`.

```python
anchored = CompositeSubjectFactory(
    angelina, brad, house_anchor="midheaven"
).get_midpoint_composite_subject_model()

print(anchored.house_anchor)  # what was asked for
print(anchored.house_frame)   # what was actually built
```

`house_frame` reports the outcome rather than the request: `"anchored"` (a frame
was hung from the angle and the twelve cover the circle exactly once),
`"midpoints"` (no frame spans the two charts, so every cusp is its own near
midpoint and the twelve are still a house division), or `"gapped"` (as
`"midpoints"`, but the twelve leave gaps). A Davison chart averages no cusps, so
both fields are `None` on it.

## What the two subjects must agree on

The midpoint method averages cusps, so both parents' cusps have to come from the
same house division — and a subject's *requested* and *effective* systems can
differ, since a quadrant system is substituted inside the polar circle. The
factory compares `effective_houses_system_identifier` and refuses with a message
naming both. Zodiac type, sidereal mode, custom ayanamsa values, house system
name and perspective must match too.

A Davison composite is free of all of it: it recasts a whole new chart rather
than averaging cusps.

See [Composite Subject Factory](/content/docs/composite_subject_factory) for the
full methodology, and [Relationship Score](/content/examples/relationship-score)
for the other way of measuring a pair.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
