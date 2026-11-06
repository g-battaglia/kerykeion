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
    """Verify pytest is serial unless parallelism is explicitly requested."""
    config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    args = shlex.split(config["tool"]["pytest"]["ini_options"]["addopts"])
    assert args[args.index("-n") + 1] == "0"
    bounded = config["tool"]["poe"]["tasks"]["test:bounded"]
    assert bounded["env"]["LIBEPHEMERIS_LEB_READER"] == "indexed"
    assert "-n 0" in bounded["cmd"]


@pytest.mark.parametrize("jobs", [None, 2])
def test_cold_imports_are_serial_by_default_and_parallel_only_on_request(monkeypatch, jobs):
    """Verify cold imports are serial by default and parallel only on request."""
    limits = []

    class Executor:
        """Exercise Executor behavior in the watchdog regression."""
        def __init__(self, *, max_workers):
            """Exercise   init   behavior in the watchdog regression."""
            limits.append(max_workers)

        def __enter__(self):
            """Exercise   enter   behavior in the watchdog regression."""
            return self

        def __exit__(self, *args):
            """Exercise   exit   behavior in the watchdog regression."""
            return False

        def shutdown(self, *, wait, cancel_futures):
            """Exercise shutdown behavior in the watchdog regression."""
            assert wait and cancel_futures

        def map(self, function, items):
            # Do not create native ephemeris processes for a scheduling test.
            """Exercise map behavior in the watchdog regression."""
            return []

    monkeypatch.setattr(check_import_graph, "ThreadPoolExecutor", Executor)
    kwargs = {} if jobs is None else {"jobs": jobs}
    check_import_graph.check_fresh_imports(check_import_graph.Report(), **kwargs)
    assert limits == [1 if jobs is None else jobs]


def test_command_exit_code_and_output_are_preserved(capfd):
    """Verify command exit code and output are preserved."""
    result = run_command(
        [sys.executable, "-c", "print('child output'); raise SystemExit(7)"],
        rss_limit_bytes=256 * 2**20,
    )
    assert result.returncode == 7
    assert not result.limit_exceeded
    assert "child output" in capfd.readouterr().out


@pytest.mark.parametrize("jobs", [None, 2])
def test_isolated_doc_snippets_are_serial_unless_requested(monkeypatch, tmp_path, capsys, jobs):
    """Verify isolated doc snippets are serial unless requested."""
    page = tmp_path / "examples.md"
    page.write_text("```python\nprint(1)\n```\n\n```python\nprint(2)\n```\n")
    limits = []

    class Executor:
        """Exercise Executor behavior in the watchdog regression."""
        def __init__(self, *, max_workers):
            """Exercise   init   behavior in the watchdog regression."""
            limits.append(max_workers)

        def __enter__(self):
            """Exercise   enter   behavior in the watchdog regression."""
            return self

        def __exit__(self, *args):
            """Exercise   exit   behavior in the watchdog regression."""
            return False

        def map(self, function, items):
            """Exercise map behavior in the watchdog regression."""
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
    """Verify nonpositive doc snippet jobs fail before running."""
    monkeypatch.setattr(sys, "argv", ["snippets", "--jobs", "0"])
    with pytest.raises(SystemExit) as error:
        snippet_runner.main()
    assert error.value.code == 2


@pytest.mark.skipif(os.name != "posix", reason="POSIX process-group cleanup contract")
def test_combined_child_memory_stops_the_whole_tree(tmp_path):
    """Verify combined child memory stops the whole tree."""
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
    """Verify invalid limits fail before starting a command."""
    with pytest.raises(ValueError, match="positive"):
        run_command(["must-not-run"], rss_limit_bytes=limit, interval=interval)


@pytest.mark.skipif(os.name != "posix", reason="POSIX unreaped leader shutdown")
@pytest.mark.parametrize("descendant", [False, True, "slow-termination"])
def test_memory_threshold_preserves_the_leaders_sigterm_cleanup(tmp_path, monkeypatch, descendant):
    """Empty/quickly exiting descendant sets cannot truncate leader cleanup."""
    marker = tmp_path / "cleanup.txt"
    if descendant == "slow-termination":
        terminate = psutil.Process.terminate

        def delayed_terminate(process):
            """Exercise delayed terminate behavior in the watchdog regression."""
            time.sleep(0.9)
            terminate(process)

        monkeypatch.setattr(psutil.Process, "terminate", delayed_terminate)
    code = """
import pathlib, signal, subprocess, sys, time
def cleanup(signum, frame):
    time.sleep(0.2)
    pathlib.Path(sys.argv[1]).write_text('finished', encoding='utf-8')
    raise SystemExit(0)
signal.signal(signal.SIGTERM, cleanup)
if sys.argv[2] == 'True':
    subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])
data = bytearray(32 * 2**20)
time.sleep(30)
"""
    result = run_command(
        [sys.executable, "-c", code, str(marker), str(bool(descendant))],
        rss_limit_bytes=24 * 2**20,
        interval=0.02,
    )
    assert result.returncode == LIMIT_EXIT_CODE
    assert result.limit_exceeded
    assert marker.read_text(encoding="utf-8") == "finished"


@pytest.mark.skipif(os.name != "posix", reason="POSIX restricted process inspection")
def test_denied_leader_status_still_signals_and_reaps_the_owned_group(monkeypatch):
    """A restricted status query must not bypass the final group signal."""
    from types import SimpleNamespace
    from unittest.mock import Mock

    clock = [0.0]

    def sleep(seconds):
        """Advance the synthetic cleanup clock without waiting."""
        clock[0] += seconds

    leader = SimpleNamespace(children=lambda **kwargs: [], status=Mock(side_effect=psutil.AccessDenied(123)))
    child = SimpleNamespace(pid=123, wait=Mock())
    signals = Mock()
    monkeypatch.setattr(run_resource_limited, "_signal_group", signals)
    monkeypatch.setattr(run_resource_limited.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(run_resource_limited.time, "sleep", sleep)
    run_resource_limited._stop_tree(child, {123: leader})
    assert clock[0] >= 1.0
    assert signals.call_args_list[0].args == (123, signal.SIGTERM)
    assert signals.call_args_list[-1].args == (123, signal.SIGKILL)
    child.wait.assert_called_once_with()


def test_missing_executable_has_a_clear_nonzero_exit(monkeypatch, capfd):
    """Verify missing executable has a clear nonzero exit."""
    monkeypatch.setattr(sys, "argv", ["watchdog", "--", "executable-that-does-not-exist-kerykeion"])
    assert main() == 127
    assert "Cannot start command" in capfd.readouterr().err


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal and process-group cleanup")
def test_cancelling_the_watchdog_stops_its_command(tmp_path):
    """Verify cancelling the watchdog stops its command."""
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
    """Verify child signal uses the conventional shell status."""
    monkeypatch.setattr(sys, "argv", ["watchdog", "--", "stubbed-command"])
    monkeypatch.setattr(
        run_resource_limited, "run_command", lambda *args, **kwargs: run_resource_limited.RunResult(-signal.SIGTERM, 0)
    )
    assert main() == 128 + signal.SIGTERM
    assert "terminated by signal" in capsys.readouterr().err


@pytest.mark.skipif(os.name != "posix", reason="POSIX signal-mask inheritance")
def test_command_does_not_inherit_blocked_stop_signals():
    """Verify command does not inherit blocked stop signals."""
    code = """
import signal
blocked = signal.pthread_sigmask(signal.SIG_BLOCK, [])
assert not blocked.intersection({signal.SIGINT, signal.SIGTERM, signal.SIGHUP}), blocked
"""
    assert run_command([sys.executable, "-c", code], rss_limit_bytes=256 * 2**20).returncode == 0


def test_fast_exit_still_stops_background_descendant(tmp_path):
    """Verify fast exit still stops background descendant."""
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
    """Verify process handle failure still reaps command."""
    children = []
    original = subprocess.Popen

    def spawn(*args, **kwargs):
        """Track the exact child created for the cleanup regression."""
        child = original(*args, **kwargs)
        children.append(child)
        return child

    def fail_handle(pid):
        """Simulate process inspection failure after the child is owned."""
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
    """Verify group eperm waits for the owned leader to become zombie."""
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
    """Verify group eperm for a live leader remains an error."""
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
