"""Select immutable fixture variants by the actual ephemeris model.

The legacy files remain authoritative for the legacy engine. Native v4 gets
explicit, hash-listed overlays; a missing variant fails instead of quietly
comparing incompatible scientific models or weakening a tolerance.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODEL = "libephemeris-4.0.0b1"
MODEL_ROOT = ROOT / "tests/data/model_baselines" / MODEL


def active_model(backend: str | None = None, version: str | None = None) -> str | None:
    if backend is None:
        from kerykeion.ephemeris_backend import BACKEND_NAME

        backend = BACKEND_NAME
    if backend != "libephemeris":
        return None
    if version is None:
        from kerykeion.ephemeris_backend import ephe

        version = str(ephe.__version__)
    if version.startswith("3."):
        return None
    if version == "4.0.0b1":
        return MODEL
    if version in {"4.0.0b2", "4.0.0b3"}:
        return patch_qualification(version)["model"]
    raise AssertionError(
        f"No qualified model fixtures for libephemeris {version}; do not reuse another model's references"
    )


def file_sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


@lru_cache(maxsize=1024)
def _verified_digest(path: Path, expected: str, size: int, modified_ns: int) -> None:
    # Stat fields invalidate memoization when a file changes during a test run.
    assert file_sha256(path) == expected, f"Frozen model reference changed: {path}"


def verify_file(path: Path, expected: str) -> Path:
    assert path.is_file(), f"Missing model reference: {path}"
    stat = path.stat()
    _verified_digest(path, expected, stat.st_size, stat.st_mtime_ns)
    return path


@lru_cache(maxsize=2)
def patch_qualification(version: str) -> dict:
    """Bind one explicitly reviewed distribution patch to an unchanged model.

    The source-identity record is separate from frozen producer references.
    This is never a wildcard for future native versions or new model outputs.
    """
    assert version in {"4.0.0b2", "4.0.0b3"}, f"No qualified patch identity for {version}"
    path = ROOT / "tests/data/model_qualifications" / f"libephemeris-{version}.json"
    assert path.is_file(), f"Missing patch-model qualification: {path}"
    data = json.loads(path.read_text())
    assert data["engine_version"] == version and data["model"] == MODEL
    source = data["numerical_source"]
    if version == "4.0.0b2":
        assert data["schema"] == 1
        assert source["base_core_tree"] == source["candidate_core_tree"] and source["base_core_tree"]
        assert source["runtime_python_source_changed"] is False
    else:
        # b3 changes resource management, so whole-core identity would be false.
        # Its explicit source audit and reproduced references form a separate
        # qualification; never extend this branch to an unreviewed version.
        assert data["schema"] == 2 and source["review_kind"] == "runtime-resource-patch"
        assert source["base_data_tree"] == source["candidate_data_tree"] and source["base_data_tree"]
        assert len(source["candidate_commit"]) == 40 and len(source["reviewed_diff_sha256"]) == 64
        assert source["reviewed_paths"] and data["qualification_artifacts_sha256"]
        evidence = data["reference_verification"]
        for field in ("reference_bytes_identical", "scientific_manifest_identical", "legacy_files_unchanged"):
            assert evidence[field] is True
        assert evidence["baseline_producer"] == "4.0.0b1"
    verify_file(MODEL_ROOT / "manifest.json", data["baseline_manifest_sha256"])
    return data


@lru_cache(maxsize=1)
def manifest() -> dict:
    data = json.loads((MODEL_ROOT / "manifest.json").read_text())
    assert data["schema"] == 1 and data["model"] == MODEL and data["engine_version"] == "4.0.0b1"
    return data


def require_temporal_snapshot_inputs(subject_id: str) -> None:
    """Check the known coefficient contract of the two DE440 lunar snapshots.

    The qualified automatic inventory serves these dates with medium/DE440
    coefficients, even under the extended date profile. Forcing the extended
    core changes the lunar model. Reject that configuration explicitly instead
    of diagnosing a changed render as a numerical regression. No backend state
    is changed, and the original producer manifest remains immutable.
    """
    if subject_id not in {"galileo_1564", "newton_1643"} or active_model() is None:
        return
    from kerykeion.ephemeris_backend import ephe

    reader = ephe.get_leb_reader()
    assert reader is not None, "Historical SVG references require the qualified local LEB inventory"
    path = Path(reader.path)
    assert path.name in {"base_core.leb2", "medium_core.leb2"}, (
        f"{subject_id}: snapshot requires medium/DE440 coefficients at this date; "
        f"the selected primary core is {path.name}. Use the qualified automatic "
        "inventory (unset LIBEPHEMERIS_LEB), or medium_core.leb2. An explicit "
        "extended core is a different model, not a failure of numerical precision."
    )
    inputs = {item["name"]: item["sha256"] for item in manifest()["inputs"]}
    verify_file(path, inputs[path.name])
    if path.name == "base_core.leb2":
        medium = [Path(item["path"]) for item in ephe.get_leb_inventory()["files"]
                  if Path(item["path"]).name == "medium_core.leb2"]
        assert len(medium) == 1, "Historical SVG references require the qualified medium core in the inventory"
        verify_file(medium[0], inputs["medium_core.leb2"])


@lru_cache(maxsize=1)
def numeric() -> dict:
    path = verify_file(MODEL_ROOT / "positions.json", manifest()["numeric_sha256"])
    return json.loads(path.read_text())


def positions_for_model(legacy: dict) -> dict:
    if active_model() is None:
        return legacy
    data = manifest()
    path = ROOT / "tests/data/expected_positions.py"
    verify_file(path, data["legacy_files"][path.relative_to(ROOT).as_posix()])
    overlay = numeric()["positions"]
    assert set(overlay) == set(legacy), "a subject disappeared from the v4 position reference"
    selected = deepcopy(legacy)
    for identifier, groups in overlay.items():
        assert set(groups) == {"angles", "houses"}
        for group, points in groups.items():
            assert set(points) == set(legacy[identifier][group]), f"point inventory changed for {identifier}/{group}"
            selected[identifier][group] = deepcopy(points)
    return selected


def arabic_parts_for_model(legacy: dict) -> dict:
    if active_model() is None:
        return legacy
    data = manifest()
    path = ROOT / "tests/data/expected_arabic_parts.py"
    verify_file(path, data["legacy_files"][path.relative_to(ROOT).as_posix()])
    overlay = numeric()["arabic_parts"]
    assert set(overlay) == set(legacy), "a subject disappeared from the v4 Arabic Parts reference"
    for identifier in legacy:
        assert set(overlay[identifier]["arabic_parts"]) == set(legacy[identifier]["arabic_parts"])
    return deepcopy(overlay)


def fixture_path(path: Path, backend: str | None = None, version: str | None = None) -> Path:
    """Resolve a registered SVG/report, leaving synthetic comparator tests alone."""
    path = Path(path)
    parent = path.parent.resolve()
    svg_root = ROOT / "tests/data/svg"
    report_root = ROOT / "tests/fixtures"
    if parent not in (svg_root, report_root) or active_model(backend=backend, version=version) is None:
        return path
    data = manifest()
    collection = "svg" if parent == svg_root else "reports"
    assert path.name in data[collection], f"No {MODEL} reference registered for {path.name}"
    entry = data[collection][path.name]
    if entry["storage"] == "legacy":
        relative = path.resolve().relative_to(ROOT).as_posix()
        assert data["legacy_files"][relative] == entry["sha256"]
        return verify_file(path, entry["sha256"])
    assert entry["storage"] == "v4", "unknown model-reference storage"
    return verify_file(MODEL_ROOT / collection / path.name, entry["sha256"])
