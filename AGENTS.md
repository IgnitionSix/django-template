# AGENTS.md

## Project Overview

This repo is a Django template for server-rendered web apps. The default Django project is `appimage/baseapp/app`, and the only starter app is `appimage/baseapp/core`.

The template intentionally uses:

- Django.
- Tailwind.
- htmx.
- Alpine for client behavior that htmx should not own.
- Locally bundled Chart.js.
- Docker Compose for local development.
- django-allauth, django-csp, django-ratelimit, and django-simple-history.
- Terraform for an AWS ECS/RDS/Redis deployment.

Do not reintroduce DRF, django-compressor, Elasticsearch, or the old `api`/`home`/`theme` split unless the user explicitly asks for that architecture.

## Required Workflow

Use TDD for behavior changes:

1. Add or update a focused failing test.
2. Run the targeted test and confirm the expected failure.
3. Implement the smallest useful change.
4. Run the targeted test.
5. Run the full verification set before calling the work done.

## Core Commands

Local stack:

```bash
docker compose up --build
```

The Docker image default command is Gunicorn for production. Docker Compose overrides it with `run.sh` for local migrations and `runserver`.

Django tests:

```bash
cd appimage/baseapp
./.venv/bin/python manage.py test --settings=app.settings.test
```

Ruff:

```bash
cd appimage/baseapp
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
```

Frontend build:

```bash
cd appimage/baseapp/core/static_src
npm ci
npm run build
```

Production deploy check:

```bash
cd appimage/baseapp
DJANGO_SECRET_KEY='ci-secret-0123456789abcdefghijklmnopqrstuvwxyz-ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
DJANGO_ALLOWED_HOSTS='example.com' \
DJANGO_CSRF_TRUSTED_ORIGINS='https://example.com' \
POSTGRES_DB='defaultapp' \
POSTGRES_USER='postgres' \
POSTGRES_PASSWORD='postgres' \
POSTGRES_HOST='localhost' \
./.venv/bin/python manage.py check --deploy --fail-level WARNING --settings=app.settings.production
```

Terraform format and validation:

```bash
terraform fmt -check -recursive terraform/aws
cd terraform/aws/backend-bootstrap
terraform init -backend=false
terraform validate
cd ../
terraform init -backend=false
terraform validate
```

## Code Organization

- Keep starter views, URLs, templates, static assets, and tests in `core`.
- Keep the Django project package named `app`.
- Add new domain apps only for real product domains.
- Put shared model history behavior in `core.models.HistoryModel`.
- Keep settings split by intent: `base`, `local`, `test`, and `production`.
- Do not add inline scripts to templates when an external file can do the job. CSP should stay restrictive.

## Security Expectations

- Keep production secrets in environment variables or Secrets Manager.
- Keep `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` explicit in production.
- Preserve CSP middleware and default directives.
- Preserve rate-limit examples when changing starter views.
- Keep htmx, Alpine, and Chart.js bundled locally rather than loaded from CDNs.
- `SECURE_SSL_REDIRECT` defaults to true in production; only disable it for an intentional HTTP bootstrap path.
- The HTTP Terraform bootstrap path is for health checks and public pages only. Keep secure cookies enabled and require HTTPS before testing auth or forms.

## Terraform Rules

- Keep Terraform flat and teachable under `terraform/aws`.
- Prefer variables with sensible defaults over hardcoded project values.
- Track `.terraform.lock.hcl`.
- Do not track `.terraform/`, `terraform.tfvars`, `backend.hcl`, or state files.
- Run `terraform fmt -recursive terraform/aws` after edits.
- Use `terraform init -backend=false` for local validation when you do not intend to touch remote state.
- Keep the backend bootstrap stack separate from the main app stack.
