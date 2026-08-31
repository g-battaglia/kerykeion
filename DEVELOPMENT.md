# 🛠️ Development Setup Guide

Welcome to Kerykeion! This guide will help you set up your development environment to contribute to this astrology library.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.12 or higher** - Check with `python --version`
- **Git** - For cloning the repository
- **uv** - Ultra-fast Python package manager (replaces pip/poetry)

### Installing uv

If you don't have uv installed, follow the installation instructions at the official website:

**👉 [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)**

## 🚀 Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/g-battaglia/kerykeion.git
   cd kerykeion
   ```

2. **Install dependencies**
   ```bash
   # This creates a virtual environment and installs all dependencies
   uv sync --dev
   ```

3. **Verify installation**
   ```bash
   # Test that kerykeion can be imported
   uv run python -c "import kerykeion; print('✅ Setup successful!')"
   ```

## 🧪 Development Commands

Kerykeion uses [poethepoet](https://github.com/nat-n/poethepoet) as a task runner. All tasks are defined in `pyproject.toml`.

### Running Tests

Tests are organized in 4 tiers (each tier includes the previous):

```bash
# Core tests (fastest — excludes the 5 heavy parametrized suites)
uv run poe test:core

# Base tier (DE440s range: 1849-2150)
uv run poe test:base

# Medium tier (DE440 range: 1550-2650)
uv run poe test:medium

# Extended tier (DE441 full range)
uv run poe test:extended

# All offline tests (alias for test:extended; online GeoNames tests stay excluded)
uv run poe test:all

# Run with coverage
uv run poe test:core:cov

# Run specific test file
uv run pytest tests/core/test_aspects.py

# Run tests with verbose output (useful for debugging)
uv run pytest tests/core/test_aspects.py -s -vvv

# How many tests each command collects, without running them
uv run pytest tests/ --collect-only -q -m 'not online' | tail -1
```

#### The tier is auto-detected, and `LIBEPHEMERIS_PRECISION` is what widens it

`test:extended` and `test:all` both run `pytest tests/ -m 'not online'` and set
**no** `LIBEPHEMERIS_PRECISION`. `tests/conftest.py` probes the ephemeris kernel
that is actually loaded and picks the widest tier it can serve — on a default
install that is `medium`, so the extended-tier subjects (500 BC through 1492)
are **skipped with a reason**, not run and not failed. The task name says which
tier is being asked for; the installed kernel decides which one you get.

To really run the extended tier, install the full-range kernel and ask for it:

```bash
uv run python -c "import libephemeris; libephemeris.download_leb_for_tier('extended')"
LIBEPHEMERIS_PRECISION=extended uv run poe test:extended
```

The `regenerate:*` tasks and `test:gates:extended` set
`LIBEPHEMERIS_PRECISION=extended` themselves — baselines must be regenerated on
the full-range kernel or the long-range subjects are silently dropped.

### Code Quality
```bash
# Format code with Ruff
uv run poe format

# Format all code (including tests)
uv run poe format:all

# Lint with Ruff
uv run poe lint

# Type checking with Pyright
uv run poe typecheck

# Type checking with MyPy
uv run poe analyze

# Run the full quality gate (ruff lint + mypy + pyright + full pytest suite)
uv run poe quality

# Build the wheel, install it in isolation, and smoke-test packaged assets
uv run poe build:smoke
```

### Documentation
```bash
# Generate the API reference (pdoc)
uv run poe docs

# Output lands in ./docs — open docs/index.html in your browser.
# It is generated on demand and git-ignored; only docs/charts/ is tracked.

# Check that every ```python block in the docs actually runs
uv run poe docs:snippets

# Audit public-API documentation coverage
uv run poe docs:check

# Both gates also cover skills/kerykeion (the AI Agent Skill). Skill blocks
# always run standalone — no import prelude, no shared page context — even in
# the default docs:snippets run. Focused version:
uv run poe docs:snippets:skill

# Regenerate the README's showcase charts (docs/charts/)
uv run poe regenerate:docs-charts
```

#### Documentation gates

`poe docs:check` fails on an export in `kerykeion.__all__` that no user-facing
page documents. `poe docs:snippets` executes every ` ```python ` block in every
Markdown file in the repository; `poe docs:snippets:skill` is the focused run
over `skills/kerykeion/` alone. `poe regenerate:docs-charts` rewrites
`docs/charts/` — the SVGs the README embeds **by raw URL**, so they must be
regenerated whenever the chart renderer changes or the README shows charts the
library no longer draws.

### No CI — every gate is local

This project deliberately runs **no** GitHub Actions. `.github/` holds only
`FUNDING.yml`. Every gate lives in `pyproject.toml` as a poe task and is run
locally before a push or a release: `poe check`, `poe quality`, `poe test:core`,
`poe docs:check`, `poe docs:snippets`, `poe build:smoke`. Do not add a workflow
file.

## 📁 Project Structure

```
kerykeion/
├── kerykeion/                   # Main package — every module below is a package
│   ├── __init__.py              # Public API exports (__all__)
│   ├── aspects/                 # Natal, synastry and transit aspect detection
│   ├── astro_cartography/       # Astro-cartography (ACG) lines
│   ├── astrological_subject/    # AstrologicalSubjectFactory — the core subject
│   ├── chart_data/              # ChartDataFactory — chart models with aspects and distributions
│   ├── charts/                  # SVG chart rendering (natal, synastry, transit, composite, return)
│   ├── composite_subject/       # Composite (midpoint) and Davison charts
│   ├── context/                 # Serialization of the models into semantic XML for AI consumption
│   ├── dignities/               # Essential dignities for traditional evaluation
│   ├── dominants/               # Planet/sign/element/quality scoring
│   ├── eclipses/                # Localized solar and lunar eclipse search
│   ├── ephemeris_backend/       # Backend selection (libephemeris/swisseph) and the ephemeris lock
│   ├── ephemeris_data/          # EphemerisDataFactory — time-series ephemeris
│   ├── firdaria/                # Firdaria (Firdariyyat), the Persian time-lord technique
│   ├── fixed_stars/             # Dynamic fixed-star discovery and catalog
│   ├── geonames/                # GeoNames city/timezone lookup (the only networked module)
│   ├── heliacal/                # Heliacal risings and settings
│   ├── horary/                  # Horary significators and considerations before judgment
│   ├── house_comparison/        # Bidirectional synastry house overlay
│   ├── lunations/               # New/quarter/full moon moments over a range
│   ├── midpoints/               # Cosmobiology midpoints
│   ├── moon_phase_details/      # Lunar phase context and upcoming phases
│   ├── motion/                  # Per-point motion state (retrograde, stationary, slow, fast)
│   ├── mundane_aspects/         # Exact transiting-to-transiting aspects
│   ├── occultations/            # Lunar occultations
│   ├── planetary_hours/         # Chaldean planetary hours
│   ├── planetary_nodes/         # Planetary nodes and apsides
│   ├── planetary_phenomena/     # Elongation, phase, station and other observational data
│   ├── planetary_returns/       # Solar and lunar returns
│   ├── predictive/              # Shared helpers for the predictive techniques
│   ├── primary_directions/      # Placidus semi-arc primary directions
│   ├── profections/             # Annual profections, the Hellenistic year-lord technique
│   ├── receptions/              # Mutual receptions between classical planets
│   ├── relationship_score/      # Compatibility scoring (Ciro Discepolo method)
│   ├── relocated_chart/         # Relocated charts: natal positions, recomputed houses
│   ├── report/                  # Plain-text reports
│   ├── retrograde_stations/     # Retrograde/direct stations and retrograde spans
│   ├── schemas/                 # Canonical home of all public models, literals and settings
│   ├── secondary_progressions/  # Secondary progressions and solar arc
│   ├── settings/                # Global configuration, chart defaults, translations
│   ├── sign_ingresses/          # Zodiac sign-boundary crossings and sign stays
│   ├── sun_times/               # Sunrise, sunset, solar noon and the twilights
│   ├── swisseph_setup/          # Fetches the Swiss Ephemeris data files (optional backend)
│   ├── transits/                # TransitsTimeRangeFactory — transits over a period
│   ├── utilities/               # Zodiac/house lookups, Julian-day and angle math, tz resolution
│   ├── vedic/                   # Nakshatra calculations
│   ├── void_of_course_moon/     # Void-of-course Moon state and windows
│   └── zodiacal_releasing/      # Zodiacal releasing (aphesis) time-lord periods
├── tests/core/                  # Test suite (102 files — see TEST.md)
├── tests/data/, tests/fixtures/ # Golden baselines: SVGs, positions, aspects, report snapshots
├── examples/                    # Runnable usage examples (see examples/README.md)
├── scripts/                     # Developer tooling and gates (see scripts/README.md)
├── site/docs/                   # Documentation source (markdown)
├── skills/kerykeion/            # Cross-platform AI Agent Skill (agentskills.io)
├── release_notes/               # Selective longer release notes
├── docs/charts/                 # The README's showcase SVGs (regenerate:docs-charts)
├── pyproject.toml               # Project configuration and every poe task
├── uv.lock                      # Dependency lock file
└── README.md
```

## 🔧 Adding Dependencies

### Production Dependencies
```bash
# Add a new dependency
uv add requests

# Add with specific version
uv add "pydantic>=2.0.0"
```

### Development Dependencies
```bash
# Add development dependency
uv add --group dev pytest-mock

# Add to specific group
uv add --group test pytest-benchmark
```

## 🌟 Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code following the existing style
   - Add tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run tests
   uv run poe test:core
   
   # Check code style
   uv run poe format
   uv run poe analyze
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Go to GitHub and create a PR
   - Run the quality checks locally (`poe quality`, `poe test:core`) before opening the PR

## 🐛 Debugging

### Running Python Scripts
```bash
# Run any Python script with the project environment
uv run python your_script.py

# Start interactive Python with all dependencies
uv run python
```

### Common Issues

**Issue: Import errors**
```bash
# Make sure you're using uv run
uv run python -c "import kerykeion"
```

**Issue: Dependencies not found**
```bash
# Resync dependencies
uv sync --dev
```

**Issue: Tests failing**
```bash
# Run the fast tier with verbose output. Prefer this over a bare `uv run pytest`:
# `-m 'not online'` is NOT in addopts, so a plain run also fires the GeoNames
# network tests and fails without an account.
uv run poe test:core -v

# Or, if you want pytest directly, deselect the online tests yourself
uv run pytest tests/core -m 'not online' -v

# Run a specific test with debugging (tests live under tests/core/)
uv run pytest tests/core/test_aspects.py -s -vvv
```

## 📊 Code Style Guidelines

- **Line length**: 120 characters (configured in Ruff)
- **Type hints**: Required for public APIs
- **Docstrings**: Use Google style for all public functions
- **Testing**: Aim for >90% code coverage

### Example Function
```python
def calculate_aspect(planet1: Planet, planet2: Planet) -> AspectData:
    """Calculate the aspect between two planets.
    
    Args:
        planet1: The first planet
        planet2: The second planet
        
    Returns:
        AspectData containing the calculated aspect information
        
    Raises:
        ValueError: If planets are invalid
    """
    # Implementation here
    pass
```

## 🤝 Contributing

1. Check the [Issues](https://github.com/g-battaglia/kerykeion/issues) for open tasks
2. Look for issues labeled `good first issue` if you're new
3. Comment on an issue before starting work
4. Follow the development workflow above
5. Be patient and responsive during code review

## 📞 Getting Help

- **Documentation**: [kerykeion.net](https://www.kerykeion.net/)
- **Issues**: [GitHub Issues](https://github.com/g-battaglia/kerykeion/issues)
- **Discussions**: [GitHub Discussions](https://github.com/g-battaglia/kerykeion/discussions)

## 🔄 Updating Dependencies

```bash
# Update all dependencies to latest compatible versions
uv sync --upgrade

# Update specific dependency
uv add "requests>=2.32.0" --upgrade

# Check for outdated dependencies
uv tree --outdated
```

## 🏗️ Building the Package

```bash
# Build wheel and source distribution
uv build

# The built packages will be in the dist/ folder

# Release gate: build, install the wheel in isolation, and render a chart
uv run poe build:smoke
```

---

**Happy coding! 🚀** If you encounter any issues with this setup, please open an issue on GitHub.
