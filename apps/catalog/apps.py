from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """
    Django app configuration for DreamTeal's unified multi-media catalog.
    Manages global MediaItem records, genres, tags, and category-specific
    detail models for Movies, TV Series, Manga/Manhwa, and Video Games.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.catalog'
    verbose_name = 'Media Catalog'
