#!/usr/bin/env python3
"""
Regenerate the 21 stale SVG baselines for test_chart_parametrized.py.

These baselines became stale due to draw_planets.py changes from main.

Failing tests:
- 10x test_sidereal_theme_combinations
- 5x test_house_system_synastry
- 5x test_house_system_transit
- 1x test_john_and_yoko_synastry
"""

from pathlib import Path
from kerykeion import AstrologicalSubjectFactory, ChartDrawer
from kerykeion.chart_data_factory import ChartDataFactory

SVG_DIR = Path(__file__).parent.parent / "tests" / "data" / "svg"
SVG_DIR.mkdir(parents=True, exist_ok=True)

# Common birth data
JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30, "Liverpool", "GB")
PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30, "Liverpool", "GB")

# Sidereal x Theme combinations
SIDEREAL_THEME_COMBOS = [
    ("LAHIRI", "strawberry"),
    ("LAHIRI", "black-and-white"),
    ("FAGAN_BRADLEY", "dark"),
    ("FAGAN_BRADLEY", "strawberry"),
    ("KRISHNAMURTI", "light"),
    ("KRISHNAMURTI", "strawberry"),
    ("RAMAN", "dark"),
    ("RAMAN", "strawberry"),
    ("J2000", "light"),
    ("J2000", "strawberry"),
]

# House systems
HOUSE_SYSTEM_NAMES = {
    "K": "Koch",
    "W": "Whole Sign",
    "R": "Regiomontanus",
    "C": "Campanus",
    "O": "Porphyry",
}


def regenerate_sidereal_theme_combos():
    """Regenerate 10 sidereal x theme baseline SVGs."""
    print("=== Sidereal x Theme Combinations (10 files) ===")
    for sidereal_mode, theme in SIDEREAL_THEME_COMBOS:
        subject = AstrologicalSubjectFactory.from_birth_data(
            f"John Lennon {sidereal_mode} - {theme.title()} Theme",
            *JOHN_LENNON_BIRTH_DATA,
            zodiac_type="Sidereal",
            sidereal_mode=sidereal_mode,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_natal_chart_data(subject)
        chart_svg = ChartDrawer(chart_data, theme=theme).generate_svg_string()
        file_name = f"{subject.name} - Natal Chart.svg"
        file_path = SVG_DIR / file_name
        file_path.write_text(chart_svg, encoding="utf-8")
        print(f"  ✓ {file_name} ({len(chart_svg.splitlines())} lines)")


def regenerate_house_system_synastry():
    """Regenerate 5 house system synastry baseline SVGs."""
    print("\n=== House System Synastry (5 files) ===")
    for house_id, house_name in HOUSE_SYSTEM_NAMES.items():
        first = AstrologicalSubjectFactory.from_birth_data(
            f"John Lennon - {house_name} Synastry",
            *JOHN_LENNON_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            f"Paul McCartney - {house_name}",
            *PAUL_MCCARTNEY_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_synastry_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        file_name = f"John Lennon - {house_name} - Synastry Chart.svg"
        file_path = SVG_DIR / file_name
        file_path.write_text(chart_svg, encoding="utf-8")
        print(f"  ✓ {file_name} ({len(chart_svg.splitlines())} lines)")


def regenerate_house_system_transit():
    """Regenerate 5 house system transit baseline SVGs."""
    print("\n=== House System Transit (5 files) ===")
    for house_id, house_name in HOUSE_SYSTEM_NAMES.items():
        first = AstrologicalSubjectFactory.from_birth_data(
            f"John Lennon - {house_name} Transit",
            *JOHN_LENNON_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        second = AstrologicalSubjectFactory.from_birth_data(
            f"Paul McCartney - {house_name} Transit",
            *PAUL_MCCARTNEY_BIRTH_DATA,
            houses_system_identifier=house_id,
            suppress_geonames_warning=True,
        )
        chart_data = ChartDataFactory.create_transit_chart_data(first, second)
        chart_svg = ChartDrawer(chart_data).generate_svg_string()
        file_name = f"John Lennon - {house_name} - Transit Chart.svg"
        file_path = SVG_DIR / file_name
        file_path.write_text(chart_svg, encoding="utf-8")
        print(f"  ✓ {file_name} ({len(chart_svg.splitlines())} lines)")


def regenerate_john_and_yoko_synastry():
    """Regenerate John and Yoko synastry baseline SVG."""
    print("\n=== John and Yoko Synastry (1 file) ===")
    # Match test_chart_parametrized.py exactly: uses create_subject_from_dict
    # which calls AstrologicalSubjectFactory.from_birth_data with lat/lng/tz_str
    john = AstrologicalSubjectFactory.from_birth_data(
        "John and Yoko",  # name is overridden in test
        1940,
        10,
        9,
        18,
        30,
        "John Lennon",  # city = subject name per create_subject_from_dict
        "XX",
        lat=53.4084,
        lng=-2.9916,
        tz_str="Europe/London",
        suppress_geonames_warning=True,
    )
    yoko = AstrologicalSubjectFactory.from_birth_data(
        "Yoko Ono",
        1933,
        2,
        18,
        10,
        30,
        "Yoko Ono",  # city = subject name per create_subject_from_dict
        "XX",
        lat=35.6762,
        lng=139.6503,
        tz_str="Asia/Tokyo",
        suppress_geonames_warning=True,
    )
    chart_data = ChartDataFactory.create_synastry_chart_data(john, yoko)
    chart_svg = ChartDrawer(chart_data).generate_svg_string()
    file_name = "John and Yoko - Synastry Chart.svg"
    file_path = SVG_DIR / file_name
    file_path.write_text(chart_svg, encoding="utf-8")
    print(f"  ✓ {file_name} ({len(chart_svg.splitlines())} lines)")


if __name__ == "__main__":
    print(f"SVG output directory: {SVG_DIR}\n")
    regenerate_sidereal_theme_combos()
    regenerate_house_system_synastry()
    regenerate_house_system_transit()
    regenerate_john_and_yoko_synastry()
    print("\nDone! Regenerated 21 SVG baselines.")
