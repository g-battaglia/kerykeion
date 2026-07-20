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
# doc-snippet: no-run — requires your own GeoNames account (online)
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

### What `is_dst` actually selects

`is_dst` picks a **UTC offset**, not a season:

- `is_dst=True` → the reading with the **larger** UTC offset.
- `is_dst=False` → the reading with the **smaller** UTC offset.
- `is_dst=None` (the default) → raise, rather than guess.

The name is historical; the contract is the offset. Reading it as "was summer time in force?" gives the same answer almost everywhere, because a zone that advances its clocks in summer does end up with the larger offset then. It gives the *opposite* answer on zones whose tz build encodes summer as the baseline and winter as a *negative* DST shift — Ireland is the textbook case, with `Europe/Dublin` shipped by some builds as summer `dst()=0` against a winter of `-1h`; `Africa/Casablanca` and `Africa/Windhoek` have carried the same encoding. Which zones use it depends on the tz database build installed on your machine (vanguard and rearguard formats disagree), so there is no fixed list and no fixed count to quote.

If you are migrating from Kerykeion 5, which delegated to `pytz` and its `is_dst` flag, expect the selection to flip for exactly those zones. Everywhere else the resolved instant is unchanged. Anchoring on the offset is what makes the behaviour reproducible across machines: the offset is a property of the clock, the DST flag is a property of how someone chose to write the zone down.

### "Ambiguous time error! The wall time ... occurred twice in ..."

Full message:

```text
Ambiguous time error! The wall time 2023-11-05T01:30:00 occurred twice in
America/New_York: the zone's clocks moved back across it, either for daylight
saving or for a change of standard time. Please specify is_dst=True for the
earlier reading (the larger UTC offset) or is_dst=False for the later one (the
smaller).
```

**Cause:** The zone's clocks moved back across that wall time, so it happened twice (e.g. 1:30 AM occurs twice on the first Sunday of November in the US). The message names both daylight saving and a change of standard time because the tz database records the two in the same shape, and Kerykeion does not claim to know which one it was.

**Solution:** Pick the occurrence with `is_dst`:

```python
# The earlier reading — the larger UTC offset, here -04:00
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 2023, 11, 5, 1, 30,  # Ambiguous time
    lng=-74.006, lat=40.7128, tz_str="America/New_York",
    online=False,
    is_dst=True
)

# The later reading — the smaller UTC offset, here -05:00
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 2023, 11, 5, 1, 30,
    lng=-74.006, lat=40.7128, tz_str="America/New_York",
    online=False,
    is_dst=False
)
```

### "Non-existent time error! The wall time ... never occurred in ..."

Full message:

```text
Non-existent time error! The wall time 2023-03-12T02:30:00 never occurred in
America/New_York: the zone's clocks jumped forward across it, either for
daylight saving or for a change of standard time. Please specify a valid time,
or pass is_dst to choose a reading.
```

**Cause:** The zone's clocks jumped forward across that wall time, skipping it (e.g. 2:30 AM does not exist on the second Sunday of March in the US).

**Solution A — use a time the clock really showed:**

```python
# Instead of 2:30 AM (which doesn't exist)
# Use either 1:30 AM or 3:30 AM
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 2023, 3, 12, 3, 30,  # Use 3:30 instead of 2:30
    lng=-74.006, lat=40.7128, tz_str="America/New_York",
    online=False
)
```

**Solution B — resolve the gap with `is_dst`:** the flag is not limited to ambiguous times. Inside a gap it selects an offset just as it does inside a fold, which is what you want when a record says 2:30 and you have no way to correct it:

```python
# Read with the larger offset, -04:00 -> 06:30 UTC
AstrologicalSubjectFactory.from_birth_data(
    "John", 2023, 3, 12, 2, 30,
    lng=-74, lat=40.7, tz_str="America/New_York",
    online=False, is_dst=True
)

# Read with the smaller offset, -05:00 -> 07:30 UTC
AstrologicalSubjectFactory.from_birth_data(
    "John", 2023, 3, 12, 2, 30,
    lng=-74, lat=40.7, tz_str="America/New_York",
    online=False, is_dst=False
)
```

The two land an hour apart, which is the honest representation of a wall time the clock skipped: there is no single correct instant, only two defensible readings.

### Births before 1902: nothing is rejected

Below `1902-01-01` a non-unique wall time is **resolved**, never raised. This is not leniency, it is the only answerable reading.

Daylight saving did not exist yet — the earliest seasonal transition anywhere in the tz database is from 1916. What sits below that horizon instead are the 19th-century adoptions of mean and standard time: one-off, permanent moves of a city's clock. The database stores them in the same shape as a summer-time change, so they reach the resolver looking identical, and "was daylight saving in effect?" is not a question 1893 can answer. Asking a caller to answer it about their own birth certificate would be asking for a guess.

So with `is_dst` left at its default the wall time resolves to the offset **in force before the change**, which is what the clock in the room showed and what the registrar wrote down. An explicit `is_dst` still means what it means everywhere else — the larger or the smaller offset — and is honoured here too:

```python
# Rome adopted Central European Time on 1893-11-01; the wall times from
# 23:49:56 to midnight were skipped. This one casts, on Rome's own mean time.
subject = AstrologicalSubjectFactory.from_birth_data(
    "Roman birth", 1893, 10, 31, 23, 55,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome",
    online=False
)
print(subject.iso_formatted_local_datetime)  # 1893-10-31T23:55:00+00:49:56
print(subject.iso_formatted_utc_datetime)    # 1893-10-31T23:05:04+00:00
```

Folds behave the same way. New York's 1883 adoption *repeated* four minutes rather than skipping them, and 1883-11-18 12:00 resolves to the pre-change −04:56:02 rather than to the −05:00 that followed.

A chart for that instant reports −04:56:01 rather than −04:56:02, and the extra second is not a rounding slip: New York's pre-1883 record is the tz database's synthetic `LMT` entry, which carries the mean time of the zone's reference point and not of the birth place. Kerykeion replaces that one with the mean time of the birth longitude, since a sundial in the room is better data than a placeholder. Named records — Rome's `RMT`, Amsterdam's `BMT`, Kyiv's `KMT` — are documented clock times the city genuinely kept, and are never overridden.

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
from kerykeion import PlanetaryReturnFactory

factory = PlanetaryReturnFactory(
    subject,  # your natal AstrologicalSubjectModel
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)

# Correct
solar_return = factory.next_return_from_date(2024, 1, 1, return_type="Solar")
lunar_return = factory.next_return_from_date(2024, 1, 1, return_type="Lunar")

# Wrong
# factory.next_return_from_date(2024, 1, 1, return_type="solar")  # Lowercase
# factory.next_return_from_date(2024, 1, 1, return_type="Sun")    # Wrong name
```

---

## Performance & Limits

### Polar Latitudes

**Behavior:** The subject's latitude is never clamped in v6 — the real value is preserved in the model, in the topocentric observer, and in every house call. When a quadrant house system (e.g. Placidus `"P"`, Koch `"K"`) is undefined at the birth latitude, what gives way is the **house system**, not the observer's position: the cusps are recomputed with Porphyry (`"O"`) **at the real latitude**, a warning is logged naming both systems, and the substitution is recorded on the subject in `polar_house_fallbacks`, a list of `PolarHouseFallbackModel`.

The angles are untouched. Ascendant, MC, Descendant, IC and Vertex are intersections of the ecliptic with the horizon and the meridian; they do not depend on a house system, so they stay exact at any latitude. Only the intermediate cusps come from the substitute, which is what the record's `affects` field names.

The requested system also survives. `houses_system_identifier` still reports what you asked for, while `effective_houses_system_identifier` reports the division the cusps really came from — so a later relocation to a temperate latitude starts from Placidus again rather than inheriting Porphyry forever.

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Arctic Explorer", 1990, 6, 21, 12, 0,
    lng=25.0, lat=70.0,           # Real latitude, preserved everywhere
    tz_str="Europe/Helsinki",
    online=False,
    houses_system_identifier="P",  # Placidus, undefined this far north
)

print(subject.lat)                                    # 70.0 — never clamped
print(subject.houses_system_identifier)               # "P"  — what you asked for
print(subject.effective_houses_system_identifier)     # "O"  — what the cusps used

record = subject.polar_house_fallbacks[0]
print(record.strategy)      # "substitute_system"
print(record.used_latitude) # 70.0 — the substitution ran at the real latitude
print(record.threshold)     # 66.558... — the polar circle for this epoch
print(record.affects)       # ["house_cusps"] — the angles are not listed
```

**Reason:** Quadrant systems divide the semi-diurnal arc of a degree of the ecliptic. Inside the polar circle some degrees never rise or set, so that arc does not exist and there is nothing to divide. Latitude-agnostic systems (Whole Sign, Equal, Porphyry, ...) have no such limit, which is why one of them can stand in.

**About "±66°":** that figure is a rule of thumb, not the boundary. The polar circle sits at 90° minus the true obliquity of the ecliptic, which drifts with the epoch — 66.558° for a modern date, closer to 65.85° around 3000 BCE. The backend measures it per chart and reports it in the record's `threshold` field, alongside the `obliquity` it was derived from. Do not hardcode 66.

The fixed ±66° clamp survives in exactly one place: **Gauquelin sectors**. Their 36-cusp shape has no 12-cusp equivalent, so no substitute system can produce it, and the only way to get an answer is to retry the requested division just inside the limit. That case is recorded too, with `strategy="clamp_latitude"` and `affects` listing the angles as well, because there the observer really did move.

**Recommendation:** If you would rather choose the division yourself than accept a substitute, pick one that is defined everywhere:

```python
subject = AstrologicalSubjectFactory.from_birth_data(
    "Arctic Explorer", 1990, 6, 21, 12, 0,
    lng=25.0, lat=70.0,
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

### Using Removed v4 API

If you see `ImportError: cannot import name 'AstrologicalSubject'`, you're using the old v4 API that was removed in v6:

```python
# REMOVED in v6 (raises ImportError):
# from kerykeion import AstrologicalSubject
# subject = AstrologicalSubject("John", 1990, 1, 1, 12, 0, "London", "GB")

# v6 API (correct):
from kerykeion import AstrologicalSubjectFactory
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False
)
```

See the [Migration Guide](/content/docs/migration) and [Legacy API](/content/docs/legacy) for details.

---

## FAQ

### How do I suppress the GeoNames warning?

```python
# doc-snippet: no-run — illustrative fragment (placeholder arguments)
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    suppress_geonames_warning=True
)
```

### How do I cache GeoNames results?

Results are cached for 30 days by default. Customize with:

```python
# doc-snippet: no-run — illustrative fragment (placeholder arguments)
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    cache_expire_after_days=90  # Cache for 90 days
)
```

### How do I get the chart as a string instead of saving to file?

```python
chart_drawer = ChartDrawer(chart_data=chart_data)
svg_string = chart_drawer.generate_svg_string()
```

### Why are Trans-Neptunian objects missing from my chart?

Some TNOs (Eris, Sedna, etc.) may not have ephemeris data for all dates. If calculation fails, a warning is logged and the point is removed from `active_points`.

### Can I use historical dates?

Yes, Kerykeion supports historical dates including BCE dates. The Swiss Ephemeris handles Julian/Gregorian calendar conversion automatically.

### Why do Placidus houses fail for my location?

Placidus and Koch house systems fail at extreme latitudes (>60°). Use Whole Sign (`W`) or Equal (`A`) houses instead:

```python
# doc-snippet: no-run — illustrative fragment (placeholder arguments)
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    houses_system_identifier="W"  # Works at any latitude
)
```

### How do I compute secondary progressions?

Use the dedicated `SecondaryProgressionFactory`:

```python
from kerykeion import AstrologicalSubjectFactory, SecondaryProgressionFactory

natal = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)

# Simple: get the progressed chart as a standard subject
progressed = SecondaryProgressionFactory.compute(natal, target_year=2026)

# Full: get the progressed chart + progressed-to-natal aspects
result = SecondaryProgressionFactory.compute_full(
    natal, target_iso_utc_datetime="2026-06-15T00:00:00Z"
)
```

See the full [Secondary Progressions](/content/docs/secondary_progressions_factory) documentation.

### How do I find eclipses?

```python
from kerykeion import EclipseFactory

# Global search
results = EclipseFactory.search_global(start_year=2025, count=5)

# Location-specific search
results = EclipseFactory.search_from_location(lat=41.9, lng=12.5, start_year=2025)
```

See the full [Eclipse Factory](/content/docs/eclipse_factory) documentation.

### How do I generate astro-cartography lines?

```python
from kerykeion import AstrologicalSubjectFactory, AstroCartographyFactory

subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 6, 15, 14, 30,
    lng=12.5, lat=41.9, tz_str="Europe/Rome", online=False,
)
lines = AstroCartographyFactory.compute(subject, step=2)
```

See the full [Astro-Cartography](/content/docs/astro_cartography_factory) documentation.

### How do I relocate a chart to a different city?

```python
from kerykeion import RelocatedChartFactory

# `natal` is the subject from the secondary-progressions example above
relocated = RelocatedChartFactory.relocate(
    natal, new_lat=40.71, new_lng=-74.00, new_city="New York"
)
```

Planetary positions stay the same; only houses and angles change. See [Relocated Charts](/content/docs/relocated_chart_factory).

---

## Getting More Help

1. Check the [API documentation](/content/docs/)
2. Browse the [Examples Gallery](/content/examples/)
3. Open an issue on [GitHub](https://github.com/g-battaglia/kerykeion/issues)
4. Email: kerykeion.astrology@gmail.com

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
