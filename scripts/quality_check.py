"""Quality check script for kerykeion project."""
import subprocess
import sys


def run_check(name: str, command: list[str]) -> bool:
    """Run a check command and return True if successful."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )
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
        ("analize", ["mypy"]),
        ("test", ["pytest", "--tb=no", "-q"]),
    ]
    
    results = []
    for name, command in checks:
        results.append(run_check(name, command))
    
    # Return 0 if all checks passed, 1 otherwise
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
