output "video_uploaded_topic_id" {
  description = "Pub/Sub topic ID for video upload events."
  value       = google_pubsub_topic.topics["video-uploaded"].id
}

output "video_processed_topic_id" {
  description = "Pub/Sub topic ID for video processing completion events."
  value       = google_pubsub_topic.topics["video-processed"].id
}

output "moderation_alerts_topic_id" {
  description = "Pub/Sub topic ID for moderation alert events."
  value       = google_pubsub_topic.topics["moderation-alerts"].id
}

output "stream_events_topic_id" {
  description = "Pub/Sub topic ID for live stream events."
  value       = google_pubsub_topic.topics["stream-events"].id
}

output "analytics_events_topic_id" {
  description = "Pub/Sub topic ID for analytics events."
  value       = google_pubsub_topic.topics["analytics-events"].id
}

output "video_uploaded_subscription_id" {
  description = "Pub/Sub subscription ID for video upload events."
  value       = google_pubsub_subscription.subscriptions["video-uploaded"].id
}

output "moderation_alerts_subscription_id" {
  description = "Pub/Sub subscription ID for moderation alerts."
  value       = google_pubsub_subscription.subscriptions["moderation-alerts"].id
}

output "all_topic_ids" {
  description = "Map of topic name → topic ID for all VidShield Pub/Sub topics."
  value       = { for k, v in google_pubsub_topic.topics : k => v.id }
}
