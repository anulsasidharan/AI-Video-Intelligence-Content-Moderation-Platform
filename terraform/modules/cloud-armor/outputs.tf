output "policy_name" {
  description = "Cloud Armor security policy name."
  value       = google_compute_security_policy.policy.name
}

output "policy_self_link" {
  description = "Cloud Armor security policy self-link — reference this in BackendConfig annotations."
  value       = google_compute_security_policy.policy.self_link
}

output "policy_id" {
  description = "Cloud Armor security policy ID."
  value       = google_compute_security_policy.policy.id
}
