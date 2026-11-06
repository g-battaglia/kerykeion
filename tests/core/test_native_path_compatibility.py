"""Default and lunar-helper path setup must preserve native discovery."""

import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock, call

import pytest

from kerykeion.ephemeris_backend import backend
from kerykeion.moon_phase_details import utils


@pytest.mark.parametrize("native", [False, True])
@pytest.mark.parametrize("configured", ["", "/configured/ephe"])
def test_lunar_helper_uses_backend_path_rules(monkeypatch, native, configured):
    """Verify lunar helper uses backend path rules."""
    setter = Mock()
    monkeypatch.setattr(backend, "BACKEND_NAME", "libephemeris" if native else "swisseph")
    monkeypatch.setattr(backend, "EPHE_DATA_PATH", configured)
    monkeypatch.setattr(backend, "_NATIVE_SESSION_PATH", None)
    monkeypatch.setattr(backend.ephe, "set_ephe_path", setter)
    for _ in range(3):
        assert utils.configure_ephemeris_path() == backend.ephe.FLG_SWIEPH
    if native and not configured:
        setter.assert_not_called()
    else:
        assert setter.call_count == 3
        setter.assert_called_with(configured)


@pytest.mark.parametrize("native", [False, True])
def test_lunar_helper_preserves_active_native_override_and_swiss_behavior(monkeypatch, native):
    """Verify lunar helper preserves active native override and swiss behavior."""
    setter = Mock()
    monkeypatch.setattr(backend, "BACKEND_NAME", "libephemeris" if native else "swisseph")
    monkeypatch.setattr(backend, "EPHE_DATA_PATH", "")
    monkeypatch.setattr(backend, "_NATIVE_SESSION_PATH", None)
    monkeypatch.setattr(backend.ephe, "set_ephe_path", setter)
    monkeypatch.setattr(backend, "reset_ephemeris_session", Mock())
    with backend.ephemeris_session(ephe_path="/custom"):
        utils.configure_ephemeris_path()
    assert setter.call_args_list == ([call("/custom")] if native else [call("/custom"), call("")])


def test_sealed_embedded_base_path_probe():
    """Verify sealed embedded base path probe."""
    root = Path(__file__).resolve().parents[2]
    env = {**os.environ, "PYTHONPATH": str(root)}
    result = subprocess.run(
        [sys.executable, str(root / "tests/data/native_path_probe.py")],
        cwd=root, env=env, capture_output=True, text=True, timeout=90, check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["network_policy"] == "sealed"
    assert report["repeated_sessions"] == 5
    assert report["planetary_controls"] == 50 and report["house_controls"] == 60


def test_real_configured_path_survives_lunar_helpers(tmp_path):
    """Verify real configured path survives lunar helpers."""
    root = Path(__file__).resolve().parents[2]
    data = tmp_path / "data"
    data.mkdir()
    config = tmp_path / "libephemeris.toml"
    config.write_text(
        "[libephemeris]\n" + f"data_dir = {json.dumps(str(data))}\n"
        'precision = "base"\nmode = "leb"\nnetwork_policy = "sealed"\nauto_spk = false\n'
    )
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("LIBEPHEMERIS_", "KERYKEION_"))}
    env.update(PYTHONPATH=str(root), LIBEPHEMERIS_CONFIG=str(config), KERYKEION_BACKEND="libephemeris",
               KERYKEION_LEB_MODE="leb", KERYKEION_EPHE_PATH=str(tmp_path))
    code = """
import os
import libephemeris as le
from kerykeion.ephemeris_backend.backend import ephemeris_session
from kerykeion.moon_phase_details.utils import configure_ephemeris_path
for _ in range(3):
    with ephemeris_session():
        configure_ephemeris_path()
        assert le.get_library_path() == os.environ['KERYKEION_EPHE_PATH']
    le.release_data_cache()
"""
    result = subprocess.run([sys.executable, "-c", code], cwd=root, env=env,
                            capture_output=True, text=True, timeout=90, check=False)
    assert result.returncode == 0, result.stderr
