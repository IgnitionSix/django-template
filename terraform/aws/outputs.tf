output "alb_dns_name" {
  description = "DNS name for the application load balancer."
  value       = aws_lb.app.dns_name
}

output "alb_url" {
  description = "URL to open after the ECS service has a healthy task."
  value       = "${local.https_enabled ? "https" : "http"}://${aws_lb.app.dns_name}"
}

output "ecr_repository_url" {
  description = "ECR repository URL for the Django application image."
  value       = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = aws_ecs_cluster.app.name
}

output "ecs_service_name" {
  description = "ECS service name."
  value       = aws_ecs_service.app.name
}

output "ecs_background_worker_service_name" {
  description = "ECS service name for the background task worker."
  value       = aws_ecs_service.background_worker.name
}

output "ecs_task_definition_family" {
  description = "ECS task definition family for one-off tasks."
  value       = aws_ecs_task_definition.app.family
}

output "ecs_background_worker_task_definition_family" {
  description = "ECS task definition family for the background task worker."
  value       = aws_ecs_task_definition.background_worker.family
}

output "ecs_security_group_id" {
  description = "Security group ID attached to ECS tasks."
  value       = aws_security_group.ecs.id
}

output "ecs_subnet_ids" {
  description = "Subnet IDs used by ECS tasks."
  value       = local.ecs_subnet_ids
}

output "ecs_run_task_network_configuration" {
  description = "AWS CLI network configuration value for ecs run-task."
  value       = "awsvpcConfiguration={subnets=[${join(",", local.ecs_subnet_ids)}],securityGroups=[${aws_security_group.ecs.id}],assignPublicIp=${var.ecs_assign_public_ip ? "ENABLED" : "DISABLED"}}"
}

output "rds_endpoint" {
  description = "RDS endpoint hostname and port."
  value       = aws_db_instance.app.endpoint
}

output "redis_endpoint" {
  description = "Redis primary endpoint hostname."
  value       = aws_elasticache_replication_group.app.primary_endpoint_address
}

output "django_secret_key_secret_arn" {
  description = "Secrets Manager ARN for DJANGO_SECRET_KEY."
  value       = aws_secretsmanager_secret.django_secret_key.arn
}

output "database_secret_arn" {
  description = "Secrets Manager ARN for database connection details."
  value       = aws_secretsmanager_secret.database.arn
}

output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.app.id
}
