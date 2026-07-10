"""Concurrency regression test for the timing factories.

The timing factories mutate process-global Swiss Ephemeris state (ephemeris
path, sidereal mode) guarded by ``EPHEMERIS_LOCK``. This test runs tropical +
sidereal void-of-course work and sun-times work on many threads at once and
asserts every thread still gets the single-threaded result — i.e. a sidereal
sidereal-mode mutation never bleeds into a concurrent tropical calculation.
"""

from __future__ import annotations

import threading
import time

from kerykeion import (
    EclipseFactory,
    LunationFinderFactory,
    SignIngressFactory,
    SunTimesFactory,
    VoidOfCourseMoonFactory,
)

ROME = dict(latitude=41.9028, longitude=12.4964, tz_str="Europe/Rome")


def _join_with_shared_deadline(threads: list, total_seconds: float) -> list:
    """Join threads against ONE shared wall-clock deadline.

    Per-thread ``join(timeout=T)`` budgets are ordering-dependent: a uniformly
    slow run banks up to T per join and passes, while a single laggard that
    happens to be joined first fails at exactly T — that made this suite flaky
    under xdist load. A shared deadline judges total elapsed time only.
    """
    deadline = time.monotonic() + total_seconds
    for thread in threads:
        thread.join(timeout=max(0.0, deadline - time.monotonic()))
    return [t for t in threads if t.is_alive()]


def test_tropical_and_sidereal_do_not_corrupt_each_other_under_threads():
    base_trop = VoidOfCourseMoonFactory.from_datetime(2026, 6, 1, 9, 0, tz_str="Europe/Rome")
    base_sid = VoidOfCourseMoonFactory.from_datetime(
        2026, 6, 1, 9, 0, tz_str="Europe/Rome", zodiac_type="Sidereal", sidereal_mode="LAHIRI"
    )
    # The ayanamsha must actually move the Moon into a different sign, otherwise
    # the test could pass even if the lock were broken.
    assert base_trop.moon_sign != base_sid.moon_sign

    errors: list[str] = []

    def worker() -> None:
        try:
            # 5 iterations keep the workload well under the join deadline even
            # under xdist load (15 iterations measured ~117s on an idle
            # machine, within 3% of the old 120s budget — a flake by design).
            for _ in range(5):
                trop = VoidOfCourseMoonFactory.from_datetime(2026, 6, 1, 9, 0, tz_str="Europe/Rome")
                sid = VoidOfCourseMoonFactory.from_datetime(
                    2026, 6, 1, 9, 0, tz_str="Europe/Rome", zodiac_type="Sidereal", sidereal_mode="LAHIRI"
                )
                SunTimesFactory.from_date(2026, 5, 28, **ROME)
                if trop.moon_sign != base_trop.moon_sign or trop.ingress != base_trop.ingress:
                    errors.append(f"tropical corrupted: {trop.moon_sign}")
                if sid.moon_sign != base_sid.moon_sign or sid.ingress != base_sid.ingress:
                    errors.append(f"sidereal corrupted: {sid.moon_sign}")
        except Exception as exc:  # pragma: no cover - any raise is a failure
            errors.append(repr(exc))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    # Threads still alive after the shared deadline mean a deadlock/hang in the
    # shared ephemeris session — fail loudly instead of blocking the suite.
    still_alive = _join_with_shared_deadline(threads, total_seconds=300)
    assert not still_alive, f"{len(still_alive)} worker thread(s) did not finish within the timeout"

    assert not errors, errors


def test_event_scan_factories_match_single_threaded_baselines_under_threads():
    """Lunation, eclipse and ingress scans hold the ephemeris lock across many
    backend calls; run them on many threads interleaved with sidereal work and
    assert every thread reproduces the single-threaded baseline exactly — i.e.
    no concurrent session (sidereal mode, path reset) bleeds into a scan."""
    base_lun = LunationFinderFactory.from_iso_range("2026-06-01", "2026-06-30").model_dump()
    base_ecl = EclipseFactory.search_global(start_year=2026, count=2).model_dump()
    base_ing = SignIngressFactory.from_iso_range(
        "2026-06-01", "2026-06-30", planets=["Sun", "Mars"]
    ).model_dump()

    errors: list[str] = []

    def worker() -> None:
        try:
            for _ in range(3):
                # Sidereal work creates real contention: it mutates the global
                # sidereal mode inside its own session.
                VoidOfCourseMoonFactory.from_datetime(
                    2026, 6, 1, 9, 0, tz_str="Europe/Rome",
                    zodiac_type="Sidereal", sidereal_mode="LAHIRI",
                )
                lun = LunationFinderFactory.from_iso_range("2026-06-01", "2026-06-30").model_dump()
                ecl = EclipseFactory.search_global(start_year=2026, count=2).model_dump()
                ing = SignIngressFactory.from_iso_range(
                    "2026-06-01", "2026-06-30", planets=["Sun", "Mars"]
                ).model_dump()
                if lun != base_lun:
                    errors.append("lunations diverged from single-threaded baseline")
                if ecl != base_ecl:
                    errors.append("eclipses diverged from single-threaded baseline")
                if ing != base_ing:
                    errors.append("ingresses diverged from single-threaded baseline")
        except Exception as exc:  # pragma: no cover - any raise is a failure
            errors.append(repr(exc))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    # Threads still alive after the shared deadline mean a deadlock/hang in the
    # shared ephemeris session — fail loudly instead of blocking the suite.
    still_alive = _join_with_shared_deadline(threads, total_seconds=300)
    assert not still_alive, f"{len(still_alive)} worker thread(s) did not finish within the timeout"

    assert not errors, errors
