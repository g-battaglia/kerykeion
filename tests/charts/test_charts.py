from pathlib import Path
from kerykeion import AstrologicalSubject, KerykeionChartSVG

CURRENT_DIR = Path(__file__).parent


class TestCharts:
    def setup_class(self):
        self.first_subject = AstrologicalSubject("John Lennon", 1940, 10, 9, 10, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.second_subject = AstrologicalSubject("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB", geonames_username="century.boy")

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
        synastry_chart_svg_lines = synastry_chart_svg.split("\n")

        with open(CURRENT_DIR / "expected_synastry_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(synastry_chart_svg_lines)):
            assert synastry_chart_svg_lines[i] == file_content_lines[i]

    def test_transit_chart(self):
        transit_chart_svg = KerykeionChartSVG(self.first_subject, "Transit", self.second_subject).makeTemplate()
        transit_chart_svg_lines = transit_chart_svg.split("\n")

        with open(CURRENT_DIR / "expected_transit_chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(transit_chart_svg_lines)):
            assert transit_chart_svg_lines[i] == file_content_lines[i]

    def test_external_natal_chart(self):
        external_natal_chart_svg = KerykeionChartSVG(self.first_subject, "ExternalNatal").makeTemplate()
        KerykeionChartSVG(self.first_subject, "ExternalNatal").makeSVG()
        external_natal_chart_svg_lines = external_natal_chart_svg.split("\n")

        with open(CURRENT_DIR / "expected_external_natal_chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(external_natal_chart_svg_lines)):
            assert external_natal_chart_svg_lines[i] == file_content_lines[i]
