# Recheck of the v4 issue fixes — core 09236862

**Verdict: the original Kerykeion regressions are corrected, but the backend is
not completely clear.** At this recheck the full consumer suite had only its
two known consumer-only failures. Those have since been corrected and both
complete consumer suites pass; see
[RUST_CONSUMER_FIXES.md](RUST_CONSUMER_FIXES.md). The measurements below retain
the original recheck results. An independent historical grid still exposes a real
stellar/live-anchor routing defect, filed as
[#26](https://github.com/g-battaglia/libephemeris-rust/issues/26).

This report supersedes the status, not the historical measurements, in
[RUST_VALIDATION_RESULTS.md](RUST_VALIDATION_RESULTS.md).

## Build and test isolation

- Native source: `092368627e960af2859d45007ea9c352b4a28e03`.
- A forced `uv sync --reinstall-package libephemeris` rebuilt the release PyO3
  extension; the package version is still `4.0.0.dev0` and therefore cannot by
  itself identify the tested code.
- Tested extension SHA-256:
  `2150340dd0a11a9823b9b681596045ba05262e280b0bf72ed203803d9b84bd5d`.
- Same CPython 3.12.13 / Apple M5 Pro and existing local LEB files as the initial
  run. All 12 LEB2 file hashes were rechecked successfully; none was replaced.
- Everything remains in `.worktrees/kerykeion-rusty-leb`; main and the upstream
  Rust source were not edited. Reference tests use the unchanged main archive.
- Large suites ran sequentially with two workers. No fail-fast, offline-only
  selection or slow-module exclusion was used.

The new upstream package declares NumPy for compatible array inputs/results;
`uv.lock` now records that dependency. This is not a Python astronomical engine.
The clean-import integration check still passes. The native standalone consumer
lockfile also needed the newly added serde dependencies and was refreshed;
a subsequent **locked rebuild succeeded** before measuring that executable.

## Complete consumer test rerun

| Completed run | Collected | Passed | Failed | Skipped | Pytest time |
|---|---:|---:|---:|---:|---:|
| Rust v4, extended | 14,298 | **14,224** | **2** | 72 | **115.82 s** |
| Python v3.2.2 control, extended | 14,286 | **14,212** | **2** | 72 | **124.35 s** |
| Rust v4, medium boundaries | 13 | **13** | **0** | 0 | **0.25 s** |

All 14,286 original control test IDs remain covered, plus 12 integration/cache
cases. The 72 extended skips have the same documented applicability/optional
asset reasons as before; the 13 medium-only cases were separately executed.
The original 26 additional extended failures and the medium coverage failure
are gone. The full native suite took about 116 seconds instead of about 483
seconds in the previous run, although whole-suite timings are not a substitute
for controlled operation-level benchmarks.

One integration assertion required correction: it had encoded the old missing
fixed-star provenance as `source is None`. It now **requires** native `LEB`
provenance and `ephemeris` precision. No original astronomical tolerance or
golden fixture was altered; the two consumer-only tests/files were not fixed
or suppressed during this recheck.

### Confirmed fixes

Direct public-API reproductions, separate from the consumer cache, confirm:

- Sidereal and topocentric Sun/Moon crossings, generic Sun crossings and
  heliocentric Mars crossings reproduce the target in the configured frame.
  The largest of the six measured residuals is **9.34e-9 degrees**, not ~24°.
- All **47 named Sun sidereal modes** tested at the modern epoch succeed.
- An inner trace restores its parent; the outer token resets successfully.
- Fixed-star tracing records an actual native `LEB` provider row.
- The sealed-network public imports are restored; the existing gate test passes.
- A modern medium-tier Sun works with extended files present in the same root.
- All 13 medium-boundary/fallback cases pass, including the Chiron diagnostic
  coverage record that previously returned `None`.
- Raw repeated extended coverage queries have a median of about **6.65 µs**
  after first acquisition, rather than ~0.95–1.01 seconds **per query**. First
  acquisition in that process still cost about 1.20 seconds, including resource
  opening/validation; that is not a warmed-query measurement.
- A genuinely fresh external Rust consumer, with no inherited lockfile,
  resolves ureq **3.4.2**, compiles and runs. The old 3.5.0 build break is absent.

### Additional upstream binding checks

A read-only source archive of the tested upstream revision was prepared inside
this worktree, with the exact canonical base fixture obtained from the pinned
local Git blob and SHA-256 checked. A separate offline-installed v3.2.1
reference was verified against its pinned module sources by the upstream
signature helper.

The upstream Python-binding suite collected **1,380 tests**: **1,220 passed,
160 skipped, zero failures/errors**, in 11.53 seconds. The remaining optional
cases depend on external JPL/SPK/ASSIST/IERS paths unavailable to that archived
harness. They are not counted as successes. An earlier attempt against the
unprepared source checkout lacked its ignored fixture/reference inputs and is
not used as engine-validation evidence. No files were provisioned into the
actual upstream checkout.

This is consumer/API verification, not certification of the upstream project's
entire remaining P5 scientific acceptance program.

## Remaining engine problem: historical stellar support

The additional **2,457-case** identical-data v3/v4 diagnostic grid reports:

- **2,319 shared successful cases**;
- **28 shared errors**, with matching error classes;
- **110 v4-only errors**, all historical ALDEBARAN configurations;
- no returned-flag differences or successful position/angular-rate residuals
  beyond the existing Kerykeion diagnostic thresholds.

The script now supports `--check`: these errors produce **exit 1**, rather than
mistaking successful report generation for a successful comparison.

The same first-wins support defect also affects ordinary stars and the wider
live-anchor family:

| Probe | Modern 2000/2024 | Years -500, 1000, 1700 |
|---|---|---|
| 47 named Sun sidereal modes | all pass | the 13 live-anchor modes fail at each epoch |
| Regulus, Spica, Aldebaran | all pass | all fail at each epoch |
| Tropical / LAHIRI Sun | pass | pass |

### Isolated cause

With automatic base+medium+extended discovery, `get_body_coverage(EARTH, jd)`
correctly selects medium for 1700 and extended for 1000/-500. Nevertheless the
stellar observer path attempts to evaluate the **base Earth** interval and
raises `EphemerisRangeError` for body 14.

For example, at year 1000 it requests JD `2086468.0190742647` but reports bounds
`[2396757.5, 2506332.5]`. Explicitly selecting the **same existing extended core
file** makes the identical stellar and ALDEBARAN calculations succeed. This is
not absent historical coefficients or rounding noise. Explicitly choosing a
single core file is an isolation experiment, **not** a general deployment fix:
it can exclude companion asteroid/apogee/exotic coefficient groups.

The stellar path uses a flattened `CompositeIndex` whose body-id dispatch is
first-wins instead of retaining date-aware cross-tier selection. Details,
minimal code, isolation matrix and requested regressions are in
[#26](https://github.com/g-battaglia/libephemeris-rust/issues/26), with a follow-up
link on #16. No source fallback, file replacement, extrapolation or tolerance
change was added to conceal it. Until corrected, mixed-tier historical stars
and live-anchor sidereal charts cannot be declared verified.

## What to do about the two consumer-only issues

These still fail on **both** the current native backend and Python v3.2.2.
They remain open and their tracked consumer files were deliberately left alone.

### #23 — generated CLI manpage version

The independently generated candidate differs from the committed file by
**exactly one line**: `kerykeion-cli 6.0.4` versus `6.0.5`.

In the Kerykeion worktree:

```sh
uv run --no-sync poe man:generate
uv run --no-sync poe man:check
uv run --no-sync pytest tests/core/test_cli.py::TestManPage -n 0
```

Commit `cli/man/man1/kerykeion.1` and retain the generation/check step in release
version bumps. No ephemeris change is needed.
[Issue #23](https://github.com/g-battaglia/libephemeris-rust/issues/23).

### #24 — stale small-synastry ceiling expectation

The test and stored HTML say this fixture's ceiling changes the layout. Actual
**display positions** were measured, not merely compared as SVG strings, on
both engines: lifting the ceiling changes **zero degrees** on both rings, and
the SVGs are identical.

- Outer-ring ceiling: **5°**. The largest uncapped request is **5.455085°**, but
  every clipped pair already has sufficient space. For example Mercury/Sun
  has an actual **8.332189°** gap, and Chiron/Moon **6.042973°** versus its
  **5.370319°** request. Clipping a request is not the same as the cap being an
  active constraint on the final layout.
- Inner-ring ceiling: **8°**, largest uncapped request **6.990390°**; it does not
  even clip a request.
- The stored `scripts/glyph_playground.html` still has
  `ceilingBinds.small.synastry = true`; the current fixture requires **false**.

Recommended consumer change:

1. Update the small-synastry expected effect to **false**, based on the measured
   geometry, not on `BACKEND_NAME`. Update stale explanatory prose that claims
   the cap necessarily binds for that fixture.
2. Add/retain a genuinely crowded **synthetic positive case** proving that
   lifting a cap changes display angles when that constraint is active. Keep
   the uncrowded fixture as the negative case; avoid relying solely on arbitrary
   SVG text inequality to infer geometric behavior.
3. Regenerate `scripts/glyph_playground.html` from the current renderer. Its
   generator already measures the fixture effect when building the manifest.
4. Run the playground and geometric-decluttering tests, then the complete suite.

```sh
LIBEPHEMERIS_PRECISION=extended uv run --no-sync poe playground
uv run --no-sync pytest tests/core/test_glyph_playground.py \
  tests/core/test_modern_decluttering.py -n 0
```

Do **not** modify astronomical positions, production spacing floors or precision
tolerances just to force this fixture to bind.
[Issue #24](https://github.com/g-battaglia/libephemeris-rust/issues/24) now contains
the measured constraints/gaps and this follow-up plan.

## Refreshed performance and packaging

Same protocol: three fresh processes, three warmups and twenty samples per
operation, rotated backend order, identical four base LEB files verified against
both inventories, no concurrent validation workloads, warmed filesystem cache.
Swiss preflight confirms actual SE data, not Moshier fallback. Milliseconds:

| Workload | v4 Python API / Kerykeion | v3.2.2 | Swiss |
|---|---:|---:|---:|
| 100 planet calls | 4.237 | 6.545 | 0.134 |
| 100 houses | 1.843 | 3.399 | 0.265 |
| Common 12-point subject | 1.402 | 0.920 | 0.225 |
| Default subject | 2.786 | 1.031 | 0.248 |
| Full natal pipeline | 4.487 | 3.590 | 3.126 |

The correctly rebuilt standalone **current** Rust executable, retaining a
session with the same four files, measures **3.884 ms / 100 planet calls** and
**1.511 ms / 100 houses**. The earlier ~1.2 ms core result belonged to the old
revision and must not be attributed to this newly changed numerical pipeline.
These measurements do not establish the cause of every remaining cost; no
blanket end-to-end speedup over Python v3 or Swiss is claimed. The large
repeated metadata verification cost and the complete-suite runtime are clearly
improved; the consumer compatibility metadata cache is still retained.

Both wheels/sdists rebuild. Isolated library-only and library+CLI wheel smokes
pass, including chart rendering and CLI status/entry point/man rendering. That
packaging smoke does not override the source manpage version test or the
historical engine defect.

Raw results, build hashes, candidate-only manpage diff, measured glyph layout,
old/new minimal reproductions and all exit codes are under
`validation_output/recheck-09236862/`. The original run artifacts are preserved.
