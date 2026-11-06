"""Check the native v4 sidereal clock against an independent UT1 reference.

Legacy chart fixtures also encode their generating sidereal-time model. A
fixture disagreement must not be repaired by changing tolerances or forcing
v4 to reproduce a legacy clock. This check uses the existing consumer angular
budget, not an accuracy claim for every supported astronomical epoch.
"""

from __future__ import annotations

import pytest

from kerykeion.ephemeris_backend import BACKEND_NAME, ephe, ephemeris_session
from tests.core.conftest import POSITION_TOLERANCE


@pytest.mark.skipif(BACKEND_NAME != "libephemeris", reason="Native v4 model contract")
@pytest.mark.parametrize("year", [-500, -200, 100, 400, 800, 1000, 1643, 2000, 2050, 2100, 2200])
def test_apparent_sidereal_time_uses_the_requested_ut1_epoch(year):
    """Compare apparent sidereal angles, never UTC/TT mislabeled as UT1.

    Skyfield supplies an independent IAU equinox-based GAST calculation; the
    native engine uses its published continuous pole-transport convention.
    Their difference must remain within the unchanged chart angular budget.
    Built-in time tables keep this diagnostic independent of network access.
    """
    skyfield = pytest.importorskip("skyfield.api")
    timescale = skyfield.load.timescale(builtin=True)
    jd_ut1 = ephe.julday(year, 6, 15, 12.0)
    reference_degrees = float(timescale.ut1_jd(jd_ut1).gast) * 15.0
    with ephemeris_session():
        native_degrees = ephe.sidtime(jd_ut1) * 15.0
    signed_difference = (native_degrees - reference_degrees + 180.0) % 360.0 - 180.0
    assert abs(signed_difference) <= POSITION_TOLERANCE
