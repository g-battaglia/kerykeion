# -*- coding: utf-8 -*-
"""A golden chart may not ask the network where it was cast.

Every SVG baseline is a chart, and a chart is a moment AND a place. The moments
were always literals in the test file; the places were not. ``from_birth_data``
takes ``online=True`` by default and resolves a bare city name through GeoNames,
so the golden suite and the script that regenerates it both went to the network
for the same question and could get different answers.

They did. Running the golden comparison at four tolerances over one afternoon on
one unchanged tree gave 2, 6, 63 and 69 failures, because the coordinates moved
between runs. A baseline is a fixture; a fixture that a remote service can change
under you is not one, and no tolerance can be chosen against a target that does
not hold still.

This is the guard: with the network refused, the golden charts must still be
castable. Anything that reaches for GeoNames fails here rather than passing today
and drifting tomorrow. The places live in tests/data/golden_places.py.
"""

import pytest

from kerykeion.geonames.fetcher import FetchGeonames


class _NetworkWasAsked(AssertionError):
    """Raised in place of a GeoNames lookup, so the traceback names the caller."""


@pytest.fixture
def refuse_the_network(monkeypatch):
    def _refuse(self, *_args, **_kwargs):
        raise _NetworkWasAsked(
            "A golden chart asked GeoNames where it was cast. Give it explicit "
            "coordinates from tests/data/golden_places.py instead: a baseline whose "
            "place comes off the network is a fixture a remote service can change."
        )

    monkeypatch.setattr(FetchGeonames, "get_serialized_data", _refuse)
    return _refuse


def test_the_golden_subjects_are_cast_without_the_network(refuse_the_network):
    """The two subjects behind most of the 346 baselines, and a sidereal one."""
    import tests.core.test_chart_drawer as golden

    golden._subject_cache.clear()
    try:
        john = golden._make_john()
        paul = golden._make_paul()
        sidereal = golden._make_sidereal_subject("Lahiri", "LAHIRI")
    finally:
        golden._subject_cache.clear()

    # Cast where the baselines say they were cast, not merely cast successfully:
    # a silent fallback to Greenwich would satisfy "no network" and change every
    # chart.
    for subject in (john, paul, sidereal):
        assert (subject.lng, subject.lat) == (-2.97794, 53.41058)
        assert subject.tz_str == "Europe/London"
        assert subject.city == "Liverpool"


def test_every_golden_chart_test_survives_a_refused_network(refuse_the_network):
    """The whole file, not only its two helpers.

    Four tests spread the birth-data tuple themselves rather than going through a
    helper, and when the place came out of that tuple they were hermetic by
    accident. They are hermetic on purpose now, and this is what says so.
    """
    import inspect

    import tests.core.test_chart_drawer as golden

    golden._subject_cache.clear()
    failures = []
    try:
        for class_name in dir(golden):
            candidate = getattr(golden, class_name)
            if not inspect.isclass(candidate) or not class_name.startswith("Test"):
                continue
            for method_name in dir(candidate):
                if not method_name.startswith("test_"):
                    continue
                method = getattr(candidate, method_name)
                if len(inspect.signature(method).parameters) > 1:
                    continue  # takes fixtures; not ours to construct
                try:
                    method(candidate())
                except _NetworkWasAsked:
                    failures.append(f"{class_name}::{method_name}")
                except Exception:
                    # Any other failure is that test's business, not this one's.
                    pass
    finally:
        golden._subject_cache.clear()

    assert failures == []
