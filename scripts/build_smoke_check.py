"""Smoke-check the built wheel: import kerykeion and render one chart.

Run by ``poe build:smoke`` inside an isolated environment where ONLY the
wheel (and its PyPI dependencies) is installed — the repo checkout is not on
``sys.path`` — so a data file missing from the wheel (chart templates, theme
CSS) fails here instead of after publishing.

The subject is created fully offline (explicit coordinates and timezone) so
the check never hits the GeoNames API.

This environment holds the LIBRARY wheel alone, so it is also where the split
is proven: the command belongs to the separate ``kerykeion-cli`` distribution,
and a plain install must carry neither the package nor the console script.
"""

import importlib.metadata
import importlib.util

import kerykeion
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

assert importlib.util.find_spec("kerykeion_cli") is None, "the library wheel ships the CLI package"
scripts = [ep for ep in importlib.metadata.entry_points(group="console_scripts") if ep.name == "kerykeion"]
assert not scripts, f"the library wheel declares a console script: {scripts!r}"

subject = AstrologicalSubjectFactory.from_birth_data(
    "Build Smoke",
    1990,
    1,
    1,
    12,
    0,
    lng=12.4964,
    lat=41.9028,
    tz_str="Europe/Rome",
    city="Rome",
    nation="IT",
    online=False,
    suppress_geonames_warning=True,
)
data = ChartDataFactory.create_natal_chart_data(subject)
svg = ChartDrawer(data).generate_svg_string()

assert "<svg" in svg, "no SVG produced"
assert "--kerykeion-color-neutral-content" in svg, "theme CSS not embedded in the chart"
assert len(svg) > 10_000, f"suspiciously small SVG ({len(svg)} chars)"

print(f"wheel smoke OK: {kerykeion.__name__} rendered a {len(svg)}-char natal chart, and carries no CLI")
