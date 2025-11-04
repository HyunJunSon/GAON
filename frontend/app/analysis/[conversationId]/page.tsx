'use client';
// 특정 conversation에 분석 결과 페이지
// 2단계에서 TanStack Query로 GET /analysis/{conversationId} 연결
// 3단계에서 탭(/summary|/emotion|/dialog) 확장 예정

import { useParams } from 'next/navigation';
import { fetchAnalysis } from '@/apis/analysis';
import { useEffect, useState } from 'react';


type Status = 'queued' | 'processing' | 'ready' | 'failed';

export default function AnalysisDetailPage() {
  const params = useParams(); // { conversationId: string | string[] }
  const conversationId = Array.isArray(params.conversationId)
    ? params.conversationId[0]
    : (params.conversationId as string | undefined);

  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (!conversationId) return;

    let timer: ReturnType<typeof setInterval> | null = null;
    let stop = false;

    const load = async () => {
      try {
        const data = await fetchAnalysis(conversationId);
        setStatus(data.status);
        setResult(data);

        if (data.status === 'ready' || data.status === 'failed') {
          if (timer) clearInterval(timer);
          timer = null;
        }
      } catch (e: any) {
        setError(e?.message ?? '결과를 불러오지 못했습니다.');
        if (timer) clearInterval(timer);
        timer = null;
      }
    };

    // 최초 1회 + 2초 폴링
    load();
    timer = setInterval(load, 2000);

    return () => {
      if (timer) clearInterval(timer);
      stop = true;
    };
  }, [conversationId]);

  if (!conversationId) {
    return <p className="p-4 text-sm text-gray-600">유효하지 않은 ID입니다.</p>;
  }

  if (error) {
    return (
      <main className="space-y-4">
        <h1 className="text-2xl font-semibold">분석 결과</h1>
        <div className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
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

      {!status || status !== 'ready' ? (
        <section className="rounded-lg border bg-white p-4">
          <p className="text-sm text-gray-700">
            현재 상태: <strong>{status ?? 'loading...'}</strong>
          </p>
          <p className="text-xs text-gray-500 mt-1">분석 완료 시 내용이 표시됩니다.</p>
        </section>
      ) : (
        <>
          <section className="rounded-lg border bg-white p-4">
            <h2 className="text-lg font-medium mb-2">요약</h2>
            <ul className="list-disc pl-5 text-sm text-gray-700">
              {result?.summary?.bullets?.map((b: string, i: number) => <li key={i}>{b}</li>)}
            </ul>
          </section>

          <section className="rounded-lg border bg-white p-4">
            <h2 className="text-lg font-medium mb-2">감정(샘플)</h2>
            <div className="text-sm text-gray-700 space-y-2">
              {result?.emotion?.series?.map((s: any) => (
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
              {result?.dialog?.raw}
            </pre>
          </section>
        </>
      )}
    </main>
  );
}