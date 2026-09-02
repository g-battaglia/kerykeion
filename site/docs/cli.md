---
title: 'Command Line Interface'
description: 'The optional kerykeion[cli] extra exposes every chart, technique, sky event and factory from the terminal — text on a TTY, JSON in a pipe.'
category: 'Integration'
tags: ['docs', 'kerykeion', 'cli', 'terminal', 'typer']
order: 64
---

# Command Line Interface

Kerykeion ships an optional command-line interface that exposes the whole
library — every chart type, analytical technique, sky event and factory —
without writing any Python. It is a **local** engine: it computes with the same
in-process backend as the library, so it works offline and needs no API key.

Install the `cli` extra (it adds [Typer](https://typer.tiangolo.com) and
[Rich](https://rich.readthedocs.io)):

```bash
pip3 install "kerykeion[cli]"
```

`kerykeion[all]` adds the extra **and** the optional Swiss Ephemeris backend.

> **No extra, no crash.** The `kerykeion` command is installed even by a plain
> `pip install kerykeion`. Without the extra it prints a one-line install hint
> and exits `3` — never a `Traceback`. `import kerykeion` stays free of `typer`.

## Output formats

Every command that produces a payload accepts `-f/--format` and `-o/--output`:

| Format | What it is |
|--------|------------|
| `text` | The ASCII `ReportGenerator` report (the default on a terminal) |
| `json` | The Pydantic `model_dump_json()` payload |
| `xml`  | The `to_context()` XML document |
| `svg`  | An SVG chart wheel |

With no `-f`, the format is chosen for you: **text on a TTY, JSON in a pipe**.
So `kerykeion natal -s ada` reads as a report, while
`kerykeion natal -s ada | jq -r .sun.sign` works with no extra flag. `-o file`
infers the format from the suffix unless `-f` overrides it.

> Warnings (ephemeris coverage gaps, polar-house fallbacks) always go to
> **stderr**, even with `-f json`, so a payload piped to `jq` stays clean. Pass
> `--warnings-as-errors` to turn them into exit `9` (after the payload prints).

## Subject profiles

A profile is a small JSON "recipe" (perms `0600` — birth data is PII) stored
under `$XDG_CONFIG_HOME/kerykeion/subjects/`. Save once, reuse everywhere with
`-s <name>`:

```console
$ kerykeion subject save ada --name "Ada Lovelace" --date 1990-07-15 --time 10:30 \
      --lat 41.9028 --lng 12.4964 --tz Europe/Rome --offline
$ kerykeion subject list
$ kerykeion subject show ada
$ kerykeion subject verify ada        # round-trips the recipe through the factory
```

The same subject-building flags (`--date`, `--time`, `--lat`, `--lng`, `--tz`,
`--zodiac`, `--houses`, `--points`, `--with`, `--without`, `--set`, …) are
spelled identically by `subject save`, `natal` and `now`.

Profiles are stored as JSON recipes (`0600`, in a `0700` directory — birth data
is personal) and written atomically. A profile is a recipe, never a cached
chart: every read rebuilds the subject, so it cannot go stale across kerykeion
versions or backends. `subject verify` rebuilds one and prints a short summary,
the cheap pre-flight before a long batch.

## Charts

| Command | Chart |
|---------|-------|
| `natal -s ada` | Natal wheel / report |
| `now --lat … --lng … --tz …` | The current moment (transit-style snapshot) |
| `synastry -s ada -S bob` | Two-subject dual wheel |
| `transit -s ada [--to-date …]` | Natal vs a transit moment |
| `composite -s ada -S bob` | Midpoint composite |
| `return -s ada --year 2026 [--type Solar\|Lunar]` | Planetary return dual wheel |
| `progression -s ada --target-year 2026` | Secondary progression |

```console
$ kerykeion natal -s ada -f svg -o /tmp/ada.svg
$ kerykeion synastry -s ada -S bob -f text
$ kerykeion return -s ada --year 2026 --type Solar
```

### Chart appearance

Every chart command exposes the drawer's options, so an SVG is not limited to
the default look. Values are case-insensitive and an unknown one is exit `4`
listing the valid set.

| Flag | Values |
|------|--------|
| `--theme` | `classic`, `dark`, `black-and-white` (`kerykeion info methods` lists the current set) |
| `--chart-language` | `EN FR PT IT CN ES RU TR DE HI` |
| `--style` | `classic`, `modern` (default) |
| `--svg-variant` | `full` (default), `wheel`, `aspect-grid` |
| `--custom-title`, `--padding`, `--transparent-background` | title, spacing, background |
| `--auto-size/--no-auto-size`, `--zodiac-ring/--no-…`, `--diurnality/--no-…` | layout toggles |
| `--aspect-grid-type`, `--house-position-comparison/--no-…`, `--cusp-position-comparison` | dual wheels |
| `--chart-settings file.json` | `colors_settings`, `celestial_points_settings`, `aspects_settings`, `language_pack` |

```console
$ kerykeion natal -s ada -f svg -o /tmp/ada.svg --theme dark --chart-language IT
$ kerykeion natal -s ada -f svg -o /tmp/wheel.svg --svg-variant wheel
$ kerykeion natal -s ada -f svg -o /tmp/themed.svg --chart-settings ./palette.json
```

`--chart-settings` **merges** its mapping sections over the library defaults, so
overriding one colour does not require restating the palette. `--external-view`,
`--degree-indicators` and `--aspect-icons` apply to `--style classic` only; under
the default `modern` style the library ignores them and says so on stderr.

For `-f text`, `--no-aspects` and `--max-aspects N` shape the report.

## Analyses

| Command | What it reports |
|---------|-----------------|
| `aspects -s ada [-S bob] [--declinations]` | aspects within one chart or between two |
| `dominants -s ada [--method …]` | dominant signs, elements, qualities, planets |
| `moon -s ada` | moon phase details |
| `relationship-score -s ada -S bob` | Discepolo relationship score |

```console
$ kerykeion aspects -s ada --aspects trine:6,square
$ kerykeion dominants -s ada --method almuten_figuris
$ kerykeion relationship-score -s ada -S bob
```

`--aspects` takes a name or `name:orb`. Declination aspects use a single `--orb`
instead, and refuse `--aspects`/`--axis-orb-limit`, which have no meaning there.

## Techniques, sky events and time series

Curated subcommand groups cover the analytical techniques and astronomical
events. Each maps to one factory plus a renderer; their `--help` is the
reference.

```console
$ kerykeion technique profections -s ada
$ kerykeion technique firdaria -s ada
$ kerykeion technique zr -s ada --lot fortune
$ kerykeion technique solar-arc -s ada --target-year 2026
$ kerykeion technique house-comparison -s ada -S bob
$ kerykeion technique fixed-stars -s ada --orb 1.5
$ kerykeion sky eclipses --start-year 2025 --count 5
$ kerykeion sky lunations --from 2026-01-01 --to 2026-12-31
$ kerykeion sky sun-times --from 2026-06-21 --lat 41.9 --lng 12.5 --tz Europe/Rome
$ kerykeion sky mundane --from 2026-01-01 --to 2026-03-01
$ kerykeion sky ingresses --from 2026-01-01 --to 2026-12-31 --periods   # sign stays, not events
$ kerykeion sky phenomena -s ada
$ kerykeion sky occultations -s ada --planet Venus
```

Time series (`ephemeris`, `transits`) sample positions over a range. A
**pre-flight sampling check** fails fast (exit `8`) before any heavy computation
when a series would exceed the ceiling (730 days / 8760 hours / 525600 minutes);
`--no-limit` disables both the check and the library's own guard.

```console
$ kerykeion ephemeris --from 2026-01-01 --to 2026-06-30
$ kerykeion transits -s ada --from 2026-01-01 --to 2026-12-31 --events
```

## The `call` dispatcher

`kerykeion call` reaches any public `Factory.method` (or bare function) in
`kerykeion.__all__` without a dedicated command. Subject parameters are bound
from `-s`/`-S`; everything else is `--param key=value` with type coercion.

```console
$ kerykeion call --list                       # every dispatchable target
$ kerykeion call DominantsFactory.from_subject -s ada
$ kerykeion call ProfectionsFactory.from_subject --explain   # params it accepts
$ kerykeion call ProfectionsFactory.from_subject -s ada \
      --param years_before=2 --param years_after=3
```

**Security is an allowlist.** Only names in `kerykeion.__all__`, split on a
single `.`, no private members. `kerykeion call os.system` is refused — `os` is
not in `__all__`:

```console
$ kerykeion call os.system --param cmd=ls
kerykeion: error: 'os' is not in the kerykeion public API; ...
```

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | success |
| `1` | unexpected error (rerun with `--traceback`) |
| `2` | usage error (reserved for Click/Typer) |
| `3` | the `[cli]` extra is missing |
| `4` | invalid input (bad flag, unknown profile, malformed date) |
| `5` | a `KerykeionException` |
| `6` | an ephemeris / backend error |
| `7` | a network error |
| `8` | sampling limit exceeded (series too long) |
| `9` | warnings treated as errors (`--warnings-as-errors`) |
| `130` | interrupted (Ctrl-C) |

Errors are one clean line on stderr by default — never a traceback — with the
right code. `--traceback` shows the full traceback (always shown for exit `1`).

## Discovering values, and checking the install

The CLI validates against the library's own literals — 23 house systems, 48
ayanamsas, 11 perspectives, 76 points — and `info` lists them, read at runtime so
they cannot drift from what the flags accept. With `-f json` it is the source a
script should consult instead of hard-coding tables.

```console
$ kerykeion info literals                 # every enum, by name
$ kerykeion info literals SiderealMode    # one of them
$ kerykeion info houses                   # letters and name aliases
$ kerykeion info points                   # what --points accepts
$ kerykeion info methods                  # per-command strategy names
```

`status` reports the runtime environment; `status --check` judges it — the same
probes plus a real calculation — and exits `6` when the install is genuinely
broken. A widened profile-store mode or a stray `./.env` are warnings, not
failures.

```console
$ kerykeion status --json
$ kerykeion status --check
```

## Global flags

`--version`/`-V`, `--traceback`, `--warnings-as-errors` go before the
subcommand: `kerykeion --traceback natal -s ada`. A bare `kerykeion` prints help
and exits `0`.
