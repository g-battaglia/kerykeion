---
title: 'Astrological Subject Factory'
description: 'Master the creation of astrological subjects in Kerykeion. Detailed guide on birth data, zodiac types, house systems, and coordinate perspectives.'
category: 'Core'
tags: ['docs', 'subjects', 'core', 'astrology', 'kerykeion']
order: 2
---

# Astrological Subject Factory

The `AstrologicalSubjectFactory` is the central mechanism in Kerykeion for creating `AstrologicalSubject` instances. It handles the complex astronomical calculations required to generate a chart, supporting widely used zodiacs, house systems, and coordinate perspectives.

## Key Features

- **Precision**: Uses the Swiss Ephemeris (via `pyswisseph`) for high-accuracy calculations.
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
| `perspective_type`         | `PerspectiveType`        | `"Apparent Geocentric"` | `"Apparent Geocentric"`, `"True Geocentric"`, `"Heliocentric"`, or `"Topocentric"`. |
| `active_points`            | `Optional[List[str]]`    | `None`          | List of points to calculate. If `None`, uses `DEFAULT_ACTIVE_POINTS` (18 points).  |
| `is_dst`                   | `Optional[bool]`         | `None`          | Explicitly set DST for ambiguous times (see [FAQ](/content/docs/faq)).              |
| `cache_expire_after_days`  | `int`                    | `30`            | Days to cache online location lookups.                                              |
| `calculate_lunar_phase`    | `bool`                   | `True`          | Whether to calculate lunar phase details.                                           |
| `altitude`                 | `Optional[float]`        | `None`          | Altitude in meters (used with Topocentric perspective).                              |
| `suppress_geonames_warning`| `bool`                   | `False`         | Suppress the warning about using the default shared GeoNames username. Keyword-only.|
| `custom_ayanamsa_t0`      | `Optional[float]`        | `None`          | Reference epoch (Julian Day) for USER sidereal mode.                                |
| `custom_ayanamsa_ayan_t0` | `Optional[float]`        | `None`          | Ayanamsa offset in degrees at the reference epoch. Required with USER.              |

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
| `city`                     | `str`                    | `"Greenwich"`           | City name.                                                             |
| `nation`                   | `str`                    | `"GB"`                  | ISO Country code.                                                      |
| `tz_str`                   | `str`                    | `"Etc/GMT"`             | Timezone string.                                                       |
| `lng`, `lat`               | `float`                  | `0.0`, `51.5074`        | Coordinates (defaults to Greenwich).                                   |
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
| `geonames_username`        | `str`                    | `"century.boy"`         | GeoNames API username.                                                 |

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
| **"E"**    | Equal         | Equal 30° houses starting from Ascendant.                                 |
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
Fields: `zodiac_type`, `sidereal_mode`, `houses_system_identifier`, `perspective_type`, `custom_ayanamsa_t0`, `custom_ayanamsa_ayan_t0`.

#### `LocationData`

Dataclass carrying raw location information.
Fields: `city`, `nation`, `lng`, `lat`, `tz_str`, `altitude`, `city_data`.

#### `ephemeris_context`

Helper context manager for thread-safe Swisseph calculations.
**Not intended for public use.**

**Memory Usage**:

- Full Chart: ~50KB
- Minimal Chart: ~15KB

## Thread Safety Note

The underlying Swiss Ephemeris library is **not thread-safe** by default. If using Kerykeion in a multi-threaded web server (like Gunicorn/Uvicorn workers), ensure `AstrologicalSubjectFactory` usage is process-isolated or appropriately locked if sharing state (though Kerykeion objects themselves are generally self-contained).

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
