# The command tree

Global flags, before the command: `--version`, `--traceback` (show the traceback
on an unexpected error), `--warnings-as-errors` (exit 9 when any warning fires).

Every command that produces output takes `-f/--format` and `-o/--output`.

All examples below assume two stored profiles:

```bash
kerykeion subject save ada --name Ada --date 1815-12-10 --time 18:00 \
  --lat 51.5074 --lng -0.1278 --tz Europe/London --offline
kerykeion subject save bob --name Bob --date 1985-06-01 --time 09:30 \
  --lat 45.07 --lng 7.69 --tz Europe/Rome --offline
```

## Charts

| Command | Needs | Notes |
|---|---|---|
| `natal` | `-s` or the inline subject flags | the only command with the full inline flag set |
| `now` | a location | a chart for the current moment |
| `synastry` | `-s` and `-S` | dual wheel |
| `transit` | `-s` | defaults to now at the natal place; `--to-date` **and** `--to-time` for a specific moment |
| `composite` | `-s` and `-S` | midpoint composite |
| `return` | `-s`, `--year` | `--type Solar\|Lunar` |
| `progression` | `-s`, `--target-year` | secondary progression |

```bash
kerykeion natal -s ada -f json | jq -r '.sun.sign'
kerykeion synastry -s ada -S bob -f json | jq '.aspects | length'
kerykeion transit -s ada --to-date 2025-06-01 --to-time 12:00 -f json | jq -r '.chart_type'
kerykeion return -s ada --type Solar --year 2025 -f json | jq -r '.chart_type'
kerykeion progression -s ada --target-year 2026 -f json | jq -r '.chart_type'
```

A **relocated** transit or return needs `--lat`, `--lng` and `--tz` together —
two of the three is exit 4, because the natal timezone at new coordinates is a
multi-hour error in the houses and Ascendant.

## Analyses

```bash
kerykeion aspects -s ada -f json | jq '.aspects | length'
kerykeion aspects -s ada -S bob -f json | jq '.aspects | length'
kerykeion aspects -s ada --declinations --orb 1.0 -f json | jq 'length'
kerykeion dominants -s ada --method almuten_figuris -f json | jq 'keys | length'
kerykeion moon -s ada -f json | jq -r '.moon.phase_name'
kerykeion relationship-score -s ada -S bob -f json | jq -r '.score_description'
```

`--aspects` takes names or `name:orb` pairs (`--aspects trine:6,square`).
Declination aspects use a single `--orb` instead and refuse `--aspects` and
`--axis-orb-limit`, which have no meaning there.

## `technique <sub>` — analytical techniques on a stored subject

`profections`, `firdaria`, `zr`, `receptions`, `horary`, `midpoints`,
`directions`, `acg`, `heliacal`, `nodes`, `relocate`, `house-comparison`,
`solar-arc`, `fixed-stars`.

```bash
kerykeion technique profections -s ada -f json | jq -r '.current.house'
kerykeion technique zr -s ada --lot fortune --levels 2 -f json | jq 'keys | length'
kerykeion technique solar-arc -s ada --target-year 2026 -f json | jq 'keys | length'
kerykeion technique fixed-stars -s ada --orb 1.5 -f json | jq 'length'
kerykeion technique house-comparison -s ada -S bob -f json | jq 'keys | length'
kerykeion technique acg -s ada -f json | jq 'keys | length'
```

Enum-style flags (`--lot`, `--rate`, `--method`, `--type`) are case-insensitive.
`kerykeion info methods` lists what each accepts.

## `sky <sub>` — events, with or without a subject

Moment commands (`sun-times`, `hours`) need a place: `-s` or `--lat/--lng/--tz`.
Range commands (`lunations`, `ingresses`, `stations`, `mundane`) need
`--from/--to` and no place. `voc` does both; `eclipses` takes a year and an
optional place; `phenomena` and `occultations` take `-s`.

```bash
kerykeion sky sun-times -s ada --from 2025-06-01 -f json | jq -r '.sunrise'
kerykeion sky hours -s ada --from 2025-06-01T12:00 -f json | jq -r '.day_ruler'
kerykeion sky lunations --from 2025-01-01 --to 2025-03-01 -f json | jq 'length'
kerykeion sky ingresses --from 2025-01-01 --to 2025-06-01 -f json | jq 'length'
kerykeion sky stations --from 2025-01-01 --to 2025-06-01 -f json | jq 'length'
kerykeion sky ingresses --from 2025-01-01 --to 2025-06-01 --periods -f json | jq '.periods | length'
kerykeion sky stations --from 2025-01-01 --to 2025-06-01 --periods -f json | jq '.periods | length'
kerykeion sky mundane --from 2025-01-01 --to 2025-02-01 -f json | jq 'length'
kerykeion sky eclipses --start-year 2025 --count 2 -f json | jq 'length'
kerykeion sky voc --from 2025-01-01 --to 2025-01-10 --tz UTC -f json | jq 'length'
kerykeion sky phenomena -s ada -f json | jq 'keys | length'
kerykeion sky occultations -s ada --planet Venus --count 2 -f json | jq 'length'
```

`--periods` on `ingresses` and `stations` reports the spans instead of the
events — contiguous sign stays, or retrograde spans — clipped to the range, each
flagged `start_clipped`/`end_clipped` when it began before or outlives it.

`voc` ranges are UTC: pass `--tz` (or a profile) so naive bounds are interpreted
in that zone. `occultations` searches forward from the subject's moment and
requires `--planet` — the Moon is the occulter, not the occulted body.

## Time series

```bash
kerykeion ephemeris --from 2025-01-01 --to 2025-01-05 --step-type days --step 1 \
  --lat 45.0 --lng 9.0 --tz Europe/Rome -f json | jq 'length'
kerykeion transits -s ada --from 2025-01-01 --to 2025-01-05 --step-type days -f json | jq 'length'
```

Both refuse to start when the requested sampling exceeds the ceiling (exit 8);
`--no-limit` removes both the pre-check and the library's own guard.
`transits --events` collapses the series into applying→exact→separating events,
and `--refine` (which sharpens the exact moment) requires `--events`.

## Subjects, info, diagnostics

`subject save|show|list|path|verify`, `info literals|points|stars|houses|methods`,
`status [--check]`, and `call`. See
[profiles.md](profiles.md), [io-and-exit-codes.md](io-and-exit-codes.md) and
[call-dispatcher.md](call-dispatcher.md).
