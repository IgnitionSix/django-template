FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NODE_VERSION=22

WORKDIR /code

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl postgresql-client ca-certificates \
    && curl -fsSL "https://deb.nodesource.com/setup_${NODE_VERSION}.x" | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY baseapp/requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

COPY baseapp /code/baseapp
WORKDIR /code/baseapp

RUN if [ -f core/static_src/package-lock.json ]; then \
        cd core/static_src && npm ci && npm run build; \
    fi

RUN python manage.py collectstatic --noinput --settings=app.settings.base

CMD ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]
