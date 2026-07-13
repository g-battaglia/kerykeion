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
# Core tests (fastest, ~4,600 tests, excludes heavy parametrized suites)
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
```

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
```

## 📁 Project Structure

```
kerykeion/
├── kerykeion/                       # Main package
│   ├── __init__.py                  # Public API exports
│   ├── astrological_subject_factory.py  # Core subject creation
│   ├── chart_data_factory.py        # Chart data computation
│   ├── composite_subject_factory.py # Composite/Davison charts
│   ├── ephemeris_backend.py         # Backend abstraction (libephemeris/swisseph)
│   ├── ephemeris_data_factory.py    # Time-series ephemeris
│   ├── planetary_return_factory.py  # Solar/Lunar returns
│   ├── relationship_score_factory.py # Compatibility scoring
│   ├── relocated_chart_factory.py   # Relocated charts
│   ├── transits_time_range_factory.py # Transit tracking
│   ├── context_serializer.py        # AI/LLM XML export
│   ├── report.py                    # Text reports
│   ├── utilities.py                 # Zodiac math helpers
│   ├── aspects/                     # Aspect detection
│   ├── astro_cartography/           # ACG lines
│   ├── charts/                      # SVG chart rendering
│   ├── dignities/                   # Essential dignities
│   ├── dominants/                   # Planet/sign/element/quality scoring
│   ├── eclipses/                    # Eclipse search
│   ├── fixed_stars/                 # Dynamic star discovery
│   ├── heliacal/                    # Heliacal risings/settings
│   ├── house_comparison/            # Synastry house overlay
│   ├── lunations/                   # Lunar phase event search
│   ├── midpoints/                   # Cosmobiology midpoints
│   ├── moon_phase_details/          # Lunar phase context
│   ├── mundane_aspects/             # Exact transiting aspects
│   ├── occultations/                # Lunar occultations
│   ├── planetary_hours/             # Chaldean planetary hours
│   ├── planetary_nodes/             # Nodes & apsides
│   ├── planetary_phenomena/         # Elongation/station/etc
│   ├── primary_directions/          # Placidus semi-arc
│   ├── retrograde_stations/         # Retrograde/direct station search
│   ├── schemas/                     # Pydantic models & types
│   ├── secondary_progressions/      # Progressions & solar arc
│   ├── settings/                    # Configuration & constants
│   ├── sign_ingresses/              # Zodiac sign-boundary search
│   ├── sun_times/                   # Sunrise/sunset/twilight
│   ├── vedic/                       # Nakshatra support
│   ├── void_of_course_moon/         # Void-of-course state/windows
│   └── zodiacal_releasing/          # Hellenistic time-lord periods
├── tests/core/                      # Test suite (74 files)
├── examples/                        # Usage examples
├── site/docs/                       # Documentation source (markdown)
├── release_notes/                   # Per-version release notes
├── pyproject.toml                   # Project configuration
├── uv.lock                          # Dependency lock file
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
# Run tests with verbose output
uv run pytest -v

# Run specific test with debugging
uv run pytest tests/test_specific.py -s -vvv
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

# CI/release gate: build, install the wheel in isolation, and render a chart
uv run poe build:smoke
```

---

**Happy coding! 🚀** If you encounter any issues with this setup, please open an issue on GitHub.
