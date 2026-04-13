output "instance_id" {
  description = "Memorystore Redis instance ID."
  value       = google_redis_instance.cache.id
}

output "instance_name" {
  description = "Memorystore Redis instance name."
  value       = google_redis_instance.cache.name
}

output "host" {
  description = "IP address of the Redis endpoint."
  value       = google_redis_instance.cache.host
  sensitive   = true
}

output "port" {
  description = "Port of the Redis endpoint."
  value       = google_redis_instance.cache.port
}

output "redis_url" {
  description = "Redis connection URL (redis://host:port/0)."
  value       = "redis://${google_redis_instance.cache.host}:${google_redis_instance.cache.port}/0"
  sensitive   = true
}
