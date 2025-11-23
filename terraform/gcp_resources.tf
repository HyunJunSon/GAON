# GCP Storage Bucket
resource "google_storage_bucket" "gaon_data" {
  name          = "gaon-cloud-data"
  location      = "ASIA"
  force_destroy = false  # 버킷에 파일이 있으면 삭제 불가

  uniform_bucket_level_access = true

  versioning {
    enabled = true  # 파일 버전 관리 활성화
  }

  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }

  lifecycle {
    prevent_destroy = true  # terraform destroy 시 삭제 방지
  }
}

# Artifact Registry - Docker
resource "google_artifact_registry_repository" "gaon_docker" {
  location      = "asia-northeast3"
  repository_id = "gaon-docker-hub"
  description   = "GAON Docker images repository"
  format        = "DOCKER"

  lifecycle {
    prevent_destroy = true  # 삭제 방지
  }
}

# Pub/Sub Topic for Cloud Functions
resource "google_pubsub_topic" "gcs_rag_notifications" {
  name = "gcs-rag-notifications"
}

# Cloud Storage notification to Pub/Sub
resource "google_storage_notification" "rag_notification" {
  bucket         = google_storage_bucket.gaon_data.name
  payload_format = "JSON_API_V1"
  topic          = google_pubsub_topic.gcs_rag_notifications.id
  event_types    = ["OBJECT_FINALIZE"]

  depends_on = [google_pubsub_topic_iam_member.gcs_publisher]
}

# IAM for GCS to publish to Pub/Sub
data "google_storage_project_service_account" "gcs_account" {
}

resource "google_pubsub_topic_iam_member" "gcs_publisher" {
  topic  = google_pubsub_topic.gcs_rag_notifications.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}

# Cloud Function - RAG Processor (나중에 추가)
# resource "google_cloudfunctions2_function" "rag_processor" {
#   name        = "rag-processor"
#   location    = "asia-northeast3"
#   description = "RAG file processor triggered by GCS uploads"

#   build_config {
#     runtime     = "python311"
#     entry_point = "rag_file_processor"
#     source {
#       storage_source {
#         bucket = "gcf-v2-sources-${data.google_project.project.number}-asia-northeast3"
#         object = "rag-processor/function-source.zip"
#       }
#     }
#   }

#   service_config {
#     max_instance_count = 10
#     available_memory   = "512M"
#     timeout_seconds    = 540
#     environment_variables = {
#       GCP_PROJECT_ID = local.project_id
#       BUCKET_NAME    = google_storage_bucket.gaon_data.name
#     }
#   }

#   event_trigger {
#     trigger_region        = "asia-northeast3"
#     event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
#     pubsub_topic          = google_pubsub_topic.gcs_rag_notifications.id
#     retry_policy          = "RETRY_POLICY_DO_NOT_RETRY"
#     service_account_email = data.google_compute_default_service_account.default.email
#   }
# }

# Cloud Function - TOC PDF Processor (나중에 추가)
# resource "google_cloudfunctions2_function" "toc_pdf_processor" {
#   name        = "toc-pdf-processor"
#   location    = "asia-northeast3"
#   description = "TOC PDF processor"

#   build_config {
#     runtime     = "python311"
#     entry_point = "toc_pdf_processor"
#     source {
#       storage_source {
#         bucket = "gcf-v2-sources-${data.google_project.project.number}-asia-northeast3"
#         object = "toc-pdf-processor/function-source.zip"
#       }
#     }
#   }

#   service_config {
#     max_instance_count = 10
#     available_memory   = "512M"
#     timeout_seconds    = 540
#     environment_variables = {
#       GCP_PROJECT_ID = local.project_id
#     }
#   }

#   event_trigger {
#     trigger_region        = "asia-northeast3"
#     event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
#     pubsub_topic          = google_pubsub_topic.gcs_rag_notifications.id
#     retry_policy          = "RETRY_POLICY_DO_NOT_RETRY"
#     service_account_email = data.google_compute_default_service_account.default.email
#   }
# }

# Data sources
data "google_project" "project" {
  project_id = local.project_id
}

# data "google_compute_default_service_account" "default" {
# }

# Outputs
output "bucket_name" {
  value       = google_storage_bucket.gaon_data.name
  description = "GCS bucket name"
}

output "artifact_registry" {
  value       = google_artifact_registry_repository.gaon_docker.name
  description = "Artifact Registry repository name"
}

# output "rag_processor_url" {
#   value       = google_cloudfunctions2_function.rag_processor.service_config[0].uri
#   description = "RAG processor function URL"
# }

# output "toc_processor_url" {
#   value       = google_cloudfunctions2_function.toc_pdf_processor.service_config[0].uri
#   description = "TOC processor function URL"
# }
