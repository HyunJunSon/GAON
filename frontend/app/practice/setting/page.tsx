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
      <main className="mx-auto max-w-4xl p-6">
        <div className="flex items-center justify-center min-h-[500px]">
          <div className="text-center space-y-8">
            <div className="space-y-4">
              <div className="w-20 h-20 bg-gradient-to-br from-red-100 to-pink-100 rounded-2xl flex items-center justify-center mx-auto">
                <svg className="w-10 h-10 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h1 className="text-4xl font-bold text-gray-800">연습 설정</h1>
              <p className="text-xl text-gray-600">대화 분석 결과가 필요합니다</p>
            </div>

            <div className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8 max-w-md mx-auto">
              <h2 className="text-xl font-semibold text-gray-800 mb-4">설정할 수 없습니다</h2>
              <div className="space-y-4 text-gray-600">
                <p className="leading-relaxed">
                  최근 분석된 대화가 없어서 연습을 설정할 수 없습니다.
                </p>
                <div className="bg-gray-50 rounded-xl p-4">
                  <p className="text-sm leading-relaxed">
                    먼저 대화를 업로드하고 분석을 완료한 뒤, 분석 결과 페이지에서{' '}
                    <span className="font-semibold text-gray-800">"연습하러 가기"</span> 버튼을 눌러 주세요.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="space-y-8">
        {/* 헤더 */}
        <header className="text-center">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-100 to-pink-100 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-800">연습 설정</h1>
          </div>
          <p className="text-gray-600 text-lg">연습 모드와 대화 상대를 선택해주세요</p>
        </header>

        {/* 모드 선택 */}
        <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800">연습 모드</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {(
              [
                { 
                  value: 'new', 
                  label: '새로운 대화', 
                  description: '새로운 주제로 대화를 시작합니다',
                  icon: (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  )
                },
                { 
                  value: 'replay', 
                  label: '기존 대화 이어가기', 
                  description: '분석된 대화를 바탕으로 연습합니다',
                  icon: (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                    </svg>
                  )
                },
              ] satisfies { value: PracticeMode; label: string; description: string; icon: React.ReactNode }[]
            ).map(({ value, label, description, icon }) => (
              <button
                key={value}
                type="button"
                className={[
                  'p-6 rounded-xl border-2 text-left transition-all duration-200',
                  mode === value
                    ? 'border-orange-500 bg-gradient-to-br from-orange-50 to-red-50'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50',
                ].join(' ')}
                onClick={() => setMode(value)}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className={[
                    'w-8 h-8 rounded-lg flex items-center justify-center',
                    mode === value ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-600'
                  ].join(' ')}>
                    {icon}
                  </div>
                  <h3 className="font-semibold text-gray-800">{label}</h3>
                </div>
                <p className="text-sm text-gray-600">{description}</p>
              </button>
            ))}
          </div>
        </section>

        {/* 상대 선택 */}
        <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-green-100 to-emerald-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-800">대화 상대</h2>
          </div>

          {isLoading && (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="w-8 h-8 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-3"></div>
                <p className="text-gray-600">대화 상대를 불러오는 중...</p>
              </div>
            </div>
          )}

          {isError && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-2">
              <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-red-600">가족/참가자 목록을 불러오지 못했습니다.</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {participants.map(p => {
              const active = selected.includes(p.id);
              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => toggle(p.id)}
                  className={[
                    'p-4 rounded-xl border-2 text-left transition-all duration-200',
                    active
                      ? 'border-orange-500 bg-gradient-to-br from-orange-50 to-red-50'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50',
                  ].join(' ')}
                >
                  <div className="flex items-center gap-3">
                    <div className={[
                      'w-10 h-10 rounded-lg flex items-center justify-center',
                      active ? 'bg-orange-100' : 'bg-gray-100'
                    ].join(' ')}>
                      <svg className={[
                        'w-5 h-5',
                        active ? 'text-orange-600' : 'text-gray-600'
                      ].join(' ')} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <div>
                      <div className="font-semibold text-gray-800">{p.name}</div>
                      {p.relationship && (
                        <div className="text-sm text-gray-600">{p.relationship}</div>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* CTA */}
        <div className="text-center">
          <button
            type="button"
            disabled={!ready || start.isPending}
            onClick={onStart}
            className={[
              'px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-200 shadow-lg',
              ready
                ? 'bg-gradient-to-r from-orange-500 to-red-500 text-white hover:from-orange-600 hover:to-red-600 hover:shadow-xl transform hover:-translate-y-1'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed',
            ].join(' ')}
          >
            {start.isPending ? (
              <div className="flex items-center gap-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                세션 생성 중...
              </div>
            ) : (
              '대화 시작하기'
            )}
          </button>
        </div>
      </div>
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
      <main className="mx-auto max-w-4xl p-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-gray-600">연습 설정을 불러오는 중...</p>
          </div>
        </div>
      </main>
    }>
      <PracticeSettingContent />
    </Suspense>
  );
}
