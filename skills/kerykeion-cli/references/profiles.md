# Profiles: storing a subject once and reusing it

Nearly every command takes `-s <profile>` instead of a dozen inline flags. A
profile is a small JSON **recipe** — the parameters needed to rebuild the
subject — not a computed chart.

## Where it lives, and why the permissions matter

`$XDG_CONFIG_HOME/kerykeion/subjects/<name>.json` (or `~/.config/kerykeion/...`).
The file is written `0600` inside a `0700` directory: it holds birth date, time
and place, which is personal data. Writes are atomic — a temporary file replaced
into position — so an interrupted save cannot leave a truncated profile.

`-s` also accepts a path, so a profile can live in a repository next to the
script that uses it:

```bash
kerykeion subject save ada --name "Ada Lovelace" \
  --date 1815-12-10 --time 18:00 \
  --lat 51.5074 --lng -0.1278 --tz Europe/London --offline

kerykeion subject path ada
kerykeion subject show ada -f json | jq '.input.tz_str'
```

## Creating one

Dates are `YYYY-MM-DD` and accept negative years for BCE. Times are `HH:MM` or
`HH:MM:SS`. Give `--lat/--lng/--tz` and `--offline` for a subject that never
touches the network; give `--city --nation --online` to have GeoNames resolve
the place.

```bash
kerykeion subject save bob --name Bob --date 1985-06-01 --time 09:30 \
  --lat 45.07 --lng 7.69 --tz Europe/Rome --offline
kerykeion subject list
```

Frame options are stored with the recipe, so every later read uses them:

```bash
kerykeion subject save sid --name Sid --date 1990-03-21 --time 06:00 \
  --lat 19.07 --lng 72.88 --tz Asia/Kolkata --offline \
  --zodiac Sidereal --sidereal-mode LAHIRI --houses whole-sign
```

## Precedence

From lowest to highest: the library's defaults → the stored recipe → the inline
flags. So a stored subject can be re-read at another place without editing it:

```bash
kerykeion sky sun-times -s ada --from 2025-06-01 \
  --lat 40.71 --lng -74.01 --tz America/New_York
```

`--online` and `--offline` are mutually exclusive (exit 4). `--no-online` exists
and means the same as `--offline`; it is there to override a profile that was
saved with `online: true`.

## `--set` for the long tail

Options with no dedicated flag go through `--set key=value`, whitelisted against
the recipe shape so a typo is rejected rather than silently dropped:

```bash
kerykeion subject save adv --name Adv --date 1990-01-01 --time 12:00 \
  --lat 45.0 --lng 9.0 --tz Europe/Rome --offline \
  --set houses_system_identifier=W --set active_points=Sun,Moon,Mercury
```

Underscore-prefixed (private) parameters are refused.

## `--snapshot`: cache the computed subject

By default a profile is recomputed on every read. `--snapshot` also stores the
computed subject, and later reads reuse it instead of recomputing:

```bash
kerykeion subject save fast --name Fast --date 1990-01-01 --time 12:00 \
  --lat 45.0 --lng 9.0 --tz Europe/Rome --offline --snapshot
kerykeion subject verify fast -f json | jq -r '.snapshot'
```

`verify` always recomputes from the recipe — that is what it is for — and reports
how the stored copy compares:

| state | meaning |
|---|---|
| `absent` | no snapshot stored |
| `matches` | identical to a fresh computation |
| `stale` | written by another kerykeion version or backend — already being ignored |
| `drifted` | current provenance, but different: re-save it |

A snapshot is **ignored automatically** when the kerykeion version or the
ephemeris backend differs from the one that wrote it, with a note on stderr,
because reusing it would answer with numbers this installation would not
compute. Any inline override also bypasses it: the override describes something
the snapshot does not.

## Checking a profile still builds

```bash
kerykeion subject verify ada -f json | jq '{ok, sun: .sun_sign, snapshot}'
```

`verify` is the cheap pre-flight for a batch: it surfaces a malformed recipe, a
bad timezone or an ephemeris gap before a long run starts.
