"""Reader reuse and lazy batch construction preserve public results."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from kerykeion.ephemeris_backend import backend
from kerykeion.ephemeris_data import factory as batches


@pytest.mark.parametrize("native", [False, True])
@pytest.mark.parametrize("path", [None, "", "/explicit/ephe"])
@pytest.mark.parametrize("configured", ["", "/configured/ephe"])
def test_session_does_not_replace_native_default_path(monkeypatch, native, path, configured):
    setter = Mock()
    monkeypatch.setattr(backend, "BACKEND_NAME", "libephemeris" if native else "swisseph")
    monkeypatch.setattr(backend, "EPHE_DATA_PATH", configured)
    monkeypatch.setattr(backend.ephe, "set_ephe_path", setter)
    with backend.ephemeris_session(ephe_path=path):
        pass
    selected = configured if path is None else path
    if native and not selected:
        setter.assert_not_called()
    else:
        setter.assert_called_once_with(selected)


@pytest.mark.skipif(backend.BACKEND_NAME != "libephemeris", reason="native path contract")
def test_real_native_session_keeps_library_path_usable():
    backend.ephe.set_ephe_path(None)
    expected = backend.ephe.get_library_path()
    with backend.ephemeris_session():
        pass
    assert backend.ephe.get_library_path() == expected
    backend.ephe.release_data_cache()


@pytest.mark.parametrize("as_model", [False, True])
@pytest.mark.parametrize("stars", [None, ["Sirius"]])
def test_lazy_batch_matches_list_and_does_not_eagerly_calculate(monkeypatch, as_model, stars):
    factory = batches.EphemerisDataFactory(
        datetime(2025, 1, 1), datetime(2025, 1, 4), active_points=["Sun"], active_fixed_stars=stars,
    )
    calls = []
    def subject(date):
        calls.append(date)
        return SimpleNamespace(ephemeris_warnings=[], polar_house_fallbacks=[], fixed_stars=[])
    monkeypatch.setattr(factory, "_create_subject_for_date", subject)
    monkeypatch.setattr(batches, "get_houses_list", lambda subject: [])
    monkeypatch.setattr(batches, "get_available_astrological_points_list", lambda subject: [])
    stream = factory.iter_ephemeris_data(as_model=as_model)
    assert calls == []
    first = next(stream)
    assert len(calls) == 1
    stream.close()
    assert len(calls) == 1
    expected = factory.get_ephemeris_data(as_model=as_model)
    actual = list(factory.iter_ephemeris_data(as_model=as_model))
    assert actual == expected
    assert first == actual[0]
    if not as_model:
        assert ("fixed_stars" in actual[0]) == bool(stars)
