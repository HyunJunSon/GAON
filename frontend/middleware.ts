// frontend/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const publicPaths = ['/login', '/signup'];
  const hasAuth = req.cookies.get('ga_auth')?.value;

  // 응답 생성
  let response: NextResponse;

  // 이미 로그인된 사용자가 /login, /signup에 접근 시 홈으로 redirect
  if (publicPaths.some((p) => pathname.startsWith(p)) && hasAuth) {
    const url = req.nextUrl.clone();
    url.pathname = '/';
    response = NextResponse.redirect(url);
  }
  // 공개 경로는 통과
  else if (publicPaths.some((p) => pathname.startsWith(p))) {
    response = NextResponse.next();
  }
  // 정적 파일 무시
  else if (/\.(.*)$/.test(pathname)) {
    response = NextResponse.next();
  }
  // 보호 라우트 : 비로그인 시 /login 으로
  else if (!hasAuth) {
    const url = req.nextUrl.clone();
    url.pathname = '/login';
    response = NextResponse.redirect(url);
  }
  else {
    response = NextResponse.next();
  }

  // CSP 헤더 추가 (오디오 녹음을 위해)
  response.headers.set(
    'Content-Security-Policy',
    "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; font-src 'self' data:; media-src 'self' blob: data: mediastream:; connect-src 'self' https://146.56.43.80:8443; img-src 'self' data: blob:; object-src 'none';"
  );

  return response;
}

// /api로 시작하지 않는 모든 경로에 미들웨어를 적용 => Next.js 내부 API 사용 안하면 삭제
export const config = { matcher: ['/((?!api).*)'] };