#!/usr/bin/env bash
# One-time droplet setup. Run as root, from inside the cloned repo, after
# you've already cloned it to /home/django/steers-comedy-django and put
# your real values in deploy/.env (see deploy/.env.example) and your
# Cloudflare Origin Certificate at /etc/ssl/cloudflare/{origin.pem,origin.key}
# — the README's "Setting up the droplet" section walks through all of
# this in order. Safe to re-run if a step fails partway through.
set -o errexit

APP_DIR=/home/django/steers-comedy-django

echo "==> Installing system packages"
apt-get update
apt-get install -y python3-venv python3-pip nginx git ufw

echo "==> Creating the django system user (if it doesn't exist yet)"
id -u django &>/dev/null || adduser --system --group --home /home/django --shell /bin/bash django

echo "==> Python virtualenv + dependencies"
sudo -u django python3 -m venv "$APP_DIR/.venv"
sudo -u django "$APP_DIR/.venv/bin/pip" install --upgrade pip
sudo -u django "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

echo "==> Django setup (static files, database, cache table)"
sudo -u django bash -c "set -a; source $APP_DIR/deploy/.env; set +a; \
  $APP_DIR/.venv/bin/python $APP_DIR/manage.py collectstatic --noinput && \
  $APP_DIR/.venv/bin/python $APP_DIR/manage.py migrate && \
  $APP_DIR/.venv/bin/python $APP_DIR/manage.py createcachetable"

echo "==> Installing the gunicorn systemd service"
cp "$APP_DIR/deploy/gunicorn.service" /etc/systemd/system/steers-comedy.service
systemctl daemon-reload
systemctl enable --now steers-comedy

echo "==> Installing the nginx site"
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/steers-comedy
ln -sf /etc/nginx/sites-available/steers-comedy /etc/nginx/sites-enabled/steers-comedy
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> Firewall (allow SSH, HTTP, HTTPS; deny everything else)"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "==> Letting the django user restart the app without a password"
echo "django ALL=(root) NOPASSWD: /usr/bin/systemctl restart steers-comedy" \
  > /etc/sudoers.d/django-steers-comedy
chmod 440 /etc/sudoers.d/django-steers-comedy

echo "==> Done. Create your admin login with:"
echo "    sudo -u django bash -c 'set -a; source $APP_DIR/deploy/.env; set +a; $APP_DIR/.venv/bin/python $APP_DIR/manage.py createsuperuser'"
