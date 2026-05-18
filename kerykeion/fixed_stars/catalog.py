# -*- coding: utf-8 -*-
"""
Fixed Star Catalog (v7)

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

from pydantic import BaseModel, Field


class FixedStarMetadata(BaseModel):
    """Metadata for a single fixed star entry from the catalog."""

    name: str = Field(description="IAU canonical name (e.g. 'Vindemiatrix', 'Deneb Algedi').")
    slug: str = Field(description="URL/identifier-safe slug (spaces → underscores).")
    hip_number: Optional[int] = Field(default=None, description="Hipparcos catalog number.")
    nomenclature: Optional[str] = Field(
        default=None,
        description="Bayer/Flamsteed nomenclature (e.g. 'alLeo', 'epVir').",
    )
    magnitude: Optional[float] = Field(default=None, description="Visual magnitude.")


def _to_slug(name: str) -> str:
    return name.strip().replace(" ", "_").replace("-", "_")


@lru_cache(maxsize=1)
def _load_catalog() -> tuple[FixedStarMetadata, ...]:
    """Load and cache the libephemeris catalog as metadata tuples."""
    from libephemeris.fixed_stars import list_fixed_stars

    entries = list_fixed_stars()
    return tuple(
        FixedStarMetadata(
            name=e.name,
            slug=_to_slug(e.name),
            hip_number=getattr(e, "hip_number", None),
            nomenclature=getattr(e, "nomenclature", None),
            magnitude=getattr(e, "magnitude", None),
        )
        for e in entries
    )


class FixedStarCatalog:
    """Read-only accessor over the libephemeris fixed-star catalog."""

    @staticmethod
    def list_all() -> list[FixedStarMetadata]:
        """Return the full catalog as a list (a fresh shallow copy each call)."""
        return list(_load_catalog())

    @staticmethod
    def count() -> int:
        """Return the number of stars in the catalog."""
        return len(_load_catalog())

    @staticmethod
    def find(name: str) -> Optional[FixedStarMetadata]:
        """Look up by IAU name or slug, case-insensitive, ``-``/``_``/space-insensitive."""
        target = _to_slug(name).lower()
        for entry in _load_catalog():
            if entry.slug.lower() == target or entry.name.lower() == name.lower():
                return entry
        return None

    @staticmethod
    def known_slugs() -> frozenset[str]:
        """Return all slug identifiers available in the catalog."""
        return frozenset(entry.slug for entry in _load_catalog())
