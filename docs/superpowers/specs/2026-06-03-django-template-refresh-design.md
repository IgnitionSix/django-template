# Django Template Refresh Design

## Purpose

Refresh the Ignition 6 Django template so new projects start from a modern, production-minded baseline:

- Django-first, server-rendered application development.
- Tailwind and htmx as default frontend tools.
- Alpine available for client-side behavior that htmx should not own.
- Docker Compose for local development.
- A single default Django app named `core` instead of scattered `api`, `home`, and `theme` apps.
- A reusable `HistoryModel` base class backed by django-simple-history.
- Ready-to-apply AWS Terraform for the common production shape.
- Clear TDD expectations for human and agentic contributors.

## Current State

The existing template is compact but dated. The default application behavior is spread across `api`, `home`, and `theme`, while settings and URL routing live under `app`. Dependencies include Django 4.2.4, DRF, drf-spectacular, django-filter, django-compressor, Elasticsearch, and a large vendored htmx file. The README still describes the template as a DRF and Elasticsearch starter, even though the desired default is now a Django server-rendered app with htmx/Alpine.

The test story is unclear and currently includes duplicate broken tests that use `assertEqueal`. Local Docker uses a floating `python:3` image, an older Node runtime, and a `sleep 10` startup wait.

## Goals

- Consolidate default project behavior into one reusable app named `core`.
- Upgrade runtime, Python, Django, frontend, and test tooling to current supported defaults.
- Remove unused API and asset-compression dependencies.
- Include allauth, CSP, rate limiting, htmx, Alpine, Tailwind, and Chart.js by default.
- Include django-simple-history and a reusable `HistoryModel` base class for UUID primary keys, timestamps, admin change links, sticky fields, choice validation, and no-op save suppression.
- Provide a secure production settings posture that remains practical for local development.
- Provide ready-to-apply Terraform for AWS infrastructure with customizable variables and sensible defaults.
- Make README and `AGENTS.md` strong enough for a developer or coding agent to bootstrap, test, extend, and deploy the template without tribal knowledge.

## Non-Goals

- Do not turn the template into a SPA or a DRF-first API starter.
- Do not add a custom user model unless a generated project needs one.
- Do not build social-login provider configuration beyond allauth's base local account flow.
- Do not create a multi-environment Terraform module system unless the single ready-to-apply stack becomes unwieldy.
- Do not make Terraform hide AWS fundamentals; the README should teach the bootstrap path clearly.

## Recommended Architecture

Use a full template refresh rather than incremental cleanup.

`app` remains the Django project package. `core` becomes the only default local Django app. It owns:

- Default views and htmx fragments.
- URL routes for the starter app.
- Templates, including the base template.
- Static source assets and built static files.
- Default tests.
- Any small helpers needed by the starter app.

Generated projects can add domain apps later, but the template should not begin with artificial technical-layer apps.

## Django Layout

Target structure:

```text
appimage/baseapp/
  manage.py
  requirements.txt
  app/
    settings/
      base.py
      local.py
      production.py
      test.py
    urls.py
    asgi.py
    wsgi.py
  core/
    apps.py
    urls.py
    views.py
    templates/
      core/
        index.html
        _htmx_ping.html
      _base.html
      account/
        login.html
        signup.html
    static/
      js/
        app.js
      css/
        dist/
    static_src/
      package.json
      package-lock.json
      postcss.config.js
      tailwind.config.js
      src/styles.css
    models/
      __init__.py
      history.py
    tests/
      test_history_model.py
      test_views.py
      test_settings.py
      test_security.py
```

Implementation should delete the old `api`, `home`, and `theme` apps after their useful behavior is moved into `core`.

## Dependency Direction

Use current, stable, primary-source-verified versions at implementation time. As of this design pass, the intended baselines are:

- Django 5.2.x LTS.
- Python 3.13 unless a dependency incompatibility forces Python 3.12.
- psycopg 3 instead of psycopg2-binary.
- django-tailwind 4.4.x or newer compatible release.
- django-allauth current 65.x release.
- django-csp 4.x.
- django-ratelimit 4.1.x.
- django-simple-history 3.11.x.
- htmx.org 2.x bundled from npm into static assets.
- alpinejs 3.x bundled from npm into static assets.
- chart.js 4.5.x bundled from npm into static assets.

Remove:

- djangorestframework.
- drf-spectacular.
- django-filter.
- django-compressor.
- elasticsearch and related transport packages.
- cookiecutter-only packages that are not used at runtime.
- rcssmin and rjsmin if nothing else needs them.
- the DRF plain-text renderer.

## Settings And Security

Split settings by intent:

- `base.py`: shared installed apps, middleware, templates, static files, auth, cache, CSP, logging, and security defaults.
- `local.py`: local Docker/Postgres values, debug enabled, browser reload enabled, relaxed hosts, console email backend.
- `test.py`: SQLite or isolated test database, fast password hasher, locmem email/cache, deterministic settings.
- `production.py`: strict environment-driven settings for ECS, RDS, Redis, HTTPS, cookies, allowed hosts, CSRF origins, and logging.

Security defaults:

- Include `csp.middleware.CSPMiddleware` early enough to attach CSP headers.
- Keep CSP restrictive by default: `self` for scripts/styles/images/connect, with no third-party script host required by the default template.
- Prefer external JS files over inline scripts where practical.
- Enable `SECURE_SSL_REDIRECT`, secure cookies, `SECURE_PROXY_SSL_HEADER`, HSTS, `X_FRAME_OPTIONS`, and strict referrer policy in production.
- Configure cache through Redis when `REDIS_URL` is present.
- Use `django-ratelimit` on starter POST-like or htmx demo endpoints so the pattern is visible.
- Use allauth with local username/email account flow and basic templates.
- Include `simple_history.middleware.HistoryRequestMiddleware` so historical records can attach request user context when available.

## Base Model And History

The template should include django-simple-history and a reusable abstract base model at `core/models/history.py`.

The base class should be named `HistoryModel` and should provide:

- `id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`.
- `created_at` and `modified_at` timestamp fields.
- `history = HistoricalRecords(inherit=True)`.
- `is_new` property using Django model state.
- `short_id` property returning the first UUID segment.
- Choice-field validation during `save`.
- `_sticky_fields` support so subclasses can make selected fields immutable after creation.
- No-op save suppression so unchanged existing objects do not create unnecessary history rows.
- Special handling for `last_found`: when it is the only changed field, update it directly without creating a new history row.
- `get_change_url()` returning the Django admin change URL for the object.

The implementation should preserve the provided behavior while tightening template quality:

- Use imports local to the new file: `datetime as dt`, `uuid`, Django `models`, `timezone`, `reverse`, `django.core.exceptions.ValidationError` or an explicit local choice validator, and `simple_history.models.HistoricalRecords`.
- Avoid swallowing `DoesNotExist`; if an existing object cannot be reloaded, let Django surface the error.
- Compare timezone-aware datetimes consistently before deciding whether a save is a no-op.
- Add tests with a small concrete model that inherits from `HistoryModel`, including unchanged save, changed save, sticky field, choice validation, `last_found`, `short_id`, and admin URL behavior.

## Frontend Assets

Keep Tailwind as the styling default. The build should be explicit and reproducible:

- Node version should be pinned in the Docker image.
- `package-lock.json` should be committed.
- `npm ci` should be used in container builds when a lockfile exists.
- htmx and Alpine should be installed through npm and bundled into static assets, not left as stale vendored code with unknown provenance.
- Chart.js should be installed through npm and bundled into static assets. The supplied cdnjs URL is only a convenient source reference, not a runtime CDN dependency.

The base template should load:

- Tailwind output CSS.
- htmx.
- Alpine.
- Chart.js.
- A small `core/static/js/app.js` file that configures CSRF headers for htmx without inline script when feasible.

## Testing Strategy

The template should document and model TDD.

Default tests should cover:

- `GET /` renders the starter page.
- htmx demo endpoint returns the expected fragment.
- allauth account URLs are mounted.
- CSP headers are present.
- rate-limited view uses the configured rate limit.
- `HistoryModel` suppresses unchanged saves and creates history for meaningful changes.
- `HistoryModel` validates choices, preserves sticky fields, exposes `short_id`, and returns admin change URLs.
- production settings fail clearly when required environment variables are missing.
- local/test settings can boot without AWS-specific variables.

The preferred local commands should be:

```bash
cd appimage/baseapp
python manage.py test --settings=app.settings.test
python manage.py check --deploy --settings=app.settings.production
```

The GitHub Actions workflow should install dependencies, run Ruff lint/format checks, run Django tests, and run `manage.py check`.

## Docker Compose

Keep Docker Compose for local development, but modernize it:

- Use a pinned Python image such as `python:3.13-slim`.
- Use a pinned Postgres image.
- Add a Redis service to match the production cache dependency.
- Replace `sleep 10` with a small database readiness check.
- Keep separate `app` and `tailwind` services for local DX.
- Mount source code for live reload.
- Avoid floating image tags.

## Terraform AWS Stack

Add ready-to-apply Terraform under:

```text
terraform/aws/
  README.md
  backend-bootstrap/
  main.tf
  variables.tf
  outputs.tf
  providers.tf
  versions.tf
  vpc.tf
  rds.tf
  redis.tf
  ecs.tf
  alb.tf
  iam.tf
  security-groups.tf
  secrets.tf
  terraform.tfvars.example
```

The stack should create:

- VPC with public and private subnets across at least two availability zones.
- Internet gateway and NAT support, with variables controlling NAT cost posture.
- Security groups for ALB, ECS tasks, RDS, and Redis.
- RDS PostgreSQL instance with generated or supplied password.
- ElastiCache Redis, tiny by default, for Django cache/rate-limit backing.
- ECS Fargate cluster, task definition, and service for the Django app.
- Application Load Balancer and target group.
- CloudWatch log group.
- IAM task execution and task roles.
- Secrets Manager entries or SSM parameters for Django secrets and database/cache URLs.
- Outputs for ALB DNS, RDS endpoint, Redis endpoint, ECS cluster/service names, and secret ARNs.

Variables should include sensible defaults for:

- AWS region.
- Project name.
- Environment name.
- VPC CIDR and subnet CIDRs.
- Container image.
- Container port.
- Desired task count.
- CPU and memory.
- RDS instance class and storage.
- Redis node type.
- Allowed CIDRs for public ingress.
- Domain/certificate settings, optional by default.
- Deletion protection toggles.

The Terraform must be usable from a fresh AWS account after the documented bootstrap steps.

## Terraform Documentation

The root README and `terraform/aws/README.md` should walk a developer from zero to a cloud environment:

1. Install AWS CLI and Terraform.
2. Configure AWS credentials.
3. Choose a project/environment name.
4. Bootstrap remote state using `terraform/aws/backend-bootstrap`.
5. Copy and edit `terraform.tfvars.example`.
6. Run `terraform init`.
7. Run `terraform plan`.
8. Run `terraform apply`.
9. Build and push the Docker image.
10. Update the ECS service to use the image.
11. Run migrations in ECS.
12. Confirm the ALB URL serves the Django app.
13. Tear down safely when needed.

The docs should explain what Terraform creates, what it costs roughly, what values are safe to change, and which outputs map back to Django environment variables.

## README And AGENTS.md

The README should be rewritten around the current desired template:

- What the template includes.
- Local prerequisites.
- First local boot.
- Running migrations.
- Running tests.
- TDD workflow.
- Tailwind workflow.
- htmx/Alpine/Chart.js bundled asset defaults.
- allauth defaults.
- django-simple-history and `HistoryModel` defaults.
- Security defaults.
- Terraform bootstrap and deployment.
- How to create a new domain app after project generation.
- Dependency update guidance.

Add `AGENTS.md` at the repo root with:

- Project overview.
- Required TDD workflow.
- Exact commands for tests, checks, local Docker, and Tailwind.
- Code organization rules.
- Settings/environment guidance.
- Security expectations.
- Terraform editing rules.
- A warning not to reintroduce DRF/compressor/API split unless explicitly requested.

## Migration Plan

Because this is a template, prefer clean replacement over backwards-compatible shims:

1. Add focused tests that describe the desired starter behavior.
2. Create `core` and move default behavior into it.
3. Update settings and URLs to use `core`.
4. Remove obsolete apps and dependencies.
5. Modernize frontend assets and Docker.
6. Add allauth, CSP, rate limit behavior, django-simple-history, and `HistoryModel`.
7. Add Terraform.
8. Rewrite README and add `AGENTS.md`.
9. Run Django tests, Django checks, frontend build, Docker Compose boot, and Terraform validation.

## Acceptance Criteria

- `api`, `home`, and `theme` are gone from installed apps and default routing.
- `core` owns the starter page, htmx endpoint, templates, static assets, and tests.
- DRF, drf-spectacular, django-filter, django-compressor, and Elasticsearch packages are removed.
- Django, django-tailwind, htmx, Alpine, Tailwind, Chart.js, and Docker runtime versions are current and pinned.
- Chart.js 4.5.x is bundled into static assets from npm.
- allauth account URLs and starter templates work.
- CSP headers are present and compatible with the default page.
- rate limiting is installed and demonstrated.
- django-simple-history is installed and the reusable `HistoryModel` base class is tested.
- `python manage.py test --settings=app.settings.test` passes.
- `python manage.py check --deploy --settings=app.settings.production` is documented and either passes with sample env vars or fails with clear missing-variable messages.
- Docker Compose can start the local app, Postgres, Redis, and Tailwind watcher.
- Terraform validates and plans with `terraform.tfvars.example` values adapted to a caller's AWS account.
- README explains local development, TDD, and Terraform bootstrap from scratch.
- `AGENTS.md` gives agents enough context to work safely in the template.

## Open Implementation Notes

- Prefer Django 5.2 LTS over Django 6.0 for template stability unless implementation-time verification shows a strong reason to move.
- Prefer Python 3.13 for the Docker image if all chosen packages support it.
- Bundle htmx, Alpine, and Chart.js from npm into static files for CSP and offline development.
- Keep Terraform flat enough to be teachable. Use modules only if repetition becomes distracting.

## Reference Checks

- Django 5.2 release notes: https://docs.djangoproject.com/en/5.2/releases/
- django-csp: https://pypi.org/project/django-csp/
- django-allauth: https://pypi.org/project/django-allauth/
- django-simple-history: https://pypi.org/project/django-simple-history/
- django-tailwind: https://pypi.org/project/django-tailwind/
- htmx.org: https://www.npmjs.com/package/htmx.org
- Alpine.js: https://www.npmjs.com/package/alpinejs
- Chart.js 4.5.0 npm package: https://www.npmjs.com/package/chart.js/v/4.5.0
