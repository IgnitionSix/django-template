import json
import re
from pathlib import Path

from django.test import SimpleTestCase


REPO_ROOT = Path(__file__).resolve().parents[4]


class DeployWorkflowTests(SimpleTestCase):
    def test_ci_workflow_lints_github_actions(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "api-test.yml"

        contents = workflow.read_text()

        self.assertIn("github.com/rhysd/actionlint/cmd/actionlint", contents)
        self.assertIn("actionlint", contents)

    def test_deploy_workflow_builds_pushes_records_and_deploys_image(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "deploy.yml"

        contents = workflow.read_text()

        self.assertIn("aws-actions/configure-aws-credentials", contents)
        self.assertIn("aws-actions/amazon-ecr-login@v2", contents)
        self.assertIn("docker build", contents)
        self.assertIn("docker push", contents)
        self.assertIn("terraform/aws/image.auto.tfvars.json", contents)
        self.assertIn("aws-actions/amazon-ecs-render-task-definition", contents)
        self.assertIn("aws-actions/amazon-ecs-deploy-task-definition@v2", contents)
        self.assertIn("background-worker", contents)

    def test_terraform_image_file_is_auto_loaded_json(self):
        image_vars_path = REPO_ROOT / "terraform" / "aws" / "image.auto.tfvars.json"

        image_vars = json.loads(image_vars_path.read_text())

        self.assertEqual(
            image_vars,
            {"container_image": "public.ecr.aws/docker/library/python:3.13-slim"},
        )

    def test_terraform_ecs_task_definition_has_prod_ready_metadata(self):
        terraform_path = REPO_ROOT / "terraform" / "aws" / "ecs.tf"
        locals_path = REPO_ROOT / "terraform" / "aws" / "main.tf"

        contents = terraform_path.read_text()
        locals_contents = locals_path.read_text()

        self.assertIn("runtime_platform", contents)
        self.assertIn("var.task_cpu_architecture", contents)
        self.assertIn("var.task_operating_system_family", contents)
        self.assertIn("name          = local.container_port_mapping_name", contents)
        self.assertIn("appProtocol   = var.container_app_protocol", contents)
        self.assertIn("for name, value in var.app_environment", locals_contents)
        self.assertIn("for name, value_from in var.app_secrets", locals_contents)

    def test_terraform_includes_dev_and_prod_environment_examples(self):
        examples_dir = REPO_ROOT / "terraform" / "aws" / "environments"

        dev_example = (examples_dir / "dev.tfvars.example").read_text()
        prod_example = (examples_dir / "prod.tfvars.example").read_text()

        self.assertRegex(dev_example, r'environment\s+= "dev"')
        self.assertIn("task_cpu    = 512", dev_example)
        self.assertIn("task_memory = 1024", dev_example)
        self.assertRegex(prod_example, r'environment\s+= "prod"')
        self.assertIn("task_cpu    = 2048", prod_example)
        self.assertIn("task_memory = 5120", prod_example)
        self.assertIn("ecs_use_private_subnets = true", prod_example)
        self.assertTrue(re.search(r"app_secrets\s+= \{", prod_example))
