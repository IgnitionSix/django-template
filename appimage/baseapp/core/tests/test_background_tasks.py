import importlib

from django.apps import apps
from django.test import TestCase


class BackgroundTaskIntegrationTests(TestCase):
    def test_example_task_schedules_database_task(self):
        self.assertTrue(apps.is_installed("background_task"))

        tasks_module = importlib.import_module("core.tasks")
        tasks_module.example_background_task("demo@example.com")

        from background_task.models import Task

        task = Task.objects.get(task_name="core.tasks.example_background_task")
        args, kwargs = task.params()
        self.assertEqual(args, ["demo@example.com"])
        self.assertEqual(kwargs, {})
