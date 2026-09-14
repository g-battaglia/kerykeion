# Rendering: SVG appearance and report shaping

These flags are available on every chart-producing command — `natal`, `now`,
`synastry`, `transit`, `composite`, `return`, `progression`, and
`technique relocate`.

```bash
kerykeion subject save ada --name Ada --date 1815-12-10 --time 18:00 \
  --lat 51.5074 --lng -0.1278 --tz Europe/London --offline
```

## SVG appearance

| Flag | Values / effect |
|---|---|
| `--theme` | `classic`, `dark`, `black-and-white` (`kerykeion info methods` lists the current set) |
| `--chart-language` | `EN FR PT IT CN ES RU TR DE HI` |
| `--style` | `classic` or `modern` (default) |
| `--custom-title` | replaces the title line |
| `--padding` | outer padding in SVG units |
| `--transparent-background` | omit the background rectangle |
| `--auto-size` / `--no-auto-size` | fit the viewBox to the content (default on) |
| `--zodiac-ring` / `--no-zodiac-ring` | the zodiac background ring (default on) |
| `--diurnality` / `--no-diurnality` | day/night sect marking (default on) |
| `--house-position-comparison` / `--no-...` | dual wheels only (default on) |
| `--cusp-position-comparison` | dual wheels only |
| `--aspect-grid-type` | `list` or `table`, dual wheels only |
| `--svg-variant` | `full` (default), `wheel`, `aspect-grid` |

```bash
kerykeion natal -s ada -f svg -o /tmp/dark.svg --theme dark --chart-language IT
kerykeion natal -s ada -f svg -o /tmp/wheel.svg --svg-variant wheel
kerykeion natal -s ada -f svg -o /tmp/plain.svg --transparent-background --no-zodiac-ring
```

Values are case-insensitive (`--theme DARK` works) and an unknown one is exit 4
listing the valid set. `kerykeion info methods -f json` reports the same lists.

### Classic-style-only flags

`--external-view`, `--degree-indicators`/`--no-degree-indicators` and
`--aspect-icons`/`--no-aspect-icons` apply to `--style classic` only. Under the
default `modern` style the library ignores them and says so on stderr — so they
are not silently dropped, but they will not do anything either.

```bash
kerykeion natal -s ada -f svg -o /tmp/classic.svg --style classic --no-degree-indicators
```

## Structural settings

Palettes, point tables, aspect tables and language packs are too large for
flags. `--chart-settings` takes a JSON file with any of `colors_settings`,
`celestial_points_settings`, `aspects_settings`, `language_pack`:

```bash
printf '{"colors_settings": {"paper_0": "#101010"}}' > /tmp/palette.json
kerykeion natal -s ada -f svg -o /tmp/themed.svg --chart-settings /tmp/palette.json
```

Mapping sections are **merged over the library defaults**, so overriding a
single colour is enough; you never have to restate the whole palette. Unknown
top-level keys are an error naming the valid ones. List-shaped sections (the
point and aspect tables) replace rather than merge — a partial list can only
mean "use exactly these".

## Text report shaping

For `-f text`, on the same commands:

```bash
kerykeion synastry -s ada -S ada -f text --no-aspects | tail -3
kerykeion synastry -s ada -S ada -f text --max-aspects 5 | tail -3
```

`--no-aspects` drops the aspects section; `--max-aspects N` keeps the N tightest.
They act where a report has an aspects section — the chart-data models — so on a
plain subject report there is nothing for them to trim.
