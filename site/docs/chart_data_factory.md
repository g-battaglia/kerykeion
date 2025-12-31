---
title: 'Chart Data Factory'
category: 'Core'
tags: ['docs', 'chart data', 'analysis', 'kerykeion']
order: 3
---

# Chart Data Factory

The `ChartDataFactory` extracts and structures all astronomical calculations into machine-readable Pydantic models. It separates the _computational_ layer from the _visualization_ layer (`ChartDrawer`).

## Key Features

-   **Structured Output**: Returns Pydantic models (`SingleChartDataModel` or `DualChartDataModel`) perfect for APIs.
-   **Automatic Analysis**: Calculates element/quality distributions and relationship scores automatically.
-   **Optimized**: Only calculates what is necessary for the requested chart type.

## Factory Methods

### 1. `create_natal_chart_data`

Calculates all standard chart data (planets, houses, aspects, elements) for a single subject.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 6, 15, 12, 0, "London", "GB")
natal_data = ChartDataFactory.create_natal_chart_data(subject)

print(f"Elements: {natal_data.element_distribution.fire_percentage}% Fire")
print(f"Qualities: {natal_data.quality_distribution.cardinal_percentage}% Cardinal")
```

### 2. `create_synastry_chart_data`

Used for comparing two subjects. Includes relationship scoring.

```python
subject_b = AstrologicalSubjectFactory.from_birth_data("Bob", 1992, 8, 20, 14, 30, "USA", "New York")

synastry_data = ChartDataFactory.create_synastry_chart_data(
    subject,
    subject_b,
    include_relationship_score=True, # Default False
    include_house_comparison=True    # Default False
)

if synastry_data.relationship_score:
    print(f"Compatibility Score: {synastry_data.relationship_score.score_value}")
```

#### Parameters

| Parameter                    | Type                       | Default   | Description                    |
| :--------------------------- | :------------------------- | :-------- | :----------------------------- |
| `first_subject`              | `AstrologicalSubjectModel` | **Req**   | Primary subject.               |
| `second_subject`             | `AstrologicalSubjectModel` | **Req**   | Partner subject.               |
| `active_points`              | `List[str]`                | `None`    | Custom points list.            |
| `active_aspects`             | `List[dict]`               | `Default` | Custom aspects list.           |
| `include_house_comparison`   | `bool`                     | `True`    | Calculate house overlays.      |
| `include_relationship_score` | `bool`                     | `True`    | Calculate compatibility score. |

### 3. `create_transit_chart_data`

Compares a natal chart against a current/event time subject.

```python
now = AstrologicalSubjectFactory.from_current_time("Now", "London", "GB")
transit_data = ChartDataFactory.create_transit_chart_data(subject, now)
```

#### Parameters

| Parameter                  | Type                       | Default   | Description                               |
| :------------------------- | :------------------------- | :-------- | :---------------------------------------- |
| `natal_subject`            | `AstrologicalSubjectModel` | **Req**   | Birth chart.                              |
| `transit_subject`          | `AstrologicalSubjectModel` | **Req**   | Current time chart.                       |
| `active_points`            | `List[str]`                | `None`    | Custom points list.                       |
| `active_aspects`           | `List[dict]`               | `Default` | Custom aspects list.                      |
| `include_house_comparison` | `bool`                     | `True`    | Calculate natal points in transit houses. |

### 4. `create_composite_chart_data`

Creates data for a composite (midpoint) chart from a `CompositeSubjectModel`.

```python
from kerykeion import CompositeSubjectFactory

composite_subject = CompositeSubjectFactory(subject_a, subject_b).get_midpoint_composite_subject_model()
composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)
```

### 5. `create_return_chart_data`

Creates a dual-wheel planetary return chart (natal + return overlay).

```python
from kerykeion import PlanetaryReturnFactory

return_factory = PlanetaryReturnFactory(natal_subject, city="New York", nation="US")
solar_return = return_factory.next_return_from_date(2024, 1, 1, return_type="Solar")

return_data = ChartDataFactory.create_return_chart_data(natal_subject, solar_return)
```

### 6. `create_single_wheel_return_chart_data`

Creates a single-wheel view of a planetary return (return only, no natal overlay).

```python
single_return_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
```

## Data Models

### `SingleChartDataModel`

Used for Natal, Composite, and Single Return charts.

-   `subject`: The `AstrologicalSubjectModel`.
-   `aspects`: List of internal aspects.
-   `element_distribution`: Fire/Earth/Air/Water breakdown.
-   `quality_distribution`: Cardinal/Fixed/Mutable breakdown.

### `DualChartDataModel`

Used for Synastry, Transit, and Dual Return charts.

-   `first_subject`, `second_subject`: The two subjects.
-   `aspects`: Inter-chart aspects.
-   `relationship_score`: Compatibility score (if requested).
-   `house_comparison`: Planet overlays in houses (if requested).

## Analysis Example

Get a full JSON dump of a chart's data.

```python
import json
natal_data = ChartDataFactory.create_natal_chart_data(subject)

# Dump to JSON
json_output = natal_data.model_dump_json(indent=2)
print(json_output)
```
