#!/usr/bin/env python3
"""Generate a separate, audited LibEphemeris 4.0.0b1 fixture set.

Legacy fixtures are read-only. Existing v4 sets are also read-only: --check
recomputes and compares them in a temporary directory without replacing them.
Requires the unchanged local v3 environment for an independent house-geometry
control; its public houses_armc API is used, never Swiss source or data.
"""

from __future__ import annotations

import argparse
from contextlib import redirect_stdout
import hashlib
from io import StringIO
import importlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from kerykeion.ephemeris_backend import BACKEND_NAME, ephe
from kerykeion.utilities.core import HOUSE_FIELD_NAMES
from tests.core.conftest import POSITION_TOLERANCE
from tests.data.reference_recipes import _create_arabic_subject, create_subject_from_id, print_ancient_rome_report
from tests.data.compare_svg_lines import DEFAULT_ABS_TOL, DEFAULT_REL_TOL, compare_svg_lines
from tests.data.expected_arabic_parts import EXPECTED_ARABIC_PARTS
from tests.data.expected_positions import EXPECTED_POSITIONS
from tests.data.golden_drive import (
    GOLDEN_TEST_MODULES,
    SVG_DIR,
    baselines_out_of_this_runs_reach,
)
from tests.data.model_oracle import angular_distance, orientation
from tests.data.regeneration_guard import require_library_from_this_checkout

MODEL = "libephemeris-4.0.0b1"
DESTINATION = ROOT / "tests/data/model_baselines" / MODEL


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def legacy_inventory() -> dict[str, str]:
    paths = [ROOT / "tests/data/expected_positions.py", ROOT / "tests/data/expected_arabic_parts.py"]
    paths += sorted(SVG_DIR.glob("*.svg"))
    paths += sorted((ROOT / "tests/fixtures").glob("*.txt"))
    return {path.relative_to(ROOT).as_posix(): digest(path) for path in paths}


def input_inventory() -> list[dict]:
    """Record actual retained images by filename/hash, not machine-specific paths."""
    paths = sorted({Path(item["path"]) for item in ephe.get_leb_inventory()["files"]})
    assert paths and all(path.is_file() for path in paths), "full-range file inputs are required"
    assert len({path.name for path in paths}) == len(paths)
    return [{"name": path.name, "bytes": path.stat().st_size, "sha256": digest(path)} for path in paths]


def source_digest() -> str:
    """Identify the actual producer source even before its release commit exists."""
    result = hashlib.sha256()
    for path in sorted((ROOT / "kerykeion").rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix not in (".pyc", ".pyo"):
            result.update(path.relative_to(ROOT).as_posix().encode())
            result.update(b"\0")
            result.update(path.read_bytes())
    return result.hexdigest()


def projected_point(point, expected: dict) -> dict:
    actual = point.model_dump(mode="json")
    missing = set(expected) - set(actual)
    if missing:
        raise AssertionError(f"point fields disappeared: {missing}")
    return {key: actual[key] for key in expected}


def numeric_fixtures(geometry_python: Path) -> tuple[dict, dict]:
    positions, arabic, controls = {}, {}, []
    from tests.core.test_report import _assert_report_match

    # The existing report comparator explicitly covers degree/day speeds too.
    # Reuse that budget, declared before evaluating any new reference values.
    speed_budget = inspect.signature(_assert_report_match).parameters["abs_tol"].default
    max_asc, max_mc, max_speed = 0.0, 0.0, 0.0
    for identifier, legacy in EXPECTED_POSITIONS.items():
        subject = create_subject_from_id(identifier)
        positions[identifier] = {
            group: {name: projected_point(getattr(subject, name), fields) for name, fields in legacy[group].items()}
            for group in ("angles", "houses")
        }
        if abs(subject.lat) < 60.0:
            reference = orientation(subject.julian_day, subject.lat, subject.lng)
            asc_error = angular_distance(subject.ascendant.abs_pos, reference["ascendant"])
            mc_error = angular_distance(subject.medium_coeli.abs_pos, reference["medium_coeli"])
            assert max(asc_error, mc_error) <= POSITION_TOLERANCE, identifier
            max_asc, max_mc = max(max_asc, asc_error), max(max_mc, mc_error)
            low_jd, high_jd = subject.julian_day - 2.0 / 86400.0, subject.julian_day + 2.0 / 86400.0
            lower = orientation(low_jd, subject.lat, subject.lng)
            upper = orientation(high_jd, subject.lat, subject.lng)
            span = high_jd - low_jd
            for angle in ("ascendant", "medium_coeli"):
                rate = ((upper[angle] - lower[angle] + 180.0) % 360.0 - 180.0) / span
                error = abs(getattr(subject, angle).speed - rate)
                assert error <= speed_budget, (identifier, angle, error)
                max_speed = max(max_speed, error)
            controls.append(
                {
                    "id": identifier,
                    "latitude": subject.lat,
                    **reference,
                    "actual_cusps": [getattr(subject, field).abs_pos for field in HOUSE_FIELD_NAMES],
                    "actual_speeds": [getattr(subject, field).speed for field in HOUSE_FIELD_NAMES],
                    "lower": lower,
                    "upper": upper,
                    "span": span,
                }
            )
    for identifier, legacy in EXPECTED_ARABIC_PARTS.items():
        subject = _create_arabic_subject(identifier)
        arabic[identifier] = {
            "arabic_parts": {
                name: projected_point(getattr(subject, name), fields) for name, fields in legacy["arabic_parts"].items()
            }
        }

    # Separate implementation, separate interpreter, and independently computed
    # orientation inputs. Only the public v3 geometry API is called here.
    program = """
import json,sys
import libephemeris as e
assert e.__version__ == '3.2.2', 'the geometry control must be the unchanged v3 engine'
rows=json.load(sys.stdin)
results=[]
for row in rows:
    cusps,_=e.houses_armc(row['armc'],row['latitude'],row['obliquity'],b'P')
    lower,_=e.houses_armc(row['lower']['armc'],row['latitude'],row['lower']['obliquity'],b'P')
    upper,_=e.houses_armc(row['upper']['armc'],row['latitude'],row['upper']['obliquity'],b'P')
    results.append({'id':row['id'],'cusps':list(cusps),'lower':list(lower),'upper':list(upper)})
print(json.dumps(results))
"""
    result = subprocess.run(
        [str(geometry_python), "-I", "-c", program],
        input=json.dumps(controls),
        text=True,
        capture_output=True,
        check=True,
    )
    references = json.loads(result.stdout)
    assert {row["id"] for row in references} == {row["id"] for row in controls}
    by_id = {row["id"]: row for row in references}
    max_cusp = 0.0
    for row in controls:
        expected = by_id[row["id"]]["cusps"]
        assert len(expected) == len(row["actual_cusps"]) == 12
        errors = [angular_distance(a, b) for a, b in zip(row["actual_cusps"], expected)]
        assert max(errors) <= POSITION_TOLERANCE, row["id"]
        max_cusp = max(max_cusp, *errors)
        rates = [
            ((high - low + 180.0) % 360.0 - 180.0) / row["span"]
            for high, low in zip(by_id[row["id"]]["upper"], by_id[row["id"]]["lower"])
        ]
        speed_errors = [abs(actual - expected) for actual, expected in zip(row["actual_speeds"], rates)]
        assert max(speed_errors) <= speed_budget, (row["id"], speed_errors)
        max_speed = max(max_speed, *speed_errors)
    qualification = {
        "clock_and_poles": "Skyfield 1.54: UT1 GAST, true equator and ecliptic date frames",
        "angle_geometry": "closed-form horizon and meridian intersections",
        "house_geometry": "LibEphemeris 3.2.2 public houses_armc with independent orientation inputs",
        "subject_ids": [row["id"] for row in controls],
        "angular_budget_degrees": POSITION_TOLERANCE,
        "maximum_ascendant_error_degrees": max_asc,
        "maximum_midheaven_error_degrees": max_mc,
        "maximum_cusp_error_degrees": max_cusp,
        "speed_budget_degrees_per_day": speed_budget,
        "maximum_speed_error_degrees_per_day": max_speed,
        "speed_reference": "central difference at +/-2 UT1 seconds, using actual sampled JD span",
        "scope": "non-polar positions/rates at the existing consumer budgets; SVGs remain regression snapshots, not absolute accuracy certificates",
    }
    return {"positions": positions, "arabic_parts": arabic}, qualification


def same_svg(legacy: str, actual: str, options: dict) -> bool:
    left, right = legacy.splitlines(), actual.splitlines()
    if len(left) != len(right):
        return False
    try:
        for old, new in zip(left, right):
            compare_svg_lines(
                old,
                new,
                rel_tol=options.get("rel_tol", DEFAULT_REL_TOL),
                abs_tol=options.get("abs_tol", DEFAULT_ABS_TOL),
            )
    except AssertionError:
        return False
    return True


def svg_fixtures(stage: Path) -> dict:
    captured = {}
    producer_inputs = None
    if not DESTINATION.exists():
        from libephemeris.download import DATA_FILES

        # Creation has no destination manifest yet. Bind its temporal recipes
        # to the original producer's official image hashes instead; existing
        # sets continue to validate their frozen manifest without overrides.
        assert ephe.__version__ == "4.0.0b1"
        producer_inputs = {item["name"]: item["sha256"] for item in input_inventory()}
        assert all(DATA_FILES[name]["sha256"] == checksum for name, checksum in producer_inputs.items())

    def collect(path, svg, **options):
        path = Path(path)
        assert path.parent.resolve() == SVG_DIR.resolve(), path
        if path.name in captured:
            assert same_svg(captured[path.name][0], svg, options), f"conflicting recipes for {path.name}"
        else:
            captured[path.name] = (svg, options)

    class CaptureComparisons:
        """Use pytest's real fixture/setup/skip lifecycle, not a partial driver."""

        def pytest_configure(self, config):
            modules = [importlib.import_module("tests.data.compare_svg_lines")]
            modules.extend(importlib.import_module(name) for name in GOLDEN_TEST_MODULES)
            self.originals = [(module, module.compare_svg_file) for module in modules]
            self.snapshot_originals = []
            for module, _original in self.originals:
                module.compare_svg_file = collect
                if producer_inputs is not None and hasattr(module, "require_temporal_snapshot_inputs"):
                    original = module.require_temporal_snapshot_inputs
                    self.snapshot_originals.append((module, original))

                    def require_inputs(subject_id, _original=original):
                        return _original(subject_id, producer_inputs=producer_inputs)

                    module.require_temporal_snapshot_inputs = require_inputs

        def pytest_unconfigure(self, config):
            for module, original in self.originals:
                module.compare_svg_file = original
            for module, original in self.snapshot_originals:
                module.require_temporal_snapshot_inputs = original

    paths = [str(ROOT / (name.replace(".", "/") + ".py")) for name in GOLDEN_TEST_MODULES]
    result = pytest.main(
        [*paths, "--tier=extended", "-m", "not online", "-n", "0", "-q", "--tb=short", "-o", "log_cli=false"],
        plugins=[CaptureComparisons()],
    )
    assert result == 0, "a generating recipe failed; no model references will be committed"
    required = {path.name for path in SVG_DIR.glob("*.svg")} - baselines_out_of_this_runs_reach()
    assert required <= set(captured), f"undriven baselines: {sorted(required - set(captured))}"
    records = {}
    for name, (svg, options) in sorted(captured.items()):
        original = SVG_DIR / name
        if same_svg(original.read_text(), svg, options):
            records[name] = {"storage": "legacy", "sha256": digest(original)}
        else:
            path = stage / "svg" / name
            path.parent.mkdir(exist_ok=True)
            path.write_text(svg, encoding="utf-8")
            records[name] = {"storage": "v4", "sha256": digest(path)}
    return records


def report_fixture(stage: Path) -> dict:
    """Run the existing exact report recipe, not a hand-maintained second copy."""
    buffer = StringIO()
    with redirect_stdout(buffer):
        print_ancient_rome_report()
    captured = [buffer.getvalue()]
    name = "natal_ancient_rome_all_report.txt"
    path = stage / "reports" / name
    path.parent.mkdir()
    # print_report adds a final newline to the report text, as the existing test
    # expects. Preserve the exact report body rather than relaxing its comparator.
    assert captured[0].endswith("\n")
    path.write_text(captured[0][:-1], encoding="utf-8")
    return {name: {"storage": "v4", "sha256": digest(path)}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry-python", type=Path, default=ROOT / ".venv/bin/python")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    require_library_from_this_checkout(__file__)
    assert BACKEND_NAME == "libephemeris"
    if ephe.__version__ != "4.0.0b1":
        assert args.check, "only the original producer may generate this immutable model"
        from tests.data.model_fixtures import patch_qualification
        patch_qualification(ephe.__version__)
    assert ephe.get_precision_tier() == "extended", "generate against the declared full-range input set"
    if DESTINATION.exists() and not args.check:
        parser.error("the model set already exists; use --check, never overwrite immutable references")
    before = legacy_inventory()
    DESTINATION.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="v4-baseline-staging-", dir=DESTINATION.parent) as temporary:
        stage = Path(temporary)
        numeric, qualification = numeric_fixtures(args.geometry_python)
        numeric_path = stage / "positions.json"
        numeric_path.write_text(json.dumps(numeric, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
        svg = svg_fixtures(stage)
        reports = report_fixture(stage)
        import importlib.metadata

        manifest = {
            "schema": 1,
            "model": MODEL,
            "engine_version": ephe.__version__,
            "sidereal_model": "continuous VCW pole/CIO transport, UT1 rotation and TT precession",
            "producer_version": importlib.metadata.version("kerykeion"),
            "producer_source_sha256": source_digest(),
            "numeric_sha256": digest(numeric_path),
            "legacy_files": before,
            "svg": svg,
            "reports": reports,
            "independent_qualification": qualification,
            "recipe_modules": list(GOLDEN_TEST_MODULES),
            "inputs": input_inventory(),
        }
        (stage / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        assert before == legacy_inventory(), "legacy fixtures were modified"
        if args.check:
            assert DESTINATION.is_dir()
            generated = {p.relative_to(stage).as_posix(): digest(p) for p in stage.rglob("*") if p.is_file()}
            stored = {p.relative_to(DESTINATION).as_posix(): digest(p) for p in DESTINATION.rglob("*") if p.is_file()}
            # Provenance describes the ORIGINAL producer, not each compatible
            # consumer. Keep it immutable; require every reference byte and all
            # scientific/input qualification fields to reproduce unchanged.
            generated.pop("manifest.json")
            stored.pop("manifest.json")
            assert generated == stored, "the frozen model reference bytes do not reproduce"
            original_manifest = json.loads((DESTINATION / "manifest.json").read_text())
            for field in ("producer_source_sha256", "producer_version", "engine_version"):
                print(field, "original:", original_manifest.pop(field), "current:", manifest.pop(field))
            assert manifest == original_manifest, "model/input qualification changed; review a separate reference version"
            print("Frozen v4 reference bytes reproduce exactly; legacy references unchanged.")
        else:
            stage.rename(DESTINATION)
            print("Wrote", DESTINATION)
            print("Versioned SVGs:", sum(item["storage"] == "v4" for item in svg.values()))
        print(json.dumps(qualification, indent=2))


if __name__ == "__main__":
    main()
