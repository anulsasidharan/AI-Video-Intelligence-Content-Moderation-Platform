output "network_id" {
  description = "The ID of the VPC network."
  value       = google_compute_network.vpc.id
}

output "network_name" {
  description = "The name of the VPC network."
  value       = google_compute_network.vpc.name
}

output "network_self_link" {
  description = "The self-link of the VPC network."
  value       = google_compute_network.vpc.self_link
}

output "subnetwork_id" {
  description = "The ID of the primary subnetwork."
  value       = google_compute_subnetwork.private.id
}

output "subnetwork_name" {
  description = "The name of the primary subnetwork."
  value       = google_compute_subnetwork.private.name
}

output "subnetwork_self_link" {
  description = "The self-link of the primary subnetwork."
  value       = google_compute_subnetwork.private.self_link
}

output "pods_range_name" {
  description = "Secondary range name for GKE pods."
  value       = "pods"
}

output "services_range_name" {
  description = "Secondary range name for GKE services."
  value       = "services"
}

output "private_services_range_name" {
  description = "Name of the global address reserved for private services access."
  value       = google_compute_global_address.private_services_range.name
}

output "private_vpc_connection_id" {
  description = "ID of the VPC peering connection to Google managed services."
  value       = google_service_networking_connection.private_vpc_connection.id
}
