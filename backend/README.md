# GAON Backend

GAON(가족의온도) 프로젝트입니다.

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


## LangSmith 모니터링 설정

### 환경 변수 설정
`.env` 파일에 다음 설정을 추가하세요:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=Gaon
```

### LangSmith API 키 발급
1. https://smith.langchain.com 접속
2. 계정 생성 후 로그인
3. Settings > API Keys에서 새 API 키 생성
4. 생성된 키를 `.env` 파일에 추가

### 모니터링 확인
- 모든 LangChain 작업이 자동으로 추적됨
- LangSmith 대시보드에서 실시간 모니터링 가능
- 프로젝트명: "Gaon"

### 테스트 실행
```bash
cd backend
python -m app.tests.test_langsmith
```
