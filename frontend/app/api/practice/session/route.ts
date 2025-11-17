import { NextResponse } from 'next/server';
import { store } from '../_store';

export async function POST(req: Request) {
  const body = await req.json().catch(() => null) as
    | { conversationId?: string; mode?: 'chat'|'voice'|'hybrid'; participantIds?: string[] }
    | null;

  if (!body?.conversationId || !body?.mode || !Array.isArray(body.participantIds) || body.participantIds.length === 0) {
    return NextResponse.json({ message: 'INVALID_INPUT' }, { status: 400 });
  }

  const s = store.createSession({
    conversationId: body.conversationId,
    mode: body.mode,
    participantIds: body.participantIds,
  });

  return NextResponse.json({ sessionId: s.id }, { status: 200 });
}