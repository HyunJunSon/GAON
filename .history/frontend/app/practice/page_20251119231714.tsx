'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { conversationIdStorage } from '@/utils/conversationIdStorage';
import Link from 'next/link';
import { useAnalysis } from '@/hooks/useAnalysis';
import { useStartPracticeSession } from '@/hooks/usePractice';
import { useServerError } from '@/hooks/useServerError';
import ErrorAlert from '@/components/ui/ErrorAlert';

export default function PracticeEntryPage() {
  const router = useRouter();
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [checked, setChecked] = useState(false);
  const startPractice = useStartPracticeSession();
  const { serverError, handleError, clearError } = useServerError('연습 세션을 시작하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');

  useEffect(() => {
    const lastConversationId = conversationIdStorage.get();
    queueMicrotask(() => {
      if (lastConversationId) {
        setConversationId(lastConversationId)
      }
      setChecked(true);
    });
  }, []);

  const analysisId = conversationId ?? '';
  const hasConversation = !!conversationId;
  const { data, isLoading, isError } = useAnalysis(analysisId);
  const statusMap: Record<string, { label: string; badge: string; description: string }> = {
    ready: {
      label: '연습 가능',
      badge: 'bg-green-100 text-green-700 ring-1 ring-green-200',
      description: '분석이 완료되어 바로 연습을 시작할 수 있어요.',
    },
    processing: {
      label: '분석 진행 중',
      badge: 'bg-yellow-100 text-yellow-700 ring-1 ring-yellow-200',
      description: '분석이 끝나면 자동으로 연습을 안내해드릴게요.',
    },
    failed: {
      label: '분석 실패',
      badge: 'bg-red-100 text-red-700 ring-1 ring-red-200',
      description: '잠시 후 다시 시도하거나 다른 대화를 업로드해 주세요.',
    },
    unknown: {
      label: '상태 확인 중',
      badge: 'bg-gray-100 text-gray-600 ring-1 ring-gray-200',
      description: '최근 분석 정보를 불러오는 중이에요.',
    },
  };
  const currentStatusKey = (data?.status ?? (isLoading ? 'processing' : 'unknown')) as keyof typeof statusMap;
  const statusInfo = statusMap[currentStatusKey] ?? statusMap.unknown;
  
  if (!checked) {
    return null;
  }

  if (!hasConversation) {
    return (
      <main className="mx-auto w-full max-w-5xl space-y-8 px-4 pb-16 pt-8 md:space-y-10 md:px-0">
        <header className="rounded-3xl border border-orange-200 bg-gradient-to-br from-orange-50 via-white to-red-100 p-8 shadow-inner">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 text-white shadow-lg">
                  <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M8 10h8m-8 4h8M5 7a2 2 0 012-2h10a2 2 0 012 2v10a2 2 0 01-2 2H7a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wide text-orange-600">Practice Workspace</p>
                  <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">연습 준비가 필요해요</h1>
                </div>
              </div>
              <p className="text-base leading-relaxed text-gray-600 md:text-lg">
                분석된 대화가 아직 없어요. 대화를 업로드하고 분석을 완료하면 연습 모드를 활성화할 수 있습니다.
              </p>
            </div>
            <div className="rounded-2xl border border-white/80 bg-white/70 px-6 py-5 shadow-lg backdrop-blur">
              <p className="text-sm font-medium text-gray-500">연습을 시작하려면</p>
              <ul className="mt-3 space-y-2 text-sm text-gray-700">
                <li>1. 대화 파일을 업로드</li>
                <li>2. 분석 완료까지 대기</li>
                <li>3. 분석 페이지에서 연습 이동</li>
              </ul>
            </div>
          </div>
        </header>

        <section className="rounded-2xl border border-orange-100 bg-white p-10 text-center shadow-lg">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-100 to-red-100">
            <svg className="h-10 w-10 text-orange-600" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" viewBox="0 0 48 48">
              <path d="M24 38C24 38 10 28 10 18C10 12 14 8 18 8C21 8 24 11 24 11C24 11 27 8 30 8C34 8 38 12 38 18C38 28 24 38 24 38Z" />
              <line x1="24" y1="18" x2="24" y2="26" />
              <circle cx="24" cy="30" r="1.8" fill="currentColor" />
            </svg>
          </div>
          <h2 className="text-2xl font-semibold text-gray-900">분석된 대화를 먼저 준비해주세요</h2>
          <p className="mt-3 text-gray-600">
            대화를 업로드하고 분석이 완료되면 연습 페이지에서 텍스트/음성 연습을 바로 시작할 수 있습니다.
          </p>
          <div className="mt-8">
            <Link
              href="/conversation"
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-orange-500 to-red-500 px-6 py-3 text-white shadow-lg transition-all hover:from-orange-600 hover:to-red-600 hover:shadow-xl"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth={2} viewBox="0 0 24 24">
                <path d="M12 5v14m7-7H5" />
              </svg>
              대화 업로드 하러 가기
            </Link>
          </div>
        </section>
      </main>
    );
  }

  function handleStartPractice(mode: 'chat' | 'voice') {
    if (!conversationId || startPractice.isPending) return;
    clearError();

    startPractice.mutate(
      { conversationId, mode },
      {
        onSuccess: (res) => {
          router.push(`/practice/chat/${res.sessionId}?mode=${res.mode}`);
        },
        onError: (e) => {
          handleError(e);
        },
      }
    );
  }

  return (
    <main className="mx-auto w-full max-w-5xl space-y-8 px-4 pb-16 pt-8 md:space-y-10 md:px-0">
      <header className="rounded-3xl border border-orange-200 bg-gradient-to-br from-orange-50 via-white to-red-100 p-8 shadow-inner">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 text-white shadow-lg">
                <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M7 12h10M7 16h10M7 8h10M5 5h14a2 2 0 012 2v10a4 4 0 01-4 4H7a4 4 0 01-4-4V7a2 2 0 012-2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-orange-600">Practice Workspace</p>
                <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">연습 준비하기</h1>
              </div>
            </div>
            <p className="text-base leading-relaxed text-gray-600 md:text-lg">
              분석이 완료된 대화를 기반으로 텍스트/음성 연습을 시작할 수 있습니다. 아래에서 상태를 확인하고 원하는 연습을 골라보세요.
            </p>
          </div>
          <div className="rounded-2xl border border-white/80 bg-white/70 px-6 py-5 shadow-lg backdrop-blur">
            <p className="text-sm font-medium text-gray-500">최근 분석 상태</p>
            <div className="mt-4 flex flex-col gap-3">
              <span className={`inline-flex w-fit items-center rounded-full px-4 py-1 text-sm font-semibold ${statusInfo.badge}`}>
                {statusInfo.label}
              </span>
              <p className="text-sm text-gray-600">{statusInfo.description}</p>
            </div>
          </div>
        </div>
      </header>

      {serverError && (
        <div className="rounded-2xl border border-red-100 bg-red-50/70 p-6 shadow-md">
          <ErrorAlert message={serverError} />
        </div>
      )}

      {isLoading && (
        <section className="rounded-2xl border border-orange-100 bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-orange-200 border-t-orange-500" />
          <p className="text-gray-600">이전 대화 분석 결과를 불러오는 중이에요…</p>
        </section>
      )}

      {isError && (
        <section className="rounded-2xl border border-red-100 bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-50">
            <svg className="h-6 w-6 text-red-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" />
              <path d="M15 9l-6 6m0-6l6 6" />
            </svg>
          </div>
          <p className="text-red-600">이전 대화 분석 결과를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.</p>
        </section>
      )}

      {data && (
        <section className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg">
          <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div className="flex flex-1 items-start gap-4">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 text-orange-600">
                <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" viewBox="0 0 24 24">
                  <path d="M12 6v6l3 3" />
                  <circle cx="12" cy="12" r="10" />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900">최근 분석 요약</h2>
                <p className="mt-2 whitespace-pre-line text-gray-600">{data.summary ?? '요약 정보가 아직 준비되지 않았어요.'}</p>
              </div>
            </div>
            <div className="w-full rounded-2xl border border-orange-100 bg-orange-50/60 p-5 md:w-64">
              <p className="text-sm font-semibold text-orange-700">말하기 점수</p>
              <div className="mt-3 text-3xl font-bold text-gray-900">
                {typeof data.score === 'number' ? `${(data.score * 100).toFixed(0)}점` : '-'}
              </div>
              {typeof data.score === 'number' && (
                <div className="mt-4">
                  <div className="mb-1 text-xs text-gray-500">100점 만점</div>
                  <div className="h-2 rounded-full bg-white shadow-inner">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-orange-500 to-red-500 transition-all"
                      style={{ width: `${Math.min(100, data.score * 100)}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      <section className="grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg transition-shadow hover:shadow-xl">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-100 to-red-100 text-orange-600">
            <svg className="h-8 w-8" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" viewBox="0 0 24 24">
              <path d="M12 20l-4-4H6a2 2 0 01-2-2V7a2 2 0 012-2h12a2 2 0 012 2v7" />
              <path d="M10 12h4" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900">텍스트 채팅 연습</h3>
          <p className="mt-3 text-gray-600">AI와 텍스트로 대화하며 표현 방식을 다듬어 보세요.</p>
          <button
            onClick={() => handleStartPractice('chat')}
            disabled={startPractice.isPending}
            className="mt-6 w-full rounded-xl bg-gradient-to-r from-orange-500 to-red-500 px-6 py-3 text-white shadow-lg transition-all hover:from-orange-600 hover:to-red-600 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
          >
            {startPractice.isPending ? '시작 중...' : '텍스트 연습 시작'}
          </button>
        </div>

        <div className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg transition-shadow hover:shadow-xl">
          <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-100 to-red-100 text-orange-600">
            <svg className="h-8 w-8" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" viewBox="0 0 24 24">
              <path d="M9 9v6a3 3 0 006 0V9" />
              <path d="M5 10a7 7 0 0014 0" />
              <path d="M12 19v2" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900">음성 대화 연습</h3>
          <p className="mt-3 text-gray-600">실제 대화처럼 음성으로 자연스러운 소통을 연습하세요.</p>
          <button
            onClick={() => handleStartPractice('voice')}
            disabled={startPractice.isPending}
            className="mt-6 w-full rounded-xl bg-gradient-to-r from-orange-500 to-red-500 px-6 py-3 text-white shadow-lg transition-all hover:from-orange-600 hover:to-red-600 hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-50"
          >
            {startPractice.isPending ? '시작 중...' : '음성 연습 시작'}
          </button>
        </div>
      </section>

      <div className="text-center text-sm text-gray-500">
        연습은 언제든지 중단하고 결과를 확인할 수 있어요.
      </div>
    </main>
  );
}
