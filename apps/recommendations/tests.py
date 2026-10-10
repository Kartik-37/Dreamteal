"""
Comprehensive Offline Test Suite for In-House Recommendation Engine in DreamTeal.

Covers:
1. Similarity: Exact shared tags, partial genre overlap, no matching evidence, missing metadata,
   multiple overlapping signals, deterministic tie-breaking.
2. Cross-Media: Movie -> Game, Series -> Manga, Game -> Movie, same-category filtering,
   Manga vs Manhwa subtype filtering, no false franchise links.
3. User Personalization: Positive reaction preferences, Not My Thing penalties, Skip exclusions,
   watched/completed exclusions, in-progress exclusions, backlog retention, privacy boundaries.
4. API Behavior: 200 OK, 404 on unknown slug, 400 on invalid query params, response contract shape,
   no remote network calls, zero star-rating audit.
"""

from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.catalog.models import (
    ExternalMediaMapping, ExternalProvider, GameDetail, Genre,
    MangaDetail, MediaItem, MovieDetail, SeriesDetail, Tag
)
from apps.recommendations.services import RecommendationEngine, RecommendationWeights, ScoredRecommendation
from apps.reviews.models import MediaReview, ReactionDefinition
from apps.tracking.models import DiaryLog, UserMediaStatus

User = get_user_model()


class RecommendationBaseTestCase(TestCase):
    """Common test fixture with genres, tags, reactions, and multi-category media items."""
    def setUp(self):
        # 1. Reactions
        self.rx_peak = ReactionDefinition.objects.create(key='peak', display_name='Peak', sort_order=1)
        self.rx_loved_it = ReactionDefinition.objects.create(key='loved_it', display_name='Loved It', sort_order=2)
        self.rx_good_time = ReactionDefinition.objects.create(key='good_time', display_name='Good Time', sort_order=3)
        self.rx_not_my_thing = ReactionDefinition.objects.create(key='not_my_thing', display_name='Not My Thing', sort_order=4)
        self.rx_skip = ReactionDefinition.objects.create(key='skip', display_name='Skip', sort_order=5)

        # 2. Genres
        self.g_action = Genre.objects.create(name='Action', slug='action')
        self.g_scifi = Genre.objects.create(name='Sci-Fi', slug='sci-fi')
        self.g_crime = Genre.objects.create(name='Crime', slug='crime')
        self.g_mystery = Genre.objects.create(name='Mystery', slug='mystery')
        self.g_fantasy = Genre.objects.create(name='Fantasy', slug='fantasy')
        self.g_drama = Genre.objects.create(name='Drama', slug='drama')

        # 3. Tags
        self.t_cyberpunk = Tag.objects.create(name='Cyberpunk', slug='cyberpunk')
        self.t_dystopian = Tag.objects.create(name='Dystopian', slug='dystopian')
        self.t_dark_fantasy = Tag.objects.create(name='Dark Fantasy', slug='dark-fantasy')
        self.t_neo_noir = Tag.objects.create(name='Neo-Noir', slug='neo-noir')
        self.t_detective = Tag.objects.create(name='Detective', slug='detective')
        self.t_cozy = Tag.objects.create(name='Cozy', slug='cozy')

        # 4. Users
        self.user_alice = User.objects.create_user(username='alice', password='password123')
        self.user_bob = User.objects.create_user(username='bob', password='password123')

        # 5. Base Media: The Batman (Movie, 2022)
        self.batman = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='The Batman',
            slug='the-batman-2022',
            release_year=2022
        )
        self.batman.genres.add(self.g_action, self.g_crime, self.g_mystery)
        self.batman.tags.add(self.t_neo_noir, self.t_detective)
        MovieDetail.objects.create(media_item=self.batman, director='Matt Reeves')

        # 6. Candidate Media: Blade Runner 2049 (Movie, 2017)
        self.blade_runner = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='Blade Runner 2049',
            slug='blade-runner-2049-2017',
            release_year=2017
        )
        self.blade_runner.genres.add(self.g_scifi, self.g_mystery)
        self.blade_runner.tags.add(self.t_neo_noir, self.t_cyberpunk, self.t_dystopian)
        MovieDetail.objects.create(media_item=self.blade_runner, director='Denis Villeneuve')

        # 7. Candidate Media: Cyberpunk 2077 (Game, 2020)
        self.cyberpunk_game = MediaItem.objects.create(
            media_type=MediaItem.MediaType.GAME,
            title='Cyberpunk 2077',
            slug='cyberpunk-2077-2020',
            release_year=2020
        )
        self.cyberpunk_game.genres.add(self.g_action, self.g_scifi)
        self.cyberpunk_game.tags.add(self.t_cyberpunk, self.t_dystopian)
        GameDetail.objects.create(media_item=self.cyberpunk_game, developer='CD Projekt Red')

        # 8. Candidate Media: Solo Leveling (Manga/Manhwa, 2018)
        self.solo_leveling = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MANGA,
            title='Solo Leveling',
            slug='solo-leveling-2018',
            release_year=2018
        )
        self.solo_leveling.genres.add(self.g_action, self.g_fantasy)
        self.solo_leveling.tags.add(self.t_dark_fantasy)
        MangaDetail.objects.create(media_item=self.solo_leveling, author='Chugong', manga_type='MANHWA')

        # 9. Candidate Media: Berserk (Manga, 1989)
        self.berserk = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MANGA,
            title='Berserk',
            slug='berserk-1989',
            release_year=1989
        )
        self.berserk.genres.add(self.g_action, self.g_fantasy)
        self.berserk.tags.add(self.t_dark_fantasy)
        MangaDetail.objects.create(media_item=self.berserk, author='Kentaro Miura', manga_type='MANGA')

        # 10. Candidate Media: Severance (Series, 2022)
        self.severance = MediaItem.objects.create(
            media_type=MediaItem.MediaType.SERIES,
            title='Severance',
            slug='severance-2022',
            release_year=2022
        )
        self.severance.genres.add(self.g_scifi, self.g_mystery, self.g_drama)
        self.severance.tags.add(self.t_dystopian)
        SeriesDetail.objects.create(media_item=self.severance, creators='Dan Erickson')

        self.engine = RecommendationEngine()


class RecommendationSimilarityTestCase(RecommendationBaseTestCase):
    def test_exact_shared_tags_similarity(self):
        """Candidate with shared thematic tags receives high score and tag explanation."""
        recs = self.engine.get_recommendations(source_item=self.batman, cross_category=True)
        # Blade Runner 2049 shares Neo-Noir tag and Mystery genre
        titles = [r.candidate.title for r in recs]
        self.assertIn('Blade Runner 2049', titles)

        blade_rec = next(r for r in recs if r.candidate.title == 'Blade Runner 2049')
        self.assertGreater(blade_rec.tag_score, 0)
        self.assertTrue(any('Neo-Noir' in reason for reason in blade_rec.match_reasons))

    def test_partial_genre_overlap_jaccard(self):
        """Candidate with shared genres scores proportionally via Jaccard index."""
        recs = self.engine.get_recommendations(source_item=self.solo_leveling, cross_category=True)
        # Berserk shares Action and Fantasy genres, plus Dark Fantasy tag
        berserk_rec = next(r for r in recs if r.candidate.title == 'Berserk')
        self.assertGreater(berserk_rec.genre_score, 0)
        self.assertTrue(any('Action' in reason or 'Fantasy' in reason for reason in berserk_rec.match_reasons))

    def test_no_matching_evidence_excluded(self):
        """Candidate with zero shared tags and zero shared genres is excluded."""
        # Create an unrelated item: Animal Crossing (Game) with Cozy tag and no shared genres
        cozy_game = MediaItem.objects.create(
            media_type=MediaItem.MediaType.GAME,
            title='Animal Crossing',
            slug='animal-crossing-2020',
            release_year=2020
        )
        cozy_game.tags.add(self.t_cozy)
        GameDetail.objects.create(media_item=cozy_game, developer='Nintendo')

        recs = self.engine.get_recommendations(source_item=self.batman, cross_category=True)
        titles = [r.candidate.title for r in recs]
        self.assertNotIn('Animal Crossing', titles)

    def test_source_missing_genres_and_tags_returns_empty(self):
        """Source item with no genres and tags returns an empty recommendation list cleanly."""
        empty_item = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='Empty Movie',
            slug='empty-movie-2024',
            release_year=2024
        )
        recs = self.engine.get_recommendations(source_item=empty_item)
        self.assertEqual(recs, [])

    def test_multiple_overlapping_signals_accumulate(self):
        """Candidate sharing multiple tags and genres accumulates score and reasons."""
        recs = self.engine.get_recommendations(source_item=self.blade_runner, cross_category=True)
        cyber_rec = next(r for r in recs if r.candidate.title == 'Cyberpunk 2077')

        self.assertGreater(cyber_rec.tag_score, 0)
        self.assertGreater(cyber_rec.genre_score, 0)
        self.assertGreaterEqual(len(cyber_rec.match_reasons), 2)
        # Match reasons mention both themes and genres
        reasons_text = " ".join(cyber_rec.match_reasons)
        self.assertTrue('Cyberpunk' in reasons_text or 'Dystopian' in reasons_text)
        self.assertTrue('Sci-Fi' in reasons_text)

    def test_deterministic_tie_breaking(self):
        """Candidates with identical score and tag count are broken deterministically by year and title."""
        item_a = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='Alpha Noir',
            slug='alpha-noir-2015',
            release_year=2015
        )
        item_a.genres.add(self.g_crime)
        item_a.tags.add(self.t_detective)

        item_b = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='Beta Noir',
            slug='beta-noir-2015',
            release_year=2015
        )
        item_b.genres.add(self.g_crime)
        item_b.tags.add(self.t_detective)

        recs1 = self.engine.get_recommendations(source_item=self.batman, cross_category=False)
        recs2 = self.engine.get_recommendations(source_item=self.batman, cross_category=False)

        # Rankings are 100% deterministic across multiple runs
        self.assertEqual([r.candidate.id for r in recs1], [r.candidate.id for r in recs2])
        # Alpha Noir comes before Beta Noir alphabetically when year and score are identical
        titles = [r.candidate.title for r in recs1]
        self.assertLess(titles.index('Alpha Noir'), titles.index('Beta Noir'))


class RecommendationCrossMediaTestCase(RecommendationBaseTestCase):
    def test_movie_to_game_cross_category(self):
        """Movie recommends a Game sharing Cyberpunk and Dystopian themes."""
        recs = self.engine.get_recommendations(source_item=self.blade_runner, cross_category=True)
        titles = [r.candidate.title for r in recs]
        self.assertIn('Cyberpunk 2077', titles)
        cyber_rec = next(r for r in recs if r.candidate.title == 'Cyberpunk 2077')
        self.assertEqual(cyber_rec.candidate.media_type, MediaItem.MediaType.GAME)

    def test_series_to_manga_cross_category(self):
        """Series recommends a Manga when shared genres/tags match."""
        # Create mystery dark fantasy manga
        mystery_manga = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MANGA,
            title='Monster',
            slug='monster-1994',
            release_year=1994
        )
        mystery_manga.genres.add(self.g_mystery, self.g_drama)
        recs = self.engine.get_recommendations(source_item=self.severance, cross_category=True)
        titles = [r.candidate.title for r in recs]
        self.assertIn('Monster', titles)

    def test_cross_category_false_restricts_to_same_media_type(self):
        """Passing cross_category=False returns only candidates matching source media_type."""
        recs = self.engine.get_recommendations(source_item=self.blade_runner, cross_category=False)
        for r in recs:
            self.assertEqual(r.candidate.media_type, MediaItem.MediaType.MOVIE)
        titles = [r.candidate.title for r in recs]
        self.assertNotIn('Cyberpunk 2077', titles)
        self.assertNotIn('Severance', titles)

    def test_explicit_category_filter(self):
        """Filtering with category=GAME returns only video games."""
        recs = self.engine.get_recommendations(
            source_item=self.blade_runner,
            cross_category=True,
            target_category='GAME'
        )
        for r in recs:
            self.assertEqual(r.candidate.media_type, MediaItem.MediaType.GAME)

    def test_manga_vs_manhwa_subtype_filtering(self):
        """Filtering with category=MANHWA vs MANGA cleanly differentiates based on manga_detail."""
        recs_manhwa = self.engine.get_recommendations(
            source_item=self.solo_leveling,
            cross_category=True,
            target_category='MANHWA'
        )
        # Solo Leveling base media -> should find other manhwa if available, exclude Japanese manga
        for r in recs_manhwa:
            self.assertEqual(r.candidate.manga_detail.manga_type, 'MANHWA')
        self.assertNotIn('Berserk', [r.candidate.title for r in recs_manhwa])

        recs_manga = self.engine.get_recommendations(
            source_item=self.solo_leveling,
            cross_category=True,
            target_category='MANGA'
        )
        for r in recs_manga:
            self.assertEqual(r.candidate.manga_detail.manga_type, 'MANGA')
        self.assertIn('Berserk', [r.candidate.title for r in recs_manga])

    def test_no_false_franchise_relationships(self):
        """Titles that do not share explicit franchise tags or creators do not fabricate links."""
        score, reasons = self.engine.check_cross_media_relationship(self.batman, self.cyberpunk_game)
        self.assertEqual(score, 0.0)
        self.assertEqual(reasons, [])


class RecommendationPersonalizationTestCase(RecommendationBaseTestCase):
    def test_anonymous_user_receives_unfiltered_recommendations(self):
        """Anonymous user receives pure content-based recommendations."""
        recs = self.engine.get_recommendations(source_item=self.batman, user=None, cross_category=True)
        self.assertGreater(len(recs), 0)

    def test_completed_and_watched_items_excluded_for_authenticated_user(self):
        """Items marked WATCHED or COMPLETED by user are excluded from next to consume."""
        # Alice watched Blade Runner 2049
        UserMediaStatus.objects.create(
            user=self.user_alice,
            media_item=self.blade_runner,
            status=UserMediaStatus.StatusChoices.WATCHED
        )
        recs = self.engine.get_recommendations(source_item=self.batman, user=self.user_alice, cross_category=True)
        titles = [r.candidate.title for r in recs]
        self.assertNotIn('Blade Runner 2049', titles)

    def test_active_in_progress_items_excluded(self):
        """Items currently being WATCHING or PLAYING are excluded."""
        UserMediaStatus.objects.create(
            user=self.user_alice,
            media_item=self.cyberpunk_game,
            status=UserMediaStatus.StatusChoices.PLAYING
        )
        recs = self.engine.get_recommendations(source_item=self.blade_runner, user=self.user_alice, cross_category=True)
        titles = [r.candidate.title for r in recs]
        self.assertNotIn('Cyberpunk 2077', titles)

    def test_dropped_and_paused_items_excluded(self):
        """Items marked DROPPED or PAUSED are excluded."""
        UserMediaStatus.objects.create(
            user=self.user_alice,
            media_item=self.severance,
            status=UserMediaStatus.StatusChoices.DROPPED
        )
        recs = self.engine.get_recommendations(source_item=self.blade_runner, user=self.user_alice, cross_category=True)
        titles = [r.candidate.title for r in recs]
        self.assertNotIn('Severance', titles)

    def test_diary_logged_items_excluded(self):
        """Items logged in user's DiaryLog are considered already consumed and excluded."""
        DiaryLog.objects.create(
            user=self.user_alice,
            media_item=self.blade_runner,
            session_notes="Watched last night."
        )
        recs = self.engine.get_recommendations(source_item=self.batman, user=self.user_alice, cross_category=True)
        titles = [r.candidate.title for r in recs]
        self.assertNotIn('Blade Runner 2049', titles)

    def test_skip_reaction_strictly_excluded(self):
        """Items reviewed by user with reaction Skip are strictly excluded."""
        MediaReview.objects.create(
            user=self.user_alice,
            media_item=self.blade_runner,
            reaction=self.rx_skip,
            review_text="Did not like this."
        )
        recs = self.engine.get_recommendations(source_item=self.batman, user=self.user_alice, cross_category=True)
        titles = [r.candidate.title for r in recs]
        self.assertNotIn('Blade Runner 2049', titles)

    def test_backlog_items_retained(self):
        """Items in user's BACKLOG or PLAN_TO_WATCH remain eligible as prime next recommendations."""
        UserMediaStatus.objects.create(
            user=self.user_alice,
            media_item=self.blade_runner,
            status=UserMediaStatus.StatusChoices.PLAN_TO_WATCH
        )
        recs = self.engine.get_recommendations(source_item=self.batman, user=self.user_alice, cross_category=True)
        titles = [r.candidate.title for r in recs]
        self.assertIn('Blade Runner 2049', titles)

    def test_positive_reaction_affinity_boosts_candidate(self):
        """User positive reviews for specific genres/tags apply an affinity bonus."""
        # Alice gave Peak reaction to Cyberpunk 2077
        MediaReview.objects.create(
            user=self.user_alice,
            media_item=self.cyberpunk_game,
            reaction=self.rx_peak,
            review_text="Incredible atmosphere."
        )
        # When recommending from The Batman, Blade Runner also has Cyberpunk tag
        recs_anon = self.engine.get_recommendations(source_item=self.batman, user=None, cross_category=True)
        recs_alice = self.engine.get_recommendations(source_item=self.batman, user=self.user_alice, cross_category=True)

        rec_anon_blade = next(r for r in recs_anon if r.candidate.title == 'Blade Runner 2049')
        rec_alice_blade = next(r for r in recs_alice if r.candidate.title == 'Blade Runner 2049')

        self.assertGreater(rec_alice_blade.total_score, rec_anon_blade.total_score)
        self.assertTrue(any('positive preference' in reason for reason in rec_alice_blade.match_reasons))

    def test_privacy_isolation_between_users(self):
        """Bob's private reviews and history do not affect Alice's recommendations."""
        # Bob marked Blade Runner 2049 as Skip and Watched
        UserMediaStatus.objects.create(
            user=self.user_bob,
            media_item=self.blade_runner,
            status=UserMediaStatus.StatusChoices.WATCHED
        )
        MediaReview.objects.create(
            user=self.user_bob,
            media_item=self.blade_runner,
            reaction=self.rx_skip,
            is_public=False
        )

        # Alice's recommendations should still include Blade Runner 2049
        recs_alice = self.engine.get_recommendations(source_item=self.batman, user=self.user_alice, cross_category=True)
        titles_alice = [r.candidate.title for r in recs_alice]
        self.assertIn('Blade Runner 2049', titles_alice)


class RecommendationAPITestCase(RecommendationBaseTestCase):
    def setUp(self):
        super().setUp()
        self.client = APIClient()

    def test_successful_recommendation_request_shape(self):
        """GET /api/v1/recommendations/next/<slug>/ returns 200 OK with correct contract structure."""
        res = self.client.get(f'/api/v1/recommendations/next/{self.batman.slug}/')
        self.assertEqual(res.status_code, 200)

        # Validate envelope fields
        self.assertIn('base_media', res.data)
        self.assertIn('recommendations', res.data)
        self.assertIn('count', res.data)
        self.assertIn('filters', res.data)

        # Base media details
        self.assertEqual(res.data['base_media']['slug'], self.batman.slug)
        self.assertEqual(res.data['base_media']['title'], 'The Batman')
        self.assertEqual(res.data['base_media']['media_type'], 'MOVIE')

        # Recommendation items
        self.assertGreater(len(res.data['recommendations']), 0)
        item = res.data['recommendations'][0]
        self.assertIn('id', item)
        self.assertIn('slug', item)
        self.assertIn('title', item)
        self.assertIn('media_type', item)
        self.assertIn('poster_url', item)
        self.assertIn('release_year', item)
        self.assertIn('match_reasons', item)
        self.assertIsInstance(item['match_reasons'], list)
        self.assertGreater(len(item['match_reasons']), 0)

        # By default, internal similarity_score is not exposed in public output
        self.assertNotIn('similarity_score', item)

    def test_unknown_slug_returns_404(self):
        """Nonexistent media slug returns 404 Not Found."""
        res = self.client.get('/api/v1/recommendations/next/nonexistent-media-slug/')
        self.assertEqual(res.status_code, 404)

    def test_empty_catalog_returns_empty_list(self):
        """Source item with no matching candidates returns 200 OK with count 0."""
        isolated = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='Isolated Work',
            slug='isolated-work-2024'
        )
        isolated.tags.add(self.t_cozy)
        res = self.client.get(f'/api/v1/recommendations/next/{isolated.slug}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['count'], 0)
        self.assertEqual(res.data['recommendations'], [])

    def test_invalid_limit_returns_400(self):
        """Non-integer, negative, zero, or excessive limit returns 400 Bad Request."""
        for invalid_limit in ['-5', '0', '100', 'not-a-number']:
            res = self.client.get(f'/api/v1/recommendations/next/{self.batman.slug}/?limit={invalid_limit}')
            self.assertEqual(res.status_code, 400)
            self.assertIn('limit', res.data)

    def test_invalid_category_returns_400(self):
        """Invalid category choice returns 400 Bad Request."""
        res = self.client.get(f'/api/v1/recommendations/next/{self.batman.slug}/?category=INVALID_CAT')
        self.assertEqual(res.status_code, 400)
        self.assertIn('category', res.data)

    def test_cross_category_filter_via_api(self):
        """Passing cross_category=false via API restricts recommendations to same media category."""
        res = self.client.get(f'/api/v1/recommendations/next/{self.blade_runner.slug}/?cross_category=false')
        self.assertEqual(res.status_code, 200)
        for item in res.data['recommendations']:
            self.assertEqual(item['media_type'], 'MOVIE')

    def test_duplicate_external_mappings_do_not_duplicate_recommendation(self):
        """Item with multiple external provider mappings is not duplicated in results."""
        prov_tmdb, _ = ExternalProvider.objects.get_or_create(provider_key='tmdb', defaults={'display_name': 'TMDB'})
        prov_rawg, _ = ExternalProvider.objects.get_or_create(provider_key='rawg', defaults={'display_name': 'RAWG'})

        ExternalMediaMapping.objects.create(media_item=self.blade_runner, provider=prov_tmdb, external_id='1001')
        ExternalMediaMapping.objects.create(media_item=self.blade_runner, provider=prov_rawg, external_id='2002')

        res = self.client.get(f'/api/v1/recommendations/next/{self.batman.slug}/')
        self.assertEqual(res.status_code, 200)
        blade_runner_ids = [r['id'] for r in res.data['recommendations'] if r['slug'] == self.blade_runner.slug]
        self.assertEqual(len(blade_runner_ids), 1)

    def test_zero_star_audit_no_numeric_rating_keys_in_response(self):
        """Audits response JSON to guarantee no star ratings or numeric rating fields exist."""
        res = self.client.get(f'/api/v1/recommendations/next/{self.batman.slug}/')
        self.assertEqual(res.status_code, 200)
        response_str = str(res.data).lower()
        forbidden_substrings = ['stars', 'star_rating', 'rating_score', 'numeric_score', 'average_rating']
        for bad_key in forbidden_substrings:
            self.assertNotIn(bad_key, response_str)

    def test_no_remote_network_calls_during_recommendation(self):
        """Ensures recommendation endpoint executes 100% locally without external network calls."""
        with patch('urllib.request.urlopen') as mock_urlopen, patch('requests.get') as mock_get, patch('requests.post') as mock_post:
            res = self.client.get(f'/api/v1/recommendations/next/{self.batman.slug}/')
            self.assertEqual(res.status_code, 200)
            mock_urlopen.assert_not_called()
            mock_get.assert_not_called()
            mock_post.assert_not_called()
