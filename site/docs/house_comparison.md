---
title: 'House Comparison'
description: 'Explore house overlays and synastry dynamics with the House Comparison Factory. Bidirectional analysis of where planets fall in a partner’s houses.'
category: 'Analysis'
tags: ['docs', 'houses', 'synastry', 'comparison', 'kerykeion']
order: 9
---

# House Comparison

The `HouseComparisonFactory` performs a bidirectional analysis of where one subject's planets fall within another subject's houses (synastry overlays).

## Usage

Initialize the factory with two subjects to generate a bidirectional comparison report showing planet-in-house placements.

```python
from kerykeion import AstrologicalSubjectFactory, HouseComparisonFactory

# 1. Create Subjects (offline mode: explicit coordinates, no GeoNames lookup)
person_a = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 5, 15, 10, 30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)
person_b = AstrologicalSubjectFactory.from_birth_data(
    "Bob", 1992, 8, 23, 14, 45,
    lng=9.19, lat=45.4642, tz_str="Europe/Rome", online=False,
)

# 2. Generate Comparison
factory = HouseComparisonFactory(person_a, person_b)
comparison = factory.get_house_comparison()

# 3. Access Data
# Where Alice's planets fall in Bob's chart
for point in comparison.first_points_in_second_houses:
    print(f"Alice's {point.point_name} -> Bob's {point.projected_house_name}")

# Where Bob's planets fall in Alice's chart
for point in comparison.second_points_in_first_houses:
    print(f"Bob's {point.point_name} -> Alice's {point.projected_house_name}")
```

## Data Structure

The `HouseComparisonModel` contains:

**Subject Names:**

- `first_subject_name`: Name of the first subject.
- `second_subject_name`: Name of the second subject.

**Point Comparisons:**

- `first_points_in_second_houses`: Subject A's points projected into Subject B's houses.
- `second_points_in_first_houses`: Subject B's points projected into Subject A's houses.

**Cusp Comparisons:**

- `first_cusps_in_second_houses`: Subject A's house cusps projected into Subject B's houses.
- `second_cusps_in_first_houses`: Subject B's house cusps projected into Subject A's houses.

Each point model includes:

- `point_name`: Name of the planet/point (e.g. "Sun").
- `point_degree`: Degree within the sign.
- `point_sign`: Zodiac sign.
- `point_owner_name`: Owner subject name.
- `projected_house_name`: Name of the house it falls into (e.g. "Seventh_House").
- `projected_house_number`: Number of the house (1-12).
- `projected_house_owner_name`: Target subject name.
- `point_owner_house_number`: House number in owner's chart (optional).
- `point_owner_house_name`: House name in owner's chart (optional).

## Constructor Parameters

| Parameter        | Type                       | Default     | Description                    |
| :--------------- | :------------------------- | :---------- | :----------------------------- |
| `first_subject`  | `AstrologicalSubjectModel` or `PlanetReturnModel` | Required    | First subject for comparison.  |
| `second_subject` | `AstrologicalSubjectModel` or `PlanetReturnModel` | Required    | Second subject for comparison. |
| `active_points`  | `List[AstrologicalPoint]`  | `DEFAULT_ACTIVE_POINTS` | Points to include in analysis. |

## Raises

The constructor raises `KerykeionException` when the two subjects do not share
the same reference frame — zodiac type, perspective type, and (for sidereal
charts) sidereal mode — or when either input is not a subject-like model at all.
Overlaying a Tropical chart's points on a Sidereal chart's houses compares
longitudes measured from different zero points, so it is rejected up front.

The house system identifier is deliberately **not** compared: a house overlay
between two subjects cast with different house systems is legitimate.

## Utility Functions

Import from: `kerykeion.house_comparison.utils`

Lower-level functions used by the factory, useful for custom analysis pipelines.

| Function                                                                              | Description                                          |
| :------------------------------------------------------------------------------------ | :--------------------------------------------------- |
| `calculate_points_in_reciprocal_houses(point_subject, house_subject, active_points=...)` | Calculates where one subject's planets fall in the other's houses. |
| `calculate_cusps_in_reciprocal_houses(cusp_subject, house_subject)`                    | Calculates where one subject's house cusps fall in the other's houses. |

```python
from kerykeion.house_comparison.utils import calculate_points_in_reciprocal_houses
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS

# Returns List[PointInHouseModel]
points = calculate_points_in_reciprocal_houses(person_a, person_b, active_points=DEFAULT_ACTIVE_POINTS)
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
