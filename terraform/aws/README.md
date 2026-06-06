# AWS Terraform

This stack creates the default AWS shape for a generated Django project:

- VPC with public and private subnets across two or more availability zones.
- Optional NAT gateway support.
- Application Load Balancer.
- ECS Fargate cluster, task definition, and service.
- Optional ECS Fargate background task worker service.
- ECR repository for the Django image.
- RDS PostgreSQL.
- ElastiCache Redis for Django cache and rate-limit backing.
- Secrets Manager entries for `DJANGO_SECRET_KEY` and database credentials.
- CloudWatch logs and IAM roles.

## 1. Bootstrap Remote State

From a fresh AWS account, install the AWS CLI and Terraform, then configure credentials:

```bash
aws configure
aws sts get-caller-identity
```

Create the S3 state bucket and DynamoDB lock table:

```bash
cd terraform/aws/backend-bootstrap
terraform init
terraform apply
terraform output backend_config
```

Copy `terraform/aws/backend.hcl.example` to `terraform/aws/backend.hcl` and fill in the output values.

## 2. Configure The App Stack

```bash
cd terraform/aws
cp terraform.tfvars.example terraform.tfvars
```

Edit at least:

- `project_name`
- `environment`
- `aws_region`
- `desired_task_count` after the image exists
- `background_worker_desired_count` after the image exists and migrations have run, if you use background tasks

The tracked `image.auto.tfvars.json` file owns `container_image`. It starts with a safe placeholder and is updated by the GitHub deploy workflow after successful image rollouts.

First initialize with the bootstrapped backend:

```bash
terraform init -backend-config=backend.hcl
```

## 3. First Apply

Keep `desired_task_count = 0` on the first apply so Terraform can create ECR, RDS, Redis, ECS, and the ALB before an app image exists.

```bash
terraform plan
terraform apply
terraform output ecr_repository_url
```

## 4. Configure GitHub Deploys

Create a GitHub environment named `production`, or repository variables if you do not use environments. Set these variables from Terraform outputs:

```bash
AWS_REGION=us-east-1
AWS_ROLE_TO_ASSUME=arn:aws:iam::ACCOUNT_ID:role/YOUR_GITHUB_ACTIONS_ROLE
ECR_REPOSITORY_URI=$(terraform output -raw ecr_repository_url)
ECS_CLUSTER=$(terraform output -raw ecs_cluster_name)
ECS_WEB_SERVICE=$(terraform output -raw ecs_service_name)
ECS_WEB_TASK_DEFINITION=$(terraform output -raw ecs_task_definition_family)
```

If you run the background task worker, also set:

```bash
ECS_WORKER_SERVICE=$(terraform output -raw ecs_background_worker_service_name)
ECS_WORKER_TASK_DEFINITION=$(terraform output -raw ecs_background_worker_task_definition_family)
```

Run the `deploy` GitHub Action manually or push to `main`. It builds `./appimage`, pushes `${GITHUB_SHA}` and `latest` tags to ECR, updates the ECS web task definition, optionally updates the background worker task definition, waits for service stability, and commits the deployed image URI to `terraform/aws/image.auto.tfvars.json`.

Pull that commit locally, keep `desired_task_count = 0`, then apply again. This registers the app task definition with the deployed image without starting the service yet.

```bash
terraform apply
```

Run migrations as a one-off ECS task using the task definition and cluster output. Do not run migrations as the steady-state ECS service or background worker command, because multiple tasks can start at once during deploys.

```bash
aws ecs run-task \
  --cluster "$(terraform output -raw ecs_cluster_name)" \
  --task-definition "$(terraform output -raw ecs_task_definition_family)" \
  --launch-type FARGATE \
  --network-configuration "$(terraform output -raw ecs_run_task_network_configuration)" \
  --overrides '{"containerOverrides":[{"name":"app","command":["python","manage.py","migrate","--settings=app.settings.production"]}]}'
```

After migrations finish, set `desired_task_count = 1`. If you use `django-background-tasks`, also set `background_worker_desired_count = 1` to start the worker service that runs `python manage.py process_tasks`.

```bash
terraform apply
```

## 5. Open The App

```bash
terraform output alb_url
```

Without `certificate_arn`, Terraform uses HTTP and tells Django not to force SSL redirects. Secure session and CSRF cookies still remain enabled, so use the HTTP URL only for initial health checks and public pages. Configure an ACM certificate before testing auth or forms. With `certificate_arn`, Terraform creates HTTPS, redirects HTTP to HTTPS, and Django enforces SSL redirects.

## Cost And Safety Defaults

The defaults are intentionally small and bootstrap-friendly:

- `desired_task_count = 0` until the app image is pushed.
- `background_worker_desired_count = 0` until the app image is pushed and migrations have run.
- `db.t4g.micro` for RDS.
- `cache.t4g.micro` for Redis.
- NAT gateway disabled by default to avoid surprise cost.
- RDS deletion protection disabled and final snapshot skipped for easy teardown.

For production, consider:

```hcl
enable_nat_gateway        = true
ecs_use_private_subnets   = true
ecs_assign_public_ip      = false
alb_deletion_protection   = true
rds_deletion_protection   = true
rds_skip_final_snapshot   = false
```

## Tear Down

Set deletion-protection variables to `false`, confirm you no longer need the data, then run:

```bash
terraform destroy
```

Destroy the backend bootstrap stack only after the main stack is gone and you have no state left to preserve.
