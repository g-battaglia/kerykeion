---
title: 'AI Context Serializer'
category: 'Integration'
tags: ['docs', 'ai', 'context', 'kerykeion']
order: 19
---

# AI Context Serializer

The `to_context` function converts Kerykeion data models into precise, plain-text descriptions optimized for Large Language Models (LLMs).

## Usage

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

-   `AstrologicalSubjectModel` (Basic chart)
-   `SingleChartDataModel` (Chart with calculated aspects)
-   `DualChartDataModel` (Synastry/Transits with inter-aspects)
-   `CompositeSubjectModel`
-   `PlanetaryReturnModel`

## AI Integration Example

Inject the serialized context directly into your LLM system prompt:

```python
prompt = f"""
You are an expert astrologer. Analyze the following chart data:

{to_context(subject)}

Focus on career potential.
"""
```
