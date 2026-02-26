---
title: 'AI Context Serializer'
description: 'Optimize your astrological data for Large Language Models. Learn how to use the AI Context Serializer to convert charts into precise, well-formed XML.'
category: 'Integration'
tags: ['docs', 'ai', 'context', 'kerykeion']
order: 19
---

# AI Context Serializer

The `to_context` function converts Kerykeion data models into precise, well-formed XML optimized for Large Language Models (LLMs). Optional fields are omitted when `None`, and all values are properly escaped.

## Usage

The primary function is `to_context()`. It takes a Kerykeion model and returns an XML string.

```python
from kerykeion import AstrologicalSubjectFactory, to_context

# 1. Create Model
subject = AstrologicalSubjectFactory.from_birth_data("Alice", 1990, 1, 1, 12, 0, "London", "GB")

# 2. Serialize for AI
ai_context = to_context(subject)
print(ai_context)
```

**Output Preview:**

```xml
<chart name="Alice">
  <birth_data date="1990-01-01" time="12:00" city="London" nation="GB" ... />
  <config zodiac="Tropical" house_system="Placidus" perspective="Apparent Geocentric" />
  <planets>
    <point name="Sun" position="10.81" sign="Capricorn" element="Earth" quality="Cardinal" house="Tenth House" motion="direct" speed="1.02" />
    ...
  </planets>
  <houses>...</houses>
  <lunar_phase name="Waning Gibbous" phase="20" degrees_between="254.32" emoji="🌖" />
</chart>
```

## Supported Models

You can pass almost any Kerykeion object to `to_context`:

- `AstrologicalSubjectModel` (Basic chart)
- `SingleChartDataModel` (Chart with calculated aspects)
- `DualChartDataModel` (Synastry/Transits with inter-aspects)
- `CompositeSubjectModel`
- `PlanetReturnModel`
- `MoonPhaseOverviewModel`
- `KerykeionPointModel`, `LunarPhaseModel`, `AspectModel`
- `ElementDistributionModel`, `QualityDistributionModel`
- `PointInHouseModel`, `HouseComparisonModel`
- `TransitMomentModel`, `TransitsTimeRangeModel`

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
| `kerykeion_point_to_context`      | `KerykeionPointModel`      | Single planet/point as `<point />`.     |
| `lunar_phase_to_context`          | `LunarPhaseModel`          | Lunar phase as `<lunar_phase />`.       |
| `aspect_to_context`               | `AspectModel`              | Aspect as `<aspect />`.                 |
| `point_in_house_to_context`       | `PointInHouseModel`        | Point in house as `<point_in_house />`. |
| `astrological_subject_to_context` | `AstrologicalSubjectModel` | Full subject as `<chart>...</chart>`.   |
| `single_chart_data_to_context`    | `SingleChartDataModel`     | Natal chart as `<chart_analysis>`.      |
| `dual_chart_data_to_context`      | `DualChartDataModel`       | Synastry/Transit as `<chart_analysis>`. |
| `element_distribution_to_context` | `ElementDistributionModel` | Element breakdown as `<element_distribution />`. |
| `quality_distribution_to_context` | `QualityDistributionModel` | Quality breakdown as `<quality_distribution />`. |
| `house_comparison_to_context`     | `HouseComparisonModel`     | House overlay as `<house_overlay>`.     |
| `transit_moment_to_context`       | `TransitMomentModel`       | Transit snapshot as `<transit_moment>`. |
| `transits_time_range_to_context`  | `TransitsTimeRangeModel`   | Time-range transits as `<transit_analysis>`. |
| `moon_phase_overview_to_context`  | `MoonPhaseOverviewModel`   | Moon phase overview as `<moon_phase_overview>`. |

```python
from kerykeion.context_serializer import kerykeion_point_to_context

sun_context = kerykeion_point_to_context(subject.sun)
print(sun_context)
# <point name="Sun" position="10.81" sign="Capricorn" abs_pos="280.81"
#   quality="Cardinal" element="Earth" house="Tenth House" motion="direct" speed="1.02" />
```

## XML Format Details

- **Self-closing tags** for atomic data: `<point ... />`, `<aspect ... />`, `<lunar_phase ... />`
- **Nested tags** for structured data: `<chart>`, `<chart_analysis>`, `<moon_phase_overview>`
- **Optional fields omitted** when `None` — tags/attributes are not rendered at all
- **Non-qualitative** — no interpretive words like "good", "bad", "strong", "weak"
- **Properly escaped** via `xml.sax.saxutils` — safe for any input data

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
