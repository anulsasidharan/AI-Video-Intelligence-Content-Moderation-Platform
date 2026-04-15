output "instance_name" {
  description = "Cloud SQL instance name."
  value       = google_sql_database_instance.postgres.name
}

output "instance_id" {
  description = "Cloud SQL instance ID."
  value       = google_sql_database_instance.postgres.id
}

output "connection_name" {
  description = "Cloud SQL connection name in the format project:region:instance."
  value       = google_sql_database_instance.postgres.connection_name
}

output "private_ip" {
  description = "Private IP address of the Cloud SQL instance."
  value       = google_sql_database_instance.postgres.private_ip_address
  sensitive   = true
}

output "database_name" {
  description = "Application database name."
  value       = google_sql_database.app.name
}

output "database_user" {
  description = "Application database user name."
  value       = google_sql_user.app.name
}
