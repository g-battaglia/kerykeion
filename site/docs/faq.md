---
title: 'Troubleshooting & FAQ'
description: 'Common issues, error messages, and solutions for Kerykeion'
category: 'Getting Started'
tags: ['docs', 'faq', 'troubleshooting', 'errors', 'help']
order: 3
---

# Troubleshooting & FAQ

This page covers common issues, error messages, and their solutions when using Kerykeion.

## Location & GeoNames Errors

### "You need to set the city if you want to use the online mode!"

**Cause:** Using `online=True` without providing a `city` parameter.

**Solution:** Either provide city/nation or switch to offline mode:

```python
# Option 1: Use online mode with city/nation
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    city="London", nation="GB",
    geonames_username="your_username",
    online=True
)

# Option 2: Use offline mode with coordinates (recommended)
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)
```

### "No data found for this city, try again!"

**Cause:** GeoNames API couldn't find the city, or network issues.

**Solutions:**
1. Check the city name spelling
2. Try a larger nearby city
3. Check your internet connection
4. Use offline mode with known coordinates

### GeoNames Rate Limiting

**Cause:** The default GeoNames username is shared and has a limit of 2,000 requests/hour across all users.

**Solution:** Register your own free account at [geonames.org](https://www.geonames.org/login):

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    city="London", nation="GB",
    geonames_username="your_personal_username",  # Your own username
    online=True
)
```

### Best Practice: Use Offline Mode

For production applications, use offline mode to avoid API dependencies:

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276,          # Longitude
    lat=51.5074,          # Latitude
    tz_str="Europe/London",  # Timezone string
    online=False          # No API calls
)
```

---

## Timezone & DST Errors

### "Ambiguous time error! The time falls during a DST transition..."

**Cause:** During the "fall back" DST transition, the same local time occurs twice (e.g., 1:30 AM happens twice on the first Sunday of November in the US).

**Solution:** Specify which occurrence you mean with `is_dst`:

```python
# For the first occurrence (during daylight saving time)
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 2023, 11, 5, 1, 30,  # Ambiguous time
    lng=-74.006, lat=40.7128, tz_str="America/New_York",
    online=False,
    is_dst=True  # First occurrence (summer time)
)

# For the second occurrence (after DST ends)
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 2023, 11, 5, 1, 30,
    lng=-74.006, lat=40.7128, tz_str="America/New_York",
    online=False,
    is_dst=False  # Second occurrence (standard time)
)
```

### "Non-existent time error! The time does not exist..."

**Cause:** During the "spring forward" DST transition, certain times are skipped (e.g., 2:30 AM doesn't exist on the second Sunday of March in the US).

**Solution:** Use a valid time before or after the transition:

```python
# Instead of 2:30 AM (which doesn't exist)
# Use either 1:30 AM or 3:30 AM
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 2023, 3, 12, 3, 30,  # Use 3:30 instead of 2:30
    lng=-74.006, lat=40.7128, tz_str="America/New_York",
    online=False
)
```

---

## Configuration Errors

### "You can't set a sidereal mode with a Tropical zodiac type!"

**Cause:** Setting `sidereal_mode` while using `zodiac_type="Tropical"`.

**Solution:** Either use Sidereal zodiac or remove the sidereal_mode:

```python
# Correct: Sidereal zodiac with sidereal mode
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    zodiac_type="Sidereal",
    sidereal_mode="LAHIRI"
)

# Correct: Tropical zodiac (no sidereal_mode)
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    zodiac_type="Tropical"  # No sidereal_mode
)
```

### "Both subjects must have the same zodiac type/house system/perspective"

**Cause:** Creating a composite chart with subjects that have different configurations.

**Solution:** Ensure both subjects have identical settings:

```python
# Both subjects must match
subject1 = AstrologicalSubjectFactory.from_birth_data(
    "Alice", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False,
    zodiac_type="Tropical",
    houses_system_identifier="P"
)

subject2 = AstrologicalSubjectFactory.from_birth_data(
    "Bob", 1992, 6, 15, 8, 30,
    lng=-74.006, lat=40.7128, tz_str="America/New_York",
    online=False,
    zodiac_type="Tropical",  # Must match subject1
    houses_system_identifier="P"  # Must match subject1
)

composite = CompositeSubjectFactory(subject1, subject2)
```

### "Invalid return type. Use 'Solar' or 'Lunar'."

**Cause:** Using an invalid return type string.

**Solution:** Use exactly `"Solar"` or `"Lunar"` (case-sensitive):

```python
# Correct
solar_return = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
lunar_return = factory.next_return_from_date(2024, 1, 1, return_type="Lunar")

# Wrong
# factory.next_return_from_date(2024, 1, 1, return_type="solar")  # Lowercase
# factory.next_return_from_date(2024, 1, 1, return_type="Sun")    # Wrong name
```

---

## Performance & Limits

### Polar Latitude Clamping

**Behavior:** Latitudes beyond ±66° are automatically clamped to ±66°.

**Reason:** Swiss Ephemeris house calculations become unstable at extreme latitudes.

**Recommendation:** For polar locations, use Whole Sign houses:

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Arctic Explorer", 1990, 6, 21, 12, 0,
    lng=25.0, lat=70.0,  # Will be clamped to 66.0
    tz_str="Europe/Helsinki",
    online=False,
    houses_system_identifier="W"  # Whole Sign works at any latitude
)
```

### Thread Safety Warning

**Issue:** `AstrologicalSubjectFactory` is NOT thread-safe.

**Reason:** The underlying Swiss Ephemeris library maintains global state.

**Solution:** Use separate processes or implement locking:

```python
import threading

lock = threading.Lock()

def calculate_chart(data):
    with lock:  # Ensure only one calculation at a time
        subject = AstrologicalSubjectFactory.from_birth_data(**data)
        return subject
```

### Large Number of Active Points

**Warning:** Charts with more than 24 active points may have layout issues.

**Recommendation:** Limit active points for visualization:

```python
chart_data = ChartDataFactory.create_natal_chart_data(
    subject,
    active_points=[
        "Sun", "Moon", "Mercury", "Venus", "Mars",
        "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto",
        "Ascendant", "Medium_Coeli"
    ]  # Limit to essential points
)
```

---

## Common Mistakes

### Forgetting `online=False` with Manual Coordinates

```python
# Wrong: Has coordinates but online=True (will try to use GeoNames anyway)
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London"
    # Missing online=False
)

# Correct
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False  # Explicit offline mode
)
```

### Using Deprecated v4 API Without Knowing It

If you see `DeprecationWarning` messages, you're using the legacy API:

```python
# Deprecated (works but shows warning)
from kerykeion import AstrologicalSubject
subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0, "London", "GB")

# Modern (recommended)
from kerykeion import AstrologicalSubjectFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)
```

See the [Migration Guide](/content/docs/migration) for full migration instructions.

---

## FAQ

### How do I suppress the GeoNames warning?

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    suppress_geonames_warning=True
)
```

### How do I cache GeoNames results?

Results are cached for 30 days by default. Customize with:

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    cache_expire_after_days=90  # Cache for 90 days
)
```

### How do I get the chart as a string instead of saving to file?

```python
chart_drawer = ChartDrawer(chart_data=chart_data)
svg_string = chart_drawer.get_svg_string()
```

### Why are Trans-Neptunian objects missing from my chart?

Some TNOs (Eris, Sedna, etc.) may not have ephemeris data for all dates. If calculation fails, the point is silently removed from `active_points`.

### Can I use historical dates?

Yes, Kerykeion supports historical dates including BCE dates. The Swiss Ephemeris handles Julian/Gregorian calendar conversion automatically.

### Why do Placidus houses fail for my location?

Placidus and Koch house systems fail at extreme latitudes (>60°). Use Whole Sign (`W`) or Equal (`A`) houses instead:

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    houses_system_identifier="W"  # Works at any latitude
)
```

---

## Getting More Help

1. Check the [API documentation](/content/docs/)
2. Browse the [Examples Gallery](/content/examples/)
3. Open an issue on [GitHub](https://github.com/g-battaglia/kerykeion/issues)
4. Email: kerykeion.astrology@gmail.com
