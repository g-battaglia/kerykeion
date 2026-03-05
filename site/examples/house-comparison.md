---
title: 'House Comparison'
tags: ['examples', 'house comparison', 'synastry', 'overlay', 'kerykeion']
order: 19
---

# House Comparison

The `HouseComparisonFactory` performs **bidirectional house overlay analysis** between two subjects. It calculates where each person's planets and cusps fall in the other person's house system.

This is a key technique in synastry interpretation — knowing that someone's Venus falls in your 7th house, or their Sun lands in your 10th house, provides specific relational context.

## Basic Usage

```python
from kerykeion import AstrologicalSubjectFactory, HouseComparisonFactory

person_a = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)
person_b = AstrologicalSubjectFactory.from_birth_data(
    "Bob", 1988, 11, 22, 9, 30,
    lng=-0.1278, lat=51.5074, tz_str="Europe/London", online=False,
)

factory = HouseComparisonFactory(person_a, person_b)
comparison = factory.get_house_comparison()

print(f"Comparison: {comparison.first_subject_name} <-> {comparison.second_subject_name}")
```

## Understanding the Results

The `HouseComparisonModel` contains four lists for bidirectional analysis:

### Points in Partner's Houses

Where each person's planets fall in the other's house system:

```python
# Alice's planets in Bob's houses
print("\nAlice's planets in Bob's houses:")
for point in comparison.first_points_in_second_houses:
    print(f"  {point.name} -> Bob's House {point.house}")

# Bob's planets in Alice's houses
print("\nBob's planets in Alice's houses:")
for point in comparison.second_points_in_first_houses:
    print(f"  {point.name} -> Alice's House {point.house}")
```

### Cusps in Partner's Houses

Where each person's house cusps fall in the other's system:

```python
# Alice's cusps in Bob's houses
print("\nAlice's cusps in Bob's houses:")
for cusp in comparison.first_cusps_in_second_houses:
    print(f"  House {cusp.house_number} cusp -> Bob's House {cusp.falls_in_house}")

# Bob's cusps in Alice's houses
print("\nBob's cusps in Alice's houses:")
for cusp in comparison.second_cusps_in_first_houses:
    print(f"  House {cusp.house_number} cusp -> Alice's House {cusp.falls_in_house}")
```

## Using with Synastry Charts

`HouseComparisonFactory` is used internally by `ChartDataFactory` when generating synastry, transit, and dual return chart data. You can also use it standalone for data analysis:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, HouseComparisonFactory

alice = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
)
bob = AstrologicalSubjectFactory.from_birth_data(
    "Bob", 1988, 11, 22, 9, 30,
    lng=-0.1278, lat=51.5074, tz_str="Europe/London", online=False,
)

# Standalone house comparison
comparison = HouseComparisonFactory(alice, bob).get_house_comparison()

# Or via ChartDataFactory (comparison is included in the chart data)
synastry_data = ChartDataFactory.create_synastry_chart_data(alice, bob)
```

## Constructor Parameters

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `first_subject` | `AstrologicalSubjectModel` or `PlanetReturnModel` | **Required** | First subject |
| `second_subject` | `AstrologicalSubjectModel` or `PlanetReturnModel` | **Required** | Second subject |
| `active_points` | `list[AstrologicalPoint]` | `DEFAULT_ACTIVE_POINTS` | Which points to include |

## Return Model

`get_house_comparison()` returns a `HouseComparisonModel` with:

| Field | Type | Description |
| :--- | :--- | :--- |
| `first_subject_name` | `str` | Name of the first subject |
| `second_subject_name` | `str` | Name of the second subject |
| `first_points_in_second_houses` | `list` | First subject's points placed in second's houses |
| `second_points_in_first_houses` | `list` | Second subject's points placed in first's houses |
| `first_cusps_in_second_houses` | `list` | First subject's cusps placed in second's houses |
| `second_cusps_in_first_houses` | `list` | Second subject's cusps placed in first's houses |

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
