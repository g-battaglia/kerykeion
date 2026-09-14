"""Regenerate the two glyph-width tables the chart info panel's row guard uses.

There are two, deliberately:

- ``_MEASURED_EM`` in ``kerykeion/charts/glyph_metrics.py`` — the widths
  :func:`~kerykeion.charts.glyph_metrics.estimate_text_width` charges, rounded
  **up** to 1/50 em so the estimate never reads narrower than the text renders.
  Bucketed by width to keep the literal readable.
- ``tests/data/glyph_advances.json`` — the same measurements *unrounded*, and
  over a wider range of scripts, so the row-width test can check the rendered
  rows against real type metrics instead of against the estimator that sized
  them. An assertion phrased in the estimator's own terms is satisfied by
  construction; that is how a previous version stayed green while seven rows
  overran the wheel.

Both come from the same three fonts, taking the widest advance each character
has across them. The panel's text nodes name no font-family, so the real glyphs
are the viewer's choice; these three are a reference set, not a promise.

The fonts are macOS system copies, so this script only runs there. Its outputs
are committed, so nothing else needs it — run it if the reference set changes or
a script is added to the covered ranges.

Usage::

    poe regenerate:glyph-widths
"""

from __future__ import annotations

import collections
import json
import math
import sys
import unicodedata
from pathlib import Path

from fontTools.ttLib import TTCollection, TTFont

ROOT = Path(__file__).resolve().parents[1]

#: (path, index-within-collection). A serif, a grotesque, and a pan-Unicode face.
REFERENCE_FONTS: list[tuple[str, int | None]] = [
    ("/System/Library/Fonts/Times.ttc", 0),
    ("/System/Library/Fonts/Helvetica.ttc", 0),
    ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", None),
]

#: What the estimator carries in source: the scripts the shipped translations and
#: the overwhelming majority of names are written in. Devanagari is here because
#: Hindi is a shipped chart language: under the block ceiling its mark-heavy rows
#: read more than twice their rendered width, and the row trims that share this
#: estimator amputated text that actually fit.
ESTIMATOR_RANGES = [(0x20, 0x7E), (0xA0, 0x24F), (0x370, 0x3FF), (0x400, 0x4FF), (0x900, 0x97F), (0x2010, 0x2027)]

#: What the test fixture carries: the above plus every script the estimator has
#: no measurements for, so the test can measure them rather than assume.
FIXTURE_RANGES = ESTIMATOR_RANGES + [
    (0x300, 0x36F),  # combining diacritics
    (0x590, 0x6FF),  # Hebrew, Arabic
    (0x900, 0x97F),  # Devanagari
    (0xE00, 0xE7F),  # Thai
    (0x3000, 0x30FF),  # CJK punctuation, kana
    (0x4E00, 0x4FFF),  # CJK ideographs (sample)
    (0xAC00, 0xACFF),  # Hangul syllables (sample)
    (0xFF00, 0xFF60),  # fullwidth forms
]

#: Excluded from the *test fixture* because the row-width test treats them as
#: what shaping makes them — zero advance: a matra stacks on the letter before
#: it, a zero-width joiner fuses two code points into one glyph.
#:
#: The *estimator* table no longer excludes them. It used to, which sent every
#: combining mark to the block ceiling; on Devanagari that charged each matra
#: and virama a full 1.04 em, read mark-heavy Hindi rows at over twice their
#: rendered width, and made the row trims amputate text that fit with a third
#: of the slot to spare. What the fonts' hmtx tables declare for a mark is a
#: measurement like any other — most are zero, the soft hyphen is its real
#: 0.34 em — and never an underestimate of what shaping renders, which only
#: fuses and stacks, never widens. Controls stay out of both tables.
FIXTURE_SKIP_CATEGORIES = frozenset({"Mn", "Me", "Cf", "Cc"})
ESTIMATOR_SKIP_CATEGORIES = frozenset({"Cc"})


def _load_fonts() -> list[tuple[int, dict, dict]]:
    loaded = []
    for path, index in REFERENCE_FONTS:
        if not Path(path).exists():
            sys.exit(f"{path} not found — this script needs the macOS system fonts.")
        font = TTCollection(path).fonts[index] if index is not None else TTFont(path)
        loaded.append((font["head"].unitsPerEm, font.getBestCmap(), font["hmtx"].metrics))
    return loaded


def _widest_advances(
    fonts: list[tuple[int, dict, dict]], ranges: list[tuple[int, int]], skip: frozenset[str]
) -> dict[int, float]:
    """The widest advance each code point in *ranges* has across *fonts*, in em.

    Characters whose Unicode category is in *skip* are left out — the two
    tables skip different sets, which is the reason this is a parameter.
    """
    advances: dict[int, float] = {}
    for low, high in ranges:
        for code_point in range(low, high + 1):
            if unicodedata.category(chr(code_point)) in skip:
                continue
            widths = [hmtx[cmap[code_point]][0] / upem for upem, cmap, hmtx in fonts if cmap.get(code_point)]
            if widths:
                advances[code_point] = max(widths)
    return advances


def main() -> None:
    """Print the estimator table to paste and write the test fixture in place."""
    fonts = _load_fonts()

    estimator = _widest_advances(fonts, ESTIMATOR_RANGES, ESTIMATOR_SKIP_CATEGORIES)
    buckets: dict[float, list[str]] = collections.defaultdict(list)
    for code_point, width in estimator.items():
        buckets[math.ceil(width * 50) / 50].append(chr(code_point))
    lines = [f"    {width:.2f}: {''.join(sorted(chars))!r}," for width, chars in sorted(buckets.items())]
    print(f"_MEASURED_EM: {len(estimator)} characters in {len(buckets)} buckets — paste into glyph_metrics.py:\n")
    print("_MEASURED_EM: dict[float, str] = {\n" + "\n".join(lines) + "\n}")

    fixture = _widest_advances(fonts, FIXTURE_RANGES, FIXTURE_SKIP_CATEGORIES)
    target = ROOT / "tests" / "data" / "glyph_advances.json"
    target.write_text(
        json.dumps(
            {
                "_comment": (
                    "Widest advance width, in em, of each character across Times, Helvetica and "
                    "Arial Unicode (macOS system copies), read from their hmtx tables. Committed so "
                    "the info panel's width guard can be checked against real type metrics on any "
                    "platform, and so that check stays independent of the rounded table the estimator "
                    "itself uses. Regenerate with poe regenerate:glyph-widths."
                ),
                "advances": {f"{cp:04X}": round(w, 6) for cp, w in sorted(fixture.items())},
            },
            ensure_ascii=False,
            indent=0,
        )
    )
    print(f"\nWrote {len(fixture)} advances to {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
