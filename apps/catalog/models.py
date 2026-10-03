"""
Media Catalog Models for DreamTeal.

Defines the core pop-culture catalog hierarchy:
- Base MediaItem (shared metadata across Movies, Series, Manga, Games)
- Genre & Tag (thematic vibe metadata)
- Media-type extension models: MovieDetail, SeriesDetail, MangaDetail, GameDetail
"""

import uuid
from django.core.exceptions import ValidationError
from django.db import models


class Genre(models.Model):
    """
    Standardized global genre classification (e.g., Action, Sci-Fi, Cyberpunk).
    Shared across all media categories to enable cross-category matching.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Genre'
        verbose_name_plural = 'Genres'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    Thematic vibe, atmosphere, and keyword tags (e.g. 'Mind-Bending', 'Cozy', 'Dark Fantasy').
    Key pillar for DreamTeal's deterministic 'What to consume next' recommendation engine.
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'

    def __str__(self):
        return self.name


class MediaItem(models.Model):
    """
    Base catalog representation for all media formats in DreamTeal.
    Stores shared high-level metadata; specialized category attributes are stored
    in 1:1 extension models (MovieDetail, SeriesDetail, MangaDetail, GameDetail).
    """

    class MediaType(models.TextChoices):
        MOVIE = 'MOVIE', 'Movie'
        SERIES = 'SERIES', 'TV Series'
        MANGA = 'MANGA', 'Manga / Manhwa'
        GAME = 'GAME', 'Video Game'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
        db_index=True,
        help_text="Primary category format of this pop-culture media item."
    )
    title = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(
        max_length=280,
        unique=True,
        db_index=True,
        help_text="Unique URL slug, formatted as {title-kebab-case}-{year}."
    )
    synopsis = models.TextField(blank=True, default='')
    release_year = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    poster_url = models.URLField(max_length=500, blank=True, default='')
    backdrop_url = models.URLField(max_length=500, blank=True, default='')

    # Relational taxonomy
    genres = models.ManyToManyField(Genre, blank=True, related_name='media_items')
    tags = models.ManyToManyField(Tag, blank=True, related_name='media_items')

    # Optional third-party integration ingestion hooks
    tmdb_id = models.CharField(max_length=50, blank=True, null=True, help_text="Optional TMDb ID")
    mal_id = models.CharField(max_length=50, blank=True, null=True, help_text="Optional MyAnimeList ID")
    rawg_id = models.CharField(max_length=50, blank=True, null=True, help_text="Optional RAWG Game ID")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-release_year', 'title']
        verbose_name = 'Media Item'
        verbose_name_plural = 'Media Items'
        indexes = [
            models.Index(fields=['media_type', 'release_year']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        year_str = f" ({self.release_year})" if self.release_year else ""
        return f"{self.title}{year_str} [{self.get_media_type_display()}]"


class MovieDetail(models.Model):
    """
    Category extension for Movies.
    Linked 1:1 to MediaItem where media_type == MOVIE.
    """
    media_item = models.OneToOneField(
        MediaItem,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='movie_detail'
    )
    director = models.CharField(max_length=255, blank=True, default='')
    runtime_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Runtime in minutes.")
    studio = models.CharField(max_length=255, blank=True, default='')
    ott_providers = models.JSONField(
        default=list,
        blank=True,
        help_text="List of streaming services (e.g. ['Netflix', 'Prime Video'])."
    )

    class Meta:
        verbose_name = 'Movie Detail'
        verbose_name_plural = 'Movie Details'

    def clean(self):
        super().clean()
        if self.media_item.media_type != MediaItem.MediaType.MOVIE:
            raise ValidationError(
                f"Cannot attach MovieDetail to MediaItem with media_type='{self.media_item.media_type}'. Must be 'MOVIE'."
            )

    def __str__(self):
        return f"Movie Details: {self.media_item.title}"


class SeriesDetail(models.Model):
    """
    Category extension for TV / Episodic Series.
    Linked 1:1 to MediaItem where media_type == SERIES.
    """
    class SeriesStatus(models.TextChoices):
        AIRING = 'AIRING', 'Airing'
        ENDED = 'ENDED', 'Ended'
        CANCELLED = 'CANCELLED', 'Cancelled'

    media_item = models.OneToOneField(
        MediaItem,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='series_detail'
    )
    creators = models.CharField(max_length=255, blank=True, default='')
    total_seasons = models.PositiveIntegerField(default=1)
    total_episodes = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=SeriesStatus.choices,
        default=SeriesStatus.AIRING
    )
    ott_providers = models.JSONField(
        default=list,
        blank=True,
        help_text="List of broadcast networks/streaming platforms."
    )

    class Meta:
        verbose_name = 'Series Detail'
        verbose_name_plural = 'Series Details'

    def clean(self):
        super().clean()
        if self.media_item.media_type != MediaItem.MediaType.SERIES:
            raise ValidationError(
                f"Cannot attach SeriesDetail to MediaItem with media_type='{self.media_item.media_type}'. Must be 'SERIES'."
            )

    def __str__(self):
        return f"Series Details: {self.media_item.title} ({self.total_seasons} Seasons)"


class MangaDetail(models.Model):
    """
    Category extension for Manga, Manhwa, Manhua, and Webtoons.
    Linked 1:1 to MediaItem where media_type == MANGA.
    """
    class MangaType(models.TextChoices):
        MANGA = 'MANGA', 'Manga'
        MANHWA = 'MANHWA', 'Manhwa'
        MANHUA = 'MANHUA', 'Manhua'
        WEBTOON = 'WEBTOON', 'Webtoon'

    class PublicationStatus(models.TextChoices):
        PUBLISHING = 'PUBLISHING', 'Publishing'
        FINISHED = 'FINISHED', 'Finished'
        HIATUS = 'HIATUS', 'On Hiatus'

    media_item = models.OneToOneField(
        MediaItem,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='manga_detail'
    )
    author = models.CharField(max_length=255, blank=True, default='')
    artist = models.CharField(max_length=255, blank=True, default='')
    manga_type = models.CharField(
        max_length=20,
        choices=MangaType.choices,
        default=MangaType.MANGA
    )
    status = models.CharField(
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PUBLISHING
    )
    total_chapters = models.PositiveIntegerField(null=True, blank=True, help_text="Null if ongoing publication.")

    class Meta:
        verbose_name = 'Manga Detail'
        verbose_name_plural = 'Manga Details'

    def clean(self):
        super().clean()
        if self.media_item.media_type != MediaItem.MediaType.MANGA:
            raise ValidationError(
                f"Cannot attach MangaDetail to MediaItem with media_type='{self.media_item.media_type}'. Must be 'MANGA'."
            )

    def __str__(self):
        return f"{self.get_manga_type_display()} Details: {self.media_item.title}"


class GameDetail(models.Model):
    """
    Category extension for Video Games.
    Linked 1:1 to MediaItem where media_type == GAME.
    """
    media_item = models.OneToOneField(
        MediaItem,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='game_detail'
    )
    developer = models.CharField(max_length=255, blank=True, default='')
    publisher = models.CharField(max_length=255, blank=True, default='')
    platforms = models.JSONField(
        default=list,
        blank=True,
        help_text="Supported platforms, e.g. ['PC', 'PS5', 'Xbox', 'Switch']."
    )
    average_story_hours = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Estimated main story completion time in hours."
    )

    class Meta:
        verbose_name = 'Game Detail'
        verbose_name_plural = 'Game Details'

    def clean(self):
        super().clean()
        if self.media_item.media_type != MediaItem.MediaType.GAME:
            raise ValidationError(
                f"Cannot attach GameDetail to MediaItem with media_type='{self.media_item.media_type}'. Must be 'GAME'."
            )

    def __str__(self):
        return f"Game Details: {self.media_item.title}"


class ExternalProvider(models.Model):
    """
    Registry of third-party pop-culture metadata providers (e.g., TMDB, AniList, Jikan, RAWG).
    Stores service identifiers and data-driven legal attribution notices.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider_key = models.SlugField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Canonical provider identifier (e.g. 'tmdb', 'anilist', 'jikan', 'rawg')."
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Human-readable title (e.g. 'TMDB', 'AniList', 'Jikan', 'RAWG')."
    )
    base_url = models.URLField(max_length=255, blank=True, default='')
    attribution_text = models.TextField(
        blank=True,
        default='',
        help_text="Mandatory legal attribution notice required by provider terms."
    )
    attribution_url = models.URLField(max_length=255, blank=True, default='')
    active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Toggle enabling or disabling integration with this provider."
    )

    class Meta:
        ordering = ['provider_key']
        verbose_name = 'External Provider'
        verbose_name_plural = 'External Providers'

    def __str__(self):
        return self.display_name


class ExternalMediaMapping(models.Model):
    """
    Links a DreamTeal MediaItem to its external provider identifier.
    Guarantees that (provider, external_id) is unique so third-party records
    do not map to multiple DreamTeal media items.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    media_item = models.ForeignKey(
        MediaItem,
        on_delete=models.CASCADE,
        related_name='external_mappings',
        help_text="The local DreamTeal media catalog record."
    )
    provider = models.ForeignKey(
        ExternalProvider,
        on_delete=models.CASCADE,
        related_name='mappings',
        help_text="The external source provider."
    )
    external_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="The provider's unique ID for this media (e.g. TMDB movie ID, AniList media ID)."
    )
    external_url = models.URLField(
        max_length=500,
        blank=True,
        default='',
        help_text="Direct link to media page on the provider's platform."
    )
    last_synced_at = models.DateTimeField(auto_now=True)
    source_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when provider last updated this record, if reported."
    )

    class Meta:
        verbose_name = 'External Media Mapping'
        verbose_name_plural = 'External Media Mappings'
        constraints = [
            models.UniqueConstraint(
                fields=['provider', 'external_id'],
                name='unique_provider_external_id'
            )
        ]
        indexes = [
            models.Index(fields=['provider', 'external_id']),
            models.Index(fields=['media_item', 'provider']),
        ]

    def __str__(self):
        return f"{self.provider.display_name}:{self.external_id} -> {self.media_item.title}"

