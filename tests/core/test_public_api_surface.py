# -*- coding: utf-8 -*-
"""
Public API surface invariants (v6 export-parity policy).

Locks the rules agreed for 6.0.0b1:

1. ``kerykeion.schemas`` is the canonical one-stop home: every public
   Pydantic model defined anywhere in the package is importable from it
   (same class object, not a copy).
2. Feature subpackages export the models defined inside them.
3. Any model appearing in the return annotation of a public callable of a
   top-level export is itself a top-level export.
4. ``typing.get_type_hints`` resolves on every public model class — the
   Astrologer API (FastAPI) relies on runtime introspection of these models.
5. Public model names end in ``Model``.
6. Names renamed in 6.0.0b1 stay importable as deprecated aliases that
   warn and resolve to the new class.
"""

import importlib
import inspect
import pkgutil
import typing
import warnings

import pydantic
import pytest

import kerykeion
import kerykeion.schemas as schemas

# Modules that must not be imported by the discovery walk.
# __main__ modules run a CLI when executed; the walk must not trigger them.
_EXCLUDED_MODULES = ("__main__",)


def _collect_public_models() -> dict[str, type]:
    """Map name -> class for every public BaseModel defined in the package."""
    models: dict[str, type] = {}
    for module_info in pkgutil.walk_packages(kerykeion.__path__, "kerykeion."):
        if any(excluded in module_info.name for excluded in _EXCLUDED_MODULES):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            module = importlib.import_module(module_info.name)
        for name, obj in vars(module).items():
            if (
                inspect.isclass(obj)
                and issubclass(obj, pydantic.BaseModel)
                and obj.__module__ == module_info.name
                and not name.startswith("_")
            ):
                models[name] = obj
    return models


PUBLIC_MODELS = _collect_public_models()

# Pre-6.0.0b1 aliases removed in 6.0.0 stable (as their DeprecationWarning
# promised): old name -> (import surface, new name).
REMOVED_PRE_B1_ALIASES = {
    "ProgressedToNatalAspect": ("kerykeion", "ProgressedToNatalAspectModel"),
    "SecondaryProgressionsResult": ("kerykeion", "SecondaryProgressionsResultModel"),
    "SolarArcDirectedAspect": ("kerykeion", "SolarArcDirectedAspectModel"),
    "SolarArcDirectedPoint": ("kerykeion", "SolarArcDirectedPointModel"),
    "ACGLine": ("kerykeion.astro_cartography.acg_factory", "ACGLineModel"),
    "ACGLinePoint": ("kerykeion.astro_cartography.acg_factory", "ACGLinePointModel"),
    "SpeculumEntry": ("kerykeion.primary_directions.directions_factory", "SpeculumEntryModel"),
    "FixedStarMetadata": ("kerykeion.fixed_stars", "FixedStarMetadataModel"),
}


def test_every_public_model_is_importable_from_schemas():
    """Rule 1 — kerykeion.schemas re-exports every public model, by identity."""
    missing = sorted(name for name in PUBLIC_MODELS if name not in schemas.__all__)
    assert not missing, f"models missing from kerykeion.schemas.__all__: {missing}"

    mismatched = sorted(
        name for name, cls in PUBLIC_MODELS.items() if getattr(schemas, name, None) is not cls
    )
    assert not mismatched, f"schemas attribute is not the defining class for: {mismatched}"


def test_schemas_all_resolves_completely():
    """Every name in schemas.__all__ (eager or lazy) resolves to an object."""
    unresolved = [name for name in schemas.__all__ if getattr(schemas, name, None) is None]
    assert not unresolved, f"schemas.__all__ names that do not resolve: {unresolved}"


def test_feature_subpackages_export_their_own_models():
    """Rule 2 — a model defined under kerykeion.<feature>.* is exported there."""
    problems = []
    for name, cls in PUBLIC_MODELS.items():
        parts = cls.__module__.split(".")
        if len(parts) < 3 or parts[1] == "schemas":
            continue  # top-level module or the schemas package itself
        subpackage = importlib.import_module(".".join(parts[:2]))
        exported = name in getattr(subpackage, "__all__", ()) and getattr(subpackage, name, None) is cls
        if not exported:
            problems.append(f"{name} (defined in {cls.__module__}, not exported by {subpackage.__name__})")
    assert not problems, f"feature models not exported by their subpackage: {problems}"


def _models_in_annotation(annotation, found: set) -> None:
    if (
        inspect.isclass(annotation)
        and issubclass(annotation, pydantic.BaseModel)
        and annotation.__module__.startswith("kerykeion")
    ):
        found.add(annotation.__name__)
    for arg in typing.get_args(annotation):
        _models_in_annotation(arg, found)


def test_factory_return_models_are_top_level_exports():
    """Rule 3 — models returned by public callables of top-level exports."""
    referenced: set = set()
    for export_name in kerykeion.__all__:
        exported = getattr(kerykeion, export_name)
        if not inspect.isclass(exported):
            continue
        for member_name, member in inspect.getmembers(exported):
            if member_name.startswith("_") or not callable(member):
                continue
            function = inspect.unwrap(getattr(member, "__func__", member))
            try:
                hints = typing.get_type_hints(function)
            except (NameError, TypeError):
                # Unresolved forward ref / un-hintable callable: skip this member
                # but let any other (unexpected) error surface as a real failure
                # rather than silently hiding an API regression.
                continue
            if "return" in hints:
                _models_in_annotation(hints["return"], referenced)

    missing = sorted(referenced - set(kerykeion.__all__))
    assert not missing, f"factory-returned models missing from kerykeion.__all__: {missing}"


def test_get_type_hints_resolves_on_every_public_model():
    """Rule 4 — runtime introspection (FastAPI) must never break."""
    failures = []
    for name, cls in sorted(PUBLIC_MODELS.items()):
        try:
            typing.get_type_hints(cls)
        except Exception as error:  # noqa: BLE001 — report all failures at once
            failures.append(f"{name}: {type(error).__name__}: {error}")
    assert not failures, f"get_type_hints failures: {failures}"


def test_get_type_hints_resolves_on_every_public_callable():
    """Rule 4, extended to CALLABLES — a FastAPI app introspects factory methods,
    not just models, and ``test_factory_return_models_are_top_level_exports``
    deliberately swallows NameError, so a broken forward ref on a public method's
    signature would slip past every other test here.

    Scoped to kerykeion-owned callables: pydantic's own inherited deprecated
    methods (``copy``/``parse_file``/``parse_raw``/``model_rebuild``) reference
    names like ``AbstractSetIntStr`` that only resolve inside pydantic and are
    not our contract.
    """
    failures = []
    for export_name in sorted(kerykeion.__all__):
        exported = getattr(kerykeion, export_name)
        if not inspect.isclass(exported):
            continue
        for member_name, member in inspect.getmembers(exported, callable):
            if member_name.startswith("_"):
                continue
            function = inspect.unwrap(getattr(member, "__func__", member))
            if not getattr(function, "__module__", "").startswith("kerykeion"):
                continue
            try:
                typing.get_type_hints(function)
            except Exception as error:  # noqa: BLE001 — collect all at once
                failures.append(f"{export_name}.{member_name}: {type(error).__name__}: {error}")
    assert not failures, f"get_type_hints failures on public callables: {failures}"


def test_public_model_names_end_with_model_suffix():
    """Rule 5 — naming convention (ActiveAspect is a TypedDict, not collected)."""
    offenders = sorted(name for name in PUBLIC_MODELS if not name.endswith("Model"))
    assert not offenders, f"public models without the *Model suffix: {offenders}"


def test_top_level_all_attributes_exist():
    missing = [name for name in kerykeion.__all__ if not hasattr(kerykeion, name)]
    assert not missing, f"kerykeion.__all__ names without an attribute: {missing}"


@pytest.mark.parametrize("old_name", sorted(REMOVED_PRE_B1_ALIASES))
def test_removed_pre_b1_aliases_raise(old_name):
    """Rule 6 — pre-b1 alias names are gone in 6.0.0 stable: plain
    AttributeError (or the v5 ImportError path for kerykeion itself),
    while the new *Model name still resolves."""
    surface, new_name = REMOVED_PRE_B1_ALIASES[old_name]
    module = importlib.import_module(surface)
    with pytest.raises((AttributeError, ImportError)):
        getattr(module, old_name)
    assert getattr(module, new_name) is PUBLIC_MODELS[new_name]
    assert old_name not in getattr(module, "__all__", ())


def test_relationship_and_ephemeris_models_top_level_exported():
    """Round-4: result models of exported factories must be importable from the
    top-level namespace, like every other factory's result model."""
    import kerykeion
    from kerykeion import RelationshipScoreModel, EphemerisDictModel  # noqa: F401
    assert "RelationshipScoreModel" in kerykeion.__all__
    assert "EphemerisDictModel" in kerykeion.__all__
