"""
Django settings for DreamTeal pop-culture tracking platform.
Phase 1: Backend Data Foundations.
"""

import os
import sys
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Automatically load environment variables from .env if present
load_dotenv(BASE_DIR / '.env')

# Add 'apps' to Python sys.path so apps can import cleanly if needed
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG_ENV = os.environ.get('DEBUG')
DEBUG = DEBUG_ENV.lower() in ('true', '1', 'yes') if DEBUG_ENV is not None else True

# SECURITY WARNING: keep the secret key used in production secret!
# Never keep a known default fallback in source code.
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if 'test' in sys.argv:
        # Ephemeral isolated key strictly for offline test runner execution when no .env is present
        SECRET_KEY = 'django-insecure-test-runner-ephemeral-key-never-used-in-production'
    else:
        raise ImproperlyConfigured(
            "The SECRET_KEY environment variable is required. "
            "Please create a .env file (copy from .env.example) or export SECRET_KEY in your environment."
        )

# Validate that insecure development keys are never permitted when DEBUG is False
if not DEBUG and 'django-insecure' in SECRET_KEY:
    raise ImproperlyConfigured("Insecure development SECRET_KEY cannot be used when DEBUG=False.")

ALLOWED_HOSTS_ENV = os.environ.get('ALLOWED_HOSTS')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS_ENV.split(',') if h.strip()]
elif DEBUG:
    ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
else:
    raise ImproperlyConfigured("ALLOWED_HOSTS must be explicitly defined in environment/.env when DEBUG=False.")



# Application definition

INSTALLED_APPS = [
    # Core Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party packages
    'rest_framework',
    'corsheaders',

    # DreamTeal modular apps
    'apps.catalog.apps.CatalogConfig',
    'apps.tracking.apps.TrackingConfig',
    'apps.reviews.apps.ReviewsConfig',
    'apps.users.apps.UsersConfig',
    'apps.recommendations.apps.RecommendationsConfig',
]

MIDDLEWARE = [
    # CorsMiddleware must be as high as possible, especially before CommonMiddleware
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dreamteal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'dreamteal.wsgi.application'


# Database
# Built-in SQLite for development; structured for effortless PostgreSQL migration via standard fields
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static and Media Files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Django REST Framework Configuration
# Uses SessionAuthentication with CSRF enforcement per approved product decisions
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 24,
}


# CORS & CSRF Configuration (Approved for React + Vite Frontend)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
]
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:3000',
]

# Ensure cookies can be shared smoothly in development and production
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Allows frontend JavaScript to read csrftoken for X-CSRFToken header

# External Metadata Providers Configuration (Server-Side Only)
# Never expose these credentials to the client/React bundle.
TMDB_ACCESS_TOKEN = os.environ.get('TMDB_ACCESS_TOKEN', '')
TMDB_API_KEY = os.environ.get('TMDB_API_KEY', '')
RAWG_API_KEY = os.environ.get('RAWG_API_KEY', '')

# Provider Synchronization & Freshness
CATALOG_SYNC_FRESHNESS_HOURS = int(os.environ.get('CATALOG_SYNC_FRESHNESS_HOURS', '24'))
PROVIDER_HTTP_TIMEOUT = int(os.environ.get('PROVIDER_HTTP_TIMEOUT', '8'))

# Region configuration for provider streaming data (e.g. TMDB watch providers)
DEFAULT_PROVIDER_REGION = os.environ.get('DEFAULT_PROVIDER_REGION', 'IN').upper()


