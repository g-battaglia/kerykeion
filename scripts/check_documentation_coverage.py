#!/usr/bin/env python3
import os
import pkgutil
import importlib
import inspect
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_public_members(module):
    """
    Return a list of (name, object) for all public classes and functions in the module.
    """
    members = []

    # If the module defines __all__, use it
    if hasattr(module, "__all__"):
        for name in module.__all__:
            if hasattr(module, name):
                obj = getattr(module, name)
                members.append((name, obj))
    else:
        # Fallback: inspect module members (less reliable for identifying what is truly "exported")
        for name, obj in inspect.getmembers(module):
            if name.startswith("_"):
                continue
            if inspect.isclass(obj) or inspect.isfunction(obj):
                # Ensure the object is defined in this module or one of its submodules
                # This prevents listing imported externals
                if hasattr(obj, "__module__") and obj.__module__ and obj.__module__.startswith("kerykeion"):
                    members.append((name, obj))

    return members


def scan_package(package_name):
    """
    Recursively scan the package for modules and return a dictionary of {module_name: [members]}.
    """
    package = importlib.import_module(package_name)
    results = {}

    # Helper to process a single module
    def process_module(mod_name):
        try:
            mod = importlib.import_module(mod_name)
            members = get_public_members(mod)
            results[mod_name] = members
        except Exception as e:
            print(f"Error importing {mod_name}: {e}")

    # Walk through the package
    if hasattr(package, "__path__"):
        for _, name, is_pkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            process_module(name)
    else:
        process_module(package_name)

    return results


def load_documentation_content(docs_dir):
    """
    Load all content from markdown files in the docs directory.
    Returns a single string containing all documentation text.
    """
    content = ""
    docs_path = Path(docs_dir)
    for md_file in docs_path.glob("**/*.md"):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content += f.read() + "\n"
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    return content


def main():
    print("Starting Kerykeion Documentation Coverage Audit...")

    # 1. Scan Codebase
    codebase_members = scan_package("kerykeion")

    # 2. Load Documentation
    docs_path = Path(__file__).parent.parent / "site" / "docs"
    if not docs_path.exists():
        print(f"Error: Documentation directory not found at {docs_path}")
        return

    docs_content = load_documentation_content(docs_path)

    # 3. Cross-reference
    missing_items = {}
    documented_count = 0
    total_count = 0

    # Exclude list (things we know we don't document or are implementation details)
    excludes = [
        "settings",  # Module itself
        "schemas",  # Module itself
        "charts",  # Module itself
        "utilities",  # Module itself
        "__init__",
        "kerykeion",
        "print_function",
    ]

    for mod_name, members in codebase_members.items():
        for name, obj in members:
            # Skip if name is in excludes
            if name in excludes:
                continue

            total_count += 1

            # Simple check: is the name present in the docs?
            # A more robust check would look for headers or backticks, but this is a good first pass
            if name in docs_content:
                documented_count += 1
            else:
                if mod_name not in missing_items:
                    missing_items[mod_name] = []
                missing_items[mod_name].append(name)

    # 4. Report
    print(f"\nAudit Complete.")
    print(f"Total Public Items Found: {total_count}")
    print(f"Documented Items: {documented_count}")
    print(f"Coverage: {documented_count / total_count * 100:.1f}%\n")

    if missing_items:
        print("MISSING DOCUMENTATION FOR:")
        print("========================")
        for mod, items in missing_items.items():
            print(f"\nModule: {mod}")
            for item in items:
                print(f"  - {item}")
    else:
        print("All identified public items appear to be documented!")


if __name__ == "__main__":
    main()
