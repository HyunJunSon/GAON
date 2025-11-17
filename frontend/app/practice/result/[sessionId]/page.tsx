// app/practice/result/[sessionId]/page.tsx
'use client';

import { useParams } from 'next/navigation';
import { usePracticeResult } from '@/hooks/usePractice';
import ErrorAlert from '@/components/ui/ErrorAlert';

export default function PracticeResultPage() {
  const { sessionId } = useParams<{ sessionId: string }>();

  // useParams 제네릭으로 string으로 받는다고 알려줬으니 그대로 사용
  const { data, isLoading, isError, error } = usePracticeResult(sessionId);

  if (isLoading || !data) {
    return (
      <main className="mx-auto max-w-3xl p-4 md:p-6">
        <h1 className="text-lg font-semibold">연습 결과 분석 중…</h1>
        <p className="mt-2 text-sm text-gray-600">
          방금 진행한 연습 대화를 분석하고 있어요. 잠시만 기다려 주세요.
        </p>
      </main>
    );
  }

  if (isError) {
    return (
      <main className="mx-auto max-w-3xl space-y-4 p-4 md:p-6">
        <h1 className="text-lg font-semibold">연습 결과</h1>
        <ErrorAlert
          message={
            error?.message ||
            '연습 결과를 불러오는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.'
          }
        />
      </main>
    );
  }

  const result = data;

  return (
    <main className="mx-auto max-w-3xl space-y-6 p-4 md:p-6">
      {/* 헤더 영역 */}
      <header className="space-y-1">
        <h1 className="text-xl font-semibold">연습 결과</h1>
        <p className="text-xs text-gray-500">
          세션 ID: <span className="font-mono">{result.sessionId}</span> · 모드:{' '}
          <span className="font-medium">
            {result.mode === 'chat' ? '실시간 채팅 연습' : '음성 대화 연습'}
          </span>
        </p>
      </header>

      {/* 점수 요약 */}
      <section className="rounded-xl border bg-white p-4 text-sm">
        <h2 className="text-sm font-semibold">총평 점수</h2>
        <p className="mt-2 text-2xl font-bold">
          {(result.score * 100).toFixed(0)}점
          <span className="ml-1 text-sm font-normal text-gray-500">/ 100점</span>
        </p>
        <p className="mt-2 text-xs text-gray-600">
          점수는 이번 연습에서의 말하기 방식, 감정 표현, 경청 태도 등을 종합해서 계산된 값이에요.
        </p>
      </section>

      {/* 잘한 점 / 개선할 점 */}
      <section className="grid gap-4 text-sm md:grid-cols-2">
        <div className="rounded-xl border bg-white p-4">
          <h2 className="text-sm font-semibold">잘한 점</h2>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-gray-700">
            {result.strengths.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
        <div className="rounded-xl border bg-white p-4">
          <h2 className="text-sm font-semibold">더 개선하면 좋은 점</h2>
          <ul className="mt-2 list-disc space-y-1 pl-4 text-gray-700">
            {result.improvements.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </div>
      </section>

      {/* 체크포인트 반영 여부 */}
      <section className="rounded-xl border bg-white p-4 text-sm">
        <h2 className="text-sm font-semibold">체크 포인트 반영 여부</h2>
        <p className="mt-1 text-xs text-gray-600">
          분석 페이지에서 제안된 체크 포인트를 이번 연습에서 얼마나 반영했는지 정리했어요.
        </p>
        <ul className="mt-3 space-y-2">
          {result.checkpoints.map((cp) => (
            <li
              key={cp.id}
              className="flex items-start gap-2 rounded-lg bg-gray-50 px-3 py-2"
            >
              <span
                className={
                  cp.achieved
                    ? 'mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-500 text-[10px] text-white'
                    : 'mt-0.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-gray-400 text-[10px] text-gray-500'
                }
              >
                {cp.achieved ? '✓' : '!'}
              </span>
              <div>
                <p className="text-xs font-semibold">
                  {cp.title}{' '}
                  <span className="ml-1 text-[11px] font-normal text-gray-500">
                    {cp.achieved ? '실행됨' : '아직 연습 중'}
                  </span>
                </p>
                <p className="mt-1 text-xs text-gray-700">{cp.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {/* 전체 요약 */}
      <section className="rounded-xl border bg-white p-4 text-sm">
        <h2 className="text-sm font-semibold">전체 요약</h2>
        <p className="mt-2 whitespace-pre-line text-gray-700">
          {result.summary}
        </p>
      </section>
    </main>
  );
}