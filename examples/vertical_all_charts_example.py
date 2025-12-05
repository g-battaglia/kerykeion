"""
Example script to generate vertical A4 portrait charts for all chart types.

This demonstrates:
- Natal chart (single wheel, aspect grid)
- Composite chart (single wheel, aspect grid)
- Transit chart (double wheel, aspect list vs aspect grid)
- Synastry chart (double wheel, aspect list vs aspect grid)
- DualReturnChart (double wheel, aspect list vs aspect grid)
- SingleReturnChart (single wheel, aspect grid)
"""

from pathlib import Path
from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.composite_subject_factory import CompositeSubjectFactory
from kerykeion.chart_data_factory import ChartDataFactory
from kerykeion.charts.chart_drawer import ChartDrawer
from kerykeion.planetary_return_factory import PlanetaryReturnFactory

# Output directory
OUTPUT_DIR = Path("./vertical_charts_output")
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 60)
print("VERTICAL A4 PORTRAIT CHARTS - All Types Demo")
print("=" * 60)

# Create subjects
john = AstrologicalSubjectFactory.from_birth_data(
    "John Lennon", 1940, 10, 9, 18, 30, "Liverpool", "GB"
)
yoko = AstrologicalSubjectFactory.from_birth_data(
    "Yoko Ono", 1933, 2, 18, 20, 30, "Tokyo", "JP"
)
transit = AstrologicalSubjectFactory.from_iso_utc_time(
    "Transit", "2024-12-05T12:00:00+00:00"
)

# Return factory for solar/lunar returns
return_factory = PlanetaryReturnFactory(
    john,
    city="Los Angeles",
    nation="US",
    lng=-118.2437,
    lat=34.0522,
    tz_str="America/Los_Angeles",
    altitude=0
)

# ============================================================
# 1. NATAL CHART (single wheel)
# ============================================================
print("\n1. Generating Natal Chart (vertical)...")
natal_data = ChartDataFactory.create_natal_chart_data(john)
natal_drawer = ChartDrawer(natal_data, theme="classic", chart_language="EN")
natal_drawer.save_vertical_svg(
    output_path=OUTPUT_DIR,
    filename="01_natal_vertical"
)
print("   ✓ Saved: 01_natal_vertical.svg")

# ============================================================
# 2. COMPOSITE CHART (single wheel)
# ============================================================
print("\n2. Generating Composite Chart (vertical)...")
# Create composite subject using the factory
composite_factory = CompositeSubjectFactory(john, yoko)
composite_subject = composite_factory.get_midpoint_composite_subject_model()
composite_data = ChartDataFactory.create_composite_chart_data(composite_subject)
composite_drawer = ChartDrawer(composite_data, theme="dark", chart_language="EN")
composite_drawer.save_vertical_svg(
    output_path=OUTPUT_DIR,
    filename="02_composite_vertical"
)
print("   ✓ Saved: 02_composite_vertical.svg")


# ============================================================
# 3. TRANSIT CHART - Aspect List mode (default)
# ============================================================
print("\n3. Generating Transit Chart - Aspect List mode (vertical)...")
transit_data = ChartDataFactory.create_transit_chart_data(john, transit)
transit_drawer_list = ChartDrawer(
    transit_data,
    theme="strawberry",
    chart_language="EN",
    double_chart_aspect_grid_type="list"
)
transit_drawer_list.save_vertical_svg(
    output_path=OUTPUT_DIR,
    filename="03_transit_aspect_list_vertical"
)
print("   ✓ Saved: 03_transit_aspect_list_vertical.svg")

# ============================================================
# 4. TRANSIT CHART - Aspect Grid mode
# ============================================================
print("\n4. Generating Transit Chart - Aspect Grid mode (vertical)...")
transit_drawer_grid = ChartDrawer(
    transit_data,
    theme="strawberry",
    chart_language="EN",
    double_chart_aspect_grid_type="table"
)
transit_drawer_grid.save_vertical_svg(
    output_path=OUTPUT_DIR,
    filename="04_transit_aspect_grid_vertical"
)
print("   ✓ Saved: 04_transit_aspect_grid_vertical.svg")

# ============================================================
# 5. SYNASTRY CHART - Aspect List mode (default)
# ============================================================
print("\n5. Generating Synastry Chart - Aspect List mode (vertical)...")
synastry_data = ChartDataFactory.create_synastry_chart_data(john, yoko)
synastry_drawer_list = ChartDrawer(
    synastry_data,
    theme="classic",
    chart_language="EN",
    double_chart_aspect_grid_type="list"
)
synastry_drawer_list.save_vertical_svg(
    output_path=OUTPUT_DIR,
    filename="05_synastry_aspect_list_vertical"
)
print("   ✓ Saved: 05_synastry_aspect_list_vertical.svg")

# ============================================================
# 6. SYNASTRY CHART - Aspect Grid mode
# ============================================================
print("\n6. Generating Synastry Chart - Aspect Grid mode (vertical)...")
synastry_drawer_grid = ChartDrawer(
    synastry_data,
    theme="classic",
    chart_language="EN",
    double_chart_aspect_grid_type="table"
)
synastry_drawer_grid.save_vertical_svg(
    output_path=OUTPUT_DIR,
    filename="06_synastry_aspect_grid_vertical"
)
print("   ✓ Saved: 06_synastry_aspect_grid_vertical.svg")

# ============================================================
# 7. DUAL RETURN CHART (Solar Return) - Aspect List mode
# ============================================================
print("\n7. Generating Dual Solar Return Chart - Aspect List mode (vertical)...")
solar_return = return_factory.next_return_from_iso_formatted_time(
    "2024-10-09T00:00:00+00:00",
    return_type="Solar",
)
solar_return_data = ChartDataFactory.create_return_chart_data(
    john, solar_return
)
solar_return_drawer_list = ChartDrawer(
    solar_return_data,
    theme="dark",
    chart_language="EN",
    double_chart_aspect_grid_type="list"
)
solar_return_drawer_list.save_vertical_svg(
    output_path=OUTPUT_DIR,
    filename="07_solar_return_aspect_list_vertical"
)
print("   ✓ Saved: 07_solar_return_aspect_list_vertical.svg")

# ============================================================
# 8. DUAL RETURN CHART (Solar Return) - Aspect Grid mode
# ============================================================
print("\n8. Generating Dual Solar Return Chart - Aspect Grid mode (vertical)...")
solar_return_drawer_grid = ChartDrawer(
    solar_return_data,
    theme="dark",
    chart_language="EN",
    double_chart_aspect_grid_type="table"
)
solar_return_drawer_grid.save_vertical_svg(
    output_path=OUTPUT_DIR,
    filename="08_solar_return_aspect_grid_vertical"
)
print("   ✓ Saved: 08_solar_return_aspect_grid_vertical.svg")

# ============================================================
# 9. SINGLE WHEEL RETURN CHART
# ============================================================
print("\n9. Generating Single Wheel Solar Return Chart (vertical)...")
single_return_data = ChartDataFactory.create_single_wheel_return_chart_data(
    solar_return
)
single_return_drawer = ChartDrawer(
    single_return_data,
    theme="strawberry",
    chart_language="EN"
)
single_return_drawer.save_vertical_svg(
    output_path=OUTPUT_DIR,
    filename="09_single_return_vertical"
)
print("   ✓ Saved: 09_single_return_vertical.svg")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 60)
print("ALL VERTICAL CHARTS GENERATED SUCCESSFULLY!")
print("=" * 60)
print(f"\nOutput directory: {OUTPUT_DIR.absolute()}")
print("\nGenerated files:")
for f in sorted(OUTPUT_DIR.glob("*.svg")):
    print(f"  - {f.name}")
