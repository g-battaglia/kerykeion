"""Minimal public-API reproductions of v4 migration gaps (no Swiss inputs)."""

import importlib
import json

from kerykeion.ephemeris_backend import ephe as e
from kerykeion.schemas.literals import SiderealMode
from typing import get_args


def setup(mode=None, topo=False):
    e.reset_session()
    e.set_calc_mode("leb")
    e.set_precision_tier("extended")
    e.set_network_policy("sealed")
    e.set_iers_delta_t_enabled(False)
    if mode is not None:
        e.set_sid_mode(mode)
    if topo:
        e.set_topo(12.5, 41.9, 80.0)


def reset(token):
    if hasattr(token, "reset"):
        return token.reset()
    token.var.reset(token)
    return True


def main():
    out = {"version": e.__version__, "crossings": {}, "sidereal_modes": {}}
    natal = e.julday(1990, 6, 15, 12.0)
    start = e.julday(2024, 1, 1, 0.0)
    for name, body, search, extra in [
        ("solar_sidereal", e.SUN, e.solcross_ut, e.FLG_SIDEREAL),
        ("lunar_sidereal", e.MOON, e.mooncross_ut, e.FLG_SIDEREAL),
        (
            "helio_mars_sidereal",
            e.MARS,
            lambda target, jd, flags: e.helio_cross_ut(e.MARS, target, jd, flags),
            e.FLG_SIDEREAL | e.FLG_HELCTR,
        ),
        ("solar_topocentric", e.SUN, e.solcross_ut, e.FLG_TOPOCTR),
        ("lunar_topocentric", e.MOON, e.mooncross_ut, e.FLG_TOPOCTR),
        (
            "generic_solar_sidereal",
            e.SUN,
            lambda target, jd, flags: e.cross_ut(e.SUN, target, jd, flags),
            e.FLG_SIDEREAL,
        ),
    ]:
        setup(e.SIDM_LAHIRI, bool(extra & e.FLG_TOPOCTR))
        flags = e.FLG_SWIEPH | e.FLG_SPEED | extra
        target = e.calc_ut(natal, body, flags)[0][0]
        try:
            crossing = search(target, start, flags)
            actual = e.calc_ut(crossing, body, flags)[0][0]
            out["crossings"][name] = {
                "target": target,
                "crossing_jd": crossing,
                "longitude_at_crossing": actual,
                "residual_degree": abs((actual - target + 180.0) % 360.0 - 180.0),
            }
        except Exception as exc:
            out["crossings"][name] = {"error": type(exc).__name__, "message": str(exc)}

    for mode in get_args(SiderealMode):
        if mode == "USER":
            continue
        setup(getattr(e, "SIDM_" + mode))
        try:
            e.calc_ut(start, e.SUN, e.FLG_SWIEPH | e.FLG_SPEED | e.FLG_SIDEREAL)
            out["sidereal_modes"][mode] = {"ok": True}
        except Exception as exc:
            out["sidereal_modes"][mode] = {"error": type(exc).__name__, "message": str(exc)}

    # Modern-epoch success must not hide observer/tier routing failures in
    # historical live-anchor calculations. Keep errors visible in the output.
    out["historical_sidereal_modes"] = {}
    out["historical_fixed_stars"] = {}
    for year in [-500, 1000, 1700, 2000]:
        jd = e.julday(year, 6, 15, 12.0)
        modes = {}
        for mode in get_args(SiderealMode):
            if mode == "USER":
                continue
            setup(getattr(e, "SIDM_" + mode))
            try:
                e.calc_ut(jd, e.SUN, e.FLG_SWIEPH | e.FLG_SPEED | e.FLG_SIDEREAL)
                modes[mode] = {"ok": True}
            except Exception as exc:
                modes[mode] = {"error": type(exc).__name__, "message": str(exc)}
        out["historical_sidereal_modes"][str(year)] = modes
        stars = {}
        setup()
        for name in ["Regulus", "Spica", "Aldebaran"]:
            try:
                e.fixstar_ut(name, jd, e.FLG_SWIEPH | e.FLG_SPEED)
                stars[name] = {"ok": True}
            except Exception as exc:
                stars[name] = {"error": type(exc).__name__, "message": str(exc)}
        out["historical_fixed_stars"][str(year)] = stars

    setup()
    outer = e.start_tracing()
    e.calc_ut(start, e.SUN, e.FLG_SPEED)
    before = e.get_trace_results()
    inner = e.start_tracing()
    e.calc_ut(start, e.MOON, e.FLG_SPEED)
    reset(inner)
    out["nested_trace"] = {"parent_before": before, "parent_after": e.get_trace_results(), "outer_reset": reset(outer)}
    token = e.start_tracing()
    e.fixstar_ut("Regulus", start, e.FLG_SPEED)
    out["fixed_star_trace"] = e.get_trace_results()
    reset(token)
    net = importlib.import_module("libephemeris.net")
    out["net_exports"] = {name: hasattr(net, name) for name in ["NetworkSealedError", "require_network"]}
    e.set_precision_tier("medium")
    try:
        e.calc_ut(start, e.SUN, e.FLG_SWIEPH | e.FLG_SPEED)
        out["mixed_tier_directory"] = {"ok": True}
    except Exception as exc:
        out["mixed_tier_directory"] = {"error": type(exc).__name__, "message": str(exc)}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
