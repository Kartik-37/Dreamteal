"""
TMDB (The Movie Database) Metadata Provider Adapter for DreamTeal.
Handles Movie and TV Series search, details, and multi-mode discovery (Popular, Latest, Trending, Upcoming).

Strictly complies with DreamTeal Zero-Star Rating Policy:
Does NOT import, normalize, or expose TMDB vote_average or numeric scores.
Region-Aware Streaming:
Uses configured DEFAULT_PROVIDER_REGION (default 'IN') for flatrate OTT watch providers.
Never falls back to arbitrary random countries when region data is absent.
"""

import logging
from typing import Any, Dict, List, Optional
import requests
from django.conf import settings
from django.utils.text import slugify

from .base import BaseMetadataProvider, DiscoveryMode, NormalizedMediaDetail, NormalizedSearchResult

logger = logging.getLogger(__name__)


class TMDBProvider(BaseMetadataProvider):
    provider_key = 'tmdb'
    display_name = 'TMDB'
    base_url = 'https://api.themoviedb.org/3'
    image_base_poster = 'https://image.tmdb.org/t/p/w500'
    image_base_backdrop = 'https://image.tmdb.org/t/p/w1280'

    capabilities = {
        'search': True,
        'details': True,
        'popular': True,
        'latest': True,
        'trending': True,
        'upcoming': True,
    }

    def __init__(self):
        self.access_token = getattr(settings, 'TMDB_ACCESS_TOKEN', '')
        self.api_key = getattr(settings, 'TMDB_API_KEY', '')
        self.timeout = getattr(settings, 'PROVIDER_HTTP_TIMEOUT', 8)
        self.default_region = getattr(settings, 'DEFAULT_PROVIDER_REGION', 'IN').upper()

    def _get_headers(self) -> Dict[str, str]:
        headers = {'Accept': 'application/json'}
        if self.access_token:
            headers['Authorization'] = f"Bearer {self.access_token}"
        return headers

    def _get_params(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = extra.copy() if extra else {}
        if not self.access_token and self.api_key:
            params['api_key'] = self.api_key
        return params

    def get_external_url(self, external_id: str, media_type: str = 'movie') -> str:
        segment = 'tv' if media_type.upper() == 'SERIES' else 'movie'
        return f"https://www.themoviedb.org/{segment}/{external_id}"

    def search(self, query: str, limit: int = 20, media_type: Optional[str] = None) -> List[NormalizedSearchResult]:
        results: List[NormalizedSearchResult] = []
        if not query.strip():
            return results

        types_to_search = []
        if media_type:
            types_to_search = ['SERIES'] if media_type.upper() == 'SERIES' else ['MOVIE']
        else:
            types_to_search = ['MOVIE', 'SERIES']

        for mtype in types_to_search:
            endpoint = f"{self.base_url}/search/movie" if mtype == 'MOVIE' else f"{self.base_url}/search/tv"
            try:
                resp = requests.get(
                    endpoint,
                    headers=self._get_headers(),
                    params=self._get_params({'query': query, 'page': 1}),
                    timeout=self.timeout
                )
                if resp.status_code == 200:
                    data = resp.json().get('results', [])
                    for item in data[:limit]:
                        results.append(self._normalize_search_item(item, mtype))
                else:
                    logger.warning("TMDB search returned %d for query %s", resp.status_code, query)
            except requests.RequestException as e:
                logger.error("TMDB search failed for query %s: %s", query, str(e))

        return results[:limit]

    def _normalize_search_item(self, item: Dict[str, Any], media_type: str) -> NormalizedSearchResult:
        ext_id = str(item.get('id', ''))
        title = item.get('title') if media_type == 'MOVIE' else item.get('name', '')
        date_str = item.get('release_date') if media_type == 'MOVIE' else item.get('first_air_date', '')
        release_year = None
        if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
            release_year = int(date_str[:4])

        poster_path = item.get('poster_path')
        backdrop_path = item.get('backdrop_path')

        return NormalizedSearchResult(
            provider=self.provider_key,
            external_id=ext_id,
            title=title or 'Untitled',
            media_type=media_type,
            release_year=release_year,
            poster_url=f"{self.image_base_poster}{poster_path}" if poster_path else '',
            backdrop_url=f"{self.image_base_backdrop}{backdrop_path}" if backdrop_path else '',
            synopsis=item.get('overview', ''),
            genres=[],  # Detailed genres resolved on import
            external_url=self.get_external_url(ext_id, media_type)
        )

    def get_details(self, external_id: str, media_type: str = 'MOVIE') -> Optional[NormalizedMediaDetail]:
        is_movie = media_type.upper() == 'MOVIE'
        endpoint = f"{self.base_url}/movie/{external_id}" if is_movie else f"{self.base_url}/tv/{external_id}"

        try:
            resp = requests.get(
                endpoint,
                headers=self._get_headers(),
                params=self._get_params({'append_to_response': 'credits,watch/providers'}),
                timeout=self.timeout
            )
            if resp.status_code != 200:
                logger.warning("TMDB get_details returned %d for ID %s", resp.status_code, external_id)
                return None

            data = resp.json()
            return self._normalize_detail_payload(data, external_id, media_type.upper())
        except requests.RequestException as e:
            logger.error("TMDB get_details failed for ID %s: %s", external_id, str(e))
            return None

    def _normalize_detail_payload(self, data: Dict[str, Any], external_id: str, media_type: str) -> NormalizedMediaDetail:
        is_movie = media_type == 'MOVIE'
        title = data.get('title') if is_movie else data.get('name', 'Untitled')
        date_str = data.get('release_date') if is_movie else data.get('first_air_date', '')
        release_year = None
        if date_str and len(date_str) >= 4 and date_str[:4].isdigit():
            release_year = int(date_str[:4])

        slug_base = f"{slugify(title)}-{release_year}" if release_year else slugify(title)
        poster_path = data.get('poster_path')
        backdrop_path = data.get('backdrop_path')
        genres = [g.get('name') for g in data.get('genres', []) if g.get('name')]

        # OTT streaming providers: Region-aware lookup
        ott_providers: List[str] = []
        watch_data = data.get('watch/providers', {}).get('results', {})
        # Strictly look up the configured region (e.g. 'IN'); never pick arbitrary fallback country
        region_data = watch_data.get(self.default_region, {})
        if isinstance(region_data, dict):
            for provider_entry in region_data.get('flatrate', []):
                p_name = provider_entry.get('provider_name')
                if p_name and p_name not in ott_providers:
                    ott_providers.append(p_name)

        if is_movie:
            director = ''
            credits_data = data.get('credits', {})
            for crew in credits_data.get('crew', []):
                if crew.get('job') == 'Director':
                    director = crew.get('name', '')
                    break

            companies = data.get('production_companies', [])
            studio = companies[0].get('name', '') if companies else ''
            runtime = data.get('runtime')

            return NormalizedMediaDetail(
                provider=self.provider_key,
                external_id=external_id,
                external_url=self.get_external_url(external_id, 'MOVIE'),
                title=title,
                media_type='MOVIE',
                slug_candidate=slug_base,
                release_year=release_year,
                synopsis=data.get('overview', ''),
                poster_url=f"{self.image_base_poster}{poster_path}" if poster_path else '',
                backdrop_url=f"{self.image_base_backdrop}{backdrop_path}" if backdrop_path else '',
                genres=genres,
                director=director,
                runtime_minutes=runtime,
                studio=studio,
                ott_providers=ott_providers
            )
        else:
            creators_list = [c.get('name') for c in data.get('created_by', []) if c.get('name')]
            creators = ', '.join(creators_list)

            # TV Status mapping
            raw_status = data.get('status', '')
            status_map = {
                'Returning Series': 'AIRING',
                'In Production': 'AIRING',
                'Planned': 'AIRING',
                'Ended': 'ENDED',
                'Canceled': 'CANCELLED',
            }
            series_status = status_map.get(raw_status, 'AIRING')

            # Networks as fallback OTT/broadcast providers if region has no flatrate entries
            if not ott_providers:
                for network in data.get('networks', []):
                    n_name = network.get('name')
                    if n_name and n_name not in ott_providers:
                        ott_providers.append(n_name)

            return NormalizedMediaDetail(
                provider=self.provider_key,
                external_id=external_id,
                external_url=self.get_external_url(external_id, 'SERIES'),
                title=title,
                media_type='SERIES',
                slug_candidate=slug_base,
                release_year=release_year,
                synopsis=data.get('overview', ''),
                poster_url=f"{self.image_base_poster}{poster_path}" if poster_path else '',
                backdrop_url=f"{self.image_base_backdrop}{backdrop_path}" if backdrop_path else '',
                genres=genres,
                creators=creators,
                total_seasons=data.get('number_of_seasons', 1) or 1,
                total_episodes=data.get('number_of_episodes'),
                series_status=series_status,
                ott_providers=ott_providers
            )

    def _fetch_feed(self, endpoint: str, media_type: str, limit: int = 20) -> List[NormalizedSearchResult]:
        try:
            resp = requests.get(
                endpoint,
                headers=self._get_headers(),
                params=self._get_params({'page': 1}),
                timeout=self.timeout
            )
            if resp.status_code == 200:
                results = []
                data = resp.json().get('results', [])
                for item in data[:limit]:
                    results.append(self._normalize_search_item(item, media_type))
                return results
            return []
        except requests.RequestException as e:
            logger.error("TMDB feed request failed (%s): %s", endpoint, str(e))
            return []

    def discover_popular(self, media_type: str, limit: int = 20) -> List[NormalizedSearchResult]:
        mtype = 'SERIES' if media_type.upper() == 'SERIES' else 'MOVIE'
        endpoint = f"{self.base_url}/movie/popular" if mtype == 'MOVIE' else f"{self.base_url}/tv/popular"
        return self._fetch_feed(endpoint, mtype, limit)

    def discover_latest(self, media_type: str, limit: int = 20) -> List[NormalizedSearchResult]:
        mtype = 'SERIES' if media_type.upper() == 'SERIES' else 'MOVIE'
        # Genuine new release endpoints: now_playing for movies, on_the_air for TV
        endpoint = f"{self.base_url}/movie/now_playing" if mtype == 'MOVIE' else f"{self.base_url}/tv/on_the_air"
        return self._fetch_feed(endpoint, mtype, limit)

    def discover_trending(self, media_type: str, limit: int = 20) -> List[NormalizedSearchResult]:
        mtype = 'SERIES' if media_type.upper() == 'SERIES' else 'MOVIE'
        segment = 'tv' if mtype == 'SERIES' else 'movie'
        endpoint = f"{self.base_url}/trending/{segment}/week"
        return self._fetch_feed(endpoint, mtype, limit)

    def discover_upcoming(self, media_type: str, limit: int = 20) -> List[NormalizedSearchResult]:
        mtype = 'SERIES' if media_type.upper() == 'SERIES' else 'MOVIE'
        # Movies have native upcoming; TV uses on_the_air as closest scheduled release
        endpoint = f"{self.base_url}/movie/upcoming" if mtype == 'MOVIE' else f"{self.base_url}/tv/on_the_air"
        return self._fetch_feed(endpoint, mtype, limit)
