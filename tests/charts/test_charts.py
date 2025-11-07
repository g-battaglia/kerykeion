from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDrawer, CompositeSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory
from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS
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
        self.first_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.second_subject = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.lahiri_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Lahiri", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI", suppress_geonames_warning=True)
        self.fagan_bradley_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Fagan-Bradley", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY", suppress_geonames_warning=True)
        self.deluce_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon DeLuce", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="DELUCE", suppress_geonames_warning=True)
        self.j2000_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon J2000", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="J2000", suppress_geonames_warning=True)
        self.morinus_house_system_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - House System Morinus", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system_identifier="M", suppress_geonames_warning=True)
        self.heliocentric_perspective_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Heliocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True, perspective_type="Heliocentric")
        self.topocentric_perspective_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Topocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True, perspective_type="Topocentric")
        self.true_geocentric_perspective_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - True Geocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True, perspective_type="True Geocentric")
        self.minified_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Minified", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.dark_theme_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.dark_high_contrast_theme_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark High Contrast Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.light_theme_natal_chart = AstrologicalSubjectFactory.from_birth_data("John Lennon - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.dark_theme_external_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark Theme External", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.dark_theme_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - DTS", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.wheel_only_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)

        self.wheel_external_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel External Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.wheel_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Synastry Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.wheel_transit_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Transit Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        # Subject with all active points enabled
        self.all_active_points_subject = AstrologicalSubjectFactory.from_birth_data(
            "John Lennon - All Active Points", 1940, 10, 9, 18, 30, "Liverpool", "GB",
            suppress_geonames_warning=True, active_points=ALL_ACTIVE_POINTS
        )
        self.sidereal_dark_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Lahiri - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI", suppress_geonames_warning=True)
        self.sidereal_light_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Fagan-Bradley - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY", suppress_geonames_warning=True)
        self.aspect_grid_only_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Only", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.aspect_grid_dark_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.aspect_grid_light_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.aspect_grid_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.aspect_grid_transit_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Transit", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.aspect_grid_dark_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Dark Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        self.transit_chart_with_table_grid_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - TCWTG", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)

        # Language Tests
        self.chinese_subject = AstrologicalSubjectFactory.from_birth_data("Hua Chenyu", 1990, 2, 7, 12, 0, "Hunan", "CN", suppress_geonames_warning=True)
        self.french_subject = AstrologicalSubjectFactory.from_birth_data("Jeanne Moreau", 1928, 1, 23, 10, 0, "Paris", "FR", suppress_geonames_warning=True)
        self.spanish_subject = AstrologicalSubjectFactory.from_birth_data("Antonio Banderas", 1960, 8, 10, 12, 0, "Malaga", "ES", suppress_geonames_warning=True)
        self.portuguese_subject = AstrologicalSubjectFactory.from_birth_data("Cristiano Ronaldo", 1985, 2, 5, 5, 25, "Funchal", "PT", suppress_geonames_warning=True)
        self.italian_subject = AstrologicalSubjectFactory.from_birth_data("Sophia Loren", 1934, 9, 20, 2, 0, "Rome", "IT", suppress_geonames_warning=True)
        self.russian_subject = AstrologicalSubjectFactory.from_birth_data("Mikhail Bulgakov", 1891, 5, 15, 12, 0, "Kiev", "UA", suppress_geonames_warning=True)
        self.turkish_subject = AstrologicalSubjectFactory.from_birth_data("Mehmet Oz", 1960, 6, 11, 12, 0, "Istanbul", "TR", suppress_geonames_warning=True)
        self.german_subject = AstrologicalSubjectFactory.from_birth_data("Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE", suppress_geonames_warning=True)
        self.hindi_subject = AstrologicalSubjectFactory.from_birth_data("Amitabh Bachchan", 1942, 10, 11, 4, 0, "Allahabad", "IN", suppress_geonames_warning=True)

        # Composite Chart
        self.angelina_jolie = AstrologicalSubjectFactory.from_birth_data("Angelina Jolie", 1975, 6, 4, 9, 9, "Los Angeles", "US", lng=-118.15, lat=34.03, tz_str="America/Los_Angeles", suppress_geonames_warning=True)
        self.brad_pit = AstrologicalSubjectFactory.from_birth_data("Brad Pitt", 1963, 12, 18, 6, 31, "Shawnee", "US", lng=-96.56, lat=35.20, tz_str="America/Chicago", suppress_geonames_warning=True)

        # Synastry subject with all active points
        self.all_active_points_second_subject = AstrologicalSubjectFactory.from_birth_data(
            "Paul McCartney - All Active Points", 1942, 6, 18, 15, 30, "Liverpool", "GB",
            suppress_geonames_warning=True, active_points=ALL_ACTIVE_POINTS
        )


    def test_natal_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.first_subject)
        s = ChartDrawer(chart_data)
        birth_chart_svg = s.generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_synastry_chart(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        synastry_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        synastry_chart_svg_lines = synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon - Synastry Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_black_and_white_synastry_chart(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        synastry_chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg("John Lennon - Black and White Theme - Synastry Chart.svg", synastry_chart_svg)

    def test_synastry_chart_without_house_comparison_grid(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(self.first_subject, self.second_subject)
        synastry_chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Synastry Chart - No House Comparison.svg", synastry_chart_svg)

    def test_transit_chart(self):
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        transit_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        transit_chart_svg_lines = transit_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon - Transit Chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, transit_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_black_and_white_transit_chart(self):
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        transit_chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg("John Lennon - Black and White Theme - Transit Chart.svg", transit_chart_svg)

    def test_transit_chart_without_house_comparison_grid(self):
        chart_data = ChartDataFactory.create_transit_chart_data(self.first_subject, self.second_subject)
        transit_chart_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg("John Lennon - Transit Chart - No House Comparison.svg", transit_chart_svg)

    def test_external_natal_chart(self):
        external_natal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - ExternalNatal", 1940, 10, 9, 18, 30, "Liverpool", "GB", suppress_geonames_warning=True)
        external_natal_chart_data = ChartDataFactory.create_natal_chart_data(external_natal_subject)
        external_natal_chart_svg = ChartDrawer(external_natal_chart_data, external_view=True).generate_svg_string()
        external_natal_chart_svg_lines = external_natal_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(external_natal_chart_data, external_view=True).save_svg()

        with open(self.SVG_DIR / "John Lennon - ExternalNatal - Natal Chart.svg", "r", encoding="utf-8") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, external_natal_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_lahiri_birth_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.lahiri_subject)
        birth_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon Lahiri - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_fagan_bradley_birth_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.fagan_bradley_subject)
        birth_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon Fagan-Bradley - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_deluce_birth_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.deluce_subject)
        birth_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon DeLuce - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_j2000_birth_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.j2000_subject)
        birth_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon J2000 - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_morinus_house_system_birth_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.morinus_house_system_subject)
        birth_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon - House System Morinus - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_heliocentric_perspective_natals_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.heliocentric_perspective_natal_chart)
        heliocentric_perspective_natals_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        heliocentric_perspective_natals_chart_svg_lines = heliocentric_perspective_natals_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon - Heliocentric - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, heliocentric_perspective_natals_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_topocentric_perspective_natals_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.topocentric_perspective_natal_chart)
        topocentric_perspective_natals_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        topocentric_perspective_natals_chart_svg_lines = topocentric_perspective_natals_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon - Topocentric - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, topocentric_perspective_natals_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_true_geocentric_perspective_natals_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.true_geocentric_perspective_natal_chart)
        true_geocentric_perspective_natals_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        true_geocentric_perspective_natals_chart_svg_lines = true_geocentric_perspective_natals_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon - True Geocentric - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, true_geocentric_perspective_natals_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_natal_chart_from_model(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.first_subject)
        birth_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg()

        with open(self.SVG_DIR / "John Lennon - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_minified_natal_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.minified_natal_chart)
        birth_chart_svg = ChartDrawer(chart_data).generate_svg_string(minify=True)
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_svg(minify=True)

        with open(self.SVG_DIR / "John Lennon - Minified - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_dark_theme_natal_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.dark_theme_natal_chart)
        birth_chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, theme="dark").save_svg()

        with open(self.SVG_DIR / "John Lennon - Dark Theme - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_dark_high_contrast_theme_natal_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.dark_high_contrast_theme_natal_chart)
        birth_chart_svg = ChartDrawer(chart_data, theme="dark-high-contrast").generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, theme="dark-high-contrast").save_svg()

        with open(self.SVG_DIR / "John Lennon - Dark High Contrast Theme - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_light_theme_natal_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.light_theme_natal_chart)
        birth_chart_svg = ChartDrawer(chart_data, theme="light").generate_svg_string()
        birth_chart_svg_lines = birth_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, theme="light").save_svg()

        with open(self.SVG_DIR / "John Lennon - Light Theme - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, birth_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_black_and_white_natal_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.first_subject)
        birth_chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg("John Lennon - Black and White Theme - Natal Chart.svg", birth_chart_svg)

    def test_all_active_points_natal_chart(self):
        """Natal chart rendered with ALL_ACTIVE_POINTS should match the baseline SVG."""
        chart_data = ChartDataFactory.create_natal_chart_data(
            self.all_active_points_subject,
            active_points=ALL_ACTIVE_POINTS,
        )
        all_points_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Natal Chart.svg", all_points_svg)

    def test_dark_theme_external_natal_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.dark_theme_external_subject)
        external_natal_chart_svg = ChartDrawer(chart_data, theme="dark", external_view=True).generate_svg_string()
        external_natal_chart_svg_lines = external_natal_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, theme="dark", external_view=True).save_svg()

        with open(self.SVG_DIR / "John Lennon - Dark Theme External - Natal Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, external_natal_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_dark_theme_synastry_chart(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(self.dark_theme_synastry_subject, self.second_subject)
        synastry_chart_svg = ChartDrawer(chart_data, theme="dark").generate_svg_string()
        synastry_chart_svg_lines = synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, theme="dark").save_svg()

        with open(self.SVG_DIR / "John Lennon - DTS - Synastry Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_wheel_only_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.wheel_only_subject)
        wheel_only_chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()

        wheel_only_chart_svg_lines = wheel_only_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_wheel_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Wheel Only - Natal Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, wheel_only_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_wheel_external_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.wheel_external_subject)
        wheel_external_chart_svg = ChartDrawer(chart_data, external_view=True).generate_wheel_only_svg_string()

        wheel_external_chart_svg_lines = wheel_external_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, external_view=True).save_wheel_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Wheel External Only - ExternalNatal Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, wheel_external_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_wheel_synastry_chart(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(self.wheel_synastry_subject, self.second_subject)
        wheel_synastry_chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()

        wheel_synastry_chart_svg_lines = wheel_synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_wheel_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Wheel Synastry Only - Synastry Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, wheel_synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_wheel_transit_chart(self):
        chart_data = ChartDataFactory.create_transit_chart_data(self.wheel_transit_subject, self.second_subject)
        wheel_transit_chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()

        wheel_transit_chart_svg_lines = wheel_transit_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_wheel_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Wheel Transit Only - Transit Chart - Wheel Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, wheel_transit_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_wheel_only_all_active_points_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(
            self.all_active_points_subject,
            active_points=ALL_ACTIVE_POINTS,
        )

        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)

        wheel_only_chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Natal Chart - Wheel Only.svg", wheel_only_chart_svg)

    def test_wheel_only_all_active_points_synastry_chart(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.all_active_points_subject,
            self.all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )

        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)

        wheel_only_chart_svg = ChartDrawer(chart_data).generate_wheel_only_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Wheel Only.svg", wheel_only_chart_svg)

    def test_aspect_grid_only_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.aspect_grid_only_subject)
        aspect_grid_only_chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()

        aspect_grid_only_chart_svg_lines = aspect_grid_only_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_aspect_grid_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Only - Natal Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_only_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_dark_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.aspect_grid_dark_subject)
        aspect_grid_dark_chart_svg = ChartDrawer(chart_data, theme="dark").generate_aspect_grid_only_svg_string()

        aspect_grid_dark_chart_svg_lines = aspect_grid_dark_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, theme="dark").save_aspect_grid_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Dark Theme - Natal Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_dark_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_light_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.aspect_grid_light_subject)
        aspect_grid_light_chart_svg = ChartDrawer(chart_data, theme="light").generate_aspect_grid_only_svg_string()

        aspect_grid_light_chart_svg_lines = aspect_grid_light_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, theme="light").save_aspect_grid_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Light Theme - Natal Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_light_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_synastry_chart(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(self.aspect_grid_synastry_subject, self.second_subject)
        aspect_grid_synastry_chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()

        aspect_grid_synastry_chart_svg_lines = aspect_grid_synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_aspect_grid_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Synastry - Synastry Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_transit(self):
        chart_data = ChartDataFactory.create_transit_chart_data(self.aspect_grid_transit_subject, self.second_subject)
        aspect_grid_transit_chart_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()

        aspect_grid_transit_chart_svg_lines = aspect_grid_transit_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data).save_aspect_grid_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Transit - Transit Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_transit_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_aspect_grid_all_active_points_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(
            self.all_active_points_subject,
            active_points=ALL_ACTIVE_POINTS,
        )

        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)

        aspect_grid_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Natal Chart - Aspect Grid Only.svg", aspect_grid_svg)

    def test_aspect_grid_all_active_points_synastry_chart(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.all_active_points_subject,
            self.all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )

        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)

        aspect_grid_svg = ChartDrawer(chart_data).generate_aspect_grid_only_svg_string()
        self._compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Aspect Grid Only.svg", aspect_grid_svg)

    def test_synastry_chart_all_active_points_list(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.all_active_points_subject,
            self.all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )

        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)

        synastry_svg = ChartDrawer(
            chart_data,
            double_chart_aspect_grid_type="list",
        ).generate_svg_string()

        self._compare_chart_svg("John Lennon - All Active Points - Synastry Chart - List.svg", synastry_svg)

    def test_synastry_chart_all_active_points_grid(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(
            self.all_active_points_subject,
            self.all_active_points_second_subject,
            active_points=ALL_ACTIVE_POINTS,
        )

        assert set(chart_data.active_points) == set(ALL_ACTIVE_POINTS)

        synastry_svg = ChartDrawer(
            chart_data,
            double_chart_aspect_grid_type="table",
        ).generate_svg_string()

        self._compare_chart_svg("John Lennon - All Active Points - Synastry Chart - Grid.svg", synastry_svg)

    def test_aspect_grid_dark_synastry(self):
        chart_data = ChartDataFactory.create_synastry_chart_data(self.aspect_grid_dark_synastry_subject, self.second_subject)
        aspect_grid_dark_synastry_chart_svg = ChartDrawer(chart_data, theme="dark").generate_aspect_grid_only_svg_string()

        aspect_grid_dark_synastry_chart_svg_lines = aspect_grid_dark_synastry_chart_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, theme="dark").save_aspect_grid_only_svg_file()

        with open(self.SVG_DIR / "John Lennon - Aspect Grid Dark Synastry - Synastry Chart - Aspect Grid Only.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, aspect_grid_dark_synastry_chart_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_transit_chart_with_table_grid(self):
        chart_data = ChartDataFactory.create_transit_chart_data(self.transit_chart_with_table_grid_subject, self.second_subject)
        transit_chart_with_table_grid_svg = ChartDrawer(chart_data, double_chart_aspect_grid_type="table", theme="dark").generate_svg_string()

        transit_chart_with_table_grid_svg_lines = transit_chart_with_table_grid_svg.splitlines()

        if self.WRITE_TO_FILE:
            ChartDrawer(chart_data, double_chart_aspect_grid_type="table").save_svg()

        with open(self.SVG_DIR / "John Lennon - TCWTG - Transit Chart.svg", "r") as f:
            file_content = f.read()

        file_content_lines = file_content.splitlines()

        for expected_line, actual_line in zip(file_content_lines, transit_chart_with_table_grid_svg_lines):
            compare_svg_lines(expected_line, actual_line)

    def test_chinese_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.chinese_subject)
        chinese_chart_svg = ChartDrawer(chart_data, chart_language="CN").generate_svg_string()
        self._compare_chart_svg("Hua Chenyu - Natal Chart.svg", chinese_chart_svg)

    def test_french_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.french_subject)
        french_chart_svg = ChartDrawer(chart_data, chart_language="FR").generate_svg_string()
        self._compare_chart_svg("Jeanne Moreau - Natal Chart.svg", french_chart_svg)

    def test_spanish_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.spanish_subject)
        spanish_chart_svg = ChartDrawer(chart_data, chart_language="ES").generate_svg_string()
        self._compare_chart_svg("Antonio Banderas - Natal Chart.svg", spanish_chart_svg)

    def test_portuguese_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.portuguese_subject)
        portuguese_chart_svg = ChartDrawer(chart_data, chart_language="PT").generate_svg_string()
        self._compare_chart_svg("Cristiano Ronaldo - Natal Chart.svg", portuguese_chart_svg)

    def test_italian_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.italian_subject)
        italian_chart_svg = ChartDrawer(chart_data, chart_language="IT").generate_svg_string()
        self._compare_chart_svg("Sophia Loren - Natal Chart.svg", italian_chart_svg)

    def test_russian_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.russian_subject)
        russian_chart_svg = ChartDrawer(chart_data, chart_language="RU").generate_svg_string()
        self._compare_chart_svg("Mikhail Bulgakov - Natal Chart.svg", russian_chart_svg)

    def test_turkish_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.turkish_subject)
        turkish_chart_svg = ChartDrawer(chart_data, chart_language="TR").generate_svg_string()
        self._compare_chart_svg("Mehmet Oz - Natal Chart.svg", turkish_chart_svg)

    def test_german_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.german_subject)
        german_chart_svg = ChartDrawer(chart_data, chart_language="DE").generate_svg_string()
        self._compare_chart_svg("Albert Einstein - Natal Chart.svg", german_chart_svg)

    def test_hindi_chart(self):
        chart_data = ChartDataFactory.create_natal_chart_data(self.hindi_subject)
        hindi_chart_svg = ChartDrawer(chart_data, chart_language="HI").generate_svg_string()
        self._compare_chart_svg("Amitabh Bachchan - Natal Chart.svg", hindi_chart_svg)

    def test_composite_chart(self):
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pit)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        composite_chart_svg = ChartDrawer(chart_data).generate_svg_string()
        self._compare_chart_svg("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart.svg", composite_chart_svg)

    def test_black_and_white_composite_chart(self):
        factory = CompositeSubjectFactory(self.angelina_jolie, self.brad_pit)
        composite_subject = factory.get_midpoint_composite_subject_model()
        chart_data = ChartDataFactory.create_composite_chart_data(composite_subject)
        composite_chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg(
            "Angelina Jolie and Brad Pitt Composite Chart - Black and White Theme - Composite Chart.svg",
            composite_chart_svg,
        )

    def test_dual_return_solar_chart(self):
        """
        Test Dual Return Chart (Natal + Solar Return) against SVG baseline.
        Uses offline location data to ensure determinism and no network.
        """
        # Create PlanetaryReturnFactory with offline Liverpool coordinates
        return_factory = PlanetaryReturnFactory(
            self.first_subject,
            lng=-2.9833,
            lat=53.4000,
            tz_str="Europe/London",
            online=False,
        )

        # Use a fixed starting date to get a deterministic Solar Return
        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Solar",
        )

        # Build dual return chart (natal + return)
        chart_data = ChartDataFactory.create_return_chart_data(self.first_subject, solar_return)
        dual_return_chart_svg = ChartDrawer(chart_data).generate_svg_string()

        # Compare with expected SVG lines
        self._compare_chart_svg("John Lennon - DualReturnChart Chart - Solar Return.svg", dual_return_chart_svg)

        dual_return_chart_no_house_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Solar Return - No House Comparison.svg",
            dual_return_chart_no_house_svg,
        )

    def test_black_and_white_dual_return_chart(self):
        return_factory = PlanetaryReturnFactory(
            self.first_subject,
            lng=-2.9833,
            lat=53.4000,
            tz_str="Europe/London",
            online=False,
        )

        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Solar",
        )

        chart_data = ChartDataFactory.create_return_chart_data(self.first_subject, solar_return)
        dual_return_chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - Black and White Theme - DualReturnChart Chart - Solar Return.svg",
            dual_return_chart_svg,
        )

    def test_single_return_solar_chart(self):
        """
        Test Single Wheel Return Chart (Solar Return only) against SVG baseline.
        Uses offline location data to ensure determinism and no network.
        """
        return_factory = PlanetaryReturnFactory(
            self.first_subject,
            lng=-2.9833,
            lat=53.4000,
            tz_str="Europe/London",
            online=False,
        )

        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Solar",
        )

        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        single_return_chart_svg = ChartDrawer(chart_data).generate_svg_string()

        self._compare_chart_svg("John Lennon Solar Return - SingleReturnChart Chart.svg", single_return_chart_svg)

    def test_black_and_white_single_return_chart(self):
        return_factory = PlanetaryReturnFactory(
            self.first_subject,
            lng=-2.9833,
            lat=53.4000,
            tz_str="Europe/London",
            online=False,
        )

        solar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Solar",
        )

        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(solar_return)
        single_return_chart_svg = ChartDrawer(chart_data, theme="black-and-white").generate_svg_string()
        self._compare_chart_svg(
            "John Lennon Solar Return - Black and White Theme - SingleReturnChart Chart.svg",
            single_return_chart_svg,
        )

    def test_dual_return_lunar_chart(self):
        """
        Test Dual Return Chart (Natal + Lunar Return) against SVG baseline.
        Uses offline location data to ensure determinism and no network.
        """
        return_factory = PlanetaryReturnFactory(
            self.first_subject,
            lng=-2.9833,
            lat=53.4000,
            tz_str="Europe/London",
            online=False,
        )

        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Lunar",
        )

        chart_data = ChartDataFactory.create_return_chart_data(self.first_subject, lunar_return)
        dual_return_chart_svg = ChartDrawer(chart_data).generate_svg_string()

        self._compare_chart_svg("John Lennon - DualReturnChart Chart - Lunar Return.svg", dual_return_chart_svg)

        dual_return_chart_no_house_svg = ChartDrawer(
            chart_data,
            show_house_position_comparison=False,
        ).generate_svg_string()
        self._compare_chart_svg(
            "John Lennon - DualReturnChart Chart - Lunar Return - No House Comparison.svg",
            dual_return_chart_no_house_svg,
        )

    def test_single_return_lunar_chart(self):
        """
        Test Single Wheel Return Chart (Lunar Return only) against SVG baseline.
        Uses offline location data to ensure determinism and no network.
        """
        return_factory = PlanetaryReturnFactory(
            self.first_subject,
            lng=-2.9833,
            lat=53.4000,
            tz_str="Europe/London",
            online=False,
        )

        lunar_return = return_factory.next_return_from_iso_formatted_time(
            "2025-01-09T18:30:00+01:00",
            return_type="Lunar",
        )

        chart_data = ChartDataFactory.create_single_wheel_return_chart_data(lunar_return)
        single_return_chart_svg = ChartDrawer(chart_data).generate_svg_string()

        self._compare_chart_svg("John Lennon Lunar Return - SingleReturnChart Chart.svg", single_return_chart_svg)
