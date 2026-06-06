import tempfile

from django.core.files.storage import storages
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse


class CoreViewTests(TestCase):
    def test_index_renders_template_stack(self):
        response = self.client.get(reverse("core:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Django Template")
        self.assertContains(response, "hx-get")
        self.assertTemplateUsed(response, "core/index.html")

    def test_index_renders_without_collected_static_manifest(self):
        with tempfile.TemporaryDirectory() as static_root:
            storages._storages.clear()
            with override_settings(DEBUG=False, STATIC_ROOT=static_root):
                response = self.client.get(reverse("core:index"))
            storages._storages.clear()

        self.assertEqual(response.status_code, 200)

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
