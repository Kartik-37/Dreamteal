"""
AniList GraphQL Metadata Provider Adapter for DreamTeal.
Handles Manga and Manhwa search, details, and multi-mode discovery (Popular, Latest, Trending, Upcoming).

Strictly complies with DreamTeal Zero-Star Rating Policy:
Does NOT import, normalize, or expose AniList averageScore or community scores.
Exposes idMal for deterministic cross-provider linking with Jikan (MyAnimeList).
"""

import logging
import re
from typing import Any, Dict, List, Optional
import requests
from django.conf import settings
from django.utils.text import slugify

from .base import BaseMetadataProvider, DiscoveryMode, NormalizedMediaDetail, NormalizedSearchResult

logger = logging.getLogger(__name__)


class AniListProvider(BaseMetadataProvider):
    provider_key = 'anilist'
    display_name = 'AniList'
    graphql_url = 'https://graphql.anilist.co'

    capabilities = {
        'search': True,
        'details': True,
        'popular': True,
        'trending': True,
        'latest': True,
        'upcoming': True,
    }

    def __init__(self):
        self.timeout = getattr(settings, 'PROVIDER_HTTP_TIMEOUT', 8)

    def get_external_url(self, external_id: str) -> str:
        return f"https://anilist.co/manga/{external_id}"

    def _post_graphql(self, query: str, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'DreamTeal/1.0',
        }
        try:
            resp = requests.post(
                self.graphql_url,
                json={'query': query, 'variables': variables},
                headers=headers,
                timeout=self.timeout
            )
            if resp.status_code == 200:
                return resp.json().get('data')
            logger.warning("AniList GraphQL returned status %d", resp.status_code)
            return None
        except requests.RequestException as e:
            logger.error("AniList GraphQL request failed: %s", str(e))
            return None

    def search(self, query: str, limit: int = 20, subtype: Optional[str] = None) -> List[NormalizedSearchResult]:
        if not query.strip():
            return []

        country_var_decl = ", $country: CountryCode" if subtype in ['MANGA', 'MANHWA', 'MANHUA'] else ""
        country_filter = ", countryOfOrigin: $country" if subtype in ['MANGA', 'MANHWA', 'MANHUA'] else ""

        gql_query = f"""
        query ($search: String, $perPage: Int{country_var_decl}) {{
          Page(page: 1, perPage: $perPage) {{
            media(search: $search, type: MANGA{country_filter}, sort: SEARCH_MATCH) {{
              id
              title {{
                romaji
                english
                native
              }}
              countryOfOrigin
              format
              status
              startDate {{ year }}
              coverImage {{ large }}
              bannerImage
              description(asHtml: false)
              genres
            }}
          }}
        }}
        """
        vars_payload: Dict[str, Any] = {'search': query, 'perPage': limit}
        if subtype == 'MANHWA':
            vars_payload['country'] = 'KR'
        elif subtype == 'MANGA':
            vars_payload['country'] = 'JP'
        elif subtype == 'MANHUA':
            vars_payload['country'] = 'CN'

        data = self._post_graphql(gql_query, vars_payload)
        if not data:
            return []

        results = []
        media_list = data.get('Page', {}).get('media', [])
        for item in media_list:
            results.append(self._normalize_search_item(item))
        return results

    def _normalize_search_item(self, item: Dict[str, Any]) -> NormalizedSearchResult:
        ext_id = str(item.get('id', ''))
        titles = item.get('title', {})
        chosen_title = titles.get('english') or titles.get('romaji') or titles.get('native') or 'Untitled Manga'

        # Clean HTML tags if any leaked into description
        raw_desc = item.get('description') or ''
        clean_desc = re.sub(r'<[^>]+>', '', raw_desc)

        cover = item.get('coverImage', {}).get('large', '')
        banner = item.get('bannerImage', '')
        year = item.get('startDate', {}).get('year')

        country = item.get('countryOfOrigin', 'JP')
        if country == 'KR':
            subtype = 'MANHWA'
        elif country == 'CN':
            subtype = 'MANHUA'
        else:
            subtype = 'MANGA'

        return NormalizedSearchResult(
            provider=self.provider_key,
            external_id=ext_id,
            title=chosen_title,
            media_type='MANGA',
            subtype=subtype,
            release_year=year,
            poster_url=cover or '',
            backdrop_url=banner or '',
            synopsis=clean_desc,
            genres=item.get('genres', []),
            external_url=self.get_external_url(ext_id)
        )

    def get_details(self, external_id: str) -> Optional[NormalizedMediaDetail]:
        try:
            anilist_id = int(external_id)
        except ValueError:
            logger.error("Invalid AniList ID: %s", external_id)
            return None

        gql_query = """
        query ($id: Int) {
          Media(id: $id, type: MANGA) {
            id
            idMal
            title {
              romaji
              english
              native
            }
            countryOfOrigin
            format
            status
            startDate { year }
            chapters
            volumes
            coverImage { large }
            bannerImage
            description(asHtml: false)
            genres
            staff(sort: RELEVANCE) {
              edges {
                role
                node {
                  name {
                    full
                  }
                }
              }
            }
          }
        }
        """
        data = self._post_graphql(gql_query, {'id': anilist_id})
        if not data:
            return None

        media = data.get('Media')
        if not media:
            return None

        titles = media.get('title', {})
        chosen_title = titles.get('english') or titles.get('romaji') or titles.get('native') or 'Untitled Manga'
        alt_titles = [t for t in [titles.get('romaji'), titles.get('english'), titles.get('native')] if t and t != chosen_title]

        year = media.get('startDate', {}).get('year')
        slug_base = f"{slugify(chosen_title)}-{year}" if year else slugify(chosen_title)

        raw_desc = media.get('description') or ''
        clean_desc = re.sub(r'<[^>]+>', '', raw_desc)

        cover = media.get('coverImage', {}).get('large', '')
        banner = media.get('bannerImage', '')

        # Country of origin & format to MangaType
        country = media.get('countryOfOrigin', 'JP')
        if country == 'KR':
            manga_type = 'MANHWA'
        elif country == 'CN':
            manga_type = 'MANHUA'
        else:
            manga_type = 'MANGA'

        # Status mapping
        raw_status = media.get('status', 'RELEASING')
        status_map = {
            'RELEASING': 'PUBLISHING',
            'FINISHED': 'FINISHED',
            'CANCELLED': 'HIATUS',
            'HIATUS': 'HIATUS',
            'NOT_YET_RELEASED': 'PUBLISHING',
        }
        pub_status = status_map.get(raw_status, 'PUBLISHING')

        # Staff: author and artist
        author = ''
        artist = ''
        staff_edges = media.get('staff', {}).get('edges', [])
        for edge in staff_edges:
            role = (edge.get('role') or '').lower()
            name = edge.get('node', {}).get('name', {}).get('full', '')
            if not author and any(k in role for k in ['story', 'author', 'original']):
                author = name
            if not artist and any(k in role for k in ['art', 'illustration']):
                artist = name

        if not author and staff_edges:
            author = staff_edges[0].get('node', {}).get('name', {}).get('full', '')
        if not artist:
            artist = author

        id_mal = str(media.get('idMal')) if media.get('idMal') else None

        return NormalizedMediaDetail(
            provider=self.provider_key,
            external_id=str(media.get('id')),
            external_url=self.get_external_url(str(media.get('id'))),
            title=chosen_title,
            media_type='MANGA',
            slug_candidate=slug_base,
            release_year=year,
            synopsis=clean_desc,
            poster_url=cover or '',
            backdrop_url=banner or '',
            genres=media.get('genres', []),
            alternative_titles=alt_titles,
            id_mal=id_mal,
            author=author,
            artist=artist,
            manga_type=manga_type,
            publication_status=pub_status,
            total_chapters=media.get('chapters')
        )

    def _fetch_page(self, sort_enum: str, extra_filter: str = '', limit: int = 20, media_type: str = 'MANGA') -> List[NormalizedSearchResult]:
        country_filter = ''
        if media_type.upper() == 'MANHWA':
            country_filter = ', countryOfOrigin: KR'
        elif media_type.upper() == 'MANGA':
            country_filter = ', countryOfOrigin: JP'

        combined_filter = f"{extra_filter}{country_filter}"
        gql_query = f"""
        query ($perPage: Int) {{
          Page(page: 1, perPage: $perPage) {{
            media(type: MANGA, sort: [{sort_enum}] {combined_filter}) {{
              id
              title {{
                romaji
                english
                native
              }}
              countryOfOrigin
              status
              startDate {{ year }}
              coverImage {{ large }}
              bannerImage
              description(asHtml: false)
              genres
            }}
          }}
        }}
        """
        data = self._post_graphql(gql_query, {'perPage': limit})
        if not data:
            return []

        results = []
        for item in data.get('Page', {}).get('media', []):
            results.append(self._normalize_search_item(item))
        return results

    def discover_popular(self, media_type: str = 'MANGA', limit: int = 20) -> List[NormalizedSearchResult]:
        return self._fetch_page('POPULARITY_DESC', limit=limit, media_type=media_type)

    def discover_trending(self, media_type: str = 'MANGA', limit: int = 20) -> List[NormalizedSearchResult]:
        return self._fetch_page('TRENDING_DESC', limit=limit, media_type=media_type)

    def discover_latest(self, media_type: str = 'MANGA', limit: int = 20) -> List[NormalizedSearchResult]:
        return self._fetch_page('START_DATE_DESC', limit=limit, media_type=media_type)

    def discover_upcoming(self, media_type: str = 'MANGA', limit: int = 20) -> List[NormalizedSearchResult]:
        return self._fetch_page('POPULARITY_DESC', extra_filter=', status: NOT_YET_RELEASED', limit=limit, media_type=media_type)
