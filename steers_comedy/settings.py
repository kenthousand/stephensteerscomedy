"""
Django settings for the Steers Comedy site.

This is a small, single-app project meant to be easy to run and easy to
hand off. For local development the defaults below work out of the box
(SQLite, DEBUG on). Before deploying anywhere public, read through the
"PRODUCTION" notes marked below and the project README.
"""

from pathlib import Path
import os
import secrets

BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY -----------------------------------------------------------
# PRODUCTION: set a real, secret SECRET_KEY via an environment variable
# (e.g. `export DJANGO_SECRET_KEY=...`) instead of relying on this
# randomly-generated fallback, which changes every time the app restarts
# unless SECRET_KEY_FALLBACK is set below.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or secrets.token_urlsafe(50)

# PRODUCTION: set DEBUG=False and fill in ALLOWED_HOSTS with your real
# domain(s) before this ever goes on the public internet.
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# --- APPS -----------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'comedy',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'steers_comedy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'steers_comedy.wsgi.application'
ASGI_APPLICATION = 'steers_comedy.asgi.application'

# --- DATABASE ---------------------------------------------------------
# SQLite is fine for a single-comedian site with light traffic. Swap in
# Postgres later by changing this block if you outgrow it.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

# --- STATIC & MEDIA -----------------------------------------------------
STATIC_URL = 'static/'
# PRODUCTION: run `python manage.py collectstatic` and serve STATIC_ROOT
# with your web server (or whitenoise) instead of Django's dev server.
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# --- CACHE -----------------------------------------------------------
# Backs the Instagram sync (comedy/instagram.py): recent posts are fetched
# live and cached for an hour rather than stored permanently, since
# Instagram's media URLs are signed and expire. A database-backed cache
# (instead of Django's default in-memory cache) means this works correctly
# even behind multiple worker processes. Run `python manage.py
# createcachetable` once after the first migrate to create its table.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Where the booking form's "thanks" redirect and admin links point.
LOGIN_URL = '/admin/login/'
