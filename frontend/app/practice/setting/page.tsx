'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useState, useMemo, Suspense } from 'react';
import type { PracticeMode } from '@/schemas/practice';
import { useParticipants, useStartPractice } from '@/hooks/usePractice';
import { conversationIdStorage } from '@/utils/conversationIdStorage';

/**
 * 연습 설정 페이지 내부 컴포넌트
 */
function PracticeSettingContent() {
  const router = useRouter();
  const sp = useSearchParams();

  // 1) URL 쿼리와 storage 둘 다에서 conversationId를 찾아본다.
  const fromQuery = sp.get('conversationId');
  const fromStorage = conversationIdStorage.get();
  const conversationId = fromQuery || fromStorage || '';

  // 2) 연습 모드: 'new' | 'replay' 중 하나 / 초기값은 null
  const [mode, setMode] = useState<PracticeMode | null>(null);

  // 3) 선택된 대화 상대 id 리스트
  const [selected, setSelected] = useState<string[]>([]);

  const { data, isLoading, isError } = useParticipants();
  const start = useStartPractice();

  const participants = data?.participants ?? [];

  // 4) 버튼 활성 조건: conversationId + mode + 선택된 상대
  const ready = useMemo(
    () => !!conversationId && !!mode && selected.length > 0,
    [conversationId, mode, selected]
  );

  const toggle = (id: string) => {
    setSelected(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const onStart = async () => {
    // 안전장치
    if (!ready || !mode) return;

    const res = await start.mutateAsync({
      conversationId,
      mode,
      participantIds: selected,
    });

    router.push(`/practice/chat/${res.sessionId}`);
  };

  // 5) conversationId 자체가 없으면 안내만 보여주기
  if (!conversationId) {
    return (
      <main className="mx-auto max-w-2xl space-y-4 p-6">
        <h1 className="text-xl font-semibold">연습 설정</h1>
        <p className="text-sm text-gray-700">
          최근 분석된 대화가 없어서 연습을 설정할 수 없어요.
        </p>
        <p className="text-sm text-gray-600">
          먼저 대화를 업로드하고 분석을 완료한 뒤, 분석 결과 페이지에서{' '}
          <strong>"연습하러 가기"</strong> 버튼을 눌러 주세요.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl p-6 space-y-6">
      <h1 className="text-xl font-semibold">연습 설정</h1>

      {/* 모드 선택 */}
      <section className="space-y-2">
        <h2 className="text-sm font-medium">연습 모드</h2>
        <div className="flex gap-2">
          {(
            [
              { value: 'new', label: '새로운 대화' },
              { value: 'replay', label: '기존 대화 이어가기' },
            ] satisfies { value: PracticeMode; label: string }[]
          ).map(({ value, label }) => (
            <button
              key={value}
              type="button"
              className={[
                'rounded-lg border px-3 py-2 text-sm',
                mode === value
                  ? 'border-black bg-black text-white'
                  : 'border-gray-300 hover:bg-gray-50',
              ].join(' ')}
              onClick={() => setMode(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </section>

      {/* 상대 선택 */}
      <section className="space-y-2">
        <h2 className="text-sm font-medium">대화 상대</h2>
        {isLoading && (
          <p className="text-sm text-gray-500">가져오는 중…</p>
        )}
        {isError && (
          <p className="text-sm text-red-600">
            가족/참가자 목록을 불러오지 못했습니다.
          </p>
        )}
        <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {participants.map(p => {
            const active = selected.includes(p.id);
            return (
              <li key={p.id}>
                <button
                  type="button"
                  onClick={() => toggle(p.id)}
                  className={[
                    'w-full rounded-lg border p-3 text-left text-sm',
                    active
                      ? 'border-black bg-gray-900 text-white'
                      : 'border-gray-300 hover:bg-gray-50',
                  ].join(' ')}
                >
                  <div className="font-medium">{p.name}</div>
                  {p.relationship && (
                    <div className="text-xs opacity-70">
                      {p.relationship}
                    </div>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </section>

      {/* CTA */}
      <button
        type="button"
        disabled={!ready || start.isPending}
        onClick={onStart}
        className={[
          'w-full rounded-xl py-3 text-sm font-medium transition-all',
          ready
            ? 'bg-black text-white hover:opacity-90'
            : 'bg-gray-200 text-gray-500 cursor-not-allowed',
        ].join(' ')}
      >
        {start.isPending ? '세션 생성 중…' : '대화 시작하기'}
      </button>
    </main>
  );
}

/**
 * 연습 설정 페이지
 * - 연습 모드 선택: 새로운 대화 / 기존 대화 이어가기
 * - 대화 상대 선택(복수): 서버에서 participants 조회
 * - "대화 시작하기": 세션 생성 → /practice/chat/[sessionId]
 */
export default function PracticeSettingPage() {
  return (
    <Suspense fallback={
      <main className="mx-auto max-w-2xl p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-32"></div>
          <div className="h-4 bg-gray-200 rounded w-48"></div>
        </div>
      </main>
    }>
      <PracticeSettingContent />
    </Suspense>
  );
}
