#!/bin/bash

set -e

echo "🚀 Starting GAON deployment..."

export BACKEND_IMAGE=asia-northeast3-docker.pkg.dev/gaon-477004/gaon-docker-hub/backend:latest
export FRONTEND_IMAGE=asia-northeast3-docker.pkg.dev/gaon-477004/gaon-docker-hub/frontend:latest

docker network create gaon_network 2>/dev/null || true

echo "📦 Pulling latest images..."
docker pull $BACKEND_IMAGE
docker pull $FRONTEND_IMAGE

echo "🧹 Cleaning up existing containers..."
# 애플리케이션 컨테이너만 강제 제거 (PostgreSQL 제외)
docker rm -f gaon-backend gaon-frontend gaon-nginx 2>/dev/null || true

# Docker Compose로 애플리케이션 컨테이너만 정리
docker-compose -f docker-compose.prod.yml stop gaon_backend gaon_frontend nginx 2>/dev/null || true
docker-compose -f docker-compose.prod.yml rm -f gaon_backend gaon_frontend nginx 2>/dev/null || true

# 시스템 정리 (사용하지 않는 이미지만)
docker image prune -f

echo "⏳ Waiting for cleanup to complete..."
sleep 5

echo "🔄 Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d

echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Deployment completed!"
