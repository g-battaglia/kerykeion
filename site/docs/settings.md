---
title: 'Settings'
category: 'Reference'
description: 'Global configuration settings for Kerykeion'
tags: ['docs', 'settings', 'config']
order: 17
---

# Settings (`kerykeion.settings`)

This module handles the global configuration for Kerykeion calculations, default parameters, and cache management.

## Configuration Constants

Import from: `kerykeion.settings.config_constants`

### Active Points Presets

| Constant                | Description                                                        |
| :---------------------- | :----------------------------------------------------------------- |
| `DEFAULT_ACTIVE_POINTS` | Standard points: Sun, Moon, planets, Chiron, Lilith, 4 angles      |
| `ALL_ACTIVE_POINTS`     | Complete list including asteroids, TNOs, Arabic parts, fixed stars |

```python
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS, ALL_ACTIVE_POINTS

# Use extended point set
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    active_points=ALL_ACTIVE_POINTS
)
```

### Active Aspects Presets

| Constant                         | Description                                                      |
| :------------------------------- | :--------------------------------------------------------------- |
| `DEFAULT_ACTIVE_ASPECTS`         | Major aspects only (conj, opp, trine, sextile, square, quintile) |
| `ALL_ACTIVE_ASPECTS`             | Includes minor aspects (semi-sextile, quincunx, etc.)            |
| `DISCEPOLO_SCORE_ACTIVE_ASPECTS` | Orbs per Ciro Discepolo scoring methodology                      |

```python
from kerykeion.settings.config_constants import ALL_ACTIVE_ASPECTS

aspects = AspectsFactory.single_chart_aspects(
    subject,
    active_aspects=ALL_ACTIVE_ASPECTS
)
```

## Settings Model

### `KerykeionSettingsModel`

The settings are defined by a Pydantic model that controls various aspects of the library's behavior.

**Key Configuration Options:**

-   `json_dir`: Directory to store JSON output (default: "json").
-   `cache_dir`: Directory to store cache files (default: "cache").

_(See `kerykeion.schemas.settings_models` for the full list of configurable options)_

## Translation Utilities

Import from: `kerykeion.settings`

Helper functions to access the library's internal localization strings (planets, signs, etc.).

### `get_translations`

Fetches a localized string from the internal dictionary.

```python
from kerykeion.settings import get_translations

# Get Italian name for Sun
sun_it = get_translations(
    "celestial_points.Sun",
    default="Sole",
    language="IT"
)
print(sun_it) # "Sole"
```

### `load_language_settings`

Returns the entire language setting dictionary, optionally merging with overrides.

```python
# Create custom overrides
overrides = {
    "IT": {
        "celestial_points": {"Sun": "Il Sole"}
    }
}
settings = load_language_settings(overrides)
```
