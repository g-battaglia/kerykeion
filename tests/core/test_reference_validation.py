# -*- coding: utf-8 -*-
"""Reference-anchored validation of the predictive engine and its defaults.

Each subject in ``_REFERENCE_SUBJECTS`` carries a secondary-progression
ephemeris date that was independently verified against a mainstream online
progressed-chart calculator. Every subject is then exercised by several
tests covering the day-for-a-year engine and the configurable orb defaults:

* ``test_reference_sp_ephemeris_date``       — engine vs the external reference
* ``test_reference_day_for_year_formula``    — ephemeris JD matches the formula
* ``test_reference_solar_arc_equals_sun_delta`` — solar arc definition
* ``test_reference_compute_full_matches_compute`` — API consistency
* ``test_reference_orb_config_monotonic``    — configurable predictive orb
* ``test_reference_predictive_aspects_ptolemaic`` — predictive aspect set

The pool spans 26 cities across all inhabited continents, births 1925-2010
and progression targets 2024-2079. 130 subjects were cross-checked; one
(early-1926 China) was excluded for an unrelated historical-timezone
mismatch in the natal layer, not a day-for-a-year discrepancy. The
ephemeris dates are permanent regression baselines.
"""

from datetime import datetime, timezone
from functools import lru_cache

import pytest

from kerykeion import (
    AstrologicalSubjectFactory,
    SecondaryProgressionFactory,
    SolarArcFactory,
)
from kerykeion.ephemeris_backend import ephe
from kerykeion.secondary_progressions.secondary_progression_factory import (
    DAYS_PER_TROPICAL_YEAR,
)

# (name, year, month, day, hour, minute, lat, lng, tz, target_date,
#  (ref_year, ref_month, ref_day, ref_hour, ref_minute))
# ref_* = SP ephemeris date verified against an external progressed-chart
# calculator (UT, displayed to the minute).
_REFERENCE_SUBJECTS = [
    ("Athens1967i006", 1967, 7, 11, 6, 42, 37.98, 23.73, "Europe/Athens", "2042-06-15", (1967, 9, 24, 3, 2)),
    ("Athens1977i032", 1977, 5, 17, 8, 4, 37.98, 23.73, "Europe/Athens", "2064-06-15", (1977, 8, 12, 7, 1)),
    ("Athens1987i058", 1987, 3, 23, 10, 26, 37.98, 23.73, "Europe/Athens", "2030-06-15", (1987, 5, 5, 13, 58)),
    ("Athens1997i084", 1997, 1, 1, 12, 48, 37.98, 23.73, "Europe/Athens", "2052-06-15", (1997, 2, 25, 21, 39)),
    ("Athens2007i110", 2007, 11, 7, 14, 10, 37.98, 23.73, "Europe/Athens", "2074-06-15", (2008, 1, 13, 2, 39)),
    ("Auckland1931i050", 1931, 11, 19, 2, 10, -36.85, 174.76, "Pacific/Auckland", "2062-06-15", (1932, 3, 28, 3, 57)),
    ("Auckland1941i076", 1941, 9, 25, 4, 32, -36.85, 174.76, "Pacific/Auckland", "2028-06-15", (1941, 12, 20, 9, 54)),
    ("Auckland1951i102", 1951, 7, 3, 6, 54, -36.85, 174.76, "Pacific/Auckland", "2050-06-15", (1951, 10, 9, 17, 47)),
    ("Auckland1961i128", 1961, 5, 9, 8, 16, -36.85, 174.76, "Pacific/Auckland", "2072-06-15", (1961, 8, 27, 22, 46)),
    ("Auckland2007i024", 2007, 1, 13, 0, 48, -36.85, 174.76, "Pacific/Auckland", "2040-06-15", (2007, 2, 14, 21, 57)),
    ("Bangkok1930i099", 1930, 4, 26, 15, 3, 13.76, 100.5, "Asia/Bangkok", "2041-06-15", (1930, 8, 15, 11, 23)),
    ("Bangkok1940i125", 1940, 2, 4, 17, 25, 13.76, 100.5, "Asia/Bangkok", "2063-06-15", (1940, 6, 6, 19, 4)),
    ("Bangkok1986i021", 1986, 10, 8, 9, 57, 13.76, 100.5, "Asia/Bangkok", "2031-06-15", (1986, 11, 21, 19, 23)),
    ("Bangkok1996i047", 1996, 8, 14, 11, 19, 13.76, 100.5, "Asia/Bangkok", "2053-06-15", (1996, 10, 10, 0, 22)),
    ("Bangkok2006i073", 2006, 6, 20, 13, 41, 13.76, 100.5, "Asia/Bangkok", "2075-06-15", (2006, 8, 28, 6, 21)),
    ("Beijing1972i019", 1972, 12, 14, 7, 23, 39.9, 116.4, "Asia/Shanghai", "2025-06-15", (1973, 2, 4, 11, 26)),
    ("Beijing1982i045", 1982, 10, 20, 9, 45, 39.9, 116.4, "Asia/Shanghai", "2047-06-15", (1982, 12, 23, 17, 25)),
    ("Beijing1992i071", 1992, 8, 26, 11, 7, 39.9, 116.4, "Asia/Shanghai", "2069-06-15", (1992, 11, 10, 22, 24)),
    ("Beijing2002i097", 2002, 6, 4, 13, 29, 39.9, 116.4, "Asia/Shanghai", "2035-06-15", (2002, 7, 7, 6, 11)),
    ("Berlin1953i004", 1953, 9, 17, 4, 8, 52.52, 13.41, "Europe/Berlin", "2036-06-15", (1953, 12, 8, 21, 0)),
    ("Berlin1963i030", 1963, 7, 23, 6, 30, 52.52, 13.41, "Europe/Berlin", "2058-06-15", (1963, 10, 26, 3, 3)),
    ("Berlin1973i056", 1973, 5, 1, 8, 52, 52.52, 13.41, "Europe/Berlin", "2024-06-15", (1973, 6, 21, 10, 50)),
    ("Berlin1983i082", 1983, 3, 7, 10, 14, 52.52, 13.41, "Europe/Berlin", "2046-06-15", (1983, 5, 9, 15, 49)),
    ("Berlin1993i108", 1993, 1, 13, 12, 36, 52.52, 13.41, "Europe/Berlin", "2068-06-15", (1993, 3, 29, 21, 40)),
    (
        "BuenosAires1951i016",
        1951,
        9,
        9,
        16,
        32,
        -34.6,
        -58.38,
        "America/Argentina/Buenos_Aires",
        "2072-06-15",
        (1952, 1, 8, 13, 56),
    ),
    (
        "BuenosAires1961i042",
        1961,
        7,
        15,
        18,
        54,
        -34.6,
        -58.38,
        "America/Argentina/Buenos_Aires",
        "2038-06-15",
        (1961, 9, 30, 19, 53),
    ),
    (
        "BuenosAires1971i068",
        1971,
        5,
        21,
        20,
        16,
        -34.6,
        -58.38,
        "America/Argentina/Buenos_Aires",
        "2060-06-15",
        (1971, 8, 19, 0, 56),
    ),
    (
        "BuenosAires1981i094",
        1981,
        3,
        27,
        22,
        38,
        -34.6,
        -58.38,
        "America/Argentina/Buenos_Aires",
        "2026-06-15",
        (1981, 5, 12, 6, 49),
    ),
    (
        "BuenosAires1991i120",
        1991,
        1,
        5,
        0,
        0,
        -34.6,
        -58.38,
        "America/Argentina/Buenos_Aires",
        "2048-06-15",
        (1991, 3, 3, 12, 39),
    ),
    ("Cairo1928i025", 1928, 6, 24, 13, 5, 30.04, 31.24, "Africa/Cairo", "2043-06-15", (1928, 10, 17, 10, 28)),
    ("Cairo1938i051", 1938, 4, 2, 15, 27, 30.04, 31.24, "Africa/Cairo", "2065-06-15", (1938, 8, 7, 18, 21)),
    ("Cairo1948i077", 1948, 2, 8, 17, 49, 30.04, 31.24, "Africa/Cairo", "2031-06-15", (1948, 5, 2, 0, 10)),
    ("Cairo1958i103", 1958, 12, 14, 19, 11, 30.04, 31.24, "Africa/Cairo", "2053-06-15", (1959, 3, 19, 5, 14)),
    ("Cairo1968i129", 1968, 10, 20, 21, 33, 30.04, 31.24, "Africa/Cairo", "2075-06-15", (1969, 2, 4, 11, 9)),
    ("Chicago1933i038", 1933, 11, 27, 14, 46, 41.88, -87.63, "America/Chicago", "2026-06-15", (1934, 2, 28, 9, 53)),
    ("Chicago1943i064", 1943, 9, 5, 16, 8, 41.88, -87.63, "America/Chicago", "2048-06-15", (1943, 12, 19, 15, 47)),
    ("Chicago1953i090", 1953, 7, 11, 18, 30, 41.88, -87.63, "America/Chicago", "2070-06-15", (1953, 11, 5, 21, 46)),
    ("Chicago1963i116", 1963, 5, 17, 20, 52, 41.88, -87.63, "America/Chicago", "2036-06-15", (1963, 7, 30, 3, 47)),
    ("Chicago2009i012", 2009, 1, 21, 12, 24, 41.88, -87.63, "America/Chicago", "2060-06-15", (2009, 3, 14, 3, 55)),
    ("Lima1958i017", 1958, 2, 20, 5, 49, -12.05, -77.04, "America/Lima", "2075-06-15", (1958, 6, 17, 18, 23)),
    ("Lima1968i043", 1968, 12, 26, 7, 11, -12.05, -77.04, "America/Lima", "2041-06-15", (1969, 3, 8, 23, 25)),
    ("Lima1978i069", 1978, 10, 4, 9, 33, -12.05, -77.04, "America/Lima", "2063-06-15", (1978, 12, 28, 7, 14)),
    ("Lima1988i095", 1988, 8, 10, 11, 55, -12.05, -77.04, "America/Lima", "2029-06-15", (1988, 9, 20, 13, 11)),
    ("Lima1998i121", 1998, 6, 16, 13, 17, -12.05, -77.04, "America/Lima", "2051-06-15", (1998, 8, 8, 18, 10)),
    ("Lisbon1925i086", 1925, 11, 23, 14, 22, 38.72, -9.14, "Europe/Lisbon", "2058-06-15", (1926, 4, 5, 3, 47)),
    ("Lisbon1935i112", 1935, 9, 1, 16, 44, 38.72, -9.14, "Europe/Lisbon", "2024-06-15", (1935, 11, 29, 10, 39)),
    ("Lisbon1981i008", 1981, 5, 5, 8, 16, 38.72, -9.14, "Europe/Lisbon", "2048-06-15", (1981, 7, 11, 9, 59)),
    ("Lisbon1991i034", 1991, 3, 11, 10, 38, 38.72, -9.14, "Europe/Lisbon", "2070-06-15", (1991, 5, 29, 16, 58)),
    ("Lisbon2001i060", 2001, 1, 17, 12, 0, 38.72, -9.14, "Europe/Lisbon", "2036-06-15", (2001, 2, 21, 21, 47)),
    ("London1939i002", 1939, 11, 23, 2, 34, 51.51, -0.13, "Europe/London", "2030-06-15", (1940, 2, 21, 16, 2)),
    ("London1949i028", 1949, 9, 1, 4, 56, 51.51, -0.13, "Europe/London", "2052-06-15", (1949, 12, 12, 22, 51)),
    ("London1959i054", 1959, 7, 7, 6, 18, 51.51, -0.13, "Europe/London", "2074-06-15", (1959, 10, 30, 3, 54)),
    ("London1969i080", 1969, 5, 13, 8, 40, 51.51, -0.13, "Europe/London", "2040-06-15", (1969, 7, 23, 9, 52)),
    ("London1979i106", 1979, 3, 19, 10, 2, 51.51, -0.13, "Europe/London", "2062-06-15", (1979, 6, 10, 14, 51)),
    (
        "LosAngeles1926i037",
        1926,
        6,
        16,
        1,
        29,
        34.05,
        -118.24,
        "America/Los_Angeles",
        "2079-06-15",
        (1926, 11, 16, 9, 27),
    ),
    (
        "LosAngeles1936i063",
        1936,
        4,
        22,
        3,
        51,
        34.05,
        -118.24,
        "America/Los_Angeles",
        "2045-06-15",
        (1936, 8, 9, 15, 24),
    ),
    (
        "LosAngeles1946i089",
        1946,
        2,
        28,
        5,
        13,
        34.05,
        -118.24,
        "America/Los_Angeles",
        "2067-06-15",
        (1946, 6, 29, 20, 15),
    ),
    (
        "LosAngeles1956i115",
        1956,
        12,
        6,
        7,
        35,
        34.05,
        -118.24,
        "America/Los_Angeles",
        "2033-06-15",
        (1957, 2, 21, 4, 7),
    ),
    (
        "LosAngeles2002i011",
        2002,
        8,
        10,
        23,
        7,
        34.05,
        -118.24,
        "America/Los_Angeles",
        "2057-06-15",
        (2002, 10, 5, 2, 23),
    ),
    ("Madrid1960i005", 1960, 2, 28, 17, 25, 40.42, -3.7, "Europe/Madrid", "2039-06-15", (1960, 5, 17, 23, 27)),
    ("Madrid1970i031", 1970, 12, 6, 19, 47, 40.42, -3.7, "Europe/Madrid", "2061-06-15", (1971, 3, 7, 7, 21)),
    ("Madrid1980i057", 1980, 10, 12, 21, 9, 40.42, -3.7, "Europe/Madrid", "2027-06-15", (1980, 11, 28, 12, 15)),
    ("Madrid1990i083", 1990, 8, 18, 23, 31, 40.42, -3.7, "Europe/Madrid", "2049-06-15", (1990, 10, 16, 17, 17)),
    ("Madrid2000i109", 2000, 6, 24, 1, 53, 40.42, -3.7, "Europe/Madrid", "2071-06-15", (2000, 9, 2, 23, 16)),
    (
        "MexicoCity1937i014",
        1937,
        11,
        15,
        14,
        58,
        19.43,
        -99.13,
        "America/Mexico_City",
        "2066-06-15",
        (1938, 3, 24, 10, 54),
    ),
    (
        "MexicoCity1947i040",
        1947,
        9,
        21,
        16,
        20,
        19.43,
        -99.13,
        "America/Mexico_City",
        "2032-06-15",
        (1947, 12, 15, 15, 55),
    ),
    (
        "MexicoCity1957i066",
        1957,
        7,
        27,
        18,
        42,
        19.43,
        -99.13,
        "America/Mexico_City",
        "2054-06-15",
        (1957, 11, 1, 21, 54),
    ),
    ("MexicoCity1967i092", 1967, 5, 5, 20, 4, 19.43, -99.13, "America/Mexico_City", "2076-06-15", (1967, 8, 23, 4, 47)),
    (
        "MexicoCity1977i118",
        1977,
        3,
        11,
        22,
        26,
        19.43,
        -99.13,
        "America/Mexico_City",
        "2042-06-15",
        (1977, 5, 16, 10, 40),
    ),
    ("Milan1932i001", 1932, 6, 12, 13, 17, 45.46, 9.19, "Europe/Rome", "2027-06-15", (1932, 9, 15, 12, 26)),
    ("Milan1942i027", 1942, 4, 18, 15, 39, 45.46, 9.19, "Europe/Rome", "2049-06-15", (1942, 8, 3, 17, 29)),
    ("Milan1952i053", 1952, 2, 24, 17, 1, 45.46, 9.19, "Europe/Rome", "2071-06-15", (1952, 6, 22, 23, 20)),
    ("Milan1962i079", 1962, 12, 2, 19, 23, 45.46, 9.19, "Europe/Rome", "2037-06-15", (1963, 2, 15, 7, 13)),
    ("Milan1972i105", 1972, 10, 8, 21, 45, 45.46, 9.19, "Europe/Rome", "2059-06-15", (1973, 1, 3, 13, 7)),
    ("Moscow1928i111", 1928, 4, 18, 3, 27, 55.76, 37.62, "Europe/Moscow", "2077-06-15", (1928, 9, 14, 5, 19)),
    ("Moscow1974i007", 1974, 12, 22, 19, 59, 55.76, 37.62, "Europe/Moscow", "2045-06-15", (1975, 3, 3, 4, 30)),
    ("Moscow1984i033", 1984, 10, 28, 21, 21, 55.76, 37.62, "Europe/Moscow", "2067-06-15", (1985, 1, 19, 9, 25)),
    ("Moscow1994i059", 1994, 8, 6, 23, 43, 55.76, 37.62, "Europe/Moscow", "2033-06-15", (1994, 9, 14, 16, 16)),
    ("Moscow2004i085", 2004, 6, 12, 1, 5, 55.76, 37.62, "Europe/Moscow", "2055-06-15", (2004, 8, 1, 21, 15)),
    ("Mumbai1933i124", 1933, 9, 21, 4, 8, 19.08, 72.88, "Asia/Kolkata", "2060-06-15", (1934, 1, 25, 16, 16)),
    ("Mumbai1979i020", 1979, 5, 25, 20, 40, 19.08, 72.88, "Asia/Kolkata", "2028-06-15", (1979, 7, 13, 16, 34)),
    ("Mumbai1989i046", 1989, 3, 3, 22, 2, 19.08, 72.88, "Asia/Kolkata", "2050-06-15", (1989, 5, 3, 23, 20)),
    ("Mumbai1999i072", 1999, 1, 9, 0, 24, 19.08, 72.88, "Asia/Kolkata", "2072-06-15", (1999, 3, 23, 5, 19)),
    ("Mumbai2009i098", 2009, 11, 15, 2, 46, 19.08, 72.88, "Asia/Kolkata", "2038-06-15", (2009, 12, 13, 11, 13)),
    ("NewYork1929i062", 1929, 11, 11, 14, 34, 40.71, -74.01, "America/New_York", "2042-06-15", (1930, 3, 4, 9, 45)),
    ("NewYork1939i088", 1939, 9, 17, 16, 56, 40.71, -74.01, "America/New_York", "2064-06-15", (1940, 1, 20, 14, 48)),
    ("NewYork1949i114", 1949, 7, 23, 18, 18, 40.71, -74.01, "America/New_York", "2030-06-15", (1949, 10, 12, 19, 46)),
    ("NewYork1995i010", 1995, 3, 27, 10, 50, 40.71, -74.01, "America/New_York", "2054-06-15", (1995, 5, 25, 21, 5)),
    ("NewYork2005i036", 2005, 1, 5, 12, 12, 40.71, -74.01, "America/New_York", "2076-06-15", (2005, 3, 18, 3, 47)),
    ("Oslo1932i087", 1932, 4, 6, 3, 39, 59.91, 10.75, "Europe/Oslo", "2061-06-15", (1932, 8, 13, 7, 17)),
    ("Oslo1942i113", 1942, 2, 12, 5, 1, 59.91, 10.75, "Europe/Oslo", "2027-06-15", (1942, 5, 8, 11, 7)),
    ("Oslo1988i009", 1988, 10, 16, 21, 33, 59.91, 10.75, "Europe/Oslo", "2051-06-15", (1988, 12, 18, 12, 23)),
    ("Oslo1998i035", 1998, 8, 22, 23, 55, 59.91, 10.75, "Europe/Oslo", "2073-06-15", (1998, 11, 5, 17, 26)),
    ("Oslo2008i061", 2008, 6, 28, 1, 17, 59.91, 10.75, "Europe/Oslo", "2039-06-15", (2008, 7, 28, 22, 23)),
    ("Paris1946i003", 1946, 4, 6, 15, 51, 48.86, 2.35, "Europe/Paris", "2033-06-15", (1946, 7, 2, 19, 28)),
    ("Paris1956i029", 1956, 2, 12, 17, 13, 48.86, 2.35, "Europe/Paris", "2055-06-15", (1956, 5, 22, 0, 19)),
    ("Paris1966i055", 1966, 12, 18, 19, 35, 48.86, 2.35, "Europe/Paris", "2077-06-15", (1967, 4, 8, 6, 23)),
    ("Paris1976i081", 1976, 10, 24, 21, 57, 48.86, 2.35, "Europe/Paris", "2043-06-15", (1976, 12, 30, 12, 16)),
    ("Paris1986i107", 1986, 8, 2, 23, 19, 48.86, 2.35, "Europe/Paris", "2065-06-15", (1986, 10, 20, 18, 9)),
    ("Rome1925i000", 1925, 1, 1, 0, 0, 41.9, 12.5, "Europe/Rome", "2024-06-15", (1925, 4, 10, 9, 54)),
    ("Rome1935i026", 1935, 11, 7, 2, 22, 41.9, 12.5, "Europe/Rome", "2046-06-15", (1936, 2, 25, 15, 54)),
    ("Rome1945i052", 1945, 9, 13, 4, 44, 41.9, 12.5, "Europe/Rome", "2068-06-15", (1946, 1, 13, 20, 53)),
    ("Rome1955i078", 1955, 7, 19, 6, 6, 41.9, 12.5, "Europe/Rome", "2034-06-15", (1955, 10, 6, 2, 54)),
    ("Rome1965i104", 1965, 5, 25, 8, 28, 41.9, 12.5, "Europe/Rome", "2056-06-15", (1965, 8, 24, 8, 53)),
    ("SaoPaulo1944i015", 1944, 4, 26, 3, 15, -23.55, -46.63, "America/Sao_Paulo", "2069-06-15", (1944, 8, 29, 9, 33)),
    ("SaoPaulo1954i041", 1954, 2, 4, 5, 37, -23.55, -46.63, "America/Sao_Paulo", "2035-06-15", (1954, 4, 26, 17, 13)),
    ("SaoPaulo1964i067", 1964, 12, 10, 7, 59, -23.55, -46.63, "America/Sao_Paulo", "2057-06-15", (1965, 3, 12, 23, 17)),
    ("SaoPaulo1974i093", 1974, 10, 16, 9, 21, -23.55, -46.63, "America/Sao_Paulo", "2079-06-15", (1975, 1, 29, 4, 16)),
    (
        "SaoPaulo1984i119",
        1984,
        8,
        22,
        11,
        43,
        -23.55,
        -46.63,
        "America/Sao_Paulo",
        "2045-06-15",
        (1984, 10, 22, 10, 13),
    ),
    ("Seoul1927i074", 1927, 11, 3, 2, 58, 37.57, 126.98, "Asia/Seoul", "2078-06-15", (1928, 4, 1, 8, 48)),
    ("Seoul1937i100", 1937, 9, 9, 4, 20, 37.57, 126.98, "Asia/Seoul", "2044-06-15", (1937, 12, 24, 13, 45)),
    ("Seoul1947i126", 1947, 7, 15, 6, 42, 37.57, 126.98, "Asia/Seoul", "2066-06-15", (1947, 11, 10, 19, 48)),
    ("Seoul1993i022", 1993, 3, 19, 22, 14, 37.57, 126.98, "Asia/Seoul", "2034-06-15", (1993, 4, 29, 18, 59)),
    ("Seoul2003i048", 2003, 1, 25, 0, 36, 37.57, 126.98, "Asia/Seoul", "2056-06-15", (2003, 3, 19, 0, 57)),
    ("Sydney1934i075", 1934, 4, 14, 15, 15, -33.87, 151.21, "Australia/Sydney", "2025-06-15", (1934, 7, 14, 9, 22)),
    ("Sydney1944i101", 1944, 2, 20, 17, 37, -33.87, 151.21, "Australia/Sydney", "2047-06-15", (1944, 6, 2, 14, 13)),
    ("Sydney1954i127", 1954, 12, 26, 19, 59, -33.87, 151.21, "Australia/Sydney", "2069-06-15", (1955, 4, 19, 21, 17)),
    ("Sydney2000i023", 2000, 8, 2, 11, 31, -33.87, 151.21, "Australia/Sydney", "2037-06-15", (2000, 9, 7, 22, 21)),
    ("Sydney2010i049", 2010, 6, 8, 13, 53, -33.87, 151.21, "Australia/Sydney", "2059-06-15", (2010, 7, 27, 4, 20)),
    ("Tokyo1965i018", 1965, 7, 3, 18, 6, 35.68, 139.77, "Asia/Tokyo", "2078-06-15", (1965, 10, 24, 7, 56)),
    ("Tokyo1975i044", 1975, 5, 9, 20, 28, 35.68, 139.77, "Asia/Tokyo", "2044-06-15", (1975, 7, 17, 13, 57)),
    ("Tokyo1985i070", 1985, 3, 15, 22, 50, 35.68, 139.77, "Asia/Tokyo", "2066-06-15", (1985, 6, 4, 19, 51)),
    ("Tokyo1995i096", 1995, 1, 21, 0, 12, 35.68, 139.77, "Asia/Tokyo", "2032-06-15", (1995, 2, 27, 0, 49)),
    ("Tokyo2005i122", 2005, 11, 27, 2, 34, 35.68, 139.77, "Asia/Tokyo", "2054-06-15", (2006, 1, 14, 6, 45)),
    ("Toronto1930i013", 1930, 6, 4, 1, 41, 43.65, -79.38, "America/Toronto", "2063-06-15", (1930, 10, 15, 6, 26)),
    ("Toronto1940i039", 1940, 4, 10, 3, 3, 43.65, -79.38, "America/Toronto", "2029-06-15", (1940, 7, 8, 12, 23)),
    ("Toronto1950i065", 1950, 2, 16, 5, 25, 43.65, -79.38, "America/Toronto", "2051-06-15", (1950, 5, 28, 18, 14)),
    ("Toronto1960i091", 1960, 12, 22, 7, 47, 43.65, -79.38, "America/Toronto", "2073-06-15", (1961, 4, 14, 0, 18)),
    ("Toronto1970i117", 1970, 10, 28, 9, 9, 43.65, -79.38, "America/Toronto", "2039-06-15", (1971, 1, 5, 5, 15)),
]

_IDS = [row[0] for row in _REFERENCE_SUBJECTS]
_REFERENCE_TOLERANCE_S = 180.0  # external reference is displayed to the minute


@lru_cache(maxsize=None)
def _natal(name, y, mo, d, h, mn, lat, lng, tz):
    return AstrologicalSubjectFactory.from_birth_data(
        name,
        y,
        mo,
        d,
        h,
        mn,
        lng=lng,
        lat=lat,
        tz_str=tz,
        online=False,
    )


def _natal_for(row):
    name, y, mo, d, h, mn, lat, lng, tz = row[:9]
    return _natal(name, y, mo, d, h, mn, lat, lng, tz)


def _target_iso(row):
    return row[9] + "T00:00:00Z"


def test_reference_subject_pool_is_large():
    """The reference pool keeps growing — guard against accidental shrink."""
    assert len(_REFERENCE_SUBJECTS) >= 100
    assert len(set(_IDS)) == len(_IDS), "duplicate reference subject names"


@pytest.mark.parametrize("row", _REFERENCE_SUBJECTS, ids=_IDS)
def test_reference_sp_ephemeris_date(row):
    """SP ephemeris date must match the external reference within 3 minutes."""
    natal = _natal_for(row)
    sp = SecondaryProgressionFactory.compute_full(natal, target_iso_utc_datetime=_target_iso(row))
    our = datetime.fromisoformat(sp.ephemeris_iso_utc_datetime.replace("Z", "+00:00"))
    ref = datetime(*row[10], tzinfo=timezone.utc)
    diff = abs((our - ref).total_seconds())
    assert diff < _REFERENCE_TOLERANCE_S, f"{row[0]}: SP ephemeris off by {diff:.0f}s — ours={our} reference={ref}"


@pytest.mark.parametrize("row", _REFERENCE_SUBJECTS, ids=_IDS)
def test_reference_day_for_year_formula(row):
    """Progressed JD must equal natal_jd + (target - natal) / tropical year."""
    natal = _natal_for(row)
    sp = SecondaryProgressionFactory.compute_full(natal, target_iso_utc_datetime=_target_iso(row))
    ty, tm, td = (int(x) for x in row[9].split("-"))
    target_jd = ephe.julday(ty, tm, td, 0.0)
    expected = natal.julian_day + (target_jd - natal.julian_day) / DAYS_PER_TROPICAL_YEAR
    assert sp.progressed_subject.julian_day == pytest.approx(expected, abs=2e-3)


@pytest.mark.parametrize("row", _REFERENCE_SUBJECTS, ids=_IDS)
def test_reference_solar_arc_equals_sun_delta(row):
    """Solar arc must equal the forward delta of the progressed Sun."""
    natal = _natal_for(row)
    progressed = SecondaryProgressionFactory.compute(natal, target_iso_utc_datetime=_target_iso(row))
    sa = SolarArcFactory.compute(natal, target_iso_utc_datetime=_target_iso(row), compute_aspects=False)
    expected = (progressed.sun.abs_pos - natal.sun.abs_pos) % 360.0
    assert sa.solar_arc == pytest.approx(expected, abs=1e-6)


@pytest.mark.parametrize("row", _REFERENCE_SUBJECTS, ids=_IDS)
def test_reference_compute_full_matches_compute(row):
    """compute_full().progressed_subject must equal a bare compute() call."""
    natal = _natal_for(row)
    bare = SecondaryProgressionFactory.compute(natal, target_iso_utc_datetime=_target_iso(row))
    full = SecondaryProgressionFactory.compute_full(natal, target_iso_utc_datetime=_target_iso(row))
    assert full.progressed_subject.julian_day == pytest.approx(bare.julian_day, abs=1e-9)
    assert full.progressed_subject.sun.abs_pos == pytest.approx(bare.sun.abs_pos, abs=1e-9)
    assert full.progressed_subject.moon.abs_pos == pytest.approx(bare.moon.abs_pos, abs=1e-9)


@pytest.mark.parametrize("row", _REFERENCE_SUBJECTS, ids=_IDS)
def test_reference_orb_config_monotonic(row):
    """The configurable predictive orb must be honoured: every cross-aspect
    stays within the requested orb, and a wider orb never yields fewer."""
    natal = _natal_for(row)
    counts = []
    for orb in (1.0, 2.0, 3.0, 5.0):
        sp = SecondaryProgressionFactory.compute_full(
            natal,
            target_iso_utc_datetime=_target_iso(row),
            aspect_orb=orb,
        )
        for aspect in sp.progressed_to_natal_aspects:
            assert aspect.orb <= orb + 1e-6, f"{row[0]}: orb {aspect.orb} exceeds {orb}"
        counts.append(len(sp.progressed_to_natal_aspects))
    for i in range(len(counts) - 1):
        assert counts[i] <= counts[i + 1], f"{row[0]}: aspect count not monotonic {counts}"


@pytest.mark.parametrize("row", _REFERENCE_SUBJECTS, ids=_IDS)
def test_reference_predictive_aspects_ptolemaic(row):
    """Predictive cross-aspects use only the five Ptolemaic aspects."""
    natal = _natal_for(row)
    ptolemaic = {"conjunction", "opposition", "trine", "sextile", "square"}
    sp = SecondaryProgressionFactory.compute_full(
        natal,
        target_iso_utc_datetime=_target_iso(row),
        aspect_orb=3.0,
    )
    sa = SolarArcFactory.compute(
        natal,
        target_iso_utc_datetime=_target_iso(row),
        aspect_orb=3.0,
    )
    assert {a.aspect for a in sp.progressed_to_natal_aspects} <= ptolemaic
    assert {a.aspect for a in sa.directed_to_natal_aspects} <= ptolemaic
