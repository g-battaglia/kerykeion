#!/usr/bin/env python3
"""
Generate the 43 new modern chart SVG baselines required by the expanded
TestModernChartStyle test class.

Categories:
  A1. Synastry  — 2 files (bw, FR)
  A2. Transit   — 2 files (bw, ES)
  A3. Composite — 4 files (dark, bw, wheel-only, IT)
  A4. DualReturn Solar  — 2 files (dark, bw)
  A5. DualReturn Lunar  — 3 files (default, dark, bw)
  A6. SingleReturn Solar — 2 files (dark, wheel-only)
  A7. SingleReturn Lunar — 3 files (default, dark, wheel-only)
  A8. Natal — 2 files (sidereal LAHIRI, FR language)
  A9. No Zodiac Ring — 4 files (natal, synastry, composite, single return)
  A10. All Points All Aspects — 14 files (all chart types, modern style)
  A11. Optional marks — 6 files (one per opt-in mark, all styles' shared panels)
  A12. Glyph sizes — 8 files (small/large cluster profiles; medium is every
       other baseline in this directory and needs no twin)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tests.data.golden_places import golden_place
from tests.data.regeneration_guard import require_library_from_this_checkout, require_the_baseline_backend

require_library_from_this_checkout(__file__)
require_the_baseline_backend()

from kerykeion import AstrologicalSubjectFactory
from kerykeion.chart_data.factory import ChartDataFactory
from kerykeion.charts.drawer import ChartDrawer
from kerykeion.composite_subject.factory import CompositeSubjectFactory
from kerykeion.planetary_returns.factory import PlanetaryReturnFactory

SVG_DIR = Path(__file__).parent.parent / "tests" / "data" / "svg"

# --- Subject helpers (mirror test_chart_drawer.py) ---

JOHN_LENNON_BIRTH_DATA = (1940, 10, 9, 18, 30)
PAUL_MCCARTNEY_BIRTH_DATA = (1942, 6, 18, 15, 30)
# The place is pinned, not resolved: the tests cast from the same frozen coordinates.
LIVERPOOL = golden_place("Liverpool", "GB")
RETURN_ISO = "2025-01-09T18:30:00+01:00"


def _make_john(suffix="", **kwargs):
    name = f"John Lennon - {suffix}" if suffix else "John Lennon"
    return AstrologicalSubjectFactory.from_birth_data(
        name,
        *JOHN_LENNON_BIRTH_DATA,
        suppress_geonames_warning=True,
        **LIVERPOOL,
        **kwargs,
    )


def _make_paul(suffix="", **kwargs):
    name = f"Paul McCartney - {suffix}" if suffix else "Paul McCartney"
    return AstrologicalSubjectFactory.from_birth_data(
        name,
        *PAUL_MCCARTNEY_BIRTH_DATA,
        suppress_geonames_warning=True,
        **LIVERPOOL,
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
        ("BW Theme Synastry", "black-and-white"),
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
        ("BW Theme Transit", "black-and-white"),
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

    # Sidereal LAHIRI — must match _make_sidereal_subject() in tests
    subj = AstrologicalSubjectFactory.from_birth_data(
        "John Lennon Sidereal LAHIRI",
        *JOHN_LENNON_BIRTH_DATA,
        **LIVERPOOL,
        zodiac_type="Sidereal",
        sidereal_mode="LAHIRI",
        suppress_geonames_warning=True,
    )
    data = ChartDataFactory.create_natal_chart_data(subj)
    svg = ChartDrawer(data).generate_svg_string(style="modern")
    _write("John Lennon - Sidereal LAHIRI - Natal Chart - Modern.svg", svg)

    # French language — must match test
    subj = AstrologicalSubjectFactory.from_birth_data(
        "Jeanne Moreau",
        1928,
        1,
        23,
        10,
        0,
        **golden_place("Paris", "FR"),
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


def generate_a11_optional_marks():
    """One baseline per opt-in mark, each on a subject that actually has its referent.

    A mark drawn on a chart that has nothing to mark would pin an empty
    promise: the station subject really does have Mercury at a station, the
    out-of-bounds one really does have a body past the obliquity, and so on.
    """
    print("\n=== A11. Optional marks (6 files) ===")

    # Station markers — Mercury turns retrograde on this date.
    station = AstrologicalSubjectFactory.from_birth_data(
        "Mercury Station", 1990, 8, 25, 12, 0, suppress_geonames_warning=True, **golden_place("London", "GB")
    )
    data = ChartDataFactory.create_natal_chart_data(station)
    svg = ChartDrawer(data, show_motion_state=True).generate_svg_string(style="modern")
    _write("Mercury Station - Motion State - Natal Chart - Modern.svg", svg)

    # Separating aspects dashed, on the same chart.
    svg = ChartDrawer(data, show_aspect_movement=True).generate_svg_string(style="modern")
    _write("Mercury Station - Aspect Movement - Natal Chart - Modern.svg", svg)

    # Out-of-bounds badge — Uranus sits past the obliquity here.
    oob = AstrologicalSubjectFactory.from_birth_data(
        "Out Of Bounds", 1990, 1, 1, 12, 0, suppress_geonames_warning=True, **golden_place("London", "GB")
    )
    data = ChartDataFactory.create_natal_chart_data(oob)
    svg = ChartDrawer(data, show_out_of_bounds=True).generate_svg_string(style="modern")
    _write("Out Of Bounds - Natal Chart - Modern.svg", svg)

    # Relationship score line.
    john, paul = _make_john("Relationship Score"), _make_paul()
    data = ChartDataFactory.create_synastry_chart_data(john, paul)
    svg = ChartDrawer(data, show_relationship_score=True).generate_svg_string(style="modern")
    _write("John Lennon - Relationship Score - Synastry Chart - Modern.svg", svg)

    # Ayanamsa offset in degrees.
    sidereal = _make_john("Ayanamsa Value", zodiac_type="Sidereal", sidereal_mode="LAHIRI")
    data = ChartDataFactory.create_natal_chart_data(sidereal)
    svg = ChartDrawer(data, show_ayanamsa_value=True).generate_svg_string(style="modern")
    _write("John Lennon - Ayanamsa Value - Natal Chart - Modern.svg", svg)

    # Polar fallback note — Placidus is undefined this far north.
    polar = AstrologicalSubjectFactory.from_birth_data(
        "Polar Fallback",
        1990,
        6,
        15,
        12,
        0,
        "Longyearbyen",
        "SJ",
        lng=15.6,
        lat=78.2,
        tz_str="Arctic/Longyearbyen",
        houses_system_identifier="P",
        suppress_geonames_warning=True,
    )
    data = ChartDataFactory.create_natal_chart_data(polar)
    svg = ChartDrawer(data, show_polar_fallback_note=True).generate_svg_string(style="modern")
    _write("Polar Fallback - Natal Chart - Modern.svg", svg)


def generate_a12_glyph_sizes():
    """The small and large cluster profiles, on the charts that stress them.

    Eight files, chosen small on purpose — the profile numbers are pinned
    numerically in test_modern_decluttering, so these baselines exist to catch
    STRUCTURAL surprises (a row landing elsewhere, a tether re-anchored, the
    resolver spreading differently), not to re-pin the profiles:
    natal small/large (the parity chart), the large wheel-only (no 0.92/4.8
    wrapper), synastry small/large (both dual rings, large is the tight one),
    a transit at large (retrograde-heavy outer ring), the all-points natal at
    large (the documented over-subscription path), and a composite at small
    (single ring, second subject shape).
    """
    print("\n=== A12. Glyph sizes (8 files) ===")

    john, paul = _make_john(), _make_paul()
    natal = ChartDataFactory.create_natal_chart_data(john)
    for size in ("small", "large"):
        svg = ChartDrawer(natal).generate_svg_string(style="modern", glyph_size=size)
        _write(f"John Lennon - Natal Chart - Modern {size.capitalize()}.svg", svg)
    svg = ChartDrawer(natal).generate_wheel_only_svg_string(style="modern", glyph_size="large")
    _write("John Lennon - Natal Chart - Modern Large Wheel Only.svg", svg)

    synastry = ChartDataFactory.create_synastry_chart_data(john, paul)
    for size in ("small", "large"):
        svg = ChartDrawer(synastry).generate_svg_string(style="modern", glyph_size=size)
        _write(f"John Lennon - Synastry Chart - Modern {size.capitalize()}.svg", svg)

    transit = ChartDataFactory.create_transit_chart_data(john, paul)
    svg = ChartDrawer(transit).generate_svg_string(style="modern", glyph_size="large")
    _write("John Lennon - Transit Chart - Modern Large.svg", svg)

    from kerykeion.settings.config_constants import ALL_ACTIVE_POINTS

    all_points = _make_john("All Active Points", active_points=ALL_ACTIVE_POINTS)
    data = ChartDataFactory.create_natal_chart_data(all_points, active_points=ALL_ACTIVE_POINTS)
    svg = ChartDrawer(data).generate_svg_string(style="modern", glyph_size="large")
    _write("John Lennon - All Active Points - Natal Chart - Modern Large.svg", svg)

    angelina, brad = _make_angelina(), _make_brad()
    model = CompositeSubjectFactory(angelina, brad).get_midpoint_composite_subject_model()
    data = ChartDataFactory.create_composite_chart_data(model)
    svg = ChartDrawer(data).generate_svg_string(style="modern", glyph_size="small")
    _write("Angelina Jolie and Brad Pitt Composite Chart - Composite Chart - Modern Small.svg", svg)


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
    generate_a11_optional_marks()
    generate_a12_glyph_sizes()
    print("\nDone! Generated 57 modern SVG baselines.")
