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

**Cause:** `PlanetaryReturnFactory` was constructed with `online=True` and no
`city` (the companion message *"You need to set the city and nation if you want
to use the online mode!"* covers a missing `nation`). Both are raised by that
factory only.

`AstrologicalSubjectFactory.from_birth_data` never raises them: with `online=True`
and no `city` it falls back to `"Greenwich"` / `"GB"` and looks *that* up, so a
missing city produces a chart for the wrong place rather than an error. Always
name the city, or pass coordinates and `online=False`.

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

### "No data found for this city, try again! Maybe check your connection?"

**Cause:** `PlanetaryReturnFactory` asked GeoNames for a city and got nothing back.

The equivalent failure on `AstrologicalSubjectFactory.from_birth_data` reads
*"Missing data from geonames: `<fields>`. Check your connection or try a
different location."*, naming the fields the response was missing
(`countryCode`, `timezonestr`, `lat`, `lng`). A response whose `lat`/`lng` are
present but not numeric raises *"Invalid coordinates from geonames for
`<city>`, `<nation>` ..."* instead.

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

### "Both subjects must have the same ..."

**Cause:** Creating a composite chart with subjects that have different
configurations. `CompositeSubjectFactory` checks six properties and names the
first mismatch it finds:

- `Both subjects must have the same zodiac type`
- `Both subjects must have the same sidereal mode`
- `Both subjects must have the same custom ayanamsa values` (only when `sidereal_mode="USER"`)
- `Both subjects must have the same houses system`
- `Both subjects must have the same houses system name`
- `Both subjects must have the same perspective type`

Disjoint `active_points` are refused separately, with *"The two subjects share
no common active points; a composite chart needs at least one. Align their
active_points."*

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

**On the chart:** the info panel has always printed the system actually used, not the one requested. `ChartDrawer(..., show_polar_fallback_note=True)` also admits that a substitution happened, printing `Porphyry* (polar fallback)` on the domification line — the difference between a reader trusting the line and a reader being misled by it. The note is absent whenever the requested system was honoured.

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

### Threads, Locks, and Throughput

**Issue:** the ephemeris backend keeps process-global state (ephemeris path,
sidereal mode, topocentric observer), so two concurrent calculations would
overwrite each other's configuration.

**What Kerykeion does about it:** every backend call is serialised behind an
internal lock. `kerykeion.ephemeris_backend` exposes `EPHEMERIS_LOCK` and the
`ephemeris_session` context manager, which acquires the lock, applies the
requested configuration, yields the calculation flag, then resets the session
and releases the lock. Calling the factories from several threads is therefore
**safe** — but not **parallel**: the threads queue on that lock.

**Solution:** for throughput, use processes rather than threads. Each process
gets its own backend state and runs at full speed.

```python
from concurrent.futures import ProcessPoolExecutor

def build(birth_data):
    from kerykeion import AstrologicalSubjectFactory
    return AstrologicalSubjectFactory.from_birth_data(**birth_data)

births = [
    {"name": "Alice", "year": 1990, "month": 1, "day": 1, "hour": 12, "minute": 0,
     "lng": -0.1276, "lat": 51.5074, "tz_str": "Europe/London", "online": False},
    {"name": "Bob", "year": 1992, "month": 6, "day": 15, "hour": 8, "minute": 30,
     "lng": -74.006, "lat": 40.7128, "tz_str": "America/New_York", "online": False},
]

if __name__ == "__main__":
    with ProcessPoolExecutor(max_workers=2) as pool:
        for subject in pool.map(build, births):
            print(subject.name, subject.sun.sign)
```

Only reach for `EPHEMERIS_LOCK` directly if you call `ephe.*` yourself; the
public factories already hold it.

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

GeoNames is contacted only when `tz_str`, `lat` or `lng` is missing, so a call
that already carries all three computes offline whatever `online` says. What
`online=True` still costs there is the default-username warning and the
ambiguity of a call whose intent is not stated:

```python
# Works, but says the opposite of what it does
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London"
    # Missing online=False
)

# Correct: the mode matches the data
subject = AstrologicalSubjectFactory.from_birth_data(
    "John", 1990, 1, 1, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    online=False  # Explicit offline mode
)
```

Drop any one of the three and `online=True` does reach the network — with
coordinates but no `tz_str` and no `city`, the timezone is resolved from the
coordinates themselves rather than from the `"Greenwich"` default. With
`online=False` the same call raises `KerykeionException("For offline mode, you
must provide timezone (tz_str) and coordinates (lat, lng)")`.

### Using Removed v4 API

`kerykeion.__getattr__` raises `ImportError` (not `AttributeError`) for every
name removed in v6, so the message reaches you verbatim through
`from kerykeion import ...`:

```text
'AstrologicalSubject' was removed in v6. Use the factory instead:
    from kerykeion import AstrologicalSubjectFactory
    subject = AstrologicalSubjectFactory.from_birth_data(...)

Note: v6 also changed defaults that affect RESULTS, not just imports:
  - active points: 18 -> 14 (Descendant, Imum_Coeli, True_South_Lunar_Node,
    Mean_Lilith are no longer active unless requested)
  - aspect orbs are narrower (conjunction/opposition 10 -> 6 degrees,
    quintile dropped), and transits/returns/progressions now use a flat
    3-degree orb, so expect FEWER aspects
  - chart style: 'classic' -> 'modern'
Porting the call above does not restore v5 output. See 'What changes in the
results' in the guide; kerykeion.settings.V5_DEFAULT_ACTIVE_POINTS restores
the old point set, and the guide gives the v5 aspect list.
Migration guide: https://www.kerykeion.net/content/docs/migration
```

The trade-off is that `hasattr(kerykeion, "AstrologicalSubject")` and
`getattr(kerykeion, "AstrologicalSubject", None)` raise as well; feature-detect
with `try` / `except ImportError`.

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

The warning fires because the shared default username is in use. Registering
your own account and exporting it removes both the warning and the shared rate
limit:

```bash
export KERYKEION_GEONAMES_USERNAME="your_username"
```

The username is resolved from `geonames_username`, then the
`KERYKEION_GEONAMES_USERNAME` environment variable, then the shared default. To
silence the warning without changing the username:

```python
# doc-snippet: no-run — illustrative fragment (placeholder arguments)
subject = AstrologicalSubjectFactory.from_birth_data(
    ...,
    suppress_geonames_warning=True
)
```

### Why do I see libephemeris log lines, and how do I quiet them?

Kerykeion pins libephemeris to its sealed `leb` mode by default: positions
come only from local, verified ephemeris files or from declared analytical
models — no network, no silent source substitution. That is the normal,
intended state, not a misconfiguration. The backend logs through its own
`libephemeris` logger, so standard logging configuration controls it:

```python
import logging

logging.getLogger("libephemeris").setLevel(logging.ERROR)
```

Two messages people ask about:

- `Excluding ['Earth'] from active_points` — informational and correct: you
  passed the perspective's center body in `active_points`, and it has no
  position as seen from itself. Remove it from your list or ignore the line.
- `LEB body=NN ... unavailable in sealed mode` for bodies 40–47/56 (Uranian
  points, White Moon) — a logging bug of older libephemeris releases. Those
  bodies are always computed from their analytical models by design, and the
  routing is no longer reported as a warning. Kerykeion's dependency floor is
  already `libephemeris>=3.1.0`, so a fresh install does not show the line.

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

How far back depends on the ephemeris tier installed for the default
libephemeris backend. Outside the active range a date does not degrade quietly:
it raises `KerykeionException("Cannot calculate Sun for JD ...: ... is outside
active LEB coverage range ...")`, because sealed `leb` mode refuses to
substitute a lower-precision source.

| Tier | Range | Kernel | Size |
| :-- | :-- | :-- | :-- |
| `base` | 1850 - 2150 | DE440s | ~31 MB (bundled) |
| `medium` | 1550 - 2650 | DE440 | ~114 MB |
| `extended` | -13200 to +17191 (BCE included) | DE441 | ~3.1 GB |

Install a wider tier to reach earlier dates:

```python
# doc-snippet: no-run — downloads a multi-gigabyte ephemeris kernel
import libephemeris

libephemeris.download_leb_for_tier("extended")
```

The optional Swiss Ephemeris backend (`pip install kerykeion[swiss]`, then
`KERYKEION_BACKEND=swisseph`) is the other route: it falls back to its built-in
Moshier analytical ephemeris for dates its data files do not cover. Both
backends handle the Julian/Gregorian calendar switch themselves.

### Why did my Placidus chart come back with Porphyry cusps?

Quadrant systems (Placidus `"P"`, Koch `"K"`, ...) are undefined inside the
polar circle, so Kerykeion substitutes Porphyry (`"O"`) **at the real latitude**
rather than failing or moving the observer. The substitution is logged, recorded
in `subject.polar_house_fallbacks`, and reported by
`effective_houses_system_identifier` while `houses_system_identifier` still
returns what you asked for. See [Polar Latitudes](#polar-latitudes) for the full
behaviour, including why the boundary is not a fixed 66°.

To pick the division yourself instead of accepting a substitute, use one that is
defined everywhere:

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
