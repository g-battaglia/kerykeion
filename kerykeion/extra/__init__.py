# -*- coding: utf-8 -*-
"""Optional extras — subpackages that need an optional dependency group.

Nothing here is imported by the library: ``import kerykeion`` never reaches
this package, and each subpackage guards its own optional imports. Today it
holds :mod:`kerykeion.extra.cli`, the command-line interface behind the
``kerykeion[cli]`` extra.
"""
