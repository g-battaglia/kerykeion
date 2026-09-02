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
* the runner drives ``main()`` in-process (counts toward coverage); a couple
  of cases it cannot demonstrate (the real entry point, ``import kerykeion``
  not importing the CLI) use a subprocess.
"""

from __future__ import annotations

import inspect
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
    """Isolate the terminal width and the profile store from the dev shell (argparse wraps help at COLUMNS)."""
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "dumb")
    monkeypatch.setenv("COLUMNS", "100")
    monkeypatch.setenv("LINES", "40")
    return tmp_path


class _Invocation:
    def __init__(self, exit_code: int, stdout: str, stderr: str) -> None:
        self.exit_code, self.stdout, self.stderr = exit_code, stdout, stderr
        self.output = stdout + stderr


class _Runner:
    """In-process ``main(argv)`` with captured streams, in the shape the tests were written against."""

    def invoke(self, _app, args):
        import contextlib
        import io

        from kerykeion.extra.cli import main

        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main(list(args)) or 0
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
        return _Invocation(code, out.getvalue(), err.getvalue())


@pytest.fixture
def runner(deterministic_cli_env):
    return _Runner()


@pytest.fixture
def app():
    return None  # the runner drives main(); kept so ``invoke(app, ...)`` reads as before


@pytest.fixture(autouse=True)
def _reset_cli_error_policy():
    """Reset the CLI's process-global error knobs around every test.

    ``--traceback`` and ``--warnings-as-errors`` set module globals in
    :mod:`kerykeion.extra.cli.errors` that nothing resets, so without this a
    test that escalates warnings leaks the policy into every
    later test in the same process — making the suite order-dependent. Reset
    before and after so each test starts and ends clean.
    """
    from kerykeion.extra.cli import errors

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
        assert "usage:" in r.output.lower()

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

    # Profiles written before 6.0.0a93 carry a ``snapshot`` key; they must still load.
    def test_profile_with_legacy_keys_still_loads(self, runner, app, ada_profile):
        from kerykeion.extra.cli import profiles

        path = profiles.profile_path(ada_profile)
        stored = json.loads(path.read_text(encoding="utf-8"))
        stored["snapshot"] = None
        path.write_text(json.dumps(stored), encoding="utf-8")
        r = runner.invoke(app, ["subject", "verify", ada_profile, "-f", "json"])
        assert r.exit_code == 0, r.output
        assert json.loads(r.output)["ok"] is True

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
        # 740 days > the 730-day ceiling; --no-limit lifts it so the series
        # actually computes instead of exiting 8.
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
        import kerykeion.extra.cli.registry as registry

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

    def test_import_kerykeion_does_not_load_the_cli(self):
        script = textwrap.dedent(
            """
            import sys
            import kerykeion
            assert "kerykeion.extra.cli" not in sys.modules, "kerykeion.extra.cli auto-imported"
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
        from kerykeion.extra.cli import rendering

        monkeypatch.setattr(rendering, "stdout_is_tty", lambda: True)
        assert rendering.resolve_format(None, None) == "text"
        monkeypatch.setattr(rendering, "stdout_is_tty", lambda: False)
        assert rendering.resolve_format(None, None) == "json"


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


# ── kerykeion status (diagnostics) ───────────────────────────────────────────


class TestStatus:
    """``kerykeion status`` reports runtime backend/ephemeris state."""

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
        from kerykeion.extra.cli import introspect, registry

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
        from kerykeion.extra.cli import profiles

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
        from kerykeion.extra.cli import rendering as _emit
        from kerykeion.extra.cli import errors, warnings

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
        from kerykeion.extra.cli import errors

        try:
            from libephemeris import EphemerisRangeError
        except ImportError:
            pytest.skip("libephemeris not installed")
        errors._backend_types = None  # rebuild the cached tuple for this test
        try:
            assert errors.classify(EphemerisRangeError("out of range")) is errors.ExitCode.EPHEMERIS
        finally:
            errors._backend_types = None  # rebuild normally afterwards

    # F11: main(argv) must honor an explicit argv over sys.argv.
    def test_main_honors_explicit_argv(self, monkeypatch):
        from kerykeion.extra.cli import main

        # If argv were ignored, the parser would see this bogus command line and
        # exit 2 (unknown command). A 0 means the explicit argv won.
        monkeypatch.setattr(sys, "argv", ["kerykeion", "definitely-not-a-command"])
        with pytest.raises(SystemExit) as ei:
            main(["--version"])
        assert ei.value.code == 0

    # F7: -o files keep LF endings on every platform (no CRLF translation), so
    # byte-exact JSON/SVG survives a Windows save for jq/diff.
    def test_output_file_uses_lf(self, tmp_path):
        from kerykeion.extra.cli.rendering import write_output

        out = tmp_path / "o.json"
        write_output("a\nb", str(out))
        assert out.read_bytes() == b"a\nb\n"

    # F6: a saved profile is UTF-8 with LF endings and round-trips, even with a
    # non-ASCII name (the Windows cp1252 default would otherwise raise).
    def test_profile_save_is_utf8_lf_and_round_trips(self, runner, app, deterministic_cli_env):
        from kerykeion.extra.cli import profiles

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
        from kerykeion.extra.cli.subject_resolver import resolve_house_system

        assert resolve_house_system("porphyry") == "O"
        assert resolve_house_system("porphyrius") == "O"
        assert resolve_house_system("apc") == "Y"
        assert resolve_house_system("placidus") == "P"  # unchanged sanity check

    # #6: an unknown single letter is rejected here with a helpful message, not
    # deferred to a confusing pydantic "input does not match the literal".
    def test_unknown_house_letter_is_rejected_cleanly(self):
        from kerykeion.extra.cli.subject_resolver import resolve_house_system

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
        from kerykeion.extra.cli import profiles

        # Persist a Sidereal profile into the isolated store.
        profiles.save(
            profiles.profile_path("cyb"),
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
            from kerykeion.extra.cli import main
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
        from kerykeion.extra.cli.introspect import coerce_value

        assert coerce_value(dict, '{"sun": 1.5}') == {"sun": 1.5}
        with pytest.raises(ValueError):
            coerce_value(dict, "not json")

    # #11: emit_warnings resolves sys.stderr at call time so a redirected stderr
    # (CliRunner, capsys, an embedding host) actually captures the warnings.
    def test_emit_warnings_honors_redirected_stderr(self, monkeypatch):
        import io

        from kerykeion.extra.cli import warnings as _w

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
        from kerykeion.extra.cli.rendering import write_output

        out = tmp_path / "new" / "deep" / "o.json"
        write_output("{}", str(out))
        assert out.read_text() == "{}\n"

    # #13: a lookup miss for -s must not create the profile store as a side
    # effect of gathering "did you mean" suggestions.
    def test_resolve_path_does_not_create_store_on_miss(self, deterministic_cli_env, monkeypatch):
        from kerykeion.extra.cli import profiles

        store = profiles.profiles_dir()
        assert not store.exists()
        with pytest.raises(profiles.ProfileNotFound):
            profiles.resolve_path("nonexistent")
        # Still absent: the read-only lookup did not mkdir anything.
        assert not store.exists()

    # #15: commands that render a derivative of a subject still surface (and can
    # escalate via --warnings-as-errors) the warnings carried on that subject.
    def test_output_with_warnings_collects_from_warning_source(self, monkeypatch):
        import io

        from kerykeion.extra.cli import warnings as _w

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
        from kerykeion.extra.cli.commands.sky import _location

        # ada is London (51.5074 / -0.1278); inline 40 / 10 wins.
        assert _location(ada_profile, 40.0, 10.0, "Europe/Rome", "t") == (
            40.0, 10.0, "Europe/Rome",
        )
        # The timezone-free form (eclipses, occultations) resolves the same way.
        assert _location(ada_profile, 40.0, 10.0, None, "t", require_tz=False)[:2] == (
            40.0, 10.0,
        )
        # Without inline flags the profile is used.
        lat, _lng, _tz = _location(ada_profile, None, None, None, "t")
        assert abs(lat - 51.5074) < 1e-3

    # sky voc range: --tz is honoured by attaching the zone's offset to naive
    # bounds (from_iso_range is UTC-only).
    def test_sky_attach_tz_offset_for_naive_bound(self):
        from kerykeion.extra.cli.commands.sky import _attach_tz_offset

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
        from kerykeion.extra.cli.warnings import collect_warnings

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

        from kerykeion.extra.cli.introspect import coerce_value

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
        from kerykeion.extra.cli.introspect import _classify, _is_subject, _strip_optional

        assert _strip_optional(int | None) is int
        assert _classify(int | str | None) == "cli"
        # A PEP 604 subject union is recognised as a subject binding site.
        assert _is_subject(AstrologicalSubjectModel | None) is True

    # series: mixed offset-aware/naive bounds are refused as invalid input.
    def test_mixed_awareness_bounds_are_invalid_input(self, runner, app):
        r = runner.invoke(
            app,
            ["ephemeris", "--lat", "0", "--lng", "0", "--tz", "UTC",
             "--from", "2024-01-01", "--to", "2024-01-03T00:00+00:00"],
        )
        assert r.exit_code == 4
        assert "same ISO form" in r.output

    # sky: --zodiac accepts the casing the library accepts.
    def test_zodiac_kwargs_case_insensitive(self):
        from kerykeion.extra.cli.commands.sky import _zodiac_kwargs

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
        from kerykeion.extra.cli.commands.sky import _moment

        # 2024-10-27 01:30 UTC = 02:30 Europe/Rome, the second (CET/fold=1) reading.
        with pytest.raises(ValueError, match="ambiguous wall time"):
            _moment("2024-10-27T01:30:00+00:00", "hours", "Europe/Rome")

    # subject_resolver: explicit --seconds 0 is forwarded to the factory rather
    # than dropped by `if seconds:` truthiness (latent today — the factory
    # default is 0 — but the codebase already fixed this antipattern for --step).
    def test_seconds_zero_is_forwarded_to_factory(self, monkeypatch):
        import inspect

        from kerykeion import AstrologicalSubjectFactory
        from kerykeion.extra.cli import subject_resolver as sr

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
        flags = sr.SubjectFlags(
            name="A", date="2000-01-01", time="12:30:45", seconds=0,
            lat=45.0, lng=9.0, tz="Europe/Rome", offline=True,
        )
        sr.resolve_subject(flags, None)
        # Without the fix seconds=0 is dropped (absent); with it, forwarded as 0.
        assert captured.get("seconds") == 0

    # introspect: --param none / null maps to None, matching --set.
    def test_coerce_scalar_maps_none_to_None(self):
        from typing import Any

        from kerykeion.extra.cli.introspect import coerce_value

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

        from kerykeion.extra.cli.introspect import CLI, _classify, coerce_value

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
        from kerykeion.extra.cli.subject_resolver import resolve_house_system

        assert resolve_house_system("i") == "i"
        assert resolve_house_system("I") == "I"
        # The convenience upper-casing survives for unambiguous letters.
        assert resolve_house_system("p") == "P"
        assert resolve_house_system("placidus") == "P"
        with pytest.raises(ValueError):
            resolve_house_system("G")

    # subject save is atomic: a failure mid-write must not destroy the profile
    # that was already on disk (it holds birth data and has no backup).
    def test_save_failure_leaves_the_previous_profile_intact(
        self, runner, app, ada_profile, monkeypatch, deterministic_cli_env
    ):
        from kerykeion.extra.cli import profiles

        path = profiles.profile_path(ada_profile)
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
        from kerykeion.extra.cli import profiles

        assert profiles.app_dir().stat().st_mode & 0o777 == 0o700
        assert profiles.profiles_dir().stat().st_mode & 0o777 == 0o700

    # --no-online was documented and implemented in the resolver, but the parser was
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
        from kerykeion.extra.cli import subject_resolver
        from kerykeion.extra.cli.commands import sky

        def boom(*a, **k):  # pragma: no cover - must never run
            raise AssertionError("resolve_subject called despite complete inline coords")

        monkeypatch.setattr(subject_resolver, "resolve_subject", boom)
        assert sky._location(ada_profile, 40.0, 10.0, "Europe/Rome", "sun-times") == (
            40.0, 10.0, "Europe/Rome",
        )
        assert sky._location(ada_profile, 40.0, 10.0, None, "eclipses", require_tz=False)[
            :2
        ] == (40.0, 10.0)

    # The rendering helpers that bypassed -o and the warnings funnel are gone;
    # write_output/render are the only funnel.
    def test_stdout_bypassing_emitters_are_gone(self):
        from kerykeion.extra.cli import rendering

        assert not [name for name in dir(rendering) if name.startswith("emit")]


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
        from kerykeion.extra.cli.render_options import chart_choices

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

    # @with_render_flags marks the commands whose parser declares the shared
    # knobs, so every chart command must actually offer all of them. A knob added to the
    # table but not reaching the commands is the silent no-op this guards.
    @pytest.mark.parametrize(
        "command",
        ["natal", "now", "synastry", "transit", "composite", "return", "progression",
         "technique relocate"],
    )
    def test_every_chart_command_exposes_the_render_flags(self, runner, app, command):
        from kerykeion.extra.cli.commands._shared import _RENDER_FLAGS

        result = runner.invoke(app, [*command.split(), "--help"])
        assert result.exit_code == 0
        rendered = " ".join(result.output.split())
        for flag in _RENDER_FLAGS:
            assert f"--{flag.replace('_', '-')}" in rendered, f"{command} is missing --{flag}"

    # The marked command receives the assembled RenderOptions as `opts`; the
    # flags themselves are declared by the parser and never reach its signature.
    def test_render_flags_reach_the_command_as_options(self):
        from kerykeion.extra.cli.commands import charts

        parameters = inspect.signature(charts.natal).parameters
        assert "opts" in parameters
        assert "theme" not in parameters
        assert charts.natal.render_flags is True


class TestCuratedCommands:
    """Every public factory now has a command; `call` stays the universal valve."""

    @pytest.mark.parametrize("args", [
        ["aspects", "-s", "ada"],
        ["aspects", "-s", "ada", "-S", "bob"],
        ["aspects", "-s", "ada", "--declinations"],
        ["aspects", "-s", "ada", "--aspects", "trine:6,square"],
        ["dominants", "-s", "ada"],
        ["dominants", "-s", "ada", "--method", "almuten_figuris"],
        ["moon", "-s", "ada"],
        ["relationship-score", "-s", "ada", "-S", "bob"],
        ["technique", "house-comparison", "-s", "ada", "-S", "bob"],
        ["technique", "solar-arc", "-s", "ada", "--target-year", "2026"],
        ["technique", "fixed-stars", "-s", "ada", "--orb", "1.5"],
        ["sky", "mundane", "--from", "2025-01-01", "--to", "2025-02-01"],
        ["sky", "lunations", "--from", "2025-01-01", "--to", "2025-02-01"],
        ["sky", "ingresses", "--from", "2025-01-01", "--to", "2025-02-01", "--planets", "Sun"],
        ["sky", "ingresses", "--from", "2025-01-01", "--to", "2025-02-01", "--planets", "Sun", "--periods"],
        ["sky", "stations", "--from", "2025-01-01", "--to", "2025-04-01", "--planets", "Mercury"],
        ["sky", "stations", "--from", "2025-01-01", "--to", "2025-04-01", "--planets", "Mercury", "--periods"],
        ["sky", "phenomena", "-s", "ada"],
        ["sky", "occultations", "-s", "ada", "--planet", "Venus", "--count", "2"],
    ])
    def test_command_produces_json(self, runner, app, ada_profile, bob_profile, args):
        result = runner.invoke(app, [*args, "-f", "json"])
        assert result.exit_code == 0, result.output
        assert json.loads(result.output) is not None

    # The declination variants take (subject, active_points, orb) — no
    # active_aspects, no axis_orb_limit. Forwarding those crashed the factory.
    def test_declination_aspects_take_a_single_orb(self, runner, app, ada_profile):
        assert runner.invoke(
            app, ["aspects", "-s", "ada", "--declinations", "--orb", "1.5", "-f", "json"]
        ).exit_code == 0

    @pytest.mark.parametrize("flags,needle", [
        (["--declinations", "--aspects", "trine:6"], "--aspects does not apply"),
        (["--declinations", "--axis-orb-limit", "2"], "--axis-orb-limit does not apply"),
        (["--orb", "1.5"], "--orb applies to --declinations"),
    ])
    def test_mismatched_aspect_options_are_refused(
        self, runner, app, ada_profile, flags, needle
    ):
        result = runner.invoke(app, ["aspects", "-s", "ada", *flags])
        assert result.exit_code == 4
        assert needle in result.output

    def test_dominants_method_is_validated_against_the_library(self, runner, app, ada_profile):
        result = runner.invoke(app, ["dominants", "-s", "ada", "--method", "nope"])
        assert result.exit_code == 4
        assert "--method must be one of" in result.output

    def test_relationship_score_needs_both_subjects(self, runner, app, ada_profile):
        result = runner.invoke(app, ["relationship-score", "-s", "ada"])
        assert result.exit_code == 4
        assert "-S" in result.output

    # Occultations search from a Julian day and the Moon is the occulter, so
    # there is no sensible default body: it must be asked for.
    def test_occultations_require_a_planet(self, runner, app, ada_profile):
        result = runner.invoke(app, ["sky", "occultations", "-s", "ada"])
        assert result.exit_code == 4
        assert "--planet" in result.output


class TestPeriodQueries:
    """``--periods`` reaches the a92 span queries, not a filtered event scan."""

    def test_ingress_periods_match_the_factory(self, runner, app):
        from kerykeion import SignIngressFactory

        result = runner.invoke(app, [
            "sky", "ingresses", "--from", "2025-01-01", "--to", "2025-02-01",
            "--planets", "Sun,Mercury", "--periods", "-f", "json",
        ])
        assert result.exit_code == 0, result.output
        expected = SignIngressFactory.sign_periods_from_iso_range("2025-01-01", "2025-02-01", planets=["Sun", "Mercury"])
        assert json.loads(result.output) == json.loads(expected.model_dump_json())
        assert json.loads(result.output)["periods"], "a month of Sun and Mercury has at least one sign stay"

    def test_station_periods_match_the_factory(self, runner, app):
        from kerykeion import RetrogradeStationFactory

        result = runner.invoke(app, [
            "sky", "stations", "--from", "2025-01-01", "--to", "2025-04-01",
            "--planets", "Mercury", "--periods", "-f", "json",
        ])
        assert result.exit_code == 0, result.output
        expected = RetrogradeStationFactory.retrograde_periods_from_iso_range("2025-01-01", "2025-04-01", planets=["Mercury"])
        assert json.loads(result.output) == json.loads(expected.model_dump_json())


class TestAspectsFlagHasOneMeaning:
    """`--aspects` used to mean angle-names on one command and nothing elsewhere."""

    def test_name_and_name_with_orb_both_parse(self):
        from kerykeion.extra.cli.commands._shared import _active_aspects, _parse_aspects

        parsed = _parse_aspects(["trine:6", "square"])
        assert parsed == [("trine", 6.0), ("square", None)]
        # An omitted orb takes the library's own default for that aspect.
        from kerykeion.settings import config_constants as cc

        defaults = {entry["name"]: entry["orb"] for entry in cc.ALL_ACTIVE_ASPECTS}
        assert _active_aspects(parsed) == [
            {"name": "trine", "orb": 6.0},
            {"name": "square", "orb": defaults["square"]},
        ]

    def test_a_non_numeric_orb_is_named(self):
        from kerykeion.extra.cli.commands._shared import _parse_aspects

        with pytest.raises(ValueError, match="is not a number for the orb"):
            _parse_aspects(["trine:wide"])

    # The factories that take plain names must refuse an orb instead of dropping
    # it — a silently ignored orb is the failure mode this shared parser avoids.
    def test_orb_is_refused_where_it_cannot_be_used(self):
        from kerykeion.extra.cli.commands._shared import _aspect_names, _parse_aspects

        assert _aspect_names(_parse_aspects(["trine", "square"]), "mundane") == [
            "trine", "square",
        ]
        with pytest.raises(ValueError, match="without an orb"):
            _aspect_names(_parse_aspects(["trine:6"]), "mundane")

    def test_directions_still_validates_its_angles(self, runner, app, ada_profile):
        result = runner.invoke(
            app, ["technique", "directions", "-s", "ada", "--aspects", "nonsense"]
        )
        assert result.exit_code == 4
        assert "--aspects must be one of" in result.output


class TestInfoAndChecks:
    """The CLI can list what it validates against, and judge its own install."""

    def test_literals_are_derived_from_the_library(self, runner, app):
        import typing

        from kerykeion.schemas import literals as lib

        result = runner.invoke(app, ["info", "literals", "-f", "json"])
        assert result.exit_code == 0, result.output
        tables = json.loads(result.output)
        # Read from the source of truth, never transcribed: compare to the library.
        assert tables["HousesSystemIdentifier"] == list(
            typing.get_args(lib.HousesSystemIdentifier)
        )
        assert tables["SiderealMode"] == list(typing.get_args(lib.SiderealMode))
        assert len(tables["SiderealMode"]) > 40

    def test_a_single_literal_can_be_named_case_insensitively(self, runner, app):
        result = runner.invoke(
            app, ["info", "literals", "housessystemidentifier", "-f", "json"]
        )
        assert result.exit_code == 0, result.output
        assert list(json.loads(result.output)) == ["HousesSystemIdentifier"]

    def test_an_unknown_literal_suggests_and_exits_four(self, runner, app):
        result = runner.invoke(app, ["info", "literals", "HouseSystem"])
        assert result.exit_code == 4
        assert "no literal named" in result.output

    # info must describe what the flags actually accept, so it is read from the
    # resolver's own tables rather than a copy.
    def test_points_and_stars_match_the_resolver(self, runner, app):
        from kerykeion.extra.cli import subject_resolver

        points = json.loads(runner.invoke(app, ["info", "points", "-f", "json"]).output)
        stars = json.loads(runner.invoke(app, ["info", "stars", "-f", "json"]).output)
        assert points == subject_resolver._point_sets()
        assert stars == subject_resolver._fixed_star_sets()

    def test_houses_lists_both_letters_and_names(self, runner, app):
        body = json.loads(runner.invoke(app, ["info", "houses", "-f", "json"]).output)
        # Case matters: 'i' and 'I' are different systems and both must show.
        assert "i" in body["letters"] and "I" in body["letters"]
        assert body["names"]["placidus"] == "P"

    def test_methods_reports_the_library_strategies(self, runner, app):
        from kerykeion import DominantsFactory

        body = json.loads(runner.invoke(app, ["info", "methods", "-f", "json"]).output)
        assert body["dominants_method"] == list(DominantsFactory.available_methods())

    def test_status_check_passes_on_a_working_install(self, runner, app):
        result = runner.invoke(app, ["status", "--check", "--json"])
        assert result.exit_code == 0, result.output
        body = json.loads(result.output)
        assert body["ok"] is True
        names = {c["check"] for c in body["checks"]}
        assert {"backend", "ephemeris data", "sample calculation"} <= names

    def test_status_check_text_is_readable_not_json(self, runner, app):
        result = runner.invoke(app, ["status", "--check"])
        assert result.exit_code == 0
        assert "All checks passed." in result.output
        assert not result.output.lstrip().startswith("{")

    # This is what separates --check from a plain status: it judges, and says so.
    def test_status_check_fails_when_a_calculation_raises(self, runner, app, monkeypatch):
        import kerykeion

        def boom(*args, **kwargs):
            raise RuntimeError("ephemeris unreachable")

        monkeypatch.setattr(
            kerykeion.AstrologicalSubjectFactory, "from_birth_data", staticmethod(boom)
        )
        result = runner.invoke(app, ["status", "--check", "--json"])
        assert result.exit_code == 6
        body = json.loads(result.output)
        assert body["ok"] is False
        assert any(c["status"] == "fail" for c in body["checks"])
        # a plain status only reports, so it stays green on the same broken install.
        assert runner.invoke(app, ["status", "--json"]).exit_code == 0


class TestFourthReviewPass:
    """Regressions from the fourth code-review sweep (feat/cli vs alpha/v6).

    Every finding was reproduced on a live interpreter before the fix; these
    pin the fixed behaviour. Numbering mirrors the review's report.
    """

    @staticmethod
    def _save_profile(store_name: str, **recipe):
        from kerykeion.extra.cli import profiles

        base = dict(
            name=store_name.capitalize(), mode="birth",
            date="2000-01-01", time="12:00",
            lat=0.0, lng=0.0, tz_str="UTC", online=False,
        )
        base.update(recipe)
        profiles.save(
            profiles.profile_path(store_name),
            profiles.Profile(
                name=base["name"],
                input=profiles.ProfileInput(**base),
                meta=profiles.make_meta(),
            ),
        )

    @staticmethod
    def _run_cli(args: list[str], env_root) -> "subprocess.CompletedProcess[str]":
        # {args!r} is a flat list literal, so `+` splices it after the prog name.
        script = textwrap.dedent(f"""
            import sys
            from kerykeion.extra.cli import main
            sys.argv = ["kerykeion"] + {args!r}
            sys.exit(main())
        """)
        env = {
            **os.environ, "XDG_CONFIG_HOME": str(env_root),
            "NO_COLOR": "1", "TERM": "dumb",
        }
        # Force the offline default-geo fallback: a developer's GEONAMES
        # username would turn this test into a network call.
        env.pop("KERYKEION_GEONAMES_USERNAME", None)
        return subprocess.run(
            [sys.executable, "-c", script], env=env, capture_output=True, text=True,
        )

    # #1: `transit --city X --online` used to inherit the natal coordinates,
    # which satisfied the factory's geocode gate — the wheel stayed cast for
    # the natal birthplace (London) while the requested city (Paris) appeared
    # as a display label.
    def test_transit_city_geocodes_instead_of_inheriting(self, deterministic_cli_env):
        self._save_profile(
            "geosrc", lat=51.5074, lng=-0.1278, tz_str="Europe/London",
        )
        out = deterministic_cli_env / "transit_geo.json"
        res = self._run_cli(
            ["transit", "-s", "geosrc", "--city", "Paris", "--nation", "FR",
             "--online", "-f", "json", "-o", str(out)],
            deterministic_cli_env,
        )
        assert res.returncode == 0, res.stderr

        geo: list[tuple[float, str]] = []

        def _walk(node):
            if isinstance(node, dict):
                if "lat" in node and "tz_str" in node:
                    geo.append((node["lat"], node["tz_str"]))
                for value in node.values():
                    _walk(value)
            elif isinstance(node, list):
                for value in node:
                    _walk(value)

        _walk(json.loads(out.read_text(encoding="utf-8")))
        paris = [lat for lat, tz in geo if tz == "Europe/Paris"]
        assert paris and any(abs(lat - 48.85) < 0.1 for lat in paris), geo

    # …and a city cannot be resolved against an explicit --offline: refusing
    # beats silently stamping the label over the natal birthplace.
    def test_transit_city_with_offline_is_rejected(self, runner, app, ada_profile):
        r = runner.invoke(app, ["transit", "-s", "ada", "--city", "Paris", "--offline"])
        assert r.exit_code == 4
        assert "--offline" in r.output

    # #2: USER-ayanamsa profiles crashed only on transit/transits — the custom
    # pair was not inherited with the rest of the natal frame, so a Sidereal
    # USER rebuild had no numbers to work with.
    def test_transit_with_user_ayanamsa_profile(self, deterministic_cli_env):
        self._save_profile(
            "useray", zodiac_type="Sidereal", sidereal_mode="USER",
            custom_ayanamsa_t0=2451545.0, custom_ayanamsa_ayan_t0=23.85,
        )
        out = deterministic_cli_env / "useray_transit.json"
        res = self._run_cli(
            ["transit", "-s", "useray", "-f", "json", "-o", str(out)],
            deterministic_cli_env,
        )
        assert res.returncode == 0, res.stderr

    def test_transits_series_with_user_ayanamsa_profile(self, deterministic_cli_env):
        # Not CliRunner: the series command emits a sampling warning via logging
        # mid-run, and under ``log_cli`` pytest's live handler suspends the global
        # capture — whose suspend closes whatever sys.stdout currently is, i.e.
        # typer's own stream (pytest/pytest#12658 territory). A subprocess with
        # ``-o`` sidesteps the whole interaction, like the transit test above.
        self._save_profile(
            "useray", zodiac_type="Sidereal", sidereal_mode="USER",
            custom_ayanamsa_t0=2451545.0, custom_ayanamsa_ayan_t0=23.85,
        )
        out = deterministic_cli_env / "useray_transits.json"
        res = self._run_cli(
            ["transits", "-s", "useray",
             "--from", "2025-01-01", "--to", "2025-01-02", "-f", "json", "-o", str(out)],
            deterministic_cli_env,
        )
        assert res.returncode == 0, res.stderr
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["transits"], "the series must have sampled its range"

    # #3: a partial --lat/--lng/--tz group used to silently blend the user's
    # values with the geocoded Greenwich defaults (their latitude, Greenwich's
    # longitude and timezone).
    def test_partial_coordinate_group_is_rejected(self, runner, app):
        r = runner.invoke(app, [
            "natal", "--name", "T", "--date", "2000-01-01", "--time", "12:00",
            "--lat", "40.7", "-f", "json",
        ])
        assert r.exit_code == 4
        assert "all-or-nothing" in r.output

    # #4: a fully specified relocated return (--lat/--lng/--tz + --online) was
    # rejected with "needs --city": the geocode requirement was checked before
    # the complete-coordinates branch.
    def test_return_online_with_full_coordinates(self, runner, app, ada_profile):
        r = runner.invoke(app, [
            "return", "-s", "ada", "--year", "2030",
            "--lat", "40.7", "--lng", "-74", "--tz", "America/New_York", "--online",
        ])
        assert r.exit_code == 0, r.output

    # #5: a profile named foo.json was stored as foo.json.json and listed as
    # "foo.json" — a name -s can never load, because any .json spec resolves
    # as a file path first.
    def test_subject_save_rejects_json_suffix(self, runner, app):
        r = runner.invoke(app, [
            "subject", "save", "foo.json", "--name", "F",
            "--date", "2000-01-01", "--time", "12:00",
            "--lat", "0", "--lng", "0", "--tz", "UTC",
        ])
        assert r.exit_code == 4
        assert "cannot end in '.json'" in r.output

    # #6: enum-shaped flag typos must be invalid input (exit 4) like every
    # other bad flag, not kerykeion-level errors (exit 5) that pipeline
    # branching cannot distinguish from library bugs.
    def test_sidereal_mode_is_canonicalised(self):
        from kerykeion.extra.cli.subject_resolver import resolve_sidereal_mode

        assert resolve_sidereal_mode("lahiri") == "LAHIRI"
        assert resolve_sidereal_mode("USER") == "USER"
        with pytest.raises(ValueError) as ei:
            resolve_sidereal_mode("lahari")
        assert "LAHIRI" in str(ei.value)  # the difflib hint points at the fix

    def test_perspective_is_canonicalised(self):
        from kerykeion.extra.cli.subject_resolver import resolve_perspective

        assert resolve_perspective("apparent geocentric") == "Apparent Geocentric"
        assert resolve_perspective("Topocentric") == "Topocentric"
        assert resolve_perspective("true-geocentric") == "True Geocentric"
        with pytest.raises(ValueError) as ei:
            resolve_perspective("apparent")
        assert "Apparent Geocentric" in str(ei.value)

    def test_sidereal_mode_typo_is_exit_four(self, runner, app):
        r = runner.invoke(app, [
            "natal", "--name", "T", "--date", "2000-01-01", "--time", "12:00",
            "--lat", "0", "--lng", "0", "--tz", "UTC",
            "--zodiac", "Sidereal", "--sidereal-mode", "lahari", "-f", "text",
        ])
        assert r.exit_code == 4
        assert "sidereal mode" in r.output

    def test_axis_orb_limit_zero_is_exit_four(self, runner, app, ada_profile):
        r = runner.invoke(app, ["aspects", "-s", "ada", "--axis-orb-limit", "0"])
        assert r.exit_code == 4
        assert "positive" in r.output

    # #7: the CLI skill's bash-block gate must run from the aggregate gates —
    # a broken example would otherwise ship verified-by-nothing while
    # `poe check` and `poe quality` stay green.
    def test_skill_cli_bash_gate_is_wired_into_the_aggregates(self):
        import re
        from pathlib import Path

        repo = Path(__file__).resolve().parents[2]
        pyproject = (repo / "pyproject.toml").read_text(encoding="utf-8")
        sequence = re.search(r"^sequence = \[(.*?)\]", pyproject, re.MULTILINE | re.DOTALL)
        assert sequence and '"skill:cli:smoke"' in sequence.group(1), (
            "skill:cli:smoke must stay in the `poe check` sequence"
        )
        quality = (repo / "scripts" / "quality_check.py").read_text(encoding="utf-8")
        assert "test_skill_cli_snippets.py" in quality, (
            "`poe quality` must run the CLI skill's bash gate too"
        )

    # #8: a consumer closing the pipe (`… | head`) is a benign truncation:
    # exit 0, not "invalid input" (4) with a broken-pipe message.
    def test_broken_pipe_is_a_benign_truncation(self, monkeypatch):
        from kerykeion.extra.cli import errors

        assert errors.classify(BrokenPipeError()) == errors.ExitCode.OK
        # Neutralise the stdout-to-devnull redirect: the real one would point
        # this pytest process's fd 1 at devnull for every later test.
        monkeypatch.setattr(errors.os, "dup2", lambda *a: None)
        with pytest.raises(SystemExit) as ei:
            errors.handle_uncaught(BrokenPipeError())
        assert ei.value.code == 0


class TestFifthReviewPass:
    """Regressions from the fifth code-review sweep (lens: cross-command
    consistency of the fourth pass's relocation fixes).

    The sweep found `return --city` silently ignored (recast at the natal
    birthplace) whenever --online was not explicit — the same label-over-place
    bug the fourth pass had just fixed in `transit` — plus two contract gaps:
    `--city --offline` exited 5 on `natal`/`now`/`save` but 4 on `transit`, and
    `--city` mixed with `--lat/--lng/--tz` silently picked one place on every
    command.
    """

    # #1: `return --city Paris` (no --online) used to ignore the city and cast
    # the return at the natal birthplace — exit 0, London houses, Paris label.
    def test_return_city_geocodes_without_explicit_online(self, deterministic_cli_env):
        TestFourthReviewPass._save_profile(
            "geosrc", lat=51.5074, lng=-0.1278, tz_str="Europe/London",
        )
        out = deterministic_cli_env / "return_geo.json"
        res = TestFourthReviewPass._run_cli(
            ["return", "-s", "geosrc", "--year", "2030",
             "--city", "Paris", "--nation", "FR", "-f", "json", "-o", str(out)],
            deterministic_cli_env,
        )
        assert res.returncode == 0, res.stderr

        geo: list[tuple[float, str]] = []

        def _walk(node):
            if isinstance(node, dict):
                if "lat" in node and "tz_str" in node:
                    geo.append((node["lat"], node["tz_str"]))
                for value in node.values():
                    _walk(value)
            elif isinstance(node, list):
                for value in node:
                    _walk(value)

        _walk(json.loads(out.read_text(encoding="utf-8")))
        paris = [lat for lat, tz in geo if tz == "Europe/Paris"]
        assert paris and any(abs(lat - 48.85) < 0.1 for lat in paris), geo

    # …and the city must be honoured or refused, never dropped: --offline
    # cannot geocode, so exit 4 with the fix instead of a silent birthplace.
    def test_return_city_with_offline_is_exit_four(self, runner, app, ada_profile):
        r = runner.invoke(app, ["return", "-s", "ada", "--year", "2030", "--city", "Paris", "--offline"])
        assert r.exit_code == 4
        assert "cannot be resolved with --offline" in r.output

    # #2: a city and explicit coordinates are two answers to one question —
    # `return` used to drop the coordinates' rival silently (and `transit` the
    # city's). One command, one place: refuse the mix everywhere.
    def test_return_city_and_coordinates_is_exit_four(self, runner, app, ada_profile):
        r = runner.invoke(app, [
            "return", "-s", "ada", "--year", "2030", "--city", "Paris",
            "--lat", "40.7", "--lng", "-74", "--tz", "America/New_York",
        ])
        assert r.exit_code == 4
        assert "not both" in r.output

    def test_transit_city_and_coordinates_is_exit_four(self, runner, app, ada_profile):
        r = runner.invoke(app, [
            "transit", "-s", "ada", "--city", "Paris",
            "--lat", "40.7", "--lng", "-74", "--tz", "America/New_York", "--online",
        ])
        assert r.exit_code == 4
        assert "not both" in r.output

    def test_natal_city_and_coordinates_is_exit_four(self, runner, app):
        r = runner.invoke(app, [
            "natal", "--name", "T", "--date", "2000-01-01", "--time", "12:00",
            "--city", "Paris", "--lat", "0", "--lng", "0", "--tz", "UTC", "--online",
        ])
        assert r.exit_code == 4
        assert "not both" in r.output

    # #3: `--city --offline` used to exit 5 (a kerykeion-level error from the
    # factory) on natal/now/save while transit exited 4 — the same mistake with
    # two different codes breaks the documented contract for pipeline branching.
    def test_natal_city_with_offline_is_exit_four(self, runner, app):
        r = runner.invoke(app, [
            "natal", "--name", "T", "--date", "2000-01-01", "--time", "12:00",
            "--city", "Paris", "--nation", "FR", "--offline", "-f", "json",
        ])
        assert r.exit_code == 4
        assert "cannot be resolved with --offline" in r.output

    def test_now_city_with_offline_is_exit_four(self, runner, app):
        r = runner.invoke(app, ["now", "--city", "Paris", "--nation", "FR", "--offline"])
        assert r.exit_code == 4
        assert "cannot be resolved with --offline" in r.output

    def test_subject_save_city_with_offline_is_exit_four(self, runner, app):
        # Fails at the keyboard, not at the first `-s` read: an offline recipe
        # with a city can never materialise.
        r = runner.invoke(app, [
            "subject", "save", "x", "--name", "X",
            "--date", "2000-01-01", "--time", "12:00",
            "--city", "Paris", "--offline",
        ])
        assert r.exit_code == 4
        assert "cannot be resolved with --offline" in r.output
