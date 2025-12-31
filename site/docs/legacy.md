---
title: 'Legacy API'
category: 'Reference'
description: 'Documentation for deprecated classes and backward compatibility layers.'
tags: ['docs', 'legacy', 'v4', 'backwards-compatibility']
order: 20
---

# Legacy API (Backward Compatibility)

Kerykeion v5 introduces a new factory-based architecture. However, to support existing codebases, the library includes a backward compatibility layer defined in `kerykeion.backword`.

> [!WARNING]
> These classes are deprecated and may be removed in future versions (v6+). New projects should use the proper Factories (e.g., `AstrologicalSubjectFactory`).

## `AstrologicalSubject` (Legacy Wrapper)

A wrapper class that emulates the behavior of the old `AstrologicalSubject` class.

```python
# Legacy usage (still works but issues warning)
from kerykeion import AstrologicalSubject

subject = AstrologicalSubject(
    "Alice", 1990, 5, 15, 10, 30,
    city="London", nat="GB"
)
print(subject.sun["sign"])
```

### Constructor

The constructor signature attempts to match v4, forwarding arguments to `AstrologicalSubjectFactory.from_birth_data`.

-   `name` (str)
-   `year`, `month`, `day`, `hour`, `minute` (int)
-   `lng`, `lat` (float, optional)
-   `tz_str` (str, optional)
-   `city`, `nat` (str, optional): `nat` is mapped to `nation`.
-   `online` (bool)

## `KerykeionChartSVG` (Legacy Wrapper)

Wrapper for the chart generation logic, delegating to `ChartDrawer`.

```python
from kerykeion import KerykeionChartSVG

chart = KerykeionChartSVG(subject)
chart.makeSVG()
print(chart.content)
```

## `NatalAspects` & `SynastryAspects`

Wrappers for `AspectsFactory`.

```python
from kerykeion import NatalAspects

aspects = NatalAspects(subject)
for aspect in aspects.aspects:
    print(aspect)
```
