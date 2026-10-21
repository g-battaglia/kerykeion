#!/bin/bash
# Sequential, memory-bounded validation. Preserve each completed exit status.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
OUT="$ROOT/validation_output"
REFERENCE="$OUT/reference"
V3_PYTHON="${V3_PYTHON:-$ROOT/../../.venv/bin/python}"
FAILED=0
mkdir -p "$OUT"
if [ ! -f "$REFERENCE/pyproject.toml" ]; then
    mkdir -p "$REFERENCE"
    git archive b81527d6 | tar -x -C "$REFERENCE" || exit 1
fi

run_check() {
    local name="$1"
    shift
    echo "Starting $name at $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    /usr/bin/time -p "$@" > "$OUT/$name.log" 2>&1
    local result=$?
    printf '%s\n' "$result" > "$OUT/$name.exit"
    if [ "$result" -ne 0 ]; then FAILED=1; fi
    echo "Finished $name: exit $result at $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
}

# Read-only views of existing datasets. Never download or replace data.
.venv/bin/python - <<'PY'
from pathlib import Path
source = Path.home() / '.libephemeris'
for tier, groups in [('base', ['base']), ('medium', ['base', 'medium'])]:
    view = Path('validation_output') / f'data-{tier}'
    (view / 'leb').mkdir(parents=True, exist_ok=True)
    for group in groups:
        for path in (source / 'leb').glob(f'{group}_*.leb2'):
            dest = view / 'leb' / path.name
            if not dest.exists():
                dest.symlink_to(path)
    for name in ['de440s.bsp', 'de440.bsp']:
        dest = view / name
        if (source / name).exists() and not dest.exists():
            dest.symlink_to(source / name)
PY
if [ $? -ne 0 ]; then exit 1; fi

run_check native-build env CARGO_TARGET_DIR="$ROOT/.rust-target" \
    cargo build --manifest-path benchmarks/native/Cargo.toml --release --locked
run_check benchmarks .venv/bin/python scripts/benchmark_backends.py \
    --reference-python "$V3_PYTHON" --reference-root "$REFERENCE" \
    --data-dir "$OUT/data-base"

for i in 1 2 3; do
    run_check "native-benchmark-$i" "$ROOT/.rust-target/release/kerykeion-rusty-leb-benchmark" \
        "$HOME/.libephemeris/leb/base_core.leb2"
    run_check "native-composite-benchmark-$i" "$ROOT/.rust-target/release/kerykeion-rusty-leb-benchmark" \
        "$HOME/.libephemeris/leb/base_core.leb2" "$HOME/.libephemeris/leb/base_apogee.leb2" \
        "$HOME/.libephemeris/leb/base_asteroids.leb2" "$HOME/.libephemeris/leb/base_exotics.leb2"
done

run_check rust-full env LIBEPHEMERIS_PRECISION=extended KERYKEION_BACKEND=libephemeris \
    KERYKEION_EPHE_PATH="$HOME/.kerykeion/sweph" \
    "$ROOT/.venv/bin/python" -m pytest tests/ --tier=extended -n 2 --tb=short \
    --durations=50 --junitxml="$OUT/rust-full.xml"

# Exercise the medium-range boundaries that an extended run legitimately skips.
.venv/bin/python - <<'PY'
from pathlib import Path
import xml.etree.ElementTree as E
nodes = []
for case in E.parse('validation_output/rust-full.xml').getroot().iter('testcase'):
    skip = case.find('skipped')
    if skip is None or 'medium' not in skip.get('message', '').lower():
        continue
    parts = case.get('classname').split('.')
    index = next(i for i, part in enumerate(parts) if part.startswith('test_'))
    path = '/'.join(parts[:index + 1]) + '.py'
    nodes.append('::'.join([path, *parts[index + 1:], case.get('name').split('@')[0]]))
Path('validation_output/medium-boundary-nodeids.txt').write_text('\n'.join(nodes) + '\n')
PY
if [ $? -ne 0 ]; then exit 1; fi
run_check rust-medium-boundaries env LIBEPHEMERIS_PRECISION=medium \
    LIBEPHEMERIS_DATA_DIR="$OUT/data-medium" KERYKEION_BACKEND=libephemeris \
    "$ROOT/.venv/bin/python" -m pytest -n 0 --tb=short \
    --junitxml="$OUT/rust-medium-boundaries.xml" $(tr '\n' ' ' < "$OUT/medium-boundary-nodeids.txt")

# A green consumer suite alone does not cover historical live-anchor routing.
run_check numeric-comparison "$ROOT/.venv/bin/python" scripts/compare_rust_v3.py \
    --check --reference-python "$V3_PYTHON" --reference-root "$REFERENCE" \
    --output "$OUT/numeric-comparison.json"

cd "$REFERENCE" || exit 1
run_check python-v3-full env PYTHONPATH="$REFERENCE:$REFERENCE/cli" \
    LIBEPHEMERIS_PRECISION=extended KERYKEION_BACKEND=libephemeris \
    KERYKEION_EPHE_PATH="$HOME/.kerykeion/sweph" \
    "$V3_PYTHON" -m pytest tests/ --tier=extended -n 2 --tb=short \
    --durations=50 --junitxml="$OUT/python-v3-full.xml"
run_check python-v3-medium-boundaries env PYTHONPATH="$REFERENCE:$REFERENCE/cli" \
    LIBEPHEMERIS_PRECISION=medium LIBEPHEMERIS_DATA_DIR="$OUT/data-medium" \
    KERYKEION_BACKEND=libephemeris "$V3_PYTHON" -m pytest -n 0 --tb=short \
    --junitxml="$OUT/python-v3-medium-boundaries.xml" $(tr '\n' ' ' < "$OUT/medium-boundary-nodeids.txt")
exit "$FAILED"
