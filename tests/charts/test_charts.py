from pathlib import Path
from kerykeion import AstrologicalSubject, KerykeionChartSVG

CURRENT_DIR = Path(__file__).parent


class TestCharts:
    def setup_class(self):
        self.first_subject = AstrologicalSubject("John Lennon", 1940, 10, 9, 10, 30, "Liverpool", "GB")
        self.second_subject = AstrologicalSubject("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

    def test_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.first_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.split("\n")

        with open(CURRENT_DIR / "expected_birth_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_synastry_chart(self):
        synastry_chart_svg = KerykeionChartSVG(self.first_subject, "Synastry", self.second_subject).makeTemplate()
        KerykeionChartSVG(self.first_subject, "Synastry", self.second_subject).makeSVG()
        synastry_chart_svg_lines = synastry_chart_svg.split("\n")

        with open(CURRENT_DIR / "expected_synastry_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(synastry_chart_svg_lines)):
            assert synastry_chart_svg_lines[i] == file_content_lines[i]