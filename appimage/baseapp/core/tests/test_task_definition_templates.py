import importlib.util
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase


REPO_ROOT = Path(__file__).resolve().parents[4]
RENDERER_PATH = REPO_ROOT / "terraform" / "aws" / "render_task_definition.py"
WEB_TEMPLATE_PATH = REPO_ROOT / "terraform" / "aws" / "task-definitions" / "web.json"
WORKER_TEMPLATE_PATH = (
    REPO_ROOT / "terraform" / "aws" / "task-definitions" / "background-worker.json"
)


def load_renderer_module():
    spec = importlib.util.spec_from_file_location(
        "render_task_definition", RENDERER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TaskDefinitionTemplateTests(SimpleTestCase):
    def test_web_template_renders_to_ecs_task_definition_json(self):
        renderer = load_renderer_module()
        values = {
            "TASK_DEFINITION_FAMILY": "django-template-prod-app",
            "ECS_TASK_EXECUTION_ROLE_ARN": "arn:aws:iam::123456789012:role/django-template-prod-ecs-execution",
            "ECS_TASK_ROLE_ARN": "arn:aws:iam::123456789012:role/django-template-prod-ecs-task",
            "CONTAINER_IMAGE": "123456789012.dkr.ecr.us-east-1.amazonaws.com/django-template:abc123",
            "CONTAINER_PORT_MAPPING_NAME": "django-template-prod-8000-tcp",
            "CONTAINER_PORT": "8000",
            "AWS_REGION": "us-east-1",
            "ECS_LOG_GROUP": "/ecs/django-template-prod",
            "DJANGO_ALLOWED_HOSTS": "app.example.com,example-alb.us-east-1.elb.amazonaws.com",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://app.example.com",
            "POSTGRES_DB": "defaultapp",
            "POSTGRES_USER": "django",
            "POSTGRES_HOST": "db.example.com",
            "POSTGRES_PORT": "5432",
            "REDIS_URL": "rediss://redis.example.com:6379/0",
            "SECURE_SSL_REDIRECT": "true",
            "SECURE_HSTS_SECONDS": "31536000",
            "DJANGO_SECRET_KEY_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:django-secret",
            "DATABASE_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:database",
            "TASK_CPU": "2048",
            "TASK_MEMORY": "5120",
            "TASK_CPU_ARCHITECTURE": "X86_64",
            "TASK_OPERATING_SYSTEM_FAMILY": "LINUX",
            "APP_ENVIRONMENT_JSON": '{"BASIC_AUTH_USERNAME": "launch"}',
            "APP_SECRETS_JSON": '{"BASIC_AUTH_PASSWORD": "arn:aws:secretsmanager:us-east-1:123456789012:secret:basic-auth"}',
        }

        rendered = renderer.render_template(WEB_TEMPLATE_PATH, values)

        self.assertEqual(rendered["family"], "django-template-prod-app")
        self.assertEqual(rendered["cpu"], "2048")
        self.assertEqual(rendered["memory"], "5120")
        self.assertEqual(
            rendered["runtimePlatform"],
            {"cpuArchitecture": "X86_64", "operatingSystemFamily": "LINUX"},
        )
        container = rendered["containerDefinitions"][0]
        self.assertEqual(container["name"], "app")
        self.assertEqual(container["image"], values["CONTAINER_IMAGE"])
        self.assertEqual(container["portMappings"][0]["containerPort"], 8000)
        self.assertEqual(container["portMappings"][0]["appProtocol"], "http")
        self.assertIn(
            {"name": "DJANGO_SETTINGS_MODULE", "value": "app.settings.production"},
            container["environment"],
        )
        self.assertIn(
            {"name": "BASIC_AUTH_USERNAME", "value": "launch"},
            container["environment"],
        )
        self.assertIn(
            {
                "name": "POSTGRES_PASSWORD",
                "valueFrom": values["DATABASE_SECRET_ARN"] + ":password::",
            },
            container["secrets"],
        )
        self.assertIn(
            {
                "name": "BASIC_AUTH_PASSWORD",
                "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:basic-auth",
            },
            container["secrets"],
        )

    def test_renderer_writes_background_worker_definition(self):
        renderer = load_renderer_module()
        values = {
            "TASK_DEFINITION_FAMILY": "django-template-prod-background-worker",
            "ECS_TASK_EXECUTION_ROLE_ARN": "arn:aws:iam::123456789012:role/execution",
            "ECS_TASK_ROLE_ARN": "arn:aws:iam::123456789012:role/task",
            "CONTAINER_IMAGE": "123456789012.dkr.ecr.us-east-1.amazonaws.com/django-template:abc123",
            "AWS_REGION": "us-east-1",
            "ECS_LOG_GROUP": "/ecs/django-template-prod",
            "DJANGO_ALLOWED_HOSTS": "app.example.com",
            "DJANGO_CSRF_TRUSTED_ORIGINS": "https://app.example.com",
            "POSTGRES_DB": "defaultapp",
            "POSTGRES_USER": "django",
            "POSTGRES_HOST": "db.example.com",
            "POSTGRES_PORT": "5432",
            "REDIS_URL": "rediss://redis.example.com:6379/0",
            "SECURE_SSL_REDIRECT": "true",
            "SECURE_HSTS_SECONDS": "31536000",
            "DJANGO_SECRET_KEY_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:django-secret",
            "DATABASE_SECRET_ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:database",
            "TASK_CPU": "512",
            "TASK_MEMORY": "1024",
            "TASK_CPU_ARCHITECTURE": "X86_64",
            "TASK_OPERATING_SYSTEM_FAMILY": "LINUX",
        }

        with TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "worker.json"
            renderer.write_rendered_template(
                WORKER_TEMPLATE_PATH,
                output_path,
                values,
            )
            rendered = renderer.load_json(output_path)

        container = rendered["containerDefinitions"][0]
        self.assertEqual(container["name"], "background-worker")
        self.assertEqual(
            container["command"],
            [
                "python",
                "manage.py",
                "process_tasks",
                "--settings=app.settings.production",
            ],
        )
        self.assertEqual(
            container["logConfiguration"]["options"]["awslogs-stream-prefix"],
            "background-worker",
        )
