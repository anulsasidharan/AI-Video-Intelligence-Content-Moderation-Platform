output "cluster_name" {
  description = "GKE cluster name."
  value       = google_container_cluster.primary.name
}

output "cluster_id" {
  description = "GKE cluster resource ID."
  value       = google_container_cluster.primary.id
}

output "cluster_endpoint" {
  description = "GKE control plane endpoint."
  value       = google_container_cluster.primary.endpoint
  sensitive   = true
}

output "cluster_ca_certificate" {
  description = "Base64-encoded cluster CA certificate."
  value       = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
  sensitive   = true
}

output "node_pool_name" {
  description = "Name of the primary node pool."
  value       = google_container_node_pool.primary.name
}

output "workload_identity_pool" {
  description = "Workload Identity pool identifier."
  value       = "${var.project_id}.svc.id.goog"
}
