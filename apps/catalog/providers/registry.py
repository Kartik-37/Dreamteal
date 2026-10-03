"""
Provider Registry & Catalog Synchronization Service Layer for DreamTeal.

Orchestrates:
- Routing requests to appropriate providers by media category
- Seamless fallback handling (AniList -> Jikan for Manga/Manhwa)
- Balanced universal multi-media search interleaving (movies, series, manga, games)
- Multi-mode discovery feeds (popular, latest, trending, upcoming)
- Safe cross-provider deduplication using MediaMatcherService
- Safe catalog import and metadata synchronization without touching user data
"""

from datetime import timedelta
import logging
from typing import Any, Dict, List, Optional, Tuple
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.catalog.models import (
    ExternalMediaMapping, ExternalProvider, GameDetail, Genre,
    MangaDetail, MediaItem, MovieDetail, SeriesDetail, Tag
)
from .anilist import AniListProvider
from .base import BaseMetadataProvider, DiscoveryMode, NormalizedMediaDetail, NormalizedSearchResult
from .jikan import JikanProvider
from .matcher import MediaMatcherService
from .rawg import RAWGProvider
from .tmdb import TMDBProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Central registry routing media categories to metadata providers with fallback support.
    """

    def __init__(self):
        self.tmdb = TMDBProvider()
        self.anilist = AniListProvider()
        self.jikan = JikanProvider()
        self.rawg = RAWGProvider()

        self._providers: Dict[str, BaseMetadataProvider] = {
            'tmdb': self.tmdb,
            'anilist': self.anilist,
            'jikan': self.jikan,
            'rawg': self.rawg,
        }

    def get_provider(self, key: str) -> Optional[BaseMetadataProvider]:
        return self._providers.get(key.lower())

    def is_provider_active(self, provider_key: str) -> bool:
        """
        Checks whether the provider is active. If an ExternalProvider database
        record exists with active=False, routing to this provider is suppressed.
        """
        try:
            prov = ExternalProvider.objects.filter(provider_key=provider_key.lower()).first()
            if prov is not None:
                return prov.active
        except Exception:
            pass
        return True

    def search(self, query: str, category: Optional[str] = None, limit: int = 20) -> List[NormalizedSearchResult]:
        """
        Routes search queries across providers matching the target category.
        When no category is specified, applies balanced category interleaving
        (round-robin) so no single provider dominates universal search results.
        Respects provider active status.
        """
        if not query.strip():
            return []

        cat = category.upper() if category else None

        if cat:
            results: List[NormalizedSearchResult] = []
            if cat in ['MOVIE', 'SERIES']:
                if self.is_provider_active('tmdb'):
                    results = self.tmdb.search(query, limit=limit, media_type=cat)
            elif cat in ['MANGA', 'MANHWA']:
                subtype = 'MANHWA' if cat == 'MANHWA' else 'MANGA'
                # Primary: AniList
                if self.is_provider_active('anilist'):
                    results = self.anilist.search(query, limit=limit, subtype=subtype)
                if not results and self.is_provider_active('jikan'):
                    logger.info("AniList returned no results for '%s'; attempting Jikan fallback.", query)
                    results = self.jikan.search(query, limit=limit, subtype=subtype)
            elif cat == 'GAME':
                if self.is_provider_active('rawg'):
                    results = self.rawg.search(query, limit=limit)

            return self._enrich_with_local_state(results)[:limit]

        # Universal Search (No Category): Balanced round-robin interleaving
        quota = max(limit // 4, 3)

        movies = self.tmdb.search(query, limit=quota, media_type='MOVIE') if self.is_provider_active('tmdb') else []
        series = self.tmdb.search(query, limit=quota, media_type='SERIES') if self.is_provider_active('tmdb') else []

        manga = []
        if self.is_provider_active('anilist'):
            manga = self.anilist.search(query, limit=quota)
        if not manga and self.is_provider_active('jikan'):
            logger.info("AniList returned no search results for '%s'; attempting Jikan fallback.", query)
            manga = self.jikan.search(query, limit=quota)

        games = self.rawg.search(query, limit=quota) if self.is_provider_active('rawg') else []

        # Interleave buckets round-robin: [Movie, Series, Manga, Game, Movie, ...]
        interleaved: List[NormalizedSearchResult] = []
        buckets = [movies, series, manga, games]
        max_len = max(len(b) for b in buckets) if buckets else 0

        for i in range(max_len):
            for b in buckets:
                if i < len(b):
                    interleaved.append(b[i])

        return self._enrich_with_local_state(interleaved)[:limit]

    def discover(self, category: str, mode: str = DiscoveryMode.POPULAR, limit: int = 20) -> List[NormalizedSearchResult]:
        """
        Fetches discovery feeds for a specific media category with semantic modes:
        - popular
        - latest
        - trending
        - upcoming
        Respects provider active status.
        """
        cat = category.upper()
        results: List[NormalizedSearchResult] = []

        if cat in ['MOVIE', 'SERIES']:
            if self.is_provider_active('tmdb'):
                results = self.tmdb.discover(cat, mode=mode, limit=limit)
        elif cat in ['MANGA', 'MANHWA']:
            if self.is_provider_active('anilist'):
                results = self.anilist.discover(cat, mode=mode, limit=limit)
            if not results and self.is_provider_active('jikan'):
                logger.info("AniList discovery unavailable; falling back to Jikan.")
                results = self.jikan.discover(cat, mode=mode, limit=limit)
        elif cat == 'GAME':
            if self.is_provider_active('rawg'):
                results = self.rawg.discover(cat, mode=mode, limit=limit)

        return self._enrich_with_local_state(results)[:limit]

    def _enrich_with_local_state(self, results: List[NormalizedSearchResult]) -> List[NormalizedSearchResult]:
        """
        Cross-references candidate results with ExternalMediaMapping in the local database.
        Sets is_imported=True and slug when already stored in DreamTeal.
        """
        if not results:
            return results

        provider_ids = [(r.provider, r.external_id) for r in results]
        existing_mappings = ExternalMediaMapping.objects.filter(
            provider__provider_key__in=[p for p, _ in provider_ids],
            external_id__in=[eid for _, eid in provider_ids]
        ).select_related('media_item', 'provider')

        mapping_lookup = {
            (m.provider.provider_key, m.external_id): m.media_item
            for m in existing_mappings
        }

        for r in results:
            key = (r.provider, r.external_id)
            if key in mapping_lookup:
                item = mapping_lookup[key]
                r.is_imported = True
                r.slug = item.slug

        return results

    def fetch_details(
        self,
        provider_key: str,
        external_id: str,
        media_type: Optional[str] = None,
        title_hint: Optional[str] = None
    ) -> Optional[NormalizedMediaDetail]:
        """
        Fetches normalized details from the specified provider with safe fallback.
        When AniList detail retrieval fails, safely searches Jikan using title matching
        and verifies confidence threshold; NEVER assumes AniList ID equals Jikan ID.
        """
        if not self.is_provider_active(provider_key):
            # If AniList is inactive, and we have a title_hint, attempt Jikan fallback directly
            if provider_key == 'anilist' and self.is_provider_active('jikan') and title_hint:
                logger.info("AniList is inactive; routing directly to Jikan fallback for '%s'", title_hint)
            else:
                logger.warning("Provider '%s' is inactive in system configuration.", provider_key)
                return None

        provider = self.get_provider(provider_key)
        if not provider:
            logger.error("Provider '%s' not registered.", provider_key)
            return None

        if provider_key == 'tmdb':
            mtype = media_type or 'MOVIE'
            return self.tmdb.get_details(external_id, mtype)

        elif provider_key == 'anilist':
            detail = self.anilist.get_details(external_id) if self.is_provider_active('anilist') else None
            if detail:
                return detail

            # Safe AniList -> Jikan Fallback
            # Do NOT use external_id as a Jikan ID! AniList IDs != MAL IDs.
            if title_hint and self.is_provider_active('jikan'):
                logger.info(
                    "AniList details unavailable for ID %s; attempting safe title-based Jikan fallback with '%s'",
                    external_id, title_hint
                )
                jikan_candidates = self.jikan.search(title_hint, limit=5)
                for cand in jikan_candidates:
                    # Fetch candidate details from Jikan and compare confidence
                    cand_detail = self.jikan.get_details(cand.external_id)
                    if cand_detail:
                        norm_hint = MediaMatcherService.normalize_string(title_hint)
                        cand_norm_title = MediaMatcherService.normalize_string(cand_detail.title)
                        score = MediaMatcherService.calculate_string_similarity(norm_hint, cand_norm_title)
                        if score >= 75.0:
                            logger.info("Found confident Jikan fallback match: %s (MAL ID %s, Score: %.1f)", cand_detail.title, cand.external_id, score)
                            return cand_detail

            logger.warning("AniList details failed for ID %s and no confident Jikan fallback was found.", external_id)
            return None

        elif provider_key == 'jikan':
            return self.jikan.get_details(external_id)

        elif provider_key == 'rawg':
            return self.rawg.get_details(external_id)

        return provider.get_details(external_id)

    @transaction.atomic
    def import_media(
        self,
        provider_key: str,
        external_id: str,
        media_type: Optional[str] = None,
        force_refresh: bool = False,
        title_hint: Optional[str] = None
    ) -> Tuple[MediaItem, bool]:
        """
        Imports an external media item into DreamTeal's database or returns the existing record.
        Returns:
            Tuple[MediaItem, bool]: (media_item, created)
            created is True for new catalog entries (201 Created),
            created is False for existing/refreshed items (200 OK).

        Strictly preserves all user-owned data (status, progress, diary logs, reviews).
        Updates provider-owned metadata upon force_refresh.
        Reconciles provider genres and tags.
        Uses MediaMatcherService for safe cross-provider deduplication.
        """
        provider_key_clean = provider_key.lower()
        if not self.is_provider_active(provider_key_clean):
            if not (provider_key_clean == 'anilist' and self.is_provider_active('jikan') and title_hint):
                raise ValueError(f"Provider '{provider_key}' is currently disabled in system settings.")

        # 1. Ensure ExternalProvider record exists
        provider_obj, _ = ExternalProvider.objects.get_or_create(
            provider_key=provider_key_clean,
            defaults={'display_name': provider_key.upper(), 'active': True}
        )

        # 2. Check existing mapping for this exact (provider, external_id)
        existing_mapping = ExternalMediaMapping.objects.filter(
            provider=provider_obj,
            external_id=external_id
        ).select_related('media_item').first()

        freshness_hours = getattr(settings, 'CATALOG_SYNC_FRESHNESS_HOURS', 24)
        is_fresh = False
        if existing_mapping:
            is_fresh = timezone.now() - existing_mapping.last_synced_at < timedelta(hours=freshness_hours)

        if existing_mapping and is_fresh and not force_refresh:
            return existing_mapping.media_item, False

        # If title_hint was not passed, borrow from existing_mapping title if available
        if not title_hint and existing_mapping:
            title_hint = existing_mapping.media_item.title

        # 3. Fetch normalized details from provider
        norm = self.fetch_details(provider_key_clean, external_id, media_type, title_hint=title_hint)
        if not norm:
            if existing_mapping:
                return existing_mapping.media_item, False
            raise ValueError(f"Unable to fetch details from provider '{provider_key}' for ID '{external_id}'.")

        # 4. Check for Cross-Provider Deduplication if no mapping exists yet
        created = False
        if existing_mapping:
            media_item = existing_mapping.media_item
        else:
            # Check if another provider already imported this exact media item
            matched_item, match_score = MediaMatcherService.find_match(norm)
            if matched_item:
                media_item = matched_item
                logger.info(
                    "Cross-provider deduplication merged %s:%s into existing MediaItem %s (Score: %.1f)",
                    provider_key, external_id, media_item.slug, match_score
                )
            else:
                # Create a brand new MediaItem
                base_slug = norm.slug_candidate or slugify(norm.title)
                slug = base_slug
                counter = 1
                while MediaItem.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                media_item = MediaItem(
                    media_type=norm.media_type,
                    slug=slug,
                )
                created = True

        # 5. Update catalog metadata (only catalog-owned fields, never user data)
        # On initial creation or on force_refresh, update provider-owned fields
        if created or force_refresh or not media_item.title:
            if norm.title:
                media_item.title = norm.title
        if created or force_refresh or not media_item.release_year:
            if norm.release_year:
                media_item.release_year = norm.release_year
        if created or force_refresh or not media_item.synopsis:
            if norm.synopsis:
                media_item.synopsis = norm.synopsis
        if created or force_refresh or not media_item.poster_url:
            if norm.poster_url:
                media_item.poster_url = norm.poster_url
        if created or force_refresh or not media_item.backdrop_url:
            if norm.backdrop_url:
                media_item.backdrop_url = norm.backdrop_url
        media_item.save()

        # 6. Reconcile Genres and Tags (Provider-owned taxonomy synchronization)
        if norm.genres:
            provider_genres = []
            for g_name in norm.genres:
                g_name = g_name.strip()
                if g_name:
                    genre, _ = Genre.objects.get_or_create(
                        slug=slugify(g_name),
                        defaults={'name': g_name}
                    )
                    provider_genres.append(genre)
            media_item.genres.set(provider_genres)

        if norm.tags:
            provider_tags = []
            for t_name in norm.tags:
                t_name = t_name.strip()
                if t_name:
                    tag, _ = Tag.objects.get_or_create(
                        slug=slugify(t_name),
                        defaults={'name': t_name}
                    )
                    provider_tags.append(tag)
            media_item.tags.set(provider_tags)

        # 7. Category-specific detail models: update_or_create overwrites provider-owned detail fields
        if norm.media_type == 'MOVIE':
            MovieDetail.objects.update_or_create(
                media_item=media_item,
                defaults={
                    'director': norm.director,
                    'runtime_minutes': norm.runtime_minutes,
                    'studio': norm.studio,
                    'ott_providers': norm.ott_providers,
                }
            )
        elif norm.media_type == 'SERIES':
            SeriesDetail.objects.update_or_create(
                media_item=media_item,
                defaults={
                    'creators': norm.creators,
                    'total_seasons': norm.total_seasons,
                    'total_episodes': norm.total_episodes,
                    'status': norm.series_status,
                    'ott_providers': norm.ott_providers,
                }
            )
        elif norm.media_type == 'MANGA':
            MangaDetail.objects.update_or_create(
                media_item=media_item,
                defaults={
                    'author': norm.author,
                    'artist': norm.artist,
                    'manga_type': norm.manga_type,
                    'status': norm.publication_status,
                    'total_chapters': norm.total_chapters,
                }
            )
        elif norm.media_type == 'GAME':
            GameDetail.objects.update_or_create(
                media_item=media_item,
                defaults={
                    'developer': norm.developer,
                    'publisher': norm.publisher,
                    'platforms': norm.platforms,
                    'average_story_hours': norm.average_story_hours,
                }
            )

        # 8. Create or update ExternalMediaMapping for this provider
        ExternalMediaMapping.objects.update_or_create(
            provider=provider_obj,
            external_id=str(external_id),
            defaults={
                'media_item': media_item,
                'external_url': norm.external_url,
                'last_synced_at': timezone.now(),
            }
        )

        # If AniList item exposed an idMal, also record/preserve a mapping for Jikan
        if provider_key_clean == 'anilist' and norm.id_mal:
            jikan_provider, _ = ExternalProvider.objects.get_or_create(
                provider_key='jikan',
                defaults={'display_name': 'Jikan', 'active': True}
            )
            ExternalMediaMapping.objects.get_or_create(
                provider=jikan_provider,
                external_id=str(norm.id_mal),
                defaults={
                    'media_item': media_item,
                    'external_url': f"https://myanimelist.net/manga/{norm.id_mal}",
                }
            )
        # If fallback from AniList -> Jikan occurred, also map the resolved Jikan record
        elif provider_key_clean == 'anilist' and norm.provider == 'jikan':
            jikan_provider, _ = ExternalProvider.objects.get_or_create(
                provider_key='jikan',
                defaults={'display_name': 'Jikan', 'active': True}
            )
            ExternalMediaMapping.objects.update_or_create(
                provider=jikan_provider,
                external_id=str(norm.external_id),
                defaults={
                    'media_item': media_item,
                    'external_url': norm.external_url,
                    'last_synced_at': timezone.now(),
                }
            )

        return media_item, created


# Global shared provider registry instance
registry = ProviderRegistry()
