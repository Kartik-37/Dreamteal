"""
Django Admin Configuration for Tracking, Progress, and Diary Logs.
"""

from django.contrib import admin
from .models import (
    UserMediaStatus,
    UserMediaProgress,
    SeriesProgress,
    MangaProgress,
    GameProgress,
    DiaryLog
)


@admin.register(UserMediaStatus)
class UserMediaStatusAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_item', 'status', 'is_favorite', 'updated_at')
    list_filter = ('status', 'is_favorite')
    search_fields = ('user__username', 'media_item__title')


class SeriesProgressInline(admin.StackedInline):
    model = SeriesProgress
    can_delete = False
    extra = 0


class MangaProgressInline(admin.StackedInline):
    model = MangaProgress
    can_delete = False
    extra = 0


class GameProgressInline(admin.StackedInline):
    model = GameProgress
    can_delete = False
    extra = 0


@admin.register(UserMediaProgress)
class UserMediaProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_item', 'updated_at')
    search_fields = ('user__username', 'media_item__title')
    inlines = [SeriesProgressInline, MangaProgressInline, GameProgressInline]


@admin.register(SeriesProgress)
class SeriesProgressAdmin(admin.ModelAdmin):
    list_display = ('progress', 'current_season', 'current_episode', 'last_watched_episode_title')
    search_fields = ('progress__user__username', 'progress__media_item__title')


@admin.register(MangaProgress)
class MangaProgressAdmin(admin.ModelAdmin):
    list_display = ('progress', 'current_chapter', 'current_volume')
    search_fields = ('progress__user__username', 'progress__media_item__title')


@admin.register(GameProgress)
class GameProgressAdmin(admin.ModelAdmin):
    list_display = ('progress', 'hours_played', 'completion_type', 'platform_played_on')
    list_filter = ('completion_type',)
    search_fields = ('progress__user__username', 'progress__media_item__title')


@admin.register(DiaryLog)
class DiaryLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'media_item', 'logged_date', 'is_rewatch_or_replay', 'created_at')
    list_filter = ('is_rewatch_or_replay', 'logged_date')
    search_fields = ('user__username', 'media_item__title', 'session_notes')
