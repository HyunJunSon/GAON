import { NextResponse } from 'next/server';
import { store } from '../../_store';

export async function GET(_req: Request, ctx: { params: Promise<{ sessionId: string }> }) {
  const { sessionId } = await ctx.params;
  const s = store.getSession(sessionId);
  if (!s) return NextResponse.json({ message: 'NOT_FOUND' }, { status: 404 });

  // 간단한 목업 결과 생성 (실제론 분석 결과를 DB에서 읽어옴)
  const userTurns = s.messages.filter(m => m.role === 'user').length;
  const assistantTurns = s.messages.filter(m => m.role === 'assistant').length;
  const score = Math.min(0.95, 0.6 + userTurns * 0.03 + assistantTurns * 0.02);

  return NextResponse.json({
    sessionId,
    score,
    strengths: ['상대에게 질문으로 맥락을 확장함', '감정 라벨링으로 공감 표현'],
    improvements: ['말의 길이를 더 간결하게', '상대 말 끊지 않기'],
    summary: `총 ${s.messages.length}개 메시지 교환.\n- 사용자: ${userTurns}턴\n- 어시스턴트: ${assistantTurns}턴\n하이브리드 모드일 경우 음성-텍스트 변환 메시지도 기록됩니다.`,
    createdAt: new Date().toISOString(),
  }, { status: 200 });
}