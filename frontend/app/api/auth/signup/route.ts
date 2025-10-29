// frontend/app/api/auth/signup/route.ts
import { NextResponse } from 'next/server';

type SignupBody = { name: string; email: string; password: string };

// 이미 존재하는 이메일 에러를 흉내내기 위한 고정값
const DUP_EMAIL = 'user@example.com';

export async function POST(req: Request) {
  const body = (await req.json()) as SignupBody;

  // 아주 단순한 중복 체크 목업
  if (body.email === DUP_EMAIL) {
    return NextResponse.json(
      { message: '이미 가입된 이메일입니다.' },
      { status: 409 }
    );
  }

  // 실제 서비스라면 여기서 사용자 저장 후 201 반환
  return NextResponse.json(
    {
      message: '가입 성공. 로그인 페이지로 이동합니다.',
      user: { id: 'u_999', name: body.name, email: body.email },
    },
    { status: 201 }
  );
}