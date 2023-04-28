from pathlib import Path
from kerykeion import (
    KerykeionSubject,
    KerykeionChartSVG,
)

CURRENT_DIR = Path(__file__).parent


class TestCharts:
    def setup_class(self):
        self.first_subject = KerykeionSubject("John Lennon", 1940, 10, 9, 10, 30, "Liverpool", "GB")
        self.second_subject = KerykeionSubject("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

    def test_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.first_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.split("\n")

        with open(CURRENT_DIR / "expected_birth_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_composite_chart(self):
        composite_chart_svg = KerykeionChartSVG(self.first_subject, "Composite", self.second_subject).makeTemplate()
        KerykeionChartSVG(self.first_subject, "Composite", self.second_subject).makeSVG()
        composite_chart_svg_lines = composite_chart_svg.split("\n")

        with open(CURRENT_DIR / "expected_composite_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(composite_chart_svg_lines)):
            assert composite_chart_svg_lines[i] == file_content_lines[i]
