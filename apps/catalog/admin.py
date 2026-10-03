"""
Django Admin Configuration for Media Catalog.
"""

from django.contrib import admin
from .models import (
    Genre, Tag, MediaItem, MovieDetail, SeriesDetail, MangaDetail, GameDetail,
    ExternalProvider, ExternalMediaMapping
)


class MovieDetailInline(admin.StackedInline):
    model = MovieDetail
    can_delete = False
    verbose_name_plural = 'Movie Details'
    extra = 0


class SeriesDetailInline(admin.StackedInline):
    model = SeriesDetail
    can_delete = False
    verbose_name_plural = 'Series Details'
    extra = 0


class MangaDetailInline(admin.StackedInline):
    model = MangaDetail
    can_delete = False
    verbose_name_plural = 'Manga Details'
    extra = 0


class GameDetailInline(admin.StackedInline):
    model = GameDetail
    can_delete = False
    verbose_name_plural = 'Game Details'
    extra = 0


class ExternalMediaMappingInline(admin.TabularInline):
    model = ExternalMediaMapping
    extra = 0
    readonly_fields = ('last_synced_at',)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(MediaItem)
class MediaItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'media_type', 'release_year', 'created_at')
    list_filter = ('media_type', 'release_year', 'genres')
    search_fields = ('title', 'synopsis', 'slug')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('genres', 'tags')
    inlines = [
        MovieDetailInline, SeriesDetailInline, MangaDetailInline, GameDetailInline,
        ExternalMediaMappingInline
    ]


@admin.register(MovieDetail)
class MovieDetailAdmin(admin.ModelAdmin):
    list_display = ('media_item', 'director', 'runtime_minutes', 'studio')
    search_fields = ('media_item__title', 'director', 'studio')


@admin.register(SeriesDetail)
class SeriesDetailAdmin(admin.ModelAdmin):
    list_display = ('media_item', 'total_seasons', 'total_episodes', 'status')
    list_filter = ('status',)
    search_fields = ('media_item__title', 'creators')


@admin.register(MangaDetail)
class MangaDetailAdmin(admin.ModelAdmin):
    list_display = ('media_item', 'author', 'manga_type', 'status', 'total_chapters')
    list_filter = ('manga_type', 'status')
    search_fields = ('media_item__title', 'author', 'artist')


@admin.register(GameDetail)
class GameDetailAdmin(admin.ModelAdmin):
    list_display = ('media_item', 'developer', 'publisher', 'average_story_hours')
    search_fields = ('media_item__title', 'developer', 'publisher')


@admin.register(ExternalProvider)
class ExternalProviderAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'provider_key', 'base_url', 'active')
    list_editable = ('active',)
    search_fields = ('display_name', 'provider_key')


@admin.register(ExternalMediaMapping)
class ExternalMediaMappingAdmin(admin.ModelAdmin):
    list_display = ('media_item', 'provider', 'external_id', 'last_synced_at')
    list_filter = ('provider',)
    search_fields = ('media_item__title', 'external_id')
    readonly_fields = ('last_synced_at',)
