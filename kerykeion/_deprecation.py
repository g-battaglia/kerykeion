# -*- coding: utf-8 -*-
"""
Internal helper for deprecated import aliases (PEP 562 module ``__getattr__``).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import warnings
from typing import Any, Callable, Dict


def deprecated_alias_getattr(module_name: str, aliases: Dict[str, Any]) -> Callable[[str], Any]:
    """Build a module-level ``__getattr__`` resolving renamed-class aliases.

    Old names keep working (``from <module> import OldName`` returns the very
    same class object, so ``isinstance`` checks are unaffected) but emit a
    ``DeprecationWarning`` pointing at the replacement.

    TODO remove together with all alias dicts in 6.0.0 stable.
    """

    def __getattr__(name: str) -> Any:
        if name in aliases:
            replacement = aliases[name]
            warnings.warn(
                f"'{module_name}.{name}' is deprecated, use '{replacement.__name__}' instead. "
                "This alias will be removed in kerykeion 6.0.0 stable.",
                DeprecationWarning,
                stacklevel=2,
            )
            return replacement
        raise AttributeError(f"module {module_name!r} has no attribute {name!r}")

    return __getattr__
