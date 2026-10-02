"""Public coefficient scopes integrate centrally without changing factory APIs."""

from __future__ import annotations

from pathlib import Path

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.ephemeris_backend import backend


@pytest.fixture
def routed(monkeypatch):
    ephe = backend.ephe
    if not hasattr(ephe, "calculation_session"):
        pytest.skip("Requires coefficient-session backend")
    old_mode = ephe.get_calc_mode()
    old_tier = ephe.get_precision_tier()
    old_policy = ephe.get_configured_network_policy()
    path = Path(ephe.__file__).parent / "data/leb2/base_core.leb2"
    ephe.set_tier_routes({"base": ephe.TierRoute("leb", (str(path),))})
    ephe.set_calc_mode("routed")
    ephe.set_precision_tier("base")
    ephe.set_network_policy("auto")
    monkeypatch.setattr(backend, "_PINNED_LEB_MODE", "routed")
    try:
        yield ephe
    finally:
        ephe.set_tier_routes(None)
        ephe.set_calc_mode(old_mode)
        ephe.set_precision_tier(old_tier)
        ephe.set_network_policy(old_policy)


def subject():
    return AstrologicalSubjectFactory.from_birth_data(
        name="Coefficient scope",
        year=2000,
        month=1,
        day=1,
        hour=12,
        minute=0,
        lat=41.9,
        lng=12.5,
        tz_str="UTC",
        online=False,
        active_points=["Sun", "Moon", "Mars"],
        calculate_lunar_phase=False,
    )


def test_chart_uses_one_public_scope_and_retains_local_source(routed, monkeypatch):
    from libephemeris.db import backend as db

    owners = []
    original = routed.calc_ut

    def calculate(*args, **kwargs):
        owners.append(db._operation_state.reader)
        return original(*args, **kwargs)

    monkeypatch.setattr(routed, "calc_ut", calculate)
    result = subject()
    assert owners and all(owner is owners[0] for owner in owners)
    assert db._operation_state.reader is None
    assert result.sun.source == result.mars.source == "LEB"
    assert result.sun.precision_class == "ephemeris"
    assert routed.get_calc_mode() == "routed"


def test_optional_body_storage_failure_cannot_return_partial_chart(routed, monkeypatch):
    from libephemeris.operations import source_guard
    from libephemeris.db import backend as db

    original = routed.calc_ut

    @source_guard
    def calculate(jd, body, flags=0):
        if body == routed.MARS:
            raise routed.DBError("Test coefficient outage")
        return original(jd, body, flags)

    monkeypatch.setattr(routed, "calc_ut", calculate)
    with pytest.raises(routed.DBError, match="outage"):
        subject()
    assert db._operation_state.reader is None


def test_transit_refinement_cannot_swallow_a_fatal_source_error(routed, monkeypatch):
    from libephemeris.operations import source_guard
    from kerykeion.transits.factory import TransitsTimeRangeFactory

    factory = object.__new__(TransitsTimeRangeFactory)
    factory.natal_chart = subject()

    @source_guard
    def unavailable(*args, **kwargs):
        raise routed.DBError("Refinement source outage")

    monkeypatch.setattr(routed, "calc_ut", unavailable)
    with pytest.raises(routed.DBError, match="Refinement"):
        factory._refine_exact_moment("Mars", "Sun", "conjunction", "2000-01-01T00:00:00", "2000-01-02T00:00:00")


def test_station_factory_retains_fatal_category_through_normalization(routed, monkeypatch):
    from libephemeris.operations import source_guard
    from kerykeion.retrograde_stations.factory import RetrogradeStationFactory

    @source_guard
    def unavailable(*args, **kwargs):
        raise routed.DBDataError("Station source corruption")

    monkeypatch.setattr(routed, "calc_ut", unavailable)
    with pytest.raises(routed.DBDataError, match="Station"):
        RetrogradeStationFactory.from_julian_day(2451545.0, 2451550.0, planets=["Mars"])


def test_existing_session_nesting_guard_remains(routed):
    with backend.ephemeris_session():
        with pytest.raises(RuntimeError):
            with backend.ephemeris_session():
                pass
