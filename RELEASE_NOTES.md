# Release Notes

## 6.0.0a37 — 2026-05-08

Kerykeion 6.0.0a37 separates fixed-star discovery by ephemeris backend.

Highlights:

- `swisseph` continues to use the Swiss Ephemeris `sefstars.txt` catalog.
- `libephemeris` now uses its native fixed-star catalog and batch API; it never
  reads Swiss catalog files.
- Discovery output includes optional `near_point`, `orb`, `aspect`, `longitude`,
  `latitude`, and `degree` metadata for API/UI consumers.
- Swiss discovery avoids calculating fixed-star speed during the full catalog
  scan and only enriches matching stars.

This alpha is backward-compatible for existing point fields. Backend catalogs are
intentionally independent, so exact discovery result sets can differ between
`swisseph` and `libephemeris`.
