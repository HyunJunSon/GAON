terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# GCP 서비스 계정 키에서 project_id 읽기
locals {
  gcp_credentials = jsondecode(file("${path.module}/../backend/gcp_service_account_key.json"))
  project_id      = local.gcp_credentials.project_id
}

provider "google" {
  credentials = file("${path.module}/../backend/gcp_service_account_key.json")
  project     = local.project_id
  region      = var.region
}

# SSH 키 생성
resource "tls_private_key" "gaon_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "private_key" {
  content         = tls_private_key.gaon_key.private_key_pem
  filename        = pathexpand("~/.ssh/gaon_ver2.key")
  file_permission = "0600"
}

resource "local_file" "public_key" {
  content         = tls_private_key.gaon_key.public_key_openssh
  filename        = pathexpand("~/.ssh/gaon_ver2.key.pub")
  file_permission = "0644"
}

# 방화벽 규칙 - HTTP
resource "google_compute_firewall" "gaon_http" {
  name    = "gaon-allow-http"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gaon-backend"]
}

# 방화벽 규칙 - HTTPS
resource "google_compute_firewall" "gaon_https" {
  name    = "gaon-allow-https"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gaon-backend"]
}

# 방화벽 규칙 - Backend API
resource "google_compute_firewall" "gaon_backend_api" {
  name    = "gaon-allow-backend-api"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["8000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gaon-backend"]
}

# 방화벽 규칙 - SSH
resource "google_compute_firewall" "gaon_ssh" {
  name    = "gaon-allow-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["gaon-backend"]
}

# Backend VM
resource "google_compute_instance" "gaon_backend" {
  name         = "gaon-backend-server"
  machine_type = var.machine_type
  zone         = var.zone

  tags = ["gaon-backend"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = var.disk_size
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata = {
    ssh-keys = "ubuntu:${tls_private_key.gaon_key.public_key_openssh}"
  }

  metadata_startup_script = templatefile("${path.module}/startup-backend.sh", {
    db_user     = var.db_user
    db_password = var.db_password
    db_name     = var.db_name
  })

  scheduling {
    preemptible       = false
    automatic_restart = true
  }
}

output "backend_ip" {
  value       = google_compute_instance.gaon_backend.network_interface[0].access_config[0].nat_ip
  description = "Backend server public IP"
}

output "ssh_command" {
  value       = "ssh -i ~/.ssh/gaon_ver2.key ubuntu@${google_compute_instance.gaon_backend.network_interface[0].access_config[0].nat_ip}"
  description = "SSH command to connect to backend server"
}
