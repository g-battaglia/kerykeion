---
name: kerykeion-cli
description: >-
  Drive kerykeion from the terminal — astrology without writing Python. Use this
  skill WHENEVER the task is to run astrology from a shell, a pipeline, a
  Makefile, a cron job or CI: natal / synastry / transit / composite / return /
  progression charts and SVG wheels; aspects, dominants, moon phase,
  relationship score; profections, firdaria, zodiacal releasing, horary, primary
  directions, solar arc, astrocartography, house comparison, fixed stars;
  eclipses, lunations, ingresses, stations, void-of-course Moon, sun times,
  planetary hours, mundane aspects, phenomena, occultations; ephemeris and
  transit time series. Trigger on "kerykeion" plus any of terminal, shell, bash,
  command line, CLI, pipe, jq, script, cron, CI, or on a pasted `kerykeion ...`
  command. Covers the profile store, exit codes, stdout-vs-stderr discipline,
  the `call` dispatcher that reaches every public factory, and the traps that
  silently produce a wrong chart. To write Python instead, use `kerykeion`.
license: AGPL-3.0
---

# Driving Kerykeion from the terminal

Verified against **kerykeion 6.0.0a92**, Python 3.12+.

The CLI ships as an optional extra. Everything the library computes is reachable
from the shell: about fifty curated commands, plus `kerykeion call` as a guarded
dispatcher over the rest of the public API.

**Accuracy rule for you:** never invent a flag or a value. The CLI describes
itself — `kerykeion info literals -f json` lists every accepted value, and
`kerykeion call <Factory>.<method> --explain` describes every parameter. Read
those instead of guessing; the tables are large (48 ayanamsas, 23 house systems,
76 points) and change between releases.

## Install

```bash
# gate: skip
pip install "kerykeion[cli]"     # or: uv tool install kerykeion-cli
```

The command lives in its own package, `kerykeion-cli`, which the extra installs;
a plain `pip install kerykeion` has the library and no command. The interface is
built on the standard library alone, so nothing third-party comes with it.
`kerykeion status` is always safe to run first.

## The three rules that keep output usable

1. **The payload goes to stdout; warnings and notes always go to stderr.** This
   holds for every format, including JSON. Never parse stderr, and never assume
   a clean stderr means success — check the exit code.
2. **Format follows the destination**: a terminal gets text, a pipe gets JSON.
   Force it with `-f text|json|xml|svg`, or let `-o out.svg` infer from the
   suffix. Scripts should pass `-f` explicitly rather than rely on the default.
3. **Exit codes are the contract.** Branch on them; do not match on messages.

```bash
kerykeion subject save ada --name "Ada Lovelace" \
  --date 1815-12-10 --time 18:00 \
  --lat 51.5074 --lng -0.1278 --tz Europe/London --offline

kerykeion natal -s ada -f json | head -3        # JSON, no ANSI, clean to pipe
kerykeion natal -s ada -f svg -o /tmp/ada.svg   # SVG to a file
```

If a consumer cannot read stderr, `--envelope` puts provenance and the warnings
in the JSON itself:

```bash
kerykeion natal -s ada -f json --envelope
```

## Exit codes

| Code | Meaning | What to do |
|---|---|---|
| 0 | success | — |
| 1 | unexpected error | rerun with `--traceback`; this is a bug |
| 2 | usage error (from the parser) | fix the command line |
| 4 | invalid input | fix the flag the message names |
| 5 | kerykeion rejected the request | astrological/domain error |
| 6 | ephemeris problem | date out of coverage, missing data files |
| 7 | network | GeoNames unreachable; prefer `--offline` |
| 8 | sampling ceiling | narrow the range/step, or `--no-limit` |
| 9 | warnings escalated | you passed `--warnings-as-errors` |
| 130 | interrupted | — |

`kerykeion status --check` runs the install checks and exits 6 when the install
is genuinely broken; a plain `kerykeion status` only reports and always exits 0.

```bash
kerykeion status --check --json
```

## Subjects live in profiles

Almost every command takes `-s <profile>` rather than fifteen inline flags. A
profile is a JSON *recipe* stored under `$XDG_CONFIG_HOME/kerykeion/subjects/`,
written `0600` inside a `0700` directory because birth data is personal.

```bash
kerykeion subject list
kerykeion subject show ada -f json
kerykeion subject verify ada -f json
```

Inline flags override the profile, so a stored subject can be reused for a
relocated reading without editing it. Full details and `--set`:
[references/profiles.md](references/profiles.md).

## Capability routing — find the command, then open the reference

| You want | Command | Reference |
|---|---|---|
| natal, synastry, transit, composite, return, progression | `natal`, `synastry`, … | [commands.md](references/commands.md) |
| an SVG with a theme, a language, a variant | any chart command `-f svg` | [rendering.md](references/rendering.md) |
| aspects, dominants, moon phase, relationship score | `aspects`, `dominants`, `moon`, `relationship-score` | [commands.md](references/commands.md) |
| profections, firdaria, ZR, horary, directions, solar arc, ACG, relocation | `technique <sub>` | [commands.md](references/commands.md) |
| eclipses, lunations, ingresses, stations, VoC, hours, sun times, mundane, phenomena, occultations | `sky <sub>` | [commands.md](references/commands.md) |
| a time series of positions, or transits over a range | `ephemeris`, `transits` | [commands.md](references/commands.md) |
| storing and reusing a subject | `subject <sub>` | [profiles.md](references/profiles.md) |
| something with no curated command | `kerykeion call …` | [call-dispatcher.md](references/call-dispatcher.md) |
| the list of valid values for a flag | `kerykeion info …` | [io-and-exit-codes.md](references/io-and-exit-codes.md) |

## Top traps

These produce a **wrong chart silently** or a confusing failure. They are the
reason to read before composing a command.

- **House-system letters are case-sensitive.** `i` (Sunshine/alt.) and `I`
  (Sunshine) are different systems. `--houses placidus` (a name) is safer than a
  letter; `kerykeion info houses` lists both.
- **A relocated `transit`/`return` takes either `--lat`/`--lng`/`--tz` together
  or `--city` (geocoded; needs the network or the local default-geo database).**
  Two coordinates out of three is exit 4, on purpose: the natal timezone at new
  coordinates is a multi-hour error in the houses and Ascendant. Passing both
  `--city` and coordinates is also exit 4 — one command, one place, never a
  silent pick between the two.
- **`--online` and `--offline` are mutually exclusive** (exit 4). Prefer
  `--offline` in scripts; the default goes online only when lat/lng/tz are not
  all known.
- **`sky voc --from/--to` is a UTC range.** Pass `--tz` (or a profile) so naive
  bounds are read in that zone rather than as UTC.
- **An offset-bearing `--from` on a DST fall-back hour is refused** rather than
  guessed, because the moment factories take wall-clock parts without a fold.
- **`transits --refine` requires `--events`.** Alone it would be a silent no-op.
- **A long series hits the sampling ceiling (exit 8) before computing anything.**
  Widen the step or pass `--no-limit` deliberately.
- **Chart flags `--degree-indicators`, `--aspect-icons` and `--external-view`
  only apply to `--style classic`.** Under the default `modern` style the
  library ignores them and says so on stderr.

## Never invent values

```bash
kerykeion info literals -f json | head -5      # every accepted enum, by name
kerykeion info houses                           # letters and name aliases
kerykeion info points                           # what --points accepts
kerykeion info methods                          # strategy names per command
```

## Reference index

- [references/commands.md](references/commands.md) — the whole command tree, with
  what each one needs.
- [references/io-and-exit-codes.md](references/io-and-exit-codes.md) — formats,
  streams, `--envelope`, exit codes, `info`, `status --check`.
- [references/profiles.md](references/profiles.md) — the profile store, `--set`,
  permissions and PII.
- [references/rendering.md](references/rendering.md) — every SVG and report
  option, and which chart types they affect.
- [references/call-dispatcher.md](references/call-dispatcher.md) — reaching any
  public factory, `--explain`, and `--param` coercion.
- [references/recipes.md](references/recipes.md) — task-shaped examples for
  pipelines, batches and CI.

For writing Python against the library rather than driving it from a shell, use
the **`kerykeion`** skill instead.
