"""
Service layer for tracking and consumption diary synchronization in DreamTeal.
Maintains transactional consistency between DiaryLog sessions and category-specific progress.
"""

from decimal import Decimal
import logging
from typing import Optional
from django.db import transaction

from apps.tracking.models import (
    DiaryLog, GameProgress, MangaProgress, SeriesProgress, UserMediaProgress
)

logger = logging.getLogger(__name__)


class GameSessionTrackingService:
    """
    Transactional service governing the lifecycle of Game consumption sessions.
    Maintains GameProgress.hours_played consistently across session creation, edits,
    and deletions while preserving discrete DiaryLog entries.
    """

    @classmethod
    @transaction.atomic
    def apply_session_create(cls, log: DiaryLog, sync_progress: bool = True) -> None:
        """
        Called when a DiaryLog is created.
        If sync_progress=True, atomically adds session_hours to GameProgress.hours_played
        and records _synced_hours in progress_snapshot.
        If sync_progress=False, records _synced_hours='0.0' and leaves GameProgress unchanged.
        """
        if log.media_item.media_type != 'GAME':
            return

        if not log.progress_snapshot:
            log.progress_snapshot = {}

        session_hours_raw = log.progress_snapshot.get('session_hours')
        try:
            session_hours = Decimal(str(session_hours_raw)) if session_hours_raw is not None else Decimal('0.0')
        except (ValueError, TypeError):
            session_hours = Decimal('0.0')

        if session_hours < 0:
            session_hours = Decimal('0.0')

        if not sync_progress:
            log.progress_snapshot['_synced_hours'] = '0.0'
            DiaryLog.objects.filter(pk=log.pk).update(progress_snapshot=log.progress_snapshot)
            return

        base_progress, _ = UserMediaProgress.objects.get_or_create(
            user=log.user,
            media_item=log.media_item
        )
        game_prog, _ = GameProgress.objects.get_or_create(progress=base_progress)

        if session_hours > 0:
            game_prog.hours_played += session_hours
            log.progress_snapshot['_synced_hours'] = str(session_hours)
            DiaryLog.objects.filter(pk=log.pk).update(progress_snapshot=log.progress_snapshot)
        else:
            log.progress_snapshot['_synced_hours'] = '0.0'
            DiaryLog.objects.filter(pk=log.pk).update(progress_snapshot=log.progress_snapshot)

        completion_type = log.progress_snapshot.get('completion_type')
        if completion_type and completion_type in GameProgress.CompletionType.values:
            game_prog.completion_type = completion_type
        if 'platform' in log.progress_snapshot:
            game_prog.platform_played_on = log.progress_snapshot['platform']

        game_prog.save()

    @classmethod
    @transaction.atomic
    def apply_session_update(
        cls,
        log: DiaryLog,
        old_synced_hours: Decimal,
        new_session_hours: Decimal,
        sync_progress: bool = True
    ) -> None:
        """
        Called when an existing DiaryLog is modified.
        Computes delta (new_session_hours - old_synced_hours) and adjusts GameProgress.hours_played.
        Prevents double-counting and handles turning sync_progress off/on safely.
        """
        if log.media_item.media_type != 'GAME':
            return

        if not log.progress_snapshot:
            log.progress_snapshot = {}

        if new_session_hours < 0:
            new_session_hours = Decimal('0.0')

        if not sync_progress:
            # When sync_progress is explicitly False, retain previously synced hours or do not accumulate
            log.progress_snapshot['_synced_hours'] = str(old_synced_hours)
            DiaryLog.objects.filter(pk=log.pk).update(progress_snapshot=log.progress_snapshot)
            return

        base_progress, _ = UserMediaProgress.objects.get_or_create(
            user=log.user,
            media_item=log.media_item
        )
        game_prog, _ = GameProgress.objects.get_or_create(progress=base_progress)

        diff = new_session_hours - old_synced_hours
        if diff != Decimal('0.0'):
            game_prog.hours_played = max(Decimal('0.0'), game_prog.hours_played + diff)

        log.progress_snapshot['_synced_hours'] = str(new_session_hours)
        DiaryLog.objects.filter(pk=log.pk).update(progress_snapshot=log.progress_snapshot)

        completion_type = log.progress_snapshot.get('completion_type')
        if completion_type and completion_type in GameProgress.CompletionType.values:
            game_prog.completion_type = completion_type
        if 'platform' in log.progress_snapshot:
            game_prog.platform_played_on = log.progress_snapshot['platform']

        game_prog.save()

    @classmethod
    @transaction.atomic
    def apply_session_delete(cls, log: DiaryLog) -> None:
        """
        Called when a DiaryLog is deleted (either individually or in bulk).
        Deducts previously synced session hours from GameProgress.hours_played.
        """
        if log.media_item.media_type != 'GAME' or not log.progress_snapshot:
            return

        raw_h = log.progress_snapshot.get('_synced_hours')
        synced_hours = Decimal('0.0')
        if raw_h is not None:
            try:
                synced_hours = Decimal(str(raw_h))
            except (ValueError, TypeError):
                synced_hours = Decimal('0.0')

        if synced_hours > 0:
            base_progress = UserMediaProgress.objects.filter(
                user=log.user,
                media_item=log.media_item
            ).first()
            if base_progress and hasattr(base_progress, 'game_progress'):
                game_prog = base_progress.game_progress
                game_prog.hours_played = max(Decimal('0.0'), game_prog.hours_played - synced_hours)
                game_prog.save()
