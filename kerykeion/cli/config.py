# -*- coding: utf-8 -*-
"""Profile storage paths (XDG). Profiles hold birth data, so the store is 0700 and each file 0600."""

from __future__ import annotations

import os
import re
from pathlib import Path

APP_DIR_NAME = "kerykeion"
PROFILES_SUBDIR = "subjects"


def app_dir() -> Path:
    """``$XDG_CONFIG_HOME/kerykeion`` or ``~/.config/kerykeion`` — a path only, never created here."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    return (Path(xdg).expanduser() if xdg else Path.home() / ".config") / APP_DIR_NAME


def profiles_dir() -> Path:
    return app_dir() / PROFILES_SUBDIR


def ensure_profile_store() -> Path:
    """Create the 0700 store if missing (the write path only, so a lookup miss has no side effects)."""
    for directory in (app_dir(), profiles_dir()):
        directory.mkdir(parents=True, exist_ok=True)
        try:
            directory.chmod(0o700)
        except OSError:  # non-POSIX filesystems ignore the mode
            pass
    return profiles_dir()


def profile_path(name: str) -> Path:
    """The on-disk path for a profile name, restricted to a safe charset so it cannot escape the store."""
    if not name:
        raise ValueError("profile name must not be empty")
    cleaned = re.sub(r"[^A-Za-z0-9_.\- ]+", "_", name).strip(" .")
    if not cleaned or cleaned in {".", ".."}:
        raise ValueError(f"profile name {name!r} has no usable characters")
    return profiles_dir() / f"{cleaned}.json"
