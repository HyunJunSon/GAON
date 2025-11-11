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
# 모든 gaon 관련 컨테이너 강제 제거
docker rm -f gaon-backend gaon-frontend gaon-nginx gaon-postgres 2>/dev/null || true
docker rm -f $(docker ps -aq --filter "name=gaon") 2>/dev/null || true

# Docker Compose로 정리
docker-compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

# 시스템 정리
docker system prune -f

echo "⏳ Waiting for cleanup to complete..."
sleep 5

echo "🔄 Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d --remove-orphans

echo "⏳ Waiting for services to start..."
sleep 10

echo "🔄 Applying database migrations..."
docker exec gaon-backend alembic upgrade head || {
    echo "🚨 Error detected! Rolling back..."
    docker-compose -f docker-compose.prod.yml down
    exit 1
}

echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Deployment completed!"
