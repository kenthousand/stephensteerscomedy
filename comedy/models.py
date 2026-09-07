from django.db import models


class SingletonModel(models.Model):
    """A model that only ever has one row (pk=1).

    Used for the page content that isn't a list of things (hero copy,
    about section, footer) — editable from one page in the admin instead
    of a list of near-duplicate rows.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # singleton rows aren't deletable from the admin

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HomePage(SingletonModel):
    """The editable copy and media for the one-page site.

    There is only ever one row of this — edit it from Site content ›
    Home page content in the admin.
    """

    # Hero
    hero_headline = models.CharField(max_length=40, default='STEERS')
    hero_tag = models.CharField(max_length=40, default='COMEDY')
    hero_subline = models.CharField(max_length=80, default='LIVE. LOUD. SOLD OUT.')
    hero_description = models.TextField(
        default='Stand-up from Mexico City and wherever the next flight goes.'
    )
    hero_image = models.ImageField(
        upload_to='hero/', blank=True, null=True,
        help_text='Background photo for the hero section. Ignored if a hero video is set.',
    )
    hero_video = models.FileField(
        upload_to='hero/', blank=True, null=True,
        help_text='Optional background video (MP4, ideally under ~15MB, no audio). '
                   'Takes priority over the hero photo when set.',
    )

    # About
    about_heading = models.CharField(max_length=80, default='Same guy. Louder room.')
    about_body = models.TextField(
        default='Steers has spent a few too many years turning very normal life '
                'experience into stand-up that is, according to at least one heckler, '
                'unreasonably funny. Based in Mexico City, performing everywhere that '
                'will have him.'
    )
    about_photo = models.ImageField(upload_to='about/', blank=True, null=True)
    about_quote = models.CharField(
        max_length=160, blank=True,
        default='"Actually pretty good." — a friend, probably',
    )

    # Site-wide
    site_tagline = models.CharField(max_length=80, default='Stand-up comedy from Steers.')
    footer_note = models.CharField(
        max_length=120, blank=True, default='Steers Comedy',
        help_text='Shown in the footer next to the copyright year.',
    )

    class Meta:
        verbose_name = 'Home page content'
        verbose_name_plural = 'Home page content'

    def __str__(self):
        return 'Home page content'


class TourDate(models.Model):
    date = models.DateField()
    venue = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    ticket_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'{self.date} — {self.venue}, {self.city}'


class Clip(models.Model):
    PLATFORM_CHOICES = [
        ('youtube', 'YouTube'),
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=140)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='youtube')
    url = models.URLField()
    thumbnail = models.ImageField(upload_to='clips/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first.')
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return self.title


class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('tiktok', 'TikTok'),
        ('youtube', 'YouTube'),
        ('x', 'X'),
        ('other', 'Other'),
    ]

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    url = models.URLField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'platform']

    def __str__(self):
        return f'{self.get_platform_display()} — {self.url}'


class ShowRequest(models.Model):
    """A booking / 'request a show' submission from the site."""

    name = models.CharField(max_length=120)
    email = models.EmailField()
    venue_city = models.CharField('Venue / city', max_length=160)
    preferred_dates = models.CharField(max_length=160, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_reviewed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Show request'

    def __str__(self):
        return f'{self.name} — {self.venue_city}'


class InstagramSettings(SingletonModel):
    """Credentials + options for pulling recent posts into the Clips section.

    Get these values by following the "Instagram sync" section of the
    README. There's only ever one row — edit it from Site content ›
    Instagram settings in the admin.
    """

    ig_user_id = models.CharField(
        'Instagram user ID', max_length=60, blank=True,
        help_text='The numeric Instagram user ID for the professional '
                   '(Business or Creator) account to pull posts from.',
    )
    access_token = models.TextField(
        blank=True,
        help_text='A long-lived Instagram access token for that account. '
                   'Expires roughly every 60 days — see the README for how '
                   'to renew it.',
    )
    token_expires_at = models.DateTimeField(
        blank=True, null=True,
        help_text='Set automatically (assumes 60 days) when you paste in a new token, '
                   'or precisely by the refresh_instagram_token command.',
    )
    last_synced_at = models.DateTimeField(blank=True, null=True, editable=False)
    sync_enabled = models.BooleanField(
        default=True,
        help_text='Turn off to stop pulling from Instagram and fall back to '
                   'the manually-added Clips below, without losing the saved token.',
    )
    max_posts = models.PositiveIntegerField(
        default=6, help_text='How many recent posts to show in the Clips section.',
    )

    class Meta:
        verbose_name = 'Instagram settings'
        verbose_name_plural = 'Instagram settings'

    def __str__(self):
        return 'Instagram settings'

    @property
    def is_configured(self):
        return bool(self.ig_user_id and self.access_token)


class EmailSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email
