output "repository_id" {
  description = "Artifact Registry repository ID."
  value       = google_artifact_registry_repository.docker.repository_id
}

output "repository_url" {
  description = "Base URL for Docker images in this repository (REGION-docker.pkg.dev/PROJECT/REPO)."
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.docker.repository_id}"
}

output "repository_name" {
  description = "Full resource name of the repository."
  value       = google_artifact_registry_repository.docker.name
}
