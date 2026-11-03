"""Integration contracts specific to the experimental native v4 backend."""

import importlib.machinery
import subprocess
import sys

import pytest

from kerykeion import AstrologicalSubjectFactory
from kerykeion.astrological_subject.factory import ephemeris_trace
from kerykeion.ephemeris_backend import BACKEND_NAME, ephe, ephemeris_session
from kerykeion.fixed_stars.factory import _star_source_trace

pytestmark = pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="Rust v4 backend contract")


def test_backend_is_native_v4_without_python_astronomy_engines():
    import libephemeris._core as core

    assert ephe.__version__.startswith("4.")
    assert any(core.__file__.endswith(suffix) for suffix in importlib.machinery.EXTENSION_SUFFIXES)
    # Other tests deliberately import Skyfield as an independent oracle.
    # Probe a clean interpreter, not pytest's shared collection-time imports.
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "import kerykeion, sys; assert not {'skyfield', 'jplephem', 'numpy'}.intersection(sys.modules)",
        ],
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr


@pytest.mark.parametrize("inner_scope", [ephemeris_trace, _star_source_trace])
@pytest.mark.parametrize("fail", [False, True])
def test_native_trace_scope_resets_even_on_error(inner_scope, fail):
    assert ephe.get_trace_results() == {}
    try:
        with inner_scope():
            ephe.calc_ut(2451545.0, ephe.MOON, ephe.FLG_SPEED)
            assert ephe.MOON in ephe.get_trace_results()
            if fail:
                raise RuntimeError("intentional scope failure")
    except RuntimeError as exc:
        assert str(exc) == "intentional scope failure"
    assert ephe.get_trace_results() == {}
    with ephemeris_trace():
        ephe.calc_ut(2451545.0, ephe.SUN, ephe.FLG_SPEED)
        assert ephe.get_trace_results() == {ephe.SUN: "LEB"}
    assert ephe.get_trace_results() == {}


def test_subject_with_fixed_star_leaves_no_native_trace_scope():
    subject = AstrologicalSubjectFactory.from_birth_data(
        "Rust tracing",
        2000,
        1,
        1,
        12,
        0,
        lat=41.9,
        lng=12.5,
        tz_str="Europe/Rome",
        online=False,
        active_points=["Sun", "Moon", "Ascendant"],
        active_fixed_stars=["Regulus"],
    )
    assert subject.sun.source == "LEB"
    assert len(subject.fixed_stars) == 1
    # The native fixed-star route now emits its actual provider (#17).
    assert subject.fixed_stars[0].source == "LEB"
    assert subject.fixed_stars[0].precision_class == "ephemeris"
    assert 149.0 < subject.fixed_stars[0].abs_pos < 150.0
    assert ephe.get_trace_results() == {}


def test_session_cleanup_preserves_sealed_leb_mode():
    with ephemeris_session(zodiac_type="Sidereal", sidereal_mode="LAHIRI") as flags:
        ephe.calc_ut(2451545.0, ephe.SUN, flags)
    assert ephe.get_calc_mode() == "leb"
    assert ephe.get_network_policy() == "sealed"
