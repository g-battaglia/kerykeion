# Recipes

Task-shaped examples. All of them assume a stored profile.

```bash
kerykeion subject save ada --name "Ada Lovelace" --date 1815-12-10 --time 18:00 \
  --lat 51.5074 --lng -0.1278 --tz Europe/London --offline
```

## Pull one value out of a chart

```bash
kerykeion natal -s ada -f json | jq -r '.sun.sign, .moon.sign, .first_house.sign'
```

## Batch a directory of profiles

`subject list` prints one name per line in text mode, a JSON array in a pipe.

```bash
for name in $(kerykeion subject list -f text); do
  kerykeion natal -s "$name" -f json -o "./out/$name.json" || echo "failed: $name" >&2
done
ls ./out/ada.json
```

## Verify before a long run

`verify` rebuilds the recipe and surfaces a bad timezone or an ephemeris gap
cheaply, before an expensive series starts.

```bash
kerykeion subject verify ada -f json | jq -e '.ok' > /dev/null && echo "recipe is sound"
```

## A year of transits, as events

```bash
kerykeion transits -s ada --from 2025-01-01 --to 2025-02-01 \
  --step-type days --step 1 --events -f json | jq 'length'
```

If this exits 8, the requested sampling exceeds the ceiling: widen `--step`,
narrow the range, or pass `--no-limit` on purpose.

## An SVG for a web page

```bash
kerykeion natal -s ada -f svg -o ./out/ada-dark.svg \
  --theme dark --transparent-background --svg-variant wheel
head -c 40 ./out/ada-dark.svg
```

## Machine-readable errors in CI

Capture the payload and branch on the code; warnings stay on stderr and never
corrupt the JSON.

```bash
set +e
kerykeion natal -s ada -f json -o ./out/ci.json 2>./out/ci.err
code=$?
set -e
echo "exit=$code warnings=$(wc -l < ./out/ci.err)"
```

For a consumer that only reads stdout, fold the warnings into the payload:

```bash
kerykeion natal -s ada -f json --envelope | jq '.warnings | length'
```

## Reuse one subject across many commands

```bash
kerykeion subject save fast --name Fast --date 1990-01-01 --time 12:00 \
  --lat 45.0 --lng 9.0 --tz Europe/Rome --offline
kerykeion natal -s fast -f json | jq -r '.name'
kerykeion aspects -s fast -f json | jq '.aspects | length'
```

Every read rebuilds the subject from the recipe, so the profile never goes
stale across kerykeion versions or backends.

## Reach something with no curated command

```bash
kerykeion call --list -f json | jq -r '.[] | select(.owner | test("Factory$")) | .owner' | head -3
kerykeion call DominantsFactory.from_subject --explain -f json | jq -r '.[].name' | head -3
kerykeion call DominantsFactory.from_subject -s ada -f json | jq 'keys | length'
```
