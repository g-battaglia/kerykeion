from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion import ChartDrawer
from pathlib import Path
from os import makedirs as mkdirs

OUTPUT = str(Path.home() / "kerykeion_charts_output")
mkdirs(OUTPUT, exist_ok=True)
THEMES = ["black-and-white", "classic", "dark-high-contrast", "dark", "light", "strawberry"]

# ── Subject 1: John Lennon ──────────────────────────────────────────────────
lennon = AstrologicalSubjectFactory.from_birth_data(
    name="John Lennon",
    year=1940, month=10, day=9, hour=18, minute=30,
    city="Liverpool", nation="GB",
    tz_str="Europe/London", lat=53.4084, lng=-2.9916,
)

# ── Subject 2: Yoko Ono (for synastry) ──────────────────────────────────────
yoko = AstrologicalSubjectFactory.from_birth_data(
    name="Yoko Ono",
    year=1933, month=2, day=18, hour=20, minute=30,
    city="Tokyo", nation="JP",
    tz_str="Asia/Tokyo", lat=35.6762, lng=139.6503,
)

# ── Subject 3: Day Lennon met McCartney - July 6, 1957 (transit) ────────────
transit = AstrologicalSubjectFactory.from_birth_data(
    name="Lennon Meets McCartney",
    year=1957, month=7, day=6, hour=16, minute=0,
    city="Liverpool", nation="GB",
    tz_str="Europe/London", lat=53.4084, lng=-2.9916,
)

def generate_charts_for_theme(theme_name):
    prefix = f"{theme_name}_"

    # ════════════════════════════════════════════════════════════════════════════
    # 0. McCartney meeting event as STANDALONE natal chart (for comparison)
    # ════════════════════════════════════════════════════════════════════════════
    meeting_data = ChartDataFactory.create_natal_chart_data(transit)
    meeting_drawer = ChartDrawer(meeting_data, theme=theme_name)
    meeting_drawer.save_minimalist_svg_file(output_path=OUTPUT, filename=f"{prefix}mccartney_meeting_natal")

    # ════════════════════════════════════════════════════════════════════════════
    # 1. NATAL CHART (single, regression check)
    # ════════════════════════════════════════════════════════════════════════════
    natal_data = ChartDataFactory.create_natal_chart_data(lennon)
    natal_drawer = ChartDrawer(natal_data, theme=theme_name)
    natal_drawer.save_minimalist_svg_file(output_path=OUTPUT, filename=f"{prefix}lennon_natal")

    # ════════════════════════════════════════════════════════════════════════════
    # 2. SYNASTRY CHART (Lennon + Yoko Ono)
    # ════════════════════════════════════════════════════════════════════════════
    synastry_data = ChartDataFactory.create_synastry_chart_data(lennon, yoko)
    synastry_drawer = ChartDrawer(synastry_data, theme=theme_name)

    synastry_drawer.save_minimalist_dual_svg_file(
        output_path=OUTPUT,
        filename=f"{prefix}lennon_yoko_synastry"
    )

    synastry_drawer.save_minimalist_dual_svg_file(
        output_path=OUTPUT,
        show_houses_2=False,
        filename=f"{prefix}lennon_yoko_synastry_transit_style"
    )

    # ════════════════════════════════════════════════════════════════════════════
    # 3. TRANSIT CHART (Lennon natal + McCartney meeting date)
    # ════════════════════════════════════════════════════════════════════════════
    transit_data = ChartDataFactory.create_transit_chart_data(lennon, transit)
    transit_drawer = ChartDrawer(transit_data, theme=theme_name)

    transit_drawer.save_minimalist_dual_svg_file(
        output_path=OUTPUT,
        filename=f"{prefix}lennon_mccartney_transit"
    )

    transit_drawer.save_minimalist_dual_svg_file(
        output_path=OUTPUT,
        show_houses_2=True,
        filename=f"{prefix}lennon_mccartney_transit_both_houses"
    )

    # ════════════════════════════════════════════════════════════════════════════
    # 4. SYNASTRY with cusp rings toggled off
    # ════════════════════════════════════════════════════════════════════════════
    synastry_drawer.save_minimalist_dual_svg_file(
        output_path=OUTPUT,
        show_cusp_ring_1=False,
        show_cusp_ring_2=False,
        filename=f"{prefix}lennon_yoko_synastry_no_cusps"
    )

    # ════════════════════════════════════════════════════════════════════════════
    # 5. Synastry with zodiac ring explicitly OFF (override new default)
    # ════════════════════════════════════════════════════════════════════════════
    synastry_drawer.save_minimalist_dual_svg_file(
        output_path=OUTPUT,
        show_zodiac_background_ring=False,
        filename=f"{prefix}lennon_yoko_synastry_no_zodiac"
    )

for theme in THEMES:
    print(f"\n🎨 Generating charts for theme: {theme}")
    generate_charts_for_theme(theme)

print("\n🎉 All charts generated successfully!")
