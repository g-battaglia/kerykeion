#!/usr/bin/env python3
"""
Generate the 43 new modern chart SVG baselines required by the expanded
TestModernChartStyle test class.

Categories:
  A1. Synastry  — 4 files (light, bw, strawberry, FR)
  A2. Transit   — 4 files (light, bw, strawberry, ES)
  A3. Composite — 5 files (dark, bw, strawberry, wheel-only, IT)
  A4. DualReturn Solar  — 2 files (dark, bw)
  A5. DualReturn Lunar  — 3 files (default, dark, bw)
  A6. SingleReturn Solar — 2 files (dark, wheel-only)
  A7. SingleReturn Lunar — 3 files (default, dark, wheel-only)
  A8. Natal — 2 files (sidereal LAHIRI, FR language)
  A9. No Zodiac Ring — 4 files (natal, synastry, composite, single return)
  A10. All Points All Aspects — 14 files (all chart types, modern style)
"""

from pathlib import Path

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

SVG_DIR = Path(__file__).parent.parent / "tests" / "data" / "svg"

# --- Subject helpers (mirror test_chart_drawer.py) ---

JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30, "Liverpool", "GB")
PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30, "Liverpool", "GB")
RETURN_ISO = "2025-01-09T18:30:00+01:00"


def _make_john(suffix="", **kwargs):
    name = f"John Lennon - {suffix}" if suffix else "John Lennon"
    return AstrologicalSubjectFactory.from_birth_data(
        name,
        *JOHN_LENNON_BIRTH_DATA,
        lng=-2.9916,
        lat=53.4084,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
        **kwargs,
    )


def _make_paul(suffix="", **kwargs):
    name = f"Paul McCartney - {suffix}" if suffix else "Paul McCartney"
    return AstrologicalSubjectFactory.from_birth_data(
        name,
        *PAUL_MCCARTNEY_BIRTH_DATA,
        lng=-2.9916,
        lat=53.4084,
        tz_str="Europe/London",
        online=False,
        suppress_geonames_warning=True,
        **kwargs,
    )


def _make_angelina():
    return AstrologicalSubjectFactory.from_birth_data(
        "Angelina Jolie",
        1975,
        6,
        4,
        9,
        9,
        "Los Angeles",
        "US",
        lng=-118.15,
        lat=34.03,
        tz_str="America/Los_Angeles",
        online=False,
        suppress_geonames_warning=True,
    )


def _make_brad():
    return AstrologicalSubjectFactory.from_birth_data(
        "Brad Pitt",
        1963,
        12,
        18,
        6,
        31,
        "Shawnee",
        "US",
        lng=-96.56,
        lat=35.20,
        tz_str="America/Chicago",
        online=False,
        suppress_geonames_warning=True,
    )


def _make_return_factory(subject):
    return PlanetaryReturnFactory(subject, lng=-2.9833, lat=53.4000, tz_str="Europe/London", online=False)


def _write(filename, svg):
    path = SVG_DIR / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    print(f"  OK  {filename} ({len(svg.splitlines())} lines)")


def generate_a1_synastry():
    print("\n=== A1. Synastry (4 files) ===")

    for suffix, theme in [
        ("Light Theme Synastry", "light"),
        ("BW Theme Synastry", "black-and-white"),
        ("Strawberry Theme Synastry", "strawberry"),
    ]:
        john, paul = _make_john(suffix), _make_paul()
        data = ChartDataFactory.create_synastry_chart_data(john, paul)
        svg = ChartDrawer(data, theme=theme).generate_svg_string(style="modern")
        _write(f"John Lennon - {suffix} - Synastry Chart - Modern.svg", svg)

    # French language
    john, paul = _make_john("FR Synastry"), _make_paul()
    data = ChartDataFactory.create_synastry_chart_data(john, paul)
    svg = ChartDrawer(data, chart_language="FR").generate_svg_string(style="modern")
    _write("John Lennon - FR Synastry - Synastry Chart - Modern.svg", svg)


def generate_a2_transit():
    print("\n=== A2. Transit (4 files) ===")

    for suffix, theme in [
        ("Light Theme Transit", "light"),
        ("BW Theme Transit", "black-and-white"),
        ("Strawberry Theme Transit", "strawberry"),
    ]:
        john, paul = _make_john(suffix), _make_paul()
        data = ChartDataFactory.create_transit_chart_data(john, paul)
        svg = ChartDrawer(data, theme=theme).generate_svg_string(style="modern")
        _write(f"John Lennon - {suffix} - Transit Chart - Modern.svg", svg)

    # Spanish language
    john, paul = _make_john("ES Transit"), _make_paul()
    data = ChartDataFactory.create_transit_chart_data(john, paul)
    svg = ChartDrawer(data, chart_language="ES").generate_svg_string(style="modern")
    _write("John Lennon - ES Transit - Transit Chart - Modern.svg", svg)


def generate_a3_composite():
    print("\n=== A3. Composite (5 files) ===")

    for theme_label, theme in [
        ("Dark Theme", "dark"),
        ("BW Theme", "black-and-white"),
        ("Strawberry Theme", "strawberry"),
    ]:
        angelina, brad = _make_angelina(), _make_brad()
        factory = CompositeSubjectFactory(angelina, brad)
        model = factory.get_midpoint_composite_subject_model()
        data = ChartDataFactory.create_composite_chart_data(model)
        svg = ChartDrawer(data, theme=theme).generate_svg_string(style="modern")
        _write(f"Angelina Jolie and Brad Pitt Composite Chart - {theme_label} - Composite Chart - Modern.svg", svg)

    # Wheel only
    angelina, brad = _make_angelina(), _make_brad()
    factory = CompositeSubjectFactory(angelina, brad)
    model = factory.get_midpoint_composite_subject_model()
    data = ChartDataFactory.create_composite_chart_data(model)
    svg = ChartDrawer(data).generate_wheel_only_svg_string(style="modern")
    _write("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart - Modern Wheel Only.svg", svg)

    # Italian language
    angelina, brad = _make_angelina(), _make_brad()
    factory = CompositeSubjectFactory(angelina, brad)
    model = factory.get_midpoint_composite_subject_model()
    data = ChartDataFactory.create_composite_chart_data(model)
    svg = ChartDrawer(data, chart_language="IT").generate_svg_string(style="modern")
    _write("Angelina Jolie and Brad Pitt Composite Chart - IT - Composite Chart - Modern.svg", svg)


def generate_a4_dual_return_solar():
    print("\n=== A4. DualReturn Solar (2 files) ===")

    john = _make_john()
    factory = _make_return_factory(john)
    sr = factory.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Solar")

    for theme_label, theme in [("Dark Theme", "dark"), ("BW Theme", "black-and-white")]:
        data = ChartDataFactory.create_return_chart_data(john, sr)
        svg = ChartDrawer(data, theme=theme).generate_svg_string(style="modern")
        _write(f"John Lennon - {theme_label} - DualReturnChart Chart - Solar Return - Modern.svg", svg)


def generate_a5_dual_return_lunar():
    print("\n=== A5. DualReturn Lunar (3 files) ===")

    john = _make_john()
    factory = _make_return_factory(john)
    lr = factory.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Lunar")

    # Default theme
    data = ChartDataFactory.create_return_chart_data(john, lr)
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon - DualReturnChart Chart - Lunar Return - Modern.svg", svg)

    for theme_label, theme in [("Dark Theme", "dark"), ("BW Theme", "black-and-white")]:
        data = ChartDataFactory.create_return_chart_data(john, lr)
        svg = ChartDrawer(data, theme=theme).generate_svg_string(style="modern")
        _write(f"John Lennon - {theme_label} - DualReturnChart Chart - Lunar Return - Modern.svg", svg)


def generate_a6_single_return_solar():
    print("\n=== A6. SingleReturn Solar (2 files) ===")

    john = _make_john()
    factory = _make_return_factory(john)
    sr = factory.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Solar")

    # Dark theme
    data = ChartDataFactory.create_single_wheel_return_chart_data(sr)
    svg = ChartDrawer(data, theme="dark").generate_svg_string(style="modern")
    _write("John Lennon Solar Return - Dark Theme - SingleReturnChart Chart - Modern.svg", svg)

    # Wheel only
    data = ChartDataFactory.create_single_wheel_return_chart_data(sr)
    svg = ChartDrawer(data).generate_wheel_only_svg_string(style="modern")
    _write("John Lennon Solar Return - SingleReturnChart Chart - Modern Wheel Only.svg", svg)


def generate_a7_single_return_lunar():
    print("\n=== A7. SingleReturn Lunar (3 files) ===")

    john = _make_john()
    factory = _make_return_factory(john)
    lr = factory.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Lunar")

    # Default theme
    data = ChartDataFactory.create_single_wheel_return_chart_data(lr)
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon Lunar Return - SingleReturnChart Chart - Modern.svg", svg)

    # Dark theme
    data = ChartDataFactory.create_single_wheel_return_chart_data(lr)
    svg = ChartDrawer(data, theme="dark").generate_svg_string(style="modern")
    _write("John Lennon Lunar Return - Dark Theme - SingleReturnChart Chart - Modern.svg", svg)

    # Wheel only
    data = ChartDataFactory.create_single_wheel_return_chart_data(lr)
    svg = ChartDrawer(data).generate_wheel_only_svg_string(style="modern")
    _write("John Lennon Lunar Return - SingleReturnChart Chart - Modern Wheel Only.svg", svg)


def generate_a8_natal():
    print("\n=== A8. Natal (2 files) ===")

    # Sidereal LAHIRI — name must match _make_sidereal_subject() in tests
    subj = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon Sidereal LAHIRI",
        *JOHN_LENNON_BIRTH_DATA,
        lng=-2.9916,
        lat=53.4084,
        tz_str="Europe/London",
        online=False,
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
        suppress_geonames_warning=True,
    )
    data = ChartDataFactory.create_natal_chart_data(subj)
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon - Sidereal LAHIRI - Natal Chart - Modern.svg", svg)

    # French language
    subj = AstrologicalSubjectFactory.from_birth_data(
        "Jeanne Moreau",
        1928,
        1,
        23,
        10,
        0,
        "Paris",
        "FR",
        lng=2.3522,
        lat=48.8566,
        tz_str="Europe/Paris",
        online=False,
        suppress_geonames_warning=True,
    )
    data = ChartDataFactory.create_natal_chart_data(subj)
    svg = ChartDrawer(data, chart_language="FR").generate_svg_string(style="modern")
    _write("Jeanne Moreau - Natal Chart - Modern.svg", svg)


def generate_a9_no_zodiac_ring():
    print("\n=== A9. No Zodiac Ring (4 files) ===")

    # Natal - No zodiac ring
    john = _make_john("No Zodiac Ring")
    data = ChartDataFactory.create_natal_chart_data(john)
    svg = ChartDrawer(data).generate_svg_string(style="modern", show_zodiac_background_ring=False)
    _write("John Lennon - No Zodiac Ring - Natal Chart - Modern.svg", svg)

    # Synastry - No zodiac ring
    john, paul = _make_john("No Zodiac Ring Synastry"), _make_paul()
    data = ChartDataFactory.create_synastry_chart_data(john, paul)
    svg = ChartDrawer(data).generate_svg_string(style="modern", show_zodiac_background_ring=False)
    _write("John Lennon - No Zodiac Ring Synastry - Synastry Chart - Modern.svg", svg)

    # Composite - No zodiac ring
    angelina, brad = _make_angelina(), _make_brad()
    factory = CompositeSubjectFactory(angelina, brad)
    model = factory.get_midpoint_composite_subject_model()
    data = ChartDataFactory.create_composite_chart_data(model)
    svg = ChartDrawer(data).generate_svg_string(style="modern", show_zodiac_background_ring=False)
    _write("Angelina Jolie and Brad Pitt Composite Chart - No Zodiac Ring - Composite Chart - Modern.svg", svg)

    # Single Return Solar - No zodiac ring
    john = _make_john()
    factory = _make_return_factory(john)
    sr = factory.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Solar")
    data = ChartDataFactory.create_single_wheel_return_chart_data(sr)
    svg = ChartDrawer(data).generate_svg_string(style="modern", show_zodiac_background_ring=False)
    _write("John Lennon Solar Return - No Zodiac Ring - SingleReturnChart Chart - Modern.svg", svg)


def generate_a10_all_points_all_aspects():
    """Generate modern baselines with ALL active points + ALL active aspects."""
    from kerykeion.settings.config_constants import ALL_ACTIVE_ASPECTS, ALL_ACTIVE_POINTS

    print("\n=== A10. All Points All Aspects — modern (14 files) ===")

    # --- Natal ---
    john = _make_john("All Points All Aspects", active_points=ALL_ACTIVE_POINTS)
    data = ChartDataFactory.create_natal_chart_data(
        john,
        active_points=ALL_ACTIVE_POINTS,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon - All Points All Aspects - Natal Chart - Modern.svg", svg)

    svg = ChartDrawer(data).generate_wheel_only_svg_string(style="modern")
    _write("John Lennon - All Points All Aspects - Natal Chart - Modern Wheel Only.svg", svg)

    # --- Synastry ---
    john = _make_john("All Points All Aspects", active_points=ALL_ACTIVE_POINTS)
    paul = _make_paul("All Points All Aspects", active_points=ALL_ACTIVE_POINTS)
    data = ChartDataFactory.create_synastry_chart_data(
        john,
        paul,
        active_points=ALL_ACTIVE_POINTS,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon - All Points All Aspects - Synastry Chart - Modern.svg", svg)

    svg = ChartDrawer(data).generate_wheel_only_svg_string(style="modern")
    _write("John Lennon - All Points All Aspects - Synastry Chart - Modern Wheel Only.svg", svg)

    # --- Transit ---
    john = _make_john("All Points All Aspects", active_points=ALL_ACTIVE_POINTS)
    paul = _make_paul("All Points All Aspects", active_points=ALL_ACTIVE_POINTS)
    data = ChartDataFactory.create_transit_chart_data(
        john,
        paul,
        active_points=ALL_ACTIVE_POINTS,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon - All Points All Aspects - Transit Chart - Modern.svg", svg)

    svg = ChartDrawer(data).generate_wheel_only_svg_string(style="modern")
    _write("John Lennon - All Points All Aspects - Transit Chart - Modern Wheel Only.svg", svg)

    # --- Composite ---
    angelina = AstrologicalSubjectFactory.from_birth_data(
        "Angelina Jolie",
        1975,
        6,
        4,
        9,
        9,
        "Los Angeles",
        "US",
        lng=-118.15,
        lat=34.03,
        tz_str="America/Los_Angeles",
        online=False,
        suppress_geonames_warning=True,
        active_points=ALL_ACTIVE_POINTS,
    )
    brad = AstrologicalSubjectFactory.from_birth_data(
        "Brad Pitt",
        1963,
        12,
        18,
        6,
        31,
        "Shawnee",
        "US",
        lng=-96.56,
        lat=35.20,
        tz_str="America/Chicago",
        online=False,
        suppress_geonames_warning=True,
        active_points=ALL_ACTIVE_POINTS,
    )
    factory = CompositeSubjectFactory(angelina, brad)
    model = factory.get_midpoint_composite_subject_model()
    data = ChartDataFactory.create_composite_chart_data(
        model,
        active_points=ALL_ACTIVE_POINTS,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write(
        "Angelina Jolie and Brad Pitt Composite Chart - All Points All Aspects - Composite Chart - Modern.svg",
        svg,
    )

    svg = ChartDrawer(data).generate_wheel_only_svg_string(style="modern")
    _write(
        "Angelina Jolie and Brad Pitt Composite Chart - All Points All Aspects - Composite Chart - Modern Wheel Only.svg",
        svg,
    )

    # --- DualReturn Solar ---
    john = _make_john(active_points=ALL_ACTIVE_POINTS)
    rf = _make_return_factory(john)
    sr = rf.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Solar")
    data = ChartDataFactory.create_return_chart_data(
        john,
        sr,
        active_points=ALL_ACTIVE_POINTS,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon - All Points All Aspects - DualReturnChart Chart - Solar Return - Modern.svg", svg)

    # --- DualReturn Lunar ---
    john = _make_john(active_points=ALL_ACTIVE_POINTS)
    rf = _make_return_factory(john)
    lr = rf.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Lunar")
    data = ChartDataFactory.create_return_chart_data(
        john,
        lr,
        active_points=ALL_ACTIVE_POINTS,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon - All Points All Aspects - DualReturnChart Chart - Lunar Return - Modern.svg", svg)

    # --- SingleReturn Solar ---
    john = _make_john(active_points=ALL_ACTIVE_POINTS)
    rf = _make_return_factory(john)
    sr = rf.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Solar")
    data = ChartDataFactory.create_single_wheel_return_chart_data(
        sr,
        active_points=ALL_ACTIVE_POINTS,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon Solar Return - All Points All Aspects - SingleReturnChart Chart - Modern.svg", svg)

    svg = ChartDrawer(data).generate_wheel_only_svg_string(style="modern")
    _write("John Lennon Solar Return - All Points All Aspects - SingleReturnChart Chart - Modern Wheel Only.svg", svg)

    # --- SingleReturn Lunar ---
    john = _make_john(active_points=ALL_ACTIVE_POINTS)
    rf = _make_return_factory(john)
    lr = rf.next_return_from_iso_formatted_time(RETURN_ISO, return_type="Lunar")
    data = ChartDataFactory.create_single_wheel_return_chart_data(
        lr,
        active_points=ALL_ACTIVE_POINTS,
        active_aspects=ALL_ACTIVE_ASPECTS,
    )
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon Lunar Return - All Points All Aspects - SingleReturnChart Chart - Modern.svg", svg)

    svg = ChartDrawer(data).generate_wheel_only_svg_string(style="modern")
    _write("John Lennon Lunar Return - All Points All Aspects - SingleReturnChart Chart - Modern Wheel Only.svg", svg)


if __name__ == "__main__":
    print(f"SVG output directory: {SVG_DIR}")
    generate_a1_synastry()
    generate_a2_transit()
    generate_a3_composite()
    generate_a4_dual_return_solar()
    generate_a5_dual_return_lunar()
    generate_a6_single_return_solar()
    generate_a7_single_return_lunar()
    generate_a8_natal()
    generate_a9_no_zodiac_ring()
    generate_a10_all_points_all_aspects()
    print("\nDone! Generated 43 modern SVG baselines.")
