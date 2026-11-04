# Python performance changes for 6.1.0b1

Evaluated against `release/6.1.0b1` at `fa998782`, using the November 3 diagnostic report as hypotheses rather than accepting its proposed implementation wholesale.

## Implemented

- **R1/R2:** classic wheel emission is separate from informational panels. Full modern charts skip the classic fragments they replace; wheel-only exports omit panels and grids; grid-only exports build only the requested grid. Full charts retain template-model validation, and partial exports retain escaped titles, descriptions and metadata.
- **A1/A2/A3:** runtime `Mapping` checks use `collections.abc`. Scalar effective orb windows are prepared once per distinct adjustment within an aspect calculation. Aspect-keyed and custom numeric adjustments keep the general path, including validation and overflow checks. Point membership and same-chart artifact partners are prepared locally without changing catalog order, closest-match selection or ties.
- **T1/T2:** translation copies specialize exact dict/string trees while retaining deepcopy's memo, cycles, aliasing and custom-type fallback. The drawer validates live source data directly. English is validated once while its exposed dictionary and fallback remain independent. Public accessors still return independent copies.
- **G1:** astrocartography prepares latitude tangents and rounded meridians once. Only sidereal time and equatorial coordinate reads remain inside the backend session; geometry and model allocation follow session cleanup.
- **Benchmark corrections:** styles are explicit, and the full pipeline no longer calculates and discards an extra set of aspects. Full charts, wheels, grids, optimization, translations and astrocartography are measured separately, with JSON sampling output.

No public signature, default, astronomical formula, backend dependency or golden SVG fixture changed.

## Measurements

Python 3.12.13, macOS arm64, libephemeris 4.0.0b1, LEB **base** tier, Pydantic 2.12.5, svg-polish 1.0.0. Offline inputs; logging disabled; three warmups followed by five blocks of ten calls (one call per block for minification and the 0.1-degree ACG grid). Each SVG timing includes a new drawer, with subjects and ChartData prepared outside the timer. The complete pipeline includes subject and ChartData construction.

Baseline and candidate ran in separate, sequential processes. Their peak process-tree RSS was 163.5 and 157.7 MiB respectively. Each run was supervised with a 1 GiB RSS limit. These are local warm measurements with a small corpus; small differences can be noise. They do not predict universal speedups or cold-start behavior. [Raw timing samples and environment](python-6.1.0b1.json) are included.

| Operation | Before, ms | After, ms | Time reduction |
|---|---:|---:|---:|
| Natal SVG (modern) | 2.035 | 1.466 | 28.0% |
| Synastry SVG (modern) | 4.616 | 3.567 | 22.7% |
| Natal wheel (classic) | 1.198 | 0.898 | 25.0% |
| Natal wheel (modern) | 1.874 | 1.009 | 46.1% |
| Synastry wheel (modern) | 4.203 | 2.392 | 43.1% |
| Natal aspect grid | 0.912 | 0.121 | 86.8% |
| Synastry aspect grid | 1.963 | 0.211 | 89.3% |
| Natal aspects | 0.120 | 0.080 | 32.9% |
| Synastry aspects | 0.282 | 0.196 | 30.6% |
| Translation pair (EN) | 0.072 | 0.025 | 65.2% |
| Astrocartography (step 0.1 degree) | 46.025 | 42.678 | 7.3% |
| Full natal pipeline (modern) | 2.801 | 2.260 | 19.3% |
| Natal SVG (modern, minified) | 34.548 | 33.945 | 1.7% |

Minification remains dominated by the SVG optimizer. Its behavior is preserved; the chart documentation now explains its cost and application-level asset reuse.

## Correctness and checks

- 1,470 output comparisons against the unchanged base: byte-identical SVG hashes and equivalent serialized models/ACG results. Covers natal, synastry, transit, composite, both return charts, progression, Gauquelin, sidereal charts, all shipped languages and glyph sizes, plus themes, transparency, CSS inlining and minification. Reproduce with `scripts/compare_performance_outputs.py` using the same backend/tier on both versions.
- Complete follow-up: **14,331 passed, 72 skipped** on the extended dataset with `LIBEPHEMERIS_LEB_READER=indexed`, `--tier=extended` and `-n 0`. Sampled process-tree peak RSS: **408.7 MiB**. The three GeoNames online tests also passed in a separate serial run (211.8 MiB).
- The two DST failures reproduced on the original branch are corrected by the separate test-only commit anchoring Havana's fold to the observed November 2025 transition. The complete suite now passes, including those cases.
- All **1,470** reference comparisons also match with indexed reads against the stored owned-reader outputs (sampled peak 106.3 MiB), preserving the calculation tier and result bytes.
- Complete `poe check` passed in an isolated checkout combining this branch with the resource-safety fix: Ruff, mypy, pyright, structural/fresh imports, **7,913 core tests**, **1,155 baseline-gate tests**, CLI smoke, **39 CLI examples**, and generated manpage verification. Sampled process-tree peak: **581.8 MiB**.
- The original `poe check` attempt inherited `-n auto` and launched 18 workers. [PR #274](https://github.com/g-battaglia/kerykeion/pull/274) makes test/cold-import parallelism opt-in and adds a monitored runner. Its sanitized system evidence records the kernel watchdog timeout and subsequent Jetsam memory-exhaustion event. Subsequent validation used one process, indexed reads and a 1 GiB sampled RSS stop threshold.
- The final combined `poe test:bounded` run passed **14,341 tests** (including ten resource-control regressions), with **72 explained skips** and a **415.0 MiB** sampled peak. The medium-only boundary configuration was verified separately: **26 passed**, no skips, **108.3 MiB** sampled peak. Three online tests passed separately. Full validation results and skip categories are recorded in PR #274.
- Regression tests cover independent translation graphs and fallbacks, live defaults, unused rendering stages, drawer reuse across styles/outputs, overlapping/tied aspect windows, custom unhashable numeric adjustments and ACG session boundaries. Existing golden fixtures are unchanged.

## Proposals not included

| Proposal | Decision |
|---|---|
| H1, prepared house geometry | Prototyped and removed. Less than 3% improvement on the measured subject workloads, including 52 active points; insufficient benefit for the added lookup plumbing. |
| R4/R5, metadata scans and collision geometry | No broad measured gain established. The report's isolated trigonometric change was near noise; preserve the existing geometry and interactive metadata. |
| V1, VoC candidate bracketing | Requires a separate numerical algorithm and an extended root/event corpus. Rejecting linear estimates outside the window is not a correctness-preserving shortcut. |
| E1/E2/TR1/TR2, streaming and prepared transit engines | Useful feature directions, but require explicit output/iterator contracts or a larger event-aggregation refactor. No hidden replacement of complete subject models or snapshot behavior. |
| S1/I1, serialization and lazy exports | No automatic change: JSON formatting and import/introspection behavior are observable contracts, and savings need workload-specific validation. |
| Q1, test scheduling; asset/result caches | No persistent/global result caches or weakened hermeticity guards. Default parallel test scheduling was not suitable for this local machine; validation was switched to a single worker and monitored RSS. |
| Other event solvers, midpoint indexes and compact ACG output | No measured transparent improvement established for this patch; retain tolerances, ordering and output shape. |

## Reproduction with bounded resources

```sh
# One process, using the base dataset; no xdist workers.
LIBEPHEMERIS_PRECISION=base uv run pytest tests/core/test_performance_contracts.py -n 0 -m 'not online'
LIBEPHEMERIS_PRECISION=base uv run python scripts/benchmark.py --rounds 5 --iterations 10 --json /path/to/timings.json
```

For source comparisons, run the same benchmark script and interpreter twice with `PYTHONPATH` pointing first to the base checkout and then to the candidate. Create a hash file with the comparison script on the base, then check that file on the candidate. Keep backend, tier and dependency versions identical. Avoid concurrent benchmark/test runs and do not use `-n auto` for a memory-constrained validation run.
