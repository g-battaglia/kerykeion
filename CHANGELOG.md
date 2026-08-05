# Changelog

## [Unreleased]

## 6.0.0a79 - 2026-08-05

### Fixed

- **`solar_noon` is now the meridian transit, which is what it always claimed to
  be.** It was the midpoint between sunrise and sunset. The two coincide only
  while the Sun's declination is stationary, so the old value was right at the
  solstices and on the equator — where anyone spot-checking it would look — and
  wrong everywhere else: measured against two national observatories, +21.5 s at
  Rome on the equinox, +33.5 s at Ushuaia, +62.4 s at Reykjavík. Worse, when the
  rise/set pair straddles local midnight the midpoint lands on the wrong civil
  day entirely, which is what Singapore did. Nothing in the library consumed the
  field — it is printed in the report, serialised into the AI context and
  returned to callers — so the correction is visible rather than structural.
  - `solar_noon` is now also reported on **polar days and polar nights**, where
    it previously had to be `None`. A transit is a meridian crossing, not a
    horizon crossing: the Sun culminates on a day it never rises. `day_length`
    stays `None` there, since there is no pair to measure.
  - `MoonPhaseSunInfoModel.solar_noon` moved with it, and stays in the subject's
    local timezone as before.
  - **New contract, stated because it is a real regression for one case class.**
    The transit is now searched independently from local midnight instead of
    being derived from the pair, so `sunrise < solar_noon < sunset` is no longer
    guaranteed. It holds for every location whose timezone matches its longitude
    (0 violations in 300 matched city/zone samples), and fails when they do not:
    65 of 300 random lat/lon/zone triples, 75 of 300 with `tz_str="UTC"` at
    arbitrary longitudes. Measured worst case: 62.71 N / 121.43 E under UTC
    reports a solar noon 15 hours BEFORE its sunrise, because the two belong to
    different solar days. The old midpoint was inside the window by construction
    and was, for this class alone, better. Both the library API and
    `/api/v6/sun-times` accept latitude, longitude and timezone as an
    unvalidated triple, so it is reachable — pass a timezone that belongs to the
    longitude and it cannot occur.

### Added

- **Sunrise, sunset and solar noon are now anchored to published data we did not
  produce.** `tests/core/test_sun_times_anchors.py` carries values transcribed by
  hand from the US Naval Observatory and from IMCCE (Observatoire de Paris) for
  the same UTC civil day, with the capture date recorded. No script regenerates
  them: a golden snapshot proves constancy, an anchor proves truth, and only the
  second kind survives a bad engine bump followed by a blind regeneration.
  - The tolerances are shaped by what the sources actually do rather than by what
    would be convenient. The two agree on sunrise and transit, so those are held
    to 45 s of USNO; they disagree by about two minutes on sunset (a horizon
    convention), so every event is additionally required to lie inside the span
    the two of them bracket. Above 60° latitude no time-domain claim is made at
    all — the Sun grazes the horizon there and clock time stops being a
    well-conditioned way to state an error, which the sources demonstrate
    themselves by differing by 10 and 11 minutes at Tromsø. A test asserts that
    divergence, so the cut-off is earned rather than assumed.
- **An angle-based check that does not degrade with latitude.**
  `tests/core/test_sun_times_altitude_invariant.py` never compares times: it takes
  the instant we return and asks Skyfield — a separate position pipeline — where
  the Sun was. Across ten sites and four seasons the true upper limb sits at
  −33.59′ with a spread of 2.5″, solar noon has an hour angle under 0.1 s, and
  `is_diurnal` flips within a second of the geometric centre crossing zero.
  - The documented gap between sunrise and diurnality (3.3 min at the equator,
    4.4 at Rome, 8.2 at Reykjavík) is pinned there too, so the prose cannot drift
    away from the code.

### Changed

- `libephemeris` floor raised to **>=3.0.0,<4** (from the exact `==3.0.0rc15`).
  Validated rather than assumed, and the evidence is worth stating precisely
  because a first draft of this entry overstated it.

  The cross-engine parity campaign, run against a file-backed reference before
  and after, returned **identical per-domain counts over 5213 compared
  quantities** and no divergence appearing or disappearing. Note the verdict it
  returns is RED in both runs — the pre-existing sidereal-ayanamsa and
  deep-time offenders — so "identical" means unchanged, not clean. The campaign
  was also run under kerykeion `6.0.0a75`, the version its lockfile pins.

  Two further measurements come from ad-hoc scripts rather than from that
  campaign, and are reproducible but not archived in any repository: a
  value-by-value diff of 16337 quantities found 16267 bit-identical, and the
  eight Uranian points move from a ±20″ scatter against the reference to a
  uniform +2..3″ bias (8 of 9 improve, Kronos by 20″). The parity grid does not
  cover the Uranian family at all, which is exactly why those bodies could move
  36″ and pass 5213 comparisons unseen.

  What the fixtures show directly: **exactly eleven points changed position** —
  the eight Uranian points, White Moon, mean Lilith and mean Priapus, every one
  analytically modelled. No planet, angle or cusp changed POSITION.

  SPEEDS did, and this is where a first correction of this entry was itself
  wrong — it said 80 cells, which is the number of (fixture, angle) pairs, not
  of table cells; dual charts carry the same angle two or three times per file.
  Counted properly: **104 angle-speed cells** (Ascendant 37, Medium Coeli 37,
  Descendant 15, Imum Coeli 15) across 28 fixtures, plus **122 non-angle speed
  cells** — the Uranian points and, not previously named anywhere,
  True Lilith 12, True Priapus 12 and Interpolated Perigee 11 — and
  **19 declination cells** (Mean Lilith 8, Mean Priapus 8, Hades 1, White
  Moon 1, Admetos 1 — a first count said 17, having taken the dual-return
  fixture's Lilith and Priapus rows once when that file carries them in both
  its tables: the very duplicate-cell trap this paragraph warns about).
  `ascmc_speed` comes from `houses_ex2`; the parity
  front excludes cusp and angle speed by design, so the campaign could not have
  seen any of it.

  Magnitudes: the scale-free figure is **five parts per million** (5.15–5.74 over
  all 104 cells). In absolute terms the MC and IC move about 0.002 °/day; the
  Ascendant's median is 0.0016 with a worst case of 0.0046, so "about 0.002" is
  right for two of the four angles and loose for the other two.

  Two knock-on effects worth naming rather than leaving to be discovered: one
  report gains an aspect row (`Pallas sesquiquadrate Poseidon`, an orb-boundary
  crossing) and three Zeus aspects flip their Movement column to `Static` as its
  speed crosses the 0.001 °/day display floor.

### Documentation

- The rise/set horizon convention is now stated where callers will meet it: the
  apparent upper limb, a semidiameter taken from the real distance rather than a
  fixed 16′, standard-atmosphere refraction, and a level sea horizon at any
  elevation. Both the README and the model docstrings say plainly that sunrise
  and `is_diurnal` answer different questions and must never be derived from one
  another.
- `_APPARENT_UPPER_LIMB_HORIZON_DEGREES` now explains why the polar
  discriminator's textbook −0.833° differs from the −0.827° the search itself
  implies, and why closing that 0.006° gap would buy nothing.

## 6.0.0a78 - 2026-08-05

### Added

- Charts now report their **diurnality** — whether the Sun stood above the
  horizon or below it — on a sixth line of the bottom-left info panel, reading
  `Diurnality: Diurnal` or `Diurnality: Nocturnal`. The value has always been on
  the subject as `is_diurnal`, computed from the Sun's true geometric altitude
  and therefore correct for sidereal and heliocentric charts and at polar
  latitudes; until now nothing drew it. The same line was added to the text
  report. The wording is deliberately descriptive rather than doctrinal: where
  the Sun was is an observation every tradition shares, while "sect" is one
  tradition's name for what follows from it and does not belong in a neutral
  info panel.
  - Two-wheel charts report both wheels, because diurnality belongs to a single
    chart and the same placement reads differently under each: a transit shows
    `Natal Nocturnal · Transit Diurnal`, a synastry names both subjects
    (shortened, like every other name in that panel). A bare value on a biwheel
    would be worse than no line, since the reader could not tell which chart it
    described. That row carries no `Diurnality:` heading. The reason is the
    budget rather than the total: the row has about 228px of clear width, the
    values and separator are fixed, and what is left is shared between the two
    wheel names — so a heading would not overflow the row, it would come
    straight out of the names. (Measured with `estimate_text_width`, the headed
    English form is 196px and fits; nine of the ten shipped languages do, Hindi
    being the exception at 314px. An earlier draft of this entry said it did not
    fit, which was checkably wrong.) The names are cut to that width rather than to
    a character count, since eight ideographs are twice the width of eight Latin
    letters: `kerykeion.charts.glyph_metrics.estimate_text_width` is the public
    entry point (re-exported from `chart_drawer` for convenience). Note this is
    *not* what sizes the planet grid, the legend or the auto-size canvas —
    `ChartDrawer._estimate_text_width` still uses its own 0.7-of-the-em average
    there. Pointing that at the measured table is a layout change (28 baselines
    move — 27 under `tests/data/svg` plus the gallery's transit chart, and none
    under `docs/charts` — one canvas from 1244px to 1177px) and belongs in a change about grid
    geometry, not in this one. It charges each character the widest advance that character has
    across Times, Helvetica and Arial Unicode, rounded up, so it reads at or
    above what those three render. Regenerate the table with
    `poe regenerate:glyph-widths` if the reference set changes. Known residual,
    since the panel names no font-family: under a CJK system font the
    Ambiguous-width characters — Cyrillic, Greek, the middot — render full-width,
    wider than any of the three reference faces.
  - The line is omitted, not guessed, on every perspective not cast from the
    Earth — eight of the eleven, of which seven draw a Sun that is not the one
    measured and one (heliocentric) draws none at all. `is_diurnal` comes from a tropical *geocentric*
    Sun, so a Marscentric or Selenocentric chart draws a Sun that is not the one
    measured: on a Liverpool nativity the measured Sun is at 196° while the
    Marscentric wheel draws 354°, and the panel was asserting "Nocturnal" one row
    under `Perspective: Marscentric`. Apparent Geocentric, True Geocentric and
    Topocentric keep the line — they differ by parallax and aberration, never by
    a hemisphere.
  - The line is omitted, not guessed, where it has no referent: a heliocentric
    chart excludes the Sun (it is the centre body), and a midpoint composite
    represents no single sky (`is_diurnal` is `None`). Note a heliocentric chart
    does still have an Ascendant and houses — the objection is the missing Sun,
    not a missing horizon. Note that `resolve_sect_is_diurnal`
    defaults a missing value to day, which is right for calculations that must
    pick a branch but would mislabel a composite here.
  - `ChartDrawer(..., show_diurnality=False)` omits it entirely. Nothing shifts
    to accommodate the line — the rows below the wheel's centre get wider the
    lower they sit, and the new one lands in the widest band of the six. Only the
    moon glyph moves, dropping 14px out of its way, and only when a line was
    actually produced. Heliocentric charts and midpoint composites therefore keep
    the previous layout too, as does any caller who opts out.
  - New translation keys `diurnality`, `diurnal` and `nocturnal` in all ten
    shipped languages, plus `heliocentric_return` and `node_return` for the
    mislabelled return types under *Fixed* — five keys, all with English
    defaults so an older third-party pack still validates.

### Changed

- **Breaking for direct constructors of `ChartTemplateModel`:** the new panel row
  adds a required field, `bottom_left_5`. The model is public, so code building
  one by hand now raises a pydantic `missing` error until it supplies the key.
  Required rather than defaulted on purpose, and the opposite call from the
  language keys above: a language pack is written by a third party against a
  released version and cannot be fixed retroactively, whereas this model is
  filled in by a renderer in this repository — a renderer that forgets the row
  should fail loudly at validation rather than silently draw a chart with a
  blank line where the value belongs. Callers using `ChartDrawer` are unaffected.
- `uv.lock` no longer carries `[options] prerelease-mode = "allow"`. Not a
  deliberate policy change: the block came from a `--prerelease` flag passed at
  lock time, `pyproject.toml` declares no `[tool.uv]` section, and current uv
  writes the lock without it — which is also what makes `uv lock --check` pass
  here and fail on the previous release. Verified inert: the lock resolves the
  same 58 packages at the same versions, the only difference being kerykeion's
  own bump. The `libephemeris==3.0.0rc15` pin is explicit, so the default
  `if-necessary-or-explicit` mode still admits it.

### Fixed

- Heliocentric returns and lunar node crossings announced themselves as **"Lunar
  Return"** in the chart's Type line — and, once the diurnality row shipped, on
  that row too — contradicting the `return_type` in the same response. The label
  was a Solar/else-Lunar binary written when those two return types did not
  exist; it is now a map over all four — and over every heading and filename,
  not just the Type line: the chart title, the dual chart's outer planet grid and its
  house-comparison width estimators were four further copies of the same binary,
  so a heliocentric return read `Type: Heliocentric Return` under a title ending
  "Lunar Return". Two more turned up after that: the default filename suffix,
  where a heliocentric and a node return for one subject collided on the same
  name and the second overwrote the first, and the Italian `return_aspects`
  heading, which hardcoded "Ritorno Solare" on the aspect grid of every return
  type — nine of the ten packs were already generic, so an English-only check
  could not see it. The text report reuses the same mapping now too, rather than
  deriving "Lunar Node Crossing" where the chart says "Node Return". Two of the four `ReturnType` values
  carried the wrong label — which downstream is most of what gets asked for:
  Astrologer Studio's return picker offers eight bodies, six of which route to
  one of those two. The mapping reads `return_type` by duck-typing: an
  `isinstance` gate on `PlanetReturnModel` had reinstated the very binary this
  entry describes, discarding the declared type of anything else and labelling it
  Lunar — reachable through `kerykeion.report`, which reads subjects with
  `getattr` by design. A type the map does not know now yields the neutral
  `Return` — the key every pack already ships (`Ritorno`, `Rückkehr`, `回归`) and
  which the house-comparison grid already renders — rather than borrowing the
  lunar label. An unhashable `return_type` is treated as absent instead of
  raising: widening the read to duck-typed subjects had made a list or a dict a
  `TypeError` where the old code returned a label. Caught from the lookup rather
  than screened with `isinstance(str)`, so a `UserString` or a lazy-translation
  proxy — which hash and compare equal to `str` without subclassing it — still
  match the map. (A `str`-mixin enum resolves too, but it always did: it is a
  `str` subclass, so it satisfied the screen as readily as the fix.)
- Never shipped in this state, recorded because the reasoning is worth keeping:
  the five new translation keys were first declared **required** on
  `KerykeionLanguageModel`, which would have rejected every third-party language
  pack written against an earlier release with a pydantic `missing` error, and
  its author could not have fixed a release already out. All five carry English
  defaults, as the sixteen keys added before them do.

## 6.0.0a77 - 2026-07-21

### Fixed

- Births before 1902 no longer fail in the minutes around a zone's adoption of
  mean or standard time. Those adoptions move a clock once and permanently, and
  the tz database records them in the same shape as a summer-time change, so
  6.0.0a76 rejected the skipped or repeated wall times as ambiguous and told the
  caller to answer with `is_dst` — a question about daylight saving, which did
  not exist yet. `Europe/Rome` on 1893-10-31 between 23:49:56 and midnight,
  `America/New_York` in the four minutes noon struck twice on 1883-11-18,
  `Australia/Adelaide` in the half hour it skipped on 1899-05-01: 264 of the 598
  zones carry at least one such window. Below 1902-01-01 a non-unique wall time
  now resolves to the offset in force before the change and logs at INFO instead
  of raising. The date is what decides, because nothing else can: the earliest
  seasonal transition anywhere in the database is from 1916, and the `dst()` flag
  that would otherwise tell an adoption apart from a summer-time fold is encoded
  with opposite signs by different builds of the database. The modern contract is
  unchanged — an ambiguous or non-existent time from 1902 onwards still raises.
- A midpoint composite no longer overwrites the requested house system with the
  substituted one. Two subjects inside the polar circle who both asked for
  Placidus hold Porphyry cusps, and 6.0.0a76 reported `houses_system_identifier`
  as `"O"` on the composite — so relocating that relationship to a temperate
  latitude carried a substitution forced by somewhere else, with nothing left to
  say why. The requested pair is kept, the parents' own `polar_house_fallbacks`
  records travel with the composite, and `effective_houses_system_identifier`
  reports Porphyry as it does on a subject. Composing parents whose cusps came
  from *different* divisions still raises: each composite cusp is the circular
  mean of the two same-numbered cusps, so averaging across systems would produce
  a boundary belonging to neither.

### Changed

- The two transition error messages now name the wall time and the zone, offer
  both possible causes rather than asserting daylight saving, and define `is_dst`
  by the offset it selects. Their `"Ambiguous time error!"` and
  `"Non-existent time error!"` prefixes are unchanged, so callers matching on
  those keep working.

### Corrected notes for 6.0.0a76

The points below were wrong or missing when 6.0.0a76 shipped. They have been
corrected in place in its own section, and are recorded here so the change is
visible rather than a silent rewrite of a published release.

- The historical-charts line described the change as recorded city mean times
  reaching the chart "with their seconds intact". That is a real effect and a
  negligible one. The effect that actually moves charts went unstated: for a date
  between a zone's adoption of a recorded civil time and 1901-12-13, the previous
  backend's truncated table did not know the adoption had happened, so the chart
  fell back to a mean time derived from the birth longitude. It now uses the
  record the zone actually kept. Measured at 1900 Amsterdam that is 19m35s, or
  4.90° of Ascendant; 1895 Tokyo 18m46s (4.69°); 1875 Milan 13m10s (3.29°).
  Minutes and degrees, not seconds.
- Nothing was said about `is_dst` changing which side of a fold it selects in
  zones whose tz build records daylight saving as a negative offset — Ireland,
  Morocco and Namibia among them. `Europe/Dublin` on 2023-10-29 at 01:30 with
  `is_dst=True` resolved to 01:30Z before and resolves to 00:30Z now, about 10°
  of Ascendant. The new answer is the intended one: `is_dst=True` means the
  larger UTC offset, which is the summer reading whichever way the database
  books the flag. The count of affected zones is deliberately not stated — it
  depends on which build of the tz database the host ships.
- Nothing was said about the composite at all, though 6.0.0a76 both introduced
  the overwrite corrected above and began refusing parents whose cusps came from
  different divisions, with a new message.

## 6.0.0a76 - 2026-07-20

### Fixed

- Timezone offsets are now resolved with the standard library's `zoneinfo`
  instead of `pytz`. `pytz` builds its transition table bounded by 32-bit
  `time_t`, so for any date after ~2037 or before 1901-12-13 it froze the offset
  at the nearest known transition: northern zones stayed on standard time,
  southern zones stayed on DST, and every affected chart was up to an hour off.
  Because the Ascendant advances ~15°/hour, that surfaced as an Ascendant wrong
  by up to ~12° — for example a 2100 New York chart was cast on EST instead of
  EDT.
- Charts before 1902 now use the civil time the zone actually kept. Between a
  zone's adoption of a recorded mean or standard time and 1901-12-13, the old
  transition table did not know the adoption had happened, so the chart fell back
  to a mean time derived from the birth longitude — a sundial reading standing in
  for a clock that existed and was documented. Measured at 1900 Amsterdam the
  correction is 19m35s, or 4.90° of Ascendant; 1895 Tokyo 18m46s (4.69°); 1875
  Milan 13m10s (3.29°). Separately, and much smaller, the old table rounded
  pre-standardization offsets to whole minutes, so those records now also reach
  the chart with their seconds intact — worth up to ~30 seconds.
- `is_dst=True` now selects the larger UTC offset in every zone, including those
  whose tz build records daylight saving as a negative offset (Ireland, Morocco,
  Namibia among them). There the old rule keyed on a non-zero `dst()`, which in
  that encoding is the WINTER side, so the selection was inverted:
  `Europe/Dublin` on 2023-10-29 at 01:30 with `is_dst=True` resolved to 01:30Z
  and now resolves to 00:30Z, about 10° of Ascendant. The larger offset is the
  summer reading whichever way the database books the flag, which is why the rule
  no longer consults it. How many zones this touches depends on which build of
  the tz database the host ships, so no count is given.
- The polar house fallback no longer corrupts the Ascendant. House systems that
  are undefined inside the polar circle used to be retried at a latitude clamped
  to ±66°, and the angles from that retry were reported as the subject's own —
  so the same place and instant yielded a different Ascendant depending on the
  house system, which cannot be true of a horizon intersection. Those systems
  now fall back to Porphyry at the real latitude: cusps stay quadrant-based with
  the first cusp exactly on the Ascendant, and the angles are exact. The
  substitution is declared rather than silent (see below). The clamp survives
  only for Gauquelin sectors, whose 36-cusp output shape admits no substitute.
- Solar noon in the moon-phase details is computed in instant space. The prior
  wall-clock arithmetic relied on a fixed-offset tzinfo and would have shifted
  the result by an hour across a DST transition under a live tzinfo.

### Added

- `AstrologicalSubjectModel.polar_house_fallbacks`: a list of
  `PolarHouseFallbackModel` records naming the requested and substituted house
  system, the real and used latitude, and the backend-reported polar threshold.
  A chart can carry more than one (a main-system substitution and a Gauquelin
  clamp), so it is a list. Empty for every chart outside the polar circle.
- Fixed stars now declare `source` and `precision_class` like every other point,
  on both the requested-star and discovery paths. Per-body coverage and reviewed
  status stay `None`: the backend keys its coverage inventory by body id and has
  no star entries, so reporting a window would be an unbacked claim.

### Changed

- `tzdata` is now a hard runtime dependency and `pytz` is gone. `zoneinfo`
  searches `TZPATH` (the host's own database) first and falls back to the
  `tzdata` package only when a zone is not found there, so the dependency is a
  floor rather than a pin: it guarantees every zone resolves on hosts that ship
  no system database — Alpine, Windows, slim containers — where the library
  would otherwise raise. It does **not** override a differently-aged system
  database, so two hosts can still disagree about a zone whose rules changed
  recently. Pinning outright would require clearing `TZPATH` at import, which
  would override the deliberate choices of anyone who maintains their own.
- A local time of year 9999 east of UTC now resolves instead of raising. The old
  failure was an artifact of `pytz` probing ±1 day around the requested instant,
  not a real limit.
- **Output shape:** every `EphemerisDataFactory.get_ephemeris_data()` sample now
  carries a `polar_house_fallbacks` key in both the plain-dict and
  `as_model=True` forms. It is a list of the sample's structured fallback
  records, empty when no polar substitution was needed. Consumers that validate
  plain-dict keys strictly must accept the new always-present key.
- A midpoint composite now refuses two subjects whose cusps came from different
  house divisions, with a new message naming both. Matching *requests* is no
  longer enough: inside the polar circle two subjects that both asked for
  Placidus can hold Placidus cusps and Porphyry cusps, and each composite cusp is
  the circular mean of the two same-numbered ones. A Davison composite is
  unaffected — it recasts a new chart rather than averaging existing cusps.
  (6.0.0a76 also overwrote the composite's requested house system with the
  substituted one; that was a defect and is fixed in 6.0.0a77.)

## 6.0.0a75 - 2026-07-18

### Added

- Ephemeris-backed points calculated through libephemeris can now expose their
  selected `source`, `precision_class`, reviewed status and backend-reported
  coverage window. Tracing is collected independently of DEBUG logging and
  survives normal model serialization.
- Geometrically derived points inherit provenance from their primaries on the
  libephemeris backend (like all provenance metadata, this is not populated on
  the pyswisseph backend): besides the opposite-point antipodes (South Nodes,
  Priapus variants, Descendant, Imum Coeli, Anti-Vertex), Arabic Parts / Lots
  are now labelled `source="Derived"` with precision, coverage window and
  reviewed status inherited from the ephemeris-backed points in their formula
  (distinct precision classes collapse to `mixed`; coverage is the
  intersection). Relocated charts preserve the inherited lot provenance.
  Points computed directly from house geometry (Ascendant, Medium Coeli,
  Vertex, house cusps) and fixed stars intentionally carry no per-body
  coverage metadata.
- `EphemerisDataFactory` accepts `active_fixed_stars`: requested stars are
  calculated on every generated subject and, when the list is non-empty, each
  `get_ephemeris_data` sample carries a `fixed_stars` key with the star point
  models (same shape as `subject.fixed_stars`); subjects returned by
  `get_ephemeris_data_as_astrological_subjects` expose them via
  `subject.fixed_stars`. With no stars requested no `fixed_stars` key is added
  to the plain-dict samples; `as_model=True` serialization gains an empty
  `fixed_stars` list on every sample (like `ephemeris_warnings` in this same
  alpha cycle).
- Subjects expose structured `ephemeris_warnings` for optional points omitted
  after neither the selected ephemeris nor a permitted local model produced a
  value. Backend exception details remain in logs rather than public payloads.

### Changed

- **Output shape:** every `EphemerisDataFactory.get_ephemeris_data()` sample now
  carries an `ephemeris_warnings` key — a list, empty when nothing was omitted —
  in both the plain-dict and `as_model=True` forms. The plain-dict sample is
  therefore **not** key-identical to pre-a75 releases even when no stars are
  requested; the keys are now `date`, `planets`, `houses`, `ephemeris_warnings`
  (plus `fixed_stars` only when `active_fixed_stars` is non-empty). Consumers
  that validate keys strictly, golden-diff the raw dict, or serialize
  `sample.items()` into a pinned payload must accept the new key.
- A point's `precision_class` is no longer defaulted to `ephemeris` for source
  labels the coarse mapping does not recognize. Only the tabulated-ephemeris
  labels (`LEB`, `SPK`, `Skyfield`) map to `ephemeris`; `Keplerian*` and
  `Analytical*` keep `approximate` / `analytical`, and anything else — notably
  `ASSIST`, libephemeris' live n-body integration fallback, which libephemeris
  itself classifies as `numerical-model` — now reports `numerical-model` rather
  than overstating the point as ephemeris-grade.
- LEB mode now enforces libephemeris' sealed network policy and delegates
  source selection to libephemeris. For a configured maximum tier, the
  highest-priority manifest-pinned LEB artifact covering each body and date is
  preferred; an explicitly supported local model remains available and is
  labelled with its actual source. Only a point for which no permitted source
  succeeds is omitted from `active_points` and reported through
  `ephemeris_warnings`.
- Planetocentric failures are no longer replaced with geocentric coordinates.
  In particular, a Sun or Moon failure now aborts the subject instead of
  returning a mislabeled frame; swisseph installations therefore need the
  corresponding planetary ephemeris files for those perspectives.
- The dependency advances to libephemeris 3.0.0rc14, which supplies the pinned
  data-v3 modular set, sealed-network gate, best-by-date tier routing and
  coverage inventory.
- Tier range shorthands ("1550–2650" for medium) are upper-bound exclusive:
  the medium LEB core covers `[1550-01-01, 2650-01-01)` — JD `[2287185.5,
  2688952.5)`. Dates at or beyond the boundary now raise the typed
  `EphemerisRangeError` (wrapped in `KerykeionException` for luminaries)
  instead of being served by a silently substituted lower-precision source
  as in rc12.

## 6.0.0a73 - 2026-07-16

### Fixed

- **Nested ephemeris sessions can no longer corrupt an outer calculation.**
  `ephemeris_session()` now rejects same-thread nesting before the inner call
  mutates process-global sidereal/topocentric state. Previously the inner
  cleanup reset the still-active outer session; a LAHIRI calculation could
  silently continue with tropical/default state.
- **Predictive Julian-Day range APIs reject non-finite bounds consistently.**
  Lunation, retrograde-station, sign-ingress, and mundane-aspect searches now
  raise `ValueError` for `NaN` or infinite bounds instead of returning a
  plausible empty model, serializing `null`, or leaking a later overflow.
- **Eclipse and occultation searches reject negative event counts.** `count=0`
  remains an explicit empty search; negative counts now raise `ValueError`
  rather than succeeding vacuously.
- **Void-of-course backend error normalization is statically typed.** Backend
  exception classes are resolved and validated once, preserving the documented
  `KerykeionException` boundary while restoring a clean mypy gate.
- **ISO range endpoints preserve every separator accepted by Python.** The five
  timing range factories now distinguish date-only bounds by parsing them as
  dates. Datetimes using valid non-`T` separators such as `_` are no longer
  mistaken for dates and widened through the end of the day.
- **Orb and astrocartography numeric contracts reject non-finite values.**
  Aspect-axis limits, declination orbs, fixed-star discovery orbs, and ACG
  latitude steps now reject `NaN` and infinities. ACG latitude bounds must also
  be finite, ordered, and contained within the geographic -90..+90 range.
- **Low-level ephemeris and predictive inputs now fail fast.** Unknown zodiac
  or perspective session values, non-finite USER ayanamsha/topocentric values,
  non-finite single Julian Days, and invalid eclipse/occultation longitudes no
  longer select defaults, bypass work through empty requests, or persist
  invalid model fields.
- **Primary directions validate their calculation contract.** Unknown rate
  keys, invalid horizons, malformed or unknown aspect filters, duplicate
  aspect names, and non-finite subject geometry are rejected or normalized
  before calculation instead of returning plausible empty/corrupt/duplicated
  directions.
- **Primary-direction coordinates now preserve the subject's reference frame.**
  Planetocentric specula use the requested center-body vector, sidereal labels
  no longer leak into physical equatorial coordinates, and Topocentric subjects
  retain and reuse their observer altitude.
- **Fast paths no longer bypass subject and filter validation.** Fixed-star
  discovery rejects non-finite subject Julian Days before catalog shortcuts
  (raising the factory's documented `KerykeionException`); astro-cartography
  also rejects non-finite Julian Days, malformed or unknown planet filters,
  and projected grids above 1,000,000 line points (generous enough for
  step=0.01 high-resolution maps with all ten planets).
- **Per-point aspect adjustments reject corrupt numeric input.** Non-string
  keys and non-finite adjustment values now fail before single-, dual-,
  progression-, or solar-arc aspect calculation. Boolean values are rejected
  wherever numeric coordinates, orbs, steps, or backend tuples are validated
  (`True`/`False` pass `isinstance(..., Real)` but are always caller
  mistakes).
- **Heliacal and occultation searches reject physically invalid requests.**
  Heliacal coordinates, event types, counts, atmosphere/observer tuples, and
  Julian Days are validated even for empty searches. Raw occultation body IDs
  now obey the same real-body restriction as named bodies.
- **Dual-chart SVG baselines include the a70 projected-house attributes.** The
  eleven affected synastry/transit goldens now match the additive metadata
  contract instead of failing the base-tier suite.

### Documentation

- Added complete guides for mundane aspects, Sun times, planetary hours, and
  void-of-course Moon windows; updated timing, eclipse, heliacal, planetary
  return, SVG metadata, public-model, development, and test-suite references.
- Rebuilt the documentation coverage audit around the explicit 102-name
  package-root export contract. It now scans README, the AI guide, site docs,
  and examples and exits non-zero for real omissions; current coverage is 100%.
- The Markdown snippet gate now includes site examples by default, no longer
  skips all docs when the optional `swisseph` package is absent, and uses a
  fast page-level pass with cumulative replay only for diagnostics. All 380
  maintained runnable snippets pass.
- Development/test counts and Markdown EOF hygiene were aligned with the
  current tree, and the primary-directions guide documents the public
  `compute_speculum()` helper.
- Corrected backend license assignments, active-point/fixed-star configuration
  guidance, and the all-points example; added the backend precision guide to
  navigation. README chart/license resources now use verified absolute URLs so
  they render from wheel metadata on PyPI.

### Removed

- **Hosted CI removed again (no-CI policy).** The GitHub Actions workflow that
  crept back in during the review rounds is deleted; the project deliberately
  has no hosted CI. Every gate runs locally through `poe`: `quality` (ruff,
  mypy, pyright, full pytest suite), `docs:check`, `docs:snippets`, and
  `build:smoke` for the isolated wheel smoke test.

## 6.0.0a72 - 2026-07-15

### Changed (6.0.0a72 — libephemeris 3.0.0rc11 repin)

- **Repins libephemeris to 3.0.0rc11.** rc11 refines the computed position of
  the mean lunar apogee — the **White Moon (Selena)** — by roughly 0.2° versus
  rc10 (the natal sample subject moves from 26.26° to 26.44° Cancer, for
  example), with the corresponding shift in every aspect orb that references
  that point. No zodiac framing, public API, or model field changed; the 13
  affected `*_report.txt` snapshots were regenerated to match. Tropical
  longitudes, house cusps, the ascendant, and all other points are unaffected.

## 6.0.0a70 - 2026-07-13

### Added (6.0.0a70 — dual-chart projected-house SVG metadata)

- **Dual-chart `ChartPoint` nodes now expose both house meanings.** Existing
  `kr:house` remains the point owner's own house, preserving the SVG contract
  for consumers that display both subjects' domifications. New
  `kr:projectedhouse` reports the same point in the other subject's house
  system, while `kr:projectedhoroscope` identifies that target ring (`0` or
  `1`). The metadata is emitted for both rings of every dual chart type:
  Transit, Synastry, DualReturnChart (including solar and lunar returns), and
  Progression. It is present in classic and modern wheels, full and wheel-only
  SVGs, and is calculated directly from the reciprocal cusps even when optional
  house-comparison tables are disabled. No visual geometry or existing
  attribute changed.

## 6.0.0a69 - 2026-07-12

### Added (6.0.0a69 — sidereal mundane event finders)

- **Sidereal support for the mundane event finders** — `SignIngressFactory`,
  `LunationFinderFactory`, `RetrogradeStationFactory` and `EclipseFactory` now
  accept `zodiac_type` (`"Tropical"` default / `"Sidereal"`) and `sidereal_mode`
  keyword arguments on their public entry points (`from_iso_range` /
  `from_julian_day`, and `search_global` / `search_from_location` for eclipses),
  mirroring the already-zodiac-aware `MundaneAspectFactory` and
  `VoidOfCourseMoonFactory`. Each factory runs its scan inside
  `ephemeris_session(zodiac_type=…, sidereal_mode=…)` so `calc_ut` reports
  longitudes in the requested frame — an astro-calendar can now render
  consistently in a single zodiac. Frame-independent event TIMES stay identical
  (lunation phase = Sun-Moon elongation; station = speed zero, found in the
  tropical frame; eclipse maximum = shadow geometry); only the reported SIGN
  labels shift. Sign-ingress TIMES legitimately shift (the sidereal boundary is
  ~24° away). `season_marker` stays **tropical-only** — a sidereal cardinal
  crossing is not the equinox/solstice, so it is `None` on every sidereal
  ingress. All additive: the two new kwargs default to the previous tropical
  behavior, and no existing signature or model field changed.

### Changed (6.0.0a69 — void-of-course range normalization)

- **`VoidOfCourseMoonFactory.from_iso_range` now normalizes civil-range
  overflow to `KerykeionException`.** Near the year-1 boundary the sign-by-sign
  Moon walk can step before 1 CE, where `julian_day_to_utc` raises a bare
  `OverflowError`/`ValueError` (Python's `datetime` has no BCE support) that the
  previous `except getattr(ephe, "Error", ())` did not catch — leaking a 500
  downstream. The range scan now also catches `OverflowError`/`ValueError` and
  normalizes them to `KerykeionException` with the same "narrow the date range"
  message the single-moment `from_datetime` path already uses.

## 6.0.0a68 - 2026-07-11

### Added (astrological calendar primitives)

- **Mundane aspectarian** — new `MundaneAspectFactory`
  (`kerykeion/mundane_aspects/`): every exact transiting-to-transiting aspect
  within a date range, the content of a printed astrological calendar's
  aspectarian. Uniform 6-hour sampling of the signed pairwise separation with
  bisection refinement (unconditionally convergent — Newton diverges on slow
  mutual pairs near stations), midpoint splitting for relative-motion reversals
  inside a step, and a branch-cut guard against antipode wraps. Default scan
  set is Sun..Pluto with the five Ptolemaic aspects; the Moon is opt-in (its
  ~75 events/month are noise for most consumers); the full minor-aspect
  vocabulary from the chart defaults is accepted. Aspect instants are
  zodiac-independent (verified by a sidereal-invariance test); reported
  longitudes/signs follow the requested zodiac. Returns
  `MundaneAspectsCollectionModel` with per-event longitudes, signs and
  retrograde flags.
- **Void-of-course windows over a range** — new
  `VoidOfCourseMoonFactory.from_iso_range`: walks the Moon sign by sign and
  returns every VoC window intersecting the range (unclipped), each framed by
  its opening aspect and closing ingress, as
  `VoidOfCourseWindowsCollectionModel`. Reuses the shipped single-moment
  Newton machinery unchanged; whole-sign voids (no aspect in the sign) are
  reported with `last_aspect: null`.
- **Season markers on Sun ingresses** — `IngressModel.season_marker`
  (optional): Sun ingresses at the cardinal boundaries now carry
  `march_equinox` / `june_solstice` / `september_equinox` /
  `december_solstice`. Hemisphere-neutral month-based names; `None` on all
  other ingresses. Additive and backward compatible.

### Changed (6.0.0a68 — backend repinned rc3 → rc6, golden fixtures regenerated)

Default backend repinned `libephemeris==3.0.0rc3` → `==3.0.0rc6` (the tagged
`6.0.0a67` intermediate pin to `rc5` is superseded; `rc5` and `rc6` are
numerically identical — `rc6` is a provenance/independence release — so the
effective trajectory is `rc3 → rc6`). No public API change; both upstream test
backends green at 16024 each.

- **Reference-frame transforms refined ~1.5″ across rc3 → rc6.** Sidereal
  fixed-reference modes (`J1900`/`J2000`/`B1950`) and the heliocentric /
  topocentric / true-geocentric perspectives moved closer to Swiss Ephemeris.
  Spot-check, John Lennon Moon sidereal `J2000`: `rc6` 304.37271839 is 0.17″
  off Swiss; the previous rc3 fixture 304.37313858 was 1.69″ off — `rc6` is
  ~10× closer, the fixture carried the *less* accurate value.
- **Golden position fixtures regenerated on rc6.** All 41 sidereal-mode and 3
  non-default-perspective expected-position fixtures (23 files). The 8
  tolerance failures the repin surfaced (Moon/Mercury/Pluto, frame-transform
  paths, sub-arcsecond) are resolved; suite green at 9689 passed.
- **SVG chart baselines unchanged.** A ~1.5″ shift is far below rendering
  precision, so every chart baseline is byte-identical and all chart tests
  stay green without regeneration.

### Fixed (6.0.0a68)

- **`test_defaults_to_current_time_when_none` compared against the wrong
  timezone.** `AstrologicalSubjectFactory.from_birth_data` resolves "now" in
  the subject's own timezone (`Etc/GMT` = UTC for the test subject); the
  assertion used naive `datetime.now()` (local), so it failed whenever the
  local day differed from the UTC day near midnight in a non-UTC timezone —
  silently green on UTC CI. It now compares against `datetime.now(timezone.utc)`.

### Fixed (fresh full-codebase review, round 48)

A from-scratch review that deliberately ignored every previous round's "clean"
verdict. 48 finders, three adversarial skeptics per finding, then an execution
proof for each survivor: a reproduction script, or a mutation test showing the
suite stayed green without it. Findings that could not be reproduced were
dropped, including two raised by the reviewer itself.

- **Rendering regressions were silently skipped, not failed.** Five
  baseline-comparison tests in `test_chart_parametrized.py` wrapped the
  comparison in `except Exception -> pytest.skip`. `AssertionError` inherits
  from `Exception`, so any SVG mismatch was reported as a skip and the suite
  stayed green. The same swallow hid a violated backwards-search invariant in
  `test_heliocentric_returns.py`.
- **The tier filter skipped 25 tests that need no ephemeris.** Extended-kernel
  tests were selected by matching `"bce"`, `"ancient_rome"` and
  `"historical_date"` as bare substrings of the node id, so pure string-formatting
  tests (`test_jd_to_iso_bce_year` in three modules, all of `TestAncientISOFormat`
  including `test_year_zero`, the BCE sampling-gap tests) never ran on the default
  tier. No regex can separate them — a test's *name* says "bce" while its body
  never leaves the civil range — so intent is now declared with an explicit
  `@pytest.mark.extended` marker on the 40 tests that genuinely need DE441.
- **`test_chart_drawer_save_svg_method` never tested `save_svg`.** It passed a
  file path where the method expects a directory, so every call raised, and the
  `except Exception: assert hasattr(chart, "save_svg")` fallback made the test
  pass regardless. It now asserts the file is written and non-empty.
- **Coverage config was silently ignored.** `.coveragerc` took precedence over
  `pyproject.toml`, so `source = ["kerykeion"]` and the whole `omit` list never
  applied — while `.coveragerc`'s own comment claimed "the main configuration is
  in pyproject.toml". Removed; `pyproject.toml` now takes effect.
- **Fixed stars received none of the point enrichments.** They live in a list
  under `calc_data["fixed_stars"]`, not as `KerykeionPointModel` values, so the
  loops that iterate `point_keys` skipped them: Algol (declination +40.9°, plainly
  out of bounds) returned `azimuth`, `altitude_above_horizon`, `gauquelin_sector`,
  `is_out_of_bounds` and `nakshatra` all `None` while the Moon was fully populated.
  The frame-independent enrichments now reach them. Essential dignities stay
  point-only: rulership is not defined for stars.
- **Almuten Figuris ignored `include_score_breakdown=False`.** The essential-dignity
  loop guarded its appends with the flag; `_add_accidental_dignities` appended
  unconditionally, so `include_accidental_dignities=True` populated the audit trail
  the caller had opted out of. Scores were always correct and are unchanged.
- **Astronomical year 0 rendered as `-0000`.** Both formatters in
  `SecondaryProgressionFactory` tested `year > 0`, sending year 0 down the negative
  branch and emitting malformed ISO 8601, inconsistent with
  `_predictive_utils.jd_to_iso_utc`, which tests `year < 0`.
- **Cusp-in-house report table showed `First_House`.** The projected house name
  skipped the `_humanize()` call that the adjacent cell uses. Report snapshots
  under `tests/fixtures/` regenerated accordingly.
- **`draw_planets` indicator helpers could raise `IndexError`.** Both iterated
  `range(len(points_settings))` while indexing `points_abs_positions`; every
  sibling helper bounds the loop with `min(...)`. Not reachable through the
  shipped `ChartDrawer`, which re-aligns the two lists, so this is hardening.
- **Untested guards.** The `phase < 1` lower bound in `_get_lunar_phase_index` and
  the non-finite/negative orb validation in `build_aspect_settings` had no test at
  all: deleting either left the suite green. Both are now covered, verified by
  mutation.

### Documentation (fresh full-codebase review, round 48)

- **`libephemeris` is AGPL-3.0-only.** `LICENSING.md`, `COMMERCIAL-LICENSE.md`
  and `NOTICE` describe the default backend as AGPL-3.0-only. It is authored by the
  same maintainer as Kerykeion, so the commercial edition covers `libephemeris`
  through its own commercial license alongside Kerykeion's grant; redistributions
  must preserve its copyright and attribution notices, including its `NOTICE` file.
- **`SolarEclipseModel.duration_minutes` was documented as its own opposite.** The
  field description and the `_solar_gamma_duration` docstring said the value is the
  global span of the shadow path across the Earth and explicitly "not the totality
  duration at any single place"; the backend returns exactly that local
  totality/annularity duration at the point of greatest eclipse (verified: 6.42 min
  for the 2027-08-02 total eclipse, against its published 6m23s maximum).
- **`PlanetaryReturnFactory.altitude` was documented as inert.** "Reserved for future
  astronomical calculations" — but it is forwarded to the topocentric observer setup
  and does move positions (~0.56″ at 8848 m).
- The module and class docstrings of `PlanetaryReturnFactory` claimed the Swiss
  Ephemeris library, while the default runtime uses `libephemeris` and never imports
  `pyswisseph`.
- `CompositeSubjectFactory` docstrings described house sorting; the implementation
  deliberately does not sort (a comment in the body says so, because sorting would
  swap the composite MC and IC).
- `download_swisseph_data` documented an `asteroids` key of downloaded paths that is
  always empty — asteroid files are only detected, never downloaded.
- Four `charts_utils` grid docstrings stated `x_position` defaults of 620/870/720/970
  against real defaults of 645/910/750/1015.
- `site/docs/eclipse_factory.md` typed `magnitude`/`obscuration` as `float`; both are
  `Optional[float]` defaulting to `None`.
- The `--ai-guide` flag advertised `AI_AGENT_GUIDE.md`; it scans `kerykeion/llms.txt`.
- Snapshot-regeneration instructions named two different commands, one of which
  (`poe regenerate:report-snapshots`) does not exist; unified on `poe regenerate:reports`.
  The SVG baseline message named `poe regenerate:charts`, also nonexistent.
- `scripts/quality_check.py` ran `pytest` without `-m "not online"`, so the local
  quality gate depended on GeoNames being reachable.
- Removed the duplicate `[tool.pyright]` table shadowed by `pyrightconfig.json`, and
  the stale generated pdoc tree under `docs/` (12 of its pages documented modules
  deleted in v6). It is regenerated on demand with `poe docs` and is now git-ignored.

## 6.0.0a67 - 2026-07-10

### Changed (6.0.0a67 — libephemeris 3.0.0rc5)

- **Bumped the `libephemeris` pin to `==3.0.0rc5`** (from `==3.0.0rc3`), pulling
  in the upstream release-candidate fixes since rc3. No kerykeion computation
  code changed; the commit only advances the dependency floor. The pin will move
  to the stable `3.0.0` at the 6.0.0 tag (see the `TODO` in `pyproject.toml`).

## 6.0.0a66 - 2026-07-10

### Added (6.0.0a66 — astrological calendar primitives)

- **Mundane aspectarian** — new `MundaneAspectFactory`
  (`kerykeion/mundane_aspects/`): every exact transiting-to-transiting aspect
  within a date range, the content of a printed astrological calendar's
  aspectarian. Uniform 6-hour sampling of the signed pairwise separation with
  bisection refinement (unconditionally convergent — Newton diverges on slow
  mutual pairs near stations), midpoint splitting for relative-motion reversals
  inside a step, and a branch-cut guard against antipode wraps. Default scan
  set is Sun..Pluto with the five Ptolemaic aspects; the Moon is opt-in (its
  ~75 events/month are noise for most consumers); the full minor-aspect
  vocabulary from the chart defaults is accepted. Aspect instants are
  zodiac-independent (verified by a sidereal-invariance test); reported
  longitudes/signs follow the requested zodiac. Returns
  `MundaneAspectsCollectionModel` with per-event longitudes, signs and
  retrograde flags.
- **Void-of-course windows over a range** — new
  `VoidOfCourseMoonFactory.from_iso_range`: walks the Moon sign by sign and
  returns every VoC window intersecting the range (unclipped), each framed by
  its opening aspect and closing ingress, as
  `VoidOfCourseWindowsCollectionModel`. Reuses the shipped single-moment
  Newton machinery unchanged; whole-sign voids (no aspect in the sign) are
  reported with `last_aspect: null`.
- **Season markers on Sun ingresses** — `IngressModel.season_marker`
  (optional): Sun ingresses at the cardinal boundaries now carry
  `march_equinox` / `june_solstice` / `september_equinox` /
  `december_solstice`. Hemisphere-neutral month-based names; `None` on all
  other ingresses. Additive and backward compatible.


## 6.0.0a65 - 2026-07-10

### Fixed (6.0.0a65 — zero-bug review campaign, rounds 36–47)

Twelve further review rounds, each rotating a fresh runtime-reproduced lens, and
each round adversarially re-reviewing the previous round's own diff. Rounds 45,
46 and 47 closed with zero findings. Every fix below was reproduced by execution
before being applied and is covered by a regression test.

- **Golden baselines regenerated on the pinned engine.** `6.0.0a63` regenerated
  the baselines with libephemeris `3.0.0rc1` while the same commit pinned
  `==3.0.0rc3`, whose upstream speed-model fixes shift speeds by ~1e-4 °/day —
  enough to fail 58 tests on tolerance and flip near-threshold aspect-movement
  labels in the report snapshots. All expected-position/aspect/subject data and
  report fixtures were regenerated on rc3 at the `extended` (DE441) tier, which
  also restored the previously unregenerable `natal_ancient_rome` fixture.
- **BCE event splitting.** `TransitsTimeRangeFactory` computed sampling gaps with
  `datetime.fromisoformat`, which raises on extended-year ISO strings; the
  `except` mapped that to "gap 0", silently merging every recurrence of an aspect
  in a BCE range into a single event (`applying_start`/`separating_end`/`orb_rate`
  all `None`). Both call sites now use the module's BCE-safe day arithmetic.
- **Pre-1 CE progression window.** A progressed Julian Day landing in the ~2-day
  window before 1 CE Jan 1 (proleptic Gregorian) decomposed to Julian year 1,
  which `from_birth_data` reinterpreted as Gregorian — building the progressed
  chart exactly two days late, silently. Clamped with a warning, mirroring the
  Davison composite guard.
- **Civil-range edges.** `pytz.localize` probes the surrounding day to resolve
  DST, so the first and last civil days (`0001-01-01`, `9999-12-31`) crashed with
  a raw `OverflowError` in `SunTimesFactory`, `PlanetaryHoursFactory` and
  `VoidOfCourseMoonFactory` instead of the documented `KerykeionException`.
- **Transits to non-default points.** `EphemerisDataFactory` accepted no
  `active_points`, so every ephemeris subject carried only the defaults and
  transits to asteroids/TNOs on the natal chart silently produced zero events
  while the parameter was advertised. The factory now forwards an optional
  `active_points` list, and `TransitsTimeRangeFactory` warns when a requested
  point is missing from the natal side, the ephemeris side, or both (points the
  subject factory drops by design for the chart's frame stay silent).
- **Sect (`is_diurnal`) lost at the model boundary.** The value was computed by
  the return and Davison factories but silently dropped by pydantic (field
  undeclared on `PlanetReturnModel` / `CompositeSubjectModel`), so sect-aware
  consumers — dominants, almuten, zodiacal releasing — treated every night return
  as a day chart. Both models now declare `is_diurnal: Optional[bool]`, and the
  new `utilities.resolve_sect_is_diurnal` coalesces the midpoint composite's
  `None` ("no single sky") back to the historical day-chart default.
- **`Interpolated_Perigee` phantom.** `SE_INTP_PERG` was missing from the
  geocentric-only exclusion, so in non-geocentric frames libephemeris echoed the
  geocentric value while swisseph returned a 0° Aries phantom — the exact silent
  backend disagreement the exclusion exists to prevent.
- **Geocentric-only points dropped silently.** Explicitly requesting lunar nodes
  or Lilith/apogee variants in a non-geocentric chart removed them with no log at
  any level (the analogous center-body drop warns), and a list containing *only*
  such points returned a silent EMPTY chart. Both now warn and raise respectively.
- **`active_points` contract.** Unknown names (a typo such as `"Sunn"`) were
  silently dropped from the chart; an explicit empty list inverted into a FULL
  default chart. Both now raise `KerykeionException`; fixed-star names still
  redirect to `active_fixed_stars` with a warning.
- **Error contracts hardened.** `CompositeSubjectFactory` /
  `RelationshipScoreFactory` raised raw `AttributeError` on non-subject inputs
  (and `require_same_frame` let two frameless inputs through, sentinel ==
  sentinel); `create_chart_data` answered an unknown `chart_type` with a
  misleading "second subject is required" message; `PlanetaryHoursFactory`
  accepted out-of-range latitude/longitude; `ChartDrawer` silently fell back on
  an unknown `chart_language` (to EN) or `double_chart_aspect_grid_type` (to
  table); `TransitsTimeRangeFactory` validated `axis_orb_limit` only deep inside
  `get_transit_moments`. All now fail up front with actionable messages. A
  `language_pack` still legitimizes a custom `chart_language` code.
- **Fixed-star discovery on composites.** `find_prominent_stars` fed a `None`
  Julian Day to `fixstar_ut`, which returns NaN positions on libephemeris, so
  every orb comparison was false and the caller silently received `[]`. It now
  raises like the sibling planetary-nodes factory.
- **Zodiacal releasing on returns and Davison charts.** `from_subject` crashed
  with a raw `AttributeError` on `PlanetReturnModel` / `CompositeSubjectModel`
  (no split `year`/`month`/`day` fields) — the very models that carry sect for
  it. Both now anchor on their ISO timestamp; midpoint composites, which have no
  single moment in time, raise a clear `KerykeionException`.
- **Nakshatra pada boundaries.** The pada was computed from the remainder against
  the span constant, inheriting its floating-point error: exactly representable
  boundaries (20.0°, 30.0°, 60.0°, 70.0°, …) landed in the *previous* pada while
  the nakshatra itself was correct. Both values now derive from a single global
  108-quarter index.
- **Swiss Ephemeris backend suite restored to green.** The backend itself proved
  healthy (sub-arcsecond parity with libephemeris, worst 0.25″ on Chiron); the
  failures were test-side: a Lilith reference calc forced the Moshier fallback
  by resetting the ephemeris path outside the lock; `test_barycentric` asserted
  the barycentric Sun sits within 0.05° of the geocentric one (physically wrong —
  both backends agree it is ~25° away); backward return searches are a documented
  libephemeris-only feature; TNO-dependent tests now auto-skip when the swisseph
  install lacks the manual-download asteroid files. Kernel-edge tests are gated on
  the detected ephemeris tier.
- **Documentation.** ~140 verified corrections across `site/docs`, `site/examples`,
  `README.md` and `kerykeion/llms.txt`: wrong API names (`swe` → `ephe`, Equal
  house code `"A"`), wrong defaults and types, crashing or undefined-variable
  snippets, and stale example outputs — every snippet re-executed and its printed
  output pasted from the real run. The snippet harness itself was rehabilitated:
  it pointed at long-gone directories, and once fixed, three interacting defects
  (joint dedent, a geonames mask that swallowed tracebacks, and masked passes
  feeding the page context) were producing ~16% false passes.

## 6.0.0a64 - 2026-07-09

### Added (6.0.0a64 — modern SVG focus-mode contract parity)

The `kr:*` SVG attribute vocabulary the modern (`style="modern"`) charts emit
now matches the classic engine, so downstream focus/highlight code (which
selects nodes via `kr:node` and matches related nodes by STRING equality of
`kr:absoluteposition` / `kr:horoscope`) works identically on both styles.
All changes are SVG metadata only — no astrological computation moved.

- **Modern house-focus owner attributes.** `Cusp` and `HouseNumber` nodes now
  carry `kr:horoscope="0"` (single and dual charts, mirroring classic);
  `HouseSector` wedges carry `kr:horoscope="0"` in dual charts (single charts
  stay bare, mirroring classic).
- **Indicator ownership (both styles).** Every degree-tick `Indicator` node now
  carries `kr:absoluteposition`, interpolated from the SAME float object as its
  owning `ChartPoint`, so the two attribute strings are guaranteed identical.
  Dual charts also carry `kr:horoscope` (`"0"` inner ring / `"1"` outer ring).
  In classic dual charts the second subject's tick line + degree text — which
  previously rendered unwrapped — are now wrapped in a proper
  `<g kr:node="Indicator" kr:slug kr:absoluteposition kr:horoscope="1">` group.
  `ConnectingLine` nodes (external natal) carry `kr:absoluteposition` too.
- **Modern Gauquelin metadata.** Modern `ChartPoint` nodes now carry
  `kr:gauquelinsector` like classic ones.
- **`kr:cx` / `kr:cy` normalized to SVG-root user space in every output.**
  Previously the values were wheel-local: classic outputs were off by the
  `Full_Wheel` translate (100, 50/offset) and the modern full-chart output by
  the composed scale+translate, so consumers converting them via `getCTM()`
  got displaced glyph centers everywhere except the modern wheel-only output.
  A single rebase pass in `ChartDrawer` now rewrites the values per template,
  honoring the documented contract ("glyph center in chart SVG root coords").
  Consumers that already treated them as root coords need no change and become
  correct; anything that compensated manually must drop the compensation.
- New structural test suite `tests/core/test_svg_focus_contract.py` pins the
  contract (owner attributes, Indicator↔ChartPoint string equality, aspect
  endpoint formatting, root-space glyph centers, Gauquelin metadata) for both
  styles; all SVG golden baselines regenerated.

## 6.0.0a63 - 2026-07-08

### Changed (6.0.0a63 — golden-baseline regeneration on the DE441 extended kernel)

Regenerated every test golden baseline on the `extended` (DE441) precision tier
with libephemeris `3.0.0rc1`, restoring the nine pre-1550 historical subjects a
prior `medium`-tier regeneration had silently dropped (41 subjects again, not 32).
No kerykeion computation bug was involved; the diff decomposes into:

- **Stale-baseline fixes now captured.** The previous baselines predated two
  house-ring fixes (composite MC/IC no longer swapped by re-sorting non-monotone
  cusps; `get_planet_house` resolves non-monotone rings via the shortest arc — e.g.
  Horizon houses at the equator). The regenerated fixtures encode the corrected
  (invariant-satisfying) values: composite 10th cusp == MC, and equatorial-Horizon
  planets distributed across houses instead of collapsed into the 1st.
- **libephemeris behavioural updates (documented upstream).** `houses_ex2` now
  reports true time-derivative cusp speeds, so sign-locked systems (Whole Sign,
  Aries, Krusinski) carry the guiding-point (Asc/MC) rate instead of `0`; the
  Interpolated-Lilith/osculating-apogee position drifted ~0.02–0.06° after the
  upstream apogee fixes. Report snapshots (which track the shipped base/medium
  kernel) were regenerated accordingly.
- **Heliocentric charts** no longer carry geocentric lunar nodes.
- **Test fix.** `TestDavisonBCE` derived the era from `davison.year`, but
  `CompositeSubjectModel` exposes only ISO datetimes; it now parses the
  extended-year ISO string. These BCE tests only run on the extended kernel, so the
  latent failure was invisible to the default-tier CI.

## 6.0.0a62 - 2026-07-08

### Fixed (pre-6.0.0 zero-bug review campaign, rounds 26–35)

Ten further review rounds, each rotating a fresh runtime-reproduced lens. Every
finding below was reproduced offline before fixing and covered by a regression
test; the fixes are error-contract / validation / display-consistency hardening
with no change to any correct computed value.

- **Error contract at the ephemeris/date boundary.** `from_iso_utc_time` wrapped a
  raw `OverflowError`/`OSError` for an instant near `datetime.max/min` whose local
  wall time overflows during the UTC→local conversion (round 26). The
  `PlanetaryReturnFactory` crossing searches (`solcross_ut`/`mooncross_ut` and the
  sibling `helio_cross_ut`/`mooncross_node_ut`, forward **and** backward) leaked a
  raw `libephemeris` error when the search stepped off the loaded ephemeris range;
  all are now normalized to `KerykeionException` like every sibling event factory
  (rounds 31–32). `RelocatedChartFactory` leaked the same `astimezone` overflow for
  an extended-kernel extreme-year subject (round 27).
- **Year 0 / BCE calendrical & ISO.** Year 0 (1 BCE) stored as the ISO-8601 unsigned
  `"0000"` crashed chart rendering because two display helpers
  (`format_datetime_with_timezone`, `format_iso_display`) routed it to
  `datetime.fromisoformat` (min year 1); both now take the manual branch (round 27).
  BCE subjects rendered the local ISO's LMT offset at minute resolution while
  deriving the Julian Day / UTC ISO from the exact offset, so the two ISO fields of
  one subject disagreed about the instant by up to ~30 s; the offset is now quantized
  to the whole second (matching the CE LMT path) and rendered `+HH:MM:SS` (round 34).
- **Serialization / display consistency.** The text and LLM-context serializers
  rendered a within-~0.005°-of-cusp `position`/`abs_pos` as the impossible `"30.00"`
  / out-of-range `"360.00"`; a shared `format_degrees_below_bound` now clamps just
  below the cusp (round 27). `dominants.zodiac_breakdown` raised `IndexError` on a
  tiny-negative input; a fold-back guard mirrors `get_kerykeion_point_from_degree`
  (round 27).
- **Input validation.** `EclipseFactory.search_from_location` and
  `OccultationFactory.search_local` accepted an impossible latitude (`|lat|>90`,
  reachable via a lat/lng swap) and returned a bogus "visible" event; both now
  `validate_latitude`. Occultation search accepted non-physical calculated points
  (nodes, Lilith, Uranian hypotheticals) and fabricated events; it is now restricted
  to an occultable-body allowlist (round 35).
- **Documentation & type-contract accuracy.** `KerykeionPointModel.dignity_score`
  documented range corrected to its true `[-9, +11]` net-sum span (round 28); the
  four Solar/Lunar `PlanetaryReturnFactory` methods narrowed `return_type` from the
  4-member `ReturnType` to `Literal["Solar","Lunar"]` (the accepted set); several
  `Raises:`/parameter docstrings aligned to the actual `KerykeionException` contract
  (rounds 31, 34); stale example output values in the SunTimes docstring and the
  README Moon-phase examples refreshed (round 33).

Lenses that ran fully **clean** across these rounds (extensive runtime evidence, no
defect): algebraic/property invariants, aliasing/shared-mutable-state, concurrency &
shared-cache thread-safety, resource lifecycle/long-run stability, cross-field model
internal-consistency, model serialization round-trip (all types), SVG rendering at
degenerate/extreme configs, two-subject techniques (composite/Davison/synastry/score),
transit-series & chart-data assembly, predictive-technique arithmetic (progressions/
returns/directions/zodiacal-releasing), perspective & coordinate transforms, peripheral
reference values (Arabic parts/fixed stars/nodes/ACG/eclipses/nutation), settings &
translation completeness (10 languages), configurable-input correctness & public-API
integrity. The southern-polar quadrant-house MC behavior flagged in round 29 was
confirmed upstream (libephemeris#46) as intended Swiss Ephemeris parity, not a defect —
see Known limitations.

### Fixed (pre-6.0.0 invariants + calendrical + doc-contract review, round 25)

- **BCE dates reject an impossible day-of-month instead of silently rolling it
  over.** The year-<1 (Julian-calendar) path validated only `1 ≤ day ≤ 31`, so
  e.g. a `2 BCE Feb 29` (non-leap) or `100 BCE Apr 31` was silently normalized by
  `ephe.julday` to the following month — computing a wrong Julian Day and a
  `iso_formatted_utc_datetime` that disagreed with the stored
  `iso_formatted_local_datetime` (off by 1–3 days). The BCE path now validates
  the day against the proleptic-Julian month length (leap when `year % 4 == 0`),
  matching the rejection the CE path already got from `datetime()`.
- **Year 0 (1 BCE) is formatted as ISO-8601-conformant `0000`.** Ancient ISO
  strings rendered astronomical year 0 as the non-standard `-0000` (the minus
  sign is reserved for years ≤ −1); a standards-conformant external parser would
  reject or misread it. Year 0 now formats as the unsigned `0000`, and
  `extract_year_from_iso` parses both `0000` and the legacy `-0000` to 0.
- **Docs**: removed the unsupported `Gonggong` from the TNO list in the LLM guide
  (`llms.txt`) — only the seven TNOs in the `AstrologicalPoint` type are listed;
  refreshed the README Moon-phase report example (it was stale and disagreed with
  its own adjacent JSON block) and the `model_dump_json()` output comment (v6
  adds ~25 fields after `retrograde`).

This round added three fresh lenses. **Algebraic/property-based invariants**
(aspect reciprocity, longitude algebra, house partition, midpoint/composite/
relationship symmetry, return fixed-points, JD round-trips, event monotonicity)
were verified across thousands of randomized inputs — all hold. The
**documentation-vs-behavior** lens found no code defects (every house-system and
perspective literal, default, deprecation, and README example matches runtime);
only the three doc drifts above.

### Fixed (pre-6.0.0 security + performance + backend-differential review, round 24)

- **`EphemerisDataFactory` enforces its size cap before building the series.**
  Each step-type branch built the full `dates_list` and only then checked it
  against `max_days`/`max_hours`/`max_minutes`, so an over-cap range paid the
  full allocation (~66 MB / ~13 s at 2.2× over the minute cap; unbounded for a
  wider range — a single-call resource exhaustion) before raising. The projected
  count is now checked in O(1) and the `ValueError` is raised before any list is
  materialized (over-cap now rejected in well under a second with negligible
  memory; in-cap output unchanged).
- **Passing `active_points` no longer triggers a 1447-entry catalog scan.**
  Detecting v5-style fixed-star names in an explicit `active_points` list ran a
  linear `FixedStarCatalog.find()` per point — so a subject built with
  `active_points` (a documented performance optimization) took ~2.5× as long as
  one without. Replaced with an O(1) cached-set membership check
  (`FixedStarCatalog.is_known_name`), byte-for-byte equivalent to the old
  detection; the optimization now actually speeds builds up.
- **Reports sanitize untrusted subject strings.** A birth `name`/`city`/`nation`
  containing control or ANSI-escape characters flowed verbatim into the
  plain-text report (terminal title/screen manipulation when an operator views a
  report of user-submitted data). The report now strips XML-illegal control
  characters from those fields, matching the existing `context_serializer`
  behavior (the shared sanitizer was factored into `utilities`). Normal text is
  unchanged.

Security lens: path traversal (`save`/SVG output), GeoNames-response poisoning,
SVG/LLM-context injection, ReDoS, and deserialization were all re-probed and
hold. Performance lens: ephemeris generation, aspect grids, and date-range scans
are dominated by inherent astronomy (single hoisted session, no per-step churn).
Backend-differential lens: for the supported configuration `libephemeris` and
`swisseph` agree within documented tolerances across core positions, the full
house matrix (including the polar fallback), Gauquelin sectors, sidereal
ayanamsas, and every event factory except heliacal (a visibility-model
difference now documented under Known limitations); the remaining divergences
trace to `swisseph` running on its Moshier fallback without `.se1` data files.

### Fixed (pre-6.0.0 error-contract + R22-diff review, round 23)

- **Heliacal search no longer swallows backend errors as "no event".**
  `HeliacalFactory.search_events` returned an empty list — indistinguishable
  from a genuine "no events in window" — when the backend raised an
  out-of-range / unknown-body / bad-config error (a mistyped planet name, or a
  window at the edge of the ephemeris). Those hard errors now surface as
  `KerykeionException`; only a genuine no-solution result still yields `[]`.
  `search_events` also validates its `planets` argument against the supported
  set up front. (The single-event entry points that accept a fixed-star name —
  e.g. `next_heliacal_rising` — still return the correct exception *type* for an
  unrecognized body but a less precise message; full star-name validation is
  tracked as a mandatory evolution.)
- **Gauquelin sector cusps are preserved at polar latitudes.** With
  `calculate_gauquelin=True` above the polar circle, the `b"G"` house call
  raised `PolarCircleError`, which was swallowed, leaving `gauquelin_sector_cusps`
  `None` — and three consumers (secondary progressions, planetary returns,
  composite charts) infer "gauquelin disabled" from that, so the sectors
  vanished downstream too. The call now routes through the same polar fallback
  as the main house cusps (clamped to ±66° with a warning).
- **`MoonPhaseDetailsFactory` and `VoidOfCourseMoonFactory` honor their
  documented error contracts near the ephemeris edge.** Their "expected: date
  out of range → degrade gracefully" handlers caught `RuntimeError`, which no
  backend raises, so a date within ~one synodic month of the range end leaked a
  raw backend `EphemerisRangeError`. Moon-phase details now return a model with
  `None` fields; void-of-course now raises `KerykeionException` (its documented
  type).
- **`from_birth_data` normalizes non-integer date/time components.** A string or
  float component (e.g. `month="06"` from JSON/form data), and a non-int `year`,
  raised a raw `TypeError`; both now raise `KerykeionException` like the
  existing out-of-range-component contract.
- **Aspects signal dropped `active_points` names.** A requested point that
  resolves to nothing is still dropped, but now logs a `WARNING` for an
  unrecognized name (typo) or `DEBUG` for a known point simply absent from the
  subject — instead of vanishing silently.
- **Polar-fallback diagnostics corrected.** The fallback warning now states that
  the clamp affects "house cusps and angles" (the returned Ascendant/MC/Vertex
  also come from the clamped retry, not just the cusps); on the swisseph
  backend, a non-polar houses failure no longer emits a spurious polar warning
  or masks the original error behind the clamped retry.

This round completed two coverage-gap lenses (numeric precision — clean, no
findings — and error-swallowing / error-contract) plus an adversarial re-review
of the round-22 diff (polar clamp + frame validation), which held.

### Fixed (pre-6.0.0 convergence review, round 20)

- **`from_iso_utc_time(None)` (or any non-string) raises `KerykeionException`.**
  The `.replace("Z", …)` call is now inside the guarded block, so a non-string
  timestamp surfaces as the library's exception instead of a raw
  `AttributeError` — completing the ISO error-contract consistency from round 19.

This round was primarily a convergence check: an adversarial re-review of the
round-19 diff, a thread-safety sweep (300 concurrent tasks across 32 workers —
all bit-identical to sequential references, thread-local session-depth counter
correctly isolated, TTL-segregated cache safe under concurrent creation), and a
data-table audit (fixed stars, Arabic Parts day/night formulas, Vimshottari
nakshatra lords, exaltation degrees, aspect-degree maps, sign element/quality
tables) — all verified correct with no changes needed beyond the fix above.

### Fixed (pre-6.0.0 cross-cutting review, round 19)

- **Malformed ISO timestamps raise `KerykeionException`, not a raw
  `ValueError`.** `AstrologicalSubjectFactory.from_iso_utc_time` and the three
  `PlanetaryReturnFactory.*_from_iso_formatted_time` entry points wrapped
  `datetime.fromisoformat`, so an empty/garbage/out-of-range timestamp
  (`""`, `"not-a-date"`, `"2023-06-15T25:00:00Z"`) now fails with the library's
  own exception — matching `from_birth_data` and the `from_iso_range` timing
  factories. (`EphemerisDataFactory` keeps its documented, tested `ValueError`
  contract.)

### Fixed (pre-6.0.0 cross-cutting review, round 18)

- **GeoNames request cache is segregated by TTL.** requests-cache stamps each
  entry's expiry at write time and every instance shared one sqlite store, so a
  caller asking for a 1-day `cache_expire_after_days` could be served a 30-day
  entry another instance wrote. The store filename now carries the TTL suffix.
- **`FetchGeonames` releases its session** via a new `close()` and context-
  manager protocol; every internal lookup now uses `with FetchGeonames(...)`,
  so the sqlite-backed session's file descriptors are freed deterministically
  instead of at GC time.
- **Nested `ephemeris_session` calls now warn.** The lock is re-entrant, but an
  inner session's cleanup resets the sidereal/topocentric state the outer one
  configured (a silent ~0.88° shift). No internal path nests; the warning
  guards raw callers.
- **Chart-data `active_points` metadata lists the fixed stars actually
  aspected.** `SingleChartDataModel`/`DualChartDataModel` now source
  `active_points` and `active_aspects` from the aspects model, so catalog stars
  appear and ignored declination aspects (`parallel`/`contra-parallel`) do not —
  the serialized metadata describes the real calculation.
- **Aspects models drop uncomputed declination aspects from `active_aspects`.**
  A `parallel`/`contra-parallel` entry the longitudinal engine ignores no
  longer appears in the serialized `active_aspects`.
- **`to_context([])` fails with an actionable message.** An empty list is
  ambiguous (empty midpoints vs empty aspects); the `TypeError` now points at
  `midpoints_to_context([])` for an intentionally empty midpoints set (this also
  restores a clear path for `MidpointFactory.compute` returning `[]`).
- **Docs/examples**: `ChartDataFactory` class docstring enables
  `include_relationship_score`; `settings.md` marks `load_settings_mapping`
  deprecated; `aspects.md` uses `DEFAULT_CELESTIAL_POINTS_SETTINGS` instead of
  undefined placeholders; the transit examples use a 4-hour ephemeris step
  (no sub-sampling warning); the pandas cookbook recipe notes its prerequisite.

### Known limitations

- **DST-zone charts after 2037 use a frozen offset.** Local↔UTC conversion for
  named IANA timezones goes through `pytz`, whose compiled transition tables
  end around 2037. For a birth/event date past the last compiled transition in
  a DST zone (e.g. a summer 2038+ `America/New_York` chart), `pytz` freezes the
  offset at the last known entry instead of applying the zone's perpetual DST
  rule, so the resolved instant can be off by one hour (Moon ≈ 0.55°, angles up
  to ~15°). `from_iso_utc_time` is unaffected (it starts from the UTC instant).
  Dates within the mainstream range (through ~2037) are exact; a `zoneinfo`-based
  resolution that honors perpetual rules is planned for a future release.
- **Converse primary directions are approximate.** `PrimaryDirectionsFactory`
  computes the converse arc as the arithmetic complement of the direct arc
  (`360 - direct`), not the classical converse method (swap significator and
  promissor, recompute the oblique ascension under the promissor's pole).
  Converse (`is_converse=True`) timings should not be relied on for precise
  work; a proper implementation is planned for a future release. Direct
  directions are unaffected.
- **BCE event timestamps use the proleptic Gregorian calendar** (as ISO 8601
  mandates), while BCE *natal chart* dates use the Julian calendar (the
  astro.com convention). For the same ancient instant, an event ISO timestamp
  and a chart date differ by the Julian/Gregorian gap (~2 days near year 0).
  This is a deliberate split: ISO strings stay standards-conformant, chart
  dates stay astrological.
- **Minor bodies degrade silently to a Keplerian approximation near the date
  range edges.** For birth years roughly outside ~1600–2450 (the SPK coverage
  of the bundled asteroid kernels), the default `libephemeris` backend returns
  an unperturbed two-body position for Chiron, the asteroids and TNOs (error up
  to several degrees), with the same success flag as an accurate value — so
  kerykeion cannot detect it and the body is not dropped. The Sun, Moon and
  main planets stay accurate across the loaded ephemeris' whole date range (the
  default `DE440s` install covers 1849–2150; the `medium` tier extends the
  planet range to 1550–2650 — see the supported-date-range note in the README),
  and mainstream modern charts (1900–2100) are unaffected. Install the wider SPK
  kernels (or enable auto-download) for accurate minor-body positions at extreme
  dates; libephemeris logs a `source=Keplerian (fallback)` warning to stderr
  when this happens.
- **Intermediate house-cusp speeds are backend-dependent.** Only the four
  angular cusps (1st/ASC, 4th/IC, 7th/DSC, 10th/MC) carry a physically
  meaningful diurnal speed. The `speed` of the eight intermediate cusps is a
  house-system construction artefact with no standard astrological meaning, and
  the `libephemeris` and `swisseph` backends disagree on it by up to several
  deg/day. The cusp longitudes themselves are identical across backends; only
  the intermediate-cusp `speed` field differs.
- **Heliacal event dates are backend-dependent (visibility-model difference).**
  `HeliacalFactory` passes identical arguments to each backend's `heliacal_ut`,
  but the two backends use different visibility models — `libephemeris` routes
  the computation through Skyfield, `swisseph` uses its native arcus-visionis
  algorithm — so a heliacal rising/setting date can differ by up to ~9 days
  between backends (the underlying planet positions feeding the search agree to
  arcseconds; only the visibility threshold differs). The planetary positions,
  house matrix (including the polar fallback), Gauquelin sectors, sidereal
  ayanamsas, and every other event factory agree across backends within the
  documented ~0.2° / few-second tolerances; heliacal is the one technique whose
  *output date* is materially model-dependent.
- **Secondary progressions are rebuilt through a whole-second ISO round-trip.**
  `SecondaryProgressionFactory` derives the progressed instant as a float Julian
  Day but rebuilds the chart via an ISO-8601 UTC string (`from_iso_utc_time`),
  which is second-precision, so the progressed Julian Day is rounded to the
  nearest second (≤ ~0.5 s error). Fast bodies deviate from the exact-float-JD
  ephemeris by up to ~0.3 arcsecond (~8e-5° for the Moon) — sub-arcsecond and
  astrologically negligible (far inside the day-for-a-year technique's own
  precision), but not bit-exact against a raw `ephe.calc_ut` at the float JD.
- **Quadrant house systems flip the MC and reverse their cusps inside the polar
  circle (Swiss Ephemeris convention).** For latitudes inside the polar circle
  (onset ~66.5°, depending on ARMC), Campanus (`C`), Regiomontanus (`R`),
  Polich-Page (`T`), APC (`Y`) and Sunshine (`I`) return a Medium Coeli on the
  `RA = ARMC + 180°` branch (the *above-horizon* meridian∩ecliptic point) and a
  correspondingly reversed cusp ring (the 12 `abs_pos` gaps sum to ~3960° rather
  than 360°); `Sunshine` (`I`) further collapses several cusps onto one longitude
  when the Sun is circumpolar, in both hemispheres. This is **not a defect**: it
  is the reference Swiss Ephemeris convention (inside the polar circle the
  quadrant MC is redefined as the above-horizon meridian point), reproduced by
  `libephemeris` for bit-for-bit parity — verified 0 mismatches vs the reference
  across an 800-case grid, and documented upstream as working-as-intended
  (libephemeris#46, `known-differences` §2.4). The *astronomical* MC — a function
  of RAMC only — is what the latitude-independent systems Whole Sign (`W`), Equal
  (`A`), Porphyry (`O`) and Meridian (`X`) return, unflipped, at every latitude;
  the Ascendant is never flipped either. Placidus (`P`) and Koch (`K`) instead
  raise `PolarCircleError` inside the polar circle, which kerykeion catches and
  clamps to the ±66° limit with a warning. Real-world impact is nil (no Antarctic
  births). Callers who need forward-partitioning cusps at polar latitudes should
  use `W`/`A`/`O`/`X`, or validate that the 12 cusp gaps sum to 360°. An opt-in
  polar-safe mode (astronomical MC + forward cusps, or a raise) may be offered in
  a future release, mirroring the upstream v4 opt-in flag.

### Changed (breaking, pre-6.0.0 full-codebase review, third pass)

- **`AspectName` literal: `"contra_parallel"` renamed to `"contra-parallel"`**,
  aligning the separator with every other multi-word aspect name
  (`"semi-sextile"`, `"semi-square"`). The old underscore spelling is gone from
  the literal, the aspects factory output and the report glyph table; update
  any stored configuration or JSON consumers before upgrading.
- **Single-chart aspects skip mean×true lunar-node artifact pairs.** With both
  node variants active, every chart used to report a permanent ≤1.75°-orb
  Mean×True conjunction (and near-opposition with the opposite end) — a
  configuration artifact, not an aspect. Cross-chart (synastry/transit) node
  pairs are unaffected. Golden report fixtures were regenerated.
- **Declination aspect methods now share the longitudinal contract**:
  `single_chart_declination_aspects` / `dual_chart_declination_aspects`
  intersect the caller's `active_points` with each subject's own
  `active_points` (they previously replaced them) and reject a negative `orb`
  with `KerykeionException`.
- **Uniform error contract: `KerykeionException` replaces `ValueError`** in
  `AspectsFactory` (`axis_orb_limit`), fixed-star discovery (negative `orb`),
  and `SignIngressFactory.from_iso_range` / `RetrogradeStationFactory.
  from_iso_range` (malformed ISO input, matching the lunation factory).
- **`to_context([])` raises the documented `TypeError`** instead of silently
  serializing any empty list as a zero-count midpoints analysis
  (`midpoints_to_context([])` remains available for an intentional empty set).
- **`RelocatedChartFactory.relocate` rejects Topocentric subjects** with
  `KerykeionException`: planets would keep the natal observer's parallax (up
  to ~1-2° for the Moon), producing an internally inconsistent chart.
  Recreate the subject at the new coordinates instead.
- **`from_iso_utc_time` no longer overwrites explicit coordinates**: passing
  `lat`/`lng` skips the GeoNames lookup entirely (same semantics as
  `from_birth_data`); the fetched city centroid only fills in what is missing.
- **BCE dates are validated**: the `year < 1` path used to pass raw fields to
  `julday`, silently extrapolating impossible dates (month 13, day 32) into a
  different chart; it now raises `KerykeionException` like the CE path.
- **GeoNames is reached over HTTPS** (`secure.geonames.org`) and the request
  cache default moved from the CWD-relative `cache/` to the per-user
  `~/.kerykeion/cache/` (a read-only CWD no longer breaks online charts).
  With explicit `lat`/`lng` but no `tz_str` and no `city`, `from_birth_data`
  now resolves the timezone from the coordinates (timezoneJSON) instead of
  silently using the default city's timezone (Tokyo coordinates no longer get
  Greenwich time, ~9 h off).
- **`MoonPhaseDetailsFactory`: malformed/empty subject timestamps raise**
  `KerykeionException` instead of silently computing the phase for "now".
- **`EclipseFactory.search_global`/`search_local` default `start_year`** is now
  the current UTC year instead of the hardcoded 2025.
- **Dominants**: the `modern` strategy's aspect channel always sees all four
  angles, so the ranking no longer changes with the subject's `active_points`
  configuration; the `elemental` strategy treats an explicit `active_points=[]`
  as a real empty filter (zero totals), matching the factory convention above.
- **`kerykeion.settings.__all__` drops `load_settings_mapping`** (deprecated at
  birth, "removed in 7.0.0"); it stays importable from
  `kerykeion.settings.kerykeion_settings` for the v6 cycle. The sibling
  `load_language_pair` is now re-exported as its `__all__` promised.

### Fixed (pre-6.0.0 full-codebase review, third pass)

- **Dual-wheel charts: the second subject's glyphs are always drawn.**
  `show_degree_indicators=False` used to remove the entire outer ring of
  transit/partner planets (glyphs included); the flag now gates only tick
  lines and degree labels.
- **Glyph anti-collision works across 0°/360°**: the overlap scan is now
  circular (it starts after the widest gap), so a conjunction straddling the
  Aries point (29°58' Pisces + 0°10' Aries) is spread like any other pair
  instead of overlapping. Dense stelliums that exceed the available space now
  get a proportional partial spread instead of no spread at all.
- **Arc-seconds render correctly in chart grids**: the degree formatter emits
  `&quot;` so the SVG quote-replace pass can't corrupt `24°05'23"` into
  `24°05'23'` (previously wrong on every rendered chart, declination column
  included).
- **Transit chart "table" aspect grid no longer clips**: it uses the same
  (550, 450) anchor as Synastry/DualReturn — the hardcoded (600, 520) pushed
  the glyph header row past the viewBox bottom on every table-mode Transit.
- **Declination aspects can't masquerade as conjunctions**: both aspect grids
  and the modern wheel's aspect core skip aspects that have no entry in
  `aspects_settings` (a hand-built `parallel` aspect used to render the
  conjunction glyph / a longitude chord).
- **Dual-chart aspect models honor `*_subject_is_fixed` for axis-axis pairs**:
  the speed override now applies before the axis-axis branch, so fixed charts
  no longer persist synthetic cusp speeds (~360°/day) on those pairs.
- **Composite factories: `hash(CompositeSubjectFactory)` works** (it hashed
  unhashable pydantic models — every call raised `TypeError`); missing
  `julian_day` on composite subjects is now caught with a clear
  `KerykeionException` in `PlanetaryNodesFactory`, `PlanetaryPhenomenaFactory`
  and `next_heliocentric_return` instead of a raw backend `TypeError`.
- **Transit refinement works on BCE ranges**: `_sampling_gaps_days` parses
  extended-year ISO timestamps (the same ones `_iso_chronological_key`
  supports), so per-pass splitting/refinement no longer silently degrades;
  flat orb plateaus of any width dedupe to a single exactness event.
- **`inline_css_variables_in_svg` can't hang**: self-referential CSS variables
  in a custom theme now hit an iteration cap (with a warning) instead of
  looping forever.
- **Partial-date defaults use the subject's timezone**: `from_birth_data`
  without a date used to capture the host machine's naive wall clock and
  reinterpret it in the target timezone (off by the full host-target offset).
- **Report/serializer parity**: `ReportGenerator` accepts raw
  `CompositeSubjectModel`/`PlanetReturnModel` like `to_context` always did.
- **Models**: the midpoints, primary-directions, astro-cartography,
  secondary-progressions and fixed-star-catalog models are subscriptable like
  every other public model; `SingleChartDataModel.active_points` /
  `DualChartDataModel.active_points` accept catalog star names (matching the
  aspects models); `PointInHouseModel`'s owner-house fields are optional with
  `None` defaults; `kr_models` imports its literals directly from
  `kr_literals` (removing a fragile import-order dependency).

### Added (pre-6.0.0 full-codebase review, third pass)

- **GitHub Actions CI** (`.github/workflows/ci.yml`): ruff + mypy + pyright and
  the base-tier offline test suite on Python 3.12/3.13, with ephemeris-kernel
  caching and a build smoke check.
- **`OccultationFactory` accepts planet names** (`"Venus"`) in addition to raw
  Swiss Ephemeris integer ids; **`HeliacalFactory` accepts `lat=`/`lng=`/
  `altitude=` keywords** as a safer alternative to the `geopos` tuple
  (longitude first — the tuple order is now documented).
- **`FetchGeonames.get_timezone_for_coordinates(lat, lng)`**: coordinate-based
  timezone resolution over the same cached session.
- **`CHART_TYPE_PROGRESSION` constant** completes the `ChartType` coverage in
  `kerykeion.settings.config_constants`.

### Changed (breaking)

- **`ChartDataFactory` now treats an explicit `active_points=[]` as a real
  (empty) filter**, not as "use the subject's own points" — `None` is the
  documented sentinel for the latter. A chart requested with `active_points=[]`
  therefore has no active points (no aspects, element/quality distributions all
  0.0). This aligns with the timing factories' convention, but is the *opposite*
  of `AstrologicalSubjectFactory`, where an emptied list still means "no filter →
  all points"; pass `None` (or omit the argument) to get the subject's points.

### Fixed (pre-6.0.0 full-package review, second pass)

- **Fixed stars in `pure_count` distributions count as 1**, not 0.2: the
  weighted-mode star table weight leaked into `pure_count`, breaking its integer
  semantics (a Sun+Moon+Regulus count read 2.2). `DominantsFactory`'s elemental
  school also opts into fixed stars so its numbers keep matching the chart's
  element/quality distributions for a star-bearing subject.

- **Online GeoNames gating**: PlanetaryReturnFactory fetches when ANY of
  tz_str/lat/lng is missing (an AND gate crashed callers passing only tz_str);
  explicit lat/lng/nation/tz are never overwritten by the fetched city
  centroid; `from_current_time` resolves the target timezone BEFORE capturing
  the instant (the naive host wall clock shifted the "current moment" by the
  full host-city offset); `from_iso_utc_time` raises `KerykeionException`
  instead of a bare `KeyError` on failed lookups.
- **Chart rendering**: ASC/MC/DSC/IC get their dedicated radius via NAME
  classification (the fossil index window pointed at Ceres/Pallas/Juno/Vesta
  and shifted with filtering); dual charts no longer paint two spurious ticks
  at the last natal planet's angle; degree-indicator grouping is
  circular-aware; exact full/new moons render bright/dark instead of inverted;
  a reduced `aspects_settings` no longer breaks every render on missing
  `orb_color_*`; unknown-aspect rows no longer emit `xlink:href="#orbNone"`.
- **Aspects**: applying/separating no longer flips for tight aspects to
  fast movers (adaptive lookahead step; axes carry ~300 deg/day synthetic
  speeds); `AspectModel.diff` wraps at 0/360; overlapping user orbs classify
  by the closest aspect.
- **Time series**: EphemerisDataFactory steps in UTC — the naive wall-clock
  series duplicated samples across DST spring-forward and corrupted transit
  detection.
- **Returns/report/XML**: Heliocentric and node-crossing returns are titled
  by their actual type (was always "Lunar Return"); the AI-context XML emits
  positions for every active point (TNOs, Uranian points, mean nodes, Arabic
  parts were referenced by <aspects> but never serialized); the transit
  subject has one consistent name in house overlays.
- **Factories**: RelationshipScoreFactory raises `KerykeionException` when a
  subject lacks the Sun; relocation applies the natal polar clamp; midnight-sun
  days re-pair sunrise/sunset (day_length was negative at Reykjavik in June);
  heliacal scans skip backend "no event" signals from BOTH backends (pyswisseph
  errors aborted the scan; libephemeris jd=0.0 sentinels emitted fake events
  dated -4713); `PlanetaryNodesFactory` validates `method` ('Mean' silently
  selected osculating data labeled with the caller's string).
- **Edge cases**: polar day/night at exactly ±90° respects the -0.833°
  apparent-horizon threshold; the ACG latitude grid reaches the requested
  edge (float accumulation dropped 66.0 at step=0.1); infinitesimally negative
  longitudes no longer wrap to exactly 360.0 and crash; an explicit empty
  `active_points` list on ChartDataFactory is a real filter (None remains the
  "subject's own points" sentinel); a station exactly on the range's first
  sample is counted; `applying_start=None` semantics documented (truncation OR
  undersampled fast pass).
- **Deprecations**: `natal_aspects`/`synastry_aspects` emit a real
  DeprecationWarning (removal 7.0.0); `next_return_from_month_and_year` names
  its removal version; `load_settings_mapping` is deprecated in favor of the
  cached `translations.load_language_settings`. Docs snippet gate is green
  (75/75); `llms.txt` performance tips show kwargs on their actual factories.

### Fixed

- **`PlanetaryNodesFactory` passed `method`/`flags` to `nod_aps_ut` in swapped
  positions**, so every `method="mean"` request silently returned *osculating*
  nodes/apsides on both backends (Moon mean ascending node came back ~123.95°
  instead of ~125.04° at J2000). The regression test made the same swapped call
  and agreed on the wrong answer; a new test locks `mean != osculating`.
- **Gauquelin sector rendering assumed ascending cusps** while `houses_ex2(b'G')`
  returns *descending* (diurnal) ones: classic sector labels landed exactly 180°
  away in the opposite sector, the classic fallback grid was anchored at 0° Aries
  instead of the ASC, the clickable sector wedges rendered as mirrored-center
  lens shapes, and the modern overlay rotated with `rotate(+angle)` (mirror image
  of every other chart element). All drawers now share the descending,
  ASC-anchored convention.
- **BCE Davison composites were cast days away from the true time midpoint**
  (~74 h at year −100, lng 30E): the midpoint JD was decomposed proleptic-Gregorian
  while the BCE birth path re-encodes components in the Julian calendar with a
  longitude-LMT offset. Ante-CE midpoints now decompose as the exact inverse of
  that path (round-trip < 1 s).
- **Planetocentric charts stored the center body's geocentric position under a
  planetocentric label** (e.g. a Marscentric chart carried the geocentric Mars in
  aspects and houses). The center body is now excluded from the active points
  with a warning, including via Arabic-Part prerequisite auto-activation;
  `lunar_phase` is `None` for Selenocentric subjects. An explicit
  `active_points` list containing *only* the center body raises
  `KerykeionException` (an emptied list would otherwise mean "no filter" and
  silently invert into a full chart).
- With `KERYKEION_BACKEND=swisseph` and no `KERYKEION_EPHE_PATH`, the backend now
  **auto-detects the default download directory of
  `python -m kerykeion.swisseph_setup` (`~/.kerykeion/sweph`)** before falling
  back to Moshier — previously the downloaded files were silently ignored unless
  the env var was also exported (dropping Chiron and fixed stars).
- Ante-CE `day_of_week` is computed from the local-mean-time date (like the
  CE path) instead of the UT julian day; heliacal BCE datestamps format as
  `-0049`, not `-049`; heliocentric-return and node-crossing charts keep the
  solver's sub-second precision instead of flooring to the second.
- The five v6 Lilith/Priapus/apse points (`Interpolated_Lilith`,
  `Mean_Priapus`, `True_Priapus`, `Interpolated_Perigee`, `White_Moon`) render
  with **dedicated glyphs** in all chart styles instead of the generic
  fixed-star symbol, and the latter two weigh 0.5 (not the 1.0 fallback) in
  element/quality distributions.
- **Fixed stars count toward element/quality distributions again** (weight 0.2
  for every star unless the table overrides it): v6 moved stars to
  `subject.fixed_stars`, which made the star weight-table entries unreachable.
  Star inclusion is opt-in via `include_fixed_stars=True` on the element/quality
  helpers — single-subject *and* synastry (the chart data factory opts in for
  both) — so callers naming an explicit point subset get exactly those points;
  star names go through the shared catalog slugger.
- `DualReturnChart` without secondary points now raises `KerykeionException`
  like every other dual chart type instead of silently rendering a bi-wheel
  with the outer return wheel missing.

### Performance

- **Sign-ingress and retrograde-station scans are ~8-10x faster** with
  identical results: sampling steps are sized per planet from station
  acceleration (Mercury keeps the half-day step; the Pluto tier moves to 7
  days) and bisection stops at the output's 1-second granularity instead of
  40 fixed iterations. Verified event-identical (timestamps within 10 ms)
  against the previous implementation on a 1980–2100 full-planet scan.

### Internal

- Consolidated duplicated helpers ahead of the API freeze: one shared
  `jd_to_iso_utc` (was five private copies with two divergent day-boundary
  behaviors), one `utilities.wrap_180` (was four wrap-to-±180 variants with
  two boundary conventions), planet-name→ephemeris-id maps derived from the
  canonical `POINT_NUMBER_MAP`, and `MidpointFactory._shorter_arc_midpoint`
  delegating to `utilities.circular_mean`.

### Removed

- **The deprecated pre-6.0.0b1 alias names were removed**, as their
  `DeprecationWarning` promised ("removed in kerykeion 6.0.0 stable"):
  `ProgressedToNatalAspect`, `SecondaryProgressionsResult`,
  `SolarArcDirectedAspect`, `SolarArcDirectedPoint` (from `kerykeion`),
  `ACGLine`, `ACGLinePoint` (astro_cartography), `SpeculumEntry`
  (primary_directions) and `FixedStarMetadata` (fixed_stars), together with the
  internal `kerykeion._deprecation` helper. Use the corresponding `*Model` names.

### Changed

- **`libephemeris` dependency relaxed from the exact `==3.0.0rc1` pin to
  `>=3.0.0rc1,<4`** so the stable release does not conflict with other
  constraints; the README now documents the bundled data range (1849–2150,
  DE440s) and how to install the wider `medium`/`extended` tiers.
- `next_return_from_year`'s deprecation message now states the removal target
  (kerykeion 7.0.0), consistent with the package's other deprecations.
- Note for feature-detection code: accessing removed v5 names such as
  `kerykeion.AstrologicalSubject` raises `ImportError` with migration guidance —
  this also applies to `hasattr()`/`getattr(..., default)`; use
  `try/except ImportError` instead.

- **BREAKING (alpha):** the chart geometry/time helpers in
  `kerykeion.charts.charts_utils` were renamed to PEP8 `snake_case` with **no
  compatibility aliases**: `sliceToX`→`wheel_x`, `sliceToY`→`wheel_y`,
  `decHourJoin`→`hms_to_decimal_hours`, `offsetToTz`→`timedelta_to_decimal_hours`,
  `degreeDiff`→`degree_difference`, `degreeSum`→`degree_sum`,
  `normalizeDegree`→`normalize_degree`, `makeLunarPhase`→`make_lunar_phase`. Code
  importing the old names directly must update its imports. Pure refactor —
  numerically identical output. The template-dict key `"makeLunarPhase"` is
  intentionally left unchanged.

### Documentation

- **Documentation completeness, accuracy & navigation pass** (no code or public-API
  changes — only docs and one model docstring). Documented previously-undocumented
  public features in the README and the `site/docs/` set: chart **Dominants**
  (`DominantsFactory`), **Zodiacal Releasing / aphesis** (`ZodiacalReleasingFactory`),
  the date-range event finders **Lunation / Retrograde-station / Sign-ingress**
  (`LunationFinderFactory`, `RetrogradeStationFactory`, `SignIngressFactory`),
  **House Comparison** (`HouseComparisonFactory`) and the **Arabic Parts / Lots**
  (`Pars_Fortunae`/`Pars_Spiritus`/`Pars_Amoris`/`Pars_Fidei`); added five new
  `site/docs/` pages and README sections + TOC entries. Corrected stale figures to
  match the code: `DEFAULT_ACTIVE_POINTS` is **14 points** (not 18), the default
  aspect set is the **five majors** (Quintile is not active by default),
  `PerspectiveType` has **11 values**, and the libephemeris pin in the a60 note is
  `3.0.0a6`. Reframed the backend wording to "libephemeris by default, optional
  Swiss Ephemeris", fixed broken README links and a TOC ampersand, removed CI
  references (no-CI policy) from `TEST.md`/`DEVELOPMENT.md`, retitled the root
  migration stub to "v4/v5 → v6", reduced `RELEASE_NOTES.md` to a pointer at this
  changelog, marked `REFACTORY.md` as an internal/historical note, and expanded the
  `AstrologicalBaseModel` docstring to describe the computed celestial/house fields.
- **Second documentation review — expansion & corrections** (docs only). Documented
  the `PlanetaryReturnFactory` **heliocentric returns** and **lunar-node crossings**
  (8 entrypoints the page previously advertised but did not cover) and added
  `Heliocentric` / `Lunar_Node_Crossing` to the `ReturnType` reference; documented the
  **Davison** time-space composite on the Composite Subject Factory page and
  `SolarArcFactory.compute_directed_subject` (biwheel-ready directed chart); added
  per-point custom-orb docs (`point_orb_adjustments`) and a runnable custom-aspects
  README example; documented `DominantsFactory.available_methods()`. Filled out the
  result-model field tables for the Lunation/Retrograde/Sign-ingress finders and the
  Dominants/Zodiacal-Releasing models. Fixed regressions from the first pass:
  `station_type` values are **`"SR"`/`"SD"`** (not "retrograde"/"direct"), removed the
  leftover Quintile from the default-aspect listing in `constants.md`/`settings.md`,
  and corrected the README "Timing Factories" count (six, not three). Reframed
  remaining "Swiss Ephemeris"-as-engine wording (eclipse/occultation/planetary-return)
  to backend-neutral, and surfaced the Swiss Ephemeris configuration page in the docs
  nav.

## 6.0.0a60

_2026-06-24_

### Changed

- **Bumped `libephemeris` pin to `3.0.0a6`** and **regenerated all golden
  baselines on the full-range DE441 extended kernel (±8000+).** Positions, SVG
  charts, report fixtures and configuration goldens now reflect DE441 across the
  whole supported range, so ancient/far-future subjects (e.g. 500 BCE, 3000 CE)
  are computed accurately instead of falling back at the short-range kernel edge.
  Modern charts are unchanged beyond sub-arcsecond ephemeris-version drift
  (libephemeris a4→a6, ≤ ~3.5″ on far-future points only).
  Verified vs Swiss Ephemeris: at matched ΔT the engines agree to < 0.1″ on all
  bodies; the remaining far-epoch differences are the ΔT-extrapolation model
  (documented in libephemeris, benign). Full suite on the extended kernel:
  10617 passed · 0 failed.

### Fixed

- `test_ancient_rome_has_fewer_points_due_to_ephemeris` is now kernel-aware: the
  "fewer points due to ephemeris" behaviour only holds on the short-range default
  kernel; with the full-range kernel the ancient TNOs are computable, so the test
  skips (with reason) instead of failing.

## 6.0.0a59

_2026-06-24_

### Changed (breaking)

- **`MoonPhaseSunInfoModel` sun-timing fields are now native date/time types** —
  `sunrise` and `sunset` change from an integer epoch timestamp to a
  timezone-aware `datetime`; `solar_noon` changes from `str` to `datetime`; and
  `day_length` changes from `str` to `timedelta`. The two convenience string
  fields `sunrise_timestamp` and `sunset_timestamp` (previously `"HH:MM"`
  strings) are removed with no alias. The serialized JSON shape changes
  accordingly (ISO-8601 datetimes/duration instead of integers/strings).
  Migration: derive the old `"HH:MM"` value via `sun.sunrise.strftime("%H:%M")`
  instead of reading `sun.sunrise_timestamp`, and treat `sun.sunrise` as a
  `datetime` rather than an epoch integer. `get_type_hints()` on the public API
  is unaffected.
- **`axis_orb_limit` now also filters dual-chart aspects** — previously the
  axis-specific orb limit was applied to single-chart aspects only and was a
  documented no-op for synastry/transit/composite (dual-chart) calculations.
  It is now applied uniformly: when a non-`None` `axis_orb_limit` is passed to
  `AspectsFactory.dual_chart_aspects` (and through `TransitsTimeRangeFactory`
  and `RelationshipScoreFactory`), aspects involving a chart axis
  (Ascendant, Medium_Coeli, Descendant, Imum_Coeli) on either subject are kept
  only when their orb is below the limit. Callers that previously relied on the
  value being ignored for dual charts will see fewer axis aspects (and, for
  relationship scoring, possibly a different score). The default remains `None`
  (no axis filtering), so callers that never set `axis_orb_limit` are unaffected.

### Fixed

_Follow-up pass addressing the CodeRabbit review on PR #224._

- **`house_position` chart label was a duplicate of `natal_house`** — the new
  `house_position` field (the "house position" comparison-grid column header for
  transit/return charts) shipped with the `natal_house` value ("Natal House" and
  its translations) in all 10 languages, the model default, and the three
  `chart_drawer` fallbacks. It now renders the correct, distinct label
  ("House Position", "Posizione in casa", "Position en maison", "宫位", …). The
  affected English golden SVG fixtures were updated accordingly.
- **`MoonPhaseSunInfoModel.solar_noon` could carry the wrong local offset on
  DST-transition days** — the midpoint was computed with raw `pytz` arithmetic,
  which keeps sunrise's offset; the instant was correct but the serialized
  wall-clock offset could be off by the DST shift. The midpoint is now
  normalized back through the timezone.
- **`format_timedelta_hhmm` used banker's rounding** — exact half-minute
  durations (e.g. `0:30`) rounded to the nearest *even* minute. It now rounds
  half-up, so report and LLM-context durations are consistent at the boundary.
- **`AspectsFactory` axis filtering rejects non-positive `axis_orb_limit`** — a
  `0` or negative value silently dropped every axis aspect; it now raises
  `ValueError`.
- **`MoonPhaseSunInfoModel` enforces timezone-aware sun times** — `sunrise`,
  `sunset` and `solar_noon` now reject naive `datetime` values via a validator,
  matching the documented local-time contract. The field annotations are
  unchanged, so `get_type_hints()` on the public API is unaffected.

### Documentation

- `ephemeris_session()` now documents the shared `DEFAULT_SIDEREAL_MODE` fallback
  instead of a hardcoded `"FAGAN_BRADLEY"`; the `TransitsTimeRangeFactory`
  `axis_orb_limit` docstrings now list all four axial points.

## 6.0.0a57

_2026-06-16_

### Fixed

- **Fixed-star discovery no longer drops bright stars to a position collision** —
  `FixedStarDiscoveryFactory.find_prominent_stars` deduplicated candidates by
  ecliptic longitude rounded to two decimals (`round(deg, 2)`). With the small
  curated catalog this was harmless, but libephemeris 3's 1447-star catalog packs
  many physically distinct stars within 0.01° of longitude, so the second star in
  catalog order was silently discarded — and catalog order is not magnitude order.
  This suppressed astrologically relevant bright stars in favour of faint
  neighbours (e.g. Nunki, σ Sgr mag 2.02, lost to Beta Scuti mag 4.22, both at
  282.26°). Deduplication is now by star identity (`entry.name`) instead of
  position, so every distinct star within orb is reported. Discovery results grow
  accordingly (more conjunct stars returned for a given orb).

## 6.0.0a56

_2026-06-16_

Rebased on **libephemeris 3** (`3.0.0a3`), the first major release of the
ephemeris backend. The dependency pin moves from `>=2.0.2,<3.0.0` to
`==3.0.0a3`. Two backend behaviour changes propagate into chart output; the
affected report and SVG golden fixtures were regenerated.

### Changed (breaking)

- **Ephemeris backend handle renamed `swe` → `ephe`** — the unified backend
  object exposed by `kerykeion.ephemeris_backend` is now `ephe`
  (`from kerykeion.ephemeris_backend import ephe`). The old `swe` name is
  removed with no alias: it implied Swiss Ephemeris is the engine, but
  libephemeris is the primary backend and swisseph is a legacy fallback. Update
  any `from kerykeion.ephemeris_backend import swe` import to `ephe`. The
  internal helper `compute_sun_rise_set_swe` is likewise `compute_sun_rise_set_ephe`.

### Changed

- **Dependency: libephemeris `2.x` → `3.0.0a3`** — bumped to the new major
  series and pinned exactly while it is in alpha. libephemeris 3 ships the
  four-backend architecture (Skyfield, the LEB fast path, JPL Horizons, and an
  adaptive `auto` mode) behind the same `calc_ut()` interface; core planetary
  positions are unchanged within tolerance.

### Changed (ephemeris output)

- **White Moon / Selena repositioned** — libephemeris 3 computes Selena
  (body 56) on a ~7-year period (≈ `+0.1408°/d`) instead of the previous
  ~8.8-year period (≈ `+0.1120°/d`), shifting the point by up to a full sign in
  every chart that includes it. White Moon is part of `ALL_ACTIVE_POINTS` (not
  the default point set), so default charts are unaffected; all-points reports
  and SVGs change their White Moon placement, element/quality distribution, and
  aspect list.
- **Out-of-SPK-range bodies fall back to a Keplerian approximation** — for dates
  outside the SPK kernel coverage (≈ 1900–2100), asteroids and TNOs that were
  previously dropped now return a degraded two-body position (~1–2°) instead of
  raising, so historical and far-future all-points charts list more points
  (e.g. the 1879 Einstein natal report grows from 45 to 53 active points).

## 6.0.0a55

_2026-06-11_

Stabilization pass: process-wide thread safety for
ephemeris access, sidereal-zodiac correctness across every search and
refinement path, aspect and SVG-rendering fixes, hardened event finders,
packaging cleanup — followed by a five-round review with a final
hardening pass (below).

### Added (hardening)

- **Public model export parity** — every public Pydantic model (87) is now
  importable from `kerykeion.schemas`, the canonical home the `kr_types`
  deprecation message points to (37 were previously reachable only from the
  deprecated path or deep module paths). Feature subpackages (`eclipses`,
  `astro_cartography`, `primary_directions`, `planetary_nodes`) now export
  their result models, and top-level `kerykeion` exports every model returned
  by a public factory (`AstrologicalSubjectModel`, `TransitEventsTimeRangeModel`,
  `SolarEclipseModel`, ...). A new regression test
  (`tests/core/test_public_api_surface.py`) locks the policy: schemas parity,
  subpackage exports, factory-return exports, `typing.get_type_hints` on every
  public model, and `*Model` naming.
- **`kerykeion.__version__`** — the installed package version, read from
  package metadata at import time.

- **v5 migration errors** — importing the removed v5 entry points
  (`AstrologicalSubject`, `KerykeionChartSVG`, `NatalAspects`,
  `SynastryAspects`) now raises an `ImportError` naming the v6 replacement and
  the migration guide; `ChartDrawer` rejects non-`ChartDataFactory` input with
  the two-step example instead of an opaque pydantic `AttributeError`.
- **Ephemeris tier auto-detection** — a plain `pytest` run probes the loaded
  kernel and skips out-of-range tests with explicit reasons instead of failing
  (pass `--tier=extended` to force-run everything); forcing
  `KERYKEION_BACKEND=swisseph` without `.se1` data files now exits upfront
  with download instructions instead of failing hundreds of golden tests.
- **`poe build:smoke`** — builds sdist+wheel, then imports the wheel and
  renders a natal chart offline in an isolated environment, so missing
  packaged data files (templates, themes) are caught before publishing.

### Changed (hardening)

- **Model naming normalized to `*Model`** — eight new-in-v6 classes renamed
  for consistency with the rest of the public models:
  `SecondaryProgressionsResult` → `SecondaryProgressionsResultModel`,
  `ProgressedToNatalAspect` → `ProgressedToNatalAspectModel`,
  `SolarArcDirectedAspect` → `SolarArcDirectedAspectModel`,
  `SolarArcDirectedPoint` → `SolarArcDirectedPointModel`,
  `ACGLine` → `ACGLineModel`, `ACGLinePoint` → `ACGLinePointModel`,
  `SpeculumEntry` → `SpeculumEntryModel`,
  `FixedStarMetadata` → `FixedStarMetadataModel`. The old names keep working
  as deprecated aliases (emitting `DeprecationWarning`) and will be removed in
  6.0.0 stable.
- **Quality gates green** — mypy (103 source files), pyright and ruff all pass;
  annotation-only fixes, no behavior changes.
- **README** — all 68 embedded code snippets now validated against the real
  API (six were stale: fixed-star access via `active_fixed_stars` +
  `find_fixed_star()`, planetary-phenomena/nodes iteration, field renames
  `nutation_longitude` and `altitude_above_horizon`).

### Fixed

- **Sidereal correctness** — planetary returns (the crossing search now runs in
  the subject's zodiac frame), transit refinement, relocation house cusps,
  fixed-star discovery, astrocartography and planetary nodes all honor the
  active sidereal mode instead of mixing tropical longitudes into sidereal
  charts.
- **Aspects** — the South Node's speed is no longer negated, fixing
  applying/separating classification; geometric opposite pairs
  (Vertex/Anti-Vertex, Lilith/Priapus) and star–star pairs no longer emit fake
  aspects, on both the longitude and the declination paths.
- **Charts** — user-provided strings are XML-escaped in SVG output (XSS / parse
  fix); chart filenames are sanitized; exactly-conjunct planets no longer lose
  a glyph (previously one of two points at the same degree was silently
  dropped); biquintile aspects get their glyph in the modern wheel (the icon
  map used a hyphenated key); the classic theme defines its base palette
  variables, so Uranian-planet colors no longer inline to empty `fill` values,
  and now also the shared General tokens (`neutral-content`, `base-*`,
  `info`/`success`/`error`, `black`/`white`) every other theme defines — the
  house/cusp comparison-grid text referenced an undefined variable in the
  default theme (empty `fill` when CSS variables are inlined);
  SVG minification keeps the optimizer's output intact and applies the
  string-based quote/whitespace fallback only when the optimizer fails.
- **Transits** — `get_transit_events` splits recurring/retrograde passes into
  separate events instead of merging them; under-sampled fast bodies now emit a
  warning; exact-moment refinement uses a true ternary search — the previous
  quartile probing could discard the actual minimum on asymmetric orb curves
  (e.g. near a station) and converge to a slightly wrong moment — and
  `refinement_iterations` now defaults to 21 ternary steps (precision ≥ the
  previously documented 12 halvings).
- **Primary directions** — corrected Placidian pole computation, ecliptic
  aspect-point conversion and the horizon test; directions are labeled
  direct/converse.
- **Events** — DST-gap midnights are resolved for sun times and planetary
  hours; eclipse/lunation backend errors now raise instead of silently
  truncating the scan; BCE timestamps fixed; lunation range parsing accepts
  lowercase-`t` ISO strings.
- **Zodiacal releasing** — peak periods are measured from the Lot of Fortune
  for all released lots.
- **Core** — an out-of-range Sun or Moon raises `KerykeionException` instead of
  silently degrading the subject (note: bulk scans such as
  `EphemerisDataFactory` ranges now fail loudly at the first out-of-range step
  rather than yielding partially gutted subjects); Julian conversions use the
  proleptic Gregorian calendar (pre-1582 dates round-trip); star names passed
  to `active_points` redirect to `active_fixed_stars` with a warning;
  `from_current_time` gains the v6 calc flags and an altitude parameter;
  offset-less ISO timestamps are treated as UTC; a failed planetocentric
  calculation logs a warning before falling back to geocentric positions
  instead of substituting them silently; the swisseph White Moon fallback
  re-activates the point even when it was the only active point requested.

### Changed

- **Thread safety** — a shared `ephemeris_session` context manager in
  `kerykeion.ephemeris_backend` now serializes ephemeris access for all
  factories; `swe.close()` is never called directly, and the pinned
  libephemeris calc mode survives session resets.
- **SVG test baselines re-generated** — the committed baselines predated the
  XML-escape and base-palette fixes above, which silently downgraded their
  comparisons to the lenient line-count path; regenerating restores strict
  per-line comparison. `regenerate:svg` now skips its out-of-kernel 1500 CE
  subject (keeping that baseline stale, like the extended script's ancient
  subjects) instead of aborting, so regeneration completes on short ephemeris
  kernels.

### Changed (breaking — alpha channel)

- **`NatalAspectsModel` / `SynastryAspectsModel` removed** (retroactive note:
  these v5 aliases of `SingleChartAspectsModel` / `DualChartAspectsModel` were
  dropped earlier in the v6 alpha line without a changelog entry). Use
  `SingleChartAspectsModel` / `DualChartAspectsModel` instead.

### Packaging

- **`libephemeris` installed from PyPI** — the local-path `[tool.uv.sources]`
  entry is gone and the pin is relaxed to `>=2.0.2,<3.0.0`.
- **`MANIFEST.in` removed** — dead config under hatchling (which ignores it);
  sdist contents are governed by `[tool.hatch.build.targets.sdist]`. Wheel and
  sdist were inspected to confirm all data files (templates, themes,
  `llms.txt`) ship.
- **No hosted CI** — a GitHub Actions workflow briefly added during the alpha
  line was removed before release; verification is local (`poe check`, tiered
  `pytest`, `poe build:smoke`).

## 6.0.0a54

_2026-06-05_

Adds two sky-event finders: planetary retrograde/direct stations and zodiac
sign ingresses, each scanning a date or Julian-Day range.

### Added

- **`RetrogradeStationFactory`** (`kerykeion.retrograde_stations`) — finds
  planetary retrograde and direct stations (the moments a planet's apparent
  longitudinal motion reverses) across a date or Julian-Day range
  (`from_iso_range` / `from_julian_day`). Backend-agnostic: samples the
  `swe.calc_ut` longitudinal speed and bisects each sign change to the zero
  crossing, like `LunationFinderFactory`. Returns a
  `RetrogradeStationsCollectionModel` whose `StationModel` items carry the
  planet, station type (`SR`/`SD`), UTC timestamp, Julian Day and zodiac
  position. The Sun and Moon are excluded (they never station). Re-exported from
  the package root (`RetrogradeStationFactory`, `StationModel`,
  `RetrogradeStationsCollectionModel`).
- **`SignIngressFactory`** (`kerykeion.sign_ingresses`) — finds zodiac sign
  ingresses (a body crossing a 30° boundary) across a date or Julian-Day range.
  Its `IngressModel` items carry the planet, from/to signs, a retrograde flag for
  re-entries, UTC timestamp and Julian Day. Detects multiple crossings within a
  single sampling interval (a retrograde re-entry near a station) via a recursive
  midpoint probe. The Moon is opt-in. Re-exported from the package root
  (`SignIngressFactory`, `IngressModel`, `SignIngressesCollectionModel`).

Both validate against known anchors (the 2026 Mercury retrograde windows, the
solar equinoxes/solstices, and the 2023–2024 Pluto Capricorn↔Aquarius ingress
dance) and support BCE ranges via `from_julian_day`.

## 6.0.0a52

_2026-06-03_

Adds a lunation-calendar finder and enriches eclipse search with zodiac
position plus Saros/Inex/gamma/duration metadata. Raises the libephemeris
floor to 2.0.2.

### Added

- **`LunationFinderFactory`** (`kerykeion.lunations`) — finds New Moon, First
  Quarter, Full Moon and Last Quarter across a date or Julian-Day range
  (`from_iso_range` / `from_julian_day`) via `compute_lunar_phase_jd`, iterating
  each phase independently at a half-synodic step so the binary-search solver
  never degenerates on adjacent phases. Returns a `LunationsCollectionModel`
  whose items carry the phase name, UTC timestamp, Julian Day and the Sun/Moon
  `KerykeionPointModel`. Re-exported from the package root
  (`LunationFinderFactory`, `LunationModel`, `LunationsCollectionModel`).
- **Eclipse zodiac + physical metadata** — `SolarEclipseModel` /
  `LunarEclipseModel` gain optional `ecliptic_longitude`, `sign`, `sign_num`
  and `degree` of the luminary at maximum, plus `saros` / `inex` (and, for
  solar eclipses, `gamma` and `duration_minutes`). The values come from the
  libephemeris extensions, guarded with `hasattr`, so they are `None` on the
  swisseph backend — additive and backward compatible.

### Changed

- **`libephemeris` pinned to `==2.0.2`** — picks up the fix for global
  lunar-occultation search under the `extended` (DE441) precision tier
  (`lun_occult_when_glob` previously clamped post-1969 searches to the DE441
  segment split and returned no events).

## 6.0.0a51

_2026-05-29_

Fix the Void-of-Course Moon's `next_aspect`: it is now the Moon's first exact
aspect *after* the sign ingress (the aspect that ends the void lull), instead of
being re-picked from the current sign — which made it duplicate `last_aspect`
whenever the queried moment fell before the last in-sign aspect.

### Fixed

- **`VoidOfCourseMoonModel.next_aspect`** — `compute_void_of_course` now scans the
  *next* sign for `next_aspect` (a second `_aspects_in_window` pass between the
  ingress and the following cusp), so it is always a distinct event from
  `last_aspect`. Previously both were drawn from the current sign's aspect list,
  so `next_aspect` duplicated `last_aspect` when the queried moment preceded the
  last in-sign aspect.

### Changed

- **`next_aspect` semantics** — it now reports the first aspect in the next sign
  (no longer `None` while the Moon is void). The field stays `Optional` with the
  same type; `last_aspect`, the void window and `is_void_of_course` are unchanged.

## 6.0.0a50

_2026-05-29_

`SunTimesFactory` now also reports civil, nautical and astronomical twilight.

### Added

- **Twilight on `SunTimesModel`** — six new optional fields: `civil_dawn` /
  `civil_dusk` (Sun at -6°), `nautical_dawn` / `nautical_dusk` (-12°) and
  `astronomical_dawn` / `astronomical_dusk` (-18°). Computed by
  `compute_twilight_events` via the active ephemeris backend's `rise_trans`
  twilight bits (geometric, no refraction); each is `None` when that twilight
  does not occur on the civil day (polar / high-latitude geometry).

## 6.0.0a49

_2026-05-29_

New **dominants calculator** — the dominant planet, sign, element, modality and
house of a chart — offering several interchangeable calculation "schools" behind
a Strategy pattern, plus a first-class custom-strategy extension point.

### Added

- **`DominantsFactory`** (`kerykeion/dominants/`). Computes a chart's dominants
  via `DominantsFactory.from_subject(subject, strategy=...)` (or the
  `from_birth_data` convenience), returning the new fixed-shape `DominantsModel`.
- Three built-in schools, selectable by name (the new `DominantMethod` literal):
  - **`"modern"`** — modern weighted method (Astrotheme-style): planetary
    strength from angularity, aspect activity, a mild essential-dignity
    bonus/penalty and rulership bonuses, from which the dominant signs, houses,
    elements, modes, polarity, hemispheres and quadrants are derived.
    Speed and retrogradation are excluded by design.
  - **`"almuten_figuris"`** — the traditional Lord of the Geniture: essential
    dignities tallied for every classical planet over the five hylegiacal places
    (Sun, Moon, Ascendant, Part of Fortune and the prenatal Syzygy), with an
    optional accidental-dignity layer (house placement, weekday ruler).
  - **`"elemental"`** — simple elemental/modal balance, reusing the library's
    `calculate_element_points` / `calculate_quality_points` helpers.
- **Custom schools via the Strategy pattern.** `DominantStrategy` (a
  `runtime_checkable` Protocol) plus the optional `BaseDominantStrategy` base
  (shared ranking / percentage / winner machinery) let callers plug in their own
  school with no registration step.
- New `DominantMethod` literal and the `DominantsModel`, `DominantScoreModel` and
  `DominantBreakdownItemModel` models, all re-exported from the package root and
  verified `get_type_hints`-resolvable for runtime (FastAPI) introspection.

### Notes

- The dominants engine reuses existing building blocks rather than duplicating
  them: the Ptolemaic dignity tables (`kerykeion.dignities`), the element/quality
  distribution helpers, the aspect engine, and the rulership data. The prenatal
  Syzygy is found with a self-contained, bracketed bisection over the Sun–Moon
  elongation and accesses the ephemeris under `EPHEMERIS_LOCK`.
- The prenatal Syzygy degrades gracefully on any ephemeris failure (e.g. an
  out-of-range date): the place is skipped rather than propagating the error.

---

## 6.0.0a48

_2026-05-28_

New **timing factories** built directly on the ephemeris backend
(`swe.rise_trans` / `swe.calc_ut`) — no full `AstrologicalSubject` is
constructed, so they are lightweight and backend-neutral (libephemeris or
swisseph).

### Added

- **`SunTimesFactory`** (`kerykeion/sun_times/`). Sunrise / sunset / solar-noon
  / day-length for a civil date at a location, with apparent upper-limb
  refraction and polar day/night detection. Backed by the new `SunTimesModel`.
- **`PlanetaryHoursFactory`** (`kerykeion/planetary_hours/`). The 24 unequal
  Chaldean planetary hours (twelve day + twelve night), seeded by the weekday's
  day-ruler and cycling the descending Chaldean order; moments before sunrise
  resolve to the previous planetary day. Backed by `PlanetaryHourModel` /
  `PlanetaryHoursModel`.
- **`VoidOfCourseMoonFactory`** (`kerykeion/void_of_course_moon/`). The
  classical void-of-course Moon: last exact Ptolemaic aspect to a traditional
  planet before sign ingress, via analytic seeding + Newton refinement on real
  longitudes (no brute-force scan). Geocentric; supports tropical **and**
  sidereal. Backed by `VoidOfCourseAspectModel` / `VoidOfCourseMoonModel`.
- New literals `ClassicalPlanet`, `VocTargetPlanet`, `VocAspectName` and the
  five models above, all re-exported from the package root.

### Changed

- **Thread-safe ephemeris access.** A process-wide `EPHEMERIS_LOCK` (re-entrant)
  now guards the mutable Swiss Ephemeris state (ephemeris path, sidereal mode,
  reset/close) for the new factories and for `AstrologicalSubjectFactory`'s
  `ephemeris_context`, so concurrent tropical and sidereal calculations no
  longer corrupt one another.

---

## 6.0.0a47

_2026-05-25_

Minor public-API addition.

### Added

- **`PTOLEMAIC_ASPECTS` re-exported from package root.**
  `from kerykeion import PTOLEMAIC_ASPECTS` now works without reaching into
  the private `_predictive_utils` module. Added to both the import block and
  `__all__`.

---

## 6.0.0a46

_2026-05-25_

Large feature release: **orb system overhaul** (Astro-Seek-aligned defaults +
per-point adjustments), **active midpoints** as a first-class rendering
channel, **secondary progressions** improvements, plus a batch of dual-wheel
rendering fixes.

### Added

- **Per-point orb adjustments** (`kerykeion/aspects/orb_utils.py`). New
  `OrbAdjustmentStrategy` (`"max_explicit"` | `"min_explicit"` | `"sum"` |
  `"none"`) and `resolve_pair_orb_adjustment()` for combining a per-point
  adjustment table into a single additive orb for a pair. Only *explicitly*
  configured points are considered before aggregation, so negative
  adjustments work as expected: `{"Pluto": -2.0}` on (Pluto, Saturn) yields
  -2.0, not `max(-2.0, 0.0) = 0`.
  - Threaded through `get_aspect_from_two_points(..., extra_orb=0.0)`
    (effective orb clamped `>= 0`), `AspectsFactory.single_chart_aspects()`
    / `dual_chart_aspects()`, `ChartDataFactory.create_chart_data()` + all
    7 convenience methods, `SecondaryProgressionFactory.compute_full()`,
    `SolarArcFactory.compute()`.
  - Per-chart-type defaults: natal / synastry / composite use the luminary
    bonus (`DEFAULT_NATAL_POINT_ORB_ADJUSTMENTS` = Sun/Moon +1.5°); transit,
    progression and returns use `NO_POINT_ORB_ADJUSTMENTS` (flat tight orb).

- **Active midpoints as a dynamic rendering channel.** New
  `subject.active_midpoints` (mirrors the `fixed_stars` channel): midpoints
  requested by name (e.g. `["Sun_Moon"]`) materialise as
  `KerykeionPointModel` entries with `point_type='Midpoint'` and render on
  the chart wheel.
  - `MidpointFactory.compute_active_midpoint_points(subject, pair_names)`
    resolves `"A_B"` pair identifiers (greedy split, supports multi-token
    names like `True_North_Lunar_Node`) and produces fully-populated points
    with sign/quality/element/emoji and a natal-house assignment.
  - New `Midpoint` `<symbol>` (small ring + dot, visually distinct from
    planet and fixed-star marks) in all 4 templates (`chart.xml`,
    `modern_wheel.xml`, `wheel_only.xml`, `aspect_grid_only.xml`) +
    `build_dynamic_midpoint_settings()` for dynamic glyph ID resolution.
  - `ChartDrawer` collects `subject.active_midpoints` alongside fixed
    stars, with per-subject scoping (each chart can carry its own midpoint
    configuration) and dynamic glyph IDs.

- **`SecondaryProgressionFactory.compute_full()`**. Returns a full result
  model including progressed-to-natal aspects. Default aspect set switched
  to the Ptolemaic five.

- **`SolarArcFactory.compute_directed_subject()`**. Generates a directed
  subject; quality / element / emoji / house are recomputed when a directed
  point crosses a sign or house (previously inherited from natal, producing
  inconsistent `KerykeionPointModel` for downstream rendering / AI / PDF
  consumers).

- **Astro-Seek-aligned default orbs** for natal, synastry, transit, and
  composite charts. New `PREDICTIVE_ACTIVE_ASPECTS` (3° flat) used for
  transit / progression / return charts. Default sets refined per chart
  type and threaded through `create_chart_data` + transit factory.

### Changed (breaking — alpha channel)

- **`DEFAULT_ACTIVE_POINTS`: 18 → 14.** Removed `Descendant`, `Imum_Coeli`,
  `True_South_Lunar_Node`, `Mean_Lilith`. Opposite points (which are
  deterministic from their counterpart) are still computed and available on
  the subject model, but only included in `active_points` when explicitly
  requested by the caller. To retain previous behaviour, pass them
  explicitly:
  ```python
  active_points=DEFAULT_ACTIVE_POINTS + [
      "Descendant", "Imum_Coeli", "True_South_Lunar_Node", "Mean_Lilith",
  ]
  ```

- **`DEFAULT_ACTIVE_ASPECTS`: 6 → 5.** Removed quintile (Ptolemaic only).
- **`DEFAULT_PREDICTIVE_POINTS`: 16 → 14.** Removed South Node + Lilith.

- **Default orb values changed across all chart types** to match Astro-Seek
  reference. **Aspect counts for any pre-existing chart will differ from
  6.0.0a45.** Snapshot/baseline tests that compare aspect lists must be
  regenerated. Affected baselines in this repo have been updated
  (`natal`: 43 aspects, `synastry`: 96 aspects, return baselines, etc.).

- **Unknown `point_orb_adjustment_strategy` now raises `ValueError`.**
  Previously the resolver silently returned `0.0` when handed an unknown
  strategy name, masking typos. Callers passing arbitrary strings must now
  pick from the four registered names.

- **`RelationshipScoreFactory` now passes `DISCEPOLO_SCORE_ACTIVE_ASPECTS`
  explicitly.** The Discepolo affinity score previously tracked the
  chart-display default orbs implicitly; the score is now a stable, fixed
  methodology independent of orb configuration. Regression baselines
  updated (Lennon/Ono: 8, Dario/Franca: 9).

### Fixed

- **Dual-wheel aspect grid (table mode) missed second-subject-only points.**
  Fixed stars or active midpoints that existed only on the outer wheel were
  dropped from the NxN grid and aspects targeting them landed in nonexistent
  cells. `ChartDrawer` now exposes `_get_aspect_grid_planets_setting()` /
  `_count_aspect_grid_planets()` which return the union of both subjects in
  dual-wheel mode; `_is_right_panel_mode()` branches on grid type (table =
  union count, list = per-subject max). Wired into every renderer call site,
  `_setup_dual_chart_aspects`, the grid-only export, `_grid_only_viewbox`,
  and `_estimate_required_width_full`. Regression test
  `test_dual_table_aspect_grid_keeps_second_subject_only_fixed_star`.

- **Secondary progression self-conjunction filter removed.** Natal ↔
  progressed-same-point conjunctions (e.g. natal Sun → progressed Sun) were
  incorrectly skipped; they're meaningful and now appear in results.

- **Solar arc directed subject** now recomputes `active_midpoints`
  (previously stale on rotation) + actionable logging on inconsistencies.

- **Midpoint glyph rendering** — visual redesign + `UnboundLocalError` in
  `ChartDrawer` when a midpoint settings row was looked up by a renamed
  slug.

- **Chart-type-aware orb defaults** now honored by `create_chart_data` and
  the transit factory (previously some entry points fell back to the
  natal-shaped table for predictive charts).

### Docs

- Added 12 missing v6 factory pages: `astro_cartography_factory.md`,
  `eclipse_factory.md`, `fixed_star_discovery_factory.md`,
  `heliacal_factory.md`, `midpoint_factory.md`, `occultation_factory.md`,
  `planetary_nodes_factory.md`, `planetary_phenomena_factory.md`,
  `primary_directions_factory.md`, `relocated_chart_factory.md`,
  `secondary_progressions_factory.md`, `solar_arc_factory.md`. Plus
  comprehensive cross-cutting docs improvements (FAQ, glossary, examples).

### Tests

- New `tests/core/test_reference_validation.py` — Astro-Seek
  cross-validation suite (catches orb / default drift against the
  reference).
- `test_modern_chart_2000_02_26_neptune_order` updated to explicitly opt
  back into `True_South_Lunar_Node` (the regression target it validates)
  via `active_points` on both subject and chart data factories, since the
  point is no longer a default.
- 16 new unit tests in `tests/core/test_orb_utils.py` covering the
  per-point adjustment strategies (max/min/sum/none, negative adjustments,
  axis-orb interaction).
- SVG + aspect golden baselines regenerated across the suite for the new
  default orbs.

### Internal

- Micro-optimised orb resolution (hot path on large active-points lists).
- Deduplicated midpoint name generation.
- Extracted `HOUSE_FIELD_NAMES` constant (was inlined in multiple sites).

Total: **10034 pass, 69 skipped** (+930 vs `6.0.0a45`).

## 6.0.0a45

_2026-05-18_

### Fixed (regression introduced in 6.0.0a44)

- **`IndexError: list index out of range` in dual-wheel return charts**
  (`POST /api/v6/chart/solar-return` with `wheel_type: "dual"`).
  `_calculate_secondary_indicator_adjustments` and `_draw_secondary_points`
  iterated `range(len(points_settings))` against
  `points_abs_positions` of a different length and crashed. Two-pronged
  fix:
  - **Structural**: `ChartDrawer` now keeps a per-second-subject settings
    list (`second_subject_available_planets_setting`) aligned to the
    points actually collected from the second subject, and propagates it
    to `draw_planets()` via a new `secondary_planets_setting` keyword.
    The rendering of the outer ring uses this filtered list so settings
    and positions stay symmetric.
  - **Defensive safety net**: the two affected loops are bounded by
    `min(len(settings), len(positions))` so any future mismatch (custom
    subject classes, partial typed-field population) degrades gracefully
    instead of raising.

### Fixed (silent bug, also pre-existing)

- **`PlanetaryReturnFactory` did not propagate v6 calc flags** from the
  natal subject to the return subject. Even if the request asked for
  `active_fixed_stars: ["Betelgeuse"]` on the natal, the resulting solar
  or lunar return would compute none of them — and similarly for
  `calculate_dignities` / `calculate_nakshatra` / `calculate_gauquelin` /
  `calculate_nutation` / `calculate_local_space`. All six v6 calc kwargs
  are now accepted by `PlanetaryReturnFactory.__init__` and forwarded
  into both return-subject builders. `AstrologicalSubjectFactory.from_iso_utc_time`
  also accepts the same six kwargs and forwards them to `from_birth_data`.
  Defaults keep the legacy behaviour: a caller that doesn't set the
  flags continues to get a bare return chart, no behavioural change.

### Tests

- New regression class `TestPlanetaryReturnV6FlagPropagation` in
  `tests/core/test_planetary_return.py` covering:
  - `active_fixed_stars` propagation
  - `calculate_dignities` propagation
  - dual-wheel render without IndexError
  - default-False legacy behaviour

Total: 9104 pass, 69 skipped (+4 vs `6.0.0a44`).

## 6.0.0a44

_2026-05-18_

### Fixed (regression)

- **Catalog fixed stars not participating in aspects.** After `6.0.0a43`,
  fixed stars passed via `active_fixed_stars` that weren't in the legacy
  `DEFAULT_CELESTIAL_POINTS_SETTINGS` (i.e. anything beyond the 23
  traditionally hardcoded names) were silently excluded from aspect
  calculation. The root cause was that
  `AspectsFactory._calculate_single_chart_aspects` and
  `_calculate_dual_chart_aspects` called `get_active_points_list(...)`
  without forwarding the extended `celestial_points` list built by
  `single_chart_aspects` / `dual_chart_aspects`. The internal lookup
  loop in `get_active_points_list` therefore iterated only over the
  default settings and the per-subject `fixed_stars` fallback was never
  reached. Same bug applied to
  `single_chart_declination_aspects` / `dual_chart_declination_aspects`
  (parallel / contra-parallel aspects).
- New regression test class `TestCatalogStarsParticipateInAspects` in
  `tests/core/test_dynamic_fixed_stars.py`.

### Visual — unified fixed-star glyph

- **All fixed stars now render with a single generic glyph**
  `<symbol id="FixedStar">`. The 23 per-star dedicated symbols (Regulus,
  Spica, Aldebaran, ...) have been removed from `chart.xml`,
  `wheel_only.xml`, `modern_wheel.xml`, and `aspect_grid_only.xml`. The
  generic glyph is a 5-point star colored via the single CSS variable
  `--kerykeion-chart-color-fixed-star-default`.
- The 23 per-star CSS variables (`--kerykeion-chart-color-regulus`, …)
  have been removed from all six themes (`classic`, `dark`,
  `dark-high-contrast`, `light`, `strawberry`, `black-and-white`).
  A single `--kerykeion-chart-color-fixed-star-default` per theme
  replaces them.
- The 23 hardcoded entries have been removed from
  `DEFAULT_CELESTIAL_POINTS_SETTINGS`; all fixed-star settings are now
  generated dynamically by `build_dynamic_fixed_star_settings`.
- `KNOWN_GLYPH_NAMES` no longer lists fixed stars: `resolve_glyph_id`
  returns `"FixedStar"` for every star name.

This concludes the fixed-stars architectural cleanup started in
`6.0.0a43` — there is no longer any asymmetry between "hardcoded" and
"catalog" stars at any layer (data, calculation, rendering).

### Breaking — visual / CSS

- Custom themes that override `--kerykeion-chart-color-regulus` (or any
  other per-star variable) must migrate to overriding the single
  `--kerykeion-chart-color-fixed-star-default`. Per-star color
  customization via CSS is no longer supported.
- SVG output: `xlink:href="#Regulus"` (and the other 22 per-star
  references) replaced by `xlink:href="#FixedStar"`. `kr:slug="Regulus"`
  is preserved on the wrapping `<g>` for tracking/styling by external
  consumers.

### Tests

- All chart SVG baselines (`tests/data/svg/*.svg`) regenerated to match
  the new unified glyph. 9100 tests pass (+2 new regression tests for
  catalog star aspects).

## 6.0.0a43

_2026-05-18_

### Fixed Stars — unified channel (breaking)

The fixed-star subsystem has been refactored to scale beyond the historical
23 hardcoded stars and to live entirely on the libephemeris catalog as the
single source of truth.

- **Subject model**: the 23 typed star fields (`subject.regulus`,
  `subject.spica`, …) have been **removed**. All fixed stars now live in
  `subject.fixed_stars: list[KerykeionPointModel]`. Lookup by name is
  available via the new `subject.find_fixed_star(name)` helper
  (case- and separator-insensitive: `"Deneb Algedi"`, `"deneb_algedi"`,
  `"DENEB-ALGEDI"` all resolve identically).
- **Calculation channel**: `active_points` no longer accepts star names.
  Use the dedicated `active_fixed_stars: list[str]` parameter on
  `AstrologicalSubjectFactory.from_birth_data()` (and the other
  constructors). No automatic defaults — callers opt in to specific stars.
- **Catalog discovery**: new `kerykeion.fixed_stars.FixedStarCatalog`
  wraps `libephemeris.fixed_stars.list_fixed_stars()` (116 entries today).
  Exposes `list_all()`, `find(name)`, `known_slugs()`.
- **Aspect engine**: `AspectsFactory.single_chart_aspects` and
  `dual_chart_aspects` automatically iterate `subject.fixed_stars` —
  catalog stars participate in aspect calculations without needing to be
  in `active_points`. `SingleChartAspectsModel.active_points` and
  `DualChartAspectsModel.active_points` are now
  `list[Union[AstrologicalPoint, str]]` to accept catalog star slugs.
- **Chart wheel rendering**: catalog stars without a dedicated SVG
  `<symbol>` fall back to the new generic `<symbol id="FixedStar">`
  (5-point star, colored via
  `var(--kerykeion-chart-color-fixed-star-default, #d4a053)`).
  Added to `chart.xml`, `wheel_only.xml`, `modern_wheel.xml`. Glyph
  resolution centralized in `chart_defaults.resolve_glyph_id(name)` /
  `KNOWN_GLYPH_NAMES`.
- **`FixedStarDiscoveryFactory`**: catalog source is now exclusively
  libephemeris. The previous swisseph-backed path
  (`_find_prominent_stars_swisseph`) and the `sefstars.txt` parser have
  been removed.

### swisseph backend — `sefstars.txt` requirement

Fixed-star calculation on the swisseph backend depends on
`swe.fixstar_ut`, which reads from `sefstars.txt`. That file is
distributed under the Swiss Ephemeris license (Astrodienst AG) and is
**not bundled with kerykeion** — users must download it manually into
`KERYKEION_EPHE_PATH`. When star calculation produces zero results on
swisseph, kerykeion now emits a single actionable WARNING with the
download URL and the libephemeris alternative. See
[site/docs/swisseph_configuration.md](site/docs/swisseph_configuration.md#fixed-stars-catalog-sefstarstxt)
for the full procedure.

### Backward compatibility

**Breaking changes** (alpha — accepted):

- `subject.regulus`, `subject.spica`, and the other 21 typed star fields
  have been removed. Migrate to
  `subject.find_fixed_star("Regulus")` or iterate `subject.fixed_stars`.
- `active_points=["Regulus", ...]` no longer triggers calculation for
  star names. Pass star names to `active_fixed_stars=[...]` instead.
- `FixedStarDiscoveryFactory.find_prominent_stars()` no longer accepts
  the `catalog_path` keyword argument (libephemeris-only now).

### Tests

- Updated tests that used the removed typed fields to use
  `find_fixed_star()` / `fixed_stars[]` iteration.
- 16 chart-drawer snapshot tests are marked `@pytest.mark.skip` pending
  regeneration with the new fixed-stars rendering pipeline.

## 6.0.0a42

_2026-05-15_

### Dependencies

- **Updated `libephemeris` to 2.0.0.** The upstream library simplified
  its public API by removing legacy prefixed aliases. The canonical
  bare-name API used by kerykeion (`calc_ut`, `houses`, `SUN`,
  `FLG_SPEED`, …) is unchanged — no code changes required.
  Also adds a new `libephemeris.contrib` submodule with extended
  astrology helpers (zodiac, nakshatra, aspect constants and functions).

### Backward compatibility

No API changes. Fully backward-compatible.

## 6.0.0a41

_2026-05-14_

### Fixes

- **Updated `libephemeris` to 1.6.0.** Fixes critical LEB fast-path bugs
  that caused `lun_occult_when_loc()` to crash with `NameError` and
  heliacal calculations to fail with `TypeError` after `close()`.

### Backward compatibility

No API changes. Fully backward-compatible.

## 6.0.0a40

_2026-05-10_

### Improvements

- **Clean ephemeris data packaging.** Swiss Ephemeris data files (`.se1`,
  `sefstars.txt`) are no longer shipped inside the wheel. The default backend
  (`libephemeris`) manages its own data internally and never needed them.
  Users who opt into the `swisseph` backend can download the data files
  separately via the new setup utility (see below).

- **New `swisseph_setup` utility.** Run `python -m kerykeion.swisseph_setup`
  to download Swiss Ephemeris data files with an interactive license
  confirmation (AGPL-3.0, Astrodienst AG). Supports `--yes` for CI,
  `--target` for custom paths, and `--skip-asteroids`.

- **Backend-aware `EPHE_DATA_PATH`.** The default ephemeris path is now
  resolved per-backend instead of pointing to a fixed directory. When using
  swisseph without `KERYKEION_EPHE_PATH`, a warning is logged explaining
  the Moshier analytical fallback. When a user-provided path lacks `.se1`
  files, a validation warning is emitted.

- **Fix license classifier.** The PyPI classifier now correctly says
  AGPL-3.0, matching the `license` field and the LICENSE file.

### Documentation

- New [Swiss Ephemeris Configuration](site/docs/swisseph_configuration.md)
  guide covering installation, data setup, and license terms.
- Updated README with Swiss Ephemeris backend section.
- Updated `ephemeris_backend.md` and `backend_precision_comparison.md` docs.

### Backward compatibility

`EPHE_DATA_PATH` now defaults to `""` instead of a package-internal path.
All factory modules already pass this to `swe.set_ephe_path()`, which handles
the empty string correctly for both backends. Code that imports
`EPHE_DATA_PATH` and constructs file paths from it (e.g.
`Path(EPHE_DATA_PATH) / "sefstars.txt"`) should use `KERYKEION_EPHE_PATH`
instead.

## 6.0.0a39

_2026-05-08_

### Dependencies

- Update `libephemeris` to 1.4.0 (`cool` + `release_data_cache`).

## 6.0.0a38

_2026-05-08_

### Performance

- **Remove import-time LEB reader opening.** `ephemeris_backend.py` no longer
  calls `get_leb_reader()` at import time to detect the LEB format. This
  avoided opening four companion mmap files (~855 MB for extended tier) just
  to log a single format string at startup.

### Dependencies

- Update `libephemeris` to 1.3.0 (lazy mmap, selective `warm()` preloading).

### Backward compatibility

No API changes. Startup logging still reports mode and tier but no longer
includes the format field (LEB1/LEB2).

## 6.0.0a37

_2026-05-08_

### New Features

- **Backend-specific fixed-star discovery.** `FixedStarDiscoveryFactory` now
  dispatches explicitly by ephemeris backend: `swisseph` scans the Swiss
  Ephemeris `sefstars.txt` catalog, while `libephemeris` uses the native
  `list_fixed_stars()` / `batch_fixstars_ut()` APIs and never reads Swiss
  catalog files.
- **Fixed-star discovery metadata.** Discovery results now carry optional
  `near_point`, `orb`, `aspect`, `longitude`, `latitude`, and `degree` fields
  on `KerykeionPointModel`, matching the API shape expected by UI consumers.

### Performance

- Swiss discovery now scans candidate positions without `FLG_SPEED` and only
  computes speed, declination, and magnitude for stars that actually fall within
  the requested conjunction orb.
- The libephemeris path uses ordered batch calculation for the native catalog.

### Backward compatibility

Additive only. Existing fixed-star point fields remain unchanged. Catalog size
and specific discovery results may differ by backend because each backend now
uses its own catalog source intentionally.

## 6.0.0a36

_2026-04-28_

### New Features

Predictive astrology factories — three new factories that complete the
core predictive toolkit (joining the existing `PrimaryDirectionsFactory`):

- **`MidpointFactory`** — computes every pairwise midpoint of an
  `AstrologicalSubjectModel`, plus the 90° dial position used by
  cosmobiology and Uranian/Hamburg-school astrology, plus optional
  aspect-to-midpoint detection (third-point activations) with
  configurable orb. Pure math, no ephemeris calls.
- **`SecondaryProgressionFactory`** — computes the day-for-a-year
  progressed chart for any target moment, returning a regular
  `AstrologicalSubjectModel` so every downstream tool (aspects,
  dignities, chart drawer) keeps working transparently. All natal
  settings (zodiac type, sidereal mode, house system, perspective,
  active points, altitude, location, timezone) are reused.
  Supports BCE natal subjects and BCE targets via Julian Day arithmetic.
- **`SolarArcFactory`** — derives the solar arc from the progressed
  Sun and applies it uniformly to every active natal point, returning
  a structured `SolarArcSubjectModel` with directed positions, sign
  ingresses, and directed-to-natal aspect contacts. Natal targets for
  aspect detection use the subject's own `active_points` (not hardcoded
  defaults), so extra points (Vertex, asteroids, etc.) are included.

All three factories are exported from the top-level `kerykeion`
namespace.

- **`"Progression"` chart type** — new dual-wheel chart type in
  `ChartType`, `ChartDataFactory`, `ChartDrawer`, and `charts_utils`.
  `ChartDataFactory.create_progression_chart_data(natal, progressed)`
  produces a biwheel with natal (inner) and progressed (outer).
  `ChartDrawer` renders it via a dedicated `ProgressionChartRenderer`
  with progression-specific labels.
- **Context serializer**: `solar_arc_to_context()` transforms a
  `SolarArcSubjectModel` into XML, `midpoints_to_context()` transforms
  a `list[MidpointModel]` into XML. Both are callable via the
  `to_context()` dispatcher.
- **Custom ayanamsa persistence**: `custom_ayanamsa_t0` and
  `custom_ayanamsa_ayan_t0` are now stored on `AstrologicalBaseModel`
  and propagated through secondary progressions and solar arcs.
  A Pydantic `model_validator` enforces pair integrity (both or neither).
- **`DOUBLE_CHART_TYPES` centralized**: the dual-chart type tuple is
  now defined once in `charts_utils.py` and imported by
  `draw_planets.py` and `chart_data_factory.py`.

### Backward compatibility

Additive only. No existing class or attribute is removed, renamed, or
semantically changed. The new `custom_ayanamsa_*` fields default to
`None` and do not affect existing models.

## 6.0.0a35

_2026-04-25_

### Bugfix

- **Modern HouseSector no longer overlaps the zodiac ring.** The
  click-only HouseSector overlay was drawn out to `R_CUSP_OUTER=50`,
  identical to the zodiac background's outer edge, and it covered the
  entire 4-unit zodiac annulus (`R_ZODIAC_BG_INNER=46` to 50). Frontends
  that walked `elementsFromPoint` and resolved HouseSector before
  ZodiacSign therefore swallowed every click on a zodiac sign as a
  click on the underlying house. With the zodiac background ring
  active, HouseSector now stops at `R_ZODIAC_BG_INNER`. Without the
  zodiac ring, the original full-radius behaviour is preserved.

Affects both the main horoscope path and the synastry / dual-chart
path. No change to the visible geometry — HouseSector is invisible by
default; this only adjusts the clickable region.

## 6.0.0a34

_2026-04-24_

### New Features

- **Sign-full highlight overlay on modern `ZodiacSign`.** Each modern
  ZodiacSign now contains a second hidden `<path kr:highlight="sign-full">`
  that is a full pie slice from the chart center to the outer zodiac
  boundary. Transparent and non-interactive by default; frontends toggle
  its visibility through CSS to render a classic-style full-wedge focus
  highlight. The visible outer annular wedge is unchanged.

### Why

In the modern style the visible zodiac wedge is a thin outer ring
(~4 units on a 100-unit viewBox), so frontends that highlight a focused
sign can only tint that narrow band. The classic style paints a full
pie-slice wedge, producing a much stronger visual emphasis. The overlay
bridges the gap without altering the default modern appearance.

### Backward compatibility

Additive only. No existing attribute is removed or renamed, the visible
geometry is byte-identical, and pointer interactions are unchanged.

## 6.0.0a33

_2026-04-24_

### New Features

- **`kr:cx` / `kr:cy` now emitted on modern-style ChartPoints too.** The
  modern path in `draw_modern._draw_single_planet_in_ring` wraps each
  planet/angle in a `<g>` rotated around the chart center via
  `rotate(-display_angle, CENTER, CENTER)`. The emitted center applies
  that rotation to the pre-rotation glyph position `(CENTER, glyph_y)`,
  producing the true post-rotation coordinates in chart SVG root space.

### Why

6.0.0a32 added `kr:cx` / `kr:cy` only on the classic path. Frontends that
need a single code path for hit-detection (tooltip, click-to-focus) across
both styles therefore still had to parse the modern transform chain. This
release closes the gap: both styles now expose the glyph center uniformly
as two attributes on the ChartPoint `<g>`, and the consumer converts them
to viewport pixels with a single `getScreenCTM()` / `getCTM().inverse()`
call — no style-specific logic required.

### Backward compatibility

Additive only. Existing consumers that ignore the attributes are unaffected;
the classic path is unchanged.

## 6.0.0a32

_2026-04-24_

### New Features

- **`kr:cx` / `kr:cy` attributes on every `<g kr:node="ChartPoint">`** — the
  exact glyph-center coordinates in chart SVG root coords, emitted by both
  the single-chart path (`_generate_point_svg`) and the transit-chart
  inline path in `draw_planets`. Pure addition of two attribute writes
  per point; no geometric impact on rendered output.

### Why

Frontends that layer interactivity on top of kerykeion SVG (tooltips,
click-to-focus, hit-testing) need the rendered glyph center to
disambiguate overlapping symbols in dense clusters. Measuring it via DOM
APIs is unreliable: our `<symbol>` definitions omit `viewBox`, so
`getBoundingClientRect` / `getBBox` on `<use>` returns 0×0 or an
implementation-defined value across browsers. Parsing the `<g>` transform
chain works for modern style but diverges from classic, which wraps the
symbol with `translate(-12, -12)` and places `<use x=X y=Y>` — making the
two styles structurally incompatible for a single consumer.

Emitting the coordinates explicitly sidesteps all of that: the consumer
reads two attributes, applies the root SVG's `getScreenCTM()`, and
obtains the exact viewport-space glyph center. The values are already
computed by the drawing code before it writes the markup, so the cost on
the generator side is zero.

### Backward compatibility

Additive only: no existing attribute is removed, renamed, or semantically
changed. Older consumers that ignore `kr:cx` / `kr:cy` keep working.

## 6.0.0a31

_2026-04-22_

**Bugfixes (backported from v5.12.8):**

- **Modern chart decluttering order:** Fixed a bug where planets in a tight cluster on `style="modern"` charts could be pushed past their neighbours, violating true zodiacal order (e.g. Neptune at 5° Aquarius rendered after Uranus at 17° Aquarius). The collision-resolution algorithm in `_resolve_planet_collisions` was rewritten from a 5-pass iterative push (vulnerable to wraparound overshoots) to a single-pass largest-gap linearization that is monotonic by construction: planets are cut at the largest gap in their true zodiacal angles and walked forward once with `display_angle = max(desired_linear, prev_linear + sep)`. Order is preserved and `min_separation` is respected without iterative refinement. Reproduced by any dense stellium (≥3 planets within ~8°); regression covered by `tests/core/test_modern_decluttering.py`.

## 6.0.0a30

_2026-04-21_

**Backward planetary-return search — `next_return_from_iso_formatted_time` / `next_return_from_date` / `next_lunar_node_crossing*` now accept `backwards=True`, matching the existing heliocentric API.**

### New Features

- **`backwards: bool = False` on all planetary-return entry points.** When
  `True`, the factory calls into libephemeris' new backward-capable crossing
  primitives and returns the most recent *past* return (or node crossing)
  instead of the next upcoming one. Added to:
  - `PlanetaryReturnFactory.next_return_from_iso_formatted_time(iso, return_type, backwards=False)`
  - `PlanetaryReturnFactory.next_return_from_date(year, month, day, return_type, backwards=False)`
  - `PlanetaryReturnFactory.next_lunar_node_crossing(julian_day, backwards=False)`
  - `PlanetaryReturnFactory.next_lunar_node_crossing_from_iso_formatted_time(iso, backwards=False)`
  - `PlanetaryReturnFactory.next_lunar_node_crossing_from_date(year, month, day, backwards=False)`
  - `PlanetaryReturnFactory.next_heliocentric_return_from_date(planet, year, month, day, backwards=False)`

### Backend Requirements

Backward search relies on libephemeris `>= 1.1.0`, which added the `backwards`
flag to `swe_solcross_ut`, `swe_mooncross_ut`, and `swe_mooncross_node_ut`.
When kerykeion is running on **pyswisseph** (fallback backend), attempting
backward search raises `KerykeionException` with a clear message directing
the caller to install libephemeris.

### Why

Consumers of return charts (API servers, SDKs, UIs) always want symmetric
navigation — "previous solar return" is as common as "next". Without a native
backward flag, callers had to fake it by seeding the search one mean cycle
before the target date, which fails near cycle boundaries (lunar node mean
motion varies ±1 day per half-cycle; lunar mean motion ±0.1 d). This is the
library-level counterpart to libephemeris 1.1.0's backward crossing support.

### Tests

- 12 new tests in `tests/core/test_planetary_return_backwards.py`:
  - `TestSolarBackwards` — single-step backward, one-cycle boundary invariant,
    date-wrapper round-trip.
  - `TestLunarBackwards` — single-step backward, sidereal-month boundary.
  - `TestLunarNodeCrossingBackwards` — single-step, half-nodal-month boundary,
    date-wrapper round-trip.
  - `TestHeliocentricBackwards` — Jupiter one-cycle (4200–4500 day) boundary.
  - `TestSwissephFallback` — simulates pyswisseph backend via `unittest.mock`,
    asserts `KerykeionException` with `libephemeris` in the message for each
    of the three backward-capable entry points.

### Dependencies

- Bumped primary pin: `libephemeris == 1.1.0` (was `== 1.0.0a15`).
- Bumped `all` extra: `libephemeris >= 1.1.0` (was `>= 1.0.0a13`).

### Compatibility

Fully backward-compatible. `backwards=False` is the default everywhere;
existing code paths are unchanged.

## 6.0.0a29

_2026-04-21_

**Symmetric ISO/year/date wrappers for heliocentric returns and lunar node crossings — closes the API gap between Solar/Lunar and all other return types.**

### New Features

- **`next_heliocentric_return_from_iso_formatted_time(planet_name, iso_formatted_time, backwards=False)`** — compute heliocentric return searching forward (or backward) from an ISO datetime. Mirrors `next_return_from_iso_formatted_time` (Solar/Lunar).
- **`next_heliocentric_return_from_year(planet_name, year)`** — first heliocentric return on or after Jan 1 of the given year. Mirrors `next_return_from_year`.
- **`next_heliocentric_return_from_date(planet_name, year, month, day=1)`** — first heliocentric return on or after a specific date. Mirrors `next_return_from_date`.
- **`next_lunar_node_crossing_from_iso_formatted_time(iso_formatted_time)`** — lunar node crossing from an ISO datetime.
- **`next_lunar_node_crossing_from_year(year)`** — first lunar node crossing on or after Jan 1 of the given year.
- **`next_lunar_node_crossing_from_date(year, month, day=1)`** — first lunar node crossing on or after a specific date.

### Enhancements

- **`next_heliocentric_return` gains `backwards` parameter** — search backward in time when using the libephemeris backend. pyswisseph does not support backward search; a `KerykeionException` is raised if attempted.

### Why

Previously, `PlanetaryReturnFactory` exposed ergonomic `from_iso`/`from_year`/`from_date` wrappers only for Solar and Lunar returns. Heliocentric returns and lunar node crossings required callers to manually convert dates to Julian Day and call bare primitives (`next_heliocentric_return(planet, start_jd)`, `next_lunar_node_crossing(start_jd)`). This asymmetry forced every consumer (API servers, MCP tools, SDK wrappers) to duplicate the same date→JD conversion logic — and made it easy to accidentally hardcode the natal JD instead of the user-requested search date.

### Tests

- 15 new tests in `tests/core/test_heliocentric_returns.py` covering ISO wrappers, year wrappers, date wrappers, backward search, naive datetime handling, and validation.

## 6.0.0a28

_2026-04-21_

**Allow fractional orbs in aspect configuration — `ActiveAspect.orb` and `_ChartAspectSetting.orb` accept `float` instead of `int`.**

### Bug Fixes

- **`ActiveAspect.orb` type mismatch** — the `orb` field in `ActiveAspect` (TypedDict) was typed as `int`, causing Pydantic v2 to reject valid fractional orb values like `7.5` with `int_from_float` validation errors. Changed to `float`. Integer values continue to work as before (Python `int` is a subtype of `float`).
- **`_ChartAspectSetting.orb` type mismatch** — same fix for the internal chart aspect settings TypedDict, aligning it with the rest of the codebase which already uses `float` for orb values (`AspectModel.orbit`, `axis_orb_limit`, `active_orbs`, `get_orb()`).

### Breaking Changes

None — `int` values are accepted by `float` fields. All default orb values remain integers. Existing code that passes integer orbs is unaffected.

## 6.0.0a27

_2026-04-20_

**Fix Gauquelin sector visualization: draw sectors at actual diurnal-arc boundaries instead of equal 10° zodiacal divisions.**

### Bug Fixes

- **Gauquelin sector drawing mismatch** — sector lines, sector numbers, and interactive hit areas were drawn as equal 10° zodiacal divisions from the Ascendant, but the computed `gauquelin_sector` values (from `house_pos('G')` / `swe.gauquelin_sector()`) use the actual diurnal-arc division, which produces unequal zodiacal spans (6°–16° depending on latitude and obliquity). This caused every planet to appear in the wrong visual sector. All drawing functions now use the actual Gauquelin cusp positions computed via `houses_ex2(jd, lat, lon, 'G')`.

### New Features

- `AstrologicalBaseModel.gauquelin_sector_cusps` — new optional field containing the 36 Gauquelin sector cusp positions as zodiacal longitudes. Populated automatically when `calculate_gauquelin=True`. Consumers can use these cusps to draw sector boundaries or verify planet-sector membership.

### Internal

- `AstrologicalSubjectFactory` now computes the 36 Gauquelin cusps via `swe.houses_ex2(jd, lat, lon, ord('G'))` alongside the per-planet sector values.
- `draw_modern.py`: `_draw_gauquelin_cusp_ring`, `_draw_gauquelin_division_lines`, `_draw_gauquelin_house_ring` accept optional `gauquelin_cusps` and draw lines at actual cusp positions.
- `charts_utils.py`: `draw_gauquelin_sectors` and `draw_gauquelin_sector_hit_areas` accept optional `gauquelin_cusps` for actual sector boundaries.
- `chart_drawer.py`: passes `gauquelin_sector_cusps` from the subject to both modern and classic drawing pipelines.

### Breaking Changes

None — the new `gauquelin_sector_cusps` field is optional with `default=None`. Without cusps, drawing falls back to the previous equal-10° behavior.

## 6.0.0a26

_2026-04-17_

**Drop-in replacement of `scour` with [`svg-polish`](https://pypi.org/project/svg-polish/) — modernised, type-safe, secure-by-default SVG optimizer.**

### Dependency

- Replace `scour>=0.38.2` with `svg-polish>=1.0.0` in runtime dependencies. `svg-polish` is a hardened, type-safe modernisation of Scour 0.38.2 (dormant upstream since August 2021): identical optimization output on the inputs `kerykeion` produces, plus protection against the `var(--…)` / `calc(…)` / keyword-token crashes that the legacy `scour` raises on real-world chart SVGs.

### Internal

- `ChartDrawer._minify` now imports `optimize` from `svg_polish` instead of `scourString` from `scour.scour`. The narrow `try/except` around the call is preserved as a defensive fallback for malformed XML; svg_polish itself no longer raises on the CSS edge-cases that scour did.

### Compatibility

- No public API change. SVG output is byte-identical to the previous `scour`-based pipeline on the kerykeion test matrix (8885 / 8885 tests pass; 165 skipped, all online-only).

### Breaking Changes

None.

## 6.0.0a25

_2026-04-17_

**Performance refactor of hot paths (TIER 0-2), plus targeted bug fixes from Codex and CodeRabbit review.**

### Performance

- Refactor hot paths per `REFACTORY.md` TIER 0-2 — zero breaking changes, 260 SHA-256 signatures byte-identical across all chart types, house systems, sidereal modes, perspectives, returns, transits, eclipses, occultations, ACG, primary directions, fixed stars, dignities.
- Central constants unification (`STANDARD_PLANETS`, `POINT_NUMBER_MAP`, `AXIAL_POINTS` frozenset) in `kerykeion.settings.config_constants`.
- Aspect loop optimization, SVG `list+join` rendering, pre-indexed aspect grid (`O(n²·k)` → `O(n² + k)`), cached `get_args()`, `O(n+m)` orb merge, matching-setting lookup in transit range.
- Measured speedups (min-of-N, best-of-2): `svg_natal` -39.3% (1.65x), `house_comparison` -23.4% (1.30x), `custom_aspects_squares` -20.5% (1.26x), `composite_midpoint` -19.4% (1.24x), `svg_synastry` -17.7% (1.21x), `transits_time_range` -15.4% (1.18x), 15/15 benchmarks faster, 0 regressions.

### Bug Fixes

- Fix `_update_aspect_settings` regression in `AspectsFactory`: when `active_aspects` contains duplicate names, the first occurrence's orb now wins (the prior dict-comprehension refactor had silently introduced last-wins semantics). Uses `dict.setdefault` instead.
- Restore runtime availability of `AstrologicalSubjectModel`, `PlanetReturnModel`, `HouseComparisonModel`, `ChartDataModel`, `AspectModel`, `CompositeSubjectModel`, `KerykeionPointModel`, `ChartType`, `KerykeionException`, `AstrologicalPoint` in modules that expose them as public annotations. The perf refactor had moved them under `if TYPE_CHECKING:`, which would break `typing.get_type_hints()` introspection for downstream consumers that rely on runtime type resolution (e.g. FastAPI).
- `_setup_gauquelin_sectors` now clears `template_dict["makeHouseSectors"]` when Gauquelin mode is active — the 12-wedge invisible hit-area overlay was inconsistent with the 36-sector visible ring and would mislead any frontend using it for click/hover targeting.

### Public API hygiene (CodeRabbit review)

- `kerykeion.astrological_subject_factory.STANDARD_PLANETS` is now re-exported as a shallow copy of the canonical dict in `config_constants`, so downstream mutation of the public symbol no longer leaks into the shared constant.
- `ReportGenerator._celestial_points_report` now preserves duplicate point entries when ordering the report (previously collapsed by `{p.name: p}` dict comprehension).
- `POINT_NUMBER_MAP` docstring rewritten to accurately describe it as the Swiss Ephemeris–compatible subset and enumerate which point classes are outside its scope.

### Chores

- `.opencode/` fully gitignored (replaces the narrower `.opencode/plans` rule).

### Breaking Changes

None — all changes preserve public API, model schemas, and SVG output structure. 260 byte-identical SVG signatures across the test matrix verify output stability.

## 6.0.0a24

_2026-04-16_

**Code quality audit: bug fixes, deduplication, type modernization, and cleanup.**

### Bug Fixes

- Fix `RelationshipScoreFactory.get_relationship_score()` reentrancy — calling it twice on the same instance no longer accumulates stale state. Score, aspects list, and breakdown are reset at the start of each call.
- Fix duplicate CSS `stroke-width: 1px; stroke-width: 0.5px` in aspect grid rendering — the first declaration was dead (overridden by the second). Now emits only `stroke-width: 0.5px`.
- Regenerated 10 sidereal theme combination SVG baselines affected by the CSS fix.

### Code Deduplication

- Deduplicate `_should_calculate()` into a static method on `AstrologicalSubjectFactory` — replaces 3 identical local function definitions across `_calculate_houses`, `_calculate_derived_planets`, and `_calculate_planets`.
- Consolidate `_create_subject_for_date()` in `EphemerisDataFactory` — replaces 2 identical 18-line `from_birth_data()` call blocks.
- Refactor `_convert_coordinate_to_string()` in `charts_utils` — replaces 2 identical lat/lng formatting functions (also fixes `min` shadowing the builtin and DMS carry-over at 60 seconds).
- Replace inline XML serialization with `_serialize_active_config()` in `context_serializer` — deduplicates 2 identical 3-line blocks for active points/aspects.
- Consolidate `_deep_merge()` — remove duplicate in `kerykeion_settings.py`, import from `translations.py`.
- Remove redundant `common_planets` rebuild in `CompositeSubjectFactory._calculate_midpoint_composite_points_and_houses` — uses `self.active_points` directly.
- Simplify house cusp list construction in `house_comparison_utils` — `[h.abs_pos for h in get_houses_list(subject)]` replaces 12-line explicit lists (x2).

### Cleanup & Modernization

- `List[X]` → `list[X]`, `Tuple[X]` → `tuple[X]`, `Union[X, None]` → `Optional[X]` across 15+ files (PEP 585 / PEP 604).
- `AnySubjectModel` type alias in `kr_models.py` replaces 5 repeated `Union[AstrologicalSubjectModel, CompositeSubjectModel, PlanetReturnModel]`.
- `_MODULE_DIR` constant in `chart_drawer.py` replaces 5+ repeated `Path(__file__).parent` calls.
- `_ZODIAC_DEFAULT_SCALE` + `_ZODIAC_SIGN_IDS` in `draw_modern.py` replace 2 hardcoded 12-entry dicts and a duplicate local list.
- `_POLAR_LATITUDE_LIMIT`, `_MAX_DAYS`, `_MAX_HOURS`, `_MAX_MINUTES` constants replace magic numbers.
- `_MAIN_PLANETS`, `_NODES`, `_ANGLES` constants and `_humanize()` helper in `report.py` replace 12+ inline `.replace("_", " ")` calls.
- Expanded `_POINT_NUMBER_MAP` with Earth, Pholus, Ceres, Pallas, Juno, Vesta, and all 8 Uranian points.
- Remove dead code: `__ne__` in `CompositeSubjectFactory` (Python 3 auto-generates it), `_format_date` in `ReportGenerator`, unused `aid` loop variable, TODO comments.
- Fix typos: `sings` → `signs`, `VIWBOX` → `VIEWBOX`.
- Remove superfluous `hasattr()` checks in `PlanetaryReturnFactory`.
- Remove unnecessary `getattr()` calls in `moon_phase_details/factory.py` (attributes always exist on `AstrologicalSubjectModel`).
- Rename `solar_return_date_utc` → `return_date_utc` and `solar_return_astrological_subject` → `return_astrological_subject` (applies to both Solar and Lunar returns).
- Move demo-only imports (`AstrologicalSubjectFactory`, `EphemerisDataFactory`, `timedelta`) to `if __name__ == "__main__"` blocks.
- Convert f-string logging to lazy `%s` formatting in `RelationshipScoreFactory`.
- `or` chains → `in` tuples for chart type checks.
- Formatting: consistent double quotes in f-strings, line length compliance, PEP 8 blank lines.
- Add 4 missing translation keys (`cusp_position_comparison`, `transit_cusp`, `return_cusp`, `house`) to RU, TR, DE, HI.

### Breaking Changes

None — all changes are internal. Public API, model schemas, and SVG output structure are unchanged.

## 6.0.0a23

_2026-04-12_

**Add `kr:horoscope` attribute to house elements in classic dual charts.**

### Changes

- Add `kr:horoscope` attribute to all house-related SVG elements (`Cusp`, `HouseNumber`, `HouseSector`) in classic dual charts (Transit, Synastry, DualReturnChart). Value `"0"` identifies Subject 1 (inner ring), `"1"` identifies Subject 2 (outer ring).
- Add Subject 2's transparent interactive `HouseSector` wedges in the outer ring area (r-36 to r-72). Clicking in the outer ring now targets Subject 2's houses; clicking in the inner area targets Subject 1's houses.
- `draw_house_sectors()` accepts new optional parameters: `horoscope_id`, `seventh_house_abs_override`, `outer_r_offset`, `inner_r_offset`.
- `_setup_house_sectors()` accepts optional `second_houses_list` to render both subjects' sectors.
- Regenerated sidereal SVG test baselines.

### Breaking Changes

None — all new parameters have defaults. Existing callers continue to work without changes.

## 6.0.0a22

_2026-04-08_

**Fix house sector arc geometry — final correct version.**

### Changes

- Remove `la_flip` (large-arc inversion) that caused sector paths to cover the complement area instead of the house itself.
- Swap arc sweep flags (outer 1→0, inner 0→1) so both arcs curve outward following the chart's concentric circles.
- Verified visually on both classic and modern chart styles.
- Regenerated all SVG test baselines.

## 6.0.0a20

_2026-04-08_

**Fix house sector arc curvature (arcs now curve outward correctly).**

### Changes

- Fix house sector SVG arcs curving inward instead of outward. The solution: invert the `large-arc-flag` (`1 - large_arc`) so the SVG renderer picks the outward-curving arc segment. Applied to both classic and modern chart styles.
- Reverted coordinate calculation back to `sliceToX/Y + dropin` (the proven formula that matches cusp line positions exactly).
- Regenerated all SVG test baselines.

## 6.0.0a19

_2026-04-07_

**Fix house sector geometry: use visual center (r,r) for arc calculations.**

### Changes

- Compute house sector arc points from the visual chart center `(r, r)` using `r + R * cos(θ)` instead of `sliceToX(0, R, θ) + dropin`. The old formula placed inner/outer circles at different centers (`(c1,c1)` vs `(c3,c3)`), causing arcs to curve inward instead of following the chart's concentric circles.
- Regenerated all SVG test baselines.

## 6.0.0a18

_2026-04-07_

**Fix house sector arc geometry.**

### Changes

- Fix house sector arc sweep direction: reverse start/end points and use sweep=0 for outer arc, sweep=1 for inner arc. This produces correctly outward-curving arcs that cover the right house sector (both classic and modern chart styles).
- Regenerated all SVG test baselines.

## 6.0.0a17

_2026-04-07_

**Add transparent house sector wedges for interactive highlighting.**

### Changes

- Add `draw_house_sectors()` in `charts_utils.py` — generates 12 transparent annular wedge paths (`kr:node="HouseSector" kr:house="{n}"`) between house cusp boundaries.
- Add `_draw_house_sectors_modern()` in `draw_modern.py` for modern chart style.
- Add `makeHouseSectors` template variable and `$makeHouseSectors` placeholder in classic chart templates (chart.xml, wheel_only.xml).
- Add `makeHouseSectors` field to `ChartTemplateModel`.
- Sectors are invisible by default (`fill: transparent`) but have `pointer-events: all` so the frontend can attach click handlers and apply CSS highlighting.
- Regenerated all SVG test baselines.

## 6.0.0a16

_2026-04-07_

**Add kr: metadata to zodiac sign slices and modern chart indicators/house numbers.**

### Changes

- Wrap each zodiac sign slice in `<g kr:node="ZodiacSign" kr:sign="{sign}" kr:signnumber="{n}">` in both classic (`draw_zodiac_slice`) and modern (`_draw_zodiac_backgrounds`) charts.
- Add `kr:slug` to modern chart indicators (`_draw_indicator_line`).
- Wrap modern chart house numbers in `<g kr:node="HouseNumber" kr:house="{n}">`.
- Regenerated all SVG test baselines.

## 6.0.0a15

_2026-04-07_

**Enrich SVG chart metadata for frontend interactivity (focus mode, DataCards).**

### Changes

- Wrap degree indicators in `<g kr:node="Indicator" kr:slug="{planet}">` so they can be targeted by planet slug (both primary outer-ring and inner dual-chart indicators).
- Add full `kr:` metadata to transit/secondary planet glyphs (`kr:node="ChartPoint"`, `kr:slug`, `kr:house`, `kr:sign`, `kr:absoluteposition`, `kr:signposition`) — previously only had `class="transit-planet-name"`.
- Add `kr:house` attribute to `HouseNumber` elements (`<g kr:node="HouseNumber" kr:house="{n}">`) for direct querying without parsing text content.
- Wrap external-view connecting lines in `<g kr:node="ConnectingLine" kr:slug="{planet}">`.
- Fix typo: `kr:sing` → `kr:sign` on Cusp elements (both first and second subject).
- Regenerated all SVG test baselines.

## 6.0.0a14

_2026-04-03_

**Performance optimizations, benchmark tooling, and baseline regeneration.**

### Changes

- Cache SVG templates and CSS themes with `@lru_cache` (eliminates ~400KB disk I/O per render after first call).
- Consolidate `model_copy()` calls in optional calculations: accumulate all updates per point, apply single `model_copy` at the end (reduces Pydantic model constructions from up to 345 to max 69).
- Convert string concatenation (`output +=`) to list-join pattern in SVG drawing functions.
- Cache `load_language_settings()` for the common no-overrides case.
- Use `reset_session()` instead of `close()` in `ephemeris_context` to preserve LEB reader, Skyfield timescale, and LRU caches across consecutive calculations.
- Added `poe benchmark` for measuring subject creation, aspects, and SVG rendering performance.
- Added `poe regenerate:configurations` and included it in `poe regenerate:all`.
- Regenerated all configuration-specific baselines (sidereal modes, perspectives, house systems, returns, composite, ephemeris, arabic parts) for libephemeris 1.0.0a15.
- Relaxed Pluto-Chiron aspect movement test to accept both Static and Applying (boundary-sensitive with slow planets).

## 6.0.0a13

_2026-04-03_

**Regenerate test baselines for libephemeris 1.0.0a15 and fix cross-backend test tolerances.**

### Changes

- Regenerated all SVG, report, and expected-data test baselines with libephemeris 1.0.0a15.
- Fixed cross-backend test tolerances: baselines are now generated with libephemeris (not swisseph), so swisseph gets relaxed tolerances and libephemeris gets tight tolerances.
- Increased position tolerance from 0.15° to 0.2° for swisseph cross-backend comparison to accommodate ancient date ΔT divergence (500 BC).
- Skipped heliocentric synastry SVG test for swisseph (house comparison integers differ across backends).

## 6.0.0a7

_2026-04-01_

**Ephemeris trace output now follows canonical planetary order instead of zodiac degree order.**

This release makes the new DEBUG trace easier to scan during debugging sessions. The `Ephemeris trace` table now follows the stable astrological order of bodies (`Sun`, `Moon`, `Mercury`, `Venus`, `Mars`, ...) instead of reordering rows by absolute position in the zodiac for each chart.

### Changes

- Changed `AstrologicalSubjectFactory._calculate_planets()` trace ordering from absolute degree sorting to canonical point ordering based on the declared `STANDARD_PLANETS`, `White_Moon`, and `TNO_PLANETS` sequences.
- Kept absolute degree as a displayed value in the table, but no longer use it as the primary sort key.

## 6.0.0a6

_2026-04-01_

**DEBUG logging for backend tracing and chart layout is now concise, structured, and module-scoped.**

This release cleans up the new ephemeris tracing logs introduced in `6.0.0a5`. Backend provenance is still available only in DEBUG mode, but the output is now grouped by concern: a compact ephemeris trace table during subject calculation, and overlap-group summaries during chart layout. Per-point rendering noise and root-logger output have been removed.

### Changes

- Replaced one-line-per-body backend trace logs with an ordered `Ephemeris trace` table showing point, absolute degree, and backend.
- Removed noisy per-point `Planet index` and `distance_to_prev` / `distance_to_next` logs from `draw_planets.py`.
- Added compact `Layout overlap groups` DEBUG logs that only report actual collision groups that require visual spreading.
- Switched these debug paths to module loggers instead of `root`, so log output now identifies `kerykeion.astrological_subject_factory`, `kerykeion.charts.draw_planets`, and `kerykeion.aspects.aspects_factory` explicitly.

## 6.0.0a5

_2026-04-01_

**Backend debug tracing stays out of the public model and is exposed only through DEBUG logs.**

This release keeps `KerykeionPointModel` clean while still making ephemeris provenance visible during debugging. When `libephemeris` is the active backend and logging is set to DEBUG, kerykeion now logs which backend computed each body (for example `LEB`, `Skyfield`, `Horizons`, `SPK`, `ASSIST`, `Keplerian`) without adding any new public response fields.

### Changes

- Added DEBUG-only tracing logs in `AstrologicalSubjectFactory._calculate_planets()` using `libephemeris.start_tracing()` / `get_trace_results()`.
- Improved chart rendering debug logs to include both point index and point name.
- Pinned the core `libephemeris` dependency to `1.0.0a8`, which provides the tracing API required by this release.

## 6.0.0a4

_2026-03-31_

**Remove `source` field from `KerykeionPointModel`.**

The `source` field added in 6.0.0a3 (`"ephemeris"`, `"derived"`, `"formula"`) has been removed. It provided redundant information -- the provenance of every point is already obvious from its name and type (e.g. Descendant is always derived from ASC+180, Pars Fortunae is always a formula). The field added noise to every API response without aiding actual debugging.

Ephemeris backend tracing (LEB vs Skyfield vs SPK vs Horizons) -- which is the genuinely useful debug information -- is handled at the API layer via an opt-in `X-Debug-Ephemeris` header that captures `libephemeris` log output. This keeps kerykeion clean and the debug infrastructure where it belongs.

### Breaking Changes

- **Removed `source` field** from `KerykeionPointModel`. Consumers that read `.source` on points will get an `AttributeError`. Since this field was only introduced in 6.0.0a3 (never in a stable release), the impact is minimal.
- **Removed `source` parameter** from `get_kerykeion_point_from_degree()` in `utilities.py`.

## 6.0.0a3

_2026-03-31_

**Ephemeris delegation refactor -- delegate derived/analytical points to backends, new celestial points.**

This release refactors how kerykeion computes derived and analytical astrological points, following the principle: _"Astronomical calculations belong to the backend. Astrological logic belongs to Kerykeion."_

### New Celestial Points

- **Interpolated Perigee** (`SE_INTP_PERG = 22`) -- the interpolated lunar perigee (closest approach), computed natively by the ephemeris backend. Not the same as `Lilith + 180` -- the actual perigee can differ by ~25° from the geometric opposite of the apogee.

- **White Moon / Selena** (`SE_WHITE_MOON = 56`) -- computed natively when the backend supports it; falls back to `Mean Lilith + 180` on backends that don't (e.g. swisseph). The fallback computes Mean Lilith locally without leaking it into the public model.

### Breaking Changes

- **Interpolated Lilith now uses `SE_INTP_APOG = 21`** instead of the previous naive `circular_mean(Mean, True)` formula. The new value is the astronomically correct interpolated apogee computed via the ELP2000-82B perturbation series (~50 terms). This is numerically different from the old formula and is no longer constrained to lie between Mean and True Lilith.

### `OPPOSITE_PAIRS` Consolidation

All `+180°` derived points are now declared in a single `OPPOSITE_PAIRS` dictionary and computed by one `_calculate_opposite_points()` method. This replaces ~7 separate inline blocks scattered across `_calculate_houses()` and `_calculate_planets()`.

Consolidated pairs: Descendant (from ASC), Imum Coeli (from MC), Anti-Vertex (from Vertex), Mean/True South Lunar Node (from North Nodes), Mean/True Priapus (from Mean/True Lilith).

### Bug Fixes

- **`SE_JUL_CAL` → `JUL_CAL`** -- fixed cross-backend compatibility for BCE date support. `swisseph` exposes `JUL_CAL`, `libephemeris` exposes both. Using `JUL_CAL` for compatibility. This fixes all 38 `test_bce_dates.py` failures on the swisseph backend.

- **Anti-Vertex with Vertex not requested** -- Vertex is now always computed and stored internally when either `Vertex` or `Anti_Vertex` is in `active_points`, so the opposite-pair derivation always has its primary available.

- **Descendant / Imum Coeli with ASC/MC not requested** -- ASC and MC are now always stored in `data` (they are already computed at zero cost by `houses_ex2`), so `active_points=["Descendant"]` or `["Imum_Coeli"]` works correctly. Only added to `active_points` output when explicitly requested.

- **White Moon fallback on swisseph** -- the fallback path now computes Mean Lilith locally via `swe.calc_ut(jd, 12, flags)` without writing it to the public model, preventing an unrequested `mean_lilith` field from leaking into the subject.

### Internal Changes

- Added `Interpolated_Perigee` and `White_Moon` to: `AstrologicalPoint` literal type, `AstrologicalBaseModel`, `KerykeionLanguageCelestialPointModel`, `DEFAULT_CELESTIAL_POINTS_SETTINGS`, `ALL_ACTIVE_POINTS`, and all 10 language translation dictionaries.
- Updated `_POINT_NUMBER_MAP` in `utilities.py` with correct body IDs for `True_Lilith` (13), `Interpolated_Lilith` (21), `Interpolated_Perigee` (22), `White_Moon` (56).
- Regenerated all modern SVG chart baselines to reflect new points.
- Updated `test_lilith_variants.py` to reflect the new `SE_INTP_APOG` semantics.

## 6.0.0a2

_2026-03-30_

**BCE date support -- historical charts for dates before 1 AD.**

### BCE Date Support

- **Dates before 1 AD are now fully supported.** Pass negative years (astronomical year numbering: 0 = 1 BCE, -1 = 2 BCE, etc.) to `AstrologicalSubjectFactory.from_birth_data()` and all chart types work: natal, transit, synastry, with any house system or sidereal mode.

- **How it works:** For `year < 1`, Python's `datetime` is bypassed entirely. Julian Day is computed directly via `swe.julday()` with the Julian calendar (`SE_JUL_CAL`). Timezone offset uses Local Mean Time (LMT) based on longitude -- historically correct for dates predating standardized time zones.

- **Both backends supported:** Works identically with libephemeris and swisseph. Julian Day agreement < 1e-6, Sun position agreement < 0.1°.

- **Chart rendering:** SVG charts (natal, transit, synastry) render correctly for BCE dates. ISO 8601 extended year format (e.g. `-0500-03-21T12:00:00+01:35`) used throughout.

- **New utility functions:** `format_ancient_iso()`, `format_iso_display()`, `extract_year_from_iso()` in `kerykeion.utilities` for BCE-safe date formatting.

- **68 new tests** covering subject creation, Julian Day baselines, LMT offset, ISO formatting, day of week, planetary positions, SVG baselines (natal/transit/synastry), house systems, sidereal modes, backend comparison, report generation, and modern date regression.

#### Example

```python
from kerykeion import AstrologicalSubjectFactory

# Spring equinox in Ancient Greece, 501 BCE
subject = AstrologicalSubjectFactory.from_birth_data(
    name="Ancient Greece",
    year=-500, month=3, day=21, hour=12, minute=0,
    lat=37.9838, lng=23.7275, tz_str="Europe/Athens",
    online=False,
)
print(subject.sun.sign)  # Pis
print(subject.julian_day)  # 1538512.934...
```

## 6.0.0a1

_2026-03-29_

**First alpha release of Kerykeion v6 -- major feature release with 22 new astrological features, 8 new standalone factories, and 11 new celestial points.**

All v6 features are **opt-in** -- existing code works unchanged with no breaking changes to the public API.

### New Standalone Factories

- **PrimaryDirectionsFactory** -- Placidus semi-arc primary directions with Ptolemy (1 deg = 1 year) and Naibod (0.9856 deg/year) rate keys. Computes speculum with equatorial coordinates, meridian distance, and semi-arc data.

- **AstroCartographyFactory** -- Planetary line mapping (ACG). Computes MC, IC, ASC, DSC lines globally with configurable step size, geographic tolerance, and latitude range.

- **EclipseFactory** -- Localized and global solar/lunar eclipse search. Returns eclipse type (total, annular, partial, penumbral), magnitude, obscuration, and sun altitude for visibility.

- **PlanetaryPhenomenaFactory** -- Observational phenomena: phase angle, illumination, elongation, apparent diameter/magnitude, and morning/evening star detection for Mercury and Venus.

- **PlanetaryNodesFactory** -- Ascending/descending nodes and perihelion/aphelion for all planets. Supports mean and osculating (instantaneous) calculation methods.

- **HeliacalFactory** -- Heliacal rising, setting, evening first, and morning last events. Customizable atmospheric conditions (pressure, temperature, humidity, extinction) and observer parameters.

- **OccultationFactory** -- Lunar occultation search (global and location-specific). Returns occultation type (total, partial, annular), maximum Julian Day, and datestamp.

- **FixedStarDiscoveryFactory** -- Auto-discover fixed stars near natal planets beyond the default 23. Configurable orb tolerance, accesses the full Swiss Ephemeris star catalog.

### New Chart Features

- **Davison Composite Chart** -- New composite method that calculates the midpoint in both time and space (vs. existing zodiac-midpoint method). Available via `CompositeSubjectFactory.get_davison_composite_subject_model()`.

- **Relocated Charts** (`RelocatedChartFactory`) -- Recalculate houses and angles for a different geographic location while keeping all planetary positions unchanged.

### New Celestial Points

- **8 Uranian / Hamburg School hypothetical planets:** Cupido, Hades, Zeus, Kronos, Apollon, Admetos, Vulkanus, Poseidon. Full SVG symbols, CSS color variables (all 6 themes), and chart default settings included.

- **3 Lilith/Priapus variants:** Interpolated Lilith, Mean Priapus, and True Priapus (anti-Lilith points, opposite of Mean/True Lilith).

### New Calculation Options

All activated via `AstrologicalSubjectFactory.from_birth_data()` keyword arguments:

- **`calculate_dignities=True`** -- Ptolemaic essential dignities. New fields: `decan_number`, `decan_ruler`, `term_ruler`, `essential_dignity` ("Domicile"/"Exaltation"/"Detriment"/"Fall"/"Peregrine"), `dignity_score` (-5 to +5).

- **`calculate_nakshatra=True`** -- Vedic lunar mansions (27 Nakshatras). New fields: `nakshatra`, `nakshatra_number` (1-27), `nakshatra_pada` (1-4), `nakshatra_lord` (Vimsottari Dasha ruler).

- **`calculate_gauquelin=True`** -- Gauquelin 36-sector system for statistical astrology. New field: `gauquelin_sector` (1.0-36.99). Full SVG rendering with sector lines replacing house cusps in both classic and modern chart styles.

- **`calculate_local_space=True`** -- Horizon coordinates. New fields: `azimuth` (compass bearing 0-360) and `altitude_above_horizon` (degrees above/below horizon).

- **`calculate_nutation=True`** -- Earth's nutation model. New model-level field: `nutation` (`NutationObliquityModel` with `true_obliquity`, `mean_obliquity`, `nutation_longitude`, `nutation_obliquity`).

- **`active_fixed_stars=["Sirius", ...]`** -- Dynamically add fixed stars beyond the default 23-star catalog.

### New Perspective Types

- **Barycentric** perspective (solar system barycenter as origin). Added to the existing set: Apparent Geocentric, True Geocentric, Heliocentric, Topocentric, and 7 planetocentric variants (Seleno-, Mercury-, Venus-, Mars-, Jupiter-, Saturn-centric).

### New Aspect Types

- **Declination aspects:** `parallel` (same declination) and `contra_parallel` (opposite declination).

### Enhanced Returns & Transits

- **Heliocentric returns** and **Lunar Node Crossing** returns via `PlanetaryReturnFactory`.
- **Transit exactness refinement** via bisection: `refine_exact_moments=True` with configurable `refinement_iterations` (default 12 = ~0.244s precision).

### New Model Fields on KerykeionPointModel

- `is_out_of_bounds: Optional[bool]` -- True when declination exceeds the Sun's maximum (~23.44°), indicating a planet operating outside normal boundaries. Always populated when declination is available.
- All dignity, nakshatra, gauquelin, local space, and azimuth fields listed above.

### Bug Fixes

- **Modern style Gauquelin rendering:** Fixed three bugs that broke the modern chart wheel when Gauquelin sectors were active:
  - House division lines (12 thick lines crossing the planet ring) were still drawn instead of 36 sector lines. Now correctly draws Gauquelin sector divisions through the planet ring.
  - The inner house ring used wrong Y coordinates and inconsistent rotation sign, causing sector markers to render as a misplaced bar.
  - Added new `_draw_gauquelin_division_lines()` function for sector lines in the planet ring.

- **Multi-column grid headers:** When many active points cause the Gauquelin unified grid to split into multiple columns, the header row (Planet, Longitude, Decl., Sector) now appears on all columns instead of only the first.

- **SVG height for many active points:** The triangular aspect grid grows by 14px per point but the SVG height was only growing by 8px per point. With 55+ active points, the aspect grid was clipped at the top. Height calculation now accounts for the aspect grid's actual growth rate.

- **Aspect grid / planet grid overlap:** With multi-column Gauquelin layouts, the planet grid extends leftward and could overlap the aspect grid. The aspect grid X position now shifts rightward together with the planet grid.

- **Gauquelin grid centering:** The unified Gauquelin grid (220px wide) now shifts 30px left for better visual symmetry.

### Ephemeris Backend Abstraction

- **Dual-backend architecture**: Kerykeion now supports two interchangeable ephemeris backends -- **libephemeris** (pure Python, AGPL-3.0, default) and **swisseph** (C bindings, GPL-2.0, optional). Both are 100% API-compatible; all features work identically on both.
- **libephemeris** uses NASA JPL DE440/DE441 ephemeris data via Skyfield. No C compiler required. Installed by default with `pip install kerykeion`.
- **swisseph** remains available via `pip install kerykeion[swiss]` for users who need maximum speed or have existing GPL workflows.
- Backend selection: auto-detected (libephemeris preferred) or explicit via `KERYKEION_BACKEND=swisseph|libephemeris` environment variable.
- **Barycentric precision**: libephemeris uses JPL DE440 native barycentric coordinates (N-body gravitational dynamics), making it the more accurate backend for barycentric work.
- Planetary longitude agreement < 0.02 deg across backends; house cusps < 0.05 deg; retrograde status always identical. See `site/docs/backend_precision_comparison.md` for full details.
- Three test suites: `poe test:swe` (swisseph, 8659 tests), `poe test:lib` (libephemeris, 2460+ tests), `poe test:compare` (cross-backend equivalence).

### Internal / Deprecations

- Removed v4 backward compatibility layer (`kr_types` module excluded from coverage, marked for deprecation).
- Removed stale v6 planning docs (all features implemented and tested).
- `SubscriptableBaseModel` added for dictionary-style field access on Pydantic models.
- 8700+ tests passing across both backends, including 50+ dedicated v6 feature tests and factory coverage at 98-100%.

## 5.12.0

_2026-03-18_

**Bugfixes:**

- **Modern chart decluttering order (v5.12.8):** Fixed a bug where planets in a tight cluster on `style="modern"` charts could be pushed past their neighbours, violating true zodiacal order (e.g. Neptune at 5° Aquarius rendered after Uranus at 17° Aquarius). The collision-resolution algorithm in `_resolve_planet_collisions` was rewritten from a 5-pass iterative push (vulnerable to wraparound overshoots) to a single-pass largest-gap linearization that is monotonic by construction: planets are cut at the largest gap in their true zodiacal angles and walked forward once with `display_angle = max(desired_linear, prev_linear + sep)`. Order is preserved and `min_separation` is respected without iterative refinement. Reproduced by any dense stellium (≥3 planets within ~8°); regression covered by `tests/core/test_modern_decluttering.py`.

**New Features:**

- **Retrograde indicator on classic wheel (v5.12.7):** The ℞ (retrograde) symbol is now rendered next to retrograde planet glyphs directly on the classic style chart wheel. Previously, retrograde status was only visible in the sidebar grid and in modern style charts. The symbol appears at the bottom-right foot of each retrograde planet glyph on both inner-ring (natal) and outer-ring (transit/synastry) planets. A `kr:retrograde="true"` attribute is also added to the planet group elements for programmatic consumers.

- **House cusp speeds (v5.12.1):** Replaced `swe.houses_ex()` with `swe.houses_ex2()` to expose cusp velocities. All 12 house cusps and the 4 angular points (ASC, MC, DSC, IC) now carry a `speed` field (degrees/day) representing the real rate of diurnal motion. Useful for primary directions and profection techniques.

- **Expanded fixed stars (v5.12.2):** Grew the fixed star catalogue from 2 to 23 stars. The 21 new stars are: Aldebaran, Antares, Sirius, Fomalhaut, Algol, Betelgeuse, Canopus, Procyon, Arcturus, Pollux, Deneb, Altair, Rigel, Achernar, Capella, Vega, Alcyone, Alphecca, Algorab, Deneb_Algedi, and Alkaid. The set now includes all 15 Behenian stars of the medieval/Hermetic tradition and the 4 Royal Stars of Persian/Hellenistic astrology (Regulus, Aldebaran, Antares, Fomalhaut). Each fixed star now also reports apparent visual magnitude via `swe.fixstar2_mag()` and equatorial declination.

- **Expanded sidereal modes (v5.12.3):** Grew supported ayanamsa systems from 20 to 47 named modes plus a `USER` mode for custom ayanamsa definitions (48 total). New mode families include additional Indian/Vedic variants (Aryabhata, Suryasiddhanta, True Citra/Pushya/Revati, Lahiri sub-variants), Babylonian systems (Britton), galactic alignment systems, and the Valens Moon ayanamsa. The `USER` mode accepts `custom_ayanamsa_t0` (reference epoch as Julian Day) and `custom_ayanamsa_ayan_t0` (ayanamsa offset in degrees at that epoch).

- **Ayanamsa value exposure (v5.12.4):** Added `ayanamsa_value` field to `AstrologicalBaseModel`. For sidereal charts, this contains the computed angular offset (in degrees) between tropical and sidereal 0 Aries at the chart's date/time. `None` for tropical charts. Calculated via `swe.get_ayanamsa_ex_ut()`.

- **SVG rendering for new stars:** Added SVG symbol definitions, CSS color variables (all 6 themes), chart default settings, and weighted point weights for all 21 new fixed stars. Each star has a unique icon representing its traditional astronomical/astrological character.

- **Right-panel aspect layout:** Charts with more than 24 active points now render the aspect list/grid to the right of the wheel instead of below it, preventing excessive vertical growth. Controlled by the internal `_RIGHT_PANEL_POINTS_THRESHOLD` constant.

- **Fixed star color contrast:** Darkened 7 fixed star colors in the classic theme (Sirius, Procyon, Canopus, Capella, Deneb, Altair, Pollux) for better visibility against white/light backgrounds.

- **`style` and `show_zodiac_background_ring` on constructor:** Promoted `style` and `show_zodiac_background_ring` from render-method-only arguments (v5.11) to `ChartDrawer.__init__()` keyword arguments. This allows setting a per-instance default that applies to all subsequent render calls, while still permitting per-render overrides via the `_UNSET` sentinel pattern.

**New Fields (all Optional, default None -- no breaking changes):**

- `KerykeionPointModel.speed` -- daily motion in degrees/day
- `KerykeionPointModel.declination` -- equatorial declination in degrees
- `KerykeionPointModel.magnitude` -- apparent visual magnitude (fixed stars only)
- `AstrologicalBaseModel.ayanamsa_value` -- ayanamsa offset in degrees (sidereal only)
- `AstrologicalBaseModel.aldebaran` through `.alkaid` -- 21 new fixed star fields
- `ChartConfiguration.custom_ayanamsa_t0` -- Julian Day reference epoch for USER mode
- `ChartConfiguration.custom_ayanamsa_ayan_t0` -- ayanamsa degrees at t0 for USER mode

**Documentation:**

- Comprehensive docstrings for all new/modified functions explaining Indian astrology concepts (ayanamsa, sidereal zodiac, precession) for Western astrology users
- `SiderealMode` literal now includes a full docstring with mode families, typical ayanamsa values, and USER mode usage
- `AstrologicalPoint` literal docstring corrected and expanded with fixed star categorization (Royal Stars, navigational stars)
- All factory methods (`from_birth_data`, `from_iso_utc_time`, `from_current_time`) document custom ayanamsa parameters
- `_calculate_houses` docstring documents `houses_ex2` switch and cusp speed semantics
- `_calculate_planets` fixed stars section updated for 23 stars with magnitude/declination
- `FIXED_STARS` constant annotated with star identifications and magnitudes
- `ALL_ACTIVE_POINTS` and `DEFAULT_ACTIVE_POINTS` organized with section comments

**Tests:**

- 266 dedicated v5.12 tests across 9 test classes covering house cusp speeds, expanded fixed stars, star magnitudes, star declinations, sidereal modes, USER-defined ayanamsa, ayanamsa value exposure, and guiding principles (no breaking changes)

## 5.11.0

_2026-03-18_

**New Features:**

- Added **modern chart style** — a concentric-ring layout alternative to the classic wheel. Pass `style="modern"` to `save_svg()`, `generate_svg_string()`, `save_wheel_only_svg_file()`, or `generate_wheel_only_svg_string()`. The modern layout renders 5 rings: cusp/zodiac signs, graduated ruler scale, planet data clusters, house numbers, and aspect lines with midpoint glyphs. Works with all six themes and all chart types (Natal, Synastry, Transit, Lunar/Solar Return, Composite).

- Added `show_zodiac_background_ring` parameter (modern style only) — when set to `False`, omits the colored zodiac wedges from the outer ring.

- Added `KerykeionChartStyle` literal type (`"classic"` | `"modern"`) to `kerykeion.schemas`.

- New drawing module `kerykeion.charts.draw_modern` with `draw_modern_horoscope()` and `draw_modern_dual_horoscope()` functions.

- New SVG template `kerykeion/charts/templates/modern_wheel.xml` for standalone modern wheel rendering.

**Bugfixes:**

- Fixed modern chart zodiac background ring using only 2 alternating colors instead of the full per-element color cycle. The outer ring now matches the classic chart's 4-color element pattern (fire/earth/air/water) in the default theme, with all 12 `--kerykeion-modern-zodiac-bg-*` CSS variables properly defined across all 6 themes.
- Fixed ruler ring ticks to be uniformly spaced across the full 360° circle.
- Fixed planet cluster sub-element sizes and reduced size progression for better readability.

**Documentation:**

- Added 2×2 chart style showcase grid (classic/modern × default/dark) to README
- Added Modern Chart Style section to README with examples for Natal, Synastry, Transit, and Wheel-Only
- Added `site/examples/modern-charts.md` example page
- Added `site/docs/charts.md` documentation with modern style API reference
- Added several new example/documentation pages (active points, ephemeris data, house comparison, transits time range)
- Simplified `MIGRATION_V4_TO_V5.md` — content moved to main documentation site

**Tests:**

- Added 36+ comprehensive modern chart style tests covering all chart types, themes, and rendering modes
- Added tests for `show_zodiac_background_ring=False` across chart types
- Added modern SVG baselines to the regeneration pipeline (`regenerate:svg:modern` poe task)

**Maintenance:**

- Updated all 6 CSS themes with modern-style variables
- Added `scripts/generate_modern_baselines.py` and `scripts/regenerate_docs_charts.py`
- Added example script `examples/modern_chart_john_lennon.py`

## 5.10.0

_Released 26/02/2026_

**Breaking Changes:**

- **Context Serializer XML Migration:** The `to_context()` function and all `*_to_context()` helper functions now produce well-formed **XML output** instead of plain text. This affects all 13 converter functions. XML uses semantic tags with attributes (e.g. `<point name="Sun" sign="Capricorn" ... />`), self-closing tags for atomic data, and nested tags for structured data. Optional/`None` fields are omitted from the output rather than rendered as empty tags. All values are properly escaped via `xml.sax.saxutils`.

**New Features:**

- Added `moon_phase_overview_to_context()` — serializes `MoonPhaseOverviewModel` to XML with full support for all nested fields (moon summary, sun info, location, zodiac, upcoming phases, eclipses, visibility, illumination details, events)
- Added `MoonPhaseOverviewModel` support in the `to_context()` dispatcher

**Bugfixes:**

- Fixed house cusp sign abbreviation in context serializer output (e.g. `"Ari"` now correctly rendered as `"Aries"` via `SIGN_FULL_NAMES` mapping)
- Fixed `llms.txt` import example (added missing `AstrologicalSubjectFactory`, `ChartDataFactory` imports)

**Documentation:**

- Updated `README.md` AI Context Serializer section with XML output examples
- Updated `site/docs/context_serializer.md` with XML format documentation and examples
- Updated `kerykeion/llms.txt` Section 6 to document XML output format
- Updated `examples/context_serializer_example.py` with Element/Quality Distribution and Moon Phase Overview examples

**Tests:**

- Rewrote all context serializer test assertions for XML format in `tests/core/test_context_serializer.py`
- Added 17 tests for `MoonPhaseOverviewToContext` covering all nested branches (zodiac, moonrise/moonset, eclipses, detailed position, visibility, illumination, events, sun info, extended location)
- Extended `TestNonQualitativeOutput` to verify subject, natal chart, synastry chart, and moon phase overview outputs
- Added synastry relationship score, transit data, house comparison, and point-in-house assertion enhancements
- Removed 2 dead stub tests
- Updated 7 context serializer edge case test classes for XML assertions

## 5.9.0

_Released 26/02/2026_

**New Features:**

- Added `MoonPhaseDetailsFactory` — a new factory class that computes detailed moon phase information from an `AstrologicalSubjectModel`. Uses Swiss Ephemeris binary search (1-second precision) to find exact times of upcoming and previous New Moon, First Quarter, Full Moon, and Last Quarter. Also computes illumination percentage, waxing/waning stage, moon age, lunar cycle progress, next lunar/solar eclipses, sunrise/sunset, solar noon, day length, and Sun/Moon zodiac signs.

- Added `MoonPhaseOverviewModel` report support in `ReportGenerator` — a new `"moon_phase_overview"` report kind that renders all moon phase details as a human-readable text report with sections for Moon Summary, Illumination Details, Upcoming Phases, Next Lunar Eclipse, Sun Info, Next Solar Eclipse, and Location.

**Documentation:**

- Added `moon_phase_details_factory.md` documentation page with API reference, nested data access patterns, JSON serialization, precision notes, and edge cases
- Added `moon-phase-details.md` examples page with practical usage examples (basic usage, upcoming phases, eclipses, sun times, report generation, JSON export, zodiac info, location metadata)
- Updated `report.md` with Moon Phase Overview Report section and configuration table
- Updated `index.md` with Moon Phase Details Factory link in the Forecasting section
- Updated `README.md` with Moon Phase Details section, code example, and links to documentation

**Tests:**

- Added 54 mocked unit tests for `MoonPhaseDetailsFactory` (helper functions, full `from_subject()` with mocked Swiss Ephemeris layer, null/failure edge cases, phase angle boundary tests)
- Added 21 report tests with golden snapshot fixture for moon phase overview
- Added 2042 historical verification tests against AstroPixels reference data (2001–2040), covering angle accuracy, phase names, emojis, factory major_phase, illumination, waxing/waning stage, upcoming phases, eclipse predictions, synodic month bounds, and 28-phase boundary mapping

**Bugfixes:**

- Fixed `ReportGenerator` crash when `_primary_subject` is `None` (added defensive `assert` guards in `_build_subject_report`, `_build_single_chart_report`, and `_build_dual_chart_report`)
- Fixed pre-existing `RelationshipScoreFactory` code snippet bug in `README.md` (wrong method name and field names)
- Fixed frontmatter ordering collision between `transits_time_range_factory.md` and `ephemeris_data_factory.md`

**Maintenance:**

- Added `charts_output/` to `.gitignore`
- Added example scripts: `moon_phase_report_example.py`, `moon_phase_json_example.py`

## 5.8.1

_Released 26/02/2026_

**Bugfixes:**

- Fixed degree label rotation on SVG chart outer ring.

**Maintenance:**

- Removed legacy chart drawing module (`draw_planets_legacy.py`)

## 5.8.0

_Released 24/02/2026_

**New Features:**

- Added `is_diurnal` field to `AstrologicalSubjectModel` — a boolean indicating whether the chart is diurnal (Sun above horizon) or nocturnal (Sun below horizon). This sect classification is calculated using the Sun's geometric altitude via `swe.azalt()`, making it independent of house system, zodiac type, and perspective type.

- Added `--arabic-parts` option to `regenerate_all.py` for generating Arabic Parts snapshots (`expected_arabic_parts.py`)

**Bugfixes:**

- Fixed day/night chart detection for Arabic Parts (Pars Fortunae, Spiritus). The previous logic used house position (`house < 7`) which was astronomically inverted — houses 1-6 are below the horizon (night), not above. The fix uses the Sun's geometric altitude, which is astronomically precise and house-system independent.

- Fixed Arabic Parts calculation for sidereal and heliocentric charts. Previously, the day/night detection used the Sun's position from the chart's coordinate system (sidereal or heliocentric), which gave incorrect results. Now it always uses a tropical geocentric reference position.

**Improvements:**

- Refactored `regenerate_all.py` to use `model_dump(exclude_none=True)` instead of manual field extraction, making it future-proof for new model fields

- Simplified `_compute_is_diurnal()` with a single fallback to `True` (diurnal) when calculation fails, with clear warning logging

- Added comprehensive test coverage for `is_diurnal` (15 tests) and Arabic Parts (68 tests total)

## 5.7.3

_Released 18/02/2026_

**Bugfixes:**

- Fixed floating point comparison in `is_point_between()` function that caused `ValueError` crashes when a planet falls exactly on a house cusp (difference ~1e-15°). The fix uses `math.isclose()` instead of exact equality (`==`). This affected Carter, Krusinski, and Uranian house systems.

## 5.7.2

_Released 05/02/2026_

**New Features:**

- Added support for `KERYKEION_GEONAMES_USERNAME` environment variable to configure GeoNames API username without code changes

**Bugfixes:**

- Regenerated extended chart SVG baselines (strawberry theme, sidereal×theme combinations, house system×chart type combinations) to align with the precise orb comparison fix from v5.7.1
- Updated relationship score test expectations to reflect stricter aspect filtering
- Fixed `regenerate:all` task to include `regenerate_test_charts_extended.py` script, preventing future baseline drift

**Maintenance:**

- Added `regenerate:charts-extended` poe task for regenerating extended test charts

## 4.2.0

_Released 08/01/2023_

**Bugfixes:**

- fixing float-int presidence bug

**Dependency Updates:**

- Updated `pydantic` to `2.5`

**Credits:**

- Thanks to @jackklika for the PR, more details [here](https://github.com/g-battaglia/kerykeion/pull/98)

## 4.4.0

_Released 05/03/2024_

**New Features:**

Allow UTC datetime to be passed in the constructor as an alternative to year, month, day, hour, minute and timezone (#108)

**Credits:**

- Thanks to @jackklika for the PR, more details [here](https://github.com/g-battaglia/kerykeion/pull/108)

## 4.5.0

- _AstrologicalSubject_ Is now possible to disable Chiron calculation with `disable_chiron=True` for better compatibility with older dates.
- New module enums added for better type hinting, still to be expanded and really used.

## 4.5.1

- Fixed | bug for compatibility with Python 3.9

## 4.6.0

- Now the `lunar_phase` contains also the `lunar_phase_name` property, which is a string representation of the phase.
- Minor general cleanup and refactoring of the codebase.

## 4.7.0

A lot of refactoring and clean up.
`Fix`: In the old version the 4 last planets of the Transit chart were always removed, now we check if those are Axes and then
remove them.

## 4.8.0

Added the optional `minify` argument to makeTemplate in the charts module.

## 4.10.0

- Added the `sidereal_mode` argument to the `AstrologicalChart` class to allow differet Ayanamsa calculation methods.

## 4.11.0

- Added different House Systems to the `AstrologicalChart` class.

## 4.14.0

- Added Lilith to astrological calculations and chart rendering.
- Deprecated `disable_chiron` in favor of `disable_chiron_and_lilith` with deprecation warning.
- Updated configuration in `kr.config.json` for Lilith settings.

## 4.16.0

- Added themed astrological charts (`theme` parameter), including Classic, Dark, Dark High Contrast, and Light themes.
- Added wheel-only charts and separate aspect table SVG.
- Added grid view for aspect tables in synastry and transit charts.

## 4.17.0

- Added `chart_language` parameter to set chart language (EN, FR, PT, ES, TR, RU, IT, CN, DE).
- Enhanced `get_settings` function to accept a dictionary or `KerykeionSettingsModel` instance.

## 4.19.0

- Added support for True and Mean Lunar Nodes (`true_node`, `true_south_node`, `mean_node`, `mean_south_node`).
- Default activation of mean nodes; configurable activation of true nodes via `kr.config.json`.

## 4.21.0

- Customizable Geonames cache timeout (default extended from 24 hours to 30 days).

**Credits:**

- Thanks to @tomshaffner for the idea and implementation.

## 4.22.0

- Explicit calculation of Ascendant (AC), Descendant (DC), Midheaven (MC), and Imum Coeli (IC) axes.
- Introduced `axial_cusps_names_list` parameter and replaced `check_if_between` with `is_point_between` utility.
- Configuration updates for axes in `kr.config.json`.

**Credits:**

- Thanks to @fkostadinov for implementing these changes in PR #138.

## 4.23.0

- Added `active_points` parameter to `KerykeionChartSVG` for runtime specification of active planets and axial cusps.

## 4.24.0

- Added `active_aspects` parameter to `KerykeionChartSVG` for runtime specification of active aspects and orbs.

## 4.25.0

- Added composite charts feature: create composite subjects and charts using the midpoint method.

## 4.26.0

- Introduced `TransitsTimeRangeFactory` for calculating transit events across specified time ranges.
- Added `get_ephemeris_data_as_astrological_subjects` method in `EphemerisDataFactory`.
- Added `p*_owner` fields in aspect models for subject identification in `natal_aspects` and `synastry_aspects`.
