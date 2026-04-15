# ── prod.tfvars ────────────────────────────────────────────────────────────────
# Full-scale production configuration.
# Regional Cloud SQL HA, STANDARD_HA Redis, deletion protection, tight alarms.
# terraform apply -var-file=environments/prod.tfvars

project_id  = "vidshield-prod"
project     = "vidshield"
region      = "us-central1"
environment = "prod"

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
gke_cluster_name = "vidshield-gke-prod"
gke_machine_type = "e2-standard-4" # 4 vCPU, 16 GB — production workload size
gke_min_nodes    = 2               # always-on 2 nodes minimum
gke_max_nodes    = 10
gke_disk_size_gb = 100

# ── Artifact Registry ─────────────────────────────────────────────────────────
gar_repository = "vidshield"

# ── Cloud SQL ─────────────────────────────────────────────────────────────────
# availability_type is automatically set to REGIONAL when environment = "prod"
db_tier         = "db-custom-2-4096" # 2 vCPU, 4 GB RAM — upgrade as needed
db_disk_size_gb = 50
db_name         = "vidshield"
db_username     = "vidshield"

# ── Memorystore Redis ─────────────────────────────────────────────────────────
redis_tier           = "STANDARD_HA" # replicated with automatic failover
redis_memory_size_gb = 4

# ── GCS ────────────────────────────────────────────────────────────────────────
cors_origins = [
  "https://vidshield.ai",
  "https://www.vidshield.ai",
  "https://app.vidshield.ai",
]

# ── Cloud Armor ───────────────────────────────────────────────────────────────
armor_ip_rate_limit = 100 # 100 req/min per IP — strict for production
armor_enable_owasp  = true

# ── Monitoring ────────────────────────────────────────────────────────────────
alert_email           = "anu.sasidharan@orionvexa.ca"
api_health_check_host = "api.vidshield.ai"
api_5xx_threshold     = 5 # tight threshold — alert on any spike
