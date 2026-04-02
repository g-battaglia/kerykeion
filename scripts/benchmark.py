"""
Performance benchmark for Kerykeion.

Measures the time for the core operations:
  1. Subject creation (single + batch)
  2. Aspects calculation (natal + synastry)
  3. Chart rendering (SVG generation)

Run via:  poe benchmark
"""

import time
import statistics
import sys

from kerykeion import (
    AstrologicalSubjectFactory,
    AspectsFactory,
    ChartDataFactory,
    ChartDrawer,
)
from kerykeion.ephemeris_backend import BACKEND_NAME


# ---------------------------------------------------------------------------
# Test subjects (offline, no geonames calls)
# ---------------------------------------------------------------------------
SUBJECTS_DATA = [
    ("John Lennon", 1940, 10, 9, 18, 30, 53.4084, -2.9916, "Europe/London"),
    ("Johnny Depp", 1963, 6, 9, 0, 0, 37.7743, -87.1133, "America/Chicago"),
    ("Paul McCartney", 1942, 6, 18, 15, 30, 53.4084, -2.9916, "Europe/London"),
    ("Albert Einstein", 1879, 3, 14, 11, 30, 48.3985, 9.9918, "Europe/Berlin"),
    ("Marie Curie", 1867, 11, 7, 12, 0, 52.2297, 21.0122, "Europe/Warsaw"),
]

WARMUP_ROUNDS = 3
BENCH_ROUNDS = 20
BATCH_SIZE = len(SUBJECTS_DATA)


def create_subject(name, year, month, day, hour, minute, lat, lng, tz_str):
    return AstrologicalSubjectFactory.from_birth_data(
        name, year, month, day, hour, minute,
        lat=lat, lng=lng, tz_str=tz_str, online=False,
        suppress_geonames_warning=True,
    )


def bench(label, func, rounds=BENCH_ROUNDS, warmup=WARMUP_ROUNDS):
    """Run func() for warmup + rounds iterations, report stats."""
    for _ in range(warmup):
        func()

    times = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        func()
        times.append(time.perf_counter() - t0)

    med = statistics.median(times)
    mn = min(times)
    mx = max(times)
    print(f"  {label:.<50s} median {med*1000:8.2f}ms  "
          f"(min {mn*1000:.2f}, max {mx*1000:.2f})")
    return med


def main():
    print(f"Kerykeion benchmark  |  backend: {BACKEND_NAME}")
    print(f"Python {sys.version.split()[0]}  |  {BENCH_ROUNDS} rounds, {WARMUP_ROUNDS} warmup")
    print("=" * 72)

    # Pre-create subjects for aspects/chart benchmarks
    subjects = [create_subject(*d) for d in SUBJECTS_DATA]

    # ------------------------------------------------------------------
    # 1. Subject creation
    # ------------------------------------------------------------------
    print("\n[1] Subject creation")

    bench("Single subject (John Lennon)",
          lambda: create_subject(*SUBJECTS_DATA[0]))

    bench(f"Batch {BATCH_SIZE} subjects",
          lambda: [create_subject(*d) for d in SUBJECTS_DATA])

    bench("Subject with all optional calcs",
          lambda: AstrologicalSubjectFactory.from_birth_data(
              "Full", 1990, 1, 1, 12, 0,
              lat=41.9028, lng=12.4964, tz_str="Europe/Rome", online=False,
              suppress_geonames_warning=True,
              calculate_dignities=True,
              calculate_nakshatra=True,
              calculate_gauquelin=True,
              calculate_nutation=True,
              calculate_local_space=True,
          ))

    bench("Subject sidereal LAHIRI",
          lambda: AstrologicalSubjectFactory.from_birth_data(
              "Sidereal", 1940, 10, 9, 18, 30,
              lat=53.4084, lng=-2.9916, tz_str="Europe/London", online=False,
              suppress_geonames_warning=True,
              zodiac_type="Sidereal", sidereal_mode="LAHIRI",
          ))

    # ------------------------------------------------------------------
    # 2. Aspects
    # ------------------------------------------------------------------
    print("\n[2] Aspects calculation")

    bench("Natal aspects",
          lambda: AspectsFactory.single_chart_aspects(subjects[0]))

    bench("Synastry aspects",
          lambda: AspectsFactory.dual_chart_aspects(subjects[0], subjects[2]))

    # ------------------------------------------------------------------
    # 3. Chart SVG rendering
    # ------------------------------------------------------------------
    print("\n[3] Chart SVG rendering")

    chart_data_natal = ChartDataFactory.create_chart_data("Natal", subjects[0])
    bench("Natal SVG (classic)",
          lambda: ChartDrawer(chart_data_natal, theme="classic").generate_svg_string())

    chart_data_synastry = ChartDataFactory.create_chart_data(
        "Synastry", subjects[0], subjects[2])
    bench("Synastry SVG (classic)",
          lambda: ChartDrawer(chart_data_synastry, theme="classic").generate_svg_string())

    bench("ChartData creation (Natal)",
          lambda: ChartDataFactory.create_chart_data("Natal", subjects[0]))

    # ------------------------------------------------------------------
    # 4. Full pipeline (subject + aspects + chart)
    # ------------------------------------------------------------------
    print("\n[4] Full pipeline (create subject + aspects + SVG)")

    def full_pipeline():
        s = create_subject(*SUBJECTS_DATA[0])
        AspectsFactory.single_chart_aspects(s)
        cd = ChartDataFactory.create_chart_data("Natal", s)
        ChartDrawer(cd, theme="classic").generate_svg_string()

    bench("Full natal pipeline", full_pipeline)

    print("\n" + "=" * 72)
    print("Done.")


if __name__ == "__main__":
    main()
