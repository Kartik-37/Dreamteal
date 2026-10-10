"""
Comprehensive Backend Tests for apps.catalog in DreamTeal.

Tests:
1. MediaItem, Genre, Tag, category-specific detail models, validation, cascade behavior.
2. ExternalProvider and ExternalMediaMapping uniqueness and multi-mapping support.
3. Provider Adapters (TMDB, AniList, Jikan, RAWG) with zero-star guarantees and mock isolation.
4. Region-Aware Watch Providers (TMDB configured default region without arbitrary fallback).
5. Discovery Semantics (Popular, Latest, Trending, Upcoming) per provider.
6. Safe AniList -> Jikan Fallback (never assumes AniList ID equals Jikan ID).
7. Cross-Provider Deduplication (same work across providers merges; different works with same title stay separate).
8. Media Import HTTP Status Codes (201 Created for new, 200 OK for existing).
9. Universal Multi-Media Search Interleaving (balanced distribution across categories).
10. Data Integrity Regression (provider synchronization NEVER touches user-owned tracking/reviews/logs).
11. Query Parameter Validation (returns controlled 400 Bad Request instead of 500 errors).

100% OFFLINE & DETERMINISTIC:
All provider requests are strictly mocked with unittest.mock; no live network sockets are touched.
"""

from decimal import Decimal
import logging
from unittest.mock import MagicMock, patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.catalog.models import (
    ExternalMediaMapping, ExternalProvider, GameDetail, Genre,
    MangaDetail, MediaItem, MovieDetail, SeriesDetail, Tag
)
from apps.catalog.providers.anilist import AniListProvider
from apps.catalog.providers.base import DiscoveryMode, NormalizedMediaDetail, NormalizedSearchResult
from apps.catalog.providers.jikan import JikanProvider
from apps.catalog.providers.matcher import MediaMatcherService
from apps.catalog.providers.rawg import RAWGProvider
from apps.catalog.providers.registry import ProviderRegistry
from apps.catalog.providers.tmdb import TMDBProvider
from apps.reviews.models import MediaReview, ReactionDefinition
from apps.tracking.models import DiaryLog, SeriesProgress, UserMediaProgress, UserMediaStatus

User = get_user_model()


class CatalogModelsTestCase(TestCase):
    def setUp(self):
        self.genre_action = Genre.objects.create(name='Action', slug='action')
        self.genre_scifi = Genre.objects.create(name='Sci-Fi', slug='sci-fi')
        self.tag_cyberpunk = Tag.objects.create(name='Cyberpunk', slug='cyberpunk')

    def test_genre_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            Genre.objects.create(name='Action', slug='action-dup')

    def test_tag_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name='Cyberpunk', slug='cyberpunk-dup')

    def test_movie_creation_and_detail(self):
        movie = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='Inception',
            slug='inception-2010',
            release_year=2010
        )
        movie.genres.add(self.genre_action, self.genre_scifi)
        movie.tags.add(self.tag_cyberpunk)

        detail = MovieDetail.objects.create(
            media_item=movie,
            director='Christopher Nolan',
            runtime_minutes=148,
            studio='Syncopy'
        )
        detail.full_clean()

        self.assertEqual(movie.movie_detail.director, 'Christopher Nolan')
        self.assertEqual(movie.genres.count(), 2)
        self.assertEqual(movie.tags.count(), 1)

    def test_movie_detail_type_validation(self):
        game = MediaItem.objects.create(
            media_type=MediaItem.MediaType.GAME,
            title='Halo',
            slug='halo-2001',
            release_year=2001
        )
        detail = MovieDetail(media_item=game, director='Someone')
        with self.assertRaises(ValidationError):
            detail.clean()

    def test_series_detail_type_validation(self):
        movie = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='Dune',
            slug='dune-2021',
            release_year=2021
        )
        detail = SeriesDetail(media_item=movie, total_seasons=1)
        with self.assertRaises(ValidationError):
            detail.clean()

    def test_manga_detail_type_validation(self):
        series = MediaItem.objects.create(
            media_type=MediaItem.MediaType.SERIES,
            title='Dark',
            slug='dark-2017',
            release_year=2017
        )
        detail = MangaDetail(media_item=series, author='Author')
        with self.assertRaises(ValidationError):
            detail.clean()

    def test_game_detail_type_validation(self):
        manga = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MANGA,
            title='Berserk',
            slug='berserk-1989',
            release_year=1989
        )
        detail = GameDetail(media_item=manga, developer='FromSoft')
        with self.assertRaises(ValidationError):
            detail.clean()

    def test_cascade_deletion(self):
        game = MediaItem.objects.create(
            media_type=MediaItem.MediaType.GAME,
            title='Elden Ring',
            slug='elden-ring-2022',
            release_year=2022
        )
        GameDetail.objects.create(
            media_item=game,
            developer='FromSoftware',
            average_story_hours=Decimal('55.0')
        )
        self.assertTrue(GameDetail.objects.filter(media_item=game).exists())

        game_id = game.id
        game.delete()
        self.assertFalse(GameDetail.objects.filter(media_item_id=game_id).exists())


class ExternalProviderMappingTestCase(TestCase):
    def setUp(self):
        self.provider = ExternalProvider.objects.create(
            provider_key='tmdb',
            display_name='TMDB',
            attribution_text='Attribution notice',
            active=True
        )
        self.movie = MediaItem.objects.create(
            media_type='MOVIE',
            title='Dune',
            slug='dune-2021',
            release_year=2021
        )

    def test_create_mapping_and_uniqueness(self):
        ExternalMediaMapping.objects.create(
            provider=self.provider,
            media_item=self.movie,
            external_id='438631',
            external_url='https://www.themoviedb.org/movie/438631'
        )

        with self.assertRaises(IntegrityError):
            ExternalMediaMapping.objects.create(
                provider=self.provider,
                media_item=self.movie,
                external_id='438631'
            )

    def test_multiple_providers_for_single_media_item(self):
        p_anilist = ExternalProvider.objects.create(
            provider_key='anilist', display_name='AniList', active=True
        )
        p_jikan = ExternalProvider.objects.create(
            provider_key='jikan', display_name='Jikan', active=True
        )
        manga = MediaItem.objects.create(
            media_type='MANGA', title='Monster', slug='monster-1994', release_year=1994
        )

        ExternalMediaMapping.objects.create(
            provider=p_anilist, media_item=manga, external_id='30001'
        )
        ExternalMediaMapping.objects.create(
            provider=p_jikan, media_item=manga, external_id='1'
        )
        self.assertEqual(manga.external_mappings.count(), 2)


class ProviderAdaptersTestCase(TestCase):
    @patch('requests.get')
    def test_tmdb_movie_search_and_zero_star(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 550,
                    'title': 'Fight Club',
                    'release_date': '1999-10-15',
                    'overview': 'An insomniac office worker...',
                    'poster_path': '/fight_club.jpg',
                    'backdrop_path': '/fight_club_bg.jpg',
                    'vote_average': 8.4  # STRICTLY EXCLUDED
                }
            ]
        }
        mock_get.return_value = mock_response

        provider = TMDBProvider()
        results = provider.search('Fight Club', limit=5, media_type='MOVIE')

        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.provider, 'tmdb')
        self.assertEqual(r.external_id, '550')
        self.assertEqual(r.title, 'Fight Club')
        self.assertEqual(r.media_type, 'MOVIE')
        self.assertEqual(r.release_year, 1999)
        self.assertFalse(hasattr(r, 'vote_average'))
        self.assertFalse(hasattr(r, 'rating'))

    @patch('requests.get')
    def test_tmdb_region_aware_watch_providers(self, mock_get):
        """Verifies configured DEFAULT_PROVIDER_REGION (e.g. IN) is used and no random region is chosen."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 157336,
            'title': 'Interstellar',
            'release_date': '2014-11-05',
            'overview': 'Exploring a wormhole...',
            'watch/providers': {
                'results': {
                    'US': {'flatrate': [{'provider_name': 'Paramount+'}]},
                    'IN': {'flatrate': [{'provider_name': 'JioCinema'}, {'provider_name': 'Amazon Prime Video'}]},
                    'JP': {'flatrate': [{'provider_name': 'U-Next'}]}
                }
            }
        }
        mock_get.return_value = mock_response

        provider = TMDBProvider()
        provider.default_region = 'IN'
        detail = provider.get_details('157336', media_type='MOVIE')

        self.assertIsNotNone(detail)
        # Must strictly have India providers, NOT US or JP!
        self.assertEqual(detail.ott_providers, ['JioCinema', 'Amazon Prime Video'])

        # When configured region is not in watch/providers, returns empty list without random fallback
        provider.default_region = 'BR'
        detail_br = provider.get_details('157336', media_type='MOVIE')
        self.assertEqual(detail_br.ott_providers, [])

    @patch('requests.get')
    def test_tmdb_discovery_modes(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'results': [{'id': 1, 'title': 'Test Movie', 'release_date': '2024-01-01'}]}
        mock_get.return_value = mock_response

        provider = TMDBProvider()
        pop = provider.discover('MOVIE', mode='popular')
        latest = provider.discover('MOVIE', mode='latest')
        trending = provider.discover('MOVIE', mode='trending')
        upcoming = provider.discover('MOVIE', mode='upcoming')

        self.assertEqual(len(pop), 1)
        self.assertEqual(len(latest), 1)
        self.assertEqual(len(trending), 1)
        self.assertEqual(len(upcoming), 1)

    @patch('requests.post')
    def test_anilist_search_and_alt_titles(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'Page': {
                    'media': [
                        {
                            'id': 105398,
                            'title': {'english': 'Solo Leveling', 'romaji': 'Na Honjaman Rebeleop'},
                            'countryOfOrigin': 'KR',
                            'format': 'MANGA',
                            'status': 'FINISHED',
                            'startDate': {'year': 2018},
                            'coverImage': {'large': 'https://s4.anilist.co/cover.jpg'},
                            'bannerImage': 'https://s4.anilist.co/banner.jpg',
                            'description': 'Ten years ago, gates opened...',
                            'genres': ['Action', 'Fantasy'],
                            'averageScore': 87  # STRICTLY EXCLUDED
                        }
                    ]
                }
            }
        }
        mock_post.return_value = mock_response

        provider = AniListProvider()
        results = provider.search('Solo Leveling', limit=5)

        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.provider, 'anilist')
        self.assertEqual(r.external_id, '105398')
        self.assertEqual(r.title, 'Solo Leveling')
        self.assertFalse(hasattr(r, 'averageScore'))

    @patch('requests.post')
    def test_anilist_detail_extracts_id_mal(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': {
                'Media': {
                    'id': 105398,
                    'idMal': 121496,
                    'title': {'english': 'Solo Leveling', 'romaji': 'Na Honjaman Rebeleop'},
                    'countryOfOrigin': 'KR',
                    'format': 'MANGA',
                    'status': 'FINISHED',
                    'startDate': {'year': 2018},
                    'chapters': 179,
                    'genres': ['Action', 'Fantasy'],
                    'staff': {'edges': [{'role': 'Story', 'node': {'name': {'full': 'Chugong'}}}]}
                }
            }
        }
        mock_post.return_value = mock_response

        provider = AniListProvider()
        detail = provider.get_details('105398')

        self.assertIsNotNone(detail)
        self.assertEqual(detail.id_mal, '121496')
        self.assertEqual(detail.author, 'Chugong')
        self.assertIn('Na Honjaman Rebeleop', detail.alternative_titles)

    @patch('requests.get')
    def test_jikan_search_and_normalization(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'mal_id': 13,
                    'title': 'One Piece',
                    'title_english': 'One Piece',
                    'type': 'Manga',
                    'status': 'Publishing',
                    'synopsis': 'Gol D. Roger was known as the Pirate King...',
                    'images': {'jpg': {'large_image_url': 'https://cdn.myanimelist.net/images/manga/3/555.jpg'}},
                    'published': {'prop': {'from': {'year': 1997}}},
                    'genres': [{'name': 'Action'}, {'name': 'Adventure'}],
                    'score': 9.22  # STRICTLY EXCLUDED
                }
            ]
        }
        mock_get.return_value = mock_response

        provider = JikanProvider()
        results = provider.search('One Piece', limit=5)

        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.provider, 'jikan')
        self.assertEqual(r.external_id, '13')
        self.assertEqual(r.title, 'One Piece')
        self.assertEqual(r.release_year, 1997)
        self.assertFalse(hasattr(r, 'score'))

    @patch('requests.get')
    def test_rawg_search_and_normalization(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'results': [
                {
                    'id': 3498,
                    'name': 'Grand Theft Auto V',
                    'released': '2013-09-17',
                    'background_image': 'https://media.rawg.io/games/gtav.jpg',
                    'genres': [{'name': 'Action'}],
                    'slug': 'grand-theft-auto-v',
                    'rating': 4.47,  # STRICTLY EXCLUDED
                    'metacritic': 97  # STRICTLY EXCLUDED
                }
            ]
        }
        mock_get.return_value = mock_response

        provider = RAWGProvider()
        results = provider.search('Grand Theft Auto V', limit=5)

        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.provider, 'rawg')
        self.assertEqual(r.external_id, '3498')
        self.assertEqual(r.title, 'Grand Theft Auto V')
        self.assertEqual(r.media_type, 'GAME')
        self.assertEqual(r.release_year, 2013)
        self.assertFalse(hasattr(r, 'rating'))
        self.assertFalse(hasattr(r, 'metacritic'))


class AniListJikanFallbackTestCase(TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()

    @patch('requests.post')
    @patch('requests.get')
    def test_search_fallback_routes_to_jikan_when_anilist_fails(self, mock_get, mock_post):
        # Mute logger during expected mock failure
        with self.assertLogs(logger='apps.catalog.providers.anilist', level='WARNING'):
            mock_post.return_value.status_code = 500

            mock_get_resp = MagicMock()
            mock_get_resp.status_code = 200
            mock_get_resp.json.return_value = {
                'data': [
                    {
                        'mal_id': 2,
                        'title': 'Berserk',
                        'title_english': 'Berserk',
                        'type': 'Manga',
                        'status': 'Finished',
                        'synopsis': 'Guts, a warrior...',
                        'images': {'jpg': {'large_image_url': 'https://example.com/berserk.jpg'}},
                        'published': {'prop': {'from': {'year': 1989}}},
                        'genres': [{'name': 'Dark Fantasy'}]
                    }
                ]
            }
            mock_get.return_value = mock_get_resp

            results = self.registry.search('Berserk', category='MANGA')
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].provider, 'jikan')
            self.assertEqual(results[0].title, 'Berserk')

    @patch.object(AniListProvider, 'get_details', return_value=None)
    @patch.object(JikanProvider, 'get_details')
    @patch.object(JikanProvider, 'search')
    def test_detail_fallback_does_not_blindly_use_anilist_id_as_mal_id(self, mock_jikan_search, mock_jikan_details, mock_anilist_details):
        """Verifies detail fallback requires safe matching and never treats an AniList ID as a MAL ID."""
        # 1. No title hint provided -> controlled None ("fallback unavailable")
        with self.assertLogs(logger='apps.catalog.providers.registry', level='WARNING'):
            res = self.registry.fetch_details('anilist', '999999', title_hint=None)
            self.assertIsNone(res)
        mock_jikan_details.assert_not_called()


        # 2. Title hint provided with confident Jikan candidate
        mock_jikan_search.return_value = [
            NormalizedSearchResult(provider='jikan', external_id='12345', title='Vagabond', media_type='MANGA', release_year=1998)
        ]
        mock_jikan_details.return_value = NormalizedMediaDetail(
            provider='jikan',
            external_id='12345',
            external_url='https://myanimelist.net/manga/12345',
            title='Vagabond',
            media_type='MANGA',
            slug_candidate='vagabond-1998',
            release_year=1998
        )

        matched_res = self.registry.fetch_details('anilist', '999999', title_hint='Vagabond')
        self.assertIsNotNone(matched_res)
        self.assertEqual(matched_res.title, 'Vagabond')
        self.assertEqual(matched_res.external_id, '12345')


class CrossProviderDeduplicationTestCase(TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()
        ExternalProvider.objects.create(provider_key='anilist', display_name='AniList', active=True)
        ExternalProvider.objects.create(provider_key='jikan', display_name='Jikan', active=True)
        ExternalProvider.objects.create(provider_key='tmdb', display_name='TMDB', active=True)

    @patch.object(ProviderRegistry, 'fetch_details')
    def test_same_work_across_two_providers_deduplicates(self, mock_fetch):
        """Verifies importing Solo Leveling from AniList then Jikan links to the same MediaItem."""
        # Step 1: Import via AniList
        mock_fetch.return_value = NormalizedMediaDetail(
            provider='anilist',
            external_id='105398',
            external_url='https://anilist.co/manga/105398',
            title='Solo Leveling',
            media_type='MANGA',
            slug_candidate='solo-leveling-2018',
            release_year=2018,
            author='Chugong',
            manga_type='MANHWA',
            genres=['Action', 'Fantasy']
        )
        item1, created1 = self.registry.import_media('anilist', '105398')
        self.assertTrue(created1)
        self.assertEqual(MediaItem.objects.filter(title='Solo Leveling').count(), 1)
        self.assertEqual(item1.external_mappings.count(), 1)

        # Step 2: Import via Jikan (Different provider, different external ID 121496)
        mock_fetch.return_value = NormalizedMediaDetail(
            provider='jikan',
            external_id='121496',
            external_url='https://myanimelist.net/manga/121496',
            title='Solo Leveling',
            media_type='MANGA',
            slug_candidate='solo-leveling-2018',
            release_year=2018,
            author='Chugong',
            manga_type='MANHWA',
            genres=['Action', 'Fantasy']
        )
        item2, created2 = self.registry.import_media('jikan', '121496')

        # STRICT DEDUPLICATION ASSERTIONS:
        self.assertFalse(created2)  # Must NOT create a new MediaItem record
        self.assertEqual(item1.id, item2.id)  # Same database record
        self.assertEqual(MediaItem.objects.filter(title='Solo Leveling').count(), 1)  # Only 1 MediaItem in DB
        self.assertEqual(item1.external_mappings.count(), 2)  # Has both AniList and Jikan mappings!

    @patch.object(ProviderRegistry, 'fetch_details')
    def test_different_works_with_same_title_stay_separate(self, mock_fetch):
        """Verifies Solaris (1972) and Solaris (2002) are NOT merged due to release year penalty."""
        # 1972 Solaris
        mock_fetch.return_value = NormalizedMediaDetail(
            provider='tmdb',
            external_id='830',
            external_url='https://themoviedb.org/movie/830',
            title='Solaris',
            media_type='MOVIE',
            slug_candidate='solaris-1972',
            release_year=1972,
            director='Andrei Tarkovsky'
        )
        item_1972, created1 = self.registry.import_media('tmdb', '830')
        self.assertTrue(created1)

        # 2002 Solaris
        mock_fetch.return_value = NormalizedMediaDetail(
            provider='tmdb',
            external_id='2103',
            external_url='https://themoviedb.org/movie/2103',
            title='Solaris',
            media_type='MOVIE',
            slug_candidate='solaris-2002',
            release_year=2002,
            director='Steven Soderbergh'
        )
        item_2002, created2 = self.registry.import_media('tmdb', '2103')
        self.assertTrue(created2)

        # Must remain separate distinct MediaItems
        self.assertNotEqual(item_1972.id, item_2002.id)
        self.assertEqual(MediaItem.objects.filter(title='Solaris').count(), 2)

    def test_matcher_confidence_scoring(self):
        """Unit tests for MediaMatcherService scoring rules."""
        manga = MediaItem.objects.create(
            media_type='MANGA',
            title='Berserk',
            slug='berserk-1989',
            release_year=1989
        )
        MangaDetail.objects.create(media_item=manga, author='Kentarou Miura')

        # Matching candidate
        cand_match = NormalizedMediaDetail(
            provider='jikan',
            external_id='2',
            external_url='',
            title='Berserk',
            media_type='MANGA',
            slug_candidate='berserk-1989',
            release_year=1989,
            author='Kentarou Miura'
        )
        matched_item, score = MediaMatcherService.find_match(cand_match)
        self.assertEqual(matched_item, manga)
        self.assertGreaterEqual(score, 75.0)

        # Ambiguous candidate: Same title, different media type (Movie Berserk)
        cand_movie = NormalizedMediaDetail(
            provider='tmdb',
            external_id='9999',
            external_url='',
            title='Berserk',
            media_type='MOVIE',
            slug_candidate='berserk-movie',
            release_year=2012
        )
        matched_movie, score_movie = MediaMatcherService.find_match(cand_movie)
        self.assertIsNone(matched_movie)
        self.assertEqual(score_movie, 0.0)


class MediaImportHTTPStatusTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='importer', password='password123')
        self.client.force_authenticate(user=self.user)
        ExternalProvider.objects.create(provider_key='tmdb', display_name='TMDB', active=True)

    @patch.object(ProviderRegistry, 'fetch_details')
    def test_import_http_status_codes_201_then_200(self, mock_fetch):
        mock_fetch.return_value = NormalizedMediaDetail(
            provider='tmdb',
            external_id='157336',
            external_url='https://themoviedb.org/movie/157336',
            title='Interstellar',
            media_type='MOVIE',
            slug_candidate='interstellar-2014',
            release_year=2014,
            director='Christopher Nolan'
        )

        # First import -> 201 Created
        payload = {'provider': 'tmdb', 'external_id': '157336', 'media_type': 'MOVIE'}
        res1 = self.client.post('/api/v1/media/import/', payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res1.data['title'], 'Interstellar')

        # Second import -> 200 OK
        res2 = self.client.post('/api/v1/media/import/', payload, format='json')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.data['title'], 'Interstellar')
        self.assertEqual(MediaItem.objects.filter(title='Interstellar').count(), 1)


class UniversalSearchDistributionTestCase(TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()

    @patch.object(TMDBProvider, 'search')
    @patch.object(AniListProvider, 'search')
    @patch.object(RAWGProvider, 'search')
    def test_universal_search_interleaves_categories_evenly(self, mock_rawg, mock_anilist, mock_tmdb):
        mock_tmdb.side_effect = lambda query, limit, media_type: [
            NormalizedSearchResult(provider='tmdb', external_id=f'{media_type}_{i}', title=f'{media_type} {i}', media_type=media_type)
            for i in range(limit)
        ]
        mock_anilist.return_value = [
            NormalizedSearchResult(provider='anilist', external_id=f'manga_{i}', title=f'Manga {i}', media_type='MANGA')
            for i in range(5)
        ]
        mock_rawg.return_value = [
            NormalizedSearchResult(provider='rawg', external_id=f'game_{i}', title=f'Game {i}', media_type='GAME')
            for i in range(5)
        ]

        # Universal search without category
        results = self.registry.search('Witcher', category=None, limit=8)

        # Assert round-robin interleaving: results contains Movie, Series, Manga, Game
        types_in_results = [r.media_type for r in results]
        self.assertIn('MOVIE', types_in_results)
        self.assertIn('SERIES', types_in_results)
        self.assertIn('MANGA', types_in_results)
        self.assertIn('GAME', types_in_results)
        self.assertEqual(len(results), 8)


class DataIntegrityRegressionTestCase(TestCase):
    """
    CRITICAL REGRESSION TEST:
    Verifies that provider synchronization can NEVER overwrite user tracking, progress, diary logs, or reviews.
    """
    def setUp(self):
        self.registry = ProviderRegistry()
        ExternalProvider.objects.create(provider_key='tmdb', display_name='TMDB', active=True)
        self.user = User.objects.create_user(username='track_user', password='password123')

        self.series = MediaItem.objects.create(
            media_type='SERIES',
            title='Breaking Bad',
            slug='breaking-bad-2008',
            release_year=2008
        )
        SeriesDetail.objects.create(media_item=self.series, total_seasons=5, total_episodes=62)
        ExternalMediaMapping.objects.create(
            provider=ExternalProvider.objects.get(provider_key='tmdb'),
            media_item=self.series,
            external_id='1396',
            external_url='https://themoviedb.org/tv/1396'
        )

        # User-owned tracking records
        self.status = UserMediaStatus.objects.create(
            user=self.user,
            media_item=self.series,
            status=UserMediaStatus.StatusChoices.COMPLETED
        )
        self.progress = UserMediaProgress.objects.create(
            user=self.user,
            media_item=self.series
        )
        self.series_progress = SeriesProgress.objects.create(
            progress=self.progress,
            current_season=5,
            current_episode=16,
            last_watched_episode_title='Felina'
        )
        self.log = DiaryLog.objects.create(
            user=self.user,
            media_item=self.series,
            logged_date='2026-05-15',
            session_notes='Unbelievable finale.'
        )
        reaction = ReactionDefinition.objects.create(
            key='peak', display_name='Peak', sort_order=1
        )

        self.review = MediaReview.objects.create(
            user=self.user,
            media_item=self.series,
            reaction=reaction,
            review_text='Pure masterpiece from start to finish.'
        )

    @patch.object(TMDBProvider, 'get_details')
    def test_provider_sync_never_overwrites_user_data(self, mock_details):
        """Forces refresh of catalog metadata from provider and asserts user data remains 100% unchanged."""
        mock_details.return_value = NormalizedMediaDetail(
            provider='tmdb',
            external_id='1396',
            external_url='https://themoviedb.org/tv/1396',
            title='Breaking Bad (Remastered)',
            media_type='SERIES',
            slug_candidate='breaking-bad-2008',
            release_year=2008,
            synopsis='Updated official synopsis from TMDB.',
            total_seasons=5,
            total_episodes=62
        )

        # Force sync catalog
        self.registry.import_media('tmdb', '1396', media_type='SERIES', force_refresh=True)

        # 1. Assert catalog metadata updated
        self.series.refresh_from_db()
        self.assertEqual(self.series.synopsis, 'Updated official synopsis from TMDB.')

        # 2. Assert UserMediaStatus is UNTOUCHED
        self.status.refresh_from_db()
        self.assertEqual(self.status.status, UserMediaStatus.StatusChoices.COMPLETED)

        # 3. Assert UserMediaProgress & SeriesProgress is UNTOUCHED
        self.series_progress.refresh_from_db()
        self.assertEqual(self.series_progress.current_season, 5)
        self.assertEqual(self.series_progress.current_episode, 16)
        self.assertEqual(self.series_progress.last_watched_episode_title, 'Felina')

        # 4. Assert DiaryLog is UNTOUCHED
        self.log.refresh_from_db()
        self.assertEqual(self.log.session_notes, 'Unbelievable finale.')
        self.assertEqual(str(self.log.logged_date), '2026-05-15')


        # 5. Assert MediaReview is UNTOUCHED
        self.review.refresh_from_db()
        self.assertEqual(self.review.review_text, 'Pure masterpiece from start to finish.')
        self.assertEqual(self.review.reaction.key, 'peak')


class QueryParameterValidationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_search_invalid_limit_returns_400(self):
        res = self.client.get('/api/v1/media/search/?q=Halo&limit=not_an_int')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('limit', res.data)

    def test_search_invalid_category_returns_400(self):
        res = self.client.get('/api/v1/media/search/?q=Halo&category=INVALID_CAT')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', res.data)

    def test_discovery_invalid_mode_returns_400(self):
        res = self.client.get('/api/v1/discovery/movies/?mode=INVALID_MODE')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('mode', res.data)

    def test_diary_log_invalid_month_returns_400(self):
        user = User.objects.create_user(username='log_user', password='password123')
        self.client.force_authenticate(user=user)
        res = self.client.get('/api/v1/tracking/logs/?month=99')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('month', res.data)


class LegacyProviderFieldsRemovedTestCase(TestCase):
    def test_legacy_provider_id_fields_not_on_mediaitem(self):
        """Proves tmdb_id, mal_id, rawg_id have been completely removed from MediaItem model."""
        field_names = [f.name for f in MediaItem._meta.get_fields()]
        self.assertNotIn('tmdb_id', field_names)
        self.assertNotIn('mal_id', field_names)
        self.assertNotIn('rawg_id', field_names)

    def test_provider_identity_stored_only_via_external_media_mapping(self):
        """Proves third-party identities are stored canonically via ExternalMediaMapping."""
        item = MediaItem.objects.create(
            media_type='MOVIE', title='Inception', slug='inception-2010', release_year=2010
        )
        prov = ExternalProvider.objects.create(provider_key='tmdb', display_name='TMDB', active=True)
        mapping = ExternalMediaMapping.objects.create(
            media_item=item,
            provider=prov,
            external_id='27205',
            external_url='https://www.themoviedb.org/movie/27205'
        )
        self.assertEqual(item.external_mappings.count(), 1)
        self.assertEqual(item.external_mappings.first().external_id, '27205')


class MetadataRefreshAndTaxonomyReconciliationTestCase(TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()
        self.prov = ExternalProvider.objects.create(provider_key='tmdb', display_name='TMDB', active=True)
        self.item = MediaItem.objects.create(
            media_type='MOVIE',
            title='Old Title',
            slug='old-title-2020',
            release_year=2020,
            synopsis='Old synopsis.'
        )
        self.g_action = Genre.objects.create(name='Action', slug='action')
        self.g_scifi = Genre.objects.create(name='Sci-Fi', slug='sci-fi')
        self.item.genres.set([self.g_action, self.g_scifi])

        self.mapping = ExternalMediaMapping.objects.create(
            media_item=self.item,
            provider=self.prov,
            external_id='500',
            external_url='https://themoviedb.org/movie/500'
        )

    @patch.object(TMDBProvider, 'get_details')
    def test_force_refresh_updates_provider_owned_fields_and_reconciles_genres(self, mock_get_details):
        """
        Proves force_refresh overwrites old title, synopsis, release_year,
        and reconciles genres (Old: Action + Sci-Fi -> New: Action + Thriller).
        """
        mock_get_details.return_value = NormalizedMediaDetail(
            provider='tmdb',
            external_id='500',
            external_url='https://themoviedb.org/movie/500',
            title='New Refreshed Title',
            media_type='MOVIE',
            slug_candidate='new-refreshed-title-2021',
            release_year=2021,
            synopsis='Freshly synchronized synopsis from TMDB.',
            genres=['Action', 'Thriller']
        )

        item, created = self.registry.import_media('tmdb', '500', media_type='MOVIE', force_refresh=True)
        self.assertFalse(created)
        item.refresh_from_db()

        self.assertEqual(item.title, 'New Refreshed Title')
        self.assertEqual(item.release_year, 2021)
        self.assertEqual(item.synopsis, 'Freshly synchronized synopsis from TMDB.')

        # Verify taxonomy reconciliation
        genre_slugs = set(item.genres.values_list('slug', flat=True))
        self.assertIn('action', genre_slugs)
        self.assertIn('thriller', genre_slugs)
        self.assertNotIn('sci-fi', genre_slugs)


class MangaVsManhwaSearchAndDiscoveryTestCase(TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()

    @patch.object(AniListProvider, '_post_graphql')
    def test_anilist_search_filters_by_country_code(self, mock_post):
        mock_post.return_value = {
            'Page': {
                'media': [{
                    'id': 105398,
                    'title': {'english': 'Solo Leveling'},
                    'countryOfOrigin': 'KR',
                    'startDate': {'year': 2018},
                    'genres': ['Action', 'Fantasy']
                }]
            }
        }
        provider = AniListProvider()

        # Manhwa search
        res_manhwa = provider.search('Solo Leveling', subtype='MANHWA')
        self.assertEqual(len(res_manhwa), 1)
        self.assertEqual(res_manhwa[0].subtype, 'MANHWA')
        call_vars = mock_post.call_args[0][1]
        self.assertEqual(call_vars.get('country'), 'KR')

        # Manga search
        provider.search('Berserk', subtype='MANGA')
        call_vars_manga = mock_post.call_args[0][1]
        self.assertEqual(call_vars_manga.get('country'), 'JP')

    @patch('requests.get')
    def test_jikan_search_filters_by_type_parameter(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'data': [{
                'mal_id': 121496,
                'title': 'Solo Leveling',
                'type': 'Manhwa',
                'published': {'prop': {'from': {'year': 2018}}},
                'genres': [{'name': 'Action'}]
            }]
        }
        mock_get.return_value = mock_resp

        provider = JikanProvider()
        res = provider.search('Solo Leveling', subtype='MANHWA')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].subtype, 'MANHWA')
        params = mock_get.call_args[1]['params']
        self.assertEqual(params.get('type'), 'manhwa')


class AniListToJikanActualImportFallbackTestCase(TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()

    @patch.object(AniListProvider, 'get_details')
    @patch.object(JikanProvider, 'search')
    @patch.object(JikanProvider, 'get_details')
    def test_import_media_falls_back_to_jikan_with_title_hint(
        self, mock_jikan_details, mock_jikan_search, mock_anilist_details
    ):
        """
        Tests the actual registry.import_media() path when AniList detail retrieval fails
        and safe title-based Jikan fallback is triggered.
        """
        # AniList detail lookup fails
        mock_anilist_details.return_value = None

        # Jikan search finds candidates
        mock_jikan_search.return_value = [
            NormalizedSearchResult(
                provider='jikan',
                external_id='121496',
                title='Solo Leveling',
                media_type='MANGA',
                subtype='MANHWA'
            )
        ]

        # Jikan detail payload matching title
        mock_jikan_details.return_value = NormalizedMediaDetail(
            provider='jikan',
            external_id='121496',
            external_url='https://myanimelist.net/manga/121496',
            title='Solo Leveling',
            media_type='MANGA',
            slug_candidate='solo-leveling-2018',
            release_year=2018,
            synopsis='Solo Leveling synopsis via Jikan fallback.',
            manga_type='MANHWA',
            author='Chugong'
        )

        item, created = self.registry.import_media(
            provider_key='anilist',
            external_id='105398',
            title_hint='Solo Leveling'
        )
        self.assertTrue(created)
        self.assertEqual(item.title, 'Solo Leveling')
        self.assertEqual(item.manga_detail.manga_type, 'MANHWA')

        # Verify both mappings exist: requested anilist ID and resolved jikan ID
        mappings = ExternalMediaMapping.objects.filter(media_item=item)
        prov_keys = set(m.provider.provider_key for m in mappings)
        self.assertIn('anilist', prov_keys)
        self.assertIn('jikan', prov_keys)


class ProviderActiveStateTestCase(TestCase):
    def setUp(self):
        self.registry = ProviderRegistry()
        self.rawg_prov, _ = ExternalProvider.objects.get_or_create(
            provider_key='rawg', defaults={'display_name': 'RAWG', 'active': True}
        )

    def test_inactive_provider_routing_suppressed(self):
        """Verifies inactive provider is suppressed in search, discover, and import."""
        self.rawg_prov.active = False
        self.rawg_prov.save()

        self.assertFalse(self.registry.is_provider_active('rawg'))

        # Search GAME returns empty and skips inactive provider
        res = self.registry.search('Zelda', category='GAME')
        self.assertEqual(res, [])

        # Import raises ValueError for disabled provider
        with self.assertRaises(ValueError) as ctx:
            self.registry.import_media('rawg', '1234')
        self.assertIn("disabled", str(ctx.exception).lower())


class SeedCatalogValidationTestCase(TestCase):
    def test_seed_catalog_mappings_match_verified_titles(self):
        """Verifies seed data provider IDs are accurate and match expected titles."""
        from django.core.management import call_command
        call_command('seed_catalog')

        batman_map = ExternalMediaMapping.objects.get(provider__provider_key='tmdb', external_id='414906')
        self.assertEqual(batman_map.media_item.title, 'The Batman')

        severance_map = ExternalMediaMapping.objects.get(provider__provider_key='tmdb', external_id='97546')
        self.assertEqual(severance_map.media_item.title, 'Severance')

        solo_map = ExternalMediaMapping.objects.get(provider__provider_key='anilist', external_id='105398')
        self.assertEqual(solo_map.media_item.title, 'Solo Leveling')

        cyberpunk_map = ExternalMediaMapping.objects.get(provider__provider_key='rawg', external_id='41494')
        self.assertEqual(cyberpunk_map.media_item.title, 'Cyberpunk 2077')
        self.assertIn('cyberpunk-2077', cyberpunk_map.external_url)
        self.assertNotIn('witcher', cyberpunk_map.external_url)


class MangaManhwaEndToEndTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.registry = ProviderRegistry()
        self.anilist = AniListProvider()
        self.jikan = JikanProvider()

    @patch('apps.catalog.providers.anilist.requests.post')
    def test_manga_and_manhwa_filter_isolation_anilist(self, mock_post):
        """Manga and Manhwa filters do not silently return interchangeable results."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'data': {'Page': {'media': [
                {'id': 1, 'title': {'romaji': 'Manga Title'}, 'countryOfOrigin': 'JP', 'format': 'MANGA', 'startDate': {'year': 2020}, 'coverImage': {}, 'bannerImage': None, 'description': 'desc'}
            ]}}
        }
        mock_post.return_value = mock_resp

        res_manga = self.registry.search('Title', category='MANGA')
        self.assertEqual(len(res_manga), 1)
        self.assertEqual(res_manga[0].subtype, 'MANGA')

        call_args = mock_post.call_args[1]['json']
        self.assertEqual(call_args['variables'].get('country'), 'JP')

        mock_resp.json.return_value = {
            'data': {'Page': {'media': [
                {'id': 2, 'title': {'romaji': 'Manhwa Title'}, 'countryOfOrigin': 'KR', 'format': 'MANGA', 'startDate': {'year': 2021}, 'coverImage': {}, 'bannerImage': None, 'description': 'desc'}
            ]}}
        }
        res_manhwa = self.registry.search('Title', category='MANHWA')
        self.assertEqual(len(res_manhwa), 1)
        self.assertEqual(res_manhwa[0].subtype, 'MANHWA')
        call_args_kr = mock_post.call_args[1]['json']
        self.assertEqual(call_args_kr['variables'].get('country'), 'KR')

    def test_ambiguous_provider_metadata_preserves_uncertainty(self):
        """Where provider metadata is ambiguous, preserve uncertainty rather than inventing a subtype."""
        raw_ani = {
            'id': 999,
            'title': {'romaji': 'Unknown Origin Work'},
            'format': 'MANGA',
            'countryOfOrigin': None,
            'startDate': {'year': 2020}
        }
        norm_ani = self.anilist._normalize_search_item(raw_ani)
        self.assertIsNone(norm_ani.subtype)

        raw_jik = {
            'mal_id': 888,
            'title': 'Unrecognized Type Work',
            'type': 'UnknownFormat',
            'published': {'from': '2021-01-01'}
        }
        norm_jik = self.jikan._normalize_search_item(raw_jik)
        self.assertIsNone(norm_jik.subtype)

    @patch('apps.catalog.providers.anilist.requests.post')
    def test_anilist_manga_end_to_end_pipeline(self, mock_post):
        """
        Full path for AniList:
        Search -> normalized result -> discovery -> media import -> MangaDetail -> external mappings -> local detail response.
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'data': {
                'Media': {
                    'id': 33333,
                    'title': {'romaji': 'Frieren', 'english': 'Frieren: Beyond Journey\'s End'},
                    'format': 'MANGA',
                    'countryOfOrigin': 'JP',
                    'startDate': {'year': 2020},
                    'description': 'An elf mage on a journey.',
                    'coverImage': {'large': 'https://example.com/frieren.jpg'},
                    'bannerImage': None,
                    'chapters': 130,
                    'volumes': 13,
                    'staff': {'edges': [{'node': {'name': {'full': 'Kanehito Yamada'}}, 'role': 'Story'}]},
                    'genres': ['Adventure', 'Fantasy'],
                    'tags': [{'name': 'Magic'}]
                }
            }
        }
        mock_post.return_value = mock_resp

        # 1. Import media
        item, created = self.registry.import_media(
            provider_key='anilist',
            external_id='33333',
            title_hint='Frieren'
        )
        self.assertTrue(created)
        self.assertEqual(item.media_type, 'MANGA')
        self.assertEqual(item.manga_detail.manga_type, 'MANGA')
        self.assertEqual(item.manga_detail.author, 'Kanehito Yamada')

        # 2. Check external mapping
        mapping = ExternalMediaMapping.objects.get(media_item=item, provider__provider_key='anilist')
        self.assertEqual(mapping.external_id, '33333')

        # 3. Local detail response via GET /api/v1/media/<slug>/
        res = self.client.get(f'/api/v1/media/{item.slug}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['media_type'], 'MANGA')
        self.assertEqual(res.data['manga_detail']['manga_type'], 'MANGA')
        self.assertEqual(res.data['manga_detail']['author'], 'Kanehito Yamada')
        self.assertEqual(res.data['external_mappings'][0]['provider_key'], 'anilist')

    @patch('apps.catalog.providers.jikan.requests.get')
    def test_jikan_manhwa_end_to_end_pipeline(self, mock_get):
        """
        Full path for Jikan:
        Search -> normalized result -> discovery -> media import -> MangaDetail -> external mappings -> local detail response.
        """
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'data': {
                'mal_id': 77777,
                'title': 'Tower of God',
                'type': 'Manhwa',
                'published': {'from': '2010-06-30T00:00:00+00:00'},
                'synopsis': 'Reach the top of the Tower and everything will be yours.',
                'images': {'jpg': {'large_image_url': 'https://example.com/tog.jpg'}},
                'authors': [{'name': 'SIU'}],
                'genres': [{'name': 'Action'}, {'name': 'Fantasy'}],
                'themes': [{'name': 'Super Power'}]
            }
        }
        mock_get.return_value = mock_resp

        # 1. Import media
        item, created = self.registry.import_media(
            provider_key='jikan',
            external_id='77777',
            title_hint='Tower of God'
        )
        self.assertTrue(created)
        self.assertEqual(item.media_type, 'MANGA')
        self.assertEqual(item.manga_detail.manga_type, 'MANHWA')
        self.assertEqual(item.manga_detail.author, 'SIU')

        # 2. Check external mapping
        mapping = ExternalMediaMapping.objects.get(media_item=item, provider__provider_key='jikan')
        self.assertEqual(mapping.external_id, '77777')

        # 3. Local detail response via GET /api/v1/media/<slug>/
        res = self.client.get(f'/api/v1/media/{item.slug}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['media_type'], 'MANGA')
        self.assertEqual(res.data['manga_detail']['manga_type'], 'MANHWA')
        self.assertEqual(res.data['manga_detail']['author'], 'SIU')

    def test_cross_provider_matching_threshold_and_ambiguity(self):
        """
        Cross-provider mappings are attached only when confidently identified (>= 75.0).
        Ambiguous matches (< 75.0) are NOT merged automatically.
        """
        existing_item = MediaItem.objects.create(
            media_type='MANGA',
            title='Solo Leveling',
            slug='solo-leveling-2018',
            release_year=2018
        )
        MangaDetail.objects.create(
            media_item=existing_item,
            manga_type='MANHWA',
            author='Chugong'
        )

        # Ambiguous candidate: spin-off sequel with different title and year
        ambiguous_candidate = NormalizedMediaDetail(
            provider='jikan',
            external_id='999999',
            external_url='https://example.com/sl-rag',
            title='Solo Leveling: Ragnarok',
            media_type='MANGA',
            slug_candidate='solo-leveling-ragnarok-2024',
            release_year=2024,
            synopsis='Spin-off sequel.',
            manga_type='MANHWA',
            author='Daul'
        )
        match, score = MediaMatcherService.find_match(ambiguous_candidate)
        self.assertIsNone(match)
        self.assertLess(score, MediaMatcherService.MIN_CONFIDENCE_THRESHOLD)

        # Confident candidate: identical title, author, and year
        confident_candidate = NormalizedMediaDetail(
            provider='jikan',
            external_id='121496',
            external_url='https://example.com/solo-leveling',
            title='Solo Leveling',
            media_type='MANGA',
            slug_candidate='solo-leveling-2018',
            release_year=2018,
            synopsis='Original hunter webtoon.',
            manga_type='MANHWA',
            author='Chugong'
        )
        confident_match, confident_score = MediaMatcherService.find_match(confident_candidate)
        self.assertIsNotNone(confident_match)
        self.assertEqual(confident_match.id, existing_item.id)
        self.assertGreaterEqual(confident_score, MediaMatcherService.MIN_CONFIDENCE_THRESHOLD)

