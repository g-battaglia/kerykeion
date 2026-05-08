# Release Notes

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
