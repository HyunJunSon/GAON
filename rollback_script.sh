#!/bin/bash

# 롤백할 이미지 ID 설정
BACKEND_ROLLBACK_IMAGE="4091de41549e"
FRONTEND_ROLLBACK_IMAGE="9ec397a4b311"

echo "🔄 Starting rollback to previous stable images..."
echo "Backend: $BACKEND_ROLLBACK_IMAGE"
echo "Frontend: $FRONTEND_ROLLBACK_IMAGE"

# 현재 컨테이너 중지
echo "⏹️ Stopping current containers..."
docker-compose -f docker-compose.prod.yml down || true

# 이전 이미지에 태그 생성
echo "🏷️ Tagging rollback images..."
docker tag $BACKEND_ROLLBACK_IMAGE gaon:back-server
docker tag $FRONTEND_ROLLBACK_IMAGE gaon:front-server

# 환경 변수 설정
export BACKEND_IMAGE=gaon:back-server
export FRONTEND_IMAGE=gaon:front-server

# PostgreSQL 확인 및 시작
echo "🗄️ Ensuring PostgreSQL is running..."
if ! docker ps | grep -q gaon-postgres; then
    docker-compose -f docker-compose-db.yml up -d
    sleep 10
fi

# 롤백된 이미지로 서비스 시작
echo "🚀 Starting services with rollback images..."
docker-compose -f docker-compose.prod.yml up -d

# 서비스 시작 대기
echo "⏳ Waiting for services to start..."
sleep 30

# 헬스체크
echo "🏥 Performing health check..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health; then
        echo "✅ Backend rollback successful!"
        break
    fi
    echo "⏳ Waiting for backend... ($i/30)"
    sleep 2
done

echo "✅ Rollback completed!"
echo "📋 Current running containers:"
docker ps | grep gaon
