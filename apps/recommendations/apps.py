from django.apps import AppConfig


class RecommendationsConfig(AppConfig):
    """
    Django app configuration for DreamTeal's in-house deterministic recommendation engine.
    Computes explainable, multi-signal "What to consume next" suggestions across Movies,
    TV Series, Manga/Manhwa, and Video Games without external APIs or black-box ML.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.recommendations'
    verbose_name = 'Recommendations Engine'
