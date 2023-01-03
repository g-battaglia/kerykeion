from pathlib import Path
from kerykeion import (
    KrInstance,
    MakeSvgInstance,
)

CURRENT_DIR = Path(__file__).parent


class TestCharts:
    def setup_class(self):
        self.first_subject = KrInstance("John Lennon", 1940, 10, 9, 10, 30, "Liverpool", "GB")
        self.second_subject = KrInstance("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

    def test_birth_chart(self):
        birth_chart_svg = MakeSvgInstance(self.first_subject).makeTemplate()
        with open(CURRENT_DIR / "expected_legacy_birth_chart.svg", "r") as f:
            file_content = f.read()

        assert birth_chart_svg == file_content

    def test_composite_chart(self):
        composite_chart_svg = MakeSvgInstance(self.first_subject, "Composite", self.second_subject).makeTemplate()
        with open(CURRENT_DIR / "expected_legacy_composite_chart.svg", "r") as f:
            file_content = f.read()

        assert composite_chart_svg == file_content