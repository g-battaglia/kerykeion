#!/usr/bin/env python3
"""What the chart glyph set contains, in the order it ships.

The artwork lives in `build_chart_glyphs.py` and the poster in
`generate_glyph_gallery.py`; the *list* lives here, once, because it used to live
in both and had already drifted. The published gallery carried its own section
table and was missing five symbols — Interpolated Lilith, Mean/True Priapus,
White Moon, Interpolated Perigee — the same five that had gone undeclared in the
generator, so the documentation of the set described a set the library no longer
drew.

Deliberately free of third-party imports. `build_chart_glyphs.py` needs fontTools
to trace outlines; the docs path needs nothing but this list, and making the
poster depend on a font library to print a list of names is how the two ended up
apart in the first place.

Two facts per symbol, kept in separate fields:

  * `family` — what the thing *is*. Also the heading printed above it. Named
    from the library's own vocabulary (`schemas/literals.py`,
    `settings/chart_defaults.KNOWN_GLYPH_NAMES`) rather than invented here.
  * the render class its family maps to (`FAMILY_BOX`) — which coordinate box
    the renderers scale it in.

They were one field before, and that field could not express "same size,
different family": Chiron sat among the planets and Pholus among the points
purely so each would land in a box, while `BOX` carried two keys with the same
value promising a distinction no renderer makes. Ten families share the body box
now, and `FAMILY_BOX` says so in one place.

Every symbol the templates carry must appear here. The block between the
GLYPHS:BEGIN / GLYPHS:END markers is rewritten wholesale, so anything absent from
SPEC is not merely stale — it is deleted on the next build.
"""
from __future__ import annotations

# --------------------------------------------------------------- render classes
#: Coordinate box per render class, matching the `<use>` transforms in the
#: renderers. Four classes, four distinct sizes: a key here exists only when the
#: renderers actually draw that size differently.
BOX = {"body": 24, "sign": 32, "aspect": 10, "retro": 12}

# ------------------------------------------------------------------- families
PLANET = "Planets"
NODE = "Lunar nodes"
#: Neutral on purpose: it names the orbit, not a tradition. The ids keep their
#: conventional names (Lilith, Priapus), but the heading a reader meets first
#: should not pick a school for them.
APSIDE = "Lunar apsides"
CENTAUR = "Centaurs"
ASTEROID = "Asteroids"
TNO = "Trans-Neptunian objects"
URANIAN = "Uranian points"
LOT = "Arabic parts"
ANGLE = "Angles"
OTHER = "Axes and other points"
SIGN = "Signs"
ASPECT = "Aspects"
RETRO = "Retrograde"

#: Which box each family is drawn in. Most families are bodies on the wheel and
#: share one box; the three that do not are the three the renderers size apart.
FAMILY_BOX = {
    PLANET: "body",
    NODE: "body",
    APSIDE: "body",
    CENTAUR: "body",
    ASTEROID: "body",
    TNO: "body",
    URANIAN: "body",
    LOT: "body",
    ANGLE: "body",
    OTHER: "body",
    SIGN: "sign",
    ASPECT: "aspect",
    RETRO: "retro",
}

# ----------------------------------------------------------------------- spec
# (id, family, label, kind, payload)
#   kind "S" -> Symbola outline:   payload = (css_var_name, [codepoints])
#   kind "N" -> Noto Symbols 2:    payload = (css_var_name, [codepoints])
#   kind "L" -> Noto Sans letters: payload = (css_var_name, "As")
#   kind "C" -> clean-room:        payload = None; the artwork is CLEAN[id]
#
# The label is a field rather than a lookup table with a fallback. A
# `NAME.get(id, id)` reads as tolerant and is really just silent: it is what let
# the gallery print five symbols' bare ids for weeks without anyone noticing they
# were the five that had no entry.
SPEC = [
    ("Sun", PLANET, "Sun", "C", None),
    ("Moon", PLANET, "Moon", "S", ("moon", [0x263D])),
    ("Mercury", PLANET, "Mercury", "S", ("mercury", [0x263F])),
    ("Venus", PLANET, "Venus", "S", ("venus", [0x2640])),
    ("Mars", PLANET, "Mars", "S", ("mars", [0x2642])),
    ("Jupiter", PLANET, "Jupiter", "C", None),
    ("Saturn", PLANET, "Saturn", "S", ("saturn", [0x2644])),
    ("Uranus", PLANET, "Uranus", "C", None),
    ("Neptune", PLANET, "Neptune", "S", ("neptune", [0x2646])),
    ("Pluto", PLANET, "Pluto", "C", None),
    # Drawn, not traced: Symbola's U+260A/U+260B read as a blob at wheel sizes.
    ("Mean_North_Lunar_Node", NODE, "Mean North Node", "C", None),
    ("True_North_Lunar_Node", NODE, "True North Node", "C", None),
    ("Mean_South_Lunar_Node", NODE, "Mean South Node", "C", None),
    ("True_South_Lunar_Node", NODE, "True South Node", "C", None),
    # Six of these seven wear two shapes, not six: the glyph says which end of
    # the apsidal line a point is, the colour says which method computed it.
    # Unicode does offer U+2BDE for the true Black Moon, but it is a diamond on a
    # cross — adopting it would put a third shape on the apogee axis and break
    # the very rule that lets the family be read at a glance. White Moon is the
    # exception and keeps a mark of its own: it is not a third method of finding
    # the same point, it is a different point.
    ("Mean_Lilith", APSIDE, "Mean Lilith", "S", ("mean-lilith", [0x26B8])),
    ("True_Lilith", APSIDE, "True Lilith", "S", ("true-lilith", [0x26B8])),
    ("Interpolated_Lilith", APSIDE, "Interpolated Lilith", "S", ("interpolated-lilith", [0x26B8])),
    ("Mean_Priapus", APSIDE, "Mean Priapus", "C", None),
    ("True_Priapus", APSIDE, "True Priapus", "C", None),
    ("Interpolated_Perigee", APSIDE, "Interpolated Perigee", "C", None),
    ("White_Moon", APSIDE, "White Moon", "C", None),
    ("Chiron", CENTAUR, "Chiron", "C", None),
    ("Pholus", CENTAUR, "Pholus", "C", None),
    ("Ceres", ASTEROID, "Ceres", "S", ("ceres", [0x26B3])),
    ("Pallas", ASTEROID, "Pallas", "S", ("pallas", [0x26B4])),
    ("Juno", ASTEROID, "Juno", "S", ("juno", [0x26B5])),
    ("Vesta", ASTEROID, "Vesta", "S", ("vesta", [0x26B6])),
    ("Eris", TNO, "Eris", "C", None),
    ("Sedna", TNO, "Sedna", "N", ("sedna", [0x2BF2])),
    ("Haumea", TNO, "Haumea", "N", ("haumea", [0x1F77B])),
    ("Makemake", TNO, "Makemake", "N", ("makemake", [0x1F77C])),
    ("Ixion", TNO, "Ixion", "C", None),
    ("Orcus", TNO, "Orcus", "N", ("orcus", [0x1F77F])),
    ("Quaoar", TNO, "Quaoar", "N", ("quaoar", [0x1F77E])),
    ("Cupido", URANIAN, "Cupido", "N", ("cupido", [0x2BE0])),
    ("Hades", URANIAN, "Hades", "N", ("hades", [0x2BE1])),
    ("Zeus", URANIAN, "Zeus", "N", ("zeus", [0x2BE2])),
    ("Kronos", URANIAN, "Kronos", "N", ("kronos", [0x2BE3])),
    ("Apollon", URANIAN, "Apollon", "N", ("apollon", [0x2BE4])),
    ("Admetos", URANIAN, "Admetos", "N", ("admetos", [0x2BE5])),
    ("Vulkanus", URANIAN, "Vulkanus", "N", ("vulkanus", [0x2BE6])),
    ("Poseidon", URANIAN, "Poseidon", "N", ("poseidon", [0x2BE7])),
    ("Pars_Fortunae", LOT, "Pars Fortunae", "C", None),
    ("Pars_Spiritus", LOT, "Pars Spiritus", "C", None),
    ("Pars_Amoris", LOT, "Pars Amoris", "C", None),
    ("Pars_Fidei", LOT, "Pars Fidei", "C", None),
    ("Ascendant", ANGLE, "Ascendant", "L", ("first-house", "As")),
    ("Medium_Coeli", ANGLE, "Medium Coeli", "L", ("tenth-house", "Mc")),
    ("Descendant", ANGLE, "Descendant", "L", ("seventh-house", "Ds")),
    ("Imum_Coeli", ANGLE, "Imum Coeli", "L", ("fourth-house", "Ic")),
    ("Vertex", OTHER, "Vertex", "L", ("vertex", "Vx")),
    ("Anti_Vertex", OTHER, "Anti-Vertex", "L", ("anti-vertex", "Av")),
    ("East_Point", OTHER, "East Point", "C", None),
    ("Earth", OTHER, "Earth", "C", None),
    ("FixedStar", OTHER, "Fixed Star", "C", None),
    ("Midpoint", OTHER, "Midpoint", "C", None),
    ("Ari", SIGN, "Aries", "S", ("zodiac-icon-0", [0x2648])),
    ("Tau", SIGN, "Taurus", "S", ("zodiac-icon-1", [0x2649])),
    ("Gem", SIGN, "Gemini", "S", ("zodiac-icon-2", [0x264A])),
    ("Can", SIGN, "Cancer", "S", ("zodiac-icon-3", [0x264B])),
    ("Leo", SIGN, "Leo", "S", ("zodiac-icon-4", [0x264C])),
    ("Vir", SIGN, "Virgo", "S", ("zodiac-icon-5", [0x264D])),
    ("Lib", SIGN, "Libra", "S", ("zodiac-icon-6", [0x264E])),
    ("Sco", SIGN, "Scorpio", "S", ("zodiac-icon-7", [0x264F])),
    ("Sag", SIGN, "Sagittarius", "S", ("zodiac-icon-8", [0x2650])),
    ("Cap", SIGN, "Capricorn", "S", ("zodiac-icon-9", [0x2651])),
    ("Aqu", SIGN, "Aquarius", "S", ("zodiac-icon-10", [0x2652])),
    ("Pis", SIGN, "Pisces", "S", ("zodiac-icon-11", [0x2653])),
    ("orb0", ASPECT, "Conjunction", "C", None),
    ("orb30", ASPECT, "Semi-sextile", "C", None),
    ("orb45", ASPECT, "Semi-square", "C", None),
    ("orb60", ASPECT, "Sextile", "C", None),
    ("orb72", ASPECT, "Quintile", "C", None),
    ("orb90", ASPECT, "Square", "C", None),
    ("orb120", ASPECT, "Trine", "C", None),
    ("orb135", ASPECT, "Sesquiquadrate", "C", None),
    ("orb144", ASPECT, "Biquintile", "C", None),
    ("orb150", ASPECT, "Quincunx", "C", None),
    ("orb180", ASPECT, "Opposition", "C", None),
    ("retrograde", RETRO, "Retrograde", "S", ("paper-0", [0x211E])),
]

#: Ship order, for anything that only needs the names.
IDS = [entry[0] for entry in SPEC]


def box_of(family: str) -> int:
    """The coordinate box a family's symbols are drawn in."""
    return BOX[FAMILY_BOX[family]]


def families() -> list[tuple[str, list[tuple[str, str]]]]:
    """`[(family, [(id, label), ...]), ...]` in ship order.

    Families are contiguous in SPEC, so this is a fold rather than a sort — the
    poster and the template headings get the same grouping without either
    restating it.
    """
    grouped: list[tuple[str, list[tuple[str, str]]]] = []
    for sid, family, label, _kind, _payload in SPEC:
        if not grouped or grouped[-1][0] != family:
            grouped.append((family, []))
        grouped[-1][1].append((sid, label))
    return grouped
