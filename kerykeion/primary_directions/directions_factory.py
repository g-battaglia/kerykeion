# -*- coding: utf-8 -*-
"""
Primary Directions Factory (v6.0)

Implements Placidus semi-arc primary directions ("under the pole" variant) —
the most widely used method in classical/traditional astrology for predicting
life events. Formulas follow the standard recipe as documented in
M. Gansten, "Primary Directions: Astrology's Old Master Technique".

Algorithm:
    1. Convert each point's position to true equatorial coordinates (RA, Dec).
    2. Compute the ascensional difference at the birth latitude:
           AD_phi = asin(tan(dec) * tan(geo_lat))
       and from it the diurnal/nocturnal semi-arcs:
           DSA = 90 + AD_phi,  NSA = 90 - AD_phi
    3. Compute the meridian distance (MD) from the nearer meridian: from the
       MC when the point is above the horizon (|MD_MC| <= DSA), from the IC
       otherwise.
    4. Compute the pole of the significator ("under the pole" recipe):
           AD_P = (MD / SA) * AD_phi      # proportional ascensional difference
           pole = atan(sin(AD_P) / tan(dec))
       A point on the meridian (MD ~ 0) has pole 0 — directions to the MC/IC
       are pure right-ascension arcs.
    5. Build each promissor's aspect points on the ECLIPTIC: longitude
       lambda_promissor +/- aspect with latitude 0, converted to RA/Dec
       through the obliquity.
    6. Take the oblique ascension (eastern significators) or oblique
       descension (western significators) of the aspect point under the
       significator's pole:
           OA = RA - AD,  OD = RA + AD,  AD = asin(tan(dec) * tan(pole))
    7. Arc of direction:
           direct   = (OA_promissor - OA_significator) mod 360
           converse = 360 - direct
       Both are reported as separate entries (``is_converse`` marker).

       .. warning::
           The converse arc here is the arithmetic complement of the direct
           arc, NOT the classical converse method (which swaps the roles of
           significator and promissor and recomputes the oblique ascension
           under the *promissor's* pole). Converse (``is_converse=True``)
           timings are therefore an approximation and should not be relied on
           for precise converse-direction work; a proper implementation is
           planned for a future release. Direct directions are unaffected.
    8. Convert the arc to years using the rate key (Ptolemy: 1 deg = 1 year,
       Naibod: 0.98564 deg = 1 year).

This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""

import logging
import math
from kerykeion.ephemeris_backend import ephe, ephemeris_session
from typing import List, Optional, Literal, Tuple, cast
from pydantic import BaseModel, Field

from kerykeion.schemas.kr_literals import AstrologicalPoint
from kerykeion.schemas.kr_models import AstrologicalSubjectModel

logger = logging.getLogger(__name__)

# MD (in degrees of RA) below which a point is treated as being on the meridian.
_ON_MERIDIAN_TOLERANCE = 1e-6


class SpeculumEntryModel(BaseModel):
    """Speculum (coordinate table) entry for a single celestial point."""
    name: str
    ecliptic_longitude: float = Field(description="Ecliptic longitude (0-360), in the subject's zodiac")
    right_ascension: float = Field(description="Right Ascension in degrees (0-360)")
    declination: float = Field(description="Declination in degrees (-90 to +90)")
    meridian_distance: float = Field(description="MD = signed angular distance from MC in RA degrees (-180 to 180)")
    semi_arc: float = Field(description="Semi-arc (diurnal if above horizon, nocturnal if below) in degrees")
    is_above_horizon: bool = Field(description="True if the point is above the horizon (|MD| <= DSA)")
    pole: float = Field(description="Placidian pole of the point ('under the pole' recipe)")
    oblique_ascension: float = Field(
        description="Oblique ascension (eastern hemisphere) or oblique descension (western) under own pole"
    )


class PrimaryDirectionModel(BaseModel):
    """A single primary direction result."""
    promissor: str = Field(description="The directed planet (moving point)")
    significator: str = Field(description="The receiving point (fixed target)")
    aspect: str = Field(description="Aspect type (conjunction, opposition, trine, square, sextile)")
    arc: float = Field(description="Arc of direction in degrees of RA")
    direction_years: float = Field(description="Equivalent years using the selected rate key")
    rate_key: str = Field(description="Rate key used (ptolemy or naibod)")
    is_converse: bool = Field(
        default=False,
        description="False for direct directions (with primary motion), True for converse (against it)",
    )


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
            List of PrimaryDirectionModel sorted by direction_years. Both
            direct and converse directions are included, distinguished by the
            ``is_converse`` field. For sextile, square and trine, both the
            dexter and sinister aspect points (lambda - aspect and
            lambda + aspect) are directed.
        """
        if aspects is None:
            aspects = list(PrimaryDirectionsFactory.ASPECT_ANGLES.keys())

        rate = 1.0 if rate_key == "ptolemy" else 0.98564

        jd = subject.julian_day
        lat = subject.lat

        with ephemeris_session() as iflag:
            # True obliquity of the ecliptic
            obliquity = ephe.calc_ut(jd, ephe.ECL_NUT, iflag)[0][0]

            # RAMC (Right Ascension of the Medium Coeli):
            # local sidereal time = Greenwich sidereal time + observer longitude
            ramc = (ephe.sidtime(jd) * 15.0 + subject.lng) % 360

            # Build speculum
            speculum = PrimaryDirectionsFactory._build_speculum(
                subject, jd, iflag, obliquity, ramc, lat
            )

        if not speculum:
            return []

        # Aspect points live on the ecliptic. For sidereal charts abs_pos is a
        # sidereal longitude; the equatorial conversion below needs the
        # tropical longitude, so add the ayanamsa back (None for tropical).
        ayanamsa = getattr(subject, "ayanamsa_value", None) or 0.0

        # Compute directions
        directions: List[PrimaryDirectionModel] = []

        speculum_dict = {s.name: s for s in speculum}

        for sig_name, sig in speculum_dict.items():
            # Eastern hemisphere (rising side): MD >= 0; significators in the
            # east are directed by oblique ascension, in the west by oblique
            # descension. On the meridian pole = 0 and AD = 0, so OA == OD.
            sig_is_eastern = sig.meridian_distance >= 0

            for prom_name, prom in speculum_dict.items():
                if sig_name == prom_name:
                    continue

                prom_lambda_tropical = (prom.ecliptic_longitude + ayanamsa) % 360

                for aspect_name in aspects:
                    aspect_angle = PrimaryDirectionsFactory.ASPECT_ANGLES.get(aspect_name)
                    if aspect_angle is None:
                        continue

                    # Aspect points are ecliptic: lambda +/- aspect, latitude 0.
                    # 0 and 180 are their own mirror; the others have a dexter
                    # and a sinister point.
                    offsets: Tuple[int, ...]
                    if aspect_angle in (0, 180):
                        offsets = (aspect_angle,)
                    else:
                        offsets = (aspect_angle, -aspect_angle)

                    for offset in offsets:
                        aspect_lambda = (prom_lambda_tropical + offset) % 360

                        try:
                            ra_asp, dec_asp = PrimaryDirectionsFactory._ecliptic_to_equatorial(
                                aspect_lambda, obliquity
                            )
                            # OA/OD of the aspect point under the significator's pole
                            if sig_is_eastern:
                                oa_prom = PrimaryDirectionsFactory._oblique_ascension(
                                    ra_asp, dec_asp, sig.pole
                                )
                            else:
                                oa_prom = PrimaryDirectionsFactory._oblique_descension(
                                    ra_asp, dec_asp, sig.pole
                                )
                        except (ValueError, ArithmeticError) as exc:
                            # A degenerate geometry (math-domain / division error)
                            # means this aspect point has no valid arc here — skip
                            # it, but log so the omission is observable rather than
                            # silent. Anything else is a bug and must propagate.
                            logger.debug(
                                "Skipping aspect point lambda=%.4f for significator %s: %s",
                                aspect_lambda,
                                getattr(sig, "name", sig),
                                exc,
                            )
                            continue

                        # Direct arc: the promissor is carried by primary motion
                        # (increasing RAMC) onto the significator's place.
                        arc_direct = (oa_prom - sig.oblique_ascension) % 360
                        # Converse arc: APPROXIMATED as the arithmetic complement
                        # of the direct arc. This is NOT the classical converse
                        # method (swap significator/promissor, recompute the
                        # oblique ascension under the promissor's pole); see the
                        # module docstring warning. Converse timings are
                        # therefore approximate.
                        arc_converse = (360.0 - arc_direct) % 360

                        for arc, is_converse in ((arc_direct, False), (arc_converse, True)):
                            years = arc / rate
                            if 0.1 < years <= max_years:
                                directions.append(PrimaryDirectionModel(
                                    promissor=prom_name,
                                    significator=sig_name,
                                    aspect=aspect_name,
                                    arc=round(arc, 4),
                                    direction_years=round(years, 2),
                                    rate_key=rate_key,
                                    is_converse=is_converse,
                                ))

        directions.sort(key=lambda d: d.direction_years)
        return directions

    @staticmethod
    def compute_speculum(subject: AstrologicalSubjectModel) -> List[SpeculumEntryModel]:
        """Compute and return the speculum (coordinate table) for a chart."""
        jd = subject.julian_day
        with ephemeris_session() as iflag:
            obliquity = ephe.calc_ut(jd, ephe.ECL_NUT, iflag)[0][0]
            ramc = (ephe.sidtime(jd) * 15.0 + subject.lng) % 360
            speculum = PrimaryDirectionsFactory._build_speculum(
                subject, jd, iflag, obliquity, ramc, subject.lat
            )
        return speculum

    @staticmethod
    def _build_speculum(
        subject: AstrologicalSubjectModel,
        jd: float,
        iflag: int,
        obliquity: float,
        ramc: float,
        geo_lat: float,
    ) -> List[SpeculumEntryModel]:
        """Build the speculum (RA, declination, semi-arc, pole, OA/OD) for all
        direction points.

        Must be called inside an :func:`ephemeris_session` (``iflag`` is the
        session flag).
        """
        from kerykeion.astrological_subject_factory import STANDARD_PLANETS

        entries: List[SpeculumEntryModel] = []
        lat_rad = math.radians(geo_lat)

        # For sidereal charts abs_pos is sidereal; the ecliptic->equatorial
        # fallback below requires tropical longitudes.
        ayanamsa = getattr(subject, "ayanamsa_value", None) or 0.0

        for point_name in PrimaryDirectionsFactory.DIRECTION_POINTS:
            point = getattr(subject, point_name.lower(), None)
            if point is None:
                continue

            ecl_lon = point.abs_pos
            ecl_lon_tropical = (ecl_lon + ayanamsa) % 360
            dec: Optional[float] = point.declination

            # Compute RA from equatorial coordinates via Swiss Ephemeris.
            # This is more accurate than converting from ecliptic, as it accounts
            # for the planet's ecliptic latitude (important for Moon, asteroids).
            ra: Optional[float] = None
            # DIRECTION_POINTS entries are all valid AstrologicalPoint names.
            planet_id = STANDARD_PLANETS.get(cast(AstrologicalPoint, point_name))
            if planet_id is not None:
                try:
                    eq_coords = ephe.calc_ut(jd, planet_id, iflag | ephe.FLG_EQUATORIAL)[0]
                    ra = eq_coords[0]  # RA in degrees
                    dec = eq_coords[1]  # Dec in degrees (more precise)
                except Exception:
                    ra = None

            if ra is None or dec is None:
                # ASC/MC (exact: they lie on the ecliptic, latitude 0) and
                # planetary fallback (zero ecliptic latitude approximation).
                ra_from_ecliptic, dec_from_ecliptic = PrimaryDirectionsFactory._ecliptic_to_equatorial(
                    ecl_lon_tropical, obliquity
                )
                if ra is None:
                    ra = ra_from_ecliptic
                if dec is None:
                    dec = dec_from_ecliptic

            # Meridian distance: signed angular distance from MC in RA, [-180, 180]
            md = ra - ramc
            if md > 180:
                md -= 360
            elif md < -180:
                md += 360

            # Ascensional difference at the birth latitude and semi-arcs:
            #   AD_phi = asin(tan(dec) * tan(lat)); DSA = 90 + AD_phi; NSA = 90 - AD_phi
            dec_rad = math.radians(dec)
            sin_ad_phi = math.tan(dec_rad) * math.tan(lat_rad)
            sin_ad_phi = max(-1.0, min(1.0, sin_ad_phi))  # Clamp for circumpolar
            ad_phi = math.degrees(math.asin(sin_ad_phi))
            dsa = 90.0 + ad_phi  # Diurnal semi-arc
            nsa = 90.0 - ad_phi  # Nocturnal semi-arc

            # Above the horizon iff the meridian distance from the MC does not
            # exceed the diurnal semi-arc. (A plain |MD| < 90 test ignores
            # declination and misclassifies points near the horizon.)
            is_above = abs(md) <= dsa

            if is_above:
                semi_arc = dsa
                md_for_pole = abs(md)  # MD from the MC
            else:
                semi_arc = nsa
                md_for_pole = 180.0 - abs(md)  # MD from the IC

            # Placidian pole ("under the pole" recipe). Points on the meridian
            # have pole 0: directions to the MC/IC are pure RA arcs.
            try:
                pole = PrimaryDirectionsFactory._placidian_pole(
                    md_for_pole, semi_arc, dec, geo_lat
                )
            except (ValueError, ZeroDivisionError):
                pole = 0.0

            # Oblique ascension (eastern hemisphere) or descension (western)
            # under the point's own pole.
            if md >= 0:
                oa = PrimaryDirectionsFactory._oblique_ascension(ra, dec, pole)
            else:
                oa = PrimaryDirectionsFactory._oblique_descension(ra, dec, pole)

            entries.append(SpeculumEntryModel(
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
    def _placidian_pole(md: float, semi_arc: float, dec: float, geo_lat: float) -> float:
        """Compute the Placidian pole of a point ("under the pole" recipe).

        Standard formulas (Gansten):
            AD_phi = asin(tan(dec) * tan(geo_lat))   # AD at the birth latitude
            AD_P   = (MD / SA) * AD_phi              # proportional AD under the pole
            pole   = atan(sin(AD_P) / tan(dec))      # pole of the point

        Args:
            md: Absolute meridian distance from the nearer meridian (MC if the
                point is above the horizon, IC if below), in degrees of RA.
            semi_arc: The matching semi-arc (diurnal/nocturnal) in degrees.
            dec: Declination of the point in degrees.
            geo_lat: Geographic latitude of the birthplace in degrees.

        Returns:
            The pole in degrees. A point on the meridian (MD ~ 0) has pole 0
            (directions to the MC/IC are pure RA arcs); a point on the horizon
            (MD = SA) has pole equal to the geographic latitude.
        """
        if abs(md) < _ON_MERIDIAN_TOLERANCE:
            return 0.0
        if semi_arc <= _ON_MERIDIAN_TOLERANCE:
            # Degenerate circumpolar case (semi-arc collapsed to zero).
            return 0.0

        ratio = min(abs(md) / semi_arc, 1.0)

        dec_rad = math.radians(dec)
        lat_rad = math.radians(geo_lat)

        sin_ad_phi = math.tan(dec_rad) * math.tan(lat_rad)
        sin_ad_phi = max(-1.0, min(1.0, sin_ad_phi))  # Clamp for circumpolar
        ad_phi = math.asin(sin_ad_phi)  # radians
        ad_p = ratio * ad_phi  # proportional AD, radians

        tan_dec = math.tan(dec_rad)
        if abs(tan_dec) < 1e-12:
            # Continuous limit for dec -> 0:
            # pole = atan(sin(ratio * tan(dec) * tan(lat)) / tan(dec)) -> atan(ratio * tan(lat))
            return math.degrees(math.atan(ratio * math.tan(lat_rad)))

        return math.degrees(math.atan(math.sin(ad_p) / tan_dec))

    @staticmethod
    def _ecliptic_to_equatorial(ecl_lon: float, obliquity: float) -> Tuple[float, float]:
        """Convert an ecliptic point with zero latitude to equatorial coordinates.

            dec = asin(sin(eps) * sin(lambda))
            RA  = atan2(sin(lambda) * cos(eps), cos(lambda))

        Args:
            ecl_lon: TROPICAL ecliptic longitude in degrees.
            obliquity: Obliquity of the ecliptic in degrees.

        Returns:
            (right_ascension, declination) in degrees, RA normalized to [0, 360).
        """
        lon_rad = math.radians(ecl_lon % 360)
        eps_rad = math.radians(obliquity)
        dec = math.degrees(math.asin(math.sin(eps_rad) * math.sin(lon_rad)))
        ra = math.degrees(math.atan2(
            math.sin(lon_rad) * math.cos(eps_rad),
            math.cos(lon_rad)
        )) % 360
        return ra, dec

    @staticmethod
    def _ascensional_difference(dec: float, pole: float) -> float:
        """Ascensional difference of a point under a given pole, in degrees.

        AD = asin(tan(dec) * tan(pole)), clamped for circumpolar combinations.
        """
        try:
            ad_sin = math.tan(math.radians(dec)) * math.tan(math.radians(pole))
            ad_sin = max(-1.0, min(1.0, ad_sin))
            return math.degrees(math.asin(ad_sin))
        except (ValueError, ZeroDivisionError):
            return 0.0

    @staticmethod
    def _oblique_ascension(ra: float, dec: float, pole: float) -> float:
        """Oblique ascension of a point under a given pole: OA = RA - AD."""
        return (ra - PrimaryDirectionsFactory._ascensional_difference(dec, pole)) % 360

    @staticmethod
    def _oblique_descension(ra: float, dec: float, pole: float) -> float:
        """Oblique descension of a point under a given pole: OD = RA + AD."""
        return (ra + PrimaryDirectionsFactory._ascensional_difference(dec, pole)) % 360

