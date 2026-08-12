# -*- coding: utf-8 -*-
"""Tests for the ``kerykeion[cli]`` command-line interface.

Design rules (see DEVELOPMENT.md / TEST.md):

* payloads are tested for **identity**, not against golden snapshots —
  ``json.loads(stdout) == json.loads(model.model_dump_json())`` is immune to
  ephemeris drift (both sides move together), so there is no
  ``regenerate:cli`` task to keep in step;
* every test runs offline against the base ephemeris tier (dates in
  1849–2150), so this file is never skipped under ``poe test:swe``;
* the file name and every test name avoid the token ``all_points`` —
  ``tests/conftest.py`` skips TNO-needing node ids by regex, and that token
  would silently disable tests on the Swiss-Ephemeris backend;
* CliRunner runs in-process (counts toward coverage); a couple of cases that
  CliRunner cannot demonstrate (the real entry point, ``import kerykeion``
  staying typer-free) use a subprocess.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap

import pytest

pytestmark = pytest.mark.cli

# A fully-offline recipe (coords complete -> online=False, no network). The
# same numbers are reused below to rebuild the model for the identity asserts,
# so a change here must change both sides together.
_ADA = dict(
    name="Ada", year=1900, month=12, day=10, hour=18, minute=0,
    lat=51.5074, lng=-0.1278, tz_str="Europe/London", online=False,
)


@pytest.fixture
def deterministic_cli_env(tmp_path, monkeypatch):
    """Isolate Rich's terminal probing and the profile store from the dev shell.

    Rich reads the width from ``os.get_terminal_size()`` on fds 0/1/2 of the
    process, NOT from the Console file — so CliRunner alone does not shield us
    from the developer's terminal width. Pinning COLUMNS/LINES does.
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "dumb")
    monkeypatch.setenv("COLUMNS", "100")
    monkeypatch.setenv("LINES", "40")
    return tmp_path


@pytest.fixture
def runner(deterministic_cli_env):
    from typer.testing import CliRunner

    return CliRunner()


@pytest.fixture
def app():
    from kerykeion.cli.app import app

    return app


@pytest.fixture
def ada_profile(runner, app):
    """Save the Ada profile once; most chart tests reuse it."""
    result = runner.invoke(app, [
        "subject", "save", "ada",
        "--name", "Ada", "--date", "1900-12-10", "--time", "18:00",
        "--lat", "51.5074", "--lng", "-0.1278", "--tz", "Europe/London", "--offline",
    ])
    assert result.exit_code == 0, result.output
    return "ada"


# ── root: version / help / bare ───────────────────────────────────────────────


class TestRoot:
    def test_version_flag_exits_zero(self, runner, app):
        r = runner.invoke(app, ["--version"])
        assert r.exit_code == 0
        assert r.output.strip().split(".")[-1]  # something like 6.0.0aXX

    def test_help_lists_commands(self, runner, app):
        r = runner.invoke(app, ["--help"])
        assert r.exit_code == 0
        for cmd in ("natal", "synastry", "transit", "subject", "technique", "sky", "call"):
            assert cmd in r.output

    def test_bare_invocation_shows_help_and_exits_zero(self, runner, app):
        r = runner.invoke(app, [])
        assert r.exit_code == 0
        assert "Usage:" in r.output or "Commands" in r.output

    def test_unknown_command_is_usage_error(self, runner, app):
        r = runner.invoke(app, ["definitely-not-a-command"])
        # Click reports unknown command as exit 2.
        assert r.exit_code == 2


# ── errors are clean (no traceback) and carry the right code ─────────────────


class TestErrorBoundary:
    def test_missing_date_is_invalid_input_not_crash(self, runner, app):
        r = runner.invoke(app, ["natal", "--name", "x"])
        assert r.exit_code == 4
        assert "Traceback" not in r.output

    def test_missing_profile_is_invalid_input(self, runner, app):
        r = runner.invoke(app, ["natal", "-s", "nope_not_a_profile"])
        assert r.exit_code == 4
        assert "Traceback" not in r.output

    def test_traceback_flag_shows_traceback(self, runner, app):
        r = runner.invoke(app, ["--traceback", "natal", "--name", "x"])
        assert r.exit_code == 4
        assert "Traceback" in r.output


# ── output discipline: stdout payload, no ANSI in a pipe ─────────────────────


class TestOutputDiscipline:
    def test_json_in_pipe_is_parseable_and_ansi_free(self, runner, app, ada_profile):
        r = runner.invoke(app, ["natal", "-s", "ada", "-f", "json"])
        assert r.exit_code == 0
        assert "\x1b[" not in r.output  # no ANSI escapes in the payload
        payload = json.loads(r.output)
        assert payload["name"] == "Ada"
        assert payload["sun"]["sign"]

    def test_text_report_is_ansi_free(self, runner, app, ada_profile):
        r = runner.invoke(app, ["natal", "-s", "ada", "-f", "text"])
        assert r.exit_code == 0
        assert "\x1b[" not in r.output

    def test_svg_output_contains_svg_tag(self, runner, app, ada_profile, tmp_path):
        out = tmp_path / "ada.svg"
        r = runner.invoke(app, ["natal", "-s", "ada", "-f", "svg", "-o", str(out)])
        assert r.exit_code == 0
        content = out.read_text()
        assert "<svg" in content and "</svg>" in content

    def test_xml_output_is_valid_chart_xml(self, runner, app, ada_profile):
        # to_context() is a standalone function (not a model method) and it does
        # support the subject — it emits a <chart …> XML document.
        r = runner.invoke(app, ["natal", "-s", "ada", "-f", "xml"])
        assert r.exit_code == 0
        assert "\x1b[" not in r.output
        assert r.output.lstrip().startswith("<chart")


# ── identity (not snapshot): the CLI payload equals the library model ────────


class TestIdentity:
    def test_natal_json_matches_factory_model(self, runner, app, ada_profile):
        from kerykeion import AstrologicalSubjectFactory

        r = runner.invoke(app, ["natal", "-s", "ada", "-f", "json"])
        assert r.exit_code == 0
        cli_payload = json.loads(r.output)
        model = AstrologicalSubjectFactory.from_birth_data(**_ADA)
        assert cli_payload == json.loads(model.model_dump_json())

    def test_verify_summary_round_trips(self, runner, app, ada_profile):
        r = runner.invoke(app, ["subject", "verify", "ada", "-f", "json"])
        assert r.exit_code == 0
        summary = json.loads(r.output)
        assert summary["ok"] is True
        assert summary["name"] == "Ada"


# ── subject profile store ────────────────────────────────────────────────────


class TestSubjectStore:
    def test_save_creates_file_with_restrictive_perms(self, runner, app, deterministic_cli_env):
        r = runner.invoke(app, [
            "subject", "save", "ada",
            "--date", "1900-12-10", "--time", "18:00",
            "--lat", "51.5074", "--lng", "-0.1278", "--tz", "Europe/London", "--offline",
        ])
        assert r.exit_code == 0
        path = r.output.strip().splitlines()[0]  # first stdout line is the path
        assert os.path.isfile(path)
        # Birth data is PII: the store must be 0600.
        mode = os.stat(path).st_mode & 0o777
        assert mode == 0o600

    def test_list_and_show(self, runner, app, ada_profile):
        r_list = runner.invoke(app, ["subject", "list"])
        assert r_list.exit_code == 0
        assert "ada" in r_list.output
        r_show = runner.invoke(app, ["subject", "show", "ada"])
        assert r_show.exit_code == 0
        assert "Ada" in r_show.output


# ── sampling limit (exit 8) ──────────────────────────────────────────────────


class TestSamplingLimit:
    def test_over_ceiling_is_exit_eight(self, runner, app):
        # ~3 years of daily data > 730-day ceiling.
        r = runner.invoke(app, ["ephemeris", "--from", "2025-01-01", "--to", "2028-01-01"])
        assert r.exit_code == 8
        assert "Traceback" not in r.output

    def test_no_limit_overrides_ceiling(self, runner, app):
        # 740 days > the 730-day ceiling; --no-limit bypasses the pre-flight check
        # so the series actually computes instead of exiting 8.
        r = runner.invoke(app, [
            "ephemeris", "--from", "2025-01-01", "--to", "2027-01-11",
            "--no-limit", "-f", "json",
        ])
        assert r.exit_code == 0
        assert len(json.loads(r.output)) > 730


# ── dispatcher: security and introspection ───────────────────────────────────


class TestCallDispatcher:
    def test_os_system_is_refused(self, runner, app):
        # The headline security guarantee: 'os' is not in kerykeion.__all__.
        r = runner.invoke(app, ["call", "os.system", "--param", "cmd=ls"])
        assert r.exit_code == 4
        assert "Traceback" not in r.output
        assert "public API" in r.output or "not in" in r.output

    def test_list_returns_known_factories(self, runner, app):
        r = runner.invoke(app, ["call", "--list", "--json"])
        assert r.exit_code == 0
        owners = {item["owner"] for item in json.loads(r.output)}
        assert "ProfectionsFactory" in owners
        assert "os" not in owners

    def test_explain_classifies_subject_param(self, runner, app):
        r = runner.invoke(app, ["call", "ProfectionsFactory.from_subject", "--explain", "--json"])
        assert r.exit_code == 0
        params = {p["name"]: p["cli"] for p in json.loads(r.output)}
        assert params.get("subject") == "subject"
        assert params.get("years_before") == "cli"

    def test_unknown_owner_refused(self, runner, app):
        r = runner.invoke(app, ["call", "NoSuchFactory.method"])
        assert r.exit_code == 4


# ── entry point & import isolation (subprocess — CliRunner can't show these) ──


class TestEntryPoint:
    def test_entry_point_registered(self):
        from importlib.metadata import entry_points

        names = {ep.name for ep in entry_points(group="console_scripts")}
        assert "kerykeion" in names

    def test_import_kerykeion_does_not_load_typer(self):
        # The [cli] extra is optional; importing the library must stay typer-free
        # so `pip install kerykeion` (without [cli]) never fails on the guard.
        script = textwrap.dedent(
            """
            import sys
            import kerykeion
            assert "typer" not in sys.modules, "typer leaked into import kerykeion"
            assert "kerykeion.cli" not in sys.modules, "kerykeion.cli auto-imported"
            """
        )
        r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr

    def test_real_entry_point_version(self):
        # `python -m kerykeion` exercises the real __main__ (not CliRunner), which
        # is PATH-robust and does not depend on the console-script being on $PATH.
        r = subprocess.run([sys.executable, "-m", "kerykeion", "--version"], capture_output=True, text=True)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip()


# ── TTY detection seam ───────────────────────────────────────────────────────


class TestTtyDetection:
    def test_format_defaults_to_text_on_tty_and_json_in_pipe(self, runner, app, ada_profile, monkeypatch):
        # The single seam: patch stdout_is_tty and confirm the default format flips.
        # NB formats.py does `from ...io import stdout_is_tty`, so the live reference
        # lives in the formats namespace — patch it there, not in io.
        from kerykeion.cli.rendering import formats

        monkeypatch.setattr(formats, "stdout_is_tty", lambda: True)
        assert formats.resolve_format(None, None) == "text"
        monkeypatch.setattr(formats, "stdout_is_tty", lambda: False)
        assert formats.resolve_format(None, None) == "json"
