// frontend/app/api/auth/me/route.ts
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';

export async function GET() {
  const token = (await cookies()).get('ga_token')?.value;

  if (!token) {
    return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
  }

  // 토큰 검증은 생략(목업). 항상 같은 유저 리턴
  return NextResponse.json(
    { id: 'u_123', name: '홍길동', email: 'user@example.com' },
    { status: 200 }
  );
}