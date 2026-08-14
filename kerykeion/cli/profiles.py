# -*- coding: utf-8 -*-
"""Profile store: the editable "recipe" that rebuilds a subject.

A profile file (JSON, 0600 — it holds birth data, which is PII) has three parts:

* ``input`` — the small, editable, git-friendly recipe (the parameters the
  factory needs, in CLI shapes: ``date``/``time`` as strings, point-set aliases,
  etc.). The subject resolver turns this into a factory call.
* ``snapshot`` (optional) — a full ``AstrologicalSubjectModel.model_dump``,
  written by ``subject save --snapshot``, so the subject can be reused instantly
  and offline without recomputing.
* ``meta`` — provenance (kerykeion version, backend, created_at).

Nothing here imports a kerykeion symbol at module level; pydantic is a runtime
dependency of kerykeion and always present.
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
    extra: Optional[dict[str, Any]] = None  # for --set values persisted to the recipe


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


def _now_iso() -> str:
    # Aware UTC so ``created_at`` carries an offset and reads identically in
    # every timezone, instead of a naive local wall time.
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_meta() -> dict[str, Any]:
    """Provenance block for a freshly written profile."""
    try:
        from kerykeion import BACKEND_NAME, __version__

        return {
            "kerykeion_version": __version__,
            "backend": BACKEND_NAME,
            "created_at": _now_iso(),
        }
    except Exception:  # pragma: no cover - defensive; kerykeion is the core dep
        return {"created_at": _now_iso()}


def save(path: Path, profile: Profile) -> None:
    """Write *profile* to *path* atomically, with mode 0600 (PII: birth data).

    The write goes to a temporary file in the destination directory and is then
    ``os.replace``d onto *path*. Overwriting in place (``O_TRUNC``) would empty
    an existing profile *before* writing the new one, so a full disk, a Ctrl-C
    or a serialisation failure between the two left a zero-byte or half-written
    recipe — the user's birth data, gone, with every later ``-s`` failing to
    validate. ``os.replace`` is atomic within a filesystem: the profile is
    either the old one or the new one, never a fragment.
    """
    # Ensure the store exists with 0700 perms (birth data is PII). Only enforce
    # the restrictive mode when writing into the standard XDG store, so a
    # user-chosen path elsewhere is created but not chmodmed.
    store = config.profiles_dir()
    if path.parent == store:
        config.ensure_profile_store()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)

    data = profile.model_dump_json(indent=2)
    # Same directory as the target, so os.replace stays within one filesystem
    # (a cross-device rename is not atomic and would raise).
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    tmp_path = Path(tmp_name)
    try:
        try:
            # Pin UTF-8 and LF: the locale default encoding would raise
            # UnicodeEncodeError on a non-ASCII name under Windows cp1252, and
            # the default newline translation would write CRLF — both breaking
            # the round-trip with load(), which reads UTF-8. Matches
            # write_output().
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            os.close(fd)
            raise
        # mkstemp already creates 0600; set it explicitly so the mode is pinned
        # regardless of platform, before the file becomes visible as the profile.
        try:
            tmp_path.chmod(0o600)
        except OSError:
            pass
        os.replace(tmp_path, path)
    except BaseException:
        # Never leave the scratch file behind on failure — including Ctrl-C.
        tmp_path.unlink(missing_ok=True)
        raise


def load(path: Path) -> Profile:
    """Read and validate a profile from *path*."""
    return Profile.model_validate_json(path.read_text(encoding="utf-8"))


def list_profiles() -> list[str]:
    """Names of every profile in the store (usable with ``-s``).

    Read-only: it does not create the store (a missing directory simply yields
    an empty list), so a lookup miss for ``-s`` never has filesystem side effects.
    """
    store = config.profiles_dir()
    if not store.is_dir():
        return []
    return sorted(p.stem for p in store.glob("*.json"))


def resolve_path(spec: str) -> Path:
    """Resolve a ``-s VALUE``: an existing file path first, then a store name.

    Raises :class:`ProfileNotFound` with close-match suggestions when neither
    matches. A leading ``/`` or ``~`` is treated as an explicit file path and
    surfaces a normal ``FileNotFoundError`` if it does not exist.
    """
    if spec in ("-", "/dev/stdin"):
        raise ProfileNotFound(spec, [])
    candidate_path = Path(spec).expanduser()
    looks_like_path = spec.startswith(("/", "~")) or "/" in spec or spec.endswith(".json")
    if candidate_path.is_file():
        return candidate_path
    if looks_like_path:
        raise FileNotFoundError(f"No such profile file: {candidate_path}")
    in_store = config.profile_path(spec)
    if in_store.is_file():
        return in_store
    suggestions = difflib.get_close_matches(spec, list_profiles(), n=5, cutoff=0.4)
    raise ProfileNotFound(spec, suggestions)


