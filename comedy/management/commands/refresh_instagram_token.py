from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta

from comedy.instagram import InstagramAPIError, refresh_long_lived_token
from comedy.models import InstagramSettings


class Command(BaseCommand):
    help = (
        'Renew the saved Instagram access token before it expires (Instagram '
        'long-lived tokens last ~60 days). Run this on a schedule — a monthly '
        'cron job or your host\'s scheduled-task feature — well before then. '
        'The token must already be at least 24 hours old for Instagram to '
        'allow refreshing it.'
    )

    def handle(self, *args, **options):
        settings_obj = InstagramSettings.get_solo()

        if not settings_obj.access_token:
            raise CommandError('No Instagram access token saved yet — nothing to refresh.')

        try:
            new_token, expires_in = refresh_long_lived_token(settings_obj.access_token)
        except InstagramAPIError as exc:
            raise CommandError(str(exc)) from exc

        settings_obj.access_token = new_token
        if expires_in:
            settings_obj.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
        settings_obj.save()

        self.stdout.write(self.style.SUCCESS(
            f'Token refreshed. New expiry: {settings_obj.token_expires_at:%Y-%m-%d}.'
        ))
