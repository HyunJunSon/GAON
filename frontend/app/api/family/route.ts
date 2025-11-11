// app/api/family/route.ts
import { NextResponse } from 'next/server';

type Member = { id: string; name: string; email: string; joinedAt?: string };

let members: Member[] = [
  { id: 'u1', name: '엄마', email: 'mom@example.com', joinedAt: new Date().toISOString() },
  { id: 'u2', name: '아들', email: 'son@example.com', joinedAt: new Date().toISOString() },
];

export async function GET() {
  return NextResponse.json({ members }, { status: 200 });
}

export async function POST(req: Request) {
  try {
    const { email } = await req.json();
    if (!email || typeof email !== 'string') {
      return NextResponse.json({ ok: false, message: '이메일이 필요합니다.' }, { status: 400 });
    }
    // 중복 체크
    if (members.some(m => m.email === email)) {
      return NextResponse.json({ ok: false, message: '이미 추가된 이메일입니다.' }, { status: 409 });
    }
    const member: Member = {
      id: 'm_' + Math.random().toString(36).slice(2),
      name: email.split('@')[0],
      email,
      joinedAt: new Date().toISOString(),
    };
    members = [member, ...members];
    return NextResponse.json({ ok: true, member }, { status: 200 });
  } catch {
    return NextResponse.json({ ok: false, message: '요청 형식이 올바르지 않습니다.' }, { status: 400 });
  }
}