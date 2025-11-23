# 기존 GCP 리소스 Import 가이드

기존에 생성된 GCP 리소스를 Terraform으로 관리하기 위해 import합니다.

## Import 명령어

```bash
# 1. Storage Bucket
terraform import google_storage_bucket.gaon_data gaon-cloud-data

# 2. Artifact Registry
terraform import google_artifact_registry_repository.gaon_docker projects/gaon-477004/locations/asia-northeast3/repositories/gaon-docker-hub

# 3. Pub/Sub Topic
terraform import google_pubsub_topic.gcs_rag_notifications projects/gaon-477004/topics/gcs-rag-notifications

# 4. Cloud Function - RAG Processor
terraform import google_cloudfunctions2_function.rag_processor projects/gaon-477004/locations/asia-northeast3/functions/rag-processor

# 5. Cloud Function - TOC Processor
terraform import google_cloudfunctions2_function.toc_pdf_processor projects/gaon-477004/locations/asia-northeast3/functions/toc-pdf-processor
```

## Import 순서

1. **먼저 plan 실행**
   ```bash
   terraform plan
   ```

2. **리소스가 생성되려고 하면 import**
   ```bash
   # 위의 import 명령어 실행
   ```

3. **다시 plan으로 확인**
   ```bash
   terraform plan
   # No changes 또는 최소한의 변경만 있어야 함
   ```

## 주의사항

- Cloud Functions의 소스 코드는 별도로 관리됩니다
- Import 후에도 소스 코드 배포는 기존 방식 유지
- Terraform은 인프라 구조만 관리합니다

## 선택적 관리

모든 리소스를 Terraform으로 관리하지 않아도 됩니다:

- **Terraform 관리 권장**: VM, 방화벽, Storage Bucket, Artifact Registry
- **수동 관리 가능**: Cloud Functions (코드 변경이 잦은 경우)

수동 관리를 원하면 `gcp_resources.tf`에서 해당 리소스를 주석 처리하세요.
