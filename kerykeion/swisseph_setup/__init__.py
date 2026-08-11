# -*- coding: utf-8 -*-
"""
Swiss Ephemeris Setup

Downloader for the Swiss Ephemeris data files required by the ``swisseph``
backend. Kerykeion never ships those files: they are AGPL-licensed and must
be fetched deliberately, after accepting the license terms.

Usually invoked as a CLI rather than imported:

    python -m kerykeion.swisseph_setup

The main entry points are:
    - download_swisseph_data
    - main
"""

from .download import download_swisseph_data, main

__all__ = ["download_swisseph_data", "main"]
