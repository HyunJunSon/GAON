#!/bin/bash

set -e

echo "🚀 Starting GAON deployment..."

export BACKEND_IMAGE=asia-northeast3-docker.pkg.dev/gaon-477004/gaon-docker-hub/backend:latest
export FRONTEND_IMAGE=asia-northeast3-docker.pkg.dev/gaon-477004/gaon-docker-hub/frontend:latest

docker network create gaon_network 2>/dev/null || true

echo "📦 Pulling latest images..."
docker pull $BACKEND_IMAGE
docker pull $FRONTEND_IMAGE

echo "🧹 Cleaning up existing containers (DB 제외)..."
# DB 제외하고 다른 컨테이너만 제거
docker rm -f gaon-backend gaon-frontend gaon-nginx 2>/dev/null || true

# Docker Compose로 정리 (DB 제외)
docker-compose -f docker-compose.prod.yml stop gaon_backend gaon_frontend nginx 2>/dev/null || true
docker-compose -f docker-compose.prod.yml rm -f gaon_backend gaon_frontend nginx 2>/dev/null || true

echo "⏳ Waiting for cleanup to complete..."
sleep 3

echo "🔄 Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d --remove-orphans

echo "⏳ Waiting for services to start..."
sleep 10

echo "🔄 Applying database migrations..."
docker exec -w /app gaon-backend alembic upgrade head || {
    echo "🚨 Error detected! Rolling back..."
    docker-compose -f docker-compose.prod.yml stop gaon_backend gaon_frontend nginx
    exit 1
}

echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Deployment completed!"
