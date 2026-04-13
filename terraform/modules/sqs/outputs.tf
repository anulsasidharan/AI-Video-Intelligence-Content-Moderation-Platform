output "video_processing_queue_url" {
  description = "URL of the video processing SQS queue."
  value       = aws_sqs_queue.video_processing.url
}

output "video_processing_queue_arn" {
  description = "ARN of the video processing SQS queue."
  value       = aws_sqs_queue.video_processing.arn
}

output "video_dlq_url" {
  description = "URL of the video processing dead-letter queue."
  value       = aws_sqs_queue.video_dlq.url
}

output "video_dlq_arn" {
  description = "ARN of the video processing dead-letter queue."
  value       = aws_sqs_queue.video_dlq.arn
}

output "moderation_queue_url" {
  description = "URL of the moderation SQS queue."
  value       = aws_sqs_queue.moderation.url
}

output "moderation_queue_arn" {
  description = "ARN of the moderation SQS queue."
  value       = aws_sqs_queue.moderation.arn
}

output "moderation_dlq_arn" {
  description = "ARN of the moderation dead-letter queue."
  value       = aws_sqs_queue.moderation_dlq.arn
}
