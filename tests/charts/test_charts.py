from pathlib import Path
from kerykeion import AstrologicalSubject, KerykeionChartSVG


class TestCharts:
    SPLIT_LINE_LENGTH = 80  # Define the length of lines to split for comparison
    WRITE_TO_FILE = False  # Change this flag as needed
    CURRENT_DIR = Path(__file__).parent

    def _compare_chart_svg(self, file_name, chart_svg):
        chart_svg_lines = [chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(chart_svg), self.SPLIT_LINE_LENGTH)]

        with open(self.CURRENT_DIR / file_name, "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(chart_svg_lines)):
            assert chart_svg_lines[i] == file_content_lines[i]
            
    def setup_class(self):
        self.first_subject = AstrologicalSubject("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.second_subject = AstrologicalSubject("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.lahiri_subject = AstrologicalSubject("John Lennon Lahiri", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI", geonames_username="century.boy")
        self.fagan_bradley_subject = AstrologicalSubject("John Lennon Fagan-Bradley", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY", geonames_username="century.boy")
        self.deluce_subject = AstrologicalSubject("John Lennon DeLuce", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="DELUCE", geonames_username="century.boy")
        self.j2000_subject = AstrologicalSubject("John Lennon J2000", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="J2000", geonames_username="century.boy")
        self.morinus_house_system_subject = AstrologicalSubject("John Lennon - House System Morinus", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system_identifier="M", geonames_username="century.boy")
        self.heliocentric_perspective_natal_chart = AstrologicalSubject("John Lennon - Heliocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy", perspective_type="Heliocentric")
        self.topocentric_perspective_natal_chart = AstrologicalSubject("John Lennon - Topocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy", perspective_type="Topocentric")
        self.true_geocentric_perspective_natal_chart = AstrologicalSubject("John Lennon - True Geocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy", perspective_type="True Geocentric")
        self.minified_natal_chart = AstrologicalSubject("John Lennon - Minified", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.dark_theme_natal_chart = AstrologicalSubject("John Lennon - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.dark_high_contrast_theme_natal_chart = AstrologicalSubject("John Lennon - Dark High Contrast Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.light_theme_natal_chart = AstrologicalSubject("John Lennon - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.dark_theme_external_subject = AstrologicalSubject("John Lennon - Dark Theme External", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.dark_theme_synastry_subject = AstrologicalSubject("John Lennon - DTS", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.wheel_only_subject = AstrologicalSubject("John Lennon - Wheel Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")

        self.wheel_external_subject = AstrologicalSubject("John Lennon - Wheel External Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.wheel_synastry_subject = AstrologicalSubject("John Lennon - Wheel Synastry Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.wheel_transit_subject = AstrologicalSubject("John Lennon - Wheel Transit Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.sidereal_dark_subject = AstrologicalSubject("John Lennon Lahiri - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        self.sidereal_light_subject = AstrologicalSubject("John Lennon Fagan-Bradley - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY")
        self.aspect_grid_only_subject = AstrologicalSubject("John Lennon - Aspect Grid Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_dark_subject = AstrologicalSubject("John Lennon - Aspect Grid Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_light_subject = AstrologicalSubject("John Lennon - Aspect Grid Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_synastry_subject = AstrologicalSubject("John Lennon - Aspect Grid Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_transit_subject = AstrologicalSubject("John Lennon - Aspect Grid Transit", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_dark_synastry_subject = AstrologicalSubject("John Lennon - Aspect Grid Dark Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.transit_chart_with_table_grid_subject = AstrologicalSubject("John Lennon - TCWTG", 1940, 10, 9, 18, 30, "Liverpool", "GB")

        # Language Tests
        self.chinese_subject = AstrologicalSubject("Hua Chenyu", 1990, 2, 7, 12, 0, "Hunan", "CN")
        self.french_subject = AstrologicalSubject("Jeanne Moreau", 1928, 1, 23, 10, 0, "Paris", "FR")
        self.spanish_subject = AstrologicalSubject("Antonio Banderas", 1960, 8, 10, 12, 0, "Malaga", "ES")
        self.portuguese_subject = AstrologicalSubject("Cristiano Ronaldo", 1985, 2, 5, 5, 25, "Funchal", "PT")
        self.italian_subject = AstrologicalSubject("Sophia Loren", 1934, 9, 20, 2, 0, "Rome", "IT")
        self.russian_subject = AstrologicalSubject("Mikhail Bulgakov", 1891, 5, 15, 12, 0, "Kiev", "UA")
        self.turkish_subject = AstrologicalSubject("Mehmet Oz", 1960, 6, 11, 12, 0, "Istanbul", "TR")
        self.german_subject = AstrologicalSubject("Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE")
        self.hindi_subject = AstrologicalSubject("Amitabh Bachchan", 1942, 10, 11, 4, 0, "Allahabad", "IN")

    def test_natal_chart(self):
        s = KerykeionChartSVG(self.first_subject)
        birth_chart_svg = s.makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject).makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    '''
    def test_synastry_chart(self):
        synastry_chart_svg = KerykeionChartSVG(self.first_subject, "Synastry", self.second_subject).makeTemplate()
        synastry_chart_svg_lines = [synastry_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(synastry_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject, "Synastry", self.second_subject).makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Synastry Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(synastry_chart_svg_lines)):
            assert synastry_chart_svg_lines[i] == file_content_lines[i]

    def test_transit_chart(self):
        transit_chart_svg = KerykeionChartSVG(self.first_subject, "Transit", self.second_subject).makeTemplate()
        transit_chart_svg_lines = [transit_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(transit_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject, "Transit", self.second_subject).makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Transit Chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(transit_chart_svg_lines)):
            assert transit_chart_svg_lines[i] == file_content_lines[i]

    def test_external_natal_chart(self):
        external_natal_chart_svg = KerykeionChartSVG(self.first_subject, "ExternalNatal").makeTemplate()
        external_natal_chart_svg_lines = [external_natal_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(external_natal_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject, "ExternalNatal").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - ExternalNatal Chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(external_natal_chart_svg_lines)):
            assert external_natal_chart_svg_lines[i] == file_content_lines[i]

    def test_lahiri_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.lahiri_subject).makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.lahiri_subject).makeSVG()

        with open(self.CURRENT_DIR / "John Lennon Lahiri - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_fagan_bradley_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.fagan_bradley_subject).makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.fagan_bradley_subject).makeSVG()

        with open(self.CURRENT_DIR / "John Lennon Fagan-Bradley - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_deluce_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.deluce_subject).makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.deluce_subject).makeSVG()

        with open(self.CURRENT_DIR / "John Lennon DeLuce - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_j2000_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.j2000_subject).makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.j2000_subject).makeSVG()

        with open(self.CURRENT_DIR / "John Lennon J2000 - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_morinus_house_system_birth_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.morinus_house_system_subject).makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.morinus_house_system_subject).makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - House System Morinus - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_heliocentric_perspective_natals_chart(self):
        heliocentric_perspective_natals_chart_svg = KerykeionChartSVG(self.heliocentric_perspective_natal_chart).makeTemplate()
        heliocentric_perspective_natals_chart_svg_lines = [heliocentric_perspective_natals_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(heliocentric_perspective_natals_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject, perspective="Heliocentric").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Heliocentric - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(heliocentric_perspective_natals_chart_svg_lines)):
            assert heliocentric_perspective_natals_chart_svg_lines[i] == file_content_lines[i]

    def test_topocentric_perspective_natals_chart(self):
        topocentric_perspective_natals_chart_svg = KerykeionChartSVG(self.topocentric_perspective_natal_chart).makeTemplate()
        topocentric_perspective_natals_chart_svg_lines = [topocentric_perspective_natals_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(topocentric_perspective_natals_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject, perspective="Topocentric").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Topocentric - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(topocentric_perspective_natals_chart_svg_lines)):
            assert topocentric_perspective_natals_chart_svg_lines[i] == file_content_lines[i]

    def test_true_geocentric_perspective_natals_chart(self):
        true_geocentric_perspective_natals_chart_svg = KerykeionChartSVG(self.true_geocentric_perspective_natal_chart).makeTemplate()
        true_geocentric_perspective_natals_chart_svg_lines = [true_geocentric_perspective_natals_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(true_geocentric_perspective_natals_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject, perspective="True Geocentric").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - True Geocentric - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(true_geocentric_perspective_natals_chart_svg_lines)):
            assert true_geocentric_perspective_natals_chart_svg_lines[i] == file_content_lines[i]

    def test_natal_chart_from_model(self):
        birth_chart_svg = KerykeionChartSVG(self.first_subject).makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.first_subject.model()).makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_minified_natal_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.minified_natal_chart).makeTemplate(minify=True)
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.minified_natal_chart).makeSVG(minify=True)

        with open(self.CURRENT_DIR / "John Lennon - Minified - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_dark_theme_natal_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.dark_theme_natal_chart, theme="dark").makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.dark_theme_natal_chart, theme="dark").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Dark Theme - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_dark_high_contrast_theme_natal_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.dark_high_contrast_theme_natal_chart, theme="dark-high-contrast").makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.dark_high_contrast_theme_natal_chart, theme="dark-high-contrast").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Dark High Contrast Theme - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_light_theme_natal_chart(self):
        birth_chart_svg = KerykeionChartSVG(self.light_theme_natal_chart, theme="light").makeTemplate()
        birth_chart_svg_lines = [birth_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(birth_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.light_theme_natal_chart, theme="light").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Light Theme - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(birth_chart_svg_lines)):
            assert birth_chart_svg_lines[i] == file_content_lines[i]

    def test_dark_theme_external_natal_chart(self):
        external_natal_chart_svg = KerykeionChartSVG(self.dark_theme_external_subject, theme="dark", chart_type="ExternalNatal").makeTemplate()
        external_natal_chart_svg_lines = [external_natal_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(external_natal_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.dark_theme_external_subject, theme="dark").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - Dark Theme External - ExternalNatal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(external_natal_chart_svg_lines)):
            assert external_natal_chart_svg_lines[i] == file_content_lines[i]

    def test_dark_theme_synastry_chart(self):
        synastry_chart_svg = KerykeionChartSVG(self.dark_theme_synastry_subject, "Synastry", self.second_subject, theme="dark").makeTemplate()
        synastry_chart_svg_lines = [synastry_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(synastry_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.dark_theme_synastry_subject, theme="dark").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - DTS - Synastry Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(synastry_chart_svg_lines)):
            assert synastry_chart_svg_lines[i] == file_content_lines[i]

    def test_wheel_only_chart(self):
        wheel_only_chart_svg = KerykeionChartSVG(self.wheel_only_subject).makeWheelOnlyTemplate()

        wheel_only_chart_svg_lines = [wheel_only_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(wheel_only_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.wheel_only_subject).makeWheelOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Wheel Only - Natal Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(wheel_only_chart_svg_lines)):
            assert wheel_only_chart_svg_lines[i] == file_content_lines[i]

    def test_wheel_external_chart(self):
        wheel_external_chart_svg = KerykeionChartSVG(self.wheel_external_subject, chart_type="ExternalNatal").makeWheelOnlyTemplate()

        wheel_external_chart_svg_lines = [wheel_external_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(wheel_external_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.wheel_external_subject, chart_type="ExternalNatal").makeWheelOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Wheel External Only - ExternalNatal Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(wheel_external_chart_svg_lines)):
            assert wheel_external_chart_svg_lines[i] == file_content_lines[i]

    def test_wheel_synastry_chart(self):
        wheel_synastry_chart_svg = KerykeionChartSVG(self.wheel_synastry_subject, chart_type="Synastry", second_obj=self.second_subject).makeWheelOnlyTemplate()

        wheel_synastry_chart_svg_lines = [wheel_synastry_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(wheel_synastry_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.wheel_synastry_subject, chart_type="Synastry", second_obj=self.second_subject).makeWheelOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Wheel Synastry Only - Synastry Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(wheel_synastry_chart_svg_lines)):
            assert wheel_synastry_chart_svg_lines[i] == file_content_lines[i]

    def test_wheel_transit_chart(self):
        wheel_transit_chart_svg = KerykeionChartSVG(self.wheel_transit_subject, chart_type="Transit", second_obj=self.second_subject).makeWheelOnlyTemplate()

        wheel_transit_chart_svg_lines = [wheel_transit_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(wheel_transit_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.wheel_transit_subject, chart_type="Transit", second_obj=self.second_subject).makeWheelOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Wheel Transit Only - Transit Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(wheel_transit_chart_svg_lines)):
            assert wheel_transit_chart_svg_lines[i] == file_content_lines[i]

    def test_aspect_grid_only_chart(self):
        aspect_grid_only_chart_svg = KerykeionChartSVG(self.aspect_grid_only_subject).makeAspectGridOnlyTemplate()

        aspect_grid_only_chart_svg_lines = [aspect_grid_only_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(aspect_grid_only_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.aspect_grid_only_subject).makeAspectGridOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Aspect Grid Only - Natal Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(aspect_grid_only_chart_svg_lines)):
            assert aspect_grid_only_chart_svg_lines[i] == file_content_lines[i]

    def test_aspect_grid_dark_chart(self):
        aspect_grid_dark_chart_svg = KerykeionChartSVG(self.aspect_grid_dark_subject, theme="dark").makeAspectGridOnlyTemplate()

        aspect_grid_dark_chart_svg_lines = [aspect_grid_dark_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(aspect_grid_dark_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.aspect_grid_dark_subject, theme="dark").makeAspectGridOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Aspect Grid Dark Theme - Natal Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(aspect_grid_dark_chart_svg_lines)):
            assert aspect_grid_dark_chart_svg_lines[i] == file_content_lines[i]

    def test_aspect_grid_light_chart(self):
        aspect_grid_light_chart_svg = KerykeionChartSVG(self.aspect_grid_light_subject, theme="light").makeAspectGridOnlyTemplate()

        aspect_grid_light_chart_svg_lines = [aspect_grid_light_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(aspect_grid_light_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.aspect_grid_light_subject, theme="light").makeAspectGridOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Aspect Grid Light Theme - Natal Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(aspect_grid_light_chart_svg_lines)):
            assert aspect_grid_light_chart_svg_lines[i] == file_content_lines[i]

    def test_aspect_grid_synastry_chart(self):
        aspect_grid_synastry_chart_svg = KerykeionChartSVG(self.aspect_grid_synastry_subject, "Synastry", self.second_subject).makeAspectGridOnlyTemplate()

        aspect_grid_synastry_chart_svg_lines = [aspect_grid_synastry_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(aspect_grid_synastry_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.aspect_grid_synastry_subject, "Synastry", self.second_subject).makeAspectGridOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Aspect Grid Synastry - Synastry Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(aspect_grid_synastry_chart_svg_lines)):
            assert aspect_grid_synastry_chart_svg_lines[i] == file_content_lines[i]

    def test_aspect_grid_transit(self):
        aspect_grid_transit_chart_svg = KerykeionChartSVG(self.aspect_grid_transit_subject, "Transit", self.second_subject).makeAspectGridOnlyTemplate()

        aspect_grid_transit_chart_svg_lines = [aspect_grid_transit_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(aspect_grid_transit_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.aspect_grid_transit_subject, "Transit", self.second_subject).makeAspectGridOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Aspect Grid Transit - Transit Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(aspect_grid_transit_chart_svg_lines)):
            assert aspect_grid_transit_chart_svg_lines[i] == file_content_lines[i]

    def test_aspect_grid_dark_synastry(self):
        aspect_grid_dark_synastry_chart_svg = KerykeionChartSVG(self.aspect_grid_dark_synastry_subject, "Synastry", self.second_subject, theme="dark").makeAspectGridOnlyTemplate()

        aspect_grid_dark_synastry_chart_svg_lines = [aspect_grid_dark_synastry_chart_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(aspect_grid_dark_synastry_chart_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.aspect_grid_dark_synastry_subject, "Synastry", self.second_subject, theme="dark").makeAspectGridOnlySVG()

        with open(self.CURRENT_DIR / "John Lennon - Aspect Grid Dark Synastry - Synastry Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(aspect_grid_dark_synastry_chart_svg_lines)):
            assert aspect_grid_dark_synastry_chart_svg_lines[i] == file_content_lines[i]

    def test_transit_chart_with_table_grid(self):
        transit_chart_with_table_grid_svg = KerykeionChartSVG(self.transit_chart_with_table_grid_subject, "Transit", self.second_subject, double_chart_aspect_grid_type="table", theme="dark").makeTemplate()

        transit_chart_with_table_grid_svg_lines = [transit_chart_with_table_grid_svg[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(transit_chart_with_table_grid_svg), self.SPLIT_LINE_LENGTH)]

        if self.WRITE_TO_FILE:
            KerykeionChartSVG(self.transit_chart_with_table_grid_subject, "Transit", self.second_subject, double_chart_aspect_grid_type="table").makeSVG()

        with open(self.CURRENT_DIR / "John Lennon - TCWTG - Transit Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = [file_content[i : i + self.SPLIT_LINE_LENGTH] for i in range(0, len(file_content), self.SPLIT_LINE_LENGTH)]

        for i in range(len(transit_chart_with_table_grid_svg_lines)):
            assert transit_chart_with_table_grid_svg_lines[i] == file_content_lines[i]

    def test_chinese_chart(self):
        chinese_chart_svg = KerykeionChartSVG(self.chinese_subject, chart_language="CN").makeTemplate()
        self._compare_chart_svg("Hua Chenyu - Natal Chart.svg", chinese_chart_svg)

    def test_french_chart(self):
        french_chart_svg = KerykeionChartSVG(self.french_subject, chart_language="FR").makeTemplate()
        self._compare_chart_svg("Jeanne Moreau - Natal Chart.svg", french_chart_svg)

    def test_spanish_chart(self):
        spanish_chart_svg = KerykeionChartSVG(self.spanish_subject, chart_language="ES").makeTemplate()
        self._compare_chart_svg("Antonio Banderas - Natal Chart.svg", spanish_chart_svg)

    def test_portuguese_chart(self):
        portuguese_chart_svg = KerykeionChartSVG(self.portuguese_subject, chart_language="PT").makeTemplate()
        self._compare_chart_svg("Cristiano Ronaldo - Natal Chart.svg", portuguese_chart_svg)

    def test_italian_chart(self):
        italian_chart_svg = KerykeionChartSVG(self.italian_subject, chart_language="IT").makeTemplate()
        self._compare_chart_svg("Sophia Loren - Natal Chart.svg", italian_chart_svg)

    def test_russian_chart(self):
        russian_chart_svg = KerykeionChartSVG(self.russian_subject, chart_language="RU").makeTemplate()
        self._compare_chart_svg("Mikhail Bulgakov - Natal Chart.svg", russian_chart_svg)

    def test_turkish_chart(self):
        turkish_chart_svg = KerykeionChartSVG(self.turkish_subject, chart_language="TR").makeTemplate()
        self._compare_chart_svg("Mehmet Oz - Natal Chart.svg", turkish_chart_svg)

    def test_german_chart(self):
        german_chart_svg = KerykeionChartSVG(self.german_subject, chart_language="DE").makeTemplate()
        self._compare_chart_svg("Albert Einstein - Natal Chart.svg", german_chart_svg)

    def test_hindi_chart(self):
        hindi_chart_svg = KerykeionChartSVG(self.hindi_subject, chart_language="HI").makeTemplate()
        self._compare_chart_svg("Amitabh Bachchan - Natal Chart.svg", hindi_chart_svg)
    '''

if __name__ == "__main__":
    import pytest
    import logging

    # Set the log level to CRITICAL
    logging.basicConfig(level=logging.CRITICAL)
    
    pytest.main(["-vv", "--log-level=CRITICAL", "--log-cli-level=CRITICAL", __file__])
