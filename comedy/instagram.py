"""Pull recent posts from Instagram for the Clips section.

Uses the Instagram API with Instagram Login (the current replacement for
the retired Basic Display API) — see the "Instagram sync" section of the
README for how to get an access token for your own account. Standard
Access is enough for this (no Meta App Review needed) as long as the app
only ever reads the account that created it, which is the only thing
this does.

Nothing here talks to Instagram unless InstagramSettings has sync turned
on and both an ig_user_id and access_token saved — see get_recent_clips().
"""

import logging

import requests
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

GRAPH_API_BASE = 'https://graph.instagram.com'
MEDIA_FIELDS = 'id,caption,media_type,media_url,permalink,thumbnail_url,timestamp'
CACHE_KEY = 'instagram:recent_media'
CACHE_TIMEOUT_SECONDS = 60 * 60  # re-check Instagram at most once an hour
REQUEST_TIMEOUT_SECONDS = 6


class InstagramAPIError(Exception):
    """Raised when Instagram's API returns an error or an unusable response."""


def fetch_recent_media(ig_user_id, access_token, limit=6):
    """Fetch raw media objects for one Instagram professional account.

    Raises InstagramAPIError (or a requests exception) on any failure —
    callers are expected to catch and fall back gracefully.
    """
    url = f'{GRAPH_API_BASE}/{ig_user_id}/media'
    params = {'fields': MEDIA_FIELDS, 'limit': limit, 'access_token': access_token}
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    payload = response.json()
    if response.status_code != 200 or 'error' in payload:
        message = (payload.get('error') or {}).get('message', 'Unknown Instagram API error')
        raise InstagramAPIError(f'Instagram API error ({response.status_code}): {message}')
    return payload.get('data', [])


def normalize_media(raw_items):
    """Turn Instagram's media objects into the same shape the templates use
    for manually-added Clips: title, url, thumbnail_url, platform_label."""
    normalized = []
    for item in raw_items:
        media_type = item.get('media_type')
        if media_type == 'VIDEO':
            thumbnail_url = item.get('thumbnail_url') or item.get('media_url')
        else:
            thumbnail_url = item.get('media_url')

        caption = (item.get('caption') or '').strip()
        first_line = caption.splitlines()[0] if caption else ''
        title = (first_line[:77] + '…') if len(first_line) > 80 else first_line
        title = title or 'Instagram post'

        normalized.append({
            'title': title,
            'url': item.get('permalink', '#'),
            'thumbnail_url': thumbnail_url,
            'platform_label': 'Instagram',
        })
    return normalized


def get_recent_clips(settings_obj):
    """Return (items, source) for the Clips section.

    items is a list of normalized dicts (see normalize_media). source is
    'instagram' or None — None means "use the manual Clips fallback",
    which the caller (comedy.views.index) handles.
    """
    if not settings_obj.sync_enabled or not settings_obj.is_configured:
        return [], None

    cached = cache.get(CACHE_KEY)
    if cached is not None:
        return cached, 'instagram'

    try:
        raw = fetch_recent_media(
            settings_obj.ig_user_id, settings_obj.access_token, settings_obj.max_posts,
        )
        items = normalize_media(raw)
    except Exception:
        logger.warning('Instagram sync failed; falling back to manual clips.', exc_info=True)
        return [], None

    cache.set(CACHE_KEY, items, timeout=CACHE_TIMEOUT_SECONDS)
    settings_obj.last_synced_at = timezone.now()
    settings_obj.save(update_fields=['last_synced_at'])
    return items, 'instagram'


def refresh_long_lived_token(access_token):
    """Exchange a long-lived token that's nearing expiry for a fresh one.

    Instagram requires the token to be at least 24h old (and not yet
    expired) for this to work. Returns (new_token, expires_in_seconds).
    """
    url = f'{GRAPH_API_BASE}/refresh_access_token'
    params = {'grant_type': 'ig_refresh_token', 'access_token': access_token}
    response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    payload = response.json()
    if response.status_code != 200 or 'access_token' not in payload:
        message = (payload.get('error') or {}).get('message', 'Unknown Instagram API error')
        raise InstagramAPIError(f'Token refresh failed ({response.status_code}): {message}')
    return payload['access_token'], payload.get('expires_in')
