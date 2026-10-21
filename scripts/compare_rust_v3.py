"""Compare v4 and Python v3 on identical local inputs (never Swiss fixtures).

Produces diagnostic residuals, not new golden fixtures or relaxed tolerances.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def capture():
    from kerykeion.astrological_subject.factory import STANDARD_PLANETS, TNO_PLANETS
    from kerykeion.ephemeris_backend import ephe

    ephe.set_iers_delta_t_enabled(False)
    ephe.set_topo(12.5, 41.9, 30.0)
    ephe.set_sid_mode(ephe.SIDM_LAHIRI)
    bodies = dict(STANDARD_PLANETS)
    bodies.update({name: ephe.AST_OFFSET + value for name, value in TNO_PLANETS.items()})
    bodies["White_Moon"] = 56
    perspectives = {
        "apparent": 0,
        "true": ephe.FLG_TRUEPOS,
        "equatorial": ephe.FLG_EQUATORIAL,
        "heliocentric": ephe.FLG_HELCTR,
        "topocentric": ephe.FLG_TOPOCTR,
        "sidereal_lahiri": ephe.FLG_SIDEREAL,
        "sidereal_aldebaran_15tau": ephe.FLG_SIDEREAL,
    }
    rows = {}
    for year in [-500, 1000, 1700, 1900, 1940, 1963, 2000, 2024, 2100]:
        jd = ephe.julday(year, 6, 15, 12.0)
        for perspective, flag in perspectives.items():
            if perspective.startswith("sidereal_"):
                ephe.set_sid_mode(ephe.SIDM_ALDEBARAN_15TAU if "aldebaran" in perspective else ephe.SIDM_LAHIRI)
            for body, body_id in bodies.items():
                key = f"{year}/{perspective}/{body}"
                try:
                    values, returned = ephe.calc_ut(jd, body_id, ephe.FLG_SWIEPH | ephe.FLG_SPEED | flag)
                    rows[key] = {"values": list(values), "flags": returned}
                except Exception as exc:
                    rows[key] = {"error": type(exc).__name__, "message": str(exc)}
    from typing import get_args
    from kerykeion.schemas.literals import SiderealMode

    ayanamsas = {}
    jd = ephe.julday(1940, 10, 9, 17.5)
    for mode in get_args(SiderealMode):
        if mode == "USER":
            continue
        ephe.set_sid_mode(getattr(ephe, f"SIDM_{mode}"))
        ayanamsas[mode] = ephe.get_ayanamsa_ex_ut(jd, ephe.FLG_SWIEPH)[1]
    stars = {}
    for name in ["Regulus", "Spica", "Aldebaran", "Antares", "Sirius"]:
        stars[name] = list(ephe.fixstar_ut(name, jd, ephe.FLG_SWIEPH | ephe.FLG_SPEED)[0])
    return {
        "version": ephe.__version__,
        "inventory": ephe.get_leb_inventory(),
        "rows": rows,
        "ayanamsas": ayanamsas,
        "fixed_stars": stars,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--reference-python", type=Path)
    parser.add_argument("--reference-root", type=Path)
    parser.add_argument("--output", type=Path, default=Path("validation_output/numeric-comparison.json"))
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(capture()))
        return
    if not args.reference_python or not args.reference_root:
        parser.error("reference Python and source are required")
    root = Path(__file__).resolve().parents[1]
    records = {}
    for name, python, source in [
        ("rust_v4", sys.executable, root),
        ("python_v3", str(args.reference_python.absolute()), args.reference_root.absolute()),
    ]:
        env = os.environ.copy()
        for key in list(env):
            if key.startswith(("LIBEPHEMERIS_", "KERYKEION_")):
                del env[key]
        env.update(
            {
                "PYTHONPATH": str(source),
                "KERYKEION_BACKEND": "libephemeris",
                "LIBEPHEMERIS_PRECISION": "extended",
                "KERYKEION_LEB_MODE": "leb",
                "LIBEPHEMERIS_NETWORK_POLICY": "sealed",
            }
        )
        result = subprocess.run(
            [python, str(Path(__file__).resolve()), "--worker"],
            cwd=source,
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        records[name] = json.loads(result.stdout)
    summary = {
        "cases": len(records["rust_v4"]["rows"]),
        "both_success": 0,
        "both_error": 0,
        "one_sided_errors": [],
        "flag_differences": [],
        "max_abs_residuals": [0.0] * 6,
        "max_residual_cases": [None] * 6,
        "position_above_0.01_degree": [],
        "angular_speed_above_0.0001_degree_per_day": [],
    }
    for key, rust in records["rust_v4"]["rows"].items():
        reference = records["python_v3"]["rows"][key]
        if "error" in rust or "error" in reference:
            if "error" in rust and "error" in reference:
                summary["both_error"] += 1
            else:
                summary["one_sided_errors"].append({"case": key, "rust": rust, "v3": reference})
            continue
        summary["both_success"] += 1
        if rust["flags"] != reference["flags"]:
            summary["flag_differences"].append(key)
        residuals = [abs(a - b) for a, b in zip(rust["values"], reference["values"])]
        residuals[0] = abs((rust["values"][0] - reference["values"][0] + 180) % 360 - 180)
        for component, difference in enumerate(residuals):
            if difference > summary["max_abs_residuals"][component]:
                summary["max_abs_residuals"][component] = difference
                summary["max_residual_cases"][component] = key
        if max(residuals[:2]) > 0.01:
            summary["position_above_0.01_degree"].append({"case": key, "residuals": residuals})
        if max(residuals[3:5]) > 0.0001:
            summary["angular_speed_above_0.0001_degree_per_day"].append({"case": key, "residuals": residuals})
    summary["ayanamsa_residuals_degree"] = {
        name: abs(value - records["python_v3"]["ayanamsas"][name])
        for name, value in records["rust_v4"]["ayanamsas"].items()
    }
    summary["fixed_star_residuals"] = {
        name: [abs(a - b) for a, b in zip(values, records["python_v3"]["fixed_stars"][name])]
        for name, values in records["rust_v4"]["fixed_stars"].items()
    }
    records["summary"] = summary
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
