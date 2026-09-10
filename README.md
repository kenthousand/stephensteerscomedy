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
Run this periodically, well before it expires:

```bash
python manage.py refresh_instagram_token
```

On the droplet, a monthly cron job is the simplest way — as the `django`
user (`crontab -e`), add a line like:

```
0 3 1 * * cd /home/django/steers-comedy-django && set -a && . deploy/.env && set +a && .venv/bin/python manage.py refresh_instagram_token >> /home/django/refresh_instagram.log 2>&1
```

(runs at 3am on the 1st of each month; check `refresh_instagram.log` if
posts stop updating).

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

## Deploying to a DigitalOcean droplet + Cloudflare

This is the low-cost path: a single $6/month Basic Droplet running
Django directly (gunicorn behind nginx, managed by systemd) with
SQLite — no separate database service to pay for, and uploads persist
on the droplet's own disk instead of vanishing on redeploy the way they
would on a platform-as-a-service host. Cloudflare sits in front for
DNS, the free SSL certificate visitors see, and caching. Everything
host-specific lives under `deploy/`.

**1. Create the droplet.** In the DigitalOcean control panel, **Create
> Droplets**: Ubuntu 24.04 LTS, the $6/mo Basic plan (1 GB RAM — the
$4/mo 512 MB plan can be tight when installing Pillow and running
migrations together), whichever region is closest to your visitors,
and your SSH key. Note the droplet's IP address once it's up.

**2. Clone the repo onto it.** SSH in as root, create the app user, and
clone as that user (using the same GitHub auth — token or SSH key —
you set up on your Mac):

```bash
ssh root@YOUR_DROPLET_IP
adduser --system --group --home /home/django --shell /bin/bash django
su - django
git clone https://github.com/kenthousand/stephensteerscomedy.git steers-comedy-django
cd steers-comedy-django
```

**3. Set your real environment values.** Still as the `django` user:

```bash
cp deploy/.env.example deploy/.env
nano deploy/.env
```

Generate a real secret key to paste in for `DJANGO_SECRET_KEY`:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```
Set `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to your
real domain (both are already filled in with `stephensteerscomedy.com`
as an example — just confirm they match).

**4. Get a Cloudflare Origin Certificate.** In the Cloudflare dashboard
for your domain: **SSL/TLS > Origin Server > Create Certificate**
(defaults are fine — it'll cover your domain and `*.yourdomain.com`).
Cloudflare shows you two blocks of text, the certificate and the
private key. Back on the droplet, as root:

```bash
exit   # back to root, if you're still in as django
mkdir -p /etc/ssl/cloudflare
nano /etc/ssl/cloudflare/origin.pem   # paste the certificate block, save
nano /etc/ssl/cloudflare/origin.key   # paste the private key block, save
chmod 600 /etc/ssl/cloudflare/origin.key
```

**5. Run the setup script.** Still as root:

```bash
cd /home/django/steers-comedy-django
bash deploy/setup.sh
```

This installs nginx/Python, creates the virtualenv, installs
dependencies, runs `collectstatic`/`migrate`/`createcachetable`, and
sets up + starts the gunicorn systemd service, the nginx site, and the
firewall (only SSH, HTTP, and HTTPS are left open). It's safe to re-run
if something fails partway through.

**6. Create your admin login** (the command it prints at the end):

```bash
sudo -u django bash -c 'set -a; source /home/django/steers-comedy-django/deploy/.env; set +a; /home/django/steers-comedy-django/.venv/bin/python /home/django/steers-comedy-django/manage.py createsuperuser'
```

**7. Point Cloudflare at the droplet.** In Cloudflare's DNS settings for
your domain, add an `A` record for both the bare domain and `www`
pointing at the droplet's IP address, proxy status **Proxied**
(orange cloud). Then in **SSL/TLS**, set the mode to **Full (strict)**
— this tells Cloudflare to trust the Origin Certificate you installed
in step 4 rather than talking plain HTTP to the droplet.

DNS changes can take anywhere from a few minutes to a few hours to
propagate. Once they do, your domain should load the site over HTTPS.

**Future updates:** push to GitHub as usual, then on the droplet (as
the `django` user, from inside the repo):
```bash
./deploy/deploy.sh
```
which pulls the latest code, reinstalls any new dependencies, reruns
`collectstatic`/`migrate`, and restarts the app.

**Ongoing maintenance you're now responsible for** (this is the
trade-off for the lower cost vs. a managed platform): keep the server
patched with `apt update && apt upgrade` occasionally, and it's worth
setting DigitalOcean's automatic droplet backups on later if the site
grows to matter more.

## Project layout

```
steers_comedy/               Django project settings, urls
comedy/                       The one app: models, admin, forms, views, templates, CSS
comedy/instagram.py           Fetch + cache recent Instagram posts, token refresh
comedy/management/commands/   sync_instagram, refresh_instagram_token
comedy/templates/             base.html + index.html (the whole one-page site)
comedy/static/                style.css — all the brand styling lives here
media/                         Uploaded images/video land here (git-ignored)
deploy/                         Droplet deploy files: nginx config, systemd service,
                                 setup.sh (one-time), deploy.sh (updates), .env.example
```
