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

import dj_database_url

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

# Comma-separated in the env var, e.g. "stephensteerscomedy.com,www.stephensteerscomedy.com".
# Render's own *.onrender.com hostname is added automatically so health
# checks and the dashboard preview link keep working alongside your domain.
ALLOWED_HOSTS = [h for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',') if h]
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Django checks the Origin header on POSTs (both site forms use this) against
# this list once DEBUG is off. Needs the scheme, e.g. "https://stephensteerscomedy.com".
CSRF_TRUSTED_ORIGINS = [o for o in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')

if not DEBUG:
    # Render terminates TLS at its proxy and talks plain HTTP to the app,
    # so this header is what tells Django the original request was HTTPS.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 1 week to start; raise once you're confident
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

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
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
# Reads DATABASE_URL when it's set (Render provides this automatically once
# a Postgres database is attached to the service) and falls back to the
# local SQLite file otherwise, so `manage.py runserver` on your machine
# needs no extra setup.
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
    )
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
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise serves collected static files directly from the app process —
# no separate web server or CDN needed — and this storage backend adds
# far-future cache headers plus gzip/brotli compression for free.
# build.sh runs `collectstatic` on every deploy to populate STATIC_ROOT.
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

MEDIA_URL = 'media/'
# On Render, set MEDIA_ROOT (via the DJANGO_MEDIA_ROOT env var) to the mount
# path of an attached persistent disk — e.g. /var/data/media — otherwise
# uploaded photos/video vanish on every redeploy, since the rest of the
# filesystem is wiped and rebuilt each time. See render.yaml.
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', BASE_DIR / 'media'))

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
