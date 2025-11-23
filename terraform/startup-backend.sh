#!/bin/bash
set -e

echo "🚀 Starting GAON server setup..."

# 시스템 업데이트
apt-get update
apt-get upgrade -y

# Docker 설치
apt-get install -y ca-certificates curl gnupg lsb-release
mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Docker 서비스 시작
systemctl start docker
systemctl enable docker

# ubuntu 사용자를 docker 그룹에 추가
usermod -aG docker ubuntu

# GCP 인증 설정
gcloud auth configure-docker asia-northeast3-docker.pkg.dev --quiet

# 프로젝트 디렉토리 생성
mkdir -p /home/ubuntu/gaon
cd /home/ubuntu/gaon

# .env 파일 생성
cat > .env << EOF
DB_USER=${db_user}
DB_PASSWORD=${db_password}
DB_NAME=${db_name}
EOF

# docker-compose.prod.yml 다운로드 (GitHub에서)
curl -o docker-compose.prod.yml https://raw.githubusercontent.com/HyunJunSon/GAON/main/docker-compose.prod.yml

# nginx 설정 다운로드
curl -o nginx.conf https://raw.githubusercontent.com/HyunJunSon/GAON/main/nginx.conf

# Docker 이미지 pull 및 실행
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# 권한 설정
chown -R ubuntu:ubuntu /home/ubuntu/gaon

echo "✅ Setup completed successfully!"
