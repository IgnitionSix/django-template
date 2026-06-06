from django.apps import apps
from django.core.management import get_commands
from django.test import SimpleTestCase


class SettingsTests(SimpleTestCase):
    def test_core_template_apps_are_installed(self):
        self.assertTrue(apps.is_installed("core"))
        self.assertTrue(apps.is_installed("allauth"))
        self.assertTrue(apps.is_installed("simple_history"))
        self.assertTrue(apps.is_installed("background_task"))

    def test_background_task_worker_command_is_available(self):
        self.assertIn("process_tasks", get_commands())

    def test_removed_apps_are_not_installed(self):
        removed_app_labels = (
            "rest_framework",
            "drf_spectacular",
            "compressor",
            "api",
            "home",
            "theme",
        )

        for app_label in removed_app_labels:
            self.assertFalse(apps.is_installed(app_label))
