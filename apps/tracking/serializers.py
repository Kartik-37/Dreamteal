"""
Serializers for User Tracking, Progress, and History-Preserving Diary Logs in DreamTeal.
Strictly adheres to the Zero-Star Rating Policy.
"""

from decimal import Decimal
from rest_framework import serializers
from apps.tracking.models import (
    DiaryLog, GameProgress, MangaProgress, SeriesProgress,
    UserMediaProgress, UserMediaStatus
)


class UserMediaStatusSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = UserMediaStatus
        fields = [
            'id',
            'user',
            'username',
            'media_item',
            'status',
            'status_display',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, attrs):
        media_item = attrs.get('media_item') or getattr(self.instance, 'media_item', None)
        status_val = attrs.get('status') or getattr(self.instance, 'status', None)

        if media_item and status_val:
            # Temporary instance for clean() validation
            user = self.context['request'].user
            instance = UserMediaStatus(user=user, media_item=media_item, status=status_val)
            instance.clean()
        return attrs


class SeriesProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeriesProgress
        fields = ['id', 'current_season', 'current_episode', 'last_watched_episode_title']
        read_only_fields = ['id']


class MangaProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = MangaProgress
        fields = ['id', 'current_chapter', 'current_volume']
        read_only_fields = ['id']


class GameProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameProgress
        fields = ['id', 'hours_played', 'completion_type', 'platform_played_on']
        read_only_fields = ['id']


class UserMediaProgressSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    series_progress = SeriesProgressSerializer(required=False)
    manga_progress = MangaProgressSerializer(required=False)
    game_progress = GameProgressSerializer(required=False)

    class Meta:
        model = UserMediaProgress
        fields = [
            'id',
            'user',
            'username',
            'media_item',
            'series_progress',
            'manga_progress',
            'game_progress',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = validated_data.pop('user', getattr(self.context.get('request'), 'user', None))
        series_data = validated_data.pop('series_progress', None)
        manga_data = validated_data.pop('manga_progress', None)
        game_data = validated_data.pop('game_progress', None)

        progress = UserMediaProgress.objects.create(user=user, **validated_data)
        media_type = progress.media_item.media_type

        if media_type == 'SERIES' and series_data:
            SeriesProgress.objects.create(progress=progress, **series_data)
        elif media_type == 'MANGA' and manga_data:
            MangaProgress.objects.create(progress=progress, **manga_data)
        elif media_type == 'GAME' and game_data:
            GameProgress.objects.create(progress=progress, **game_data)

        return progress

    def update(self, instance, validated_data):
        series_data = validated_data.pop('series_progress', None)
        manga_data = validated_data.pop('manga_progress', None)
        game_data = validated_data.pop('game_progress', None)

        media_type = instance.media_item.media_type

        if media_type == 'SERIES' and series_data:
            sp, _ = SeriesProgress.objects.update_or_create(
                progress=instance,
                defaults=series_data
            )
            instance.series_progress = sp
        elif media_type == 'MANGA' and manga_data:
            mp, _ = MangaProgress.objects.update_or_create(
                progress=instance,
                defaults=manga_data
            )
            instance.manga_progress = mp
        elif media_type == 'GAME' and game_data:
            gp, _ = GameProgress.objects.update_or_create(
                progress=instance,
                defaults=game_data
            )
            instance.game_progress = gp

        instance.save()
        return instance


class DiaryLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    media_title = serializers.CharField(source='media_item.title', read_only=True)
    sync_progress = serializers.BooleanField(write_only=True, default=True, required=False)

    class Meta:
        model = DiaryLog
        fields = [
            'id',
            'user',
            'username',
            'media_item',
            'media_title',
            'logged_date',
            'is_rewatch_or_replay',
            'session_notes',
            'progress_snapshot',
            'sync_progress',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = validated_data.pop('user', getattr(self.context.get('request'), 'user', None))
        sync_progress = validated_data.pop('sync_progress', True)
        return DiaryLog.objects.create(user=user, sync_progress=sync_progress, **validated_data)
