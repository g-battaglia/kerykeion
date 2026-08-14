# `kerykeion call` — reaching any public factory

The curated commands cover the common work. `call` covers **everything else**:
it dispatches to any name in `kerykeion.__all__`, so no library capability is
out of reach from a shell.

## Safety model

The target must be a name in `kerykeion.__all__`, split on **one** `.` only.
Private members are refused, models and exceptions are not dispatchable, and
lookup uses `inspect.getattr_static`, so no descriptor runs during resolution.
`kerykeion call os.system --param cmd=ls` fails because `os` is not part of the
public API — that is the test this command exists to pass.

## Discovering targets

```bash
kerykeion call --list --json | jq -r '.[0:3][] | .owner'
kerykeion call ProfectionsFactory.from_subject --explain --json
```

`--explain` classifies every parameter, which is what tells you how to pass it:

| class | meaning | how to pass it |
|---|---|---|
| `cli` | a scalar, enum, list or date | `--param name=value` |
| `subject` | an `AstrologicalSubjectModel` | `-s <profile>` (and `-S` for a second) |
| `json-only` | a mapping or a nested model | `--param name='{"k": 1}'`, or a JSON file path for a model |
| `unsupported` | a Protocol or similar | not reachable; use a curated command |

## Binding subjects and parameters

```bash
kerykeion subject save ada --name Ada --date 1815-12-10 --time 18:00 \
  --lat 51.5074 --lng -0.1278 --tz Europe/London --offline

kerykeion call DominantsFactory.from_subject -s ada -f json | jq 'keys | length'
kerykeion call MidpointFactory.compute -s ada --param active_points=Sun,Moon -f json | jq 'length'
```

`--param` coercion follows the parameter's annotation:

- scalars: `int`, `float`, `bool` (`true/yes/1` and `false/no/0`), `str`
- `none` / `null` → `None`
- `datetime` / `date`: ISO
- `Literal`: membership, case-checked, with a suggestion on a near miss
- lists **and abstract sequences** (`list[str]`, `Sequence[str]`): comma-separated
- mappings: JSON, e.g. `--param custom_weights='{"Sun": 1.5}'`
- a Pydantic model parameter: the path to a JSON file holding it

An unknown `--param` key is rejected up front, so a typo cannot silently run the
factory with defaults.

## Two shapes of factory

Most are static or classmethods. Some need construction first
(`PlanetaryReturnFactory`, `TransitsTimeRangeFactory`, `RelationshipScoreFactory`,
`HouseComparisonFactory`, `CompositeSubjectFactory`, `EphemerisDataFactory`,
`HeliacalFactory`, `OccultationFactory`). For those, the constructor and method
parameters share one flat namespace — `--explain` shows the union, and you pass
them all the same way.

## When to prefer a curated command

`call` gives no `--help` for the underlying parameters and no domain-specific
validation. If a curated command exists for the job, it will give better errors
and a shorter command line. `call` is for the tail: a method with no command, or
a parameter a command does not expose.
