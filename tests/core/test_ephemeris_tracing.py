"""Trace scopes must restore their caller's state on both token protocols."""

from __future__ import annotations

from contextvars import ContextVar
from types import SimpleNamespace

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.astrological_subject import factory as subject_factory
from kerykeion.ephemeris_backend import BACKEND_NAME, ephe
from kerykeion.fixed_stars import factory as star_factory


class TraceFailure(RuntimeError):
    """An error from the calculation, which cleanup must preserve."""


@pytest.mark.parametrize("scope", [subject_factory.ephemeris_trace, star_factory._star_source_trace])
@pytest.mark.parametrize("fail", [False, True], ids=["success", "exception"])
@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="Native LibEphemeris tracing contract")
def test_native_scope_restores_outer_trace(scope, fail):
    """Nested native tokens restore the outer map without swallowing errors."""
    outer = ephe.start_tracing()
    try:
        ephe.calc_ut(2451545.0, ephe.SUN)
        expected = dict(ephe.get_trace_results())
        assert expected

        def calculate():
            with scope():
                assert ephe.get_trace_results() == {}
                ephe.calc_ut(2451545.0, ephe.MOON)
                assert ephe.MOON in ephe.get_trace_results()
                if fail:
                    raise TraceFailure("calculation failed")

        if fail:
            with pytest.raises(TraceFailure, match="calculation failed"):
                calculate()
        else:
            calculate()
        assert ephe.get_trace_results() == expected
    finally:
        outer.reset()


@pytest.mark.parametrize(
    "module, scope_name",
    [
        (subject_factory, "ephemeris_trace"),
        (star_factory, "_star_source_trace"),
    ],
)
@pytest.mark.parametrize("fail", [False, True], ids=["success", "exception"])
def test_contextvar_token_remains_supported(monkeypatch, module, scope_name, fail):
    """The existing ContextVar token path remains valid on legacy backends."""
    trace = ContextVar("test_backend_trace", default=None)
    sentinel = {"outer": "unchanged"}
    outer = trace.set(sentinel)
    backend = SimpleNamespace(start_tracing=lambda: trace.set({}), get_trace_results=trace.get)
    monkeypatch.setattr(module, "BACKEND_NAME", "libephemeris")
    monkeypatch.setattr(module, "ephe", backend)
    scope = getattr(module, scope_name)
    try:

        def calculate():
            with scope():
                assert trace.get() == {}
                if fail:
                    raise TraceFailure("calculation failed")

        if fail:
            with pytest.raises(TraceFailure, match="calculation failed"):
                calculate()
        else:
            calculate()
        assert trace.get() is sentinel
    finally:
        trace.reset(outer)


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="Native LibEphemeris tracing contract")
@pytest.mark.parametrize("fail_star", [False, True], ids=["star-success", "star-exception"])
def test_subject_fixed_star_scope_restores_native_parent(monkeypatch, fail_star):
    """The factory's inline star scope restores its enclosing planetary trace."""
    outer = ephe.start_tracing()
    if fail_star:

        def unavailable_star(*args, **kwargs):
            raise TraceFailure("star calculation failed")

        monkeypatch.setattr(ephe, "fixstar_ut", unavailable_star)
    try:
        # The factory also computes nutation outside its planetary trace scope.
        # Include that legitimate label so this assertion isolates restoration.
        ephe.calc_ut(2451545.0, ephe.ECL_NUT)
        ephe.calc_ut(2451545.0, ephe.SUN)
        expected = dict(ephe.get_trace_results())
        subject = AstrologicalSubjectFactory.from_birth_data(
            name="Native trace restoration",
            year=2024,
            month=6,
            day=21,
            hour=12,
            minute=0,
            lat=41.9,
            lng=12.5,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=["Sun", "Moon"],
            active_fixed_stars=["Regulus"],
        )
        assert ephe.get_trace_results() == expected
        assert len(subject.fixed_stars) == (0 if fail_star else 1)
        assert subject.sun.source == "LEB"
        assert subject.moon.source == "LEB"
    finally:
        outer.reset()
