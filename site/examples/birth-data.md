---
layout: ../../layouts/DocLayout.astro
title: 'Birth Data'
---

# Birth Data

Use `AstrologicalSubjectFactory` to create an `AstrologicalSubjectModel` from birth data. This model is the foundation for all calculations and chart rendering in Kerykeion v5.

## Creating a Subject (v5)

Create a subject offline by specifying longitude, latitude, and timezone, or enable online lookup with GeoNames credentials. The factory validates inputs and computes all celestial points and houses.

```python
from kerykeion import AstrologicalSubjectFactory

# Create an AstrologicalSubjectModel (offline)
subject = AstrologicalSubjectFactory.from_birth_data(
    "Kanye", 1977, 6, 8, 8, 45,
    lng=-84.38798,  # Longitude for Atlanta
    lat=33.7490,    # Latitude for Atlanta
    tz_str="America/New_York",
    online=False,
)

# Retrieve information about the Sun
print(subject.sun.model_dump_json())

# Retrieve information about the first house
print(subject.first_house.model_dump_json())

# Element of the Moon sign
print(subject.moon.element)
```

Key options include:
- `houses_system_identifier` (e.g., `"P"` Placidus, `"W"` Whole Sign)
- `zodiac_type` ("Tropical" or "Sidereal") and `sidereal_mode` (e.g., `"LAHIRI"`)
- `perspective_type` (e.g., `"Apparent Geocentric"`, `"Heliocentric"`)
- `geonames_username` and `online=True` for automatic lookup

For the complete reference, see the API docs: https://www.kerykeion.net/pydocs/kerykeion.html
