"""
Jikan (Unofficial MyAnimeList API v4) Fallback Provider Adapter for DreamTeal.
Serves as secondary/fallback provider for Manga and Manhwa metadata.

Strictly complies with DreamTeal Zero-Star Rating Policy:
Does NOT import, normalize, or expose MyAnimeList/Jikan scores or numeric ratings.
Captures alternative titles for cross-provider matching.
"""

import logging
from typing import Any, Dict, List, Optional
import requests
from django.conf import settings
from django.utils.text import slugify

from .base import BaseMetadataProvider, DiscoveryMode, NormalizedMediaDetail, NormalizedSearchResult

logger = logging.getLogger(__name__)


class JikanProvider(BaseMetadataProvider):
    provider_key = 'jikan'
    display_name = 'Jikan (MyAnimeList)'
    base_url = 'https://api.jikan.moe/v4'

    capabilities = {
        'search': True,
        'details': True,
        'popular': True,
        'latest': True,
        'upcoming': True,
        'trending': False,  # Jikan does not provide trending metric; falls back to popular
    }

    def __init__(self):
        self.timeout = getattr(settings, 'PROVIDER_HTTP_TIMEOUT', 8)

    def get_external_url(self, external_id: str) -> str:
        return f"https://myanimelist.net/manga/{external_id}"

    def search(self, query: str, limit: int = 20) -> List[NormalizedSearchResult]:
        if not query.strip():
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/manga",
                params={'q': query, 'limit': min(limit, 25)},
                headers={'User-Agent': 'DreamTeal/1.0'},
                timeout=self.timeout
            )
            if resp.status_code == 200:
                results = []
                data = resp.json().get('data', [])
                for item in data[:limit]:
                    results.append(self._normalize_search_item(item))
                return results
            logger.warning("Jikan search returned status %d", resp.status_code)
            return []
        except requests.RequestException as e:
            logger.error("Jikan search failed: %s", str(e))
            return []

    def _normalize_search_item(self, item: Dict[str, Any]) -> NormalizedSearchResult:
        ext_id = str(item.get('mal_id', ''))
        title = item.get('title_english') or item.get('title', 'Untitled')
        images = item.get('images', {}).get('jpg', {})
        poster_url = images.get('large_image_url') or images.get('image_url', '')

        published_from = item.get('published', {}).get('prop', {}).get('from', {})
        release_year = published_from.get('year')

        genres = [g.get('name') for g in item.get('genres', []) if g.get('name')]

        return NormalizedSearchResult(
            provider=self.provider_key,
            external_id=ext_id,
            title=title,
            media_type='MANGA',
            release_year=release_year,
            poster_url=poster_url,
            synopsis=item.get('synopsis') or '',
            genres=genres,
            external_url=self.get_external_url(ext_id)
        )

    def get_details(self, external_id: str) -> Optional[NormalizedMediaDetail]:
        try:
            resp = requests.get(
                f"{self.base_url}/manga/{external_id}/full",
                headers={'User-Agent': 'DreamTeal/1.0'},
                timeout=self.timeout
            )
            if resp.status_code != 200:
                logger.warning("Jikan get_details returned %d for ID %s", resp.status_code, external_id)
                return None

            data = resp.json().get('data')
            if not data:
                return None

            return self._normalize_detail_payload(data, external_id)
        except requests.RequestException as e:
            logger.error("Jikan get_details failed for ID %s: %s", external_id, str(e))
            return None

    def _normalize_detail_payload(self, data: Dict[str, Any], external_id: str) -> NormalizedMediaDetail:
        title = data.get('title_english') or data.get('title', 'Untitled')
        alt_titles = []
        if data.get('title') and data.get('title') != title:
            alt_titles.append(data.get('title'))
        if data.get('title_japanese'):
            alt_titles.append(data.get('title_japanese'))
        for syn in data.get('titles', []):
            syn_title = syn.get('title')
            if syn_title and syn_title not in alt_titles and syn_title != title:
                alt_titles.append(syn_title)

        published_from = data.get('published', {}).get('prop', {}).get('from', {})
        release_year = published_from.get('year')
        slug_base = f"{slugify(title)}-{release_year}" if release_year else slugify(title)

        images = data.get('images', {}).get('jpg', {})
        poster_url = images.get('large_image_url') or images.get('image_url', '')

        # Type mapping
        raw_type = (data.get('type') or '').upper()
        if raw_type == 'MANHWA':
            manga_type = 'MANHWA'
        elif raw_type == 'MANHUA':
            manga_type = 'MANHUA'
        elif raw_type in ['LIGHT NOVEL', 'NOVEL']:
            manga_type = 'MANGA'
        else:
            manga_type = 'MANGA'

        # Status mapping
        raw_status = (data.get('status') or '').lower()
        if 'finished' in raw_status:
            pub_status = 'FINISHED'
        elif 'hiatus' in raw_status or 'discontinued' in raw_status:
            pub_status = 'HIATUS'
        else:
            pub_status = 'PUBLISHING'

        # Authors
        authors_list = [a.get('name') for a in data.get('authors', []) if a.get('name')]
        author_str = ', '.join(authors_list)

        genres = [g.get('name') for g in data.get('genres', []) if g.get('name')]

        return NormalizedMediaDetail(
            provider=self.provider_key,
            external_id=external_id,
            external_url=self.get_external_url(external_id),
            title=title,
            media_type='MANGA',
            slug_candidate=slug_base,
            release_year=release_year,
            synopsis=data.get('synopsis') or '',
            poster_url=poster_url,
            genres=genres,
            alternative_titles=alt_titles,
            id_mal=external_id,
            author=author_str,
            artist=author_str,
            manga_type=manga_type,
            publication_status=pub_status,
            total_chapters=data.get('chapters')
        )

    def _fetch_endpoint(self, endpoint: str, params: Dict[str, Any], limit: int = 20) -> List[NormalizedSearchResult]:
        try:
            resp = requests.get(
                endpoint,
                params=params,
                headers={'User-Agent': 'DreamTeal/1.0'},
                timeout=self.timeout
            )
            if resp.status_code == 200:
                results = []
                data = resp.json().get('data', [])
                for item in data[:limit]:
                    results.append(self._normalize_search_item(item))
                return results
            return []
        except requests.RequestException as e:
            logger.error("Jikan feed request failed (%s): %s", endpoint, str(e))
            return []

    def discover_popular(self, media_type: str = 'MANGA', limit: int = 20) -> List[NormalizedSearchResult]:
        return self._fetch_endpoint(
            f"{self.base_url}/top/manga",
            {'filter': 'bypopularity', 'limit': min(limit, 25)},
            limit
        )

    def discover_latest(self, media_type: str = 'MANGA', limit: int = 20) -> List[NormalizedSearchResult]:
        return self._fetch_endpoint(
            f"{self.base_url}/manga",
            {'order_by': 'start_date', 'sort': 'desc', 'limit': min(limit, 25)},
            limit
        )

    def discover_upcoming(self, media_type: str = 'MANGA', limit: int = 20) -> List[NormalizedSearchResult]:
        return self._fetch_endpoint(
            f"{self.base_url}/top/manga",
            {'filter': 'upcoming', 'limit': min(limit, 25)},
            limit
        )

    def discover_trending(self, media_type: str = 'MANGA', limit: int = 20) -> List[NormalizedSearchResult]:
        # Jikan lacks trending endpoint; documented fallback to popular
        logger.debug("Jikan does not support native trending; falling back to popular manga.")
        return self.discover_popular(media_type, limit=limit)
