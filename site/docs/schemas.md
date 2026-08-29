---
title: 'Types & Schemas'
category: 'Reference'
description: 'Core data models, type definitions, and schemas'
tags: ['docs', 'types', 'models', 'pydantic', 'kerykeion', 'schemas']
order: 13
---

# Types & Schemas

This section documents the core data structures, Pydantic models, and type definitions used throughout the Kerykeion library to ensure type safety and data consistency.

## Overview

The `kerykeion.schemas` package contains all the data definitions:

-   **`models`**: Pydantic models for astrological subjects, charts, and points.
-   **`literals`**: String literals for strict type hinting (Zodiac signs, Planets, Houses, etc.).
-   **`settings_models`**: Configuration models for library settings.
-   **`chart_template_model`**: Models for SVG chart generation.
-   **`exceptions`**: Standard exception class for the library.

### Subscriptable Models

All Kerykeion models inherit from `SubscriptableBaseModel`, allowing dictionary-like access to fields in addition to dot notation.

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False
)
# Access as object
print(subject.name)
# Access as dict
print(subject["name"])
```

## Core Models (`models`)

Import from: `kerykeion.schemas.models`

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
| `altitude`             | `float \| None` | Observer altitude in meters; used by Topocentric calculations |
| `tz_str`               | `str`          | Timezone string (e.g., "Europe/Rome") |
| `zodiac_type`          | `ZodiacType`   | "Tropical" or "Sidereal"              |
| `sidereal_mode`        | `SiderealMode \| None` | Specific Ayanamsa if Sidereal         |
| `ayanamsa_value`       | `float \| None`| Ayanamsa offset in degrees (sidereal only) |
| `nakshatra_ayanamsa`   | `SiderealMode \| None` | Ayanamsa used to place the nakshatras on a non-sidereal chart. `None` on a sidereal chart, on a chart with no nakshatras, and when the legacy uncorrected behaviour was requested |
| `nakshatra_ayanamsa_value` | `float \| None` | Degrees actually subtracted before the 27-fold division. `None` exactly when `nakshatra_ayanamsa` is |
| `is_diurnal`           | `bool`         | Whether the chart is diurnal (Sun above horizon) |

### KerykeionPointModel

Detailed information about a celestial body or house cusp.

| Field        | Type                              | Description                                  |
| :----------- | :-------------------------------- | :------------------------------------------- |
| `name`       | `AstrologicalPoint \| Houses`     | Planet/Point/House name (e.g., "Sun", "First_House") |
| `sign`       | `Sign`                            | Zodiac sign (e.g., "Ari")                    |
| `sign_num`   | `SignNumbers`                     | 0-11 index of the sign                       |
| `position`   | `float`                           | Degree within the sign (0-30)                |
| `abs_pos`    | `float`                           | Absolute zodiac degree (0-360)               |
| `emoji`      | `str`                             | Unicode emoji for the sign                   |
| `point_type` | `PointType`                       | `"AstrologicalPoint"` or `"House"`           |
| `house`      | `Houses \| None`                  | House placement (None for house cusps)       |
| `retrograde` | `bool \| None`                    | True if retrograde (None for house cusps)    |
| `element`    | `Element`                         | Fire, Earth, Air, or Water                   |
| `quality`    | `Quality`                         | Cardinal, Fixed, or Mutable                  |
| `speed`      | `float \| None`                   | Daily motion in degrees/day                  |
| `declination`| `float \| None`                   | Equatorial declination in degrees            |
| `magnitude`  | `float \| None`                   | Apparent visual magnitude (fixed stars only) |
| `is_out_of_bounds` | `bool \| None`             | True if declination exceeds the Sun's maximum (~23.44°) |
| `essential_dignity` | `str \| None`              | Ptolemaic dignity (Domicile, Exaltation, etc.). Requires `calculate_dignities=True` |
| `nakshatra`  | `str \| None`                     | Vedic lunar mansion name. Requires `calculate_nakshatra=True`; on a non-sidereal chart the longitude is rotated by `nakshatra_ayanamsa` first |
| `nakshatra_pada` | `int \| None`                 | Nakshatra pada/quarter (1-4). Requires `calculate_nakshatra=True` |
| `nakshatra_lord` | `str \| None`                 | Vimsottari Dasha lord planet. Requires `calculate_nakshatra=True` |
| `gauquelin_sector` | `float \| None`             | Gauquelin 36-sector position. Requires `calculate_gauquelin=True` |
| `motion_state` | `MotionState \| None`           | Speed classification (`retrograde`/`stationary`/`stationary_retrograde`/`stationary_direct`/`slow`/`average`/`fast`). Populated for the ten planets in Earth-centred perspectives. |
| `azimuth`    | `float \| None`                   | Azimuth angle in degrees. Requires `calculate_local_space=True` |
| `altitude_above_horizon` | `float \| None`       | Altitude above horizon. Requires `calculate_local_space=True` |

### SingleChartDataModel

The complete data structure for a calculated single chart (Natal, Return, etc.).

| Field                  | Type                       | Description                                 |
| :--------------------- | :------------------------- | :------------------------------------------ |
| `chart_type`           | `Literal`                  | `"Natal"`, `"Composite"`, or `"SingleReturnChart"` |
| `subject`              | Subject Model              | The subject (`AstrologicalSubjectModel`, `CompositeSubjectModel`, or `PlanetReturnModel`) |
| `aspects`              | `List[AspectModel]`        | List of internal aspects                    |
| `element_distribution` | `ElementDistributionModel` | Points/Percentage for each element          |
| `quality_distribution` | `QualityDistributionModel` | Points/Percentage for each quality          |
| `angularities`         | `List[AngularityModel]`    | Classical planets conjunct the four angles (within orb) |
| `stelliums`            | `List[StelliumModel]`      | Houses with three or more classical planets |
| `active_points`        | `List[AstrologicalPoint]`  | Points used in calculation                  |
| `active_aspects`       | `List[ActiveAspect]`       | Aspect configuration used                   |

### DualChartDataModel

Data structure for comparing two charts (Synastry, Transits).

| Field                  | Type                       | Description                             |
| :--------------------- | :------------------------- | :-------------------------------------- |
| `chart_type`           | `Literal`                  | `"Transit"`, `"Synastry"`, `"DualReturnChart"`, or `"Progression"` |
| `first_subject`        | `AstrologicalSubjectModel \| CompositeSubjectModel \| PlanetReturnModel` | The primary subject (e.g., Natal) |
| `second_subject`       | `AstrologicalSubjectModel \| PlanetReturnModel` | The secondary subject (e.g., Transit) |
| `aspects`              | `List[AspectModel]`        | Inter-chart aspects                     |
| `house_comparison`     | `HouseComparisonModel \| None` | Analysis of planets in partner's houses (optional) |
| `relationship_score`   | `RelationshipScoreModel \| None` | Compatibility scoring (optional, synastry only) |
| `element_distribution` | `ElementDistributionModel` | Points/Percentage for each element      |
| `quality_distribution` | `QualityDistributionModel` | Points/Percentage for each quality      |
| `first_subject_angularities` | `List[AngularityModel]` | Angularities for the first subject    |
| `first_subject_stelliums` | `List[StelliumModel]`     | Stelliums for the first subject       |
| `second_subject_angularities` | `List[AngularityModel]` | Angularities for the second subject  |
| `second_subject_stelliums` | `List[StelliumModel]`    | Stelliums for the second subject      |
| `active_points`        | `List[AstrologicalPoint]`  | Points used in calculation              |
| `active_aspects`       | `List[ActiveAspect]`       | Aspect configuration used               |

### AngularityModel

A classical planet conjunct one of the four chart angles.

| Field      | Type    | Description                                                        |
| :--------- | :------ | :----------------------------------------------------------------- |
| `point`    | `str`   | The planet's name.                                                 |
| `angle`    | `str`   | Which angle (`Ascendant`, `Medium_Coeli`, `Descendant`, `Imum_Coeli`). |
| `distance` | `float` | Shortest ecliptic arc between planet and angle, in degrees.        |

### StelliumModel

A concentration of classical planets in one house.

| Field    | Type         | Description                                  |
| :------- | :----------- | :------------------------------------------- |
| `house`  | `int`        | House number (1-12).                         |
| `points` | `list[str]`  | Names of the planets gathered there.         |

### AspectModel

Represents an astrological aspect between two points.

| Field                | Type                 | Description                              |
| :------------------- | :------------------- | :--------------------------------------- |
| `p1_name`, `p2_name` | `str`                | Names of the two points involved         |
| `p1_owner`, `p2_owner` | `str`              | Owner subject names (same for single chart, different for dual) |
| `aspect`             | `str`                | Name of the aspect (e.g., "conjunction") |
| `orbit`              | `float`              | The actual orb (deviation from exact, always non-negative) |
| `aspect_degrees`     | `int`                | Theoretical angle (e.g., 120 for trine)  |
| `aspect_movement`    | `AspectMovementType` | "Applying", "Separating", or "Static"    |
| `p1_abs_pos`         | `float`              | Absolute position of first point         |
| `p2_abs_pos`         | `float`              | Absolute position of second point        |
| `diff`               | `float`              | Angular difference between the points    |
| `p1`, `p2`           | `int`                | Swiss Ephemeris IDs of the points        |
| `p1_speed`, `p2_speed` | `float`            | Speed (degrees/day) of each point        |

### CompositeSubjectModel

Represents a composite chart derived from two subjects.

| Field                  | Type                       | Description                        |
| :--------------------- | :------------------------- | :--------------------------------- |
| `first_subject`        | `AstrologicalSubjectModel` | First source subject.              |
| `second_subject`       | `AstrologicalSubjectModel` | Second source subject.             |
| `composite_chart_type` | `str`                      | Type of composite (e.g. Midpoint). |
| `is_diurnal`           | `bool \| None`             | Sect of the chart. Real boolean for Davison charts; `None` for midpoint composites (no single sky). Sect-aware consumers treat `None` as a day chart. |

Inherits all celestial point fields from `AstrologicalBaseModel`.

### PlanetReturnModel

Represents a planetary return chart.

| Field         | Type         | Description             |
| :------------ | :----------- | :---------------------- |
| `return_type` | `ReturnType` | `"Solar"`, `"Lunar"`, `"Heliocentric"`, or `"Lunar_Node_Crossing"`. |
| `is_diurnal`  | `bool \| None` | Sect of the return moment (Sun above/below the horizon). Populated by `PlanetaryReturnFactory`. |

Inherits all celestial point fields from `AstrologicalBaseModel`.

### AstrologicalBaseModel

Base model for all astrological subjects. Contains common fields for location, time, and all celestial points.

Key fields: `name`, `city`, `nation`, `lng`, `lat`, `altitude`, `tz_str`,
`zodiac_type`, `houses_system_identifier`, `perspective_type`, `sun`, `moon`,
`mercury`..., `first_house`..., `ascendant`, `polar_house_fallbacks`,
`effective_houses_system_identifier`, `effective_houses_system_name`, etc.
`altitude` is the observer height in meters retained for Topocentric
calculations.

`houses_system_identifier` (and its `houses_system_name`) always report the
**requested** system, even when the cusps did not come from it. Inside the polar
circle a quadrant system is undefined and the cusps are recomputed with a system
that is defined everywhere; the request survives untouched so that a relocation
or a re-cast starts from what the caller asked for rather than inheriting the
substitute.

- `polar_house_fallbacks` (`list[PolarHouseFallbackModel]`, empty when nothing was substituted) records each substitution: the requested and used systems, the real latitude, the latitude the successful call ran at, the epoch's polar threshold and obliquity, and which chart products changed.
- `effective_houses_system_identifier` / `effective_houses_system_name` are derived from that list and report the division the cusps really came from. With no fallback they equal the requested pair.

New in v5.12: `ayanamsa_value` (`float | None`) -- the computed ayanamsa offset in degrees for sidereal charts (`None` for tropical).

New in v6: `nakshatra_ayanamsa` (`SiderealMode | None`) and `nakshatra_ayanamsa_value` (`float | None`) -- the ayanamsa a **non-sidereal** chart rotated its longitudes by to derive the nakshatras, and the offset in degrees it actually subtracted. Both are `None` on a sidereal chart (its own `sidereal_mode`/`ayanamsa_value` apply), on a chart that computed no nakshatras, and when `nakshatra_ayanamsa=None` selected the legacy uncorrected behaviour.

### EphemerisDictModel

Snapshot of planetary positions for a specific date.

| Field     | Type                        | Description             |
| :-------- | :-------------------------- | :---------------------- |
| `date`    | `str`                       | ISO 8601 formatted date |
| `planets` | `List[KerykeionPointModel]` | Planet positions        |
| `houses`  | `List[KerykeionPointModel]` | House cusps             |
| `fixed_stars` | `List[KerykeionPointModel]` | Fixed star positions. Empty unless the producing factory requested stars via `active_fixed_stars`. |
| `ephemeris_warnings` | `List[EphemerisWarningModel]` | Requested optional points omitted at this sample because no permitted ephemeris or local model produced a value. Empty when nothing was dropped. |
| `polar_house_fallbacks` | `List[PolarHouseFallbackModel]` | House systems substituted at this sample because the requested one is undefined at the sample's latitude. Empty at temperate latitudes. |

### LunarPhaseModel

Compact lunar phase information attached to every `AstrologicalSubjectModel` (via the `lunar_phase` field).

| Field                 | Type              | Description                                              |
| :-------------------- | :---------------- | :------------------------------------------------------- |
| `degrees_between_s_m` | `float \| int`    | Angular separation between the Sun and Moon in degrees.  |
| `moon_phase`          | `int`             | Lunation day (1-28), derived from the Sun-Moon angle.    |
| `moon_emoji`          | `LunarPhaseEmoji` | Emoji representation of the phase (e.g. `"🌕"`).        |
| `moon_phase_name`     | `LunarPhaseName`  | Text name (e.g. `"Full Moon"`, `"Waxing Crescent"`).    |
| `major_phase`         | `str`             | Nearest of the four syzygies (New Moon, First Quarter, Full Moon, Last Quarter). |
| `stage`               | `str`             | `"waxing"` or `"waning"`.                                |

`moon_phase_name` and `moon_emoji` come from windows **centred on the syzygies**: New and Full span ±6.4286° of the exact aspect, the two quarters ±19.2857°, and the four crescent/gibbous names fill the rest. The name therefore tracks the event rather than a bin boundary. The `moon_phase` index (1-28) is unchanged.

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False
)
print(subject.lunar_phase.moon_phase_name)   # e.g. "Waxing Gibbous"
print(subject.lunar_phase.moon_emoji)         # e.g. "🌔"
print(subject.lunar_phase.degrees_between_s_m)  # e.g. 135.7
```

### MoonPhaseOverviewModel

Top-level model returned by `MoonPhaseDetailsFactory`. Groups timestamp, Sun summary, Moon summary, and location data into a single structure suitable for API responses or serialization.

| Field       | Type                              | Description                                                |
| :---------- | :-------------------------------- | :--------------------------------------------------------- |
| `timestamp` | `int`                             | Unix timestamp of the observation moment.                  |
| `datestamp`  | `str`                             | ISO 8601 formatted date string.                            |
| `sun`       | `MoonPhaseSunInfoModel \| None`   | Sun rise/set times, position, next solar eclipse info.     |
| `moon`      | `MoonPhaseMoonSummaryModel`       | Phase name, illumination, zodiac signs, moonrise/moonset, etc. |
| `location`  | `MoonPhaseLocationModel \| None`  | Latitude, longitude, and precision metadata.               |

**Nested models** (all fields optional unless noted):

| Model                              | Key Fields                                                                      |
| :--------------------------------- | :------------------------------------------------------------------------------ |
| `MoonPhaseSunInfoModel`            | `sunrise`, `sunset`, `solar_noon`, `day_length`, `position`, `next_solar_eclipse` |
| `MoonPhaseSunPositionModel`        | `altitude`, `azimuth`, `distance`                                               |
| `MoonPhaseMoonSummaryModel`        | `phase`, `phase_name`, `major_phase`, `stage`, `illumination`, `age_days`, `emoji`, `zodiac`, `moonrise`, `moonrise_timestamp`, `moonset`, `moonset_timestamp`, `detailed`, `events` |
| `MoonPhaseMoonPositionModel`       | `altitude`, `azimuth`, `distance`, `parallactic_angle`, `phase_angle`           |
| `MoonPhaseMoonDetailedModel`       | `position`, `visibility`, `upcoming_phases`, `illumination_details`             |
| `MoonPhaseUpcomingPhasesModel`     | `new_moon`, `first_quarter`, `full_moon`, `last_quarter` (each a `MoonPhaseMajorPhaseWindowModel`) |
| `MoonPhaseIlluminationDetailsModel`| `percentage`, `visible_fraction`, `phase_angle`                                 |
| `MoonPhaseZodiacModel`             | `sun_sign`, `moon_sign`                                                         |
| `MoonPhaseLocationModel`           | `latitude`, `longitude`, `precision`, `using_default_location`, `note`          |

### ZodiacSignModel

Metadata for a zodiac sign.

| Field      | Type         | Description              |
| :--------- | :----------- | :----------------------- |
| `sign`     | `Sign`       | e.g. `"Ari"`             |
| `quality`  | `Quality`    | Cardinal, Fixed, Mutable |
| `element`  | `Element`    | Fire, Earth, Air, Water  |
| `emoji`    | `SignsEmoji` | e.g. `"♈️"`             |
| `sign_num` | `SignNumbers`| 0-11                     |

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
| `details`     | `Optional[str]` | Optional extra info (e.g. "orbit: 1.5°"). Defaults to `None`. |

### ActiveAspect

TypedDict for configuring aspect orbs.

| Field  | Type         | Description     |
| :----- | :----------- | :-------------- |
| `name` | `AspectName` | e.g. "trine".   |
| `orb`  | `float`      | Orb in degrees. |

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
| `subject`  | `AstrologicalSubjectModel \| None` | The natal subject.        |
| `dates`    | `List[str] \| None`                | All dates in the range.   |

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
| `point_owner_house_number`   | `Optional[int]` | House number in owner's chart. |
| `point_owner_house_name`     | `Optional[str]` | House name in owner's chart.  |

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

| Field | Type | Description |
| :--------------- | :------------------------- | :-------------------------- |
| `subject` | Subject Model | The chart subject (`AstrologicalSubjectModel`, `CompositeSubjectModel`, or `PlanetReturnModel`). |
| `aspects` | `List[AspectModel]` | Internal aspects. |
| `active_points` | `List[AstrologicalPoint]` | Points used in calculation. |
| `active_aspects` | `List[ActiveAspect]` | Aspect configuration. |

### DualChartAspectsModel

Aspects between two charts (Synastry, Transit).

| Field | Type | Description |
| :--------------- | :------------------------- | :-------------------- |
| `first_subject` | Subject Model | Primary chart (`AstrologicalSubjectModel`, `CompositeSubjectModel`, or `PlanetReturnModel`). |
| `second_subject` | Subject Model | Secondary chart (`AstrologicalSubjectModel`, `CompositeSubjectModel`, or `PlanetReturnModel`). |
| `aspects` | `List[AspectModel]` | Inter-chart aspects. |
| `active_points` | `List[AstrologicalPoint]` | Points used. |
| `active_aspects` | `List[ActiveAspect]` | Aspect configuration. |

### ChartDataModel (Union)

Type alias: `Union[SingleChartDataModel, DualChartDataModel]`. Represents any chart data output from `ChartDataFactory`.

---

## V6 Advanced Models

These models are returned by the v6 advanced calculation factories. Each factory's documentation page has the full field reference.

### Predictive Models

| Model | Factory | Description |
| :---- | :------ | :---------- |
| `SecondaryProgressionsResultModel` | [`SecondaryProgressionFactory`](/content/docs/secondary_progressions_factory) | Progressed subject + progressed-to-natal aspects |
| `ProgressedToNatalAspectModel` | `SecondaryProgressionFactory` | A single progressed-to-natal aspect contact |
| `SolarArcSubjectModel` | [`SolarArcFactory`](/content/docs/solar_arc_factory) | Solar arc, directed points, directed-to-natal aspects |
| `SolarArcDirectedPointModel` | `SolarArcFactory` | A natal point after applying the solar-arc shift |
| `SolarArcDirectedAspectModel` | `SolarArcFactory` | A directed-to-natal aspect |
| `PrimaryDirectionModel` | [`PrimaryDirectionsFactory`](/content/docs/primary_directions_factory) | A single primary direction result (arc, years) |
| `SpeculumEntryModel` | `PrimaryDirectionsFactory` | Speculum coordinate table entry |
| `MidpointModel` | [`MidpointFactory`](/content/docs/midpoint_factory) | Midpoint of two points + aspect activations |
| `MidpointAspectModel` | `MidpointFactory` | An aspect formed between a midpoint and a third point |

### Astronomical Models

| Model | Factory | Description |
| :---- | :------ | :---------- |
| `EclipseSearchResultModel` | [`EclipseFactory`](/content/docs/eclipse_factory) | Container for solar + lunar eclipse search results |
| `SolarEclipseModel` | `EclipseFactory` | A single solar eclipse event |
| `LunarEclipseModel` | `EclipseFactory` | A single lunar eclipse event |
| `PlanetaryPhenomenaCollectionModel` | [`PlanetaryPhenomenaFactory`](/content/docs/planetary_phenomena_factory) | Collection of planetary phenomena |
| `PlanetaryPhenomenaModel` | `PlanetaryPhenomenaFactory` | Phenomena for a single planet, including `solar_phase` |
| `SolarPhaseThresholdsModel` | `PlanetaryPhenomenaFactory` | The three elongation cut-offs a collection's `solar_phase` labels were read against |
| `PlanetaryNodesCollectionModel` | [`PlanetaryNodesFactory`](/content/docs/planetary_nodes_factory) | Collection of orbital nodes/apsides |
| `PlanetaryNodeModel` | `PlanetaryNodesFactory` | Nodes and apsides for one planet (`periapsis`/`apoapsis`/`apsis_kind`; `perihelion`/`aphelion` deprecated) |
| `HeliacalEventModel` | [`HeliacalFactory`](/content/docs/heliacal_factory) | A single heliacal visibility event |
| `OccultationModel` | [`OccultationFactory`](/content/docs/occultation_factory) | A single lunar occultation event |
| `ACGLineModel` | [`AstroCartographyFactory`](/content/docs/astro_cartography_factory) | A planetary line on the ACG map |
| `ACGLinePointModel` | `AstroCartographyFactory` | A geographic coordinate on an ACG line |

### Traditional / Hellenistic Models

| Model | Factory | Description |
| :---- | :------ | :---------- |
| `ProfectionsModel` | [`ProfectionsFactory`](/content/docs/profections_factory) | Annual profection timeline with activated houses |
| `ProfectionYearModel` | `ProfectionsFactory` | A single profection year |
| `FirdariaModel` | [`FirdariaFactory`](/content/docs/firdaria_factory) | Firdaria planetary period timeline |
| `FirdariaPeriodModel` | `FirdariaFactory` | A major firdaria period |
| `FirdariaSubPeriodModel` | `FirdariaFactory` | A sub-period within a major firdaria |
| `MutualReceptionModel` | [`MutualReceptionsFactory`](/content/docs/receptions_factory) | A single mutual reception pair |
| `MutualReceptionsModel` | `MutualReceptionsFactory` | Collection of mutual receptions in a chart |
| `HoraryIndicatorsModel` | [`HoraryIndicatorsFactory`](/content/docs/horary_factory) | Horary chart analysis with significators and considerations |
| `HorarySignificatorModel` | `HoraryIndicatorsFactory` | A horary significator planet |
| `HoraryConsiderationModel` | `HoraryIndicatorsFactory` | A horary consideration before judgment |

### Chart Analysis Models

| Model | Factory | Description |
| :---- | :------ | :---------- |
| `AngularityModel` | [`ChartDataFactory`](/content/docs/chart_data_factory) | A planet conjunct a chart angle (within orb) |
| `StelliumModel` | `ChartDataFactory` | A house concentration of three or more planets |
| `ProgressedPointModel` | [`SecondaryProgressionFactory`](/content/docs/secondary_progressions_factory) | Per-point natal-vs-progressed comparison with sign-change flag |

---

## Literals & Constants (`literals`)

Import from: `kerykeion.schemas.literals`

These Literal types define the allowed string values for various model fields, providing strict type checking and autocompletion in your IDE.

---

### `MotionState`

Classification of a celestial body's speed relative to its mean daily motion. Populated on `KerykeionPointModel.motion_state` for the ten planets in Earth-centred perspectives; `None` elsewhere.

| Value                     | Description                                                                    |
| :------------------------ | :------------------------------------------------------------------------------ |
| `"retrograde"`            | Moving backward, outside the stationary band.                                   |
| `"stationary"`            | Inside the stationary band (< 5% of mean motion, either direction), turn unknown. |
| `"stationary_retrograde"` | Inside the band with the speed still falling: the retrograde phase is opening.   |
| `"stationary_direct"`     | Inside the band with the speed rising: the retrograde phase is closing.          |
| `"slow"`                  | Below 80% of mean daily motion.                                                  |
| `"average"`               | Between 80% and 120% of mean daily motion.                                       |
| `"fast"`                  | Above 120% of mean daily motion.                                                 |

The band brackets zero on both sides and is tested before the sign of the speed,
so a body creeping backwards at a hundredth of its mean motion reports a station
rather than a plain `"retrograde"`. The two stations are read differently and the
sign of the speed cannot separate them — both are approached from one side of
zero and left on the other — so they are told apart by the trend: a second speed
sample a day later, falling or rising through the band. Without a usable second
sample the generic `"stationary"` stands, which is an absence of a claim rather
than a guess.

> **Downstream matching.** `"stationary_retrograde"` and `"stationary_direct"`
> are new values on this literal. Code that matches `motion_state` exhaustively —
> a `match` statement, a dict keyed by every value, a TypeScript union mirrored
> from the schema — must be extended before it sees a chart cast at a station.

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
`"Chiron"`, `"Mean_Lilith"`, `"True_Lilith"`, `"Interpolated_Lilith"`, `"Mean_Priapus"`, `"True_Priapus"`, `"Earth"`, `"Pholus"`, `"Vertex"`, `"Anti_Vertex"`, `"Interpolated_Perigee"`, `"White_Moon"`

**Uranian / Hamburg School:**
`"Cupido"`, `"Hades"`, `"Zeus"`, `"Kronos"`, `"Apollon"`, `"Admetos"`, `"Vulkanus"`, `"Poseidon"`

**Asteroids:**
`"Ceres"`, `"Pallas"`, `"Juno"`, `"Vesta"`

**Trans-Neptunian Objects (TNOs):**
`"Eris"`, `"Sedna"`, `"Haumea"`, `"Makemake"`, `"Ixion"`, `"Orcus"`, `"Quaoar"`

**Fixed Stars:**
`"Regulus"`, `"Spica"`, `"Aldebaran"`, `"Antares"`, `"Sirius"`, `"Fomalhaut"`, `"Algol"`, `"Betelgeuse"`, `"Canopus"`, `"Procyon"`, `"Arcturus"`, `"Pollux"`, `"Deneb"`, `"Altair"`, `"Rigel"`, `"Achernar"`, `"Capella"`, `"Vega"`, `"Alcyone"`, `"Alphecca"`, `"Algorab"`, `"Deneb_Algedi"`, `"Alkaid"`

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
| `"Progression"`       | A secondary progression chart overlaid on the natal chart. |

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
| `"parallel"`       | —       | Declination aspect (v6): same declination, same side of the equator. |
| `"contra-parallel"`| —       | Declination aspect (v6): same declination, opposite sides of the equator. |

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

48 modes total: 47 named + USER for custom ayanamsa definitions.

**Classic modes (pre-v5.12):**

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

**New in v5.12:**

| Value                       | Category           | Description                                          |
| :-------------------------- | :----------------- | :--------------------------------------------------- |
| `"ARYABHATA"`               | Indian/Vedic       | Aryabhata ayanamsa.                                  |
| `"ARYABHATA_522"`           | Indian/Vedic       | Aryabhata (522 CE epoch).                            |
| `"ARYABHATA_MSUN"`          | Indian/Vedic       | Aryabhata (mean Sun).                                |
| `"SURYASIDDHANTA"`          | Indian/Vedic       | Suryasiddhanta ayanamsa.                             |
| `"SURYASIDDHANTA_MSUN"`     | Indian/Vedic       | Suryasiddhanta (mean Sun).                           |
| `"SS_CITRA"`                | Indian/Vedic       | Suryasiddhanta (Citra/Spica reference).              |
| `"SS_REVATI"`               | Indian/Vedic       | Suryasiddhanta (Revati/zeta Piscium reference).      |
| `"TRUE_CITRA"`              | True star-based    | True Citra (Spica at 0° Libra).                      |
| `"TRUE_MULA"`               | True star-based    | True Mula (lambda Scorpii at 0° Sagittarius).        |
| `"TRUE_PUSHYA"`             | True star-based    | True Pushya (delta Cancri reference).                |
| `"TRUE_REVATI"`             | True star-based    | True Revati (zeta Piscium at 0° Aries).              |
| `"TRUE_SHEORAN"`            | True star-based    | True Sheoran ayanamsa.                               |
| `"LAHIRI_1940"`             | Lahiri variants    | Lahiri (1940 epoch).                                 |
| `"LAHIRI_ICRC"`             | Lahiri variants    | Lahiri (ICRC standard).                              |
| `"LAHIRI_VP285"`            | Lahiri variants    | Lahiri (VP285 variant).                              |
| `"KRISHNAMURTI_VP291"`      | Lahiri variants    | Krishnamurti (VP291 variant).                        |
| `"GALCENT_0SAG"`            | Galactic alignment | Galactic Center at 0° Sagittarius.                   |
| `"GALCENT_COCHRANE"`        | Galactic alignment | Galactic Center (Cochrane).                          |
| `"GALCENT_MULA_WILHELM"`    | Galactic alignment | Galactic Center (Mula/Wilhelm).                      |
| `"GALCENT_RGILBRAND"`       | Galactic alignment | Galactic Center (Rgilbrand).                         |
| `"GALEQU_FIORENZA"`         | Galactic alignment | Galactic Equator (Fiorenza).                         |
| `"GALEQU_IAU1958"`          | Galactic alignment | Galactic Equator (IAU 1958).                         |
| `"GALEQU_MULA"`             | Galactic alignment | Galactic Equator (Mula).                             |
| `"GALEQU_TRUE"`             | Galactic alignment | Galactic Equator (true).                             |
| `"GALALIGN_MARDYKS"`        | Galactic alignment | Galactic alignment (Mardyks).                        |
| `"BABYL_BRITTON"`           | Babylonian         | Babylonian (Britton).                                |
| `"VALENS_MOON"`             | Historical         | Vettius Valens Moon ayanamsa.                        |
| `"USER"`                    | User-defined       | Custom ayanamsa. Requires `custom_ayanamsa_t0` (Julian Day epoch) and `custom_ayanamsa_ayan_t0` (degrees at epoch). |

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
| `"Selenocentric"`       | Moon-centered.                                                                              |
| `"Mercurycentric"`      | Mercury-centered.                                                                          |
| `"Venuscentric"`        | Venus-centered.                                                                            |
| `"Marscentric"`         | Mars-centered.                                                                             |
| `"Jupitercentric"`      | Jupiter-centered.                                                                          |
| `"Saturncentric"`       | Saturn-centered.                                                                           |
| `"Barycentric"`         | Centered on the Solar System barycenter.                                                   |

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

### `SolarPhase`

How near the Sun a body is, named as a condition of visibility. Set on every `PlanetaryPhenomenaModel`.

| Value               | Meaning                                                  |
| :------------------ | :------------------------------------------------------- |
| `"cazimi"`          | In the heart of the Sun; the narrowest of the four.       |
| `"combust"`         | Burnt — close enough that the body cannot be seen at all. |
| `"under_the_beams"` | Within the Sun's rays; not yet out of the twilight.       |
| `"free"`            | Far enough from the Sun to be seen in a dark sky.         |

The three cut-offs that separate them are conventions, not constants of nature, and the schools disagree on all three. They live in `SolarPhaseThresholdsModel` (`cazimi_deg` 0.2833, `combust_deg` 8.5, `under_beams_deg` 17.0), which every phenomena collection echoes back and any caller may replace. The quantity compared is the true angular separation from the Sun (latitude included), not the difference in ecliptic longitude.

---

### `ApsisKind`

Which body the apsides of an orbit are measured against. Set on every `PlanetaryNodeModel`.

| Value             | Meaning                                        |
| :---------------- | :--------------------------------------------- |
| `"heliocentric"`  | Apsides about the Sun — every planet.           |
| `"geocentric"`    | Apsides about the Earth — the Moon alone.       |

The generic `periapsis`/`apoapsis` fields are correct under either reading; this literal says which one is in force. The older `perihelion`/`aphelion` name the Sun and are deprecated for that reason.

---

### `KerykeionChartTheme`

Available visual themes for chart rendering.

| Value                  | Description                                         |
| :--------------------- | :-------------------------------------------------- |
| `"classic"`            | Traditional white background, standard colors.      |
| `"dark"`               | Modern dark mode for reduced eye strain.            |
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

| Value                   | Description                                                              |
| :---------------------- | :--------------------------------------------------------------------- |
| `"Solar"`               | Sun returns to natal position; annual birthday chart.                  |
| `"Lunar"`               | Moon returns to natal position; monthly cycle chart.                   |
| `"Heliocentric"`        | A planet returns to its natal heliocentric longitude (not Sun/Moon).   |
| `"Lunar_Node_Crossing"` | The Moon crosses its own node (ecliptic latitude = 0).                 |

---

### `CompositeChartType`

Types of composite charts.

| Value        | Description                                       |
| :----------- | :------------------------------------------------ |
| `"Midpoint"` | Chart created from midpoints of two natal charts. |
| `"Davison"`  | Chart cast for the midpoint in time and space between two births. |

---

### `PointType`

Distinguishes between celestial bodies, house cusps, and midpoints.

| Value                 | Description                           |
| :-------------------- | :------------------------------------ |
| `"AstrologicalPoint"` | Planets, asteroids, angles, etc.      |
| `"House"`             | House cusps (1st through 12th house). |
| `"Midpoint"`          | Midpoint between two points (see `MidpointFactory`). |

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

Defines all the string labels used in chart generation and reports. Planet/point names are accessed via the nested `celestial_points` field (`KerykeionLanguageCelestialPointModel`), not directly on the model.

-   `celestial_points`: `KerykeionLanguageCelestialPointModel` — localized names for Sun, Moon, Mercury, etc.
-   `fire`, `earth`, `air`, `water` (Element names, lowercase keys)
-   Additional layout/formatting strings used in chart rendering.

---

## Exceptions (`exceptions`)

Import from: `kerykeion.schemas.exceptions`

### `KerykeionException`

The base exception class for all library-specific errors.

```python
from kerykeion.schemas import KerykeionException
from kerykeion import AstrologicalSubjectFactory

try:
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Example", 1990, 1, 1, 12, 0,
        city="UnknownCity", nation="XX",
        online=True
    )
except KerykeionException as e:
    print(f"Error calculating chart: {e}")
```

## Internal Schemas (`chart_template_model`)

These models are used internally for SVG generation but exposed for advanced customization.

### `ChartTemplateModel`

Variables passed to the Jinja2 template for rendering the SVG.

| Field                                  | Type    | Description                                            |
| :------------------------------------- | :------ | :----------------------------------------------------- |
| `viewbox`                              | `str`   | SVG viewBox attribute value.                           |
| `chart_width`, `chart_height`          | `float` | Dimensions of the chart in pixels.                     |
| `stringTitle`                          | `str`   | Chart title string.                                    |
| `paper_color_0`                        | `str`   | Font color.                                            |
| `background_color`                     | `str`   | Dynamic background color (theme color or transparent). |
| `planets_color_0` ... `planets_color_61` | `str` | Per-point colors (index 0 = Sun, 1 = Moon, ...).       |
| `zodiac_color_0` ... `zodiac_color_11` | `str`   | Per-sign colors (index 0 = Aries).                     |
| `orb_color_0` ... `orb_color_180`      | `str`   | Aspect colors keyed by aspect degrees.                 |
| `makeZodiac`, `makeHouses`, `makePlanets`, `makeAspects` | `str` | SVG markup fragments for each chart layer. |
| `makeLunarPhase`                       | `str`   | SVG markup for the lunar phase.                        |

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

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
