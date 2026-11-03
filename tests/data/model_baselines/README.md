# Model-specific scientific references

`libephemeris-4.0.0b1/` contains a separate native-v4 overlay. It does **not**
replace the legacy Python fixtures, SVGs or reports, and does not relax their
comparators. Unknown future engine versions fail rather than inheriting a
scientifically incompatible reference set.

- `positions.json`: angle/house and Arabic Parts records for all 41 existing
  subjects. Planetary and lunar reference data remain inherited from the legacy
  set and are still tested against their original budgets.
- `svg/`, `reports/`: 28 changed SVGs and the ancient-Rome report. The manifest
  explicitly shares the other 326 SVGs with their unchanged legacy files.
- `manifest.json`: hashes of all 398 legacy reference files, 12 input LEB2
  images, frozen-reference hashes, producer identity and independent checks.

The independent orientation control uses Skyfield 1.54 UT1 GAST and date-frame
poles, then closed-form horizon/meridian geometry. All 12 Placidus cusps also
use a separate LibEphemeris 3.2.2 `houses_armc` control with those independent
inputs. Central differences check rates against the existing report budget.
All 38 non-polar subjects are covered; the three polar subjects retain their
separate fallback/identity regression coverage. These are consumer-budget
checks, not absolute ephemeris accuracy certification or independent SVG
geometry certification.

With the complete extended input inventory and a preserved v3 environment:

```bash
LIBEPHEMERIS_PRECISION=extended LIBEPHEMERIS_NETWORK_POLICY=sealed \
  python scripts/generate_v4_model_baselines.py --check \
  --geometry-python /path/to/v3-environment/bin/python
```

The generator runs the real pytest recipes (including fixtures and setup),
requires their success and complete reachable SVG coverage, and never overwrites
an existing model set. `--check` recomputes in a temporary directory: reference
bytes and scientific/input qualification must agree exactly. Original producer
provenance stays frozen; a compatible consumer's source identity is printed
separately, not substituted into the original attestation. Legacy regeneration
commands refuse v4 output so they cannot overwrite v3 references accidentally.
