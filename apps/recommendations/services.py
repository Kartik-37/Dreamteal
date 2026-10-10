"""
In-House Deterministic Recommendation Engine for DreamTeal.

Answers: "What should I watch, read, or play next?"
Uses transparent, explainable, multi-signal metadata scoring across:
1. Normalized Genre Similarity (Jaccard index)
2. Thematic & Aesthetic Vibe Tag Similarity (Jaccard index)
3. Cross-Media & Franchise Relationship (Verified franchise tags / creators)
4. Qualitative Reaction Affinity (User preferences & community Peak/Loved It verdicts)

Strict Guarantees:
- ZERO Star Ratings: No numeric averages, star mappings, or fake scores.
- Deterministic & Explainable: Every candidate includes human-readable match reasons.
- 100% Offline: Database-driven; never calls third-party APIs during recommendations.
- Privacy & Ownership: User exclusions and affinity use only the requesting user's records.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Count, Q, QuerySet

from apps.catalog.models import MediaItem
from apps.reviews.models import MediaReview
from apps.tracking.models import DiaryLog, UserMediaStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RecommendationWeights:
    """
    Tunable configuration weights for deterministic recommendation scoring.
    Provisional values that can be calibrated without schema or database migrations.
    """
    tag_similarity: float = 40.0       # Thematic vibe tags (e.g. Cyberpunk, Dark Fantasy)
    genre_similarity: float = 30.0     # Normalized genre taxonomy overlap (Jaccard)
    cross_media_link: float = 15.0     # Verified franchise or creator relationship
    reaction_affinity: float = 15.0    # User & community qualitative reaction verdicts
    min_evidence_score: float = 15.0   # Minimum total score required for inclusion


# Explicit, verified franchise/universe identifier tag slugs for cross-media relationship detection.
# Critical: Generic themes (e.g. 'cyberpunk', 'dystopian', 'dark-fantasy', 'cozy') are thematic vibe tags,
# NOT franchises, and must never be treated as verified franchise links.
KNOWN_FRANCHISE_IDENTIFIERS: Set[str] = {
    'star-wars', 'middle-earth', 'lord-of-the-rings',
    'batman-universe', 'witcher-universe', 'dune-universe',
    'marvel-cinematic-universe', 'dc-universe', 'game-of-thrones-universe',
    'dragon-ball-universe', 'one-piece-universe', 'solo-leveling-universe'
}


@dataclass
class UserPreferenceSignals:
    """
    Authenticated requesting user's qualitative reaction history.
    Strictly isolated to the requesting user; never shared across users or leaked anonymously.
    """
    preferred_genres: Set[str] = field(default_factory=set)
    preferred_tags: Set[str] = field(default_factory=set)
    disliked_genres: Set[str] = field(default_factory=set)
    disliked_tags: Set[str] = field(default_factory=set)
    not_my_thing_media_ids: Set[UUID] = field(default_factory=set)


@dataclass
class ScoredRecommendation:
    """
    Internal structured recommendation match representation.
    Retains detailed scoring breakdown, matched signals, and human-readable explanations.
    """
    candidate: MediaItem
    total_score: float
    tag_score: float
    genre_score: float
    cross_media_score: float
    reaction_score: float
    match_reasons: List[str] = field(default_factory=list)
    shared_tags: List[str] = field(default_factory=list)
    shared_genres: List[str] = field(default_factory=list)


class RecommendationEngine:
    """
    Core deterministic recommendation service for DreamTeal.
    Evaluates candidate MediaItems against a base MediaItem using content-based
    similarity, franchise detection, and user/community qualitative reaction verdicts.
    """

    def __init__(self, weights: Optional[RecommendationWeights] = None):
        self.weights = weights or RecommendationWeights()

    def get_recommendations(
        self,
        source_item: MediaItem,
        user: Optional[AbstractBaseUser] = None,
        cross_category: bool = True,
        target_category: Optional[str] = None,
        limit: int = 10
    ) -> List[ScoredRecommendation]:
        """
        Computes top deterministic "What to consume next" recommendations.

        :param source_item: Base MediaItem from which to compute recommendations.
        :param user: Requesting user (authenticated or anonymous).
        :param cross_category: If False, restricts candidates to source_item's media_type.
        :param target_category: Optional explicit category filter ('MOVIE', 'SERIES', 'MANGA', 'MANHWA', 'GAME').
        :param limit: Maximum number of ranked recommendations to return (bounded 1-50).
        :return: List of ScoredRecommendation objects ordered deterministically.
        """
        # 1. Extract source item metadata
        source_genre_slugs, source_genre_names = self._extract_genres(source_item)
        source_tag_slugs, source_tag_names = self._extract_tags(source_item)

        # If source item has no genres or tags and no franchise identifiers, no similarity can be proven
        if not source_genre_slugs and not source_tag_slugs:
            logger.info("Source item '%s' has no genres or tags. Returning empty recommendations.", source_item.slug)
            return []

        # 2. Retrieve eligible candidate queryset
        candidate_qs = self._get_candidate_queryset(
            source_item=source_item,
            user=user,
            cross_category=cross_category,
            target_category=target_category
        )

        # 3. Pre-fetch user preference signals if authenticated
        user_preferences: Optional[UserPreferenceSignals] = None
        if user and user.is_authenticated:
            user_preferences = self._get_user_preferences(user)

        # 4. Score each candidate
        scored_candidates: List[ScoredRecommendation] = []

        for candidate in candidate_qs:
            rec = self._score_candidate(
                source_item=source_item,
                candidate=candidate,
                source_genre_slugs=source_genre_slugs,
                source_genre_names=source_genre_names,
                source_tag_slugs=source_tag_slugs,
                source_tag_names=source_tag_names,
                user_preferences=user_preferences
            )
            # Only retain candidates meeting the minimum evidence threshold and with valid explanations
            if rec.total_score >= self.weights.min_evidence_score and rec.match_reasons:
                scored_candidates.append(rec)

        # 5. Deterministic tie-breaking and ranking
        ranked_candidates = self._rank_candidates(scored_candidates)

        return ranked_candidates[:limit]

    def _extract_genres(self, item: MediaItem) -> Tuple[Set[str], Dict[str, str]]:
        """Extracts genre slugs and mapping of {slug: display_name}."""
        slugs = set()
        names = {}
        for g in item.genres.all():
            slugs.add(g.slug)
            names[g.slug] = g.name
        return slugs, names

    def _extract_tags(self, item: MediaItem) -> Tuple[Set[str], Dict[str, str]]:
        """Extracts tag slugs and mapping of {slug: display_name}."""
        slugs = set()
        names = {}
        for t in item.tags.all():
            slugs.add(t.slug)
            names[t.slug] = t.name
        return slugs, names

    def _get_candidate_queryset(
        self,
        source_item: MediaItem,
        user: Optional[AbstractBaseUser],
        cross_category: bool,
        target_category: Optional[str]
    ) -> QuerySet[MediaItem]:
        """
        Builds optimized candidate queryset with prefetching, category constraints,
        and user-history exclusions.
        """
        qs = MediaItem.objects.exclude(id=source_item.id)

        # Target category or cross-category filtering
        if target_category:
            cat_upper = target_category.upper()
            if cat_upper == 'MANHWA':
                qs = qs.filter(
                    media_type=MediaItem.MediaType.MANGA,
                    manga_detail__manga_type='MANHWA'
                )
            elif cat_upper == 'MANGA':
                qs = qs.filter(
                    media_type=MediaItem.MediaType.MANGA
                ).exclude(manga_detail__manga_type='MANHWA')
            elif cat_upper in [MediaItem.MediaType.MOVIE, MediaItem.MediaType.SERIES, MediaItem.MediaType.GAME]:
                qs = qs.filter(media_type=cat_upper)
        elif not cross_category:
            # Constrain strictly to same media category
            qs = qs.filter(media_type=source_item.media_type)

        # User History Exclusions (Personalized Privacy Boundary)
        if user and user.is_authenticated:
            excluded_ids: Set[UUID] = set()

            # Status exclusions: Already watched/completed/finished, active in-progress, dropped, paused
            excluded_statuses = [
                UserMediaStatus.StatusChoices.WATCHED,
                UserMediaStatus.StatusChoices.COMPLETED,
                UserMediaStatus.StatusChoices.FINISHED,
                UserMediaStatus.StatusChoices.WATCHING,
                UserMediaStatus.StatusChoices.READING,
                UserMediaStatus.StatusChoices.PLAYING,
                UserMediaStatus.StatusChoices.DROPPED,
                UserMediaStatus.StatusChoices.PAUSED,
            ]
            status_excluded_ids = UserMediaStatus.objects.filter(
                user=user,
                status__in=excluded_statuses
            ).values_list('media_item_id', flat=True)
            excluded_ids.update(status_excluded_ids)

            # Diary log exclusions: User already consumed or logged sessions for this item
            diary_excluded_ids = DiaryLog.objects.filter(
                user=user
            ).values_list('media_item_id', flat=True)
            excluded_ids.update(diary_excluded_ids)

            # Skip review exclusions: Items user rejected
            skip_excluded_ids = MediaReview.objects.filter(
                user=user,
                reaction__key='skip'
            ).values_list('media_item_id', flat=True)
            excluded_ids.update(skip_excluded_ids)

            if excluded_ids:
                qs = qs.exclude(id__in=excluded_ids)

        # Prevent N+1 queries by selecting details and prefetching taxonomy
        qs = qs.select_related(
            'movie_detail',
            'series_detail',
            'manga_detail',
            'game_detail'
        ).prefetch_related(
            'genres',
            'tags'
        )

        return qs

    def _get_user_preferences(self, user: AbstractBaseUser) -> UserPreferenceSignals:
        """
        Retrieves user's demonstrated positive and negative qualitative reaction history.
        - Positive reviews (Peak, Loved It, Good Time): genres and tags user enjoys.
        - Negative reviews (Not My Thing): genres and tags of disliked works provide negative preference signals.
        Strictly owner-scoped to the authenticated user; never queries or leaks other users' records.
        """
        signals = UserPreferenceSignals()

        # User's positive reviews: Peak, Loved It, Good Time
        positive_reviews = MediaReview.objects.filter(
            user=user,
            reaction__key__in=['peak', 'loved_it', 'good_time']
        ).select_related('media_item').prefetch_related('media_item__genres', 'media_item__tags')

        for rev in positive_reviews:
            for g in rev.media_item.genres.all():
                signals.preferred_genres.add(g.slug)
            for t in rev.media_item.tags.all():
                signals.preferred_tags.add(t.slug)

        # User's negative preference reviews: Not My Thing
        nmt_reviews = MediaReview.objects.filter(
            user=user,
            reaction__key='not_my_thing'
        ).select_related('media_item').prefetch_related('media_item__genres', 'media_item__tags')

        for rev in nmt_reviews:
            signals.not_my_thing_media_ids.add(rev.media_item_id)
            for g in rev.media_item.genres.all():
                signals.disliked_genres.add(g.slug)
            for t in rev.media_item.tags.all():
                signals.disliked_tags.add(t.slug)

        return signals

    def _score_candidate(
        self,
        source_item: MediaItem,
        candidate: MediaItem,
        source_genre_slugs: Set[str],
        source_genre_names: Dict[str, str],
        source_tag_slugs: Set[str],
        source_tag_names: Dict[str, str],
        user_preferences: Optional[UserPreferenceSignals] = None
    ) -> ScoredRecommendation:
        """Computes multi-signal similarity score and generates explainable match reasons."""
        cand_genre_slugs, cand_genre_names = self._extract_genres(candidate)
        cand_tag_slugs, cand_tag_names = self._extract_tags(candidate)

        match_reasons: List[str] = []

        # -------------------------------------------------------------
        # Signal 1: Thematic Vibe Tag Similarity (Weight: tag_similarity)
        # -------------------------------------------------------------
        tag_score = 0.0
        shared_tag_slugs = source_tag_slugs & cand_tag_slugs
        shared_tag_names = [cand_tag_names[s] for s in shared_tag_slugs if s in cand_tag_names]

        if shared_tag_slugs:
            union_tags = source_tag_slugs | cand_tag_slugs
            jaccard_tags = len(shared_tag_slugs) / max(1, len(union_tags))
            tag_score = self.weights.tag_similarity * jaccard_tags

            # Generate tag match reason
            if len(shared_tag_names) == 1:
                match_reasons.append(f"Shares the {shared_tag_names[0]} theme.")
            elif len(shared_tag_names) <= 3:
                tags_str = " and ".join(shared_tag_names) if len(shared_tag_names) == 2 else f"{shared_tag_names[0]}, {shared_tag_names[1]}, and {shared_tag_names[2]}"
                match_reasons.append(f"Shares {tags_str} themes.")
            else:
                match_reasons.append(f"Shares multiple thematic vibes ({shared_tag_names[0]}, {shared_tag_names[1]}, +{len(shared_tag_names) - 2} more).")

        # -------------------------------------------------------------
        # Signal 2: Normalized Genre Similarity (Weight: genre_similarity)
        # -------------------------------------------------------------
        genre_score = 0.0
        shared_genre_slugs = source_genre_slugs & cand_genre_slugs
        shared_genre_names = [cand_genre_names[s] for s in shared_genre_slugs if s in cand_genre_names]

        if shared_genre_slugs:
            union_genres = source_genre_slugs | cand_genre_slugs
            jaccard_genres = len(shared_genre_slugs) / max(1, len(union_genres))
            genre_score = self.weights.genre_similarity * jaccard_genres

            if len(shared_genre_names) == 1:
                match_reasons.append(f"Shares the {shared_genre_names[0]} genre.")
            else:
                genres_str = " and ".join(shared_genre_names[:2])
                match_reasons.append(f"Shares {genres_str} genres.")

        # -------------------------------------------------------------
        # Signal 3: Cross-Media & Franchise Relationship (Weight: cross_media_link)
        # -------------------------------------------------------------
        cross_media_score, cross_media_reasons = self.check_cross_media_relationship(
            source=source_item,
            candidate=candidate,
            source_tag_slugs=source_tag_slugs,
            cand_tag_slugs=cand_tag_slugs
        )
        match_reasons.extend(cross_media_reasons)

        # -------------------------------------------------------------
        # Signal 4: Reaction Affinity (Weight: reaction_affinity)
        # -------------------------------------------------------------
        reaction_score = 0.0

        # User personal affinity (strictly for requesting user)
        if user_preferences:
            # 1. Candidate directly reviewed as Not My Thing by user
            if candidate.id in user_preferences.not_my_thing_media_ids:
                reaction_score -= 10.0

            # 2. Positive preference alignment from Peak, Loved It, Good Time
            user_shared_p_tags = cand_tag_slugs & user_preferences.preferred_tags
            user_shared_p_genres = cand_genre_slugs & user_preferences.preferred_genres
            if user_shared_p_tags or user_shared_p_genres:
                user_bonus = min(
                    self.weights.reaction_affinity * 0.5,
                    (len(user_shared_p_tags) * 3.0 + len(user_shared_p_genres) * 2.0)
                )
                reaction_score += user_bonus
                if user_shared_p_tags:
                    p_tag_name = cand_tag_names[next(iter(user_shared_p_tags))]
                    match_reasons.append(f"Matches your positive preference for {p_tag_name}.")

            # 3. Negative preference feedback from Not My Thing on candidate's genres/tags
            # Only penalize tags/genres that user disliked and does NOT also have as a positive preference
            net_disliked_tags = (cand_tag_slugs & user_preferences.disliked_tags) - user_preferences.preferred_tags
            net_disliked_genres = (cand_genre_slugs & user_preferences.disliked_genres) - user_preferences.preferred_genres
            if net_disliked_tags or net_disliked_genres:
                disliked_penalty = min(
                    self.weights.reaction_affinity * 0.5,
                    (len(net_disliked_tags) * 3.0 + len(net_disliked_genres) * 2.0)
                )
                reaction_score -= disliked_penalty

        # Community qualitative verdict consensus
        community_score, comm_reason = self._compute_community_reaction_score(candidate)
        reaction_score += community_score
        if comm_reason:
            match_reasons.append(comm_reason)

        total_score = max(0.0, tag_score + genre_score + cross_media_score + reaction_score)

        return ScoredRecommendation(
            candidate=candidate,
            total_score=round(total_score, 2),
            tag_score=round(tag_score, 2),
            genre_score=round(genre_score, 2),
            cross_media_score=round(cross_media_score, 2),
            reaction_score=round(reaction_score, 2),
            match_reasons=match_reasons,
            shared_tags=shared_tag_names,
            shared_genres=shared_genre_names
        )

    def check_cross_media_relationship(
        self,
        source: MediaItem,
        candidate: MediaItem,
        source_tag_slugs: Optional[Set[str]] = None,
        cand_tag_slugs: Optional[Set[str]] = None
    ) -> Tuple[float, List[str]]:
        """
        Detects verified franchise or cross-media relationship.
        Evaluates explicit shared universe/franchise tags and creator overlap across media.
        Reuses prefetched tag slugs to avoid repeated database queries.
        """
        score = 0.0
        reasons: List[str] = []

        # 1. Check for shared franchise/universe tags
        if source_tag_slugs is None:
            source_tag_slugs = {t.slug for t in source.tags.all()}
        if cand_tag_slugs is None:
            cand_tag_slugs = {t.slug for t in candidate.tags.all()}

        shared = source_tag_slugs & cand_tag_slugs

        for tag_slug in shared:
            if (
                tag_slug in KNOWN_FRANCHISE_IDENTIFIERS
                or tag_slug.startswith('franchise-')
                or tag_slug.startswith('universe-')
                or tag_slug.startswith('franchise:')
            ):
                score += self.weights.cross_media_link
                clean_name = (
                    tag_slug.replace('franchise-', '')
                    .replace('universe-', '')
                    .replace('franchise:', '')
                    .replace('-universe', '')
                    .replace('-', ' ')
                    .title()
                )
                reasons.append(f"Part of the {clean_name} universe.")
                return score, reasons

        # 2. Check for creator overlap across media formats
        source_creators = self._get_creator_names(source)
        cand_creators = self._get_creator_names(candidate)

        shared_creators = source_creators & cand_creators
        if shared_creators and source.media_type != candidate.media_type:
            creator_name = next(iter(shared_creators))
            score += self.weights.cross_media_link
            reasons.append(
                f"Connected by shared creator ({creator_name.title()}) across "
                f"{source.get_media_type_display()} and {candidate.get_media_type_display()}."
            )

        return score, reasons

    def _get_creator_names(self, item: MediaItem) -> Set[str]:
        """Extracts normalized creator names across media type extensions."""
        creators = set()
        invalid_names = {'', 'unknown', 'various', 'n/a', 'none'}

        def _clean_and_add(val: Optional[str]):
            if val:
                cleaned = val.strip().lower()
                if cleaned and len(cleaned) >= 3 and cleaned not in invalid_names:
                    creators.add(cleaned)

        try:
            if item.media_type == MediaItem.MediaType.MOVIE and hasattr(item, 'movie_detail') and item.movie_detail:
                _clean_and_add(item.movie_detail.director)
            elif item.media_type == MediaItem.MediaType.SERIES and hasattr(item, 'series_detail') and item.series_detail:
                _clean_and_add(item.series_detail.creators)
            elif item.media_type == MediaItem.MediaType.MANGA and hasattr(item, 'manga_detail') and item.manga_detail:
                _clean_and_add(item.manga_detail.author)
                _clean_and_add(item.manga_detail.artist)
            elif item.media_type == MediaItem.MediaType.GAME and hasattr(item, 'game_detail') and item.game_detail:
                _clean_and_add(item.game_detail.developer)
        except Exception:
            pass

        return creators

    def _compute_community_reaction_score(self, candidate: MediaItem) -> Tuple[float, Optional[str]]:
        """
        Computes bonus for candidates with positive qualitative community verdicts.
        Uses pure qualitative reaction counts (Peak and Loved It) without any numeric averages.
        Requires a meaningful sample size (total >= 3) to prevent unsupported claims.
        """
        # Count public qualitative verdicts
        public_reviews = MediaReview.objects.filter(media_item=candidate, is_public=True)
        counts = public_reviews.aggregate(
            total=Count('id'),
            peak=Count('id', filter=Q(reaction__key='peak')),
            loved_it=Count('id', filter=Q(reaction__key='loved_it'))
        )
        total = counts.get('total') or 0
        if total < 3:
            # Insufficient community evidence sample
            return 0.0, None

        positive_count = (counts.get('peak') or 0) + (counts.get('loved_it') or 0)
        positive_ratio = positive_count / total

        bonus = (self.weights.reaction_affinity * 0.5) * positive_ratio

        reason = None
        if positive_ratio >= 0.70:
            reason = "Received strong community Peak and Loved It qualitative reactions."

        return round(bonus, 2), reason

    def _rank_candidates(self, candidates: List[ScoredRecommendation]) -> List[ScoredRecommendation]:
        """
        Applies deterministic tie-breaking to candidate rankings.
        Order precedence:
        1. Total Score (descending)
        2. Number of shared tags (descending)
        3. Number of shared genres (descending)
        4. Release Year (descending, nulls last)
        5. Title (alphabetical ascending)
        6. Unique UUID id (ascending)
        """
        def tie_breaker_key(rec: ScoredRecommendation):
            return (
                -rec.total_score,
                -len(rec.shared_tags),
                -len(rec.shared_genres),
                -(rec.candidate.release_year or 0),
                rec.candidate.title.lower(),
                str(rec.candidate.id)
            )

        return sorted(candidates, key=tie_breaker_key)
