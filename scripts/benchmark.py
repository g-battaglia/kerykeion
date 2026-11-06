"""
Performance benchmark for Kerykeion.

Measures the time for the core operations:
  1. Subject creation (single + batch)
  2. Aspects calculation (natal + synastry)
  3. Full, wheel-only and grid-only rendering in explicit classic/modern styles
  4. Translations and astrocartography
  5. Complete subject -> ChartData -> SVG pipelines

Run via:  poe benchmark
"""

import argparse
import json
import logging
import os
import subprocess
import platform
from importlib.metadata import version
from pathlib import Path
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
from kerykeion.astro_cartography import AstroCartographyFactory
from kerykeion.settings.translations import load_language_pair


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
        name,
        year,
        month,
        day,
        hour,
        minute,
        lat=lat,
        lng=lng,
        tz_str=tz_str,
        online=False,
        suppress_geonames_warning=True,
    )


def bench(label, func, *, rounds, warmup, iterations=1):
    """Run func() for warmup + rounds iterations, report stats."""
    for _ in range(warmup):
        func()

    times = []
    cpu_times = []
    for _ in range(rounds):
        cpu_t0 = time.process_time()
        t0 = time.perf_counter()
        for _ in range(iterations):
            func()
        times.append((time.perf_counter() - t0) / iterations)
        cpu_times.append((time.process_time() - cpu_t0) / iterations)

    med = statistics.median(times)
    mn = min(times)
    mx = max(times)
    print(f"  {label:.<50s} median {med * 1000:8.2f}ms  (min {mn * 1000:.2f}, max {mx * 1000:.2f})")
    return {
        "median_ms": med * 1000,
        "min_ms": mn * 1000,
        "max_ms": mx * 1000,
        "samples_ms": [t * 1000 for t in times],
        "iterations": iterations,
        "cpu_median_ms": statistics.median(cpu_times) * 1000,
        "cpu_samples_ms": [t * 1000 for t in cpu_times],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=BENCH_ROUNDS)
    parser.add_argument("--warmup", type=int, default=WARMUP_ROUNDS)
    parser.add_argument("--iterations", type=int, default=10, help="Calls per timing sample")
    parser.add_argument("--json", type=Path, dest="json_path", help="Write timings and environment as JSON")
    args = parser.parse_args()
    if args.rounds < 1 or args.warmup < 0 or args.iterations < 1:
        parser.error("rounds and iterations must be positive; warmup must be non-negative")
    logging.disable(logging.CRITICAL)
    source_file = Path(sys.modules[AstrologicalSubjectFactory.__module__].__file__).resolve()
    source_root = source_file.parents[2]
    try:
        git_root = subprocess.check_output(
            ["git", "-C", str(source_root), "rev-parse", "--show-toplevel"], text=True, stderr=subprocess.DEVNULL
        ).strip()
        source_commit = subprocess.check_output(
            ["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip() if Path(git_root).resolve() == source_root else None
    except (OSError, subprocess.CalledProcessError):
        source_commit = None
    environment = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "backend": BACKEND_NAME,
        "source_commit": source_commit,
        "source_module": str(source_file.relative_to(source_root)),
        "leb_reader": os.environ.get("LIBEPHEMERIS_LEB_READER", "backend default"),
        "timers": {"wall": "perf_counter", "cpu": "process_time"},
        "versions": {name: version(name) for name in ("kerykeion", "libephemeris", "pydantic", "svg-polish")},
        "rounds": args.rounds,
        "warmup": args.warmup,
        "iterations": args.iterations,
        "theme": "classic",
        "offline": True,
    }
    if BACKEND_NAME == "libephemeris":
        import libephemeris

        environment.update(mode=libephemeris.get_calc_mode(), tier=libephemeris.get_precision_tier())
    results = {}

    def measure(label, func, *, iterations=None):
        """Record the configured timing samples for one named workload."""
        results[label] = bench(
            label,
            func,
            rounds=args.rounds,
            warmup=args.warmup,
            iterations=args.iterations if iterations is None else iterations,
        )

    print(f"Kerykeion benchmark  |  backend: {BACKEND_NAME}")
    print(
        f"Python {sys.version.split()[0]}  |  {args.rounds} rounds, {args.warmup} warmup, {args.iterations} calls/sample"
    )
    print("=" * 72)

    # Pre-create subjects for aspects/chart benchmarks
    subjects = [create_subject(*d) for d in SUBJECTS_DATA]

    # ------------------------------------------------------------------
    # 1. Subject creation
    # ------------------------------------------------------------------
    print("\n[1] Subject creation")

    measure("Single subject (John Lennon)", lambda: create_subject(*SUBJECTS_DATA[0]))

    measure(f"Batch {BATCH_SIZE} subjects", lambda: [create_subject(*d) for d in SUBJECTS_DATA])

    measure(
        "Subject with all optional calcs",
        lambda: AstrologicalSubjectFactory.from_birth_data(
            "Full",
            1990,
            1,
            1,
            12,
            0,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            calculate_dignities=True,
            calculate_nakshatra=True,
            calculate_gauquelin=True,
            calculate_nutation=True,
            calculate_local_space=True,
        ),
    )

    measure(
        "Subject sidereal LAHIRI",
        lambda: AstrologicalSubjectFactory.from_birth_data(
            "Sidereal",
            1940,
            10,
            9,
            18,
            30,
            lat=53.4084,
            lng=-2.9916,
            tz_str="Europe/London",
            online=False,
            suppress_geonames_warning=True,
            zodiac_type="Sidereal",
            sidereal_mode="LAHIRI",
        ),
    )

    # ------------------------------------------------------------------
    # 2. Aspects
    # ------------------------------------------------------------------
    print("\n[2] Aspects calculation")

    measure("Natal aspects", lambda: AspectsFactory.single_chart_aspects(subjects[0]))

    measure("Synastry aspects", lambda: AspectsFactory.dual_chart_aspects(subjects[0], subjects[2]))

    # ------------------------------------------------------------------
    # 3. Chart SVG rendering
    # ------------------------------------------------------------------
    print("\n[3] Chart SVG rendering")

    chart_data_natal = ChartDataFactory.create_chart_data("Natal", subjects[0])
    chart_data_synastry = ChartDataFactory.create_chart_data("Synastry", subjects[0], subjects[2])
    for label, data in (("Natal", chart_data_natal), ("Synastry", chart_data_synastry)):
        for style in ("classic", "modern"):
            measure(
                f"{label} SVG ({style})",
                lambda data=data, style=style: ChartDrawer(data, theme="classic", style=style).generate_svg_string(),
            )
            measure(
                f"{label} wheel ({style})",
                lambda data=data, style=style: ChartDrawer(
                    data, theme="classic", style=style
                ).generate_wheel_only_svg_string(),
            )
        measure(
            f"{label} aspect grid",
            lambda data=data: ChartDrawer(data, theme="classic").generate_aspect_grid_only_svg_string(),
        )
    measure(
        "Natal SVG (modern, minified)",
        lambda: ChartDrawer(chart_data_natal, style="modern").generate_svg_string(minify=True),
        iterations=1,
    )
    measure("ChartData creation (Natal)", lambda: ChartDataFactory.create_chart_data("Natal", subjects[0]))
    measure("Translation pair (EN)", lambda: load_language_pair("EN"))
    measure("Astrocartography (step 1 degree)", lambda: AstroCartographyFactory.compute(subjects[0]))
    measure(
        "Astrocartography (step 0.1 degree)",
        lambda: AstroCartographyFactory.compute(subjects[0], step=0.1),
        iterations=1,
    )

    print("\n[4] Full pipeline (create subject + ChartData + SVG)")

    def full_pipeline(style):
        """Calculate a fresh subject and render a complete natal chart."""
        subject = create_subject(*SUBJECTS_DATA[0])
        data = ChartDataFactory.create_chart_data("Natal", subject)
        return ChartDrawer(data, theme="classic", style=style).generate_svg_string()

    for style in ("classic", "modern"):
        measure(f"Full natal pipeline ({style})", lambda style=style: full_pipeline(style))

    if args.json_path:
        args.json_path.write_text(json.dumps({"environment": environment, "results": results}, indent=2) + "\n")

    print("\n" + "=" * 72)
    print("Done.")


if __name__ == "__main__":
    main()
