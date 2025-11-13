'use client';

import { useParams } from 'next/navigation';

/**
 * /practice/result/[sessionId]
 * - 연습이 끝난 뒤, 분석 결과를 보여주는 페이지
 * - 2단계 이후:
 *   - 점수
 *   - 칭찬(강점)
 *   - 개선점
 *   - 체크 포인트 반영 여부(분석 페이지에서 제공한 포인트를 잘 지켰는지)
 *   - 전체 요약
 */
export default function PracticeResultPage() {
  const params = useParams<{ sessionId: string }>();
  const raw = params.sessionId;
  const sessionId = Array.isArray(raw) ? raw[0] : raw;

  return (
    <main className="mx-auto max-w-2xl space-y-4 p-6">
      <h1 className="text-xl font-semibold">연습 결과 (임시 뼈대)</h1>

      <p className="text-sm text-gray-600">
        이 페이지에서는 연습에 대한 분석 결과를 보여줄 예정입니다.
      </p>

      <div className="rounded border bg-white p-4 text-sm text-gray-700">
        <p>세션 ID: <span className="font-mono">{sessionId}</span></p>
        <p className="mt-2">
          다음 단계에서 다음 정보들을 표시하게 될 거예요:
        </p>
        <ul className="mt-1 list-disc pl-5">
          <li>LLM 평가 점수</li>
          <li>잘한 점(칭찬)</li>
          <li>더 개선할 점</li>
          <li>체크 포인트 반영 여부</li>
          <li>전체 요약</li>
        </ul>
      </div>
    </main>
  );
}