from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion import ChartDrawer
from pathlib import Path
from os import makedirs as mkdirs

OUTPUT = str(Path.home() / "kerykeion_charts_output")
THEMES = ["classic", "black-and-white", "dark", "dark-high-contrast", "light", "strawberry"]

# ── Subject 1: John Lennon ──────────────────────────────────────────────────
lennon = AstrologicalSubjectFactory.from_birth_data(
    name="John Lennon",
    year=1940,
    month=10,
    day=9,
    hour=18,
    minute=30,
    city="Liverpool",
    nation="GB",
    tz_str="Europe/London",
    lat=53.4084,
    lng=-2.9916,
    online=False,
)

# ── Subject 2: Yoko Ono (for synastry) ──────────────────────────────────────
yoko = AstrologicalSubjectFactory.from_birth_data(
    name="Yoko Ono",
    year=1933,
    month=2,
    day=18,
    hour=20,
    minute=30,
    city="Tokyo",
    nation="JP",
    tz_str="Asia/Tokyo",
    lat=35.6762,
    lng=139.6503,
    online=False,
)

# ── Subject 3: Day Lennon met McCartney - July 6, 1957 (transit) ────────────
transit = AstrologicalSubjectFactory.from_birth_data(
    name="Lennon Meets McCartney",
    year=1957,
    month=7,
    day=6,
    hour=16,
    minute=0,
    city="Liverpool",
    nation="GB",
    tz_str="Europe/London",
    lat=53.4084,
    lng=-2.9916,
    online=False,
)


def generate_charts_for_theme(theme_name):
    prefix = f"{theme_name}_"

    # ════════════════════════════════════════════════════════════════════════════
    # 0. McCartney meeting event as STANDALONE natal chart
    # ════════════════════════════════════════════════════════════════════════════
    meeting_data = ChartDataFactory.create_natal_chart_data(transit)
    meeting_drawer = ChartDrawer(meeting_data, theme=theme_name)
    meeting_drawer.save_svg(output_path=OUTPUT, filename=f"{prefix}mccartney_meeting_natal", style="modern")
    meeting_drawer.save_wheel_only_svg_file(
        output_path=OUTPUT, filename=f"{prefix}mccartney_meeting_natal_wheel", style="modern"
    )

    # ════════════════════════════════════════════════════════════════════════════
    # 1. NATAL CHART (single) — zodiac ring on by default
    # ════════════════════════════════════════════════════════════════════════════
    natal_data = ChartDataFactory.create_natal_chart_data(lennon)
    natal_drawer = ChartDrawer(natal_data, theme=theme_name)
    natal_drawer.save_svg(output_path=OUTPUT, filename=f"{prefix}lennon_natal", style="modern")
    natal_drawer.save_wheel_only_svg_file(output_path=OUTPUT, filename=f"{prefix}lennon_natal_wheel", style="modern")

    # ════════════════════════════════════════════════════════════════════════════
    # 2. NATAL CHART — without zodiac ring (for comparison)
    # ════════════════════════════════════════════════════════════════════════════
    natal_drawer.save_svg(
        output_path=OUTPUT,
        filename=f"{prefix}lennon_natal_no_zodiac",
        style="modern",
        show_zodiac_background_ring=False,
    )
    natal_drawer.save_wheel_only_svg_file(
        output_path=OUTPUT,
        filename=f"{prefix}lennon_natal_no_zodiac_wheel",
        style="modern",
        show_zodiac_background_ring=False,
    )

    # ════════════════════════════════════════════════════════════════════════════
    # 3. SYNASTRY CHART (Lennon + Yoko Ono) — zodiac ring on by default
    # ════════════════════════════════════════════════════════════════════════════
    synastry_data = ChartDataFactory.create_synastry_chart_data(lennon, yoko)
    synastry_drawer = ChartDrawer(synastry_data, theme=theme_name)
    synastry_drawer.save_svg(output_path=OUTPUT, filename=f"{prefix}lennon_yoko_synastry", style="modern")
    synastry_drawer.save_wheel_only_svg_file(
        output_path=OUTPUT, filename=f"{prefix}lennon_yoko_synastry_wheel", style="modern"
    )

    # ════════════════════════════════════════════════════════════════════════════
    # 4. TRANSIT CHART (Lennon natal + McCartney meeting date)
    # ════════════════════════════════════════════════════════════════════════════
    transit_data = ChartDataFactory.create_transit_chart_data(lennon, transit)
    transit_drawer = ChartDrawer(transit_data, theme=theme_name)
    transit_drawer.save_svg(output_path=OUTPUT, filename=f"{prefix}lennon_mccartney_transit", style="modern")
    transit_drawer.save_wheel_only_svg_file(
        output_path=OUTPUT, filename=f"{prefix}lennon_mccartney_transit_wheel", style="modern"
    )

    # ════════════════════════════════════════════════════════════════════════════
    # 5. SYNASTRY without zodiac ring (for comparison)
    # ════════════════════════════════════════════════════════════════════════════
    synastry_drawer.save_svg(
        output_path=OUTPUT,
        filename=f"{prefix}lennon_yoko_synastry_no_zodiac",
        style="modern",
        show_zodiac_background_ring=False,
    )


def main():
    mkdirs(OUTPUT, exist_ok=True)
    for theme in THEMES:
        print(f"\n  Generating charts for theme: {theme}")
        generate_charts_for_theme(theme)

    print("\n  All charts generated successfully!")


if __name__ == "__main__":
    main()
