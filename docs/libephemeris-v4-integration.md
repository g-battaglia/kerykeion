# LibEphemeris 4.0.0 integration

Local consumer migration on `codex/kerykeion-libephemeris-v4`, based on Kerykeion
`b81527d689991f806f8ea991364b7c3fed4c4c41`. Kerykeion and its CLI remain 6.0.5;
this work does not publish a package, push a branch or create a pull request.

## Dependency and runtime behavior

- Distribution metadata requires `libephemeris==4.0.0`.
- Repository installs and `uv.lock` select the Rust repository at
  `b5b513d8d0cf7c91d6296f9b3bdd166be427ef25`, the integrated, qualified main.
- Actual LibEphemeris calls use its compiled Rust extension. Skyfield is absent
  from the isolated installation. The optional Swiss backend remains the
  `pyswisseph` distribution, 2.10.3.2 in the lockfile and validation environment.
- All three trace cleanup sites call a native token's `reset()` method when
  available, otherwise the existing ContextVar reset protocol. Exceptions from
  calculations retain the existing cleanup behavior.
- Optional legacy Skyfield error discovery uses a dynamic import; its absence
  neither creates a dependency nor prevents type checking. Native range errors
  remain hard errors.

## Validation

Local macOS arm64 validation uses only existing LEB files under
`/Users/giacomo/.libephemeris`, with network access sealed and automatic downloads
disabled. All 12 LEB2 asset hashes are unchanged. No ephemeris, astronomical
formula or numerical tolerance is modified in this consumer migration.

| Check | Result |
| --- | --- |
| Complete offline suite, Rust backend, Python 3.12 | 14153 passed, 3 existing failures, 73 skipped |
| Complete offline suite, Rust backend, Python 3.14 | 14136 passed, 3 existing failures, 90 skipped |
| Native/legacy token regression tests, each interpreter | 10 passed |
| Focused Python 3.14 tracing/provenance/stars/heliacal suite | 117 passed, 3 skipped |
| Rust edge profiles, both interpreters and both readers | 60 complete model/exception results exactly match the qualified captures |
| Swiss complete model/exception comparisons | 7 exact pairs against unchanged Kerykeion main |
| Complete offline suite, Swiss, Python 3.12 | 13680 passed, 19 existing failures, 530 skipped |
| Same Swiss suite on unchanged Kerykeion main | 13676 passed, the same 19 failing node IDs, 524 skipped |
| Public backend comparison suite | 30 passed; numerical outputs discarded |
| Ruff, MyPy, Pyright, CLI smoke, lockfile check | Passed |
| Library/CLI wheels and sdists | Built locally; wheel metadata and all three tracing fixes checked |

Python 3.14 uses the same locked runtime dependencies, pytest and fonttools;
Swiss is absent there, accounting for additional optional-backend skips. The
initial incomplete test environment's missing-fonttools failures remain in its
log; after installing that declared development dependency, the final complete
run has only the three baseline failures above.

The three Rust-backend failures are reproduced on unchanged Kerykeion main with
the previous LibEphemeris 3.2.2 installation and the same production data:

- Galileo 1564 and Newton 1643 SVG baselines: the existing numerical SVG
  comparator rejects small rendered-coordinate changes.
- `TestManPage.test_manpage_matches_the_parser_tree`: the committed page says
  6.0.4 while the package and generated parser page say 6.0.5.

These failures remain failures; no baseline is regenerated or tolerance widened.
Swiss failures are confined to existing historical chart cases and the same man
page. Swiss values/residuals are not retained as fixtures; temporary Swiss test
output directories are removed after the runs. Python 3.14 Swiss is not claimed.

### Focused failure diagnosis — 2026-10-30

The 18 Swiss SVG failures all have the same concrete consequence: Chiron is
omitted. Each baseline has 14 chart points; each generated chart has 13, with no
extra point and no non-finite position among the remaining points. The public
backend raises for Chiron: ten test cases report a missing file, while eight
report its restricted coverage. Theme variants repeat some underlying dates.
These classifications come only from public API diagnostics, not inspection of
Swiss source or data contents.

The installed local Swiss directory contains only `seas_18.se1`, `semo_18.se1`
and `sepl_18.se1`. Historical Chiron requests ask for absent `seas_06.se1`
(for example, year 800) or `seas_12.se1` (for example, year 1564). The eight
restricted cases are the four earliest subjects and their dark-theme variants.
The test tier detector probes only the Sun at years 1000/1700; Sun availability
does not establish Chiron coverage. At year 1000 its public returned flags
confirm Moshier fallback, yet the detector calls this `extended`. Thus the
detector admits historical snapshot tests while their required optional-body
data is unavailable.

Kerykeion removes the unavailable optional body from `active_points` and records
`ephemeris_calculation_failed` in `ephemeris_warnings`. That warning message is
not displayed in the resulting SVG. Chiron's indicator and associated aspects
are also absent. This is an actual completeness limitation for those historical
charts, rather than a numeric-tokenizer artifact or evidence of wrong values
for every remaining planet. Adding files cannot resolve the cases the backend
explicitly refuses as outside its supported coverage. A complete-chart consumer
must inspect warnings or explicitly reject omission of required points.

Both LibEphemeris cases retain all 14 points, with no public calculation errors
or non-finite positions. Against the old SVG metadata, maximum longitude shifts
are lunar: about 0.319653 arcsec (Galileo) and 0.142389 arcsec (Newton). Visible
degree-label comparison also crosses a one-arcsecond formatting boundary; the
differences therefore are not exclusively invisible SVG-coordinate roundoff.

On the identical current data, the maximum v4-versus-3.2.2 longitude difference
over all 14 points is 3.99041e-7 arcsec for Galileo (Mercury), and 9.07568e-5
arcsec for Newton (Moon). The larger mismatch with the saved images is already
present in 3.2.2. This supports a stale-reference diagnosis for the migration;
the crossed file/tier controls below isolate its cause more precisely. An SVG
is not an independent scientific reference, so no absolute-accuracy claim
follows from this comparison and no tolerance or fixture was changed.

A separate precision limitation is visible in the Galileo subject: Chiron uses
the existing `Keplerian` / `approximate` route in both versions. The date 1564 is
outside the installed stored-body coverage, which begins at 1600-01-01 and ends
at 2500-01-01. It must not be described as a fully qualified numerical
ephemeris. Newton uses the existing local LEB asset; v4 labels it
`unverified-local` rather than asserting a review.

Severity assessment: the manual header is a low-impact documentation defect;
the two LibEphemeris snapshots are a validation-configuration mismatch as
isolated below; missing Chiron is a meaningful
functional limitation whenever a historical chart is expected to include it.
Ignoring the structured warning can leave a user with an apparently complete
SVG that omits requested information. None is newly introduced by this branch.

### Isolated lunar root cause: mixed LEB tiers

The medium fixture/data association was tested without changing code, stored
images, tolerances or astronomical assets. Both original failing pytest cases
pass with the existing owner-root `medium_core.leb2` and tier `medium`
(`medium-two-snapshots.log`: 2 passed). Their maximum numeric SVG differences
are below 3e-8, against the unchanged 1e-4 threshold.

Crossed controls separate the runtime tier from the selected coefficient file:

| Runtime tier | Selected core file | SVG numeric slots beyond the original threshold, Galileo / Newton |
| --- | --- | --- |
| medium | medium | 0 / 0 |
| extended | extended | 7 / 4 |
| medium | extended | 7 / 4 |
| extended | medium | 0 / 0 |

The difference follows the loaded coefficient file. Public tier metadata maps
`medium` to DE440 and `extended` to DE441. The old images match the medium
data, while the complete qualification run explicitly selected extended data.
Consequently, the earlier stale-image suspicion is narrowed to a demonstrated
mixed-tier comparison; the test failures do not identify a Rust lunar
calculation defect. Keep the intended production tier and make fixture inputs
explicit, or qualify separate model-specific references. Do not widen a
tolerance or silently substitute medium for an extended calculation.

The manual root cause is also explicit in history: the page was last generated
for 6.0.4, while the 6.0.5 release changed both project versions without updating
that generated page. It has no numerical or backend effect.

One version-specific glyph playground expectation changes from true to false.
The old LibEphemeris 3.2.2 shipped/lifted comparison differed only in four SVG
`cx`/`cy` values at about 1e-14 wheel units. With Rust 4.0.0 those renders are
identical. The new assertion preserves exact string comparison and all other
glyph/diff tests; the generator continues to measure the active backend's
ceiling behavior. This is not an astronomical tolerance change.

Detailed local commands/results are in the ignored
`build/libephemeris-v4-validation/` directory. Local distributions are in
`dist/libephemeris-v4/`. The Rust edge check uses exact binary64 words, including
signed zero, and also verifies restoration of its enclosing native trace. These
are compatibility checks against qualified results, not a new independent
astronomical accuracy certification.

## Reproduction

```bash
uv sync --locked --all-packages --extra swiss --python 3.12

LIBEPHEMERIS_DATA_DIR=/Users/giacomo/.libephemeris \
LIBEPHEMERIS_PRECISION=extended \
LIBEPHEMERIS_LEB=/Users/giacomo/.libephemeris/leb/extended_core.leb2 \
LIBEPHEMERIS_NETWORK_POLICY=sealed \
LIBEPHEMERIS_AUTO_SPK=0 LIBEPHEMERIS_IERS_AUTO_DOWNLOAD=0 \
KERYKEION_BACKEND=libephemeris \
uv run --no-sync pytest tests/ -m 'not online' \
  --ignore=tests/core/test_backend_comparison.py -n 2 -q -o log_cli=false
```

The Git source makes repository installs reproducible before the owner publishes
LibEphemeris 4.0.0. Built Kerykeion distributions retain the ordinary exact
version dependency, without a Git URL or local path in their requirements.
