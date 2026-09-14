# -*- coding: utf-8 -*-
"""
Fixed Star Catalog (v6)

Single source of truth for the fixed-star catalog used across kerykeion.
Wraps ``libephemeris.fixed_stars.list_fixed_stars()`` and exposes a
metadata model that downstream consumers (Astrologer API, frontend)
can rely on.

The Swiss Ephemeris ``sefstars.txt`` file is NOT used (licensing).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import ConfigDict, Field
from kerykeion.schemas.models import SubscriptableBaseModel


class FixedStarMetadataModel(SubscriptableBaseModel):
    """Metadata for a single fixed star entry from the catalog."""

    # Frozen: the catalog is lru_cache-backed and hands the SAME instances to
    # every caller, so mutable models would let one caller's edit poison the
    # cache process-wide. Immutable entries make the shared cache safe.
    model_config = ConfigDict(frozen=True)

    name: str = Field(description="IAU canonical name (e.g. 'Vindemiatrix', 'Deneb Algedi').")
    slug: str = Field(description="URL/identifier-safe slug (spaces → underscores).")
    hip_number: Optional[int] = Field(default=None, description="Hipparcos catalog number.")
    nomenclature: Optional[str] = Field(
        default=None,
        description="Bayer/Flamsteed nomenclature (e.g. 'alLeo', 'epVir').",
    )
    magnitude: Optional[float] = Field(default=None, description="Visual magnitude.")
    constellation: Optional[str] = Field(
        default=None,
        description="Full IAU constellation name (e.g. 'Eridanus'), derived from the nomenclature suffix.",
    )


# IAU three-letter constellation abbreviations → full names. The Bayer/
# Flamsteed nomenclature in the catalog always ends with this abbreviation
# ('alLeo' → Leo, 'epVir' → Virgo), so the constellation is factual catalog
# data derived once here — not something for clients to hardcode per star.
CONSTELLATION_NAMES: dict[str, str] = {
    "And": "Andromeda", "Ant": "Antlia", "Aps": "Apus", "Aqr": "Aquarius",
    "Aql": "Aquila", "Ara": "Ara", "Ari": "Aries", "Aur": "Auriga",
    "Boo": "Boötes", "Cae": "Caelum", "Cam": "Camelopardalis", "Cnc": "Cancer",
    "CVn": "Canes Venatici", "CMa": "Canis Major", "CMi": "Canis Minor",
    "Cap": "Capricornus", "Car": "Carina", "Cas": "Cassiopeia",
    "Cen": "Centaurus", "Cep": "Cepheus", "Cet": "Cetus", "Cha": "Chamaeleon",
    "Cir": "Circinus", "Col": "Columba", "Com": "Coma Berenices",
    "CrA": "Corona Australis", "CrB": "Corona Borealis", "Crv": "Corvus",
    "Crt": "Crater", "Cru": "Crux", "Cyg": "Cygnus", "Del": "Delphinus",
    "Dor": "Dorado", "Dra": "Draco", "Equ": "Equuleus", "Eri": "Eridanus",
    "For": "Fornax", "Gem": "Gemini", "Gru": "Grus", "Her": "Hercules",
    "Hor": "Horologium", "Hya": "Hydra", "Hyi": "Hydrus", "Ind": "Indus",
    "Lac": "Lacerta", "Leo": "Leo", "LMi": "Leo Minor", "Lep": "Lepus",
    "Lib": "Libra", "Lup": "Lupus", "Lyn": "Lynx", "Lyr": "Lyra",
    "Men": "Mensa", "Mic": "Microscopium", "Mon": "Monoceros", "Mus": "Musca",
    "Nor": "Norma", "Oct": "Octans", "Oph": "Ophiuchus", "Ori": "Orion",
    "Pav": "Pavo", "Peg": "Pegasus", "Per": "Perseus", "Phe": "Phoenix",
    "Pic": "Pictor", "Psc": "Pisces", "PsA": "Piscis Austrinus",
    "Pup": "Puppis", "Pyx": "Pyxis", "Ret": "Reticulum", "Sge": "Sagitta",
    "Sgr": "Sagittarius", "Sco": "Scorpius", "Scl": "Sculptor",
    "Sct": "Scutum", "Ser": "Serpens", "Sex": "Sextans", "Tau": "Taurus",
    "Tel": "Telescopium", "Tri": "Triangulum", "TrA": "Triangulum Australe",
    "Tuc": "Tucana", "UMa": "Ursa Major", "UMi": "Ursa Minor", "Vel": "Vela",
    "Vir": "Virgo", "Vol": "Volans", "Vul": "Vulpecula",
}

_CONSTELLATION_NAMES_LOWER = {abbr.lower(): name for abbr, name in CONSTELLATION_NAMES.items()}


def _constellation_from_nomenclature(nomenclature: Optional[str]) -> Optional[str]:
    """Full constellation name from a Bayer/Flamsteed designation, or ``None``.

    Handles multiple-star component suffixes too ('th01OriA' → Orion). Some
    catalog entries carry no real designation (the nomenclature just echoes
    the proper name, e.g. 'Bharani'): those legitimately resolve to ``None``.
    """
    if not nomenclature or len(nomenclature) < 4:
        return None
    candidates = [nomenclature[-3:]]
    # A trailing component letter (A/B/C…) shifts the abbreviation left by one.
    if nomenclature[-1].isupper() and len(nomenclature) >= 5:
        candidates.append(nomenclature[-4:-1])
    for suffix in candidates:
        match = CONSTELLATION_NAMES.get(suffix) or _CONSTELLATION_NAMES_LOWER.get(suffix.lower())
        if match:
            return match
    return None


def _to_slug(name: str) -> str:
    return name.strip().replace(" ", "_").replace("-", "_")


def star_slug(name: str) -> str:
    """Public canonical slug for a fixed-star name (strip, spaces/hyphens → underscores).

    Case is preserved (catalog slugs are cased); lowercase the result for
    case-insensitive table lookups.
    """
    return _to_slug(name)


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[FixedStarMetadataModel, ...]:
    """Load and cache the libephemeris catalog as metadata tuples."""
    from libephemeris.fixed_stars import list_fixed_stars

    entries = list_fixed_stars()
    return tuple(
        FixedStarMetadataModel(
            name=e.name,
            slug=_to_slug(e.name),
            hip_number=getattr(e, "hip_number", None),
            nomenclature=getattr(e, "nomenclature", None),
            magnitude=getattr(e, "magnitude", None),
            constellation=_constellation_from_nomenclature(getattr(e, "nomenclature", None)),
        )
        for e in entries
    )


class FixedStarCatalog:
    """Read-only accessor over the libephemeris fixed-star catalog."""

    @staticmethod
    def list_all() -> list[FixedStarMetadataModel]:
        """Return the full catalog as a list (a fresh shallow copy each call)."""
        return list(_load_catalog())

    @staticmethod
    def count() -> int:
        """Return the number of stars in the catalog."""
        return len(_load_catalog())

    @staticmethod
    def find(name: str) -> Optional[FixedStarMetadataModel]:
        """Look up by IAU name or slug, case-insensitive, ``-``/``_``/space-insensitive."""
        target = _to_slug(name).lower()
        for entry in _load_catalog():
            if entry.slug.lower() == target or entry.name.lower() == name.lower():
                return entry
        return None

    @staticmethod
    @lru_cache(maxsize=1)
    def _lookup_sets() -> tuple[frozenset[str], frozenset[str]]:
        """Cached lowercased (slug, name) membership sets for O(1) lookups."""
        catalog = _load_catalog()
        return (
            frozenset(e.slug.lower() for e in catalog),
            frozenset(e.name.lower() for e in catalog),
        )

    @staticmethod
    def is_known_name(name: str) -> bool:
        """True iff ``find(name)`` would resolve — O(1), used for hot-path detection."""
        slugs_lower, names_lower = FixedStarCatalog._lookup_sets()
        return _to_slug(name).lower() in slugs_lower or str(name).lower() in names_lower

    @staticmethod
    def known_slugs() -> frozenset[str]:
        """Return all slug identifiers available in the catalog."""
        return frozenset(entry.slug for entry in _load_catalog())

