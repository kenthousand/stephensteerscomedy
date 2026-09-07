from django.core.cache import cache
from django.core.management.base import BaseCommand

from comedy.instagram import CACHE_KEY, get_recent_clips
from comedy.models import InstagramSettings


class Command(BaseCommand):
    help = (
        'Force-refresh the cached Instagram posts shown in the Clips section, '
        'instead of waiting for the hourly cache to expire on its own.'
    )

    def handle(self, *args, **options):
        settings_obj = InstagramSettings.get_solo()

        if not settings_obj.sync_enabled:
            self.stdout.write(self.style.WARNING('Instagram sync is turned off in the admin.'))
            return
        if not settings_obj.is_configured:
            self.stdout.write(self.style.WARNING(
                'No Instagram user ID / access token saved yet — nothing to sync.'
            ))
            return

        cache.delete(CACHE_KEY)
        items, source = get_recent_clips(settings_obj)

        if source == 'instagram':
            self.stdout.write(self.style.SUCCESS(f'Synced {len(items)} post(s) from Instagram.'))
        else:
            self.stdout.write(self.style.ERROR(
                'Sync failed — check the server logs for details. '
                'The site will keep showing the manual Clips in the meantime.'
            ))
