from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.chart_data_factory import ChartDataFactory
from .compare_svg_lines import compare_svg_lines


class TestIndicatorsOff:
    WRITE_TO_FILE = False
    SVG_DIR = Path(__file__).parent / "svg"

    def _compare_chart_svg(self, file_name, chart_svg):
        chart_svg_lines = chart_svg.splitlines()

        with open(self.SVG_DIR / file_name, "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        assert len(chart_svg_lines) == len(file_content_lines), (
            f"Line count mismatch: Expected {len(file_content_lines)} lines, "
            f"but found {len(chart_svg_lines)} lines in the chart SVG."
        )

        for expected_line, actual_line in zip(file_content_lines, chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def setup_class(self):
        self.first_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True
        )
        self.second_subject = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB", suppress_geonames_warning=True
        )

    def test_natal_chart_no_indicators(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.first_subject)
        s = ChartDrawer(chart_data, show_degree_indicators=False)
        birth_chart_svg = s.generate_svg_string()
        self._compare_chart_svg("John Lennon - Natal Chart - No Degree Indicators.svg", birth_chart_svg)

    def test_synastry_chart_no_indicators(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        chart = ChartDrawer(chart_data, show_degree_indicators=False)
        chart_svg = chart.generate_svg_string()
        self._compare_chart_svg("John Lennon - Synastry Chart - No Degree Indicators.svg", chart_svg)

    def test_transit_chart_no_indicators(self):
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        chart = ChartDrawer(chart_data, show_degree_indicators=False)
        chart_svg = chart.generate_svg_string()
        self._compare_chart_svg("John Lennon - Transit Chart - No Degree Indicators.svg", chart_svg)
