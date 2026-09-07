from django import forms

from .models import EmailSubscriber, ShowRequest


class ShowRequestForm(forms.ModelForm):
    class Meta:
        model = ShowRequest
        fields = ['name', 'email', 'venue_city', 'preferred_dates', 'details']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@email.com'}),
            'venue_city': forms.TextInput(attrs={'placeholder': 'Venue name, city'}),
            'preferred_dates': forms.TextInput(attrs={'placeholder': 'e.g. weekend of March 14, or flexible'}),
            'details': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Room size, event type, budget — whatever helps.'}),
        }


class EmailSignupForm(forms.ModelForm):
    class Meta:
        model = EmailSubscriber
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={'placeholder': 'you@email.com', 'aria-label': 'Email address'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        return email

    def save(self, commit=True):
        # Signing up twice with the same address should feel like success,
        # not an error — re-use the existing row instead of raising.
        email = self.cleaned_data['email']
        obj, _created = EmailSubscriber.objects.get_or_create(email=email)
        return obj
