# GAON

AI 기반 문서 분석 및 대화형 서비스

## 기술 스택
- **Frontend**: Next.js 16, React 19, TanStack Query
- **Backend**: FastAPI, PostgreSQL, LangChain
- **Infrastructure**: Docker, GCP Artifact Registry, OCI

## CI/CD 파이프라인

### 자동 배포 트리거
- **main** 브랜치 push → 운영 환경 배포
- **develop** 브랜치 push → 개발 환경 배포

### 배포 프로세스
1. **변경 감지**: backend/frontend 파일 변경 시에만 해당 이미지 빌드
2. **Docker 빌드**: 자동 이미지 빌드 및 GCP Artifact Registry 업로드
3. **무중단 배포**: OCI 서버에 롤링 업데이트 방식으로 배포
4. **헬스체크**: 배포 후 서비스 정상 동작 확인
5. **자동 롤백**: 실패 시 이전 버전으로 자동 복구

### 배포 환경
- **Container Registry**: GCP Artifact Registry
- **Deployment Server**: OCI (Oracle Cloud Infrastructure)
- **Container Names**: `gaon:back-server`, `gaon:front-server`
- **Orchestration**: Docker Compose

### 필요한 Secrets 설정
```
GCP_SA_KEY          # GCP 서비스 계정 키 (JSON)
GCP_PROJECT_ID      # GCP 프로젝트 ID
OCI_HOST           # 배포 서버 IP
OCI_USERNAME       # SSH 사용자명
OCI_SSH_KEY        # SSH 개인키
OCI_PORT           # SSH 포트
```

### 로컬 개발
```bash
# 개발 환경 실행
docker-compose up -d

# 운영 환경 테스트
docker-compose -f docker-compose.prod.yml up -d
```

# Deploy with login fixes Fri Nov  7 11:03:10 KST 2025
# Force CI/CD trigger Fri Nov  7 13:39:36 KST 2025
