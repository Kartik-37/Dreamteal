from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    """
    Django app configuration for DreamTeal's qualitative reaction system
    and written reviews. Strictly excludes star and numeric ratings.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reviews'
    verbose_name = 'Reviews & Reactions'
