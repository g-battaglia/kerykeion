# AI Context Serializer

The `context_serializer` module is designed to convert Kerykeion's astrological data models into precise, non-qualitative, and non-repetitive textual descriptions. This output is optimized for consumption by Large Language Models (LLMs) and AI applications, providing them with the essential data context needed to generate interpretations or answer astrological questions.

## Overview

The module provides a single main entry point, the `to_context` function, which accepts any supported Kerykeion Pydantic model and returns a formatted string.

**Key Features:**

-   **Standardized Output:** Consistent formatting for all astrological data.
-   **Non-Qualitative:** Provides raw data (positions, aspects, etc.) without interpretive text (e.g., "good", "bad", "lucky").
-   **Comprehensive Support:** Handles Natal, Synastry, Composite, Transit, Solar/Lunar Return, Dual Return charts, and individual components.
-   **House & Cusp Comparison:** Serializes both planetary overlays and cusp-in-house overlays for dual charts.
-   **Type-Safe:** Built on Kerykeion's Pydantic v2 models.

## Basic Usage

The primary way to use the serializer is via the `to_context` function.

```python
from kerykeion import AstrologicalSubjectFactory, to_context

# 1. Create a subject
subject = AstrologicalSubjectFactory.from_birth_data(
    "John Doe", 1990, 1, 1, 12, 0, "London", "GB"
)

# 2. Convert to context
context = to_context(subject)
print(context)
```

**Output Example:**

```text
Chart for John Doe
Birth data: 1990-01-01 12:00, London, GB
Coordinates: 51.51°N, -0.13°W
Timezone: Europe/London
Zodiac system: Tropical
House system: Placidus
Perspective: Apparent Geocentric

Celestial Points:
  - Sun at 10.81° in Capricorn in Tenth House, quality: Cardinal, element: Earth, direct motion, speed 1.0195°/day, declination -23.00°
  - Moon at 25.60° in Aquarius in Eleventh House, quality: Fixed, element: Air, direct motion, speed 12.4796°/day, declination -15.08°
  ...
```

## Supported Models

The `to_context` function supports the following Kerykeion models:

| Model Type                 | Description                                            |
| :------------------------- | :----------------------------------------------------- |
| `AstrologicalSubjectModel` | Basic natal chart information (planets, houses, axes). |
| `SingleChartDataModel`     | Natal chart with calculated aspects.                   |
| `DualChartDataModel`       | Dual charts (Transit, Synastry, DualReturnChart) with inter-aspects and house comparison. |
| `CompositeSubjectModel`    | Composite chart (midpoint or other methods).           |
| `PlanetReturnModel`        | Solar and Lunar Return charts.                         |
| `KerykeionPointModel`      | Individual celestial points (e.g., just the Sun).      |
| `LunarPhaseModel`          | Lunar phase information.                               |
| `AspectModel`              | Individual planetary aspects.                          |
| `ElementDistributionModel` | Element balance (Fire, Earth, Air, Water).             |
| `QualityDistributionModel` | Quality balance (Cardinal, Fixed, Mutable).            |

## Advanced Examples

### Natal Chart with Aspects

To include aspects in the context, create a `SingleChartDataModel` first:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, to_context

subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1985, 10, 26, 8, 15, "New York", "US"
)
chart_data = ChartDataFactory.create_natal_chart_data(subject)

print(to_context(chart_data))
```

### Synastry

Generate context for relationship analysis:

```python
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, to_context

alice = AstrologicalSubjectFactory.from_birth_data("Alice", ...)
bob = AstrologicalSubjectFactory.from_birth_data("Bob", ...)

synastry_data = ChartDataFactory.create_synastry_chart_data(alice, bob)

print(to_context(synastry_data))
```

### Solar Return

Generate context for predictive analysis:

```python
from kerykeion import AstrologicalSubjectFactory, PlanetaryReturnFactory, to_context

subject = AstrologicalSubjectFactory.from_birth_data("Alice", ...)
factory = PlanetaryReturnFactory(subject, online=False, lng=subject.lng, lat=subject.lat, tz_str=subject.tz_str)
solar_return = factory.next_return_from_year(2024, "Solar")

print(to_context(solar_return))
```

## Integration with AI Prompts

The output of `to_context` is designed to be directly injected into system prompts for AI agents.

**Example Prompt Template:**

> You are an expert astrologer. I will provide you with the astrological data for a subject.
> Please analyze the chart focusing on career potential.
>
> **Astrological Data:**
>
> ```
> {context_output}
> ```

This approach ensures the AI receives accurate, structured data without hallucinating planetary positions.
