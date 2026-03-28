# -*- coding: utf-8 -*-
"""
Primary Directions Factory (v6.0)

Implements Placidus semi-arc primary directions — the most widely used
method in classical/traditional astrology for predicting life events.

Algorithm:
    1. Convert each planet's ecliptic position to equatorial (RA, Dec)
    2. Compute the semi-arc (diurnal or nocturnal) for each planet
    3. Compute the meridian distance (RA - RAMC or RAMC + 180 - RA)
    4. Compute the pole of the significator (house cusp latitude)
    5. Compute oblique ascension of promissor under the significator's pole
    6. The arc of direction = OA(promissor under sig's pole) - OA(significator)
    7. Convert arc to years using the rate key (Ptolemy: 1 degree = 1 year)

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import math
import logging
import swisseph as swe
from pathlib import Path
from typing import List, Optional, Literal
from dataclasses import dataclass
from pydantic import BaseModel, Field

from kerykeion.schemas.kr_models import AstrologicalSubjectModel


class SpeculumEntry(BaseModel):
    """Speculum (coordinate table) entry for a single celestial point."""
    name: str
    ecliptic_longitude: float = Field(description="Ecliptic longitude (0-360)")
    right_ascension: float = Field(description="Right Ascension in degrees (0-360)")
    declination: float = Field(description="Declination in degrees (-90 to +90)")
    meridian_distance: float = Field(description="MD = angular distance from MC in RA degrees")
    semi_arc: float = Field(description="Semi-arc (diurnal or nocturnal) in degrees")
    is_above_horizon: bool = Field(description="True if planet is above the horizon")
    pole: float = Field(description="Pole of the house position (Placidus)")
    oblique_ascension: float = Field(description="Oblique ascension under own pole")


class PrimaryDirectionModel(BaseModel):
    """A single primary direction result."""
    promissor: str = Field(description="The directed planet (moving point)")
    significator: str = Field(description="The receiving point (fixed target)")
    aspect: str = Field(description="Aspect type (conjunction, opposition, trine, square, sextile)")
    arc: float = Field(description="Arc of direction in degrees of RA")
    direction_years: float = Field(description="Equivalent years using the selected rate key")
    rate_key: str = Field(description="Rate key used (ptolemy or naibod)")


class PrimaryDirectionsFactory:
    """
    Factory for computing primary directions using the Placidus semi-arc method.

    Example:
        >>> subject = AstrologicalSubjectFactory.from_birth_data(
        ...     "John", 1940, 10, 9, 18, 30, "Liverpool", "GB"
        ... )
        >>> directions = PrimaryDirectionsFactory.compute(subject, max_years=80)
        >>> for d in directions:
        ...     print(f"Year {d.direction_years:.1f}: {d.promissor} {d.aspect} {d.significator}")
    """

    # Planets used as promissors and significators
    DIRECTION_POINTS = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
                        "Ascendant", "Medium_Coeli"]

    ASPECT_ANGLES = {
        "conjunction": 0,
        "sextile": 60,
        "square": 90,
        "trine": 120,
        "opposition": 180,
    }

    @staticmethod
    def compute(
        subject: AstrologicalSubjectModel,
        *,
        max_years: float = 100,
        rate_key: Literal["ptolemy", "naibod"] = "ptolemy",
        aspects: Optional[List[str]] = None,
    ) -> List[PrimaryDirectionModel]:
        """
        Compute primary directions for a natal chart.

        Args:
            subject: The natal chart subject.
            max_years: Maximum number of years to compute directions for.
            rate_key: Conversion rate — "ptolemy" (1 deg = 1 year) or
                "naibod" (0.98564 deg = 1 year, the mean daily motion of the Sun).
            aspects: List of aspect names to compute. Defaults to all major aspects.

        Returns:
            List of PrimaryDirectionModel sorted by direction_years.
        """
        if aspects is None:
            aspects = list(PrimaryDirectionsFactory.ASPECT_ANGLES.keys())

        rate = 1.0 if rate_key == "ptolemy" else 0.98564

        # Setup ephemeris
        ephe_path = str(Path(__file__).parent.parent / "sweph")
        swe.set_ephe_path(ephe_path)

        jd = subject.julian_day
        lat = subject.lat
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED

        # Get obliquity
        try:
            obliquity = swe.calc_ut(jd, swe.ECL_NUT, iflag)[0][0]
        except Exception:
            obliquity = 23.4393

        # Get RAMC (Right Ascension of the Medium Coeli)
        # Local sidereal time = Greenwich sidereal time + observer longitude
        ramc = (swe.sidtime(jd) * 15.0 + subject.lng) % 360

        # Build speculum
        speculum = PrimaryDirectionsFactory._build_speculum(
            subject, jd, iflag, obliquity, ramc, lat
        )

        swe.close()

        if not speculum:
            return []

        # Compute directions
        directions: List[PrimaryDirectionModel] = []
        max_arc = max_years * rate

        speculum_dict = {s.name: s for s in speculum}

        for sig_name, sig in speculum_dict.items():
            for prom_name, prom in speculum_dict.items():
                if sig_name == prom_name:
                    continue

                for aspect_name in aspects:
                    aspect_angle = PrimaryDirectionsFactory.ASPECT_ANGLES.get(aspect_name)
                    if aspect_angle is None:
                        continue

                    # Compute OA of promissor's aspect point under significator's pole
                    prom_ra_aspected = (prom.right_ascension + aspect_angle) % 360

                    # Oblique ascension under significator's pole
                    try:
                        oa_prom = PrimaryDirectionsFactory._oblique_ascension(
                            prom_ra_aspected, prom.declination, sig.pole, obliquity
                        )
                    except Exception:
                        continue

                    # Arc = OA(promissor under sig pole) - OA(significator)
                    # Direct arc (clockwise) and converse arc (counterclockwise)
                    raw_arc = oa_prom - sig.oblique_ascension

                    # Normalize to [0, 360)
                    arc = raw_arc % 360
                    # Primary directions use both direct and converse arcs.
                    # We report the smaller of the two arcs as the "active" direction.
                    if arc > 180:
                        arc = 360 - arc

                    # Convert to years
                    years = arc / rate

                    if 0.1 < years <= max_years:
                        directions.append(PrimaryDirectionModel(
                            promissor=prom_name,
                            significator=sig_name,
                            aspect=aspect_name,
                            arc=round(arc, 4),
                            direction_years=round(years, 2),
                            rate_key=rate_key,
                        ))

        directions.sort(key=lambda d: d.direction_years)
        return directions

    @staticmethod
    def compute_speculum(subject: AstrologicalSubjectModel) -> List[SpeculumEntry]:
        """Compute and return the speculum (coordinate table) for a chart."""
        ephe_path = str(Path(__file__).parent.parent / "sweph")
        swe.set_ephe_path(ephe_path)
        jd = subject.julian_day
        iflag = swe.FLG_SWIEPH | swe.FLG_SPEED
        obliquity = swe.calc_ut(jd, swe.ECL_NUT, iflag)[0][0]
        ramc = (swe.sidtime(jd) * 15.0 + subject.lng) % 360
        speculum = PrimaryDirectionsFactory._build_speculum(
            subject, jd, iflag, obliquity, ramc, subject.lat
        )
        swe.close()
        return speculum

    @staticmethod
    def _build_speculum(
        subject: AstrologicalSubjectModel,
        jd: float,
        iflag: int,
        obliquity: float,
        ramc: float,
        geo_lat: float,
    ) -> List[SpeculumEntry]:
        """Build the speculum for all direction points."""
        from kerykeion.astrological_subject_factory import STANDARD_PLANETS

        entries: List[SpeculumEntry] = []
        lat_rad = math.radians(geo_lat)

        for point_name in PrimaryDirectionsFactory.DIRECTION_POINTS:
            point = getattr(subject, point_name.lower(), None)
            if point is None:
                continue

            ecl_lon = point.abs_pos
            dec = point.declination if point.declination is not None else 0.0

            # Compute RA from equatorial coordinates via Swiss Ephemeris
            # This is more accurate than converting from ecliptic, as it accounts
            # for the planet's ecliptic latitude (important for Moon, asteroids).
            planet_id = STANDARD_PLANETS.get(point_name)
            if planet_id is not None:
                try:
                    eq_coords = swe.calc_ut(jd, planet_id, iflag | swe.FLG_EQUATORIAL)[0]
                    ra = eq_coords[0]  # RA in degrees
                    dec = eq_coords[1]  # Dec in degrees (more precise)
                except Exception:
                    # Fallback: compute from ecliptic (zero ecliptic latitude approximation)
                    eps_rad = math.radians(obliquity)
                    ecl_rad = math.radians(ecl_lon)
                    ra = math.degrees(math.atan2(
                        math.sin(ecl_rad) * math.cos(eps_rad),
                        math.cos(ecl_rad)
                    )) % 360
            else:
                # For non-standard points (ASC, MC), compute from ecliptic longitude
                eps_rad = math.radians(obliquity)
                ecl_rad = math.radians(ecl_lon)
                ra = math.degrees(math.atan2(
                    math.sin(ecl_rad) * math.cos(eps_rad),
                    math.cos(ecl_rad)
                )) % 360

            # Meridian distance: angular distance from MC in RA
            md = ra - ramc
            if md > 180:
                md -= 360
            elif md < -180:
                md += 360

            # Determine if above horizon
            is_above = -90 < md < 90  # Simplified: within 90 deg of MC

            # Semi-arc (Placidus)
            dec_rad = math.radians(dec)
            try:
                # Diurnal semi-arc = acos(-tan(dec) * tan(lat))
                cos_sa = -math.tan(dec_rad) * math.tan(lat_rad)
                cos_sa = max(-1.0, min(1.0, cos_sa))  # Clamp for polar
                dsa = math.degrees(math.acos(cos_sa))
            except (ValueError, ZeroDivisionError):
                dsa = 90.0  # Fallback for circumpolar/never-rise

            nsa = 180 - dsa  # Nocturnal semi-arc
            semi_arc = dsa if is_above else nsa

            # Pole (Placidus house pole)
            if abs(md) < 0.001:
                pole = geo_lat  # On MC/IC
            else:
                try:
                    sa = dsa if is_above else nsa
                    pole_sin = math.sin(lat_rad) * math.sin(math.radians(abs(md))) / math.sin(math.radians(sa))
                    pole_sin = max(-1.0, min(1.0, pole_sin))
                    pole = math.degrees(math.asin(pole_sin))
                except (ValueError, ZeroDivisionError):
                    pole = 0.0

            # Oblique ascension under own pole
            oa = PrimaryDirectionsFactory._oblique_ascension(ra, dec, pole, obliquity)

            entries.append(SpeculumEntry(
                name=point_name,
                ecliptic_longitude=round(ecl_lon, 4),
                right_ascension=round(ra, 4),
                declination=round(dec, 4),
                meridian_distance=round(md, 4),
                semi_arc=round(semi_arc, 4),
                is_above_horizon=is_above,
                pole=round(pole, 4),
                oblique_ascension=round(oa, 4),
            ))

        return entries

    @staticmethod
    def _oblique_ascension(ra: float, dec: float, pole: float, obliquity: float) -> float:
        """Compute oblique ascension of a point under a given pole.

        OA = RA - ascensional_difference
        ascensional_difference = asin(tan(dec) * tan(pole))
        """
        dec_rad = math.radians(dec)
        pole_rad = math.radians(pole)

        try:
            ad_sin = math.tan(dec_rad) * math.tan(pole_rad)
            ad_sin = max(-1.0, min(1.0, ad_sin))
            ad = math.degrees(math.asin(ad_sin))
        except (ValueError, ZeroDivisionError):
            ad = 0.0

        return (ra - ad) % 360
