'use client';

import { useParams } from 'next/navigation';

/**
 * /practice/chat/[sessionId]
 * - 연습 채팅/음성 대화가 실제로 이루어지는 페이지
 * - 2단계 이후:
 *   - LLM과의 실시간 채팅 UI
 *   - 음성 모드 토글(추후)
 *   - 로컬 메시지 상태 관리
 *   - "연습 종료" 버튼 → 서버에 기록 전송 + 분석 요청 → /practice/result/[sessionId]로 이동
 */
export default function PracticeChatPage() {
  const params = useParams<{ sessionId: string }>();
  const raw = params.sessionId;
  const sessionId = Array.isArray(raw) ? raw[0] : raw;

  return (
    <main className="mx-auto flex h-full max-w-2xl flex-col gap-4 p-6">
      <h1 className="text-xl font-semibold">연습 채팅 (임시 뼈대)</h1>

      <p className="text-sm text-gray-600">
        이 페이지에서는 LLM과의 실시간 채팅/음성 연습이 이루어질 예정입니다.
      </p>

      <div className="rounded border bg-white p-4 text-sm text-gray-700">
        <p>세션 ID: <span className="font-mono">{sessionId}</span></p>
        <p className="mt-2">
          다음 단계에서:
        </p>
        <ul className="mt-1 list-disc pl-5">
          <li>채팅 메시지 리스트</li>
          <li>입력창 및 전송 버튼</li>
          <li>음성 모드 토글 버튼</li>
          <li>“연습 종료” CTA 버튼</li>
        </ul>
      </div>
    </main>
  );
}