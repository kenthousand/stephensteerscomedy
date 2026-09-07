# Steers Comedy — one-page site

A small Django project for a one-page comedian site: hero (with a photo
or video background), about, tour dates, clips, socials, an email
sign-up, and a "request a show" booking form. Everything editable
from the built-in Django admin — no code changes needed to update
tour dates, swap the hero photo, or review show requests.

Built to match the "Marquee" brand direction (Anton + Poppins,
midnight / rust / sky / tan / pearl).

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createcachetable
python manage.py createsuperuser
python manage.py runserver
```

Then visit:

- `http://127.0.0.1:8000/` — the site
- `http://127.0.0.1:8000/admin/` — the admin, log in with the
  superuser you just created

## Editing content

Everything on the page comes from the database, editable in the admin
under **Site content**:

- **Home page content** — the one row that holds the hero headline,
  tagline, description, hero photo/video, the about section text and
  photo, and the footer note. There's only ever one row; the admin
  always opens it directly.
  - Set a **hero video** to use video in the hero background instead
    of a photo — it takes priority over the hero photo when both are
    set. Keep it short and silent (the template autoplays it muted
    and looped); an MP4 under ~15MB loads fastest.
- **Tour dates** — add/edit/remove rows; only ones marked "published"
  show on the site, ordered by date automatically.
- **Clips** — title, platform, link, optional thumbnail image, and an
  order number (lower shows first). These only show up on the site as a
  *fallback* — see "Instagram sync" below, which takes over the Clips
  section automatically once it's configured.
- **Social links** — platform + URL, shown as icons in the Follow
  Along section.
- **Show requests** — every "request a show" submission lands here.
  Mark ones you've handled as reviewed.
- **Email subscribers** — every sign-up. Select rows and use
  **Export selected as CSV** from the Actions dropdown to pull a list
  for your email tool of choice.

## Instagram sync

The "Recent sets & recordings" section pulls your most recent Instagram
posts automatically once you've connected an account — no code changes,
just an admin field or two. As of 2026, Meta requires a **Business or
Creator** Instagram account for any API access; personal accounts aren't
supported ([source](https://www.keyapi.ai/blog/instagram-basic-display-api/)).
If your account is still personal, switch it in the Instagram app first
(Settings → Account type).

**One-time setup:**

1. Create a Meta developer app at
   [developers.facebook.com](https://developers.facebook.com/) and add the
   **Instagram API** product to it, using **Business Login for Instagram**
   (this is the current replacement for the old Basic Display API — see
   the [Instagram Platform docs](https://developers.facebook.com/docs/instagram-platform/overview/)).
   No Facebook Page is required for this login type.
2. Since this only ever needs to read *your own* account, **Standard
   Access** is enough — you don't need to submit the app for Meta's App
   Review or Business Verification.
3. Follow Meta's flow to authorize your own Instagram account against the
   app and generate a **long-lived access token** (valid ~60 days), and
   note your Instagram **user ID**.
4. In the site's admin, go to **Site content → Instagram settings** and
   paste in the user ID and access token. Saving it sets an assumed
   60-day expiry automatically.

That's it — the Clips section will start showing your real posts within
an hour (it re-checks Instagram at most once an hour, not on every page
load, to stay fast and avoid rate limits). To force an immediate refresh
instead of waiting:

```bash
python manage.py sync_instagram
```

**Keeping the token alive.** The token expires roughly every 60 days.
Run this periodically — a monthly cron job, or your host's scheduled-task
feature (Render/Railway both have one) — well before it expires:

```bash
python manage.py refresh_instagram_token
```

If the token does expire before you renew it, the site doesn't break —
it just quietly falls back to the manually-added Clips until you paste in
a fresh token.

Turn sync off at any time from the same admin page without losing the
saved token — the site falls back to the manual Clips immediately.

## Notes on the forms

Both forms save straight to the database (`ShowRequest` and
`EmailSubscriber` — see `comedy/models.py`) and show up in the admin;
they don't send email or push to a mailing-list service on their own.
If you want a real email notification when a show request comes in,
or want sign-ups to land in Mailchimp/ConvertKit/etc. instead of just
the database, that's a small addition to `comedy/views.py` — happy to
wire it up once you've picked a service.

## Before deploying anywhere public

This is set up for local development (`DEBUG=True`, a SQLite database,
`ALLOWED_HOSTS=['*']`). Before it goes on the public internet:

1. Set a real `DJANGO_SECRET_KEY` environment variable (don't use the
   auto-generated dev fallback in `settings.py`).
2. Set `DJANGO_DEBUG=False` and `DJANGO_ALLOWED_HOSTS` to your real
   domain(s).
3. Run `python manage.py collectstatic` and serve the `staticfiles/`
   folder (and `media/` for uploads) through your web server or a
   host like Render/Railway/Fly/PythonAnywhere.
4. Consider Postgres instead of SQLite if you expect real traffic —
   swap the `DATABASES` block in `steers_comedy/settings.py`.

## Project layout

```
steers_comedy/               Django project settings, urls
comedy/                       The one app: models, admin, forms, views, templates, CSS
comedy/instagram.py           Fetch + cache recent Instagram posts, token refresh
comedy/management/commands/   sync_instagram, refresh_instagram_token
comedy/templates/             base.html + index.html (the whole one-page site)
comedy/static/                style.css — all the brand styling lives here
media/                         Uploaded images/video land here (git-ignored)
```
