import importlib.util
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase


REPO_ROOT = Path(__file__).resolve().parents[4]
BOOTSTRAP_PATH = REPO_ROOT / "terraform" / "aws" / "bootstrap.py"


def load_bootstrap_module():
    spec = importlib.util.spec_from_file_location(
        "terraform_aws_bootstrap", BOOTSTRAP_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TerraformBootstrapTests(SimpleTestCase):
    def test_render_tfvars_customizes_prod_task_and_secret_values(self):
        bootstrap = load_bootstrap_module()
        config = bootstrap.BootstrapConfig(
            profile="prod",
            project_name="launch-pad",
            environment="prod",
            aws_region="us-east-2",
            domain_names=["app.example.com", "admin.example.com"],
            certificate_arn="arn:aws:acm:us-east-2:123456789012:certificate/example",
            desired_task_count=0,
            background_worker_desired_count=0,
            task_cpu=2048,
            task_memory=5120,
            enable_nat_gateway=True,
            ecs_use_private_subnets=True,
            ecs_assign_public_ip=False,
            alb_deletion_protection=True,
            rds_deletion_protection=True,
            rds_skip_final_snapshot=False,
            app_environment={"BASIC_AUTH_USERNAME": "launch"},
            app_secrets={
                "BASIC_AUTH_PASSWORD": "arn:aws:secretsmanager:us-east-2:123456789012:secret:launch-pad-prod:BASIC_AUTH_PASSWORD::"
            },
            app_secret_access_arns=[
                "arn:aws:secretsmanager:us-east-2:123456789012:secret:launch-pad-prod*"
            ],
            backend_bucket="launch-pad-prod-tfstate",
            backend_key="prod/terraform.tfstate",
            backend_region="us-east-2",
            backend_dynamodb_table="launch-pad-prod-locks",
            github_environment="production",
            github_role_to_assume="arn:aws:iam::123456789012:role/launch-pad-github",
        )

        tfvars = bootstrap.render_tfvars(config)

        self.assertIn('project_name = "launch-pad"', tfvars)
        self.assertIn('environment  = "prod"', tfvars)
        self.assertIn('aws_region   = "us-east-2"', tfvars)
        self.assertRegex(
            tfvars,
            r'domain_names\s+= \["app\.example\.com", "admin\.example\.com"\]',
        )
        self.assertIn("task_cpu    = 2048", tfvars)
        self.assertIn("task_memory = 5120", tfvars)
        self.assertIn("ecs_use_private_subnets = true", tfvars)
        self.assertIn('BASIC_AUTH_USERNAME = "launch"', tfvars)
        self.assertIn("BASIC_AUTH_PASSWORD", tfvars)
        self.assertIn("app_secret_access_arns = [", tfvars)

    def test_writes_backend_and_deploy_notes_for_github_environment(self):
        bootstrap = load_bootstrap_module()
        config = bootstrap.BootstrapConfig(
            profile="dev",
            project_name="launch-pad",
            environment="dev",
            aws_region="us-east-1",
            backend_bucket="launch-pad-dev-tfstate",
            backend_key="dev/terraform.tfstate",
            backend_region="us-east-1",
            backend_dynamodb_table="launch-pad-dev-locks",
            github_environment="development",
            github_role_to_assume="arn:aws:iam::123456789012:role/launch-pad-github",
        )

        with TemporaryDirectory() as tmpdir:
            paths = bootstrap.write_bootstrap_files(config, Path(tmpdir))

            self.assertEqual(
                (Path(tmpdir) / "terraform.tfvars").read_text(),
                bootstrap.render_tfvars(config),
            )
            self.assertIn(
                'bucket         = "launch-pad-dev-tfstate"',
                (Path(tmpdir) / "backend.hcl").read_text(),
            )
            self.assertIn(
                "GitHub environment: development",
                paths.github_vars_path.read_text(),
            )
            self.assertIn(
                "AWS_ROLE_TO_ASSUME=arn:aws:iam::123456789012:role/launch-pad-github",
                paths.github_vars_path.read_text(),
            )
            self.assertIn(
                "terraform output -raw ecs_service_name",
                paths.next_steps_path.read_text(),
            )
