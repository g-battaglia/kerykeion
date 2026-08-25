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

from pathlib import Path

import pytest

from kerykeion.geonames.fetcher import FetchGeonames

from tests.core.test_every_baseline_has_a_reader import SVG_DIR, _names_this_run_cannot_reach
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


#: Tests in the golden modules the driver cannot call, because they take a fixture
#: — tmp_path, caplog, monkeypatch, a mock. None of them compares a baseline: they
#: write to a temporary directory or read a log. Listed by name and asserted
#: EQUAL below, so a golden test that starts taking a fixture — and so stops being
#: driven, and so stops being vouched for — shows up here instead of vanishing.
#: The first version of the driver skipped five baseline readers that way in
#: silence; the guard said "every golden test" and was wrong.
TAKES_A_FIXTURE_AND_COMPARES_NO_BASELINE = {
    "TestChartDrawerBasic::test_chart_drawer_logging",
    "TestMinifyFallbackScope::test_string_fallback_applies_when_optimizer_fails",
    "TestModernChartStyle::test_classic_only_options_warn_once_per_drawer",
    "TestModernChartStyle::test_classic_only_options_warn_under_modern",
    "TestModernChartStyle::test_default_save_filenames_carry_style_suffix",
    "TestModernChartStyle::test_modern_wheel_only_filename_does_not_claim_external_view",
    "TestModernChartStyle::test_save_modern_svg_creates_file",
    "TestModernChartStyle::test_save_modern_wheel_only_creates_file",
    "TestModernChartStyle::test_save_svg_default_filename_modern_suffix",
    "TestModernChartStyle::test_save_wheel_only_default_filename_modern_suffix",
    "TestOutputToFile::test_save_aspect_grid_only_creates_file",
    "TestOutputToFile::test_save_svg_creates_file",
    "TestOutputToFile::test_save_wheel_only_creates_file",
    "TestSvgOutputPathSafety::test_filename_traversal_is_sanitized",
    "TestSvgOutputPathSafety::test_subject_name_with_path_separators_is_sanitized",
}


#: Baselines no driven golden test hands to the comparison, and why — so the guard
#: can demand that every other one was reached with the network refused.
CAST_BY_NO_DRIVEN_GOLDEN_TEST = {
    "Moon Phases.svg": "a sheet of lunar-phase icons, read by test_lunar_phase_svg.py, which casts no chart",
    "Historical Subject - Natal Chart - Classic.svg": (
        "a 1500 chart, @extended; on the medium kernel its test fails before it can compare"
    ),
}


def test_every_golden_chart_test_survives_a_refused_network(refuse_the_network):
    """Every test in every golden module, every parametrized case — and the driver
    says which tests it could not call, so "every" is checked rather than assumed.

    Two assertions carry it. Nothing asked the network; and every stored baseline
    the kernel can reach was actually handed to the comparison — without the second,
    a golden suite that failed for any other reason before casting its chart would
    pass this guard by never getting as far as the network.
    """
    asked_the_network: list[str] = []
    not_driven: list[str] = []
    compared: set[str] = set()

    def record_nothing(baseline_path, _generated_svg, **_kwargs):
        compared.add(Path(baseline_path).name)

    def note_network_calls(qualified_name: str, failure: BaseException) -> None:
        if isinstance(failure, _NetworkWasAsked):
            asked_the_network.append(qualified_name)
        # Any other failure is that test's business, not this one's.

    drive_every_golden_test(record_nothing, on_failure=note_network_calls, on_unreachable=not_driven.append)

    assert sorted(set(asked_the_network)) == [], (
        "These golden tests asked GeoNames where their chart was cast:\n  "
        + "\n  ".join(sorted(set(asked_the_network)))
    )
    assert set(not_driven) == TAKES_A_FIXTURE_AND_COMPARES_NO_BASELINE, (
        "The driver could not call these tests, so this guard cannot vouch for them. "
        "A golden test must take nothing but its parametrize arguments (use setup_class "
        "for shared subjects); a test that compares no baseline goes in the list above.\n"
        f"  not driven, not listed: {sorted(set(not_driven) - TAKES_A_FIXTURE_AND_COMPARES_NO_BASELINE)}\n"
        f"  listed, but driven now: {sorted(TAKES_A_FIXTURE_AND_COMPARES_NO_BASELINE - set(not_driven))}"
    )
    stored = {path.name for path in SVG_DIR.glob("*.svg")}
    never_reached = sorted(stored - _names_this_run_cannot_reach() - compared - set(CAST_BY_NO_DRIVEN_GOLDEN_TEST))
    assert never_reached == [], (
        "With the network refused, no driven golden test got as far as comparing these "
        "baselines, so nothing here vouches for how their charts are cast:\n  " + "\n  ".join(never_reached)
    )
