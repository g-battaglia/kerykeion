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

### CompositeSubjectModel

Represents a composite chart derived from two subjects.

| Field                  | Type                       | Description                        |
| :--------------------- | :------------------------- | :--------------------------------- |
| `first_subject`        | `AstrologicalSubjectModel` | First source subject.              |
| `second_subject`       | `AstrologicalSubjectModel` | Second source subject.             |
| `composite_chart_type` | `str`                      | Type of composite (e.g. Midpoint). |

Inherits all celestial point fields from `AstrologicalBaseModel`.

### PlanetReturnModel

Represents a Solar or Lunar return chart.

| Field         | Type         | Description             |
| :------------ | :----------- | :---------------------- |
| `return_type` | `ReturnType` | `"Solar"` or `"Lunar"`. |

Inherits all celestial point fields from `AstrologicalBaseModel`.

### AstrologicalBaseModel

Base model for all astrological subjects. Contains common fields for location, time, and all celestial points.

Key fields: `name`, `city`, `nation`, `lng`, `lat`, `tz_str`, `zodiac_type`, `houses_system_identifier`, `sun`, `moon`, `mercury`..., `first_house`..., `ascendant`, etc.

### EphemerisDictModel

Snapshot of planetary positions for a specific date.

| Field     | Type                        | Description             |
| :-------- | :-------------------------- | :---------------------- |
| `date`    | `str`                       | ISO 8601 formatted date |
| `planets` | `List[KerykeionPointModel]` | Planet positions        |
| `houses`  | `List[KerykeionPointModel]` | House cusps             |

### ZodiacSignModel

Metadata for a zodiac sign.

| Field      | Type         | Description              |
| :--------- | :----------- | :----------------------- |
| `sign`     | `Sign`       | e.g. `"Ari"`             |
| `quality`  | `Quality`    | Cardinal, Fixed, Mutable |
| `element`  | `Element`    | Fire, Earth, Air, Water  |
| `emoji`    | `SignsEmoji` | e.g. `"♈️"`             |
| `sign_num` | `int`        | 0-11                     |

### RelationshipScoreModel

Complete compatibility scoring result.

| Field               | Type                                 | Description                    |
| :------------------ | :----------------------------------- | :----------------------------- |
| `score_value`       | `int`                                | Total numerical score.         |
| `score_description` | `RelationshipScoreDescription`       | Category (e.g. "Exceptional"). |
| `is_destiny_sign`   | `bool`                               | Sun-sign compatibility match.  |
| `aspects`           | `List[RelationshipScoreAspectModel]` | Contributing aspects.          |
| `score_breakdown`   | `List[ScoreBreakdownItemModel]`      | Detailed point explanations.   |
| `subjects`          | `List[AstrologicalSubjectModel]`     | The two compared subjects.     |

### RelationshipScoreAspectModel

Aspect contributing to relationship score.

| Field     | Type    | Description          |
| :-------- | :------ | :------------------- |
| `p1_name` | `str`   | First point name.    |
| `p2_name` | `str`   | Second point name.   |
| `aspect`  | `str`   | Aspect name.         |
| `orbit`   | `float` | Actual orb distance. |

### ScoreBreakdownItemModel

Explains a single scoring rule.

| Field         | Type  | Description                               |
| :------------ | :---- | :---------------------------------------- |
| `rule`        | `str` | Rule ID (e.g. "sun_sun_major").           |
| `description` | `str` | Human-readable explanation.               |
| `points`      | `int` | Points awarded.                           |
| `details`     | `str` | Optional extra info (e.g. "orbit: 1.5°"). |

### ActiveAspect

TypedDict for configuring aspect orbs.

| Field  | Type         | Description     |
| :----- | :----------- | :-------------- |
| `name` | `AspectName` | e.g. "trine".   |
| `orb`  | `int`        | Orb in degrees. |

### TransitMomentModel

Snapshot of transits at a specific time.

| Field     | Type                | Description             |
| :-------- | :------------------ | :---------------------- |
| `date`    | `str`               | ISO 8601 datetime.      |
| `aspects` | `List[AspectModel]` | Active transit aspects. |

### TransitsTimeRangeModel

Time series of transit snapshots.

| Field      | Type                       | Description               |
| :--------- | :------------------------- | :------------------------ |
| `transits` | `List[TransitMomentModel]` | List of moment snapshots. |
| `subject`  | `AstrologicalSubjectModel` | The natal subject.        |
| `dates`    | `List[str]`                | All dates in the range.   |

### PointInHouseModel

A point from one chart placed in another chart's house system.

| Field                        | Type    | Description                   |
| :--------------------------- | :------ | :---------------------------- |
| `point_name`                 | `str`   | Planet/point name.            |
| `point_degree`               | `float` | Degree within sign.           |
| `point_sign`                 | `str`   | Zodiac sign.                  |
| `point_owner_name`           | `str`   | Owner subject name.           |
| `projected_house_number`     | `int`   | House in target chart (1-12). |
| `projected_house_name`       | `str`   | House name in target chart.   |
| `projected_house_owner_name` | `str`   | Target subject name.          |

### HouseComparisonModel

Bidirectional house comparison between two subjects.

| Field                           | Type                      | Description                                |
| :------------------------------ | :------------------------ | :----------------------------------------- |
| `first_subject_name`            | `str`                     | Name of first subject.                     |
| `second_subject_name`           | `str`                     | Name of second subject.                    |
| `first_points_in_second_houses` | `List[PointInHouseModel]` | First subject's points in second's houses. |
| `second_points_in_first_houses` | `List[PointInHouseModel]` | Second subject's points in first's houses. |
| `first_cusps_in_second_houses`  | `List[PointInHouseModel]` | First subject's cusps in second's houses.  |
| `second_cusps_in_first_houses`  | `List[PointInHouseModel]` | Second subject's cusps in first's houses.  |

### ElementDistributionModel

Element distribution in a chart.

| Field              | Type    | Description                |
| :----------------- | :------ | :------------------------- |
| `fire`             | `float` | Fire element total points. |
| `earth`            | `float` | Earth element total.       |
| `air`              | `float` | Air element total.         |
| `water`            | `float` | Water element total.       |
| `fire_percentage`  | `int`   | Fire percentage.           |
| `earth_percentage` | `int`   | Earth percentage.          |
| `air_percentage`   | `int`   | Air percentage.            |
| `water_percentage` | `int`   | Water percentage.          |

### QualityDistributionModel

Quality/modality distribution in a chart.

| Field                 | Type    | Description             |
| :-------------------- | :------ | :---------------------- |
| `cardinal`            | `float` | Cardinal quality total. |
| `fixed`               | `float` | Fixed quality total.    |
| `mutable`             | `float` | Mutable quality total.  |
| `cardinal_percentage` | `int`   | Cardinal percentage.    |
| `fixed_percentage`    | `int`   | Fixed percentage.       |
| `mutable_percentage`  | `int`   | Mutable percentage.     |

### SingleChartAspectsModel

Aspects within a single chart (Natal, Composite, Return).

| Field            | Type                       | Description                 |
| :--------------- | :------------------------- | :-------------------------- |
| `subject`        | `AstrologicalSubjectModel` | The chart subject.          |
| `aspects`        | `List[AspectModel]`        | Internal aspects.           |
| `active_points`  | `List[AstrologicalPoint]`  | Points used in calculation. |
| `active_aspects` | `List[ActiveAspect]`       | Aspect configuration.       |

### DualChartAspectsModel

Aspects between two charts (Synastry, Transit).

| Field            | Type                       | Description           |
| :--------------- | :------------------------- | :-------------------- |
| `first_subject`  | `AstrologicalSubjectModel` | Primary chart.        |
| `second_subject` | `AstrologicalSubjectModel` | Secondary chart.      |
| `aspects`        | `List[AspectModel]`        | Inter-chart aspects.  |
| `active_points`  | `List[AstrologicalPoint]`  | Points used.          |
| `active_aspects` | `List[ActiveAspect]`       | Aspect configuration. |

### ChartDataModel (Union)

Type alias: `Union[SingleChartDataModel, DualChartDataModel]`. Represents any chart data output from `ChartDataFactory`.

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

| Value              | Number | Description                                       |
| :----------------- | :----- | :------------------------------------------------ |
| `"First_House"`    | 1      | Self, identity, physical appearance, beginnings.  |
| `"Second_House"`   | 2      | Possessions, values, self-worth, resources.       |
| `"Third_House"`    | 3      | Communication, siblings, short trips, learning.   |
| `"Fourth_House"`   | 4      | Home, family, roots, emotional foundation.        |
| `"Fifth_House"`    | 5      | Creativity, romance, children, pleasure, play.    |
| `"Sixth_House"`    | 6      | Health, daily work, service, routines.            |
| `"Seventh_House"`  | 7      | Partnerships, marriage, open enemies, contracts.  |
| `"Eighth_House"`   | 8      | Transformation, shared resources, death, rebirth. |
| `"Ninth_House"`    | 9      | Philosophy, higher education, travel, expansion.  |
| `"Tenth_House"`    | 10     | Career, public image, reputation, authority.      |
| `"Eleventh_House"` | 11     | Friends, groups, hopes, wishes, social networks.  |
| `"Twelfth_House"`  | 12     | Subconscious, secrets, spirituality, isolation.   |

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

| Value               | Description                                                  |
| :------------------ | :----------------------------------------------------------- |
| `"FAGAN_BRADLEY"`   | Standard Western Sidereal ayanamsa, widely used in the West. |
| `"LAHIRI"`          | Standard Vedic/Jyotish ayanamsa, official in India.          |
| `"DELUCE"`          | DeLuce ayanamsa.                                             |
| `"RAMAN"`           | B.V. Raman's ayanamsa, popular in South India.               |
| `"USHASHASHI"`      | Ushashashi ayanamsa.                                         |
| `"KRISHNAMURTI"`    | K.S. Krishnamurti's ayanamsa for KP system.                  |
| `"DJWHAL_KHUL"`     | Djwhal Khul (Theosophical) ayanamsa.                         |
| `"YUKTESHWAR"`      | Sri Yukteshwar's ayanamsa.                                   |
| `"JN_BHASIN"`       | J.N. Bhasin's ayanamsa.                                      |
| `"BABYL_KUGLER1"`   | Babylonian (Kugler 1).                                       |
| `"BABYL_KUGLER2"`   | Babylonian (Kugler 2).                                       |
| `"BABYL_KUGLER3"`   | Babylonian (Kugler 3).                                       |
| `"BABYL_HUBER"`     | Babylonian (Huber).                                          |
| `"BABYL_ETPSC"`     | Babylonian (ETPSC).                                          |
| `"ALDEBARAN_15TAU"` | Aldebaran at 15° Taurus, ancient reference point.            |
| `"HIPPARCHOS"`      | Based on Hipparchos' observations.                           |
| `"SASSANIAN"`       | Sassanian (Persian) ayanamsa.                                |
| `"J2000"`           | Julian epoch J2000.0 reference frame.                        |
| `"J1900"`           | Julian epoch J1900.0 reference frame.                        |
| `"B1950"`           | Besselian epoch B1950.0 reference frame.                     |

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

| Value               | Phase Index | Description                                   |
| :------------------ | :---------- | :-------------------------------------------- |
| `"New Moon"`        | 0           | Moon conjunct Sun; invisible, new beginnings. |
| `"Waxing Crescent"` | 1           | First sliver visible; intention setting.      |
| `"First Quarter"`   | 2           | Half moon; action, challenges, decisions.     |
| `"Waxing Gibbous"`  | 3           | Building toward full; refinement, adjustment. |
| `"Full Moon"`       | 4           | Moon opposite Sun; culmination, illumination. |
| `"Waning Gibbous"`  | 5           | Disseminating; sharing, teaching, gratitude.  |
| `"Last Quarter"`    | 6           | Half moon waning; release, letting go.        |
| `"Waning Crescent"` | 7           | Final sliver; rest, surrender, preparation.   |

---

### `LunarPhaseEmoji`

Emojis corresponding to the lunar phases.

| Emoji  | Phase Index | Phase Name      |
| :----- | :---------- | :-------------- |
| `"🌑"` | 0           | New Moon        |
| `"🌒"` | 1           | Waxing Crescent |
| `"🌓"` | 2           | First Quarter   |
| `"🌔"` | 3           | Waxing Gibbous  |
| `"🌕"` | 4           | Full Moon       |
| `"🌖"` | 5           | Waning Gibbous  |
| `"🌗"` | 6           | Last Quarter    |
| `"🌘"` | 7           | Waning Crescent |

---

### `KerykeionChartTheme`

Available visual themes for chart rendering.

| Value                  | Description                                         |
| :--------------------- | :-------------------------------------------------- |
| `"classic"`            | Traditional white background, standard colors.      |
| `"light"`              | Minimalist light mode with soft tones.              |
| `"dark"`               | Modern dark mode for reduced eye strain.            |
| `"dark-high-contrast"` | Dark mode with enhanced contrast for accessibility. |
| `"strawberry"`         | Pink/red color palette, playful aesthetic.          |
| `"black-and-white"`    | High contrast monochrome for print output.          |

---

### `KerykeionChartLanguage`

Supported language codes for chart labels.

| Code   | Language   |
| :----- | :--------- |
| `"EN"` | English    |
| `"FR"` | French     |
| `"PT"` | Portuguese |
| `"IT"` | Italian    |
| `"CN"` | Chinese    |
| `"ES"` | Spanish    |
| `"RU"` | Russian    |
| `"TR"` | Turkish    |
| `"DE"` | German     |
| `"HI"` | Hindi      |

---

### `ReturnType`

Types of planetary returns supported.

| Value     | Description                                           |
| :-------- | :---------------------------------------------------- |
| `"Solar"` | Sun returns to natal position; annual birthday chart. |
| `"Lunar"` | Moon returns to natal position; monthly cycle chart.  |

---

### `CompositeChartType`

Types of composite charts.

| Value        | Description                                       |
| :----------- | :------------------------------------------------ |
| `"Midpoint"` | Chart created from midpoints of two natal charts. |

---

### `PointType`

Distinguishes between celestial bodies and house cusps.

| Value                 | Description                           |
| :-------------------- | :------------------------------------ |
| `"AstrologicalPoint"` | Planets, asteroids, angles, etc.      |
| `"House"`             | House cusps (1st through 12th house). |

---

### `SignsEmoji`

Zodiac sign symbols.

| Emoji   | Sign        |
| :------ | :---------- |
| `"♈️"` | Aries       |
| `"♉️"` | Taurus      |
| `"♊️"` | Gemini      |
| `"♋️"` | Cancer      |
| `"♌️"` | Leo         |
| `"♍️"` | Virgo       |
| `"♎️"` | Libra       |
| `"♏️"` | Scorpio     |
| `"♐️"` | Sagittarius |
| `"♑️"` | Capricorn   |
| `"♒️"` | Aquarius    |
| `"♓️"` | Pisces      |

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

## Internal Schemas (`chart_template_model`)

These models are used internally for SVG generation but exposed for advanced customization.

### `ChartTemplateModel`

Variables passed to the Jinja2 template for rendering the SVG.

| Field                         | Type                                         | Description                             |
| :---------------------------- | :------------------------------------------- | :-------------------------------------- |
| `viewBox`                     | `str`                                        | SVG viewbox string.                     |
| `chart_width`, `chart_height` | `int`                                        | Dimensions of the chart.                |
| `cx`, `cy`                    | `float`                                      | Center coordinates.                     |
| `outer_radius`                | `int`                                        | Radius of the outer rim.                |
| `inner_radius`                | `int`                                        | Radius of the inner wheel.              |
| `planets_settings`            | `List[KerykeionSettingsCelestialPointModel]` | Configuration for each planet.          |
| `paper_color_0`               | `str`                                        | Background color.                       |
| `chart_name`                  | `str`                                        | Title of the chart.                     |
| `chart_first_subject`         | `str`                                        | Name of the primary subject.            |
| `makeLunarPhase`              | `str`                                        | SVG path data for the lunar phase icon. |

_(And many more styling variables)_

## Detailed Settings Models

### `KerykeionLanguageCelestialPointModel`

Used within `KerykeionLanguageModel` to define localized names for specific bodies.

| Field                    | Description                           |
| :----------------------- | :------------------------------------ |
| `Sun`                    | Localized name for Sun.               |
| `Moon`                   | Localized name for Moon.              |
| `Mercury`, `Venus`, etc. | Localized name for respective planet. |
| `True_North_Lunar_Node`  | Localized name for North Node.        |
| `Pars_Fortunae`          | Localized name for Part of Fortune.   |
