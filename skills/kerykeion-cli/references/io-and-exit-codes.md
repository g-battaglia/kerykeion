# Output, streams, exit codes, and asking the CLI what it accepts

## Which format you get

Resolution order, first match wins:

1. `-f/--format text|json|xml|svg`
2. the suffix of `-o/--output` (`.json`, `.xml`, `.svg`, anything else → text)
3. `$KERYKEION_CLI_FORMAT`
4. stdout is a terminal → `text`; stdout is a pipe or a file → `json`

The fourth rule is why `kerykeion natal -s ada | jq .` works with no flags. In a
script, pass `-f` anyway: it removes the dependence on whether something is
attached to stdout.

```bash
kerykeion subject save ada --name Ada --date 1815-12-10 --time 18:00 \
  --lat 51.5074 --lng -0.1278 --tz Europe/London --offline

kerykeion natal -s ada -f json | jq -r '.sun.sign'
kerykeion natal -s ada -f xml | head -2
kerykeion natal -s ada -f svg -o /tmp/ada.svg
```

`xml` is `to_context()`, the LLM-oriented serialisation: a natal chart is ~5 KB
against ~35 KB of JSON, so it is the shape to read into a context window when
the full model is not needed. It supports a narrower set of models than JSON;
on an unsupported one you get exit 4 naming the supported types rather than a
silent format switch. JSON preserves nested Pydantic models as JSON objects;
project the result with `jq`.

## Streams

The payload is written to **stdout**. Warnings (ephemeris coverage, polar-house
fallbacks) and notes are written to **stderr**, in every format. A JSON payload is therefore always clean to pipe.

`--warnings-as-errors` turns any warning into exit 9 — but only *after* the
payload has been written, so nothing is lost.

To carry the warnings in-band, for a consumer that only captures stdout,
`--envelope` — every command that produces a payload takes it:

```bash
kerykeion natal -s ada -f json --envelope | jq '{backend: .kerykeion.backend, warnings: .warnings | length}'
```

The envelope is `{kerykeion: {version, backend, generated_at}, warnings: [...],
data: ...}`, where `data` is byte-for-byte the payload you would have got
without it. It is JSON-only; asking for it with another format is exit 4.

## Exit codes

| Code | Name | Meaning |
|---|---|---|
| 0 | OK | success |
| 1 | UNEXPECTED | a bug; rerun with `--traceback` to see it |
| 2 | usage | the argument parser rejected the command line |
| 4 | INVALID_INPUT | a flag or value is wrong; the message names it |
| 5 | KERYKEION_ERROR | the library refused the request |
| 6 | EPHEMERIS | outside coverage, or the data files are unusable |
| 7 | NETWORK | GeoNames unreachable |
| 8 | SAMPLING_LIMIT | the series exceeds the ceiling; nothing was computed |
| 9 | WARNINGS_AS_ERRORS | you asked for warnings to be fatal |
| 130 | INTERRUPTED | Ctrl-C |

Branch on the code, never on the text:

```bash
if kerykeion natal -s ada -f json -o /tmp/out.json 2>/tmp/err.log; then
  echo "ok"
else
  case $? in
    4) echo "bad input: $(cat /tmp/err.log)" ;;
    6) echo "date outside ephemeris coverage" ;;
    *) echo "unexpected" ;;
  esac
fi
```

## Ask the CLI, do not guess

`info` reads the library at runtime, so it cannot fall out of step with what the
flags accept. Prefer it to any table copied into a prompt.

```bash
kerykeion info literals -f json | jq 'keys | length'
kerykeion info literals SiderealMode -f json | jq '.SiderealMode | length'
kerykeion info houses -f json | jq '.names.placidus'
kerykeion info points -f json | jq 'keys'
kerykeion info methods -f json | jq '.dominants_method'
```

`info literals` with no argument returns every enum the CLI validates against.
Naming one is case-insensitive, and a typo gets a suggestion.

## Checking the install

`status` reports; `status --check` judges.

```bash
kerykeion status -f json | jq -r '.backend, .calc_mode'
kerykeion status --check -f json | jq -r '.ok, (.checks[] | "\(.status) \(.check)")'
```

`--check` adds the install assertions, a real natal calculation included, and
exits **6** when something is genuinely broken. Warnings — a widened store mode,
a stray `.env` in the working directory — do not fail it. That `.env` check
matters: the ephemeris backend loads `./.env` at import, so a stray file can
silently repoint the data directory or the calc mode.
