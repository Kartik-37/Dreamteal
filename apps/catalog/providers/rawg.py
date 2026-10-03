"""
RAWG Video Game Metadata Provider Adapter for DreamTeal.
Handles Video Game search, details, and multi-mode discovery (Popular, Latest, Upcoming).

Strictly complies with DreamTeal Zero-Star Rating Policy:
Does NOT import, normalize, or expose RAWG ratings, metacritic scores, or user review numbers.
"""

from datetime import date, timedelta
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import requests
from django.conf import settings
from django.utils.text import slugify

from .base import BaseMetadataProvider, DiscoveryMode, NormalizedMediaDetail, NormalizedSearchResult

logger = logging.getLogger(__name__)


class RAWGProvider(BaseMetadataProvider):
    provider_key = 'rawg'
    display_name = 'RAWG'
    base_url = 'https://api.rawg.io/api'

    capabilities = {
        'search': True,
        'details': True,
        'popular': True,
        'latest': True,
        'upcoming': True,
        'trending': False,  # RAWG lacks native trending; falls back to popular
    }

    def __init__(self):
        self.api_key = getattr(settings, 'RAWG_API_KEY', '')
        self.timeout = getattr(settings, 'PROVIDER_HTTP_TIMEOUT', 8)

    def _get_params(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = extra.copy() if extra else {}
        if self.api_key:
            params['key'] = self.api_key
        return params

    def get_external_url(self, external_id: str, slug: Optional[str] = None) -> str:
        identifier = slug or external_id
        return f"https://rawg.io/games/{identifier}"

    def search(self, query: str, limit: int = 20) -> List[NormalizedSearchResult]:
        if not query.strip():
            return []

        try:
            resp = requests.get(
                f"{self.base_url}/games",
                params=self._get_params({'search': query, 'page_size': min(limit, 20)}),
                headers={'User-Agent': 'DreamTeal/1.0'},
                timeout=self.timeout
            )
            if resp.status_code == 200:
                results = []
                data = resp.json().get('results', [])
                for item in data[:limit]:
                    results.append(self._normalize_search_item(item))
                return results
            logger.warning("RAWG search returned status %d", resp.status_code)
            return []
        except requests.RequestException as e:
            logger.error("RAWG search failed for query %s: %s", query, str(e))
            return []

    def _normalize_search_item(self, item: Dict[str, Any]) -> NormalizedSearchResult:
        ext_id = str(item.get('id', ''))
        title = item.get('name', 'Untitled Game')
        released = item.get('released', '')
        release_year = None
        if released and len(released) >= 4 and released[:4].isdigit():
            release_year = int(released[:4])

        genres = [g.get('name') for g in item.get('genres', []) if g.get('name')]
        poster_url = item.get('background_image') or ''

        return NormalizedSearchResult(
            provider=self.provider_key,
            external_id=ext_id,
            title=title,
            media_type='GAME',
            release_year=release_year,
            poster_url=poster_url,
            backdrop_url=poster_url,
            synopsis='',
            genres=genres,
            external_url=self.get_external_url(ext_id, item.get('slug'))
        )

    def get_details(self, external_id: str) -> Optional[NormalizedMediaDetail]:
        try:
            resp = requests.get(
                f"{self.base_url}/games/{external_id}",
                params=self._get_params(),
                headers={'User-Agent': 'DreamTeal/1.0'},
                timeout=self.timeout
            )
            if resp.status_code != 200:
                logger.warning("RAWG get_details returned %d for ID %s", resp.status_code, external_id)
                return None

            data = resp.json()
            return self._normalize_detail_payload(data, external_id)
        except requests.RequestException as e:
            logger.error("RAWG get_details failed for ID %s: %s", external_id, str(e))
            return None

    def _normalize_detail_payload(self, data: Dict[str, Any], external_id: str) -> NormalizedMediaDetail:
        title = data.get('name', 'Untitled Game')
        released = data.get('released', '')
        release_year = None
        if released and len(released) >= 4 and released[:4].isdigit():
            release_year = int(released[:4])

        slug_base = f"{slugify(title)}-{release_year}" if release_year else slugify(title)
        synopsis = data.get('description_raw') or data.get('description', '')
        poster_url = data.get('background_image') or ''
        backdrop_url = data.get('background_image_additional') or poster_url

        # Alternative names if any
        alt_titles = []
        if data.get('name_original') and data.get('name_original') != title:
            alt_titles.append(data.get('name_original'))

        # Platforms
        platforms: List[str] = []
        for p_entry in data.get('platforms', []):
            p_obj = p_entry.get('platform', {})
            p_name = p_obj.get('name')
            if p_name and p_name not in platforms:
                platforms.append(p_name)

        # Developers & Publishers
        devs = [d.get('name') for d in data.get('developers', []) if d.get('name')]
        pubs = [p.get('name') for p in data.get('publishers', []) if p.get('name')]
        developer_str = ', '.join(devs)
        publisher_str = ', '.join(pubs)

        # Playtime to average story hours
        playtime = data.get('playtime')
        story_hours = Decimal(str(playtime)) if playtime and playtime > 0 else None

        genres = [g.get('name') for g in data.get('genres', []) if g.get('name')]
        tags = [t.get('name') for t in data.get('tags', []) if t.get('name')][:10]

        return NormalizedMediaDetail(
            provider=self.provider_key,
            external_id=external_id,
            external_url=self.get_external_url(external_id, data.get('slug')),
            title=title,
            media_type='GAME',
            slug_candidate=slug_base,
            release_year=release_year,
            synopsis=synopsis,
            poster_url=poster_url,
            backdrop_url=backdrop_url,
            genres=genres,
            tags=tags,
            alternative_titles=alt_titles,
            developer=developer_str,
            publisher=publisher_str,
            platforms=platforms,
            average_story_hours=story_hours
        )

    def _fetch_feed(self, extra_params: Dict[str, Any], limit: int = 20) -> List[NormalizedSearchResult]:
        params = {'page_size': min(limit, 20)}
        params.update(extra_params)
        try:
            resp = requests.get(
                f"{self.base_url}/games",
                params=self._get_params(params),
                headers={'User-Agent': 'DreamTeal/1.0'},
                timeout=self.timeout
            )
            if resp.status_code == 200:
                results = []
                data = resp.json().get('results', [])
                for item in data[:limit]:
                    results.append(self._normalize_search_item(item))
                return results
            return []
        except requests.RequestException as e:
            logger.error("RAWG feed request failed: %s", str(e))
            return []

    def discover_popular(self, media_type: str = 'GAME', limit: int = 20) -> List[NormalizedSearchResult]:
        return self._fetch_feed({'ordering': '-added'}, limit=limit)

    def discover_latest(self, media_type: str = 'GAME', limit: int = 20) -> List[NormalizedSearchResult]:
        # Genuine recent releases (past 6 months to today)
        today = date.today()
        six_months_ago = today - timedelta(days=180)
        dates_range = f"{six_months_ago.isoformat()},{today.isoformat()}"
        return self._fetch_feed({'dates': dates_range, 'ordering': '-released'}, limit=limit)

    def discover_upcoming(self, media_type: str = 'GAME', limit: int = 20) -> List[NormalizedSearchResult]:
        # Scheduled unreleased games (today to 1 year ahead)
        today = date.today()
        one_year_ahead = today + timedelta(days=365)
        dates_range = f"{today.isoformat()},{one_year_ahead.isoformat()}"
        return self._fetch_feed({'dates': dates_range, 'ordering': 'released'}, limit=limit)

    def discover_trending(self, media_type: str = 'GAME', limit: int = 20) -> List[NormalizedSearchResult]:
        # RAWG lacks native trending; fallback to popular with documented notice
        logger.debug("RAWG does not support native trending; falling back to popular games.")
        return self.discover_popular(media_type, limit=limit)
