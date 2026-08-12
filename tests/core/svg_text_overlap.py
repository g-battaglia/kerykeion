# -*- coding: utf-8 -*-
"""Find text that overlaps other text in a rendered chart.

The panels and tables are laid out with hardcoded column offsets against
hand-chosen font sizes, and nothing checked that the two agreed. What that
bought was a chart where "N. Node (M)" and "N. Node (T)" printed on top of each
other in adjacent columns, shipped and unnoticed, because no test looks at
where text lands and a passing suite says nothing about it.

This reads the finished SVG and asks the only question that matters: do two
strings on the same baseline occupy the same pixels.

Scope, and why it is not the whole file: text inside a rotated group is
positioned by its rotation, so comparing x ranges in a flat frame would report
overlaps that do not exist and miss ones that do. Every rotated subtree is
therefore skipped, which excludes the wheel's own labels — those are governed
by the separation model in :mod:`kerykeion.charts.draw_modern`, measured in a
browser, and are not what this is for. What remains is exactly where the
defects were: the title, the info panel, and every grid and table.

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from html import unescape
from typing import Iterator

from kerykeion.charts.glyph_metrics import estimate_text_width

#: Tag stream: an opening group, a closing group, or a text node with its body.
_TOKEN = re.compile(r"<g\b([^>]*)>|</g>|<text\b([^>]*)>([^<]*)</text>")
#: ``translate(x)`` is legal SVG with y defaulting to 0, and the minifier emits
#: exactly that. Requiring both arguments silently dropped the offset and put
#: every grid row back at the origin, on top of the left-hand panel.
_TRANSLATE = re.compile(r"translate\(\s*([-\d.]+)(?:[ ,]\s*([-\d.]+))?\s*\)")
_ROTATE = re.compile(r"\brotate\(")
_FONT_SIZE = re.compile(r"font-size:\s*([\d.]+)|font-size=['\"]([\d.]+)")
_X = re.compile(r"\bx=['\"]([-\d.]+)")
_Y = re.compile(r"\by=['\"]([-\d.]+)")

#: Two strings whose ink comes within this many px are treated as touching.
#: Not zero: the width table is an upper bound per character, so a hair of
#: overlap between two estimates is noise rather than a defect.
TOUCH_TOLERANCE = 0.5


@dataclass(frozen=True)
class Overlap:
    """Two strings sharing a baseline and some pixels."""

    y: float
    left: str
    right: str
    amount: float

    def __str__(self) -> str:
        return f"y={self.y:.0f}: {self.left!r} runs {self.amount:.1f}px into {self.right!r}"


#: ``<defs>`` holds glyph definitions, not drawings. The four angle symbols each
#: carry a text node at y=20 in there, so scanning them reports "As" landing on
#: "Ds" — two labels that are never on the page together at all, let alone at
#: the same point.
_DEFS = re.compile(r"<defs\b.*?</defs>", re.DOTALL)


def _placed_text(svg: str) -> Iterator[tuple[float, float, float, str]]:
    """Yield ``(y, x0, x1, text)`` for every text node in an unrotated frame."""
    svg = _DEFS.sub("", svg)
    # Each entry is (dx, dy, rotated) accumulated from the root.
    stack: list[tuple[float, float, bool]] = [(0.0, 0.0, False)]

    for token in _TOKEN.finditer(svg):
        opening, text_attrs, body = token.group(1), token.group(2), token.group(3)

        if opening is not None:
            move = _TRANSLATE.search(opening)
            dx = float(move.group(1)) if move else 0.0
            dy = float(move.group(2)) if move and move.group(2) else 0.0
            parent_x, parent_y, parent_rotated = stack[-1]
            # A group with no transform still nests, so it must still be pushed:
            # popping it on </g> otherwise unwinds one level too far and every
            # coordinate after it is measured from the wrong origin.
            stack.append((parent_x + dx, parent_y + dy, parent_rotated or bool(_ROTATE.search(opening))))
            continue

        if text_attrs is None:
            if len(stack) > 1:
                stack.pop()
            continue

        content = unescape(body)
        if not content.strip():
            continue
        origin_x, origin_y, rotated = stack[-1]
        if rotated or _ROTATE.search(text_attrs):
            continue

        size_match = _FONT_SIZE.search(text_attrs)
        size = float(size_match.group(1) or size_match.group(2)) if size_match else 10.0
        local_x = float(_X.search(text_attrs).group(1)) if _X.search(text_attrs) else 0.0
        local_y = float(_Y.search(text_attrs).group(1)) if _Y.search(text_attrs) else 0.0

        width = estimate_text_width(content, size)
        start = origin_x + local_x - (width if "text-anchor='end'" in text_attrs or 'text-anchor="end"' in text_attrs else 0.0)
        yield round(origin_y + local_y, 2), start, start + width, content


def find_text_overlaps(svg: str) -> list[Overlap]:
    """Every pair of strings that share a baseline and some pixels, worst first."""
    rows: dict[float, list[tuple[float, float, str]]] = defaultdict(list)
    for y, x0, x1, text in _placed_text(svg):
        rows[y].append((x0, x1, text))

    overlaps: list[Overlap] = []
    for y, placed in rows.items():
        placed.sort()
        for (left_start, left_end, left), (right_start, right_end, right) in zip(placed, placed[1:]):
            if right_start < left_end - TOUCH_TOLERANCE:
                overlaps.append(Overlap(y, left, right, left_end - right_start))
    return sorted(overlaps, key=lambda o: -o.amount)
