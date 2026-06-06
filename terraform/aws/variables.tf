variable "aws_region" {
  description = "AWS region for all application infrastructure."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short name used in AWS resource names."
  type        = string
  default     = "django-template"
}

variable "environment" {
  description = "Environment name, such as dev, staging, or production."
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Extra tags applied to all supported AWS resources."
  type        = map(string)
  default     = {}
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs. Provide at least two."
  type        = list(string)
  default     = ["10.20.0.0/20", "10.20.16.0/20"]

  validation {
    condition     = length(var.public_subnet_cidrs) >= 2
    error_message = "Provide at least two public subnet CIDRs."
  }
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDRs for RDS, Redis, and optionally ECS. Provide at least two."
  type        = list(string)
  default     = ["10.20.128.0/20", "10.20.144.0/20"]

  validation {
    condition     = length(var.private_subnet_cidrs) >= 2
    error_message = "Provide at least two private subnet CIDRs."
  }
}

variable "enable_nat_gateway" {
  description = "Create NAT gateway support for private ECS tasks. This improves posture but increases cost."
  type        = bool
  default     = false
}

variable "single_nat_gateway" {
  description = "Use one NAT gateway instead of one per public subnet."
  type        = bool
  default     = true
}

variable "ecs_use_private_subnets" {
  description = "Run ECS tasks in private subnets. Set enable_nat_gateway=true or add VPC endpoints so tasks can pull images and secrets."
  type        = bool
  default     = false
}

variable "ecs_assign_public_ip" {
  description = "Assign public IPs to ECS tasks. Keep true when ecs_use_private_subnets=false."
  type        = bool
  default     = true
}

variable "allowed_ingress_cidrs" {
  description = "CIDR blocks allowed to reach the ALB."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "certificate_arn" {
  description = "Optional ACM certificate ARN. When set, the stack creates HTTPS and redirects HTTP to HTTPS."
  type        = string
  default     = null
}

variable "alb_deletion_protection" {
  description = "Protect the application load balancer from deletion."
  type        = bool
  default     = false
}

variable "domain_names" {
  description = "Optional hostnames that will be sent to Django in DJANGO_ALLOWED_HOSTS and CSRF origins."
  type        = list(string)
  default     = []
}

variable "app_allowed_hosts" {
  description = "Additional values for DJANGO_ALLOWED_HOSTS."
  type        = list(string)
  default     = []
}

variable "app_csrf_trusted_origins" {
  description = "Additional fully-qualified CSRF trusted origins, for example https://app.example.com."
  type        = list(string)
  default     = []
}

variable "container_image" {
  description = "Container image for the Django app. The default is a placeholder; build and push your app image before setting desired_task_count above zero."
  type        = string
  default     = "public.ecr.aws/docker/library/python:3.13-slim"
}

variable "container_port" {
  description = "Port the Django container listens on."
  type        = number
  default     = 8000
}

variable "container_command" {
  description = "Optional command override for the Django container."
  type        = list(string)
  default     = []
}

variable "desired_task_count" {
  description = "Number of ECS tasks to run. Keep 0 until your Django image is pushed."
  type        = number
  default     = 0
}

variable "background_worker_desired_count" {
  description = "Number of background task worker ECS tasks to run. Keep 0 until your Django image is pushed and migrations have run."
  type        = number
  default     = 0
}

variable "background_worker_command" {
  description = "Command override for the background task worker container."
  type        = list(string)
  default     = ["python", "manage.py", "process_tasks", "--settings=app.settings.production"]
}

variable "task_cpu" {
  description = "Fargate task CPU units."
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Fargate task memory in MiB."
  type        = number
  default     = 1024
}

variable "health_check_path" {
  description = "ALB target group health check path."
  type        = string
  default     = "/"
}

variable "ecr_repository_name" {
  description = "Optional ECR repository name. Defaults to project-environment-app."
  type        = string
  default     = null
}

variable "rds_database_name" {
  description = "Initial PostgreSQL database name."
  type        = string
  default     = "defaultapp"
}

variable "rds_username" {
  description = "PostgreSQL admin username for the Django app."
  type        = string
  default     = "django"
}

variable "rds_instance_class" {
  description = "RDS instance class."
  type        = string
  default     = "db.t4g.micro"
}

variable "rds_allocated_storage" {
  description = "Initial RDS storage in GiB."
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "Maximum autoscaled RDS storage in GiB."
  type        = number
  default     = 100
}

variable "rds_engine_version" {
  description = "Optional PostgreSQL engine version. Leave null for the provider/AWS default."
  type        = string
  default     = null
}

variable "rds_backup_retention_days" {
  description = "RDS backup retention period."
  type        = number
  default     = 7
}

variable "rds_deletion_protection" {
  description = "Protect the RDS instance from deletion."
  type        = bool
  default     = false
}

variable "rds_skip_final_snapshot" {
  description = "Skip final RDS snapshot during destroy. Set false for production."
  type        = bool
  default     = true
}

variable "redis_node_type" {
  description = "ElastiCache Redis node type."
  type        = string
  default     = "cache.t4g.micro"
}

variable "redis_port" {
  description = "Redis port."
  type        = number
  default     = 6379
}

variable "redis_engine_version" {
  description = "Optional Redis engine version. Leave null for AWS default."
  type        = string
  default     = null
}

variable "log_retention_days" {
  description = "CloudWatch log retention for ECS app logs."
  type        = number
  default     = 30
}

variable "django_secret_key" {
  description = "Optional Django SECRET_KEY. Leave null to generate one in Secrets Manager."
  type        = string
  default     = null
  sensitive   = true
}

variable "postgres_password" {
  description = "Optional PostgreSQL password. Leave null to generate one in Secrets Manager."
  type        = string
  default     = null
  sensitive   = true
}

variable "secure_hsts_seconds" {
  description = "HSTS seconds sent to Django. Defaults to one year."
  type        = number
  default     = 31536000
}
