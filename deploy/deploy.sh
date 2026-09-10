#!/usr/bin/env bash
# Run this on the droplet (as the django user, from inside the repo)
# whenever you've pushed changes and want them live:
#   ssh django@your-droplet-ip
#   cd steers-comedy-django && ./deploy/deploy.sh
set -o errexit

git pull
.venv/bin/pip install -r requirements.txt
set -a; source deploy/.env; set +a
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py migrate

echo "==> Restarting the app (needs sudo)"
sudo systemctl restart steers-comedy
