# Consumer-only fixes: manpage and glyph playground

The Kerykeion-owned defects reported in
[#23](https://github.com/g-battaglia/libephemeris-rust/issues/23) and
[#24](https://github.com/g-battaglia/libephemeris-rust/issues/24) are fixed in
branch `kerykeion-rusty-leb`. Main and the upstream Rust source remain unchanged.
The engine defect [#26](https://github.com/g-battaglia/libephemeris-rust/issues/26)
is still reproducible and remains separate: a green consumer suite does not
mean that historical stellar/live-anchor calculations are validated.

## #23 — regenerate the CLI manpage

Regenerated `cli/man/man1/kerykeion.1` from the real parser. The only source
change is its version line, **6.0.4 → 6.0.5**. `poe man:check` passes for all
49 command paths. Both the source test and the built CLI wheel were verified:
the wheel contains the exact regenerated 6.0.5 manpage, not an older cached copy.
The existing release/parser anti-drift gate is retained.

## #24 — measure the actual layout, not a backend label or SVG text

- The fixed chart fixtures do not change display positions when their ceiling
  is lifted. Their expectations now say so, independently of backend identity.
- `render_with_layout()` captures the real collision resolver's output while
  producing the real SVG. `ceilingBinds` is calculated from those placements,
  not from unrelated SVG-string differences.
- Layout signatures use the renderer's existing six-decimal rotation precision,
  canonicalize circularly equivalent 0/360-degree rotations, and ignore point
  ordering. This is presentation precision, not a changed astronomy tolerance.
- Added nine regression cases: a real-ink synthetic negative/positive pair,
  rotation precision/wrap checks, agreement with actual SVG point transforms,
  and four tests separating geometry changes from SVG text changes.
- The positive case jams two clusters diagonally with the **unchanged real
  small-outer profile**: its production 5-degree cap actively constrains the
  layout, and lifting it increases the gap. No production separation, measured
  ink metric or astronomical position was adjusted to manufacture that case.
- Regenerated the complete self-contained `scripts/glyph_playground.html`
  (270 charts). `ceilingBinds.small.synastry` now correctly reads `false`.
  Stale explanatory prose was corrected; ordinary renderer geometry is untouched.

## Completed verification

Native engine: `092368627e960af2859d45007ea9c352b4a28e03`, Python package
4.0.0.dev0, CPython 3.12.13. The force-rebuilt extension from the preceding
recheck was reused unchanged (SHA-256
`2150340dd0a11a9823b9b681596045ba05262e280b0bf72ed203803d9b84bd5d`).
Same local coefficient data and memory-bounded two-worker protocol. No
online/slow exclusions or fail-fast option were used.

| Run | Passed | Failed | Skipped | Pytest time |
|---|---:|---:|---:|---:|
| Targeted manpage/playground/decluttering, Rust | **138** | **0** | 0 | 1.67 s |
| Same targeted checks, Python v3.2.2 | **138** | **0** | 0 | 0.62 s |
| Complete Kerykeion suite, Rust extended | **14,235** | **0** | 72 | 118.09 s |
| Medium-only boundary cases, Rust | **13** | **0** | 0 | 0.25 s |
| Complete Python v3.2.2 consumer control | **14,223** | **0** | 72 | 119.69 s |
| Medium-only boundary cases, Python v3.2.2 | **13** | **0** | 0 | 0.24 s |

There are nine additional geometry tests compared with the previous run. The
Rust suite contains the same twelve native-integration/cache cases absent from
the v3 control. Extended skips keep their existing applicability/optional-asset
reasons; the thirteen medium-specific cases were exercised separately.

The Python v3 control is a fresh archive of unchanged main commit `b81527d6`
with **only the same four consumer fixes** copied in: generator, playground
HTML, playground tests and generated manpage. It uses the existing v3.2.2
interpreter/environment, not the v4-only integration code or its native tests.
Thus the result does not rely on changing the ephemeris engine to make the two
consumer failures disappear. The validation runner now prepares this separate
consumer reference automatically while retaining the untouched original archive
for numerical comparisons and benchmarks. Shell syntax and preparation were
checked, including byte-for-byte verification of the four copied files and
preservation of the original reference; its prepared v3 tree passes the 138
targeted checks and thirteen medium boundaries.

Library/CLI wheels and sdists build successfully. Isolated CLI wheel smoke
passes entry point, version/help, expected input-error handling, info, status and
installed man rendering. Ruff on the changed Python files, `man:check` and
`git diff --check` pass. No existing astronomical tolerances or golden
astronomical/chart baselines were changed.

## Engine work is not hidden by these fixes

The separate strict comparison still exits **1**:

- 2,457 cases; 2,319 shared successes;
- 28 matching error cases;
- **110 native-only historical ALDEBARAN failures**;
- no flag or successful-value differences above the existing consumer checks.

This is the already reported mixed-tier stellar-observer acquisition problem
in [#26](https://github.com/g-battaglia/libephemeris-rust/issues/26), not a new
consumer regression or a reason to weaken tests. The issue remains open; no
duplicate was created. Details and the independent ordinary-star reproduction
remain in [RUST_RECHECK_RESULTS.md](RUST_RECHECK_RESULTS.md).

Raw logs, JUnit XML, exit codes, strict comparison output and the independent
v3 source/control run are in `validation_output/consumer-fixes/`. The preceding
recheck and initial measurement artifacts are preserved.
