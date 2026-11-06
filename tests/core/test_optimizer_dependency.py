"""Existing unoptimized installations must not satisfy the final beta contract."""
from importlib.metadata import requires

from packaging.requirements import Requirement
from packaging.version import Version


def test_installed_package_requires_the_qualified_optimizer_fix():
    """Make ordinary dependency resolution upgrade an existing 1.0.0 optimizer."""
    requirements = [Requirement(value) for value in requires('kerykeion')]
    optimizer = next(value for value in requirements if value.name.replace('_', '-') == 'svg-polish')
    assert Version('1.0.0') not in optimizer.specifier
    assert Version('1.0.1') in optimizer.specifier
