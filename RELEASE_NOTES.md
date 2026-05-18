# Release Notes

## 6.0.0a42 — 2026-05-15

Updated `libephemeris` to 2.0.0.

Highlights:

- Upstream library simplified its public API by removing legacy prefixed
  aliases. The canonical bare-name API used by kerykeion (`calc_ut`,
  `houses`, `SUN`, `FLG_SPEED`, ...) is unchanged.
- Adds a new `libephemeris.contrib` submodule with extended astrology
  helpers (zodiac, nakshatra, aspect constants and functions).

No API changes. Backward-compatible.

## 6.0.0a41 — 2026-05-14

Updated `libephemeris` to 1.6.0 with critical LEB fast-path bug fixes.

Highlights:

- `lun_occult_when_loc()` no longer crashes in LEB mode (was
  `NameError: ts`).
- Heliacal calculations no longer fail after `close()` (was
  `TypeError` on closed mmap).
- `set_leb_file()` and `clear_caches()` now properly clean up stale
  LEB reader state.

No API changes. Backward-compatible.

## 6.0.0a40 — 2026-05-10

Clean ephemeris packaging and new Swiss Ephemeris setup utility.

Highlights:

- Swiss Ephemeris data files are no longer shipped in the wheel. The
  default backend (`libephemeris`) works out of the box without them.
- New `python -m kerykeion.swisseph_setup` command for users who want
  the optional Swiss Ephemeris backend: downloads data files with
  license confirmation (AGPL-3.0, Astrodienst AG).
- `EPHE_DATA_PATH` is now backend-aware (empty string default).
- PyPI license classifier corrected to AGPL-3.0.
- New Swiss Ephemeris Configuration guide in docs.

No API changes. Backward-compatible.

## 6.0.0a38 — 2026-05-08

Kerykeion 6.0.0a38 reduces startup memory by removing the import-time
LEB reader opening.

Highlights:

- `ephemeris_backend.py` no longer calls `get_leb_reader()` at import time.
  Previously this opened four companion mmap files just to log the format
  string (LEB1/LEB2), causing unnecessary memory allocation before any
  calculation.
- Updated `libephemeris` dependency to 1.3.0, which removes global
  `madvise(MADV_WILLNEED)` and adds selective mmap preloading via `warm()`.

No API changes. Backward-compatible.
