# Ephemeris backends

Source of truth: `kerykeion/ephemeris_backend.py`. Kerykeion never imports
`swisseph`/`libephemeris` directly — every internal call goes through the single
`ephe` object exposed by that module, so both backends present the same API.

## The two backends

| | `libephemeris` (default) | `swisseph` (`pyswisseph`) |
|---|---|---|
| Install | bundled by `pip install kerykeion` | `pip install "kerykeion[swiss]"` |
| Engine | NASA JPL DE440/DE441 via Skyfield + precomputed `.leb` binary files | Swiss Ephemeris C library |
| Compiler | none (pure Python) | C bindings |
| Data files | manages its own (`~/.libephemeris/leb/`) | needs `.se1`; else falls back to Moshier (lower precision) |
| Provenance metadata on points | **populated** (`source`, `precision_class`, coverage, `source_reviewed`) | always `None` |
| License note | AGPL-3.0 (Kerykeion project) | AGPL-3.0 (Astrodienst AG), third-party |

Auto-detection (when `KERYKEION_BACKEND` is unset) tries `libephemeris` first,
then `swisseph`. A backend that is installed-but-broken is logged and skipped
rather than silently swapped.

Detect the active backend:

```python
from kerykeion import BACKEND_NAME              # top-level re-export
# or: from kerykeion.ephemeris_backend import BACKEND_NAME
```

## Environment variables

- **`KERYKEION_BACKEND`** = `libephemeris` | `swisseph`. Forces the backend.
  An invalid value raises `ValueError`; a forced-but-uninstalled backend raises
  `ImportError` with the exact `pip install` line.
- **`KERYKEION_LEB_MODE`** (libephemeris only) = `leb` (default) | `auto` |
  `skyfield` | `horizons`.
  - `leb` — require `.leb` files; **enforces the sealed network policy**
    (`set_network_policy("sealed")`). A clear failure beats a silent
    download/degrade. This is the shipped default.
  - `auto` — LEB if available, else Skyfield/DE440.
  - `skyfield` — always Skyfield/DE440.
  An invalid value raises `ValueError`.
- **`KERYKEION_EPHE_PATH`** — ephemeris data directory.
  - libephemeris: a no-op (it manages its own data).
  - swisseph: point it at a directory of `.se1` files. Without it, the default
    download dir of `python -m kerykeion.swisseph_setup` is auto-detected; if
    nothing is found, swisseph uses its internal Moshier ephemeris (a warning is
    logged, and precision drops).
- **`KERYKEION_GEONAMES_USERNAME`** — default GeoNames username for `online=True`.

## Sealed LEB mode — why it matters for calling code

In the default `leb` mode the backend is *sealed*: it will not reach the network
and will not silently substitute a lower-precision source. Two visible
consequences you must code for:

1. **Out-of-range dates raise instead of degrading.** The medium LEB core covers
   `[1550-01-01, 2650-01-01)` = JD `[2287185.5, 2688952.5)` (upper bound
   **exclusive**). A fresh install only ships 1849–2150 (DE440s). Past the loaded
   coverage you get a typed `EphemerisRangeError` for optional bodies (recorded in
   `subject.ephemeris_warnings`) or a `KerykeionException` for the luminaries.
   This changed in a75 — rc12 used to serve a silently substituted source.
2. **Provenance is real, not decorative.** Because the source was chosen under
   the sealed manifest, `point.source`, `point.precision_class`,
   `point.ephemeris_coverage_start_jd/_end_jd`, and `point.source_reviewed`
   describe what actually produced the number. `precision_class` for LEB bodies
   comes straight from the backend's date-aware `get_body_coverage(body_id, jd)`.

Widen coverage before charting deep-past/future dates:

```python
import libephemeris
libephemeris.download_leb_for_tier("medium")     # 1550–2650 (through 2649-12-31)
libephemeris.download_leb_for_tier("extended")   # full range, incl. BCE
```

## Precision-class values

`point.precision_class` (libephemeris only) is machine-readable, one of:
`ephemeris`, `analytical`, `approximate`, `numerical-model`, `mixed`,
`unverified-local`. The factory assigns a coarse class from the source name
(`keplerian*` → `approximate`, `analytical*` → `analytical`, else `ephemeris`),
then, for `source == "LEB"`, overrides it with the backend's per-body coverage
class. Derived points collapse multiple distinct classes to `mixed`.

## Swiss Ephemeris data setup

If you must use the C backend at full precision:

```bash
python -m kerykeion.swisseph_setup          # downloads .se1 into the default dir
export KERYKEION_BACKEND=swisseph
# optionally: export KERYKEION_EPHE_PATH=/path/to/se1files
```

Without `.se1` files swisseph still runs, but on the Moshier analytical
ephemeris — acceptable for rough work, not for precision comparisons.

## Sessions (advanced)

`ephemeris_session(...)` is the only supported way to touch process-global
ephemeris state (sidereal mode, topocentric coords). It serializes on a lock,
yields the `iflag`, and self-cleans on exit. **Same-thread nesting raises
`RuntimeError`** before the inner call corrupts the outer session's
sidereal/topocentric state — never build a subject or call another factory from
inside an open session. Most code never needs this directly; the factories open
their own sessions.
