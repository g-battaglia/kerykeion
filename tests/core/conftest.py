"""
Core test fixtures and helpers for the Kerykeion test suite.

Provides:
- Canonical subject fixtures (session-scoped)
- Position comparison helpers
- SVG comparison helpers
- Report comparison helpers
- Tolerance constants
- Marker registration
"""

import pytest
from pytest import approx
from pathlib import Path
from typing import Any, Dict


# =============================================================================
# TOLERANCE CONSTANTS
# =============================================================================

POSITION_TOLERANCE = 1e-2  # 0.01 degrees (about 36 arcseconds)
SPEED_TOLERANCE = 1e-4  # For planetary speeds
DECLINATION_TOLERANCE = 1e-2  # For declinations
ORB_TOLERANCE = 1e-2  # For aspect orbs
PERCENTAGE_TOLERANCE = 2  # Integer percentages (±2%)


# =============================================================================
# CANONICAL SUBJECT FIXTURES (session-scoped)
# =============================================================================


@pytest.fixture(scope="session")
def johnny_depp():
    """
    Johnny Depp — LEGACY TEST SUBJECT.

    Birth data: June 9, 1963, 00:00, Owensboro, US (37.7742, -87.1133)
    """
    from kerykeion import AstrologicalSubjectFactory

    return AstrologicalSubjectFactory.from_birth_data(
        "Johnny Depp",
        1963,
        6,
        9,
        0,
        0,
        lat=37.7742,
        lng=-87.1133,
        tz_str="America/Chicago",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def john_lennon():
    """
    John Lennon — PRIMARY TEST SUBJECT.

    Birth data: October 9, 1940, 18:30, Liverpool, GB (53.4084, -2.9916)
    """
    from kerykeion import AstrologicalSubjectFactory

    return AstrologicalSubjectFactory.from_birth_data(
        "John Lennon",
        1940,
        10,
        9,
        18,
        30,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def yoko_ono():
    """
    Yoko Ono — for John+Yoko synastry.

    Birth data: February 18, 1933, 20:30, Tokyo, JP (35.6762, 139.6503)
    Note: Hour is 20:30 per the plan's canonical data for core tests.
    """
    from kerykeion import AstrologicalSubjectFactory

    return AstrologicalSubjectFactory.from_birth_data(
        "Yoko Ono",
        1933,
        2,
        18,
        20,
        30,
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        online=False,
        suppress_geonames_warning=True,
    )


@pytest.fixture(scope="session")
def paul_mccartney():
    """
    Paul McCartney.

    Birth data: June 18, 1942, 14:00, Liverpool, GB (53.4084, -2.9916)

    NOTE: 14:00, not the 15:30 used by the same-named fixture in tests/conftest.py
    and by the canonical ``paul_mccartney_1942`` matrix subject. Two different
    charts share one display name. This fixture shadows the root one for every
    test under tests/core/, and the hand-written expectations in test_aspects.py /
    expected_positions.py were generated from THIS 14:00 chart. Changing either
    time invalidates a different set of baselines — check which fixture a test
    actually receives before touching them.
    """
    from kerykeion import AstrologicalSubjectFactory

    return AstrologicalSubjectFactory.from_birth_data(
        "Paul McCartney",
        1942,
        6,
        18,
        14,
        0,
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
    )


# =============================================================================
# POSITION COMPARISON HELPERS
# =============================================================================


def assert_position_equal(actual: float, expected: float, abs_tol: float = POSITION_TOLERANCE) -> None:
    """Assert that two positions are equal within tolerance."""
    assert actual == approx(expected, abs=abs_tol), f"Position mismatch: got {actual}, expected {expected}"


def assert_positions_match(actual_point: Any, expected_data: Dict[str, Any]) -> None:
    """
    Assert that an actual point matches expected data dictionary.

    Args:
        actual_point: KerykeionPointModel from calculation
        expected_data: Dictionary with expected values
    """
    # Required attributes
    assert actual_point.name == expected_data["name"]
    assert actual_point.abs_pos == approx(expected_data["abs_pos"], abs=POSITION_TOLERANCE)
    assert actual_point.position == approx(expected_data["position"], abs=POSITION_TOLERANCE)
    assert actual_point.sign == expected_data["sign"]
    assert actual_point.sign_num == expected_data["sign_num"]

    # Optional attributes
    if "element" in expected_data:
        assert actual_point.element == expected_data["element"]
    if "quality" in expected_data:
        assert actual_point.quality == expected_data["quality"]
    if "retrograde" in expected_data and expected_data["retrograde"] is not None:
        assert actual_point.retrograde == expected_data["retrograde"]
    if "speed" in expected_data:
        assert actual_point.speed == approx(expected_data["speed"], abs=SPEED_TOLERANCE)
    if "declination" in expected_data:
        assert actual_point.declination == approx(expected_data["declination"], abs=DECLINATION_TOLERANCE)
    if "house" in expected_data and expected_data["house"] is not None:
        assert actual_point.house == expected_data["house"]


# =============================================================================
# SVG WELL-FORMEDNESS HELPER
# =============================================================================


def assert_svg_wellformed(svg: str, *, expect_css_variables: bool = True) -> None:
    """Validate that an SVG string is structurally sound and parseable.

    This is the primary guard against SVG generation regressions such as:
    - Attribute merging during minification (``<svgxmlns=...``)
    - Missing XML namespace declarations
    - Malformed XML due to incorrect string processing
    - Accidental removal of CSS custom properties

    Args:
        svg: The SVG string to validate.
        expect_css_variables: When True (default), assert that CSS custom
            properties (``var(--…)``) and a ``<style>`` block are present.
            Set to False when ``remove_css_variables=True`` was used.
    """
    from xml.etree import ElementTree

    assert isinstance(svg, str), f"SVG must be a string, got {type(svg).__name__}"
    assert len(svg) > 100, f"SVG suspiciously short ({len(svg)} chars)"

    # ── XML well-formedness ─────────────────────────────────────────────
    # This single check would have caught the <svgxmlns> attribute-merging
    # bug: ElementTree.fromstring() raises ParseError on malformed XML.
    try:
        tree = ElementTree.fromstring(svg)
    except ElementTree.ParseError as exc:
        # Show first 500 chars for debugging
        preview = svg[:500]
        raise AssertionError(f"SVG is not valid XML: {exc}\nFirst 500 chars:\n{preview}") from exc

    # ── Root element must be <svg> ──────────────────────────────────────
    # ElementTree expands namespaces, so tag is {ns}svg
    local_name = tree.tag.rsplit("}", 1)[-1] if "}" in tree.tag else tree.tag
    assert local_name == "svg", f"Expected <svg> root element, got <{local_name}>"

    # ── Namespace declarations ──────────────────────────────────────────
    assert "http://www.w3.org/2000/svg" in tree.tag or tree.attrib.get("xmlns") == "http://www.w3.org/2000/svg", (
        "SVG must declare xmlns='http://www.w3.org/2000/svg'"
    )

    # ── String-level anti-regression checks ─────────────────────────────
    # These catch issues that XML parsing alone might not flag
    assert "<svgxmlns" not in svg, "SVG tag name merged with attributes — minification broke attribute spacing"

    # ── CSS custom properties ───────────────────────────────────────────
    if expect_css_variables:
        assert "var(--" in svg, (
            "SVG must contain CSS custom properties (var(--…)) for consumer restyling. "
            "If remove_css_variables=True was intended, pass expect_css_variables=False."
        )
        assert "<style" in svg, "SVG must contain a <style> block with CSS custom property definitions."
    else:
        assert "var(--" not in svg, "SVG should NOT contain CSS custom properties when remove_css_variables=True"


# =============================================================================
# SVG COMPARISON HELPER
# =============================================================================


# `assert_svg_matches_baseline` stood here with no callers anywhere in the
# repository — a fourth copy of the SVG comparison, with its own third tolerance,
# that TEST.md advertised as an active helper. The one comparison lives in
# tests/data/compare_svg_lines.py; import compare_svg_file from there.


# =============================================================================
# REPORT COMPARISON HELPER
# =============================================================================


def assert_report_matches_snapshot(generated_report: str, snapshot_path: Path) -> None:
    """
    Compare a generated report against a golden snapshot file.

    Args:
        generated_report: The generated report string
        snapshot_path: Path to the golden snapshot text file
    """
    assert snapshot_path.exists(), (
        f"Report snapshot not found: {snapshot_path}\nRegenerate with: uv run poe regenerate:reports"
    )

    expected = snapshot_path.read_text()
    assert generated_report == expected, (
        f"Report mismatch for {snapshot_path.name}.\nRegenerate with: uv run poe regenerate:reports"
    )


@pytest.fixture(autouse=True)
def _skip_when_the_two_ephemerides_disagree_by_construction(request):
    """Honour ``@pytest.mark.reference_backend_only``.

    A handful of golden charts are cast two millennia back, where libephemeris and
    swisseph genuinely compute different skies — far enough apart that a planet
    changes house or an aspect falls in or out of orb, so the SVG differs in its
    STRUCTURE and not only in its numbers. One stored baseline cannot be true of
    both, and loosening the comparison until it is would reopen the hole the
    comparator was tightened to close.

    So those few say so, one at a time and with a reason, and skip off the backend
    their baseline came from. Everything else is compared structurally on every
    backend.
    """
    if request.node.get_closest_marker("reference_backend_only") is None:
        return
    from tests.data.compare_svg_lines import BASELINE_BACKEND, active_backend, numbers_are_comparable

    if not numbers_are_comparable():
        pytest.skip(
            f"The baseline was generated with {BASELINE_BACKEND}; on {active_backend()} this "
            f"chart differs in structure, not in precision."
        )
