---
title: 'Planetary Return Factory'
description: 'Precisely calculate solar, lunar, and planetary returns with Kerykeion. High-precision timing for forecasting yearly and monthly astrological cycles.'
category: 'Forecasting'
tags: ['docs', 'returns', 'forecasting', 'kerykeion']
order: 11
---

# Planetary Return Factory

The `PlanetaryReturnFactory` calculates the precise moment when a planet returns to its natal position (e.g., Solar Returns). It uses Swiss Ephemeris for high-precision timing.

## What Are Planetary Returns?

A **Planetary Return** occurs when a transiting planet returns to the exact degree it occupied at birth. The return chart cast for that precise moment becomes a forecast for the cycle ahead:

**Solar Return (Birthday Chart):**

- Happens once per year on or near your birthday
- The Sun returns to its natal position (~365.25 days)
- Forecasts themes and events for the coming year
- Traditionally cast for your current location (relocated solar return)

**Lunar Return:**

- Happens approximately every 27-29 days
- The Moon returns to its natal position
- Forecasts the emotional climate for the coming month
- Useful for timing short-term events and emotional cycles

> Kerykeion currently supports **Solar** and **Lunar** returns. Other planetary return types (Mercury, Venus, Mars, Jupiter, Saturn) are not yet implemented.

## Usage

Calculating a return involves the **Natal Subject** and the **Return Location** (which can differ from birth location).

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

# 1. Create Natal Subject
natal_subject = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 6, 15, 12, 0, "London", "GB"
)

# 2. Initialize Calculator (with Return Location)
# Here we calculate the return for New York
return_factory = PlanetaryReturnFactory(
    natal_subject,
    city="New York",
    nation="US",
    online=True
)

# 3. specific Return (e.g., Solar Return for 2024)
solar_return = return_factory.next_return_from_date(
    year=2024,
    month=1,
    day=1, # Start searching from this date
    return_type="Solar"
)

print(f"Return Date: {solar_return.iso_formatted_local_datetime}")
print(f"Sun Position: {solar_return.sun.abs_pos:.2f}°")
```

**Expected Output:**

```text
Return Date: 2024-06-15T08:23:47
Sun Position: 84.32°
```

> **Note:** The Sun position matches Alice's natal Sun position exactly (within calculation precision).

### Custom Ayanamsa in Returns

When using `sidereal_mode="USER"` on the natal subject, pass the custom ayanamsa parameters to `PlanetaryReturnFactory` so the return chart uses the same ayanamsa:

```python
from kerykeion import AstrologicalSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    "Sidereal User", 1990, 6, 15, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    zodiac_type="Sidereal",
    sidereal_mode="USER",
    custom_ayanamsa_t0=2451545.0,
    custom_ayanamsa_ayan_t0=23.5,
)

return_factory = PlanetaryReturnFactory(
    natal,
    city="London", nation="GB",
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    custom_ayanamsa_t0=2451545.0,
    custom_ayanamsa_ayan_t0=23.5,
)

solar_return = return_factory.next_return_from_year(2024, "Solar")
print(f"Return ayanamsa: {solar_return.ayanamsa_value:.4f}°")
```

> Both `custom_ayanamsa_t0` and `custom_ayanamsa_ayan_t0` are required when the natal subject uses `sidereal_mode="USER"`. Omitting them raises a `KerykeionException`.

## Supported Return Types

- `"Solar"` (Sun) -- Yearly forecast.
- `"Lunar"` (Moon) -- Monthly forecast.

> **Note:** The `return_type` parameter is case-sensitive. Use exactly `"Solar"` or `"Lunar"`.

## Constructor Parameters

| Parameter                  | Type                     | Default     | Description                                                        |
| :------------------------- | :----------------------- | :---------- | :----------------------------------------------------------------- |
| `subject`                  | `AstrologicalSubjectModel` | **Required** | The natal subject whose return is being calculated.              |
| `city`                     | `Optional[str]`          | `None`      | City name for the return location.                                 |
| `nation`                   | `Optional[str]`          | `None`      | ISO country code for the return location.                          |
| `lng`                      | `Optional[float]`        | `None`      | Longitude of the return location.                                  |
| `lat`                      | `Optional[float]`        | `None`      | Latitude of the return location.                                   |
| `tz_str`                   | `Optional[str]`          | `None`      | Timezone string for the return location.                           |
| `online`                   | `bool`                   | `True`      | Whether to resolve location via GeoNames API.                      |
| `geonames_username`        | `Optional[str]`          | `None`      | GeoNames username for online mode.                                 |
| `cache_expire_after_days`  | `int`                    | `30`        | Days to cache online location lookups.                             |
| `altitude`                 | `Optional[float]`        | `None`      | Altitude in meters for the return location.                        |
| `custom_ayanamsa_t0`       | `Optional[float]`        | `None`      | Reference epoch (Julian Day) for USER sidereal mode.               |
| `custom_ayanamsa_ayan_t0`  | `Optional[float]`        | `None`      | Ayanamsa offset at epoch (required with USER sidereal mode).       |

## Methods

### `next_return_from_date(year, month, day, *, return_type)`

Finds the next return starting search from a specific year/month/day. This is the **primary method**.

```python
result = calculator.next_return_from_date(2025, 1, 1, return_type="Solar")
```

| Parameter     | Type         | Default     | Description                              |
| :------------ | :----------- | :---------- | :--------------------------------------- |
| `year`        | `int`        | **Required** | Year to start searching from.           |
| `month`       | `int`        | **Required** | Month to start searching from.          |
| `day`         | `int`        | `1`          | Day to start searching from.            |
| `return_type` | `ReturnType` | **Required** | `"Solar"` or `"Lunar"` (keyword-only).  |

### `next_return_from_iso_formatted_time(iso_formatted_time, return_type)`

Finds the next return starting search from a precise ISO timestamp.

```python
result = calculator.next_return_from_iso_formatted_time("2024-06-15T12:00:00", "Lunar")
```

### `next_return_from_year(year, return_type)` _(Deprecated)_

Finds the first return occurring in a given calendar year. **Deprecated** -- use `next_return_from_date` instead.

```python
result = calculator.next_return_from_year(2025, "Solar")  # Deprecated
result = calculator.next_return_from_date(2025, 1, 1, return_type="Solar")  # Preferred
```

## Relocation Astrology

Planetary returns are often calculated for the subject's **current location** rather than birth location. Simply pass the current residence coordinates/city to the `PlanetaryReturnFactory` constructor to generate a relocated return chart.

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
