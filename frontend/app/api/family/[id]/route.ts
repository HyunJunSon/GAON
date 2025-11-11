// app/api/family/[id]/route.ts
import { NextResponse } from 'next/server';
import { getMembers, setMembers } from '../_store';

export async function DELETE(
  _req: Request,
  // params 가 Promise 라는 점을 타입으로도 명시
  context: { params: Promise<{ id: string }> }
) {
  // ⬇️ 반드시 await 해서 id를 꺼냄
  const { id } = await context.params;

  const members = getMembers();
  const before = members.length;

  const next = members.filter(m => m.id !== id);
  if (next.length === before) {
    return NextResponse.json({ ok: false, message: 'NOT_FOUND' }, { status: 404 });
  }

  setMembers(next);
  return NextResponse.json({ ok: true }, { status: 200 });
}