# -*- coding: utf-8 -*-
"""The glyph system: one declared set, one weight, one colour, no silent deletions.

The <symbol> block in every template is *generated*. `build_chart_glyphs.py`
rewrites everything between the GLYPHS:BEGIN / GLYPHS:END markers wholesale, so
the block has two failure modes that no other test covers and that both actually
happened:

    - A symbol edited by hand inside the generated block. It survives until the
      next build and is then silently reverted. The lunar nodes were redrawn
      this way and would have gone back to their font outlines.
    - A symbol added to the templates but never declared in the catalog. The next
      build does not revert it — it *deletes* it. Five points (Interpolated
      Lilith, Mean/True Priapus, White Moon, Interpolated Perigee) were in
      exactly that state, and a single regeneration would have removed them.

So the guard here is not "does the artwork look right" — an eye settles that —
but "is what ships still what the generator produces, is every symbol accounted
for, and do the facts about a symbol agree wherever they are written down".

That last one is why the rest of this file exists. A glyph's identity is spelled
out in four places — `scripts/glyph_catalog.py`, the templates, the published
gallery, and `settings/chart_defaults.py` — and every one of them has drifted at
least once: the gallery lost five symbols, East Point borrowed Ceres' colour, and
four of the lunar apsides drew themselves in one colour while writing their
degree in another.

These run offline: they compare the catalog against the templates, against the
library's own tables, and against each other. Only the drift test needs the
generator, which is skipped when the font cache is cold rather than reaching for
the network in CI.

Usage:
    pytest tests/core/test_glyph_system.py -v
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

from kerykeion.settings.chart_defaults import DEFAULT_CELESTIAL_POINTS_SETTINGS, KNOWN_GLYPH_NAMES

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "kerykeion" / "charts" / "templates"
TEMPLATE_FILES = ["chart.xml", "wheel_only.xml", "aspect_grid_only.xml", "modern_wheel.xml"]

BEGIN = "GLYPHS:BEGIN"
END = "GLYPHS:END"

SYMBOL_RE = re.compile(r'<symbol id="([^"]+)">(.*?)</symbol>', re.S)
WIDTH_RE = re.compile(r'stroke-width="([0-9.]+)"')
CHART_VAR_RE = re.compile(r"var\((--kerykeion-chart-color-[a-z0-9-]+)")


def _load(name: str):
    """Import a script by path — scripts/ is not an importable package."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _catalog():
    """The list of what ships. No fontTools, so it loads anywhere."""
    return _load("glyph_catalog")


def _load_builder():
    return _load("build_chart_glyphs")


def _block(template: str) -> str:
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    return text[text.index(BEGIN) : text.index(END)]


def _symbols(template: str) -> dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in SYMBOL_RE.finditer(_block(template))}


class TestEverySymbolIsDeclared:
    """A symbol the generator does not know about is a symbol it will delete."""

    def test_no_template_symbol_is_missing_from_the_catalog(self):
        declared = _catalog().IDS
        shipped = list(_symbols("modern_wheel.xml"))

        undeclared = [sid for sid in shipped if sid not in declared]
        assert not undeclared, (
            "these symbols ship but are not in glyph_catalog.py, so the next "
            f"build_chart_glyphs.py run deletes them: {undeclared}"
        )

    def test_the_catalog_declares_nothing_the_templates_lack(self):
        shipped = set(_symbols("modern_wheel.xml"))
        assert [sid for sid in _catalog().IDS if sid not in shipped] == []

    def test_every_template_carries_the_same_set_in_the_same_order(self):
        reference = list(_symbols(TEMPLATE_FILES[0]))
        for name in TEMPLATE_FILES[1:]:
            assert list(_symbols(name)) == reference, f"{name} diverged from {TEMPLATE_FILES[0]}"

    def test_the_shipped_order_is_the_catalog_order(self):
        """The gallery groups by walking the catalog; the templates print headings
        by walking it too. If the shipped order were free to differ, a symbol
        could sit under a heading that belongs to another family."""
        assert list(_symbols("modern_wheel.xml")) == _catalog().IDS


class TestTheBoxesAreNotRedundant:
    """A render class exists only where the renderers actually draw a size."""

    def test_no_two_classes_share_a_box(self):
        box = _catalog().BOX
        assert len(set(box.values())) == len(box), (
            f"two render classes claim the same box: {box}. A key that duplicates "
            "another's value promises a distinction no renderer makes — which is "
            "how 'planet' and 'point' both came to mean 24, and why Chiron had to "
            "be filed as a planet to get a size."
        )

    def test_every_family_maps_to_a_real_class(self):
        cat = _catalog()
        families = {family for _, family, _, _, _ in cat.SPEC}
        assert families <= set(cat.FAMILY_BOX), (
            f"families with no render class: {sorted(families - set(cat.FAMILY_BOX))}"
        )
        assert set(cat.FAMILY_BOX.values()) <= set(cat.BOX), (
            f"classes with no box: {sorted(set(cat.FAMILY_BOX.values()) - set(cat.BOX))}"
        )

    def test_no_family_is_declared_and_never_used(self):
        cat = _catalog()
        unused = set(cat.FAMILY_BOX) - {family for _, family, _, _, _ in cat.SPEC}
        assert not unused, f"FAMILY_BOX describes families nothing belongs to: {sorted(unused)}"


class TestHeadingsAreTheFamily:
    """The heading and the box come from the same field, so they cannot disagree."""

    def test_every_symbol_sits_under_the_heading_its_family_names(self):
        cat = _catalog()
        block = _block("modern_wheel.xml")
        family_of = dict((sid, family) for sid, family, _, _, _ in cat.SPEC)
        headings = {family for _, family, _, _, _ in cat.SPEC}

        current = None
        wrong = []
        for m in re.finditer(r"<!--\s+([^<>]+?)\s+-->|<symbol id=\"([^\"]+)\"", block):
            if m.group(1) in headings:
                current = m.group(1)
            elif m.group(2):
                if family_of[m.group(2)] != current:
                    wrong.append((m.group(2), family_of[m.group(2)], current))

        assert not wrong, (
            "these symbols are printed under a heading that is not their family: "
            f"{wrong}"
        )

    def test_each_family_is_contiguous(self):
        seen: list[str] = []
        for _, family, _, _, _ in _catalog().SPEC:
            if not seen or seen[-1] != family:
                seen.append(family)
        assert len(seen) == len(set(seen)), (
            f"a family is split across the list, so its heading would print twice: {seen}"
        )

    def test_every_symbol_carries_a_label(self):
        """`NAME.get(id, id)` is what let the gallery print bare ids for the five
        symbols it had no entry for. A label is a field now; empty is the only
        way left to lose one."""
        blank = [sid for sid, _, label, _, _ in _catalog().SPEC if not label.strip()]
        assert not blank, f"symbols with no label: {blank}"


class TestTheCatalogAndTheLibraryAgree:
    """`resolve_glyph_id` sends a point to a symbol; the symbol has to be there."""

    def test_every_known_glyph_name_ships_a_symbol(self):
        shipped = set(_symbols("modern_wheel.xml"))
        missing = sorted(KNOWN_GLYPH_NAMES - shipped)
        assert not missing, (
            "KNOWN_GLYPH_NAMES promises a dedicated symbol for these, but the "
            f"templates carry none — they would render as a blank <use>: {missing}"
        )

    def test_every_point_with_a_symbol_is_a_known_glyph_name(self):
        """The other direction. A point that ships a symbol but is not in
        KNOWN_GLYPH_NAMES falls back to the generic fixed-star glyph, so the
        artwork is drawn, shipped and never used."""
        settings_names = {entry["name"] for entry in DEFAULT_CELESTIAL_POINTS_SETTINGS}
        shipped = set(_symbols("modern_wheel.xml"))
        orphans = sorted((shipped & settings_names) - KNOWN_GLYPH_NAMES)
        assert not orphans, f"symbols that resolve_glyph_id will never ask for: {orphans}"


class TestTheColourIsDecidedOnce:
    """A point's glyph and its degree have to be the same colour."""

    def test_the_settings_colour_is_the_colour_the_symbol_paints_with(self):
        """Two places decide a point's colour, and only one of them reaches the
        glyph: the `var()` baked into the <symbol> paints the mark, while
        `DEFAULT_CELESTIAL_POINTS_SETTINGS["color"]` paints the degree text and
        the pointer line. They must agree, or one point is drawn in two colours.

        This is not hypothetical. East Point once borrowed Ceres' variable, and
        four of the lunar apsides drew themselves in their own method colour
        while writing their degree in the mean apogee's.
        """
        symbols = _symbols("modern_wheel.xml")
        mismatched = []
        checked = 0
        for entry in DEFAULT_CELESTIAL_POINTS_SETTINGS:
            body = symbols.get(entry["name"])
            if body is None:
                continue  # no dedicated symbol: falls back to the generic star
            used = sorted(set(CHART_VAR_RE.findall(body)))
            if len(used) != 1:
                continue  # a mark drawn in more than one colour states its own rule
            checked += 1
            if entry["color"] != f"var({used[0]})":
                mismatched.append((entry["name"], entry["color"], used[0]))

        assert checked > 40, f"only {checked} points compared — did the settings shape change?"
        assert not mismatched, (
            "these points draw their glyph in one colour and their degree in "
            f"another (name, settings, symbol): {mismatched}"
        )

    def test_every_colour_a_glyph_uses_is_defined_in_every_theme(self):
        """A theme that misses a variable does not fall back to a sensible
        colour — with no `var()` fallback it renders as nothing at all."""
        used = {
            var
            for body in _symbols("modern_wheel.xml").values()
            for var in CHART_VAR_RE.findall(body)
        }
        assert used, "no chart colour variables found — did the artwork stop using them?"

        gaps = {}
        for theme in sorted((ROOT / "kerykeion" / "charts" / "themes").glob("*.css")):
            defined = set(re.findall(r"(--kerykeion-chart-color-[a-z0-9-]+)\s*:", theme.read_text(encoding="utf-8")))
            if missing := sorted(used - defined):
                gaps[theme.name] = missing
        assert not gaps, f"themes missing colours their glyphs use: {gaps}"


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

    def test_every_font_source_is_credited_in_the_templates(self):
        """The header line ships inside every rendered chart, which is where an
        OFL attribution is actually read. Noto Sans was traced for the lettered
        marks and went uncredited there for six commits."""
        builder = _load_builder()
        credits = [credit for _url, _sha, credit in builder.FONT_SOURCES.values()]
        for name in TEMPLATE_FILES:
            header = (TEMPLATES / name).read_text(encoding="utf-8").split("\n", 1)[0]
            missing = [c for c in credits if c not in header]
            assert not missing, f"{name}'s header does not credit {missing}"


class TestOneWeightForEveryGlyph:
    """Stroke widths are derived from the box, never written as literals."""

    def test_only_the_derived_widths_appear_in_the_templates(self):
        builder = _load_builder()
        allowed = {f"{builder.stroke_for(box)}" for box in builder.BOX.values()}
        # One sanctioned exception: the Midpoint's rule joins its dots rather
        # than being a stroke of the mark, and at full weight it reads a third
        # the diameter of the dots it connects. Declared rather than left to
        # slip through — W_CONNECTOR currently equals stroke_for(12) by pure
        # arithmetic coincidence, so without naming it here the guard would
        # "pass" for the wrong reason and stop catching a second exception.
        allowed.add(f"{builder.W_CONNECTOR}")
        found = set(WIDTH_RE.findall(_block("modern_wheel.xml")))

        assert found <= allowed, (
            f"undeclared stroke widths in the templates: {sorted(found - allowed)}. "
            f"Widths must come from stroke_for(box), which yields {sorted(allowed)}. "
            "If a glyph needs another weight, name it here with the reason rather "
            "than writing the number into the artwork."
        )

    def test_the_connector_is_the_only_width_that_is_not_a_box_weight(self):
        builder = _load_builder()
        derived = {f"{builder.stroke_for(box)}" for box in builder.BOX.values()}
        # It may only appear in the Midpoint; anywhere else it is a leak.
        wearers = [
            sid
            for sid, body in _symbols("modern_wheel.xml").items()
            if f"{builder.W_CONNECTOR}" in WIDTH_RE.findall(body)
            and f"{builder.W_CONNECTOR}" not in derived - {f"{builder.W_CONNECTOR}"}
        ]
        assert wearers == ["Midpoint"], (
            f"the connector weight should be the Midpoint's alone, found on: {wearers}"
        )

    def test_the_derived_width_tracks_the_measured_silhouette_weight(self):
        builder = _load_builder()
        # The silhouettes' median stem is 7.41% of their ink, and outline() puts
        # that ink at 84% of the box. A change to either constant is a change to
        # how the whole set reads, so it should not pass unnoticed.
        assert builder.stroke_for(24) == pytest.approx(1.494, abs=0.001)
        assert builder.stroke_for(10) == pytest.approx(0.622, abs=0.001)
        assert builder.stroke_for(24) / builder.stroke_for(10) == pytest.approx(2.4, abs=0.01)
