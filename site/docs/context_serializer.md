---
title: 'AI Context Serializer'
description: 'Optimize your astrological data for Large Language Models. Learn how to use the AI Context Serializer to convert charts into precise, plain-text descriptions.'
category: 'Integration'
tags: ['docs', 'ai', 'context', 'kerykeion']
order: 19
---

# AI Context Serializer

The `to_context` function converts Kerykeion data models into precise, plain-text descriptions optimized for Large Language Models (LLMs).

## Usage

The primary function is `to_context()`. It takes a Kerykeion model and returns a formatted string.

```python
from kerykeion import AstrologicalSubjectFactory, to_context

# 1. Create Model
subject = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 1, 1, 12, 0, "London", "GB")

# 2. Serialize for AI
ai_context = to_context(subject)
print(ai_context)
```

**Output Preview:**

```text
Chart for Alice
Birth data: 1990-01-01 12:00, London, GB
...
Celestial Points:
  - Sun at 10.81° in Capricorn (Earth) in Tenth House, speed 1.02°/day...
  ...
```

## Supported Models

You can pass almost any Kerykeion object to `to_context`:

- `AstrologicalSubjectModel` (Basic chart)
- `SingleChartDataModel` (Chart with calculated aspects)
- `DualChartDataModel` (Synastry/Transits with inter-aspects)
- `CompositeSubjectModel`
- `PlanetaryReturnModel`

## AI Integration Example

Inject the serialized context directly into your LLM system prompt:

```python
prompt = f"""
You are an expert astrologer. Analyze the following chart data:

{to_context(subject)}

Focus on career potential.
"""
```

## Helper Functions

For finer control, use these individual converters:

| Function                          | Input Model                | Description                             |
| :-------------------------------- | :------------------------- | :-------------------------------------- |
| `kerykeion_point_to_context`      | `KerykeionPointModel`      | Describes a single planet/point.        |
| `lunar_phase_to_context`          | `LunarPhaseModel`          | Describes the lunar phase.              |
| `aspect_to_context`               | `AspectModel`              | Describes an aspect between two points. |
| `point_in_house_to_context`       | `PointInHouseModel`        | Describes a point in another's house.   |
| `astrological_subject_to_context` | `AstrologicalSubjectModel` | Full subject description.               |
| `single_chart_data_to_context`    | `SingleChartDataModel`     | Natal chart with aspects.               |
| `dual_chart_data_to_context`      | `DualChartDataModel`       | Synastry/Transit with inter-aspects.    |
| `element_distribution_to_context` | `ElementDistributionModel` | Element breakdown.                      |
| `quality_distribution_to_context` | `QualityDistributionModel` | Quality breakdown.                      |
| `house_comparison_to_context`     | `HouseComparisonModel`     | House overlay analysis.                 |
| `transit_moment_to_context`       | `TransitMomentModel`       | Single transit moment snapshot.         |
| `transits_time_range_to_context`  | `TransitsTimeRangeModel`   | Time-range transit data.                |

```python
from kerykeion.context_serializer import kerykeion_point_to_context

sun_context = kerykeion_point_to_context(subject.sun)
print(sun_context)
# "Sun at 10.81° in Capricorn in First House, quality: Cardinal, element: Earth..."
```
