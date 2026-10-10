"""
Serializers for User Tracking, Progress, and History-Preserving Diary Logs in DreamTeal.
Strictly adheres to the Zero-Star Rating Policy.
Enforces strict category-specific validation, numeric bounds, and transaction safety.
"""

from decimal import Decimal
from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import MediaItem
from apps.tracking.models import (
    DiaryLog, GameProgress, MangaProgress, SeriesProgress,
    UserMediaProgress, UserMediaStatus
)


class UserMediaStatusSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    media_item = serializers.PrimaryKeyRelatedField(
        queryset=MediaItem.objects.all(),
        required=False
    )
    media_id = serializers.PrimaryKeyRelatedField(
        queryset=MediaItem.objects.all(),
        source='media_item',
        required=False,
        write_only=True
    )

    class Meta:
        model = UserMediaStatus
        fields = [
            'id',
            'user',
            'username',
            'media_item',
            'media_id',
            'status',
            'status_display',
            'is_favorite',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, attrs):
        media_item = attrs.get('media_item') or getattr(self.instance, 'media_item', None)
        status_val = attrs.get('status') or getattr(self.instance, 'status', None)

        if not media_item and not self.instance:
            raise serializers.ValidationError({'media_item': 'This field is required.'})

        if media_item and status_val:
            user = self.context.get('request').user if 'request' in self.context else getattr(self.instance, 'user', None)
            if user:
                instance = UserMediaStatus(user=user, media_item=media_item, status=status_val)
                instance.clean()
        return attrs


class SeriesProgressSerializer(serializers.ModelSerializer):
    current_season = serializers.IntegerField(min_value=0, default=0)
    current_episode = serializers.IntegerField(min_value=0, default=0)

    class Meta:
        model = SeriesProgress
        fields = ['id', 'current_season', 'current_episode', 'last_watched_episode_title']
        read_only_fields = ['id']


class MangaProgressSerializer(serializers.ModelSerializer):
    current_chapter = serializers.IntegerField(min_value=0, default=0)
    current_volume = serializers.IntegerField(min_value=0, required=False, allow_null=True)

    class Meta:
        model = MangaProgress
        fields = ['id', 'current_chapter', 'current_volume']
        read_only_fields = ['id']


class GameProgressSerializer(serializers.ModelSerializer):
    hours_played = serializers.DecimalField(
        max_digits=6,
        decimal_places=1,
        min_value=Decimal('0.0'),
        default=Decimal('0.0')
    )

    class Meta:
        model = GameProgress
        fields = ['id', 'hours_played', 'completion_type', 'platform_played_on']
        read_only_fields = ['id']


class UserMediaProgressSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    media_item = serializers.PrimaryKeyRelatedField(
        queryset=MediaItem.objects.all(),
        required=False
    )
    media_id = serializers.PrimaryKeyRelatedField(
        queryset=MediaItem.objects.all(),
        source='media_item',
        required=False,
        write_only=True
    )
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
            'media_id',
            'series_progress',
            'manga_progress',
            'game_progress',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, attrs):
        media_item = attrs.get('media_item') or getattr(self.instance, 'media_item', None)
        if not media_item and not self.instance:
            raise serializers.ValidationError({'media_item': 'This field is required.'})

        if media_item:
            media_type = media_item.media_type
            # Check for incompatible nested progress objects
            series_in = 'series_progress' in self.initial_data or 'series_progress' in attrs
            manga_in = 'manga_progress' in self.initial_data or 'manga_progress' in attrs
            game_in = 'game_progress' in self.initial_data or 'game_progress' in attrs

            if media_type == 'SERIES':
                if manga_in:
                    raise serializers.ValidationError({'manga_progress': 'Manga progress cannot be attached to a SERIES media item.'})
                if game_in:
                    raise serializers.ValidationError({'game_progress': 'Game progress cannot be attached to a SERIES media item.'})
            elif media_type == 'MANGA':
                if series_in:
                    raise serializers.ValidationError({'series_progress': 'Series progress cannot be attached to a MANGA media item.'})
                if game_in:
                    raise serializers.ValidationError({'game_progress': 'Game progress cannot be attached to a MANGA media item.'})
            elif media_type == 'GAME':
                if series_in:
                    raise serializers.ValidationError({'series_progress': 'Series progress cannot be attached to a GAME media item.'})
                if manga_in:
                    raise serializers.ValidationError({'manga_progress': 'Manga progress cannot be attached to a GAME media item.'})
            elif media_type == 'MOVIE':
                if series_in or manga_in or game_in:
                    raise serializers.ValidationError({'detail': 'Nested progress objects cannot be attached to a MOVIE media item.'})

        return attrs

    @transaction.atomic
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

    @transaction.atomic
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
    media_item = serializers.PrimaryKeyRelatedField(
        queryset=MediaItem.objects.all(),
        required=False
    )
    media_id = serializers.PrimaryKeyRelatedField(
        queryset=MediaItem.objects.all(),
        source='media_item',
        required=False,
        write_only=True
    )
    sync_progress = serializers.BooleanField(write_only=True, default=True, required=False)

    class Meta:
        model = DiaryLog
        fields = [
            'id',
            'user',
            'username',
            'media_item',
            'media_id',
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

    def validate_progress_snapshot(self, value):
        if value is not None:
            if not isinstance(value, dict):
                raise serializers.ValidationError("progress_snapshot must be a JSON object.")
            # Strip internal _synced_hours so clients can never forge synced totals
            value.pop('_synced_hours', None)

            # Validate numeric bounds
            if 'session_hours' in value:
                try:
                    h = Decimal(str(value['session_hours']))
                    if h < 0:
                        raise serializers.ValidationError("session_hours cannot be negative.")
                except (ValueError, TypeError):
                    raise serializers.ValidationError("session_hours must be a valid number.")

            for int_field in ['season', 'episode', 'chapter', 'volume']:
                if int_field in value and value[int_field] is not None:
                    try:
                        iv = int(value[int_field])
                        if iv < 0:
                            raise serializers.ValidationError(f"{int_field} cannot be negative.")
                    except (ValueError, TypeError):
                        raise serializers.ValidationError(f"{int_field} must be a valid integer.")
        return value

    def validate(self, attrs):
        media_item = attrs.get('media_item') or getattr(self.instance, 'media_item', None)
        if not media_item and not self.instance:
            raise serializers.ValidationError({'media_item': 'This field is required.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        user = validated_data.pop('user', getattr(self.context.get('request'), 'user', None))
        sync_progress = validated_data.pop('sync_progress', True)
        return DiaryLog.objects.create(user=user, sync_progress=sync_progress, **validated_data)

    @transaction.atomic
    def update(self, instance, validated_data):
        sync_progress = validated_data.pop('sync_progress', True)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(sync_progress=sync_progress)
        return instance
