# AWS Terraform

This stack creates the default AWS shape for a generated Django project:

- VPC with public and private subnets across two or more availability zones.
- Optional NAT gateway support.
- Application Load Balancer.
- ECS Fargate cluster, task definition, and service.
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
- `container_image` after you push an app image
- `desired_task_count` after the image exists

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

## 4. Build And Push The Django Image

Return to the repo root, then use the generated ECR repository URL:

```bash
cd ../..
aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

docker build -t my-django-app ./appimage
docker tag my-django-app:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/my-django-app-dev-app:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/my-django-app-dev-app:latest
```

Return to the Terraform stack directory:

```bash
cd terraform/aws
```

Set `container_image` to the pushed tag, keep `desired_task_count = 0`, then apply again. This registers the app task definition without starting the service yet.

```bash
terraform apply
```

Run migrations as a one-off ECS task using the task definition and cluster output. Do not run migrations as the steady-state ECS service command, because multiple tasks can start at once during deploys.

```bash
aws ecs run-task \
  --cluster "$(terraform output -raw ecs_cluster_name)" \
  --task-definition "$(terraform output -raw ecs_task_definition_family)" \
  --launch-type FARGATE \
  --network-configuration "$(terraform output -raw ecs_run_task_network_configuration)" \
  --overrides '{"containerOverrides":[{"name":"app","command":["python","manage.py","migrate","--settings=app.settings.production"]}]}'
```

After migrations finish, set `desired_task_count = 1` and apply again to start the service:

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
