resource "random_id" "bucket_suffix" {
  byte_length = 4

  keepers = {
    project     = var.project_name
    environment = var.environment
  }
}

locals {
  name_prefix      = "${var.project_name}-${var.environment}"
  state_bucket     = coalesce(var.state_bucket_name, "${local.name_prefix}-terraform-state-${random_id.bucket_suffix.hex}")
  lock_table       = coalesce(var.lock_table_name, "${local.name_prefix}-terraform-locks")
  backend_key_hint = "${var.environment}/terraform.tfstate"
}

resource "aws_s3_bucket" "terraform_state" {
  bucket        = local.state_bucket
  force_destroy = var.force_destroy_state_bucket
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = local.lock_table
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}

