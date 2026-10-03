"""
User Tracking & Progress Models for DreamTeal.

Separates:
- UserMediaStatus (Current state: Watching, Completed, Backlog, Dropped, etc.)
- UserMediaProgress (Base quantitative progress tracker)
- Category-Specific Progress Extensions (SeriesProgress, MangaProgress, GameProgress)
- DiaryLog (History-preserving consumption records supporting controlled editing
  and automatic forward synchronization)
"""

import uuid
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class UserMediaStatus(models.Model):
    """
    Current status of a user's relationship with a media item.
    Enforces category-appropriate statuses per media type.
    """
    class StatusChoices(models.TextChoices):
        # Movies & Series
        PLAN_TO_WATCH = 'PLAN_TO_WATCH', 'Plan to Watch'
        WATCHING = 'WATCHING', 'Watching'
        WATCHED = 'WATCHED', 'Watched'
        COMPLETED = 'COMPLETED', 'Completed'

        # Manga / Webtoons
        PLAN_TO_READ = 'PLAN_TO_READ', 'Plan to Read'
        READING = 'READING', 'Reading'

        # Video Games
        BACKLOG = 'BACKLOG', 'Backlog'
        PLAYING = 'PLAYING', 'Playing'
        FINISHED = 'FINISHED', 'Finished'

        # Universal
        PAUSED = 'PAUSED', 'Paused'
        DROPPED = 'DROPPED', 'Dropped / Abandoned'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='media_statuses'
    )
    media_item = models.ForeignKey(
        'catalog.MediaItem',
        on_delete=models.CASCADE,
        related_name='user_statuses'
    )
    status = models.CharField(
        max_length=30,
        choices=StatusChoices.choices,
        db_index=True
    )
    is_favorite = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Media Status'
        verbose_name_plural = 'User Media Statuses'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'media_item'],
                name='unique_user_media_status'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['media_item']),
        ]

    def clean(self):
        super().clean()
        if not self.media_item_id:
            return

        media_type = self.media_item.media_type
        # Validate status appropriateness for media category
        valid_statuses = {
            'MOVIE': [
                self.StatusChoices.PLAN_TO_WATCH,
                self.StatusChoices.WATCHING,
                self.StatusChoices.WATCHED,
                self.StatusChoices.DROPPED
            ],
            'SERIES': [
                self.StatusChoices.PLAN_TO_WATCH,
                self.StatusChoices.WATCHING,
                self.StatusChoices.COMPLETED,
                self.StatusChoices.PAUSED,
                self.StatusChoices.DROPPED
            ],
            'MANGA': [
                self.StatusChoices.PLAN_TO_READ,
                self.StatusChoices.READING,
                self.StatusChoices.COMPLETED,
                self.StatusChoices.PAUSED,
                self.StatusChoices.DROPPED
            ],
            'GAME': [
                self.StatusChoices.BACKLOG,
                self.StatusChoices.PLAYING,
                self.StatusChoices.FINISHED,
                self.StatusChoices.PAUSED,
                self.StatusChoices.DROPPED
            ],
        }
        allowed = valid_statuses.get(media_type, [])
        if self.status not in allowed:
            raise ValidationError(
                f"Status '{self.status}' is not valid for media type '{media_type}'."
            )

    def __str__(self):
        return f"{self.user.username} - {self.media_item.title}: {self.get_status_display()}"


class UserMediaProgress(models.Model):
    """
    Base progress container for a user's active consumption position.
    Links 1:1 to category-specific progress extension models:
    - SeriesProgress
    - MangaProgress
    - GameProgress
    Movies typically do not require an extension unless resume points are added.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='media_progresses'
    )
    media_item = models.ForeignKey(
        'catalog.MediaItem',
        on_delete=models.CASCADE,
        related_name='user_progresses'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Media Progress'
        verbose_name_plural = 'User Media Progresses'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'media_item'],
                name='unique_user_media_progress'
            )
        ]

    def __str__(self):
        return f"Progress: {self.user.username} on {self.media_item.title}"


class SeriesProgress(models.Model):
    """
    Category-specific progress extension for TV Series.
    Tracks current season and episode numbers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    progress = models.OneToOneField(
        UserMediaProgress,
        on_delete=models.CASCADE,
        related_name='series_progress'
    )
    current_season = models.PositiveIntegerField(default=1)
    current_episode = models.PositiveIntegerField(default=0)
    last_watched_episode_title = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = 'Series Progress'
        verbose_name_plural = 'Series Progresses'

    def clean(self):
        super().clean()
        if self.progress.media_item.media_type != 'SERIES':
            raise ValidationError("SeriesProgress can only be attached to a TV Series media item.")

    def __str__(self):
        return f"S{self.current_season}E{self.current_episode} ({self.progress.media_item.title})"


class MangaProgress(models.Model):
    """
    Category-specific progress extension for Manga/Manhwa/Webtoons.
    Tracks current chapter and volume reached.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    progress = models.OneToOneField(
        UserMediaProgress,
        on_delete=models.CASCADE,
        related_name='manga_progress'
    )
    current_chapter = models.PositiveIntegerField(default=0)
    current_volume = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Manga Progress'
        verbose_name_plural = 'Manga Progresses'

    def clean(self):
        super().clean()
        if self.progress.media_item.media_type != 'MANGA':
            raise ValidationError("MangaProgress can only be attached to a Manga/Manhwa media item.")

    def __str__(self):
        return f"Ch. {self.current_chapter} ({self.progress.media_item.title})"


class GameProgress(models.Model):
    """
    Category-specific progress extension for Video Games.
    Tracks accumulated gameplay hours, completion tier, and platform played.
    """
    class CompletionType(models.TextChoices):
        MAIN_STORY = 'MAIN_STORY', 'Main Story'
        MAIN_EXTRA = 'MAIN_EXTRA', 'Main + Extra'
        COMPLETIONIST = 'COMPLETIONIST', '100% Completionist'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    progress = models.OneToOneField(
        UserMediaProgress,
        on_delete=models.CASCADE,
        related_name='game_progress'
    )
    hours_played = models.DecimalField(
        max_digits=6,
        decimal_places=1,
        default=Decimal('0.0'),
        help_text="Cumulative hours invested in this game."
    )
    completion_type = models.CharField(
        max_length=20,
        choices=CompletionType.choices,
        null=True,
        blank=True
    )
    platform_played_on = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        verbose_name = 'Game Progress'
        verbose_name_plural = 'Game Progresses'

    def clean(self):
        super().clean()
        if self.progress.media_item.media_type != 'GAME':
            raise ValidationError("GameProgress can only be attached to a Video Game media item.")

    def __str__(self):
        return f"{self.hours_played}h ({self.progress.media_item.title})"


class DiaryLog(models.Model):
    """
    History-preserving consumption records supporting controlled log editing.
    Represents distinct consumption events: "I consumed this on this date."

    Controlled Editing:
    - Users can edit logged_date, is_rewatch_or_replay, session_notes, progress_snapshot.
    - Preserves distinct UUID rows; never collapses rewatches/re-reads into one entry.
    - Syncs forward to UserMediaProgress automatically without backward regression.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='diary_logs'
    )
    media_item = models.ForeignKey(
        'catalog.MediaItem',
        on_delete=models.CASCADE,
        related_name='diary_logs'
    )
    logged_date = models.DateField(
        default=timezone.now,
        help_text="Date the consumption session occurred. Editable."
    )
    is_rewatch_or_replay = models.BooleanField(
        default=False,
        help_text="Flag indicating whether this session was a rewatch, re-read, or replay."
    )
    session_notes = models.TextField(
        blank=True,
        default='',
        help_text="User's thoughts or quick notes for this specific consumption session."
    )
    progress_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Snapshot of progress at log time (e.g. {'season': 2, 'episode': 5} or {'session_hours': 2.5})."
    )

    created_at = models.DateTimeField(auto_now_add=True, help_text="Immutable creation audit timestamp.")
    updated_at = models.DateTimeField(auto_now=True, help_text="Timestamp of last controlled edit.")

    def __init__(self, *args, **kwargs):
        self._sync_progress = kwargs.pop('sync_progress', True)
        super().__init__(*args, **kwargs)

    class Meta:
        ordering = ['-logged_date', '-created_at']
        verbose_name = 'Diary Log'
        verbose_name_plural = 'Diary Logs'
        indexes = [
            models.Index(fields=['user', '-logged_date']),
            models.Index(fields=['media_item']),
        ]

    def sync_to_progress(self, sync_progress=True, is_new=True, old_synced_hours=Decimal('0.0')):
        """
        Implements approved Automatic Diary -> Progress Synchronization Rules:
        1. Default Behavior: advances current progress forward.
        2. Historical Non-Reversal Rule: historical logs never move progress backward.
        3. Manga forward advance: chapter advances forward.
        4. Game session-based hours aggregation:
           - Game diary sessions are the source of truth for session playtime.
           - Create: session_hours accumulates to total hours_played.
           - Edit: adjusts hours_played by the delta between new and old session hours.
           - Delete: decrements the session's hours from hours_played safely.
        5. sync_progress=False bypasses active progress updates.
        """
        if not self.progress_snapshot:
            return

        media_type = self.media_item.media_type
        base_progress, _ = UserMediaProgress.objects.get_or_create(
            user=self.user,
            media_item=self.media_item
        )

        if not sync_progress:
            if media_type == 'GAME':
                if is_new:
                    self.progress_snapshot['_synced_hours'] = '0.0'
                else:
                    self.progress_snapshot['_synced_hours'] = str(old_synced_hours)
                DiaryLog.objects.filter(pk=self.pk).update(progress_snapshot=self.progress_snapshot)
            return

        if media_type == 'SERIES':
            snapshot_season = self.progress_snapshot.get('season')
            snapshot_episode = self.progress_snapshot.get('episode')
            if snapshot_season is not None and snapshot_episode is not None:
                series_prog, _ = SeriesProgress.objects.get_or_create(progress=base_progress)
                # Historical non-reversal check: only advance forward
                current_tuple = (series_prog.current_season, series_prog.current_episode)
                logged_tuple = (int(snapshot_season), int(snapshot_episode))
                if logged_tuple > current_tuple:
                    series_prog.current_season = logged_tuple[0]
                    series_prog.current_episode = logged_tuple[1]
                    if 'episode_title' in self.progress_snapshot:
                        series_prog.last_watched_episode_title = self.progress_snapshot['episode_title']
                    series_prog.save()

        elif media_type == 'MANGA':
            snapshot_chapter = self.progress_snapshot.get('chapter')
            if snapshot_chapter is not None:
                manga_prog, _ = MangaProgress.objects.get_or_create(progress=base_progress)
                logged_chapter = int(snapshot_chapter)
                # Historical non-reversal: only advance forward
                if logged_chapter > manga_prog.current_chapter:
                    manga_prog.current_chapter = logged_chapter
                    if 'volume' in self.progress_snapshot:
                        manga_prog.current_volume = self.progress_snapshot['volume']
                    manga_prog.save()

        elif media_type == 'GAME':
            game_prog, _ = GameProgress.objects.get_or_create(progress=base_progress)
            session_hours_raw = self.progress_snapshot.get('session_hours')
            current_session_hours = Decimal(str(session_hours_raw)) if session_hours_raw is not None else Decimal('0.0')

            if is_new:
                if current_session_hours > 0:
                    game_prog.hours_played += current_session_hours
                    self.progress_snapshot['_synced_hours'] = str(current_session_hours)
                    DiaryLog.objects.filter(pk=self.pk).update(progress_snapshot=self.progress_snapshot)
            else:
                diff = current_session_hours - old_synced_hours
                if diff != Decimal('0.0'):
                    game_prog.hours_played = max(Decimal('0.0'), game_prog.hours_played + diff)
                self.progress_snapshot['_synced_hours'] = str(current_session_hours)
                DiaryLog.objects.filter(pk=self.pk).update(progress_snapshot=self.progress_snapshot)

            completion_type = self.progress_snapshot.get('completion_type')
            if completion_type and completion_type in GameProgress.CompletionType.values:
                game_prog.completion_type = completion_type
            if 'platform' in self.progress_snapshot:
                game_prog.platform_played_on = self.progress_snapshot['platform']
            game_prog.save()

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Override save to handle automatic progress sync on creation and updates
        with strict transaction safety.
        """
        sync_progress = kwargs.pop('sync_progress', getattr(self, '_sync_progress', True))
        is_new = self._state.adding

        old_synced_hours = Decimal('0.0')
        if not is_new and self.media_item.media_type == 'GAME':
            orig = DiaryLog.objects.filter(pk=self.pk).values('progress_snapshot').first()
            if orig and orig.get('progress_snapshot'):
                snap = orig['progress_snapshot']
                raw_h = snap.get('_synced_hours')
                if raw_h is not None:
                    try:
                        old_synced_hours = Decimal(str(raw_h))
                    except (ValueError, TypeError):
                        old_synced_hours = Decimal('0.0')

        super().save(*args, **kwargs)
        self.sync_to_progress(sync_progress=sync_progress, is_new=is_new, old_synced_hours=old_synced_hours)

    @transaction.atomic
    def delete(self, *args, **kwargs):
        """
        Override delete to decrement game session hours from GameProgress
        if this session was previously synced.
        """
        if self.media_item.media_type == 'GAME' and self.progress_snapshot:
            raw_h = self.progress_snapshot.get('_synced_hours')
            synced_hours = Decimal('0.0')
            if raw_h is not None:
                try:
                    synced_hours = Decimal(str(raw_h))
                except (ValueError, TypeError):
                    synced_hours = Decimal('0.0')

            if synced_hours > 0:
                base_progress = UserMediaProgress.objects.filter(
                    user=self.user,
                    media_item=self.media_item
                ).first()
                if base_progress and hasattr(base_progress, 'game_progress'):
                    game_prog = base_progress.game_progress
                    game_prog.hours_played = max(Decimal('0.0'), game_prog.hours_played - synced_hours)
                    game_prog.save()

        super().delete(*args, **kwargs)

    def __str__(self):
        rewatch = " (Rewatch)" if self.is_rewatch_or_replay else ""
        return f"{self.user.username} logged {self.media_item.title} on {self.logged_date}{rewatch}"
