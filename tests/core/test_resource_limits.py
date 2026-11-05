"""Test resource defaults and bounded-process cleanup without large allocations."""

import os
from pathlib import Path
import shlex
import signal
import subprocess
import time
import sys
import tomllib

import psutil
import pytest

from scripts import check_import_graph, run_resource_limited
from scripts import test_markdown_snippets as snippet_runner
from scripts.run_resource_limited import LIMIT_EXIT_CODE, main, run_command

ROOT = Path(__file__).resolve().parents[2]


def test_pytest_is_serial_unless_parallelism_is_explicitly_requested():
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    args = shlex.split(config["tool"]["pytest"]["ini_options"]["addopts"])
    assert args[args.index("-n") + 1] == "0"
    bounded = config["tool"]["poe"]["tasks"]["test:bounded"]
    assert bounded["env"]["LIBEPHEMERIS_LEB_READER"] == "indexed"
    assert "-n 0" in bounded["cmd"]


@pytest.mark.parametrize("jobs", [None, 2])
def test_cold_imports_are_serial_by_default_and_parallel_only_on_request(monkeypatch, jobs):
    limits = []

    class Executor:
        def __init__(self, *, max_workers):
            limits.append(max_workers)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def shutdown(self, *, wait, cancel_futures):
            assert wait and cancel_futures

        def map(self, function, items):
            # Do not create native ephemeris processes for a scheduling test.
            return []

    monkeypatch.setattr(check_import_graph, "ThreadPoolExecutor", Executor)
    kwargs = {} if jobs is None else {"jobs": jobs}
    check_import_graph.check_fresh_imports(check_import_graph.Report(), **kwargs)
    assert limits == [1 if jobs is None else jobs]


def test_command_exit_code_and_output_are_preserved(capfd):
    result = run_command(
        [sys.executable, "-c", "print('child output'); raise SystemExit(7)"],
        rss_limit_bytes=256 * 2**20,
    )
    assert result.returncode == 7
    assert not result.limit_exceeded
    assert "child output" in capfd.readouterr().out


@pytest.mark.parametrize("jobs", [None, 2])
def test_isolated_doc_snippets_are_serial_unless_requested(monkeypatch, tmp_path, capsys, jobs):
    page = tmp_path / "examples.md"
    page.write_text("```python\nprint(1)\n```\n\n```python\nprint(2)\n```\n")
    limits = []

    class Executor:
        def __init__(self, *, max_workers):
            limits.append(max_workers)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def map(self, function, items):
            return [function(item) for item in items]

    args = ["snippets", "--isolated", str(page)]
    if jobs is not None:
        args.extend(["--jobs", str(jobs)])
    monkeypatch.setattr(sys, "argv", args)
    monkeypatch.setattr(snippet_runner, "ThreadPoolExecutor", Executor)
    monkeypatch.setattr(snippet_runner, "test_snippet", lambda *args, **kwargs: (True, None))
    snippet_runner.main()
    assert limits == [1 if jobs is None else jobs]
    assert "2/2 snippets passed" in capsys.readouterr().out


def test_nonpositive_doc_snippet_jobs_fail_before_running(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["snippets", "--jobs", "0"])
    with pytest.raises(SystemExit) as error:
        snippet_runner.main()
    assert error.value.code == 2


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group cleanup contract")
def test_combined_child_memory_stops_the_whole_tree(tmp_path):
    child_pid_file = tmp_path / "child.pid"
    code = """
import os, signal, subprocess, sys, time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
child = subprocess.Popen([sys.executable, '-c',
    'import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); data=bytearray(16*2**20); time.sleep(30)'])
with open(sys.argv[1], 'w') as out:
    out.write(str(child.pid))
data = bytearray(16*2**20)
time.sleep(30)
"""
    # Each process stays small; the combined RSS must trigger the limit. This
    # exercises forced cleanup without reproducing gigabyte ephemeris loads.
    result = run_command(
        [sys.executable, "-c", code, str(child_pid_file)],
        rss_limit_bytes=38 * 2**20,
        interval=0.02,
    )
    assert result.returncode == LIMIT_EXIT_CODE
    assert result.limit_exceeded
    assert result.peak_rss > 38 * 2**20
    pid = int(child_pid_file.read_text())
    try:
        process = psutil.Process(pid)
        deadline = time.monotonic() + 5
        while process.status() != psutil.STATUS_ZOMBIE and time.monotonic() < deadline:
            time.sleep(0.01)
        assert process.status() == psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        pass


@pytest.mark.parametrize("limit, interval", [(0, 0.1), (1, 0)])
def test_invalid_limits_fail_before_starting_a_command(limit, interval):
    with pytest.raises(ValueError, match="positive"):
        run_command(["must-not-run"], rss_limit_bytes=limit, interval=interval)


def test_missing_executable_has_a_clear_nonzero_exit(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["watchdog", "--", "executable-that-does-not-exist-kerykeion"])
    assert main() == 127
    assert "Cannot start command" in capsys.readouterr().err


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal and process-group cleanup")
def test_cancelling_the_watchdog_stops_its_command(tmp_path):
    pid_file = tmp_path / "command.pid"
    command = "import os,sys,time; open(sys.argv[1], 'w').write(str(os.getpid())); time.sleep(30)"
    wrapper = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_resource_limited.py"),
            "--",
            sys.executable,
            "-c",
            command,
            str(pid_file),
        ]
    )
    try:
        deadline = time.monotonic() + 5
        while not (pid_file.exists() and pid_file.stat().st_size) and time.monotonic() < deadline:
            time.sleep(0.02)
        assert pid_file.exists()
        child_pid = int(pid_file.read_text())
        wrapper.send_signal(signal.SIGTERM)
        assert wrapper.wait(timeout=5) == 128 + signal.SIGTERM
        assert not psutil.pid_exists(child_pid)
    finally:
        if wrapper.poll() is None:
            wrapper.terminate()
            try:
                wrapper.wait(timeout=5)
            except subprocess.TimeoutExpired:
                wrapper.kill()
                wrapper.wait()
        if pid_file.exists() and pid_file.stat().st_size:
            try:
                psutil.Process(int(pid_file.read_text())).kill()
            except psutil.NoSuchProcess:
                pass


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal exit status")
def test_child_signal_uses_the_conventional_shell_status(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["watchdog", "--", "stubbed-command"])
    monkeypatch.setattr(
        run_resource_limited, "run_command", lambda *args, **kwargs: run_resource_limited.RunResult(-signal.SIGTERM, 0)
    )
    assert main() == 128 + signal.SIGTERM
    assert "terminated by signal" in capsys.readouterr().err


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal-mask inheritance")
def test_command_does_not_inherit_blocked_stop_signals():
    code = """
import signal
blocked = signal.pthread_sigmask(signal.SIG_BLOCK, [])
assert not blocked.intersection({signal.SIGINT, signal.SIGTERM, signal.SIGHUP}), blocked
"""
    assert run_command([sys.executable, "-c", code], rss_limit_bytes=256 * 2**20).returncode == 0


def test_fast_exit_still_stops_background_descendant(tmp_path):
    pid_file = tmp_path / "background.pid"
    code = """
import subprocess, sys
from pathlib import Path
child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
Path(sys.argv[1]).write_text(str(child.pid))
"""
    result = run_command([sys.executable, "-c", code, str(pid_file)],
                         rss_limit_bytes=256 * 2**20, interval=0.5)
    assert result.returncode == 0
    pid = int(pid_file.read_text())
    try:
        process = psutil.Process(pid)
        deadline = time.monotonic() + 5
        while process.status() != psutil.STATUS_ZOMBIE and time.monotonic() < deadline:
            time.sleep(0.01)
        assert process.status() == psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        pass


@pytest.mark.skipif(os.name != "posix", reason="POSIX setup cleanup")
def test_process_handle_failure_still_reaps_command(monkeypatch):
    children = []
    original = subprocess.Popen

    def spawn(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    def fail_handle(pid):
        raise RuntimeError("handle setup failed")

    monkeypatch.setattr(run_resource_limited.subprocess, "Popen", spawn)
    monkeypatch.setattr(run_resource_limited.psutil, "Process", fail_handle)
    with pytest.raises(RuntimeError, match="handle setup failed"):
        run_command([sys.executable, "-c", "import time; time.sleep(30)"], rss_limit_bytes=256 * 2**20)
    assert len(children) == 1
    assert children[0].returncode is not None


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group cleanup")
@pytest.mark.parametrize("live_observations", [0, 1, 3])
def test_group_eperm_waits_for_the_owned_leader_to_become_zombie(monkeypatch, live_observations):
    from types import SimpleNamespace
    from unittest.mock import Mock

    denied = PermissionError("group is exiting")
    kill = Mock(side_effect=denied)
    status = Mock(side_effect=[psutil.STATUS_RUNNING] * live_observations + [psutil.STATUS_ZOMBIE])
    sleep = Mock()
    monkeypatch.setattr(run_resource_limited.os, "killpg", kill)
    monkeypatch.setattr(run_resource_limited.psutil, "Process", lambda pid: SimpleNamespace(status=status))
    monkeypatch.setattr(run_resource_limited.time, "sleep", sleep)
    run_resource_limited._signal_group(123, signal.SIGKILL)
    kill.assert_called_once_with(123, signal.SIGKILL)
    assert sleep.call_count == live_observations


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group cleanup")
def test_group_eperm_for_a_live_leader_remains_an_error(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock

    denied = PermissionError("persistent denial")
    kill = Mock(side_effect=denied)
    sleep = Mock()
    monkeypatch.setattr(run_resource_limited.os, "killpg", kill)
    monkeypatch.setattr(run_resource_limited.psutil, "Process",
                        lambda pid: SimpleNamespace(status=lambda: psutil.STATUS_RUNNING))
    monkeypatch.setattr(run_resource_limited.time, "sleep", sleep)
    with pytest.raises(PermissionError) as error:
        run_resource_limited._signal_group(123, signal.SIGKILL)
    assert error.value is denied
    kill.assert_called_once_with(123, signal.SIGKILL)
    assert sleep.call_count == 10
