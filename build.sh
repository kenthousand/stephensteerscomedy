#!/usr/bin/env bash
# Render runs this on every deploy (see render.yaml).
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createcachetable  # no-op if it already exists
