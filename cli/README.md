# kerykeion-cli

**Astrology command line for agents and humans.**

Calculate astrology charts, inspect results and generate SVGs from the terminal, without writing Python integration code. `kerykeion-cli` runs the [Kerykeion](https://www.kerykeion.net) library locally, with readable reports and command help for people, plus structured output, command discovery and explicit error codes for AI agents and automation.

A dedicated **[CLI Agent Skill](https://github.com/g-battaglia/kerykeion/tree/main/skills/kerykeion-cli)** teaches agents which commands to use, how to supply birth data, how to interpret outputs and how to handle errors. Install the skill alongside the CLI for agent-driven use.

## Install

Requires **Python 3.12+**. Choose one installation method:

```bash
# Isolated tool, available on PATH
uv tool install "kerykeion-cli"

# Or install the library and CLI in your Python environment
pip install "kerykeion[cli]"
```

The CLI pins the matching `kerykeion` release exactly and adds no dependencies beyond the library itself. A plain `pip install kerykeion` installs no shell command. `python -m kerykeion_cli` is the alternative entry point when the package is installed in the active Python environment.

## Install the AI Agent Skill

The [CLI Agent Skill](https://github.com/g-battaglia/kerykeion/tree/main/skills/kerykeion-cli) is a separate folder in the repository, not part of the Python package. It follows the [Agent Skills](https://agentskills.io/) format and works with compatible coding agents.

```bash
git clone --depth 1 --branch main https://github.com/g-battaglia/kerykeion.git
cd kerykeion

# Claude Code: replace /path/to/project with your target project
mkdir -p /path/to/project/.claude/skills
cp -r skills/kerykeion-cli /path/to/project/.claude/skills/

# Codex and agents using .agents/skills
mkdir -p /path/to/project/.agents/skills
cp -r skills/kerykeion-cli /path/to/project/.agents/skills/
```

For other tools, copy `skills/kerykeion-cli` into the tool's supported skills directory. The skill includes command routing, saved-profile rules, output and exit-code contracts, factory discovery, and executable recipes. For agents writing Python code instead, use the separate [library skill](https://github.com/g-battaglia/kerykeion/tree/main/skills/kerykeion).

An example task for an agent with the CLI skill loaded:

> Use kerykeion-cli to calculate an offline natal chart for 15 July 1990 at 18:00 in London, using latitude 51.5074, longitude -0.1278 and Europe/London. Save a Modern SVG with the Dark theme and a JSON result including warnings. Report any coverage limitations instead of filling in missing data.

## First chart

Save the birth data once, then reuse the profile:

```bash
kerykeion status --check -f json

kerykeion subject save example --name "Example Person" --date 1990-07-15 --time 18:00 \
  --lat 51.5074 --lng -0.1278 --tz Europe/London --offline

kerykeion natal -s example -f text
kerykeion natal -s example -f json --envelope -o example.json
kerykeion natal -s example -f svg -o example.svg --theme dark
kerykeion natal -s example -f xml -o example.xml
```

Modern is the default chart style. SVG output is suitable for display or embedding; JSON preserves the calculation data; XML supplies structured chart context for an LLM. Format support depends on the command and result type. Unsupported formats are rejected rather than silently substituted.

## An agent workflow: discover, calculate, inspect

Ask the installed CLI what it supports instead of guessing parameter names:

```bash
kerykeion --help
kerykeion info literals SiderealMode -f json
kerykeion call --list -f json
kerykeion call ProfectionsFactory.from_subject --explain -f json
kerykeion call ProfectionsFactory.from_subject -s example -f json
```

Prefer the curated commands for common tasks. Use `call` when a public factory or parameter is not covered by them. The dispatcher accepts public library targets, refuses private or arbitrary Python names, and reports unsupported parameter types. It is not an arbitrary-code execution interface or a security sandbox.

## What you can calculate

| Area | Capabilities |
| --- | --- |
| Charts | Natal, synastry, transit, returns, midpoint composite and progressions |

> **Davison note:** the library's `CompositeSubjectFactory.get_davison_composite_subject_model`
> has no dedicated `composite --davison` command. The `composite` command is the midpoint
> composite; reach Davison from the terminal with
> `kerykeion call CompositeSubjectFactory.get_davison_composite_subject_model -s ada -S bob`.
| Analysis | Aspects, dominants, relationship scores, Moon context and midpoints |
| Predictive and locational | Primary directions, solar arc, secondary progressions and astrocartography |
| Traditional | Profections, firdaria, zodiacal releasing, receptions and horary indicators |
| Sky events | Eclipses, lunations, ingresses, stations, occultations and heliacal events |
| Time series | Ephemeris samples and transit timelines, with optional subjects and dignities |
| Daily calculations | Sun times, planetary hours and void-of-course Moon |

For example, reuse the profile above to build a transit timeline, or query sky events independently:

```bash
kerykeion transits -s example --from 2026-01-01 --to 2026-01-02 \
  --include-subjects --calculate-dignities -f json -o transits.json

kerykeion sky lunations --from 2026-01-01 --to 2026-02-01 -f json
kerykeion sky ingresses --help
kerykeion sky stations --help
```

## Output contracts for agents and scripts

Output defaults to text on a terminal and JSON in a pipe. In automation, specify `-f` explicitly so the result does not depend on terminal detection. Use `-o` to write a file.

Payloads go to **stdout**; warnings and diagnostics go to **stderr**. With `-f json --envelope`, the output contains:

| Field | Content |
| --- | --- |
| `kerykeion` | Version, backend and generation timestamp |
| `warnings` | Structured warnings, including coverage and fallback information |
| `data` | The calculation payload |

Inspect the result with `jq` (installed separately):

```bash
kerykeion natal -s example -f json --envelope \
  | jq '{backend: .kerykeion.backend, warnings: .warnings, sun: .data.sun.sign}'
```

`--envelope` is JSON-only. `--warnings-as-errors` returns exit 9 if warnings occur, **after writing the payload**. Do not treat a written file as proof of success without checking the exit code.

| Exit code | Meaning |
| --- | --- |
| 0 | Success |
| 1 | Unexpected error; use `--traceback` for diagnostics |
| 2 | Command-line syntax rejected by the parser |
| 4 | Invalid input or unsupported output format |
| 5 | Library calculation error |
| 6 | Ephemeris coverage or data-file problem |
| 7 | Network error |
| 8 | Sampling limit exceeded |
| 9 | Warnings treated as errors |
| 130 | Interrupted |

## Input accuracy, privacy and coverage

Always supply explicit coordinates, an IANA timezone and `--offline` when location lookup is unnecessary. Do not let an agent invent an unknown birth time, timezone or coordinate. Ambiguous local times require an explicit choice; inspect command help before proceeding.

Saved profiles contain personal birth data. Profile files are written with `0600` permissions. Keep real profiles, exported charts and JSON results out of public repositories and logs.

Calculations use local ephemeris data. The default libephemeris tier covers **1850 to 2150, upper bound exclusive**. Wider dates require additional data tiers, and optional bodies may have narrower coverage. Inspect warnings and provenance before using a result. See [backend configuration](https://www.kerykeion.net/python-library/docs/v6/ephemeris_backend).

## Commercial projects

For commercial projects, use the hosted **[Astrologer API](https://www.kerykeion.net/content/astrologer-api/)**. CLI access through Astrologer API is coming soon. The package documented here is the local Kerykeion CLI, not a client for that hosted service.

The local library and CLI are distributed under **AGPL-3.0**. The API recommendation does not change the rights and obligations of that license. See [licensing](https://github.com/g-battaglia/kerykeion/blob/main/LICENSING.md).

## Documentation and man page

- [CLI reference](https://www.kerykeion.net/python-library/docs/v6/cli/)
- [CLI Agent Skill and tested recipes](https://github.com/g-battaglia/kerykeion/tree/main/skills/kerykeion-cli)
- [Python library README](https://github.com/g-battaglia/kerykeion/blob/main/README.md)

The wheel includes a generated `kerykeion(1)` man page. In a prefix whose `share/man` directory is indexed, use `man kerykeion`. For an isolated `uv tool` installation:

```bash
man -M "$(uv tool dir)/kerykeion-cli/share/man" kerykeion
```
