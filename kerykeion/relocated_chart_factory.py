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
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional

from kerykeion.ephemeris_backend import swe, ephemeris_session

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
        houses_list = [
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

        axis_degrees = {
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
            relocated_data["iso_formatted_local_datetime"] = utc_dt.astimezone(pytz.timezone(new_tz_str)).isoformat()

        # Sect (day/night) depends on the observer's horizon: recompute it for
        # the new location so the Arabic part formulas pick the right branch.
        from kerykeion.astrological_subject_factory import ARABIC_PARTS_CONFIG, AstrologicalSubjectFactory

        is_diurnal = AstrologicalSubjectFactory._compute_is_diurnal(jd, new_lat, new_lng, 0.0)
        relocated_data["is_diurnal"] = is_diurnal

        # Recompute the Ascendant-derived Arabic parts with the relocated ASC
        # and the recomputed sect (planet positions are unchanged).
        for part_name, part_config in ARABIC_PARTS_CONFIG.items():
            part_field = part_name.lower()
            if relocated_data.get(part_field) is None:
                continue

            positions = []
            for required_point in part_config["required"]:
                if required_point == "Ascendant":
                    positions.append(asc_deg)
                    continue
                required_data = relocated_data.get(required_point.lower())
                if required_data is None:
                    positions = None
                    break
                positions.append(required_data["abs_pos"])
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
            point = relocated_data.get(field_name)
            if point is not None and isinstance(point, dict) and "abs_pos" in point:
                new_house = get_planet_house(point["abs_pos"], houses_degree_ut)
                point["house"] = new_house

        return AstrologicalSubjectModel(**relocated_data)
