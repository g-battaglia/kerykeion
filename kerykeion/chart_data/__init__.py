# -*- coding: utf-8 -*-
"""
Chart Data

Assembles the complete data structure a chart is drawn from: points,
houses, aspects, distributions and the chart's own metadata.

The main entry point is:
    - ChartDataFactory
"""

from .factory import ChartDataFactory

__all__ = ["ChartDataFactory"]
