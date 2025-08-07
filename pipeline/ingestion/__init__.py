"""
Nova Corpus Ingestion Module
Handles 24/7 data acquisition from multiple sources
"""

from .engine import IngestionEngine
from .sources import GitHubSource, ArXivSource, HackerNewsSource

__all__ = [
    'IngestionEngine',
    'GitHubSource', 
    'ArXivSource',
    'HackerNewsSource'
]