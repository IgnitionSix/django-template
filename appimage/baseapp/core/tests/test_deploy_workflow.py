import json
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
