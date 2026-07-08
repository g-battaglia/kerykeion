# Mandatory Evolutions

Work that is **not an as-is bug** (the current implementation is internally
correct and documented) but that **must** be done in a future cycle to remove a
structural limitation. Distinct from the zero-bug review campaign, whose scope is
correctness of the current code. Each item is a deliberate, scheduled change with
its own review — not something to fold into a bug-fix round.

Status legend: 🔴 not started · 🟡 in progress · 🟢 done

---

## 1. 🔴 Migrate timezone handling from `pytz` to `zoneinfo`

**Why (limitation being removed).** `pytz` compiles only the *explicit* IANA DST
transitions, which end around 2037. Beyond the last compiled transition it
**freezes** the offset at the last known entry instead of applying the zone's
perpetual POSIX rule. For a birth/event date past ~2037 in a DST zone (e.g. a
summer 2038+ `America/New_York` chart) the resolved instant can be off by one
hour (Moon ≈ 0.55°, angles up to ~15°). The ephemeris range reaches 2650, so
future charts are in scope. `zoneinfo` (stdlib ≥ 3.9) reads the TZif POSIX
footer and extrapolates future DST correctly.

Documented meanwhile as a "Known limitation" in `CHANGELOG.md`.

**Secondary benefits.** Removes the `pytz` API footguns the codebase currently
works around: mandatory `tz.localize()` (never the `datetime(tzinfo=…)`
constructor — it attaches the LMT offset), `tz.normalize()` after arithmetic,
and `is_dst=` disambiguation. `zoneinfo` uses the standard PEP 495 `fold`
attribute instead and handles wall-clock arithmetic natively.

**Scope (files with pytz coupling — audit before starting).**
- `kerykeion/astrological_subject_factory.py` — the core local↔UTC conversion,
  DST fold handling via `is_dst`, `from_current_time`, partial-date defaults.
- `kerykeion/ephemeris_data_factory.py` — per-step localize/`astimezone`.
- `kerykeion/moon_phase_details/factory.py` — the `tzinfo.normalize(...)` call
  for solar-noon offset.
- `kerykeion/relocated_chart_factory.py`, `kerykeion/utilities.py` (`safe_timezone`),
  and any `import pytz` / `.localize(` / `.normalize(` / `is_dst` site
  (`grep -rn "pytz\|localize\|normalize\|is_dst" kerykeion/`).
- `pyproject.toml` — drop the `pytz` dependency (add `tzdata` for platforms
  without a system tz database, e.g. Windows).

**Risk.** High. Rounds 16–17 built careful DST-fold handling on the pytz
`is_dst` model; the fold/ambiguous/non-existent-time semantics must be
re-expressed on PEP 495 `fold` with identical results. Extensive golden
baselines (positions, houses, reports, SVG) encode current instants — most are
pre-2037 and must stay byte-identical; only post-2037 DST-zone cases should
change (and become correct).

**Acceptance criteria.**
- All existing tests pass; pre-2037 instants byte-identical (no baseline churn
  except intentional post-2037 corrections).
- New tests: a summer 2038+ chart in a DST zone resolves to the DST offset
  (matching `zoneinfo`), spring-forward gap and fall-back fold still handled.
- `import pytz` gone from `kerykeion/`; the CHANGELOG limitation note removed.
- Quality gate green.

---

## 2. 🔴 Canonical backend-error taxonomy + runtime name validation

**Why (limitation being removed).** The library repeatedly rediscovers, module
by module, that the ephemeris backend does *not* raise `RuntimeError` for its
failures (libephemeris raises an `Error` hierarchy — `CalculationError` /
`EphemerisRangeError`, `DataNotFoundError` / `UnknownBodyError`, `ConfigurationError`;
pyswisseph raises a generic `swisseph.Error`). Three modules independently
learned this the hard way (`dominants/utils.py`, `lunations/lunation_factory.py`,
and — fixed in round 23 — `moon_phase_details`, `void_of_course_moon`,
`heliacal`). Each site resolves the backend error type ad hoc with
`getattr(ephe, "Error", …)`. There is no single source of truth that also
distinguishes the *range* / *data* / *config* subtrees, so "expected no-event"
vs "hard failure" is re-derived everywhere and easy to get wrong (round 23's
HIGH was exactly this: heliacal treating every backend error as "no event").

**Scope.**
- Export a canonical tuple/enum from `kerykeion/ephemeris_backend.py`, e.g.
  `BACKEND_ERROR_TYPES` (the base) plus distinguishable `BACKEND_RANGE_ERRORS`,
  `BACKEND_DATA_ERRORS`, `BACKEND_CONFIG_ERRORS`, resolved once for the active
  backend (swisseph collapses to the generic `Error` — document that these
  cannot be told apart there). Include the *Skyfield* `EphemerisRangeError`
  (libephemeris runs `heliacal_ut` through Skyfield, which raises its own
  `ValueError` subclass — round 23 discovered this).
- Migrate every ad-hoc `getattr(ephe, "Error", …)` handler and the remaining
  dead `except RuntimeError` site (`sun_times/utils.py:346`, left untouched in
  round 23 because no harm was reproduced) to the canonical types.
- **Runtime validation of open `str` name parameters** at public entries whose
  type is only a `Literal` at static-check time (no runtime enforcement for
  API/JSON/form callers): aspects `active_points`, heliacal `planets` and the
  fixed-star-accepting `planet_name_or_star` (validate against the
  fixed-star catalog so a mistyped star yields "unknown body", not a misleading
  "no event found"), `active_fixed_stars`. Round 23 hard-validated only the
  closed `PLANETS` set in `search_events`; the star-accepting entries still
  return a correct exception *type* but an imprecise message.

**Risk.** Low–medium. Mostly mechanical, but the range/data/config split must
match real backend behavior on both backends, and tightening name validation
could reject inputs some caller currently relies on failing softly — audit
tests for expected soft-failures first.

**Acceptance criteria.**
- One canonical error taxonomy in `ephemeris_backend`; no module resolves the
  backend error type ad hoc; no `except RuntimeError` left for a backend call.
- A mistyped fixed-star name to `next_heliacal_rising` raises an "unknown body"
  `KerykeionException`, not "no rising found in the search window".
- All existing tests pass; new tests cover each name-validation entry and the
  range/data/config discrimination on the default backend.
- Quality gate green.

---

## 3. 🔴 Surface degraded/substituted points on the model (swisseph-without-data)

**Why (limitation being removed).** With the `swisseph` backend installed but its
`.se1` data files not yet fetched (`python -m kerykeion.swisseph_setup`), swisseph
runs on its Moshier analytical fallback. In that state several points silently
degrade and a user diffing against the `libephemeris` backend gets a materially
different chart with only scattered log lines to explain it:
- **Planetocentric perspectives** (e.g. `Marscentric`): a point whose `calc_pctr`
  needs a missing planetary kernel (notably the **Sun**, which needs `sepl_18.se1`)
  falls back to its **geocentric** position — returned under the planetocentric
  label, ~62° off, with only a `logging.warning`. The fallback is deliberate and
  logged (see the comment at `astrological_subject_factory.py` ~2353), but the
  point is not flagged as degraded on the returned model.
- **Chiron / asteroids / TNOs** need `seas_18.se1`; **fixed stars** need
  `sefstars.txt`; **barycentric** perspectives need `sepl_*.se1`. These are
  dropped (set to None / removed from `active_points`) with a log line.

The `libephemeris` default backend and a fully-provisioned `swisseph` install are
both correct — this is only the incomplete-swisseph state. The test suite
`conftest.py` fail-fasts there, so it is invisible to CI but reachable by a real
user immediately after `pip install kerykeion[swiss]`.

**Scope.**
- Add a machine-readable degradation signal on the subject model (e.g. a
  `degraded_points: list[str]` / per-point `is_degraded` flag) so a consumer can
  detect a substituted/dropped point without scraping logs.
- For the planetocentric Sun (and any pctr point) that cannot be computed,
  reconsider substituting a *mislabeled geocentric* value vs. dropping it (as
  lunar nodes are dropped for non-geocentric perspectives) — the two degradation
  philosophies in `_calculate_planet` are currently inconsistent.
- Consider a one-time prominent runtime warning when swisseph is active without
  data files (parallel to the import-time Moshier warning), pointing at
  `swisseph_setup`.

**Risk.** Low. Additive model field + a consistency decision on the pctr
fallback. No change to the correct (libephemeris / provisioned-swisseph) paths.

**Acceptance criteria.**
- A degraded/substituted point is detectable from the returned model, not only
  from logs.
- The planetocentric-fallback philosophy is consistent with the lunar-node
  drop-don't-fake rule (documented either way).
- Quality gate green; libephemeris output unchanged.

---

## 4. 🔴 Post-hoc house-cusp partition validation (southern-polar backend defect)

**Why (limitation being removed).** `houses_ex2_with_polar_fallback` trusts the
backend to *raise* `POLAR_HOUSES_ERROR_TYPES` when a quadrant house system is
undefined inside the polar circle, and only then clamps to the ±66° limit. But
at deep **southern** latitudes (onset ~−67°, inside the Antarctic circle) the
bundled `libephemeris 3.0.0rc1` does **not** raise for Campanus (`C`),
Regiomontanus (`R`), Polich-Page (`T`), APC (`Y`) and Sunshine (`I`) — it
silently returns **non-partitioning cusps** (they run backwards, so the 12
consecutive `abs_pos` gaps sum to ~3960° instead of 360°) and a **Medium Coeli
flipped by 180°** (MC is a function of RAMC only and cannot depend on latitude).
`Sunshine` (`I`) additionally collapses several cusps onto a single longitude
whenever the Sun is circumpolar, in *both* hemispheres (its sibling `i` correctly
raises and falls back). Because nothing is raised, the polar fallback never fires
and the degenerate cusps reach the model, silently mis-assigning every house.
Reproduced round 29 (config-matrix lens); the northern-polar equivalents and
every other house system are correct, and the four angular cusps are correct.
Root cause is the backend (this is the pre-6.0.0 `libephemeris` rc — the same
release blocker); real-world impact is nil (no Antarctic-circle births).

**Scope.**
- Add a cusp-partition validator (the 12 consecutive gaps each strictly in
  `(0, 360)` and summing to 360 within tolerance; also reject any ~0-width house
  to catch the Sunshine collapse). Run it on the cusps returned by
  `houses_ex2_with_polar_fallback` **whether or not** the backend raised.
- On a degenerate result: route through the existing clamp-and-retry path (the
  ±66° clamp recovers `C`/`R`/`Y`/`I`). If the clamped retry is *still*
  degenerate (`T`/Polich-Page is degenerate at the −66° clamp target itself, and
  `I` when the Sun stays circumpolar), raise a clear `KerykeionException`
  ("house system undefined at this latitude") rather than shipping bad cusps —
  the same never-ship-garbage contract used for the raised case.
- Validate the clamped retry on the **raised** path too (currently returned
  unvalidated), so both paths share the guarantee.
- **Report upstream to `libephemeris`**: the backend should raise (as it does in
  the northern hemisphere and for Placidus/Koch) instead of returning a
  180°-flipped MC and backwards cusps at southern-polar latitudes. Prefer the
  upstream fix; the kerykeion validator is defense-in-depth.

**Risk.** Medium. Touches the core house-computation path. The validator must
never false-positive on legitimately narrow-but-valid polar quadrant houses
(valid cusps at ±66° can have &lt;0.5° houses but still sum to 360°); key on the
partition sum + zero-width test, not a min-gap threshold. Changes the error
contract for `T`/`I` at southern-polar latitudes (silent garbage → clear raise);
audit tests/goldens for any southern-polar chart using these systems first
(none found in round 29).

**Acceptance criteria.**
- No config ever returns cusps whose gaps do not partition [0, 360); degenerate
  backend output is either clamped to valid cusps (with the existing warning) or
  raises `KerykeionException`.
- New tests: `C`/`R`/`Y`/`I` at −78° recover valid partitioning cusps with the
  correct (un-flipped) MC; `T` at −78° and `I` with a circumpolar Sun raise a
  clear exception; northern-polar and normal-latitude output unchanged.
- Upstream `libephemeris` issue filed (link recorded here).
- Quality gate green.

<!-- Add further mandatory evolutions below, same structure. -->
