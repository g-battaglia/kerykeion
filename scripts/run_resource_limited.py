"""Run a command with a sampled RSS stop threshold for its process tree.

Example: uv run python scripts/run_resource_limited.py -- python -m pytest -n 0
The default threshold is 1 GiB. This is a watchdog, not an OS allocation limit:
short-lived allocation spikes between samples may exceed it. Child stdout and
stderr are inherited, and normal command exit codes are propagated unchanged.
On POSIX, descendants that deliberately create another session before they can
be sampled are outside this watchdog contract; use OS containment for such jobs.
"""

from __future__ import annotations

import argparse
import importlib
from contextlib import contextmanager
from dataclasses import dataclass
import os
import signal
import subprocess
import sys
import time
import threading

import psutil

LIMIT_EXIT_CODE = 125


class StopRequested(BaseException):
    def __init__(self, signum: int):
        self.signum = signum


@dataclass(frozen=True)
class RunResult:
    returncode: int
    peak_rss: int
    limit_exceeded: bool = False


@contextmanager
def _defer_stop_signals():
    """Do not interrupt spawn ownership or the final kill/wait sequence."""
    # Defer Python handlers rather than blocking the thread's signal mask:
    # a child would inherit a blocked mask and could never handle SIGTERM.
    # Python only delivers handlers on the main thread.
    if threading.current_thread() is not threading.main_thread():
        yield
        return
    signals = {signal.SIGINT, signal.SIGTERM}
    if hasattr(signal, "SIGHUP"):
        signals.add(signal.SIGHUP)
    previous = {sig: signal.getsignal(sig) for sig in signals}
    pending = []

    def remember(signum, frame):
        pending.append((signum, frame))

    try:
        for sig in signals:
            signal.signal(sig, remember)
        yield
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        if pending:
            signum, frame = pending[0]
            handler = previous[signum]
            if callable(handler):
                handler(signum, frame)
            elif handler == signal.SIG_DFL:
                signal.raise_signal(signum)


def _signal_group(pid: int, signum: int) -> None:
    """Signal an owned group, accepting macOS's EPERM for a zombie-only group."""
    try:
        os.killpg(pid, signum)
    except ProcessLookupError:
        pass
    except PermissionError:
        # macOS can report EPERM while its unreaped leader is exiting, just
        # before psutil observes ZOMBIE. Do not reap it or signal a new group:
        # briefly wait for that transition, then propagate persistent EPERM.
        process = psutil.Process(pid)
        for attempt in range(11):
            if process.status() == psutil.STATUS_ZOMBIE:
                return
            if attempt == 10:
                raise
            time.sleep(0.01)


def _stop_tree(child: subprocess.Popen, known: dict[int, psutil.Process], job=None) -> None:
    """Terminate the owned group before reaping its leader (no reused PGID)."""
    with _defer_stop_signals():
        if job is not None:
            job.close()
            child.wait()
            return
        process = known.get(child.pid)
        if process is not None:
            try:
                for descendant in process.children(recursive=True):
                    known[descendant.pid] = descendant
            except psutil.Error:
                pass
        # Never let psutil.wait_procs reap the direct child: its PID reserves
        # the process-group identity until our last signal has been sent.
        descendants = [member for pid, member in known.items() if pid != child.pid]
        for member in reversed(descendants):
            try:
                member.terminate()
            except psutil.Error:
                pass
        if os.name == "posix":
            _signal_group(child.pid, signal.SIGTERM)
        else:
            child.terminate()
        deadline = time.monotonic() + 1.0
        _, alive = psutil.wait_procs(descendants, timeout=max(0.0, deadline - time.monotonic()))
        if os.name == "posix" and process is not None:
            # wait_procs([]) returns immediately, and descendants may finish
            # before their leader. Inspect status without wait()/poll(): the
            # unreaped leader must reserve the PGID through the final signal.
            while time.monotonic() < deadline:
                try:
                    if process.status() == psutil.STATUS_ZOMBIE:
                        break
                except psutil.NoSuchProcess:
                    break
                except psutil.Error:
                    # Restricted procfs/non-dumpable children can deny status.
                    # Preserve grace, then still signal the entire owned group.
                    pass
                time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
        for member in alive:
            try:
                member.kill()
            except psutil.Error:
                pass
        if os.name == "posix":
            _signal_group(child.pid, signal.SIGKILL)
        elif child.poll() is None:
            child.kill()
        child.wait()


def run_command(command: list[str], *, rss_limit_bytes: int, interval: float = 0.1) -> RunResult:
    """Supervise the command and sampled descendants, preserving its exit code."""
    if rss_limit_bytes <= 0 or interval <= 0:
        raise ValueError("RSS limit and sampling interval must be positive")
    child = None
    job = None
    known: dict[int, psutil.Process] = {}
    peak_rss = 0
    exceeded = False
    try:
        with _defer_stop_signals():
            if os.name == "nt":
                # Both module and script invocation are supported.
                module = importlib.import_module(".windows_job", __package__) if __package__ else importlib.import_module("windows_job")
                job = module.WindowsJob()
                child = job.start(command)
            else:
                child = subprocess.Popen(command, start_new_session=True)
            try:
                process = psutil.Process(child.pid)
            except psutil.NoSuchProcess:
                return RunResult(child.wait(), 0)
            known[process.pid] = process
            if os.name == "posix":
                try:
                    process.nice(10)
                except psutil.Error:
                    pass
        while True:
            try:
                # status() does not reap the leader, unlike Popen.poll().
                if process.status() == psutil.STATUS_ZOMBIE:
                    break
                if os.name != "posix" and child.poll() is not None:
                    break
                for descendant in process.children(recursive=True):
                    known[descendant.pid] = descendant
            except psutil.NoSuchProcess:
                break
            except psutil.Error:
                pass
            rss = 0
            for pid, member in list(known.items()):
                try:
                    if member.is_running():
                        rss += member.memory_info().rss
                    else:
                        known.pop(pid)
                except psutil.Error:
                    known.pop(pid, None)
            peak_rss = max(peak_rss, rss)
            if rss > rss_limit_bytes:
                exceeded = True
                break
            time.sleep(interval)
    finally:
        if child is not None:
            try:
                _stop_tree(child, known, job)
            finally:
                # Even failed process inspection/group signalling must reap the
                # direct child. No further group signals follow this point, so
                # polling here cannot expose a reused process-group identity.
                with _defer_stop_signals():
                    if child.poll() is None:
                        child.kill()
                    child.wait()
        elif job is not None:
            job.close()
    return RunResult(LIMIT_EXIT_CODE if exceeded else child.returncode, peak_rss, exceeded)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rss-limit-mib", type=int, default=1024)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.rss_limit_mib < 1:
        parser.error("--rss-limit-mib must be positive")
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("provide a command after --")

    def stop_requested(signum, frame):
        raise StopRequested(signum)

    stop_signals = [signal.SIGTERM]
    if hasattr(signal, "SIGHUP"):
        stop_signals.append(signal.SIGHUP)
    previous_handlers = {sig: signal.getsignal(sig) for sig in stop_signals}
    try:
        for sig in stop_signals:
            signal.signal(sig, stop_requested)
        result = run_command(command, rss_limit_bytes=args.rss_limit_mib * 2**20)
    except StopRequested as exc:
        return 128 + exc.signum
    except KeyboardInterrupt:
        return 130
    except OSError as exc:
        print(f"Cannot start command: {exc}", file=sys.stderr)
        return 127
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
    if result.limit_exceeded:
        status = "RSS threshold exceeded; command stopped"
    elif result.returncode < 0:
        status = f"command terminated by signal {-result.returncode}"
    else:
        status = f"exit {result.returncode}"
    print(f"Resource watchdog: {status}; sampled peak tree RSS {result.peak_rss / 2**20:.1f} MiB", file=sys.stderr)
    return result.returncode if result.returncode >= 0 else 128 - result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
