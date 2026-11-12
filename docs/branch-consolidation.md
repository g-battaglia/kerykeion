# Beta branch consolidation (historical)

This page records the beta consolidation and b5 preparation, not the current
stable candidate. See the [current 6.1.0 stable preparation](../release_notes/v6.1.0-stable.md)
for the matching stable versions, backend qualification and publication gates.
The beta history and published beta packages remain unchanged; stable source
preparation does not itself merge `main` or publish either distribution.

The maintained development branch is `beta-v6`. Its package versions are
Kerykeion and CLI `6.1.0b5` in preparation, with `libephemeris==4.0.0b4`. The owner published the b4
library and CLI with the reviewed horizon, coverage and rendering fixes; all
four archives match the qualified build checksums. The registry lock also pins
the qualified SVG Polish 1.0.1 optimizer. The earlier Kerykeion/CLI b3 and native
b4 distributions were published on PyPI on 2026-11-06; all nine artifacts from
that earlier publication match their prepared checksums. The native backend
remains pinned to the same published b4 distribution.
The branch remains proposed to `main`; published tags remain immutable and this
beta integration does not promote main or a stable release.

## Consolidated histories

- `release/6.1.0b1` and `release/6.1.0b2`: the latest b2 release includes the b1
  optimizations, resource safeguards, opt-in score v2, fixed-star migration notes
  and the explicitly qualified backend patch.
- `codex/release-6.1.0` at `4be151ed`: retain the earlier stable-preparation
  commits and its archived release notes/checksums. Keep the published b2 package
  metadata rather than restoring the old stable version or backend-b1 pin.
- `codex/kerykeion-libephemeris-v4` at `f12b8e28`: retain the original native
  integration/diagnostic history. The current published-backend adapter,
  tracing/coverage behavior, fixed stars, heliacal configuration and glyph
  activation supersede the earlier Git SDK pin and historical failure reports.
- `kerykeion-rusty-leb` at `635cb41c`: retain the earlier local-backend checks,
  prototypes and validation history. The current beta already incorporates the
  production man-page/glyph fixes and native integration; the old local SDK
  path, experiments and old result summaries are not restored as current code.

The superseded branches were joined as history-only merges. Their commits and
original source snapshots remain reachable. Subsequent integration includes the
bounded-memory and v4-closure changes, plus reviewed corrections for mutable
translations, coverage invalidation, score inputs, subprocess lifecycle and
reference provenance. Published b1/b2 packages and their references remain
immutable. The archived stable draft is historical.

The owner excluded LibEphemeris PR #82 (the v3 PostgreSQL provider). That PR and
the related detached coefficient-routing experiment remain outside this
consolidation. No PostgreSQL port or dependency-source substitution is implied.
The bounded-memory and v4-closure workstreams are now integrated. The b4
publication preparation retains the exact native b4 registry pin and lockfile. The previous b2 metadata is historical, not a version for new builds.

`main` remains the review destination. Consolidation does not publish packages,
move release tags, regenerate data or alter numerical tolerances.


### Final b5 preparation

Kerykeion and the CLI advance together to 6.1.0b5, retaining LibEphemeris
4.0.0b4 and the qualified SVG Polish 1.0.1 lock. The distribution now requires
SVG Polish >=1.0.1, so an already-installed 1.0.0 cannot silently satisfy the
optimized beta. No ephemeris algorithms or frozen scientific references change.
Watchdog docstrings close the review coverage finding; native producer guard
unit tests use an isolated backend fake when the integration matrix is Swiss.
The original producer/candidate restrictions and coefficient hashes remain
strict. Publication is a separate owner action after artifact qualification.
