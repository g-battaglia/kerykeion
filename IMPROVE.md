# Simplification & Maintainability Requirements for `AstrologicalSubjectFactory`

## Objective
Provide a simple, robust, and maintainable API to create complete astrological subjects (planetary positions, houses, special points) by separating pure computation from side effects and reducing duplication and global state.

## Operational Summary
1. The current lightweight OOP approach is fine but should be more modular: separate pure computation from I/O and Swiss Ephemeris global state.
2. Introduce a points registry to eliminate repetitive `if` branches.
3. Make time handling deterministic and safe, including DST and angle normalization.
4. Wrap Swiss Ephemeris (`swe`) global state in a context manager.
5. Reduce duplicate calls and unnecessary recalculations.
6. Improve testability and performance with single-pass computations and injected dependencies.

## Immediate Mandatory Fixes
1. Default time handling
   - Problem: `NOW = datetime.now()` is captured at import time and becomes stale.
   - Requirement: use `None` defaults and resolve values inside methods.

```python
def from_birth_data(..., year=None, month=None, day=None, hour=None, minute=None, seconds=None, ...):
    now = datetime.now()
    year   = year   if year   is not None else now.year
    month  = month  if month  is not None else now.month
    day    = day    if day    is not None else now.day
    hour   = hour   if hour   is not None else now.hour
    minute = minute if minute is not None else now.minute
    seconds = seconds if seconds is not None else now.second
```

2. DST ambiguity and UTC→local round-trip
   - Problem: `from_iso_utc_time` converts to local, then `from_birth_data` re-localizes a naive datetime, risking `AmbiguousTimeError`.
   - Requirement: accept an aware `datetime` (or a `utc_datetime`) and compute JD directly, avoiding unnecessary relocalization. Also handle `NonExistentTimeError`.

3. Day of week
   - Problem: inconsistency between docstring, comment, and `swe.day_of_week` mapping.
   - Requirement: derive the weekday name using the standard library.

```python
from datetime import datetime
def _calculate_day_of_week(data):
    dt = datetime.fromisoformat(data["iso_formatted_local_datetime"])
    data["day_of_week"] = dt.strftime("%A")
```

4. Angle normalization
   - Problem: `math.fmod` may produce negative degrees.
   - Requirement: always normalize to [0, 360).

```python
def norm360(deg: float) -> float:
    return (deg % 360 + 360) % 360
```

5. Duplicate `fixstar_ut` calls
   - Problem: double invocation for the same star.
   - Requirement: call once and reuse the result.

```python
pos, _ = swe.fixstar_ut("Regulus", julian_day, iflag)
regulus_deg = pos[0]
```

6. Avoid recomputing houses/Ascendant
   - Problem: recomputation in multiple places, especially for Parts.
   - Requirement: reuse `_calculate_houses` output or an accessor that reads from a cache.

## Required Design
1. Functional core, imperative shell
   - Requirement: split the pipeline into pure functions and a thin imperative shell:
     - `resolve_location`
     - `resolve_time`
     - `with_ephemeris_context`
     - `calc_houses`
     - `calc_points`
     - `calc_derived`
     - `assemble_model`

2. Context manager for Swiss Ephemeris
   - Requirement: encapsulate `swe` global settings in a context manager and return `iflag`.

```python
from contextlib import contextmanager
@contextmanager
def ephemeris_context(path: str, config: ChartConfiguration, lng: float, lat: float, alt: float | None):
    swe.set_ephe_path(path)
    iflag = swe.FLG_SWIEPH + swe.FLG_SPEED

    if config.perspective_type == "True Geocentric":
        iflag += swe.FLG_TRUEPOS
    elif config.perspective_type == "Heliocentric":
        iflag += swe.FLG_HELCTR
    elif config.perspective_type == "Topocentric":
        iflag += swe.FLG_TOPOCTR
        swe.set_topo(lng, lat, alt or 0)

    if config.zodiac_type == "Sidereal":
        iflag += swe.FLG_SIDEREAL
        swe.set_sid_mode(getattr(swe, f"SIDM_{config.sidereal_mode}"))

    try:
        yield iflag
    finally:
        # Add resets if needed
        pass
```

5. Time API
   - Requirement: accept aware `datetime` inputs (UTC or local). If UTC is passed, skip localization. Expose parameters to bypass `is_dst`.

6. Dependency Injection
   - Requirement: pass `FetchGeonames` and `ephe_path` as injected dependencies to simplify testing and mocking.
   - Requirement: make `DEFAULT_ACTIVE_POINTS` an immutable `tuple` and always copy it with `list(...)`.

## Targeted Refactors
1. Degree normalization
   - Requirement: use `norm360` for Descendant, IC, Anti-Vertex, Parts, and any angular combination.

2. House system name
   - Requirement: remove `houses_system_name` if unused.

3. Logging and user-visible messages
   - Requirement: in addition to logging, accumulate warnings in `data["messages"]`.

4. `LocationData.prepare_for_calculation`
   - Requirement: document the polar adjustment criterion and consider a pure function that returns adjusted values.

5. `ChartConfiguration.validate`
   - Requirement: move validation to `__post_init__` to guarantee valid objects post-construction.

6. Vertex
   - Requirement: compute Vertex once and cache. If a different house system is required, make it explicit in the API.

## Use `@staticmethod` for Internal Helpers

Internal methods like `_calculate_time_conversions`, `_setup_ephemeris`, and `_calculate_houses` are currently defined as `@classmethod` and take `cls` as the first argument, but they don’t actually use it. They only operate on the `calc_data` dictionary passed in.

**Problem:** Using `@classmethod` suggests the method operates on the class itself (e.g., accessing class variables or calling other class methods). If it doesn’t, the intent is misleading.

**Solution:** Define these methods as `@staticmethod`.

```python
@staticmethod
def _calculate_time_conversions(calc_data: Dict[str, Any], location: LocationData) -> None:
    # Logic remains the same, but 'cls' is no longer needed
    # ...

@staticmethod
def _setup_ephemeris(calc_data: Dict[str, Any], config: ChartConfiguration) -> None:
    # ...
```

## Performance
1. Requirement: a single pass for registered bodies with `swe.calc_ut`.
2. Requirement: compute houses once and reuse the results.
3. Requirement: avoid duplicate calls to `swe.houses*` and `swe.fixstar_ut`.
4. Requirement: pre-compute constant sets from `get_args(...)` outside hot paths.

## Testability
1. Requirement: golden tests on known dates for JD and key positions.
2. Requirement: property tests for `norm360` and Part formulas.
3. Requirement: DST tests on changeover dates for multiple time zones.
4. Requirement: mock `FetchGeonames` and the ephemeris path via dependency injection.
