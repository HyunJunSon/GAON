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
  
  if (!checked) {
    return null;
  }

  if (!hasConversation) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#FAF5F2] to-[#F5EDE8]">
        <div className="mx-auto max-w-4xl px-6 py-12">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-[#E5664C] to-[#D95A42] rounded-2xl mb-6">
              <svg width="32" height="32" viewBox="0 0 48 48" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
                <rect x="10" y="14" width="28" height="20" rx="2"/>
                <path d="M 18 24 Q 21 20, 24 24 Q 27 28, 30 24"/>
                <circle cx="18" cy="22" r="1.5" fill="white"/>
                <circle cx="30" cy="22" r="1.5" fill="white"/>
              </svg>
            </div>
            <h1 className="text-3xl font-semibold text-[#2C2C2C] mb-4">연습하기</h1>
            <p className="text-lg text-[#666] leading-relaxed">
              가족과의 대화를 연습해보세요
            </p>
          </div>

          {/* Empty State Card */}
          <div className="bg-white rounded-2xl shadow-sm border border-[#F0F0F0] p-8 text-center">
            <div className="w-20 h-20 bg-[#F0C5B8] rounded-full flex items-center justify-center mx-auto mb-6">
              <svg width="40" height="40" viewBox="0 0 48 48" fill="none" stroke="#D95A42" strokeWidth="2" strokeLinecap="round">
                <path d="M24 38 C24 38, 10 28, 10 18 C10 12, 14 8, 18 8 C21 8, 24 11, 24 11 C24 11, 27 8, 30 8 C34 8, 38 12, 38 18 C38 28, 24 38, 24 38 Z"/>
                <line x1="24" y1="18" x2="24" y2="26" />
                <circle cx="24" cy="29" r="2" fill="#D95A42"/>
              </svg>
            </div>
            
            <h2 className="text-xl font-medium text-[#2C2C2C] mb-4">분석된 대화가 없어요</h2>
            <p className="text-[#666] mb-8 leading-relaxed">
              먼저 <strong className="text-[#D95A42]">대화 파일을 업로드</strong>하고,<br/>
              <strong className="text-[#D95A42]">분석 결과 페이지</strong>에서 "연습하러 가기" 버튼을 눌러주세요.
            </p>

            <Link
              href="/conversation"
              className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-[#E5664C] to-[#D95A42] text-white font-medium rounded-xl hover:shadow-lg transition-all duration-200 hover:scale-105"
            >
              <svg width="20" height="20" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="mr-2">
                <path d="M 12 36 L 12 24 L 24 16 L 36 24 L 36 36"/>
                <line x1="12" y1="36" x2="36" y2="36"/>
                <rect x="20" y="28" width="8" height="8" rx="1"/>
              </svg>
              대화 업로드 하러 가기
            </Link>
          </div>
        </div>
      </div>
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
    <div className="min-h-screen bg-gradient-to-br from-[#FAF5F2] to-[#F5EDE8]">
      <div className="mx-auto max-w-4xl px-6 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-[#E5664C] to-[#D95A42] rounded-2xl mb-6">
            <svg width="32" height="32" viewBox="0 0 48 48" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
              <rect x="10" y="14" width="28" height="20" rx="2"/>
              <path d="M 18 24 Q 21 20, 24 24 Q 27 28, 30 24"/>
              <circle cx="18" cy="22" r="1.5" fill="white"/>
              <circle cx="30" cy="22" r="1.5" fill="white"/>
            </svg>
          </div>
          <h1 className="text-3xl font-semibold text-[#2C2C2C] mb-4">연습 준비하기</h1>
          <p className="text-lg text-[#666] leading-relaxed">
            분석된 대화를 바탕으로 연습을 시작해보세요
          </p>
        </div>

        {/* Error Alert */}
        {serverError && (
          <div className="mb-8">
            <ErrorAlert message={serverError} />
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="bg-white rounded-2xl shadow-sm border border-[#F0F0F0] p-8 text-center mb-8">
            <div className="animate-pulse">
              <div className="w-12 h-12 bg-[#F0C5B8] rounded-full mx-auto mb-4"></div>
              <p className="text-[#666]">이전 대화 분석 결과를 불러오는 중이에요…</p>
            </div>
          </div>
        )}

        {/* Error State */}
        {isError && (
          <div className="bg-white rounded-2xl shadow-sm border border-red-200 p-8 text-center mb-8">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#DC2626" strokeWidth="2">
                <circle cx="12" cy="12" r="10"/>
                <line x1="15" y1="9" x2="9" y2="15"/>
                <line x1="9" y1="9" x2="15" y2="15"/>
              </svg>
            </div>
            <p className="text-red-600">
              이전 대화 분석 결과를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.
            </p>
          </div>
        )}

        {/* Analysis Summary */}
        {data && data.status === 'ready' && (
          <div className="bg-white rounded-2xl shadow-sm border border-[#F0F0F0] p-8 mb-8">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-[#E6907A] to-[#F0C5B8] rounded-xl flex items-center justify-center flex-shrink-0">
                <svg width="24" height="24" viewBox="0 0 48 48" fill="none" stroke="#D95A42" strokeWidth="2" strokeLinecap="round">
                  <circle cx="24" cy="24" r="12"/>
                  <path d="M 18 24 L 21 20 L 24 22 L 27 18 L 30 20"/>
                  <line x1="18" y1="28" x2="30" y2="28" opacity="0.4"/>
                  <line x1="20" y1="31" x2="28" y2="31" opacity="0.3"/>
                </svg>
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-medium text-[#2C2C2C] mb-2">이전 대화 분석 결과</h2>
                <p className="text-[#666] leading-relaxed whitespace-pre-line">
                  {data.summary}
                </p>
              </div>
            </div>

            {typeof data.score === 'number' && (
              <div className="bg-gradient-to-r from-[#F0C5B8] to-[#FFFFFF] rounded-xl p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-[#666] mb-1">말하기 점수</h3>
                    <p className="text-2xl font-semibold text-[#D95A42]">
                      {(data.score * 100).toFixed(0)}점
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-[#666] mb-1">100점 만점</div>
                    <div className="w-24 h-2 bg-white rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-[#E5664C] to-[#D95A42] rounded-full transition-all duration-500"
                        style={{ width: `${data.score * 100}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Practice Options */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Text Chat Practice */}
          <div className="bg-white rounded-2xl shadow-sm border border-[#F0F0F0] p-8 hover:shadow-lg transition-all duration-200">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-[#E6907A] to-[#F0C5B8] rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg width="32" height="32" viewBox="0 0 48 48" fill="none" stroke="#D95A42" strokeWidth="2" strokeLinecap="round">
                  <path d="M 18 24 Q 21 20, 24 24 Q 27 28, 30 24"/>
                  <rect x="10" y="14" width="28" height="20" rx="2"/>
                  <line x1="16" y1="32" x2="20" y2="36"/>
                </svg>
              </div>
              <h3 className="text-xl font-medium text-[#2C2C2C] mb-3">텍스트 채팅 연습</h3>
              <p className="text-[#666] mb-6 leading-relaxed">
                AI와 텍스트로 대화하며<br/>
                표현 방법을 연습해보세요
              </p>
              <button
                onClick={() => handleStartPractice('chat')}
                disabled={startPractice.isPending}
                className="w-full px-6 py-3 bg-gradient-to-r from-[#E5664C] to-[#D95A42] text-white font-medium rounded-xl hover:shadow-lg transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {startPractice.isPending ? '시작 중...' : '텍스트 연습 시작'}
              </button>
            </div>
          </div>

          {/* Voice Practice */}
          <div className="bg-white rounded-2xl shadow-sm border border-[#F0F0F0] p-8 hover:shadow-lg transition-all duration-200">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-[#E6907A] to-[#F0C5B8] rounded-2xl flex items-center justify-center mx-auto mb-6">
                <svg width="32" height="32" viewBox="0 0 48 48" fill="none" stroke="#D95A42" strokeWidth="2" strokeLinecap="round">
                  <path d="M 24 36 Q 24 30, 24 26"/>
                  <path d="M 18 34 Q 18 28, 18 26"/>
                  <path d="M 30 34 Q 30 28, 30 26"/>
                  <circle cx="24" cy="20" r="3"/>
                  <path d="M 21 18 L 24 14 L 27 18"/>
                </svg>
              </div>
              <h3 className="text-xl font-medium text-[#2C2C2C] mb-3">음성 대화 연습</h3>
              <p className="text-[#666] mb-6 leading-relaxed">
                실제 대화처럼 음성으로<br/>
                자연스러운 소통을 연습해보세요
              </p>
              <button
                onClick={() => handleStartPractice('voice')}
                disabled={startPractice.isPending}
                className="w-full px-6 py-3 bg-gradient-to-r from-[#E5664C] to-[#D95A42] text-white font-medium rounded-xl hover:shadow-lg transition-all duration-200 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
              >
                {startPractice.isPending ? '시작 중...' : '음성 연습 시작'}
              </button>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-12 text-center">
          <div className="inline-flex items-center gap-2 text-sm text-[#666]">
            <svg width="16" height="16" viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="24" cy="24" r="13"/>
              <path d="M 24 13 L 24 24 L 30 27"/>
              <circle cx="24" cy="24" r="2" fill="currentColor"/>
            </svg>
            연습은 언제든지 중단하고 결과를 확인할 수 있어요
          </div>
        </div>
      </div>
    </div>
  );
}
