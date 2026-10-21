# Rust v4 integration: completed validation and benchmarks

**2026-10-21 — experimental, not production-ready.** Some successful sidereal
return searches produce results about **24 degrees wrong**. Other supported-v3
configurations raise native errors. Do not interpret passing ordinary natal
positions or a green packaging smoke test as validation of these techniques.

## Environment and isolation

- Worktree/branch: `.worktrees/kerykeion-rusty-leb` / `kerykeion-rusty-leb`.
- Unchanged main/control source: Kerykeion 6.0.5, `b81527d689991f806f8ea991364b7c3fed4c4c41`.
- Native package: LibEphemeris `4.0.0.dev0`, release PyO3 extension built from
  `2e0e52459ed8aece8e3e0e88192c0f373ddc194e`.
- Control engine: Python LibEphemeris **3.2.2**. Swiss bindings: **2.10.3.2**.
- Apple M5 Pro, 48 GiB RAM, macOS 26.5.2 arm64, CPython **3.12.13**.
- Local existing LEB2 files only; SHA-256 list in `validation_output/leb-sha256.txt`.
  Data files were not replaced or regenerated. Reviewed flags are not fabricated.
- Python v3 tests run from a source archive inside the worktree, using the
  existing v3 interpreter/environment. The main checkout/environment was not
  replaced. No upstream Rust source changes were made by this integration.
- The pre-reboot runs were interrupted and are **not** counted as completed.
  Post-reboot suites ran sequentially with **two workers**, not concurrent large
  suites. The cause of the machine crash was not established.

The native extension SHA-256 is
`21ec12449d534a584bc1329f515373e8ae3315a89b0670f23a176abd8c3ee070`.
Machine/package metadata is saved in `validation_output/environment.json`.

## 1. Complete test execution

Command: `pytest tests/ --tier=extended -n 2 --tb=short --durations=50`.
**No `-m 'not online'`, slow-test exclusion, fail-fast or reduced test directory.**
All original consumer tests were collected, including online, historical, chart,
CLI and independent solar-altitude tests, plus 12 new integration/cache cases.

| Completed suite | Collected | Passed | Failed | Skipped | Pytest time | External wall time |
|---|---:|---:|---:|---:|---:|---:|
| Rust v4, extended | 14,298 | **14,198** | **28** | 72 | **482.94 s** | 484.05 s |
| Python v3.2.2, extended | 14,286 | **14,212** | **2** | 72 | **126.35 s** | 128.21 s |
| Rust v4, medium boundaries | 13 | **12** | **1** | 0 | 1.05 s | 1.68 s |
| Python v3.2.2, same boundaries | 13 | **13** | **0** | 0 | 0.22 s | 1.36 s |

The first completed native run lacked a test-only dependency and skipped the
35-case independent Skyfield horizon module at collection. That was **not**
accepted as complete coverage: Skyfield/skyfield-data were added to the dev
extras and the whole extended suite was rerun. All 35 oracle cases now execute.
Skyfield is not a native runtime computation backend. The oracle used Skyfield
1.55 / skyfield-data 7.0.0; the unchanged v3 environment has Skyfield 1.54.

The 13 medium-specific range-edge/fallback cases, inapplicable on extended, were
then executed against an isolated base+medium view of the same existing files.
The remaining 59 distinct skipped cases are: 50 absent expected lunar-node
fixture rows, 3 fixed-reference-frame/traditional-ayanamsa distinctions, 4
minified SVG path-rewrite textual checks covered by separate symbol checks,
1 optional CairoSVG/system-Cairo preview check and 1 cold font-cache check.
Skips are **not** successes.

No existing tolerances, expected positions or golden SVG/report fixtures were
changed. The full suites correctly exit **1**, not green. Whole-suite elapsed
work is slower on v4 in this configuration; it is not a controlled per-operation
speed benchmark because failures, initialization and collection also differ.

### Every failure classified and linked

There are **29 failing cases across the extended + medium runs**, with **27
new failures relative to the v3 control** and 2 pre-existing consumer failures.
`validation_output/failure-issue-map.json` maps every failing node to its issue;
there are no unmapped failures.

| Cause | Cases | Classification / evidence | Issue |
|---|---:|---|---|
| Stored-LEB crossing configuration | 8 | **Serious correctness/configuration error.** Sidereal Sun/Moon/Mars crossings miss their target by ~24.19 degrees; a solar return is ~25 days early. Topocentric crossings reject an observer that direct `calc_ut` accepts. Includes heliocentric sidereal returns. | [#15](https://github.com/g-battaglia/libephemeris-rust/issues/15) |
| Live-anchor sidereal modes | 13 | **Unsupported functionality, not rounding.** `calc_ut` raises `STAR-04 scope` for 13 named modes including ALDEBARAN, TRUE_CITRA and GALCENT_0SAG. Eleven direct consumer failures plus two golden-driver gates blocked by chart construction. Scalar ayanamsas can still be available. | [#16](https://github.com/g-battaglia/libephemeris-rust/issues/16) |
| Fixed-star tracing | 4 | **Provenance metadata regression.** Stellar positions succeed, but an unnested `fixstar_ut` call emits no trace row. Source/precision fields and serialized provenance remain absent rather than invented. | [#17](https://github.com/g-battaglia/libephemeris-rust/issues/17) |
| Sealed-network public exports | 1 | **API compatibility gap.** v3.2.2 `libephemeris.net.NetworkSealedError` and `require_network` cannot be imported. The test stops at import: this does **not** demonstrate a Rust network escape. | [#18](https://github.com/g-battaglia/libephemeris-rust/issues/18) |
| Date-aware out-of-range coverage record | 1 | **Metadata/API difference.** Native Chiron coverage at 1580 is `None`; v3 supplies out-of-range stored bounds. The companion fallback-position series test passes. Not evidence of a wrong Chiron position. | [#25](https://github.com/g-battaglia/libephemeris-rust/issues/25) |
| CLI man-page version | 1 | **Pre-existing consumer-only failure.** Generated page still says 6.0.4 while the parser/package is 6.0.5. Fails on both engines. | [#23](https://github.com/g-battaglia/libephemeris-rust/issues/23) |
| Small-synastry glyph-cap expectation | 1 | **Pre-existing consumer-only failure.** Shipped/lifted renders are equal, contrary to the hard-coded `binds_lib=True` expectation. Fails on both engines; not a new v4 numerical defect. | [#24](https://github.com/g-battaglia/libephemeris-rust/issues/24) |

Additional independently reproduced integration/build defects:

- **Nested trace restoration:** native inner scopes invalidate/discard the
  parent. The consumer is adapted to sequential scopes; the compatibility gap
  is recorded in [#19](https://github.com/g-battaglia/libephemeris-rust/issues/19).
- **Repeated digest verification:** each raw coverage query hashes all active
  immutable images; ~0.95–1.01 seconds per extended query, ~11.6–11.8 seconds
  for an uncached subject. A bounded metadata-only consumer cache mitigates the
  warm path, not all cold costs. [#20](https://github.com/g-battaglia/libephemeris-rust/issues/20).
- **Tier discovery:** installing extended files beside medium/base can make a
  modern Sun query fail with a misleading corrupt-index/tier error. Added
  independent v3.2.2 evidence to existing
  [#4](https://github.com/g-battaglia/libephemeris-rust/issues/4);
  [#21](https://github.com/g-battaglia/libephemeris-rust/issues/21) was closed as
  its duplicate rather than tracking the same cause twice. Use extended with
  the full hierarchy or an isolated eligible-tier data view for now.
- **External Rust build:** a fresh consumer resolves ureq 3.5.0 and fails at
  `NextTimeout` initializers. Pinning its lock to 3.4.2 makes the standalone
  benchmark compile. [#22](https://github.com/g-battaglia/libephemeris-rust/issues/22).

Eleven issues were created (#15–#25), one closed as the duplicate above. The two
consumer-only issues were explicitly marked as such, as requested, not falsely
attributed to native ephemeris calculations.

### Direct numerical diagnostic (not independent scientific certification)

`scripts/compare_rust_v3.py`: **2,457 cases**, 9 epochs (500 BCE–2100), 39
body/point names, 7 perspectives, identical local extended inputs, IERS Delta T
disabled. These include ALDEBARAN configurations, not just the working modes.

- **2,182 shared successes**, **28 shared errors**, **247 v4-only errors**.
  The one-sided errors are the unsupported ALDEBARAN routes, not silently
  omitted rows. No returned-flag differences on shared successful cases.
- Maximum shared longitude residual: **1.198e-10 degrees** (~4.31e-7 arcsec).
- Maximum latitude residual: **1.421e-14 degrees**.
- Maximum longitude-rate residual: **9.581e-9 degrees/day**.
- No shared success exceeds the existing consumer 0.01-degree position or
  0.0001-degree/day angular-rate thresholds. These are reported diagnostics,
  not newly relaxed tolerances or a claim that every native configuration works.
- Named scalar ayanamsas at the additional 1940 probe agree within floating-point
  noise; that does not make their position-calculation modes supported.
- Five fixed-star longitudes at that probe agree exactly; latitude residuals
  are at floating-point noise level. Small distance/radial-rate differences
  remain in the raw output; no independent stellar-derivative accuracy claim is
  made here.

The return-search errors are **separate** from these direct-position residuals:
a search can return the wrong epoch/frame even while `calc_ut` itself agrees.

## 2. Controlled benchmarks: native core, Python v3 and Swiss

Three fresh processes per backend, rotated order; **3 warmups + 20 samples** per
operation/process; median of process medians, sequential and not concurrent with
the suites. Warm OS filesystem cache; no cache flushing or downloads.

Python v3 and v4 use the **same four base LEB2 group files**, checked against
both returned inventories. Swiss uses local SE files; preflight rejects Moshier
fallback. IERS Delta T is disabled in both LibEphemeris configurations. Runtime
and test-oracle dependencies are separate. Values below are **milliseconds**.

### Standalone Rust, no Python or PyO3

The release executable retains one native `Session`, uses the same epochs,
flags and four base files, and consumes results with `black_box`:

| Operation | Native Rust, 4 files | Native Rust, core file only |
|---|---:|---:|
| 100 planet `calc_ut` calls | **1.200** | 1.098 |
| 100 Placidus house calls | **1.382** | 1.396 |

Against the Python-v3 public kernel timings below, the retained native Session
is approximately **5.5x faster for planets** and **2.4x for houses**. This is a
core/API workload comparison, not a standalone implementation of all Kerykeion
chart assembly. The four-file native result avoids conflating single-file vs
composite provider selection.

### Through the Python APIs / Kerykeion

| Operation | Rust v4 / PyO3 | Python v3.2.2 | Swiss |
|---|---:|---:|---:|
| 100 planet `calc_ut` calls | **3.790** | 6.551 | **0.131** |
| 100 Placidus house calls | 4.147 | 3.331 | **0.253** |
| Subject, common 12 points | 1.826 | 0.923 | **0.220** |
| Subject, default points | 3.377 | 1.029 | **0.251** |
| Five common-point subjects | 9.195 | 7.136 | **1.086** |
| Subject, LAHIRI | 2.150 | 1.124 | **0.230** |
| Subject, optional calculations | 4.015 | 5.271 | **0.401** |
| Natal aspects | 0.112 | 0.113 | 0.112 |
| Synastry aspects | 0.229 | 0.227 | 0.226 |
| Natal SVG from prepared data | 2.209 | 2.134 | 2.186 |
| Full natal subject + chart/SVG pipeline | 4.390 | 3.556 | **2.796** |

**Conclusion: a substantial core speed gain does not yet translate into a
faster Kerykeion integration.** The default subject is currently about **3.3x
slower than v3** and **13.5x slower than Swiss**. The full natal pipeline is
about **23% slower than v3**. Swiss is also faster than the retained native Rust
Session on these measured planet/house workloads.

The global-runtime/binding path costs about 3.2x the retained native Session for
planet calls. These measurements do not identify PyO3 itself as the sole cause:
configuration/provider acquisition and repeated discovery work also differ.
Related profiling evidence is attached to
[#7](https://github.com/g-battaglia/libephemeris-rust/issues/7); digest work is
separately tracked in [#20](https://github.com/g-battaglia/libephemeris-rust/issues/20).
Rendering/aspect workloads are largely backend-independent Python work.

### Fresh process and raw metadata costs

| Metric | Rust v4 | Python v3 | Swiss |
|---|---:|---:|---:|
| Fresh `import kerykeion` | 376 ms | 865 ms | 374 ms |
| First subject after kernel preflight | 176 ms | 7.24 ms | 5.24 ms |
| Raw `get_body_coverage`, one base query | 15.36 ms | 0.0064 ms | n/a |

The first subject is not a cold OS disk-cache measurement. Warm subject timings
benefit from the consumer metadata cache; the native solver/position calls are
not memoized by Kerykeion. The original single-core-file benchmark draft was
rejected because v4 and v3 interpreted explicit file selection differently;
only the verified equal-four-file runs appear in the comparison table.

## 3. Packaging and final checks

- `uv build --all-packages`: library and CLI wheels/sdists built successfully.
- Isolated library wheel, no editable project: natal SVG rendered; library wheel
  correctly carries no CLI command.
- Isolated library + CLI wheels: command on PATH, version 6.0.5, help, expected
  exit 4, info, `status --check`, installed man page rendering all pass. The
  separate source man-page-version gate remains a documented baseline failure.
- Final focused trace/cache/heliacal checks: **62 passed, 1 medium-only skip**.
- Separate Swiss import + offline subject smoke passes.
- Ruff, targeted MyPy, native rustfmt and shell syntax checks pass. No claim is
  made that the entire pre-existing repository type/lint suite was run.

See [RUST_BACKEND.md](RUST_BACKEND.md) for installation and reproducible commands.
Raw JUnit, logs, benchmark samples, minimal gap reproductions, data hashes and
failure/issue mapping remain under ignored `validation_output/`. No Swiss
numerical reference outputs or new golden fixtures were stored.
