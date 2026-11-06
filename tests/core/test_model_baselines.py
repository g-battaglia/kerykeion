"""Protect legacy references and keep native model selection explicit and strict."""

from copy import deepcopy

import pytest

from kerykeion.ephemeris_backend import BACKEND_NAME
from tests.data import model_fixtures as fixtures
from tests.data.expected_arabic_parts import EXPECTED_ARABIC_PARTS
from tests.data.expected_positions import EXPECTED_POSITIONS
from tests.data.model_oracle import angular_distance, orientation
from tests.core.conftest import POSITION_TOLERANCE


def test_model_selection_is_explicit():
    assert fixtures.active_model("libephemeris", "3.2.2") is None
    assert fixtures.active_model("swisseph", "4.0.0b1") is None
    assert fixtures.active_model("libephemeris", "4.0.0b1") == fixtures.MODEL
    assert fixtures.active_model("libephemeris", "4.0.0b2") == fixtures.MODEL
    for version in ("4.0.0", "4.0.0b5", "4.0.1", "5.0.0"):
        with pytest.raises(AssertionError, match="No qualified model fixtures"):
            fixtures.active_model("libephemeris", version)


def test_patch_distribution_uses_an_authenticated_unchanged_model():
    record = fixtures.patch_qualification("4.0.0b2")
    assert record["model"] == fixtures.MODEL
    assert record["numerical_source"]["base_tag"] == "python-v4.0.0b1"
    assert record["numerical_source"]["candidate_tag"] == "python-v4.0.0b2"
    assert len(record["published_files_sha256"]) == 5
    path = fixtures.ROOT / "tests/data/svg/Ancient Greece 500BC - Natal Chart - Classic.svg"
    assert fixtures.fixture_path(path, backend="libephemeris", version="4.0.0b1") == fixtures.fixture_path(path, backend="libephemeris", version="4.0.0b2")
    with pytest.raises(AssertionError, match="No qualified patch identity"):
        fixtures.patch_qualification("4.0.0b5")


def test_legacy_reference_bytes_are_unchanged():
    for relative, expected in fixtures.manifest()["legacy_files"].items():
        fixtures.verify_file(fixtures.ROOT / relative, expected)


def test_native_overlays_preserve_every_case_and_point(monkeypatch):
    monkeypatch.setattr(fixtures, "active_model", lambda **kwargs: fixtures.MODEL)
    original = deepcopy(EXPECTED_POSITIONS)
    selected = fixtures.positions_for_model(EXPECTED_POSITIONS)
    assert selected.keys() == EXPECTED_POSITIONS.keys()
    for identifier, legacy in original.items():
        assert selected[identifier].keys() == legacy.keys()
        for group in ("angles", "houses"):
            assert selected[identifier][group].keys() == legacy[group].keys()
            for point in legacy[group]:
                assert selected[identifier][group][point].keys() == legacy[group][point].keys()
        for group in legacy.keys() - {"angles", "houses"}:
            assert selected[identifier][group] == legacy[group]
    assert EXPECTED_POSITIONS == original
    parts = fixtures.arabic_parts_for_model(EXPECTED_ARABIC_PARTS)
    assert parts.keys() == EXPECTED_ARABIC_PARTS.keys()
    selected["ancient_500bc"]["angles"]["ascendant"]["abs_pos"] = -999
    assert fixtures.numeric()["positions"]["ancient_500bc"]["angles"]["ascendant"]["abs_pos"] >= 0


def test_legacy_model_returns_original_references(monkeypatch):
    monkeypatch.setattr(fixtures, "active_model", lambda **kwargs: None)
    assert fixtures.positions_for_model(EXPECTED_POSITIONS) is EXPECTED_POSITIONS
    assert fixtures.arabic_parts_for_model(EXPECTED_ARABIC_PARTS) is EXPECTED_ARABIC_PARTS
    path = fixtures.ROOT / "tests/data/svg/Ancient Greece 500BC - Natal Chart - Classic.svg"
    assert fixtures.fixture_path(path) == path


def test_native_variants_have_no_missing_or_orphan_files():
    data = fixtures.manifest()
    expected = {"positions.json", "manifest.json"}
    for collection, original_directory in (("svg", "tests/data/svg"), ("reports", "tests/fixtures")):
        for name, record in data[collection].items():
            path = fixtures.fixture_path(
                fixtures.ROOT / original_directory / name, backend="libephemeris", version="4.0.0b1"
            )
            fixtures.verify_file(path, record["sha256"])
            if record["storage"] == "v4":
                expected.add(f"{collection}/{name}")
    assert expected == {
        path.relative_to(fixtures.MODEL_ROOT).as_posix() for path in fixtures.MODEL_ROOT.rglob("*") if path.is_file()
    }


def test_unknown_native_chart_cannot_fall_back_to_legacy():
    with pytest.raises(AssertionError, match="No .* reference registered"):
        fixtures.fixture_path(
            fixtures.ROOT / "tests/data/svg/unregistered.svg", backend="libephemeris", version="4.0.0b1"
        )


def test_missing_and_corrupted_reference_files_fail(tmp_path):
    path = tmp_path / "reference.json"
    with pytest.raises(AssertionError, match="Missing model reference"):
        fixtures.verify_file(path, "0" * 64)
    path.write_text("original")
    expected = fixtures.file_sha256(path)
    fixtures.verify_file(path, expected)
    path.write_text("corrupted")
    with pytest.raises(AssertionError, match="Frozen model reference changed"):
        fixtures.verify_file(path, expected)


def test_v4_cannot_rewrite_legacy_svg(monkeypatch):
    from tests.data.compare_svg_lines import compare_svg_file
    from tests.data.regeneration_guard import require_the_baseline_backend

    monkeypatch.setattr(fixtures, "active_model", lambda **kwargs: fixtures.MODEL)
    monkeypatch.setenv("KERYKEION_REGEN_BASELINES", "1")
    path = fixtures.ROOT / "tests/data/svg/Ancient Greece 500BC - Natal Chart - Classic.svg"
    before = fixtures.file_sha256(path)
    with pytest.raises(AssertionError, match="cannot overwrite legacy"):
        compare_svg_file(path, "wrong chart")
    assert fixtures.file_sha256(path) == before
    with pytest.raises(SystemExit, match="Refusing to overwrite legacy"):
        require_the_baseline_backend()


@pytest.mark.extended
@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="independent qualification of the native v4 model only")
@pytest.mark.parametrize("subject_id", fixtures.manifest()["independent_qualification"]["subject_ids"])
def test_native_angles_against_independent_clock_and_geometry(subject_id):
    from tests.core.test_houses_positions import create_subject_from_id

    subject = create_subject_from_id(subject_id)
    reference = orientation(subject.julian_day, subject.lat, subject.lng)
    for angle in ("ascendant", "medium_coeli"):
        assert angular_distance(getattr(subject, angle).abs_pos, reference[angle]) <= POSITION_TOLERANCE


@pytest.mark.parametrize("primary", ["base_core.leb2", "medium_core.leb2"])
def test_historical_svg_inputs_verify_both_routing_and_asset_identity(monkeypatch, primary):
    from types import SimpleNamespace
    from kerykeion.ephemeris_backend import ephe

    checked = []
    monkeypatch.setattr(fixtures, "active_model", lambda: fixtures.MODEL)
    monkeypatch.setattr(fixtures, "manifest", lambda: {"inputs": [
        {"name": "base_core.leb2", "sha256": "base-digest"},
        {"name": "medium_core.leb2", "sha256": "medium-digest"},
    ]})
    monkeypatch.setattr(fixtures, "verify_file", lambda path, digest: checked.append((path.name, digest)))
    monkeypatch.setattr(ephe, "get_leb_reader", lambda: SimpleNamespace(path=primary), raising=False)
    monkeypatch.setattr(ephe, "get_leb_inventory", lambda: {"files": [{"path": "medium_core.leb2"}]}, raising=False)
    fixtures.require_temporal_snapshot_inputs("galileo_1564")
    expected = [(primary, "base-digest" if primary.startswith("base") else "medium-digest")]
    if primary.startswith("base"):
        expected.append(("medium_core.leb2", "medium-digest"))
    assert checked == expected


def test_historical_svg_rejects_different_core_without_switching_it(monkeypatch):
    from types import SimpleNamespace
    from kerykeion.ephemeris_backend import ephe

    reader = SimpleNamespace(path="extended_core.leb2")
    monkeypatch.setattr(fixtures, "active_model", lambda: fixtures.MODEL)
    monkeypatch.setattr(ephe, "get_leb_reader", lambda: reader, raising=False)
    with pytest.raises(AssertionError, match="different model"):
        fixtures.require_temporal_snapshot_inputs("newton_1643")
    assert reader.path == "extended_core.leb2"


def test_foreign_backend_has_no_native_coefficient_precondition(monkeypatch):
    monkeypatch.setattr(fixtures, "active_model", lambda: None)
    fixtures.require_temporal_snapshot_inputs("galileo_1564")


def test_original_producer_can_validate_temporal_inputs_before_manifest_exists(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from kerykeion.ephemeris_backend import ephe

    base = tmp_path / "base_core.leb2"
    medium = tmp_path / "medium_core.leb2"
    base.write_bytes(b"base producer fixture")
    medium.write_bytes(b"medium producer fixture")
    monkeypatch.setattr(fixtures, "active_model", lambda: fixtures.MODEL)
    monkeypatch.setattr(fixtures, "MODEL_ROOT", tmp_path / "missing-model")
    monkeypatch.setattr(ephe, "__version__", "4.0.0b1")
    monkeypatch.setattr(ephe, "get_leb_reader", lambda: SimpleNamespace(path=str(base)))
    monkeypatch.setattr(ephe, "get_leb_inventory", lambda: {"files": [{"path": str(medium)}]})
    inputs = {path.name: fixtures.file_sha256(path) for path in (base, medium)}
    fixtures.require_temporal_snapshot_inputs("galileo_1564", producer_inputs=inputs)
    medium.write_bytes(b"wrong coefficients")
    with pytest.raises(AssertionError, match="Frozen model reference changed"):
        fixtures.require_temporal_snapshot_inputs("newton_1643", producer_inputs=inputs)


def test_candidate_cannot_use_producer_inputs_without_a_frozen_manifest(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from kerykeion.ephemeris_backend import ephe

    monkeypatch.setattr(fixtures, "active_model", lambda: fixtures.MODEL)
    monkeypatch.setattr(fixtures, "MODEL_ROOT", tmp_path / "missing-model")
    monkeypatch.setattr(ephe, "__version__", "4.0.0b4")
    monkeypatch.setattr(ephe, "get_leb_reader", lambda: SimpleNamespace(path="base_core.leb2"))
    with pytest.raises(AssertionError, match="Only the original producer"):
        fixtures.require_temporal_snapshot_inputs("galileo_1564", producer_inputs={})


def test_b3_resource_patch_has_separate_evidence_without_rewriting_provenance():
    record = fixtures.patch_qualification("4.0.0b3")
    assert fixtures.active_model("libephemeris", "4.0.0b3") == fixtures.MODEL
    assert record["schema"] == 2
    assert record["reference_verification"]["reference_bytes_identical"] is True
    assert fixtures.manifest()["engine_version"] == "4.0.0b1"


def test_b4_path_contract_keeps_the_qualified_scientific_model():
    record = fixtures.patch_qualification("4.0.0b4")
    assert fixtures.active_model("libephemeris", "4.0.0b4") == fixtures.MODEL
    assert record["schema"] == 2
    assert record["reference_verification"]["reference_bytes_identical"] is True
    assert fixtures.manifest()["engine_version"] == "4.0.0b1"
