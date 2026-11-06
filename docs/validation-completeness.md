# Optimization test-coverage audit

This audit predates the four-PR beta integration. The later [published b2 qualification](../release_notes/v6.1.0b2-validation.md) covers 14,663 unique cases and package checks. Subsequent native-path work has its own [compatibility report](native-path-compatibility.md); these historical audit counts do not describe the current branch.

The verification checkout combines optimization PR #273, resource-safety
PR #274 and this test-coverage change. Validation uses one process, indexed LEB
reads and a 1 GiB sampled process-tree RSS watchdog. All runs use `-W error`:
unexpected Python warnings fail the tests.

## Result

| Profile | Passed | Skipped in this profile | Failures | Unhandled warnings | Sampled peak RSS |
|---|---:|---:|---:|---:|---:|
| Extended, including online and optional rendering/font tests | 14,404 | 13 | 0 | 0 | 489.1 MiB |
| Medium-only range boundaries | 26 | 0 | 0 | 0 | 160.5 MiB |

The audit records test identifiers, not just counts. Every one of the extended
profile's 13 skips occurs in the medium profile's passed identifiers. Across the
matrix, **all 14,417 unique collected tests passed at least once**, with **zero
unverified tests, failures or unhandled warnings**. Per-profile counts overlap and
must not be added as unique tests. The [machine-readable summary](validation-completeness.json)
contains all 13 cross-profile matches, medium passed IDs and complete-set hashes.

The 13 tests specifically assert behavior at DE440's medium-tier range boundaries.
Those dates are not range boundaries of the extended kernel; running them under
medium is the applicable test, rather than suppressing a failure or reducing the
dates used by the extended suite.

## Gaps closed

- **50 mean-node cases:** default-point reference fixtures contain true nodes
  only. Mean nodes are now explicitly requested and checked against the independent
  Swiss Ephemeris mean-node model. The existing `POSITION_ABS_TOL` is unchanged;
  the diagnostic comparison's maximum difference was 0.000520 degrees against the
  native suite's existing 0.01-degree tolerance. Missing mandatory point output is
  an assertion failure, not a skip. Existing true-node fixture assertions remain.
- **Three fixed-reference modes:** J1900, J2000 and B1950 can change longitudes
  without crossing sign boundaries. Their test now verifies longitude changes;
  the traditional-mode sign-change assertions and per-mode numeric references
  remain in place.
- **Four minified glyph checks:** stored relative paths are compared exactly to
  current glyph geometry passed through the same SVG optimizer. Surviving glyph
  inventories and all geometry attributes are checked. A mutation test proves a
  changed outline fails. No numeric tolerance or baseline regeneration is used.
- **Optional asset tests:** the three font files were fetched into the ignored
  cache and verified using the generator's existing hashes, without invoking its
  template-writing entry point. CairoSVG and Pillow were provided to an isolated
  test environment. Both generator reproducibility and PNG rendering checks ran.
- **Warnings:** deprecated settings-API tests require exactly their documented
  warning. The independent altitude oracle opens the same bundled DE421 file
  directly and explicitly uses Skyfield's built-in timescale. It no longer checks
  expiration of the unrelated `finals2000A.all` file it never consumed. No warning
  filter, changed timescale table or broader assertion tolerance was introduced.

Only tests and validation documentation change. Production code, reference
fixtures and dependency pins are untouched by this coverage change.

## Reproduction

Apply all three PRs to the verification checkout, retain the installed extended
and medium LEB datasets, and keep the font files unchanged while testing. For
optional rendering on this Mac, the existing Cairo library was made visible with
`DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib`.

Use an isolated environment with the optional renderers and populate only the
font cache (not the templates):

```sh
uv run --isolated --frozen --all-extras --with cairosvg --with pillow python - <<'PY'
import runpy
builder = runpy.run_path('scripts/build_chart_glyphs.py', run_name='cache_only')
for name in builder['FONT_SOURCES']:
    font = builder['fetch_font'](name)
    font.ttf.close()
PY
```

Run the extended suite, including online tests, under the resource watchdog:

```sh
LIBEPHEMERIS_PRECISION=extended LIBEPHEMERIS_LEB_READER=indexed \
  uv run --isolated --frozen --all-extras --with cairosvg --with pillow \
  python scripts/run_resource_limited.py -- \
  python -m pytest tests/ --tier=extended -n 0 -W error -q -rs
```

Run the medium profile separately, with `LIBEPHEMERIS_PRECISION=medium`,
`--tier=medium`, and the identifiers listed in
`profiles.medium_boundaries.passed_ids` in the JSON summary. Keep `-n 0 -W error`.
No benchmarks or other test commands ran concurrently with this matrix.
