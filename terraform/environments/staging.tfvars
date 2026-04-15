# ── staging.tfvars ─────────────────────────────────────────────────────────────
# Production-like staging environment with smaller instances.
# terraform apply -var-file=environments/staging.tfvars

project_id  = "vidshield-staging"
project     = "vidshield"
region      = "us-central1"
environment = "staging"

# GitHub — used to configure Workload Identity Federation
github_org  = "your-github-org" # replace with your GitHub org/user
github_repo = "vidshield-ai"

# ── VPC ────────────────────────────────────────────────────────────────────────
subnet_cidr           = "10.0.0.0/20"
pods_cidr             = "10.48.0.0/14"
services_cidr         = "10.52.0.0/20"
master_ipv4_cidr      = "172.16.0.0/28"
private_services_cidr = "10.64.0.0/16"

# ── GKE ────────────────────────────────────────────────────────────────────────
gke_cluster_name = "vidshield-gke-staging"
gke_machine_type = "e2-standard-2"
gke_min_nodes    = 1
gke_max_nodes    = 5
gke_disk_size_gb = 50

# ── Artifact Registry ─────────────────────────────────────────────────────────
gar_repository = "vidshield"

# ── Cloud SQL ─────────────────────────────────────────────────────────────────
db_tier         = "db-g1-small"
db_disk_size_gb = 20
db_name         = "vidshield"
db_username     = "vidshield"

# ── Memorystore Redis ─────────────────────────────────────────────────────────
redis_tier           = "BASIC"
redis_memory_size_gb = 2

# ── GCS ────────────────────────────────────────────────────────────────────────
cors_origins = [
  "https://staging.vidshield.ai",
  "https://app.staging.vidshield.ai",
  "http://localhost:3000",
]

# ── Cloud Armor ───────────────────────────────────────────────────────────────
armor_ip_rate_limit = 200
armor_enable_owasp  = true

# ── Monitoring ────────────────────────────────────────────────────────────────
alert_email           = "platform-alerts@yourcompany.com" # replace with real email
api_health_check_host = "api.staging.vidshield.ai"        # replace with real domain
api_5xx_threshold     = 20
