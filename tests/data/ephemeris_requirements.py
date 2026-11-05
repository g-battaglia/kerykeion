"""Explicit availability requirements for complete historical chart snapshots.

These checks do not establish numerical accuracy. They distinguish a known
backend/data limitation from a missing point caused by a consumer regression.
No numerical results or backend exception text are retained.
"""

from kerykeion.astrological_subject.factory import STANDARD_PLANETS
from kerykeion.ephemeris_backend import BACKEND_NAME, ephe, ephemeris_session
from kerykeion.schemas.models import AstrologicalSubjectModel
from kerykeion.settings.config_constants import DEFAULT_ACTIVE_POINTS


def unavailable_snapshot_points(subject: AstrologicalSubjectModel) -> tuple[str, ...]:
    """Explain missing required points only when the Swiss public API confirms it.

    Unknown calculation errors propagate. A successful direct call with a missing
    consumer point is a regression, as is an omission with no structured warning.
    LibEphemeris snapshots retain their original, strict comparison path.
    """
    if BACKEND_NAME != "swisseph":
        return ()
    unavailable = []
    warnings = {warning.point_name for warning in subject.ephemeris_warnings}
    for name in DEFAULT_ACTIVE_POINTS:
        if name not in STANDARD_PLANETS or getattr(subject, name.lower(), None) is not None:
            continue
        assert name in warnings, f"Required point {name} disappeared without an ephemeris warning"
        with ephemeris_session() as flags:
            try:
                ephe.calc_ut(subject.julian_day, STANDARD_PLANETS[name], flags)
            except ephe.Error as error:
                message = str(error).lower()
                if "not found" in message and "file" in message:
                    reason = "required local ephemeris file is unavailable"
                elif "restricted to" in message or ("outside" in message and "range" in message):
                    reason = "requested date is outside the backend's supported coverage"
                else:
                    raise
            else:
                raise AssertionError(f"Swiss can calculate {name}, but Kerykeion omitted it")
        unavailable.append(f"{name}: {reason}")
    return tuple(unavailable)
