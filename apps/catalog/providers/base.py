"""
Base Metadata Provider Interface & Data Normalization Containers for DreamTeal.

Defines:
- DiscoveryMode: Standardized discovery feeds (Latest, Popular, Trending, Upcoming).
- NormalizedSearchResult: Common representation for candidate search & discovery results.
- NormalizedMediaDetail: Complete standardized metadata payload for catalog creation/update.
- BaseMetadataProvider: Extensible abstract base class for all third-party provider adapters.

STRICT ZERO-STAR RULE:
These structures deliberately omit any star rating, score, points, or numeric review attributes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Dict, List, Optional


class DiscoveryMode:
    """Standardized semantics for discovery feeds across all media categories."""
    LATEST = 'latest'        # Real new releases / currently in theatres / airing
    POPULAR = 'popular'      # High all-time / sustained engagement
    TRENDING = 'trending'    # Rapid momentum / high recent discussion
    UPCOMING = 'upcoming'    # Unreleased / scheduled for future release

    ALL = (LATEST, POPULAR, TRENDING, UPCOMING)


@dataclass
class NormalizedSearchResult:
    """
    Standardized lightweight candidate search/discovery item.
    Enables frontend to render identical media cards regardless of source provider.
    """
    provider: str
    external_id: str
    title: str
    media_type: str  # 'MOVIE', 'SERIES', 'MANGA', 'GAME'
    release_year: Optional[int] = None
    poster_url: str = ''
    backdrop_url: str = ''
    synopsis: str = ''
    genres: List[str] = field(default_factory=list)
    is_imported: bool = False
    slug: Optional[str] = None
    external_url: str = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'provider': self.provider,
            'external_id': self.external_id,
            'title': self.title,
            'media_type': self.media_type,
            'release_year': self.release_year,
            'poster_url': self.poster_url,
            'backdrop_url': self.backdrop_url,
            'synopsis': self.synopsis,
            'genres': self.genres,
            'is_imported': self.is_imported,
            'slug': self.slug,
            'external_url': self.external_url,
        }


@dataclass
class NormalizedMediaDetail:
    """
    Complete standardized payload used by the catalog service to create or
    update DreamTeal MediaItem and category-specific extension models.
    """
    provider: str
    external_id: str
    external_url: str
    title: str
    media_type: str  # 'MOVIE', 'SERIES', 'MANGA', 'GAME'
    slug_candidate: str
    release_year: Optional[int] = None
    synopsis: str = ''
    poster_url: str = ''
    backdrop_url: str = ''
    genres: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    alternative_titles: List[str] = field(default_factory=list)

    # Cross-provider bridge (e.g. AniList exposes MAL ID)
    id_mal: Optional[str] = None

    # Movie-specific
    director: str = ''
    runtime_minutes: Optional[int] = None
    studio: str = ''
    ott_providers: List[str] = field(default_factory=list)

    # Series-specific
    creators: str = ''
    total_seasons: int = 1
    total_episodes: Optional[int] = None
    series_status: str = 'AIRING'  # 'AIRING', 'ENDED', 'CANCELLED'

    # Manga-specific
    author: str = ''
    artist: str = ''
    manga_type: str = 'MANGA'  # 'MANGA', 'MANHWA', 'MANHUA', 'WEBTOON'
    publication_status: str = 'PUBLISHING'  # 'PUBLISHING', 'FINISHED', 'HIATUS'
    total_chapters: Optional[int] = None

    # Game-specific
    developer: str = ''
    publisher: str = ''
    platforms: List[str] = field(default_factory=list)
    average_story_hours: Optional[Decimal] = None


class BaseMetadataProvider(ABC):
    """
    Abstract adapter for third-party pop-culture metadata providers.
    Every provider must implement normalization to DreamTeal's schemas.
    """

    provider_key: str = ''
    display_name: str = ''

    # Capabilities matrix indicating genuine provider support
    capabilities: Dict[str, bool] = {
        'search': True,
        'details': True,
        'latest': False,
        'popular': False,
        'trending': False,
        'upcoming': False,
    }

    @abstractmethod
    def search(self, query: str, limit: int = 20) -> List[NormalizedSearchResult]:
        """Search the external provider and return normalized results."""
        pass

    @abstractmethod
    def get_details(self, external_id: str) -> Optional[NormalizedMediaDetail]:
        """Fetch full details for an external ID and return normalized payload."""
        pass

    @abstractmethod
    def get_external_url(self, external_id: str) -> str:
        """Construct the canonical direct link on the provider's platform."""
        pass

    def discover(self, media_type: str, mode: str = DiscoveryMode.POPULAR, limit: int = 20) -> List[NormalizedSearchResult]:
        """
        Dispatches discovery requests according to semantic mode.
        Falls back gracefully if the provider lacks a specific native mode.
        """
        mode = mode.lower()
        if mode == DiscoveryMode.LATEST:
            return self.discover_latest(media_type, limit=limit)
        elif mode == DiscoveryMode.TRENDING:
            return self.discover_trending(media_type, limit=limit)
        elif mode == DiscoveryMode.UPCOMING:
            return self.discover_upcoming(media_type, limit=limit)
        else:  # default to POPULAR
            return self.discover_popular(media_type, limit=limit)

    def discover_popular(self, media_type: str, limit: int = 20) -> List[NormalizedSearchResult]:
        """Fetch items with sustained popularity."""
        return []

    def discover_latest(self, media_type: str, limit: int = 20) -> List[NormalizedSearchResult]:
        """Fetch newly released or currently running items."""
        # Default fallback to popular if provider does not support dedicated latest
        return self.discover_popular(media_type, limit=limit)

    def discover_trending(self, media_type: str, limit: int = 20) -> List[NormalizedSearchResult]:
        """Fetch items experiencing rapid recent momentum."""
        # Default fallback to popular if provider does not support dedicated trending
        return self.discover_popular(media_type, limit=limit)

    def discover_upcoming(self, media_type: str, limit: int = 20) -> List[NormalizedSearchResult]:
        """Fetch scheduled/upcoming unreleased items."""
        return []

    def health_check(self) -> bool:
        """Optional health check capability to test provider reachability."""
        return True
