# Experimental Rust/PyO3 backend

This branch uses **LibEphemeris 4.0.0.dev0**, built from the local
`/Users/giacomo/dev/libephemeris-rust` checkout, instead of Python LibEphemeris
3.2.2. The distribution/import name is still `libephemeris` and
`KERYKEION_BACKEND=libephemeris` still selects it. Swiss Ephemeris remains an
explicit optional backend; no Swiss code or numerical models were added to Rust.

This is a development integration, **not a validated v4 release**. The upstream
Rust project still lists scientific validation work in progress.

## Install in the dedicated worktree

```sh
cd /Users/giacomo/dev/kerykeion/.worktrees/kerykeion-rusty-leb
CARGO_TARGET_DIR="$PWD/.rust-target" uv sync --python 3.12
LIBEPHEMERIS_PRECISION=extended uv run --no-sync python -c \
  'from kerykeion.ephemeris_backend import ephe; print(ephe.__version__)'
```

Rust, a C compiler and Python >=3.12 are required. `uv` builds a **non-editable**
PyO3 extension in this worktree's own environment; it does not replace the main
checkout's venv or edit the backend sources. The uv source path
`../../../libephemeris-rust` is relative to this worktree, not a portable PyPI
installation recipe. Moving the worktree requires adjusting that path.

After updating the development backend, rebuild explicitly:

```sh
CARGO_TARGET_DIR="$PWD/.rust-target" uv sync --reinstall-package libephemeris
```

Use `libephemeris._core.__file__` to verify the native extension. The `skyfield`
calculation-mode name is retained upstream for compatibility; in v4 it selects
a **native Rust JPL/SPK reader**, not a Python/Skyfield computation backend.
The default Kerykeion mode remains sealed-network `leb`.

## Consumer changes

- Dependency and uv lockfile select the local v4 development distribution.
- Native tracing tokens use `reset()`. They replace, rather than nest, native
  trace generations. Planetary provenance is harvested **before** independent
  fixed-star scopes, preventing stars from erasing planetary provenance.
- Current v4 fixed-star calls emit no trace rows. Their source/precision metadata
  stays `None` rather than inventing a source; the existing provenance tests
  deliberately continue to expose this upstream gap.
- v4.dev0's raw coverage query re-verifies every active LEB digest on every call.
  With the local extended files, a raw query took about one second and an
  uncached default subject about twelve seconds. Kerykeion now memoizes **only
  native coverage metadata**, not positions, searches or astronomical results.
  Keys distinguish all overlapping date-coverage regions. Configuration changes,
  file identity/content timestamps and group-directory changes invalidate the
  bounded cache. Native precision classes and reviewed flags are retained
  unchanged. `clear_coverage_cache()` is also available in
  `kerykeion.ephemeris_backend.coverage` after external provisioning.
- Regression tests cover trace cleanup on exceptions, planetary provenance with
  requested stars, overlapping coverage, file replacement, added groups,
  configuration changes and monkeypatched API bypass.
- Skyfield and skyfield-data are explicit **development-only independent test
  oracles**, restoring 35 horizon/altitude tests previously supplied by v3's
  transitive dependencies. A clean subprocess verifies that importing Kerykeion
  with the Rust backend does not import Skyfield, jplephem or NumPy, even when
  those test tools are installed. Legacy Skyfield exception probing is disabled
  for native v4 and Swiss backends.

## Reproduce complete tests and benchmarks

No test tolerances or golden fixtures are regenerated to hide differences.

```sh
LIBEPHEMERIS_PRECISION=extended KERYKEION_BACKEND=libephemeris \
  .venv/bin/python -m pytest tests/ --tier=extended -n 2 --tb=short \
  --durations=50 --junitxml=validation_output/rust-full.xml
```

This includes slow, historical, chart, CLI and online tests. Explicit test
skip/xfail conditions are recorded in the JUnit report. Full-range local data
are required; `--tier=extended` does not create or extend their coverage.

The test runs before the machine restart were **interrupted**, not passed.
The post-restart validation uses two workers and runs suites sequentially to
bound memory. The crash's cause was not established.

The benchmark runner launches three fresh processes per backend, rotates order,
uses three warmups and twenty measurements per operation, and reports the median
of the three process medians. Backends use the same CPython 3.12 interpreter and
modern-epoch recipes. Python v3 and Rust must expose identical LEB inventories;
Swiss preflight refuses a silent Moshier fallback. Benchmark only while other
validation jobs are stopped. A fresh process is **not** a cleared OS disk cache.

Create an isolated base-only data view (symlinks, no dataset modifications):

```sh
mkdir -p validation_output/data-base/leb
for file in "$HOME"/.libephemeris/leb/base_*.leb2; do
  ln -s "$file" validation_output/data-base/leb/
done
ln -s "$HOME/.libephemeris/de440s.bsp" validation_output/data-base/

.venv/bin/python scripts/benchmark_backends.py \
  --reference-python /Users/giacomo/dev/kerykeion/.venv/bin/python \
  --reference-root /Users/giacomo/dev/kerykeion \
  --data-dir "$PWD/validation_output/data-base"
```

Do not set `LIBEPHEMERIS_LEB=base_core.leb2` for the multi-body comparison:
v4 interprets it as a single-file provider, whereas v3 also discovers companion
groups. The runner clears inherited backend variables and verifies inventories.

A separate executable measures the same 100-position and 100-house workloads
**without Python or PyO3**:

```sh
CARGO_TARGET_DIR="$PWD/.rust-target" cargo build \
  --manifest-path benchmarks/native/Cargo.toml --release --locked
.rust-target/release/kerykeion-rusty-leb-benchmark \
  "$HOME/.libephemeris/leb/base_core.leb2" \
  "$HOME/.libephemeris/leb/base_apogee.leb2" \
  "$HOME/.libephemeris/leb/base_asteroids.leb2" \
  "$HOME/.libephemeris/leb/base_exotics.leb2"
```

`scripts/compare_rust_v3.py` compares 2,457 planetary cases across nine epochs
(500 BCE to 2100), seven perspectives and 39 point/body names using identical
local extended datasets and disabled IERS Delta T. This includes unsupported
ALDEBARAN sidereal configurations: one-sided errors are recorded, not excluded
from the results. It additionally compares all named ayanamsas and five fixed
stars. It saves raw v3/v4 residuals, **not Swiss
numerical fixtures**. This is a diagnostic grid, not independent scientific
certification or proof for every date/configuration.

`scripts/run_rust_validation.sh` orchestrates sequential benchmark/native/full
Rust/full v3 runs plus the medium-range boundary cases, preserving logs, exit
codes and JUnit files under the ignored `validation_output/` directory. It exits
nonzero when any validation step fails; currently the recorded suites are not
green. Its v3 reference is a source archive of the
unchanged main commit `b81527d6`; no main-checkout files are rewritten.

## Measured results

See [RUST_VALIDATION_RESULTS.md](RUST_VALIDATION_RESULTS.md) for completed-run
counts, failure diagnosis,
backend timings and limitations. Raw logs and machine-readable outputs are kept
in `validation_output/`; they are not package contents.
