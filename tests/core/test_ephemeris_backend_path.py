# -*- coding: utf-8 -*-
"""Tests for ephemeris backend path resolution (EPHE_DATA_PATH).

Since ephemeris_backend.py resolves EPHE_DATA_PATH at import time,
these tests run in subprocesses with controlled environment variables.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

KERYKEION_ROOT = Path(__file__).resolve().parent.parent.parent


def _run_backend_probe(env_overrides: dict) -> dict:
    """Run a subprocess that imports ephemeris_backend and reports its state."""
    env = os.environ.copy()
    env.pop("KERYKEION_EPHE_PATH", None)
    env.pop("KERYKEION_BACKEND", None)
    env.update(env_overrides)

    code = (
        "import json; "
        "from kerykeion.ephemeris_backend import BACKEND_NAME, EPHE_DATA_PATH; "
        "print(json.dumps({'backend': BACKEND_NAME, 'ephe_path': EPHE_DATA_PATH}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(KERYKEION_ROOT),
        timeout=30,
    )
    if result.returncode != 0:
        pytest.fail(f"Subprocess failed:\nstderr: {result.stderr}")
    return json.loads(result.stdout.strip())


class TestEpheDataPathDefaults:
    """EPHE_DATA_PATH defaults to empty string when KERYKEION_EPHE_PATH is unset."""

    def test_default_path_is_empty_string(self):
        info = _run_backend_probe({})
        assert info["ephe_path"] == ""

    def test_user_path_is_respected(self, tmp_path):
        info = _run_backend_probe({"KERYKEION_EPHE_PATH": str(tmp_path)})
        assert info["ephe_path"] == str(tmp_path)

    def test_whitespace_only_path_treated_as_unset(self):
        info = _run_backend_probe({"KERYKEION_EPHE_PATH": "   "})
        assert info["ephe_path"] == ""


class TestSwephDirectoryRemoved:
    """The bundled kerykeion/sweph/ directory must not exist."""

    def test_sweph_directory_does_not_exist(self):
        sweph_dir = KERYKEION_ROOT / "kerykeion" / "sweph"
        assert not sweph_dir.exists(), (
            "kerykeion/sweph/ still exists — Swiss Ephemeris data must not be bundled"
        )

    def test_no_se1_files_in_package(self):
        se1_files = list((KERYKEION_ROOT / "kerykeion").rglob("*.se1"))
        assert se1_files == [], (
            f"Found .se1 files in kerykeion/: {[str(f) for f in se1_files]}"
        )

    def test_no_sefstars_in_package(self):
        sefstars = list((KERYKEION_ROOT / "kerykeion").rglob("sefstars.txt"))
        assert sefstars == [], (
            f"Found sefstars.txt in kerykeion/: {[str(f) for f in sefstars]}"
        )


class TestSwissephPathValidation:
    """When swisseph is active and KERYKEION_EPHE_PATH is set, warn if no .se1 files."""

    @pytest.fixture
    def _require_swisseph(self):
        try:
            import swisseph  # noqa: F401
        except ImportError:
            pytest.skip("pyswisseph not installed")

    def test_warns_on_empty_directory(self, tmp_path, _require_swisseph):
        env = {
            "KERYKEION_BACKEND": "swisseph",
            "KERYKEION_EPHE_PATH": str(tmp_path),
        }
        result = subprocess.run(
            [sys.executable, "-W", "all", "-c",
             "import logging; logging.basicConfig(level=logging.WARNING); "
             "from kerykeion.ephemeris_backend import EPHE_DATA_PATH"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, **env},
            cwd=str(KERYKEION_ROOT),
        )
        assert "does not contain readable .se1 files" in result.stderr

    def test_no_warning_when_se1_present(self, tmp_path, _require_swisseph):
        (tmp_path / "test.se1").write_bytes(b"dummy")
        env = {
            "KERYKEION_BACKEND": "swisseph",
            "KERYKEION_EPHE_PATH": str(tmp_path),
        }
        result = subprocess.run(
            [sys.executable, "-W", "all", "-c",
             "import logging; logging.basicConfig(level=logging.WARNING); "
             "from kerykeion.ephemeris_backend import EPHE_DATA_PATH"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, **env},
            cwd=str(KERYKEION_ROOT),
        )
        assert "does not contain readable .se1 files" not in result.stderr
