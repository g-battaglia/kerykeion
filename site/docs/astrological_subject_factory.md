---
title: 'Astrological Subject Factory'
category: 'Core'
tags: ['docs', 'subjects', 'core', 'astrology', 'kerykeion']
order: 2
---

# Astrological Subject Factory

The `AstrologicalSubjectFactory` is the central mechanism in Kerykeion for creating `AstrologicalSubject` instances. It handles the complex astronomical calculations required to generate a chart, supporting widely used zodiacs, house systems, and coordinate perspectives.

## Key Features

-   **Precision**: Uses the Swiss Ephemeris (via `pyswisseph`) for high-accuracy calculations.
-   **Flexibility**: Supports Tropical/Sidereal zodiacs, multiple House systems (Placidus, Whole Sign, etc.), and various coordinate (Geocentric/Heliocentric) perspectives.
-   **Optimization**: The `active_points` argument allows you to calculate only what you need, saving resources.
-   **Online/Offline**: Can resolve locations automatically via GeoNames (Online) or accept raw coordinates (Offline).

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

-   `name` (str): Name of the subject.
-   `year`, `month`, `day`, `hour`, `minute` (int): Birth time components.
-   `city`, `nation` (str): Location for online lookup.
-   `lng`, `lat` (float): Coordinates for offline mode (if `city`/`nation` omitted or `online=False`).
-   `tz_str` (str): Timezone string (e.g., "Europe/London") for offline mode.
-   `zodiac_type` (str): "Tropical" (default) or "Sidereal".
-   `sidereal_mode` (str): Ayanamsha mode (e.g., "LAHIRI") if `zodiac_type="Sidereal"`.
-   `houses_system_identifier` (str): House system code (default "P").
-   `perspective_type` (str): "Apparent Geocentric" (default), "True Geocentric", "Heliocentric", or "Topocentric".
-   `active_points` (list[str]): List of points to calculate (defaults to full set).

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

### 3. `from_current_time`

Creates a subject for the current moment ("Now"), useful for Horary astrology or transits.

```python
now_chart = AstrologicalSubjectFactory.from_current_time(
    name="Current Transits",
    city="Tokyo", nation="JP",
    geonames_username="your_username"
)
```

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

-   **Tropical** (Default): Fixed to seasons (0° Aries = Vernal Equinox). Standard in Western astrology.
-   **Sidereal**: Fixed to constellations. Standard in Vedic astrology. Requires `sidereal_mode`.
    -   _Common Modes_: "LAHIRI" (most common), "FAGAN_BRADLEY", "RAMAN".

### Perspectives

-   **Apparent Geocentric** (Default): Earth-centered, includes light-time correction.
-   **True Geocentric**: Earth-centered, geometric position only.
-   **Heliocentric**: Sun-centered. Earth becomes a planet.
-   **Topocentric**: Observer-centered (surface of Earth), accounts for parallax.

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

**Memory Usage**:

-   Full Chart: ~50KB
-   Minimal Chart: ~15KB

## Thread Safety Note

The underlying Swiss Ephemeris library is **not thread-safe** by default. If using Kerykeion in a multi-threaded web server (like Gunicorn/Uvicorn workers), ensure `AstrologicalSubjectFactory` usage is process-isolated or appropriately locked if sharing state (though Kerykeion objects themselves are generally self-contained).
