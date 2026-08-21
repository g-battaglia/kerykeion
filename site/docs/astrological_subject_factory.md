---
title: 'Astrological Subject Factory'
description: 'Master the creation of astrological subjects in Kerykeion. Detailed guide on birth data, zodiac types, house systems, and coordinate perspectives.'
category: 'Core'
tags: ['docs', 'subjects', 'core', 'astrology', 'kerykeion']
order: 2
---

# Astrological Subject Factory

The `AstrologicalSubjectFactory` is the central mechanism in Kerykeion for creating `AstrologicalSubjectModel` instances. It handles the complex astronomical calculations required to generate a chart, supporting widely used zodiacs, house systems, and coordinate perspectives.

## Key Features

- **Precision**: Uses libephemeris by default. A fresh install bundles DE440s
  coverage for 1849–2150; wider medium/extended data tiers (including the full
  DE441 range) must be downloaded separately. An optional Swiss Ephemeris
  (`pyswisseph`) backend is also available.
- **Flexibility**: Supports Tropical/Sidereal zodiacs, multiple House systems (Placidus, Whole Sign, etc.), and various coordinate (Geocentric/Heliocentric) perspectives.
- **Optimization**: The `active_points` argument allows you to calculate only what you need, saving resources.
- **Online/Offline**: Can resolve locations automatically via GeoNames (Online) or accept raw coordinates (Offline).

## Factory Methods

### 1. `from_birth_data` (Primary)

Creates a subject from standard civil birth details.

```python
from kerykeion import AstrologicalSubjectFactory

# Online mode (requires GeoNames username)
subject = AstrologicalSubjectFactory.from_birth_data(
    name="John Doe",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    city="London", nation="GB",
    geonames_username="your_username",
    zodiac_type="Tropical",
    houses_system_identifier="P"  # Placidus
)

print(f"Sun: {subject.sun.sign} {subject.sun.abs_pos:.2f}°")
print(f"Ascendant: {subject.ascendant.sign} {subject.ascendant.abs_pos:.2f}°")
```

**Parameters:**

| Parameter                  | Type                     | Default         | Description                                                            |
| :------------------------- | :----------------------- | :-------------- | :--------------------------------------------------------------------- |
| `name`                     | `str`                    | `"Now"`         | Name or identifier for the subject.                                    |
| `year`, `month`, `day`     | `Optional[int]`          | `None`          | Date components. Defaults to current date if omitted.                  |
| `hour`, `minute`           | `Optional[int]`          | `None`          | Time components. Defaults to current time if omitted.                  |
| `seconds`                  | `int`                    | `0`             | Seconds component of the time.                                         |
| `city`                     | `Optional[str]`          | `None`          | City name (used with `online=True`).                                   |
| `nation`                   | `Optional[str]`          | `None`          | ISO Country code (e.g., "GB").                                         |
| `lng`, `lat`               | `Optional[float]`        | `None`          | Coordinates (used with `online=False` or as override).                 |
| `tz_str`                   | `Optional[str]`          | `None`          | Timezone ID (e.g., "Europe/London"). Required if `online=False`.       |
| `geonames_username`        | `Optional[str]`          | `None`          | GeoNames username (required for `online=True`). Can also be set via `KERYKEION_GEONAMES_USERNAME` env var. |
| `online`                   | `bool`                   | `True`          | Whether to fetch location/timezone data from GeoNames API.             |
| `zodiac_type`              | `ZodiacType`             | `"Tropical"`    | "Tropical" or "Sidereal".                                              |
| `sidereal_mode`            | `Optional[SiderealMode]` | `None`          | Ayanamsha mode (e.g., "LAHIRI"). Required if `zodiac_type="Sidereal"`. |
| `houses_system_identifier` | `HousesSystemIdentifier` | `"P"`           | House system code (e.g., "P" for Placidus, "W" for Whole Sign).        |
| `perspective_type`         | `PerspectiveType`        | `"Apparent Geocentric"` | 11 options including Geocentric, Heliocentric, Topocentric, Barycentric, and Planetocentric variants. |
| `active_points`            | `Optional[List[str]]`    | `None`          | List of points to calculate. If `None`, uses `DEFAULT_ACTIVE_POINTS` (14 points).  |
| `is_dst`                   | `Optional[bool]`         | `None`          | Which UTC offset to take when a transition makes the wall time non-unique: `True` = the larger, `False` = the smaller, `None` = raise (see [FAQ](/content/docs/faq)).              |
| `cache_expire_after_days`  | `int`                    | `30`            | Days to cache online location lookups.                                              |
| `calculate_lunar_phase`    | `bool`                   | `True`          | Whether to calculate lunar phase details.                                           |
| `altitude`                 | `Optional[float]`        | `None`          | Altitude in meters (used with Topocentric perspective).                              |
| `suppress_geonames_warning`| `bool`                   | `False`         | Suppress the warning about using the default shared GeoNames username. Keyword-only.|
| `custom_ayanamsa_t0`      | `Optional[float]`        | `None`          | Reference epoch (Julian Day) for USER sidereal mode.                                |
| `custom_ayanamsa_ayan_t0` | `Optional[float]`        | `None`          | Ayanamsa offset in degrees at the reference epoch. Required with USER.              |
| `calculate_dignities`      | `bool`                   | `False`         | Compute essential dignity scores for each planet.                                    |
| `calculate_nakshatra`      | `bool`                   | `False`         | Compute Vedic nakshatra, pada, and dasha lord for each point.                       |
| `calculate_gauquelin`      | `bool`                   | `False`         | Compute Gauquelin sector (1-36) for each point.                                     |
| `calculate_nutation`       | `bool`                   | `False`         | Compute nutation in longitude and obliquity.                                        |
| `calculate_local_space`    | `bool`                   | `False`         | Compute azimuth and altitude for each point.                                        |
| `active_fixed_stars`       | `Optional[List[str]]`    | `None`          | Fixed star names to compute (e.g., `["Regulus"]`). Access via `find_fixed_star()`.  |

### 2. `from_iso_utc_time`

Creates a subject from a UTC ISO 8601 timestamp, useful for event charts or standardized data.

```python
subject = AstrologicalSubjectFactory.from_iso_utc_time(
    name="Event Chart",
    iso_utc_time="2023-06-21T12:00:00Z",
    city="New York", nation="US",
    geonames_username="your_username"
)
```

**Parameters:**

| Parameter                  | Type                     | Default                 | Description                                                            |
| :------------------------- | :----------------------- | :---------------------- | :--------------------------------------------------------------------- |
| `name`                     | `str`                    | **Required**            | Name or identifier for the subject.                                    |
| `iso_utc_time`             | `str`                    | **Required**            | UTC timestamp in ISO 8601 format (e.g., `"2023-06-21T12:00:00Z"`).    |
| `city`                     | `Optional[str]`          | `None`                  | City used for online lookup; omitted locations fall back to Greenwich. |
| `nation`                   | `Optional[str]`          | `None`                  | ISO country code used for online lookup; omitted locations fall back to `"GB"`. |
| `tz_str`                   | `str`                    | `"Etc/GMT"`             | Timezone string.                                                       |
| `lng`, `lat`               | `Optional[float]`        | `None`                  | Explicit coordinates override lookup values. Missing values are looked up online or fall back to `0.0`, `51.5074` offline. |
| `online`                   | `bool`                   | `True`                  | Whether to resolve location via GeoNames API.                          |
| `zodiac_type`              | `ZodiacType`             | `"Tropical"`            | `"Tropical"` or `"Sidereal"`.                                          |
| `sidereal_mode`            | `Optional[SiderealMode]` | `None`                  | Ayanamsha mode. Required if `zodiac_type="Sidereal"`.                  |
| `houses_system_identifier` | `HousesSystemIdentifier` | `"P"`                   | House system code.                                                     |
| `perspective_type`         | `PerspectiveType`        | `"Apparent Geocentric"` | Calculation perspective.                                               |
| `active_points`            | `Optional[List[str]]`    | `None`                  | Points to calculate.                                                   |
| `suppress_geonames_warning`| `bool`                   | `False`                 | Suppress the default GeoNames username warning.                        |
| `altitude`                 | `Optional[float]`        | `None`                  | Altitude in meters above sea level.                                    |
| `calculate_lunar_phase`    | `bool`                   | `True`                  | Whether to calculate lunar phase data.                                 |
| `custom_ayanamsa_t0`       | `Optional[float]`        | `None`                  | Julian Day epoch for custom ayanamsa (requires `sidereal_mode="USER"`). |
| `custom_ayanamsa_ayan_t0`  | `Optional[float]`        | `None`                  | Ayanamsa degrees at epoch (requires `sidereal_mode="USER"`).           |
| `geonames_username`        | `str`                    | `DEFAULT_GEONAMES_USERNAME` | GeoNames API username.                                              |
| `calculate_dignities`      | `bool`                   | `False`                 | Calculate essential dignities for each point.                          |
| `calculate_nakshatra`      | `bool`                   | `False`                 | Calculate Vedic Nakshatra/Pada/Dasha lord.                             |
| `calculate_gauquelin`      | `bool`                   | `False`                 | Calculate Gauquelin 36-sector positions.                               |
| `calculate_nutation`       | `bool`                   | `False`                 | Include true/mean obliquity and nutation data.                         |
| `calculate_local_space`    | `bool`                   | `False`                 | Calculate azimuth and altitude for each point.                         |
| `active_fixed_stars`       | `Optional[List[str]]`    | `None`                  | Fixed stars to compute into `subject.fixed_stars`. Default `None` computes none; `DEFAULT_FIXED_STARS` is an opt-in 23-star preset. |

### 3. `from_current_time`

Creates a subject for the current moment ("Now"), useful for Horary astrology or transits. Uses the system clock -- does **not** accept `year`/`month`/`day`/`hour`/`minute` parameters.

```python
now_chart = AstrologicalSubjectFactory.from_current_time(
    name="Current Transits",
    city="Tokyo", nation="JP",
    geonames_username="your_username"
)
```

**Parameters:**

| Parameter                  | Type                     | Default                 | Description                                                            |
| :------------------------- | :----------------------- | :---------------------- | :--------------------------------------------------------------------- |
| `name`                     | `str`                    | `"Now"`                 | Name or identifier.                                                    |
| `city`                     | `Optional[str]`          | `None`                  | City name (used with `online=True`).                                   |
| `nation`                   | `Optional[str]`          | `None`                  | ISO Country code.                                                      |
| `lng`, `lat`               | `Optional[float]`        | `None`                  | Coordinates (used with `online=False`).                                |
| `tz_str`                   | `Optional[str]`          | `None`                  | Timezone string. Required if `online=False`.                           |
| `online`                   | `bool`                   | `True`                  | Whether to resolve location via GeoNames API.                          |
| `zodiac_type`              | `ZodiacType`             | `"Tropical"`            | `"Tropical"` or `"Sidereal"`.                                          |
| `sidereal_mode`            | `Optional[SiderealMode]` | `None`                  | Ayanamsha mode. Required if `zodiac_type="Sidereal"`.                  |
| `houses_system_identifier` | `HousesSystemIdentifier` | `"P"`                   | House system code.                                                     |
| `perspective_type`         | `PerspectiveType`        | `"Apparent Geocentric"` | Calculation perspective.                                               |
| `active_points`            | `Optional[List[str]]`    | `None`                  | Points to calculate.                                                   |
| `suppress_geonames_warning`| `bool`                   | `False`                 | Suppress the default GeoNames username warning.                        |
| `geonames_username`        | `Optional[str]`          | `None`                  | GeoNames API username.                                                 |
| `calculate_lunar_phase`    | `bool`                   | `True`                  | Whether to calculate lunar phase data.                                 |
| `custom_ayanamsa_t0`       | `Optional[float]`        | `None`                  | Julian Day epoch for custom ayanamsa (requires `sidereal_mode="USER"`). |
| `custom_ayanamsa_ayan_t0`  | `Optional[float]`        | `None`                  | Ayanamsa degrees at epoch (requires `sidereal_mode="USER"`).           |
| `altitude`                 | `Optional[float]`        | `None`                  | Observer altitude in meters (used by Topocentric calculations).        |
| `active_fixed_stars`       | `Optional[List[str]]`    | `None`                  | Fixed-star catalog names to compute into `subject.fixed_stars`.         |
| `calculate_dignities`      | `bool`                   | `False`                 | Calculate essential dignities for each point.                          |
| `calculate_nakshatra`      | `bool`                   | `False`                 | Calculate Vedic Nakshatra/Pada/Dasha lord data.                        |
| `calculate_gauquelin`      | `bool`                   | `False`                 | Calculate Gauquelin 36-sector positions.                               |
| `calculate_nutation`       | `bool`                   | `False`                 | Include true/mean obliquity and nutation data.                         |
| `calculate_local_space`    | `bool`                   | `False`                 | Calculate azimuth and altitude for each point.                         |

## Understanding Position Fields

Every `KerykeionPointModel` (planet, angle, etc.) has two position fields:

| Field      | Range     | Description                                                |
| :--------- | :-------- | :--------------------------------------------------------- |
| `position` | 0° - 30°  | Degree within the sign (e.g., 22.54° of Cancer).           |
| `abs_pos`  | 0° - 360° | Absolute ecliptic longitude (e.g., 112.54° on the zodiac). |

Use `position` for display purposes and `abs_pos` for calculations (aspect detection, midpoints, etc.).

## Configuration Options

### House Systems (`houses_system_identifier`)

| Identifier | System        | Description                                                               |
| :--------- | :------------ | :------------------------------------------------------------------------ |
| **"P"**    | Placidus      | **Default**. Time-based system, standard in modern Western astrology.     |
| **"K"**    | Koch          | Time-based, often used in German schools.                                 |
| **"W"**    | Whole Sign    | Each house is exactly 30°, matching signs. Standard in Hellenistic/Vedic. |
| **"R"**    | Regiomontanus | Standard for Horary astrology.                                            |
| **"A"**    | Equal         | Equal 30° houses starting from Ascendant.                                 |
| **"M"**    | Morinus       | Space-based system.                                                       |

### Zodiac Types

- **Tropical** (Default): Fixed to seasons (0° Aries = Vernal Equinox). Standard in Western astrology.
- **Sidereal**: Fixed to constellations. Standard in Vedic astrology. Requires `sidereal_mode`.
  - 48 modes total: 47 named + `USER` for custom ayanamsa definitions.
  - _Common Modes_: `LAHIRI` (most common), `FAGAN_BRADLEY`, `RAMAN`.
  - _USER mode_: Requires `custom_ayanamsa_t0` (Julian Day epoch) and `custom_ayanamsa_ayan_t0` (degrees at epoch).
  - The computed ayanamsa offset is available via `subject.ayanamsa_value` (degrees, `None` for tropical).

### Perspectives

- **Apparent Geocentric** (Default): Earth-centered, includes light-time correction.
- **True Geocentric**: Earth-centered, geometric position only.
- **Heliocentric**: Sun-centered. Earth becomes a planet.
- **Topocentric**: Observer-centered (surface of Earth), accounts for parallax.
- **Barycentric**: Solar system barycenter.
- **Selenocentric**: Moon-centered.
- **Mercurycentric**, **Venuscentric**, **Marscentric**, **Jupitercentric**, **Saturncentric**: Planet-centered.

## V6 Optional Enrichments

These opt-in features add extra data to the subject model. All are disabled by default and have zero overhead when not enabled.

### Essential Dignities (`calculate_dignities=True`)

Adds `essential_dignity` field to each point (Domicile, Exaltation, Detriment, Fall, Term, Peregrine).

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False,
    calculate_dignities=True
)
print(subject.sun.essential_dignity)  # e.g. "Domicile"
```

### Vedic Nakshatras (`calculate_nakshatra=True`)

Adds `nakshatra`, `nakshatra_pada`, and `nakshatra_lord` fields. Best used with `zodiac_type="Sidereal"`.

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London", online=False,
    zodiac_type="Sidereal", sidereal_mode="LAHIRI",
    calculate_nakshatra=True
)
print(f"{subject.moon.nakshatra}, pada {subject.moon.nakshatra_pada}")
```

### Gauquelin Sectors (`calculate_gauquelin=True`)

Adds `gauquelin_sector` field (1-36) to each point, plus `gauquelin_sector_cusps` on the subject.

### Nutation (`calculate_nutation=True`)

Adds `subject.nutation` with `true_obliquity`, `mean_obliquity`, `nutation_in_longitude`, and `nutation_in_obliquity`.

### Local Space (`calculate_local_space=True`)

Adds `azimuth` and `altitude_above_horizon` fields for each point. Useful for astro-locality work.

### Motion State

Always computed for the ten planets (Sun through Pluto) in Earth-centred perspectives. Access via `subject.sun.motion_state`. Returns a `MotionState` literal: `"stationary_retrograde"`, `"stationary_direct"` or `"stationary"` (inside the band of < 5% of mean motion, either direction), `"retrograde"` (backward, outside that band), `"slow"` (< 80%), `"average"` (80-120%), or `"fast"` (> 120%). `None` for nodes, asteroids, fixed stars, and non-geocentric perspectives.

The stationary band brackets zero speed and is tested before the sign, so a
planet edging backwards at a hundredth of its mean motion is reported as a
station instead of a plain retrograde. Which station it is comes from the trend
rather than the sign: the factory samples the speed again a day later, and a
speed falling through the band opens the retrograde phase
(`"stationary_retrograde"`) while a speed rising through it closes the phase
(`"stationary_direct"`). The extra sample is only ever spent on a body already
inside the band; where it is unavailable the generic `"stationary"` stands.

```python
from kerykeion import AstrologicalSubjectFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "Mercury Station", 1990, 8, 25, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False, suppress_geonames_warning=True,
)
print(subject.mercury.motion_state)  # stationary_retrograde
print(subject.mercury.speed)         # 0.0123... — still forward, already turning
```

For the instants of the stations themselves rather than the state of one chart, see [Retrograde Stations](/content/docs/retrograde_station_factory), which reports the same two events as `SR` and `SD`.

### Declination & Out-of-Bounds

Always computed. Access via `subject.sun.declination` and `subject.sun.is_out_of_bounds`. A planet is out-of-bounds when its declination exceeds the Sun's maximum (~23.44°).

### Lilith Variants & Priapus

Enable via `active_points`: `"Mean_Lilith"`, `"True_Lilith"`, `"Interpolated_Lilith"`, `"Mean_Priapus"`, `"True_Priapus"`. None of these are in `DEFAULT_ACTIVE_POINTS` — every Lilith/Priapus variant is opt-in.

## Performance & Optimization

Subject creation involves complex calculations. For high-performance applications (e.g., scanning thousands of dates), limit the `active_points` to only what you need.

```python
# Minimal calculation (approx. 3-4x faster than full)
fast_chart = AstrologicalSubjectFactory.from_birth_data(
    name="Research Point",
    year=2000, month=1, day=1,
    hour=12, minute=0,
    city="London", nation="GB",
    geonames_username="your_username",
    # Only calculate luminaries and angles
    active_points=["Sun", "Moon", "Ascendant", "Medium_Coeli"]
)
```

### Internal Types

These `@dataclass` structures are used internally but are exposed for reference.

#### `ChartConfiguration`

Dataclass holding chart calculation settings.
Fields: `zodiac_type`, `sidereal_mode`, `houses_system_identifier`, `perspective_type`, `custom_ayanamsa_t0`, `custom_ayanamsa_ayan_t0`, `calculate_dignities`, `calculate_nakshatra`, `calculate_gauquelin`, `calculate_nutation`, `calculate_local_space`, `active_fixed_stars`.

#### `LocationData`

Dataclass carrying raw location information.
Fields: `city`, `nation`, `lng`, `lat`, `tz_str`, `altitude`, `city_data`.

#### `ephemeris_context`

Helper context manager for thread-safe ephemeris calculations.
**Not intended for public use.**

**Memory Usage**:

- Full Chart: ~50KB
- Minimal Chart: ~15KB

## Thread Safety Note

Kerykeion serializes all ephemeris access internally through a process-wide lock, so `AstrologicalSubjectFactory` is safe to call from multiple threads (e.g., Gunicorn/Uvicorn workers). The lock does mean concurrent calculations within one process run sequentially; for CPU-bound throughput, prefer multiple worker processes. Kerykeion result objects are self-contained and can be shared freely once created.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
