# GAON

**가족의 온도** - AI 기반 가족 대화 분석 및 관계 개선 서비스

## 핵심 기능
- 🎙️ **대화 분석**: 음성 파일 업로드 → STT → 화자 분리 → 감정/관계 분석
- 👨‍👩‍👧‍👦 **가족 관리**: 가족 구성원 등록 및 화자 매핑
- 💬 **대화 연습**: AI 기반 대화 시뮬레이션으로 소통 스킬 향상
- 📊 **실시간 피드백**: WebSocket 기반 분석 결과 실시간 제공

## 아키텍처

![GAON Architecture](https://drive.google.com/file/d/1z6AgPhBGHLIPm3oSrTDgwsPQqxgX69AT/view?usp=sharing)

## 기술 스택
- **Frontend**: Next.js 16, React 19, TanStack Query, Zustand
- **Backend**: FastAPI, PostgreSQL + pgvector, LangChain/LangGraph
- **AI/ML**: OpenAI, Google Gemini, Google Cloud Speech (STT), KoNLPy
- **Infrastructure**: Docker, GCP Artifact Registry, OCI

## 프로젝트 구조
```
GAON/
├── frontend/          # Next.js 앱
│   ├── app/          # App Router (페이지)
│   ├── components/   # 재사용 컴포넌트
│   ├── hooks/        # Custom Hooks
│   └── apis/         # API 클라이언트
├── backend/          # FastAPI 앱
│   └── app/
│       ├── domains/  # 도메인별 모듈
│       │   ├── auth/         # 인증
│       │   ├── conversation/ # 대화 분석
│       │   ├── family/       # 가족 관리
│       │   └── practice/     # 대화 연습
│       ├── agent/    # AI 분석 엔진
│       │   ├── Analysis/  # 대화 분석
│       │   ├── Cleaner/   # 전처리
│       │   └── QA/        # 질의응답
│       └── core/     # 공통 설정
└── data/             # 로컬 데이터
```

## 로컬 개발 환경 구축

### Prerequisites
- Node.js 20.11.1
- Python 3.11
- Docker & Docker Compose
- PostgreSQL 17 (또는 Docker 사용)

### 1. 환경 변수 설정

**backend/.env**
```env
# Database
DB_USER=gaon_admin
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=gaon

# JWT
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Keys
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# GCP (STT 사용 시)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
GCP_BUCKET_NAME=your-bucket-name

# CORS
FRONTEND_URL=http://localhost:3000
```

**frontend/.env.local**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2. 데이터베이스 초기화
```bash
# Docker로 PostgreSQL 실행
docker-compose -f docker-compose-db.yml up -d

# 마이그레이션 실행
cd backend
alembic upgrade head
```

### 3. 백엔드 실행
```bash
cd backend
uv venv .venv
source .venv/bin/activate
uv pip install -e .
uvicorn app.main:app --reload --port 8000
```

### 4. 프론트엔드 실행
```bash
cd frontend
nvm use
corepack enable
pnpm install
pnpm dev
```

### 5. 접속
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Docker로 실행
```bash
# 개발 환경
docker-compose up -d

# 운영 환경
docker-compose -f docker-compose.prod.yml up -d
```

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

