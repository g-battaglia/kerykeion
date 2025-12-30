---
title: 'Types & Models'
category: 'Reference'
description: 'Core data models and type definitions'
tags: ['docs', 'types', 'models', 'pydantic', 'kerykeion']
order: 12
---

# Kerykeion Types (`kerykeion.kr_types`)

This module exports standard models, literals, and exception types used throughout the library to maintain type safety and data structure consistency.

## Overview

The `kerykeion.kr_types` module aggregates several internal sub-modules:

- **`kr_models`**: Pydantic models for astrological data structures.
- **`kr_literals`**: Literal constants for type hinting.
- **`kerykeion_exception`**: Custom exception class.
- **`chart_types`**: Dictionary types used in chart generation.
- **`settings_models`**: Settings configuration models.

## KerykeionException

```python
from kerykeion.kr_types import KerykeionException

try:
    # calculation code
except KerykeionException as e:
    print(f"Calculation error: {e}")
```

Custom exception raised when astrological calculations fail or invalid data is provided.

## Pydantic Models

Kerykeion uses Pydantic for data validation and structure. Key models typically include:

- `AstrologicalSubjectModel`
- `ChartDataModel`
- `PlanetModel`
- `HouseModel`

_(Refer to `kr_models` source code for detailed schema definitions)_
