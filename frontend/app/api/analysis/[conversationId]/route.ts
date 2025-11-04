// app/api/analysis/[conversationId]/route.ts
import { NextResponse } from 'next/server';

/**
 * 간단 목업: 같은 conversationId로 여러 번 조회하면
 * 1~2회는 queued/processing, 이후 ready로 응답
 */
const hitMap = new Map<string, number>();

export async function GET(
  _req: Request,
  { params }: { params: { conversationId: string } }
) {
  const { conversationId } = params;
  const hits = (hitMap.get(conversationId) || 0) + 1;
  hitMap.set(conversationId, hits);

  if (hits === 1) {
    return NextResponse.json({
      conversationId,
      status: 'queued',
      updatedAt: new Date().toISOString(),
    });
  }
  if (hits === 2) {
    return NextResponse.json({
      conversationId,
      status: 'processing',
      updatedAt: new Date().toISOString(),
    });
  }

  // ready 응답 (샘플 데이터)
  return NextResponse.json({
    conversationId,
    status: 'ready',
    updatedAt: new Date().toISOString(),
    summary: {
      bullets: [
        '시험 준비 일정에 대한 합의 필요',
        '부모-자녀 간 신뢰/소통 이슈 발견',
        '휴식 시간과 학습 계획 조율 요구',
      ],
    },
    emotion: {
      series: [
        { label: '긍정', value: 62 },
        { label: '중립', value: 22 },
        { label: '부정', value: 16 },
      ],
    },
    dialog: {
      raw: `엄마: 지금 시험기간 아니야?\n아들: 잠깐 쉬는 거야...\n아빠: 잠깐이 하루 종일이냐?...`,
    },
  });
}