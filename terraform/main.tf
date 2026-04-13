terraform {
  required_version = ">= 1.6.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  # Remote state in GCS.
  # Bootstrap once before first apply:
  #   gcloud storage buckets create gs://vidshield-tf-state-<project-id> \
  #     --location=us-central1 --uniform-bucket-level-access
  #   gcloud storage buckets update gs://vidshield-tf-state-<project-id> --versioning
  backend "gcs" {
    bucket = "vidshield-tf-state-vidshield-prod" # set per environment
    prefix = "envs/prod"                         # envs/dev | envs/staging | envs/prod
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ── IAM — service accounts & Workload Identity Federation ─────────────────────

module "iam" {
  source = "./modules/iam"

  project_id        = var.project_id
  environment       = var.environment
  github_org        = var.github_org
  github_repo       = var.github_repo
  gar_repository_id = var.gar_repository
}

# ── VPC & Networking ───────────────────────────────────────────────────────────

module "vpc" {
  source = "./modules/vpc"

  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  subnet_cidr           = var.subnet_cidr
  pods_cidr             = var.pods_cidr
  services_cidr         = var.services_cidr
  master_ipv4_cidr      = var.master_ipv4_cidr
  private_services_cidr = var.private_services_cidr
}

# ── Artifact Registry ─────────────────────────────────────────────────────────

module "artifact_registry" {
  source = "./modules/artifact-registry"

  project_id    = var.project_id
  region        = var.region
  environment   = var.environment
  repository_id = var.gar_repository
  deployer_sa   = module.iam.deployer_sa_email
  gke_node_sa   = module.iam.gke_node_sa_email

  depends_on = [module.iam]
}

# ── GKE Cluster ───────────────────────────────────────────────────────────────

module "gke" {
  source = "./modules/gke"

  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  cluster_name        = var.gke_cluster_name
  network_id          = module.vpc.network_id
  subnetwork_id       = module.vpc.subnetwork_id
  pods_range_name     = module.vpc.pods_range_name
  services_range_name = module.vpc.services_range_name
  master_ipv4_cidr    = var.master_ipv4_cidr
  node_machine_type   = var.gke_machine_type
  min_nodes           = var.gke_min_nodes
  max_nodes           = var.gke_max_nodes
  disk_size_gb        = var.gke_disk_size_gb
  gke_node_sa         = module.iam.gke_node_sa_email

  depends_on = [module.vpc, module.iam]
}

# ── Cloud SQL — PostgreSQL 16 ─────────────────────────────────────────────────

module "cloud_sql" {
  source = "./modules/cloud-sql"

  project_id             = var.project_id
  region                 = var.region
  environment            = var.environment
  instance_name          = "${var.project}-pg16-${var.environment}"
  database_version       = "POSTGRES_16"
  tier                   = var.db_tier
  availability_type      = var.environment == "prod" ? "REGIONAL" : "ZONAL"
  disk_size_gb           = var.db_disk_size_gb
  network_id             = module.vpc.network_id
  private_vpc_connection = module.vpc.private_vpc_connection_id
  db_name                = var.db_name
  db_username            = var.db_username
  deletion_protection    = var.environment == "prod" ? true : false
  backup_enabled         = true
  backup_retained_count  = var.environment == "prod" ? 7 : 2

  depends_on = [module.vpc]
}

# ── Cloud Memorystore — Redis 7 ───────────────────────────────────────────────

module "memorystore" {
  source = "./modules/memorystore"

  project_id        = var.project_id
  region            = var.region
  environment       = var.environment
  instance_name     = "${var.project}-redis-${var.environment}"
  tier              = var.redis_tier
  memory_size_gb    = var.redis_memory_size_gb
  network_id        = module.vpc.network_id
  reserved_ip_range = module.vpc.private_services_range_name

  depends_on = [module.vpc]
}

# ── GCS Buckets ───────────────────────────────────────────────────────────────

module "gcs" {
  source = "./modules/gcs"

  project_id    = var.project_id
  region        = var.region
  environment   = var.environment
  project       = var.project
  app_sa_email  = module.iam.app_sa_email
  cors_origins  = var.cors_origins
  force_destroy = var.environment != "prod" ? true : false

  depends_on = [module.iam]
}

# ── Pub/Sub ───────────────────────────────────────────────────────────────────

module "pubsub" {
  source = "./modules/pubsub"

  project_id   = var.project_id
  environment  = var.environment
  project      = var.project
  app_sa_email = module.iam.app_sa_email

  depends_on = [module.iam]
}

# ── Cloud Armor Security Policy ───────────────────────────────────────────────

module "cloud_armor" {
  source = "./modules/cloud-armor"

  project_id    = var.project_id
  environment   = var.environment
  project       = var.project
  ip_rate_limit = var.armor_ip_rate_limit
  enable_owasp  = var.armor_enable_owasp
}

# ── Monitoring ────────────────────────────────────────────────────────────────

module "monitoring" {
  source = "./modules/monitoring"

  project_id         = var.project_id
  environment        = var.environment
  project            = var.project
  region             = var.region
  alert_email        = var.alert_email
  gke_cluster_name   = module.gke.cluster_name
  cloud_sql_instance = module.cloud_sql.instance_name
  redis_instance_id  = module.memorystore.instance_id

  depends_on = [module.gke, module.cloud_sql, module.memorystore]
}
