"""Concurrency regression test for the timing factories.

The timing factories mutate process-global Swiss Ephemeris state (ephemeris
path, sidereal mode) guarded by ``EPHEMERIS_LOCK``. This test runs tropical +
sidereal void-of-course work and sun-times work on many threads at once and
asserts every thread still gets the single-threaded result — i.e. a sidereal
sidereal-mode mutation never bleeds into a concurrent tropical calculation.
"""

from __future__ import annotations

import threading

from kerykeion import SunTimesFactory, VoidOfCourseMoonFactory

ROME = dict(latitude=41.9028, longitude=12.4964, tz_str="Europe/Rome")


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
            for _ in range(15):
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
    for thread in threads:
        thread.join()

    assert not errors, errors
