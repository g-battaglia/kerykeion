"""A broad Sun date range must not hide per-body failures or fake a full chart."""

from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from kerykeion import ChartDataFactory
from kerykeion.ephemeris_backend import BACKEND_NAME
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS
from tests.conftest import create_subject_from_temporal_data
from tests.data import ephemeris_requirements as requirements
from tests.data.test_subjects_matrix import TEMPORAL_SUBJECTS


class BackendError(Exception):
    pass


@pytest.fixture
def missing_chiron(monkeypatch):
    subject = SimpleNamespace(**{name.lower(): object() for name in DEFAULT_ACTIVE_POINTS})
    subject.chiron = None
    subject.julian_day = 2_000_000.0
    subject.ephemeris_warnings = [SimpleNamespace(point_name="Chiron")]
    monkeypatch.setattr(requirements, "BACKEND_NAME", "swisseph")
    monkeypatch.setattr(requirements, "ephemeris_session", lambda: nullcontext(2))
    return subject


@pytest.mark.parametrize("message,reason", [
    ("ephemeris file /private/example.se1 not found", "local ephemeris file"),
    ("Chiron is restricted to a supported interval", "supported coverage"),
    ("date outside supported range", "supported coverage"),
])
def test_only_confirmed_body_limitations_exclude_full_snapshots(monkeypatch, missing_chiron, message, reason):
    calls = []

    def calculate(jd, body, flags):
        calls.append((jd, body, flags))
        raise BackendError(message)

    monkeypatch.setattr(requirements, "ephe", SimpleNamespace(Error=BackendError, calc_ut=calculate))
    unavailable = requirements.unavailable_snapshot_points(missing_chiron)
    assert len(unavailable) == 1 and reason in unavailable[0]
    assert "/private/" not in unavailable[0]
    assert calls == [(missing_chiron.julian_day, requirements.STANDARD_PLANETS["Chiron"], 2)]


def test_successful_native_call_with_omitted_consumer_point_is_a_failure(monkeypatch, missing_chiron):
    monkeypatch.setattr(requirements, "ephe", SimpleNamespace(Error=BackendError, calc_ut=lambda *args: None))
    with pytest.raises(AssertionError, match="Kerykeion omitted"):
        requirements.unavailable_snapshot_points(missing_chiron)


def test_unexpected_error_does_not_become_a_skip(monkeypatch, missing_chiron):
    def calculate(*args):
        raise BackendError("unexpected internal calculation failure")

    monkeypatch.setattr(requirements, "ephe", SimpleNamespace(Error=BackendError, calc_ut=calculate))
    with pytest.raises(BackendError, match="unexpected internal"):
        requirements.unavailable_snapshot_points(missing_chiron)


def test_missing_structured_warning_is_a_failure(missing_chiron):
    missing_chiron.ephemeris_warnings = []
    with pytest.raises(AssertionError, match="without an ephemeris warning"):
        requirements.unavailable_snapshot_points(missing_chiron)


@pytest.mark.skipif(BACKEND_NAME != "swisseph", reason="Swiss body-availability contract")
@pytest.mark.parametrize("data", [data for data in TEMPORAL_SUBJECTS if data["year"] < 1800],
                         ids=lambda data: data["id"])
def test_historical_omissions_are_verified_even_when_complete_snapshot_is_unavailable(data):
    subject = create_subject_from_temporal_data(data)
    unavailable = requirements.unavailable_snapshot_points(subject)
    chart = ChartDataFactory.create_natal_chart_data(subject)
    if unavailable:
        assert subject.chiron is None and "Chiron" not in subject.active_points
        assert {warning.point_name for warning in subject.ephemeris_warnings} == {"Chiron"}
        assert all(aspect.p1_name != "Chiron" and aspect.p2_name != "Chiron" for aspect in chart.aspects)
    else:
        assert subject.chiron is not None and "Chiron" in subject.active_points
