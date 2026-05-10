# Release Notes

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
