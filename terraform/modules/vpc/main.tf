locals {
  name_prefix = "${var.project_id}-${var.environment}"
}

# ── VPC Network ────────────────────────────────────────────────────────────────

resource "google_compute_network" "vpc" {
  name                    = "${local.name_prefix}-vpc"
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
  project                 = var.project_id
}

# ── Subnet (GKE nodes + secondary ranges for pods/services) ───────────────────

resource "google_compute_subnetwork" "private" {
  name          = "${local.name_prefix}-subnet"
  region        = var.region
  network       = google_compute_network.vpc.id
  ip_cidr_range = var.subnet_cidr
  project       = var.project_id

  # Required for GKE pods and services to use secondary IP ranges
  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = var.pods_cidr
  }

  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = var.services_cidr
  }

  # Allows VMs in this subnet to reach Google APIs without external IPs
  private_ip_google_access = true
}

# ── Cloud Router + NAT (private GKE nodes need this to reach internet) ─────────

resource "google_compute_router" "router" {
  name    = "${local.name_prefix}-router"
  region  = var.region
  network = google_compute_network.vpc.id
  project = var.project_id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${local.name_prefix}-nat"
  router                             = google_compute_router.router.name
  region                             = var.region
  project                            = var.project_id
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

# ── Private Services Access ───────────────────────────────────────────────────
# Required by Cloud SQL (private IP) and Cloud Memorystore (PRIVATE_SERVICE_ACCESS).

resource "google_compute_global_address" "private_services_range" {
  name          = "${local.name_prefix}-private-svc-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
  address       = split("/", var.private_services_cidr)[0]
  project       = var.project_id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_services_range.name]
}

# ── Firewall Rules ────────────────────────────────────────────────────────────

# Allow internal communication within the VPC (all protocols)
resource "google_compute_firewall" "allow_internal" {
  name    = "${local.name_prefix}-allow-internal"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [var.subnet_cidr, var.pods_cidr, var.services_cidr]
  direction     = "INGRESS"
  priority      = 1000
}

# Allow GKE master to reach nodes (required for webhooks and API server → kubelet)
resource "google_compute_firewall" "allow_master_to_nodes" {
  name    = "${local.name_prefix}-allow-master-nodes"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
    ports    = ["443", "8443", "10250"]
  }

  source_ranges = [var.master_ipv4_cidr]
  target_tags   = ["gke-node"]
  direction     = "INGRESS"
  priority      = 1000
}

# Allow health checks from Google's load balancer probe ranges
resource "google_compute_firewall" "allow_health_checks" {
  name    = "${local.name_prefix}-allow-health-checks"
  network = google_compute_network.vpc.name
  project = var.project_id

  allow {
    protocol = "tcp"
  }

  # GCP load balancer health check ranges
  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
  target_tags   = ["gke-node"]
  direction     = "INGRESS"
  priority      = 1000
}
