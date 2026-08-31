---
title: 'Fetch Geonames'
category: 'Reference'
description: 'Utility to fetch location and timezone data from GeoNames API'
tags: ['docs', 'utility', 'geonames', 'location', 'timezone']
order: 21
---

# FetchGeonames (`kerykeion.geonames.fetcher`)

The `FetchGeonames` class provides an interface to the GeoNames API to retrieve geographical coordinates and timezone information necessary for chart calculations.

**Note:** this module requires internet access and a GeoNames username. The
built-in default account is shared and rate-limited; register a free one at
[geonames.org](https://www.geonames.org/login) for anything beyond trying it out.

## Usage

Initialize the class with a city and country code to fetch its geographical data.

```python
from kerykeion.geonames.fetcher import FetchGeonames

# Initialize the fetcher
geonames = FetchGeonames(
    city_name="Rome",
    country_code="IT",
    username="century.boy" # Optional: defaults to "century.boy"
)

# Get serialized data
data = geonames.get_serialized_data()
print(data)
```

## Class `FetchGeonames`

### `__init__`

```python
# doc-snippet: no-run — API signature reference
def __init__(
    self,
    city_name: str,
    country_code: str,
    username: str = "century.boy",
    cache_expire_after_days: int = 30,
    cache_name: Optional[Union[str, Path]] = None
)
```

**Parameters:**

-   `city_name`: Name of the city to search for.
-   `country_code`: Two-letter ISO country code (e.g., "IT", "US").
-   `username`: GeoNames username (default: "century.boy"). Can also be set via the `KERYKEION_GEONAMES_USERNAME` environment variable in `AstrologicalSubjectFactory`.
-   `cache_expire_after_days`: Number of days to cache the API response (default: 30).
-   `cache_name`: Optional path for the cache file. Can also be set via the `KERYKEION_GEONAMES_CACHE_NAME` environment variable.

## Environment Variables

The following environment variables can be used to configure GeoNames behavior:

| Variable | Description |
| :------- | :---------- |
| `KERYKEION_GEONAMES_USERNAME` | GeoNames API username. When set, this is used as the default username in `AstrologicalSubjectFactory` instead of the built-in default. |
| `KERYKEION_GEONAMES_CACHE_NAME` | Custom path for the cache file. Overrides the default cache location. |

### Example

```bash
export KERYKEION_GEONAMES_USERNAME="your_username"
export KERYKEION_GEONAMES_CACHE_NAME="/path/to/custom/cache"
```

```python
from kerykeion import AstrologicalSubjectFactory

# Username is automatically read from KERYKEION_GEONAMES_USERNAME
subject = AstrologicalSubjectFactory.from_birth_data(
    name="John Doe",
    year=1990, month=6, day=15,
    hour=14, minute=30,
    city="London", nation="GB",
    online=True  # No need to pass geonames_username
)
```

### Methods

#### `get_serialized_data()`

Returns a dictionary containing the necessary data for Kerykeion calculations.

**Returns:**
`dict[str, str]`: A dictionary with keys likely including:

-   `name`: City name
-   `lat`: Latitude
-   `lng`: Longitude
-   `countryCode`: Country code
-   `timezonestr`: Timezone ID (e.g., "Europe/Rome")

#### `get_timezone_for_coordinates(lat, lng)`

Resolves the timezone for explicit coordinates through the GeoNames
`timezoneJSON` endpoint. It performs no city search, and reuses the same cached
session, so repeated lookups are served locally.

**Returns:** `dict[str, str]` with `timezonestr` (and the cache status) on
success; an **empty dict** when the response carries no `timezoneId` or the
request fails.

This is the path `AstrologicalSubjectFactory.from_birth_data` takes when it is
given coordinates and no `tz_str` and no `city` — resolving the zone from the
`"Greenwich"` default would silently build the chart in the wrong zone.

#### `close()`

Closes the underlying cached HTTP session and releases its file handles. Each
`FetchGeonames` opens a sqlite-backed `CachedSession` (two file descriptors), so
a long-lived caller that keeps instances referenced can otherwise exhaust them.
The class is also a context manager, which is the preferred form:

```python
# doc-snippet: no-run — contacts the GeoNames API
from kerykeion.geonames.fetcher import FetchGeonames

with FetchGeonames("Rome", "IT") as geonames:
    data = geonames.get_serialized_data()
```

#### `set_default_cache_name(cache_name)` (classmethod)

Override the default cache path used when none is provided. The current value is
readable as the class attribute `FetchGeonames.default_cache_name`, a `Path`
that starts at `~/.kerykeion/cache/kerykeion_geonames_cache` and is also
settable through `KERYKEION_GEONAMES_CACHE_NAME`.

```python
from pathlib import Path
FetchGeonames.set_default_cache_name(Path("/custom/cache/path"))
print(FetchGeonames.default_cache_name)
```

---

> **Need this in production?** Use the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe) for hosted calculations, charts, and AI interpretations - no server setup required. [Learn more →](/content/docs/astrologer-api)
