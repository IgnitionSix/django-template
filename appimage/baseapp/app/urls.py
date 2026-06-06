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
