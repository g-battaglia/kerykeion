"""Bounded caching of native v4 *metadata*, never planetary calculations.

Early v4 snapshots verified every active LEB digest for each coverage query,
rehashing several GB per chart point. Upstream now caches immutable digests;
this compatibility cache still reuses native records while configuration,
file identities and date-coverage membership are unchanged. Precision classes and reviewed flags remain native;
we never manufacture them from filenames or promote unreviewed data.
"""

from collections import OrderedDict
import inspect
import math
import os

from kerykeion.ephemeris_backend.backend import EPHEMERIS_LOCK, ephe

_MAX_RECORDS = 512
_state = None
_paths: tuple[str, ...] = ()
_fingerprint: tuple = ()
_intervals: dict[int, list[tuple[float, float]]] = {}
_records: OrderedDict = OrderedDict()


def _stat(path: str) -> tuple:
    try:
        stat = os.stat(path)
        return (path, stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    except OSError:
        return (path, None)


def clear_coverage_cache() -> None:
    """Discard metadata snapshots (also useful after external data provisioning)."""
    global _state, _paths, _fingerprint
    with EPHEMERIS_LOCK:
        _state, _paths, _fingerprint = None, (), ()
        _intervals.clear()
        _records.clear()


def get_body_coverage(body_id: int, jd: float):
    """Return the actual backend record, caching only unchanged LEB metadata.

    Exact coverage-region membership is the cache key, not merely containment
    in a previously returned interval: an extended file may overlap a preferred
    base file. File/directory stat changes or provider/tier changes invalidate
    the snapshot. Missing, nonnative, mocked and undated APIs bypass caching.
    Callers continue to use calc_ut for scientific decisions and range errors.
    """
    global _state, _paths, _fingerprint
    getter = ephe.get_body_coverage
    if (
        not getattr(ephe, "__version__", "").startswith("4.")
        or not inspect.isbuiltin(getter)
        or jd is None
        or not math.isfinite(jd)
    ):
        return getter(body_id, jd)
    with EPHEMERIS_LOCK:
        reader = ephe.get_leb_reader()
        # Virtual/bundled readers have no filesystem identity to invalidate.
        # Their search directories can gain external groups after provisioning;
        # let the native runtime resolve those records on every request.
        if reader is None or _stat(reader.path)[1] is None:
            return getter(body_id, jd)
        # Provisioning can replace a serving image in a previously empty search
        # directory. File stamps alone cannot see it. Native invalidation tokens
        # track that transition without rescanning or hashing the inventory.
        generation = getattr(ephe, "get_leb_reader_generation", None)
        state = (getter, ephe.get_calc_mode(), ephe.get_precision_tier(), ephe.get_current_file_data(), reader.path,
                 generation() if callable(generation) else None)
        fingerprint = tuple(_stat(path) for path in _paths)
        if state != _state or fingerprint != _fingerprint:
            inventory = ephe.get_leb_inventory()
            files = inventory.get("files", [])
            # A directory stamp catches added/removed group files as well as
            # checking individual files for replacement or in-place updates.
            paths = {entry["path"] for entry in files}
            paths.update(os.path.dirname(path) for path in tuple(paths))
            _paths = tuple(sorted(paths))
            _fingerprint = tuple(_stat(path) for path in _paths)
            _state = state
            _intervals.clear()
            _records.clear()
            for entry in files:
                for body in entry.get("bodies", []):
                    _intervals.setdefault(body["body_id"], []).append((body["jd_start"], body["jd_end"]))
        membership = tuple(start <= jd <= end for start, end in _intervals.get(body_id, []))
        # An empty/all-false key cannot distinguish analytic providers, newly
        # provisioned groups or different unserved epochs. Never memoize it.
        if not any(membership):
            return getter(body_id, jd)
        key = (body_id, membership)
        if key in _records:
            _records.move_to_end(key)
            return _records[key]
        record = getter(body_id, jd)
        _records[key] = record
        if len(_records) > _MAX_RECORDS:
            _records.popitem(last=False)
        return record
