// frontend/app/api/auth/login/route.ts
import { NextResponse } from 'next/server';

type LoginBody = { email: string; password: string };

// 데모용 고정 유저/비번 (프론트 확인용 하드코딩)
const VALID_EMAIL = 'user@example.com';
const VALID_PASSWORD = 'P@ssw0rd!';

export async function POST(req: Request) {
  const body = (await req.json()) as LoginBody;

  if (body.email === VALID_EMAIL && body.password === VALID_PASSWORD) {
    // 액세스 토큰 목업
    const token = 'mock-token-abc123';

    // 쿠키에 보관 (middleware가 읽도록)
    // - httpOnly를 true로 해도 되지만, 클라이언트 JS에서 지우려면 false가 편함(목업)
    const res = NextResponse.json(
      {
        accessToken: token,
        user: { id: 'u_123', name: '홍길동', email: VALID_EMAIL },
      },
      { status: 200 }
    );
    res.cookies.set({
      name: 'ga_token',
      value: token,
      path: '/',
      httpOnly: false, // 실제 서비스 전환 시 true 권장
      sameSite: 'lax',
      maxAge: 60 * 60 * 24, // 1일
    });
    return res;
  }

  return NextResponse.json(
    { message: '이메일 또는 비밀번호가 올바르지 않습니다.' },
    { status: 401 }
  );
}