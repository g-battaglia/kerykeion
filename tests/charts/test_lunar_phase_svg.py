from pathlib import Path

from kerykeion.charts.charts_utils import makeLunarPhase

from .compare_svg_lines import compare_svg_lines


class TestLunarPhaseSVG:
    PHASE_ANGLES = (0, 45, 90, 135, 180, 225, 270, 315)
    SVG_DIR = Path(__file__).parent / "svg"

    def test_all_standard_phases_match_reference_sheet(self) -> None:
        icon_groups: list[str] = []

        for index, angle in enumerate(self.PHASE_ANGLES):
            icon_svg = makeLunarPhase(angle, 0.0)
            unique_clip_id = f"moonPhaseCutOffCircle{index}"
            icon_svg = icon_svg.replace("moonPhaseCutOffCircle", unique_clip_id)

            translated_block = [f"    <g transform=\"translate({index * 40},0)\">"]
            translated_block.extend(
                f"        {line}" for line in icon_svg.splitlines()
            )
            translated_block.append("    </g>")
            icon_groups.extend(translated_block)

        generated_lines = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="40" viewBox="0 0 320 40">',
            '    <style>',
            '        :root {',
            '            --kerykeion-chart-color-lunar-phase-0: #000000;',
            '            --kerykeion-chart-color-lunar-phase-1: #ffffff;',
            '        }',
            '    </style>',
        ]
        generated_lines.extend(icon_groups)
        generated_lines.append("</svg>")

        generated_svg = "\n".join(generated_lines)

        expected_path = self.SVG_DIR / "Moon Phases.svg"
        expected_lines = expected_path.read_text(encoding="utf-8").splitlines()
        actual_lines = generated_svg.splitlines()

        assert len(actual_lines) == len(expected_lines), (
            "Line count mismatch: expected "
            f"{len(expected_lines)}, got {len(actual_lines)}"
        )

        for expected_line, actual_line in zip(expected_lines, actual_lines):
            compare_svg_lines(expected_line, actual_line)
