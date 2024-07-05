from pathlib import Path
from kerykeion import AstrologicalSubject, KerykeionChartSVG

CURRENT_DIR = Path(__file__).parent
WRITE_TO_FILE = False
"""Useful to create new tests, since SWE has some errors"""


class TestCharts:
    def setup_class(self):
        self.first_subject = AstrologicalSubject("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.second_subject = AstrologicalSubject("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.lahiri_subject = AstrologicalSubject("John Lennon Lahiri", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI", geonames_username="century.boy")
        self.fagan_bradley_subject = AstrologicalSubject("John Lennon Fagan-Bradley", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY", geonames_username="century.boy")
        self.deluce_subject = AstrologicalSubject("John Lennon DeLuce", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="DELUCE", geonames_username="century.boy")
        self.j2000_subject = AstrologicalSubject("John Lennon J2000", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="J2000", geonames_username="century.boy")
        self.morinus_house_system_subject = AstrologicalSubject("John Lennon - House System Morinus", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system_identifier="M", geonames_username="century.boy")

    def test_natal_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.first_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.split("\n")

        if WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject).makeSVG()

        with open(CURRENT_DIR / "expected_natal_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_synastry_chart(self):
        synastry_chart_svg = KerykeionChartSVG(self.first_subject, "Synastry", self.second_subject).makeTemplate()
        synastry_chart_svg_lines = synastry_chart_svg.split("\n")
        
        if WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject, "Synastry", self.second_subject).makeSVG()

        with open(CURRENT_DIR / "expected_synastry_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(synastry_chart_svg_lines)):
            assert synastry_chart_svg_lines[i] == file_content_lines[i]

    def test_transit_chart(self):
        transit_chart_svg = KerykeionChartSVG(self.first_subject, "Transit", self.second_subject).makeTemplate()
        transit_chart_svg_lines = transit_chart_svg.split("\n")

        if WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject, "Transit", self.second_subject).makeSVG()

        with open(CURRENT_DIR / "expected_transit_chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(transit_chart_svg_lines)):
            assert transit_chart_svg_lines[i] == file_content_lines[i]

    def test_external_natal_chart(self):
        external_natal_chart_svg = KerykeionChartSVG(self.first_subject, "ExternalNatal").makeTemplate()
        external_natal_chart_svg_lines = external_natal_chart_svg.split("\n")

        if WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject, "ExternalNatal").makeSVG()

        with open(CURRENT_DIR / "expected_external_natal_chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(external_natal_chart_svg_lines)):
            assert external_natal_chart_svg_lines[i] == file_content_lines[i]

    def test_lahiri_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.lahiri_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.split("\n")

        if WRITE_TO_FILE:
            KerykeionChartSVG(self.lahiri_subject).makeSVG()

        with open(CURRENT_DIR / "expected_lahiri_birth_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]


    def test_fagan_bradley_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.fagan_bradley_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.split("\n")

        if WRITE_TO_FILE:
            KerykeionChartSVG(self.fagan_bradley_subject).makeSVG()

        with open(CURRENT_DIR / "expected_fagan_bradley_birth_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_deluce_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.deluce_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.split("\n")

        if WRITE_TO_FILE:
            KerykeionChartSVG(self.deluce_subject).makeSVG()

        with open(CURRENT_DIR / "expected_deluce_birth_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_j2000_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.j2000_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.split("\n")

        if WRITE_TO_FILE:
            KerykeionChartSVG(self.j2000_subject).makeSVG()

        with open(CURRENT_DIR / "expected_j2000_birth_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_morinus_house_system_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.morinus_house_system_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.split("\n")

        if WRITE_TO_FILE:
            KerykeionChartSVG(self.morinus_house_system_subject).makeSVG()

        with open(CURRENT_DIR / "expected_morinus_house_system_birth_chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.split("\n")

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]