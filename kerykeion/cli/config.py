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
    """The application config directory, created 0700 on first access."""
    path = _base_config_dir()
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        # Non-POSIX filesystems (Windows) ignore the mode; the directory still
        # exists. The restriction is best-effort on those platforms.
        pass
    return path


def profiles_dir() -> Path:
    """The profiles store, created 0700 on first access."""
    path = app_dir() / PROFILES_SUBDIR
    path.mkdir(parents=True, exist_ok=True)
    try:
        path.chmod(0o700)
    except OSError:
        pass
    return path


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
