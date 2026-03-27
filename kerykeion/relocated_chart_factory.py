# -*- coding: utf-8 -*-
"""Relocated chart factory.

A relocated chart keeps ALL planetary positions identical to the natal chart
but recalculates houses and angles (ASC, MC, DSC, IC) for a different
geographic location. This is equivalent to asking: "If I had been born at
the same Universal Time but in a different city, which houses would my
planets fall in?"

Swiss Ephemeris function: ``swe.houses_armc(armc, lat, eps, hsys)``
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import swisseph as swe

from kerykeion.schemas.kr_models import AstrologicalSubjectModel, KerykeionPointModel
from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.utilities import get_kerykeion_point_from_degree, get_planet_house

_EPHE_PATH = str(Path(__file__).parent / "sweph")


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

        Planetary positions remain unchanged. Only houses and angles
        are recalculated for the new latitude/longitude.

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
        swe.set_ephe_path(_EPHE_PATH)

        jd = subject.julian_day
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        hsys = subject.houses_system_identifier.encode("ascii")

        # Get obliquity of ecliptic
        eps = swe.calc_ut(jd, swe.ECL_NUT, iflag)[0][0]

        # Get ARMC (sidereal time at Greenwich in degrees) from original JD
        armc_hours = swe.sidtime(jd)  # Greenwich sidereal time in hours
        # Adjust for new longitude: local sidereal time = GST + lng/15
        local_st_hours = armc_hours + new_lng / 15.0
        armc_degrees = (local_st_hours * 15.0) % 360.0

        # Calculate new houses for the new location
        cusps, ascmc = swe.houses_armc(armc_degrees, new_lat, eps, hsys)

        # Build house degree list for planet house assignment
        houses_degree_ut = list(cusps)

        # Create house KerykeionPointModels
        house_data = {}
        house_names = [
            "first_house", "second_house", "third_house", "fourth_house",
            "fifth_house", "sixth_house", "seventh_house", "eighth_house",
            "ninth_house", "tenth_house", "eleventh_house", "twelfth_house",
        ]
        houses_list = [
            "First_House", "Second_House", "Third_House", "Fourth_House",
            "Fifth_House", "Sixth_House", "Seventh_House", "Eighth_House",
            "Ninth_House", "Tenth_House", "Eleventh_House", "Twelfth_House",
        ]
        for i, hname in enumerate(house_names):
            house_data[hname] = get_kerykeion_point_from_degree(
                cusps[i], houses_list[i], "House"
            )

        # Create angular points
        asc_deg = ascmc[0] % 360
        mc_deg = ascmc[1] % 360
        desc_deg = (asc_deg + 180) % 360
        ic_deg = (mc_deg + 180) % 360

        house_data["ascendant"] = get_kerykeion_point_from_degree(asc_deg, "Ascendant", "AstrologicalPoint")
        house_data["medium_coeli"] = get_kerykeion_point_from_degree(mc_deg, "Medium_Coeli", "AstrologicalPoint")
        house_data["descendant"] = get_kerykeion_point_from_degree(desc_deg, "Descendant", "AstrologicalPoint")
        house_data["imum_coeli"] = get_kerykeion_point_from_degree(ic_deg, "Imum_Coeli", "AstrologicalPoint")

        # Copy original subject data and override houses + angles
        relocated_data = subject.model_dump()
        relocated_data.update(house_data)
        relocated_data["city"] = new_city
        relocated_data["nation"] = new_nation or subject.nation
        relocated_data["lat"] = new_lat
        relocated_data["lng"] = new_lng
        relocated_data["tz_str"] = new_tz_str or subject.tz_str
        relocated_data["houses_names_list"] = houses_list

        # Reassign planets to new houses
        axial_points = {"Ascendant", "Medium_Coeli", "Descendant", "Imum_Coeli"}
        for point_name in subject.active_points:
            if point_name in axial_points:
                continue
            field_name = point_name.lower()
            point = relocated_data.get(field_name)
            if point is not None and isinstance(point, dict) and "abs_pos" in point:
                new_house = get_planet_house(point["abs_pos"], houses_degree_ut)
                point["house"] = new_house

        swe.close()
        return AstrologicalSubjectModel(**relocated_data)
