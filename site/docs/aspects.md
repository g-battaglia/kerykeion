---
title: 'Aspects Module'
description: 'Learn how to calculate and analyze astrological aspects with Kerykeion. Covers major and minor aspects, orbs, and factory methods for chart analysis.'
category: 'Analysis'
tags: ['docs', 'aspects', 'analysis', 'kerykeion']
order: 6
---

# Aspects Module

The `AspectsFactory` provides a unified interface for calculating angular relationships between planets. It handles both single-chart analysis (natal, return) and dual-chart analysis (synastry, transits).

## What Are Aspects?

**Aspects** are specific angular relationships between planets in a chart. They represent how planetary energies interact:

- **Harmonious aspects** (trines 120°, sextiles 60°) indicate ease and flow between planetary energies
- **Challenging aspects** (squares 90°, oppositions 180°) indicate tension, conflict, or dynamic growth opportunities
- **Neutral/Mixed** (conjunctions 0°) blend energies intensely, for better or worse depending on the planets involved

Aspects are fundamental to astrological interpretation, a chart without aspect analysis is like a musical score without chords.

## Factory Methods

### 1. `single_chart_aspects`

Calculates aspects within a single astrological subject.

```python
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

# Create subject
subject = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 6, 15, 12, 0, "London", "GB")

# Calculate aspects
aspects_data = AspectsFactory.single_chart_aspects(subject)

print(f"Total Aspects: {len(aspects_data.aspects)}")
for aspect in aspects_data.aspects[:5]:  # Show first 5
    print(f"{aspect.p1_name} {aspect.aspect} {aspect.p2_name} (orb: {aspect.orbit:.2f}°)")
```

### 2. `dual_chart_aspects`

Calculates aspects between two different subjects (Synastry/Transits).

```python
# Create second subject
subject_b = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 8, 20, 14, 30, "New York", "US")

# Calculate synastry
synastry = AspectsFactory.dual_chart_aspects(subject, subject_b)

print(f"Synastry Aspects: {len(synastry.aspects)}")
```

**Additional Parameters for `dual_chart_aspects`:**

| Parameter                 | Type   | Default | Description                                |
| :------------------------ | :----- | :------ | :----------------------------------------- |
| `first_subject_is_fixed`  | `bool` | `False` | Treat first subject as stationary (natal). |
| `second_subject_is_fixed` | `bool` | `False` | Treat second subject as stationary.        |

_These parameters affect aspect movement calculation (applying/separating)._

## Configuration

### Supported Aspects

Kerykeion calculates both major and minor aspects. Orbs can be customized.

| Aspect             | Angle | Default Orb | Type  |
| :----------------- | :---- | :---------- | :---- |
| **Conjunction**    | 0°    | 8°          | Major |
| **Opposition**     | 180°  | 8°          | Major |
| **Trine**          | 120°  | 8°          | Major |
| **Square**         | 90°   | 8°          | Major |
| **Sextile**        | 60°   | 6°          | Major |
| **Quincunx**       | 150°  | 3°          | Minor |
| **Semi-sextile**   | 30°   | 3°          | Minor |
| **Semi-square**    | 45°   | 3°          | Minor |
| **Sesquiquadrate** | 135°  | 3°          | Minor |
| **Quintile**       | 72°   | 3°          | Minor |
| **Biquintile**     | 144°  | 3°          | Minor |

### Filtering Options

You can refine calculations by specifying which points or aspects to include.

#### By Points (`active_points`)

Limit calculation to specific planets (e.g., only personal planets).

```python
personal_planets = ["Sun", "Moon", "Mercury", "Venus", "Mars"]
aspects = AspectsFactory.single_chart_aspects(subject, active_points=personal_planets)
```

#### By Aspect Types (`active_aspects`)

Define exactly which aspects to check and their specific orbs.

```python
# Only look for exact major aspects (tight orbs)
custom_aspects = [
    {"name": "conjunction", "orb": 3},
    {"name": "opposition", "orb": 3},
    {"name": "trine", "orb": 3},
    {"name": "square", "orb": 3},
]

tight_aspects = AspectsFactory.single_chart_aspects(subject, active_aspects=custom_aspects)
```

#### Axis Orbs (`axis_orb_limit`)

Apply stricter orbs when angles (Ascendant, MC) are involved.

```python
# Standard orb for planets, but strict 2° orb for Angles
aspects = AspectsFactory.single_chart_aspects(subject, axis_orb_limit=2.0)
```

## Return Data Structure

The factory returns an `AspectsModel` containing a list of `AspectModel` objects.

**Key `AspectModel` Attributes:**

- `p1_name`, `p2_name`: Names of the two points involved.
- `aspect`: Name of the aspect (e.g., "conjunction").
- `orbit`: The exact orb (deviation from exact aspect). Negative values indicate applying aspects.
- `aid`: Unique aspect ID string.

## Aspect Utilities

Import from: `kerykeion.aspects.aspects_utils`

### `calculate_aspect_movement`

Determines if an aspect is Applying (orb decreasing) or Separating (orb increasing).

```python
from kerykeion.aspects.aspects_utils import calculate_aspect_movement

movement = calculate_aspect_movement(
    point_one_abs_pos=120.0,
    point_two_abs_pos=122.0,
    aspect_degrees=0,      # Conjunction
    point_one_speed=1.0,   # Moving forward
    point_two_speed=0.5    # Moving slower forward
)
# Returns "Separating" (Distance is 2° and increasing as faster planet is ahead)
```

### `get_aspect_from_two_points`

Low-level function to check if two points form an aspect.

```python
from kerykeion.aspects.aspects_utils import get_aspect_from_two_points

aspect = get_aspect_from_two_points(
    point_one_abs_pos=0.0,
    point_two_abs_pos=120.5,
    aspects_settings=[{"name": "trine", "degree": 120, "orb": 8}]
)
# Returns dict with aspect details if found, else None
```

### `get_active_points_list`

Extracts active celestial points from a subject based on configuration.

```python
from kerykeion.aspects.aspects_utils import get_active_points_list

points = get_active_points_list(
    subject=subject,
    active_points=["Sun", "Moon", "Mercury"],
    planets_settings=settings.planets_settings
)
```

### `planet_id_decoder`

Converts a planet name to its Swiss Ephemeris ID.

```python
from kerykeion.aspects.aspects_utils import planet_id_decoder

swe_id = planet_id_decoder(planets_settings, "Jupiter")
# Returns 5
```
