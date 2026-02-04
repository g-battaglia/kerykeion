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
Sun conjunct Mercury (orb: 2.34°)
Venus conjunct Mars (orb: 5.12°)
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
  sextile: 8
  trine: 6
  square: 5
  conjunction: 4
  opposition: 3
```

---

## Batch Processing

### Process Multiple Birth Charts

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
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
from kerykeion.relationship_score_factory import RelationshipScoreFactory

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
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Export to JSON
json_output = chart_data.model_dump_json(indent=2)

with open("chart_data.json", "w") as f:
    f.write(json_output)

print("Chart data exported to chart_data.json")
```

### Export Planetary Positions to CSV

```python
import csv
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

planets = ["sun", "moon", "mercury", "venus", "mars", 
           "jupiter", "saturn", "uranus", "neptune", "pluto"]

with open("planetary_positions.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Planet", "Sign", "Position", "House", "Retrograde"])
    
    for planet_name in planets:
        planet = getattr(subject, planet_name)
        writer.writerow([
            planet.name,
            planet.sign,
            f"{planet.position:.2f}",
            planet.house,
            planet.retrograde
        ])

print("Positions exported to planetary_positions.csv")
```

**Output CSV:**
```csv
Planet,Sign,Position,House,Retrograde
Sun,Can,22.54,Eleventh_House,False
Moon,Sco,15.32,Third_House,False
...
```

### Export Ephemeris Data to Pandas DataFrame

```python
import pandas as pd
from datetime import date
from kerykeion.ephemeris_data_factory import EphemerisDataFactory

ephemeris = EphemerisDataFactory(
    start_date=date(2024, 1, 1),
    end_date=date(2024, 1, 31),
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
            "retrograde": planet["retrograde"]
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
    {"name": "conjunction", "orb": 6},  # Tighter than default 10
    {"name": "opposition", "orb": 6},
    {"name": "trine", "orb": 5},        # Tighter than default 8
    {"name": "square", "orb": 4},       # Tighter than default 5
    {"name": "sextile", "orb": 3},      # Tighter than default 6
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
from kerykeion.charts.chart_drawer import ChartDrawer
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

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Full point list including asteroids, TNOs, etc.
all_points = [
    # Main planets
    "Sun", "Moon", "Mercury", "Venus", "Mars", 
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
    # Nodes
    "True_North_Lunar_Node", "True_South_Lunar_Node",
    "Mean_North_Lunar_Node", "Mean_South_Lunar_Node",
    # Special points
    "Chiron", "Mean_Lilith", "True_Lilith",
    # Asteroids
    "Ceres", "Pallas", "Juno", "Vesta",
    # Arabic parts
    "Pars_Fortunae",
    # Angles
    "Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli",
]

chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=all_points
)

print(f"Chart includes {len(chart_data.subject.active_points)} points")
```

---

## Advanced Calculations

### Find the Next Exact Aspect

```python
from datetime import date, timedelta
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

def find_next_exact_aspect(natal_subject, planet1, planet2, aspect_type, 
                           start_date, max_days=365):
    """Find when two planets form an exact aspect."""
    
    for day_offset in range(max_days):
        check_date = start_date + timedelta(days=day_offset)
        
        transit = AstrologicalSubjectFactory.from_birth_data(
            "Transit", check_date.year, check_date.month, check_date.day, 12, 0,
            lng=natal_subject.lng, lat=natal_subject.lat, 
            tz_str=natal_subject.tz_str, online=False
        )
        
        aspects = AspectsFactory.dual_chart_aspects(natal_subject, transit)
        
        for asp in aspects.aspects:
            if (asp.p1_name == planet1 and asp.p2_name == planet2 and 
                asp.aspect == aspect_type and asp.orbit < 1.0):
                return check_date, asp.orbit
    
    return None, None

# Example usage
subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

found_date, orb = find_next_exact_aspect(
    subject, "Sun", "Jupiter", "conjunction",
    date(2024, 1, 1)
)

if found_date:
    print(f"Next Sun-Jupiter conjunction: {found_date} (orb: {orb:.2f}°)")
```

### Calculate Planetary Hours

```python
from datetime import datetime, timedelta
from kerykeion import AstrologicalSubjectFactory

def get_planetary_hours(date_obj, lng, lat, tz_str):
    """Calculate planetary hours for a given day."""
    
    # Simplified calculation (actual would need sunrise/sunset times)
    # This uses a fixed 6 AM sunrise and 6 PM sunset
    
    day_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    night_planets = day_planets.copy()
    
    # Day of week determines starting planet
    # Sunday=0 starts with Sun, Monday=1 with Moon, etc.
    weekday = date_obj.weekday()
    day_order = (weekday + 1) % 7  # Adjust for Python's Monday=0
    
    hours = []
    for i in range(24):
        planet_index = (day_order + i) % 7
        hour_start = datetime(date_obj.year, date_obj.month, date_obj.day, i, 0)
        hours.append({
            "hour": i,
            "start": hour_start.strftime("%H:%M"),
            "planet": day_planets[planet_index]
        })
    
    return hours

# Example
from datetime import date
hours = get_planetary_hours(date(2024, 7, 15), -0.1276, 51.5074, "Europe/London")

print("Planetary Hours for July 15, 2024:")
for h in hours[:12]:  # First 12 hours
    print(f"  {h['start']}: {h['planet']}")
```

### Check if Moon is Void-of-Course

```python
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

def is_moon_void_of_course(subject):
    """
    Check if the Moon is void-of-course (no more major aspects before sign change).
    Simplified version - checks if Moon has any applying aspects.
    """
    
    aspects = AspectsFactory.single_chart_aspects(subject)
    
    moon_aspects = [a for a in aspects.aspects 
                    if (a.p1_name == "Moon" or a.p2_name == "Moon")
                    and a.aspect_movement == "Applying"
                    and a.aspect in ["conjunction", "opposition", "trine", "square", "sextile"]]
    
    return len(moon_aspects) == 0

# Example
subject = AstrologicalSubjectFactory.from_birth_data(
    "Now", 2024, 7, 15, 14, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

if is_moon_void_of_course(subject):
    print(f"Moon is void-of-course in {subject.moon.sign}")
else:
    print(f"Moon in {subject.moon.sign} is NOT void-of-course")
```

### Calculate Age Progressions (Secondary)

```python
from datetime import date, timedelta
from kerykeion import AstrologicalSubjectFactory

def calculate_progressed_chart(natal_subject, target_date):
    """
    Calculate secondary progressions (1 day = 1 year).
    """
    birth_date = date(natal_subject.year, natal_subject.month, natal_subject.day)
    years_elapsed = (target_date - birth_date).days / 365.25
    
    # Progressed date: birth + days equal to years lived
    progressed_date = birth_date + timedelta(days=years_elapsed)
    
    progressed = AstrologicalSubjectFactory.from_birth_data(
        f"{natal_subject.name} (Progressed to {target_date})",
        progressed_date.year, progressed_date.month, progressed_date.day,
        natal_subject.hour, natal_subject.minute,
        lng=natal_subject.lng, lat=natal_subject.lat,
        tz_str=natal_subject.tz_str, online=False
    )
    
    return progressed

# Example
natal = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

progressed = calculate_progressed_chart(natal, date(2024, 7, 15))

print(f"Natal Sun: {natal.sun.sign} {natal.sun.position:.2f}°")
print(f"Progressed Sun: {progressed.sun.sign} {progressed.sun.position:.2f}°")
```

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

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory
import time

subject = AstrologicalSubjectFactory.from_birth_data(
    "Example", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Minimal points for faster calculation
minimal_points = ["Sun", "Moon", "Ascendant"]

start = time.time()
for _ in range(100):
    chart_data = ChartDataFactory.create_natal_chart_data(
        subject,
        active_points=minimal_points
    )
elapsed = time.time() - start

print(f"100 charts with 3 points: {elapsed:.2f}s")
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
