# django-template

An opinionated Ignition 6 starter for server-rendered Django applications.

It includes Django 5.2, Tailwind, htmx, Alpine, Chart.js, django-allauth, django-background-tasks, django-csp, django-ratelimit, django-simple-history, Docker Compose for local development, and AWS Terraform for the common production shape.

The template starts with one local Django app, `core`. Add domain apps as the project grows, but do not start by splitting behavior across artificial `api`, `home`, and `theme` apps.

## What Is Included

- Django project package in `appimage/baseapp/app`.
- Single starter app in `appimage/baseapp/core`.
- Settings split into `base`, `local`, `test`, and `production`.
- Tailwind source and npm lockfile in `appimage/baseapp/core/static_src`.
- Bundled local htmx, Alpine CSP build, Chart.js, and app JavaScript in `appimage/baseapp/core/static`.
- allauth account URLs and starter templates under `/accounts/`.
- Database-backed background tasks with a local worker service.
- CSP middleware and restrictive default policy.
- Rate-limited htmx example endpoint.
- `HistoryModel`, a UUID/timestamp/simple-history abstract base model.
- Docker Compose services for Django, background tasks, Tailwind, PostgreSQL, and Redis.
- GitHub Actions for Ruff, asset build, Django tests, deploy checks, and ECR/ECS deployment.
- Terraform under `terraform/aws` for VPC, ALB, ECS, RDS, Redis, IAM, logs, and secrets.

## Prerequisites

- Docker and Docker Compose.
- Python 3.13 for local virtualenv workflows.
- Node 22 if you build frontend assets outside Docker.
- Terraform and AWS CLI if you use the AWS stack.

## Local Bootstrap

Create the local virtualenv:

```bash
cd appimage/baseapp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the full local stack:

```bash
cd ../..
docker compose up --build
```

Open [http://localhost:8000/](http://localhost:8000/). The app container waits for PostgreSQL, runs migrations, and starts Django. The Tailwind service watches and rebuilds CSS.
The worker container runs migrations and then starts `python manage.py process_tasks` for `django-background-tasks`.

For a shell-only run:

```bash
cd appimage/baseapp
./.venv/bin/python manage.py migrate --settings=app.settings.local
./.venv/bin/python manage.py runserver --settings=app.settings.local
```

## Tests And TDD

This template expects test-first changes.

Run the full Django suite:

```bash
cd appimage/baseapp
./.venv/bin/python manage.py test --settings=app.settings.test
```

Run lint and format checks:

```bash
cd appimage/baseapp
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
```

Run the GitHub Actions workflow linter:

```bash
go install github.com/rhysd/actionlint/cmd/actionlint@v1.7.12
"$(go env GOPATH)/bin/actionlint"
```

Run the production deploy check with a sample environment:

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

For new behavior, add or update a focused test first, watch it fail for the expected reason, implement the change, then run the targeted test and the full suite.

## Frontend Assets

Frontend dependencies are managed by npm in `appimage/baseapp/core/static_src`.

```bash
cd appimage/baseapp/core/static_src
npm ci
npm run build
```

The default page loads local bundled files:

- `js/htmx.min.js`
- `js/alpine.min.js`
- `js/chart.umd.min.js`
- `js/app.js`
- `css/dist/styles.css`

Do not load htmx, Alpine, or Chart.js from a CDN in generated apps. The local bundle keeps development reproducible and CSP-friendly.

## Authentication

django-allauth is installed and mounted at `/accounts/`.

The starter uses email login, basic signup/login/logout templates, and Django's default user model. Add provider configuration only when the generated project needs it.

## HistoryModel

Use `core.models.HistoryModel` for models that should have UUID primary keys, timestamps, django-simple-history tracking, no-op save suppression, choice validation, sticky fields, and admin change URLs.

```python
from django.db import models

from core.models import HistoryModel


class Customer(HistoryModel):
    name = models.CharField(max_length=255)
```

Set `_sticky_fields = ("field_name",)` on a subclass to make fields immutable after creation.

## Background Tasks

Use `django-background-tasks` for simple database-backed work that should run outside the request/response cycle.

```python
from background_task import background


@background()
def send_welcome_email(user_id):
    ...
```

Schedule a task by calling it like a normal function:

```python
send_welcome_email(user.id)
```

The template includes `core.tasks.example_background_task` as a minimal example. Locally, `docker compose up --build` starts a `worker` service that runs `python manage.py process_tasks`. In production, the Terraform stack includes a separate ECS worker service; keep `background_worker_desired_count = 0` until the app image exists and migrations have run, then scale it to `1` or more.

## Security Defaults

Production settings require explicit environment variables for secrets, hosts, CSRF origins, and database connection details. They also enable secure cookies, HSTS, proxy SSL headers, CSP, clickjacking protection, and secure content-type sniffing defaults.

`SECURE_SSL_REDIRECT` defaults to true in production. The Terraform stack sets it to false only when no HTTPS certificate is configured so the first ALB HTTP bootstrap can work.

## AWS Terraform Bootstrap

The Terraform stack is in `terraform/aws`. It uses a small backend bootstrap stack so a new project can start with remote state.

Install and configure AWS credentials:

```bash
aws configure
aws sts get-caller-identity
```

Create the remote state bucket and lock table:

```bash
cd terraform/aws/backend-bootstrap
terraform init
terraform apply
terraform output backend_config
```

Configure the main stack backend:

```bash
cd ../
cp backend.hcl.example backend.hcl
```

Fill `backend.hcl` with the bootstrap output values.

Create your app variables:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `project_name`, `environment`, and `aws_region`. Keep `desired_task_count = 0` for the first apply so Terraform can create ECR and the infrastructure before an app image exists. The tracked `image.auto.tfvars.json` file owns `container_image`; it starts with a safe placeholder and is updated by the deploy workflow after a successful image rollout.

```bash
terraform init -backend-config=backend.hcl
terraform plan
terraform apply
terraform output ecr_repository_url
```

Configure the GitHub deployment workflow with repository or environment variables:

- `AWS_REGION`
- `AWS_ROLE_TO_ASSUME`
- `ECR_REPOSITORY_URI` from `terraform output -raw ecr_repository_url`
- `ECS_CLUSTER` from `terraform output -raw ecs_cluster_name`
- `ECS_WEB_SERVICE` from `terraform output -raw ecs_service_name`
- `ECS_WEB_TASK_DEFINITION` from `terraform output -raw ecs_task_definition_family`
- `ECS_WORKER_SERVICE` from `terraform output -raw ecs_background_worker_service_name`, if you run the worker
- `ECS_WORKER_TASK_DEFINITION` from `terraform output -raw ecs_background_worker_task_definition_family`, if you run the worker

Run the `deploy` GitHub Action manually or push to `main`. The workflow builds `./appimage`, pushes a commit-tagged image to ECR, deploys the web service and optional worker service, then commits the deployed image URI to `terraform/aws/image.auto.tfvars.json`.

Pull that image URI commit, keep `desired_task_count = 0`, then apply again. This updates the ECS task definition without starting the web service yet:

```bash
terraform apply
```

Run migrations as a one-off ECS task using the cluster, task definition, subnet, and security-group outputs. Do not run migrations as the steady-state ECS service command.

```bash
aws ecs run-task \
  --cluster "$(terraform output -raw ecs_cluster_name)" \
  --task-definition "$(terraform output -raw ecs_task_definition_family)" \
  --launch-type FARGATE \
  --network-configuration "$(terraform output -raw ecs_run_task_network_configuration)" \
  --overrides '{"containerOverrides":[{"name":"app","command":["python","manage.py","migrate","--settings=app.settings.production"]}]}'
```

After migrations finish, set `desired_task_count = 1`. If you use background tasks, also set `background_worker_desired_count = 1`. Apply again, and open the ALB URL:

```bash
terraform apply
terraform output alb_url
```

If you do not configure `certificate_arn`, the ALB bootstrap URL is HTTP. It is useful for initial health checks, but production settings still keep secure session and CSRF cookies enabled, so configure HTTPS before testing auth or forms.

For more detail, read `terraform/aws/README.md`.

## Adding Domain Apps

Create a new Django app for real product domains:

```bash
cd appimage/baseapp
./.venv/bin/python manage.py startapp billing
```

Add it to `INSTALLED_APPS` in `app/settings/base.py`, give it its own `urls.py` when it owns routes, and keep shared template/static conventions consistent with `core`.

## Updating Dependencies

Python dependencies are pinned in `appimage/baseapp/requirements.txt`. Frontend dependencies are pinned by `appimage/baseapp/core/static_src/package-lock.json`. After dependency updates, run:

```bash
cd appimage/baseapp/core/static_src
npm ci
npm run build

cd ../../
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
./.venv/bin/python manage.py test --settings=app.settings.test
```
