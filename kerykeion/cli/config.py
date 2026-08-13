# -*- coding: utf-8 -*-
"""User configuration and profile storage paths (XDG).

Profiles contain birth data — personally identifying information — so the store
directory is created 0700 and each profile file is written 0600. Nothing here
imports kerykeion; it is pure path logic and safe at module import time.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_DIR_NAME = "kerykeion"
PROFILES_SUBDIR = "subjects"
CONFIG_FILENAME = "config.json"

# Default to offline for any subject that resolves a full coordinate + timezone:
# the CLI is for batch/scripted use, and silently calling the GeoNames API from
# a pipeline is the wrong default. ``--online`` opts back in.
DEFAULT_ONLINE = False


def _base_config_dir() -> Path:
    """The XDG config root for this app ($XDG_CONFIG_HOME or ~/.config)."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / APP_DIR_NAME
    return Path.home() / ".config" / APP_DIR_NAME


def app_dir() -> Path:
    """The application config directory path (not created here).

    Pure path accessor — callers that need the directory to exist on disk use
    :func:`ensure_profile_store` (the write path). Keeping this side-effect-free
    means a read-only lookup (e.g. resolving ``-s`` for a missing profile) does
    not silently create ``~/.config/kerykeion`` or mask a read-only HOME with a
    misleading "invalid input" error.
    """
    return _base_config_dir()


def profiles_dir() -> Path:
    """The profiles store path (not created here; use :func:`ensure_profile_store`)."""
    return app_dir() / PROFILES_SUBDIR


def ensure_profile_store() -> Path:
    """Create the 0700 profile store dirs if missing; return ``profiles_dir()``.

    The store holds birth data (PII), so both the app dir and the subjects
    subdir are created ``0700``. Called from the write path (``profiles.save``),
    never from a read/lookup.
    """
    app = app_dir()
    store = app / PROFILES_SUBDIR
    for d in (app, store):
        d.mkdir(parents=True, exist_ok=True)
        try:
            d.chmod(0o700)
        except OSError:
            # Non-POSIX filesystems (Windows) ignore the mode; the directory
            # still exists. The restriction is best-effort on those platforms.
            pass
    return store


def config_file() -> Path:
    """The optional global config.json path (not auto-created)."""
    return app_dir() / CONFIG_FILENAME


def profile_path(name: str) -> Path:
    """The on-disk path for a profile by name.

    The name is restricted to a safe charset so it cannot escape the store via
    ``..`` or absolute paths, and the suffix is forced to ``.json``.
    """
    safe = _safe_profile_name(name)
    return profiles_dir() / f"{safe}.json"


def _safe_profile_name(name: str) -> str:
    import re

    if not name:
        raise ValueError("profile name must not be empty")
    # Allow letters, digits, dash, underscore, dot, space; collapse the rest.
    cleaned = re.sub(r"[^A-Za-z0-9_.\- ]+", "_", name).strip(" .")
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError(f"profile name {name!r} has no usable characters")
    return cleaned
