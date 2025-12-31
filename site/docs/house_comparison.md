---
title: 'House Comparison'
category: 'Analysis'
tags: ['docs', 'houses', 'synastry', 'comparison', 'kerykeion']
order: 9
---

# House Comparison

The `HouseComparisonFactory` performs a bidirectional analysis of where one subject's planets fall within another subject's houses (synastry overlays).

## Usage

Initialize the factory with two subjects to generate a bidirectional comparison report showing planet-in-house placements.

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.house_comparison import HouseComparisonFactory

# 1. Create Subjects
person_a = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 5, 15, 10, 30, "Rome", "IT")
person_b = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 8, 23, 14, 45, "Milan", "IT")

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

**Point Comparisons:**

-   `first_points_in_second_houses`: Subject A's points projected into Subject B's houses.
-   `second_points_in_first_houses`: Subject B's points projected into Subject A's houses.

**Cusp Comparisons:**

-   `first_cusps_in_second_houses`: Subject A's house cusps projected into Subject B's houses.
-   `second_cusps_in_first_houses`: Subject B's house cusps projected into Subject A's houses.

Each point model includes:

-   `point_name`: Name of the planet/point (e.g. "Sun").
-   `projected_house_name`: Name of the house it falls into (e.g. "Seventh_House").
-   `projected_house_number`: Number of the house (1-12).
-   `point_abs_pos`: Absolute position of the point.

## Constructor Parameters

| Parameter        | Type                       | Default     | Description                    |
| :--------------- | :------------------------- | :---------- | :----------------------------- |
| `first_subject`  | `AstrologicalSubjectModel` | Required    | First subject for comparison.  |
| `second_subject` | `AstrologicalSubjectModel` | Required    | Second subject for comparison. |
| `active_points`  | `List[AstrologicalPoint]`  | All planets | Points to include in analysis. |
