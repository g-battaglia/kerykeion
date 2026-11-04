"""Run a command with a sampled RSS stop threshold for its process tree.

Example: uv run python scripts/run_resource_limited.py -- python -m pytest -n 0
The default threshold is 1 GiB. This is a watchdog, not an OS allocation limit:
short-lived allocation spikes between samples may exceed it. Child stdout and
stderr are inherited, and normal command exit codes are propagated unchanged.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
import signal
import subprocess
import sys
import time

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


def _stop_tree(process: psutil.Process, known: dict[int, psutil.Process]) -> None:
    """Stop only the child command and its observed descendants."""
    try:
        for child in process.children(recursive=True):
            known[child.pid] = child
    except psutil.Error:
        pass
    processes = list(known.values())
    for child in reversed(processes):
        try:
            child.terminate()
        except psutil.Error:
            pass
    # POSIX commands have their own session, so escaped/reparented members of
    # this group are also stopped. Never signal the caller's process group.
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    _, alive = psutil.wait_procs(processes, timeout=1)
    for child in alive:
        try:
            child.kill()
        except psutil.Error:
            pass
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_command(command: list[str], *, rss_limit_bytes: int, interval: float = 0.1) -> RunResult:
    """Supervise a single command, including memory used by its descendants."""
    if rss_limit_bytes <= 0 or interval <= 0:
        raise ValueError("RSS limit and sampling interval must be positive")
    child = subprocess.Popen(command, start_new_session=os.name == "posix")
    process = psutil.Process(child.pid)
    known = {process.pid: process}
    if os.name == "posix":
        try:
            process.nice(10)
        except psutil.Error:
            pass
    peak_rss = 0
    try:
        while child.poll() is None:
            try:
                for descendant in process.children(recursive=True):
                    known[descendant.pid] = descendant
            except psutil.Error:
                pass
            rss = 0
            for pid, member in list(known.items()):
                try:
                    # psutil's identity check protects against PID reuse.
                    if member.is_running():
                        rss += member.memory_info().rss
                    else:
                        known.pop(pid)
                except psutil.Error:
                    known.pop(pid, None)
            peak_rss = max(peak_rss, rss)
            if rss > rss_limit_bytes:
                _stop_tree(process, known)
                child.wait()
                return RunResult(LIMIT_EXIT_CODE, peak_rss, True)
            time.sleep(interval)
        # A command may exit before a background child. End its session too;
        # otherwise an orphan could keep allocating after supervision stops.
        _stop_tree(process, known)
        return RunResult(child.returncode, peak_rss)
    except BaseException:
        _stop_tree(process, known)
        child.wait()
        raise


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
