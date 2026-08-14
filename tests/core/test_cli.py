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


@pytest.fixture(autouse=True)
def _reset_cli_error_policy():
    """Reset the CLI's process-global error knobs around every test.

    ``--traceback`` and ``--warnings-as-errors`` set module globals in
    :mod:`kerykeion.cli.errors` (via the root callback) that typer never resets,
    so without this a test that escalates warnings leaks the policy into every
    later test in the same process — making the suite order-dependent. Reset
    before and after so each test starts and ends clean.
    """
    from kerykeion.cli import errors

    errors.set_traceback_enabled(False)
    errors.set_warnings_as_errors(False)
    yield
    errors.set_traceback_enabled(False)
    errors.set_warnings_as_errors(False)


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

    def test_public_names_is_immutable_and_cached(self):
        # public_names() is @functools.cache'd, so resolve_target, `call --list`
        # and `--explain` all share ONE object. It must be immutable, or a future
        # caller filtering/extending it (names.pop(...) / names[x] = y) would leak
        # into every later dispatch in the process.
        import kerykeion.cli.registry as registry

        first = registry.public_names()
        assert registry.public_names() is first  # cached → same object
        with pytest.raises(TypeError):
            first["__inject__"] = object()


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


# ── input-validation regressions ─────────────────────────────────────────────
# Each test below pins one finding from the feat/cli review: the failure mode is
# named in the docstring so a regression points at the behaviour lost.


class TestInputValidationRegressions:
    """Guard against silent or mis-classified bad-input handling."""

    def test_natal_without_time_is_rejected(self, runner, app):
        # #1: birth mode requires --time; missing it must be exit 4 (invalid
        # input), not an opaque downstream crash or silent defaults.
        r = runner.invoke(app, [
            "natal", "--date", "1990-01-01",
            "--lat", "48.85", "--lng", "2.35", "--tz", "Europe/Paris", "--offline",
        ])
        assert r.exit_code == 4
        assert "Traceback" not in r.output

    def test_hour_twenty_four_is_rejected(self, runner, app):
        # #15: parse_time accepted 24:00 (off-by-one: hour range was <= 24);
        # 24 is not a valid wall-clock hour and must be exit 4.
        r = runner.invoke(app, [
            "natal", "--date", "2024-01-01", "--time", "24:00",
            "--lat", "48.85", "--lng", "2.35", "--tz", "Europe/Paris", "--offline",
        ])
        assert r.exit_code == 4
        assert "Traceback" not in r.output

    def test_step_zero_is_rejected_not_silently_one(self, runner, app):
        # #5: `step or 1` rewrote --step 0 to 1 (falsy-zero). The pre-flight
        # check then passed and the factory ran with step=1, producing a huge
        # series instead of an error. Now 0 is a clean exit 4.
        r = runner.invoke(app, [
            "ephemeris", "--lat", "0", "--lng", "0", "--tz", "UTC",
            "--from", "2024-01-01", "--to", "2024-01-05", "--step", "0",
        ])
        assert r.exit_code == 4
        assert "Traceback" not in r.output

    def test_transits_step_zero_is_rejected(self, runner, app, ada_profile):
        # #5b: same falsy-zero bug on `transits` (step_n was `step or 1`).
        r = runner.invoke(app, [
            "transits", "-s", "ada",
            "--from", "2024-01-01", "--to", "2024-01-05", "--step", "0",
        ])
        assert r.exit_code == 4

    def test_transit_to_time_requires_to_date(self, runner, app, ada_profile):
        # #8: `--to-time` without `--to-date` silently dropped the time and
        # built a transit to the natal date at 00:00; now a clean exit 4.
        r = runner.invoke(app, ["transit", "-s", "ada", "--to-time", "12:30"])
        assert r.exit_code == 4
        assert "--to-date" in r.output

    def test_call_param_typo_is_rejected(self, runner, app, ada_profile):
        # #14: a typoed --param key (e.g. years_beforee) was silently dropped
        # by the init/method split and the factory ran with the default — a
        # wrong result with no error. Now exit 4 naming the unknown key.
        r = runner.invoke(app, [
            "call", "ProfectionsFactory.from_subject", "-s", "ada",
            "--param", "years_beforee=3",
        ])
        assert r.exit_code == 4
        assert "Traceback" not in r.output

    def test_output_to_directory_is_exit_four(self, runner, app, ada_profile, tmp_path):
        # #10: -o on a directory raised IsADirectoryError → exit 1 with a
        # traceback; OSError now classifies as invalid input → exit 4, clean.
        r = runner.invoke(app, ["natal", "-s", "ada", "-o", str(tmp_path)])
        assert r.exit_code == 4
        assert "Traceback" not in r.output


# ── sampling-limit DST awareness (#13) ───────────────────────────────────────


class TestSamplingDstAwareness:
    """The pre-flight sample count must match the library's UTC-based count.

    Across a DST fall-back a wall-clock 48h span is 49 UTC hours; the library
    counts in UTC (one extra sample), so the pre-flight check must too, or it
    under-counts and lets an over-ceiling series slip through to exit 4 instead
    of the dedicated exit 8.
    """

    def test_fall_back_hours_count_matches_library(self):
        # Europe/Rome fell back on 2024-10-27 03:00 CEST → 02:00 CET: the local
        # 2024-10-26 → 2024-10-28 span is 48 wall-clock hours but 49 UTC hours.
        from datetime import datetime

        from kerykeion import EphemerisDataFactory
        from kerykeion.cli.sampling import count_samples

        start, end = datetime(2024, 10, 26), datetime(2024, 10, 28)
        cli_count = count_samples(start, end, "hours", 1, tz_str="Europe/Rome")
        # Library's own n_samples formula: int(utc_delta_hours) // step + 1.
        factory = EphemerisDataFactory(
            start, end, step_type="hours", step=1, tz_str="Europe/Rome"
        )
        factory.get_ephemeris_data(as_model=True)
        library_count = len(factory.dates_list)
        assert cli_count == library_count == 50
        # And the DST correction actually changed the answer vs naive.
        assert count_samples(start, end, "hours", 1) == 49

    def test_days_count_is_dst_independent(self):
        # Days use wall-clock day arithmetic in both the CLI and the library,
        # so a range that spans a fall-back boundary still counts whole days.
        from datetime import datetime

        from kerykeion.cli.sampling import count_samples

        start, end = datetime(2024, 10, 26), datetime(2024, 10, 28)
        assert count_samples(start, end, "days", 1) == 3
        assert count_samples(start, end, "days", 1, tz_str="Europe/Rome") == 3

    def test_count_samples_rejects_non_positive_step(self):
        from datetime import datetime

        from kerykeion.cli.sampling import count_samples

        with pytest.raises(ValueError):
            count_samples(datetime(2024, 1, 1), datetime(2024, 1, 2), "days", 0)
        with pytest.raises(ValueError):
            count_samples(datetime(2024, 1, 1), datetime(2024, 1, 2), "hours", -1)


# ── kerykeion status (diagnostics) ───────────────────────────────────────────
#
# ``status`` is a stdlib-only diagnostic (kerykeion/cli/diagnostics.py) served
# both by this Typer command and by the no-extra dispatch in kerykeion.cli.main.
# TestStatus exercises the Typer registration; TestNoExtraFallback exercises the
# stdlib path that a bare ``pip install kerykeion`` (no [cli]) actually sees.


class TestStatus:
    """``kerykeion status`` reports runtime backend/ephemeris state (Typer path).

    The no-extra path cannot run here (typer is installed in the dev env and
    CliRunner is in-process); it is covered by :class:`TestNoExtraFallback`.
    """

    def test_status_text_lists_backend_and_mode(self, runner, app):
        r = runner.invoke(app, ["status"])
        assert r.exit_code == 0, r.output
        assert "Backend:" in r.output
        assert "Environment:" in r.output

    def test_status_json_is_parseable(self, runner, app):
        r = runner.invoke(app, ["status", "--json"])
        assert r.exit_code == 0, r.output
        payload = json.loads(r.output)
        assert payload["backend"] in ("libephemeris", "swisseph")
        assert "kerykeion_version" in payload
        assert "python_version" in payload

    def test_status_reports_python_version_and_platform(self, runner, app):
        import platform as _platform

        r = runner.invoke(app, ["status"])
        assert r.exit_code == 0, r.output
        assert _platform.python_version() in r.output

    def test_status_lists_leb_files_on_libephemeris(self, runner, app):
        from kerykeion import BACKEND_NAME

        r = runner.invoke(app, ["status"])
        assert r.exit_code == 0, r.output
        # calc_mode / LEB inventory exist only on the libephemeris backend.
        if BACKEND_NAME == "libephemeris":
            assert "calc mode:" in r.output
            assert "Ephemeris data (libephemeris LEB):" in r.output
            assert "files:" in r.output  # the inventory summary line


class TestNoExtraFallback:
    """The stdlib core that runs when the ``[cli]`` extra is absent.

    The dev env has typer installed, and CliRunner runs in-process, so it
    cannot show the no-extra behaviour. We spawn a subprocess that blocks
    typer/rich via a ``sys.meta_path`` finder and drives ``kerykeion.cli.main``
    the way a bare ``pip install kerykeion`` would. click is NOT blocked: it is
    a transitive of libephemeris (present even without the extra), and the
    dispatch decision is based on typer, not click.
    """

    _SCRIPT = textwrap.dedent(
        """\
        import sys
        class _Blocker:
            def find_spec(self, name, path=None, target=None):
                if name in ("typer", "rich"):
                    raise ImportError("blocked by test")
                return None
        sys.meta_path.insert(0, _Blocker())
        sys.argv = ["kerykeion", *sys.argv[1:]]
        from kerykeion.cli import main
        raise SystemExit(main())
        """
    )

    def _run(self, args):
        return subprocess.run(
            [sys.executable, "-c", self._SCRIPT, *args],
            capture_output=True,
            text=True,
        )

    def test_status_works_without_extra(self):
        r = self._run(["status"])
        assert r.returncode == 0, r.stderr
        assert "Backend:" in r.stdout

    def test_status_json_works_without_extra(self):
        r = self._run(["status", "--json"])
        assert r.returncode == 0, r.stderr
        json.loads(r.stdout)  # valid JSON, no further assertion needed

    def test_version_works_without_extra(self):
        r = self._run(["--version"])
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip()

    def test_help_works_without_extra(self):
        r = self._run(["--help"])
        assert r.returncode == 0, r.stderr
        assert "Usage" in r.stdout

    def test_bare_invocation_shows_help_without_extra(self):
        r = self._run([])
        assert r.returncode == 0, r.stderr
        assert "Usage" in r.stdout

    def test_full_cli_command_degrades_to_install_hint(self):
        r = self._run(["natal", "-s", "ada"])
        assert r.returncode == 3, r.stderr
        assert "kerykeion[cli]" in r.stderr
        assert "Traceback" not in r.stderr

    def test_status_unknown_option_is_invalid_input(self):
        r = self._run(["status", "--bogus"])
        assert r.returncode == 4, r.stderr
        assert "Traceback" not in r.stderr


# ── second code-review pass (PR #249) ────────────────────────────────────────


class TestCodeReviewFixes:
    """Regressions surfaced by the v6 CLI code-review pass.

    Each test names the review finding it pins (``# Fn``). Findings deferred as
    out-of-scope or wontfix-by-design (Click-in-NOTICE, test:core without the
    extra, ``**kwargs`` dispatch with no current caller) are documented in the PR
    comment, not here.
    """

    # F1: a Union-typed subject parameter (AstrologicalSubjectModel |
    # CompositeSubjectModel | PlanetReturnModel, as in AspectsFactory) must still
    # be recognised as a -s binding site, not misclassified json-only.
    def test_union_subject_param_is_recognised(self):
        from kerykeion.cli import introspect, registry

        target = registry.resolve_target("AspectsFactory.single_chart_aspects")
        classes = [p.classification for p in introspect.explain(target)]
        assert introspect.SUBJECT in classes

    def test_call_aspects_binds_subject_flag(self, runner, app, ada_profile):
        # Before the fix this raised "has no subject parameter; -s is not used
        # here." Now -s binds; the call may need more, but never that message.
        r = runner.invoke(app, ["call", "AspectsFactory.single_chart_aspects", "-s", "ada"])
        assert "no subject parameter" not in r.output
        assert "Traceback" not in r.output

    # F2: --to-date without --to-time is the symmetric case of the already-tested
    # --to-time-without---to-date; it must not fall through to the misleading
    # "birth mode needs --time / use kerykeion now".
    def test_transit_to_date_requires_to_time(self, runner, app, ada_profile):
        r = runner.invoke(app, ["transit", "-s", "ada", "--to-date", "2025-06-01"])
        assert r.exit_code == 4
        assert "--to-time" in r.output
        assert "kerykeion now" not in r.output

    # F3: --set on a list-typed profile field (active_points) must coerce to a
    # list, matching --points / --param, not store a string the recipe rejects.
    def test_set_active_points_is_coerced_to_list(self, runner, app, deterministic_cli_env):
        from kerykeion.cli import profiles

        r = runner.invoke(app, [
            "subject", "save", "bod",
            "--name", "Bod", "--date", "2000-01-01", "--time", "12:00",
            "--lat", "0", "--lng", "0", "--tz", "UTC", "--offline",
            "--set", "active_points=sun,moon",
        ])
        assert r.exit_code == 0, r.output
        assert profiles.load(profiles.resolve_path("bod")).input.active_points == ["sun", "moon"]

    # F8: a partially-supplied --lat (no --lng) must not silently trigger a
    # global eclipse search that ignores the coordinate.
    def test_sky_eclipses_partial_coord_is_rejected(self, runner, app):
        r = runner.invoke(app, ["sky", "eclipses", "--lat", "48.14"])
        assert r.exit_code == 4
        assert "--lat" in r.output and "--lng" in r.output

    # F10: transit -s ada (no inline coords) defaults the transit moment to the
    # natal birthplace and stays offline, instead of going online with an empty
    # GeoNames query.
    def test_transit_inherits_natal_coords_offline(self, runner, app, ada_profile):
        r = runner.invoke(app, ["transit", "-s", "ada"])
        assert r.exit_code == 0, r.output
        assert r.output  # a transit chart was produced

    # F12: --warnings-as-errors must not be bypassed when the renderer itself
    # crashes; the warnings are fatal (exit 9) even then.
    def test_warnings_as_errors_survives_render_crash(self, monkeypatch):
        import kerykeion.cli.rendering.emit as _emit
        from kerykeion.cli import errors, warnings

        class _Obj:
            ephemeris_warnings = ["fake"]
            polar_house_fallbacks = None

        def _boom(*a, **k):
            raise RuntimeError("render exploded")

        errors.set_warnings_as_errors(True)
        try:
            monkeypatch.setattr(_emit, "render", _boom)
            with pytest.raises(SystemExit) as ei:
                warnings.output_with_warnings(_Obj(), "svg", None)
            assert ei.value.code == int(errors.ExitCode.WARNINGS_AS_ERRORS)
        finally:
            errors.set_warnings_as_errors(False)

    # F15: call --list must not advertise pydantic-model methods (model_validate,
    # model_dump) that resolve_target refuses to dispatch.
    def test_call_list_omits_pydantic_models(self, runner, app):
        r = runner.invoke(app, ["call", "--list", "--json"])
        assert r.exit_code == 0, r.output
        owners = {entry["owner"] for entry in json.loads(r.output)}
        assert "AstrologicalSubjectModel" not in owners

    # F9: a libephemeris coverage/data error maps to exit 6 (ephemeris), not 5/4.
    def test_libephemeris_range_error_is_exit_six(self):
        from kerykeion.cli import errors

        try:
            from libephemeris import EphemerisRangeError
        except ImportError:
            pytest.skip("libephemeris not installed")
        errors._backend_types = None  # rebuild the cached tuple for this test
        try:
            assert errors.classify(EphemerisRangeError("out of range")) is errors.ExitCode.EPHEMERIS
        finally:
            errors._backend_types = None  # rebuild normally afterwards

    # F11: main(argv) must honor an explicit argv on the typer path (Click reads
    # sys.argv, so without the swap a passed argv is silently ignored).
    def test_main_honors_explicit_argv(self, monkeypatch):
        from kerykeion.cli import main

        # If argv were ignored, Click would see this bogus command line and exit
        # 2 (unknown command). A 0 means the explicit argv won.
        monkeypatch.setattr(sys, "argv", ["kerykeion", "definitely-not-a-command"])
        with pytest.raises(SystemExit) as ei:
            main(["--version"])
        assert ei.value.code == 0

    # F7: -o files keep LF endings on every platform (no CRLF translation), so
    # byte-exact JSON/SVG survives a Windows save for jq/diff.
    def test_output_file_uses_lf(self, tmp_path):
        from kerykeion.cli.rendering.emit import write_output

        out = tmp_path / "o.json"
        write_output("a\nb", str(out))
        assert out.read_bytes() == b"a\nb\n"

    # F6: a saved profile is UTF-8 with LF endings and round-trips, even with a
    # non-ASCII name (the Windows cp1252 default would otherwise raise).
    def test_profile_save_is_utf8_lf_and_round_trips(self, runner, app, deterministic_cli_env):
        from kerykeion.cli import profiles

        r = runner.invoke(app, [
            "subject", "save", "maja",
            "--name", "München", "--date", "2000-01-01", "--time", "12:00",
            "--lat", "0", "--lng", "0", "--tz", "UTC", "--offline",
        ])
        assert r.exit_code == 0, r.output
        path = profiles.resolve_path("maja")
        raw = path.read_bytes()
        assert b"\r\n" not in raw  # LF only, no platform translation
        assert "München".encode("utf-8") in raw  # UTF-8, not cp1252-mangled
        assert profiles.load(path).input.name == "München"


class TestThirdReviewPass:
    """Regressions from the third code-review sweep (every finding verified).

    Numbering mirrors the review's final 15. ``#10`` (sampling DST divergence)
    and the ``**kwargs`` half of ``#9`` are deferred with rationale in the PR
    comment, not pinned here.
    """

    # #1 / #2: the house-system name map is checked against the authoritative
    # HousesSystemIdentifier Literal. Porphyry is "O" (not "B" = Alcabitius);
    # APC is "Y" (not "n", which is not even a member).
    def test_house_name_map_matches_the_literal(self):
        from kerykeion.cli.subject_resolver import resolve_house_system

        assert resolve_house_system("porphyry") == "O"
        assert resolve_house_system("porphyrius") == "O"
        assert resolve_house_system("apc") == "Y"
        assert resolve_house_system("placidus") == "P"  # unchanged sanity check

    # #6: an unknown single letter is rejected here with a helpful message, not
    # deferred to a confusing pydantic "input does not match the literal".
    def test_unknown_house_letter_is_rejected_cleanly(self):
        from kerykeion.cli.subject_resolver import resolve_house_system

        with pytest.raises(ValueError) as ei:
            resolve_house_system("G")
        assert "house-system letter" in str(ei.value)

    # #3: technique directions has no planet filter; --planets used to bind to
    # ``aspects`` (which wants ANGLES) and always crashed. The flag is now
    # ``--aspects`` and validates its values.
    def test_directions_aspects_rejects_non_angle(self, runner, app, ada_profile):
        r = runner.invoke(app, ["technique", "directions", "-s", "ada", "--aspects", "sun,moon"])
        assert r.exit_code == 4
        assert "must be" in r.output

    def test_directions_no_longer_advertises_a_planets_flag(self, runner, app, ada_profile):
        r = runner.invoke(app, ["technique", "directions", "-s", "ada", "--planets", "sun"])
        assert r.exit_code == 2  # Click: unknown option
        assert "Traceback" not in r.output

    # #4: the transit wheel inherits the natal frame (zodiac/sidereal/houses/
    # perspective). create_transit_chart_data does not re-frame, so both rings
    # must be built in the same zodiac. Run in a subprocess: the transit JSON is
    # large, and pushing it through CliRunner's stdout capture under pytest
    # closes the buffer (a CliRunner/pytest-capture artefact, not a CLI bug — a
    # bare-process run produces both wheels Sidereal).
    def test_transit_inherits_natal_zodiac_frame(self, deterministic_cli_env):
        from kerykeion.cli import config, profiles

        # Persist a Sidereal profile into the isolated store.
        profiles.save(
            config.profile_path("cyb"),
            profiles.Profile(
                name="Cyb",
                input=profiles.ProfileInput(
                    name="Cyb", mode="birth", date="2000-01-01", time="12:00",
                    lat=0.0, lng=0.0, tz_str="UTC", online=False, zodiac_type="Sidereal",
                ),
                meta=profiles.make_meta(),
            ),
        )
        out = deterministic_cli_env / "transit.json"
        script = textwrap.dedent(f"""
            import sys
            from kerykeion.cli import main
            sys.argv = ["kerykeion", "transit", "-s", "cyb", "-f", "json", "-o", {str(out)!r}]
            sys.exit(main())
        """)
        env = {
            **os.environ, "XDG_CONFIG_HOME": str(deterministic_cli_env),
            "NO_COLOR": "1", "TERM": "dumb",
        }
        res = subprocess.run(
            [sys.executable, "-c", script], env=env, capture_output=True, text=True,
        )
        assert res.returncode == 0, res.stderr

        def _zodiacs(node):
            found = []
            if isinstance(node, dict):
                if "zodiac_type" in node:
                    found.append(node["zodiac_type"])
                for v in node.values():
                    found.extend(_zodiacs(v))
            elif isinstance(node, list):
                for v in node:
                    found.extend(_zodiacs(v))
            return found

        zodiacs = _zodiacs(json.loads(out.read_text(encoding="utf-8")))
        assert zodiacs.count("Sidereal") >= 2  # natal inner + transit outer

    # #5: an offset-bearing --from is an absolute instant; the wall-clock parts
    # must be converted into --tz before extraction (12:30Z -> 14:30 Europe/Rome
    # in summer), not re-read verbatim as a Rome wall time.
    def test_sky_voc_moment_respects_offset(self, runner, app):
        from kerykeion import VoidOfCourseMoonFactory

        r = runner.invoke(app, [
            "sky", "voc", "--from", "2030-06-15T12:30:00Z", "--tz", "Europe/Rome",
            "-f", "json",
        ])
        assert r.exit_code == 0, r.output
        expected = VoidOfCourseMoonFactory.from_datetime(
            2030, 6, 15, 14, 30, tz_str="Europe/Rome"
        )
        assert json.loads(r.output) == json.loads(expected.model_dump_json())

    # #7: --refine only applies to the --events collapse; without --events it is
    # a silent no-op, so it must be rejected up front.
    def test_refine_requires_events(self, runner, app, ada_profile):
        r = runner.invoke(app, [
            "transits", "-s", "ada", "--from", "2025-01-01", "--to", "2025-01-10", "--refine",
        ])
        assert r.exit_code == 4
        assert "--events" in r.output

    # #8: a typo in a method name is a user-input problem (exit 4), not an
    # unexpected crash (exit 1 with a "rerun with --traceback" hint).
    def test_call_unknown_member_is_exit_four(self, runner, app):
        r = runner.invoke(app, ["call", "ChartDataFactory.nonExistentMethod"])
        assert r.exit_code == 4
        assert "no public member" in r.output
        assert "Traceback" not in r.output

    # #9: a dict/Mapping --param is parsed as JSON, not forwarded as a literal
    # string that the factory then rejects with a confusing TypeError.
    def test_call_param_dict_is_parsed_as_json(self):
        from kerykeion.cli.introspect import coerce_value

        assert coerce_value(dict, '{"sun": 1.5}') == {"sun": 1.5}
        with pytest.raises(ValueError):
            coerce_value(dict, "not json")

    # #11: emit_warnings resolves sys.stderr at call time so a redirected stderr
    # (CliRunner, capsys, an embedding host) actually captures the warnings.
    def test_emit_warnings_honors_redirected_stderr(self, monkeypatch):
        import io

        from kerykeion.cli import warnings as _w

        class _Warn:
            code = "X"
            point_name = "Moon"
            message = "boom"

        captured = io.StringIO()
        monkeypatch.setattr(sys, "stderr", captured)
        _w.emit_warnings([_Warn()], [])
        assert "kerykeion: warning:" in captured.getvalue()

    # #12: -o into a not-yet-existing directory creates it (mirroring subject
    # save) instead of failing with a confusing exit-4 "invalid input".
    def test_output_file_creates_parent_dir(self, tmp_path):
        from kerykeion.cli.rendering.emit import write_output

        out = tmp_path / "new" / "deep" / "o.json"
        write_output("{}", str(out))
        assert out.read_text() == "{}\n"

    # #13: a lookup miss for -s must not create the profile store as a side
    # effect of gathering "did you mean" suggestions.
    def test_resolve_path_does_not_create_store_on_miss(self, deterministic_cli_env, monkeypatch):
        from kerykeion.cli import config, profiles

        store = config.profiles_dir()
        assert not store.exists()
        with pytest.raises(profiles.ProfileNotFound):
            profiles.resolve_path("nonexistent")
        # Still absent: the read-only lookup did not mkdir anything.
        assert not store.exists()

    # #15: commands that render a derivative of a subject still surface (and can
    # escalate via --warnings-as-errors) the warnings carried on that subject.
    def test_output_with_warnings_collects_from_warning_source(self, monkeypatch):
        import io

        from kerykeion.cli import warnings as _w

        class _Sink:  # what is rendered (a compact summary): no warnings
            pass

        class _Subject:  # what was materialised: carries a warning
            ephemeris_warnings = ["fake"]
            polar_house_fallbacks = None

        captured = io.StringIO()
        monkeypatch.setattr(sys, "stderr", captured)
        _w.output_with_warnings(_Sink(), "json", None, warning_source=_Subject())
        assert "kerykeion: warning:" in captured.getvalue()


class TestXhighReviewFixes:
    """Regressions surfaced by the extra-high-effort (xhigh) review pass."""

    # transit: a partially-supplied relocated location is rejected, not silently
    # localised at the natal timezone (a multi-hour UTC error in houses/ASC).
    def test_transit_partial_geo_override_is_rejected(self, runner, app, ada_profile):
        r = runner.invoke(
            app, ["transit", "-s", ada_profile, "--lat", "40.0", "--lng", "-74.0"]
        )
        assert r.exit_code == 4
        assert "relocated transit needs --lat, --lng and --tz together" in r.output

    def test_return_partial_geo_override_is_rejected(self, runner, app, ada_profile):
        r = runner.invoke(
            app,
            ["return", "-s", ada_profile, "--year", "2025",
             "--lat", "40.0", "--lng", "-74.0"],
        )
        assert r.exit_code == 4
        assert "relocated return needs --lat, --lng and --tz together" in r.output

    # sky: inline --lat/--lng/--tz take precedence over the profile's location.
    def test_sky_location_inline_overrides_profile(self, ada_profile):
        from kerykeion.cli.commands.sky import _latlng, _location

        # ada is London (51.5074 / -0.1278); inline 40 / 10 wins.
        assert _location(ada_profile, 40.0, 10.0, "Europe/Rome", "t") == (
            40.0, 10.0, "Europe/Rome",
        )
        assert _latlng(ada_profile, 40.0, 10.0, "t") == (40.0, 10.0)
        # Without inline flags the profile is used.
        lat, _lng, _tz = _location(ada_profile, None, None, None, "t")
        assert abs(lat - 51.5074) < 1e-3

    # sky voc range: --tz is honoured by attaching the zone's offset to naive
    # bounds (from_iso_range is UTC-only).
    def test_sky_attach_tz_offset_for_naive_bound(self):
        from kerykeion.cli.commands.sky import _attach_tz_offset

        # Rome summer is +02:00; a naive bound becomes offset-aware.
        assert _attach_tz_offset("2025-06-01T00:00:00", "Europe/Rome", "voc") == (
            "2025-06-01T00:00:00+02:00"
        )
        # Already-aware bounds pass through unchanged.
        assert _attach_tz_offset("2025-06-01T00:00:00+00:00", "Europe/Rome", "voc") == (
            "2025-06-01T00:00:00+00:00"
        )
        assert _attach_tz_offset("2025-06-01T00:00:00", None, "voc") == (
            "2025-06-01T00:00:00"
        )
        with pytest.raises(ValueError):
            _attach_tz_offset("2025-06-01T00:00:00", "Not/A/Zone", "voc")

    # warnings: a plural `subjects` list (RelationshipScoreModel) is recursed.
    def test_collect_warnings_recurses_plural_subjects(self):
        from kerykeion.cli.warnings import collect_warnings

        class _Warn:
            code = "X"
            point_name = "Moon"
            message = "boom"

        class _Subj:
            ephemeris_warnings = [_Warn()]
            polar_house_fallbacks = None

        class _Score:
            ephemeris_warnings = None
            polar_house_fallbacks = None
            subjects = [_Subj()]

        eph, _polar = collect_warnings(_Score())
        assert len(eph) == 1

    # introspect: non-string Literal members coerce by value AND type.
    def test_coerce_value_non_string_literal(self):
        from typing import Literal

        from kerykeion.cli.introspect import coerce_value

        assert coerce_value(Literal[1, 2], "1") == 1
        assert coerce_value(Literal[1, 2], "2") == 2
        assert type(coerce_value(Literal[1, 2], "1")) is int
        with pytest.raises(ValueError):
            coerce_value(Literal[1, 2], "3")
        # bool Literal stays boolean (no bool/int aliasing).
        assert coerce_value(Literal[True, False], "true") is True
        assert coerce_value(Literal[True, False], "false") is False

    # introspect: PEP 604 `X | Y` unions are classified/coerced, not misread.
    def test_introspect_handles_pep604_union(self):
        from kerykeion import AstrologicalSubjectModel
        from kerykeion.cli.introspect import _classify, _is_subject, _strip_optional

        assert _strip_optional(int | None) is int
        assert _classify(int | str | None) == "cli"
        # A PEP 604 subject union is recognised as a subject binding site.
        assert _is_subject(AstrologicalSubjectModel | None) is True

    # sampling: mixed offset-aware/naive bounds raise a clean ValueError.
    def test_count_samples_mixed_awareness_is_clean_error(self):
        from datetime import datetime, timezone

        from kerykeion.cli.sampling import count_samples

        with pytest.raises(ValueError, match="same ISO form"):
            count_samples(
                datetime(2024, 1, 1),
                datetime(2024, 12, 31, tzinfo=timezone.utc),
                "days", 1,
            )

    # sky: --zodiac accepts the casing the library accepts.
    def test_zodiac_kwargs_case_insensitive(self):
        from kerykeion.cli.commands.sky import _zodiac_kwargs

        assert _zodiac_kwargs("tropical", None)["zodiac_type"] == "Tropical"
        assert _zodiac_kwargs("SIDEREAL", None)["zodiac_type"] == "Sidereal"
        assert _zodiac_kwargs("Tropic", None)["zodiac_type"] == "Tropical"  # legacy
        with pytest.raises(ValueError):
            _zodiac_kwargs("galactic", None)

    # series: --no-limit no longer skips the inverted-range check.
    def test_no_limit_still_rejects_inverted_range(self, runner, app):
        r = runner.invoke(
            app,
            ["ephemeris", "--lat", "0", "--lng", "0", "--tz", "UTC",
             "--from", "2025-12-31", "--to", "2025-01-01", "--no-limit"],
        )
        assert r.exit_code == 4
        assert "must not precede" in r.output

    # sky _moment: an aware instant in the fold's second reading is surfaced.
    def test_moment_rejects_ambiguous_fold(self):
        from kerykeion.cli.commands.sky import _moment

        # 2024-10-27 01:30 UTC = 02:30 Europe/Rome, the second (CET/fold=1) reading.
        with pytest.raises(ValueError, match="ambiguous wall time"):
            _moment("2024-10-27T01:30:00+00:00", "hours", "Europe/Rome")

    # sampling: the hours count across a fold bound matches the library
    # (localize_naive is_dst=False, not replace(tzinfo=tz) fold=0).
    def test_utc_bounds_fold_matches_library(self):
        from datetime import datetime

        from kerykeion import EphemerisDataFactory
        from kerykeion.cli.sampling import count_samples

        # Both bounds sit inside Rome's 2024-10-27 fall-back fold.
        start = datetime(2024, 10, 27, 1, 30)
        end = datetime(2024, 10, 27, 2, 30)
        cli = count_samples(start, end, "hours", 1, tz_str="Europe/Rome")
        factory = EphemerisDataFactory(
            start, end, step_type="hours", step=1, tz_str="Europe/Rome", is_dst=False
        )
        factory.get_ephemeris_data(as_model=True)
        assert cli == len(factory.dates_list)

    # sampling: days count on aware bounds spanning DST matches the library.
    def test_days_count_aware_matches_library_across_dst(self):
        from datetime import datetime, timezone

        from kerykeion import EphemerisDataFactory
        from kerykeion.cli.sampling import count_samples

        start = datetime(2024, 3, 30, 12, 0, tzinfo=timezone.utc)
        end = datetime(2024, 3, 31, 12, 0, tzinfo=timezone.utc)
        cli = count_samples(start, end, "days", 1, tz_str="Europe/Rome")
        factory = EphemerisDataFactory(
            start, end, step_type="days", step=1, tz_str="Europe/Rome"
        )
        factory.get_ephemeris_data(as_model=True)
        assert cli == len(factory.dates_list) == 2

    # subject_resolver: explicit --seconds 0 is forwarded to the factory rather
    # than dropped by `if seconds:` truthiness (latent today — the factory
    # default is 0 — but the codebase already fixed this antipattern for --step).
    def test_seconds_zero_is_forwarded_to_factory(self, monkeypatch):
        import inspect

        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.cli import subject_resolver as sr

        captured = {}
        # Preserve the real parameter names on the spy: _kwargs_for introspects
        # the factory signature on every call, so a bare (*args, **kwargs) spy
        # would make it filter "seconds" out before the call reaches the spy.
        real_params = list(
            inspect.signature(AstrologicalSubjectFactory.from_birth_data).parameters.values()
        )

        def _spy(*args, **kwargs):
            captured.update(kwargs)
            return object()  # only the forwarded kwargs matter here

        _spy.__signature__ = inspect.Signature(parameters=real_params)
        monkeypatch.setattr(AstrologicalSubjectFactory, "from_birth_data", _spy)
        flags = sr.build_flags(
            name="A", date="2000-01-01", time="12:30:45", seconds=0,
            iso_utc=None, lat=45.0, lng=9.0, tz="Europe/Rome", city=None,
            nation=None, online=None, offline=True, altitude=None, zodiac=None,
            sidereal_mode=None, houses=None, perspective=None, points=None,
            fixed_stars=None, with_flags=None, without_flags=None, set_flags=None,
        )
        sr.resolve_subject(flags, None)
        # Without the fix seconds=0 is dropped (absent); with it, forwarded as 0.
        assert captured.get("seconds") == 0

    # introspect: --param none / null maps to None, matching --set.
    def test_coerce_scalar_maps_none_to_None(self):
        from typing import Any

        from kerykeion.cli.introspect import coerce_value

        assert coerce_value(Any, "none") is None
        assert coerce_value(Any, "null") is None
        assert coerce_value(Any, "0") == 0


class TestFullPrReviewFixes:
    """Regressions from the xhigh review of the whole `feat/cli` PR."""

    # `Sequence[str]` params (MidpointFactory, SolarArcFactory, Heliacal…) were
    # unreachable: the origin is an ABC, so coercion fell through to "raw string"
    # and the factory rejected it. They coerce like a list now.
    def test_sequence_param_coerces_like_a_list(self):
        from typing import Optional, Sequence

        from kerykeion.cli.introspect import CLI, _classify, coerce_value

        assert coerce_value(Optional[Sequence[str]], "Sun,Moon") == ["Sun", "Moon"]
        # --explain must advertise it as usable from the CLI, not "json-only".
        assert _classify(Optional[Sequence[str]]) == CLI
        # A plain str is a Sequence too, but stays a scalar.
        assert coerce_value(str, "Sun,Moon") == "Sun,Moon"

    def test_call_binds_a_sequence_param(self, runner, app, ada_profile):
        r = runner.invoke(
            app,
            ["call", "MidpointFactory.compute", "-s", ada_profile,
             "--param", "active_points=Sun,Moon", "-f", "json"],
        )
        assert r.exit_code == 0, r.output
        assert json.loads(r.output)

    # House letters are case-SIGNIFICANT: 'i' (Sunshine/alt.) != 'I' (Sunshine).
    # Upper-casing every letter made 'i' unreachable and silently re-framed a
    # transit ring inheriting a natal 'i'.
    def test_house_letter_case_is_preserved_when_valid(self):
        from kerykeion.cli.subject_resolver import resolve_house_system

        assert resolve_house_system("i") == "i"
        assert resolve_house_system("I") == "I"
        # The convenience upper-casing survives for unambiguous letters.
        assert resolve_house_system("p") == "P"
        assert resolve_house_system("placidus") == "P"
        with pytest.raises(ValueError):
            resolve_house_system("G")

    # Bare ``@app.command`` (no parentheses) silently registered nothing and
    # rebound the module symbol to typer's decorator.
    def test_bare_command_decorator_registers(self):
        from kerykeion.cli.typer_app import KerykeionTyper

        t = KerykeionTyper()

        @t.command
        def hello() -> None: ...

        assert len(t.registered_commands) == 1
        assert hello.__name__ == "hello"

    # subject save is atomic: a failure mid-write must not destroy the profile
    # that was already on disk (it holds birth data and has no backup).
    def test_save_failure_leaves_the_previous_profile_intact(
        self, runner, app, ada_profile, monkeypatch, deterministic_cli_env
    ):
        from kerykeion.cli import config, profiles

        path = config.profile_path(ada_profile)
        original = path.read_text(encoding="utf-8")

        def boom(*a, **k):
            raise OSError("disk full")

        monkeypatch.setattr(profiles.os, "replace", boom)
        with pytest.raises(OSError):
            profiles.save(path, profiles.load(path))

        assert path.read_text(encoding="utf-8") == original
        # And no scratch file is left behind next to it.
        assert not list(path.parent.glob(".*.tmp"))

    # The store holds PII: BOTH the app dir and the subjects dir must be 0700.
    def test_profile_store_dirs_are_private(self, runner, app, ada_profile):
        from kerykeion.cli import config

        assert config.app_dir().stat().st_mode & 0o777 == 0o700
        assert config.profiles_dir().stat().st_mode & 0o777 == 0o700

    # --no-online was documented and implemented in the resolver, but typer was
    # never told to generate it, so the flag did not exist.
    def test_no_online_flag_exists(self, runner, app):
        r = runner.invoke(app, [
            "subject", "save", "bob", "--name", "Bob",
            "--date", "1990-01-01", "--time", "12:00",
            "--lat", "40.0", "--lng", "10.0", "--tz", "Europe/Rome", "--no-online",
        ])
        assert r.exit_code == 0, r.output

    # --online with --offline is contradictory; letting --online win silently
    # would geocode a subject the user asked to keep off the network.
    def test_online_and_offline_together_is_rejected(self, runner, app):
        r = runner.invoke(app, [
            "subject", "save", "clash", "--name", "C",
            "--date", "1990-01-01", "--time", "12:00",
            "--lat", "40.0", "--lng", "10.0", "--tz", "Europe/Rome",
            "--online", "--offline",
        ])
        assert r.exit_code == 4
        assert "mutually exclusive" in r.output

    # Enum-style flags follow the same case rule as --zodiac/--houses/--points.
    def test_enum_flags_are_case_insensitive(self, runner, app, ada_profile):
        assert runner.invoke(
            app, ["technique", "zr", "-s", ada_profile, "--lot", "Fortune", "-f", "json"]
        ).exit_code == 0
        assert runner.invoke(
            app, ["return", "-s", ada_profile, "--type", "solar", "--year", "2020", "-f", "json"]
        ).exit_code == 0

    # sky must not build (and discard) a subject when every coordinate is inline.
    def test_sky_skips_subject_build_when_fully_inline(self, monkeypatch, ada_profile):
        from kerykeion.cli import subject_resolver
        from kerykeion.cli.commands import sky

        def boom(*a, **k):  # pragma: no cover - must never run
            raise AssertionError("resolve_subject called despite complete inline coords")

        monkeypatch.setattr(subject_resolver, "resolve_subject", boom)
        assert sky._location(ada_profile, 40.0, 10.0, "Europe/Rome", "sun-times") == (
            40.0, 10.0, "Europe/Rome",
        )
        assert sky._latlng(ada_profile, 40.0, 10.0, "eclipses") == (40.0, 10.0)

    # The rendering helpers that bypassed -o and the warnings funnel are gone;
    # write_output/render are the only funnel.
    def test_stdout_bypassing_emitters_are_gone(self):
        from kerykeion.cli.rendering import emit, json_out, svg_out, text, xml_out

        assert not hasattr(emit, "emit")
        for module, name in (
            (json_out, "emit_json"), (text, "emit_text"),
            (xml_out, "emit_xml"), (svg_out, "emit_svg"),
        ):
            assert not hasattr(module, name), f"{name} should be deleted"
        assert hasattr(emit, "write_output") and hasattr(emit, "render")


@pytest.fixture
def bob_profile(runner, app):
    """A second stored subject, for the dual-wheel and two-subject commands."""
    result = runner.invoke(app, [
        "subject", "save", "bob",
        "--name", "Bob", "--date", "1985-06-01", "--time", "09:30",
        "--lat", "45.0", "--lng", "9.0", "--tz", "Europe/Rome", "--offline",
    ])
    assert result.exit_code == 0, result.output
    return "bob"


class TestRenderOptions:
    """The chart/report knobs: ChartDrawer's 20 parameters used to be unreachable."""

    def _svg(self, runner, app, tmp_path, name, *extra):
        target = tmp_path / f"{name}.svg"
        result = runner.invoke(
            app, ["natal", "-s", "ada", "-f", "svg", "-o", str(target), *extra]
        )
        assert result.exit_code == 0, result.output
        return target.read_text(encoding="utf-8")

    # Each flag must reach ChartDrawer and change the drawing. Asserting on the
    # rendered SVG (not on a spy) is what proves the whole chain is connected.
    @pytest.mark.parametrize("flags", [
        ["--theme", "dark"],
        ["--chart-language", "IT"],
        ["--style", "classic"],
        ["--transparent-background"],
        ["--custom-title", "ADA-XYZ"],
        ["--padding", "80"],
        ["--no-zodiac-ring"],
        ["--no-diurnality"],
        ["--no-auto-size"],
    ])
    def test_chart_flag_changes_the_svg(self, runner, app, ada_profile, tmp_path, flags):
        base = self._svg(runner, app, tmp_path, "base")
        assert self._svg(runner, app, tmp_path, "opt", *flags) != base

    # The classic-only knobs are inert under the default modern style — the
    # library says so on stderr — but must work when the style is classic.
    @pytest.mark.parametrize("flag", [
        "--no-degree-indicators", "--external-view", "--no-aspect-icons",
    ])
    def test_classic_only_flags_work_under_classic_style(
        self, runner, app, ada_profile, tmp_path, flag
    ):
        base = self._svg(runner, app, tmp_path, "classic", "--style", "classic")
        assert self._svg(runner, app, tmp_path, "opt", "--style", "classic", flag) != base

    def test_custom_title_lands_in_the_svg(self, runner, app, ada_profile, tmp_path):
        assert "ADA-XYZ" in self._svg(
            runner, app, tmp_path, "title", "--custom-title", "ADA-XYZ"
        )

    def test_svg_variants_render_different_drawings(self, runner, app, ada_profile, tmp_path):
        sizes = {
            variant: len(self._svg(runner, app, tmp_path, variant, "--svg-variant", variant))
            for variant in ("full", "wheel", "aspect-grid")
        }
        assert len(set(sizes.values())) == 3, sizes

    # Case-insensitive like every other enum flag; an unknown value is exit 4.
    @pytest.mark.parametrize("flags", [
        ["--theme", "DARK"], ["--chart-language", "it"], ["--style", "MODERN"],
    ])
    def test_chart_enums_are_case_insensitive(self, runner, app, ada_profile, tmp_path, flags):
        assert self._svg(runner, app, tmp_path, "ci", *flags)

    @pytest.mark.parametrize("flags", [
        ["--theme", "nope"], ["--svg-variant", "bogus"], ["--aspect-grid-type", "x"],
    ])
    def test_unknown_chart_value_is_invalid_input(
        self, runner, app, ada_profile, tmp_path, flags
    ):
        result = runner.invoke(
            app, ["natal", "-s", "ada", "-f", "svg", "-o", str(tmp_path / "x.svg"), *flags]
        )
        assert result.exit_code == 4
        assert "must be one of" in result.output

    # `style` is annotated with an unevaluated forward-ref in chart_drawer, so
    # reading the raw signature yields no choices and would reject everything.
    def test_chart_choices_resolve_forward_refs(self):
        from kerykeion.cli.rendering.options import chart_choices

        assert chart_choices("style") == ("classic", "modern")
        assert "dark" in chart_choices("theme")
        assert "IT" in chart_choices("chart_language")

    # Report knobs act where a report has aspects: the dual-wheel models.
    def test_report_knobs_shorten_the_report(self, runner, app, ada_profile, bob_profile):
        base = runner.invoke(app, ["synastry", "-s", "ada", "-S", "bob", "-f", "text"])
        trimmed = runner.invoke(
            app, ["synastry", "-s", "ada", "-S", "bob", "-f", "text", "--no-aspects"]
        )
        capped = runner.invoke(
            app, ["synastry", "-s", "ada", "-S", "bob", "-f", "text", "--max-aspects", "3"]
        )
        assert base.exit_code == trimmed.exit_code == capped.exit_code == 0
        assert len(trimmed.output) < len(base.output)
        assert len(capped.output) < len(base.output)

    # --envelope carries the warnings in-band for consumers that only read stdout.
    def test_envelope_wraps_without_changing_the_payload(self, runner, app, ada_profile):
        plain = runner.invoke(app, ["natal", "-s", "ada", "-f", "json"])
        wrapped = runner.invoke(app, ["natal", "-s", "ada", "-f", "json", "--envelope"])
        assert wrapped.exit_code == 0
        body = json.loads(wrapped.output)
        assert set(body) == {"kerykeion", "warnings", "data"}
        assert {"version", "backend", "generated_at"} <= set(body["kerykeion"])
        # The enveloped data must be exactly the un-enveloped payload.
        assert body["data"] == json.loads(plain.output)

    @pytest.mark.parametrize("fmt", ["text", "svg", "xml"])
    def test_envelope_outside_json_is_invalid_input(self, runner, app, ada_profile, tmp_path, fmt):
        result = runner.invoke(
            app,
            ["natal", "-s", "ada", "-f", fmt, "--envelope", "-o", str(tmp_path / f"o.{fmt}")],
        )
        assert result.exit_code == 4
        assert "--envelope" in result.output

    # A partial settings file must overlay the library defaults: replacing the
    # whole palette wholesale made ChartDrawer die on KeyError('zodiac_icon_0').
    def test_partial_chart_settings_merge_over_defaults(
        self, runner, app, ada_profile, tmp_path
    ):
        settings = tmp_path / "palette.json"
        settings.write_text(json.dumps({"colors_settings": {"paper_0": "#101010"}}))
        base = self._svg(runner, app, tmp_path, "plain")
        themed = self._svg(runner, app, tmp_path, "themed", "--chart-settings", str(settings))
        assert themed != base
        assert "#101010" in themed

    @pytest.mark.parametrize("body,needle", [
        ('{"colours": {}}', "unknown key"),
        ("[1, 2]", "must hold a JSON object"),
    ])
    def test_bad_chart_settings_are_named(
        self, runner, app, ada_profile, tmp_path, body, needle
    ):
        settings = tmp_path / "bad.json"
        settings.write_text(body)
        result = runner.invoke(
            app,
            ["natal", "-s", "ada", "-f", "svg", "-o", str(tmp_path / "x.svg"),
             "--chart-settings", str(settings)],
        )
        assert result.exit_code == 4
        assert needle in result.output

    # _render_from() reads the flags out of the caller's frame; the guard turns a
    # renamed/dropped parameter into a loud failure instead of a silent no-op.
    def test_render_from_rejects_a_missing_flag(self):
        from kerykeion.cli.commands._shared import _render_from

        with pytest.raises(AssertionError, match="absent from the command signature"):
            _render_from({"theme": "dark"})
