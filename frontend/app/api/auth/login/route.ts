// frontend/app/api/auth/login/route.ts
import { NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export async function POST(req: Request) {
  try {
    const body = await req.formData();
    
    // 백엔드로 프록시
    const response = await fetch(`${BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      body: body,
    });

    const data = await response.json();

    if (response.ok) {
      // 성공 시 토큰을 쿠키에 저장
      const res = NextResponse.json(data, { status: 200 });
      res.cookies.set({
        name: 'ga_token',
        value: data.access_token,
        path: '/',
        httpOnly: false,
        sameSite: 'lax',
        maxAge: 60 * 60 * 24, // 1일
      });
      return res;
    } else {
      return NextResponse.json(data, { status: response.status });
    }
  } catch (error) {
    console.error('Login proxy error:', error);
    return NextResponse.json(
      { message: '서버 연결 오류가 발생했습니다.' },
      { status: 500 }
    );
  }
}