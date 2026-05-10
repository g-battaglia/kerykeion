# Swiss Ephemeris Backend Configuration

Kerykeion uses **libephemeris** (pure Python) as its default ephemeris backend.
The Swiss Ephemeris C library (**pyswisseph**) is available as an optional
alternative for users who need maximum calculation speed.

> **Note:** Swiss Ephemeris data files are **not bundled** with Kerykeion.
> You must download them separately if you use the swisseph backend.

## When to use Swiss Ephemeris

- **Maximum speed**: swisseph's C implementation is faster than libephemeris
  for high-throughput workloads (batch calculations, time-range scans).
- **Existing workflows**: you already have `.se1` files and a swisseph setup.
- **Specific features**: some legacy swisseph-only features not yet ported to
  libephemeris.

For most users, **libephemeris is recommended** — it works out of the box with
no C compiler, no external data files, and no GPL license obligations.

## Installation

```bash
# Install Kerykeion with the Swiss Ephemeris optional extra
pip install kerykeion[swiss]

# Or install pyswisseph separately
pip install pyswisseph
```

## Obtaining ephemeris data files

Swiss Ephemeris requires binary `.se1` data files for full-precision
calculations. Without them, swisseph falls back to its built-in **Moshier
analytical ephemeris** (lower precision, but functional).

Download the files from the official Astrodienst FTP server:

```
https://www.astro.com/ftp/swisseph/ephe/
```

### Minimum recommended files

| File | Description |
|------|-------------|
| `seas_18.se1` | Main planetary ephemeris (asteroids, ~1800–2400 CE) |
| `semo_18.se1` | Moon ephemeris |
| `sepl_18.se1` | Planetary ephemeris (Sun, planets) |

### Optional files

| File / Directory | Description |
|------------------|-------------|
| `sefstars.txt` | Fixed star catalog (required for `FixedStarDiscoveryFactory` with swisseph) |
| `ast*/se*.se1` | Asteroid ephemeris files (Chiron, Ceres, Pholus, TNOs, etc.) |

## Configuration

### 1. Set the data directory

Point `KERYKEION_EPHE_PATH` to the directory containing your `.se1` files:

```bash
export KERYKEION_EPHE_PATH=/path/to/your/se1/files
```

### 2. Force the swisseph backend

By default, Kerykeion auto-detects the backend (preferring libephemeris).
To force swisseph:

```bash
export KERYKEION_BACKEND=swisseph
```

### 3. Run your script

```bash
KERYKEION_BACKEND=swisseph KERYKEION_EPHE_PATH=/path/to/se1 python my_script.py
```

## Verifying the configuration

```python
from kerykeion.ephemeris_backend import BACKEND_NAME, EPHE_DATA_PATH

print(f"Backend: {BACKEND_NAME}")
print(f"Data path: {EPHE_DATA_PATH}")
# Expected output:
# Backend: swisseph
# Data path: /path/to/your/se1/files
```

## Fixed star discovery

When using the swisseph backend, `FixedStarDiscoveryFactory` reads the
`sefstars.txt` catalog from the directory specified by `KERYKEION_EPHE_PATH`.
If the file is not present, the discovery returns an empty list (no crash).

With the libephemeris backend, the factory uses its own native catalog and
does not need `sefstars.txt`.

## Fallback behavior (no .se1 files)

If `KERYKEION_EPHE_PATH` is not set (or points to an empty directory),
swisseph automatically uses its **built-in Moshier analytical ephemeris**.
This provides:

- Planetary positions with ~1 arc-second accuracy (sufficient for most
  astrological work)
- No asteroid support
- No fixed star catalog

A warning is logged at startup when this fallback is active.

## License implications

**pyswisseph** is licensed under **AGPL-3.0** by Astrodienst AG. If you
distribute software that links against pyswisseph, you must comply with
the AGPL-3.0 terms (source code disclosure, copyleft).

**Kerykeion itself** is licensed under AGPL-3.0. When installed without
`pyswisseph` (i.e., using libephemeris only), there are no additional GPL
obligations beyond the AGPL-3.0 terms of Kerykeion itself.

If you need a closed-source deployment, use the default libephemeris backend
or consider the [Astrologer API](https://www.kerykeion.net/astrologer-api/subscribe).

## Comparison with libephemeris

| Feature | libephemeris (default) | swisseph (optional) |
|---------|----------------------|---------------------|
| License | AGPL-3.0 (Kerykeion project) | AGPL-3.0 (Astrodienst AG) |
| Language | Pure Python | C bindings |
| Data source | NASA JPL DE440/DE441 | Swiss Ephemeris `.se1` files |
| Data management | Automatic (`~/.libephemeris/leb/`) | Manual (download `.se1` files) |
| C compiler needed | No | Yes |
| Precision | Sub-arcsecond | Sub-arcsecond |
| Fixed stars | Native catalog | `sefstars.txt` file |

For a detailed numerical comparison, see
[Backend Precision Comparison](backend_precision_comparison.md).
