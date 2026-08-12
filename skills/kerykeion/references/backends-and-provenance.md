# Ephemeris backends and provenance

Source of truth: the `kerykeion/ephemeris_backend/` package (`backend.py` behind
the `kerykeion/ephemeris_backend/__init__.py` facade). Kerykeion never imports
`swisseph`/`libephemeris` directly — every internal call goes through the single
`ephe` object exposed there, so both backends present the same API. This file
also owns the a75 provenance contract (`source`, `precision_class`, coverage
window, `source_reviewed` on `KerykeionPointModel`) and the sealed-range rules
that decide whether an out-of-range date raises or lands in
`subject.ephemeris_warnings`.

## The two backends

| | `libephemeris` (default) | `swisseph` (`pyswisseph`) |
|---|---|---|
| Install | bundled by `pip install kerykeion` | `pip install "kerykeion[swiss]"` |
| Engine | NASA JPL DE440/DE441 via Skyfield + precomputed `.leb` binary files | Swiss Ephemeris C library |
| Compiler | none (pure Python) | C bindings |
| Data files | manages its own (`~/.libephemeris/leb/`) | needs `.se1`; else falls back to Moshier (lower precision) |
| Provenance metadata on points | **populated** (`source`, `precision_class`, coverage, `source_reviewed`) | always `None` |
| `ephemeris_warnings` | populated | only the backend-agnostic codes |
| License | AGPL-3.0 (Kerykeion project) | AGPL-3.0 (Astrodienst AG), third-party |

Auto-detection (when `KERYKEION_BACKEND` is unset) tries `libephemeris` first,
then `swisseph`. A backend that is installed-but-broken is logged and skipped
rather than silently swapped; if neither imports, `ImportError` with install
lines.

```python
from kerykeion import BACKEND_NAME    # top-level re-export: "libephemeris" | "swisseph"

subject = AstrologicalSubjectFactory.from_birth_data(
    name="Example Person", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", city="Rome", nation="IT",
    online=False)
print(BACKEND_NAME)
# Provenance fields (libephemeris only; all None on swisseph):
p = subject.sun
print(p.source, p.precision_class, p.source_reviewed)          # e.g. LEB ephemeris True
print(p.ephemeris_coverage_start_jd, p.ephemeris_coverage_end_jd)
print(subject.ascendant.source)   # None — house-geometry points carry no provenance
```

## Environment variables

- **`KERYKEION_BACKEND`** = `libephemeris` | `swisseph`. Forces the backend.
  Invalid value → `ValueError` at import; forced-but-not-installed →
  `ImportError` with the exact `pip install` line; installed-but-broken →
  `ImportError` chaining the real cause.
- **`KERYKEION_LEB_MODE`** (libephemeris only) = `leb` (default) | `auto` |
  `skyfield` | `horizons`. Invalid value → `ValueError` at import.
  - `leb` — require `.leb` files AND enforce the **sealed** network policy
    (`set_network_policy("sealed")`): a clear failure beats a silent
    download/degrade. This is the shipped default.
  - `auto` — LEB if available, else Skyfield/DE440 (may download).
  - `skyfield` — always Skyfield/DE440.
- **`KERYKEION_EPHE_PATH`** — ephemeris data directory. libephemeris: a no-op
  (manages its own data). swisseph: point it at a directory of `.se1` files;
  without it the default download dir of `python -m kerykeion.swisseph_setup`
  (`DEFAULT_SWEPH_DOWNLOAD_DIR`, `~/.kerykeion/sweph`) is auto-detected, else
  swisseph uses its internal Moshier ephemeris with a logged warning.
- **`KERYKEION_GEONAMES_USERNAME`** — GeoNames username for `online=True`
  lookups (see `references/subjects.md`); not an ephemeris variable.
- **`LIBEPHEMERIS_PRECISION` is NOT a kerykeion variable.** Kerykeion never
  reads it. It is libephemeris' own tier-selection knob (used e.g. when
  regenerating golden baselines); do not document or set it expecting kerykeion
  behavior to change.

## Sealed LEB mode — what calling code must handle

In the default `leb` mode the backend will not reach the network and will not
silently substitute a lower-precision source. Consequences:

1. **Out-of-range dates raise instead of degrading.** A fresh install ships
   only **1849–2150** (JPL DE440s). The medium LEB core covers
   `[1550-01-01, 2650-01-01)` = JD `[2287185.5, 2688952.5)` — upper bound
   **exclusive**. Past the loaded coverage the backend raises the typed
   `EphemerisRangeError` — a **libephemeris** exception, NOT re-exported by
   kerykeion (`from libephemeris import EphemerisRangeError` if you must catch
   it; kerykeion code usually catches broad backend errors via
   `getattr(ephe, "EphemerisRangeError", None)`).
2. **Luminaries vs optional bodies.** A failed Sun or Moon raises
   `KerykeionException` (a chart without them is unusable). Any other body
   (Chiron, asteroids, TNOs, White Moon, …) degrades gracefully: it is removed
   from `active_points` and a structured record is appended to
   `subject.ephemeris_warnings`.
3. **Provenance is real, not decorative** — the source recorded on each point
   is the one that actually produced the number (see below).

Widen coverage before charting deep-past/future dates:

```python
# doc-snippet: no-run  (network download)
import libephemeris
libephemeris.download_leb_for_tier("medium")     # 1550–2650 (through 2649-12-31)
libephemeris.download_leb_for_tier("extended")   # full range, incl. BCE
```

## `subject.ephemeris_warnings`

A list of `EphemerisWarningModel` (deduplicated on code+point+body+JD). Fields:
`code`, `point_name`, `body_id`, `requested_jd`, `message`,
`coverage_start_jd` / `coverage_end_jd` (advisory, from the backend's
date-aware `get_body_coverage(body_id, jd)` when available, else `None`).
Codes: `date_outside_ephemeris_coverage`, `ephemeris_calculation_failed`,
`unsupported_by_backend` (e.g. White Moon on swisseph, which has no body 56 —
kerykeion refuses to fabricate it). Backend exception text stays in the log,
never in the model.

Within the sealed range nothing warns — the empty list is the normal case:

```python
s = AstrologicalSubjectFactory.from_birth_data(
    name="Old Chart", year=1855, month=3, day=10, hour=6, minute=0,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
    active_points=["Sun", "Moon", "Chiron", "Sedna", "Ascendant"])
for w in s.ephemeris_warnings:            # empty on a default install: 1855 is
    print(w.code, w.point_name, w.message)  # inside the sealed 1849-2150 window
print(len(s.ephemeris_warnings), s.chiron.source)   # 0 LEB
```

## Provenance contract on `KerykeionPointModel` (a75, libephemeris only)

| Field | Meaning |
|---|---|
| `source` | Source label actually used: `"LEB"`, `"SPK"`, `"Skyfield"`, `"Keplerian"`, `"ASSIST"`, `"Analytical"`, `"Derived"`, … **Open set — never match exhaustively** |
| `precision_class` | `ephemeris`, `analytical`, `approximate`, `numerical-model`, `mixed`, `unverified-local` |
| `ephemeris_coverage_start_jd` / `ephemeris_coverage_end_jd` | backend-reported coverage window (JD) for the selected source |
| `source_reviewed` | whether the active source artifact passed the backend's pinned review gate |

- `"Keplerian"` is **NORMAL** for default points: it is what any body returns
  when it falls outside its LEB coverage (e.g. Chiron on a deep-past chart →
  `source="Keplerian"`, `precision_class="approximate"`). Exhaustive matches
  on `source` values will break.
- Uranian/Hamburg bodies (Cupido…Poseidon) and White Moon are **invariantly**
  `source="Analytical"` (runtime analytical model, never LEB); coverage and
  `source_reviewed` stay `None` for them.

`source` → `precision_class` coarse mapping (case-insensitive):

| source label | precision_class |
|---|---|
| `Keplerian*` | `approximate` |
| `Analytical*` | `analytical` |
| `LEB`, `SPK`, `Skyfield` | `ephemeris` |
| anything else (e.g. `ASSIST`, the live n-body fallback) | `numerical-model` |

Unrecognized labels are never promoted to `ephemeris`. For `source == "LEB"`
the backend's per-body coverage class then **overrides** the coarse value, and
the coverage window + `source_reviewed` are filled from
`get_body_coverage(body_id, jd)`.

```python
s = AstrologicalSubjectFactory.from_birth_data(
    name="Classes", year=1990, month=7, day=15, hour=10, minute=30,
    lng=12.4964, lat=41.9028, tz_str="Europe/Rome", online=False,
    active_points=["Sun", "True_North_Lunar_Node", "Cupido", "Ascendant"])
print(s.sun.precision_class)                    # ephemeris (LEB)
print(s.true_north_lunar_node.precision_class)  # analytical (nodes: analytical model)
print(s.cupido.source, s.cupido.precision_class)  # Analytical analytical
```

### Derived points and intentional gaps

- **Antipodes** (Descendant, Imum Coeli, South Nodes, Priapus, Anti-Vertex):
  `source="Derived"`, everything else inherited from the single primary.
- **Arabic parts**: `source="Derived"`; `precision_class` collapses to
  `"mixed"` when the formula primaries disagree; coverage window is the
  **intersection** (max start, min end); `source_reviewed` is the AND of the
  primaries' flags.
- **Intentionally `None`** (no per-body coverage inventory): house-geometry
  points — Ascendant, Medium Coeli, house cusps, Vertex (their honesty channel
  is `polar_house_fallbacks`, see `references/zodiac-houses-perspectives.md`);
  and **everything on the swisseph backend**. Fixed stars are the partial
  case: `source`/`precision_class` are set when a single trace label answered
  for the star, but coverage and `source_reviewed` always stay `None`.
  There is no "every point has provenance" guarantee.

## Swiss Ephemeris setup

```bash
# doc-snippet: no-run
pip install "kerykeion[swiss]"
python -m kerykeion.swisseph_setup          # downloads .se1 into ~/.kerykeion/sweph
export KERYKEION_BACKEND=swisseph
# optionally: export KERYKEION_EPHE_PATH=/path/to/se1files
```

`python -m kerykeion.swisseph_setup` still works post-refactor
(`kerykeion/swisseph_setup/` is a package with a `__main__.py`). Without `.se1`
files swisseph runs on the Moshier analytical ephemeris (warning logged,
precision drops). Fixed stars on swisseph additionally need `sefstars.txt` in
`KERYKEION_EPHE_PATH` (not bundled; a single actionable warning is logged when
every requested star fails).

## The ephemeris_backend package facade

**Subpackage import:** `from kerykeion.ephemeris_backend import ephe, BACKEND_NAME, EPHE_DATA_PATH, EPHEMERIS_LOCK, ephemeris_session, reset_ephemeris_session, DEFAULT_SWEPH_DOWNLOAD_DIR, POLAR_HOUSES_ERROR_TYPES, houses_ex2_with_polar_fallback, houses_ex2_with_polar_fallback_ex`

| Name | What it is |
|---|---|
| `ephe` | the backend module object itself; `ephe.calc_ut(jd, body, iflag)`, `ephe.houses_ex2(...)`, same API on both backends |
| `BACKEND_NAME` | `"libephemeris"` or `"swisseph"` (also re-exported at top level) |
| `EPHE_DATA_PATH` | resolved data path (`""` on libephemeris / when unset) |
| `EPHEMERIS_LOCK` | `threading.RLock` guarding the backend's mutable global state |
| `ephemeris_session(...)` | serialized, self-cleaning session context manager (below) |
| `reset_ephemeris_session()` | reset per-calc state, re-pin the LEB calc mode; callers must hold `EPHEMERIS_LOCK`; never call `ephe.close()` directly |
| `DEFAULT_SWEPH_DOWNLOAD_DIR` | target of `python -m kerykeion.swisseph_setup` |
| `POLAR_HOUSES_ERROR_TYPES` | exception types meaning "house system undefined inside the polar circle" (libephemeris `PolarCircleError`; swisseph generic `Error`) |
| `houses_ex2_with_polar_fallback(tjdut, lat, lon, hsys, flags, *, context="")` | cusps with polar substitution, returns 4-tuple `(cusps, ascmc, cusps_speed, ascmc_speed)` |
| `houses_ex2_with_polar_fallback_ex(..., polar_strategy="substitute_system")` | same plus a 5th element: the `PolarHouseFallbackModel` record or `None` |

### Sessions (advanced)

`ephemeris_session(*, zodiac_type=None, sidereal_mode=None, custom_ayanamsa_t0=None, custom_ayanamsa_ayan_t0=None, perspective_type=None, topo=None, ephe_path=None)`
is the only supported way to touch process-global ephemeris state (sidereal
mode, topocentric coords). It acquires `EPHEMERIS_LOCK`, yields the base
`iflag` (`FLG_SWIEPH | FLG_SPEED` plus perspective/sidereal flags), and resets
on exit. **Same-thread nesting raises `RuntimeError`** before the inner call
can corrupt the outer session's state — never build a subject or call another
factory inside an open session. Unknown zodiac/perspective names raise
`ValueError`. Planetocentric names are accepted but set no flag: fetch those
positions via `ephe.calc_pctr` (TT Julian Day) as the factories do.

```python
from kerykeion.ephemeris_backend import ephe, ephemeris_session
with ephemeris_session(zodiac_type="Sidereal", sidereal_mode="LAHIRI") as iflag:
    lon = ephe.calc_ut(2448088.0, ephe.SUN, iflag)[0][0]   # sidereal longitude
print(round(lon, 3))
```

Most code never needs sessions: the factories open their own.
