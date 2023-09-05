from django.urls import path

from .views.home import test

from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path(r'test', test, name='test'),
]