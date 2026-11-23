#!/bin/sh
set -eu

export ACQUISITION_DATA_DIR="${ACQUISITION_DATA_DIR:-/data}"
mkdir -p "$ACQUISITION_DATA_DIR"

# Restore the latest durable snapshot before Django migrations or Gunicorn touch SQLite.
python -m webapp.core.state_backup restore
python web_manage.py migrate --noinput
python web_manage.py collectstatic --noinput

exec gunicorn webapp.wsgi:application \
  --bind 0.0.0.0:8080 \
  --workers 1 \
  --threads 1 \
  --timeout 300 \
  --access-logfile - \
  --error-logfile -
