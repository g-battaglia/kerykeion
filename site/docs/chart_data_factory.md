---
title: 'Chart Data Factory'
description: 'Generate structured, machine-readable astrological data with the ChartDataFactory. Supports natal, synastry, transit, and composite charts.'
category: 'Core'
tags: ['docs', 'chart data', 'analysis', 'kerykeion']
order: 3
---

# Chart Data Factory

The `ChartDataFactory` extracts and structures all astronomical calculations into machine-readable Pydantic models. It separates the _computational_ layer from the _visualization_ layer (`ChartDrawer`).

## Key Features

- **Structured Output**: Returns Pydantic models (`SingleChartDataModel` or `DualChartDataModel`) perfect for APIs.
- **Automatic Analysis**: Calculates element/quality distributions and relationship scores automatically.
- **Optimized**: Only calculates what is necessary for the requested chart type.

## Factory Methods

### 1. `create_natal_chart_data`

Calculates all standard chart data (planets, houses, aspects, elements) for a single subject.

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)
natal_data = ChartDataFactory.create_natal_chart_data(subject)

print(f"Elements: {natal_data.element_distribution.fire_percentage}% Fire")
print(f"Qualities: {natal_data.quality_distribution.cardinal_percentage}% Cardinal")
```

#### Parameters

| Parameter                    | Type                       | Default      | Description                                                                   |
| :--------------------------- | :------------------------- | :----------- | :---------------------------------------------------------------------------- |
| `subject`                    | `AstrologicalSubjectModel` | **Required** | The subject to create chart data for. Also accepts `CompositeSubjectModel` or `PlanetReturnModel`. |
| `active_points`              | `List[str]`                | `None`       | Custom points list. If `None`, uses `DEFAULT_ACTIVE_POINTS`.                  |
| `active_aspects`             | `List[ActiveAspect]`       | Default      | Custom aspects list with orbs. Each item: `{"name": "conjunction", "orb": 10}`. |
| `distribution_method`        | `str`                      | `"weighted"` | Element/quality calculation method: `"weighted"` or `"pure_count"`. Keyword-only. |
| `custom_distribution_weights`| `Mapping[str, float]`      | `None`       | Override individual point weights. Use `"__default__"` for fallback. Keyword-only. |

> See [Element & Quality Distribution](/content/docs/element_quality_distribution) for details on distribution methods and custom weights.

### 2. `create_synastry_chart_data`

Used for comparing two subjects. Includes relationship scoring and house comparison.

```python
subject_b = AstrologicalSubjectFactory.from_birth_data(
    "Bob", 1992, 8, 20, 14, 30,
    lng=-74.006, lat=40.7128, tz_str="America/New_York",
    online=False
)

synastry_data = ChartDataFactory.create_synastry_chart_data(
    subject,
    subject_b,
    include_relationship_score=True,
    include_house_comparison=True
)

if synastry_data.relationship_score:
    print(f"Compatibility Score: {synastry_data.relationship_score.score_value}")
```

#### Parameters

| Parameter                    | Type                       | Default      | Description                                                                   |
| :--------------------------- | :------------------------- | :----------- | :---------------------------------------------------------------------------- |
| `first_subject`              | `AstrologicalSubjectModel` | **Required** | Primary subject.                                                              |
| `second_subject`             | `AstrologicalSubjectModel` | **Required** | Partner subject.                                                              |
| `active_points`              | `List[str]`                | `None`       | Custom points list.                                                           |
| `active_aspects`             | `List[ActiveAspect]`       | Default      | Custom aspects list with orbs.                                                |
| `include_house_comparison`   | `bool`                     | `True`       | Calculate house overlays.                                                     |
| `include_relationship_score` | `bool`                     | `True`       | Calculate Ciro Discepolo compatibility score.                                 |
| `distribution_method`        | `str`                      | `"weighted"` | Element/quality calculation method. Keyword-only.                             |
| `custom_distribution_weights`| `Mapping[str, float]`      | `None`       | Override point weights. Keyword-only.                                         |

### 3. `create_transit_chart_data`

Compares a natal chart against a current/event time subject.

```python
now = AstrologicalSubjectFactory.from_current_time("Now", "London", "GB")
transit_data = ChartDataFactory.create_transit_chart_data(subject, now)
```

#### Parameters

| Parameter                    | Type                       | Default      | Description                                                                   |
| :--------------------------- | :------------------------- | :----------- | :---------------------------------------------------------------------------- |
| `natal_subject`              | `AstrologicalSubjectModel` | **Required** | Birth chart.                                                                  |
| `transit_subject`            | `AstrologicalSubjectModel` | **Required** | Current time chart.                                                           |
| `active_points`              | `List[str]`                | `None`       | Custom points list.                                                           |
| `active_aspects`             | `List[ActiveAspect]`       | Default      | Custom aspects list.                                                          |
| `include_house_comparison`   | `bool`                     | `True`       | Calculate natal points in transit houses.                                     |
| `distribution_method`        | `str`                      | `"weighted"` | Element/quality calculation method. Keyword-only.                             |
| `custom_distribution_weights`| `Mapping[str, float]`      | `None`       | Override point weights. Keyword-only.                                         |

### 4. `create_composite_chart_data`

Creates data for a composite (midpoint) chart from a `CompositeSubjectModel`.

```python
from kerykeion import CompositeSubjectFactory

composite_subject = CompositeSubjectFactory(subject_a, subject_b).get_midpoint_composite_subject_model()
composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)
```

#### Parameters

| Parameter                    | Type                       | Default      | Description                                                                   |
| :--------------------------- | :------------------------- | :----------- | :---------------------------------------------------------------------------- |
| `composite_subject`          | `CompositeSubjectModel`    | **Required** | Composite subject from `CompositeSubjectFactory`.                             |
| `active_points`              | `List[str]`                | `None`       | Custom points list.                                                           |
| `active_aspects`             | `List[ActiveAspect]`       | Default      | Custom aspects list with orbs.                                                |
| `distribution_method`        | `str`                      | `"weighted"` | Element/quality calculation method. Keyword-only.                             |
| `custom_distribution_weights`| `Mapping[str, float]`      | `None`       | Override point weights. Keyword-only.                                         |

### 5. `create_return_chart_data`

Creates a dual-wheel planetary return chart (natal + return overlay).

```python
from kerykeion import PlanetaryReturnFactory

return_factory = PlanetaryReturnFactory(natal_subject, city="New York", nation="US")
solar_return = return_factory.next_return_from_date(2024, 1, 1, return_type="Solar")

return_data = ChartDataFactory.create_return_chart_data(natal_subject, solar_return)
```

#### Parameters

| Parameter                    | Type                       | Default      | Description                                                                   |
| :--------------------------- | :------------------------- | :----------- | :---------------------------------------------------------------------------- |
| `natal_subject`              | `AstrologicalSubjectModel` | **Required** | The natal subject (inner wheel).                                              |
| `return_subject`             | `PlanetReturnModel`        | **Required** | The return subject from `PlanetaryReturnFactory`.                             |
| `active_points`              | `List[str]`                | `None`       | Custom points list.                                                           |
| `active_aspects`             | `List[ActiveAspect]`       | Default      | Custom aspects list with orbs.                                                |
| `include_house_comparison`   | `bool`                     | `True`       | Calculate house overlays between natal and return.                            |
| `distribution_method`        | `str`                      | `"weighted"` | Element/quality calculation method. Keyword-only.                             |
| `custom_distribution_weights`| `Mapping[str, float]`      | `None`       | Override point weights. Keyword-only.                                         |

### 6. `create_single_wheel_return_chart_data`

Creates a single-wheel view of a planetary return (return only, no natal overlay).

```python
single_return_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
```

#### Parameters

| Parameter                    | Type                       | Default      | Description                                                                   |
| :--------------------------- | :------------------------- | :----------- | :---------------------------------------------------------------------------- |
| `return_subject`             | `PlanetReturnModel`        | **Required** | The return subject.                                                           |
| `active_points`              | `List[str]`                | `None`       | Custom points list.                                                           |
| `active_aspects`             | `List[ActiveAspect]`       | Default      | Custom aspects list with orbs.                                                |
| `distribution_method`        | `str`                      | `"weighted"` | Element/quality calculation method. Keyword-only.                             |
| `custom_distribution_weights`| `Mapping[str, float]`      | `None`       | Override point weights. Keyword-only.                                         |

### 7. `create_chart_data` (Generic)

The underlying generic method that all convenience methods delegate to. Use this when you need full control over the chart type.

```python
chart_data = ChartDataFactory.create_chart_data(
    chart_type="Natal",
    first_subject=subject,
    distribution_method="pure_count"
)
```

| Parameter                    | Type                       | Default      | Description                                                                   |
| :--------------------------- | :------------------------- | :----------- | :---------------------------------------------------------------------------- |
| `chart_type`                 | `ChartType`                | **Required** | `"Natal"`, `"Synastry"`, `"Transit"`, `"Composite"`, `"DualReturnChart"`, `"SingleReturnChart"`. |
| `first_subject`              | Subject Model              | **Required** | Primary subject.                                                              |
| `second_subject`             | Subject Model              | `None`       | Second subject (for dual-chart types).                                        |
| `active_points`              | `List[str]`                | `None`       | Custom points list.                                                           |
| `active_aspects`             | `List[ActiveAspect]`       | Default      | Custom aspects list with orbs.                                                |
| `include_house_comparison`   | `bool`                     | `True`       | Calculate house overlays (dual charts only).                                  |
| `include_relationship_score` | `bool`                     | `False`      | Calculate compatibility score (synastry only).                                |
| `axis_orb_limit`             | `float`                    | `None`       | Stricter orb for angles. Keyword-only.                                        |
| `distribution_method`        | `str`                      | `"weighted"` | `"weighted"` or `"pure_count"`. Keyword-only.                                 |
| `custom_distribution_weights`| `Mapping[str, float]`      | `None`       | Override point weights. Keyword-only.                                         |

## Data Models

### `SingleChartDataModel`

Used for Natal, Composite, and Single Return charts.

- `subject`: The `AstrologicalSubjectModel`.
- `aspects`: List of internal aspects.
- `element_distribution`: Fire/Earth/Air/Water breakdown.
- `quality_distribution`: Cardinal/Fixed/Mutable breakdown.

### `DualChartDataModel`

Used for Synastry, Transit, and Dual Return charts.

- `first_subject`, `second_subject`: The two subjects.
- `aspects`: Inter-chart aspects.
- `relationship_score`: Compatibility score (if requested).
- `house_comparison`: Planet overlays in houses (if requested).

## Analysis Example

Get a full JSON dump of a chart's data.

```python
import json
natal_data = ChartDataFactory.create_natal_chart_data(subject)

# Dump to JSON
json_output = natal_data.model_dump_json(indent=2)
print(json_output)
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
