"""Quality check script for kerykeion project."""

import subprocess
import sys


def run_check(name: str, command: list[str]) -> bool:
    """Run a check command and return True if successful."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        success = result.returncode == 0
        status = "OK" if success else "KO"
        icon = "✅" if success else "❌"
        print(f"{icon} {name}: {status}")
        return success
    except Exception as e:
        print(f"❌ {name}: KO (error: {e})")
        return False


def main() -> int:
    """Run all quality checks."""
    print("🔍 Running quality checks...")

    checks = [
        ("lint", ["ruff", "check"]),
        ("analyze", ["mypy"]),
        ("typecheck", ["pyright"]),
        # -m "not online": every poe test:* task excludes the network-bound
        # geonames tests, but pytest's addopts do not — without this the local
        # quality gate silently depends on GeoNames being reachable.
        ("test", ["pytest", "--tb=no", "-q", "-m", "not online"]),
        # The CLI is an optional extra; this proves the entry point still works
        # from the dev checkout and that ``import kerykeion`` never imports the CLI.
        ("cli", ["python", "scripts/cli_smoke_check.py"]),
        # The CLI skill's examples are shell, which the python snippet runner
        # and pytest both ignore; without this a broken example would ship
        # verified-by-nothing into third-party repositories.
        ("skill-cli", ["python", "scripts/test_skill_cli_snippets.py"]),
    ]

    results = []
    for name, command in checks:
        results.append(run_check(name, command))

    # Return 0 if all checks passed, 1 otherwise
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
