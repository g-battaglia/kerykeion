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

| Constant                               | Description                                                        |
| :------------------------------------- | :----------------------------------------------------------------- |
| `DEFAULT_ACTIVE_POINTS`                | Standard points: Sun, Moon, planets, True Lunar Nodes, Chiron, Lilith, 4 angles (18 points) |
| `TRADITIONAL_ASTROLOGY_ACTIVE_POINTS`  | Classical planets (Sun-Saturn) + True Lunar Nodes (9 points)       |
| `ALL_ACTIVE_POINTS`                    | Complete list including asteroids, TNOs, Arabic parts, fixed stars |

```python
from kerykeion.settings.config_constants import (
    DEFAULT_ACTIVE_POINTS,
    TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
    ALL_ACTIVE_POINTS,
)

# Use extended point set
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    active_points=ALL_ACTIVE_POINTS
)

# Use classical planets only (traditional/Hellenistic astrology)
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS
)
```

### Active Aspects Presets

| Constant                         | Description                                                      |
| :------------------------------- | :--------------------------------------------------------------- |
| `DEFAULT_ACTIVE_ASPECTS`         | Core aspects (conj, opp, trine, sextile, square) plus quintile     |
| `ALL_ACTIVE_ASPECTS`             | Includes minor aspects (semi-sextile, quincunx, etc.)            |
| `DISCEPOLO_SCORE_ACTIVE_ASPECTS` | Orbs per Ciro Discepolo scoring methodology                      |

```python
from kerykeion.settings.config_constants import ALL_ACTIVE_ASPECTS

aspects = AspectsFactory.single_chart_aspects(
    subject,
    active_aspects=ALL_ACTIVE_ASPECTS
)
```

### Chart Configuration Presets

Import from: `kerykeion.settings.chart_defaults` (also re-exported from `kerykeion.settings`)

| Constant                            | Description                                  |
| :---------------------------------- | :------------------------------------------- |
| `DEFAULT_CHART_COLORS`              | Default color scheme for charts.             |
| `DEFAULT_CELESTIAL_POINTS_SETTINGS` | Default settings for planets (colors, etc.). |
| `DEFAULT_CHART_ASPECTS_SETTINGS`    | Default aspect configuration.                |

## Settings Model

### `KerykeionSettingsModel`

The settings are defined by a Pydantic model that controls the library's language/localization behavior.

**Key Configuration Options:**

-   `language_settings`: A dictionary mapping language codes (e.g., `"EN"`, `"IT"`) to `KerykeionLanguageModel` instances containing localized strings for planet names, signs, houses, etc.

_(See `kerykeion.schemas.settings_models` for the full model definition)_

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

### `load_settings_mapping`

Resolves the full configuration mapping, including overrides for bundled language settings.

```python
from kerykeion.settings import load_settings_mapping

settings_map = load_settings_mapping()
```

### Advanced Settings Types

These types are used internally for type hinting but are exported for advanced usage.

#### `LANGUAGE_SETTINGS`

The raw dictionary containing all built-in translations. Modifying this directly is not recommended; use `load_language_settings` with overrides instead.

#### `SettingsSource`

Type alias for `Optional[Mapping[str, Any]]`. Represents the structure of a settings override dictionary.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
