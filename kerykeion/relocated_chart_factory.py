# -*- coding: utf-8 -*-
"""Relocated chart factory.

A relocated chart keeps ALL planetary positions identical to the natal chart
but recalculates houses and angles (ASC, MC, DSC, IC) for a different
geographic location. This is equivalent to asking: "If I had been born at
the same Universal Time but in a different city, which houses would my
planets fall in?"

Swiss Ephemeris function: ``swe.houses_armc(armc, lat, eps, hsys)``

Location-dependent derived points are recomputed as well: the Vertex /
Anti-Vertex (from the same ``houses_armc`` call), the Ascendant-based Arabic
parts (with the day/night formula re-selected from the Sun's altitude at the
new location), and the local ISO datetime when a new timezone is provided.
For sidereal subjects the tropical ``houses_armc`` output is shifted by the
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

from kerykeion.ephemeris_backend import swe, ephemeris_session

from kerykeion.schemas.kr_literals import AstrologicalPoint, Houses
from kerykeion.schemas.kr_models import AstrologicalSubjectModel
from kerykeion.settings.config_constants import AXIAL_POINTS
from kerykeion.utilities import get_kerykeion_point_from_degree, get_planet_house

_AXIAL_POINTS_SET: frozenset[str] = frozenset(AXIAL_POINTS)


class RelocatedChartFactory:
    """Create a relocated chart from an existing natal chart."""

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
        """
        jd = subject.julian_day
        hsys = subject.houses_system_identifier.encode("ascii")
        is_sidereal = subject.zodiac_type == "Sidereal"

        # houses_armc works in tropical longitudes. For sidereal subjects the
        # session configures the subject's ayanamsa so get_ayanamsa_ut()
        # returns the matching offset to shift cusps/angles into the
        # subject's sidereal zodiac.
        with ephemeris_session(
            zodiac_type=subject.zodiac_type,
            sidereal_mode=subject.sidereal_mode,
            custom_ayanamsa_t0=subject.custom_ayanamsa_t0,
            custom_ayanamsa_ayan_t0=subject.custom_ayanamsa_ayan_t0,
        ) as _iflag:
            # Get obliquity of ecliptic (zodiac-independent)
            eps = swe.calc_ut(jd, swe.ECL_NUT, swe.FLG_SWIEPH | swe.FLG_SPEED)[0][0]

            # Get ARMC (sidereal time at Greenwich in degrees) from original JD
            armc_hours = swe.sidtime(jd)  # Greenwich sidereal time in hours
            # Adjust for new longitude: local sidereal time = GST + lng/15
            local_st_hours = armc_hours + new_lng / 15.0
            armc_degrees = (local_st_hours * 15.0) % 360.0

            # Calculate new houses for the new location (tropical output)
            cusps, ascmc = swe.houses_armc(armc_degrees, new_lat, eps, hsys)

            # Sidereal charts: shift the tropical cusps/angles by the ayanamsa.
            # Use the subject's stored ayanamsa_value: it was computed alongside
            # the natal cusps so it is consistent by construction on both
            # backends. (pyswisseph's get_ayanamsa_ut returns the MEAN ayanamsa
            # — no nutation — while sidereal cusps use the true ayanamsa, which
            # would leave relocated cusps off by nutation-in-longitude.)
            if is_sidereal:
                ayanamsa = subject.ayanamsa_value
                if ayanamsa is None:
                    ayanamsa = swe.get_ayanamsa_ex_ut(jd, swe.FLG_SWIEPH)[1]
            else:
                ayanamsa = 0.0

        cusps = [(c - ayanamsa) % 360.0 for c in cusps]
        ascmc = [(a - ayanamsa) % 360.0 for a in ascmc]

        # Build house degree list for planet house assignment
        houses_degree_ut = list(cusps)

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

        # Vertex / Anti-Vertex come from ascmc[3] of the same houses_armc call
        # (the Vertex is house-system independent but location dependent).
        if subject.vertex is not None or subject.anti_vertex is not None:
            vertex_deg = ascmc[3] % 360
            if subject.vertex is not None:
                axis_degrees["vertex"] = ("Vertex", vertex_deg)
            if subject.anti_vertex is not None:
                axis_degrees["anti_vertex"] = ("Anti_Vertex", (vertex_deg + 180) % 360)

        for field_name, (point_name, degree) in axis_degrees.items():
            point = get_kerykeion_point_from_degree(degree, point_name, "AstrologicalPoint")
            point.house = get_planet_house(degree, houses_degree_ut)
            point.retrograde = False
            house_data[field_name] = point

        # Copy original subject data and override houses + angles
        relocated_data = subject.model_dump()

        # Per-point local-space / Gauquelin enrichments and the Gauquelin
        # sector cusps were computed for the NATAL location and are not
        # recomputed here: null them rather than carrying stale values that
        # silently describe the wrong horizon.
        for point_data in relocated_data.values():
            if isinstance(point_data, dict):
                for location_dependent_field in ("azimuth", "altitude_above_horizon", "gauquelin_sector"):
                    if location_dependent_field in point_data:
                        point_data[location_dependent_field] = None
        relocated_data["gauquelin_sector_cusps"] = None

        relocated_data.update(house_data)
        relocated_data["city"] = new_city
        relocated_data["nation"] = new_nation or subject.nation
        relocated_data["lat"] = new_lat
        relocated_data["lng"] = new_lng
        relocated_data["tz_str"] = new_tz_str or subject.tz_str
        relocated_data["houses_names_list"] = houses_list

        # Recompute the local ISO datetime for the new timezone (the UTC
        # moment is unchanged — only its local representation moves).
        if new_tz_str:
            import pytz

            utc_dt = datetime.fromisoformat(subject.iso_formatted_utc_datetime)
            if utc_dt.tzinfo is None:
                utc_dt = utc_dt.replace(tzinfo=timezone.utc)
            relocated_local_dt = utc_dt.astimezone(pytz.timezone(new_tz_str))
            relocated_data["iso_formatted_local_datetime"] = relocated_local_dt.isoformat()
            relocated_data["year"] = relocated_local_dt.year
            relocated_data["month"] = relocated_local_dt.month
            relocated_data["day"] = relocated_local_dt.day
            relocated_data["hour"] = relocated_local_dt.hour
            relocated_data["minute"] = relocated_local_dt.minute
            relocated_data["seconds"] = relocated_local_dt.second
            # The weekday follows the local calendar date, which can change
            # across timezones for the same UTC instant.
            from kerykeion.astrological_subject_factory import AstrologicalSubjectFactory as _ASF

            _ASF._calculate_day_of_week(relocated_data)

        # Sect (day/night) depends on the observer's horizon: recompute it for
        # the new location so the Arabic part formulas pick the right branch.
        from kerykeion.astrological_subject_factory import ARABIC_PARTS_CONFIG, AstrologicalSubjectFactory

        # _compute_is_diurnal calls swe.* (tropical geocentric Sun + azalt), so
        # it must run inside an ephemeris session — same lock/path contract as
        # the subject factory, which computes sect inside its own session. A
        # plain session is enough: _compute_is_diurnal builds its own flags.
        with ephemeris_session():
            is_diurnal = AstrologicalSubjectFactory._compute_is_diurnal(
                jd, new_lat, new_lng, getattr(subject, "altitude", None) or 0.0
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
            relocated_data[part_field] = part_point

        # Reassign planets to new houses
        for point_name in subject.active_points:
            if point_name in _AXIAL_POINTS_SET:
                continue
            field_name = point_name.lower()
            planet_data = relocated_data.get(field_name)
            if planet_data is not None and isinstance(planet_data, dict) and "abs_pos" in planet_data:
                new_house = get_planet_house(planet_data["abs_pos"], houses_degree_ut)
                planet_data["house"] = new_house

        # Fixed stars keep their zodiacal positions but live outside
        # active_points: reassign their houses against the relocated cusps too.
        for star_data in relocated_data.get("fixed_stars") or []:
            if isinstance(star_data, dict) and star_data.get("abs_pos") is not None:
                star_data["house"] = get_planet_house(star_data["abs_pos"], houses_degree_ut)

        return AstrologicalSubjectModel(**relocated_data)
