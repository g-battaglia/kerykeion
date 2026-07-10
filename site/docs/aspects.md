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

**Expected Output:**

```text
Total Aspects: 34
Moon sextile Venus (orb: 3.93°)
Moon trine Jupiter (orb: 1.08°)
Moon sextile Neptune (orb: 1.08°)
Moon trine Pluto (orb: 0.60°)
Moon trine Chiron (orb: 1.25°)
```

> **Note:** Orb values are always non-negative (absolute deviation from exact aspect). To determine whether an aspect is applying or separating, check the `aspect_movement` field (`"Applying"`, `"Separating"`, or `"Static"`).

### 2. `dual_chart_aspects`

Calculates aspects between two different subjects (Synastry/Transits).

```python
# Create second subject
subject_b = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 8, 20, 14, 30, "New York", "US")

# Calculate synastry
synastry = AspectsFactory.dual_chart_aspects(subject, subject_b)

print(f"Synastry Aspects: {len(synastry.aspects)}")
```

**Expected Output:**

```text
Synastry Aspects: 67
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

| Aspect             | Angle | Default Orb | Active by Default | Type  |
| :----------------- | :---- | :---------- | :---------------- | :---- |
| **Conjunction**    | 0°    | 6°          | Yes               | Major |
| **Opposition**     | 180°  | 6°          | Yes               | Major |
| **Trine**          | 120°  | 6°          | Yes               | Major |
| **Square**         | 90°   | 6°          | Yes               | Major |
| **Sextile**        | 60°   | 5°          | Yes               | Major |
| **Quintile**       | 72°   | 2°          | No                | Minor |
| **Semi-sextile**   | 30°   | 2°          | No                | Minor |
| **Semi-square**    | 45°   | 2°          | No                | Minor |
| **Sesquiquadrate** | 135°  | 2°          | No                | Minor |
| **Biquintile**     | 144°  | 2°          | No                | Minor |
| **Quincunx**       | 150°  | 2°          | No                | Minor |

> The orb values shown above are the base orbs from `DEFAULT_ACTIVE_ASPECTS` / `ALL_ACTIVE_ASPECTS`. Luminary widening (+1.5° for Sun/Moon) is applied separately via per-point orb adjustments, bringing Sun/Moon major aspects to an effective ~7.5° orb. The `DEFAULT_ACTIVE_ASPECTS` preset includes only the five major aspects (conjunction, sextile, square, trine, opposition). To enable all 11 aspects, pass `active_aspects=ALL_ACTIVE_ASPECTS` from `kerykeion.settings.config_constants`.

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

#### Per-point Orbs (`point_orb_adjustments`)

Widen or tighten the orb for specific points (for example, give the luminaries a
larger orb). `point_orb_adjustments` maps a point name to an orb value, and
`point_orb_adjustment_strategy` (default `"max_explicit"`) controls how the two
endpoints' adjustments combine.

```python
# Give the Sun and Moon a wider 10° orb; all other points keep their defaults.
aspects = AspectsFactory.single_chart_aspects(
    subject,
    point_orb_adjustments={"Sun": 10.0, "Moon": 10.0},
)
```

A built-in preset, `DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS` (luminary widening), is
available in `kerykeion.settings.config_constants`.

## Return Data Structure

The factory returns a `SingleChartAspectsModel` (for single charts) or `DualChartAspectsModel` (for dual charts) containing a list of `AspectModel` objects.

**Key `AspectModel` Attributes:**

- `p1_name`, `p2_name`: Names of the two points involved.
- `aspect`: Name of the aspect (e.g., `"conjunction"`).
- `orbit`: The exact orb (absolute deviation from exact aspect, always non-negative).
- `aspect_degrees`: The theoretical angle (e.g., 120 for trine).
- `aspect_movement`: `"Applying"`, `"Separating"`, or `"Static"`.

## Declination Aspects

In addition to ecliptic (longitude) aspects, `AspectsFactory` supports **declination-based aspects**. Two points form a **parallel** when their declinations are within orb degrees of each other (both north or both south). A **contra-parallel** occurs when their declinations are equal in magnitude but opposite in sign.

### `single_chart_declination_aspects`

```python
from kerykeion import AstrologicalSubjectFactory, AspectsFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False
)

dec_aspects = AspectsFactory.single_chart_declination_aspects(subject, orb=1.0)

for asp in dec_aspects:
    print(f"{asp.p1_name} {asp.aspect} {asp.p2_name} (orb: {asp.orbit:.2f})")
```

| Parameter       | Type         | Default | Description                                    |
| :-------------- | :----------- | :------ | :--------------------------------------------- |
| `subject`       | Subject      | --      | The astrological subject                       |
| `orb`           | float        | 1.0     | Maximum orb in degrees                         |
| `active_points` | List or None | None    | Points to include (defaults to subject's list) |

### `dual_chart_declination_aspects`

```python
dec_synastry = AspectsFactory.dual_chart_declination_aspects(subject_a, subject_b, orb=1.0)
```

Returns `List[AspectModel]` with `aspect="parallel"` or `aspect="contra-parallel"`.

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
# Returns "Applying" (Point one at 120° is behind point two at 122° and catching up due to higher speed)
```

**Expected Output:**

```text
Applying
```

### `get_aspect_from_two_points`

Low-level function to check if two points form an aspect.

```python
from kerykeion.aspects.aspects_utils import get_aspect_from_two_points

aspect = get_aspect_from_two_points(
    [{"name": "trine", "degree": 120, "orb": 8}],
    0.0,
    120.5,
)
# Returns dict with aspect details if found, else verdict=False
```

### `get_active_points_list`

Extracts active celestial points from a subject based on configuration.

```python
from kerykeion.aspects.aspects_utils import get_active_points_list
from kerykeion.settings import DEFAULT_CELESTIAL_POINTS_SETTINGS

points = get_active_points_list(
    subject,
    active_points=["Sun", "Moon", "Mercury"],
    celestial_points=DEFAULT_CELESTIAL_POINTS_SETTINGS,  # keyword-only; defaults to this
)
```

### `planet_id_decoder`

Converts a planet name to its Swiss Ephemeris ID.

```python
from kerykeion.aspects.aspects_utils import planet_id_decoder
from kerykeion.settings import DEFAULT_CELESTIAL_POINTS_SETTINGS

swe_id = planet_id_decoder(DEFAULT_CELESTIAL_POINTS_SETTINGS, "Jupiter")
# Returns 5
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
