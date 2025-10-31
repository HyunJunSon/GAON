// frontend/middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  const publicPaths = ['/login', '/signup'];
  if (publicPaths.some((p) => pathname.startsWith(p))) {
    return NextResponse.next();
  }
  // 정적 파일 무시
  if (/\.(.*)$/.test(pathname)) {
    return NextResponse.next();
  }

  const guard = req.cookies.get('ga_auth')?.value;
  if (!guard) {
    const url = req.nextUrl.clone();
    url.pathname = '/login';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

// /api로 시작하지 않는 모든 경로에 미들웨어를 적용 => Next.js 내부 API 사용 안하면 삭제
export const config = { matcher: ['/((?!api).*)'] };