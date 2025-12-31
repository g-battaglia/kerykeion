---
title: 'Planetary Return Factory'
category: 'Forecasting'
tags: ['docs', 'returns', 'forecasting', 'kerykeion']
order: 11
---

# Planetary Return Factory

The `PlanetaryReturnFactory` calculates the precise moment when a planet returns to its natal position (e.g., Solar Returns). It uses Swiss Ephemeris for high-precision timing.

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

## Supported Return Types

-   `"Solar"` (Sun) - Yearly forecast.
-   `"Lunar"` (Moon) - Monthly forecast.
-   `"Mercury"`, `"Venus"`, `"Mars"`, `"Jupiter"`, `"Saturn"`, `"Uranus"`, `"Neptune"`, `"Pluto"`
-   `"Chiron"`

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

## Relocation Astrology

Planetary returns are often calculated for the subject's **current location** rather than birth location. Simply pass the current residence coordinates/city to the `PlanetaryReturnFactory` constructor to generate a relocated return chart.
