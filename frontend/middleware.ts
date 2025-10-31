// frontend/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const publicPaths = ['/login', '/signup'];
  const hasAuth = req.cookies.get('ga_auth')?.value;

  // 이미 로그인된 사용자가 /login, /signup에 접근 시 홈으로 redirect
  if (publicPaths.some((p) => pathname.startsWith(p)) && hasAuth) {
    const url = req.nextUrl.clone();
    url.pathname = '/';
    return NextResponse.redirect(url);
  }

  // 공개 경로는 통과
  if (publicPaths.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }
  
  // 정적 파일 무시
  if (/\.(.*)$/.test(pathname)) {
    return NextResponse.next();
  }

  // 보호 라우트 : 비로그인 시 /login 으로
  if (!hasAuth) {
    const url = req.nextUrl.clone();
    url.pathname = '/login';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// /api로 시작하지 않는 모든 경로에 미들웨어를 적용 => Next.js 내부 API 사용 안하면 삭제
export const config = { matcher: ['/((?!api).*)'] };