# -*- coding: utf-8 -*-
"""
    This is part of Kerykeion (C) 2025 Giacomo Battaglia
"""


class KerykeionException(Exception):
    """
    Custom Kerykeion Exception
    """

    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super().__init__(message)
