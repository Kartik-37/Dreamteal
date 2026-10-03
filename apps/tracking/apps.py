from django.apps import AppConfig


class TrackingConfig(AppConfig):
    """
    Django app configuration for user tracking, category-specific progress,
    and history-preserving diary logging with automatic forward synchronization.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tracking'
    verbose_name = 'User Tracking & Progress'
