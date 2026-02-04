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

**Other Returns:**

- **Mercury Return** (~88 days): Communication and learning cycles
- **Venus Return** (~225 days): Relationship and value cycles
- **Mars Return** (~2 years): Action and energy cycles
- **Jupiter/Saturn Returns**: Major life transitions (every 12 and ~29 years respectively)

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

## Supported Return Types

- `"Solar"` (Sun) - Yearly forecast.
- `"Lunar"` (Moon) - Monthly forecast.
- `"Mercury"`, `"Venus"`, `"Mars"`, `"Jupiter"`, `"Saturn"`, `"Uranus"`, `"Neptune"`, `"Pluto"`
- `"Chiron"`

## Methods

### `next_return_from_date(...)`

Finds the next return starting search from a specific year/month/day.

```python
result = calculator.next_return_from_date(2025, 1, 1, return_type="Saturn")
```

### `next_return_from_iso_formatted_time(...)`

Finds the next return starting search from a precise ISO timestamp.

```python
result = calculator.next_return_from_iso_formatted_time("2024-06-15T12:00:00", "Lunar")
```

### `next_return_from_year(...)`

Finds the first return occurring in a given calendar year.

```python
result = calculator.next_return_from_year(2025, "Solar")
```

## Relocation Astrology

Planetary returns are often calculated for the subject's **current location** rather than birth location. Simply pass the current residence coordinates/city to the `PlanetaryReturnFactory` constructor to generate a relocated return chart.
