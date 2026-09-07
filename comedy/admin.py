import csv
from datetime import timedelta

from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone

from .models import (
    Clip, EmailSubscriber, HomePage, InstagramSettings, ShowRequest, SocialLink, TourDate,
)


class SingletonAdmin(admin.ModelAdmin):
    """Base admin for a SingletonModel: always edits the one row, no list, no add, no delete."""

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = self.model.get_solo()
        return redirect(f'admin:comedy_{self.model._meta.model_name}_change', obj.pk)


@admin.register(HomePage)
class HomePageAdmin(SingletonAdmin):
    fieldsets = (
        ('Hero', {
            'fields': ('hero_headline', 'hero_tag', 'hero_subline', 'hero_description',
                       'hero_image', 'hero_video'),
        }),
        ('About', {
            'fields': ('about_heading', 'about_body', 'about_photo', 'about_quote'),
        }),
        ('Site-wide', {
            'fields': ('site_tagline', 'footer_note'),
        }),
    )


@admin.register(InstagramSettings)
class InstagramSettingsAdmin(SingletonAdmin):
    fieldsets = (
        (None, {
            'fields': ('sync_enabled', 'ig_user_id', 'access_token', 'max_posts'),
            'description': 'See the "Instagram sync" section of the README for how to get '
                            'the user ID and access token. When sync is off, or these are '
                            'blank, or a fetch fails, the Clips section falls back to the '
                            'manually-added clips below.',
        }),
        ('Status (read-only)', {
            'fields': ('token_expires_at', 'last_synced_at'),
        }),
    )
    readonly_fields = ('token_expires_at', 'last_synced_at')

    def save_model(self, request, obj, form, change):
        # Pasting in a new token by hand — assume a fresh 60-day expiry.
        # A refresh via `manage.py refresh_instagram_token` sets the exact
        # value itself and doesn't go through this admin form.
        if 'access_token' in form.changed_data:
            obj.token_expires_at = timezone.now() + timedelta(days=60) if obj.access_token else None
        super().save_model(request, obj, form, change)


@admin.register(TourDate)
class TourDateAdmin(admin.ModelAdmin):
    list_display = ('date', 'venue', 'city', 'is_published')
    list_editable = ('is_published',)
    list_filter = ('is_published',)
    ordering = ('date',)


@admin.register(Clip)
class ClipAdmin(admin.ModelAdmin):
    list_display = ('title', 'platform', 'order', 'is_published')
    list_editable = ('order', 'is_published')
    list_filter = ('platform', 'is_published')


@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ('platform', 'url', 'order')
    list_editable = ('order',)


@admin.register(ShowRequest)
class ShowRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'venue_city', 'email', 'created_at', 'is_reviewed')
    list_editable = ('is_reviewed',)
    list_filter = ('is_reviewed',)
    readonly_fields = ('created_at',)
    search_fields = ('name', 'email', 'venue_city')


@admin.register(EmailSubscriber)
class EmailSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)
    actions = ['export_as_csv']

    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=email_subscribers.csv'
        writer = csv.writer(response)
        writer.writerow(['email', 'signed_up_at'])
        for sub in queryset:
            writer.writerow([sub.email, sub.created_at.isoformat()])
        return response

    export_as_csv.short_description = 'Export selected as CSV'
