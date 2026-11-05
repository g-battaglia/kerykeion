# Ephemeris integration closure

This change builds on the consolidated `beta-v6` (Kerykeion/CLI 6.1.0b2,
LibEphemeris 4.0.0b2). The native Rust backend remains the default; the optional
Swiss backend remains pyswisseph 2.10.3.2 in the locked validation environment.
No astronomical algorithm, dependency pin, frozen reference or tolerance changes.

## Corrections

- `ChartDrawer(..., show_ephemeris_notes=True)` and CLI
  `--show-ephemeris-notes` append translated, accessible notes identifying
  unavailable points and explicitly approximate positions, by subject. They
  work on full charts, wheels and aspect grids. The option defaults to false;
  empty notes leave the output unchanged. Models and CLI warning exit semantics
  are preserved. Unreviewed local data are not relabelled as approximate.
- Historical Swiss snapshots check the required bodies at the actual date.
  A known missing file or unsupported date can make a complete snapshot
  inapplicable; unexpected errors and omissions without warnings fail. Separate
  tests exercise those same historical dates and verify omissions and aspects.
- Galileo/Newton references now verify their coefficient-input contract. The
  qualified automatic inventory uses medium/DE440 at those dates. Forcing the
  extended core selects a different lunar model: both the unchanged beta and
  the initial candidate fail those two comparisons under that override, and
  both pass with qualified automatic routing. Tests now explain incompatible
  input selection and verify the relevant manifest hashes without changing
  backend state or rewriting the immutable producer manifest.
- The backend-comparison fixture previously reloaded the backend module inside
  one process, leaving imported factories bound to a different engine. It also
  cleared data paths. The unchanged beta produced 401 downstream Swiss failures
  in a complete serial run containing that module. High-level comparisons now
  execute each engine in a fresh child process, assert its actual identity and
  preserve the parent backend/environment. Direct comparison helpers preserve
  configured paths. Existing numerical assertions and tolerances are unchanged;
  comparison values remain in memory rather than becoming reference fixtures.

## Validation

Local macOS arm64 checks use only the existing owner-provided LEB inventory.
All 12 input hashes remained unchanged. Native networking and automatic data
acquisition were disabled. Test commands ran sequentially with indexed readers,
`-n 0 -W error` and a 1 GiB sampled process-tree RSS watchdog.

| Check | Result |
|---|---|
| Complete native Python 3.12 offline suite, final tree | 14,691 passed; 27 skipped; 3 online deselected |
| Complete Swiss Python 3.12 offline suite, final tree | 14,172 passed; 546 skipped; 3 online deselected |
| Medium-only boundaries and provenance controls | 26 passed |
| Direct backend comparisons, now isolated | 30 passed |
| Final native output comparisons against the unchanged beta | 1,470 comparisons; zero mismatches |
| Python 3.14 rendering, CLI, tracing, provenance, stars and heliacal checks | 548 passed; 16 skipped |
| Ruff, MyPy, Pyright, structural and fresh imports | Passed |
| CLI smoke, generated man page, locked resolution, dependency consistency | Passed |
| Runnable CLI documentation examples | 39 passed; 3 installation examples intentionally not executed |
| Public documentation and standalone skill coverage | 100% |
| Library/CLI wheel and sdist metadata | Four archives pass strict Twine validation |
| Source archive rebuilds | Wheel member names and bytes match direct builds |
| Fresh installed-wheel checks, Python 3.12 and 3.14 | Native backend, optional notes, CLI, data-root identity and dependencies passed |

Skips are not passes. Native skips include the medium-specific boundaries,
Swiss-specific historical cases and an optional font-cache check. Swiss skips
include native-only contracts, unavailable optional data and numerical
comparisons against another backend's reference set; applicable structural
checks remain strict. Live GeoNames checks and other operating systems were not
rerun for this change. Medium and Swiss runs exercise their corresponding cases;
the per-profile counts overlap and must not be summed as unique tests.

Final sampled peaks were 435.4 MiB for the native suite and 827.9 MiB for Swiss.
The watchdog threshold is sampled, not an OS-enforced allocation limit.

Notes were rendered and visually inspected in classic/full, dark/modern-wheel
and black-and-white/grid exports. Regression tests also cover unchanged default
bytes, missing/approximate distinctions, dual/composite subjects, all bundled
languages, custom labels, long untrusted names, XML escaping, minification,
CSS inlining and repeated use of one drawer.

The 1,470 unchanged-output checks cover complete serialized models, SVG hashes
and astrocartography outputs. They establish compatibility with the same native
backend and inputs, not a new independent absolute-accuracy certification.
Existing independent numerical controls remain in the native suite.

## Performance

[Paired results and process medians](performance/ephemeris-notes-6.1.0b2.json)
compare source `058276da` with `5650294c`, the final runtime implementation.
Later changes only annotate a local dictionary type and document the results.
The same interpreter, dependencies and benchmark script serve both checkouts:
Python 3.12.13, LibEphemeris 4.0.0b2, owner-root base LEB and owned reader.
Notes are disabled, matching the existing public behavior.

Six pairs ran in alternating order `AB, BA, AB, BA, AB, BA`, one process at a
time, with five warmups, seven blocks and twenty calls per block (one for
minification/dense astrocartography). Wall and CPU timers are unchanged. Every
process ran under a 512 MiB sampled watchdog; the largest observed RSS was
164.1 MiB. No test or build command was run concurrently by this workstream.

| Workload | Before | After | Wall change |
|---|---:|---:|---:|
| Complete classic natal pipeline | 2.0781 ms | 2.0674 ms | -0.51% |
| Complete modern natal pipeline | 2.3807 ms | 2.3647 ms | -0.67% |
| Translation pair | 0.02602 ms | 0.02614 ms | +0.46% |

Across all 23 workloads, changes in the medians of process medians range from
-1.24% to +1.13%. Paired samples vary in both directions: no reproducible
slowdown is established by the agreed protocol. These are warm local timings,
not statistical equivalence or a guaranteed speedup on every workload.

The initial implementation added footer labels to the ordinary translation
maps and showed a small repeatable translation-copy cost. The final version
keeps those labels in the opt-in rendering path; default translation maps and
schemas retain their previous shape. Enabling notes naturally performs the
additional formatting requested by the caller; those new exports have no
pre-change counterpart.

## Reproduction and scope

Use the qualified existing data root, without an explicit core override:

```sh
unset LIBEPHEMERIS_LEB
export LIBEPHEMERIS_DATA_DIR=/path/to/existing/inventory
export LIBEPHEMERIS_PRECISION=extended LIBEPHEMERIS_LEB_READER=indexed
export LIBEPHEMERIS_NETWORK_POLICY=sealed LIBEPHEMERIS_AUTO_SPK=0
export LIBEPHEMERIS_IERS_AUTO_DOWNLOAD=0
KERYKEION_BACKEND=libephemeris uv run python scripts/run_resource_limited.py -- \
  python -m pytest tests/ --tier=extended -m 'not online' -n 0 -W error
```

Repeat with `KERYKEION_BACKEND=swisseph` and the already installed optional
Swiss distribution/data. The comparison module can now remain in both suites.
Run the documented medium boundary profile separately. Benchmark reproduction
uses `scripts/benchmark.py --rounds 7 --iterations 20 --warmup 5 --json ...`
with identical base/owned configuration and alternating source checkouts.

No Rust-engine or Rust Swiss-bindings change was required. No new historical
Chiron data, release tags or package uploads are included. The PR targets the
beta branch and remains separate from a merge or release decision.
