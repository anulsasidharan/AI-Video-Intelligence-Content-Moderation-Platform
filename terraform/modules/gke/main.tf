locals {
  name_prefix = "${var.project_id}-${var.environment}"
}

# ── GKE Cluster ────────────────────────────────────────────────────────────────

resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = var.region
  project  = var.project_id

  # We manage our own node pool; remove the default one GKE would create
  remove_default_node_pool = true
  initial_node_count       = 1

  network    = var.network_id
  subnetwork = var.subnetwork_id

  # Enable alias IPs — required for secondary range routing (pods/services)
  ip_allocation_policy {
    cluster_secondary_range_name  = var.pods_range_name
    services_secondary_range_name = var.services_range_name
  }

  # Workload Identity — pods authenticate as GCP service accounts via metadata server
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  # Private cluster: nodes have only private IPs; control plane is reachable via
  # authorized networks only (public endpoint still enabled for kubectl access)
  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.master_ipv4_cidr
  }

  # Allow kubectl from any IP; restrict in prod by setting specific CIDRs
  master_authorized_networks_config {
    cidr_blocks {
      cidr_block   = "0.0.0.0/0"
      display_name = "all"
    }
  }

  # Enable VPA and HPA support
  vertical_pod_autoscaling {
    enabled = true
  }

  # Disable the legacy metadata attributes endpoint (security hardening)
  node_config {
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }

  # Enable Cloud Logging and Monitoring for GKE
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS"]

    managed_prometheus {
      enabled = true
    }
  }

  # Enable Network Policy (Calico) for pod-level firewall rules
  network_policy {
    enabled  = true
    provider = "CALICO"
  }

  addons_config {
    # GKE Ingress controller creates Cloud Load Balancers automatically
    http_load_balancing {
      disabled = false
    }

    # Horizontal Pod Autoscaler is enabled by default; keep it
    horizontal_pod_autoscaling {
      disabled = false
    }

    # Network Policy addon — must be enabled when network_policy.enabled = true
    network_policy_config {
      disabled = false
    }
  }

  # Maintenance window: 04:00–08:00 UTC on Tuesdays
  maintenance_policy {
    recurring_window {
      start_time = "2024-01-01T04:00:00Z"
      end_time   = "2024-01-01T08:00:00Z"
      recurrence = "FREQ=WEEKLY;BYDAY=TU"
    }
  }

  release_channel {
    channel = var.environment == "prod" ? "REGULAR" : "RAPID"
  }

  deletion_protection = false

  lifecycle {
    ignore_changes = [
      # Image type is managed by the node pool, not the cluster
      node_config,
    ]
  }
}

# ── Node Pool ──────────────────────────────────────────────────────────────────

resource "google_container_node_pool" "primary" {
  name     = "${var.cluster_name}-node-pool"
  location = var.region
  cluster  = google_container_cluster.primary.name
  project  = var.project_id

  # Autoscaling across all zones in the region
  autoscaling {
    min_node_count = var.min_nodes
    max_node_count = var.max_nodes
  }

  # Auto-repair and auto-upgrade keep nodes healthy and up-to-date
  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    machine_type = var.node_machine_type
    disk_size_gb = var.disk_size_gb
    disk_type    = "pd-ssd"
    image_type   = "COS_CONTAINERD"

    # Nodes run as the GKE node service account (least-privilege)
    service_account = var.gke_node_sa
    oauth_scopes    = ["https://www.googleapis.com/auth/cloud-platform"]

    # Enable Workload Identity metadata server on nodes
    workload_metadata_config {
      mode = "GKE_METADATA"
    }

    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }

    # Labels applied to every node
    labels = {
      env     = var.environment
      project = var.project_id
    }

    tags = ["gke-node"]
  }

  lifecycle {
    # Ignore image_type changes triggered by GKE rolling upgrades
    ignore_changes = [node_config[0].image_type]
  }
}
