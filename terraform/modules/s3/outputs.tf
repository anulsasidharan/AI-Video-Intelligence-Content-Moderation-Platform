output "videos_bucket_id" {
  description = "Videos S3 bucket name."
  value       = aws_s3_bucket.videos.id
}

output "videos_bucket_arn" {
  description = "Videos S3 bucket ARN."
  value       = aws_s3_bucket.videos.arn
}

output "thumbnails_bucket_id" {
  description = "Thumbnails S3 bucket name."
  value       = aws_s3_bucket.thumbnails.id
}

output "thumbnails_bucket_arn" {
  description = "Thumbnails S3 bucket ARN."
  value       = aws_s3_bucket.thumbnails.arn
}

output "artifacts_bucket_id" {
  description = "Artifacts S3 bucket name."
  value       = aws_s3_bucket.artifacts.id
}

output "artifacts_bucket_arn" {
  description = "Artifacts S3 bucket ARN."
  value       = aws_s3_bucket.artifacts.arn
}
