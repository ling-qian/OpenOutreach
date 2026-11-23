#!/bin/sh
set -eu

: "${DJANGO_SECRET_KEY:?DJANGO_SECRET_KEY Worker secret must be configured}"
export DJANGO_SETTINGS_MODULE=webapp.settings
export ACQUISITION_DATA_DIR="${ACQUISITION_DATA_DIR:-/data}"
mkdir -p "$ACQUISITION_DATA_DIR"

# Restore before Django or OpenOutFind opens either SQLite database.
python -m webapp.core.state_backup restore
python web_manage.py migrate --noinput
python -m webapp.core.bootstrap_admin
python -m webapp.core.state_backup backup
python web_manage.py collectstatic --noinput

exec gunicorn webapp.wsgi:application \
  --bind 0.0.0.0:8080 \
  --workers 1 \
  --threads 1 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -
