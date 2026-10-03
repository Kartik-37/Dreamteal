"""
Backend tests for apps.tracking.
Tests UserMediaStatus, category-specific progress models, history-preserving DiaryLog,
controlled editing, and automatic forward synchronization rules.
"""

from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from apps.catalog.models import MediaItem
from apps.tracking.models import (
    UserMediaStatus,
    UserMediaProgress,
    SeriesProgress,
    MangaProgress,
    GameProgress,
    DiaryLog
)

User = get_user_model()


class TrackingModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password123')
        self.other_user = User.objects.create_user(username='bob', password='password123')

        self.movie = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MOVIE,
            title='The Batman',
            slug='the-batman-2022',
            release_year=2022
        )
        self.series = MediaItem.objects.create(
            media_type=MediaItem.MediaType.SERIES,
            title='Severance',
            slug='severance-2022',
            release_year=2022
        )
        self.manga = MediaItem.objects.create(
            media_type=MediaItem.MediaType.MANGA,
            title='Solo Leveling',
            slug='solo-leveling-2018',
            release_year=2018
        )
        self.game = MediaItem.objects.create(
            media_type=MediaItem.MediaType.GAME,
            title='Cyberpunk 2077',
            slug='cyberpunk-2077-2020',
            release_year=2020
        )

    # -----------------------------------------------------
    # UserMediaStatus Tests
    # -----------------------------------------------------
    def test_status_uniqueness_per_user_and_media(self):
        """Verifies duplicate status for the same user and media raises IntegrityError."""
        UserMediaStatus.objects.create(
            user=self.user,
            media_item=self.movie,
            status=UserMediaStatus.StatusChoices.WATCHED
        )
        with self.assertRaises(IntegrityError):
            UserMediaStatus.objects.create(
                user=self.user,
                media_item=self.movie,
                status=UserMediaStatus.StatusChoices.WATCHING
            )

    def test_status_category_validation(self):
        """Verifies media-type validation on UserMediaStatus."""
        # Reading is invalid for movies
        status_invalid = UserMediaStatus(
            user=self.user,
            media_item=self.movie,
            status=UserMediaStatus.StatusChoices.READING
        )
        with self.assertRaises(ValidationError):
            status_invalid.clean()

        # Watched is valid for movies
        status_valid = UserMediaStatus(
            user=self.user,
            media_item=self.movie,
            status=UserMediaStatus.StatusChoices.WATCHED
        )
        status_valid.clean()  # Should not raise

    # -----------------------------------------------------
    # Progress Models Tests
    # -----------------------------------------------------
    def test_category_progress_extensions(self):
        """Verifies SeriesProgress, MangaProgress, and GameProgress extensions."""
        # Series
        base_series = UserMediaProgress.objects.create(user=self.user, media_item=self.series)
        sp = SeriesProgress.objects.create(
            progress=base_series,
            current_season=1,
            current_episode=5
        )
        sp.clean()
        self.assertEqual(base_series.series_progress.current_episode, 5)

        # Manga
        base_manga = UserMediaProgress.objects.create(user=self.user, media_item=self.manga)
        mp = MangaProgress.objects.create(
            progress=base_manga,
            current_chapter=80,
            current_volume=8
        )
        mp.clean()
        self.assertEqual(base_manga.manga_progress.current_chapter, 80)

        # Game
        base_game = UserMediaProgress.objects.create(user=self.user, media_item=self.game)
        gp = GameProgress.objects.create(
            progress=base_game,
            hours_played=Decimal('25.5'),
            completion_type=GameProgress.CompletionType.MAIN_STORY
        )
        gp.clean()
        self.assertEqual(base_game.game_progress.hours_played, Decimal('25.5'))

    def test_progress_wrong_category_validation(self):
        """Verifies attaching wrong progress extension raises ValidationError."""
        base_movie = UserMediaProgress.objects.create(user=self.user, media_item=self.movie)
        sp = SeriesProgress(progress=base_movie, current_season=1, current_episode=1)
        with self.assertRaises(ValidationError):
            sp.clean()

    # -----------------------------------------------------
    # History-Preserving DiaryLog Tests
    # -----------------------------------------------------
    def test_diary_preserves_multiple_entries_and_rewatches(self):
        """Verifies multiple consumption events and rewatches exist as separate distinct rows."""
        log1 = DiaryLog.objects.create(
            user=self.user,
            media_item=self.movie,
            logged_date=timezone.now().date(),
            is_rewatch_or_replay=False,
            session_notes="First cinema viewing."
        )
        log2 = DiaryLog.objects.create(
            user=self.user,
            media_item=self.movie,
            logged_date=timezone.now().date(),
            is_rewatch_or_replay=True,
            session_notes="Second viewing with friends."
        )

        self.assertNotEqual(log1.id, log2.id)
        user_movie_logs = DiaryLog.objects.filter(user=self.user, media_item=self.movie)
        self.assertEqual(user_movie_logs.count(), 2)

    def test_diary_controlled_editing(self):
        """Verifies controlled editing mutates only the targeted record."""
        log = DiaryLog.objects.create(
            user=self.user,
            media_item=self.movie,
            logged_date=timezone.now().date(),
            session_notes="Initial note."
        )
        initial_created_at = log.created_at

        # Edit note and date
        log.session_notes = "Updated corrected note."
        log.save()
        log.refresh_from_db()

        self.assertEqual(log.session_notes, "Updated corrected note.")
        self.assertEqual(log.created_at, initial_created_at)

    def test_diary_deletion_leaves_media_intact(self):
        """Verifies deleting a diary entry removes only that log without deleting catalog media."""
        log = DiaryLog.objects.create(
            user=self.user,
            media_item=self.movie,
            logged_date=timezone.now().date()
        )
        log_id = log.id
        log.delete()

        self.assertFalse(DiaryLog.objects.filter(id=log_id).exists())
        self.assertTrue(MediaItem.objects.filter(id=self.movie.id).exists())

    # -----------------------------------------------------
    # Automatic Diary -> Progress Synchronization Rules
    # -----------------------------------------------------
    def test_series_automatic_forward_progress_sync(self):
        """Verifies logging a series episode automatically advances active progress forward."""
        # Initial progress: S2E3
        base = UserMediaProgress.objects.create(user=self.user, media_item=self.series)
        sp = SeriesProgress.objects.create(progress=base, current_season=2, current_episode=3)

        # User logs diary entry for S2E4
        DiaryLog.objects.create(
            user=self.user,
            media_item=self.series,
            progress_snapshot={'season': 2, 'episode': 4}
        )

        sp.refresh_from_db()
        self.assertEqual(sp.current_season, 2)
        self.assertEqual(sp.current_episode, 4)

    def test_series_historical_non_reversal_rule(self):
        """Verifies logging a historical past episode NEVER regresses current progress backwards."""
        # Current progress is S2E8
        base = UserMediaProgress.objects.create(user=self.user, media_item=self.series)
        sp = SeriesProgress.objects.create(progress=base, current_season=2, current_episode=8)

        # User logs a retrospective diary entry for S2E4
        past_log = DiaryLog.objects.create(
            user=self.user,
            media_item=self.series,
            progress_snapshot={'season': 2, 'episode': 4}
        )

        # Diary entry is preserved with S2E4
        self.assertEqual(past_log.progress_snapshot['episode'], 4)

        # But active progress must remain S2E8!
        sp.refresh_from_db()
        self.assertEqual(sp.current_season, 2)
        self.assertEqual(sp.current_episode, 8)

    def test_manga_forward_advance_and_historical_safeguard(self):
        """Verifies manga forward advance and historical non-reversal safeguard."""
        base = UserMediaProgress.objects.create(user=self.user, media_item=self.manga)
        mp = MangaProgress.objects.create(progress=base, current_chapter=80)

        # Forward advance to chapter 84
        DiaryLog.objects.create(
            user=self.user,
            media_item=self.manga,
            progress_snapshot={'chapter': 84}
        )
        mp.refresh_from_db()
        self.assertEqual(mp.current_chapter, 84)

        # Historical diary for chapter 70 does not regress
        DiaryLog.objects.create(
            user=self.user,
            media_item=self.manga,
            progress_snapshot={'chapter': 70}
        )
        mp.refresh_from_db()
        self.assertEqual(mp.current_chapter, 84)

    def test_game_hours_additive_accumulation(self):
        """Verifies game gameplay hours accumulate additively from diary logs."""
        base = UserMediaProgress.objects.create(user=self.user, media_item=self.game)
        gp = GameProgress.objects.create(progress=base, hours_played=Decimal('12.0'))

        # User logs a 2.5 hour session
        DiaryLog.objects.create(
            user=self.user,
            media_item=self.game,
            progress_snapshot={'session_hours': 2.5}
        )
        gp.refresh_from_db()
        self.assertEqual(gp.hours_played, Decimal('14.5'))

    def test_diary_sync_progress_opt_out(self):
        """Verifies passing sync_progress=False skips active progress updates."""
        base = UserMediaProgress.objects.create(user=self.user, media_item=self.manga)
        mp = MangaProgress.objects.create(progress=base, current_chapter=50)

        DiaryLog.objects.create(
            user=self.user,
            media_item=self.manga,
            progress_snapshot={'chapter': 99},
            sync_progress=False
        )
        mp.refresh_from_db()
        self.assertEqual(mp.current_chapter, 50)


from rest_framework.test import APIClient


class TrackingAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='tester_tracking', password='pass123_secure')
        self.client.force_authenticate(user=self.user)

        self.movie = MediaItem.objects.create(
            media_type='MOVIE', title='Oppenheimer', slug='oppenheimer-2023', release_year=2023
        )
        self.series = MediaItem.objects.create(
            media_type='SERIES', title='Succession', slug='succession-2018', release_year=2018
        )

    def test_status_create_and_update(self):
        # 1. Create status
        res = self.client.post('/api/v1/tracking/status/', {
            'media_item': str(self.movie.id),
            'status': 'PLAN_TO_WATCH'
        })
        self.assertEqual(res.status_code, 201)
        status_id = res.data['id']

        # 2. Attempt duplicate create returns 409 Conflict
        res_dup = self.client.post('/api/v1/tracking/status/', {
            'media_item': str(self.movie.id),
            'status': 'WATCHING'
        })
        self.assertEqual(res_dup.status_code, 409)

        # 3. Update status using PATCH
        res_patch = self.client.patch(f'/api/v1/tracking/status/{status_id}/', {
            'status': 'WATCHED'
        })
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.data['status'], 'WATCHED')

    def test_progress_create_and_update(self):
        res = self.client.post('/api/v1/tracking/progress/', {
            'media_item': str(self.series.id),
            'series_progress': {
                'current_season': 1,
                'current_episode': 4
            }
        }, format='json')
        self.assertEqual(res.status_code, 201)
        progress_id = res.data['id']

        # Update via PATCH
        res_patch = self.client.patch(f'/api/v1/tracking/progress/{progress_id}/', {
            'series_progress': {
                'current_season': 1,
                'current_episode': 5
            }
        }, format='json')
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.data['series_progress']['current_episode'], 5)

    def test_diary_log_create_and_controlled_edit(self):
        # Create diary log with automatic forward progress sync
        res = self.client.post('/api/v1/tracking/logs/', {
            'media_item': str(self.series.id),
            'logged_date': '2026-10-01',
            'session_notes': 'Intense episode ending.',
            'progress_snapshot': {'season': 1, 'episode': 6}
        }, format='json')
        self.assertEqual(res.status_code, 201)
        log_id = res.data['id']

        # Verify progress advanced automatically
        prog = UserMediaProgress.objects.get(user=self.user, media_item=self.series)
        self.assertEqual(prog.series_progress.current_episode, 6)

        # Controlled edit of diary log notes
        res_patch = self.client.patch(f'/api/v1/tracking/logs/{log_id}/', {
            'session_notes': 'Updated: one of the best season finales ever.'
        })
        self.assertEqual(res_patch.status_code, 200)
        self.assertEqual(res_patch.data['session_notes'], 'Updated: one of the best season finales ever.')

        # Delete diary log
        res_delete = self.client.delete(f'/api/v1/tracking/logs/{log_id}/')
        self.assertEqual(res_delete.status_code, 204)

