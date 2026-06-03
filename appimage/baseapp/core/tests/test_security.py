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
