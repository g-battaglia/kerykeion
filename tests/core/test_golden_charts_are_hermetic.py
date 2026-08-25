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

This is the guard: with the network refused, every golden test in every golden
module must still cast its chart. Anything that reaches for GeoNames fails here
rather than passing today and drifting tomorrow. The places live in
tests/data/golden_places.py.

The first version of this guard drove one module and skipped every parametrized
test, which is where twenty-nine of the network calls were — the language charts
and the cross-combination matrix. It also drove the tests through the real
comparison, whose ``pytest.skip`` on a foreign backend ended the guard as skipped
at the first chart. Now it drives all four modules, every case, through a
comparison that records nothing and raises nothing.
"""

import pytest

from kerykeion.geonames.fetcher import FetchGeonames

from tests.data.golden_drive import drive_every_golden_test


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

    # Both doors: the city lookup, and the timezone-for-coordinates lookup that
    # from_birth_data opens when it has a latitude and longitude but no tz_str.
    monkeypatch.setattr(FetchGeonames, "get_serialized_data", _refuse)
    monkeypatch.setattr(FetchGeonames, "get_timezone_for_coordinates", _refuse)
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
    """Every test in every golden module, every parametrized case."""
    asked_the_network: list[str] = []

    def record_nothing(_baseline_path, _generated_svg, **_kwargs):
        pass

    def note_network_calls(qualified_name: str, failure: BaseException) -> None:
        if isinstance(failure, _NetworkWasAsked):
            asked_the_network.append(qualified_name)
        # Any other failure is that test's business, not this one's.

    drive_every_golden_test(record_nothing, on_failure=note_network_calls)

    assert sorted(set(asked_the_network)) == [], (
        "These golden tests asked GeoNames where their chart was cast:\n  "
        + "\n  ".join(sorted(set(asked_the_network)))
    )
