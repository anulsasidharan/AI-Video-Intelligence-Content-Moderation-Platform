# ── dev.tfvars ─────────────────────────────────────────────────────────────────
# Cost-optimised single-zone dev environment.
# terraform apply -var-file=environments/dev.tfvars

project_id  = "vidshield-dev"
project     = "vidshield"
region      = "us-central1"
environment = "dev"

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
gke_cluster_name = "vidshield-gke-dev"
gke_machine_type = "e2-standard-2" # 2 vCPU, 8 GB — minimum viable for dev
gke_min_nodes    = 1
gke_max_nodes    = 3
gke_disk_size_gb = 50

# ── Artifact Registry ─────────────────────────────────────────────────────────
gar_repository = "vidshield"

# ── Cloud SQL ─────────────────────────────────────────────────────────────────
db_tier         = "db-f1-micro" # cheapest tier for dev
db_disk_size_gb = 10
db_name         = "vidshield"
db_username     = "vidshield"

# ── Memorystore Redis ─────────────────────────────────────────────────────────
redis_tier           = "BASIC"
redis_memory_size_gb = 1

# ── GCS ────────────────────────────────────────────────────────────────────────
cors_origins = ["http://localhost:3000", "http://localhost:3001"]

# ── Cloud Armor ───────────────────────────────────────────────────────────────
armor_ip_rate_limit = 300 # more lenient in dev for testing
armor_enable_owasp  = true

# ── Monitoring ────────────────────────────────────────────────────────────────
alert_email = "" # set your email here to receive dev alerts
