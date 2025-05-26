"""
Genealogy Core Package

This package provides core functionality for processing genealogical data,
including reading obituaries, extracting names and relationships, and managing
obituary catalogs.
"""

from .obituary_reader import ObituaryReader
from .people_finder import PeopleFinder
from .obituary_catalog import ObituaryCatalog
from .date_normalizer import DateNormalizer

__all__ = [
    'ObituaryReader',
    'PeopleFinder',
    'ObituaryCatalog',
    'DateNormalizer'
] 