"""
Cross-Provider Media Matching & Deduplication Service for DreamTeal.

Safely identifies whether an external candidate corresponds to an existing
MediaItem in DreamTeal's catalog across different metadata providers (e.g.
AniList and Jikan for Manga, TMDB and other sources for Movies/Series).

STRICT MATCHING PRINCIPLES:
1. Media type must match strictly (Movies never match Manga or Games).
2. Never merge solely based on title equality.
3. Multi-signal confidence scoring requires:
   - Normalized title or alternative title match
   - Release year comparison (large penalty for >1 year discrepancies)
   - Creator/Author/Director/Developer overlap
   - Direct provider cross-reference IDs (e.g. AniList idMal == Jikan external_id)
4. Score threshold (>= 75.0 / 100) must be satisfied; otherwise items remain separate.
"""

import logging
import re
from typing import List, Optional, Tuple
from apps.catalog.models import MediaItem
from .base import NormalizedMediaDetail

logger = logging.getLogger(__name__)


class MediaMatcherService:
    MIN_CONFIDENCE_THRESHOLD = 75.0

    @staticmethod
    def normalize_string(text: Optional[str]) -> str:
        """Lowers, strips punctuation, and collapses whitespace."""
        if not text:
            return ''
        cleaned = re.sub(r'[^\w\s]', '', text.lower())
        return ' '.join(cleaned.split())

    @classmethod
    def find_match(cls, candidate: NormalizedMediaDetail) -> Tuple[Optional[MediaItem], float]:
        """
        Scans existing MediaItems of the same media_type and returns
        the best matching MediaItem if confidence >= MIN_CONFIDENCE_THRESHOLD.
        """
        # Strict rule 1: Media type must match exactly
        qs = MediaItem.objects.filter(media_type=candidate.media_type).select_related(
            'movie_detail', 'series_detail', 'manga_detail', 'game_detail'
        ).prefetch_related('external_mappings__provider')

        candidate_norm_title = cls.normalize_string(candidate.title)
        candidate_alt_titles = [cls.normalize_string(t) for t in candidate.alternative_titles if t]

        best_match: Optional[MediaItem] = None
        best_score = 0.0

        for item in qs:
            score = cls.calculate_confidence(item, candidate, candidate_norm_title, candidate_alt_titles)
            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score >= cls.MIN_CONFIDENCE_THRESHOLD:
            logger.info(
                "Matched candidate '%s' (%s:%s) with existing MediaItem '%s' (ID %d) with score %.1f",
                candidate.title, candidate.provider, candidate.external_id,
                best_match.title, best_match.id, best_score
            )
            return best_match, best_score

        return None, best_score

    @classmethod
    def calculate_confidence(
        cls,
        existing: MediaItem,
        candidate: NormalizedMediaDetail,
        candidate_norm_title: str,
        candidate_alt_titles: List[str]
    ) -> float:
        """
        Computes multi-signal matching score between an existing MediaItem
        and an incoming candidate NormalizedMediaDetail.
        """
        # Direct Cross-Provider ID match (e.g. AniList idMal == Jikan external_id)
        if candidate.provider == 'jikan' and candidate.external_id:
            # Check if existing item has an AniList mapping with matching idMal or Jikan mapping
            for m in existing.external_mappings.all():
                if m.provider.provider_key == 'jikan' and m.external_id == candidate.external_id:
                    return 100.0

        if candidate.provider == 'anilist' and candidate.id_mal:
            for m in existing.external_mappings.all():
                if m.provider.provider_key == 'jikan' and m.external_id == candidate.id_mal:
                    return 100.0

        # Title signal
        existing_norm_title = cls.normalize_string(existing.title)
        title_matched = False
        title_score = 0.0

        if existing_norm_title == candidate_norm_title:
            title_matched = True
            title_score = 40.0
        elif any(existing_norm_title == alt for alt in candidate_alt_titles):
            title_matched = True
            title_score = 35.0

        # If title doesn't match at all, score is 0
        if not title_matched:
            return 0.0

        score = title_score

        # Release year signal
        if existing.release_year is not None and candidate.release_year is not None:
            year_diff = abs(existing.release_year - candidate.release_year)
            if year_diff == 0:
                score += 35.0
            elif year_diff == 1:
                score += 15.0
            else:
                # Strong penalty for different release years (e.g. 1978 vs 2018 remakes/reboots)
                score -= 50.0

        # Creator / Author / Studio / Developer signal
        creator_score = cls._match_creators(existing, candidate)
        score += creator_score

        return max(0.0, score)

    @classmethod
    def _match_creators(cls, existing: MediaItem, candidate: NormalizedMediaDetail) -> float:
        """Calculates creator overlap depending on media category."""
        norm = cls.normalize_string

        if candidate.media_type == 'MOVIE' and hasattr(existing, 'movie_detail'):
            d1 = norm(existing.movie_detail.director)
            d2 = norm(candidate.director)
            s1 = norm(existing.movie_detail.studio)
            s2 = norm(candidate.studio)
            if d1 and d2 and (d1 == d2 or d1 in d2 or d2 in d1):
                return 30.0
            if s1 and s2 and (s1 == s2 or s1 in s2 or s2 in s1):
                return 15.0

        elif candidate.media_type == 'SERIES' and hasattr(existing, 'series_detail'):
            c1 = norm(existing.series_detail.creators)
            c2 = norm(candidate.creators)
            if c1 and c2 and (c1 == c2 or c1 in c2 or c2 in c1):
                return 30.0

        elif candidate.media_type == 'MANGA' and hasattr(existing, 'manga_detail'):
            a1 = norm(existing.manga_detail.author)
            a2 = norm(candidate.author)
            ar1 = norm(existing.manga_detail.artist)
            ar2 = norm(candidate.artist)
            if a1 and a2 and (a1 == a2 or a1 in a2 or a2 in a1):
                return 30.0
            if ar1 and ar2 and (ar1 == ar2 or ar1 in ar2 or ar2 in ar1):
                return 20.0

        elif candidate.media_type == 'GAME' and hasattr(existing, 'game_detail'):
            dev1 = norm(existing.game_detail.developer)
            dev2 = norm(candidate.developer)
            pub1 = norm(existing.game_detail.publisher)
            pub2 = norm(candidate.publisher)
            if dev1 and dev2 and (dev1 == dev2 or dev1 in dev2 or dev2 in dev1):
                return 30.0
            if pub1 and pub2 and (pub1 == pub2 or pub1 in pub2 or pub2 in pub1):
                return 15.0

        return 0.0
