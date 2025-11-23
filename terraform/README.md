# GAON GCP Infrastructure

Terraform으로 GCP 인프라를 프로비저닝합니다.

## 관리되는 리소스

### 컴퓨팅
- **VM 인스턴스**: gaon-backend-server (e2-medium)
- **방화벽 규칙**: HTTP (80), HTTPS (443), Backend API (8000), SSH (22)

### 스토리지 & 레지스트리
- **Cloud Storage**: gaon-cloud-data (ASIA)
- **Artifact Registry**: gaon-docker-hub (Docker)

### 서버리스
- **Cloud Functions**:
  - rag-processor (Python 3.11)
  - toc-pdf-processor (Python 3.11)
- **Pub/Sub**: gcs-rag-notifications

### 기타
- **SSH 키**: `~/.ssh/gaon_ver2.key`

## 사전 요구사항

- Terraform 설치
- GCP 서비스 계정 키: `backend/gcp_service_account_key.json`

## 사용 방법

### 1. 초기화

```bash
cd terraform
terraform init
```

### 2. DB 설정 로드 (backend/.env 사용)

```bash
# Python config에서 DB 설정 읽기
eval $(python3 get_db_config.py)
```

### 3. 기존 리소스 Import (최초 1회만)

기존에 생성된 리소스를 Terraform으로 관리하려면:

```bash
# IMPORT.md 파일 참조
terraform import google_storage_bucket.gaon_data gaon-cloud-data
terraform import google_artifact_registry_repository.gaon_docker projects/gaon-477004/locations/asia-northeast3/repositories/gaon-docker-hub
# ... (나머지는 IMPORT.md 참조)
```

### 3. 계획 확인

```bash
terraform plan
```

### 4. 인프라 생성/업데이트

```bash
terraform apply
```

### 5. SSH 접속

```bash
# Output에서 SSH 명령어 확인
terraform output ssh_command

# 또는 직접 접속
ssh -i ~/.ssh/gaon_ver2.key ubuntu@<BACKEND_IP>
```

### 6. 인프라 삭제

```bash
terraform destroy
```

## 설정 변경

`terraform.tfvars` 파일에서 설정을 변경할 수 있습니다:

```hcl
region       = "asia-northeast3"
zone         = "asia-northeast3-a"
machine_type = "e2-medium"
disk_size    = 30
```

## Outputs

- `backend_ip`: 백엔드 서버 공인 IP
- `ssh_command`: SSH 접속 명령어
- `bucket_name`: GCS 버킷 이름
- `artifact_registry`: Artifact Registry 이름
- `rag_processor_url`: RAG 프로세서 URL
- `toc_processor_url`: TOC 프로세서 URL

## 파일 구조

```
terraform/
├── main.tf              # VM, 방화벽, SSH 키
├── gcp_resources.tf     # Storage, Functions, Pub/Sub
├── variables.tf         # 변수 정의
├── terraform.tfvars     # 변수 값
├── startup-backend.sh   # VM 초기 설정
├── README.md           # 이 파일
└── IMPORT.md           # Import 가이드
```

## 주의사항

- Cloud Functions 소스 코드는 별도 배포 필요
- Terraform은 인프라 구조만 관리
- 민감정보는 `.env` 파일로 관리 (Git 제외)
