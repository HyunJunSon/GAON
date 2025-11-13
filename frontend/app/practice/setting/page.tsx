'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { useState, useMemo } from 'react';
import { useParticipants, useStartPractice } from '@/hooks/usePractice';
import type { PracticeMode } from '@/schemas/practice';

/**
 * 연습 설정 페이지
 * - 모드 선택(chat/voice/hybrid)
 * - 대화 상대 선택(복수) : 서버에서 participants 조회
 * - 대화 시작하기: 세션 생성 → /practice/chat/[sessionId]
 */
export default function PracticeSettingPage() {
  const router = useRouter();
  const sp = useSearchParams();
  const conversationId = sp.get('conversationId') || '';

  const [mode, setMode] = useState<PracticeMode | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const { data, isLoading, isError } = useParticipants();
  const start = useStartPractice();

  const participants = data?.participants ?? [];
  const ready = useMemo(() => !!conversationId && !!mode && selected.length > 0, [conversationId, mode, selected]);

  const toggle = (id: string) => {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const onStart = async () => {
    if (!ready || !mode) return;
    const res = await start.mutateAsync({
      conversationId,
      mode,
      participantIds: selected,
    });
    router.push(`/practice/chat/${res.sessionId}`);
  };

  return (
    <main className="mx-auto max-w-2xl p-6 space-y-6">
      <h1 className="text-xl font-semibold">연습 설정</h1>

      {/* 모드 선택 */}
      <section className="space-y-2">
        <h2 className="text-sm font-medium">연습 모드</h2>
        <div className="flex gap-2">
          {(['chat','voice','hybrid'] as PracticeMode[]).map(m => (
            <button
              key={m}
              type="button"
              className={[
                'rounded-lg border px-3 py-2 text-sm',
                mode === m ? 'border-black bg-black text-white' : 'border-gray-300 hover:bg-gray-50'
              ].join(' ')}
              onClick={() => setMode(m)}
            >
              {m === 'chat' ? '채팅' : m === 'voice' ? '음성' : '하이브리드'}
            </button>
          ))}
        </div>
      </section>

      {/* 상대 선택 */}
      <section className="space-y-2">
        <h2 className="text-sm font-medium">대화 상대</h2>
        {isLoading && <p className="text-sm text-gray-500">가져오는 중…</p>}
        {isError && <p className="text-sm text-red-600">가족/참가자 목록을 불러오지 못했습니다.</p>}
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
                    active ? 'border-black bg-gray-900 text-white' : 'border-gray-300 hover:bg-gray-50'
                  ].join(' ')}
                >
                  <div className="font-medium">{p.name}</div>
                  {p.relationship && <div className="text-xs opacity-70">{p.relationship}</div>}
                </button>
              </li>
            );
          })}
        </ul>
      </section>

      {/* CTA */}
      <div className="sticky bottom-[calc(56px+env(safe-area-inset-bottom))] md:static">
        <button
          type="button"
          disabled={!ready || start.isPending}
          onClick={onStart}
          className={[
            'w-full rounded-xl py-3 text-sm font-medium transition-all',
            ready ? 'bg-black text-white hover:opacity-90' : 'bg-gray-200 text-gray-500 cursor-not-allowed'
          ].join(' ')}
        >
          {start.isPending ? '세션 생성 중…' : '대화 시작하기'}
        </button>
      </div>
    </main>
  );
}