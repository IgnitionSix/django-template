locals {
  name_prefix = "${var.project_name}-${var.environment}"
  availability_zone_count = min(
    length(data.aws_availability_zones.available.names),
    length(var.public_subnet_cidrs),
    length(var.private_subnet_cidrs),
  )

  public_subnet_cidrs  = slice(var.public_subnet_cidrs, 0, local.availability_zone_count)
  private_subnet_cidrs = slice(var.private_subnet_cidrs, 0, local.availability_zone_count)
  availability_zones   = slice(data.aws_availability_zones.available.names, 0, local.availability_zone_count)

  https_enabled = var.certificate_arn != null && var.certificate_arn != ""
  app_hosts     = distinct(concat(var.app_allowed_hosts, var.domain_names, [aws_lb.app.dns_name]))
  app_origins = distinct(concat(
    var.app_csrf_trusted_origins,
    [for host in concat(var.domain_names, [aws_lb.app.dns_name]) : "${local.https_enabled ? "https" : "http"}://${host}"],
  ))

  ecs_subnet_ids = var.ecs_use_private_subnets ? aws_subnet.private[*].id : aws_subnet.public[*].id
  container_port_mapping_name = coalesce(
    var.container_port_mapping_name,
    "${local.name_prefix}-${var.container_port}-tcp",
  )

  common_environment = [
    {
      name  = "DJANGO_SETTINGS_MODULE"
      value = "app.settings.production"
    },
    {
      name  = "DJANGO_ALLOWED_HOSTS"
      value = join(",", local.app_hosts)
    },
    {
      name  = "DJANGO_CSRF_TRUSTED_ORIGINS"
      value = join(",", local.app_origins)
    },
    {
      name  = "POSTGRES_DB"
      value = var.rds_database_name
    },
    {
      name  = "POSTGRES_USER"
      value = var.rds_username
    },
    {
      name  = "POSTGRES_HOST"
      value = aws_db_instance.app.address
    },
    {
      name  = "POSTGRES_PORT"
      value = tostring(aws_db_instance.app.port)
    },
    {
      name  = "POSTGRES_CONN_MAX_AGE"
      value = "60"
    },
    {
      name  = "REDIS_URL"
      value = "rediss://${aws_elasticache_replication_group.app.primary_endpoint_address}:${var.redis_port}/0"
    },
    {
      name  = "SECURE_SSL_REDIRECT"
      value = tostring(local.https_enabled)
    },
    {
      name  = "SECURE_HSTS_SECONDS"
      value = tostring(local.https_enabled ? var.secure_hsts_seconds : 0)
    },
  ]

  task_environment = concat(
    local.common_environment,
    [
      for name, value in var.app_environment : {
        name  = name
        value = value
      }
    ],
  )

  managed_task_secrets = [
    {
      name      = "DJANGO_SECRET_KEY"
      valueFrom = aws_secretsmanager_secret.django_secret_key.arn
    },
    {
      name      = "POSTGRES_PASSWORD"
      valueFrom = "${aws_secretsmanager_secret.database.arn}:password::"
    },
  ]

  task_secrets = concat(
    local.managed_task_secrets,
    [
      for name, value_from in var.app_secrets : {
        name      = name
        valueFrom = value_from
      }
    ],
  )
}
