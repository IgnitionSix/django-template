variable "aws_region" {
  description = "AWS region where the Terraform state bucket and lock table will live."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Short project name used in state resource names."
  type        = string
  default     = "django-template"
}

variable "environment" {
  description = "Environment name used in state resource names."
  type        = string
  default     = "dev"
}

variable "state_bucket_name" {
  description = "Optional globally unique S3 bucket name. Leave null to generate one."
  type        = string
  default     = null
}

variable "lock_table_name" {
  description = "DynamoDB table name for Terraform state locking."
  type        = string
  default     = null
}

variable "force_destroy_state_bucket" {
  description = "Allow Terraform to delete a non-empty state bucket. Keep false for real projects."
  type        = bool
  default     = false
}

