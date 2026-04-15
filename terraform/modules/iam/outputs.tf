output "app_sa_email" {
  description = "Application service account email (GKE workloads via Workload Identity)."
  value       = google_service_account.app.email
}

output "app_sa_name" {
  description = "Application service account resource name."
  value       = google_service_account.app.name
}

output "gke_node_sa_email" {
  description = "GKE node service account email."
  value       = google_service_account.gke_node.email
}

output "deployer_sa_email" {
  description = "Deployer (GitHub Actions) service account email."
  value       = google_service_account.deployer.email
}

output "deployer_sa_name" {
  description = "Deployer service account resource name."
  value       = google_service_account.deployer.name
}

output "wif_pool_name" {
  description = "Workload Identity Federation pool resource name."
  value       = google_iam_workload_identity_pool.github.name
}

output "wif_provider_name" {
  description = "Workload Identity Federation provider resource name — set as GCP_WORKLOAD_IDENTITY_PROVIDER in GitHub Actions secrets."
  value       = google_iam_workload_identity_pool_provider.github_oidc.name
}
