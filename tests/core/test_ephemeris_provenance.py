"""Source propagation and sealed LEB coverage behavior."""

from __future__ import annotations

import socket
from dataclasses import dataclass

import pytest

from datetime import datetime

from kerykeion import AstrologicalSubjectFactory, EphemerisDataFactory
from kerykeion.ephemeris_backend import BACKEND_NAME, ephe


def _subject(**overrides):
    kwargs = {
        "name": "Ephemeris contract",
        "year": 1990,
        "month": 7,
        "day": 21,
        "hour": 14,
        "minute": 45,
        "city": "Liverpool",
        "nation": "GB",
        "lat": 53.4084,
        "lng": -2.9916,
        "tz_str": "Europe/London",
        "online": False,
        "calculate_lunar_phase": False,
    }
    kwargs.update(overrides)
    return AstrologicalSubjectFactory.from_birth_data(**kwargs)


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_leb_points_expose_source_precision_and_coverage() -> None:
    subject = _subject(active_points=["Sun", "Moon"])

    for point in (subject.sun, subject.moon):
        assert point is not None
        assert point.source == "LEB"
        expected_precision = "ephemeris" if point.source_reviewed else "unverified-local"
        assert point.precision_class == expected_precision
        assert point.ephemeris_coverage_start_jd is not None
        assert point.ephemeris_coverage_end_jd is not None
        dumped = point.model_dump()
        assert dumped["source"] == "LEB"
        assert dumped["precision_class"] == expected_precision


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_derived_source_does_not_depend_on_trace_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ephe, "get_trace_results", lambda: {})

    subject = _subject(active_points=["True_North_Lunar_Node", "True_South_Lunar_Node"])

    assert subject.true_south_lunar_node is not None
    assert subject.true_south_lunar_node.source == "Derived"


@dataclass
class _OutsideCoverage:
    jd_start: float = 2_400_000.0
    jd_end: float = 2_500_000.0

    def contains(self, _jd: float) -> bool:
        return False


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_uncovered_optional_body_is_reported_without_calculation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_calc_ut = ephe.calc_ut
    calls_for_chiron: list[float] = []

    def _guarded_calc_ut(jd, body_id, *args, **kwargs):  # type: ignore[no-untyped-def]
        if body_id == ephe.CHIRON:
            calls_for_chiron.append(float(jd))
            raise AssertionError("uncovered Chiron reached calc_ut")
        return real_calc_ut(jd, body_id, *args, **kwargs)

    monkeypatch.setattr(ephe, "get_body_coverage", lambda body_id: _OutsideCoverage())
    monkeypatch.setattr(ephe, "calc_ut", _guarded_calc_ut)

    subject = _subject(active_points=["Chiron"])

    assert calls_for_chiron == []
    assert subject.chiron is None
    assert subject.active_points == []
    assert len(subject.ephemeris_warnings) == 1
    warning = subject.ephemeris_warnings[0]
    assert warning.code == "date_outside_leb_coverage"
    assert warning.point_name == "Chiron"
    assert warning.body_id == ephe.CHIRON


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_ephemeris_series_preserves_coverage_warnings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ephe, "get_body_coverage", lambda body_id: _OutsideCoverage())

    factory = EphemerisDataFactory(
        start_datetime=datetime(1990, 7, 21, 12),
        end_datetime=datetime(1990, 7, 22, 12),
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        active_points=["Chiron"],
    )

    rows = factory.get_ephemeris_data(as_model=True)

    assert len(rows) == 2
    assert all(row.planets == [] for row in rows)
    assert all(len(row.ephemeris_warnings) == 1 for row in rows)
    assert all(row.ephemeris_warnings[0].code == "date_outside_leb_coverage" for row in rows)


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_leb_mode_is_socket_sealed(monkeypatch: pytest.MonkeyPatch) -> None:
    attempts: list[str] = []

    def _blocked_connect(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        attempts.append("connect")
        raise AssertionError("socket connection attempted")

    def _blocked_dns(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        attempts.append("dns")
        raise AssertionError("DNS resolution attempted")

    monkeypatch.setattr(socket.socket, "connect", _blocked_connect)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked_dns)

    subject = _subject(active_points=["Sun", "Moon"])

    assert subject.sun is not None
    assert subject.moon is not None
    assert ephe.get_network_policy() == "sealed"
    assert attempts == []
