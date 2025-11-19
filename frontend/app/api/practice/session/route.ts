// app/api/practice/session/route.ts
import { NextResponse } from 'next/server';

type PracticeMode = 'chat' | 'voice';

type StartPracticeReq = {
  conversationId: string;
  mode: PracticeMode;
};

type StartPracticeRes = {
  sessionId: string;
  mode: PracticeMode;
  conversationId: string;
};

export async function POST(req: Request) {
  const body = (await req.json()) as StartPracticeReq;

  if (!body.conversationId) {
    return NextResponse.json(
      { message: 'conversationId가 필요합니다.' },
      { status: 400 }
    );
  }

  if (body.mode !== 'chat' && body.mode !== 'voice') {
    return NextResponse.json(
      { message: 'mode는 chat 또는 voice여야 합니다.' },
      { status: 400 }
    );
  }

  // 목업용 sessionId 생성 (나중에 FastAPI로 대체 예정)
  const sessionId = `sess_${Date.now().toString(36)}`;

  const res: StartPracticeRes = {
    sessionId,
    mode: body.mode,
    conversationId: body.conversationId,
  };

  return NextResponse.json(res);
}