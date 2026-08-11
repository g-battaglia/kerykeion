"""Source propagation and sealed LEB coverage behavior."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from datetime import datetime

from kerykeion import AstrologicalSubjectFactory, EphemerisDataFactory
from kerykeion.ephemeris_backend import BACKEND_NAME, ephe


def _require_medium_tier() -> None:
    """Skip unless the loaded ephemeris is exactly the medium (DE440) kernel.

    Same gate the other deep-time boundary tests use (see
    ``test_void_of_course_moon_factory.test_range_edge_dates_raise_kerykeion_exception``):
    the 16th-century scenarios below are only meaningful on the medium kernel —
    base cannot reach them at all and extended covers them too well.
    """
    from tests.conftest import _detect_ephemeris_tier

    if _detect_ephemeris_tier() != "medium":
        pytest.skip("Requires the medium (DE440) kernel's ~1550 lower range.")


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
        body_id = ephe.SUN if point.name == "Sun" else ephe.MOON
        coverage = ephe.get_body_coverage(body_id, subject.julian_day)
        assert coverage is not None
        assert point.precision_class == coverage.precision_class
        assert point.ephemeris_coverage_start_jd is not None
        assert point.ephemeris_coverage_end_jd is not None
        dumped = point.model_dump()
        assert dumped["source"] == "LEB"
        assert dumped["precision_class"] == coverage.precision_class


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_derived_source_does_not_depend_on_trace_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ephe, "get_trace_results", lambda: {ephe.TRUE_NODE: "LEB"})

    subject = _subject(active_points=["True_North_Lunar_Node", "True_South_Lunar_Node"])

    assert subject.true_north_lunar_node is not None
    assert subject.true_south_lunar_node is not None
    assert subject.true_north_lunar_node.precision_class is not None
    assert subject.true_south_lunar_node.source == "Derived"
    assert (
        subject.true_south_lunar_node.precision_class
        == subject.true_north_lunar_node.precision_class
    )
    assert (
        subject.true_south_lunar_node.ephemeris_coverage_start_jd
        == subject.true_north_lunar_node.ephemeris_coverage_start_jd
    )
    assert (
        subject.true_south_lunar_node.ephemeris_coverage_end_jd
        == subject.true_north_lunar_node.ephemeris_coverage_end_jd
    )
    assert (
        subject.true_south_lunar_node.source_reviewed
        == subject.true_north_lunar_node.source_reviewed
    )


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
@pytest.mark.parametrize(
    ("trace_label", "expected_class"),
    [
        # Tabulated ephemeris reads: genuinely ephemeris-grade.
        ("SPK", "ephemeris"),
        ("Skyfield", "ephemeris"),
        # Explicitly recognized lower-precision models.
        ("Keplerian", "approximate"),
        ("Analytical", "analytical"),
        # ASSIST is libephemeris' live n-body integration fallback, which
        # libephemeris itself classifies as "numerical-model". An unrecognized
        # label must not be promoted to "ephemeris" either.
        ("ASSIST", "numerical-model"),
        ("SomeFutureBackend", "numerical-model"),
    ],
)
def test_trace_label_maps_to_an_honest_precision_class(
    monkeypatch: pytest.MonkeyPatch, trace_label: str, expected_class: str
) -> None:
    """The coarse source -> precision_class mapping must never overstate.

    Only the tabulated-ephemeris labels earn "ephemeris"; anything the mapping
    does not recognize falls back to "numerical-model".
    """
    monkeypatch.setattr(ephe, "get_trace_results", lambda: {ephe.CHIRON: trace_label})

    subject = _subject(active_points=["Chiron"])

    assert subject.chiron is not None
    assert subject.chiron.source == trace_label
    assert subject.chiron.precision_class == expected_class


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_arabic_parts_inherit_derived_provenance_from_primaries() -> None:
    subject = _subject(active_points=["Sun", "Moon", "Ascendant", "Pars_Fortunae"])

    assert subject.sun is not None
    assert subject.moon is not None
    assert subject.pars_fortunae is not None

    part = subject.pars_fortunae
    assert part.source == "Derived"

    primaries = [subject.sun, subject.moon]
    primary_classes = {p.precision_class for p in primaries if p.precision_class is not None}
    assert primary_classes, "test premise: Sun/Moon must carry precision metadata"
    if len(primary_classes) == 1:
        assert part.precision_class == next(iter(primary_classes))
    else:
        assert part.precision_class == "mixed"

    starts = [p.ephemeris_coverage_start_jd for p in primaries if p.ephemeris_coverage_start_jd is not None]
    ends = [p.ephemeris_coverage_end_jd for p in primaries if p.ephemeris_coverage_end_jd is not None]
    assert part.ephemeris_coverage_start_jd == max(starts)
    assert part.ephemeris_coverage_end_jd == min(ends)

    reviewed = [p.source_reviewed for p in primaries if p.source_reviewed is not None]
    if reviewed:
        assert part.source_reviewed == all(reviewed)

    # The Ascendant itself is direct house geometry: it stays unannotated and
    # must not have diluted the inherited contract.
    assert subject.ascendant is not None
    assert subject.ascendant.source is None


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_relocation_preserves_derived_lot_provenance() -> None:
    from kerykeion.relocated_chart.factory import RelocatedChartFactory

    subject = _subject(active_points=["Sun", "Moon", "Ascendant", "Pars_Fortunae"])
    part = subject.pars_fortunae
    assert part is not None
    assert part.source == "Derived"

    relocated = RelocatedChartFactory.relocate(
        subject,
        new_lat=40.7128,
        new_lng=-74.006,
        new_city="New York",
        new_nation="US",
        new_tz_str="America/New_York",
    )
    moved = relocated.pars_fortunae
    assert moved is not None
    assert moved.source == "Derived"
    assert moved.precision_class == part.precision_class
    assert moved.ephemeris_coverage_start_jd == part.ephemeris_coverage_start_jd
    assert moved.ephemeris_coverage_end_jd == part.ephemeris_coverage_end_jd
    assert moved.source_reviewed == part.source_reviewed


@dataclass
class _OutsideCoverage:
    jd_start: float = 2_400_000.0
    jd_end: float = 2_500_000.0
    precision_class: str = "ephemeris"
    reviewed: bool = True

    def contains(self, _jd: float) -> bool:
        return False


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_inventory_range_does_not_preempt_engine_source_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_calc_ut = ephe.calc_ut
    calls_for_chiron: list[float] = []

    def _observed_calc_ut(jd, body_id, *args, **kwargs):  # type: ignore[no-untyped-def]
        if body_id == ephe.CHIRON:
            calls_for_chiron.append(float(jd))
        return real_calc_ut(jd, body_id, *args, **kwargs)

    # Both arguments are required on purpose: the factory must call the rc14
    # date-aware form get_body_coverage(body_id, jd) — a regression to the old
    # one-argument call would raise TypeError here and fail the test.
    monkeypatch.setattr(ephe, "get_body_coverage", lambda body_id, jd: _OutsideCoverage())
    monkeypatch.setattr(ephe, "calc_ut", _observed_calc_ut)

    subject = _subject(active_points=["Chiron"])

    assert len(calls_for_chiron) == 2
    assert subject.chiron is not None
    assert subject.active_points == ["Chiron"]
    assert subject.ephemeris_warnings == []


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_default_chart_uses_traced_local_fallback_outside_chiron_leb_range() -> None:
    """1580 sits inside the medium (DE440) range but outside Chiron's LEB
    coverage, so the default chart falls back to the traced local Keplerian
    model.

    Gated to the medium kernel like the other boundary tests in this PR: on a
    base install (1849+) the subject's own Sun/Moon raise KerykeionException and
    this would ERROR rather than skip, while on extended the wider numerical
    trajectory can cover 1580, breaking both the premise
    (``not coverage.contains(jd)``) and the Keplerian source assertion.
    """
    _require_medium_tier()

    subject = _subject(year=1580, month=7, day=21, tz_str="Etc/GMT")

    coverage = ephe.get_body_coverage(ephe.CHIRON, subject.julian_day)
    assert coverage is not None
    assert not coverage.contains(subject.julian_day)
    assert subject.chiron is not None
    assert subject.chiron.source == "Keplerian"
    assert subject.chiron.precision_class == "approximate"
    assert subject.chiron.source_reviewed is not True
    assert "Chiron" in subject.active_points
    assert subject.ephemeris_warnings == []


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_ephemeris_series_preserves_fallback_source_per_sample() -> None:
    """The same 1580 Chiron fallback, asserted per sample across a series.
    Tier-gated for the same reason as the single-chart test above.
    """
    _require_medium_tier()

    factory = EphemerisDataFactory(
        start_datetime=datetime(1580, 7, 21, 12),
        end_datetime=datetime(1580, 7, 22, 12),
        lat=53.4084,
        lng=-2.9916,
        tz_str="Etc/GMT",
        active_points=["Chiron"],
    )

    rows = factory.get_ephemeris_data(as_model=True)

    assert len(rows) == 2
    assert all(len(row.planets) == 1 for row in rows)
    assert all(row.planets[0].name == "Chiron" for row in rows)
    assert all(row.planets[0].source == "Keplerian" for row in rows)
    assert all(row.planets[0].precision_class == "approximate" for row in rows)
    assert all(row.ephemeris_warnings == [] for row in rows)


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_optional_failure_is_reported_as_a_structured_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_calc_ut = ephe.calc_ut

    def _fail_chiron(jd, body_id, *args, **kwargs):  # type: ignore[no-untyped-def]
        if body_id == ephe.CHIRON:
            raise RuntimeError("sensitive /internal/path must stay in logs")
        return real_calc_ut(jd, body_id, *args, **kwargs)

    monkeypatch.setattr(ephe, "calc_ut", _fail_chiron)

    subject = _subject(active_points=["Chiron"])

    assert subject.chiron is None
    assert subject.active_points == []
    assert len(subject.ephemeris_warnings) == 1
    warning = subject.ephemeris_warnings[0]
    assert warning.point_name == "Chiron"
    assert warning.body_id == ephe.CHIRON
    assert warning.requested_jd == subject.julian_day
    assert warning.code == "ephemeris_calculation_failed"
    assert "/internal/path" not in warning.message


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="libephemeris contract")
def test_leb_network_gate_rejects_before_socket_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from libephemeris.net import NetworkSealedError, require_network

    attempts: list[str] = []

    def _blocked_connect(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        attempts.append("connect")
        raise AssertionError("socket connection attempted")

    def _blocked_dns(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        attempts.append("dns")
        raise AssertionError("DNS resolution attempted")

    monkeypatch.setattr("socket.socket.connect", _blocked_connect)
    monkeypatch.setattr("socket.getaddrinfo", _blocked_dns)

    assert ephe.get_network_policy() == "sealed"
    with pytest.raises(NetworkSealedError):
        require_network("Kerykeion sealed-mode regression probe")
    assert attempts == []
