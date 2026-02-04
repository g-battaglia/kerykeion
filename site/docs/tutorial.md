---
title: 'Complete Tutorial'
description: 'Build a complete astrology application from scratch with Kerykeion'
category: 'Getting Started'
tags: ['docs', 'tutorial', 'guide', 'beginner']
order: 5
---

# Complete Tutorial: Building an Astrology Application

This tutorial walks you through building a complete astrology application using Kerykeion. By the end, you'll understand how to:

1. Create birth charts
2. Calculate and analyze aspects
3. Compare two charts (synastry)
4. Calculate relationship compatibility
5. Generate solar returns
6. Create transit forecasts
7. Generate reports and visualizations
8. Integrate with AI/LLMs

## Prerequisites

- Python 3.9 or higher
- Basic Python knowledge
- No astrology knowledge required (we'll explain concepts as we go)

## Setup

Install Kerykeion:

```bash
pip install kerykeion
```

Create a project directory:

```bash
mkdir astrology_app
cd astrology_app
mkdir charts_output
```

---

## Part 1: Your First Birth Chart (10 minutes)

A **birth chart** (natal chart) is a map of the sky at the moment of birth. Let's create one.

### Creating an Astrological Subject

```python
from kerykeion import AstrologicalSubjectFactory

# Create a subject with birth data
# Using offline mode with explicit coordinates (recommended)
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Alice",
    year=1990, month=7, day=15,
    hour=10, minute=30,
    lng=-0.1276,          # London longitude
    lat=51.5074,          # London latitude
    tz_str="Europe/London",
    online=False
)

print(f"Created chart for: {subject.name}")
print(f"Julian Day: {subject.julian_day}")
```

### Accessing Planetary Positions

```python
# The Sun
print(f"Sun: {subject.sun.sign} at {subject.sun.position:.2f}°")
print(f"  House: {subject.sun.house}")
print(f"  Retrograde: {subject.sun.retrograde}")

# The Moon
print(f"Moon: {subject.moon.sign} at {subject.moon.position:.2f}°")
print(f"  Element: {subject.moon.element}")
print(f"  Quality: {subject.moon.quality}")

# The Ascendant (Rising Sign)
print(f"Ascendant: {subject.first_house.sign}")
```

**Output:**
```
Sun: Can at 22.54°
  House: Eleventh_House
  Retrograde: False
Moon: Sco at 15.32°
  Element: Water
  Quality: Fixed
Ascendant: Vir
```

### Generating an SVG Chart

```python
from pathlib import Path
from kerykeion import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer

# Step 1: Calculate chart data
chart_data = ChartDataFactory.create_natal_chart_data(subject)

# Step 2: Create the visualization
drawer = ChartDrawer(chart_data=chart_data)

# Step 3: Save the SVG
output_dir = Path("charts_output")
drawer.save_svg(output_path=output_dir, filename="alice-natal")

print(f"Chart saved to {output_dir}/alice-natal.svg")
```

Open the SVG file in a web browser to view your chart!

---

## Part 2: Understanding Aspects (15 minutes)

**Aspects** are angular relationships between planets that create energetic connections.

### Calculating Aspects

```python
from kerykeion import AspectsFactory

# Get aspects within Alice's chart
aspects_result = AspectsFactory.single_chart_aspects(subject)

print(f"Found {len(aspects_result.aspects)} aspects in Alice's chart\n")

# Display the first 5 aspects
for aspect in aspects_result.aspects[:5]:
    print(f"{aspect.p1_name} {aspect.aspect} {aspect.p2_name}")
    print(f"  Orb: {aspect.orbit:.2f}° ({aspect.aspect_movement})")
    print()
```

**Output:**
```
Sun conjunction Mercury
  Orb: 2.34° (Separating)

Moon trine Mars
  Orb: 1.87° (Applying)
...
```

### Filtering Aspects

```python
# Get only major aspects (conjunction, opposition, trine, square, sextile)
major_aspects = [a for a in aspects_result.aspects 
                 if a.aspect in ["conjunction", "opposition", "trine", "square", "sextile"]]

print(f"Major aspects: {len(major_aspects)}")

# Get only applying aspects (forming, considered stronger)
applying = [a for a in aspects_result.aspects if a.aspect_movement == "Applying"]
print(f"Applying aspects: {len(applying)}")
```

---

## Part 3: Synastry - Comparing Two Charts (15 minutes)

**Synastry** compares two birth charts to analyze relationship dynamics.

### Creating Two Subjects

```python
# Alice (from before)
alice = AstrologicalSubjectFactory.from_birth_data(
    name="Alice", year=1990, month=7, day=15, hour=10, minute=30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False
)

# Bob
bob = AstrologicalSubjectFactory.from_birth_data(
    name="Bob", year=1988, month=3, day=22, hour=14, minute=0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False
)

print(f"Alice's Sun: {alice.sun.sign}")
print(f"Bob's Sun: {bob.sun.sign}")
```

### Calculating Inter-Chart Aspects

```python
# Aspects between the two charts
synastry_aspects = AspectsFactory.dual_chart_aspects(alice, bob)

print(f"Found {len(synastry_aspects.aspects)} aspects between Alice and Bob\n")

for aspect in synastry_aspects.aspects[:5]:
    print(f"Alice's {aspect.p1_name} {aspect.aspect} Bob's {aspect.p2_name}")
    print(f"  Orb: {aspect.orbit:.2f}°")
```

### Creating a Synastry Chart

```python
# Generate synastry chart data
synastry_data = ChartDataFactory.create_synastry_chart_data(
    alice, bob,
    include_relationship_score=True,
    include_house_comparison=True
)

# Create and save the chart
drawer = ChartDrawer(chart_data=synastry_data)
drawer.save_svg(output_path=Path("charts_output"), filename="alice-bob-synastry")
```

---

## Part 4: Relationship Compatibility Score (10 minutes)

Kerykeion can calculate a compatibility score using Ciro Discepolo's method.

```python
from kerykeion.relationship_score_factory import RelationshipScoreFactory

# Calculate compatibility
score_factory = RelationshipScoreFactory(alice, bob)
result = score_factory.get_relationship_score()

print(f"Compatibility Score: {result.score_value}")
print(f"Category: {result.score_description}")
print(f"Is Destiny Sign Match: {result.is_destiny_sign}")

# Score breakdown
print("\nTop contributing factors:")
for item in result.score_breakdown[:5]:
    print(f"  {item.description}: +{item.points} points")
```

**Score Ranges:**
- 0-5: Minimal
- 5-10: Medium
- 10-15: Important
- 15-20: Very Important
- 20-30: Exceptional
- 30+: Rare Exceptional

---

## Part 5: Solar Returns (15 minutes)

A **Solar Return** is the chart for the moment the Sun returns to its natal position each year. It's used for annual forecasts.

```python
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

# Create the return factory
return_factory = PlanetaryReturnFactory(
    alice,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Get the 2024 Solar Return
solar_return = return_factory.next_return_from_date(2024, 7, 1, return_type="Solar")

print(f"Solar Return for {solar_return.name}")
print(f"Date: {solar_return.iso_formatted_local_datetime}")
print(f"Ascendant: {solar_return.first_house.sign}")
print(f"Moon: {solar_return.moon.sign}")
```

### Creating a Dual-Wheel Return Chart

```python
# Create return chart data (natal + return overlay)
return_data = ChartDataFactory.create_return_chart_data(alice, solar_return)

drawer = ChartDrawer(chart_data=return_data)
drawer.save_svg(output_path=Path("charts_output"), filename="alice-solar-return-2024")
```

### Lunar Returns

```python
# Lunar returns occur monthly
lunar_return = return_factory.next_return_from_date(2024, 7, 1, return_type="Lunar")

print(f"Next Lunar Return: {lunar_return.iso_formatted_local_datetime}")
```

---

## Part 6: Transit Forecasts (20 minutes)

**Transits** compare current planetary positions to your natal chart for timing events.

### Simple Transit Chart

```python
# Create a transit subject for a specific date
transit = AstrologicalSubjectFactory.from_birth_data(
    name="Transit - July 2024",
    year=2024, month=7, day=15, hour=12, minute=0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Create transit chart
transit_data = ChartDataFactory.create_transit_chart_data(alice, transit)

drawer = ChartDrawer(chart_data=transit_data)
drawer.save_svg(output_path=Path("charts_output"), filename="alice-transits-july2024")
```

### Transit Aspects

```python
# Calculate transit aspects
transit_aspects = AspectsFactory.dual_chart_aspects(alice, transit)

print("Active transits:")
for aspect in transit_aspects.aspects[:10]:
    print(f"Transit {aspect.p2_name} {aspect.aspect} Natal {aspect.p1_name}")
    print(f"  Orb: {aspect.orbit:.2f}°")
```

### Time-Range Transit Analysis

```python
from kerykeion.ephemeris_data_factory import EphemerisDataFactory
from kerykeion.transits_time_range_factory import TransitsTimeRangeFactory
from datetime import date

# Generate ephemeris data for a date range
ephemeris = EphemerisDataFactory(
    start_date=date(2024, 7, 1),
    end_date=date(2024, 7, 31),
    step_type="days",
    step=1,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London"
)

ephemeris_points = ephemeris.get_ephemeris_data_as_astrological_subjects()

# Calculate transits for each day
transit_factory = TransitsTimeRangeFactory(alice, ephemeris_points)
transit_moments = transit_factory.get_transit_moments()

print(f"Analyzed {len(transit_moments.dates)} days")

# Find significant transits
for moment in transit_moments.transits[:5]:
    if moment.aspects:
        print(f"\n{moment.date}:")
        for asp in moment.aspects[:3]:
            print(f"  {asp.p2_name} {asp.aspect} {asp.p1_name} (orb: {asp.orbit:.2f}°)")
```

---

## Part 7: Reports and Analysis (10 minutes)

### Generating Text Reports

```python
from kerykeion import ReportGenerator

# Report from a subject
report = ReportGenerator(subject)
report.print_report()
```

### Report from Chart Data

```python
# Report includes element/quality distribution and aspects
natal_data = ChartDataFactory.create_natal_chart_data(alice)
report = ReportGenerator(natal_data)
report_text = report.generate_report(max_aspects=10)

# Save to file
with open("alice_report.txt", "w") as f:
    f.write(report_text)
```

### Element and Quality Distribution

```python
# Access distribution directly
print("Element Distribution:")
print(f"  Fire: {natal_data.element_distribution.fire_percentage}%")
print(f"  Earth: {natal_data.element_distribution.earth_percentage}%")
print(f"  Air: {natal_data.element_distribution.air_percentage}%")
print(f"  Water: {natal_data.element_distribution.water_percentage}%")

print("\nQuality Distribution:")
print(f"  Cardinal: {natal_data.quality_distribution.cardinal_percentage}%")
print(f"  Fixed: {natal_data.quality_distribution.fixed_percentage}%")
print(f"  Mutable: {natal_data.quality_distribution.mutable_percentage}%")
```

---

## Part 8: AI/LLM Integration (10 minutes)

Kerykeion can serialize chart data for AI interpretation.

```python
from kerykeion import to_context

# Generate AI-ready context
context = to_context(alice)
print(context[:500])  # Preview
```

### Using with an LLM

```python
# Example: Creating a prompt for an LLM
system_prompt = """You are an experienced astrologer. 
Interpret the following birth chart data and provide insights 
about the person's personality, strengths, and challenges."""

user_prompt = f"""Please interpret this birth chart:

{to_context(alice)}

Focus on:
1. Core personality (Sun, Moon, Ascendant)
2. Communication style (Mercury)
3. Love and relationships (Venus)
"""

# Send to your preferred LLM API...
print("Prompt ready for LLM processing")
```

---

## Complete Example: Putting It All Together

Here's a complete script that uses all the concepts:

```python
"""
Complete Astrology Application Example
"""
from pathlib import Path
from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    AspectsFactory,
    ReportGenerator,
    to_context
)
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.relationship_score_factory import RelationshipScoreFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

# Setup
output_dir = Path("charts_output")
output_dir.mkdir(exist_ok=True)

# Create subjects
alice = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 7, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False
)

bob = AstrologicalSubjectFactory.from_birth_data(
    "Bob", 1988, 3, 22, 14, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False
)

# 1. Generate natal charts
for person in [alice, bob]:
    data = ChartDataFactory.create_natal_chart_data(person)
    drawer = ChartDrawer(chart_data=data, theme="dark")
    drawer.save_svg(output_path=output_dir, filename=f"{person.name.lower()}-natal")
    print(f"Created natal chart for {person.name}")

# 2. Synastry analysis
synastry_data = ChartDataFactory.create_synastry_chart_data(alice, bob)
drawer = ChartDrawer(chart_data=synastry_data)
drawer.save_svg(output_path=output_dir, filename="alice-bob-synastry")

# 3. Compatibility score
score = RelationshipScoreFactory(alice, bob).get_relationship_score()
print(f"\nCompatibility: {score.score_value} ({score.score_description})")

# 4. Solar return for Alice
return_factory = PlanetaryReturnFactory(
    alice, lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False
)
solar_2024 = return_factory.next_return_from_date(2024, 7, 1, return_type="Solar")
return_data = ChartDataFactory.create_return_chart_data(alice, solar_2024)
drawer = ChartDrawer(chart_data=return_data)
drawer.save_svg(output_path=output_dir, filename="alice-solar-2024")

# 5. Generate report
report = ReportGenerator(ChartDataFactory.create_natal_chart_data(alice))
with open(output_dir / "alice-report.txt", "w") as f:
    f.write(report.generate_report())

# 6. AI context
ai_context = to_context(alice)
with open(output_dir / "alice-ai-context.txt", "w") as f:
    f.write(ai_context)

print("\nAll files generated successfully!")
print(f"Check the '{output_dir}' directory for outputs.")
```

---

## Next Steps

Now that you've completed the tutorial, explore:

- [API Documentation](/content/docs/) - Full reference for all modules
- [Examples Gallery](/content/examples/) - More code examples
- [Schemas Reference](/content/docs/schemas) - All data models
- [Theming Guide](/content/examples/theming) - Customize chart appearance
- [House Systems](/content/examples/houses-systems) - All 23 house systems
- [Sidereal Modes](/content/examples/sidereal-modes) - Vedic astrology support
