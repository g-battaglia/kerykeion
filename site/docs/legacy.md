---
title: 'Legacy API'
category: 'Reference'
description: 'Information about removed backward-compatibility classes and migration to v6.'
tags: ['docs', 'legacy', 'v4', 'v5', 'migration']
order: 23
---

# Legacy API (Removed in v6)

Kerykeion v5 included a backward compatibility layer (via `kerykeion.backword`) that provided wrapper classes for the old v4 API. **This layer has been removed in v6.**

> [!WARNING]
> The following classes no longer exist and will raise `ImportError` if imported. Migrate to the factory-based API described below.

## Removed Classes

| Removed Class | v6 Replacement |
|---------------|----------------|
| `AstrologicalSubject(...)` | `AstrologicalSubjectFactory.from_birth_data(...)` |
| `KerykeionChartSVG(subject)` | `ChartDataFactory.create_natal_chart_data(subject)` + `ChartDrawer(chart_data)` |
| `NatalAspects(subject)` | `AspectsFactory.single_chart_aspects(subject)` |
| `SynastryAspects(s1, s2)` | `AspectsFactory.dual_chart_aspects(s1, s2)` |

## Migration Example

```python
# v4/v5 (NO LONGER WORKS in v6):
# from kerykeion import AstrologicalSubject
# subject = AstrologicalSubject("Alice", 1990, 5, 15, 10, 30, city="London", nation="GB")

# v6 (correct):
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 5, 15, 10, 30,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)
```

For full migration instructions, see the [Migration Guide](/content/docs/migration).

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
