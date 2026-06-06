from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path("htmx/ping/", views.htmx_ping, name="htmx_ping"),
]
