'use client';

import { useParams } from 'next/navigation';
import { useAnalysis } from '@/hooks/useAnalysis';

export default function AnalysisDetailPage() {
  const params = useParams();
  const conversationId = Array.isArray(params.conversationId)
    ? params.conversationId[0]
    : (params.conversationId as string | undefined);

  const { data, isLoading, isError, error } = useAnalysis(conversationId ?? '');

  if (!conversationId) {
    return <p className="p-4 text-sm text-gray-600">유효하지 않은 ID입니다.</p>;
  }

  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        <div className="h-6 w-40 rounded bg-gray-200 animate-pulse" />
        <div className="h-4 w-64 rounded bg-gray-200 animate-pulse" />
        <div className="h-24 w-full rounded bg-gray-200 animate-pulse" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <main className="space-y-4">
        <h1 className="text-2xl font-semibold">분석 결과</h1>
        <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {(error as Error)?.message ?? '결과를 불러오지 못했습니다.'}
        </div>
      </main>
    );
  }

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">분석 결과</h1>
        <p className="text-sm text-gray-600">
          대화 ID: <code className="rounded bg-gray-100 px-1 py-0.5">{conversationId}</code>
        </p>
      </header>

      {data.status !== 'ready' ? (
        <section className="rounded-lg border bg-white p-4">
          <p className="text-sm text-gray-700">
            현재 상태: <strong>{data.status}</strong>
          </p>
          <p className="text-xs text-gray-500 mt-1">
            분석이 완료되면 내용이 표시됩니다. (자동 새로고침)
          </p>
        </section>
      ) : (
        <>
          <section className="rounded-lg border bg-white p-4">
            <h2 className="text-lg font-medium mb-2">요약</h2>
            <ul className="list-disc pl-5 text-sm text-gray-700">
              {data.summary?.bullets?.map((b, i) => <li key={i}>{b}</li>)}
            </ul>
          </section>

          <section className="rounded-lg border bg-white p-4">
            <h2 className="text-lg font-medium mb-2">감정(샘플)</h2>
            <div className="text-sm text-gray-700 space-y-2">
              {data.emotion?.series?.map((s) => (
                <div key={s.label} className="flex items-center gap-2">
                  <span className="w-20 text-gray-500">{s.label}</span>
                  <div className="h-2 bg-gray-200 rounded w-64">
                    <div className="h-2 bg-gray-800 rounded" style={{ width: `${s.value}%` }} />
                  </div>
                  <span>{s.value}%</span>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-lg border bg-white p-4">
            <h2 className="text-lg font-medium mb-2">대화록</h2>
            <pre className="rounded bg-gray-50 p-3 text-sm whitespace-pre-wrap">
              {data.dialog?.raw}
            </pre>
          </section>
        </>
      )}
    </main>
  );
}