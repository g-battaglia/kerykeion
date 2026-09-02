---
title: 'Ephemeris Backend'
category: 'Reference'
description: 'Configuration and comparison of libephemeris and Swiss Ephemeris backends.'
tags: ['docs', 'backend', 'ephemeris', 'libephemeris', 'swisseph']
order: 20
---

# Ephemeris Backend

Kerykeion supports two selectable ephemeris backends. All astrological
calculations go through a single adapter module (`kerykeion.ephemeris_backend`)
that selects the active engine at import time. Kerykeion's core chart APIs stay
the same when switching, while backend-specific body/date coverage, fixed-star
setup, and some search directions can differ.

## Backends

| Backend | Package | License | Notes |
|---------|---------|---------|-------|
| **libephemeris** (default) | `libephemeris` | AGPL-3.0 | Pure Python. Uses NASA JPL DE440/DE441 data via LEB/Skyfield. No C compiler needed. Owned by the Kerykeion project. |
| **swisseph** | `pyswisseph` | AGPL-3.0 | C bindings to the Swiss Ephemeris library by Astrodienst AG. If you use this backend, the Swiss Ephemeris AGPL-3.0 license applies. |

## Installation

```bash
# Default (libephemeris only -- no C compiler needed)
pip install kerykeion

# Swiss Ephemeris backend (requires C compiler)
pip install kerykeion[swiss]

# Both backends (needed for comparison tests)
pip install kerykeion[all]
```

## Configuration

All configuration is done through environment variables. No code changes needed.

### `KERYKEION_BACKEND`

Force a specific backend. When unset, auto-detection tries `libephemeris`
first, then `swisseph`.

```bash
KERYKEION_BACKEND=swisseph python my_script.py
KERYKEION_BACKEND=libephemeris python my_script.py
```

### `KERYKEION_EPHE_PATH`

Override the directory where ephemeris data files are loaded from.
Default: empty string (libephemeris manages its own data internally via
`~/.libephemeris/leb/`; swisseph falls back to its built-in Moshier
analytical ephemeris).

```bash
# For swisseph: point to a directory containing .se1 files
KERYKEION_EPHE_PATH=/path/to/se1/files python my_script.py

# For libephemeris: typically not needed (uses ~/.libephemeris/leb/)
KERYKEION_EPHE_PATH=/path/to/custom/data python my_script.py
```

Both backends call `ephe.set_ephe_path(EPHE_DATA_PATH)` at init time.
For swisseph this points to `.se1` files; for libephemeris the call is
a no-op (it manages its own data directory internally).

### `KERYKEION_LEB_MODE`

*Only applies when libephemeris is the active backend.*

Controls the calculation pipeline. Default: `"leb"` (mandatory `.leb` files).

| Value | Behavior |
|-------|----------|
| `leb` | **Require** precomputed `.leb` binary files. Raises `RuntimeError` if none found. Fastest (~14x vs Skyfield). This is the default. |
| `auto` | Use `.leb` if available, fall back to Skyfield/DE440. |
| `skyfield` | Always use Skyfield/DE440 (requires local DE440 file or download). |
| `horizons` | Use NASA JPL Horizons API (requires internet). |

```bash
KERYKEION_LEB_MODE=auto python my_script.py
```

The mode is applied with `set_calc_mode()` at import time, and in the default
`leb` mode Kerykeion additionally pins `set_network_policy("sealed")`. Both
calls override whatever libephemeris read from its own `LIBEPHEMERIS_MODE` /
`LIBEPHEMERIS_NETWORK_POLICY` variables, so setting those has no effect on a
Kerykeion process — use `KERYKEION_LEB_MODE`. `reset_ephemeris_session()`
re-applies the pinned mode after every reset, since a reset would otherwise
leave the session in `auto` and silently re-enable the Skyfield fallback.

### `LIBEPHEMERIS_PRECISION`

*Only applies when libephemeris is the active backend.*

Selects the ephemeris tier — `base`, `medium` or `extended` — and therefore the
date range that can be computed. Unset, libephemeris auto-detects the widest
tier the installed kernel can serve. A date outside the active range raises
`KerykeionException`; sealed `leb` mode does not substitute a lower-precision
source.

```bash
LIBEPHEMERIS_PRECISION=extended python my_script.py
```

#### Installing `.leb` files

`.leb` files contain precomputed Chebyshev polynomial approximations and
live in `~/.libephemeris/leb/`. Download them with:

```python
# doc-snippet: no-run — downloads ephemeris kernels
from libephemeris import download_leb_for_tier

# Every tier installs the SAME 14-body core (Sun-Pluto, Earth,
# Mean/True Node, Mean Apogee). Tiers differ by DATE RANGE, not by
# which bodies the core contains.
download_leb_for_tier("base")      # 1850-2150 (DE440s), ~31 MB, bundled
download_leb_for_tier("medium")    # 1550-2650 (DE440), ~114 MB
download_leb_for_tier("extended")  # -13200 to +17191 (DE441), ~3.1 GB
```

The authoritative table is `libephemeris.list_tiers()`, which reports each
tier's name, kernel file, range and size.

Asteroids (Chiron, Ceres, Pallas, Juno, Vesta), other curated minor
bodies and exotics (centaurs, trans-Neptunians), and lunar apsides are
**separate companion groups**, available at every tier — they are not
folded into the core by tier. Install them alongside the core with
`download_leb2_for_tier`, which lives in `libephemeris.download` rather than at
the package root:

```python
# doc-snippet: no-run — downloads ephemeris kernels
from libephemeris.download import download_leb2_for_tier

download_leb2_for_tier("medium", groups=["core", "asteroids"])
```

`download_leb2_for_tier(tier_name, groups=None, force=False, show_progress=True,
quiet=False, activate=True)`; the group names are `core`, `asteroids`, `exotics`
and `apogee` (`libephemeris.leb_groups.LEB2_GROUPS`), and `groups=None` installs
all of them.

The Hamburg/Uranian points and the White Moon need **no files at all**: they are
fictitious bodies, always computed from their runtime analytical models
(provenance `source="Analytical"`), at every tier and for every date.

## Architecture

```
Application code
       |
       v
kerykeion.ephemeris_backend   <-- single import point
       |
       +-- ephe = <module>    (swisseph OR libephemeris, selected at import)
       +-- BACKEND_NAME       ("swisseph" or "libephemeris")
       +-- EPHE_DATA_PATH     (resolved data directory)
       |
       v
29 consumer modules           <-- from kerykeion.ephemeris_backend.backend
                                  import ephe, ephemeris_session
```

### Package Exports

`kerykeion.ephemeris_backend.__all__`:

| Name | What it is |
| :-- | :-- |
| `ephe` | The selected backend module itself (`libephemeris` or `swisseph`). |
| `BACKEND_NAME` | `"libephemeris"` or `"swisseph"`. |
| `EPHE_DATA_PATH` | Resolved ephemeris data directory. |
| `EPHEMERIS_LOCK` | The lock every backend call is serialized behind. |
| `ephemeris_session` | Context manager: takes the lock, applies zodiac/sidereal/perspective/topocentric configuration, yields the `iflag`, resets and releases on exit. |
| `reset_ephemeris_session` | Resets per-calculation backend state and re-pins the calc mode. Callers must hold `EPHEMERIS_LOCK`; never call `ephe.close()` directly. |
| `houses_ex2_with_polar_fallback` | House cusps with the polar substitution applied. |
| `houses_ex2_with_polar_fallback_ex` | Same, also returning the fallback record. |
| `houses_ring_with_polar_fallback` | Cusp ring variant for the 36-sector Gauquelin grid. |
| `HouseRing` | Return type of the ring helper. |
| `POLAR_HOUSES_ERROR_TYPES` | Backend exception types that mean "undefined at this latitude". |
| `DEFAULT_SWEPH_DOWNLOAD_DIR` | Where the Swiss Ephemeris data files are looked for. |

The polar helpers are the only supported way to compute houses above the polar
circle.

**Key design decisions:**

1. **Direct module re-export, not an adapter class.** The overlapping ephemeris
   API used by Kerykeion is exposed through a module alias with zero overhead.
   No wrapper, proxy, or method interception is involved; callers that use
   backend-specific functions must still account for their differences.

2. **Selection at import time.** The backend is resolved once when
   `kerykeion.ephemeris_backend` is first imported. All subsequent `ephe.*`
   calls go directly to the backend module with no indirection.

3. **Environment variables only.** No Python API to switch backends at runtime.
   This keeps the code simple and prevents accidental state corruption
   mid-calculation. Restart the process to switch.

## Detecting the Active Backend

```python
from kerykeion import BACKEND_NAME

print(BACKEND_NAME)  # "libephemeris" or "swisseph"

if BACKEND_NAME == "libephemeris":
    print("Using pure-Python backend")
```

## Licensing and Dual-License Strategy

The backend abstraction gives Kerykeion one calculation surface across two
dependencies with different licenses:

- **libephemeris** is licensed under AGPL-3.0.
- **swisseph** (Swiss Ephemeris) is licensed under AGPL-3.0 by Astrodienst AG.
  If you use this backend, the Swiss Ephemeris license terms apply to
  those components.

Users who install the `[swiss]` extra do so knowingly and accept the
AGPL-3.0 terms of Astrodienst AG for the Swiss Ephemeris components.

## Testing

Three parallel test suites verify backend correctness:

```bash
# Run all core tests with libephemeris (default backend)
poe test:lib

# Run identical core tests with swisseph
poe test:swe

# Cross-backend comparison: same calculations, both engines,
# assert results match within tolerance (requires both installed)
poe test:compare
```

The `test:lib` and `test:swe` suites are **identical** -- same test files,
same assertions. The only difference is the `KERYKEION_BACKEND` environment
variable.

Golden-file tests do **not** use a loose numeric tolerance. For SVG baselines
(`tests/data/compare_svg_lines.py`) the contract has two halves:

- **Structure is fatal on both backends.** Line count, the count of numbers per
  line, and each line with its numbers blanked out must match the baseline
  exactly, or the test fails and names the line.
- **Numbers are compared only on `libephemeris`**, the backend the baselines
  were generated with, at `abs_tol = 1e-4` with no relative component. A DMS
  label printed to the second cannot move by less than 2.78e-4, so any flipped
  label is rejected. On the other backend the structural assertions still run in
  full and the test then reports SKIPPED with a reason — not compared is not the
  same as compared and equal.

Report snapshots (`tests/core/test_report.py`) apply the same shape: line count
and the non-numeric skeleton must match exactly, and numbers are compared at
`abs_tol = 0.01`, which absorbs display-rounding flips of the last printed
decimals and nothing more.

### Numerical Differences

Both backends are astronomically valid. Small differences arise from
different ephemeris sources and algorithms:

| Metric | Typical delta | Cause |
|--------|---------------|-------|
| Planetary longitudes | < 0.02 deg | Swiss Eph vs NASA JPL DE440 |
| House cusps | < 0.01 deg | Negligible |
| Planet speeds | < 0.01 deg/day | Analytical vs finite differences |
| True Node | ~ 6 arcsec | Different osculating element methods |
| Zodiac signs | Agreement in the maintained matrix | A boundary-adjacent delta can change the label |
| Retrograde status | Agreement in the maintained matrix | A near-stationary speed can be boundary-sensitive |

## Debug: Backend Source Tracing

To see which specific backend (LEB, Skyfield, SPK, Horizons, ASSIST,
Keplerian) computed each celestial body, enable DEBUG-level logging on
the `"libephemeris"` logger:

```bash
LIBEPHEMERIS_LOG_LEVEL=DEBUG python my_script.py
```

This emits log lines like `body=0 jd=2448045.9 source=LEB` at every
dispatch point. See the libephemeris
[testing documentation](https://github.com/g-battaglia/libephemeris)
for the full list of source values.

When using the **Astrologer API**, the same information is available via the
opt-in `X-Debug-Ephemeris: true` HTTP header, which injects an
`_ephemeris_debug.backends` map into the JSON response. See the API's
[ephemeris debug documentation](https://github.com/g-battaglia/Astrologer-API)
for details.
