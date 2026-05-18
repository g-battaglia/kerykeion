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
# Core tests (fastest, ~1750+ tests, excludes heavy parametrized suites)
uv run poe test:core

# Base tier (DE440s range: 1849-2150)
uv run poe test:base

# Medium tier (DE440 range: 1550-2650)
uv run poe test:medium

# Extended tier (DE441 full range)
uv run poe test:extended

# All tests including online (GeoNames API)
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

# Run all quality checks (lint + typecheck)
uv run poe quality
```

### Documentation
```bash
# Generate documentation
uv run poe docs

# The docs will be generated in the ./docs folder
# Open docs/index.html in your browser to view them
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
│   ├── eclipses/                    # Eclipse search
│   ├── fixed_stars/                 # Dynamic star discovery
│   ├── heliacal/                    # Heliacal risings/settings
│   ├── house_comparison/            # Synastry house overlay
│   ├── midpoints/                   # Cosmobiology midpoints
│   ├── moon_phase_details/          # Lunar phase context
│   ├── occultations/                # Lunar occultations
│   ├── planetary_nodes/             # Nodes & apsides
│   ├── planetary_phenomena/         # Elongation/station/etc
│   ├── primary_directions/          # Placidus semi-arc
│   ├── schemas/                     # Pydantic models & types
│   ├── secondary_progressions/      # Progressions & solar arc
│   ├── settings/                    # Configuration & constants
│   └── vedic/                       # Nakshatra support
├── tests/core/                      # Test suite (59+ files)
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
   - Ensure all CI checks pass

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
uv tree
```

## 🏗️ Building the Package

```bash
# Build wheel and source distribution
uv build

# The built packages will be in the dist/ folder
```

---

**Happy coding! 🚀** If you encounter any issues with this setup, please open an issue on GitHub.
