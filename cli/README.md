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
pip install --pre "kerykeion[cli]==6.0.0rc1"  # the library plus this package
# or, as a standalone tool:
uv tool install --prerelease=allow "kerykeion-cli==6.0.0rc1"
```

Python 3.12+. `pip install kerykeion` alone installs the library without the
command; `python -m kerykeion_cli` reaches the same entry point. This is the
first v6 release candidate; the CLI pins the matching library version exactly.

## Use

```bash
kerykeion subject save ada --name "Example Person" --date 1990-07-15 --time 18:00 \
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
value the flags accept, read from the library at runtime. A Unix man page,
`kerykeion(1)`, ships in the wheel: after a `pip install` into a prefix whose
`share/man` is indexed (a system Python, Homebrew), `man kerykeion` works with
no further step. Isolated installs keep the page inside their own prefix, so
add it to the search path once:

```bash
man -M "$(uv tool dir)/kerykeion-cli/share/man" kerykeion   # a uv tool install
# or, in the shell profile:
#   export MANPATH="$HOME/.local/share/uv/tools/kerykeion-cli/share/man:$MANPATH"
```

## Documentation

- CLI reference: <https://www.kerykeion.net/content/docs/cli/>
- Library: <https://www.kerykeion.net>
- Agent skill, for AI coding agents: `skills/kerykeion-cli/` in the
  [repository](https://github.com/g-battaglia/kerykeion)

## License

AGPL-3.0, the same as the library it drives.
