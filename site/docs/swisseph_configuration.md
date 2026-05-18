---
title: 'Swiss Ephemeris Configuration'
category: 'Reference'
description: 'Setup guide for the optional Swiss Ephemeris (pyswisseph) backend.'
tags: ['docs', 'swisseph', 'backend', 'configuration']
order: 22
---

# Swiss Ephemeris Backend Configuration

Kerykeion uses **libephemeris** (pure Python) as its default ephemeris backend.
The Swiss Ephemeris C library (**pyswisseph**) is available as an optional
alternative backend.

> **Note:** Swiss Ephemeris data files are **not bundled** with Kerykeion.
> You must download them separately if you use the swisseph backend.

## When to use Swiss Ephemeris

- **Existing workflows**: you already have `.se1` files and a swisseph setup.
- **Specific features**: some legacy swisseph-only features not yet ported to
  libephemeris.

For most users, **libephemeris is recommended** — it works out of the box with
no C compiler and no external data files.

## Installation

```bash
# Install Kerykeion with the Swiss Ephemeris optional extra
pip install kerykeion[swiss]

# Or install pyswisseph separately
pip install pyswisseph
```

## Automatic setup (recommended)

Kerykeion includes a setup utility that downloads the required data files
and shows the license terms:

```bash
python -m kerykeion.swisseph_setup
```

This downloads the main ephemeris files (planets, Moon, asteroids, fixed
stars) from the official Swiss Ephemeris GitHub repository. The utility
will show the AGPL-3.0 license notice and ask for confirmation.

Options:

```bash
# Non-interactive (for CI/scripts)
python -m kerykeion.swisseph_setup --yes

# Custom install directory
python -m kerykeion.swisseph_setup --target /path/to/data

# Skip TNO/dwarf planet files
python -m kerykeion.swisseph_setup --skip-asteroids
```

Default install location: `~/.kerykeion/sweph/`

### TNO/dwarf planet files

TNO ephemeris files (Eris, Sedna, Haumea, Makemake, etc.) are not
available from GitHub. The setup utility will show instructions for
downloading them manually from the official Astrodienst Dropbox.
Without these files, planets and fixed stars work normally.

## Manual setup

If you prefer to download files manually:

### Minimum recommended files

| File | Source | Description |
|------|--------|-------------|
| `seas_18.se1` | [GitHub](https://github.com/aloistr/swisseph/tree/master/ephe) | Main asteroid ephemeris (~1800-2400 CE) |
| `semo_18.se1` | [GitHub](https://github.com/aloistr/swisseph/tree/master/ephe) | Moon ephemeris |
| `sepl_18.se1` | [GitHub](https://github.com/aloistr/swisseph/tree/master/ephe) | Planetary ephemeris (Sun, planets) |
| `sefstars.txt` | [GitHub](https://github.com/aloistr/swisseph/tree/master/ephe) | Fixed star catalog |

### Optional files (TNOs)

| File | Source | Description |
|------|--------|-------------|
| `ast136/s136199s.se1` | [Astrodienst Dropbox](https://www.dropbox.com/scl/fo/y3naz62gy6f6qfrhquu7u/h?rlkey=ejltdhb262zglm7eo6yfj2940&dl=0) | Eris |
| `ast136/s136108s.se1` | Astrodienst Dropbox | Haumea |
| `ast136/s136472s.se1` | Astrodienst Dropbox | Makemake |
| `ast90/se90377s.se1` | Astrodienst Dropbox | Sedna |
| `ast90/se90482s.se1` | Astrodienst Dropbox | Orcus |
| `ast50/se50000s.se1` | Astrodienst Dropbox | Quaoar |
| `ast28/se28978s.se1` | Astrodienst Dropbox | Ixion |

## Configuration

### 1. Set the data directory

Point `KERYKEION_EPHE_PATH` to the directory containing your `.se1` files:

```bash
export KERYKEION_EPHE_PATH=~/.kerykeion/sweph
```

### 2. Force the swisseph backend

By default, Kerykeion auto-detects the backend (preferring libephemeris).
To force swisseph:

```bash
export KERYKEION_BACKEND=swisseph
```

### 3. Run your script

```bash
KERYKEION_BACKEND=swisseph KERYKEION_EPHE_PATH=~/.kerykeion/sweph python my_script.py
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

## Fixed Stars Catalog (`sefstars.txt`)

> **Important — required for any fixed-star feature on the swisseph backend.**

Fixed-star functionality on the swisseph backend depends on the
`sefstars.txt` data file, which is **not bundled with kerykeion** (it is
distributed under the Swiss Ephemeris license by Astrodienst, which we
cannot redistribute). You must download it yourself.

Affected features (all require `sefstars.txt` when `KERYKEION_BACKEND=swisseph`):

| Feature | Effect when file is missing |
|---------|-----------------------------|
| `AstrologicalSubjectFactory.from_birth_data(..., active_fixed_stars=[...])` | `subject.fixed_stars` ends up empty; warning logged. |
| `FixedStarDiscoveryFactory.find_prominent_stars(subject)` | Returns `[]`; warning logged. |
| `subject.find_fixed_star(name)` | Returns `None` (the underlying array is empty). |
| Chart wheel rendering of stars passed via `active_fixed_stars` | The stars are simply absent from the SVG. |

### Where to get the file

Download `sefstars.txt` from the official Swiss Ephemeris repository:

[https://github.com/aloistr/swisseph/tree/master/ephe](https://github.com/aloistr/swisseph/tree/master/ephe)

The automatic setup utility (`python -m kerykeion.swisseph_setup`) already
downloads this file alongside the planetary ephemerides — using it is the
shortest path. If you do the setup manually, place the file in the
directory pointed to by `KERYKEION_EPHE_PATH`:

```bash
# Example: download to the default location
mkdir -p ~/.kerykeion/sweph
curl -L -o ~/.kerykeion/sweph/sefstars.txt \
  https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/sefstars.txt
export KERYKEION_EPHE_PATH=~/.kerykeion/sweph
```

### License

`sefstars.txt` is part of the Swiss Ephemeris distribution and is
licensed under **AGPL-3.0 by Astrodienst AG**. If you ship a product that
includes this file, the Swiss Ephemeris license terms apply to that
component — see <https://www.astro.com/swisseph/swephinfo_e.htm>.

### Diagnostic warning

When fixed-star calculations on the swisseph backend produce zero stars,
kerykeion logs a single warning at WARNING level:

```
No fixed stars could be calculated with the swisseph backend. The Swiss
Ephemeris fixed-star catalog file ('sefstars.txt') is not bundled with
kerykeion due to licensing. Download it from
https://github.com/aloistr/swisseph/tree/master/ephe and place it in
KERYKEION_EPHE_PATH (currently: /path/to/sweph). Alternatively, use the
libephemeris backend (KERYKEION_BACKEND=libephemeris) which ships its
own catalog. See site/docs/swisseph_configuration.md for details.
```

### Quick alternative

If you don't have a specific reason to use swisseph for fixed stars, the
**libephemeris backend ships a 116-star catalog built-in** (Hipparcos +
IAU WGSN, AGPL-3.0 owned by the kerykeion project) and does not require
any external data file:

```bash
export KERYKEION_BACKEND=libephemeris  # default; no setup needed
```

The list of available stars on either backend is exposed by
`kerykeion.fixed_stars.FixedStarCatalog.list_all()` (note: this accessor
reads from libephemeris regardless of the active backend, so the names
are usable on both backends as long as the corresponding ephemeris data
is available).

## Fallback behavior (no .se1 files)

If `KERYKEION_EPHE_PATH` is not set (or points to an empty directory),
swisseph automatically uses its **built-in Moshier analytical ephemeris**.
This provides:

- Planetary positions with ~1 arc-second accuracy (sufficient for most
  astrological work)
- No asteroid support
- No fixed star catalog

A warning is logged at startup when this fallback is active.

## License

**pyswisseph** and the Swiss Ephemeris data files are licensed under
**AGPL-3.0** by Astrodienst AG. If you use the swisseph backend, the
Swiss Ephemeris license terms apply to those components.

**Kerykeion itself** is licensed under AGPL-3.0 by the Kerykeion project.
When installed without `pyswisseph` (i.e., using libephemeris only),
only Kerykeion's own AGPL-3.0 license applies.

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
