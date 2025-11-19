// app/api/practice/result/[sessionId]/route.ts
import { NextResponse } from 'next/server';

export type PracticeResult = {
  sessionId: string;
  conversationId: string;
  mode: 'chat' | 'voice';
  score: number; // 0 ~ 1 사이 점수
  strengths: string[]; // 잘한 점 리스트
  improvements: string[]; // 개선할 점 리스트
  checkpoints: {
    id: string;
    title: string;
    achieved: boolean;
    description: string;
  }[];
  summary: string; // 전체 요약
  createdAt: string;
};

// Next.js 15의 동적 route handler는 params가 Promise인 형태라서 await 필요
export async function GET(
  _req: Request,
  ctx: { params: Promise<{ sessionId: string }> }
) {
  const { sessionId } = await ctx.params;

  // 실제로는 sessionId로 DB/캐시에서 가져오는 구조가 될 것
  // 지금은 conversationId, mode를 간단히 하드코딩
  const mock: PracticeResult = {
    sessionId,
    conversationId: 'conv_mock_1',
    mode: 'chat',
    score: 0.86,
    strengths: [
      '상대방의 감정을 인정하는 표현을 자주 사용했어요.',
      '질문을 통해 상대방의 생각을 이끌어내려는 시도가 좋았어요.',
    ],
    improvements: [
      '대화의 초반에 상황을 조금 더 구체적으로 설명해주면 좋아요.',
      '상대방의 말을 마무리까지 듣고 나서 자신의 의견을 말하는 연습이 필요해요.',
    ],
    checkpoints: [
      {
        id: 'cp1',
        title: '상대방의 감정 먼저 되짚어주기',
        achieved: true,
        description:
          '“그때 많이 힘들었겠다”처럼 감정을 먼저 언급한 부분이 있었어요.',
      },
      {
        id: 'cp2',
        title: '비난 대신 구체적인 요청 사용하기',
        achieved: false,
        description:
          '“그러니까 너는 항상…” 보다는 “다음엔 이렇게 해줄 수 있을까?” 같은 표현을 더 연습해보면 좋아요.',
      },
    ],
    summary: `
이번 연습에서 사용자는 상대방의 감정을 인정하고 공감하려는 태도가 잘 드러났습니다.
다만, 대화를 시작할 때 상황 설명이 다소 부족한 부분이 있었고,
상대방의 말을 끝까지 듣기 전에 자신의 의견을 먼저 제시하는 장면이 몇 번 관찰되었습니다.

다음 연습에서는,
1) 감정 요약 → 2) 상황 정리 → 3) 자신의 바람/요청 순서로 말하는 패턴을 의식적으로 연습해보는 것을 추천드립니다.
    `.trim(),
    createdAt: new Date().toISOString(),
  };

  return NextResponse.json(mock);
}