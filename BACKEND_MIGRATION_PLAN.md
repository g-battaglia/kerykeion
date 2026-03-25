# Backend Migration Plan: v5 → v6

This document describes the two-phase migration strategy for transitioning
kerykeion from pyswisseph (GPL-licensed) to libephemeris (AGPL-3.0, GPL-free
ephemeris data from NASA JPL) as the default backend.

## Motivation

Swiss Ephemeris (`pyswisseph`) has a dual license: GPL or commercial. For v6,
kerykeion must be completely free from the GPL dependency by default, while
still allowing users who want Swiss Ephemeris to opt in explicitly.

`libephemeris` uses NASA JPL DE440/DE441 ephemeris data (public domain) via
Skyfield, and is licensed AGPL-3.0 — no GPL entanglement with Swiss Ephemeris.

---

## Phase 1 — v5: pyswisseph default, libephemeris optional

### pyproject.toml

```toml
dependencies = [
    ...
    "pyswisseph>=2.10.3.1",        # default, backward compatible
]

[project.optional-dependencies]
lib = ["libephemeris>=1.0.0a1"]    # opt-in
```

### Runtime behavior

| Command | Installed | Backend at runtime |
|---------|-----------|-------------------|
| `pip install kerykeion` | pyswisseph | swisseph |
| `pip install kerykeion[lib]` | pyswisseph + libephemeris | swisseph (wins by default) |
| `pip install kerykeion[lib]` + `KERYKEION_BACKEND=libephemeris` | both | libephemeris (forced) |

### Detection order (ephemeris_backend.py)

1. If `KERYKEION_BACKEND` env var is set → use that backend (error if not installed)
2. Try `import swisseph` → if found, use it (backward compat)
3. Try `import libephemeris` → if found, use it
4. Neither → `ImportError`

### Key points

- **Zero breaking change** for existing users
- Users can test libephemeris via `pip install kerykeion[lib]` + env var
- pip extras are additive: `[lib]` adds libephemeris on top of pyswisseph
- The env var `KERYKEION_BACKEND` is essential — without it, users who install
  `kerykeion[lib]` cannot use libephemeris because swisseph always wins

---

## Phase 2 — v6: libephemeris default, pyswisseph optional

### pyproject.toml

```toml
dependencies = [
    ...
    "libephemeris>=1.0.0a1",       # default, GPL-free
]

[project.optional-dependencies]
swiss = ["pyswisseph>=2.10.3.1"]   # opt-in, user accepts GPL/commercial license
```

### Runtime behavior

| Command | Installed | Backend at runtime | License |
|---------|-----------|-------------------|---------|
| `pip install kerykeion` | libephemeris | libephemeris | GPL-free |
| `pip install kerykeion[swiss]` | libephemeris + pyswisseph | swisseph | GPL/commercial |
| `KERYKEION_BACKEND=libephemeris` | any | libephemeris (forced) | GPL-free |

### Detection order (ephemeris_backend.py) — unchanged

Same logic as v5. The auto-detect order (swisseph first, then libephemeris)
does not change. What changes is which package is installed by default:

- v5: pyswisseph is always present → swisseph wins
- v6: only libephemeris is present → libephemeris wins
- v6 + `[swiss]`: both present → swisseph wins (user opted in explicitly)

### What changes from v5 to v6 (code diff)

The transition is minimal:

1. **`pyproject.toml`**: Move `pyswisseph` from `dependencies` to
   `[optional-dependencies].swiss`; move `libephemeris` from
   `[optional-dependencies].lib` to `dependencies`
2. **Documentation**: Update installation instructions
3. **CHANGELOG**: Note the breaking change
4. **`ephemeris_backend.py`**: No change needed — detection logic is identical

### Breaking changes for v6

Users who do `pip install kerykeion` will get libephemeris instead of swisseph:

| Aspect | Impact |
|--------|--------|
| Positional accuracy | < 0.02° delta (negligible for astrology) |
| Zodiac signs | Identical across backends |
| Performance | Slower (pure Python vs C bindings) |
| Date range | DE440: 1550–2650 CE (vs -13000/+16800 for swisseph) |
| Rise/set times | ~1-2 second delta |
| License | GPL-free by default |

This justifies a **major version bump** (v5 → v6).

---

## Environment Variable: `KERYKEION_BACKEND`

Available in both v5 and v6.

| Value | Effect |
|-------|--------|
| `swisseph` | Force swisseph backend (error if not installed) |
| `libephemeris` | Force libephemeris backend (error if not installed) |
| *(unset)* | Auto-detect: try swisseph first, then libephemeris |

Example usage:

```bash
# Force libephemeris even when both are installed
KERYKEION_BACKEND=libephemeris python my_script.py

# In .env or shell profile
export KERYKEION_BACKEND=libephemeris
```

Programmatic check:

```python
from kerykeion import BACKEND_NAME
print(BACKEND_NAME)  # "swisseph" or "libephemeris"
```

---

## Timeline

| Phase | Version | Default Backend | Status |
|-------|---------|-----------------|--------|
| Phase 1 | v5.x | pyswisseph | In progress |
| Phase 2 | v6.0 | libephemeris | Planned |
