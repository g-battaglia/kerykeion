"""Reproduce native path integration with a sealed, bundled-base runtime.

Run with either supported Python interpreter after installing the candidate.
The probe uses only a temporary empty data directory and performs no downloads.
"""

from __future__ import annotations

import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import sys
import tempfile


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="kerykeion-native-path-") as temporary:
        root = Path(temporary)
        data = root / "data"
        data.mkdir()
        config = root / "libephemeris.toml"
        config.write_text(
            "[libephemeris]\n"
            f"data_dir = {json.dumps(str(data))}\n"
            'precision = "base"\nmode = "leb"\nnetwork_policy = "sealed"\n'
            'leb_reader = "indexed"\nauto_spk = false\n'
            "iers_auto_download = false\niers_delta_t = false\n"
        )
        for key in list(os.environ):
            if key.startswith(("LIBEPHEMERIS_", "KERYKEION_")):
                os.environ.pop(key)
        os.environ.update(
            LIBEPHEMERIS_CONFIG=str(config), KERYKEION_BACKEND="libephemeris", KERYKEION_LEB_MODE="leb"
        )

        import libephemeris as le
        from kerykeion.ephemeris_backend import backend
        from kerykeion.moon_phase_details import utils

        assert le.get_network_policy() == "sealed"
        assert le.get_calc_mode() == "leb"
        assert le.get_precision_tier() == "base"
        expected_path = le.get_library_path()
        le.release_data_cache()
        flags = le.FLG_SWIEPH | le.FLG_SPEED
        dates = (2440000.5, 2451545.0, 2459215.5, 2460000.5, 2462502.5)

        def controls():
            with backend.EPHEMERIS_LOCK:
                planets = [[le.calc_ut(jd, body, flags) for body in range(10)] for jd in dates]
                houses = [le.houses_ex(jd, 51.48, 0.0, b"P") for jd in dates]
                assert all(len(row[0]) == 12 for row in houses)
                le.set_sid_mode(le.SIDM_LAHIRI)
                sidereal = [le.calc_ut(jd, le.SUN, flags | le.FLG_SIDEREAL) for jd in dates]
                backend.reset_ephemeris_session()
                return planets, houses, sidereal

        before = controls()
        setter = le.set_ephe_path
        calls = []

        def tracked_setter(path):
            assert path != "", "Kerykeion forwarded the empty native path sentinel"
            calls.append(path)
            setter(path)

        le.set_ephe_path = tracked_setter
        try:
            phase_before = utils.compute_lunar_phase_jd(2451545.0, 0.0, forward=True)
            assert phase_before is not None
            for _ in range(5):
                with backend.ephemeris_session():
                    assert utils.configure_ephemeris_path() == le.FLG_SWIEPH
                assert le.get_library_path() == expected_path
                le.release_data_cache()
                utils.configure_ephemeris_path()
                assert le.get_library_path() == expected_path
                le.release_data_cache()
            assert calls == [], "Default helpers must preserve warm native discovery"

            custom = root / "custom"
            custom.mkdir()
            with backend.ephemeris_session(ephe_path=str(custom)):
                assert le.get_library_path() == str(custom)
                utils.configure_ephemeris_path()
                assert le.get_library_path() == str(custom), "Lunar helper replaced the session override"
                assert le.calc_ut(2451545.0, le.SUN, flags) == before[0][1][0]
            utils.configure_ephemeris_path()
            assert le.get_library_path() == expected_path

            with backend.ephemeris_session(ephe_path=str(custom)):
                pass
            external = root / "external"
            external.mkdir()
            le.set_ephe_path(str(external))
            utils.configure_ephemeris_path()
            with backend.ephemeris_session():
                assert le.get_library_path() == str(external), "External override was erased"
            setter(None)
            assert utils.compute_lunar_phase_jd(2451545.0, 0.0, forward=True) == phase_before
            assert le.get_library_path() == expected_path
            le.release_data_cache()
            assert controls() == before, "Path setup changed LEB planetary/house/sidereal results"
        finally:
            le.set_ephe_path = setter
            setter(None)

        # Pin the documented new native contract without pretending that the
        # already-published b2 package itself has been repaired.
        if le.__version__ == "4.0.0b2":
            try:
                setter("")
                try:
                    le.get_library_path()
                except le.DataNotFoundError:
                    empty_contract = "known-b2-empty-path-error; integration-never-forwards-empty"
                else:
                    raise AssertionError("The published b2 negative control no longer reproduces")
            finally:
                setter(None)
        elif le.__version__ == "4.0.0b3":
            # Retained only for reproducing the superseded prepared b3 build.
            setter("")
            assert le.get_library_path() == expected_path
            le.release_data_cache()
            setter(".")
            assert le.get_library_path() == str(Path.cwd()), "Dot must remain an explicit current directory"
            setter(None)
            empty_contract = "empty-restores-default; dot-selects-current-directory"
        else:
            setter("")
            assert le.get_library_path() == str(Path.cwd())
            le.release_data_cache()
            setter(".")
            assert le.get_library_path() == str(Path.cwd())
            setter(None)
            assert le.get_library_path() == expected_path
            le.release_data_cache()
            empty_contract = "empty-and-dot-select-current-directory; none-restores-default"

        print(json.dumps({
            "python": sys.version.split()[0], "libephemeris": le.__version__,
            "system": platform.system(), "machine": platform.machine(),
            "kerykeion_distribution": version("kerykeion"), "network_policy": le.get_network_policy(),
            "precision": le.get_precision_tier(), "repeated_sessions": 5,
            "planetary_controls": 50, "house_controls": 60, "sidereal_controls": 5,
            "controls_sha256": hashlib.sha256(json.dumps(before).encode()).hexdigest(),
            "lunar_phase_jd": phase_before, "empty_path_contract": empty_contract,
            "adapter_sha256": hashlib.sha256(Path(backend.__file__).read_bytes()).hexdigest(),
            "lunar_helpers_sha256": hashlib.sha256(Path(utils.__file__).read_bytes()).hexdigest(),
        }))


if __name__ == "__main__":
    main()
