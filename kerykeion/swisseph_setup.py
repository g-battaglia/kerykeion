"""Swiss Ephemeris data setup utility.

Downloads the Swiss Ephemeris data files needed for the swisseph backend.
These files are NOT bundled with Kerykeion to avoid inheriting the AGPL-3.0
license of Swiss Ephemeris (Astrodienst AG).

Usage::

    python -m kerykeion.swisseph_setup          # interactive (asks confirmation)
    python -m kerykeion.swisseph_setup --yes     # non-interactive (CI/scripts)
    python -m kerykeion.swisseph_setup --target /custom/path

Files are downloaded from the official Swiss Ephemeris GitHub repository
(https://github.com/aloistr/swisseph) maintained by Astrodienst AG.

Default install location: ~/.kerykeion/sweph/
"""

from __future__ import annotations

import argparse
import logging
import sys
import urllib.error
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

_GITHUB_BASE = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"

_MAIN_FILES = [
    "seas_18.se1",
    "semo_18.se1",
    "sepl_18.se1",
    "sefstars.txt",
]

_ASTEROID_FILES = [
    ("ast136", "s136108s.se1"),  # Haumea (136108)
    ("ast136", "s136199s.se1"),  # Eris (136199)
    ("ast136", "s136472s.se1"),  # Makemake (136472)
    ("ast28", "se28978s.se1"),   # Ixion (28978)
    ("ast50", "se50000s.se1"),   # Quaoar (50000)
    ("ast90", "se90377s.se1"),   # Sedna (90377)
    ("ast90", "se90482s.se1"),   # Orcus (90482)
]

_ASTEROID_DROPBOX_URL = (
    "https://www.dropbox.com/scl/fo/y3naz62gy6f6qfrhquu7u/h"
    "?rlkey=ejltdhb262zglm7eo6yfj2940&dl=0"
)

_ASTEROID_INSTRUCTIONS = """\
  TNO/dwarf planet ephemeris files (Eris, Sedna, Haumea, etc.) are not
  available from GitHub. To enable full TNO support with swisseph:

  1. Download asteroid files from the official Astrodienst Dropbox:
     {dropbox_url}
     (look in the 'long_ast' folder)

  2. Place them in subdirectories under your data path:
     {target}/ast136/s136108s.se1   (Haumea)
     {target}/ast136/s136199s.se1   (Eris)
     {target}/ast136/s136472s.se1   (Makemake)
     {target}/ast28/se28978s.se1    (Ixion)
     {target}/ast50/se50000s.se1    (Quaoar)
     {target}/ast90/se90377s.se1    (Sedna)
     {target}/ast90/se90482s.se1    (Orcus)

  Without these files, planets and fixed stars work normally;
  only TNO/dwarf planet calculations are unavailable.\
"""

_LICENSE_WARNING = """\
╔══════════════════════════════════════════════════════════════════════╗
║                 Swiss Ephemeris — License Notice                    ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                     ║
║  The Swiss Ephemeris data files are created and maintained by        ║
║  Astrodienst AG (Zurich, Switzerland) and are distributed under     ║
║  the AGPL-3.0 license.                                              ║
║                                                                     ║
║  By downloading these files, you accept the terms of the AGPL-3.0   ║
║  license for the Swiss Ephemeris data.                              ║
║                                                                     ║
║  More info: https://www.astro.com/swisseph                          ║
║  License:   https://www.gnu.org/licenses/agpl-3.0.html              ║
║                                                                     ║
║  NOTE: Kerykeion itself does not require these files.               ║
║  The default backend (libephemeris) works without them.             ║
║                                                                     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

_DEFAULT_TARGET = Path.home() / ".kerykeion" / "sweph"


def _download_file(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"  skip (exists): {dest.name}")
        return True
    try:
        print(f"  downloading:   {dest.name} ... ", end="", flush=True)
        urllib.request.urlretrieve(url, dest)
        size_kb = dest.stat().st_size / 1024
        print(f"OK ({size_kb:.0f} KB)")
        return True
    except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
        print(f"FAILED ({exc})")
        if dest.exists():
            dest.unlink()
        return False


def download_swisseph_data(target: Path, *, skip_asteroids: bool = False) -> dict:
    """Download Swiss Ephemeris data files to *target*.

    Returns a dict with 'main' and 'asteroids' lists of downloaded file paths,
    and 'failed' list of files that could not be downloaded.
    """
    target.mkdir(parents=True, exist_ok=True)
    result: dict = {"main": [], "asteroids": [], "failed": []}

    print(f"\nTarget directory: {target}\n")

    print("Main ephemeris files (from GitHub):")
    for name in _MAIN_FILES:
        dest = target / name
        url = f"{_GITHUB_BASE}/{name}"
        if _download_file(url, dest):
            result["main"].append(str(dest))
        else:
            result["failed"].append(name)

    if skip_asteroids:
        print("\nAsteroid files: skipped (--skip-asteroids)")
        return result

    print("\nTNO/dwarf planet ephemeris files:")
    existing = []
    for subdir, name in _ASTEROID_FILES:
        dest = target / subdir / name
        if dest.exists() and dest.stat().st_size > 0:
            existing.append(f"{subdir}/{name}")
            result["asteroids"].append(str(dest))
    if existing:
        for f in existing:
            print(f"  found:         {f}")
    missing = [(s, n) for s, n in _ASTEROID_FILES if f"{s}/{n}" not in existing]
    if missing:
        print(_ASTEROID_INSTRUCTIONS.format(
            dropbox_url=_ASTEROID_DROPBOX_URL, target=target,
        ))

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Swiss Ephemeris data files for the swisseph backend.",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=_DEFAULT_TARGET,
        help=f"Target directory (default: {_DEFAULT_TARGET})",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip license confirmation (for CI/scripts)",
    )
    parser.add_argument(
        "--skip-asteroids",
        action="store_true",
        help="Skip TNO/asteroid ephemeris files",
    )
    args = parser.parse_args()

    print(_LICENSE_WARNING)

    if not args.yes:
        try:
            answer = input("Do you accept the AGPL-3.0 license terms? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nAborted.")
            sys.exit(1)
        if answer not in ("y", "yes"):
            print("Download cancelled.")
            sys.exit(0)

    result = download_swisseph_data(args.target, skip_asteroids=args.skip_asteroids)

    main_ok = len(result["main"])
    ast_ok = len(result["asteroids"])
    failed = len(result["failed"])

    print(f"\n{'='*60}")
    print(f"Downloaded: {main_ok} main files, {ast_ok} asteroid files")
    if failed:
        print(f"Failed:     {failed} files")
    print(f"Location:   {args.target}")

    print("\nTo use the swisseph backend, set these environment variables:\n")
    print("  export KERYKEION_BACKEND=swisseph")
    print(f"  export KERYKEION_EPHE_PATH={args.target}")
    print()


if __name__ == "__main__":
    main()
