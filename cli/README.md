# kerykeion-cli

The [Kerykeion](https://www.kerykeion.net) astrology library from the terminal.
`pip install "kerykeion[cli]"` gives you the **`kerykeion`** command: natal,
synastry, transit, composite, return and progression charts as **text reports**,
**JSON**, **AI-ready XML context** or **SVG wheels**; aspects, dominants, moon
phase, relationship score; profections, firdaria, zodiacal releasing, horary,
primary directions, solar arc, astrocartography; eclipses, lunations, ingresses,
stations, void-of-course Moon, sun times, planetary hours; ephemeris and transit
time series — plus a guarded `call` that reaches any public factory.

- **Standard library only** (argparse): this package adds no dependency beyond
  the library itself
- **Local and offline**: the same in-process engine as the Python API, no key
- **Text on a terminal, JSON in a pipe**; `-f text|json|xml|svg`, `-o file`
- **Payload on stdout, warnings on stderr** — pipes stay clean
- **Exit codes are the contract**: 0 ok, 4 invalid input, 5 kerykeion, 6
  ephemeris, 7 network, 8 sampling ceiling, 9 warnings-as-errors
- **Saved subject profiles** (`kerykeion subject save ada …`, then `-s ada`),
  written `0600` because birth data is personal

## Install

```bash
pip install "kerykeion[cli]"          # the library plus this package
# or, as a standalone tool:
uv tool install kerykeion-cli         # pipx install kerykeion-cli
```

Python 3.12+. `pip install kerykeion` alone installs the library without the
command; `python -m kerykeion_cli` reaches the same entry point.

## Use

```bash
kerykeion subject save ada --name "Ada Lovelace" --date 1815-12-10 --time 18:00 \
  --lat 51.5074 --lng -0.1278 --tz Europe/London --offline

kerykeion natal -s ada                        # ASCII report on a terminal
kerykeion natal -s ada | jq -r .sun.sign      # JSON in a pipe, no extra flag
kerykeion natal -s ada -f svg -o ada.svg --theme dark
kerykeion sky lunations --from 2026-01-01 --to 2026-12-31
kerykeion transits -s ada --from 2026-01-01 --to 2026-01-02 \
  --include-subjects --calculate-dignities -f json
kerykeion status --check                      # judge the install (exit 6 if broken)
```

`kerykeion --help` lists every command; `kerykeion info literals` lists every
value the flags accept, read from the library at runtime.

## Documentation

- CLI reference: <https://www.kerykeion.net/content/docs/cli/>
- Library: <https://www.kerykeion.net>
- Agent skill, for AI coding agents: `skills/kerykeion-cli/` in the
  [repository](https://github.com/g-battaglia/kerykeion)

## License

AGPL-3.0, the same as the library it drives.
