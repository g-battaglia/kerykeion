# -*- coding: utf-8 -*-
"""The places the golden charts are cast at, frozen.

Every golden SVG baseline is a chart, and a chart is a moment AND a place. The
moments were always literals; the places were not — the tests and the regenerator
both passed a city name and let ``from_birth_data`` resolve it, and its ``online``
argument defaults to True, so both went to GeoNames over the network.

That makes the whole golden suite non-hermetic. A regeneration bakes whatever the
service answered that day into 346 files; a test run compares against whatever it
answers today. Running the comparison at four tolerances over one afternoon gave
2, 6, 63 and 69 failures from the same tree, because the answer moved between
runs. No tolerance can be chosen against a target that does not hold still, and
the 0.5 relative tolerance this table exists to let us retire was in part paying
for exactly this.

The coordinates below are GeoNames' own answers, captured once. They are the
values the stored baselines were generated from, so freezing them changes no
baseline; what changes is that they cannot change again by themselves.

Adding a golden chart in a new city means adding it here, not reaching for the
network. ``test_golden_charts_are_hermetic`` fails if a golden test resolves a
place any other way.
"""

#: (city, nation) -> (longitude, latitude, IANA time zone)
GOLDEN_PLACES: dict[tuple[str, str], tuple[float, float, str]] = {
    ("Liverpool", "GB"): (-2.97794, 53.41058, "Europe/London"),
    ("London", "GB"): (-0.12574, 51.50853, "Europe/London"),
    ("Rome", "IT"): (12.51133, 41.89193, "Europe/Rome"),
    ("Paris", "FR"): (2.3488, 48.85341, "Europe/Paris"),
    ("Ulm", "DE"): (9.99155, 48.39841, "Europe/Berlin"),
    ("New York", "US"): (-74.00597, 40.71427, "America/New_York"),
    ("Malaga", "ES"): (-4.42034, 36.72016, "Europe/Madrid"),
    ("Kiev", "UA"): (30.5238, 50.45466, "Europe/Kyiv"),
    ("Istanbul", "TR"): (28.94966, 41.01384, "Europe/Istanbul"),
    ("Hunan", "CN"): (112.97087, 28.19874, "Asia/Shanghai"),
    ("Funchal", "PT"): (-16.92547, 32.66568, "Atlantic/Madeira"),
    ("Florence", "IT"): (11.24626, 43.77925, "Europe/Rome"),
    ("Atlanta", "US"): (-84.38798, 33.749, "America/New_York"),
    ("Allahabad", "IN"): (81.84322, 25.44478, "Asia/Kolkata"),
    ("Los Angeles", "US"): (-118.24368, 34.05223, "America/Los_Angeles"),
    ("Shawnee", "US"): (-95.67804, 39.04833, "America/Chicago"),
    ("Owensboro", "US"): (-87.11333, 37.77422, "America/Chicago"),
    ("Tokyo", "JP"): (139.69171, 35.6895, "Asia/Tokyo"),
}


def golden_place(city: str, nation: str) -> dict:
    """The keyword arguments that cast a chart at this place without the network.

    Returns ``city`` and ``nation`` alongside the coordinates so the chart still
    prints the place it names — the panel and the ``<desc>`` read the strings, and
    a baseline that stopped naming Liverpool would be a different baseline.
    """
    try:
        longitude, latitude, tz_str = GOLDEN_PLACES[(city, nation)]
    except KeyError:
        raise KeyError(
            f"{city}, {nation} is not in GOLDEN_PLACES. A golden chart must be cast "
            f"at a frozen place: add its coordinates to tests/data/golden_places.py "
            f"rather than letting the chart resolve them over the network."
        ) from None
    return {
        "city": city,
        "nation": nation,
        "lng": longitude,
        "lat": latitude,
        "tz_str": tz_str,
        "online": False,
    }
