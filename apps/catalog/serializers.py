"""
Serializers and Query Parameter Validators for Media Catalog in DreamTeal.
Adheres strictly to the Zero-Star Rating Policy.
"""

from rest_framework import serializers
from apps.catalog.models import (
    ExternalMediaMapping, ExternalProvider, GameDetail, Genre,
    MangaDetail, MediaItem, MovieDetail, SeriesDetail, Tag
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class ExternalProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalProvider
        fields = ['provider_key', 'display_name', 'base_url', 'attribution_text', 'attribution_url', 'active']


class ExternalMediaMappingSerializer(serializers.ModelSerializer):
    provider_name = serializers.CharField(source='provider.display_name', read_only=True)
    provider_key = serializers.CharField(source='provider.provider_key', read_only=True)

    class Meta:
        model = ExternalMediaMapping
        fields = ['id', 'provider_key', 'provider_name', 'external_id', 'external_url', 'last_synced_at']


class MovieDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieDetail
        fields = ['director', 'runtime_minutes', 'studio', 'ott_providers']


class SeriesDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeriesDetail
        fields = ['creators', 'total_seasons', 'total_episodes', 'status', 'ott_providers']


class MangaDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MangaDetail
        fields = ['author', 'artist', 'manga_type', 'status', 'total_chapters']


class GameDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameDetail
        fields = ['developer', 'publisher', 'platforms', 'average_story_hours']


class MediaItemListSerializer(serializers.ModelSerializer):
    """
    Lightweight media card serializer for grid browsing, lists, and catalog search.
    """
    genres = GenreSerializer(many=True, read_only=True)
    media_type_display = serializers.CharField(source='get_media_type_display', read_only=True)

    class Meta:
        model = MediaItem
        fields = [
            'id',
            'title',
            'slug',
            'media_type',
            'media_type_display',
            'release_year',
            'poster_url',
            'backdrop_url',
            'synopsis',
            'genres',
        ]


class MediaItemDetailSerializer(serializers.ModelSerializer):
    """
    Comprehensive media item serializer with polymorphic category extension models.
    """
    genres = GenreSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    media_type_display = serializers.CharField(source='get_media_type_display', read_only=True)

    movie_detail = MovieDetailSerializer(read_only=True)
    series_detail = SeriesDetailSerializer(read_only=True)
    manga_detail = MangaDetailSerializer(read_only=True)
    game_detail = GameDetailSerializer(read_only=True)
    external_mappings = ExternalMediaMappingSerializer(many=True, read_only=True)

    class Meta:
        model = MediaItem
        fields = [
            'id',
            'title',
            'slug',
            'media_type',
            'media_type_display',
            'release_year',
            'synopsis',
            'poster_url',
            'backdrop_url',
            'genres',
            'tags',
            'movie_detail',
            'series_detail',
            'manga_detail',
            'game_detail',
            'external_mappings',
            'created_at',
            'updated_at',
        ]


# =========================================================================
# Query Parameter & Request Body Validators (Strict Error Handling: 400)
# =========================================================================

class MediaImportRequestSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(
        choices=['tmdb', 'anilist', 'jikan', 'rawg', 'TMDB', 'ANILIST', 'JIKAN', 'RAWG']
    )
    external_id = serializers.CharField(max_length=100, min_length=1)
    media_type = serializers.ChoiceField(
        choices=['MOVIE', 'SERIES', 'MANGA', 'GAME', 'movie', 'series', 'manga', 'game'],
        required=False,
        allow_blank=True,
        allow_null=True
    )
    force_refresh = serializers.BooleanField(required=False, default=False)
    title_hint = serializers.CharField(required=False, allow_blank=True, default='')


class MediaSearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, default='')
    category = serializers.ChoiceField(
        choices=['MOVIE', 'SERIES', 'MANGA', 'MANHWA', 'GAME', 'movie', 'series', 'manga', 'manhwa', 'game'],
        required=False,
        allow_null=True
    )
    limit = serializers.IntegerField(required=False, default=20, min_value=1, max_value=50)


class DiscoveryQuerySerializer(serializers.Serializer):
    mode = serializers.ChoiceField(
        choices=['popular', 'latest', 'trending', 'upcoming', 'POPULAR', 'LATEST', 'TRENDING', 'UPCOMING'],
        required=False,
        default='popular'
    )
    limit = serializers.IntegerField(required=False, default=20, min_value=1, max_value=50)


class MediaListQuerySerializer(serializers.Serializer):
    category = serializers.ChoiceField(
        choices=['MOVIE', 'SERIES', 'MANGA', 'GAME', 'movie', 'series', 'manga', 'game'],
        required=False
    )
    media_type = serializers.ChoiceField(
        choices=['MOVIE', 'SERIES', 'MANGA', 'GAME', 'movie', 'series', 'manga', 'game'],
        required=False
    )
    genre = serializers.SlugField(required=False)
    tag = serializers.SlugField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
    q = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.ChoiceField(
        choices=['-release_year', 'release_year', 'title', '-title', '-created_at', 'created_at'],
        required=False,
        default='-release_year'
    )
