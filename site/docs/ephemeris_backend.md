# Ephemeris Backend

Kerykeion supports two interchangeable ephemeris backends. All astrological
calculations go through a single adapter module (`kerykeion.ephemeris_backend`)
that selects the active engine at import time. Both backends expose an identical
API so **no application code needs to change** when switching.

## Backends

| Backend | Package | License | Notes |
|---------|---------|---------|-------|
| **libephemeris** (default) | `libephemeris` | AGPL-3.0 | Pure Python. Uses NASA JPL DE440/DE441 via Skyfield. No C compiler needed. Owned by the Kerykeion project -- safe for dual-licensing. |
| **swisseph** | `pyswisseph` | GPL-2.0 | C bindings to the Swiss Ephemeris library. Fastest option. GPL license restricts commercial redistribution. |

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
Default: the `kerykeion/sweph/` directory bundled with the package.

```bash
# Use a custom data directory (SPK files, star catalogs, etc.)
KERYKEION_EPHE_PATH=/Volumes/Data/libephemeris python my_script.py
```

Both backends call `swe.set_ephe_path(EPHE_DATA_PATH)` at init time.
For swisseph this points to `.se1` files; for libephemeris it scans
for `.bsp` (SPK) files in the directory.

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

#### Installing `.leb` files

`.leb` files contain precomputed Chebyshev polynomial approximations and
live in `~/.libephemeris/leb/`. Download them with:

```python
from libephemeris import download_leb_for_tier
download_leb_for_tier("base")      # Essential planets, ~2 MB
download_leb_for_tier("medium")    # + minor bodies, ~10 MB
download_leb_for_tier("extended")  # + asteroids, ~50 MB
```

## Architecture

```
Application code
       |
       v
kerykeion.ephemeris_backend   <-- single import point
       |
       +-- swe = <module>     (swisseph OR libephemeris, selected at import)
       +-- BACKEND_NAME       ("swisseph" or "libephemeris")
       +-- EPHE_DATA_PATH     (resolved data directory)
       |
       v
16 factory modules            <-- all import: from kerykeion.ephemeris_backend import swe
```

**Key design decisions:**

1. **Direct module re-export, not an adapter class.** Both backends are 100%
   API-compatible (as of libephemeris >= 1.0.0a4), so the adapter is just a
   module alias with zero overhead. No wrapper, no proxy, no method interception.

2. **Selection at import time.** The backend is resolved once when
   `kerykeion.ephemeris_backend` is first imported. All subsequent `swe.*`
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

The backend abstraction exists primarily to protect the project's ability
to offer **dual licensing** (AGPL-3.0 + commercial):

- **libephemeris** is owned by the Kerykeion project and licensed under
  AGPL-3.0. It can be relicensed commercially without third-party approval.
- **swisseph** (Swiss Ephemeris) is licensed under GPL-2.0 by Astrodienst.
  Code that links to swisseph inherits the GPL, which prevents commercial
  redistribution without a separate Swiss Ephemeris commercial license.

By defaulting to libephemeris and making swisseph opt-in (`pip install
kerykeion[swiss]`), the base Kerykeion package is free of GPL dependencies.
Users who install the `[swiss]` extra do so knowingly and accept the GPL terms.

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
variable. Golden-file tests (SVG baselines, report snapshots) use numeric
tolerance (0.5 degrees) to accommodate the minor positional deltas between
backends.

### Numerical Differences

Both backends are astronomically valid. Small differences arise from
different ephemeris sources and algorithms:

| Metric | Typical delta | Cause |
|--------|---------------|-------|
| Planetary longitudes | < 0.02 deg | Swiss Eph vs NASA JPL DE440 |
| House cusps | < 0.01 deg | Negligible |
| Planet speeds | < 0.01 deg/day | Analytical vs finite differences |
| True Node | ~ 6 arcsec | Different osculating element methods |
| Zodiac signs | Identical | Deltas too small to cross boundaries |
| Retrograde status | Identical | Speed sign always agrees |
