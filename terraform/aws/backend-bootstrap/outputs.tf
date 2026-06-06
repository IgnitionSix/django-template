output "state_bucket_name" {
  description = "S3 bucket name for the main stack backend."
  value       = aws_s3_bucket.terraform_state.bucket
}

output "lock_table_name" {
  description = "DynamoDB table name for state locking."
  value       = aws_dynamodb_table.terraform_locks.name
}

output "aws_region" {
  description = "AWS region used for the backend resources."
  value       = var.aws_region
}

output "backend_config" {
  description = "Backend config values to pass to terraform init in terraform/aws."
  value = {
    bucket         = aws_s3_bucket.terraform_state.bucket
    key            = local.backend_key_hint
    region         = var.aws_region
    dynamodb_table = aws_dynamodb_table.terraform_locks.name
    encrypt        = true
  }
}

