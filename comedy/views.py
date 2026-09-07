from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from .forms import EmailSignupForm, ShowRequestForm
from .instagram import get_recent_clips
from .models import Clip, HomePage, InstagramSettings, SocialLink, TourDate


def _clips_for_display():
    """Instagram posts when sync is on and working; manual Clips otherwise."""
    ig_settings = InstagramSettings.get_solo()
    items, source = get_recent_clips(ig_settings)
    if source == 'instagram' and items:
        return items, 'instagram'

    manual = Clip.objects.filter(is_published=True)
    manual_items = [
        {
            'title': clip.title,
            'url': clip.url,
            'thumbnail_url': clip.thumbnail.url if clip.thumbnail else None,
            'platform_label': clip.get_platform_display(),
        }
        for clip in manual
    ]
    return manual_items, 'manual'


def index(request):
    home = HomePage.get_solo()
    tour_dates = TourDate.objects.filter(is_published=True)
    clips, clips_source = _clips_for_display()
    socials = SocialLink.objects.all()

    show_request_form = ShowRequestForm()
    email_form = EmailSignupForm()

    if request.method == 'POST':
        which = request.POST.get('form_name')

        if which == 'show_request':
            show_request_form = ShowRequestForm(request.POST)
            if show_request_form.is_valid():
                show_request_form.save()
                messages.success(
                    request,
                    "Thanks — that's in. Expect a reply within a few days.",
                )
                return redirect(reverse('comedy:index') + '#booking')

        elif which == 'email_signup':
            email_form = EmailSignupForm(request.POST)
            if email_form.is_valid():
                email_form.save()
                messages.success(request, "You're on the list.")
                return redirect(reverse('comedy:index') + '#signup')

    context = {
        'home': home,
        'tour_dates': tour_dates,
        'clips': clips,
        'clips_source': clips_source,
        'socials': socials,
        'show_request_form': show_request_form,
        'email_form': email_form,
    }
    return render(request, 'comedy/index.html', context)
