# Stage 1: 빌더
FROM python:3.11-slim AS builder

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# 작업 디렉토리 설정
WORKDIR /app

# 패키지 빌드에 필요한 시스템 의존성 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# 가상환경 생성
RUN python -m venv /opt/venv

# 가상환경 활성화
ENV PATH="/opt/venv/bin:$PATH"

# 의존성 파일 복사 (pyproject.toml만 사용)
COPY pyproject.toml ./

# Python 의존성 설치 (pyproject.toml 사용)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Stage 2: 최종 이미지
FROM python:3.11-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

# 작업 디렉토리 설정
WORKDIR /app

# 런타임 의존성 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        curl && \
    rm -rf /var/lib/apt/lists/*

# 보안을 위한 비루트 사용자 생성
RUN adduser --disabled-password --gecos "" gaon-admin

# 빌더 스테이지에서 가상환경 복사
COPY --from=builder /opt/venv /opt/venv

# 프로젝트 소스 코드 복사
COPY . /app/

# 앱 디렉토리 소유권 변경
RUN chown -R gaon-admin:gaon-admin /app

# 비루트 사용자로 전환
USER gaon-admin

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
