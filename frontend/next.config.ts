import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  async rewrites() {
    // 개발환경에서만 백엔드로 프록시
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
        {
          source: '/health',
          destination: 'http://localhost:8000/health',
        }
      ];
    }
    return [];
  }
};

export default nextConfig;
