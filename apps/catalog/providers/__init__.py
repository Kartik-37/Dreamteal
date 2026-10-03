"""
External Metadata Providers package for DreamTeal.
Exposes BaseMetadataProvider and ProviderRegistry.
"""

from .base import BaseMetadataProvider, NormalizedMediaDetail, NormalizedSearchResult
from .registry import ProviderRegistry, registry

__all__ = [
    'BaseMetadataProvider',
    'NormalizedSearchResult',
    'NormalizedMediaDetail',
    'ProviderRegistry',
    'registry',
]
