#!/bin/sh
set -e

until pg_isready -h "${POSTGRES_HOST:-db}" -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-defaultapp}"; do
  echo "Waiting for postgres..."
  sleep 2
done

python manage.py migrate --settings="${DJANGO_SETTINGS_MODULE:-app.settings.local}"
python manage.py runserver 0.0.0.0:8000 --settings="${DJANGO_SETTINGS_MODULE:-app.settings.local}"
