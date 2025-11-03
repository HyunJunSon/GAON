# GAON Backend

GAON(가족의온도) 프로젝트입니다.

## ERD (Entity Relationship Diagram)

[ERD Cloud 링크](https://www.erdcloud.com/d/iitcrpXWjTZSgzcdN)

## 설정 방법

이 프로젝트는 설정 값을 `.env` 파일을 통해 관리합니다. 프로젝트 루트 디렉터리에 `.env` 파일을 생성하고, 다음 예시와 같이 필요한 환경 변수들을 정의해주세요:

```env
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432
DB_NAME=your_db_name
SECRET_KEY=your_secret_key
GEMINI_API_KEY=your_gemini_api_key
```

### 설정 사용 방법

애플리케이션 내에서 설정 값을 사용하려면, 다음과 같이 `Settings` 클래스를 import하여 사용합니다:

```python
from app.core.config import settings

# 데이터베이스 설정 사용 예시
db_user = settings.db_user
db_password = settings.db_password

# JWT 설정 사용 예시
secret_key = settings.secret_key
algorithm = settings.algorithm

# LLM 설정 사용 예시
gemini_api_key = settings.gemini_api_key
```

## 데이터베이스 마이그레이션

이 프로젝트는 Alembic을 사용하여 데이터베이스 마이그레이션을 관리합니다.

### 마이그레이션 생성

모델에 변경 사항이 있을 경우, 다음 명령어를 사용하여 새로운 마이그레이션 파일을 생성합니다:

```bash
cd /Users/<username>/Project/GAON/backend && PYTHONPATH=/Users/<username>/Project/GAON/backend 
alembic revision --autogenerate -m "설명"
```

### 마이그레이션 적용

데이터베이스에 변경 사항을 적용하려면 다음 명령어를 실행합니다:

```bash
cd /Users/<username>/Project/GAON/backend && PYTHONPATH=/Users/<username>/Project/GAON/backend 
alembic upgrade head
```

### 마이그레이션 롤백

이전 상태로 롤백하려면 다음 명령어를 사용합니다:

```bash
cd /Users/<username>/Project/GAON/backend && PYTHONPATH=/Users/<username>/Project/GAON/backend 
alembic downgrade -1
```

## 설치 및 실행



## 설치 전 준비

uv가 설치되어 있지 않다면 먼저 설치해주세요:

```bash
pip install uv
```

## 설치 방법 (세 가지 방법 중 하나 선택)

### 방법 1: uv 사용 (권장)

#### 1️⃣ 환경 생성
```bash
uv venv gaon-venv
```

#### 2️⃣ 활성화
```bash
source gaon-venv/bin/activate
```

#### 3️⃣ 설치
```bash
uv sync
```

#### 4️⃣ 확인
```bash
uv run python
```

---

### 방법 2: pip 사용

#### 1️⃣ 가상 환경 생성
```bash
python -m venv gaon-venv
```

#### 2️⃣ 활성화
```bash
source gaon-venv/bin/activate  # Linux/Mac
# 또는
gaon-venv\Scripts\activate     # Windows
```

#### 3️⃣ 설치
```bash
pip install -r requirements.txt
```

---

### 방법 3: conda 사용

#### 1️⃣ conda 환경 생성
```bash
conda create -n gaon-venv python=3.11
```

#### 2️⃣ 환경 활성화
```bash
conda activate gaon-venv
```

#### 3️⃣ 설치
```bash
pip install -r requirements.txt
```

---

**주의**: 위 세 가지 방법 중 하나만 선택하여 사용하세요. 여러 방법을 동시에 사용할 경우 충돌이 발생할 수 있습니다.

## 백엔드 실행 방법

```bash
cd backend
PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

또는 runserver.py를 사용:

```bash
cd backend
PYTHONPATH=. python app/runserver.py
```


서버를 실행합니다:

```bash
python app/runserver.py
```

# RAG (Retrieval Augmented Generation) 시스템

## 개요

RAG 시스템은 문서 로딩, 추출, 청킹, 임베딩, 벡터 DB 저장, 유사도 검색 기능을 통합한 Retrieval Augmented Generation 시스템입니다. 이 시스템은 다양한 문서 형식(PDF, EPUB 등)을 처리하여 벡터 데이터베이스에 저장하고, 자연어 쿼리를 통해 유사한 문서를 검색할 수 있습니다.

## 주요 기능

- **다양한 문서 형식 지원**: PDF, EPUB, TXT, DOCX 등
- **GCP 스토리지 연동**: 클라우드 스토리지에서 문서 자동 가져오기
- **지능형 청킹 전략**: 문서 형식에 맞는 최적화된 청킹
- **OpenAI 임베딩**: 고성능 텍스트 임베딩 생성
- **PostgreSQL 벡터 DB**: pgvector를 사용한 효율적인 벡터 저장 및 검색
- **확장 가능한 아키텍처**: 새로운 문서 형식 및 스토리지 시스템 손쉽게 추가 가능

## 시스템 아키텍처

```
RAG System
├── Loaders (문서 로더)
│   ├── PDFLoader
│   ├── EPUBLoader
│   └── TextLoader
├── Extractors (문서 추출기)
│   ├── PDFExtractor
│   ├── EPUBExtractor
│   └── TextExtractor
├── Chunkers (청킹 전략)
│   ├── RecursiveChunker
│   ├── SentenceChunker
│   └── FormatSpecificChunker
├── Storage Adapters (스토리지 어댑터)
│   ├── GCPStorageAdapter
│   ├── S3StorageAdapter
│   └── LocalStorageAdapter
├── Vector DB Manager (벡터 DB 관리자)
│   ├── PostgreSQL/pgvector 연동
│   └── 임베딩 저장 및 검색
└── Embedding Service (임베딩 서비스)
    └── OpenAI API 연동
```

## 설치 및 설정

### 필수 조건

- Python 3.9+
- PostgreSQL with pgvector extension
- Google Cloud SDK (GCP 사용 시)
- 필요한 Python 패키지 (requirements.txt 참조)

### 설치 방법

```bash
# 가상 환경 생성 및 활성화
python -m venv gaon-venv
source gaon-venv/bin/activate

# 필요한 패키지 설치
pip install -r requirements.txt

# Google Cloud SDK 설치 (GCP 사용 시)
# https://cloud.google.com/sdk/docs/install 참조
```

### 환경 변수 설정

`.env` 파일에 다음 변수들을 설정합니다:

```env
# 데이터베이스 설정
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
DATABASE_URL=postgresql://user:password@host:port/dbname

# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key

# GCP 설정 (GCP 사용 시)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
GCP_BUCKET_NAME=your-gcp-bucket-name

# 기타 설정
EMBEDDING_DIMENSION=1536
```

## 사용 방법

### 1. 기본 사용법

```python
from app.llm.rag import RAGSystem

# RAG 시스템 초기화
rag_system = RAGSystem(
    storage_type="gcp",  # "local", "gcp", "s3" 등
    bucket_name="your-bucket-name"  # GCP 사용 시 필요
)

# 파일 처리
results = rag_system.load_and_process_file("path/to/your/document.pdf")

# 유사도 검색
search_results = rag_system.search_similar("검색하고 싶은 질문")

# 텍스트 직접 추가
new_id = rag_system.add_document("추가할 텍스트 내용")
```

### 2. 스토리지에서 파일 처리

```python
# GCP 스토리지에서 파일 처리
storage_path = "documents/sample.pdf"
results = rag_system.load_and_process_from_storage(storage_path)

# 여러 파일 일괄 처리
file_paths = ["doc1.pdf", "doc2.epub", "doc3.txt"]
results = rag_system.process_multiple_files(file_paths)
```

### 3. 고급 설정

```python
# 청킹 전략 및 파라미터 설정
chunk_kwargs = {
    "chunk_size": 1000,
    "overlap": 100,
    "separator": "\n\n"
}

results = rag_system.load_and_process_file(
    "path/to/document.pdf",
    chunk_kwargs=chunk_kwargs
)

# 유사도 검색 파라미터 조정
search_results = rag_system.search_similar(
    "검색 쿼리",
    top_k=10,      # 반환할 결과 수
    threshold=0.7  # 유사도 임계값
)
```

## 지원하는 문서 형식

| 형식 | 지원 여부 | 특이사항 |
|------|-----------|----------|
| PDF | ✅ | pypdf 필요 |
| EPUB | ✅ | ebooklib, beautifulsoup4 필요 |
| TXT | ✅ | 기본 지원 |
| DOCX | ✅ | python-docx 필요 |
| MD | ✅ | 기본 지원 |



## 로깅

로그 파일은 `logs/rag/rag_system.log`에 저장됩니다.


## 확장 방법

### 1. 새로운 문서 형식 추가

1. `app/llm/rag/extractors/`에 새로운 추출기 클래스 구현
2. `app/llm/rag/loaders/`에 새로운 로더 클래스 구현
3. `app/llm/rag/chunkers/`에 형식별 청킹 전략 구현 (필요 시)

### 2. 새로운 스토리지 시스템 추가

1. `app/llm/rag/storage/storage_adapter.py`에 새로운 어댑터 클래스 구현
2. `StorageAdapterFactory`에 새로운 어댑터 등록

### 3. 새로운 청킹 전략 추가

1. `app/llm/rag/chunkers/chunking_strategies.py`에 새로운 청킹 전략 구현
2. `ChunkerFactory`에 새로운 전략 등록


