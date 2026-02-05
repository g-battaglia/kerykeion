# FIXME - Kerykeion Technical Debt & Improvements

> **Generated:** 2026-02-05  
> **Kerykeion Version:** 5.7.1  
> **Analysis Scope:** Full codebase review

This document tracks identified issues, improvements, and optimizations for the Kerykeion library.

> **Exclusions:** The module `kerykeion/backword.py` is intentionally excluded from this analysis.
> It contains legacy v4 compatibility code that is scheduled for removal in v6.0. Any issues in
> that module (type errors, naming conventions, etc.) are expected and will be resolved by deletion.

---

## Table of Contents

- [Critical Priority](#-critical-priority)
- [High Priority](#-high-priority)
- [Medium Priority](#-medium-priority)
- [Low Priority](#-low-priority)
- [Performance Optimizations](#-performance-optimizations)
- [Architecture Improvements](#-architecture-improvements)
- [Documentation](#-documentation)
- [Test Improvements](#-test-improvements)

---

## 🔴 Critical Priority

### ~~FIXME-001: HTTP instead of HTTPS for GeoNames API~~ [WONTFIX]

**File:** `kerykeion/fetch_geonames.py:62-63`

**Status:** WONTFIX - GeoNames free API does not support HTTPS.

**Details:** The GeoNames free tier API (`api.geonames.org`) has an invalid SSL certificate 
that doesn't match the hostname. This is a known GeoNames infrastructure issue, not a library bug.
See: https://forum.geonames.org/gforum/posts/list/27020.page

**Workaround for users requiring HTTPS:**
- Use GeoNames premium service with `secure.geonames.org`
- Or provide coordinates directly instead of using city lookup

**Action taken:** Added explanatory comment in the code documenting this limitation.

---

### FIXME-002: Mutable Default Argument Anti-pattern

**File:** `kerykeion/aspects/aspects_utils.py:200-204`

**Current:**
```python
def get_active_points_list(
    subject_model: AstrologicalSubjectModel,
    celestial_points: list,
    active_points: list = [],  # DANGEROUS!
) -> list[KerykeionPointModel]:
```

**Issue:** Mutable default argument can cause unexpected behavior across function calls.

**Fix:**
```python
def get_active_points_list(
    subject_model: AstrologicalSubjectModel,
    celestial_points: list,
    active_points: Optional[list] = None,
) -> list[KerykeionPointModel]:
    if active_points is None:
        active_points = []
```

**Effort:** 10 minutes

---

### FIXME-003: Typo in Method Name

**File:** `kerykeion/fetch_geonames.py:123`

**Current:**
```python
def __get_contry_data(self, city_name: str, country_code: str):
```

**Fix:**
```python
def __get_country_data(self, city_name: str, country_code: str):
```

**Note:** This is a private method, but the typo should still be corrected. Update all call sites.

**Effort:** 10 minutes

---

## 🟠 High Priority

### FIXME-004: Excessive `type: ignore` Comments (~54 occurrences)

**Files:**
- `kerykeion/charts/chart_drawer.py`: 21 occurrences
- `kerykeion/planetary_return_factory.py`: 9 occurrences
- `kerykeion/astrological_subject_factory.py`: 2 occurrences
- Various others: 22 occurrences

> **Note:** `kerykeion/backword.py` (16 occurrences) is excluded from this count as it contains 
> legacy code scheduled for removal in v6.0. Type errors in that module are intentionally ignored.

**Issue:** Type ignores hide potential type errors and reduce code safety.

**Action:** 
1. Audit each `type: ignore` comment
2. Fix underlying type issues where possible
3. Add specific ignore codes where unavoidable (e.g., `# type: ignore[misc]`)

**Effort:** 3-5 hours

---

### FIXME-005: Bare Exception Handling

**File:** `kerykeion/fetch_geonames.py:107-109, 114-116, 155-157, 165-167, 185-187`

**Current:**
```python
except Exception as e:
    logger.error("GeoNames timezone request failed for %s: %s", self.timezone_url, e)
    return {}
```

**Issues:**
- Catches all exceptions including `KeyboardInterrupt`, `SystemExit`
- Returns empty dict, hiding actual errors
- No error propagation for caller handling

**Fix:**
```python
except requests.RequestException as e:
    logger.error("GeoNames network error for %s: %s", self.timezone_url, e)
    raise KerykeionException(f"Failed to fetch timezone data: {e}") from e
except json.JSONDecodeError as e:
    logger.error("GeoNames invalid JSON response: %s", e)
    raise KerykeionException(f"Invalid API response: {e}") from e
```

**Effort:** 1 hour

---

### FIXME-006: Inconsistent Naming Convention (camelCase vs snake_case)

**File:** `kerykeion/charts/charts_utils.py:343-456`

**Current:**
```python
def decHourJoin(inH: int, inM: int, inS: int) -> float:
def degreeDiff(a: Union[int, float], b: Union[int, float]) -> float:
def degreeSum(a: Union[int, float], b: Union[int, float]) -> float:
def normalizeDegree(angle: Union[int, float]) -> float:
def sliceToX(slice: Union[int, float], r: Union[int, float], ...) -> float:
def sliceToY(slice: Union[int, float], r: Union[int, float], ...) -> float:
```

**Fix (with backward compatibility):**
```python
def dec_hour_join(in_h: int, in_m: int, in_s: int) -> float:
    ...

# Backward compatibility alias
decHourJoin = dec_hour_join  # Deprecated: use dec_hour_join
```

**Effort:** 2 hours (including updating all call sites)

---

### FIXME-007: Redundant Type Hint

**File:** `kerykeion/aspects/aspects_utils.py:16-17`

**Current:**
```python
aspects_settings: Union[list[dict], list[dict]],  # Redundant Union
```

**Fix:**
```python
aspects_settings: list[dict],
```

**Effort:** 5 minutes

---

### FIXME-008: Typo in Variable Name

**File:** `kerykeion/fetch_geonames.py:135`

**Current:**
```python
city_data_whitout_tz = {}  # "whitout" should be "without"
```

**Fix:**
```python
city_data_without_tz = {}
```

**Effort:** 5 minutes

---

## 🟡 Medium Priority

### FIXME-009: Code Duplication - House Cusp Assignment

**File:** `kerykeion/astrological_subject_factory.py:1141-1152`

**Current:**
```python
data["first_house"] = get_kerykeion_point_from_degree(cusps[0], "First_House", point_type=point_type)
data["second_house"] = get_kerykeion_point_from_degree(cusps[1], "Second_House", point_type=point_type)
data["third_house"] = get_kerykeion_point_from_degree(cusps[2], "Third_House", point_type=point_type)
# ... repeated 12 times
```

**Fix:**
```python
HOUSE_NAMES = [
    ("first_house", "First_House"),
    ("second_house", "Second_House"),
    # ... etc
]

for i, (attr_name, house_name) in enumerate(HOUSE_NAMES):
    data[attr_name] = get_kerykeion_point_from_degree(
        cusps[i], house_name, point_type=point_type
    )
```

**Effort:** 30 minutes

---

### FIXME-010: Code Duplication - Lunar Phase Logic

**File:** `kerykeion/utilities.py:424-443 and 462-482`

**Issue:** `get_moon_emoji_from_phase_int()` and `get_moon_phase_name_from_phase_int()` have identical conditional logic.

**Fix:**
```python
def _get_lunar_phase_index(phase: int) -> int:
    """Get the index for lunar phase lookup."""
    if phase == 1:
        return 0
    elif phase < 7:
        return 1
    elif phase == 7:
        return 2
    # ... etc

def get_moon_emoji_from_phase_int(phase: int) -> str:
    return LUNAR_PHASE_EMOJIS[_get_lunar_phase_index(phase)]

def get_moon_phase_name_from_phase_int(phase: int) -> str:
    return LUNAR_PHASE_NAMES[_get_lunar_phase_index(phase)]
```

**Effort:** 30 minutes

---

### FIXME-011: Mixed Language Comments

**File:** `kerykeion/astrological_subject_factory.py:1161-1166`

**Current:**
```python
# NOTE: Swiss Ephemeris does not provide direct speeds for angles (ASC/MC),
# but in realtà si muovono molto velocemente rispetto ai pianeti.
# Per rappresentare questo in modo coerente, assegniamo ai quattro assi
# una speed sintetica fissa, molto più alta di quella planetaria tipica.
```

**Fix:** Translate all comments to English for consistency.

**Effort:** 1 hour (codebase-wide)

---

### FIXME-012: Incomplete Docstring Placeholder

**File:** `kerykeion/fetch_geonames.py:174`

**Current:**
```python
def get_serialized_data(self) -> dict[str, str]:
    """...
    Returns:
        dict[str, str]: _description_
    """
```

**Fix:**
```python
def get_serialized_data(self) -> dict[str, str]:
    """...
    Returns:
        dict[str, str]: Dictionary containing city, latitude, longitude, 
        country code, timezone, and nation information.
    """
```

**Effort:** 10 minutes

---

### FIXME-013: Docstring Parameter Mismatch

**File:** `kerykeion/aspects/aspects_utils.py:200-220`

**Issue:** Docstring mentions `settings` parameter but function has `celestial_points`.

**Effort:** 10 minutes

---

## 🟢 Low Priority

### FIXME-014: Deprecated pytz Dependency

**File:** `pyproject.toml:55`

**Current:**
```toml
pytz>=2024.2
```

**Issue:** Python 3.9+ has `zoneinfo` in standard library. `pytz` is no longer needed.

**Action:** 
1. Replace `pytz` usage with `zoneinfo`
2. Use `backports.zoneinfo` for Python 3.8 if needed (but project requires 3.9+)

**Effort:** 2-3 hours

---

### FIXME-015: Missing Utility Function Examples

**File:** `kerykeion/utilities.py`

**Functions without docstring examples:**
- `is_point_between()` 
- `get_planet_house()`
- `datetime_to_julian()`
- `inline_css_variables_in_svg()`

**Action:** Add `Example:` sections following the project's docstring format.

**Effort:** 1 hour

---

### FIXME-016: TODO Comments to Address

**File:** `kerykeion/aspects/aspects_utils.py:5`
```python
# TODO: Better documentation and unit tests
```

**File:** `kerykeion/aspects/aspects_utils.py:35-36`
```python
# TODO: Remove the "degree" element EVERYWHERE!
```

**Action:** Either address the TODOs or convert them to GitHub issues with references.

**Effort:** Variable

---

## ⚡ Performance Optimizations

### PERF-001: Memory - List Comprehension for Large Date Ranges

**File:** `kerykeion/ephemeris_data_factory.py:186-215`

**Current:**
```python
self.dates_list = [
    self.start_datetime + timedelta(days=i * self.step)
    for i in range((self.end_datetime - self.start_datetime).days // self.step + 1)
]
```

**Issue:** For minute-step calculations over a year, this creates 500,000+ datetime objects upfront.

**Fix:**
```python
def _date_generator(self):
    """Lazy generator for date iteration."""
    current = self.start_datetime
    while current <= self.end_datetime:
        yield current
        current += timedelta(**{self.step_type: self.step})
```

**Impact:** Significant memory reduction for large ranges

**Effort:** 1 hour

---

### PERF-002: CPU - Sequential Transit Calculations

**File:** `kerykeion/transits_time_range_factory.py:242-260`

**Current:**
```python
for ephemeris_point in self.ephemeris_data_points:
    aspects = AspectsFactory.dual_chart_aspects(...)
```

**Issue:** All calculations are sequential; doesn't utilize multiple CPU cores.

**Fix:**
```python
from concurrent.futures import ProcessPoolExecutor

def _calculate_transit(ephemeris_point):
    return AspectsFactory.dual_chart_aspects(...)

with ProcessPoolExecutor() as executor:
    transit_moments = list(executor.map(_calculate_transit, self.ephemeris_data_points))
```

**Impact:** 2-8x speedup on multi-core systems

**Effort:** 2 hours

---

### PERF-003: Memory - DeepCopy Settings on Every ChartDrawer

**File:** `kerykeion/charts/chart_drawer.py:1832-1834`

**Current:**
```python
self.chart_colors_settings = deepcopy(colors_settings)
self.planets_settings = [dict(body) for body in celestial_points_settings]
self.aspects_settings = [dict(aspect) for aspect in aspects_settings]
```

**Issue:** Creates copies of 50+ dictionaries per chart instance.

**Fix:** Use frozen/immutable defaults or share read-only settings between instances.

**Effort:** 2 hours

---

### PERF-004: I/O - Synchronous GeoNames API

**File:** `kerykeion/fetch_geonames.py`

**Issue:** All HTTP requests are blocking. When creating multiple subjects for different locations, each request is sequential.

**Action:** 
1. Document that `requests_cache` provides 30-day caching (already implemented)
2. Consider providing an async alternative using `aiohttp` for batch operations

**Effort:** 4 hours (for async version)

---

### PERF-005: CPU - O(n*m) Lookup in Aspect Settings

**File:** `kerykeion/aspects/aspects_factory.py:510-518`

**Current:**
```python
for aspect_setting in aspects_settings:
    for active_aspect in active_aspects:
        if aspect_setting["name"] == active_aspect["name"]:
            ...
```

**Fix:**
```python
active_orbs = {a["name"]: a["orb"] for a in active_aspects}
for aspect_setting in aspects_settings:
    if aspect_setting["name"] in active_orbs:
        ...
```

**Impact:** Reduces O(n*m) to O(n+m)

**Effort:** 30 minutes

---

## 🏗️ Architecture Improvements

### ARCH-001: SRP Violation - AstrologicalSubjectFactory Too Large

**File:** `kerykeion/astrological_subject_factory.py` (~1200 lines)

**Current responsibilities:**
- Location data management (GeoNames integration)
- Time zone conversions
- Swiss Ephemeris initialization and configuration
- House calculations
- Planetary position calculations
- Arabic Parts calculations
- Fixed star calculations
- Lunar phase calculations
- Configuration validation

**Proposed refactoring:**
```python
class LocationResolver:
    """Handle GeoNames lookup and coordinate management."""

class EphemerisCalculator:
    """Handle Swiss Ephemeris configuration and calculations."""

class HouseCalculator:
    """Handle house cusp calculations."""

class PointCalculator:
    """Handle planetary position calculations."""
```

**Effort:** 8-16 hours (major refactoring)

---

### ARCH-002: Constructor with Too Many Parameters

**File:** `kerykeion/astrological_subject_factory.py:499-527`

**Issue:** `from_birth_data()` has 26 parameters.

**Fix:** Use Builder pattern or configuration objects:
```python
config = ChartConfig(zodiac_type="Sidereal", house_system="Koch")
birth = BirthData(1990, 1, 1, 12, 0)
location = Location(city="Rome", nation="IT")

subject = AstrologicalSubjectFactory.from_birth_data(
    name="John",
    birth_data=birth,
    location=location,
    config=config
)
```

**Effort:** 4-6 hours

---

### ARCH-003: Missing Dependency Abstraction for Swiss Ephemeris

**File:** `kerykeion/astrological_subject_factory.py:191`

**Current:**
```python
import swisseph as swe
# Direct calls like: swe.calc_ut(...)
```

**Issue:** Direct dependency makes unit testing difficult without ephemeris data.

**Fix:** Create an abstraction layer:
```python
class EphemerisProvider(Protocol):
    def calculate_planet_position(self, julian_day: float, planet_id: int) -> PlanetPosition:
        ...

class SwissEphemerisProvider(EphemerisProvider):
    """Production implementation using pyswisseph."""

class MockEphemerisProvider(EphemerisProvider):
    """Test implementation with fixed data."""
```

**Effort:** 6-8 hours

---

### ARCH-004: High Module Coupling in chart_data_factory.py

**File:** `kerykeion/chart_data_factory.py`

**Issue:** Imports from 10+ different kerykeion submodules.

**Action:** Create a facade module that aggregates commonly-needed imports.

**Effort:** 2 hours

---

## 📝 Documentation

### DOC-001: Add Thread Safety Warning to README

**File:** `README.md`

**Issue:** Thread safety warning exists only in class docstrings, not in README.

**Action:** Add a "Thread Safety" section to README.

**Effort:** 15 minutes

---

### DOC-002: Add Troubleshooting Section to README

**File:** `README.md`

**Action:** Add brief troubleshooting section or link to FAQ docs.

**Effort:** 30 minutes

---

## 🧪 Test Improvements

### TEST-001: Repetitive Test Code Not Parametrized

**File:** `tests/core/test_astrological_subject.py:36-430+`

**Current:**
```python
def test_sun(self):
    assert self.subject.sun.name == self.expected_output["sun"]["name"]
    assert self.subject.sun.quality == self.expected_output["sun"]["quality"]
    # ... 10 more similar assertions
def test_moon(self):
    assert self.subject.moon.name == self.expected_output["moon"]["name"]
    # ... same pattern repeated
```

**Fix:** Use parametrized tests:
```python
@pytest.mark.parametrize("point_name", ["sun", "moon", "mercury", ...])
def test_celestial_point(self, point_name):
    point = getattr(self.subject, point_name)
    expected = self.expected_output[point_name]
    assert point.name == expected["name"]
    assert point.quality == expected["quality"]
    # ...
```

**Effort:** 2 hours

---

### TEST-002: Tolerance Constants Not Centralized

**Issue:** Tolerance values are scattered across test files:
```python
abs=1e-2  # in one file
POSITION_TOLERANCE = 1e-2  # in conftest
POSITION_ABS_TOL = 1e-2  # in another file
```

**Action:** Centralize all tolerance constants in `tests/conftest.py`.

**Effort:** 1 hour

---

### TEST-003: Missing Direct Unit Tests

**Files with limited direct testing:**
- `kerykeion/charts/charts_utils.py` - only tested indirectly through chart tests
- `kerykeion/house_comparison/house_comparison_utils.py` - limited direct testing

**Action:** Add dedicated unit test files.

**Effort:** 4 hours

---

## Summary

| Priority | Count | Estimated Total Effort |
|----------|-------|----------------------|
| 🔴 Critical | 2 | 20 minutes |
| 🟠 High | 5 | 6-8 hours |
| 🟡 Medium | 5 | 3 hours |
| 🟢 Low | 3 | 4 hours |
| ⚡ Performance | 5 | 10 hours |
| 🏗️ Architecture | 4 | 20-32 hours |
| 📝 Documentation | 2 | 45 minutes |
| 🧪 Test | 3 | 7 hours |

**Total Issues:** 29 (1 WONTFIX)  
**Estimated Total Effort:** 51-65 hours

---

## How to Use This Document

1. **Quick Wins:** Start with Critical and High priority items marked with low effort
2. **Sprint Planning:** Group related items (e.g., all FIXME items in `fetch_geonames.py`)
3. **Tech Debt Sprints:** Dedicate time for Architecture improvements
4. **Continuous Improvement:** Address Low priority items during regular development

---

## Changelog

| Date | Author | Changes |
|------|--------|---------|
| 2026-02-05 | Automated Analysis | Initial document creation |
