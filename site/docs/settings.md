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
| `DEFAULT_ACTIVE_POINTS`                | Standard points: Sun, Moon, the planets, the True North Node, Chiron, plus Asc & MC (14 points) |
| `TRADITIONAL_ASTROLOGY_ACTIVE_POINTS`  | Classical planets (Sun-Saturn) + True Lunar Nodes (9 points)       |
| `ALL_ACTIVE_POINTS`                    | Complete list including asteroids, TNOs, Uranian points, and Arabic parts (53 names; no fixed stars -- those are requested via `active_fixed_stars`) |
| `V5_DEFAULT_ACTIVE_POINTS`             | The v5 default set (18 points), for reproducing pre-v6 output. Also importable from `kerykeion.settings` |
| `DEFAULT_PREDICTIVE_POINTS`            | The 14 points the predictive factories scan by default. Import from `kerykeion.settings.chart_defaults` |

```python
from kerykeion.settings.config_constants import (
    DEFAULT_ACTIVE_POINTS,
    TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
    ALL_ACTIVE_POINTS,
)

# Use extended point set
subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False,
    active_points=ALL_ACTIVE_POINTS
)

# Use classical planets only (traditional/Hellenistic astrology)
subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False,
    active_points=TRADITIONAL_ASTROLOGY_ACTIVE_POINTS
)
```

### Active Aspects Presets

| Constant                         | Description                                                      |
| :------------------------------- | :--------------------------------------------------------------- |
| `DEFAULT_ACTIVE_ASPECTS`         | Core aspects (conj, opp, trine, sextile, square)     |
| `ALL_ACTIVE_ASPECTS`             | Includes minor aspects (semi-sextile, quincunx, etc.)            |
| `DISCEPOLO_SCORE_ACTIVE_ASPECTS` | Orbs per Ciro Discepolo scoring methodology                      |
| `PREDICTIVE_ACTIVE_ASPECTS`      | The five Ptolemaic aspects at a flat 3° orb -- the default for transits, returns and progressions |

`DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS` (`{"Sun": 1.5, "Moon": 1.5}`) widens the
orb for the luminaries in natal work; see
[Aspects](/content/docs/aspects) for how the adjustments
are combined.

```python
from kerykeion import AspectsFactory
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
| `KNOWN_GLYPH_NAMES`                 | `frozenset` of the 55 point names that ship a dedicated SVG `<symbol>`. |

Two builders extend the celestial-point settings at render time with entries the
static table cannot hold, because the names are only known once the chart is
computed:

| Helper | Signature | Purpose |
| :----- | :-------- | :------ |
| `build_dynamic_fixed_star_settings` | `(star_names: list[str], existing_settings: list \| tuple)` | Appends a settings entry per catalog fixed star in the chart. |
| `build_dynamic_midpoint_settings` | `(midpoint_names: list[str], existing_settings: list \| tuple)` | Appends a settings entry per computed midpoint. |
| `resolve_glyph_id` | `(name: str) -> str` | Maps a point name to its SVG `<symbol>` id. Pair-specific midpoint names resolve to the generic `"Midpoint"` glyph; a name outside `KNOWN_GLYPH_NAMES` falls back to `"FixedStar"`. |

### Fixed-Star and Zodiac Defaults

Import from: `kerykeion.settings.config_constants`

| Constant | Value | Description |
| :------- | :---- | :---------- |
| `DEFAULT_FIXED_STARS` | 23 names | The opt-in fixed-star preset: the 15 Behenian stars plus 8 further bright stars. |
| `ROYAL_FIXED_STARS` | 4 names | Aldebaran, Regulus, Antares, Fomalhaut. |
| `BEHENIAN_FIXED_STARS` | 15 names | The medieval Behenian set (the 4 Royal Stars among them). |
| `DEFAULT_SIDEREAL_MODE` | `"FAGAN_BRADLEY"` | Ayanamsa used when `zodiac_type="Sidereal"` and no `sidereal_mode` is given. |
| `DEFAULT_NAKSHATRA_AYANAMSA` | `"LAHIRI"` | Ayanamsa used to place nakshatras on a non-sidereal chart. |

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
from kerykeion.settings import load_language_settings

# Create custom overrides
overrides = {
    "IT": {
        "celestial_points": {"Sun": "Il Sole"}
    }
}
settings = load_language_settings(overrides)
```

### `load_language_pair`

`load_language_pair(language, overrides=None) -> tuple[dict, dict]`

Returns `(selected_language, english_fallback)` and materializes only those two,
avoiding the full-table deepcopy `load_language_settings` performs. This is what
`ChartDrawer` uses to resolve its labels.

```python
from kerykeion.settings import load_language_pair

italian, english = load_language_pair("IT")
print(italian["celestial_points"]["Sun"])
```

### `load_settings_mapping` (deprecated)

> **Deprecated since 6.0.0, removed in 7.0.0.** Use
> [`load_language_settings`](#load_language_settings) instead — it returns the
> same language mapping and accepts the same overrides. `load_settings_mapping`
> is no longer part of `kerykeion.settings.__all__` and emits a
> `DeprecationWarning` when called.

Resolves the full configuration mapping, including overrides for bundled language settings.

```python
# Preferred:
from kerykeion.settings import load_language_settings

settings = load_language_settings()
```

### Advanced Settings Types

These types are used internally for type hinting but are exported for advanced usage.

#### `LANGUAGE_SETTINGS`

The raw dictionary containing all built-in translations. Modifying this directly is not recommended; use `load_language_settings` with overrides instead.

#### `SettingsSource`

Type alias for `Optional[Mapping[str, Any]]`. Represents the structure of a settings override dictionary.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
