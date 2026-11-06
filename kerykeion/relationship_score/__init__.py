# -*- coding: utf-8 -*-
"""
Relationship Score

Ciro Discepolo's Cosmic Synastry scoring: weighted aspect and placement
counts between two subjects, with a per-item breakdown.

The main entry point is:
    - RelationshipScoreFactory
"""

from importlib import import_module
from typing import TYPE_CHECKING

from .factory import RelationshipScoreFactory

_V2_MODELS = ("RelationshipScoreV2Model", "ScoreContactV2Model", "ScoreMetadataV2Model")

if TYPE_CHECKING:
    from .v2.models import RelationshipScoreV2Model, ScoreContactV2Model, ScoreMetadataV2Model


def __getattr__(name: str):
    """Resolve an advertised score export only when it is first requested."""
    if name in _V2_MODELS:
        value = getattr(import_module(".v2.models", __name__), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    """List the advertised score exports without eagerly importing their modules."""
    return sorted(set(globals()) | set(_V2_MODELS))


__all__ = ["RelationshipScoreFactory", "RelationshipScoreV2Model", "ScoreContactV2Model", "ScoreMetadataV2Model"]
