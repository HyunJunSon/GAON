import { NextResponse } from 'next/server';
import { store } from '../../../_store';

// Next.js 15: params는 Promise
export async function POST(req: Request, ctx: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await ctx.params;
  const body = await req.json().catch(() => null) as
    | { messages?: Array<{ role: 'user'|'assistant'|'system'; content: string; ts: number }> }
    | null;

  const s = store.getSession(sessionId);
  if (!s) return NextResponse.json({ message: 'NOT_FOUND' }, { status: 404 });

  const msgs = (body?.messages ?? [])
    .filter(m => m.role === 'user' || m.role === 'assistant')
    .map(m => ({ role: m.role as 'user'|'assistant', content: m.content, ts: m.ts }));

  if (msgs.length) store.appendMessages(sessionId, msgs);

  // 여기서 실제로는 분석 잡 생성 → 완료 시 결과 저장/조회
  return NextResponse.json({ ok: true, sessionId }, { status: 200 });
}