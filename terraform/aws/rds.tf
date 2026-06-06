resource "aws_db_subnet_group" "app" {
  name       = "${local.name_prefix}-rds"
  subnet_ids = aws_subnet.private[*].id

  tags = {
    Name = "${local.name_prefix}-rds"
  }
}

resource "aws_db_instance" "app" {
  identifier = "${local.name_prefix}-postgres"

  engine         = "postgres"
  engine_version = var.rds_engine_version
  instance_class = var.rds_instance_class

  allocated_storage     = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  storage_encrypted     = true

  db_name  = var.rds_database_name
  username = var.rds_username
  password = local.postgres_password
  port     = 5432

  db_subnet_group_name   = aws_db_subnet_group.app.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  backup_retention_period = var.rds_backup_retention_days
  deletion_protection     = var.rds_deletion_protection
  skip_final_snapshot     = var.rds_skip_final_snapshot

  tags = {
    Name = "${local.name_prefix}-postgres"
  }
}

