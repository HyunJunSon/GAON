# GAON

AI 기반 문서 분석 및 대화형 서비스

## 기술 스택
- **Frontend**: Next.js 16, React 19, TanStack Query
- **Backend**: FastAPI, PostgreSQL, LangChain
- **Infrastructure**: Docker, GCP Artifact Registry, OCI

## 배포
- **CI/CD**: Gitea Actions
- **Container Registry**: GCP Artifact Registry
- **Deployment**: OCI Server (Docker Compose)

### 배포 프로세스
1. `feature/#39_CICD_pipeline` 브랜치에 push
2. 자동 Docker 이미지 빌드 및 GCP Registry 업로드
3. OCI 서버에 무중단 배포 (롤링 업데이트)
4. 실패 시 자동 롤백
