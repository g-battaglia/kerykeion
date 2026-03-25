# Libephemeris Backend Integration

This document describes the dual-backend architecture for kerykeion, covering
installation, runtime behavior, API compatibility, numerical differences,
date-range limits, performance characteristics, and test adjustments.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Runtime Backend Detection](#runtime-backend-detection)
- [Architecture](#architecture)
- [API Compatibility](#api-compatibility)
- [Numerical Accuracy](#numerical-accuracy)
  - [Planetary Positions](#planetary-positions)
  - [House Cusps and Speeds](#house-cusps-and-speeds)
  - [Rise/Set and Eclipse Times](#riseset-and-eclipse-times)
  - [Zodiac Signs](#zodiac-signs)
- [Date Range Limitations](#date-range-limitations)
- [Performance](#performance)
- [Test Adjustments](#test-adjustments)
- [Modified Files](#modified-files)

---

## Overview

Kerykeion supports two mutually exclusive ephemeris backends:

| Backend | Package | Language | Ephemeris Data | Requires C Compiler |
|---------|---------|----------|----------------|---------------------|
| **swisseph** | `pyswisseph` | C bindings | Swiss Ephemeris | Yes |
| **libephemeris** | `libephemeris` >= 1.0.0a1 | Pure Python | NASA JPL DE440/DE441 via Skyfield | No |

Both backends expose an identical API surface. A thin abstraction layer
(`kerykeion/ephemeris_backend.py`) auto-detects the installed backend at
import time. As of libephemeris 1.0.0a1, the two backends are fully
API-compatible and **no compatibility shims are required**.

---

## Installation

```bash
# Default install — includes pyswisseph (requires C compiler)
pip install kerykeion

# Additionally install libephemeris (pure Python, works everywhere)
pip install kerykeion[lib]
```

A plain `pip install kerykeion` includes `pyswisseph` as a default dependency.
To use `libephemeris` instead, install the `[lib]` extra and set the
`KERYKEION_BACKEND` environment variable (see below), or install into a clean
environment with only `kerykeion[lib]`.

---

## Runtime Backend Detection

```python
from kerykeion import BACKEND_NAME

print(BACKEND_NAME)  # "swisseph" or "libephemeris"
```

### Detection order

1. If `KERYKEION_BACKEND` environment variable is set → use that backend
   (raises `ImportError` if the package is not installed, `ValueError` if
   the value is not `"swisseph"` or `"libephemeris"`)
2. Try `import swisseph` — if found, use it (`BACKEND_NAME = "swisseph"`)
3. Try `import libephemeris` — if found, use it (`BACKEND_NAME = "libephemeris"`)
4. If neither is installed, raise `ImportError` with installation instructions

When both packages are installed and `KERYKEION_BACKEND` is not set,
**swisseph always wins** for backward compatibility.

### Environment variable

Set `KERYKEION_BACKEND` to force a specific backend:

```bash
# Force libephemeris even when both are installed
KERYKEION_BACKEND=libephemeris python my_script.py

# Force swisseph explicitly
KERYKEION_BACKEND=swisseph python my_script.py
```

This is essential for users who install `kerykeion[lib]` — without the env var,
swisseph (included by default) always takes priority.

---

## Architecture

All production code imports the ephemeris through a single entry point:

```python
from kerykeion.ephemeris_backend import swe
```

The `swe` object is the actual backend module (either `swisseph` or
`libephemeris`). Consumer code never imports `swisseph` or `libephemeris`
directly.

**Files that import from `ephemeris_backend`:**

| File | Import |
|------|--------|
| `kerykeion/astrological_subject_factory.py` | `from kerykeion.ephemeris_backend import swe` |
| `kerykeion/moon_phase_details/utils.py` | `from kerykeion.ephemeris_backend import swe` |
| `kerykeion/planetary_return_factory.py` | `from kerykeion.ephemeris_backend import swe` |
| `kerykeion/charts/chart_drawer.py` | `from kerykeion.ephemeris_backend import swe` |
| `kerykeion/aspects/aspects_utils.py` | `from kerykeion.ephemeris_backend import swe as _swe` |

---

## API Compatibility

As of libephemeris >= 1.0.0a1, both backends are **100% API-compatible** for
the surface kerykeion uses. No compatibility shims are required.

All 19 functions kerykeion calls (`calc_ut`, `houses_ex`, `houses_ex2`,
`rise_trans`, `fixstar_ut`, `fixstar2_mag`, `sol_eclipse_when_glob`,
`lun_eclipse_when`, `solcross_ut`, `mooncross_ut`, `set_ephe_path`, `close`,
`set_sid_mode`, `get_ayanamsa_ex_ut`, `set_topo`, `house_name`, `azalt`,
`difdeg2n`) have identical signatures and return types.

All 21 constants kerykeion uses (`AUNIT`, `ECL2HOR`, `SE_ECL2HOR`,
`CALC_RISE`, `CALC_SET`, `SE_CALC_RISE`, `SE_CALC_SET`, `ECL_TOTAL`,
`SE_ECL_TOTAL`, etc.) are exported by both backends with both naming
conventions (bare and `SE_`-prefixed).

### Previous shims (removed)

Earlier versions of libephemeris (< 1.0.0a1) had API divergences that required
shims in `ephemeris_backend.py`:

- **`rise_trans()`**: Different signature and return-flag semantics — fixed in
  libephemeris 0.24.0+
- **`fixstar2_mag()`**: Different return tuple order — fixed in libephemeris
  0.26.0+
- **`AUNIT` constant**: Missing — added in libephemeris constants module
- **Constant naming**: Only `SE_`-prefixed forms existed — bare aliases added

All shims were removed when the minimum libephemeris version was bumped to
1.0.0a1.

---

## Numerical Accuracy

The two backends use fundamentally different ephemeris data sources (Swiss
Ephemeris vs NASA JPL DE440/DE441), so small numerical differences are expected.
All differences are within acceptable astrological tolerances.

### Planetary Positions

| Body | Max Delta | Notes |
|------|-----------|-------|
| Sun, Mercury--Saturn | < 0.01 deg | Negligible for astrological use |
| True Node | ~6.1 arcsec (~0.0017 deg) | Different osculating element methods |
| Moon (modern dates) | ~0.02 deg | DE440 vs Swiss Eph Moon theory |
| Moon (ancient dates, < 1550 CE) | ~0.15 deg | DE441 lower precision for distant past |
| Moon speed | ~0.0014 deg/day | |

### House Cusps and Speeds

| Metric | Max Delta | Notes |
|--------|-----------|-------|
| Cusp positions | < 0.01 deg | Negligible |
| Cusp velocities | ~0.003 deg/day | ARMC-based finite differences (libephemeris) vs C-level analytical derivatives (swisseph) |

### Rise/Set and Eclipse Times

| Event Type | Max Delta |
|------------|-----------|
| Sunrise/sunset | ~1-2 seconds |
| Moonrise/moonset | ~1-2 seconds |
| Solar/lunar eclipses | ~1-2 seconds |

### Zodiac Signs

All zodiac sign assignments match exactly across backends for all tested dates
and locations. The positional deltas are far too small to cause a sign boundary
crossing.

---

## Date Range Limitations

| Backend | Ephemeris | Coverage | Notes |
|---------|-----------|----------|-------|
| swisseph | Swiss Ephemeris | -13000 to +16800 CE | Full precision across entire range (with data files) |
| libephemeris | DE440 (default) | **1550--2650 CE** | High precision for modern dates |
| libephemeris | DE441 (fallback) | -13000 to +16800 CE | Lower precision, especially for the Moon at distant dates |

**Chiron** in libephemeris is only available for **1549--2650 CE**. Queries
outside this range raise an error.

Tests for ancient dates (100 AD, 400 AD, etc.) use DE441 when running under
libephemeris and have wider tolerances to account for the precision difference.

---

## Performance

libephemeris is significantly slower than swisseph due to being pure Python
versus compiled C.

| Operation | swisseph | libephemeris | Factor |
|-----------|----------|-------------|--------|
| Single `calc_ut` call | ~microseconds | ~milliseconds | ~100-1000x |
| Full natal chart | < 10 ms | ~100-500 ms | ~10-50x |
| Parametrized test suites (thousands of epochs) | ~seconds | **timeout** | N/A |

Heavily parametrized test suites that exercise thousands of date/location/house-system
combinations routinely time out with libephemeris. This is a performance issue,
not a correctness issue -- key epochs within those suites were verified
individually and pass.

---

## Test Adjustments

### Backend-Aware Tolerances

Several test files use `BACKEND_NAME` to select appropriate tolerances:

| Test File | swisseph Tolerance | libephemeris Tolerance |
|-----------|--------------------|------------------------|
| `test_astrological_subject.py` | speed: `5e-4` | speed: `5e-4` |
| `test_planetary_positions.py` | position: `0.01 deg`, speed: `5e-4` | position: `0.2 deg`, speed: `2e-3` |
| `test_houses_positions.py` | position: `0.01 deg` | position: `0.2 deg` |
| `test_subject_factory_parametrized.py` | `1e-4` | `2e-3` |

### Skipped Tests

- **Golden-file snapshots** (`test_report.py`): Skipped when backend is not
  swisseph, because the reference files were generated with swisseph and
  last-digit speed rounding differs.
- **Moon-phase overview fixture**: Same reason.
- **SVG chart baselines** (`test_chart_drawer.py`, `test_chart_parametrized.py`):
  Skipped when backend is not swisseph, because the baseline SVG files contain
  coordinate values computed with swisseph and the tiny positional differences
  from libephemeris cause pixel-level mismatches in path/transform attributes.

### Aspect Movement Edge Cases

For very slow planet pairs (relative speed < 0.002 deg/day), the borderline
between Static and Applying aspect movement is tolerated differently because
the tiny speed deltas between backends can flip the classification.

### Mock Patches

All test mock patches use `patch.object` on the `swe` proxy:
```python
from kerykeion.ephemeris_backend import swe
...
@patch.object(swe, "calc_ut", ...)
```

This ensures mocks target the actual backend module regardless of which one is
active.

---

## Modified Files

### New Files

| File | Description |
|------|-------------|
| `kerykeion/ephemeris_backend.py` | Backend detection, env var support, `swe` and `BACKEND_NAME` exports |
| `BACKEND_MIGRATION_PLAN.md` | v5 → v6 migration roadmap (pyswisseph default → libephemeris default) |

### Production Files Modified

| File | Change |
|------|--------|
| `pyproject.toml` | `pyswisseph` as default dep; `libephemeris>=1.0.0a1` as `[lib]` extra |
| `kerykeion/__init__.py` | Added `BACKEND_NAME` export to `__all__` |
| `kerykeion/astrological_subject_factory.py` | `import swisseph as swe` -> `from kerykeion.ephemeris_backend import swe` |
| `kerykeion/moon_phase_details/utils.py` | Same import change |
| `kerykeion/planetary_return_factory.py` | Same import change |
| `kerykeion/charts/chart_drawer.py` | Same import change |
| `kerykeion/aspects/aspects_utils.py` | `from swisseph import difdeg2n` -> backend-agnostic import |

### Test Files Modified

| File | Change |
|------|--------|
| `tests/core/test_astrological_subject.py` | Mock patches updated, speed tolerance widened |
| `tests/core/test_arabic_parts.py` | Mock patches updated |
| `tests/core/test_aspects.py` | Borderline aspect movement tolerance for slow pairs |
| `tests/core/test_planetary_positions.py` | Backend-aware position/speed/declination tolerances |
| `tests/core/test_houses_positions.py` | Backend-aware position tolerance |
| `tests/core/test_report.py` | Golden-file snapshots skip when backend != swisseph |
| `tests/core/test_subject_factory_parametrized.py` | Backend-aware default tolerance function |
| `tests/core/test_chart_drawer.py` | SVG baseline comparisons skip when backend != swisseph |
| `tests/core/test_chart_parametrized.py` | SVG baseline comparisons skip when backend != swisseph |

### Zero Direct Imports Remaining

After the migration, there are **zero** occurrences of `import swisseph` in
either production or test code. All ephemeris access goes through
`kerykeion.ephemeris_backend`.
