# General beta branch

The maintained development branch is `beta-v6`. Its package versions are
Kerykeion and CLI `6.1.0b3`, with `libephemeris==4.0.0b4`. These distributions
were published on PyPI on 2026-11-06 and all nine artifacts match the prepared
checksums. The package metadata and registry lock advance together; the locked
workspace install and installed CLI with `--show-ephemeris-notes` pass.
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
The bounded-memory and v4-closure workstreams are now integrated. The b3
publication preparation is integrated with its exact native b4 registry pin and
lockfile. The previous b2 metadata is historical, not a version for new builds.

`main` remains the review destination. Consolidation does not publish packages,
move release tags, regenerate data or alter numerical tolerances.
