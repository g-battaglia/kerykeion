# Latest backend recheck — c0fe8ac9 / LibEphemeris 4.0.0

## Verdict

The clean latest fetched upstream revision passes the complete Kerykeion suite,
medium boundaries, strict numerical comparison, historical stellar probes,
upstream Python tests with their prepared reference, and Rust workspace tests.
The historical mixed-tier defect [#26](https://github.com/g-battaglia/libephemeris-rust/issues/26)
is corrected: the previous **110 native-only errors are now zero**.

This is consumer verification, not certification of every scientific
configuration or resolution of unrelated open upstream validation issues.
Earlier reports describe earlier engine snapshots; their historical #26
failure status is superseded here. No existing astronomical tolerance, golden
baseline, production spacing or computation fallback was changed.

## Exact build and isolation

- Fetched `origin/main`: `c0fe8ac9e66c066e6f0bc396ddb9e3cb43c71a10`.
- Python distribution and Rust crate now identify as **4.0.0**, not dev0.
  Updated the dedicated branch dependency, uv lock and native benchmark lock.
- The upstream checkout already had this commit, plus uncommitted Rust/indexing
  work. Built a **clean Git archive of origin/main**, not that dirty worktree.
  No upstream Rust source was edited, stashed, reset or included accidentally.
- Release wheel rebuilt with Maturin and two Cargo build jobs; installed only
  in this worktree. Extension SHA-256:
  `65544bf6ed107ee4a37de0890dac131ed5221d58278ac54314e751e14f2d1781`.
- Refreshed the editable Kerykeion/CLI metadata without dependency resolution;
  `uv pip check` reports all **55 installed packages compatible**. No subsequent
  uv project sync replaced the clean archived wheel with the dirty path source.
- CPython 3.12.13, macOS arm64, Apple M5 Pro. All twelve existing local LEB2
  images were hashed (3,097,243,319 bytes); datasets were not replaced.
- Large suites ran sequentially, with two pytest workers. Rust compilation used
  two jobs and workspace tests two harness threads. Only fixture/reference links
  and this execution-bound Cargo configuration were staged in the archive;
  committed upstream source and tests were unchanged. Main Kerykeion was not edited.

## Completed suites

| Run | Passed | Failed/errors | Skipped/ignored | Time |
|---|---:|---:|---:|---:|
| Complete Kerykeion, native extended | **14,235** | **0** | 72 skipped | 132.25 s |
| Native medium-only boundaries | **13** | **0** | 0 | 0.31 s |
| Complete Python v3.2.2 consumer control | **14,223** | **0** | 72 skipped | 126.01 s |
| Upstream Python bindings, prepared archive | **1,288** | **0** | 164 skipped | 12.79 s |
| Rust workspace, including doctests | **2,695** | **0** | 2 ignored | 19.70 s wall |
| Final integration/cache/manpage checks | **18** | **0** | 0 | 0.64 s |

Full suites include slow and historical tests: no fail-fast or slow-module
exclusion was used. The v3 control remains main `b81527d6` plus the same four
consumer-only manpage/playground fixes, without v4-only production changes.
The native suite has twelve additional integration/cache cases.

The upstream Python archive initially lacked the sibling reference Git
repository required by its pinned-source authentication helper. That first
attempt produced eight failures and 56 errors, all in reference subprocesses,
with signature parameterization incomplete. Added a read-only link to the
existing reference repository, retained the hash-verified `5d708bdb…cb82`
fixture and pinned v3.2.1 environment, then reran the **entire unchanged suite**:
1,452 cases collected, 1,288 passed, 164 skipped. The initial failed attempt is
preserved, not counted as an engine failure or suppressed with exclusions.
The optional ExFAT-only datasets remain unavailable; those tests keep their
explicit skips. In particular, independent local historical probes below cover
stellar routing despite the upstream ExFAT-dependent test being inapplicable.

## Strict numerical and historical verification

`compare_rust_v3.py --check` now exits **0**:

- **2,457 cases: 2,429 shared successes, 28 matching errors**;
- **0** one-sided errors, error-class differences or returned-flag differences;
- **0** position/angular-speed violations of existing consumer checks;
- maximum position component difference **7.9243e-8 degrees**, about
  **0.000285 arcseconds**, below even the upstream 0.001-arcsecond angle limit;
- maximum named ayanamsa difference **2.8422e-14 degrees**.

The largest angular-rate residual remains the pre-existing year-1000
geocentric equatorial Poseidon latitude case, **1.5351e-5 degrees/day**.
It is not a newly introduced position error: an independent sequence of public
position differences converges near the native rate (finest checked native
latitude residual **2.31e-9 degrees/day**). The raw diagnostic is retained;
a passing consumer threshold is not treated as proof of every upstream rate
qualification. Stellar distances/radial rates and all six component residuals
are also retained rather than conflated with angular differences.

The existing gap reproducer passes all six crossing configurations, all 47
modern modes, **188 historical mode probes** (47 × four epochs) and twelve
historical ordinary-star probes. No historical mode/star exceptions remain.

An additional independent probe compares automatic mixed-tier discovery with
the **same actual date-selected explicit core image**, with exact result
equality and finite-value checks, not relaxed tolerances:

- extended discovery: years −500, 1000, 1700, 2000; 47 modes plus three stars
  per epoch = **200 paired checks**;
- medium-only directory: years 1700 and 2000 = **100 paired checks**;
- each mode checks both `get_ayanamsa_ut` and sidereal `calc_ut`; ordinary stars
  are Regulus, Spica and Aldebaran;
- automatic Earth images correctly select extended for −500/1000, medium for
  1700 and base for 2000. All **300 pairs** are exactly identical to the explicit
  image controls. Explicit selection is diagnostic only, not a deployment workaround.

## Fresh measurements

Same four base LEB2 groups, identical recipes, three fresh processes × twenty
samples after three warmups. Benchmarks ran without simultaneous compilation
or validation jobs; disk cache was warm, not artificially cleared.

| Workload | Rust/PyO3 | Python v3.2.2 | Swiss |
|---|---:|---:|---:|
| 100 planet calls | **4.419 ms** | 6.544 ms | 0.129 ms |
| 100 house calls | **1.663 ms** | 3.297 ms | 0.255 ms |
| Default subject | **2.706 ms** | 1.019 ms | 0.241 ms |

Standalone Rust, built against the same clean archived core, retained-session
median of process medians: **4.149 ms / 100 planets**, **1.416 ms / 100 houses**.
No large new overall speedup is demonstrated here; native calls beat Python v3
but default-subject construction remains slower. Whole-suite time differences
are not used as microbenchmark evidence. Swiss contributes timing only, not
stored scientific reference outputs or fixtures.

## Packaging and artifacts

Both library and CLI wheels/sdists build successfully. Separate isolated wheel
installs pass the library render smoke and CLI entry point/version/help,
expected input error, info/status and installed manpage rendering. The library
wheel remains free of a CLI entry point. The final manpage gate also passes.

One final Poe invocation tried to resync its configured local-path dependency,
even though the outer uv invocation specified `--no-sync`. That attempted build
hit an incompatible argument type in the upstream checkout's uncommitted indexing
work; it is not a failure of the tested `c0fe8ac9` archive. No wheel was installed
from it: the archived extension hash and dependency consistency were reverified.
The manpage gate was rerun directly and with Poe's simple executor. Use those
no-resync commands while upstream development is in progress.

All raw logs, exit codes, JUnit XML, clean archived source, pinned-reference
links, image hashes, build wheels, benchmark samples and historical diagnostics
are under `validation_output/recheck-c0fe8ac9/`. Earlier runs are preserved.
