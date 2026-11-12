"""The Windows venv executable must join its job before any thread runs."""

from types import SimpleNamespace

import pytest

from scripts import windows_job


@pytest.fixture
def launcher(monkeypatch):
    """Build an isolated Windows launcher with observable Win32 calls."""
    calls = []
    failure = {"assign": False, "resume": 1, "threads": 1}

    class Kernel:
        """Model only the Win32 operations needed by job-creation tests."""
        def OpenProcess(self, *args):
            """Record acquisition of the simulated child process handle."""
            calls.append("open-process")
            return 10

        def AssignProcessToJobObject(self, *args):
            """Record job assignment and exercise the configured failure path."""
            calls.append("assign")
            return not failure["assign"]

        def OpenThread(self, rights, inherit, tid):
            """Record acquisition of the simulated primary-thread handle."""
            assert rights == 0x0002 and not inherit and tid == 99
            calls.append("open-thread")
            return 20

        def SetEvent(self, *args):
            """Record release of the watchdog guard event."""
            calls.append("gate")
            return True

        def ResumeThread(self, handle):
            """Record primary-thread resumption after successful job assignment."""
            calls.append("resume")
            return failure["resume"]

        def CloseHandle(self, handle):
            """Record release of a simulated owned Win32 handle."""
            calls.append("close-" + str(handle))

    child = SimpleNamespace(pid=123, kill=lambda: calls.append("kill"), wait=lambda: calls.append("wait"))

    def popen(command, **kwargs):
        """Record suspended child creation without starting a real Windows process."""
        assert command[0] == windows_job.sys.executable
        assert command[-2:] == ["python", "-V"]
        assert kwargs == {"creationflags": 0x00000004}
        calls.append("create-suspended")
        return child

    job = object.__new__(windows_job.WindowsJob)
    job.kernel, job.job, job.event, job.name = Kernel(), 1, 2, "test-gate"
    monkeypatch.setattr(windows_job.subprocess, "Popen", popen)
    monkeypatch.setattr(windows_job.psutil, "Process", lambda pid: SimpleNamespace(threads=lambda: [SimpleNamespace(id=99)] * failure["threads"]))
    monkeypatch.setattr(windows_job.ctypes, "WinError", lambda code: OSError("Win32 setup failed"), raising=False)
    monkeypatch.setattr(windows_job.ctypes, "get_last_error", lambda: 5, raising=False)
    return job, child, calls, failure


def test_assign_and_gate_precede_first_thread_execution(launcher):
    """Verify assign and gate precede first thread execution."""
    job, child, calls, _ = launcher
    assert job.start(["python", "-V"]) is child
    assert calls == ["create-suspended", "open-process", "assign", "open-thread", "gate", "resume", "close-20", "close-10"]


@pytest.mark.parametrize("failure_kind,value", [("assign", True), ("resume", 0xFFFFFFFF), ("resume", 0), ("threads", 2)])
def test_failed_setup_reaps_suspended_child_and_closes_handles(launcher, failure_kind, value):
    """Verify failed setup reaps suspended child and closes handles."""
    job, _, calls, failure = launcher
    failure[failure_kind] = value
    with pytest.raises((OSError, RuntimeError)):
        job.start(["python", "-V"])
    assert calls[-2:] == ["kill", "wait"]
    assert "close-10" in calls
    if "open-thread" in calls:
        assert "close-20" in calls
    if failure_kind in {"assign", "threads"}:
        assert "resume" not in calls
