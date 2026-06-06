# Django Template Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the template as a modern Django 5.2 server-rendered starter with one `core` app, bundled frontend assets, allauth, CSP, rate limiting, django-simple-history, clear tests/docs, and ready-to-apply AWS Terraform.

**Architecture:** Keep `app` as the Django project package and consolidate starter behavior into one local app named `core`. Build assets from `core/static_src` into `core/static`, remove DRF/compressor/Elasticsearch-era code, and add a flat teachable Terraform stack under `terraform/aws`.

**Tech Stack:** Django 5.2 LTS, Python 3.13, PostgreSQL, Redis, django-allauth, django-csp, django-ratelimit, django-simple-history, django-tailwind, Tailwind, htmx, Alpine, Chart.js, Docker Compose, AWS ECS/RDS/ElastiCache/VPC/ALB, Terraform.

---

## File Structure Map

- `appimage/baseapp/app/settings/base.py`: shared Django apps, middleware, templates, static, auth, CSP, cache, allauth, simple-history, and security defaults.
- `appimage/baseapp/app/settings/local.py`: local Docker/Postgres/Redis settings with debug and browser reload.
- `appimage/baseapp/app/settings/test.py`: deterministic test settings with SQLite, locmem cache/email, fast password hashing.
- `appimage/baseapp/app/settings/production.py`: environment-driven production settings for ECS/RDS/Redis/HTTPS.
- `appimage/baseapp/app/urls.py`: admin, allauth, browser reload in local/debug, and `core.urls`.
- `appimage/baseapp/core/`: new single default Django app.
- `appimage/baseapp/core/models/history.py`: abstract `HistoryModel` base class.
- `appimage/baseapp/core/templates/`: base, home, htmx fragment, and allauth starter templates.
- `appimage/baseapp/core/static_src/`: npm/Tailwind source and lockfile.
- `appimage/baseapp/core/static/`: bundled JS and built CSS output.
- `appimage/baseapp/core/tests/`: Django tests for views, settings/security, and `HistoryModel`.
- `appimage/baseapp/requirements.txt`: modern runtime/dev dependencies.
- `appimage/Dockerfile`, `docker-compose.yml`, `appimage/baseapp/run.sh`, `appimage/baseapp/run_tailwind.sh`: pinned local runtime and readiness flow.
- `.github/workflows/api-test.yml`: rename or update workflow to run Ruff, Django tests, checks, and asset build.
- `terraform/aws/`: ready-to-apply AWS stack.
- `terraform/aws/backend-bootstrap/`: S3/DynamoDB remote-state bootstrap stack.
- `README.md`: root bootstrap guide.
- `AGENTS.md`: agent operating guide.

## Task 1: Baseline Verification And Failing Characterization Tests

**Files:**
- Create: `appimage/baseapp/core/tests/test_views.py`
- Create: `appimage/baseapp/core/tests/test_settings.py`
- Create: `appimage/baseapp/core/tests/test_security.py`
- Create: `appimage/baseapp/core/tests/test_history_model.py`

- [ ] **Step 1: Confirm current failing baseline**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
python manage.py test --settings=app.settings.test
```

Expected: FAIL because the existing tests contain `assertEqueal` and DRF-backed test imports.

- [ ] **Step 2: Create the `core` test package skeleton**

Create these empty files so Django can discover tests once `core` exists:

```text
appimage/baseapp/core/__init__.py
appimage/baseapp/core/tests/__init__.py
```

- [ ] **Step 3: Write failing view tests**

Create `appimage/baseapp/core/tests/test_views.py`:

```python
from django.test import TestCase
from django.urls import reverse


class CoreViewTests(TestCase):
    def test_index_renders_template_stack(self):
        response = self.client.get(reverse("core:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django Template")
        self.assertContains(response, "hx-get")
        self.assertTemplateUsed(response, "core/index.html")

    def test_htmx_ping_returns_fragment(self):
        response = self.client.get(
            reverse("core:htmx_ping"),
            headers={"HX-Request": "true"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This is a return value from htmx")
        self.assertTemplateUsed(response, "core/_htmx_ping.html")

    def test_allauth_urls_are_mounted(self):
        response = self.client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in")
```

- [ ] **Step 4: Write failing settings/security tests**

Create `appimage/baseapp/core/tests/test_security.py`:

```python
from django.test import TestCase, override_settings
from django.urls import reverse


class SecurityHeaderTests(TestCase):
    def test_csp_header_is_present(self):
        response = self.client.get(reverse("core:index"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("Content-Security-Policy", response.headers)
        self.assertIn("'self'", response.headers["Content-Security-Policy"])

    @override_settings(RATELIMIT_ENABLE=True)
    def test_htmx_ping_rate_limit_allows_normal_request(self):
        response = self.client.get(
            reverse("core:htmx_ping"),
            headers={"HX-Request": "true"},
        )

        self.assertEqual(response.status_code, 200)
```

Create `appimage/baseapp/core/tests/test_settings.py`:

```python
from django.conf import settings
from django.test import SimpleTestCase


class SettingsTests(SimpleTestCase):
    def test_core_template_apps_are_installed(self):
        self.assertIn("core", settings.INSTALLED_APPS)
        self.assertIn("allauth", settings.INSTALLED_APPS)
        self.assertIn("simple_history", settings.INSTALLED_APPS)

    def test_removed_apps_are_not_installed(self):
        self.assertNotIn("rest_framework", settings.INSTALLED_APPS)
        self.assertNotIn("drf_spectacular", settings.INSTALLED_APPS)
        self.assertNotIn("compressor", settings.INSTALLED_APPS)
        self.assertNotIn("api", settings.INSTALLED_APPS)
        self.assertNotIn("home", settings.INSTALLED_APPS)
        self.assertNotIn("theme", settings.INSTALLED_APPS)
```

- [ ] **Step 5: Write failing `HistoryModel` tests**

Create `appimage/baseapp/core/tests/test_history_model.py`:

```python
import datetime as dt

from django.core.exceptions import ValidationError
from django.db import connection, models
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import HistoryModel


class ExampleHistoryModel(HistoryModel):
    _sticky_fields = ("sticky_code",)

    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"

    name = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=((STATUS_ACTIVE, "Active"), (STATUS_ARCHIVED, "Archived")),
        default=STATUS_ACTIVE,
    )
    sticky_code = models.CharField(max_length=32, default="fixed")
    last_found = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = "core"


class HistoryModelTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(ExampleHistoryModel)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(ExampleHistoryModel)
        super().tearDownClass()

    def test_create_sets_uuid_timestamps_short_id_and_history(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        self.assertFalse(obj.is_new)
        self.assertEqual(obj.short_id, str(obj.id).split("-")[0])
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.modified_at)
        self.assertEqual(obj.history.count(), 1)

    def test_unchanged_save_does_not_create_history_row(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        obj.save()

        self.assertEqual(obj.history.count(), 1)

    def test_changed_save_creates_history_row(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        obj.name = "Beta"
        obj.save()

        self.assertEqual(obj.history.count(), 2)

    def test_sticky_field_is_restored_on_existing_save(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha", sticky_code="original")

        obj.name = "Beta"
        obj.sticky_code = "changed"
        obj.save()

        obj.refresh_from_db()
        self.assertEqual(obj.name, "Beta")
        self.assertEqual(obj.sticky_code, "original")

    def test_invalid_choice_raises_validation_error(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")
        obj.status = "wrong"

        with self.assertRaises(ValidationError):
            obj.save()

    def test_last_found_only_change_updates_without_history_row(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")
        found_at = timezone.make_aware(dt.datetime(2026, 6, 3, 12, 0, 0))

        obj.last_found = found_at
        obj.save()

        obj.refresh_from_db()
        self.assertEqual(obj.last_found, found_at)
        self.assertEqual(obj.history.count(), 1)

    def test_get_change_url_uses_admin_route(self):
        obj = ExampleHistoryModel.objects.create(name="Alpha")

        self.assertEqual(
            obj.get_change_url(),
            reverse("admin:core_examplehistorymodel_change", args=(obj.pk,)),
        )
```

- [ ] **Step 6: Run targeted tests and confirm failure**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
python manage.py test core.tests --settings=app.settings.test
```

Expected: FAIL because `core` is not installed and `HistoryModel` does not exist.

- [ ] **Step 7: Commit failing tests**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add appimage/baseapp/core
git commit -m "test: define refreshed django template behavior"
```

## Task 2: Create `core` App And Consolidate Routing/Templates

**Files:**
- Create: `appimage/baseapp/core/apps.py`
- Create: `appimage/baseapp/core/urls.py`
- Create: `appimage/baseapp/core/views.py`
- Create: `appimage/baseapp/core/templates/_base.html`
- Create: `appimage/baseapp/core/templates/core/index.html`
- Create: `appimage/baseapp/core/templates/core/_htmx_ping.html`
- Modify: `appimage/baseapp/app/urls.py`
- Delete after migration: `appimage/baseapp/api/`, `appimage/baseapp/home/`

- [ ] **Step 1: Add `CoreConfig`**

Create `appimage/baseapp/core/apps.py`:

```python
from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
```

- [ ] **Step 2: Add core views**

Create `appimage/baseapp/core/views.py`:

```python
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit


def index(request):
    return render(request, "core/index.html")


@ratelimit(key="ip", rate="30/m", method="GET", block=True)
def htmx_ping(request):
    return render(request, "core/_htmx_ping.html")
```

- [ ] **Step 3: Add core URLs**

Create `appimage/baseapp/core/urls.py`:

```python
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("htmx/ping/", views.htmx_ping, name="htmx_ping"),
]
```

- [ ] **Step 4: Replace project URLs**

Replace `appimage/baseapp/app/urls.py` with:

```python
from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG and "django_browser_reload" in settings.INSTALLED_APPS:
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
```

- [ ] **Step 5: Add base template**

Create `appimage/baseapp/core/templates/_base.html`:

```html
{% load static %}
{% load django_browser_reload %}
{% load tailwind_tags %}

<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Django Template{% endblock title %}</title>
    {% tailwind_css %}
    <script src="{% static 'js/htmx.min.js' %}" defer></script>
    <script src="{% static 'js/alpine.min.js' %}" defer></script>
    <script src="{% static 'js/chart.umd.min.js' %}" defer></script>
    <script src="{% static 'js/app.js' %}" defer></script>
  </head>
  <body class="min-h-screen bg-slate-50 text-slate-950">
    <main class="mx-auto max-w-5xl px-6 py-10">
      {% block content %}{% endblock content %}
    </main>
    {% if debug %}
      {% django_browser_reload_script %}
    {% endif %}
  </body>
</html>
```

- [ ] **Step 6: Add starter page**

Create `appimage/baseapp/core/templates/core/index.html`:

```html
{% extends "_base.html" %}

{% block title %}Django Template{% endblock title %}

{% block content %}
  <section class="space-y-6">
    <div class="space-y-2">
      <h1 class="text-3xl font-semibold tracking-normal">Django Template</h1>
      <p class="max-w-2xl text-base text-slate-700">
        A server-rendered Django starter with Tailwind, htmx, Alpine, Chart.js,
        allauth, CSP, rate limiting, and django-simple-history.
      </p>
    </div>

    <div class="flex flex-wrap items-center gap-3">
      <button
        class="rounded bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        type="button"
        hx-get="{% url 'core:htmx_ping' %}"
        hx-target="#htmx-output"
        hx-swap="innerHTML">
        Test htmx
      </button>
      <div id="htmx-output" class="text-sm text-slate-700"></div>
    </div>

    <div x-data="{ open: false }" class="space-y-2">
      <button
        class="rounded border border-slate-300 px-4 py-2 text-sm font-medium hover:bg-white"
        type="button"
        @click="open = !open">
        Toggle Alpine panel
      </button>
      <p x-show="open" class="text-sm text-slate-700">
        Alpine is available for small client-side interactions.
      </p>
    </div>

    <div class="max-w-xl">
      <canvas id="starter-chart" height="120" aria-label="Starter Chart.js chart"></canvas>
    </div>
  </section>
{% endblock content %}
```

- [ ] **Step 7: Add htmx fragment**

Create `appimage/baseapp/core/templates/core/_htmx_ping.html`:

```html
<span>This is a return value from htmx.</span>
```

- [ ] **Step 8: Run targeted tests**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
python manage.py test core.tests.test_views --settings=app.settings.test
```

Expected: FAIL until settings/dependencies in Task 3 are implemented.

- [ ] **Step 9: Commit core app skeleton**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add appimage/baseapp/core appimage/baseapp/app/urls.py
git commit -m "feat: consolidate starter routes into core app"
```

## Task 3: Modernize Python Dependencies And Settings

**Files:**
- Modify: `appimage/baseapp/requirements.txt`
- Modify: `appimage/baseapp/app/settings/base.py`
- Modify: `appimage/baseapp/app/settings/local.py`
- Modify: `appimage/baseapp/app/settings/test.py`
- Create: `appimage/baseapp/app/settings/production.py`
- Delete: `appimage/baseapp/app/renderers/plain_text.py`

- [ ] **Step 1: Replace requirements**

Replace `appimage/baseapp/requirements.txt` with:

```text
Django==5.2.14
django-allauth==65.18.0
django-browser-reload==1.21.0
django-csp==4.0
django-ratelimit==4.1.0
django-simple-history==3.11.0
django-tailwind==4.4.2
psycopg[binary]==3.3.4
redis==8.0.0
ruff==0.15.15
```

If implementation-time package resolution shows a patch release has superseded one of these, update to the current compatible patch and note it in the commit message.

- [ ] **Step 2: Replace shared settings**

Replace `appimage/baseapp/app/settings/base.py` with:

```python
import os
from pathlib import Path

from csp.constants import NONE, SELF

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-local-template-key")
DEBUG = False
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "csp",
    "django_browser_reload",
    "simple_history",
    "tailwind",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

WSGI_APPLICATION = "app.wsgi.application"
ASGI_APPLICATION = "app.asgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

TAILWIND_APP_NAME = "core"
NPM_BIN_PATH = os.environ.get("NPM_BIN_PATH", "npm")

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [SELF],
        "style-src": [SELF],
        "img-src": [SELF, "data:"],
        "connect-src": [SELF],
        "font-src": [SELF],
        "object-src": [NONE],
        "base-uri": [SELF],
        "frame-ancestors": [NONE],
        "form-action": [SELF],
    }
}

RATELIMIT_ENABLE = True

REDIS_URL = os.environ.get("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "django-template",
        }
    }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
```

- [ ] **Step 3: Replace local settings**

Replace `appimage/baseapp/app/settings/local.py` with:

```python
import os

from .base import *  # noqa: F403

DEBUG = True
ALLOWED_HOSTS = ["*"]

MIDDLEWARE += ["django_browser_reload.middleware.BrowserReloadMiddleware"]  # noqa: F405

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "defaultapp"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": int(os.environ.get("POSTGRES_PORT", "5432")),
    }
}

CSRF_TRUSTED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]
```

- [ ] **Step 4: Replace test settings**

Replace `appimage/baseapp/app/settings/test.py` with:

```python
from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = "django-template-test-secret"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}
```

- [ ] **Step 5: Add production settings**

Create `appimage/baseapp/app/settings/production.py`:

```python
import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403


def env(name):
    value = os.environ.get(name)
    if value in (None, ""):
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")
    return value


SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS").split(",")
CSRF_TRUSTED_ORIGINS = env("DJANGO_CSRF_TRUSTED_ORIGINS").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": int(os.environ.get("POSTGRES_PORT", "5432")),
        "CONN_MAX_AGE": int(os.environ.get("POSTGRES_CONN_MAX_AGE", "60")),
    }
}

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get("SECURE_HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "true").lower() == "true"
```

- [ ] **Step 6: Delete obsolete renderer**

Delete:

```text
appimage/baseapp/app/renderers/plain_text.py
appimage/baseapp/app/renderers/__init__.py
```

- [ ] **Step 7: Install dependencies and run settings tests**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py test core.tests.test_settings --settings=app.settings.test
```

Expected: PASS.

- [ ] **Step 8: Commit dependency/settings refresh**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add appimage/baseapp/requirements.txt appimage/baseapp/app appimage/baseapp/core
git rm -r --ignore-unmatch appimage/baseapp/app/renderers
git commit -m "feat: modernize django dependencies and settings"
```

## Task 4: Add `HistoryModel`

**Files:**
- Create: `appimage/baseapp/core/models/__init__.py`
- Create: `appimage/baseapp/core/models/history.py`
- Modify: `appimage/baseapp/core/tests/test_history_model.py`

- [ ] **Step 1: Create model package export**

Create `appimage/baseapp/core/models/__init__.py`:

```python
from .history import HistoryModel

__all__ = ["HistoryModel"]
```

- [ ] **Step 2: Implement `HistoryModel`**

Create `appimage/baseapp/core/models/history.py`:

```python
import datetime as dt
import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from simple_history.models import HistoricalRecords


class HistoryModel(models.Model):
    """Base model with UUIDs, timestamps, and no-op history suppression."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords(inherit=True)

    class Meta:
        abstract = True

    @property
    def is_new(self):
        return self._state.adding

    @property
    def short_id(self):
        return str(self.id).split("-")[0]

    def save(self, *args, **kwargs):
        self._validate_choice_fields()

        if self._state.adding:
            super().save(*args, **kwargs)
            return

        orig = self.__class__.objects.get(pk=self.pk)
        self._restore_sticky_fields(orig)

        has_changes, has_last_found_change = self._compare_field_values(orig)

        if not has_changes:
            if has_last_found_change:
                self.__class__.objects.filter(id=self.id).update(
                    last_found=getattr(self, "last_found")
                )
            return

        super().save(*args, **kwargs)

    def get_change_url(self):
        return reverse(
            "admin:%s_%s_change" % (self._meta.app_label, self._meta.model_name),
            args=(self.pk,),
        )

    def _validate_choice_fields(self):
        errors = {}
        for field in self.__class__._meta.fields:
            if not getattr(field, "choices", None):
                continue
            value = getattr(self, field.name)
            if value is None:
                continue
            valid_values = {choice_value for choice_value, _ in field.choices}
            if value not in valid_values:
                errors[field.name] = f"{value!r} is not a valid choice."
        if errors:
            raise ValidationError(errors)

    def _restore_sticky_fields(self, orig):
        for field_name in getattr(self.__class__, "_sticky_fields", ()):
            setattr(self, field_name, getattr(orig, field_name))

    def _compare_field_values(self, orig):
        has_changes = False
        has_last_found_change = False

        for field in self.__class__._meta.fields:
            original_value = getattr(orig, field.name)
            new_value = getattr(self, field.name)

            if field.name == "last_found" and original_value != new_value:
                has_last_found_change = True
                continue

            original_value, new_value = self._normalize_comparable_values(
                original_value,
                new_value,
            )
            if original_value != new_value:
                has_changes = True
                break

        return has_changes, has_last_found_change

    def _normalize_comparable_values(self, original_value, new_value):
        if isinstance(original_value, dt.datetime) and isinstance(new_value, dt.datetime):
            if timezone.is_aware(original_value):
                original_value = timezone.localtime(original_value)
            if timezone.is_aware(new_value):
                new_value = timezone.localtime(new_value)

        if (
            isinstance(original_value, dt.date)
            and not isinstance(original_value, dt.datetime)
            and isinstance(new_value, dt.datetime)
        ):
            new_value = new_value.date()

        return original_value, new_value
```

- [ ] **Step 3: Run history tests**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
python manage.py test core.tests.test_history_model --settings=app.settings.test
```

Expected: PASS.

- [ ] **Step 4: Run all core tests**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
python manage.py test core.tests --settings=app.settings.test
```

Expected: PASS or only asset-template failures that Task 5 will address.

- [ ] **Step 5: Commit history model**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add appimage/baseapp/core/models appimage/baseapp/core/tests/test_history_model.py
git commit -m "feat: add reusable history model base"
```

## Task 5: Bundle Frontend Assets With Tailwind, htmx, Alpine, And Chart.js

**Files:**
- Create: `appimage/baseapp/core/static_src/package.json`
- Create: `appimage/baseapp/core/static_src/postcss.config.js`
- Create: `appimage/baseapp/core/static_src/tailwind.config.js`
- Create: `appimage/baseapp/core/static_src/src/styles.css`
- Create: `appimage/baseapp/core/static/js/app.js`
- Create after build/copy: `appimage/baseapp/core/static/js/htmx.min.js`
- Create after build/copy: `appimage/baseapp/core/static/js/alpine.min.js`
- Create after build/copy: `appimage/baseapp/core/static/js/chart.umd.min.js`
- Delete after migration: `appimage/baseapp/theme/`

- [ ] **Step 1: Add npm package manifest**

Create `appimage/baseapp/core/static_src/package.json`:

```json
{
  "name": "django-template-assets",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "build": "npm run build:clean && npm run build:tailwind && npm run build:vendor",
    "build:clean": "rimraf ../static/css/dist ../static/js/htmx.min.js ../static/js/alpine.min.js ../static/js/chart.umd.min.js",
    "build:tailwind": "tailwindcss --postcss -i ./src/styles.css -o ../static/css/dist/styles.css --minify",
    "build:vendor": "mkdir -p ../static/js && cp ./node_modules/htmx.org/dist/htmx.min.js ../static/js/htmx.min.js && cp ./node_modules/@alpinejs/csp/dist/cdn.min.js ../static/js/alpine.min.js && cp ./node_modules/chart.js/dist/chart.umd.min.js ../static/js/chart.umd.min.js",
    "dev": "tailwindcss --postcss -i ./src/styles.css -o ../static/css/dist/styles.css -w"
  },
  "devDependencies": {
    "@tailwindcss/forms": "^0.5.10",
    "@tailwindcss/typography": "^0.5.16",
    "@alpinejs/csp": "^3.15.0",
    "autoprefixer": "^10.4.21",
    "chart.js": "4.5.0",
    "htmx.org": "^2.0.4",
    "postcss": "^8.5.4",
    "postcss-import": "^16.1.0",
    "postcss-nested": "^6.2.0",
    "rimraf": "^6.0.1",
    "tailwindcss": "^3.4.17"
  }
}
```

- [ ] **Step 2: Add PostCSS config**

Create `appimage/baseapp/core/static_src/postcss.config.js`:

```javascript
module.exports = {
  plugins: {
    "postcss-import": {},
    "postcss-nested": {},
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

- [ ] **Step 3: Add Tailwind config**

Create `appimage/baseapp/core/static_src/tailwind.config.js`:

```javascript
module.exports = {
  content: [
    "../templates/**/*.html",
    "../../core/templates/**/*.html",
    "../../core/**/*.py",
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
  ],
};
```

- [ ] **Step 4: Add Tailwind source**

Create `appimage/baseapp/core/static_src/src/styles.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 5: Add app JS**

Create `appimage/baseapp/core/static/js/app.js`:

```javascript
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(";").shift();
  }
  return "";
}

document.body.addEventListener("htmx:configRequest", (event) => {
  event.detail.headers["X-CSRFToken"] = getCookie("csrftoken");
});

document.addEventListener("DOMContentLoaded", () => {
  const canvas = document.getElementById("starter-chart");
  if (!canvas || !window.Chart) {
    return;
  }

  new window.Chart(canvas, {
    type: "bar",
    data: {
      labels: ["Django", "Tailwind", "htmx"],
      datasets: [
        {
          label: "Template defaults",
          data: [5, 4, 3],
          backgroundColor: ["#0f172a", "#2563eb", "#16a34a"],
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });
});
```

- [ ] **Step 6: Install and build assets**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp/core/static_src
npm install
npm run build
```

Expected: `package-lock.json`, `../static/css/dist/styles.css`, `../static/js/htmx.min.js`, `../static/js/alpine.min.js`, and `../static/js/chart.umd.min.js` exist.

- [ ] **Step 7: Run view/security tests**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
python manage.py test core.tests.test_views core.tests.test_security --settings=app.settings.test
```

Expected: PASS.

- [ ] **Step 8: Commit assets**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add appimage/baseapp/core/static appimage/baseapp/core/static_src appimage/baseapp/core/templates
git commit -m "feat: bundle frontend assets"
```

## Task 6: Add Allauth Starter Templates And Remove Obsolete Apps

**Files:**
- Create: `appimage/baseapp/core/templates/account/login.html`
- Create: `appimage/baseapp/core/templates/account/signup.html`
- Create: `appimage/baseapp/core/templates/account/logout.html`
- Modify: `appimage/baseapp/core/templates/_base.html`
- Delete: `appimage/baseapp/api/`
- Delete: `appimage/baseapp/home/`
- Delete: `appimage/baseapp/theme/`

- [ ] **Step 1: Add login template**

Create `appimage/baseapp/core/templates/account/login.html`:

```html
{% extends "_base.html" %}

{% block title %}Sign in{% endblock title %}

{% block content %}
  <section class="mx-auto max-w-md space-y-6">
    <h1 class="text-2xl font-semibold">Sign in</h1>
    <form method="post" action="{% url 'account_login' %}" class="space-y-4">
      {% csrf_token %}
      {{ form.as_p }}
      <button class="rounded bg-slate-950 px-4 py-2 text-sm font-medium text-white" type="submit">
        Sign in
      </button>
    </form>
  </section>
{% endblock content %}
```

- [ ] **Step 2: Add signup template**

Create `appimage/baseapp/core/templates/account/signup.html`:

```html
{% extends "_base.html" %}

{% block title %}Create account{% endblock title %}

{% block content %}
  <section class="mx-auto max-w-md space-y-6">
    <h1 class="text-2xl font-semibold">Create account</h1>
    <form method="post" action="{% url 'account_signup' %}" class="space-y-4">
      {% csrf_token %}
      {{ form.as_p }}
      <button class="rounded bg-slate-950 px-4 py-2 text-sm font-medium text-white" type="submit">
        Create account
      </button>
    </form>
  </section>
{% endblock content %}
```

- [ ] **Step 3: Add logout template**

Create `appimage/baseapp/core/templates/account/logout.html`:

```html
{% extends "_base.html" %}

{% block title %}Sign out{% endblock title %}

{% block content %}
  <section class="mx-auto max-w-md space-y-6">
    <h1 class="text-2xl font-semibold">Sign out</h1>
    <form method="post" action="{% url 'account_logout' %}">
      {% csrf_token %}
      <button class="rounded bg-slate-950 px-4 py-2 text-sm font-medium text-white" type="submit">
        Sign out
      </button>
    </form>
  </section>
{% endblock content %}
```

- [ ] **Step 4: Delete obsolete app directories**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git rm -r appimage/baseapp/api appimage/baseapp/home appimage/baseapp/theme
```

Expected: deleted app files include old DRF view, old broken tests, compressor template, and vendored htmx.

- [ ] **Step 5: Run tests**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
python manage.py test core.tests --settings=app.settings.test
```

Expected: PASS.

- [ ] **Step 6: Commit allauth templates and app deletion**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add appimage/baseapp/core/templates
git commit -m "feat: add allauth templates and remove legacy apps"
```

## Task 7: Modernize Docker Compose And Runtime Scripts

**Files:**
- Modify: `appimage/Dockerfile`
- Modify: `docker-compose.yml`
- Modify: `appimage/baseapp/run.sh`
- Modify: `appimage/baseapp/run_tailwind.sh`

- [ ] **Step 1: Replace Dockerfile**

Replace `appimage/Dockerfile` with:

```dockerfile
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV NODE_VERSION=22

WORKDIR /code

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl postgresql-client ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY baseapp/requirements.txt /code/requirements.txt
RUN pip install --upgrade pip && pip install -r /code/requirements.txt

COPY baseapp /code/baseapp

WORKDIR /code/baseapp

RUN if [ -f core/static_src/package-lock.json ]; then cd core/static_src && npm ci && npm run build; fi

CMD ["/bin/sh", "-c", "./run.sh"]
```

- [ ] **Step 2: Replace Compose file**

Replace `docker-compose.yml` with:

```yaml
services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: defaultapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - ./data/postgres:/var/lib/postgresql/data/
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d defaultapp"]
      interval: 5s
      timeout: 5s
      retries: 20
    networks:
      - backend

  redis:
    image: redis:7-alpine
    networks:
      - backend

  app:
    build: ./appimage
    environment:
      DJANGO_SETTINGS_MODULE: app.settings.local
      POSTGRES_DB: defaultapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_HOST: db
      REDIS_URL: redis://redis:6379/0
      ENVIRONMENT: local
    volumes:
      - ./appimage/baseapp:/code/baseapp
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - backend

  tailwind:
    build: ./appimage
    command: /bin/sh /code/baseapp/run_tailwind.sh
    environment:
      DJANGO_SETTINGS_MODULE: app.settings.local
      POSTGRES_DB: defaultapp
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_HOST: db
      REDIS_URL: redis://redis:6379/0
    volumes:
      - ./appimage/baseapp:/code/baseapp
    depends_on:
      - app
    tty: true
    networks:
      - backend

networks:
  backend:
    driver: bridge
```

- [ ] **Step 3: Replace app run script**

Replace `appimage/baseapp/run.sh` with:

```sh
#!/bin/sh
set -e

until pg_isready -h "${POSTGRES_HOST:-db}" -U "${POSTGRES_USER:-postgres}" -d "${POSTGRES_DB:-defaultapp}"; do
  echo "Waiting for postgres..."
  sleep 2
done

python manage.py migrate --settings="${DJANGO_SETTINGS_MODULE:-app.settings.local}"
python manage.py runserver 0.0.0.0:8000 --settings="${DJANGO_SETTINGS_MODULE:-app.settings.local}"
```

- [ ] **Step 4: Replace Tailwind run script**

Replace `appimage/baseapp/run_tailwind.sh` with:

```sh
#!/bin/sh
set -e

cd /code/baseapp/core/static_src
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi
npm run dev
```

- [ ] **Step 5: Run Docker build**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
docker compose build
```

Expected: PASS, including Python dependency install and npm asset build.

- [ ] **Step 6: Run Compose smoke test**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
docker compose up -d
docker compose ps
curl -fsS http://localhost:8000/ | grep "Django Template"
docker compose down
```

Expected: app, db, redis, and tailwind start; curl finds `Django Template`.

- [ ] **Step 7: Commit Docker modernization**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add appimage/Dockerfile docker-compose.yml appimage/baseapp/run.sh appimage/baseapp/run_tailwind.sh
git commit -m "feat: modernize docker compose dev stack"
```

## Task 8: Update GitHub Actions

**Files:**
- Modify: `.github/workflows/api-test.yml`

- [ ] **Step 1: Replace workflow**

Replace `.github/workflows/api-test.yml` with:

```yaml
name: app

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["main"]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: appimage/baseapp/core/static_src/package-lock.json

      - name: Install Python dependencies
        working-directory: ./appimage/baseapp
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Install frontend dependencies
        working-directory: ./appimage/baseapp/core/static_src
        run: npm ci

      - name: Build frontend assets
        working-directory: ./appimage/baseapp/core/static_src
        run: npm run build

      - name: Ruff
        working-directory: ./appimage/baseapp
        run: |
          ruff check .
          ruff format --check .

      - name: Django tests
        working-directory: ./appimage/baseapp
        run: python manage.py test --settings=app.settings.test

      - name: Django deploy check with sample env
        working-directory: ./appimage/baseapp
        env:
          DJANGO_SECRET_KEY: ci-secret
          DJANGO_ALLOWED_HOSTS: example.com
          DJANGO_CSRF_TRUSTED_ORIGINS: https://example.com
          POSTGRES_DB: defaultapp
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_HOST: localhost
        run: python manage.py check --deploy --settings=app.settings.production
```

- [ ] **Step 2: Run local equivalents**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
ruff check .
ruff format --check .
python manage.py test --settings=app.settings.test
DJANGO_SECRET_KEY=ci-secret \
DJANGO_ALLOWED_HOSTS=example.com \
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com \
POSTGRES_DB=defaultapp \
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_HOST=localhost \
python manage.py check --deploy --settings=app.settings.production
```

Expected: PASS. If `check --deploy` reports advisory warnings that are intentionally managed by infrastructure, fix settings when possible; otherwise document the exact accepted warning in README.

- [ ] **Step 3: Commit workflow**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add .github/workflows/api-test.yml
git commit -m "ci: run modern django template checks"
```

## Task 9: Add Ready-To-Apply AWS Terraform

**Files:**
- Create: `terraform/aws/versions.tf`
- Create: `terraform/aws/providers.tf`
- Create: `terraform/aws/variables.tf`
- Create: `terraform/aws/main.tf`
- Create: `terraform/aws/vpc.tf`
- Create: `terraform/aws/security-groups.tf`
- Create: `terraform/aws/rds.tf`
- Create: `terraform/aws/redis.tf`
- Create: `terraform/aws/iam.tf`
- Create: `terraform/aws/secrets.tf`
- Create: `terraform/aws/alb.tf`
- Create: `terraform/aws/ecs.tf`
- Create: `terraform/aws/outputs.tf`
- Create: `terraform/aws/terraform.tfvars.example`
- Create: `terraform/aws/backend-bootstrap/versions.tf`
- Create: `terraform/aws/backend-bootstrap/main.tf`
- Create: `terraform/aws/backend-bootstrap/variables.tf`
- Create: `terraform/aws/backend-bootstrap/outputs.tf`
- Create: `terraform/aws/README.md`

- [ ] **Step 1: Add backend bootstrap stack**

Create `terraform/aws/backend-bootstrap/versions.tf`:

```hcl
terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

Create `terraform/aws/backend-bootstrap/variables.tf`:

```hcl
variable "aws_region" {
  description = "AWS region for the Terraform state resources."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project slug used to name Terraform state resources."
  type        = string
  default     = "django-template"
}
```

Create `terraform/aws/backend-bootstrap/main.tf`:

```hcl
provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "state" {
  bucket = "${var.project_name}-terraform-state"
}

resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "state" {
  bucket = aws_s3_bucket.state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket                  = aws_s3_bucket.state.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "lock" {
  name         = "${var.project_name}-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
```

Create `terraform/aws/backend-bootstrap/outputs.tf`:

```hcl
output "state_bucket" {
  value = aws_s3_bucket.state.bucket
}

output "lock_table" {
  value = aws_dynamodb_table.lock.name
}
```

- [ ] **Step 2: Add root Terraform versions/providers**

Create `terraform/aws/versions.tf`:

```hcl
terraform {
  required_version = ">= 1.8.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
```

Create `terraform/aws/providers.tf`:

```hcl
provider "aws" {
  region = var.aws_region
}
```

- [ ] **Step 3: Add variables**

Create `terraform/aws/variables.tf` with variables for `aws_region`, `project_name`, `environment`, `vpc_cidr`, `public_subnet_cidrs`, `private_subnet_cidrs`, `container_image`, `container_port`, `desired_count`, `task_cpu`, `task_memory`, `rds_instance_class`, `rds_allocated_storage`, `redis_node_type`, `allowed_ingress_cidrs`, `enable_nat_gateway`, `deletion_protection`, `django_allowed_hosts`, and `django_csrf_trusted_origins`. Use defaults from the spec:

```hcl
variable "aws_region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project slug used in resource names."
  type        = string
  default     = "django-template"
}

variable "environment" {
  description = "Environment name, such as dev, staging, or production."
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.40.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs."
  type        = list(string)
  default     = ["10.40.0.0/24", "10.40.1.0/24"]
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDRs."
  type        = list(string)
  default     = ["10.40.10.0/24", "10.40.11.0/24"]
}

variable "container_image" {
  description = "Django container image URI."
  type        = string
  default     = "public.ecr.aws/docker/library/python:3.13-slim"
}

variable "container_port" {
  description = "Container port exposed by the Django app."
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Number of ECS tasks."
  type        = number
  default     = 1
}

variable "task_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 1024
}

variable "rds_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_allocated_storage" {
  description = "RDS storage in GiB."
  type        = number
  default     = 20
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type."
  type        = string
  default     = "cache.t4g.micro"
}

variable "allowed_ingress_cidrs" {
  description = "CIDRs allowed to reach the ALB."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enable_nat_gateway" {
  description = "Create NAT gateway for private subnet egress. Costs more but is production-friendly."
  type        = bool
  default     = false
}

variable "deletion_protection" {
  description = "Enable deletion protection on supported resources."
  type        = bool
  default     = false
}

variable "django_allowed_hosts" {
  description = "Comma-separated ALLOWED_HOSTS value for Django."
  type        = string
  default     = "*"
}

variable "django_csrf_trusted_origins" {
  description = "Comma-separated CSRF trusted origins for Django."
  type        = string
  default     = "http://localhost"
}
```

- [ ] **Step 4: Add AWS resources**

Implement flat Terraform files:

- `vpc.tf`: VPC, public/private subnets, route tables, internet gateway, optional NAT gateway.
- `security-groups.tf`: ALB ingress, ECS app ingress from ALB, RDS ingress from ECS, Redis ingress from ECS.
- `rds.tf`: subnet group, random password, RDS Postgres instance.
- `redis.tf`: subnet group and single-node Redis replication group or cache cluster.
- `iam.tf`: ECS task execution role and task role.
- `secrets.tf`: Secrets Manager secret for Django env values.
- `alb.tf`: ALB, target group, listener.
- `ecs.tf`: cluster, log group, task definition, service.
- `main.tf`: shared locals and tags.
- `outputs.tf`: ALB DNS, RDS endpoint, Redis endpoint, cluster/service names, secret ARN.

Do not use modules unless Terraform validation shows the flat files are unmaintainable.

- [ ] **Step 5: Add tfvars example**

Create `terraform/aws/terraform.tfvars.example`:

```hcl
aws_region                   = "us-east-1"
project_name                 = "my-django-app"
environment                  = "dev"
container_image              = "ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/my-django-app:latest"
django_allowed_hosts         = "*"
django_csrf_trusted_origins  = "http://localhost"
enable_nat_gateway           = false
deletion_protection          = false
allowed_ingress_cidrs        = ["0.0.0.0/0"]
```

- [ ] **Step 6: Add Terraform README**

Create `terraform/aws/README.md` with sections:

````markdown
# AWS Terraform

This stack creates a VPC, RDS PostgreSQL, ElastiCache Redis, ECS Fargate service, ALB, CloudWatch logs, IAM roles, and Secrets Manager entries for the Django template.

## 1. Install tools

Install Terraform 1.8+ and AWS CLI v2.

## 2. Configure AWS

Run `aws configure` or use SSO credentials.

## 3. Bootstrap remote state

Run:

```bash
cd terraform/aws/backend-bootstrap
terraform init
terraform apply -var project_name=my-django-app -var aws_region=us-east-1
```

Copy the `state_bucket` and `lock_table` outputs.

## 4. Configure the main stack

Copy `terraform.tfvars.example` to `terraform.tfvars` and edit project names, region, container image, and hostnames.

## 5. Plan and apply

Run:

```bash
cd terraform/aws
terraform init
terraform plan
terraform apply
```

## 6. Deploy the app image

Build and push your image to ECR, update `container_image`, and apply again.

## 7. Run migrations

Use ECS Exec or a one-off task to run:

```bash
python manage.py migrate --settings=app.settings.production
```

## 8. Tear down

Run `terraform destroy` for the app stack. Empty the state bucket before destroying backend bootstrap resources.
````

- [ ] **Step 7: Validate Terraform**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/terraform/aws/backend-bootstrap
terraform fmt -recursive
terraform init -backend=false
terraform validate

cd /Users/joshuag/dev/ignition6/Code/django-template/terraform/aws
terraform fmt -recursive
terraform init -backend=false
terraform validate
```

Expected: PASS.

- [ ] **Step 8: Commit Terraform**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add terraform/aws
git commit -m "feat: add aws terraform stack"
```

## Task 10: Rewrite README And Add AGENTS.md

**Files:**
- Modify: `README.md`
- Create: `AGENTS.md`

- [ ] **Step 1: Rewrite README**

Replace `README.md` with a guide containing these sections and exact commands:

````markdown
# django-template

A modern Django starter for server-rendered apps using Django 5.2 LTS, Tailwind, htmx, Alpine, Chart.js, django-allauth, django-csp, django-ratelimit, django-simple-history, Docker Compose, and AWS Terraform.

## What is included

- One default Django app: `core`
- Tailwind asset pipeline
- htmx, Alpine, and Chart.js bundled from npm
- allauth account routes and starter templates
- CSP and rate limiting defaults
- `HistoryModel` base class with django-simple-history
- Local Postgres and Redis through Docker Compose
- Ready-to-apply AWS Terraform

## Local bootstrap

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r appimage/baseapp/requirements.txt
cd appimage/baseapp/core/static_src
npm install
npm run build
cd ../../../..
docker compose up -d
````

Open http://localhost:8000/.

## Tests

```bash
cd appimage/baseapp
python manage.py test --settings=app.settings.test
ruff check .
ruff format --check .
```

## TDD workflow

Write the failing Django test first, run it to confirm failure, implement the smallest change, run the targeted test, then run the full suite.

## Terraform bootstrap

Follow `terraform/aws/README.md` from a fresh AWS account: bootstrap state, copy `terraform.tfvars.example`, run `terraform plan`, then `terraform apply`.
```

Include the longer Terraform walkthrough from the spec, including remote state, image push, migrations, outputs, and teardown.

- [ ] **Step 2: Add AGENTS.md**

Create `AGENTS.md`:

````markdown
# AGENTS.md

## Project

This is a Django template repo. Keep `app` as the Django project and `core` as the single default local app.

## Required workflow

Use TDD. Write or update tests before implementation, run the targeted test to watch it fail, implement the change, then run the targeted test and full relevant suite.

## Commands

```bash
cd appimage/baseapp
python manage.py test --settings=app.settings.test
ruff check .
ruff format --check .
DJANGO_SECRET_KEY=ci-secret DJANGO_ALLOWED_HOSTS=example.com DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com POSTGRES_DB=defaultapp POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres POSTGRES_HOST=localhost python manage.py check --deploy --settings=app.settings.production
````

Frontend:

```bash
cd appimage/baseapp/core/static_src
npm ci
npm run build
```

Docker:

```bash
docker compose build
docker compose up -d
docker compose down
```

Terraform:

```bash
cd terraform/aws
terraform fmt -recursive
terraform init -backend=false
terraform validate
```

## Rules

- Do not reintroduce DRF, django-compressor, Elasticsearch, or separate `api`/`home`/`theme` starter apps unless explicitly requested.
- Keep htmx, Alpine, and Chart.js bundled from npm into static assets.
- Keep production settings environment-driven and secure by default.
- Keep Terraform ready to apply with sensible variable defaults.
- Preserve `HistoryModel` no-op save suppression and sticky-field behavior.
```

- [ ] **Step 3: Run docs-adjacent checks**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
rg -n "Django Rest Framework|DRF|django-compressor|Elasticsearch|api and home|cdnjs|Chart.js.*CDN" README.md AGENTS.md appimage/baseapp
```

Expected: no stale default-template references. Mentions in the spec saying old code was removed are acceptable.

- [ ] **Step 4: Commit docs**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add README.md AGENTS.md terraform/aws/README.md
git commit -m "docs: document template bootstrap and agent workflow"
```

## Task 11: Final Cleanup And Verification

**Files:**
- Modify as needed: `.gitignore`
- Remove generated junk: `.DS_Store`, `__pycache__`, checked-in `.venv` files if tracked

- [ ] **Step 1: Remove generated junk from git if tracked**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git ls-files | rg '(^|/)(\\.DS_Store|__pycache__|.*\\.pyc$|\\.venv/)'
```

Expected: if tracked files are listed, remove them with:

```bash
git rm -r --cached appimage/baseapp/.venv || true
git rm -r --cached $(git ls-files | rg '(^|/)(\\.DS_Store|__pycache__|.*\\.pyc$)') || true
```

- [ ] **Step 2: Update `.gitignore`**

Ensure `.gitignore` contains:

```gitignore
.DS_Store
__pycache__/
*.py[cod]
.venv/
data/postgres/
appimage/baseapp/staticfiles/
terraform/aws/.terraform/
terraform/aws/.terraform.lock.hcl
terraform/aws/terraform.tfstate*
terraform/aws/terraform.tfvars
terraform/aws/backend-bootstrap/.terraform/
terraform/aws/backend-bootstrap/.terraform.lock.hcl
terraform/aws/backend-bootstrap/terraform.tfstate*
```

- [ ] **Step 3: Run full backend verification**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp
ruff check .
ruff format --check .
python manage.py test --settings=app.settings.test
DJANGO_SECRET_KEY=ci-secret \
DJANGO_ALLOWED_HOSTS=example.com \
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com \
POSTGRES_DB=defaultapp \
POSTGRES_USER=postgres \
POSTGRES_PASSWORD=postgres \
POSTGRES_HOST=localhost \
python manage.py check --deploy --settings=app.settings.production
```

Expected: PASS.

- [ ] **Step 4: Run frontend verification**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/appimage/baseapp/core/static_src
npm ci
npm run build
test -f ../static/js/htmx.min.js
test -f ../static/js/alpine.min.js
test -f ../static/js/chart.umd.min.js
test -f ../static/css/dist/styles.css
```

Expected: PASS.

- [ ] **Step 5: Run Terraform verification**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template/terraform/aws
terraform fmt -recursive
terraform init -backend=false
terraform validate
```

Expected: PASS.

- [ ] **Step 6: Run Docker verification**

Run:

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
docker compose build
docker compose up -d
curl -fsS http://localhost:8000/ | grep "Django Template"
docker compose down
```

Expected: PASS.

- [ ] **Step 7: Commit final cleanup**

```bash
cd /Users/joshuag/dev/ignition6/Code/django-template
git add .
git commit -m "chore: clean generated files and verify template"
```

## Self-Review Checklist

- [ ] The plan covers app consolidation into `core`.
- [ ] The plan removes DRF, drf-spectacular, django-filter, django-compressor, Elasticsearch, and old apps.
- [ ] The plan bundles htmx, Alpine, and Chart.js from npm.
- [ ] The plan includes django-allauth, django-csp, django-ratelimit, django-simple-history, and `HistoryModel`.
- [ ] The plan includes local/test/production settings.
- [ ] The plan includes Docker Compose modernization.
- [ ] The plan includes ready-to-apply Terraform and backend bootstrap.
- [ ] The plan includes README and `AGENTS.md`.
- [ ] Every task has a verification command and a commit step.
