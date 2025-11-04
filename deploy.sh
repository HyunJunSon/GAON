#!/bin/bash

set -e

echo "🚀 Starting GAON deployment..."

export BACKEND_IMAGE=asia-northeast3-docker.pkg.dev/gaon-477004/gaon-docker-hub/backend:latest
export FRONTEND_IMAGE=asia-northeast3-docker.pkg.dev/gaon-477004/gaon-docker-hub/frontend:latest

docker network create gaon_network 2>/dev/null || true

echo "📦 Pulling latest images..."
docker pull $BACKEND_IMAGE
docker pull $FRONTEND_IMAGE

echo "🛑 Stopping application containers..."
docker-compose -f docker-compose.prod.yml stop gaon_backend gaon_frontend nginx 2>/dev/null || true
docker-compose -f docker-compose.prod.yml rm -f gaon_backend gaon_frontend nginx 2>/dev/null || true

echo "🔄 Starting new containers..."
docker-compose -f docker-compose.prod.yml up -d

echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Deployment completed!"
