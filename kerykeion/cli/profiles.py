# -*- coding: utf-8 -*-
"""Profile store: the editable recipe that rebuilds a subject.

A profile (JSON, 0600 — it holds birth data) has an ``input`` recipe in CLI
shapes, an optional ``snapshot`` (a full ``AstrologicalSubjectModel`` dump
written by ``subject save --snapshot``) and ``meta`` provenance. No kerykeion
import at module level.
"""

from __future__ import annotations

import difflib
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pydantic

from kerykeion.cli import config

PROFILE_FORMAT_VERSION = 1


class ProfileInput(pydantic.BaseModel):
    """The editable recipe. Every field optional; unknown keys are rejected."""

    model_config = pydantic.ConfigDict(extra="forbid")

    name: Optional[str] = None
    mode: Optional[str] = None  # "birth" | "iso_utc" | "current"
    date: Optional[str] = None  # YYYY-MM-DD (negative year = BCE)
    time: Optional[str] = None  # HH:MM or HH:MM:SS
    seconds: Optional[int] = None
    iso_utc_time: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    tz_str: Optional[str] = None
    city: Optional[str] = None
    nation: Optional[str] = None
    online: Optional[bool] = None
    altitude: Optional[float] = None
    is_dst: Optional[bool] = None
    zodiac_type: Optional[str] = None
    sidereal_mode: Optional[str] = None
    houses_system_identifier: Optional[str] = None
    perspective_type: Optional[str] = None
    geonames_username: Optional[str] = None
    cache_expire_after_days: Optional[int] = None
    active_points: Optional[list[str]] = None
    active_fixed_stars: Optional[list[str]] = None
    custom_ayanamsa_t0: Optional[float] = None
    custom_ayanamsa_ayan_t0: Optional[float] = None
    calculate_lunar_phase: Optional[bool] = None
    calculate_dignities: Optional[bool] = None
    calculate_nakshatra: Optional[bool] = None
    calculate_gauquelin: Optional[bool] = None
    calculate_nutation: Optional[bool] = None
    calculate_local_space: Optional[bool] = None
    extra: Optional[dict[str, Any]] = None  # --set values persisted to the recipe


class Profile(pydantic.BaseModel):
    """A stored subject profile."""

    model_config = pydantic.ConfigDict(extra="forbid")

    kerykeion_profile: int = PROFILE_FORMAT_VERSION
    name: str
    input: ProfileInput
    snapshot: Optional[dict[str, Any]] = None
    meta: Optional[dict[str, Any]] = None


class ProfileNotFound(FileNotFoundError):
    def __init__(self, spec: str, suggestions: list[str]) -> None:
        self.spec = spec
        self.suggestions = suggestions
        suffix = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
        super().__init__(f"No profile named {spec!r} and no such file.{suffix}")


def make_meta() -> dict[str, Any]:
    """Provenance block for a freshly written profile (aware UTC, so it reads the same everywhere)."""
    from kerykeion import BACKEND_NAME, __version__

    return {
        "kerykeion_version": __version__,
        "backend": BACKEND_NAME,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def save(path: Path, profile: Profile) -> None:
    """Write *profile* to *path* atomically, mode 0600.

    A temporary file in the same directory is ``os.replace``d onto *path*, so a
    full disk or a Ctrl-C leaves either the old profile or the new one — never a
    truncated recipe. The 0700 store mode is enforced only inside the XDG store.
    """
    if path.parent == config.profiles_dir():
        config.ensure_profile_store()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        # UTF-8 and LF pinned: the locale default could reject a non-ASCII name and write CRLF on Windows.
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(profile.model_dump_json(indent=2))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            tmp_path.chmod(0o600)
        except OSError:
            pass
        os.replace(tmp_path, path)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def load(path: Path) -> Profile:
    return Profile.model_validate_json(path.read_text(encoding="utf-8"))


def list_profiles() -> list[str]:
    """Names of every profile in the store; read-only, a missing store is simply empty."""
    store = config.profiles_dir()
    return sorted(p.stem for p in store.glob("*.json")) if store.is_dir() else []


def resolve_path(spec: str) -> Path:
    """Resolve a ``-s VALUE``: an existing file path first, then a store name, else ``ProfileNotFound`` with suggestions."""
    if spec in ("-", "/dev/stdin"):
        raise ProfileNotFound(spec, [])
    candidate = Path(spec).expanduser()
    if candidate.is_file():
        return candidate
    if spec.startswith(("/", "~")) or "/" in spec or spec.endswith(".json"):
        raise FileNotFoundError(f"No such profile file: {candidate}")
    in_store = config.profile_path(spec)
    if in_store.is_file():
        return in_store
    raise ProfileNotFound(spec, difflib.get_close_matches(spec, list_profiles(), n=5, cutoff=0.4))
