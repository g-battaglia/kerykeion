"""Read coverage from the backend's acquired immutable calculation snapshot.

LibEphemeris 4.0.0b4 owns shared readers and verified metadata. An additional
Python cache previously statted the entire inventory for every chart point,
costing substantially more than the native query and retaining duplicate
records. Delegate selection, invalidation, coverage and errors to the backend.
"""

from kerykeion.ephemeris_backend.backend import EPHEMERIS_LOCK, ephe


def clear_coverage_cache() -> None:
    """Compatibility hook; coverage no longer retains Python-side records.

    This never reloaded backend data. Use the backend's explicit reader/data
    reload API after provisioning, as for the calculations themselves.
    """


def get_body_coverage(body_id: int, jd: float):
    """Return actual backend metadata without rescanning or copying inventory.

    Keep the same lock used for session configuration, including for custom
    backend adapters. Preserve native range selection, flags, None and errors.
    """
    with EPHEMERIS_LOCK:
        return ephe.get_body_coverage(body_id, jd)
