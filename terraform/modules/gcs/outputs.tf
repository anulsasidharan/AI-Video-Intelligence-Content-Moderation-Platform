output "videos_bucket_name" {
  description = "GCS bucket name for videos."
  value       = google_storage_bucket.videos.name
}

output "videos_bucket_url" {
  description = "GCS bucket URL for videos (gs://...)."
  value       = google_storage_bucket.videos.url
}

output "thumbnails_bucket_name" {
  description = "GCS bucket name for thumbnails."
  value       = google_storage_bucket.thumbnails.name
}

output "thumbnails_bucket_url" {
  description = "GCS bucket URL for thumbnails (gs://...)."
  value       = google_storage_bucket.thumbnails.url
}

output "thumbnails_bucket_self_link" {
  description = "GCS thumbnails bucket self-link (used for Cloud CDN backend bucket)."
  value       = google_storage_bucket.thumbnails.self_link
}

output "artifacts_bucket_name" {
  description = "GCS bucket name for AI artifacts."
  value       = google_storage_bucket.artifacts.name
}

output "artifacts_bucket_url" {
  description = "GCS bucket URL for AI artifacts (gs://...)."
  value       = google_storage_bucket.artifacts.url
}
