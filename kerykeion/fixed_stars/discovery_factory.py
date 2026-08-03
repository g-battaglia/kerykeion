# -*- coding: utf-8 -*-
"""
Fixed Star Discovery Factory (v6)

Finds fixed stars conjunct natal points within a configurable orb.

The catalog is sourced from ``libephemeris`` (``list_fixed_stars()``);
``sefstars.txt`` is NOT used for licensing reasons. Position calculations
still go through the active ephemeris backend (``ephe.fixstar_ut``), which
on libephemeris uses its own internal data and on swisseph requires a
locally-installed ``sefstars.txt`` (only relevant for users who manage
their own catalog).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

from __future__ import annotations

import logging
import math
from contextlib import contextmanager
from typing import Iterator, cast

from kerykeion._predictive_utils import validate_julian_day
from kerykeion.astrological_subject_factory import _precision_class_for_source
from kerykeion.ephemeris_backend import BACKEND_NAME, EPHE_DATA_PATH, ephemeris_session, ephe
from kerykeion.fixed_stars.catalog import FixedStarCatalog
from kerykeion.schemas.kerykeion_exception import KerykeionException
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import AstrologicalSubjectModel, KerykeionPointModel
from kerykeion.utilities import HOUSE_FIELD_NAMES
from kerykeion.utilities import get_kerykeion_point_from_degree, get_planet_house

logger = logging.getLogger(__name__)


def _collect_planet_positions(subject: AstrologicalSubjectModel) -> list[tuple[str, float]]:
    """Collect calculated active point positions for conjunction checks."""
    planet_positions: list[tuple[str, float]] = []
    for point_name in subject.active_points:
        point = subject.get(point_name.lower())
        if point is not None and hasattr(point, "abs_pos"):
            planet_positions.append((str(point_name), point.abs_pos))
    return planet_positions


def _collect_house_cusps(subject: AstrologicalSubjectModel) -> list[float]:
    """Collect house cusp longitudes for house placement.

    Direct attribute access on the canonical HOUSE_FIELD_NAMES: a missing
    house field is a broken subject and must fail loudly, not produce a
    silently short cusp list.
    """
    return [getattr(subject, house_key).abs_pos for house_key in HOUSE_FIELD_NAMES]


def _nearest_conjunction(
    star_deg: float,
    planet_positions: list[tuple[str, float]],
    orb: float,
) -> tuple[str, float] | None:
    """Return nearest conjunct point and orb, or None when outside orb."""
    nearest: tuple[str, float] | None = None
    for point_name, planet_pos in planet_positions:
        diff = abs(star_deg - planet_pos)
        if diff > 180:
            diff = 360 - diff
        if diff <= orb and (nearest is None or diff < nearest[1]):
            nearest = (point_name, diff)
    return nearest


@contextmanager
def _star_source_trace() -> Iterator[dict[str, str | None]]:
    """Scope backend source tracing to a single star's ephemeris calls.

    ``start_tracing`` sets a ContextVar, so scopes nest cleanly: opening one
    per star keeps the collected map down to that star's own body id, which is
    what lets us read the source label back without an id -> name inventory
    (the fixed-star id space, unlike the planetary one, exposes none).

    The label is written into the yielded holder on exit, so a caller that
    leaves the block early — a star that turned out to be outside orb — still
    resets the token. On backends without tracing the holder stays ``None``
    and the provenance fields are simply left unset.
    """
    holder: dict[str, str | None] = {"source": None}
    token = None
    if BACKEND_NAME == "libephemeris":
        try:
            token = ephe.start_tracing()
        except AttributeError:
            token = None  # libephemeris version without tracing support
    try:
        yield holder
    finally:
        if token is not None:
            try:
                trace_map = ephe.get_trace_results()
            except AttributeError:
                trace_map = {}
            if trace_map:
                # One scope per star means at most one traced body, so the
                # single recorded label is this star's source by construction.
                holder["source"] = str(next(iter(trace_map.values())))
            try:
                token.var.reset(token)
            except (RuntimeError, ValueError):
                pass


def _build_discovery_point(
    star_name: str,
    pos_ecl: tuple,
    pos_eq: tuple | None,
    star_mag: float | None,
    houses_degree_ut: list[float],
    near_point: str,
    discovery_orb: float,
    source: str | None = None,
) -> KerykeionPointModel:
    """Build a Kerykeion point enriched with discovery metadata."""
    star_deg = pos_ecl[0]
    star_lat = pos_ecl[1] if len(pos_ecl) > 1 else None
    star_speed = pos_ecl[3] if len(pos_ecl) > 3 else 0.0
    star_dec = pos_eq[1] if pos_eq is not None and len(pos_eq) > 1 else None

    point = get_kerykeion_point_from_degree(
        star_deg,
        # Catalog star names are an open set; the model accepts them at runtime.
        cast(AstrologicalPoint, star_name),
        point_type="AstrologicalPoint",
        speed=star_speed,
        declination=star_dec,
        magnitude=star_mag,
    )
    if houses_degree_ut:
        point.house = get_planet_house(star_deg, houses_degree_ut)
    point.retrograde = False
    point.near_point = near_point
    point.orb = discovery_orb
    point.aspect = "conjunction"
    # Discovered stars answer to the same provenance contract as every other
    # point: a star listed next to planets that declare their source, while
    # declaring nothing itself, reads as less trustworthy than it is. The
    # coverage window and the review flag stay unset on purpose — the backend
    # publishes no coverage inventory for the fixed-star id space, and filling
    # them from the planetary inventory would be a claim we cannot back.
    if source is not None:
        point.source = source
        point.precision_class = _precision_class_for_source(source)
    point.longitude = star_deg
    point.latitude = star_lat
    point.degree = point.position
    return point


class FixedStarDiscoveryFactory:
    """Factory for discovering fixed-star conjunctions in a chart.

    Catalog source is ``libephemeris`` (single source of truth, v6).
    """

    @staticmethod
    def find_prominent_stars(
        subject: AstrologicalSubjectModel,
        orb: float = 1.0,
    ) -> list[KerykeionPointModel]:
        """Find fixed stars conjunct natal planets within ``orb`` degrees.

        Star longitudes are computed in the subject's own zodiac frame (the
        ephemeris session is opened with the subject's zodiac configuration),
        so the conjunction comparison against the natal ``abs_pos`` values is
        frame-consistent for sidereal charts too. Equatorial data (declination)
        is fetched without the sidereal flag: it is physical and independent of
        the zodiac convention.

        Each returned point also carries the backend source that produced it
        and the matching precision class, so a discovered star is as auditable
        as the planets it is reported against.

        Returns a list of KerykeionPointModel sorted by magnitude (brightest first).
        Only stars that are within ``orb`` degrees of any natal planet are included.
        ``orb`` must be finite and non-negative.
        """
        if not math.isfinite(orb) or orb < 0:
            raise KerykeionException(f"orb must be a finite number >= 0, got {orb}")

        # Validate the instant before any empty-subject/catalog fast path. A
        # non-finite JD makes every per-star backend call fail; the deliberately
        # resilient per-entry handler would otherwise turn a corrupt subject
        # into a plausible empty discovery result.
        if subject.julian_day is None:
            raise KerykeionException(
                "Subject is missing Julian Day — cannot search fixed stars (composite subjects are not supported here)."
            )
        try:
            validate_julian_day(subject.julian_day)
        except ValueError as exc:
            # Keep this factory's documented KerykeionException boundary (the
            # None-JD and orb checks above raise it too).
            raise KerykeionException(
                f"Subject Julian Day must be a finite number, got {subject.julian_day!r}."
            ) from exc
        jd = subject.julian_day

        planet_positions = _collect_planet_positions(subject)
        if not planet_positions:
            return []

        catalog = FixedStarCatalog.list_all()
        if not catalog:
            return []

        houses_degree_ut = _collect_house_cusps(subject)
        prominent: list[KerykeionPointModel] = []
        seen_names: set[str] = set()
        with ephemeris_session(
            zodiac_type=getattr(subject, "zodiac_type", None),
            sidereal_mode=getattr(subject, "sidereal_mode", None),
            custom_ayanamsa_t0=getattr(subject, "custom_ayanamsa_t0", None),
            custom_ayanamsa_ayan_t0=getattr(subject, "custom_ayanamsa_ayan_t0", None),
        ) as scan_iflag:
            for entry in catalog:
                star_name = entry.name
                # Each catalog entry is a physically distinct star (unique by
                # name/hip_number), so we dedupe by identity only — guarding
                # against duplicate catalog entries, NOT by position. Two
                # different stars sharing a rounded ecliptic longitude (e.g.
                # Beta Scuti and Nunki, ~0.005° apart) must both be reported;
                # a position-based dedupe would silently drop the second one,
                # which after libephemeris 3.0's 1447-star catalog suppressed
                # bright/important stars in favour of fainter catalog neighbours.
                if star_name in seen_names:
                    continue
                seen_names.add(star_name)
                try:
                    with _star_source_trace() as star_trace:
                        pos_ecl = ephe.fixstar_ut(star_name, jd, scan_iflag)[0]
                        star_deg = pos_ecl[0]

                        nearest = _nearest_conjunction(star_deg, planet_positions, orb)
                        if nearest is None:
                            continue

                        # Declination is zodiac-independent; drop FLG_SIDEREAL so the
                        # equatorial fetch is identical for tropical and sidereal charts.
                        eq_iflag = (scan_iflag & ~ephe.FLG_SIDEREAL) | ephe.FLG_EQUATORIAL
                        pos_eq = ephe.fixstar_ut(star_name, jd, eq_iflag)[0]

                    star_mag = entry.magnitude

                    prominent.append(
                        _build_discovery_point(
                            star_name,
                            pos_ecl,
                            pos_eq,
                            star_mag,
                            houses_degree_ut,
                            near_point=nearest[0],
                            discovery_orb=nearest[1],
                            source=star_trace["source"],
                        )
                    )
                except Exception as e:
                    logger.debug(f"Skipping star {star_name}: {e}")
                    continue

        # v6: emit a single actionable warning when nothing was returned on
        # the swisseph backend — almost always means sefstars.txt is missing
        # from KERYKEION_EPHE_PATH. See site/docs/swisseph_configuration.md.
        if not prominent and BACKEND_NAME == "swisseph":
            logger.warning(
                "FixedStarDiscoveryFactory found no stars on the swisseph backend. "
                "The catalog file 'sefstars.txt' is not bundled with kerykeion due "
                "to licensing. Download it from "
                "https://github.com/aloistr/swisseph/tree/master/ephe and place it "
                "in KERYKEION_EPHE_PATH (%s). Alternatively use "
                "KERYKEION_BACKEND=libephemeris (ships its own catalog).",
                EPHE_DATA_PATH or "<unset>",
            )

        prominent.sort(key=lambda p: p.magnitude if p.magnitude is not None else 99)
        return prominent
