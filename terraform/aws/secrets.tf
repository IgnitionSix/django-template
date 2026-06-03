resource "random_password" "django_secret_key" {
  length  = 64
  special = true
}

resource "random_password" "postgres_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

locals {
  django_secret_key = coalesce(var.django_secret_key, random_password.django_secret_key.result)
  postgres_password = coalesce(var.postgres_password, random_password.postgres_password.result)
}

resource "aws_secretsmanager_secret" "django_secret_key" {
  name                    = "${local.name_prefix}/django-secret-key"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "django_secret_key" {
  secret_id     = aws_secretsmanager_secret.django_secret_key.id
  secret_string = local.django_secret_key
}

resource "aws_secretsmanager_secret" "database" {
  name                    = "${local.name_prefix}/database"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    engine   = "postgres"
    host     = aws_db_instance.app.address
    port     = aws_db_instance.app.port
    dbname   = var.rds_database_name
    username = var.rds_username
    password = local.postgres_password
  })
}
