"""Metadata memoization must not conflate overlapping serving files or settings."""

from types import SimpleNamespace

import pytest

from kerykeion.ephemeris_backend import coverage as cache


@pytest.fixture
def fake_native(tmp_path, monkeypatch):
    files = [tmp_path / "base.leb2", tmp_path / "extended.leb2"]
    for path in files:
        path.write_bytes(b"fixture")
    calls = []
    state = {"tier": "extended", "path": str(files[0])}

    def coverage(body_id, jd):
        calls.append((body_id, jd))
        return SimpleNamespace(data_file="base" if 100 <= jd <= 200 else "extended", reviewed=False)

    backend = SimpleNamespace(
        __version__="4.0.test",
        get_body_coverage=coverage,
        get_leb_reader=lambda: SimpleNamespace(path=state["path"]),
        get_calc_mode=lambda: "leb",
        get_precision_tier=lambda: state["tier"],
        get_current_file_data=lambda: (state["path"], 0.0, 300.0, 441),
        get_leb_inventory=lambda: {
            "files": [
                {"path": str(path), "bodies": [{"body_id": 0, "jd_start": start, "jd_end": end}]}
                for path, start, end in [(files[0], 100, 200), (files[1], 0, 300)]
            ]
        },
    )
    monkeypatch.setattr(cache, "ephe", backend)
    monkeypatch.setattr(cache.inspect, "isbuiltin", lambda _: True)
    cache.clear_coverage_cache()
    yield calls, state, files
    cache.clear_coverage_cache()


def test_overlapping_coverage_regions_are_not_confused(fake_native):
    calls, _, _ = fake_native
    old = cache.get_body_coverage(0, 50.0)
    modern = cache.get_body_coverage(0, 150.0)
    assert old.data_file == "extended"
    assert modern.data_file == "base"
    assert cache.get_body_coverage(0, 60.0) is old
    assert cache.get_body_coverage(0, 160.0) is modern
    assert len(calls) == 2
    assert not old.reviewed and not modern.reviewed


def test_file_changes_invalidate_records(fake_native):
    calls, _, files = fake_native
    first = cache.get_body_coverage(0, 150.0)
    files[0].write_bytes(b"changed fixture")
    assert cache.get_body_coverage(0, 150.0) is not first
    assert len(calls) == 2


def test_added_group_files_invalidate_records(fake_native):
    calls, _, files = fake_native
    first = cache.get_body_coverage(0, 150.0)
    (files[0].parent / "extra.leb2").write_bytes(b"new group")
    assert cache.get_body_coverage(0, 150.0) is not first
    assert len(calls) == 2


def test_provider_changes_invalidate_records(fake_native):
    calls, state, _ = fake_native
    first = cache.get_body_coverage(0, 150.0)
    state["tier"] = "base"
    assert cache.get_body_coverage(0, 150.0) is not first
    assert len(calls) == 2


def test_virtual_readers_do_not_cache_incomplete_inventory(fake_native):
    calls, state, _ = fake_native
    state["path"] = "<bundled>/base_core.leb2"
    cache.get_body_coverage(0, 150.0)
    cache.get_body_coverage(0, 150.0)
    assert len(calls) == 2


@pytest.mark.parametrize("body,jd", [(0, -50.0), (9999, 150.0)])
def test_unserved_or_uninventoried_regions_are_not_cached(fake_native, body, jd):
    calls, _, _ = fake_native
    cache.get_body_coverage(body, jd)
    cache.get_body_coverage(body, jd + 1.0)
    assert len(calls) == 2


def test_monkeypatched_getters_bypass_cache(fake_native, monkeypatch):
    calls, _, _ = fake_native
    monkeypatch.setattr(cache.inspect, "isbuiltin", lambda _: False)
    cache.get_body_coverage(0, 150.0)
    cache.get_body_coverage(0, 150.0)
    assert len(calls) == 2
