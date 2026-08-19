#!/usr/bin/env python3
"""Generate a comprehensive gallery of v6 test SVGs with an HTML index page.

Usage:
    python scripts/generate_v6_test_gallery.py [output_dir]

Default output: tests/data/v6_gallery/
"""

import sys
from typing import get_args
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from kerykeion import (
    AstrologicalSubjectFactory,
    ChartDataFactory,
    ChartDrawer,
    CompositeSubjectFactory,
    PlanetaryReturnFactory,
)
from kerykeion.schemas.literals import KerykeionChartTheme
from kerykeion.settings.config_constants import (
    ALL_ACTIVE_POINTS,
    DEFAULT_ACTIVE_POINTS,
    URANIAN_ACTIVE_POINTS,
    TRADITIONAL_ASTROLOGY_ACTIVE_POINTS,
)

OUTPUT_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent.parent / "tests" / "data" / "v6_gallery"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

THEMES = list(get_args(KerykeionChartTheme))
STYLES = ["classic", "modern"]

charts = []  # (filename, title, description, aspect_ratio)


def save(drawer, filename, style="classic", title="", desc=""):
    drawer.save_svg(output_path=str(OUTPUT_DIR), filename=filename, style=style)
    # Read viewBox to compute aspect ratio
    import re
    svg_path = OUTPUT_DIR / f"{filename}.svg"
    svg_head = svg_path.read_text(encoding="utf-8")[:500]
    vb_match = re.search(r"viewBox='(\d+)\s+([-\d]+)\s+(\d+)\s+(\d+)'", svg_head)
    if vb_match:
        w, h = int(vb_match.group(3)), int(vb_match.group(4))
        aspect = f"{w}/{h}"
    else:
        aspect = "890/580"
    charts.append((f"{filename}.svg", title or filename, desc, aspect))
    print(f"  OK  {filename}.svg (viewBox {w}x{h})")


# ===========================================================================
# SUBJECTS
# ===========================================================================
print("Creating subjects...")

default_pts = list(DEFAULT_ACTIVE_POINTS)
all_pts = list(ALL_ACTIVE_POINTS) + list(URANIAN_ACTIVE_POINTS)
trad_pts = list(TRADITIONAL_ASTROLOGY_ACTIVE_POINTS) + ["Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"]

john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30,
    lng=-2.9916, lat=53.4084, tz_str="Europe/London",
    city="Liverpool", nation="GB", online=False,
)
john_full = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon (Full v6)", 1940, 10, 9, 18, 30,
    lng=-2.9916, lat=53.4084, tz_str="Europe/London",
    city="Liverpool", nation="GB", online=False,
    active_points=all_pts,
    calculate_dignities=True,
    calculate_nakshatra=True,
    calculate_gauquelin=True,
)
john_gauq = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon (Gauquelin)", 1940, 10, 9, 18, 30,
    lng=-2.9916, lat=53.4084, tz_str="Europe/London",
    city="Liverpool", nation="GB", online=False,
    calculate_gauquelin=True,
)
john_uran = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon (Uranian)", 1940, 10, 9, 18, 30,
    lng=-2.9916, lat=53.4084, tz_str="Europe/London",
    city="Liverpool", nation="GB", online=False,
    active_points=default_pts + list(URANIAN_ACTIVE_POINTS),
)
paul = AstrologicalSubjectFactory.from_birth_data(
    "Paul McCartney", 1942, 6, 18, 15, 30,
    lng=-2.9916, lat=53.4084, tz_str="Europe/London",
    city="Liverpool", nation="GB", online=False,
)

# Sidereal
john_sid = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon (Sidereal Lahiri)", 1940, 10, 9, 18, 30,
    lng=-2.9916, lat=53.4084, tz_str="Europe/London",
    city="Liverpool", nation="GB", online=False,
    zodiac_type="Sidereal", sidereal_mode="LAHIRI",
    calculate_dignities=True, calculate_nakshatra=True,
)

# ===========================================================================
# SECTION 1: GAUQUELIN SECTORS — the main focus
# ===========================================================================
print("\n--- Gauquelin Sectors ---")

# Gauquelin with default points, all themes
for theme in THEMES:
    cd = ChartDataFactory.create_natal_chart_data(john_gauq)
    d = ChartDrawer(chart_data=cd, theme=theme)
    save(d, f"gauquelin_{theme}", "classic",
         f"Gauquelin - {theme} theme",
         "36 sectors replacing 12 houses. Bold lines at quadrants (1,10,19,28).")

# Gauquelin modern style
cd = ChartDataFactory.create_natal_chart_data(john_gauq)
save(ChartDrawer(chart_data=cd, theme="dark"), "gauquelin_modern", "modern",
     "Gauquelin - Modern Style", "Gauquelin sectors with modern concentric ring layout.")

# Gauquelin wheel only
d = ChartDrawer(chart_data=cd, theme="dark")
d.save_wheel_only_svg_file(output_path=str(OUTPUT_DIR), filename="gauquelin_wheel_only")
charts.append(("gauquelin_wheel_only.svg", "Gauquelin - Wheel Only", "Just the wheel with 36 sector divisions.", "1/1"))
print("  OK  gauquelin_wheel_only.svg")

# Normal houses (control)
cd_ctrl = ChartDataFactory.create_natal_chart_data(john)
save(ChartDrawer(chart_data=cd_ctrl, theme="dark"), "normal_houses_control", "classic",
     "Normal Houses (Control)", "Standard 12-house Placidus — no Gauquelin.")

# Gauquelin + ALL points
cd_full = ChartDataFactory.create_natal_chart_data(john_full)
save(ChartDrawer(chart_data=cd_full, theme="dark"), "gauquelin_all_points", "classic",
     "Gauquelin + ALL Points", "36 sectors + Uranian planets + all fixed stars + Arabic parts.")

# ===========================================================================
# SECTION 2: URANIAN PLANETS
# ===========================================================================
print("\n--- Uranian Planets ---")

for theme in THEMES:
    cd = ChartDataFactory.create_natal_chart_data(john_uran)
    save(ChartDrawer(chart_data=cd, theme=theme), f"uranian_{theme}", "classic",
         f"Uranian Planets - {theme}", "Cupido, Hades, Zeus, Kronos, Apollon, Admetos, Vulkanus, Poseidon")

cd = ChartDataFactory.create_natal_chart_data(john_uran)
save(ChartDrawer(chart_data=cd, theme="dark"), "uranian_modern", "modern",
     "Uranian - Modern Style", "8 Uranian planets in modern concentric layout.")

# ===========================================================================
# SECTION 3: FULL v6 FEATURES
# ===========================================================================
print("\n--- Full v6 Features ---")

for theme in THEMES:
    for style in STYLES:
        cd = ChartDataFactory.create_natal_chart_data(john_full)
        save(ChartDrawer(chart_data=cd, theme=theme), f"full_v6_{theme}_{style}", style,
             f"Full v6 - {theme} {style}", "All features: Gauquelin + Uranian + dignities + nakshatra")

# ===========================================================================
# SECTION 4: SYNASTRY / COMPOSITE / RETURN
# ===========================================================================
print("\n--- Synastry / Composite / Return ---")

cd_syn = ChartDataFactory.create_synastry_chart_data(john, paul)
save(ChartDrawer(chart_data=cd_syn, theme="dark"), "synastry_classic", "classic",
     "Synastry Chart", "John Lennon vs Paul McCartney")
save(ChartDrawer(chart_data=cd_syn, theme="dark"), "synastry_modern", "modern",
     "Synastry - Modern", "Dual wheel modern style")

comp = CompositeSubjectFactory(john, paul)
midpoint = comp.get_midpoint_composite_subject_model()
cd_comp = ChartDataFactory.create_composite_chart_data(midpoint)
save(ChartDrawer(chart_data=cd_comp, theme="dark"), "composite_midpoint", "classic",
     "Midpoint Composite", "Traditional midpoint composite")

# Davison
comp2 = CompositeSubjectFactory(john, paul)
davison = comp2.get_davison_composite_subject_model()
cd_dav = ChartDataFactory.create_composite_chart_data(davison)
save(ChartDrawer(chart_data=cd_dav, theme="dark"), "composite_davison", "classic",
     "Davison Composite", "Time-space midpoint composite (real chart)")

# Transit
cd_transit = ChartDataFactory.create_transit_chart_data(john, paul)
save(ChartDrawer(chart_data=cd_transit, theme="dark"), "transit_chart", "classic",
     "Transit Chart", "John Lennon natal + transits")

# Return
prf = PlanetaryReturnFactory(john, lng=-2.9916, lat=53.4084, tz_str="Europe/London",
                              city="Liverpool", nation="GB", online=False)
solar_return = prf.next_return_from_year(2025, "Solar")
cd_ret = ChartDataFactory.create_return_chart_data(john, solar_return)
save(ChartDrawer(chart_data=cd_ret, theme="dark"), "solar_return", "classic",
     "Solar Return 2025", "John Lennon solar return")

# ===========================================================================
# SECTION 5: SIDEREAL
# ===========================================================================
print("\n--- Sidereal ---")

cd_sid = ChartDataFactory.create_natal_chart_data(john_sid)
save(ChartDrawer(chart_data=cd_sid, theme="dark"), "sidereal_lahiri", "classic",
     "Sidereal Lahiri", "Vedic sidereal with dignities + nakshatra")


# ===========================================================================
# SECTION 6: OPTIONAL MARKS
# ===========================================================================
# Every mark switched on, on four subjects that between them carry every
# referent. A mark draws nothing where there is nothing to mark, so one chart
# could never show the set — and turning them all on means none of these can
# claim something its own sky does not have.
print("\n--- Optional Marks ---")

MARKS_ALL_ON = dict(
    show_motion_state=True,
    show_out_of_bounds=True,
    show_aspect_movement=True,
    show_relationship_score=True,
    show_ayanamsa_value=True,
    show_polar_fallback_note=True,
)

# 25 August 1990: Mercury at 0.012°/day is a stationary retrograde, and Uranus
# sits past the Sun's maximum declination.
station = AstrologicalSubjectFactory.from_birth_data(
    "Mercury Station", 1990, 8, 25, 12, 0,
    lng=-0.1276, lat=51.5074, tz_str="Europe/London",
    city="London", nation="GB", online=False,
)
cd_marks = ChartDataFactory.create_natal_chart_data(station)
for style in STYLES:
    save(ChartDrawer(chart_data=cd_marks, theme="dark", **MARKS_ALL_ON), f"marks_wheel_{style}", style,
         f"Wheel marks - {style}", "Station SR on Mercury, out-of-bounds Uranus, separating aspects dashed")

# Placidus is undefined inside the polar circle; the note says which system
# actually drew the cusps.
polar = AstrologicalSubjectFactory.from_birth_data(
    "Longyearbyen", 1990, 6, 15, 12, 0,
    lng=15.6, lat=78.2, tz_str="Arctic/Longyearbyen",
    city="Longyearbyen", nation="SJ", online=False,
    houses_system_identifier="P",
)
cd_polar = ChartDataFactory.create_natal_chart_data(polar)
save(ChartDrawer(chart_data=cd_polar, theme="dark", **MARKS_ALL_ON), "marks_polar", "classic",
     "Polar fallback note", "Placidus undefined at 78°N — the domification line admits the substitution")

cd_sid_marks = ChartDataFactory.create_natal_chart_data(john_sid)
save(ChartDrawer(chart_data=cd_sid_marks, theme="dark", **MARKS_ALL_ON), "marks_ayanamsa", "classic",
     "Ayanamsa offset", "The offset in degrees next to the mode name")

cd_syn_marks = ChartDataFactory.create_synastry_chart_data(john, paul)
save(ChartDrawer(chart_data=cd_syn_marks, theme="dark", **MARKS_ALL_ON), "marks_relationship_score", "classic",
     "Relationship score", "The synastry score and its band in the info panel")


# ===========================================================================
# GENERATE HTML INDEX
# ===========================================================================
print(f"\nGenerating HTML index ({len(charts)} charts)...")

sections = {
    "Gauquelin Sectors": [c for c in charts if "gauquelin" in c[0].lower() or "normal_houses" in c[0]],
    "Uranian Planets": [c for c in charts if "uranian" in c[0].lower()],
    "Full v6 Features": [c for c in charts if "full_v6" in c[0].lower()],
    "Synastry / Composite / Return": [c for c in charts if any(k in c[0] for k in ["synastry", "composite", "transit", "return"])],
    "Sidereal": [c for c in charts if "sidereal" in c[0].lower()],
    "Optional Marks": [c for c in charts if c[0].startswith("marks_")],
}

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Kerykeion v6 — Visual Test Gallery</title>
<style>
body { background: #0a0a1a; color: #eee; font-family: system-ui, sans-serif; margin: 0; padding: 20px; }
h1 { color: #e94560; border-bottom: 2px solid #e94560; padding-bottom: 10px; }
h2 { color: #fff; background: #e94560; padding: 10px 20px; border-radius: 6px; margin-top: 40px; }
.chart { margin: 16px 0; border: 1px solid #333; border-radius: 8px; overflow: hidden; background: #fff; }
.chart object { width: 100%; display: block; }
.chart-label { background: #16213e; padding: 8px 16px; font-weight: bold; font-size: 14px; }
.chart-desc { background: #16213e; padding: 4px 16px 8px; font-size: 12px; color: #999; }
.stats { background: #16213e; padding: 16px; border-radius: 8px; margin: 20px 0; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 1200px) { .grid { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<h1>Kerykeion v6.0 — Visual Test Gallery</h1>
<div class="stats">
<strong>Total charts:</strong> """ + str(len(charts)) + """ |
<strong>Generated from:</strong> <code>scripts/generate_v6_test_gallery.py</code> |
<strong>Branch:</strong> <code>tentative/v6</code>
</div>
"""

for section_name, section_charts in sections.items():
    if not section_charts:
        continue
    html += f'\n<h2>{section_name} ({len(section_charts)} charts)</h2>\n<div class="grid">\n'
    for filename, title, desc, aspect in section_charts:
        html += f"""<div class="chart">
<div class="chart-label">{title}</div>
<div class="chart-desc">{desc}</div>
<object data="{filename}" type="image/svg+xml" style="aspect-ratio: {aspect};"></object>
</div>\n"""
    html += "</div>\n"

html += "\n</body>\n</html>\n"

(OUTPUT_DIR / "index.html").write_text(html, encoding="utf-8")
print(f"\nDone! {len(charts)} charts generated in {OUTPUT_DIR}/")
print(f"Open: {OUTPUT_DIR / 'index.html'}")
