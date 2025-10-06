# Personal Workspace

This directory is designed as a **personal workspace** for developers and users who want to experiment with Kerykeion, create custom scripts, or test features without cluttering the main repository.

## Purpose

- **Experimentation**: Test new features, create prototypes, or debug issues
- **Custom Scripts**: Write your own astrological calculations and analysis tools
- **Learning**: Practice using Kerykeion's API with your own examples
- **Local Development**: Keep work-in-progress code separate from the core library

## Git Behavior

By default, **all files in this directory are ignored by Git** (except this `README.md` and `main.py`).

This means:
- ✅ You can create any files you want here without worrying about accidentally committing them
- ✅ Your personal scripts and data stay private
- ✅ The directory structure remains clean for everyone

### Want to Version Your Workspace?

If you'd like to track your workspace files in **your own fork**, you can modify `.gitignore`:

**Option 1: Track all workspace files**
```bash
# Remove or comment out these lines in .gitignore:
# workspace/*
# !workspace/README.md
# !workspace/main.py
```

**Option 2: Track specific files only**
```bash
# Add this to .gitignore to track only .py files:
!workspace/*.py
!workspace/**/*.py
```

## Getting Started

1. **Edit `main.py`**: Start with the template provided in `main.py`
2. **Create new files**: Add as many Python scripts as you need
3. **Organize**: Create subdirectories for different projects or experiments
4. **Import Kerykeion**: All Kerykeion modules are available for import

## Example Usage

```python
# workspace/my_chart.py
from kerykeion import AstrologicalSubjectFactory, ChartDataFactory, ChartDrawer

# Create your natal chart
subject = AstrologicalSubjectFactory.from_birth_data(
    "Your Name", 1990, 1, 1, 12, 0, "London", "GB"
)

chart_data = ChartDataFactory.create_natal_chart_data(subject)
drawer = ChartDrawer(chart_data=chart_data)
drawer.save_svg()

print(f"Chart saved for {subject.name}")
```

## Suggested Structure

```
workspace/
├── README.md           # This file
├── main.py            # Quick starter template
├── experiments/       # Test new features
├── scripts/           # Utility scripts
├── data/              # Store JSON, CSV, or other data files
└── output/            # Generated charts and reports
```

## Tips

- **Run from repository root**: `python workspace/main.py`
- **Use relative imports**: Import from kerykeion normally
- **Share discoveries**: If you create something useful, consider contributing to Kerykeion!
- **Ask questions**: Use [GitHub Discussions](https://github.com/g-battaglia/kerykeion/discussions) for help

## Need Help?

- 📖 Documentation: [kerykeion.readthedocs.io](https://kerykeion.readthedocs.io)
- 💬 Discussions: [GitHub Discussions](https://github.com/g-battaglia/kerykeion/discussions)
- 🐛 Issues: [GitHub Issues](https://github.com/g-battaglia/kerykeion/issues)
- 📧 Email: [kerykeion.astrology@gmail.com](mailto:kerykeion.astrology@gmail.com)

---

**Happy coding! ✨**
