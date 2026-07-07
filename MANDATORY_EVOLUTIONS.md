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

<!-- Add further mandatory evolutions below, same structure. -->
