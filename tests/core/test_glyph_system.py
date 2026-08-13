# -*- coding: utf-8 -*-
"""
The glyph system: one declared set, one weight, no silent deletions.

The <symbol> block in every template is *generated*. `build_chart_glyphs.py`
rewrites everything between the GLYPHS:BEGIN / GLYPHS:END markers wholesale, so
the block has two failure modes that no other test covers and that both actually
happened:

    - A symbol edited by hand inside the generated block. It survives until the
      next build and is then silently reverted. The lunar nodes were redrawn
      this way and would have gone back to their font outlines.
    - A symbol added to the templates but never declared in SPEC. The next build
      does not revert it — it *deletes* it. Five points (Interpolated Lilith,
      Mean/True Priapus, White Moon, Interpolated Perigee) were in exactly that
      state, and a single regeneration would have removed them from the charts.

So the guard here is not "does the artwork look right" — an eye settles that —
but "is what ships still what the generator produces, and is every symbol
accounted for".

The third test pins the weight contract. The font-derived silhouettes cannot be
re-weighted (a stroke-width has nothing to act on, and ink baked into a contour
can be added to but never removed), so they are the fixed point and the stroke
artwork is tuned to them. Before that rule existed seven unrelated widths were in
use and the aspects, drawn in a 10-unit box, carried more than twice the
silhouettes' apparent weight. A stray literal width would reopen it quietly.

These run offline: they compare the templates against SPEC and against each
other, and only the drift test needs the generator, which is skipped when the
font cache is cold rather than reaching for the network in CI.

Usage:
    pytest tests/core/test_glyph_system.py -v
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "kerykeion" / "charts" / "templates"
TEMPLATE_FILES = ["chart.xml", "wheel_only.xml", "aspect_grid_only.xml", "modern_wheel.xml"]

BEGIN = "GLYPHS:BEGIN"
END = "GLYPHS:END"

SYMBOL_RE = re.compile(r'<symbol id="([^"]+)">(.*?)</symbol>', re.S)
WIDTH_RE = re.compile(r'stroke-width="([0-9.]+)"')


def _load_builder():
    """Import the build script by path — scripts/ is not an importable package."""
    spec = importlib.util.spec_from_file_location(
        "build_chart_glyphs", ROOT / "scripts" / "build_chart_glyphs.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["build_chart_glyphs"] = module
    spec.loader.exec_module(module)
    return module


def _block(template: str) -> str:
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    return text[text.index(BEGIN) : text.index(END)]


def _symbols(template: str) -> dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in SYMBOL_RE.finditer(_block(template))}


class TestEverySymbolIsDeclared:
    """A symbol the generator does not know about is a symbol it will delete."""

    def test_no_template_symbol_is_missing_from_the_spec(self):
        builder = _load_builder()
        declared = [entry[0] for entry in builder.SPEC]
        shipped = list(_symbols("modern_wheel.xml"))

        undeclared = [sid for sid in shipped if sid not in declared]
        assert not undeclared, (
            "these symbols ship but are not in SPEC, so the next "
            f"build_chart_glyphs.py run deletes them: {undeclared}"
        )

    def test_the_spec_declares_nothing_the_templates_lack(self):
        builder = _load_builder()
        declared = [entry[0] for entry in builder.SPEC]
        shipped = set(_symbols("modern_wheel.xml"))

        assert [sid for sid in declared if sid not in shipped] == []

    def test_every_template_carries_the_same_set_in_the_same_order(self):
        reference = list(_symbols(TEMPLATE_FILES[0]))
        for name in TEMPLATE_FILES[1:]:
            assert list(_symbols(name)) == reference, f"{name} diverged from {TEMPLATE_FILES[0]}"


class TestTheTemplatesMatchTheGenerator:
    """Hand edits inside the generated block are reverted on the next build."""

    def test_regenerating_reproduces_the_shipped_block(self):
        builder = _load_builder()
        cache = ROOT / "scripts" / ".glyph-cache"
        if not all((cache / f"{key}.ttf").exists() for key in builder.FONT_SOURCES):
            pytest.skip(
                "font cache is cold; run `python scripts/build_chart_glyphs.py` once to "
                "populate it. This test never downloads, so CI stays offline."
            )

        regenerated = {
            m.group(1): m.group(2).strip()
            for m in SYMBOL_RE.finditer("\n".join(builder.build_lines()))
        }
        shipped = _symbols("modern_wheel.xml")

        drifted = [sid for sid, body in shipped.items() if regenerated.get(sid) != body]
        assert not drifted, (
            "these symbols differ from what the generator produces — they were "
            f"edited by hand inside the generated block: {drifted}"
        )


class TestOneWeightForEveryGlyph:
    """Stroke widths are derived from the box, never written as literals."""

    def test_only_the_derived_widths_appear_in_the_templates(self):
        builder = _load_builder()
        allowed = {
            f"{builder.stroke_for(box)}"
            for box in {builder.BOX[group] for group in builder.BOX}
        }
        found = set(WIDTH_RE.findall(_block("modern_wheel.xml")))

        assert found <= allowed, (
            f"undeclared stroke widths in the templates: {sorted(found - allowed)}. "
            f"Widths must come from stroke_for(box), which yields {sorted(allowed)}."
        )

    def test_the_derived_width_tracks_the_measured_silhouette_weight(self):
        builder = _load_builder()
        # The silhouettes' median stem is 7.41% of their ink, and outline() puts
        # that ink at 84% of the box. A change to either constant is a change to
        # how the whole set reads, so it should not pass unnoticed.
        assert builder.stroke_for(24) == pytest.approx(1.494, abs=0.001)
        assert builder.stroke_for(10) == pytest.approx(0.622, abs=0.001)
        assert builder.stroke_for(24) / builder.stroke_for(10) == pytest.approx(2.4, abs=0.01)
