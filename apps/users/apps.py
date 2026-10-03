from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    Django app configuration for DreamTeal user profiles and authentication.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Users & Profiles'
