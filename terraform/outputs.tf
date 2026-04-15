# ── Network ────────────────────────────────────────────────────────────────────

output "network_id" {
  description = "ID of the VPC network."
  value       = module.vpc.network_id
}

output "subnetwork_id" {
  description = "ID of the primary subnetwork."
  value       = module.vpc.subnetwork_id
}

# ── GKE ────────────────────────────────────────────────────────────────────────

output "gke_cluster_name" {
  description = "GKE cluster name — pass to gcloud container clusters get-credentials."
  value       = module.gke.cluster_name
}

output "gke_cluster_endpoint" {
  description = "GKE control plane endpoint."
  value       = module.gke.cluster_endpoint
  sensitive   = true
}

# ── Cloud SQL ─────────────────────────────────────────────────────────────────

output "cloud_sql_instance_name" {
  description = "Cloud SQL instance name."
  value       = module.cloud_sql.instance_name
}

output "cloud_sql_private_ip" {
  description = "Private IP address of the Cloud SQL instance."
  value       = module.cloud_sql.private_ip
  sensitive   = true
}

output "cloud_sql_connection_name" {
  description = "Cloud SQL connection name (project:region:instance)."
  value       = module.cloud_sql.connection_name
}

# ── Memorystore ───────────────────────────────────────────────────────────────

output "redis_host" {
  description = "Memorystore Redis host IP."
  value       = module.memorystore.host
  sensitive   = true
}

output "redis_port" {
  description = "Memorystore Redis port."
  value       = module.memorystore.port
}

# ── GCS Buckets ───────────────────────────────────────────────────────────────

output "gcs_videos_bucket" {
  description = "GCS bucket name for videos."
  value       = module.gcs.videos_bucket_name
}

output "gcs_thumbnails_bucket" {
  description = "GCS bucket name for thumbnails."
  value       = module.gcs.thumbnails_bucket_name
}

output "gcs_artifacts_bucket" {
  description = "GCS bucket name for AI artifacts."
  value       = module.gcs.artifacts_bucket_name
}

# ── Artifact Registry ─────────────────────────────────────────────────────────

output "gar_repository_url" {
  description = "Artifact Registry repository URL for Docker images."
  value       = module.artifact_registry.repository_url
}

# ── Pub/Sub ───────────────────────────────────────────────────────────────────

output "pubsub_video_uploaded_topic" {
  description = "Pub/Sub topic ID for video upload events."
  value       = module.pubsub.video_uploaded_topic_id
}

output "pubsub_moderation_alerts_topic" {
  description = "Pub/Sub topic ID for moderation alert events."
  value       = module.pubsub.moderation_alerts_topic_id
}

# ── Cloud Armor ───────────────────────────────────────────────────────────────

output "cloud_armor_policy_name" {
  description = "Cloud Armor security policy name — attach to backend services."
  value       = module.cloud_armor.policy_name
}

output "cloud_armor_policy_self_link" {
  description = "Cloud Armor security policy self-link."
  value       = module.cloud_armor.policy_self_link
}

# ── IAM ───────────────────────────────────────────────────────────────────────

output "app_sa_email" {
  description = "Application service account email (used by GKE workloads via Workload Identity)."
  value       = module.iam.app_sa_email
}

output "deployer_sa_email" {
  description = "Deployer service account email (used by GitHub Actions)."
  value       = module.iam.deployer_sa_email
}

output "wif_provider_name" {
  description = "Workload Identity Federation provider resource name — set as GCP_WORKLOAD_IDENTITY_PROVIDER in GitHub Actions."
  value       = module.iam.wif_provider_name
}

# ── Monitoring ────────────────────────────────────────────────────────────────

output "notification_channel_id" {
  description = "Cloud Monitoring notification channel ID."
  value       = module.monitoring.notification_channel_id
}
