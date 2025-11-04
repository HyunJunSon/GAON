# Stage 1: 의존성 설치
FROM node:20-alpine AS deps

WORKDIR /app

# pnpm 설치
RUN npm install -g pnpm

# 의존성 파일 복사
COPY package.json pnpm-lock.yaml ./

# 의존성 설치
RUN pnpm install --frozen-lockfile

# Stage 2: 앱 빌드
FROM node:20-alpine AS builder

WORKDIR /app

# pnpm 설치
RUN npm install -g pnpm

# 의존성과 소스 코드 복사
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 앱 빌드
RUN pnpm build

# Stage 3: 앱 실행
FROM node:20-alpine AS runner

WORKDIR /app

# 비루트 사용자 생성
RUN addgroup -g 1001 -S nodejs && \
    adduser -S gaon-admin -u 1001

# 프로덕션 환경 설정
ENV NODE_ENV=production

# 빌드된 파일 복사 (public 폴더가 있는 경우만)
COPY --from=builder --chown=gaon-admin:nodejs /app/.next/standalone ./ 
COPY --from=builder --chown=gaon-admin:nodejs /app/.next/static ./.next/static

# 비루트 사용자로 전환
USER gaon-admin

# 포트 노출
EXPOSE 3000

# 애플리케이션 실행
CMD ["node", "server.js"]
