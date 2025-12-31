---
title: 'Types & Schemas'
category: 'Reference'
description: 'Core data models, type definitions, and schemas'
tags: ['docs', 'types', 'models', 'pydantic', 'kerykeion', 'schemas']
order: 12
---

# Types & Schemas

This section documents the core data structures, Pydantic models, and type definitions used throughout the Kerykeion library to ensure type safety and data consistency.

## Overview

The `kerykeion.schemas` package contains all the data definitions:

-   **`kr_models`**: Pydantic models for astrological subjects, charts, and points.
-   **`kr_literals`**: String literals for strict type hinting (Zodiac signs, Planets, Houses, etc.).
-   **`settings_models`**: Configuration models for library settings.
-   **`chart_template_model`**: Models for SVG chart generation.
-   **`kerykeion_exception`**: Standard exception class for the library.

### Subscriptable Models

All Kerykeion models inherit from `SubscriptableBaseModel`, allowing dictionary-like access to fields in addition to dot notation.

```python
subject = AstrologicalSubjectFactory(...)
# Access as object
print(subject.name)
# Access as dict
print(subject["name"])
```

## Core Models (`kr_models`)

Import from: `kerykeion.schemas.kr_models`

### AstrologicalSubjectModel

Represents a person or event to be analyzed.

| Field                  | Type           | Description                           |
| :--------------------- | :------------- | :------------------------------------ |
| `name`                 | `str`          | Name of the subject                   |
| `year`, `month`, `day` | `int`          | Birth/Experience date                 |
| `hour`, `minute`       | `int`          | Birth/Experience time                 |
| `city`                 | `str`          | Location city                         |
| `nation`               | `str`          | Country code                          |
| `lng`, `lat`           | `float`        | Coordinates                           |
| `tz_str`               | `str`          | Timezone string (e.g., "Europe/Rome") |
| `zodiac_type`          | `ZodiacType`   | "Tropical" or "Sidereal"              |
| `sidereal_mode`        | `SiderealMode` | Specific Ayanamsa if Sidereal         |

### KerykeionPointModel

Detailed information about a celestial body or house cusp.

| Field        | Type                | Description                                  |
| :----------- | :------------------ | :------------------------------------------- |
| `name`       | `AstrologicalPoint` | Planet/Point name (e.g., "Sun", "Ascendant") |
| `sign`       | `Sign`              | Zodiac sign (e.g., "Ari")                    |
| `sign_num`   | `int`               | 0-11 index of the sign                       |
| `position`   | `float`             | Degree within the sign (0-30)                |
| `abs_pos`    | `float`             | Absolute zodiac degree (0-360)               |
| `house`      | `Houses`            | House placement                              |
| `retrograde` | `bool`              | True if retrograde                           |
| `element`    | `Element`           | Fire, Earth, Air, or Water                   |
| `quality`    | `Quality`           | Cardinal, Fixed, or Mutable                  |

### SingleChartDataModel

The complete data structure for a calculated single chart (Natal, Return, etc.).

| Field                  | Type                       | Description                                 |
| :--------------------- | :------------------------- | :------------------------------------------ |
| `subject`              | `AstrologicalSubjectModel` | The subject of the chart                    |
| `aspects`              | `List[AspectModel]`        | List of internal aspects                    |
| `element_distribution` | `ElementDistributionModel` | Points/Percentage for each element          |
| `quality_distribution` | `QualityDistributionModel` | Points/Percentage for each quality          |
| `planets`              | `Dict`                     | Dictionary of `KerykeionPointModel` objects |
| `houses`               | `Dict`                     | Dictionary of House cusps                   |

### DualChartDataModel

Data structure for comparing two charts (Synastry, Transits).

| Field                | Type                       | Description                             |
| :------------------- | :------------------------- | :-------------------------------------- |
| `first_subject`      | `AstrologicalSubjectModel` | The primary subject (e.g., Natal)       |
| `second_subject`     | `AstrologicalSubjectModel` | The secondary subject (e.g., Transit)   |
| `aspects`            | `List[AspectModel]`        | Inter-chart aspects                     |
| `house_comparison`   | `HouseComparisonModel`     | Analysis of planets in partner's houses |
| `relationship_score` | `RelationshipScoreModel`   | Compatibility scoring (Synastry only)   |

### AspectModel

Represents an astrological aspect between two points.

| Field                | Type                 | Description                              |
| :------------------- | :------------------- | :--------------------------------------- |
| `p1_name`, `p2_name` | `str`                | Names of the two points involved         |
| `aspect`             | `AspectName`         | Name of the aspect (e.g., "conjunction") |
| `orbit`              | `float`              | The actual orb (deviation from exact)    |
| `aspect_degrees`     | `int`                | Theoretical angle (e.g., 120 for trine)  |
| `aspect_movement`    | `AspectMovementType` | "Applying", "Separating", or "Static"    |

---

## Literals & Constants (`kr_literals`)

Import from: `kerykeion.schemas.kr_literals`

These Literal types define the allowed string values for various model fields, providing strict type checking and autocompletion in your IDE.

---

### `ZodiacType`

Defines the zodiac system to use for calculations.

| Value        | Description                                                                                               |
| :----------- | :-------------------------------------------------------------------------------------------------------- |
| `"Tropical"` | Based on the seasons and the position of the Sun at the spring equinox. Most common in Western astrology. |
| `"Sidereal"` | Based on the fixed stars. Commonly used in Vedic (Jyotish) astrology. Requires a `SiderealMode` setting.  |

---

### `Sign`

The 12 zodiac signs, using abbreviated 3-character names.

| Value   | Full Name   | Element | Quality  |
| :------ | :---------- | :------ | :------- |
| `"Ari"` | Aries       | Fire    | Cardinal |
| `"Tau"` | Taurus      | Earth   | Fixed    |
| `"Gem"` | Gemini      | Air     | Mutable  |
| `"Can"` | Cancer      | Water   | Cardinal |
| `"Leo"` | Leo         | Fire    | Fixed    |
| `"Vir"` | Virgo       | Earth   | Mutable  |
| `"Lib"` | Libra       | Air     | Cardinal |
| `"Sco"` | Scorpio     | Water   | Fixed    |
| `"Sag"` | Sagittarius | Fire    | Mutable  |
| `"Cap"` | Capricorn   | Earth   | Cardinal |
| `"Aqu"` | Aquarius    | Air     | Fixed    |
| `"Pis"` | Pisces      | Water   | Mutable  |

---

### `SignNumbers`

Integer indices for zodiac signs, from `0` (Aries) to `11` (Pisces).

---

### `Element`

The four classical elements.

| Value     | Signs                    |
| :-------- | :----------------------- |
| `"Fire"`  | Aries, Leo, Sagittarius  |
| `"Earth"` | Taurus, Virgo, Capricorn |
| `"Air"`   | Gemini, Libra, Aquarius  |
| `"Water"` | Cancer, Scorpio, Pisces  |

---

### `Quality`

The three modalities (also called "modes" or "quadruplicities").

| Value        | Description                   | Signs                              |
| :----------- | :---------------------------- | :--------------------------------- |
| `"Cardinal"` | Initiating energy, beginnings | Aries, Cancer, Libra, Capricorn    |
| `"Fixed"`    | Stable, resistant to change   | Taurus, Leo, Scorpio, Aquarius     |
| `"Mutable"`  | Adaptable, flexible           | Gemini, Virgo, Sagittarius, Pisces |

---

### `AstrologicalPoint`

Comprehensive literal for all supported celestial points.

**Main Planets:**
`"Sun"`, `"Moon"`, `"Mercury"`, `"Venus"`, `"Mars"`, `"Jupiter"`, `"Saturn"`, `"Uranus"`, `"Neptune"`, `"Pluto"`

**Lunar Nodes:**
`"Mean_North_Lunar_Node"`, `"True_North_Lunar_Node"`, `"Mean_South_Lunar_Node"`, `"True_South_Lunar_Node"`

**Special Points:**
`"Chiron"`, `"Mean_Lilith"`, `"True_Lilith"`, `"Earth"`, `"Pholus"`, `"Vertex"`, `"Anti_Vertex"`

**Asteroids:**
`"Ceres"`, `"Pallas"`, `"Juno"`, `"Vesta"`

**Trans-Neptunian Objects (TNOs):**
`"Eris"`, `"Sedna"`, `"Haumea"`, `"Makemake"`, `"Ixion"`, `"Orcus"`, `"Quaoar"`

**Fixed Stars:**
`"Regulus"`, `"Spica"`

**Arabic Parts (Lots):**
`"Pars_Fortunae"` (Part of Fortune), `"Pars_Spiritus"` (Part of Spirit), `"Pars_Amoris"` (Part of Love), `"Pars_Fidei"` (Part of Faith)

**Axial Cusps (Angles):**
`"Ascendant"`, `"Medium_Coeli"` (MC/Midheaven), `"Descendant"`, `"Imum_Coeli"` (IC)

---

### `Houses`

The 12 astrological houses.

`"First_House"`, `"Second_House"`, `"Third_House"`, `"Fourth_House"`, `"Fifth_House"`, `"Sixth_House"`, `"Seventh_House"`, `"Eighth_House"`, `"Ninth_House"`, `"Tenth_House"`, `"Eleventh_House"`, `"Twelfth_House"`

---

### `HouseNumbers`

Integers `1` through `12` representing the house numbers.

---

### `ChartType`

Defines the type of chart being generated.

| Value                 | Description                                               |
| :-------------------- | :-------------------------------------------------------- |
| `"Natal"`             | Birth chart for a single person or event.                 |
| `"Transit"`           | Current planetary positions overlaid on a natal chart.    |
| `"Synastry"`          | Comparison of two natal charts for relationship analysis. |
| `"Composite"`         | A single chart derived from the midpoints of two charts.  |
| `"SingleReturnChart"` | A Solar or Lunar return chart viewed alone.               |
| `"DualReturnChart"`   | A return chart overlaid on the natal chart.               |

---

### `AspectName`

The names of all supported aspects.

| Value              | Degrees | Description                                         |
| :----------------- | :------ | :-------------------------------------------------- |
| `"conjunction"`    | 0°      | Planets at the same degree; powerful, fused energy. |
| `"semi-sextile"`   | 30°     | Minor aspect; slight tension or adjustment.         |
| `"semi-square"`    | 45°     | Minor hard aspect; friction.                        |
| `"sextile"`        | 60°     | Harmonious; opportunities and talent.               |
| `"quintile"`       | 72°     | Creative aspect; talent.                            |
| `"square"`         | 90°     | Major hard aspect; challenge and growth.            |
| `"trine"`          | 120°    | Major harmonious aspect; ease and flow.             |
| `"sesquiquadrate"` | 135°    | Minor hard aspect; agitation.                       |
| `"biquintile"`     | 144°    | Creative aspect.                                    |
| `"quincunx"`       | 150°    | Inconjunct; requires adjustment.                    |
| `"opposition"`     | 180°    | Major hard aspect; polarity and awareness.          |

---

### `AspectMovementType`

Describes the phase of an aspect between two points.

| Value          | Description                                                            |
| :------------- | :--------------------------------------------------------------------- |
| `"Applying"`   | The orb is decreasing; the aspect is forming and considered stronger.  |
| `"Separating"` | The orb is increasing; the aspect is dissolving.                       |
| `"Static"`     | Neither point is moving relative to the other (e.g., two fixed stars). |

---

### `SiderealMode`

The Ayanamsa (precession mode) used for Sidereal calculations.

-   `"FAGAN_BRADLEY"` (Standard Western Sidereal)
-   `"LAHIRI"` (Standard Vedic/Jyotish)
-   `"DELUCE"`
-   `"RAMAN"`
-   `"USHASHASHI"`
-   `"KRISHNAMURTI"`
-   `"DJWHAL_KHUL"`
-   `"YUKTESHWAR"`
-   `"JN_BHASIN"`
-   `"BABYL_KUGLER1"`, `"BABYL_KUGLER2"`, `"BABYL_KUGLER3"`
-   `"BABYL_HUBER"`
-   `"BABYL_ETPSC"`
-   `"ALDEBARAN_15TAU"`
-   `"HIPPARCHOS"`
-   `"SASSANIAN"`
-   `"J2000"`, `"J1900"`, `"B1950"`

---

### `HousesSystemIdentifier`

Single-character identifiers for different house systems.

| ID    | House System                 | Description                                                        |
| :---- | :--------------------------- | :----------------------------------------------------------------- |
| `"A"` | Equal (from Asc)             | Houses are 30° each, starting from Ascendant.                      |
| `"B"` | Alcabitius                   | Medieval semi-arc system.                                          |
| `"C"` | Campanus                     | Space-based, uses prime vertical.                                  |
| `"D"` | Equal (from MC)              | Houses are 30° each, with MC on 10th cusp.                         |
| `"F"` | Carter Poli-Equatorial       | Rarely used system.                                                |
| `"H"` | Horizon/Azimuth              | Based on azimuth circle.                                           |
| `"I"` | Sunshine                     | Modern solar-based system.                                         |
| `"i"` | Sunshine/Alternate           | Alternate Sunshine calculation.                                    |
| `"K"` | **Koch**                     | Time-based, uses birthplace latitude. Popular in Germany.          |
| `"L"` | Pullen SD (Sinusoidal Delta) | Modern system.                                                     |
| `"M"` | Morinus                      | Based on the equator, rarely used.                                 |
| `"N"` | Equal / 1st House = Aries    | Fixed house system.                                                |
| `"O"` | Porphyry                     | Quadrant-based, equal division of quadrants.                       |
| `"P"` | **Placidus**                 | **Default.** Most popular in modern Western astrology. Time-based. |
| `"Q"` | Pullen SR (Sinusoidal Ratio) | Modern system.                                                     |
| `"R"` | **Regiomontanus**            | Space-based system. Standard for Horary astrology.                 |
| `"S"` | Sripati                      | Vedic-influenced system.                                           |
| `"T"` | Polich/Page (Topocentric)    | Similar to Placidus, accounts for location.                        |
| `"U"` | Krusinski-Pisa-Goelzer       | Modern system.                                                     |
| `"V"` | Equal / Vehlow               | Equal houses with Asc in middle of 1st house.                      |
| `"W"` | **Whole Sign**               | Each house is an entire sign. Standard in Hellenistic/Vedic.       |
| `"X"` | Axial Rotation / Meridian    | Meridian-based system.                                             |
| `"Y"` | APC Houses                   | Astrological PC houses.                                            |

---

### `PerspectiveType`

Defines the viewpoint for calculations.

| Value                   | Description                                                                                |
| :---------------------- | :----------------------------------------------------------------------------------------- |
| `"Apparent Geocentric"` | Earth-centered, accounting for light-time and aberration. **Standard for most astrology.** |
| `"True Geocentric"`     | Earth-centered, without light-time correction.                                             |
| `"Heliocentric"`        | Sun-centered. Used for some esoteric techniques.                                           |
| `"Topocentric"`         | Observer's exact location on Earth's surface. Most accurate for Moon position.             |

---

### `LunarPhaseName`

The eight traditional names for the Moon's phases.

`"New Moon"`, `"Waxing Crescent"`, `"First Quarter"`, `"Waxing Gibbous"`, `"Full Moon"`, `"Waning Gibbous"`, `"Last Quarter"`, `"Waning Crescent"`

---

### `LunarPhaseEmoji`

Emojis corresponding to the lunar phases.

`"🌑"`, `"🌒"`, `"🌓"`, `"🌔"`, `"🌕"`, `"🌖"`, `"🌗"`, `"🌘"`

---

### `KerykeionChartTheme`

Available visual themes for chart rendering.

`"light"`, `"dark"`, `"dark-high-contrast"`, `"classic"`, `"strawberry"`, `"black-and-white"`

---

### `KerykeionChartLanguage`

Supported language codes for chart labels.

`"EN"`, `"FR"`, `"PT"`, `"IT"`, `"CN"`, `"ES"`, `"RU"`, `"TR"`, `"DE"`, `"HI"`

---

### `ReturnType`

Types of planetary returns supported.

`"Solar"`, `"Lunar"`

---

### `CompositeChartType`

Types of composite charts.

`"Midpoint"`

---

### `PointType`

Distinguishes between celestial bodies and house cusps.

`"AstrologicalPoint"`, `"House"`

---

### `SignsEmoji`

Zodiac sign symbols.

`"♈️"`, `"♉️"`, `"♊️"`, `"♋️"`, `"♌️"`, `"♍️"`, `"♎️"`, `"♏️"`, `"♐️"`, `"♑️"`, `"♒️"`, `"♓️"`

---

### `HouseNumbers`

Integer identifiers for houses (1-12).

---

### `RelationshipScoreDescription`

Categorical descriptions for compatibility scores.

`"Minimal"`, `"Medium"`, `"Important"`, `"Very Important"`, `"Exceptional"`, `"Rare Exceptional"`

---

## Settings (`settings_models`)

Import from: `kerykeion.schemas.settings_models`

### KerykeionSettingsModel

Global configuration for the library, primarily handling internationalization.

-   **`language_settings`**: A dictionary mapping language codes (e.g., "EN", "IT") to `KerykeionLanguageModel`.

### KerykeionLanguageModel

Defines all the string labels used in chart generation and reports.

-   `Sun`, `Moon`, `Mercury`... (Planet names)
-   `Ari`, `Tau`... (Sign names)
-   `First_House`... (House names)
-   `Fire`, `Earth`... (Element names)

---

## Exceptions (`kerykeion_exception`)

Import from: `kerykeion.schemas.kerykeion_exception`

### `KerykeionException`

The base exception class for all library-specific errors.

```python
from kerykeion.schemas import KerykeionException

try:
    chart = KrInstance(...)
except KerykeionException as e:
    print(f"Error calculating chart: {e}")
```
