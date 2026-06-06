from django.shortcuts import render
from django_ratelimit.decorators import ratelimit


def index(request):
    return render(request, "core/index.html")


@ratelimit(key="ip", rate="30/m", method="GET", block=True)
def htmx_ping(request):
    return render(request, "core/_htmx_ping.html")
