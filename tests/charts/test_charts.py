from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDrawer, CompositeSubjectFactory
from .compare_svg_lines import compare_svg_lines


class TestCharts:
    WRITE_TO_FILE = False
    SVG_DIR = Path(__file__).parent / 'svg'

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
        self.first_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.second_subject = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.lahiri_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Lahiri", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI", geonames_username="century.boy")
        self.fagan_bradley_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Fagan-Bradley", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY", geonames_username="century.boy")
        self.deluce_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon DeLuce", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="DELUCE", geonames_username="century.boy")
        self.j2000_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon J2000", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="J2000", geonames_username="century.boy")
        self.morinus_house_system_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - House System Morinus", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system_identifier="M", geonames_username="century.boy")
        self.heliocentric_perspective_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Heliocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy", perspective_type="Heliocentric")
        self.topocentric_perspective_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Topocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy", perspective_type="Topocentric")
        self.true_geocentric_perspective_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - True Geocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy", perspective_type="True Geocentric")
        self.minified_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Minified", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.dark_theme_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.dark_high_contrast_theme_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark High Contrast Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.light_theme_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", geonames_username="century.boy")
        self.dark_theme_external_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark Theme External", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.dark_theme_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - DTS", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.wheel_only_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")

        self.wheel_external_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel External Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.wheel_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Synastry Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.wheel_transit_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Transit Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.sidereal_dark_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Lahiri - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
        self.sidereal_light_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Fagan-Bradley - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY")
        self.aspect_grid_only_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_dark_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_light_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_transit_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Transit", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.aspect_grid_dark_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Dark Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB")
        self.transit_chart_with_table_grid_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - TCWTG", 1940, 10, 9, 18, 30, "Liverpool", "GB")

        # Language Tests
        self.chinese_subject = AstrologicalSubjectFactory.from_birth_data("Hua Chenyu", 1990, 2, 7, 12, 0, "Hunan", "CN")
        self.french_subject = AstrologicalSubjectFactory.from_birth_data("Jeanne Moreau", 1928, 1, 23, 10, 0, "Paris", "FR")
        self.spanish_subject = AstrologicalSubjectFactory.from_birth_data("Antonio Banderas", 1960, 8, 10, 12, 0, "Malaga", "ES")
        self.portuguese_subject = AstrologicalSubjectFactory.from_birth_data("Cristiano Ronaldo", 1985, 2, 5, 5, 25, "Funchal", "PT")
        self.italian_subject = AstrologicalSubjectFactory.from_birth_data("Sophia Loren", 1934, 9, 20, 2, 0, "Rome", "IT")
        self.russian_subject = AstrologicalSubjectFactory.from_birth_data("Mikhail Bulgakov", 1891, 5, 15, 12, 0, "Kiev", "UA")
        self.turkish_subject = AstrologicalSubjectFactory.from_birth_data("Mehmet Oz", 1960, 6, 11, 12, 0, "Istanbul", "TR")
        self.german_subject = AstrologicalSubjectFactory.from_birth_data("Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE")
        self.hindi_subject = AstrologicalSubjectFactory.from_birth_data("Amitabh Bachchan", 1942, 10, 11, 4, 0, "Allahabad", "IN")

        # Composite Chart
        self.angelina_jolie = AstrologicalSubjectFactory.from_birth_data("Angelina Jolie", 1975, 6, 4, 9, 9, "Los Angeles", "US", lng=-118.15, lat=34.03, tz_str="America/Los_Angeles")
        self.brad_pit = AstrologicalSubjectFactory.from_birth_data("Brad Pitt", 1963, 12, 18, 6, 31, "Shawnee", "US", lng=-96.56, lat=35.20, tz_str="America/Chicago")


    def test_natal_chart(self):
        s = ChartDrawer(self.first_subject)
        birth_chart_svg = s.makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.first_subject).makeSVG()

        with open(self.SVG_DIR / "John Lennon - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_synastry_chart(self):
        synastry_chart_svg = ChartDrawer(self.first_subject, "Synastry", self.second_subject).makeTemplate()
        synastry_chart_svg_lines = synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.first_subject, "Synastry", self.second_subject).makeSVG()

        with open(self.SVG_DIR / "John Lennon - Synastry Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_transit_chart(self):
        transit_chart_svg = ChartDrawer(self.first_subject, "Transit", self.second_subject).makeTemplate()
        transit_chart_svg_lines = transit_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.first_subject, "Transit", self.second_subject).makeSVG()

        with open(self.SVG_DIR / "John Lennon - Transit Chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, transit_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_external_natal_chart(self):
        external_natal_chart_svg = ChartDrawer(self.first_subject, "ExternalNatal").makeTemplate()
        external_natal_chart_svg_lines = external_natal_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.first_subject, "ExternalNatal").makeSVG()

        with open(self.SVG_DIR / "John Lennon - ExternalNatal Chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, external_natal_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_lahiri_birth_chart(self):
        birth_chart_svg = ChartDrawer(self.lahiri_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.lahiri_subject).makeSVG()

        with open(self.SVG_DIR / "John Lennon Lahiri - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_fagan_bradley_birth_chart(self):
        birth_chart_svg = ChartDrawer(self.fagan_bradley_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.fagan_bradley_subject).makeSVG()

        with open(self.SVG_DIR / "John Lennon Fagan-Bradley - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_deluce_birth_chart(self):
        birth_chart_svg = ChartDrawer(self.deluce_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.deluce_subject).makeSVG()

        with open(self.SVG_DIR / "John Lennon DeLuce - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_j2000_birth_chart(self):
        birth_chart_svg = ChartDrawer(self.j2000_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.j2000_subject).makeSVG()

        with open(self.SVG_DIR / "John Lennon J2000 - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_morinus_house_system_birth_chart(self):
        birth_chart_svg = ChartDrawer(self.morinus_house_system_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.morinus_house_system_subject).makeSVG()

        with open(self.SVG_DIR / "John Lennon - House System Morinus - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_heliocentric_perspective_natals_chart(self):
        heliocentric_perspective_natals_chart_svg = ChartDrawer(self.heliocentric_perspective_natal_chart).makeTemplate()
        heliocentric_perspective_natals_chart_svg_lines = heliocentric_perspective_natals_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.first_subject, perspective="Heliocentric").makeSVG()

        with open(self.SVG_DIR / "John Lennon - Heliocentric - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, heliocentric_perspective_natals_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_topocentric_perspective_natals_chart(self):
        topocentric_perspective_natals_chart_svg = ChartDrawer(self.topocentric_perspective_natal_chart).makeTemplate()
        topocentric_perspective_natals_chart_svg_lines = topocentric_perspective_natals_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.first_subject, perspective="Topocentric").makeSVG()

        with open(self.SVG_DIR / "John Lennon - Topocentric - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, topocentric_perspective_natals_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_true_geocentric_perspective_natals_chart(self):
        true_geocentric_perspective_natals_chart_svg = ChartDrawer(self.true_geocentric_perspective_natal_chart).makeTemplate()
        true_geocentric_perspective_natals_chart_svg_lines = true_geocentric_perspective_natals_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.first_subject).makeSVG()

        with open(self.SVG_DIR / "John Lennon - True Geocentric - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, true_geocentric_perspective_natals_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_natal_chart_from_model(self):
        birth_chart_svg = ChartDrawer(self.first_subject).makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.first_subject.model()).makeSVG()

        with open(self.SVG_DIR / "John Lennon - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_minified_natal_chart(self):
        birth_chart_svg = ChartDrawer(self.minified_natal_chart).makeTemplate(minify=True)
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.minified_natal_chart).makeSVG(minify=True)

        with open(self.SVG_DIR / "John Lennon - Minified - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_dark_theme_natal_chart(self):
        birth_chart_svg = ChartDrawer(self.dark_theme_natal_chart, theme="dark").makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.dark_theme_natal_chart, theme="dark").makeSVG()

        with open(self.SVG_DIR / "John Lennon - Dark Theme - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_dark_high_contrast_theme_natal_chart(self):
        birth_chart_svg = ChartDrawer(self.dark_high_contrast_theme_natal_chart, theme="dark-high-contrast").makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.dark_high_contrast_theme_natal_chart, theme="dark-high-contrast").makeSVG()

        with open(self.SVG_DIR / "John Lennon - Dark High Contrast Theme - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_light_theme_natal_chart(self):
        birth_chart_svg = ChartDrawer(self.light_theme_natal_chart, theme="light").makeTemplate()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.light_theme_natal_chart, theme="light").makeSVG()

        with open(self.SVG_DIR / "John Lennon - Light Theme - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_dark_theme_external_natal_chart(self):
        external_natal_chart_svg = ChartDrawer(self.dark_theme_external_subject, theme="dark", chart_type="ExternalNatal").makeTemplate()
        external_natal_chart_svg_lines = external_natal_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.dark_theme_external_subject, theme="dark").makeSVG()

        with open(self.SVG_DIR / "John Lennon - Dark Theme External - ExternalNatal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, external_natal_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_dark_theme_synastry_chart(self):
        synastry_chart_svg = ChartDrawer(self.dark_theme_synastry_subject, "Synastry", self.second_subject, theme="dark").makeTemplate()
        synastry_chart_svg_lines = synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.dark_theme_synastry_subject, theme="dark").makeSVG()

        with open(self.SVG_DIR / "John Lennon - DTS - Synastry Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_wheel_only_chart(self):
        wheel_only_chart_svg = ChartDrawer(self.wheel_only_subject).makeWheelOnlyTemplate()

        wheel_only_chart_svg_lines = wheel_only_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.wheel_only_subject).makeWheelOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Wheel Only - Natal Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, wheel_only_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_wheel_external_chart(self):
        wheel_external_chart_svg = ChartDrawer(self.wheel_external_subject, chart_type="ExternalNatal").makeWheelOnlyTemplate()

        wheel_external_chart_svg_lines = wheel_external_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.wheel_external_subject, chart_type="ExternalNatal").makeWheelOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Wheel External Only - ExternalNatal Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, wheel_external_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_wheel_synastry_chart(self):
        wheel_synastry_chart_svg = ChartDrawer(self.wheel_synastry_subject, chart_type="Synastry", second_obj=self.second_subject).makeWheelOnlyTemplate()

        wheel_synastry_chart_svg_lines = wheel_synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.wheel_synastry_subject, chart_type="Synastry", second_obj=self.second_subject).makeWheelOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Wheel Synastry Only - Synastry Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, wheel_synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_wheel_transit_chart(self):
        wheel_transit_chart_svg = ChartDrawer(self.wheel_transit_subject, chart_type="Transit", second_obj=self.second_subject).makeWheelOnlyTemplate()

        wheel_transit_chart_svg_lines = wheel_transit_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.wheel_transit_subject, chart_type="Transit", second_obj=self.second_subject).makeWheelOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Wheel Transit Only - Transit Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, wheel_transit_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_only_chart(self):
        aspect_grid_only_chart_svg = ChartDrawer(self.aspect_grid_only_subject).makeAspectGridOnlyTemplate()

        aspect_grid_only_chart_svg_lines = aspect_grid_only_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.aspect_grid_only_subject).makeAspectGridOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Only - Natal Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_only_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_dark_chart(self):
        aspect_grid_dark_chart_svg = ChartDrawer(self.aspect_grid_dark_subject, theme="dark").makeAspectGridOnlyTemplate()

        aspect_grid_dark_chart_svg_lines = aspect_grid_dark_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.aspect_grid_dark_subject, theme="dark").makeAspectGridOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Dark Theme - Natal Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_dark_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_light_chart(self):
        aspect_grid_light_chart_svg = ChartDrawer(self.aspect_grid_light_subject, theme="light").makeAspectGridOnlyTemplate()

        aspect_grid_light_chart_svg_lines = aspect_grid_light_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.aspect_grid_light_subject, theme="light").makeAspectGridOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Light Theme - Natal Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_light_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_synastry_chart(self):
        aspect_grid_synastry_chart_svg = ChartDrawer(self.aspect_grid_synastry_subject, "Synastry", self.second_subject).makeAspectGridOnlyTemplate()

        aspect_grid_synastry_chart_svg_lines = aspect_grid_synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.aspect_grid_synastry_subject, "Synastry", self.second_subject).makeAspectGridOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Synastry - Synastry Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_transit(self):
        aspect_grid_transit_chart_svg = ChartDrawer(self.aspect_grid_transit_subject, "Transit", self.second_subject).makeAspectGridOnlyTemplate()

        aspect_grid_transit_chart_svg_lines = aspect_grid_transit_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.aspect_grid_transit_subject, "Transit", self.second_subject).makeAspectGridOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Transit - Transit Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_transit_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_dark_synastry(self):
        aspect_grid_dark_synastry_chart_svg = ChartDrawer(self.aspect_grid_dark_synastry_subject, "Synastry", self.second_subject, theme="dark").makeAspectGridOnlyTemplate()

        aspect_grid_dark_synastry_chart_svg_lines = aspect_grid_dark_synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.aspect_grid_dark_synastry_subject, "Synastry", self.second_subject, theme="dark").makeAspectGridOnlySVG()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Dark Synastry - Synastry Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_dark_synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_transit_chart_with_table_grid(self):
        transit_chart_with_table_grid_svg = ChartDrawer(self.transit_chart_with_table_grid_subject, "Transit", self.second_subject, double_chart_aspect_grid_type="table", theme="dark").makeTemplate()

        transit_chart_with_table_grid_svg_lines = transit_chart_with_table_grid_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(self.transit_chart_with_table_grid_subject, "Transit", self.second_subject, double_chart_aspect_grid_type="table").makeSVG()

        with open(self.SVG_DIR / "John Lennon - TCWTG - Transit Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, transit_chart_with_table_grid_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_chinese_chart(self):
        chinese_chart_svg = ChartDrawer(self.chinese_subject, chart_language="CN").makeTemplate()
        self._compare_chart_svg("Hua Chenyu - Natal Chart.svg", chinese_chart_svg)

    def test_french_chart(self):
        french_chart_svg = ChartDrawer(self.french_subject, chart_language="FR").makeTemplate()
        self._compare_chart_svg("Jeanne Moreau - Natal Chart.svg", french_chart_svg)

    def test_spanish_chart(self):
        spanish_chart_svg = ChartDrawer(self.spanish_subject, chart_language="ES").makeTemplate()
        self._compare_chart_svg("Antonio Banderas - Natal Chart.svg", spanish_chart_svg)

    def test_portuguese_chart(self):
        portuguese_chart_svg = ChartDrawer(self.portuguese_subject, chart_language="PT").makeTemplate()
        self._compare_chart_svg("Cristiano Ronaldo - Natal Chart.svg", portuguese_chart_svg)

    def test_italian_chart(self):
        italian_chart_svg = ChartDrawer(self.italian_subject, chart_language="IT").makeTemplate()
        self._compare_chart_svg("Sophia Loren - Natal Chart.svg", italian_chart_svg)

    def test_russian_chart(self):
        russian_chart_svg = ChartDrawer(self.russian_subject, chart_language="RU").makeTemplate()
        self._compare_chart_svg("Mikhail Bulgakov - Natal Chart.svg", russian_chart_svg)

    def test_turkish_chart(self):
        turkish_chart_svg = ChartDrawer(self.turkish_subject, chart_language="TR").makeTemplate()
        self._compare_chart_svg("Mehmet Oz - Natal Chart.svg", turkish_chart_svg)

    def test_german_chart(self):
        german_chart_svg = ChartDrawer(self.german_subject, chart_language="DE").makeTemplate()
        self._compare_chart_svg("Albert Einstein - Natal Chart.svg", german_chart_svg)

    def test_hindi_chart(self):
        hindi_chart_svg = ChartDrawer(self.hindi_subject, chart_language="HI").makeTemplate()
        self._compare_chart_svg("Amitabh Bachchan - Natal Chart.svg", hindi_chart_svg)

    def test_composite_chart(self):
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pit)
        composite_chart_svg = factory.get_midpoint_composite_subject_model()
        composite_chart_svg = ChartDrawer(composite_chart_svg, "Composite").makeTemplate()
        self._compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart.svg", composite_chart_svg)


if __name__ == "__main__":
    import pytest
    import logging

    # Set the log level to CRITICAL
    logging.basicConfig(level=logging.CRITICAL)

    pytest.main(["-vv", "--log-level=CRITICAL", "--log-cli-level=CRITICAL", __file__])
