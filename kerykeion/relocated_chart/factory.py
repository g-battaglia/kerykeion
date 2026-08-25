# -*- coding: utf-8 -*-
"""Relocated chart factory.

A relocated chart keeps ALL planetary positions identical to the natal chart
but recalculates houses and angles (ASC, MC, DSC, IC) for a different
geographic location. This is equivalent to asking: "If I had been born at
the same Universal Time but in a different city, which houses would my
planets fall in?"

Ephemeris function: ``houses_ex2_with_polar_fallback_ex(...)`` (a polar-safe
wrapper over the backend's ``houses_ex2``, which substitutes the house SYSTEM
rather than the latitude so the relocated angles stay exact)

Location-dependent derived points are recomputed as well: the Vertex /
Anti-Vertex (from the same house call), the Ascendant-based Arabic
parts (with the day/night formula re-selected from the Sun's altitude at the
new location), and the local ISO datetime when a new timezone is provided.
For sidereal subjects the tropical house output is shifted by the
subject's ayanamsa so the relocated cusps stay in the natal zodiac.

Per-point local-space / Gauquelin enrichments (``azimuth``,
``altitude_above_horizon``, ``gauquelin_sector``) and the subject-level
``gauquelin_sector_cusps`` are also location-dependent but are NOT recomputed
for the new location: they are reset to ``None`` on the relocated subject.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from kerykeion.ephemeris_backend.backend import ephe, ephemeris_session, houses_ex2_with_polar_fallback_ex

from kerykeion.schemas.exceptions import KerykeionException
from kerykeion.schemas.literals import AstrologicalPoint, Houses
from kerykeion.schemas.models import AstrologicalSubjectModel
from kerykeion.settings.config_constants import AXIAL_POINTS
from kerykeion.utilities.core import (
    validate_latitude,
    normalize_longitude,
    safe_timezone,
    get_kerykeion_point_from_degree,
    angle_house_identities,
    coincident_cusp_groups,
    get_planet_house,
    _assemble_ancient_iso,
    _split_decimal_hour_with_carry,
)

_AXIAL_POINTS_SET: frozenset[str] = frozenset(AXIAL_POINTS)


#: Sidereal modes that request a fixed reference frame rather than an ayanamsa
#: along the ecliptic of date; the reference keeps Sunshine 'i' on its own
#: construction under these.
_FIXED_EPOCH_SIDEREAL_MODES = frozenset({"J2000", "J1900", "B1950", "GALALIGN_MARDYKS"})


def _house_system_the_reference_casts(hsys: bytes, is_sidereal: bool, sidereal_mode: Optional[str]) -> bytes:
    """The house system the ephemeris actually computes for a sidereal request.

    Under a sidereal flag the reference implementation casts Sunshine 'i'
    (Makransky) as 'I' (Treindl) — libephemeris matches it, see its
    ``houses_ex`` — except in the fixed-epoch modes, where 'i' stays on its own
    construction. The natal chart got that ring because it asked with the
    sidereal flag. This factory asks TROPICALLY and applies the subject's own
    ayanamsa afterwards, so it has to ask for the same system the reference would
    pick, or a sidereal 'i' relocated onto its own birthplace would come back a
    different chart: Makransky cusps, tens of degrees from Treindl's at sixty
    degrees north, and inside the polar circle a refused cast substituted with
    Porphyry, where the natal has a Sunshine ring.
    """
    if is_sidereal and hsys == b"i" and sidereal_mode not in _FIXED_EPOCH_SIDEREAL_MODES:
        return b"I"
    return hsys


class RelocatedChartFactory:
    """Create a relocated chart from an existing natal chart."""

    @staticmethod
    def _recompute_local_datetime_fields(
        relocated_data: dict,
        *,
        year: int,
        julian_day: float,
        new_lng: float,
        new_tz_str: Optional[str],
        iso_utc: str,
    ) -> None:
        """Recompute the local calendar fields for a new timezone in place.

        The UTC instant is unchanged; only its local representation moves.
        Updates ``relocated_data`` with ``year``/``month``/``day``/``hour``/
        ``minute``/``seconds`` and ``iso_formatted_local_datetime`` so they stay
        mutually consistent.

        BCE subjects (``year < 1``) store extended-year ISO strings (e.g.
        ``"-0500-03-21T..."``) that ``datetime.fromisoformat`` cannot parse and
        no tzinfo can localise, so they take the subject factory's ancient
        path: derive local time from the (unchanged) UT Julian Day using the new
        longitude's Local Mean Time offset (named timezones are anachronistic
        for BCE). The h/m/s split matches ``format_ancient_iso`` so the integer
        fields and the ISO string agree.
        """
        if year < 1:
            # Quantize the LMT offset to the whole second (matching the subject
            # factory's BCE path and the CE LMT path) so the recomputed local ISO
            # offset and the UT-derived instant describe the identical time.
            lmt_offset_hours = round(new_lng / 15.0 * 3600) / 3600.0
            jd_local = julian_day + lmt_offset_hours / 24.0
            loc_year, loc_month, loc_day, loc_dec_hour = ephe.revjul(jd_local, ephe.JUL_CAL)
            loc_year, loc_month, loc_day = int(loc_year), int(loc_month), int(loc_day)
            # Decompose the integer h/m/s ONCE with the shared helper (rounds to the
            # nearest second and carries any midnight rollover into the next
            # proleptic-Julian day), then assemble the ISO string from those same
            # fields. Sourcing both the stored fields and the ISO string from a
            # single split means they can never drift apart at a second boundary
            # (int() truncation would otherwise lag the rounded string by up to ~1s).
            field_year, field_month, field_day, field_hour, field_minute, field_seconds = (
                _split_decimal_hour_with_carry(loc_year, loc_month, loc_day, loc_dec_hour)
            )
            relocated_data["year"] = field_year
            relocated_data["month"] = field_month
            relocated_data["day"] = field_day
            relocated_data["hour"] = field_hour
            relocated_data["minute"] = field_minute
            relocated_data["seconds"] = field_seconds
            relocated_data["iso_formatted_local_datetime"] = _assemble_ancient_iso(
                field_year, field_month, field_day, field_hour, field_minute, field_seconds, lmt_offset_hours
            )
        else:
            # The CE path is only entered by the caller when new_tz_str is
            # truthy (the year >= 1 branch of the gating condition); make the
            # non-None guarantee explicit for the type checker.
            assert new_tz_str is not None
            utc_dt = datetime.fromisoformat(iso_utc)
            if utc_dt.tzinfo is None:
                utc_dt = utc_dt.replace(tzinfo=timezone.utc)
            try:
                # A near-datetime.max/min instant (extended-kernel year-9999 or
                # year-1 subject) can push the local wall time past datetime's
                # representable range, raising a raw OverflowError/OSError. The
                # subject factory entry points surface the equivalent boundary as
                # KerykeionException; match that contract here.
                local_dt = utc_dt.astimezone(safe_timezone(new_tz_str))
            except (OverflowError, OSError) as exc:
                raise KerykeionException(
                    f"Relocating {iso_utc!r} to timezone {new_tz_str!r} pushes the "
                    f"local wall time outside the representable date range: {exc}."
                ) from exc
            relocated_data["iso_formatted_local_datetime"] = local_dt.isoformat()
            relocated_data["year"] = local_dt.year
            relocated_data["month"] = local_dt.month
            relocated_data["day"] = local_dt.day
            relocated_data["hour"] = local_dt.hour
            relocated_data["minute"] = local_dt.minute
            relocated_data["seconds"] = local_dt.second

    @staticmethod
    def relocate(
        subject: AstrologicalSubjectModel,
        new_lat: float,
        new_lng: float,
        new_city: str = "Relocated",
        new_nation: str = "",
        new_tz_str: Optional[str] = None,
    ) -> AstrologicalSubjectModel:
        """Relocate a natal chart to a new geographic location.

        Planetary positions remain unchanged. Houses, angles, Vertex /
        Anti-Vertex and the Ascendant-derived Arabic parts are recalculated
        for the new latitude/longitude.

        Args:
            subject: Original natal chart.
            new_lat: New latitude (north positive).
            new_lng: New longitude (east positive).
            new_city: City name for the relocated chart.
            new_nation: Country code.
            new_tz_str: Timezone (defaults to original).

        Returns:
            New AstrologicalSubjectModel with relocated houses.

        Raises:
            KerykeionException: If the subject uses the Topocentric perspective
                (its planetary positions embed the natal observer's parallax,
                so they cannot be kept while coherently moving the observer).
        """
        if subject.perspective_type == "Topocentric":
            raise KerykeionException(
                "Cannot relocate a Topocentric chart: its planetary positions "
                "embed the parallax of the natal observer, so a coherent "
                "relocation would require recomputing the planets for the new "
                "observer. Re-create the subject with the new coordinates "
                "(perspective_type='Topocentric') instead."
            )

        jd = subject.julian_day
        is_sidereal = subject.zodiac_type == "Sidereal"
        hsys = _house_system_the_reference_casts(
            subject.houses_system_identifier.encode("ascii"), is_sidereal, subject.sidereal_mode
        )

        # Validate but do NOT clamp: relocating to lat 78 must persist the real
        # latitude and cast latitude-agnostic house systems there, exactly like a
        # natal chart. Quadrant systems undefined inside the polar circle fall
        # back locally at the houses call below. Raises on impossible |lat| > 90.
        new_lat = validate_latitude(new_lat)
        # Wrap an un-normalized longitude (e.g. 370 == 10 E) into [-180, 180) as
        # the natal path does, so relocation accepts wrapped values instead of
        # the houses backend raising a raw CoordinateError.
        new_lng = normalize_longitude(new_lng)

        # houses_ex2 outputs tropical longitudes. For sidereal subjects the
        # session configures the subject's ayanamsa so get_ayanamsa_ut()
        # returns the matching offset to shift cusps/angles into the
        # subject's sidereal zodiac.
        with ephemeris_session(
            zodiac_type=subject.zodiac_type,
            sidereal_mode=subject.sidereal_mode,
            custom_ayanamsa_t0=subject.custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=subject.custom_ayanamsa_ayan_t0,
        ) as _iflag:
            # Calculate new houses for the new location via houses_ex2 — the
            # SAME call the natal path uses — so it computes the ARMC internally
            # and exactly. Reconstructing the ARMC from ephe.sidtime(jd) + lng/15
            # and feeding houses_armc introduced a sidtime-vs-internal-ARMC
            # divergence (~1 arcsec, amplified at high latitude) that made
            # relocating to one's own birthplace NOT a house no-op.
            #
            # Request TROPICAL cusps (mask FLG_SIDEREAL): the sidereal shift is
            # applied explicitly below using the subject's stored ayanamsa_value
            # (which carries nutation-in-longitude), matching the natal chart.
            # Letting houses_ex2 apply the sidereal flag itself would double-
            # subtract the ayanamsa.
            tropical_iflag = _iflag & ~ephe.FLG_SIDEREAL
            # The ``_ex`` variant also reports whether the requested house system
            # had to be substituted: relocating TOWARDS a polar latitude is the
            # most common way a real user meets the case, and the relocated
            # subject is the only place that fact can still be told.
            cusps, ascmc, _cusps_speed, _ascmc_speed, polar_fallback = houses_ex2_with_polar_fallback_ex(
                jd, new_lat, new_lng, hsys, tropical_iflag, context=new_city or subject.name
            )

            # Sidereal charts: shift the tropical cusps/angles by the ayanamsa.
            # Use the subject's stored ayanamsa_value: it was computed alongside
            # the natal cusps so it is consistent by construction on both
            # backends. (pyswisseph's get_ayanamsa_ut returns the MEAN ayanamsa
            # — no nutation — while sidereal cusps use the true ayanamsa, which
            # would leave relocated cusps off by nutation-in-longitude.)
            if is_sidereal:
                ayanamsa = subject.ayanamsa_value
                if ayanamsa is None:
                    ayanamsa = ephe.get_ayanamsa_ex_ut(jd, ephe.FLG_SWIEPH)[1]
            else:
                ayanamsa = 0.0

        cusps = [(c - ayanamsa) % 360.0 for c in cusps]
        ascmc = [(a - ayanamsa) % 360.0 for a in ascmc]

        # Build house degree list for planet house assignment
        houses_degree_ut = list(cusps)

        # Decided on the cusps and angles this chart will actually carry — after
        # the sidereal shift, which moves both by the same arc and so cannot
        # change which cusp an angle is standing on, but is part of making them.
        angle_houses = angle_house_identities(houses_degree_ut, ascmc[0], ascmc[1])

        # Create house KerykeionPointModels
        house_data = {}
        house_names = [
            "first_house",
            "second_house",
            "third_house",
            "fourth_house",
            "fifth_house",
            "sixth_house",
            "seventh_house",
            "eighth_house",
            "ninth_house",
            "tenth_house",
            "eleventh_house",
            "twelfth_house",
        ]
        houses_list: list[Houses] = [
            "First_House",
            "Second_House",
            "Third_House",
            "Fourth_House",
            "Fifth_House",
            "Sixth_House",
            "Seventh_House",
            "Eighth_House",
            "Ninth_House",
            "Tenth_House",
            "Eleventh_House",
            "Twelfth_House",
        ]
        for i, hname in enumerate(house_names):
            house_data[hname] = get_kerykeion_point_from_degree(cusps[i], houses_list[i], "House")

        # Create angular points
        asc_deg = ascmc[0] % 360
        mc_deg = ascmc[1] % 360
        desc_deg = (asc_deg + 180) % 360
        ic_deg = (mc_deg + 180) % 360

        axis_degrees: dict[str, tuple[AstrologicalPoint, float]] = {
            "ascendant": ("Ascendant", asc_deg),
            "medium_coeli": ("Medium_Coeli", mc_deg),
            "descendant": ("Descendant", desc_deg),
            "imum_coeli": ("Imum_Coeli", ic_deg),
        }

        # Vertex / Anti-Vertex come from ascmc[3] of the same houses_ex2 call
        # (the Vertex is house-system independent but location dependent).
        if subject.vertex is not None or subject.anti_vertex is not None:
            vertex_deg = ascmc[3] % 360
            if subject.vertex is not None:
                axis_degrees["vertex"] = ("Vertex", vertex_deg)
            if subject.anti_vertex is not None:
                axis_degrees["anti_vertex"] = ("Anti_Vertex", (vertex_deg + 180) % 360)

        for field_name, (point_name, degree) in axis_degrees.items():
            point = get_kerykeion_point_from_degree(degree, point_name, "AstrologicalPoint")
            # Relocating TOWARDS a polar latitude is the common way a real user
            # meets a ring with cusps on top of each other, so this is exactly
            # where an angle must be given the house it opens rather than the
            # earliest cusp that happens to share its longitude. The Vertex has no
            # such identity — it is nobody's cusp — and reads as before.
            point.house = angle_houses.get(field_name) or get_planet_house(degree, houses_degree_ut)
            point.retrograde = False
            house_data[field_name] = point

        # Copy original subject data and override houses + angles
        relocated_data = subject.model_dump()

        # Per-point local-space / Gauquelin enrichments and the Gauquelin
        # sector cusps were computed for the NATAL location and are not
        # recomputed here: null them rather than carrying stale values that
        # silently describe the wrong horizon.
        _LOCATION_DEPENDENT_FIELDS = ("azimuth", "altitude_above_horizon", "gauquelin_sector")

        def _null_location_fields(point_data: object) -> None:
            if isinstance(point_data, dict):
                for field in _LOCATION_DEPENDENT_FIELDS:
                    if field in point_data:
                        point_data[field] = None

        for point_data in relocated_data.values():
            _null_location_fields(point_data)
        # Fixed stars (and any other list-valued point collection) live in a list,
        # not as a scalar KerykeionPointModel value, so the loop above skips them.
        # Without this, a relocated chart's fixed stars keep the NATAL location's
        # azimuth/altitude/gauquelin_sector — the exact stale-horizon bug this block
        # exists to prevent.
        for star_data in relocated_data.get("fixed_stars") or []:
            _null_location_fields(star_data)
        relocated_data["gauquelin_sector_cusps"] = None

        # Any polar fallback the NATAL chart recorded describes the natal
        # location's house call, which this factory has just replaced. Overwrite
        # rather than append, for the same reason the enrichments above are
        # nulled: carrying it over would attribute a substitution to a latitude
        # that no longer produced these cusps.
        relocated_data["polar_house_fallbacks"] = [polar_fallback] if polar_fallback is not None else []
        relocated_data["coincident_house_cusps"] = coincident_cusp_groups(houses_degree_ut)
        # As in the natal path, the requested system stays in
        # `houses_system_identifier` so a further recast is not poisoned by a
        # substitution that belonged to one location. Rendering reads
        # `effective_houses_system_*` instead.

        relocated_data.update(house_data)
        relocated_data["city"] = new_city
        relocated_data["nation"] = new_nation or subject.nation
        relocated_data["lat"] = new_lat
        relocated_data["lng"] = new_lng
        relocated_data["tz_str"] = new_tz_str or subject.tz_str
        relocated_data["houses_names_list"] = houses_list

        # Recompute the local ISO datetime for the new timezone (the UTC
        # moment is unchanged — only its local representation moves). A BCE
        # subject (year < 1) has no named timezone: its local time IS Local
        # Mean Time (lng/15), so a longitude change alone makes the stored
        # local fields stale even without new_tz_str — recompute them too (the
        # BCE branch of the helper ignores new_tz_str and derives LMT from the
        # new longitude).
        if new_tz_str or subject.year < 1:
            RelocatedChartFactory._recompute_local_datetime_fields(
                relocated_data,
                year=subject.year,
                julian_day=jd,
                new_lng=new_lng,
                new_tz_str=new_tz_str,
                iso_utc=subject.iso_formatted_utc_datetime,
            )
            # The weekday follows the local calendar date, which can change
            # across timezones for the same UTC instant.
            from kerykeion.astrological_subject.factory import AstrologicalSubjectFactory as _ASF

            _ASF._calculate_day_of_week(relocated_data)

        # Sect (day/night) depends on the observer's horizon: recompute it for
        # the new location so the Arabic part formulas pick the right branch.
        from kerykeion.astrological_subject.factory import ARABIC_PARTS_CONFIG, AstrologicalSubjectFactory

        # _compute_is_diurnal calls ephe.* (tropical geocentric Sun + azalt), so
        # it must run inside an ephemeris session — same lock/path contract as
        # the subject factory, which computes sect inside its own session. A
        # plain session is enough: _compute_is_diurnal builds its own flags.
        with ephemeris_session():
            # AstrologicalSubjectModel does not carry an ``altitude`` field, so
            # the sect computation uses sea level (0.0) — the getattr here was
            # dead code that always resolved to None. Altitude only shifts sect
            # by arcminutes near sunrise/sunset; a relocation may change it
            # anyway, so 0.0 is the honest default.
            is_diurnal = AstrologicalSubjectFactory._compute_is_diurnal(
                jd, new_lat, new_lng, 0.0
            )
        relocated_data["is_diurnal"] = is_diurnal

        # Essential dignities depend on sect (the triplicity ruler flips
        # between day and night charts): recompute them with the relocated
        # sect so the model stays internally consistent when relocation flips
        # is_diurnal. Only do this when the natal subject carried dignity data
        # (the enrichment is opt-in).
        if any(
            isinstance(p, dict) and p.get("essential_dignity") is not None
            for p in relocated_data.values()
        ):
            from kerykeion.dignities import calculate_essential_dignity

            for point_data in relocated_data.values():
                if not (isinstance(point_data, dict) and "essential_dignity" in point_data):
                    continue
                if point_data.get("abs_pos") is None or point_data.get("name") is None:
                    continue
                point_data.update(
                    calculate_essential_dignity(
                        planet_name=point_data["name"],
                        sign=point_data["sign"],
                        element=point_data["element"],
                        position=point_data["position"],
                        is_diurnal=is_diurnal,
                    )
                )

        # Recompute the Ascendant-derived Arabic parts with the relocated ASC
        # and the recomputed sect (planet positions are unchanged).
        for part_name, part_config in ARABIC_PARTS_CONFIG.items():
            part_field = part_name.lower()
            if relocated_data.get(part_field) is None:
                continue

            # `collected_positions` aliases the same list; `positions` doubles as the
            # None marker for missing prerequisites (mypy cannot narrow it in the loop).
            collected_positions: list[float] = []
            positions: Optional[list[float]] = collected_positions
            for required_point in part_config["required"]:
                if required_point == "Ascendant":
                    collected_positions.append(asc_deg)
                    continue
                required_data = relocated_data.get(required_point.lower())
                if required_data is None:
                    positions = None
                    break
                collected_positions.append(required_data["abs_pos"])
            if positions is None:
                continue

            if "day_formula" in part_config and "night_formula" in part_config:
                formula = part_config["day_formula"] if is_diurnal else part_config["night_formula"]
            else:
                formula = part_config["formula"]

            part_deg = math.fmod(formula(*positions), 360)
            if part_deg < 0:
                part_deg += 360

            part_point = get_kerykeion_point_from_degree(part_deg, part_name, "AstrologicalPoint")
            part_point.house = get_planet_house(part_deg, houses_degree_ut)
            part_point.retrograde = False
            # The natal lot carries Derived provenance inherited from its
            # planetary primaries; relocation changes houses, not primaries.
            prior_part = relocated_data.get(part_field)
            if isinstance(prior_part, dict):
                part_point.source = prior_part.get("source")
                part_point.precision_class = prior_part.get("precision_class")
                part_point.ephemeris_coverage_start_jd = prior_part.get("ephemeris_coverage_start_jd")
                part_point.ephemeris_coverage_end_jd = prior_part.get("ephemeris_coverage_end_jd")
                part_point.source_reviewed = prior_part.get("source_reviewed")
            relocated_data[part_field] = part_point

        # Reassign EVERY non-axial point stored on the model to its new house —
        # not just active_points. Derived opposite points (South lunar nodes,
        # Priapus) are stored unconditionally by _calculate_opposite_points but
        # are absent from DEFAULT_ACTIVE_POINTS, so an active_points-only loop
        # left them with their stale natal house (breaking, e.g., the
        # North/South node opposition). Axial angles are recomputed above; house
        # cusps are their own reference and must not be re-housed.
        for field_name, point_data in relocated_data.items():
            if field_name.endswith("_house"):
                continue
            if not (isinstance(point_data, dict) and point_data.get("abs_pos") is not None):
                continue
            if point_data.get("name") in _AXIAL_POINTS_SET or "house" not in point_data:
                continue
            point_data["house"] = get_planet_house(point_data["abs_pos"], houses_degree_ut)

        # Fixed stars keep their zodiacal positions but live outside
        # active_points: reassign their houses against the relocated cusps too.
        for star_data in relocated_data.get("fixed_stars") or []:
            if isinstance(star_data, dict) and star_data.get("abs_pos") is not None:
                star_data["house"] = get_planet_house(star_data["abs_pos"], houses_degree_ut)

        # Active midpoints are another list field outside active_points; like the
        # fixed stars above they keep their zodiacal position but must be
        # re-housed against the relocated cusps, else they keep a stale natal
        # house (visible in report.py's House column and chart_drawer).
        for mp_data in relocated_data.get("active_midpoints") or []:
            if isinstance(mp_data, dict) and mp_data.get("abs_pos") is not None:
                mp_data["house"] = get_planet_house(mp_data["abs_pos"], houses_degree_ut)

        return AstrologicalSubjectModel(**relocated_data)
