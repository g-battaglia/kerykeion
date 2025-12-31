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

### 3. `create_transit_chart_data`

Specialized for comparing a natal chart with a current/event time subject.

```python
now = AstrologicalSubjectFactory.from_current_time("Now", "London", "GB")
transit_data = ChartDataFactory.create_transit_chart_data(subject, now)
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
