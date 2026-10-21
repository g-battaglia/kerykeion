"""Isolated, repeated backend benchmarks; no Swiss numeric outputs are saved.

Run from the dedicated worktree (after the test suite, not concurrently):
    .venv/bin/python scripts/benchmark_backends.py \
        --reference-python /path/to/main/.venv/bin/python \
        --reference-root /path/to/main --output validation_output/benchmarks.json

Each backend gets fresh processes, identical epochs/flags and explicit data paths.
Rust and v3 read the same local LEB groups. Timings include Python/PyO3 overhead;
this is not a standalone Rust executable benchmark. Cold means a fresh process,
not an emptied OS filesystem cache. No downloads or cache deletion are performed.
"""

from __future__ import annotations

import argparse
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time


def worker(rounds: int, warmup: int) -> dict:
    started = time.perf_counter()
    import kerykeion
    from kerykeion import AstrologicalSubjectFactory, AspectsFactory, ChartDataFactory, ChartDrawer
    from kerykeion.ephemeris_backend import BACKEND_NAME, ephe

    imported = time.perf_counter() - started
    if BACKEND_NAME == "libephemeris":
        ephe.set_iers_delta_t_enabled(False)
    else:
        # Kerykeion configures this at session entry; direct-kernel preflight
        # runs before the first subject/session, so configure it explicitly.
        ephe.set_ephe_path(os.environ["KERYKEION_EPHE_PATH"])
    flags = ephe.FLG_SWIEPH | ephe.FLG_SPEED
    # Preflight ensures the Swiss timing is not silently measuring Moshier.
    for body in range(10):
        _, returned = ephe.calc_ut(2451545.0, body, flags)
        if BACKEND_NAME == "swisseph" and not returned & ephe.FLG_SWIEPH:
            raise RuntimeError(f"Swiss data unavailable for body {body}: flags={returned}")

    points = [
        "Sun",
        "Moon",
        "Mercury",
        "Venus",
        "Mars",
        "Jupiter",
        "Saturn",
        "Uranus",
        "Neptune",
        "Pluto",
        "Ascendant",
        "Medium_Coeli",
    ]

    def subject(index=0, **kwargs):
        return AstrologicalSubjectFactory.from_birth_data(
            f"Benchmark {index}",
            1990 + index,
            6,
            15,
            12,
            0,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
            active_points=points,
            **kwargs,
        )

    before = time.perf_counter()
    first = subject()
    cold_subject = time.perf_counter() - before
    second = subject(1)
    chart = ChartDataFactory.create_chart_data("Natal", first)

    def positions():
        for day in range(10):
            for body in range(10):
                ephe.calc_ut(2451545.0 + day * 31.125, body, flags)

    def houses():
        for day in range(100):
            ephe.houses_ex(2451545.0 + day * 0.125, 41.9028, 12.4964, b"P", 0)

    def pipeline():
        s = subject()
        c = ChartDataFactory.create_chart_data("Natal", s)
        return ChartDrawer(c, theme="classic").generate_svg_string()

    operations = {
        "calc_ut_100": positions,
        "houses_100": houses,
        "subject_common_12_points": subject,
        "subject_default_points": lambda: AstrologicalSubjectFactory.from_birth_data(
            "Default",
            1990,
            6,
            15,
            12,
            0,
            lat=41.9028,
            lng=12.4964,
            tz_str="Europe/Rome",
            online=False,
            suppress_geonames_warning=True,
        ),
        "subject_batch_5": lambda: [subject(i) for i in range(5)],
        "subject_sidereal_lahiri": lambda: subject(zodiac_type="Sidereal", sidereal_mode="LAHIRI"),
        "subject_optional_calculations": lambda: subject(
            calculate_dignities=True,
            calculate_nakshatra=True,
            calculate_gauquelin=True,
            calculate_nutation=True,
            calculate_local_space=True,
        ),
        "natal_aspects": lambda: AspectsFactory.single_chart_aspects(first),
        "synastry_aspects": lambda: AspectsFactory.dual_chart_aspects(first, second),
        "natal_svg": lambda: ChartDrawer(chart, theme="classic").generate_svg_string(),
        "full_natal_pipeline": pipeline,
    }
    results = {}
    for label, operation in operations.items():
        for _ in range(warmup):
            operation()
        samples = []
        for _ in range(rounds):
            before = time.perf_counter()
            operation()
            samples.append(time.perf_counter() - before)
        results[label] = {
            "median_s": statistics.median(samples),
            "min_s": min(samples),
            "max_s": max(samples),
            "samples_s": samples,
        }
    metadata_samples = []
    if BACKEND_NAME == "libephemeris":
        for _ in range(3):
            before = time.perf_counter()
            ephe.get_body_coverage(ephe.SUN, 2451545.0)
            metadata_samples.append(time.perf_counter() - before)
    inventory = ephe.get_leb_inventory() if BACKEND_NAME == "libephemeris" else None
    return {
        "backend": BACKEND_NAME,
        "backend_version": ephe.__version__ if BACKEND_NAME == "libephemeris" else version("pyswisseph"),
        "backend_build_identifier": getattr(ephe, "__version__", None),
        "python": sys.version,
        "python_executable": sys.executable,
        "kerykeion_path": kerykeion.__file__,
        "ephemeris_path": ephe.__file__,
        "fresh_import_s": imported,
        "first_subject_after_preflight_s": cold_subject,
        "inventory": inventory,
        "raw_native_metadata_coverage_samples_s": metadata_samples,
        "rounds": rounds,
        "warmup": warmup,
        "operations": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--reference-python", type=Path)
    parser.add_argument("--reference-root", type=Path)
    parser.add_argument("--swiss-path", type=Path, default=Path.home() / ".kerykeion/sweph")
    parser.add_argument("--data-dir", type=Path, default=Path.home() / ".libephemeris")
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--processes", type=int, default=3)
    parser.add_argument("--output", type=Path, default=Path("validation_output/benchmarks.json"))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.rounds, args.warmup)))
        return
    if not args.reference_python or not args.reference_root:
        parser.error("--reference-python and --reference-root are required")
    root = Path(__file__).resolve().parents[1]
    configurations = [
        ("rust_v4", sys.executable, root, "libephemeris"),
        ("python_v3", str(args.reference_python.absolute()), args.reference_root.absolute(), "libephemeris"),
        ("swisseph", sys.executable, root, "swisseph"),
    ]
    output = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "clock": "perf_counter",
        "tier": "base",
        "iers_delta_t": False,
        "notes": "Sequential processes; fresh-process import, warm OS cache; no standalone Rust timings.",
        "runs": {label: [] for label, *_ in configurations},
    }
    for repetition in range(args.processes):
        # Rotate order to reduce systematic thermal/order bias.
        order = configurations[repetition % 3 :] + configurations[: repetition % 3]
        for label, python, source, backend in order:
            env = os.environ.copy()
            for key in list(env):
                if key.startswith(("KERYKEION_", "LIBEPHEMERIS_")):
                    del env[key]
            env.update(
                {
                    "PYTHONPATH": str(source),
                    "KERYKEION_BACKEND": backend,
                    "KERYKEION_LEB_MODE": "leb",
                    "LIBEPHEMERIS_PRECISION": "base",
                    "LIBEPHEMERIS_DATA_DIR": str(args.data_dir.absolute()),
                    "LIBEPHEMERIS_NETWORK_POLICY": "sealed",
                    "LIBEPHEMERIS_IERS_DELTA_T": "0",
                    "KERYKEION_EPHE_PATH": str(args.swiss_path.absolute()),
                }
            )
            command = [
                python,
                str(Path(__file__).resolve()),
                "--worker",
                "--rounds",
                str(args.rounds),
                "--warmup",
                str(args.warmup),
            ]
            before = time.perf_counter()
            result = subprocess.run(command, cwd=source, env=env, text=True, capture_output=True)
            if result.returncode:
                raise RuntimeError(f"{label} worker failed ({result.returncode}):\n{result.stderr}")
            record = json.loads(result.stdout)
            record["whole_worker_wall_s"] = time.perf_counter() - before
            output["runs"][label].append(record)
            print(f"{label} process {repetition + 1}: {record['whole_worker_wall_s']:.3f}s", flush=True)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(output, indent=2) + "\n")
    rust_files = output["runs"]["rust_v4"][0]["inventory"]["files"]
    v3_files = output["runs"]["python_v3"][0]["inventory"]["files"]
    if sorted((f["path"], f["size_bytes"]) for f in rust_files) != sorted(
        (f["path"], f["size_bytes"]) for f in v3_files
    ):
        raise RuntimeError("Backend inventories differ: timings are not an identical-data comparison")
    summary = {}
    for label, runs in output["runs"].items():
        summary[label] = {
            name: statistics.median(run["operations"][name]["median_s"] for run in runs)
            for name in runs[0]["operations"]
        }
    output["median_of_process_medians_s"] = summary
    args.output.write_text(json.dumps(output, indent=2) + "\n")
    print("operation                          Rust ms     v3 ms     Swiss ms   v3/Rust   Swiss/Rust")
    for name, seconds in summary["rust_v4"].items():
        v3, swiss = summary["python_v3"][name], summary["swisseph"][name]
        print(
            f"{name:33} {seconds * 1000:9.3f} {v3 * 1000:9.3f} {swiss * 1000:10.3f} {v3 / seconds:9.2f} {swiss / seconds:12.2f}"
        )


if __name__ == "__main__":
    main()
