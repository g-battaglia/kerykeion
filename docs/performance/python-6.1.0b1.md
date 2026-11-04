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

Final validation compares base `fa998782` with candidate `bec2af40` (runtime optimizations plus timing metadata), on an Apple M5 Pro with 18 logical CPUs. The benchmark is identical for both source checkouts and records the actually imported source commit. Python 3.12.13, macOS arm64, libephemeris 4.0.0b1, LEB **base** tier, **owned reader on both versions**, Pydantic 2.12.5, svg-polish 1.0.0. Inputs are offline, hash seed is fixed, and logging is disabled.

Six independent A/B pairs ran sequentially, alternating order `AB, BA, AB, BA, AB, BA`. Each process used five warmup calls and seven blocks of 20 calls per operation (one call per block for minification and dense ACG). Wall time uses `perf_counter`; CPU time uses `process_time`. The table gives the median of six process medians per version. The range is the minimum/maximum reduction across the six pairs, **not a confidence interval**.

Every process ran through the resource-safety watchdog with a **512 MiB sampled RSS stop threshold**. Maximum observed process-tree RSS was **164.9 MiB**. The campaign launched only one benchmark process at a time and no concurrent tests. The RAM effect of switching to indexed reads belongs to PR #274 and is not included in these CPU comparisons.

**The full modern natal pipeline saves 0.605 ms per chart: 2.791 → 2.186 ms, a 21.7% reduction in both wall and CPU time.** Across individual pairs its wall-time reduction was 12.7–25.2%. This includes subject creation, ChartData, a new drawer and SVG generation, without minification. It excludes process startup and disk I/O.

Individual SVG rows include a fresh drawer, with subjects and ChartData prepared before timing. [All 12 process runs, source identities, wall/CPU samples and aggregate calculations](python-6.1.0b1.json) are retained. Negative reductions denote slower measurements.

| Operation | Before, ms | After, ms | Saved, ms/call | Wall reduction | CPU reduction | Paired wall range |
|---|---:|---:|---:|---:|---:|---:|
| Single subject (John Lennon) | 0.470 | 0.467 | 0.003 | 0.6% | 0.5% | -1.0–1.8% |
| Batch 5 subjects | 3.694 | 3.663 | 0.031 | 0.8% | 0.8% | -8.4–3.8% |
| Subject with all optional calcs | 1.660 | 1.666 | -0.006 | -0.4% | -0.3% | -11.8–2.9% |
| Subject sidereal LAHIRI | 0.613 | 0.614 | -0.001 | -0.1% | -0.2% | -26.7–2.5% |
| Natal aspects | 0.119 | 0.082 | 0.037 | 31.4% | 31.4% | 29.5–33.2% |
| Synastry aspects | 0.279 | 0.197 | 0.081 | 29.2% | 29.2% | 26.8–31.9% |
| Natal SVG (classic) | 1.289 | 1.199 | 0.091 | 7.0% | 7.1% | 4.3–14.2% |
| Natal wheel (classic) | 1.202 | 0.876 | 0.326 | 27.1% | 27.1% | 26.4–28.3% |
| Natal SVG (modern) | 2.014 | 1.437 | 0.577 | 28.6% | 28.6% | 27.8–29.4% |
| Natal wheel (modern) | 1.834 | 1.017 | 0.816 | 44.5% | 44.5% | 43.9–45.4% |
| Natal aspect grid | 0.927 | 0.125 | 0.802 | 86.5% | 86.5% | 86.3–86.7% |
| Synastry SVG (classic) | 3.191 | 3.100 | 0.091 | 2.9% | 2.9% | -4.3–6.9% |
| Synastry wheel (classic) | 2.924 | 2.065 | 0.859 | 29.4% | 29.4% | 28.8–31.6% |
| Synastry SVG (modern) | 4.602 | 3.582 | 1.020 | 22.2% | 22.2% | 20.4–23.0% |
| Synastry wheel (modern) | 4.129 | 2.368 | 1.762 | 42.7% | 42.7% | 41.5–43.1% |
| Synastry aspect grid | 1.925 | 0.209 | 1.716 | 89.2% | 89.1% | 88.9–89.5% |
| Natal SVG (modern, minified) | 34.364 | 33.982 | 0.382 | 1.1% | 1.2% | 0.3–3.4% |
| ChartData creation (Natal) | 0.192 | 0.151 | 0.042 | 21.6% | 21.5% | 17.8–22.7% |
| Translation pair (EN) | 0.074 | 0.025 | 0.049 | 66.0% | 65.9% | 64.9–67.0% |
| Astrocartography (step 1 degree) | 3.914 | 3.493 | 0.421 | 10.8% | 10.8% | 8.5–11.9% |
| Astrocartography (step 0.1 degree) | 49.443 | 44.915 | 4.527 | 9.2% | 9.2% | 4.4–12.8% |
| Full natal pipeline (classic) | 2.061 | 1.912 | 0.149 | 7.2% | 7.2% | 1.8–11.7% |
| Full natal pipeline (modern) | 2.791 | 2.186 | 0.605 | 21.7% | 21.7% | 12.7–25.2% |

The repeatable target gains are modern rendering (22.2–28.6%), modern wheel exports (42.7–44.5%), grid exports (86.5–89.2%), aspects (29.2–31.4%), translation-pair copies (66.0%) and ACG geometry (9.2–10.8%). These percentages describe different workloads and must not be added.

Control workloads show why a single library-wide percentage would be misleading. Subject-creation medians changed by less than 1%, and some individual pairs varied substantially; no subject-creation saving is claimed. Classic synastry rendering's 2.9% median improvement crosses zero across pairs, so it is not presented as a reliable gain. With minification, the total improvement is only 1.1% because the SVG optimizer dominates. No meaningful whole-process RAM reduction is claimed for this PR; the recorded RSS values define the safe measurement envelope.

These are warm local timings on a small deterministic corpus; system activity and CPU frequency were not pinned. Different dates, point selections, languages, workloads and cold-start conditions can change the result. There are no fragile wall-time assertions in CI.

## Correctness and checks

The final four-PR beta integration passed **14,662 unique cases** across the
strict Python 3.12/3.14 extended and medium-boundary matrix. All package and
documentation checks also pass; see the [final qualification](../../release_notes/v6.1.0b1-validation.md).
The earlier optimization-specific checks below retain their original scope.

- 1,470 output comparisons against the unchanged base: byte-identical SVG hashes and equivalent serialized models/ACG results. Covers natal, synastry, transit, composite, both return charts, progression, Gauquelin, sidereal charts, all shipped languages and glyph sizes, plus themes, transparency, CSS inlining and minification. Reproduce with `scripts/compare_performance_outputs.py` using the same backend/tier on both versions.
- Final strict matrix, combining this branch with [PR #274](https://github.com/g-battaglia/kerykeion/pull/274) and [test-coverage PR #275](https://github.com/g-battaglia/kerykeion/pull/275): **all 14,417 unique collected tests passed at least once**, with zero failures, unexpected warnings or unverified cases. Extended: **14,404 passed, 13 skipped**, including online and optional font/PNG tests; medium boundaries: **26 passed, zero skipped**. All 13 extended skips occur in the medium passed IDs; profile counts overlap. Both runs use `-n 0 -W error`, indexed reads and a 1 GiB sampled watchdog. Observed peaks: **489.1 MiB** and **160.5 MiB**. [Audit, source commits, set hashes and reproduction](https://github.com/g-battaglia/kerykeion/blob/release/6.1.0b1/docs/validation-completeness.md).
- The two DST failures reproduced on the original branch are corrected by the separate test-only commit anchoring Havana's fold to the observed November 2025 transition. The complete suite now passes, including those cases.
- All **1,470** reference comparisons also match with indexed reads against the stored owned-reader outputs (sampled peak 106.3 MiB), preserving the calculation tier and result bytes.
- Complete `poe check` passed in an isolated checkout combining this branch with the resource-safety fix: Ruff, mypy, pyright, structural/fresh imports, **7,913 core tests**, **1,155 baseline-gate tests**, CLI smoke, **39 CLI examples**, and generated manpage verification. Sampled process-tree peak: **581.8 MiB**.
- The original `poe check` attempt inherited `-n auto` and launched 18 workers. [PR #274](https://github.com/g-battaglia/kerykeion/pull/274) makes test/cold-import parallelism opt-in and adds a monitored runner. Its sanitized system evidence records the kernel watchdog timeout and subsequent Jetsam memory-exhaustion event. Subsequent validation used one process, indexed reads and a 1 GiB sampled RSS stop threshold.
- The earlier actual `poe test:bounded` task also passed (14,341 tests, 72 skips, 415.0 MiB). The strict matrix above supersedes that coverage result: PR #275 adds assertions for the formerly skipped node/frame/minified-geometry cases, and the optional assets are exercised. No golden fixtures were regenerated or numeric tolerances widened.
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

Use the same interpreter, installed dependencies and benchmark script for both checkouts. Set `PYTHONPATH` to the source checkout and verify `environment.source_commit` in each JSON result. The benchmark script used by this campaign is the version in candidate commit `bec2af40`; the base checkout need not contain that script version.

Run every command sequentially through `scripts/run_resource_limited.py` from PR #274:

```sh
PYTHONPATH=/path/to/source-checkout PYTHONHASHSEED=0 \
  KERYKEION_BACKEND=libephemeris KERYKEION_LEB_MODE=leb \
  LIBEPHEMERIS_PRECISION=base LIBEPHEMERIS_LEB_READER=owned \
  LIBEPHEMERIS_NETWORK_POLICY=sealed \
  /path/to/shared/python /path/to/resource-fix/scripts/run_resource_limited.py \
    --rss-limit-mib 512 -- /path/to/shared/python \
    /path/to/candidate/scripts/benchmark.py \
    --rounds 7 --iterations 20 --warmup 5 --json /path/to/run.json
```

Repeat six pairs with checkout order `base/candidate`, `candidate/base`, three times. Within each process, take the median block time; then take the median of the six process medians for each version. Saved milliseconds are `before - after`; time reduction is `100 * (1 - after / before)`. Compute each pair's reduction separately for the reported range. The CPU calculation uses the identical aggregation on CPU samples. Keep backend, tier, reader and dependencies identical, and avoid concurrent tests/benchmarks or `-n auto`.
