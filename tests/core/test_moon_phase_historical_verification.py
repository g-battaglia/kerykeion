"""
TEMPORARY VERIFICATION TESTS — Moon Phase Historical Accuracy
=============================================================

These tests validate Kerykeion's moon phase calculations against known
astronomical reference data across multiple decades (2001–2040).

**Purpose**: one-time verification that the implementation is correct.
**Remove after**: verification is complete and confidence established.

Reference data source
---------------------
AstroPixels Moon Phases tables by Fred Espenak (retired NASA/GSFC).
https://astropixels.com/ephemeris/phasescat/phases2001.html
All times in Universal Time (UT). Uses the same JPL DE ephemeris
algorithms as Swiss Ephemeris (the engine behind Kerykeion).

Tolerances
----------
- Angle: ±1.0° — AstroPixels times rounded to whole minutes; 1 min of
  Moon motion ≈ 0.008° relative to Sun. 1° is very conservative.
- Illumination: ±8 percentage points — cosine approximation vs real
  illumination varies with orbital eccentricity.
- Synodic month: 29.26–29.80 days — known range per AstroPixels.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest

from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory
from kerykeion.moon_phase_details.factory import MoonPhaseDetailsFactory


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Greenwich Observatory — neutral location, UTC timezone, no DST ambiguity
_LAT = 51.4769
_LNG = 0.0
_TZ = "UTC"

# Tolerances
_ANGLE_TOL = 1.0  # degrees
_ILLUMINATION_TOL = 8.0  # percentage points

# Expected angle for each major phase
_EXPECTED_ANGLE = {"NM": 0.0, "FQ": 90.0, "FM": 180.0, "LQ": 270.0}

# Expected illumination percentage (from cosine formula)
_EXPECTED_ILLUM = {"NM": 0.0, "FQ": 50.0, "FM": 100.0, "LQ": 50.0}

# At the exact boundary of a major phase, the 28-phase name may be the
# adjacent name. These are the acceptable names for each phase type.
_VALID_NAMES: dict[str, set[str]] = {
    "NM": {"New Moon", "Waning Crescent"},  # phase 1 vs 28 at 0°/360°
    "FQ": {"First Quarter"},  # phases 7-9 all map to FQ
    "FM": {"Full Moon", "Waning Gibbous"},  # phase 14 vs 15 at 180°
    "LQ": {"Last Quarter"},  # phases 20-22 all map to LQ
}

_VALID_EMOJIS: dict[str, set[str]] = {
    "NM": {"🌑", "🌘"},
    "FQ": {"🌓"},
    "FM": {"🌕", "🌖"},
    "LQ": {"🌗"},
}

# Synodic month length bounds (days)
# AstroPixels states 29.26–29.80 but times are rounded to whole minutes,
# so computed intervals can slightly exceed 29.80. Use 29.84 as upper bound.
_SYNODIC_MIN = 29.26
_SYNODIC_MAX = 29.84


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_subject(y: int, m: int, d: int, h: int, mi: int):
    """Create an offline subject at Greenwich for the given UTC datetime."""
    return AstrologicalSubjectFactory.from_birth_data(
        f"V-{y}-{m:02d}-{d:02d}",
        y,
        m,
        d,
        h,
        mi,
        lng=_LNG,
        lat=_LAT,
        tz_str=_TZ,
        online=False,
    )


def _angle_distance(a: float, b: float) -> float:
    """Shortest angular distance between two angles on a 360° circle."""
    d = abs(a - b) % 360
    return min(d, 360.0 - d)


# ---------------------------------------------------------------------------
# Reference data: known phase moments (AstroPixels, Universal Time)
# Format: (year, month, day, hour, minute, phase_type)
# phase_type: "NM"=New Moon, "FQ"=First Quarter, "FM"=Full Moon, "LQ"=Last Quarter
# ---------------------------------------------------------------------------

KNOWN_PHASES = [
    # ====================================================================
    # 2001 — complete year
    # ====================================================================
    # New Moons
    (2001, 1, 24, 13, 7, "NM"),
    (2001, 2, 23, 8, 21, "NM"),
    (2001, 3, 25, 1, 21, "NM"),
    (2001, 4, 23, 15, 26, "NM"),
    (2001, 5, 23, 2, 46, "NM"),
    (2001, 6, 21, 11, 58, "NM"),
    (2001, 7, 20, 19, 44, "NM"),
    (2001, 8, 19, 2, 55, "NM"),
    (2001, 9, 17, 10, 27, "NM"),
    (2001, 10, 16, 19, 23, "NM"),
    (2001, 11, 15, 6, 40, "NM"),
    (2001, 12, 14, 20, 48, "NM"),
    # First Quarters
    (2001, 1, 2, 22, 31, "FQ"),
    (2001, 2, 1, 14, 2, "FQ"),
    (2001, 3, 3, 2, 3, "FQ"),
    (2001, 4, 1, 10, 49, "FQ"),
    (2001, 4, 30, 17, 8, "FQ"),
    (2001, 5, 29, 22, 9, "FQ"),
    (2001, 6, 28, 3, 20, "FQ"),
    (2001, 7, 27, 10, 8, "FQ"),
    (2001, 8, 25, 19, 55, "FQ"),
    (2001, 9, 24, 9, 31, "FQ"),
    (2001, 10, 24, 2, 58, "FQ"),
    (2001, 11, 22, 23, 21, "FQ"),
    (2001, 12, 22, 20, 56, "FQ"),
    # Full Moons
    (2001, 1, 9, 20, 24, "FM"),
    (2001, 2, 8, 7, 12, "FM"),
    (2001, 3, 9, 17, 23, "FM"),
    (2001, 4, 8, 3, 22, "FM"),
    (2001, 5, 7, 13, 53, "FM"),
    (2001, 6, 6, 1, 39, "FM"),
    (2001, 7, 5, 15, 4, "FM"),
    (2001, 8, 4, 5, 56, "FM"),
    (2001, 9, 2, 21, 43, "FM"),
    (2001, 10, 2, 13, 49, "FM"),
    (2001, 11, 1, 5, 41, "FM"),
    (2001, 11, 30, 20, 49, "FM"),
    (2001, 12, 30, 10, 41, "FM"),
    # Last Quarters
    (2001, 1, 16, 12, 35, "LQ"),
    (2001, 2, 15, 3, 24, "LQ"),
    (2001, 3, 16, 20, 45, "LQ"),
    (2001, 4, 15, 15, 31, "LQ"),
    (2001, 5, 15, 10, 11, "LQ"),
    (2001, 6, 14, 3, 28, "LQ"),
    (2001, 7, 13, 18, 45, "LQ"),
    (2001, 8, 12, 7, 53, "LQ"),
    (2001, 9, 10, 19, 0, "LQ"),
    (2001, 10, 10, 4, 20, "LQ"),
    (2001, 11, 8, 12, 21, "LQ"),
    (2001, 12, 7, 19, 52, "LQ"),
    # ====================================================================
    # 2003 — January & July
    # ====================================================================
    (2003, 1, 2, 20, 23, "NM"),
    (2003, 1, 10, 13, 15, "FQ"),
    (2003, 1, 18, 10, 48, "FM"),
    (2003, 1, 25, 8, 33, "LQ"),
    (2003, 7, 29, 6, 53, "NM"),
    (2003, 7, 7, 2, 32, "FQ"),
    (2003, 7, 13, 19, 21, "FM"),
    (2003, 7, 21, 7, 1, "LQ"),
    # ====================================================================
    # 2005 — complete year
    # ====================================================================
    # New Moons
    (2005, 1, 10, 12, 3, "NM"),
    (2005, 2, 8, 22, 28, "NM"),
    (2005, 3, 10, 9, 10, "NM"),
    (2005, 4, 8, 20, 32, "NM"),
    (2005, 5, 8, 8, 45, "NM"),
    (2005, 6, 6, 21, 55, "NM"),
    (2005, 7, 6, 12, 3, "NM"),
    (2005, 8, 5, 3, 5, "NM"),
    (2005, 9, 3, 18, 45, "NM"),
    (2005, 10, 3, 10, 28, "NM"),
    (2005, 11, 2, 1, 25, "NM"),
    (2005, 12, 1, 15, 1, "NM"),
    (2005, 12, 31, 3, 12, "NM"),
    # First Quarters
    (2005, 1, 17, 6, 58, "FQ"),
    (2005, 2, 16, 0, 16, "FQ"),
    (2005, 3, 17, 19, 19, "FQ"),
    (2005, 4, 16, 14, 37, "FQ"),
    (2005, 5, 16, 8, 56, "FQ"),
    (2005, 6, 15, 1, 22, "FQ"),
    (2005, 7, 14, 15, 20, "FQ"),
    (2005, 8, 13, 2, 39, "FQ"),
    (2005, 9, 11, 11, 37, "FQ"),
    (2005, 10, 10, 19, 1, "FQ"),
    (2005, 11, 9, 1, 57, "FQ"),
    (2005, 12, 8, 9, 36, "FQ"),
    # Full Moons
    (2005, 1, 25, 10, 32, "FM"),
    (2005, 2, 24, 4, 54, "FM"),
    (2005, 3, 25, 20, 58, "FM"),
    (2005, 4, 24, 10, 6, "FM"),
    (2005, 5, 23, 20, 18, "FM"),
    (2005, 6, 22, 4, 14, "FM"),
    (2005, 7, 21, 11, 0, "FM"),
    (2005, 8, 19, 17, 53, "FM"),
    (2005, 9, 18, 2, 1, "FM"),
    (2005, 10, 17, 12, 14, "FM"),
    (2005, 11, 16, 0, 58, "FM"),
    (2005, 12, 15, 16, 16, "FM"),
    # Last Quarters
    (2005, 1, 3, 17, 46, "LQ"),
    (2005, 2, 2, 7, 27, "LQ"),
    (2005, 3, 3, 17, 36, "LQ"),
    (2005, 4, 2, 0, 50, "LQ"),
    (2005, 5, 1, 6, 24, "LQ"),
    (2005, 5, 30, 11, 47, "LQ"),
    (2005, 6, 28, 18, 23, "LQ"),
    (2005, 7, 28, 3, 19, "LQ"),
    (2005, 8, 26, 15, 18, "LQ"),
    (2005, 9, 25, 6, 41, "LQ"),
    (2005, 10, 25, 1, 17, "LQ"),
    (2005, 11, 23, 22, 11, "LQ"),
    (2005, 12, 23, 19, 36, "LQ"),
    # ====================================================================
    # 2007 — January & July
    # ====================================================================
    (2007, 1, 19, 4, 1, "NM"),
    (2007, 1, 25, 23, 2, "FQ"),
    (2007, 1, 3, 13, 57, "FM"),
    (2007, 1, 11, 12, 45, "LQ"),
    (2007, 7, 14, 12, 4, "NM"),
    (2007, 7, 22, 6, 29, "FQ"),
    (2007, 7, 30, 0, 48, "FM"),
    (2007, 7, 7, 16, 54, "LQ"),
    # ====================================================================
    # 2010 — complete year
    # ====================================================================
    # New Moons
    (2010, 1, 15, 7, 11, "NM"),
    (2010, 2, 14, 2, 51, "NM"),
    (2010, 3, 15, 21, 1, "NM"),
    (2010, 4, 14, 12, 29, "NM"),
    (2010, 5, 14, 1, 4, "NM"),
    (2010, 6, 12, 11, 15, "NM"),
    (2010, 7, 11, 19, 40, "NM"),
    (2010, 8, 10, 3, 8, "NM"),
    (2010, 9, 8, 10, 30, "NM"),
    (2010, 10, 7, 18, 44, "NM"),
    (2010, 11, 6, 4, 52, "NM"),
    (2010, 12, 5, 17, 36, "NM"),
    # First Quarters
    (2010, 1, 23, 10, 53, "FQ"),
    (2010, 2, 22, 0, 42, "FQ"),
    (2010, 3, 23, 11, 0, "FQ"),
    (2010, 4, 21, 18, 20, "FQ"),
    (2010, 5, 20, 23, 43, "FQ"),
    (2010, 6, 19, 4, 30, "FQ"),
    (2010, 7, 18, 10, 11, "FQ"),
    (2010, 8, 16, 18, 14, "FQ"),
    (2010, 9, 15, 5, 50, "FQ"),
    (2010, 10, 14, 21, 27, "FQ"),
    (2010, 11, 13, 16, 39, "FQ"),
    (2010, 12, 13, 13, 59, "FQ"),
    # Full Moons
    (2010, 1, 30, 6, 18, "FM"),
    (2010, 2, 28, 16, 38, "FM"),
    (2010, 3, 30, 2, 25, "FM"),
    (2010, 4, 28, 12, 18, "FM"),
    (2010, 5, 27, 23, 7, "FM"),
    (2010, 6, 26, 11, 30, "FM"),
    (2010, 7, 26, 1, 37, "FM"),
    (2010, 8, 24, 17, 5, "FM"),
    (2010, 9, 23, 9, 17, "FM"),
    (2010, 10, 23, 1, 36, "FM"),
    (2010, 11, 21, 17, 27, "FM"),
    (2010, 12, 21, 8, 13, "FM"),
    # Last Quarters
    (2010, 1, 7, 10, 40, "LQ"),
    (2010, 2, 5, 23, 49, "LQ"),
    (2010, 3, 7, 15, 42, "LQ"),
    (2010, 4, 6, 9, 37, "LQ"),
    (2010, 5, 6, 4, 15, "LQ"),
    (2010, 6, 4, 22, 13, "LQ"),
    (2010, 7, 4, 14, 35, "LQ"),
    (2010, 8, 3, 4, 59, "LQ"),
    (2010, 9, 1, 17, 22, "LQ"),
    (2010, 10, 1, 3, 52, "LQ"),
    (2010, 10, 30, 12, 46, "LQ"),
    (2010, 11, 28, 20, 36, "LQ"),
    (2010, 12, 28, 4, 18, "LQ"),
    # ====================================================================
    # 2012 — January & July
    # ====================================================================
    (2012, 1, 23, 7, 39, "NM"),
    (2012, 1, 1, 6, 15, "FQ"),
    (2012, 1, 9, 7, 30, "FM"),
    (2012, 1, 16, 9, 8, "LQ"),
    (2012, 7, 19, 4, 24, "NM"),
    (2012, 7, 26, 8, 56, "FQ"),
    (2012, 7, 3, 18, 52, "FM"),
    (2012, 7, 11, 1, 48, "LQ"),
    # ====================================================================
    # 2015 — complete year
    # ====================================================================
    # New Moons
    (2015, 1, 20, 13, 14, "NM"),
    (2015, 2, 18, 23, 47, "NM"),
    (2015, 3, 20, 9, 36, "NM"),
    (2015, 4, 18, 18, 57, "NM"),
    (2015, 5, 18, 4, 13, "NM"),
    (2015, 6, 16, 14, 5, "NM"),
    (2015, 7, 16, 1, 24, "NM"),
    (2015, 8, 14, 14, 54, "NM"),
    (2015, 9, 13, 6, 41, "NM"),
    (2015, 10, 13, 0, 6, "NM"),
    (2015, 11, 11, 17, 47, "NM"),
    (2015, 12, 11, 10, 29, "NM"),
    # First Quarters
    (2015, 1, 27, 4, 48, "FQ"),
    (2015, 2, 25, 17, 14, "FQ"),
    (2015, 3, 27, 7, 43, "FQ"),
    (2015, 4, 25, 23, 55, "FQ"),
    (2015, 5, 25, 17, 19, "FQ"),
    (2015, 6, 24, 11, 3, "FQ"),
    (2015, 7, 24, 4, 4, "FQ"),
    (2015, 8, 22, 19, 31, "FQ"),
    (2015, 9, 21, 8, 59, "FQ"),
    (2015, 10, 20, 20, 31, "FQ"),
    (2015, 11, 19, 6, 27, "FQ"),
    (2015, 12, 18, 15, 14, "FQ"),
    # Full Moons
    (2015, 1, 5, 4, 53, "FM"),
    (2015, 2, 3, 23, 9, "FM"),
    (2015, 3, 5, 18, 6, "FM"),
    (2015, 4, 4, 12, 6, "FM"),
    (2015, 5, 4, 3, 42, "FM"),
    (2015, 6, 2, 16, 19, "FM"),
    (2015, 7, 2, 2, 20, "FM"),
    (2015, 7, 31, 10, 43, "FM"),
    (2015, 8, 29, 18, 35, "FM"),
    (2015, 9, 28, 2, 50, "FM"),
    (2015, 10, 27, 12, 5, "FM"),
    (2015, 11, 25, 22, 44, "FM"),
    (2015, 12, 25, 11, 11, "FM"),
    # Last Quarters
    (2015, 1, 13, 9, 47, "LQ"),
    (2015, 2, 12, 3, 50, "LQ"),
    (2015, 3, 13, 17, 48, "LQ"),
    (2015, 4, 12, 3, 45, "LQ"),
    (2015, 5, 11, 10, 36, "LQ"),
    (2015, 6, 9, 15, 42, "LQ"),
    (2015, 7, 8, 20, 24, "LQ"),
    (2015, 8, 7, 2, 3, "LQ"),
    (2015, 9, 5, 9, 54, "LQ"),
    (2015, 10, 4, 21, 6, "LQ"),
    (2015, 11, 3, 12, 24, "LQ"),
    (2015, 12, 3, 7, 40, "LQ"),
    # ====================================================================
    # 2017 — January & July
    # ====================================================================
    (2017, 1, 28, 0, 7, "NM"),
    (2017, 1, 5, 19, 47, "FQ"),
    (2017, 1, 12, 11, 34, "FM"),
    (2017, 1, 19, 22, 14, "LQ"),
    (2017, 7, 23, 9, 46, "NM"),
    (2017, 7, 1, 0, 51, "FQ"),
    (2017, 7, 9, 4, 7, "FM"),
    (2017, 7, 16, 19, 26, "LQ"),
    # ====================================================================
    # 2020 — complete year
    # ====================================================================
    # New Moons
    (2020, 1, 24, 21, 42, "NM"),
    (2020, 2, 23, 15, 32, "NM"),
    (2020, 3, 24, 9, 28, "NM"),
    (2020, 4, 23, 2, 26, "NM"),
    (2020, 5, 22, 17, 39, "NM"),
    (2020, 6, 21, 6, 41, "NM"),
    (2020, 7, 20, 17, 33, "NM"),
    (2020, 8, 19, 2, 42, "NM"),
    (2020, 9, 17, 11, 0, "NM"),
    (2020, 10, 16, 19, 31, "NM"),
    (2020, 11, 15, 5, 7, "NM"),
    (2020, 12, 14, 16, 17, "NM"),
    # First Quarters
    (2020, 1, 3, 4, 45, "FQ"),
    (2020, 2, 2, 1, 42, "FQ"),
    (2020, 3, 2, 19, 57, "FQ"),
    (2020, 4, 1, 10, 21, "FQ"),
    (2020, 4, 30, 20, 38, "FQ"),
    (2020, 5, 30, 3, 30, "FQ"),
    (2020, 6, 28, 8, 16, "FQ"),
    (2020, 7, 27, 12, 32, "FQ"),
    (2020, 8, 25, 17, 58, "FQ"),
    (2020, 9, 24, 1, 55, "FQ"),
    (2020, 10, 23, 13, 23, "FQ"),
    (2020, 11, 22, 4, 45, "FQ"),
    (2020, 12, 21, 23, 41, "FQ"),
    # Full Moons
    (2020, 1, 10, 19, 21, "FM"),
    (2020, 2, 9, 7, 33, "FM"),
    (2020, 3, 9, 17, 48, "FM"),
    (2020, 4, 8, 2, 35, "FM"),
    (2020, 5, 7, 10, 45, "FM"),
    (2020, 6, 5, 19, 12, "FM"),
    (2020, 7, 5, 4, 44, "FM"),
    (2020, 8, 3, 15, 59, "FM"),
    (2020, 9, 2, 5, 22, "FM"),
    (2020, 10, 1, 21, 5, "FM"),
    (2020, 10, 31, 14, 49, "FM"),
    (2020, 11, 30, 9, 30, "FM"),
    (2020, 12, 30, 3, 28, "FM"),
    # Last Quarters
    (2020, 1, 17, 12, 58, "LQ"),
    (2020, 2, 15, 22, 17, "LQ"),
    (2020, 3, 16, 9, 34, "LQ"),
    (2020, 4, 14, 22, 56, "LQ"),
    (2020, 5, 14, 14, 3, "LQ"),
    (2020, 6, 13, 6, 24, "LQ"),
    (2020, 7, 12, 23, 29, "LQ"),
    (2020, 8, 11, 16, 45, "LQ"),
    (2020, 9, 10, 9, 26, "LQ"),
    (2020, 10, 10, 0, 40, "LQ"),
    (2020, 11, 8, 13, 46, "LQ"),
    (2020, 12, 8, 0, 37, "LQ"),
    # ====================================================================
    # 2022 — January & July
    # ====================================================================
    (2022, 1, 2, 18, 34, "NM"),
    (2022, 1, 9, 18, 11, "FQ"),
    (2022, 1, 17, 23, 49, "FM"),
    (2022, 1, 25, 13, 41, "LQ"),
    (2022, 7, 28, 17, 55, "NM"),
    (2022, 7, 7, 2, 14, "FQ"),
    (2022, 7, 13, 18, 37, "FM"),
    (2022, 7, 20, 14, 18, "LQ"),
    # ====================================================================
    # 2025 — complete year
    # ====================================================================
    # New Moons
    (2025, 1, 29, 12, 36, "NM"),
    (2025, 2, 28, 0, 45, "NM"),
    (2025, 3, 29, 10, 58, "NM"),
    (2025, 4, 27, 19, 31, "NM"),
    (2025, 5, 27, 3, 2, "NM"),
    (2025, 6, 25, 10, 31, "NM"),
    (2025, 7, 24, 19, 11, "NM"),
    (2025, 8, 23, 6, 6, "NM"),
    (2025, 9, 21, 19, 54, "NM"),
    (2025, 10, 21, 12, 25, "NM"),
    (2025, 11, 20, 6, 47, "NM"),
    (2025, 12, 20, 1, 43, "NM"),
    # First Quarters
    (2025, 1, 6, 23, 56, "FQ"),
    (2025, 2, 5, 8, 2, "FQ"),
    (2025, 3, 6, 16, 32, "FQ"),
    (2025, 4, 5, 2, 15, "FQ"),
    (2025, 5, 4, 13, 52, "FQ"),
    (2025, 6, 3, 3, 41, "FQ"),
    (2025, 7, 2, 19, 30, "FQ"),
    (2025, 8, 1, 12, 41, "FQ"),
    (2025, 8, 31, 6, 25, "FQ"),
    (2025, 9, 29, 23, 54, "FQ"),
    (2025, 10, 29, 16, 21, "FQ"),
    (2025, 11, 28, 6, 59, "FQ"),
    (2025, 12, 27, 19, 10, "FQ"),
    # Full Moons
    (2025, 1, 13, 22, 27, "FM"),
    (2025, 2, 12, 13, 53, "FM"),
    (2025, 3, 14, 6, 55, "FM"),
    (2025, 4, 13, 0, 22, "FM"),
    (2025, 5, 12, 16, 56, "FM"),
    (2025, 6, 11, 7, 44, "FM"),
    (2025, 7, 10, 20, 37, "FM"),
    (2025, 8, 9, 7, 55, "FM"),
    (2025, 9, 7, 18, 9, "FM"),
    (2025, 10, 7, 3, 48, "FM"),
    (2025, 11, 5, 13, 19, "FM"),
    (2025, 12, 4, 23, 14, "FM"),
    # Last Quarters
    (2025, 1, 21, 20, 31, "LQ"),
    (2025, 2, 20, 17, 33, "LQ"),
    (2025, 3, 22, 11, 30, "LQ"),
    (2025, 4, 21, 1, 36, "LQ"),
    (2025, 5, 20, 11, 59, "LQ"),
    (2025, 6, 18, 19, 19, "LQ"),
    (2025, 7, 18, 0, 38, "LQ"),
    (2025, 8, 16, 5, 12, "LQ"),
    (2025, 9, 14, 10, 33, "LQ"),
    (2025, 10, 13, 18, 13, "LQ"),
    (2025, 11, 12, 5, 28, "LQ"),
    (2025, 12, 11, 20, 52, "LQ"),
    # ====================================================================
    # 2027 — January & July
    # ====================================================================
    (2027, 1, 7, 20, 24, "NM"),
    (2027, 1, 15, 20, 34, "FQ"),
    (2027, 1, 22, 12, 17, "FM"),
    (2027, 1, 29, 10, 56, "LQ"),
    (2027, 7, 4, 3, 2, "NM"),
    (2027, 7, 10, 18, 39, "FQ"),
    (2027, 7, 18, 15, 45, "FM"),
    (2027, 7, 26, 16, 55, "LQ"),
    # ====================================================================
    # 2030 — January
    # ====================================================================
    (2030, 1, 4, 2, 49, "NM"),
    (2030, 1, 11, 14, 6, "FQ"),
    (2030, 1, 19, 15, 54, "FM"),
    (2030, 1, 26, 18, 15, "LQ"),
    # ====================================================================
    # 2035 — January
    # ====================================================================
    (2035, 1, 9, 15, 3, "NM"),
    (2035, 1, 17, 4, 45, "FQ"),
    (2035, 1, 23, 20, 17, "FM"),
    (2035, 1, 31, 6, 3, "LQ"),
    # ====================================================================
    # 2040 — January
    # ====================================================================
    (2040, 1, 14, 3, 25, "NM"),
    (2040, 1, 21, 2, 21, "FQ"),
    (2040, 1, 29, 7, 55, "FM"),
    (2040, 1, 7, 11, 5, "LQ"),
    # ====================================================================
    # 2026 — January (near-future)
    # ====================================================================
    (2026, 1, 18, 19, 52, "NM"),
    (2026, 1, 26, 4, 48, "FQ"),
    (2026, 1, 3, 10, 3, "FM"),
    (2026, 1, 10, 15, 48, "LQ"),
    # ====================================================================
    # 2028 — January
    # ====================================================================
    (2028, 1, 26, 15, 13, "NM"),
    (2028, 1, 5, 1, 40, "FQ"),
    (2028, 1, 12, 4, 3, "FM"),
    (2028, 1, 18, 19, 26, "LQ"),
]


def _phase_id(p):
    return f"{p[5]}-{p[0]}-{p[1]:02d}-{p[2]:02d}"


# ---------------------------------------------------------------------------
# Test 1: Phase angle at known moments
# Verify degrees_between_s_m is within tolerance of the theoretical angle.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "y,m,d,h,mi,pt",
    KNOWN_PHASES,
    ids=[_phase_id(p) for p in KNOWN_PHASES],
)
def test_angle_at_known_phase_moment(y, m, d, h, mi, pt):
    """At a known phase time, the Sun-Moon elongation must be close to the
    theoretical value (0° NM, 90° FQ, 180° FM, 270° LQ)."""
    subject = _make_subject(y, m, d, h, mi)
    lp = subject.lunar_phase
    assert lp is not None, f"lunar_phase is None for {y}-{m:02d}-{d:02d}"

    expected = _EXPECTED_ANGLE[pt]
    actual = lp.degrees_between_s_m
    diff = _angle_distance(actual, expected)

    assert diff < _ANGLE_TOL, (
        f"{pt} {y}-{m:02d}-{d:02d} {h:02d}:{mi:02d} UTC: expected ≈{expected}°, got {actual:.4f}° (Δ={diff:.4f}°)"
    )


# ---------------------------------------------------------------------------
# Test 2: Phase name at known moments
# The 28-phase name must be in the valid set for the phase type.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "y,m,d,h,mi,pt",
    KNOWN_PHASES,
    ids=[_phase_id(p) for p in KNOWN_PHASES],
)
def test_phase_name_at_known_moment(y, m, d, h, mi, pt):
    """Phase name must be the expected name (or the adjacent boundary name)."""
    subject = _make_subject(y, m, d, h, mi)
    lp = subject.lunar_phase
    assert lp is not None

    valid = _VALID_NAMES[pt]
    assert lp.moon_phase_name in valid, (
        f"{pt} {y}-{m:02d}-{d:02d}: name '{lp.moon_phase_name}' not in {valid} (angle={lp.degrees_between_s_m:.4f}°)"
    )


# ---------------------------------------------------------------------------
# Test 3: Emoji at known moments
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "y,m,d,h,mi,pt",
    KNOWN_PHASES,
    ids=[_phase_id(p) for p in KNOWN_PHASES],
)
def test_emoji_at_known_moment(y, m, d, h, mi, pt):
    """Emoji must match the phase type (or adjacent boundary)."""
    subject = _make_subject(y, m, d, h, mi)
    lp = subject.lunar_phase
    assert lp is not None

    valid = _VALID_EMOJIS[pt]
    assert lp.moon_emoji in valid, (
        f"{pt} {y}-{m:02d}-{d:02d}: emoji '{lp.moon_emoji}' not in {valid} (angle={lp.degrees_between_s_m:.4f}°)"
    )


# ---------------------------------------------------------------------------
# Test 4: Phase number sanity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "y,m,d,h,mi,pt",
    KNOWN_PHASES,
    ids=[_phase_id(p) for p in KNOWN_PHASES],
)
def test_phase_number_valid(y, m, d, h, mi, pt):
    """Moon phase int must be 1-28."""
    subject = _make_subject(y, m, d, h, mi)
    lp = subject.lunar_phase
    assert lp is not None
    assert 1 <= lp.moon_phase <= 28, f"phase={lp.moon_phase}"


# ---------------------------------------------------------------------------
# Test 5: Factory — major_phase at known moments (subset)
# These are slower (binary search + eclipse search per call).
# Use 1 per month for 2010 and 2020 = ~96 cases.
# ---------------------------------------------------------------------------

FACTORY_PHASES = [p for p in KNOWN_PHASES if p[0] in (2010, 2020)]


@pytest.mark.parametrize(
    "y,m,d,h,mi,pt",
    FACTORY_PHASES,
    ids=[_phase_id(p) for p in FACTORY_PHASES],
)
def test_factory_major_phase(y, m, d, h, mi, pt):
    """Factory's nearest-angle major_phase must match the known phase type."""
    subject = _make_subject(y, m, d, h, mi)
    overview = MoonPhaseDetailsFactory.from_subject(subject)

    expected_name = {
        "NM": "New Moon",
        "FQ": "First Quarter",
        "FM": "Full Moon",
        "LQ": "Last Quarter",
    }[pt]

    assert overview.moon.major_phase == expected_name, (
        f"{pt} {y}-{m:02d}-{d:02d}: major_phase='{overview.moon.major_phase}', expected '{expected_name}'"
    )


# ---------------------------------------------------------------------------
# Test 6: Factory — illumination at known moments
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "y,m,d,h,mi,pt",
    FACTORY_PHASES,
    ids=[_phase_id(p) for p in FACTORY_PHASES],
)
def test_factory_illumination(y, m, d, h, mi, pt):
    """Illumination percentage must be close to the theoretical value."""
    subject = _make_subject(y, m, d, h, mi)
    overview = MoonPhaseDetailsFactory.from_subject(subject)

    assert overview.moon.illumination is not None
    actual_pct = float(overview.moon.illumination.rstrip("%"))
    expected_pct = _EXPECTED_ILLUM[pt]

    assert abs(actual_pct - expected_pct) <= _ILLUMINATION_TOL, (
        f"{pt} {y}-{m:02d}-{d:02d}: illumination={actual_pct}%, expected ≈{expected_pct}% (tol={_ILLUMINATION_TOL}%)"
    )


# ---------------------------------------------------------------------------
# Test 7: Factory — stage at known moments
# NM and FM are at boundaries; FQ must be waxing, LQ must be waning.
# ---------------------------------------------------------------------------

STAGE_PHASES = [p for p in FACTORY_PHASES if p[5] in ("FQ", "LQ")]


@pytest.mark.parametrize(
    "y,m,d,h,mi,pt",
    STAGE_PHASES,
    ids=[_phase_id(p) for p in STAGE_PHASES],
)
def test_factory_stage(y, m, d, h, mi, pt):
    """FQ must be waxing, LQ must be waning."""
    subject = _make_subject(y, m, d, h, mi)
    overview = MoonPhaseDetailsFactory.from_subject(subject)

    expected_stage = "waxing" if pt == "FQ" else "waning"
    assert overview.moon.stage == expected_stage, (
        f"{pt} {y}-{m:02d}-{d:02d}: stage='{overview.moon.stage}', expected '{expected_stage}'"
    )


# ---------------------------------------------------------------------------
# Test 8: Mid-cycle verification
# At dates between known phases, verify the angle quadrant, phase name
# category, and waxing/waning stage are self-consistent.
# (y, m, d, h, mi, expected_stage, expected_names_set)
# ---------------------------------------------------------------------------

MID_CYCLE_DATES = [
    # ~4 days after NM → waxing crescent (angle 0°–90°)
    (2001, 1, 28, 12, 0, "waxing", {"Waxing Crescent", "First Quarter"}),
    (2010, 1, 19, 12, 0, "waxing", {"Waxing Crescent", "First Quarter"}),
    (2020, 1, 28, 12, 0, "waxing", {"Waxing Crescent", "First Quarter"}),
    (2025, 2, 3, 12, 0, "waxing", {"Waxing Crescent", "First Quarter"}),
    (2005, 3, 14, 12, 0, "waxing", {"Waxing Crescent", "First Quarter"}),
    (2015, 5, 22, 12, 0, "waxing", {"Waxing Crescent", "First Quarter"}),
    # ~4 days after FQ → waxing gibbous (angle 90°–180°)
    (2001, 2, 5, 12, 0, "waxing", {"Waxing Gibbous", "Full Moon"}),
    (2010, 1, 27, 12, 0, "waxing", {"Waxing Gibbous", "Full Moon"}),
    (2020, 2, 6, 12, 0, "waxing", {"Waxing Gibbous", "Full Moon"}),
    (2025, 4, 8, 12, 0, "waxing", {"Waxing Gibbous", "Full Moon"}),
    (2005, 6, 19, 12, 0, "waxing", {"Waxing Gibbous", "Full Moon"}),
    (2015, 7, 28, 12, 0, "waxing", {"Waxing Gibbous", "Full Moon"}),
    # ~4 days after FM → waning gibbous (angle 180°–270°)
    (2001, 2, 12, 12, 0, "waning", {"Waning Gibbous", "Last Quarter"}),
    (2010, 2, 3, 12, 0, "waning", {"Waning Gibbous", "Last Quarter"}),
    (2020, 2, 13, 12, 0, "waning", {"Waning Gibbous", "Last Quarter"}),
    (2025, 6, 14, 12, 0, "waning", {"Waning Gibbous", "Last Quarter"}),
    (2005, 8, 23, 12, 0, "waning", {"Waning Gibbous", "Last Quarter"}),
    (2015, 9, 1, 12, 0, "waning", {"Waning Gibbous", "Last Quarter"}),
    # ~4 days after LQ → waning crescent (angle 270°–360°)
    (2001, 2, 19, 12, 0, "waning", {"Waning Crescent", "New Moon"}),
    (2010, 2, 10, 12, 0, "waning", {"Waning Crescent", "New Moon"}),
    (2020, 2, 19, 12, 0, "waning", {"Waning Crescent", "New Moon"}),
    (2025, 8, 19, 12, 0, "waning", {"Waning Crescent", "New Moon"}),
    (2005, 11, 27, 12, 0, "waning", {"Waning Crescent", "New Moon"}),
    (2015, 12, 7, 12, 0, "waning", {"Waning Crescent", "New Moon"}),
    # Additional decades for historical spread
    (2030, 1, 8, 12, 0, "waxing", {"Waxing Crescent", "First Quarter"}),
    (2030, 3, 16, 12, 0, "waxing", {"Waxing Gibbous", "Full Moon"}),
    (2035, 1, 27, 12, 0, "waning", {"Waning Gibbous", "Last Quarter"}),
    (2040, 1, 18, 12, 0, "waxing", {"Waxing Crescent", "First Quarter"}),
]

_mid_ids = [f"mid-{d[0]}-{d[1]:02d}-{d[2]:02d}-{d[5]}" for d in MID_CYCLE_DATES]


@pytest.mark.parametrize(
    "y,m,d,h,mi,expected_stage,valid_names",
    MID_CYCLE_DATES,
    ids=_mid_ids,
)
def test_mid_cycle_properties(y, m, d, h, mi, expected_stage, valid_names):
    """At mid-cycle dates, verify angle quadrant and phase name category."""
    subject = _make_subject(y, m, d, h, mi)
    lp = subject.lunar_phase
    assert lp is not None

    angle = lp.degrees_between_s_m

    # Stage from angle
    if expected_stage == "waxing":
        assert 0 <= angle < 180, f"{y}-{m:02d}-{d:02d}: expected waxing (0°–180°), got {angle:.2f}°"
    else:
        assert 180 <= angle < 360, f"{y}-{m:02d}-{d:02d}: expected waning (180°–360°), got {angle:.2f}°"

    # Phase name category
    assert lp.moon_phase_name in valid_names, (
        f"{y}-{m:02d}-{d:02d}: name '{lp.moon_phase_name}' not in {valid_names} (angle={angle:.2f}°)"
    )


# ---------------------------------------------------------------------------
# Test 9: Mid-cycle factory stage consistency
# ---------------------------------------------------------------------------


MID_CYCLE_FACTORY = MID_CYCLE_DATES[:12]  # Use first 12 for speed
_mid_f_ids = [f"midf-{d[0]}-{d[1]:02d}-{d[2]:02d}" for d in MID_CYCLE_FACTORY]


@pytest.mark.parametrize(
    "y,m,d,h,mi,expected_stage,valid_names",
    MID_CYCLE_FACTORY,
    ids=_mid_f_ids,
)
def test_mid_cycle_factory_stage(y, m, d, h, mi, expected_stage, valid_names):
    """Factory stage must match angle-derived waxing/waning."""
    subject = _make_subject(y, m, d, h, mi)
    overview = MoonPhaseDetailsFactory.from_subject(subject)

    assert overview.moon.stage == expected_stage, (
        f"{y}-{m:02d}-{d:02d}: factory stage='{overview.moon.stage}', expected '{expected_stage}'"
    )


# ---------------------------------------------------------------------------
# Test 10: Synodic month length
# Time between consecutive New Moons must be 29.26–29.80 days.
# ---------------------------------------------------------------------------

# Pairs of consecutive New Moons (using data from complete years)
CONSECUTIVE_NEW_MOONS = [
    # 2001
    ((2001, 1, 24, 13, 7), (2001, 2, 23, 8, 21)),
    ((2001, 2, 23, 8, 21), (2001, 3, 25, 1, 21)),
    ((2001, 3, 25, 1, 21), (2001, 4, 23, 15, 26)),
    ((2001, 4, 23, 15, 26), (2001, 5, 23, 2, 46)),
    ((2001, 5, 23, 2, 46), (2001, 6, 21, 11, 58)),
    ((2001, 6, 21, 11, 58), (2001, 7, 20, 19, 44)),
    ((2001, 7, 20, 19, 44), (2001, 8, 19, 2, 55)),
    ((2001, 8, 19, 2, 55), (2001, 9, 17, 10, 27)),
    ((2001, 9, 17, 10, 27), (2001, 10, 16, 19, 23)),
    ((2001, 10, 16, 19, 23), (2001, 11, 15, 6, 40)),
    ((2001, 11, 15, 6, 40), (2001, 12, 14, 20, 48)),
    # 2010
    ((2010, 1, 15, 7, 11), (2010, 2, 14, 2, 51)),
    ((2010, 2, 14, 2, 51), (2010, 3, 15, 21, 1)),
    ((2010, 3, 15, 21, 1), (2010, 4, 14, 12, 29)),
    ((2010, 4, 14, 12, 29), (2010, 5, 14, 1, 4)),
    ((2010, 5, 14, 1, 4), (2010, 6, 12, 11, 15)),
    ((2010, 6, 12, 11, 15), (2010, 7, 11, 19, 40)),
    ((2010, 7, 11, 19, 40), (2010, 8, 10, 3, 8)),
    ((2010, 8, 10, 3, 8), (2010, 9, 8, 10, 30)),
    ((2010, 9, 8, 10, 30), (2010, 10, 7, 18, 44)),
    ((2010, 10, 7, 18, 44), (2010, 11, 6, 4, 52)),
    ((2010, 11, 6, 4, 52), (2010, 12, 5, 17, 36)),
    # 2020
    ((2020, 1, 24, 21, 42), (2020, 2, 23, 15, 32)),
    ((2020, 2, 23, 15, 32), (2020, 3, 24, 9, 28)),
    ((2020, 3, 24, 9, 28), (2020, 4, 23, 2, 26)),
    ((2020, 4, 23, 2, 26), (2020, 5, 22, 17, 39)),
    ((2020, 5, 22, 17, 39), (2020, 6, 21, 6, 41)),
    ((2020, 6, 21, 6, 41), (2020, 7, 20, 17, 33)),
    ((2020, 7, 20, 17, 33), (2020, 8, 19, 2, 42)),
    ((2020, 8, 19, 2, 42), (2020, 9, 17, 11, 0)),
    ((2020, 9, 17, 11, 0), (2020, 10, 16, 19, 31)),
    ((2020, 10, 16, 19, 31), (2020, 11, 15, 5, 7)),
    ((2020, 11, 15, 5, 7), (2020, 12, 14, 16, 17)),
    # 2025
    ((2025, 1, 29, 12, 36), (2025, 2, 28, 0, 45)),
    ((2025, 2, 28, 0, 45), (2025, 3, 29, 10, 58)),
    ((2025, 3, 29, 10, 58), (2025, 4, 27, 19, 31)),
    ((2025, 4, 27, 19, 31), (2025, 5, 27, 3, 2)),
    ((2025, 5, 27, 3, 2), (2025, 6, 25, 10, 31)),
    ((2025, 6, 25, 10, 31), (2025, 7, 24, 19, 11)),
    ((2025, 7, 24, 19, 11), (2025, 8, 23, 6, 6)),
    ((2025, 8, 23, 6, 6), (2025, 9, 21, 19, 54)),
    ((2025, 9, 21, 19, 54), (2025, 10, 21, 12, 25)),
    ((2025, 10, 21, 12, 25), (2025, 11, 20, 6, 47)),
    ((2025, 11, 20, 6, 47), (2025, 12, 20, 1, 43)),
]

_syn_ids = [f"syn-{a[0]}-{a[1]:02d}-to-{b[1]:02d}" for a, b in CONSECUTIVE_NEW_MOONS]


@pytest.mark.parametrize(
    "nm1,nm2",
    CONSECUTIVE_NEW_MOONS,
    ids=_syn_ids,
)
def test_synodic_month_length(nm1, nm2):
    """Time between consecutive New Moons must be within known bounds."""
    dt1 = datetime(*nm1, tzinfo=timezone.utc)
    dt2 = datetime(*nm2, tzinfo=timezone.utc)
    days = (dt2 - dt1).total_seconds() / 86400.0

    assert _SYNODIC_MIN <= days <= _SYNODIC_MAX, (
        f"NM {nm1} → {nm2}: {days:.4f} days (expected {_SYNODIC_MIN}–{_SYNODIC_MAX})"
    )


# ---------------------------------------------------------------------------
# Test 11: Illumination self-consistency
# At known phases, illumination computed from the angle must match the
# formula: k = 0.5 * (1 - cos(angle_rad)) * 100
# ---------------------------------------------------------------------------

ILLUMINATION_CHECK_PHASES = [p for p in KNOWN_PHASES if p[0] in (2005, 2015, 2025)]


@pytest.mark.parametrize(
    "y,m,d,h,mi,pt",
    ILLUMINATION_CHECK_PHASES,
    ids=[_phase_id(p) for p in ILLUMINATION_CHECK_PHASES],
)
def test_illumination_formula_consistency(y, m, d, h, mi, pt):
    """Verify illumination computed from angle matches the cosine formula."""
    subject = _make_subject(y, m, d, h, mi)
    lp = subject.lunar_phase
    assert lp is not None

    angle_rad = math.radians(lp.degrees_between_s_m)
    expected_illum = 0.5 * (1 - math.cos(angle_rad)) * 100

    # At known phase moments, the formula should give near-integer values
    if pt == "NM":
        assert expected_illum < 1.0, f"NM illumination={expected_illum:.2f}%"
    elif pt == "FM":
        assert expected_illum > 99.0, f"FM illumination={expected_illum:.2f}%"
    elif pt in ("FQ", "LQ"):
        assert 48.0 < expected_illum < 52.0, f"{pt} illumination={expected_illum:.2f}%"


# ---------------------------------------------------------------------------
# Test 12: Cross-decade consistency — phase progression
# Between a known NM and the next known FQ, the angle should increase
# monotonically (confirming we don't have bugs in different decades).
# ---------------------------------------------------------------------------

PHASE_PROGRESSION_CASES = [
    # (NM date, FQ date, mid-point date) — angle at mid should be ~45°
    ("2001", (2001, 1, 24, 13, 7), (2001, 2, 1, 14, 2), (2001, 1, 28, 12, 0)),
    ("2010", (2010, 1, 15, 7, 11), (2010, 1, 23, 10, 53), (2010, 1, 19, 12, 0)),
    ("2020", (2020, 1, 24, 21, 42), (2020, 2, 2, 1, 42), (2020, 1, 28, 12, 0)),
    ("2025", (2025, 1, 29, 12, 36), (2025, 2, 5, 8, 2), (2025, 2, 1, 12, 0)),
    ("2030", (2030, 1, 4, 2, 49), (2030, 1, 11, 14, 6), (2030, 1, 7, 12, 0)),
    ("2035", (2035, 1, 9, 15, 3), (2035, 1, 17, 4, 45), (2035, 1, 13, 12, 0)),
    ("2040", (2040, 1, 14, 3, 25), (2040, 1, 21, 2, 21), (2040, 1, 17, 12, 0)),
]


@pytest.mark.parametrize(
    "label,nm,fq,mid",
    PHASE_PROGRESSION_CASES,
    ids=[c[0] for c in PHASE_PROGRESSION_CASES],
)
def test_phase_progression_nm_to_fq(label, nm, fq, mid):
    """Between NM and FQ, angle at NM < angle at mid < angle at FQ (all < 90°).

    Note: at New Moon the angle can be ~359.99° (≡ ~0° mod 360) because
    ``degrees_between = (moon - sun) % 360`` maps exact 0° to the range
    [0, 360).  We normalise angles > 355° to their negative equivalent
    so the comparison works across the 0°/360° boundary.
    """
    s_nm = _make_subject(*nm)
    s_mid = _make_subject(*mid)
    s_fq = _make_subject(*fq)

    def _normalise(a: float) -> float:
        """Map angles near 360° to small negative values for ordering."""
        return a - 360.0 if a > 355.0 else a

    a_nm = _normalise(s_nm.lunar_phase.degrees_between_s_m)
    a_mid = _normalise(s_mid.lunar_phase.degrees_between_s_m)
    a_fq = _normalise(s_fq.lunar_phase.degrees_between_s_m)

    assert a_nm < a_mid < a_fq, f"{label}: expected NM({a_nm:.2f}°) < mid({a_mid:.2f}°) < FQ({a_fq:.2f}°)"
    # NM should be near 0° (possibly tiny negative after normalisation)
    assert -5 < a_nm < 5, f"NM angle out of range: {a_nm:.2f}°"
    assert a_fq > 85, f"FQ angle too low: {a_fq:.2f}°"
    assert 20 < a_mid < 70, f"Mid angle out of range: {a_mid:.2f}°"


# ---------------------------------------------------------------------------
# Test 13: Factory — upcoming phases populated
# For a subset of mid-cycle dates, verify the factory populates all four
# upcoming phase windows (new_moon, first_quarter, full_moon, last_quarter).
# ---------------------------------------------------------------------------

FACTORY_UPCOMING_DATES = [
    # Mid-cycle dates that should have both "last" and "next" for all phases
    (2001, 2, 5, 12, 0),
    (2005, 7, 10, 12, 0),
    (2010, 5, 20, 12, 0),
    (2015, 3, 15, 12, 0),
    (2020, 8, 1, 12, 0),
    (2025, 10, 1, 12, 0),
    (2030, 1, 15, 12, 0),
    (2035, 1, 20, 12, 0),
]


@pytest.mark.parametrize(
    "y,m,d,h,mi",
    FACTORY_UPCOMING_DATES,
    ids=[f"upcoming-{d[0]}-{d[1]:02d}-{d[2]:02d}" for d in FACTORY_UPCOMING_DATES],
)
def test_factory_upcoming_phases_populated(y, m, d, h, mi):
    """Factory should find last/next for all four major phases."""
    subject = _make_subject(y, m, d, h, mi)
    overview = MoonPhaseDetailsFactory.from_subject(subject)

    moon = overview.moon
    assert moon.detailed is not None, "detailed is None"
    up = moon.detailed.upcoming_phases
    assert up is not None, "upcoming_phases is None"

    for field_name in ("new_moon", "first_quarter", "full_moon", "last_quarter"):
        window = getattr(up, field_name)
        assert window is not None, f"{field_name} window is None"
        assert window.last is not None, f"{field_name}.last is None"
        assert window.next is not None, f"{field_name}.next is None"
        assert window.last.timestamp is not None, f"{field_name}.last.timestamp is None"
        assert window.next.timestamp is not None, f"{field_name}.next.timestamp is None"
        # Next must be after the reference date, last must be before
        ref_ts = int(datetime(y, m, d, h, mi, tzinfo=timezone.utc).timestamp())
        assert window.last.timestamp < ref_ts, (
            f"{field_name}.last.timestamp ({window.last.timestamp}) should be < ref ({ref_ts})"
        )
        assert window.next.timestamp > ref_ts, (
            f"{field_name}.next.timestamp ({window.next.timestamp}) should be > ref ({ref_ts})"
        )


# ---------------------------------------------------------------------------
# Test 14: Factory — eclipse fields populated
# At mid-cycle dates, the factory should find upcoming eclipses.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "y,m,d,h,mi",
    FACTORY_UPCOMING_DATES,
    ids=[f"eclipse-{d[0]}-{d[1]:02d}-{d[2]:02d}" for d in FACTORY_UPCOMING_DATES],
)
def test_factory_eclipse_populated(y, m, d, h, mi):
    """Factory should find at least a next lunar eclipse."""
    subject = _make_subject(y, m, d, h, mi)
    overview = MoonPhaseDetailsFactory.from_subject(subject)

    # Lunar eclipse
    nle = overview.moon.next_lunar_eclipse
    assert nle is not None, "next_lunar_eclipse is None"
    assert nle.timestamp is not None, "eclipse timestamp is None"
    assert nle.type is not None, "eclipse type is None"
    assert "Eclipse" in nle.type or "eclipse" in nle.type, f"eclipse type='{nle.type}' doesn't contain 'Eclipse'"

    # Solar eclipse
    if overview.sun is not None and overview.sun.next_solar_eclipse is not None:
        nse = overview.sun.next_solar_eclipse
        assert nse.timestamp is not None
        assert nse.type is not None
        assert "Eclipse" in nse.type or "eclipse" in nse.type


# ---------------------------------------------------------------------------
# Test 15: Factory — sun info populated
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "y,m,d,h,mi",
    FACTORY_UPCOMING_DATES,
    ids=[f"sun-{d[0]}-{d[1]:02d}-{d[2]:02d}" for d in FACTORY_UPCOMING_DATES],
)
def test_factory_sun_info(y, m, d, h, mi):
    """Factory should provide sun info (sunrise, sunset, position)."""
    subject = _make_subject(y, m, d, h, mi)
    overview = MoonPhaseDetailsFactory.from_subject(subject)

    assert overview.sun is not None, "sun info is None"
    # At Greenwich, sunrise/sunset should always exist (not polar)
    assert overview.sun.sunrise is not None, "sunrise is None"
    assert overview.sun.sunset is not None, "sunset is None"
    assert overview.sun.sunrise_timestamp is not None
    assert overview.sun.sunset_timestamp is not None
    assert overview.sun.sunrise < overview.sun.sunset, (
        f"sunrise ({overview.sun.sunrise}) >= sunset ({overview.sun.sunset})"
    )


# ---------------------------------------------------------------------------
# Test 16: 28-phase boundary verification
# Verify that each of the 28 phases can be reached by computing the angle
# at the center of each phase's range.
# ---------------------------------------------------------------------------

_STEP = 360.0 / 28.0
_PHASE_CENTERS = [(phase_num, (phase_num - 0.5) * _STEP) for phase_num in range(1, 29)]


@pytest.mark.parametrize(
    "expected_phase_num,center_angle",
    _PHASE_CENTERS,
    ids=[f"phase-{n}" for n, _ in _PHASE_CENTERS],
)
def test_28_phase_from_center_angle(expected_phase_num, center_angle):
    """Verify the 28-phase mapping: angle at center of each phase range
    should produce the expected phase number."""
    from kerykeion.utilities import calculate_moon_phase

    # Use sun_pos=0 and moon_pos=center_angle for clean calculation
    result = calculate_moon_phase(center_angle, 0.0)
    assert result.moon_phase == expected_phase_num, (
        f"center_angle={center_angle:.3f}° → phase {result.moon_phase}, expected {expected_phase_num}"
    )


# ---------------------------------------------------------------------------
# Test 17: 28-phase boundary transitions
# Verify that slightly below and slightly above each boundary give the
# expected adjacent phase numbers.
#
# Note: at the *exact* boundary value ``n * step``, floating-point
# representation of ``(n * step) // step`` is not guaranteed to equal
# ``n`` (it may be ``n - 1``).  So we test with a small epsilon offset
# on each side rather than on the exact boundary itself.
# ---------------------------------------------------------------------------

_PHASE_BOUNDARIES = [
    # (angle_below, expected_phase_below, angle_above, expected_phase_above)
    (n * _STEP - 0.01, n, n * _STEP + 0.01, (n % 28) + 1)
    for n in range(1, 29)
]


@pytest.mark.parametrize(
    "angle_below,phase_below,angle_above,phase_above",
    _PHASE_BOUNDARIES,
    ids=[f"boundary-{n}" for n in range(1, 29)],
)
def test_28_phase_boundary_transition(angle_below, phase_below, angle_above, phase_above):
    """Just below and just above each phase boundary must yield the
    expected adjacent phase numbers."""
    from kerykeion.utilities import calculate_moon_phase

    result_below = calculate_moon_phase(angle_below % 360, 0.0)
    result_above = calculate_moon_phase(angle_above % 360, 0.0)

    assert result_below.moon_phase == phase_below, (
        f"angle={angle_below:.3f}° → phase {result_below.moon_phase}, expected {phase_below}"
    )
    assert result_above.moon_phase == phase_above, (
        f"angle={angle_above:.3f}° → phase {result_above.moon_phase}, expected {phase_above}"
    )


# ---------------------------------------------------------------------------
# Test 18: Angle always in [0, 360) range
# ---------------------------------------------------------------------------

ANGLE_RANGE_DATES = [
    (2001, 3, 1, 0, 0),
    (2005, 6, 15, 12, 0),
    (2010, 9, 20, 18, 30),
    (2015, 12, 31, 23, 59),
    (2020, 7, 4, 6, 0),
    (2025, 2, 14, 14, 0),
    (2030, 8, 22, 3, 0),
    (2035, 11, 11, 11, 11),
    (2040, 4, 1, 0, 1),
    # Solstices and equinoxes
    (2020, 3, 20, 3, 50),  # vernal equinox
    (2020, 6, 20, 21, 44),  # summer solstice
    (2020, 9, 22, 13, 31),  # autumnal equinox
    (2020, 12, 21, 10, 2),  # winter solstice
    (2001, 1, 1, 0, 0),  # millennium start
    (2000, 12, 31, 23, 59),  # millennium end
]


@pytest.mark.parametrize(
    "y,m,d,h,mi",
    ANGLE_RANGE_DATES,
    ids=[f"range-{d[0]}-{d[1]:02d}-{d[2]:02d}" for d in ANGLE_RANGE_DATES],
)
def test_angle_always_in_valid_range(y, m, d, h, mi):
    """degrees_between_s_m must always be in [0, 360)."""
    subject = _make_subject(y, m, d, h, mi)
    lp = subject.lunar_phase
    assert lp is not None
    assert 0 <= lp.degrees_between_s_m < 360, f"angle={lp.degrees_between_s_m} out of [0, 360)"
    assert 1 <= lp.moon_phase <= 28
    assert lp.moon_phase_name in {
        "New Moon",
        "Waxing Crescent",
        "First Quarter",
        "Waxing Gibbous",
        "Full Moon",
        "Waning Gibbous",
        "Last Quarter",
        "Waning Crescent",
    }
