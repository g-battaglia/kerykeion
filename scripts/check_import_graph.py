#!/usr/bin/env python3
"""Structural import gate for the kerykeion package.

Static type checking only covers `kerykeion/` (mypy `files`, pyright `include`),
so nothing validates the ~800 module paths written in `tests/`, `scripts/` and
`examples/` — nor the ones written *inside strings*, which is exactly where a
package reshuffle breaks things without raising ImportError.

Four modes, each targeting a failure that the normal gates cannot see:

--paths          every `kerykeion.*` module path, whether written as an import
                 or as a string constant, actually resolves.
--patch-targets  no `mock.patch` / `monkeypatch.setattr` target sets an attribute
                 on a *package*. When `foo.py` becomes `foo/`, patching
                 "kerykeion.foo.Thing" still succeeds but the code under test
                 reads `kerykeion.foo.impl.Thing`, so the patch silently no-ops.
--loggers        every `logger=` string in the tests names a logger that some
                 module actually registers. `caplog.at_level(logger="pkg")` keeps
                 capturing through the hierarchy after a move, so a stale name
                 leaves a decorative filter and a test that proves nothing.
--fresh-imports  each module imports on its own in a cold interpreter. pytest,
                 mypy and pkgutil.walk_packages always import `kerykeion/__init__`
                 first, so they can never see a cycle that is only reachable
                 leaf-first.

Usage:
    uv run python scripts/check_import_graph.py --all
"""

from __future__ import annotations

import argparse
import ast
import importlib
import importlib.util
import logging
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = REPO_ROOT / "kerykeion"
SCAN_ROOTS = ("kerykeion", "tests", "scripts", "examples")

MODULE_PATH_RE = re.compile(r"^kerykeion(\.[A-Za-z_]\w*)+$")
PATCH_FUNCS = {"patch", "setattr", "patch.object"}

# "kerykeion.net" is the docs domain, not a module path.
DOMAIN_SUFFIXES = {"net", "com", "org", "io", "dev", "app"}


@dataclass
class Problem:
    where: str
    detail: str


@dataclass
class Report:
    checked: int = 0
    problems: list[Problem] = field(default_factory=list)

    def fail(self, where: str, detail: str) -> None:
        self.problems.append(Problem(where, detail))


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        files.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(files)


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def module_exists(dotted: str) -> bool:
    try:
        return importlib.util.find_spec(dotted) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def safe_hasattr(obj, name: str) -> bool:
    """hasattr() that tolerates kerykeion's migration __getattr__.

    `kerykeion/__init__.py` deliberately raises ImportError (not AttributeError)
    for the removed v5 names, so plain hasattr() propagates instead of returning
    False. Here a raised ImportError means "reachable name with a helpful error",
    which for this gate counts as present.
    """
    try:
        getattr(obj, name)
    except AttributeError:
        return False
    except ImportError:
        return True
    return True


def resolve_dotted(dotted: str):
    """Resolve a dotted path to (object, longest importable module prefix).

    Walks the longest importable prefix, then getattr()s the remainder.
    Raises AttributeError / ImportError when the path does not resolve.
    """
    parts = dotted.split(".")
    module = None
    module_name = ""
    for stop in range(len(parts), 0, -1):
        candidate = ".".join(parts[:stop])
        if module_exists(candidate):
            module = importlib.import_module(candidate)
            module_name = candidate
            break
    if module is None:
        raise ImportError(f"no importable prefix in {dotted!r}")

    obj = module
    for attr in parts[len(module_name.split(".")) :]:
        obj = getattr(obj, attr)
    return obj, module_name


# --------------------------------------------------------------------------- #
# --paths
# --------------------------------------------------------------------------- #
def check_paths(report: Report) -> None:
    for path in iter_python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            report.fail(rel(path), f"syntax error: {exc}")
            continue

        for node in ast.walk(tree):
            # `from kerykeion.x.y import A, B`
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                if node.module != "kerykeion" and not node.module.startswith("kerykeion."):
                    continue
                report.checked += 1
                where = f"{rel(path)}:{node.lineno}"
                if not module_exists(node.module):
                    report.fail(where, f"module not found: {node.module}")
                    continue
                module = importlib.import_module(node.module)
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    if not safe_hasattr(module, alias.name) and not module_exists(
                        f"{node.module}.{alias.name}"
                    ):
                        report.fail(where, f"{node.module} has no {alias.name!r}")

            # `import kerykeion.x.y`
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name != "kerykeion" and not alias.name.startswith("kerykeion."):
                        continue
                    report.checked += 1
                    if not module_exists(alias.name):
                        report.fail(f"{rel(path)}:{node.lineno}", f"module not found: {alias.name}")

            # bare string constants that look like module paths
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                dotted = node.value
                if not MODULE_PATH_RE.match(dotted):
                    continue
                if dotted.split(".")[1] in DOMAIN_SUFFIXES:
                    continue
                report.checked += 1
                where = f"{rel(path)}:{node.lineno}"
                try:
                    resolve_dotted(dotted)
                except (ImportError, AttributeError) as exc:
                    report.fail(where, f"string path does not resolve: {dotted!r} ({exc})")


# --------------------------------------------------------------------------- #
# --patch-targets
# --------------------------------------------------------------------------- #
def _callee_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Attribute):
            return f"{func.value.attr}.{func.attr}"
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return ""


def _module_aliases(tree: ast.AST) -> dict[str, str]:
    """Local name -> kerykeion module path, for module objects bound by import.

    `monkeypatch.setattr(eb, "name", ...)` passes the module *object*, so the
    string scan below cannot see it. Resolving the alias catches the same
    silent no-op when `eb` turns out to be a package.
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("kerykeion") and alias.asname:
                    aliases[alias.asname] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            if node.module != "kerykeion" and not node.module.startswith("kerykeion."):
                continue
            for alias in node.names:
                candidate = f"{node.module}.{alias.name}"
                if module_exists(candidate):
                    aliases[alias.asname or alias.name] = candidate
    return aliases


def check_patch_targets(report: Report) -> None:
    for path in iter_python_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue

        aliases = _module_aliases(tree)

        # setattr(<module alias>, "attr", ...) — the object form
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _callee_name(node) not in PATCH_FUNCS:
                continue
            if len(node.args) < 2 or not isinstance(node.args[0], ast.Name):
                continue
            dotted = aliases.get(node.args[0].id)
            if dotted is None:
                continue
            report.checked += 1
            module = importlib.import_module(dotted)
            if getattr(module, "__path__", None) is not None:
                report.fail(
                    f"{rel(path)}:{node.lineno}",
                    f"patch target sets an attribute on the PACKAGE {dotted!r} — "
                    "this is a silent no-op; bind the alias to the defining submodule",
                )

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _callee_name(node) not in PATCH_FUNCS:
                continue
            if not node.args or not isinstance(node.args[0], ast.Constant):
                continue
            target = node.args[0].value
            if not isinstance(target, str) or not target.startswith("kerykeion."):
                continue

            report.checked += 1
            where = f"{rel(path)}:{node.lineno}"
            holder_path, _, attr = target.rpartition(".")
            try:
                holder, _ = resolve_dotted(holder_path)
            except (ImportError, AttributeError) as exc:
                report.fail(where, f"patch holder does not resolve: {holder_path!r} ({exc})")
                continue

            if not hasattr(holder, attr):
                report.fail(where, f"patch target has no attribute {attr!r}: {target}")
                continue

            # The silent one: patching an attribute *on a kerykeion package* that the
            # package merely re-exports rebinds only the package namespace, while the
            # code under test keeps reading the defining submodule's own binding.
            #
            # Restricted to kerykeion packages on purpose. Targets like
            # "kerykeion.eclipses.factory.ephe.sol_eclipse_when_loc" resolve their
            # holder to the *libephemeris module object* that the factory holds a
            # reference to — patching an attribute there mutates the very object the
            # code calls through, so those keep working and are not flagged.
            holder_name = getattr(holder, "__name__", "")
            if getattr(holder, "__path__", None) is not None and holder_name.startswith("kerykeion"):
                report.fail(
                    where,
                    f"patch target sets {attr!r} on the PACKAGE {holder_path!r} — "
                    "this is a silent no-op; point it at the defining submodule",
                )


# --------------------------------------------------------------------------- #
# --loggers
# --------------------------------------------------------------------------- #
def registered_logger_names() -> set[str]:
    """Module names that call logging.getLogger(__name__ / __package__)."""
    names = {"kerykeion"}
    for path in PACKAGE_ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue
        rel_parts = path.relative_to(PACKAGE_ROOT).with_suffix("").parts
        module_name = "kerykeion." + ".".join(rel_parts)
        package_name = module_name.rsplit(".", 1)[0]
        if rel_parts[-1] == "__init__":
            module_name = package_name

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or _callee_name(node) != "getLogger":
                continue
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id == "__name__":
                    names.add(module_name)
                elif isinstance(arg, ast.Name) and arg.id == "__package__":
                    names.add(package_name)
                elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    names.add(arg.value)
    return names


def check_loggers(report: Report) -> None:
    known = registered_logger_names()
    tests_root = REPO_ROOT / "tests"
    if not tests_root.is_dir():
        return

    for path in sorted(tests_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            candidates: list[tuple[int, str]] = []

            # caplog.at_level(..., logger="kerykeion.x")
            if isinstance(node, ast.Call):
                for kw in node.keywords:
                    if (
                        kw.arg == "logger"
                        and isinstance(kw.value, ast.Constant)
                        and isinstance(kw.value.value, str)
                        and kw.value.value.startswith("kerykeion")
                    ):
                        candidates.append((node.lineno, kw.value.value))

            # record.name == "kerykeion.x"
            elif isinstance(node, ast.Compare) and isinstance(node.left, ast.Attribute):
                if node.left.attr == "name":
                    for comparator in node.comparators:
                        if (
                            isinstance(comparator, ast.Constant)
                            and isinstance(comparator.value, str)
                            and comparator.value.startswith("kerykeion")
                        ):
                            candidates.append((node.lineno, comparator.value))

            for lineno, name in candidates:
                report.checked += 1
                if name not in known:
                    report.fail(
                        f"{rel(path)}:{lineno}",
                        f"logger name {name!r} is not registered by any module "
                        "(the filter still captures via the hierarchy, so this "
                        "test would pass while checking nothing)",
                    )


# --------------------------------------------------------------------------- #
# --fresh-imports
# --------------------------------------------------------------------------- #
def check_fresh_imports(report: Report) -> None:
    modules: list[str] = []
    for path in sorted(PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        parts = path.relative_to(PACKAGE_ROOT).with_suffix("").parts
        if parts[-1] == "__main__":
            continue  # importing __main__ would run the CLI
        if parts[-1] == "__init__":
            parts = parts[:-1]
        modules.append(".".join(("kerykeion", *parts)))

    # A plain `import kerykeion.foo` executes kerykeion/__init__.py first, and that
    # initializer eagerly imports most of the package — so every probe would start
    # from the same fully-warmed state as the test suite, and leaf-first ordering
    # would never actually be exercised.
    #
    # Instead, seed sys.modules with a stub root carrying only __path__. Submodules
    # then resolve normally while the real root initializer never runs, so each
    # module is imported genuinely leaf-first. A module that only works because
    # __init__ happened to import its dependencies first fails here, which is the
    # entire point. A top-level `from kerykeion import X` would fail here too — and
    # should, since that is the import shape that made the tree order-dependent.
    _PROBE = """
import sys, types, importlib
root = types.ModuleType("kerykeion")
root.__path__ = [{package_root!r}]
sys.modules["kerykeion"] = root
importlib.import_module({name!r})
"""

    def probe(name: str) -> tuple[str, int, str]:
        proc = subprocess.run(
            [sys.executable, "-c", _PROBE.format(package_root=str(PACKAGE_ROOT), name=name)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=120,
        )
        return name, proc.returncode, proc.stderr

    with ThreadPoolExecutor(max_workers=8) as pool:
        for name, code, stderr in pool.map(probe, sorted(set(modules))):
            report.checked += 1
            if code != 0:
                last = stderr.strip().splitlines()[-1] if stderr.strip() else "unknown error"
                report.fail(name, f"cold import failed: {last}")


# --------------------------------------------------------------------------- #
MODES = {
    "paths": check_paths,
    "patch-targets": check_patch_targets,
    "loggers": check_loggers,
    "fresh-imports": check_fresh_imports,
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for mode in MODES:
        parser.add_argument(f"--{mode}", action="store_true")
    parser.add_argument("--all", action="store_true", help="run every mode")
    args = parser.parse_args()

    selected = [m for m in MODES if getattr(args, m.replace("-", "_"))]
    if args.all or not selected:
        selected = list(MODES)

    logging.disable(logging.CRITICAL)
    failed = False
    for mode in selected:
        report = Report()
        MODES[mode](report)
        if report.problems:
            failed = True
            print(f"\n{mode}: {len(report.problems)} problem(s) in {report.checked} checked")
            for problem in report.problems:
                print(f"  {problem.where}: {problem.detail}")
        else:
            print(f"{mode}: OK ({report.checked} checked)")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
