"""Published metadata must upgrade affected HTTP dependencies, not just the lock."""

from importlib.metadata import requires, version

from packaging.requirements import Requirement
from packaging.version import Version
import pytest


@pytest.mark.parametrize(
    ("package", "affected", "fixed"),
    [("certifi", "2026.1.4", "2026.10.18"), ("urllib3", "2.7.0", "2.8.0")],
)
def test_installed_metadata_requires_patched_http_dependencies(package, affected, fixed):
    """An already-installed vulnerable transitive dependency must not satisfy us."""
    requirements = [Requirement(value) for value in requires("kerykeion")]
    dependency = next(item for item in requirements if item.name == package)
    assert Version(affected) not in dependency.specifier
    assert Version(fixed) in dependency.specifier
    assert Version(version(package)) >= Version(fixed)
