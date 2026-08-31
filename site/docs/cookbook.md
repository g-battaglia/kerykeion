---
title: 'Cookbook'
description: 'Practical recipes and code snippets for common astrological tasks'
category: 'Reference'
tags: ['docs', 'cookbook', 'recipes', 'examples', 'how-to']
order: 15
---

# Cookbook

This cookbook contains practical recipes for common astrological tasks. Each recipe is self-contained and can be copied directly into your projects.

## Table of Contents

- [Working with Aspects](#working-with-aspects)
- [Batch Processing](#batch-processing)
- [Data Export](#data-export)
- [Custom Configurations](#custom-configurations)
- [Advanced Calculations](#advanced-calculations)
- [Performance Optimization](#performance-optimization)

---

## Working with Aspects

### Find All Conjunctions in a Chart

```python
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

aspects = AspectsFactory.single_chart_aspects(subject)

conjunctions = [a for a in aspects.aspects if a.aspect == "conjunction"]

for conj in conjunctions:
    print(f"{conj.p1_name} conjunct {conj.p2_name} (orb: {conj.orbit:.2f}°)")
```

**Output:**
```
Sun conjunct Jupiter (orb: 0.12°)
Sun conjunct Chiron (orb: 3.43°)
Jupiter conjunct Chiron (orb: 3.31°)
Uranus conjunct Neptune (orb: 5.95°)
```

### Find Applying vs Separating Aspects

```python
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

aspects = AspectsFactory.single_chart_aspects(subject)

applying = [a for a in aspects.aspects if a.aspect_movement == "Applying"]
separating = [a for a in aspects.aspects if a.aspect_movement == "Separating"]

print(f"Applying aspects: {len(applying)}")
print(f"Separating aspects: {len(separating)}")

# Applying aspects are considered stronger
print("\nStrongest applying aspects:")
for asp in sorted(applying, key=lambda x: x.orbit)[:5]:
    print(f"  {asp.p1_name} {asp.aspect} {asp.p2_name} ({asp.orbit:.2f}°)")
```

### Filter Aspects by Orb Tightness

```python
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

aspects = AspectsFactory.single_chart_aspects(subject)

# Only aspects within 2 degrees (very tight)
tight_aspects = [a for a in aspects.aspects if a.orbit <= 2.0]

print(f"Found {len(tight_aspects)} tight aspects (orb <= 2°):")
for asp in tight_aspects:
    print(f"  {asp.p1_name} {asp.aspect} {asp.p2_name} ({asp.orbit:.2f}°)")
```

### Count Aspects by Type

```python
from collections import Counter
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

aspects = AspectsFactory.single_chart_aspects(subject)

aspect_counts = Counter(a.aspect for a in aspects.aspects)

print("Aspect distribution:")
for aspect_name, count in aspect_counts.most_common():
    print(f"  {aspect_name}: {count}")
```

**Output:**
```
Aspect distribution:
  square: 8
  sextile: 6
  conjunction: 4
  opposition: 4
  trine: 3
```

---

## Batch Processing

### Process Multiple Birth Charts

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer
from pathlib import Path

# Sample birth data
people = [
    {"name": "Alice", "year": 1990, "month": 3, "day": 15, "hour": 10, "minute": 30},
    {"name": "Bob", "year": 1988, "month": 7, "day": 22, "hour": 14, "minute": 0},
    {"name": "Carol", "year": 1995, "month": 12, "day": 8, "hour": 8, "minute": 45},
]

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

for person in people:
    subject = AstrologicalSubjectFactory.from_birth_data(
        person["name"], person["year"], person["month"], person["day"],
        person["hour"], person["minute"],
        lng=-0.1276, lat=51.5074, tz_str="Europe/London",
        online=False
    )
    
    chart_data = ChartDataFactory.create_natal_chart_data(subject)
    drawer = ChartDrawer(chart_data=chart_data)
    drawer.save_svg(output_path=output_dir, filename=f"{person['name'].lower()}-natal")
    
    print(f"Generated chart for {person['name']}: {subject.sun.sign} Sun, {subject.moon.sign} Moon")
```

### Generate All Synastry Combinations

```python
from itertools import combinations
from kerykeion import AstrologicalSubjectFactory, AspectsFactory
from kerykeion.relationship_score.factory import RelationshipScoreFactory

# Create subjects
subjects = []
people_data = [
    ("Alice", 1990, 3, 15, 10, 30),
    ("Bob", 1988, 7, 22, 14, 0),
    ("Carol", 1995, 12, 8, 8, 45),
]

for name, year, month, day, hour, minute in people_data:
    subject = AstrologicalSubjectFactory.from_birth_data(
        name, year, month, day, hour, minute,
        lng=-0.1276, lat=51.5074, tz_str="Europe/London",
        online=False
    )
    subjects.append(subject)

# Generate all pairs
print("Compatibility Scores:\n")
for person1, person2 in combinations(subjects, 2):
    score = RelationshipScoreFactory(person1, person2).get_relationship_score()
    aspects = AspectsFactory.dual_chart_aspects(person1, person2)
    
    print(f"{person1.name} + {person2.name}:")
    print(f"  Score: {score.score_value} ({score.score_description})")
    print(f"  Aspects: {len(aspects.aspects)}")
    print()
```

---

## Data Export

### Export Chart Data to JSON

```python
import json
from pathlib import Path

from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Export to JSON
json_output = chart_data.model_dump_json(indent=2)

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

with open(output_dir / "chart_data.json", "w") as f:
    f.write(json_output)

print("Chart data exported to charts_output/chart_data.json")
```

### Export Planetary Positions to CSV

```python
import csv
from pathlib import Path

from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

planets = ["sun", "moon", "mercury", "venus", "mars", 
           "jupiter", "saturn", "uranus", "neptune", "pluto"]

output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

with open(output_dir / "planetary_positions.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Planet", "Sign", "Position", "House", "Retrograde", "Speed", "Declination", "Magnitude"])
    
    for planet_name in planets:
        planet = getattr(subject, planet_name)
        writer.writerow([
            planet.name,
            planet.sign,
            f"{planet.position:.2f}",
            planet.house,
            planet.retrograde,
            f"{planet.speed:.4f}" if planet.speed is not None else "",
            f"{planet.declination:.4f}" if planet.declination is not None else "",
            f"{planet.magnitude:.2f}" if planet.magnitude is not None else "",
        ])

print("Positions exported to charts_output/planetary_positions.csv")
```

**Output CSV:**
```csv
Planet,Sign,Position,House,Retrograde,Speed,Declination,Magnitude
Sun,Can,22.65,Tenth_House,False,0.9539,21.5399,
Moon,Ari,21.80,Eighth_House,False,14.0131,13.1955,
...
```

### Export Ephemeris Data to Pandas DataFrame

> **Requires pandas** (not a Kerykeion dependency): `pip install pandas`.

```python
# doc-snippet: no-run — requires optional pandas dependency
import pandas as pd
from datetime import datetime
from kerykeion.ephemeris_data.factory import EphemerisDataFactory

ephemeris = EphemerisDataFactory(
    start_datetime=datetime(2024, 1, 1),
    end_datetime=datetime(2024, 1, 31),
    step_type="days",
    step=1,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London"
)

data = ephemeris.get_ephemeris_data()

# Convert to DataFrame
rows = []
for entry in data:
    for planet in entry["planets"]:
        rows.append({
            "date": entry["date"],
            "planet": planet["name"],
            "sign": planet["sign"],
            "position": planet["position"],
            "abs_pos": planet["abs_pos"],
            "retrograde": planet["retrograde"],
            "speed": planet.get("speed"),
            "declination": planet.get("declination"),
            "magnitude": planet.get("magnitude"),
        })

df = pd.DataFrame(rows)
df.to_csv("ephemeris_january_2024.csv", index=False)

print(f"Exported {len(df)} rows to ephemeris_january_2024.csv")
```

---

## Custom Configurations

### Using Custom Aspect Orbs

```python
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Define custom tight orbs
custom_aspects = [
    {"name": "conjunction", "orb": 6},  # Same as default 6
    {"name": "opposition", "orb": 6},   # Same as default 6
    {"name": "trine", "orb": 5},        # Tighter than default 6
    {"name": "square", "orb": 4},       # Tighter than default 6
    {"name": "sextile", "orb": 3},      # Tighter than default 5
]

aspects = AspectsFactory.single_chart_aspects(
    subject,
    active_aspects=custom_aspects
)

print(f"Found {len(aspects.aspects)} aspects with tight orbs")
```

### Limiting Active Points

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer
from pathlib import Path

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Only traditional 7 planets + angles
traditional_points = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Ascendant", "Medium_Coeli"
]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=traditional_points
)

drawer = ChartDrawer(chart_data=chart_data)
output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)
drawer.save_svg(output_path=output_dir, filename="traditional-planets-only")
```

### Including All Available Points

`active_points` must be passed to `AstrologicalSubjectFactory.from_birth_data`:
that is where the points are computed. The same argument on
`ChartDataFactory.create_natal_chart_data` only *narrows* what the subject
already carries, so handing the full preset to the chart data factory alone
leaves the 14 default points untouched.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    active_points=ALL_ACTIVE_POINTS,
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)

print(f"Chart includes {len(chart_data.subject.active_points)} points")
```

**Output:**
```
Chart includes 52 points
```

`ALL_ACTIVE_POINTS` holds 53 names; `Earth` is dropped with an informational log
line in the default Apparent Geocentric perspective, since it has no position as
seen from itself. Switch to `perspective_type="Heliocentric"` and the Sun goes
instead.

---

## Advanced Calculations

### Find the Next Exact Aspect

`TransitsTimeRangeFactory.get_transit_events()` groups a scanned range into
discrete events; `refine_exact_moments=True` then ternary-searches between the
two bracketing samples for the sub-step instant of exactness.

```python
from datetime import datetime, timedelta

from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_data.factory import EphemerisDataFactory
from kerykeion.transits.factory import TransitsTimeRangeFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
)

start = datetime(2024, 1, 1)
ephemeris = EphemerisDataFactory(
    start_datetime=start,
    end_datetime=start + timedelta(days=120),
    step_type="days",
    step=1,
    lat=natal.lat,
    lng=natal.lng,
    tz_str=natal.tz_str,
).get_ephemeris_data_as_astrological_subjects()

events = TransitsTimeRangeFactory(
    natal_chart=natal,
    ephemeris_data_points=ephemeris,
    active_points=["Sun", "Jupiter"],
).get_transit_events(refine_exact_moments=True)

# Transiting Sun to natal Jupiter only
for event in events.events:
    if event.p1_name == "Sun" and event.p2_name == "Jupiter":
        print(f"{event.aspect}: {event.exact_moment} (min orb {event.min_orb:.4f}°)")
```

**Output:**
```
opposition: 2024-01-13T05:59:51.601033+00:00 (min orb 0.0000°)
trine: 2024-03-12T14:58:37.784670+00:00 (min orb 0.0000°)
square: 2024-04-11T22:43:25.292653+00:00 (min orb 0.0000°)
```

The step size sets the resolution of the search: a `"days"` step can miss a fast
pair that comes and goes inside one day, so use `step_type="hours"` for the Moon.
A pair with no exact hit in the range simply yields no event.

See [Transits Time Range Factory](/content/docs/transits_time_range_factory) for
the full API.

### Planetary Hours

`PlanetaryHoursFactory` divides real sunrise-to-sunset into twelve unequal day
hours and sunset-to-next-sunrise into twelve night hours, then rules them in
Chaldean order starting from the weekday ruler. Equal clock hours are not the
same thing and give the wrong ruler for most of the day.

```python
from kerykeion import PlanetaryHoursFactory

hours = PlanetaryHoursFactory.from_datetime(
    2024, 7, 15, 14, 30,
    latitude=51.5074,
    longitude=-0.1276,
    tz_str="Europe/London",
)

print(f"Day ruler: {hours.day_ruler}")
print(f"Current hour {hours.current_index}: {hours.current_ruler}")

for planetary_hour in hours.hours[:6]:
    phase = "day" if planetary_hour.is_diurnal else "night"
    print(f"  {planetary_hour.index:2d} ({phase}) {planetary_hour.ruler}")
```

A moment before sunrise belongs to the previous planetary day, which the factory
resolves for you. Polar day or night leaves the bounding sunrise or sunset
undefined and raises `KerykeionException`. See
[Planetary Hours Factory](/content/docs/planetary_hours_factory).

### Check if the Moon is Void-of-Course

The Moon is void after its last exact Ptolemaic aspect in its current sign,
until the next ingress. That is a claim about the *future* of the sign, so it
cannot be read off a single chart's aspect list.
`VoidOfCourseMoonFactory` scans forward for it.

```python
from kerykeion import VoidOfCourseMoonFactory

state = VoidOfCourseMoonFactory.from_datetime(
    2024, 7, 15, 14, 30,
    tz_str="Europe/London",
)

if state.is_void_of_course:
    print(f"Moon is void-of-course in {state.moon_sign} until {state.void_end}")
else:
    print(f"Moon in {state.moon_sign} is not void; the void opens at {state.void_start}")

if state.last_aspect is not None:
    print(f"Last aspect: {state.last_aspect.aspect} to {state.last_aspect.planet}")
```

`from_iso_range(start_date, end_date)` returns every complete window over a
range instead of the state at one moment. See
[Void-of-Course Moon Factory](/content/docs/void_of_course_moon_factory).

### Secondary Progressions

Use the dedicated `SecondaryProgressionFactory` for accurate day-for-a-year progressions with progressed-to-natal aspect detection:

```python
from kerykeion import AstrologicalSubjectFactory, SecondaryProgressionFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Simple: get the progressed subject
progressed = SecondaryProgressionFactory.compute(
    natal,
    target_iso_utc_datetime="2026-07-15T00:00:00Z",
)

print(f"Natal Sun: {natal.sun.sign} {natal.sun.position:.2f}")
print(f"Progressed Sun: {progressed.sun.sign} {progressed.sun.position:.2f}")

# Full: get progressed-to-natal aspects
result = SecondaryProgressionFactory.compute_full(
    natal,
    target_iso_utc_datetime="2026-07-15T00:00:00Z",
)

for asp in result.progressed_to_natal_aspects:
    print(f"P.{asp.progressed_point} {asp.aspect} N.{asp.natal_point} (orb: {asp.orb:.2f})")
```

See [Secondary Progressions](/content/docs/secondary_progressions_factory) and [Solar Arc Directions](/content/docs/solar_arc_factory) for full documentation.

---

## Performance Optimization

### Cache Subjects for Repeated Access

```python
from functools import lru_cache
from kerykeion import AstrologicalSubjectFactory

@lru_cache(maxsize=100)
def get_cached_subject(name, year, month, day, hour, minute, lng, lat, tz_str):
    """Cache subjects to avoid recalculation."""
    return AstrologicalSubjectFactory.from_birth_data(
        name, year, month, day, hour, minute,
        lng=lng, lat=lat, tz_str=tz_str, online=False
    )

# First call calculates
subject1 = get_cached_subject("John", 1990, 7, 15, 10, 30, -0.1276, 51.5074, "Europe/London")

# Second call returns cached result
subject2 = get_cached_subject("John", 1990, 7, 15, 10, 30, -0.1276, 51.5074, "Europe/London")

print(f"Same object: {subject1 is subject2}")  # True
```

### Minimize Active Points for Speed

The cost is in computing the points, which happens in
`AstrologicalSubjectFactory`. Narrowing `active_points` on the chart data
factory filters an already-computed subject and saves nothing:

```python
import time

from kerykeion import AstrologicalSubjectFactory

minimal_points = ["Sun", "Moon", "Ascendant"]

start = time.time()
for _ in range(20):
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Example", 1990, 7, 15, 10, 30,
        lng=-0.1276, lat=51.5074, tz_str="Europe/London",
        online=False,
        active_points=minimal_points,
    )
elapsed = time.time() - start

print(f"20 subjects with 3 points: {elapsed:.2f}s")
```

### Skip Unnecessary Calculations

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    calculate_lunar_phase=False  # Skip if not needed
)

# For synastry, skip extras if not needed
second = AstrologicalSubjectFactory.from_birth_data(
    "Partner", 1992, 3, 20, 14, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    calculate_lunar_phase=False
)

synastry = ChartDataFactory.create_synastry_chart_data(
    subject, second,
    include_relationship_score=False,  # Skip if not needed
    include_house_comparison=False     # Skip if not needed
)
```

---

## See Also

- [API Documentation](/content/docs/)
- [Complete Tutorial](/content/docs/tutorial)
- [Examples Gallery](/content/examples/)
- [Troubleshooting & FAQ](/content/docs/faq)

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
