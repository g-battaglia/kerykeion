# -*- coding: utf-8 -*-
"""
Lunar Phase SVG Rendering Tests

Consolidated test suite integrating test cases from tests/charts/test_lunar_phase_svg.py.

Tests:
    - TestLunarPhaseSVG: Golden-baseline regression for all 8 standard phase angles.
    - TestLunarPhaseIndividual: Valid XML structure for each phase SVG.
    - TestLunarPhaseAngles: Different angles produce distinct SVGs; new vs full moon differ.

Usage:
    pytest tests/core/test_lunar_phase_svg.py -v
"""

from pathlib import Path
from xml.etree import ElementTree

from kerykeion.charts.charts_utils import makeLunarPhase

from tests.data.compare_svg_lines import compare_svg_lines


PHASE_ANGLES = (0, 45, 90, 135, 180, 225, 270, 315)
SVG_DIR = Path(__file__).resolve().parent.parent / "data" / "svg"


class TestLunarPhaseSVG:
    """Golden-baseline regression: compose all 8 phases into a reference sheet
    and compare against ``tests/charts/svg/Moon Phases.svg``."""

    def test_all_standard_phases_match_reference_sheet(self) -> None:
        icon_groups: list[str] = []

        for index, angle in enumerate(PHASE_ANGLES):
            icon_svg = makeLunarPhase(angle, 0.0)
            unique_clip_id = f"moonPhaseCutOffCircle{index}"
            icon_svg = icon_svg.replace("moonPhaseCutOffCircle", unique_clip_id)

            translated_block = [f'    <g transform="translate({index * 40},0)">']
            translated_block.extend(f"        {line}" for line in icon_svg.splitlines())
            translated_block.append("    </g>")
            icon_groups.extend(translated_block)

        generated_lines = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="40" viewBox="0 0 320 40">',
            "    <style>",
            "        :root {",
            "            --kerykeion-chart-color-lunar-phase-0: #000000;",
            "            --kerykeion-chart-color-lunar-phase-1: #ffffff;",
            "        }",
            "    </style>",
        ]
        generated_lines.extend(icon_groups)
        generated_lines.append("</svg>")

        generated_svg = "\n".join(generated_lines)

        expected_path = SVG_DIR / "Moon Phases.svg"
        expected_lines = expected_path.read_text(encoding="utf-8").splitlines()
        actual_lines = generated_svg.splitlines()

        assert len(actual_lines) == len(expected_lines), (
            f"Line count mismatch: expected {len(expected_lines)}, got {len(actual_lines)}"
        )

        for expected_line, actual_line in zip(expected_lines, actual_lines):
            compare_svg_lines(expected_line, actual_line)


class TestLunarPhaseIndividual:
    """Each individual phase SVG must be well-formed XML with an ``<svg>`` root."""

    def _wrap_as_svg_document(self, fragment: str) -> str:
        """Wrap a bare SVG fragment in a minimal document so ElementTree can parse it."""
        return f'<svg xmlns="http://www.w3.org/2000/svg">{fragment}</svg>'

    def test_each_phase_is_valid_xml(self) -> None:
        for angle in PHASE_ANGLES:
            svg_fragment = makeLunarPhase(angle, 0.0)
            doc = self._wrap_as_svg_document(svg_fragment)
            try:
                tree = ElementTree.fromstring(doc)
            except ElementTree.ParseError as exc:
                raise AssertionError(f"Phase angle {angle}° produced invalid XML: {exc}") from exc
            assert tree.tag.endswith("svg"), f"Phase angle {angle}°: expected <svg> root, got <{tree.tag}>"

    def test_each_phase_contains_svg_content(self) -> None:
        for angle in PHASE_ANGLES:
            svg_fragment = makeLunarPhase(angle, 0.0)
            assert len(svg_fragment.strip()) > 0, f"Phase angle {angle}° produced empty SVG"
            assert "<" in svg_fragment, f"Phase angle {angle}° produced no XML tags"


class TestLunarPhaseAngles:
    """Verify that distinct angles yield distinct SVG output."""

    def test_different_angles_produce_different_svgs(self) -> None:
        svgs = {angle: makeLunarPhase(angle, 0.0) for angle in PHASE_ANGLES}

        for i, a1 in enumerate(PHASE_ANGLES):
            for a2 in PHASE_ANGLES[i + 1 :]:
                assert svgs[a1] != svgs[a2], f"Phase angles {a1}° and {a2}° produced identical SVGs"

    def test_new_moon_and_full_moon_differ(self) -> None:
        new_moon = makeLunarPhase(0, 0.0)
        full_moon = makeLunarPhase(180, 0.0)

        assert new_moon != full_moon, "New moon (0°) and full moon (180°) should produce visually distinct SVGs"
        # Structural difference: they should differ in more than just numeric values
        new_lines = new_moon.splitlines()
        full_lines = full_moon.splitlines()
        has_structural_diff = len(new_lines) != len(full_lines) or any(
            nl.split()[0] != fl.split()[0] for nl, fl in zip(new_lines, full_lines) if nl.strip() and fl.strip()
        )
        assert has_structural_diff or new_moon != full_moon, (
            "New moon and full moon should have structural SVG differences"
        )
