
from kerykeion.utilities import setup_logging
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.charts.kerykeion_chart_svg import KerykeionChartSVG
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory

first = AstrologicalSubjectFactory.from_birth_data("John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB")
second = AstrologicalSubjectFactory.from_birth_data("Paul McCartney", 1942, 6, 18, 15, 30, "Liverpool", "GB")

# Internal Natal Chart
internal_natal_chart = KerykeionChartSVG(first)
internal_natal_chart.makeSVG()

# External Natal Chart
external_natal_chart = KerykeionChartSVG(first, "ExternalNatal", second)
external_natal_chart.makeSVG()

# Synastry Chart
synastry_chart = KerykeionChartSVG(first, "Synastry", second)
synastry_chart.makeSVG()

# Transits Chart
transits_chart = KerykeionChartSVG(first, "Transit", second)
transits_chart.makeSVG()

# Sidereal Birth Chart (Lahiri)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Lahiri", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
sidereal_chart = KerykeionChartSVG(sidereal_subject)
sidereal_chart.makeSVG()

# Sidereal Birth Chart (Fagan-Bradley)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Fagan-Bradley", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY")
sidereal_chart = KerykeionChartSVG(sidereal_subject)
sidereal_chart.makeSVG()

# Sidereal Birth Chart (DeLuce)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon DeLuce", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="DELUCE")
sidereal_chart = KerykeionChartSVG(sidereal_subject)
sidereal_chart.makeSVG()

# Sidereal Birth Chart (J2000)
sidereal_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon J2000", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="J2000")
sidereal_chart = KerykeionChartSVG(sidereal_subject)
sidereal_chart.makeSVG()

# House System Morinus
morinus_house_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - House System Morinus", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system_identifier="M")
morinus_house_chart = KerykeionChartSVG(morinus_house_subject)
morinus_house_chart.makeSVG()

## To check all the available house systems uncomment the following code:
# from kerykeion.kr_types import HousesSystemIdentifier
# from typing import get_args
# for i in get_args(HousesSystemIdentifier):
#     alternatives_house_subject = AstrologicalSubjectFactory.from_birth_data(f"John Lennon - House System {i}", 1940, 10, 9, 18, 30, "Liverpool", "GB", houses_system=i)
#     alternatives_house_chart = KerykeionChartSVG(alternatives_house_subject)
#     alternatives_house_chart.makeSVG()

# With True Geocentric Perspective
true_geocentric_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - True Geocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", perspective_type="True Geocentric")
true_geocentric_chart = KerykeionChartSVG(true_geocentric_subject)
true_geocentric_chart.makeSVG()

# With Heliocentric Perspective
heliocentric_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Heliocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", perspective_type="Heliocentric")
heliocentric_chart = KerykeionChartSVG(heliocentric_subject)
heliocentric_chart.makeSVG()

# With Topocentric Perspective
topocentric_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Topocentric", 1940, 10, 9, 18, 30, "Liverpool", "GB", perspective_type="Topocentric")
topocentric_chart = KerykeionChartSVG(topocentric_subject)
topocentric_chart.makeSVG()

# Minified SVG
minified_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Minified", 1940, 10, 9, 18, 30, "Liverpool", "GB")
minified_chart = KerykeionChartSVG(minified_subject)
minified_chart.makeSVG(minify=True)

# Dark Theme Natal Chart
dark_theme_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
dark_theme_natal_chart = KerykeionChartSVG(dark_theme_subject, theme="dark")
dark_theme_natal_chart.makeSVG()

# Dark High Contrast Theme Natal Chart
dark_high_contrast_theme_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark High Contrast Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
dark_high_contrast_theme_natal_chart = KerykeionChartSVG(dark_high_contrast_theme_subject, theme="dark-high-contrast")
dark_high_contrast_theme_natal_chart.makeSVG()

# Light Theme Natal Chart
light_theme_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
light_theme_natal_chart = KerykeionChartSVG(light_theme_subject, theme="light")
light_theme_natal_chart.makeSVG()

# Dark Theme External Natal Chart
dark_theme_external_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Dark Theme External", 1940, 10, 9, 18, 30, "Liverpool", "GB")
dark_theme_external_chart = KerykeionChartSVG(dark_theme_external_subject, "ExternalNatal", second, theme="dark")
dark_theme_external_chart.makeSVG()

# Dark Theme Synastry Chart
dark_theme_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - DTS", 1940, 10, 9, 18, 30, "Liverpool", "GB")
dark_theme_synastry_chart = KerykeionChartSVG(dark_theme_synastry_subject, "Synastry", second, theme="dark")
dark_theme_synastry_chart.makeSVG()

# Wheel Natal Only Chart
wheel_only_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
wheel_only_chart = KerykeionChartSVG(wheel_only_subject)
wheel_only_chart.makeWheelOnlySVG()

# Wheel External Natal Only Chart
wheel_external_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel External Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
wheel_external_chart = KerykeionChartSVG(wheel_external_subject, "ExternalNatal", second)
wheel_external_chart.makeWheelOnlySVG()

# Wheel Synastry Only Chart
wheel_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Synastry Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
wheel_synastry_chart = KerykeionChartSVG(wheel_synastry_subject, "Synastry", second)
wheel_synastry_chart.makeWheelOnlySVG()

# Wheel Transit Only Chart
wheel_transit_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Wheel Transit Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
wheel_transit_chart = KerykeionChartSVG(wheel_transit_subject, "Transit", second)
wheel_transit_chart.makeWheelOnlySVG()

# Wheel Sidereal Birth Chart (Lahiri) Dark Theme
sidereal_dark_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Lahiri - Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
sidereal_dark_chart = KerykeionChartSVG(sidereal_dark_subject, theme="dark")
sidereal_dark_chart.makeWheelOnlySVG()

# Wheel Sidereal Birth Chart (Fagan-Bradley) Light Theme
sidereal_light_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon Fagan-Bradley - Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB", zodiac_type="Sidereal", sidereal_mode="FAGAN_BRADLEY")
sidereal_light_chart = KerykeionChartSVG(sidereal_light_subject, theme="light")
sidereal_light_chart.makeWheelOnlySVG()

# Aspect Grid Only Natal Chart
aspect_grid_only_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Only", 1940, 10, 9, 18, 30, "Liverpool", "GB")
aspect_grid_only_chart = KerykeionChartSVG(aspect_grid_only_subject)
aspect_grid_only_chart.makeAspectGridOnlySVG()

# Aspect Grid Only Dark Theme Natal Chart
aspect_grid_dark_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Dark Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
aspect_grid_dark_chart = KerykeionChartSVG(aspect_grid_dark_subject, theme="dark")
aspect_grid_dark_chart.makeAspectGridOnlySVG()

# Aspect Grid Only Light Theme Natal Chart
aspect_grid_light_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Light Theme", 1940, 10, 9, 18, 30, "Liverpool", "GB")
aspect_grid_light_chart = KerykeionChartSVG(aspect_grid_light_subject, theme="light")
aspect_grid_light_chart.makeAspectGridOnlySVG()

# Synastry Chart Aspect Grid Only
aspect_grid_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB")
aspect_grid_synastry_chart = KerykeionChartSVG(aspect_grid_synastry_subject, "Synastry", second)
aspect_grid_synastry_chart.makeAspectGridOnlySVG()

# Transit Chart Aspect Grid Only
aspect_grid_transit_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Transit", 1940, 10, 9, 18, 30, "Liverpool", "GB")
aspect_grid_transit_chart = KerykeionChartSVG(aspect_grid_transit_subject, "Transit", second)
aspect_grid_transit_chart.makeAspectGridOnlySVG()

# Synastry Chart Aspect Grid Only Dark Theme
aspect_grid_dark_synastry_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Aspect Grid Dark Synastry", 1940, 10, 9, 18, 30, "Liverpool", "GB")
aspect_grid_dark_synastry_chart = KerykeionChartSVG(aspect_grid_dark_synastry_subject, "Synastry", second, theme="dark")
aspect_grid_dark_synastry_chart.makeAspectGridOnlySVG()

# Synastry Chart With draw_transit_aspect_list table
synastry_chart_with_table_list_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - SCTWL", 1940, 10, 9, 18, 30, "Liverpool", "GB")
synastry_chart_with_table_list = KerykeionChartSVG(synastry_chart_with_table_list_subject, "Synastry", second, double_chart_aspect_grid_type="list", theme="dark")
synastry_chart_with_table_list.makeSVG()

# Transit Chart With draw_transit_aspect_grid table
transit_chart_with_table_grid_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - TCWTG", 1940, 10, 9, 18, 30, "Liverpool", "GB")
transit_chart_with_table_grid = KerykeionChartSVG(transit_chart_with_table_grid_subject, "Transit", second, double_chart_aspect_grid_type="table", theme="dark")
transit_chart_with_table_grid.makeSVG()

# Chines Language Chart
chinese_subject = AstrologicalSubjectFactory.from_birth_data("Hua Chenyu", 1990, 2, 7, 12, 0, "Hunan", "CN")
chinese_chart = KerykeionChartSVG(chinese_subject, chart_language="CN")
chinese_chart.makeSVG()

# French Language Chart
french_subject = AstrologicalSubjectFactory.from_birth_data("Jeanne Moreau", 1928, 1, 23, 10, 0, "Paris", "FR")
french_chart = KerykeionChartSVG(french_subject, chart_language="FR")
french_chart.makeSVG()

# Spanish Language Chart
spanish_subject = AstrologicalSubjectFactory.from_birth_data("Antonio Banderas", 1960, 8, 10, 12, 0, "Malaga", "ES")
spanish_chart = KerykeionChartSVG(spanish_subject, chart_language="ES")
spanish_chart.makeSVG()

# Portuguese Language Chart
portuguese_subject = AstrologicalSubjectFactory.from_birth_data("Cristiano Ronaldo", 1985, 2, 5, 5, 25, "Funchal", "PT")
portuguese_chart = KerykeionChartSVG(portuguese_subject, chart_language="PT")
portuguese_chart.makeSVG()

# Italian Language Chart
italian_subject = AstrologicalSubjectFactory.from_birth_data("Sophia Loren", 1934, 9, 20, 2, 0, "Rome", "IT")
italian_chart = KerykeionChartSVG(italian_subject, chart_language="IT")
italian_chart.makeSVG()

# Russian Language Chart
russian_subject = AstrologicalSubjectFactory.from_birth_data("Mikhail Bulgakov", 1891, 5, 15, 12, 0, "Kiev", "UA")
russian_chart = KerykeionChartSVG(russian_subject, chart_language="RU")
russian_chart.makeSVG()

# Turkish Language Chart
turkish_subject = AstrologicalSubjectFactory.from_birth_data("Mehmet Oz", 1960, 6, 11, 12, 0, "Istanbul", "TR")
turkish_chart = KerykeionChartSVG(turkish_subject, chart_language="TR")
turkish_chart.makeSVG()

# German Language Chart
german_subject = AstrologicalSubjectFactory.from_birth_data("Albert Einstein", 1879, 3, 14, 11, 30, "Ulm", "DE")
german_chart = KerykeionChartSVG(german_subject, chart_language="DE")
german_chart.makeSVG()

# Hindi Language Chart
hindi_subject = AstrologicalSubjectFactory.from_birth_data("Amitabh Bachchan", 1942, 10, 11, 4, 0, "Allahabad", "IN")
hindi_chart = KerykeionChartSVG(hindi_subject, chart_language="HI")
hindi_chart.makeSVG()

# Kanye West Natal Chart
kanye_west_subject = AstrologicalSubjectFactory.from_birth_data("Kanye", 1977, 6, 8, 8, 45, "Atlanta", "US")
kanye_west_chart = KerykeionChartSVG(kanye_west_subject)
kanye_west_chart.makeSVG()

# Composite Chart
angelina = AstrologicalSubjectFactory.from_birth_data("Angelina Jolie", 1975, 6, 4, 9, 9, "Los Angeles", "US", lng=-118.15, lat=34.03, tz_str="America/Los_Angeles")
brad = AstrologicalSubjectFactory.from_birth_data("Brad Pitt", 1963, 12, 18, 6, 31, "Shawnee", "US", lng=-96.56, lat=35.20, tz_str="America/Chicago")

composite_subject_factory = CompositeSubjectFactory(angelina, brad)
composite_subject_model = composite_subject_factory.get_midpoint_composite_subject_model()
composite_chart = KerykeionChartSVG(composite_subject_model, "Composite")
composite_chart.makeSVG()

## TO IMPLEMENT (Or check)

# Solar Return Chart

# Single Solar Return Chart

## Transparent Background
transparent_background_subject = AstrologicalSubjectFactory.from_birth_data("John Lennon - Transparent Background", 1940, 10, 9, 18, 30, "Liverpool", "GB")
transparent_background_chart = KerykeionChartSVG(transparent_background_subject, transparent_background=True)
transparent_background_chart.makeSVG()
