'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { conversationIdStorage } from '@/utils/conversationIdStorage';
import Link from 'next/link';
import { useAnalysis } from '@/hooks/useAnalysis';
import { useStartPracticeSession } from '@/hooks/usePractice';
import { useServerError } from '@/hooks/useServerError';
import ErrorAlert from '@/components/ui/ErrorAlert';

/**
 * /practice
 * - 쿼리/스토리지 등에서 conversation_id 확인
 * - 있으면 /practice/setting 으로 라우팅
 * - 없으면 안내 문구
 */
export default function PracticeEntryPage() {
  const router = useRouter();
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [checked, setChecked] = useState(false);
  const startPractice = useStartPracticeSession();
  const { serverError, handleError, clearError } = useServerError('연습 세션을 시작하는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');

  useEffect(() => {
    // 1) 로컬 저장소 등에서 최근 conversation_id 조회
    const lastConversationId = conversationIdStorage.get();

    // if (lastConversationId) {
    //   // 2) 있으면 바로 /practice/setting 으로 이동
    //   router.replace('/practice/setting?conversationId=' + encodeURIComponent(lastConversationId));
    //   return;
    // }
    // 없으면 그냥 아래 JSX 안내문이 보이게 둔다.
    // 바로 setChecked(true)를 호출하지 않고, 다음 tick으로 살짝 미뤄서 실행
    queueMicrotask(() => {
      if (lastConversationId) {
        setConversationId(lastConversationId)
      }
      setChecked(true);
    });
  }, []);

  // useAnalysis는 항상 호출해야 하므로,
  // conversationId가 없으면 빈 문자열을 넣고
  // 훅 내부의 enabled 옵션으로 실제 호출 여부를 제어한다.
  const analysisId = conversationId ?? '';
  const hasConversation = !!conversationId;

  const { data, isLoading, isError } = useAnalysis(analysisId);
  
  // ✅ 아직 체크 중이면 아무것도 안 보여주거나, 아주 간단한 로딩만 보여주기
  if (!checked) {
    return null;
  }
  if (!hasConversation) {
    // 여기까지 왔다는 건 → conversationId가 "없다"는 뜻
    return (
      <main className="mx-auto max-w-2xl space-y-4 p-4">
        <h1 className="text-2xl font-semibold">연습하기</h1>
  
        <p className="text-sm text-gray-600">
          최근 분석된 대화가 없어서 연습을 시작할 수 없어요.
        </p>
  
        <p className="text-sm text-gray-600">
          먼저 <strong>대화 파일을 업로드</strong>하고,{' '}
          <strong>분석 결과 페이지</strong>에서 “연습하러 가기” 버튼을 눌러주세요.
        </p>
  
        <div className="mt-4">
          {/* 실제 대화 업로드/분석 시작 페이지 경로에 맞게 href 수정 */}
          <Link
            href="/conversation"
            className="inline-flex items-center rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium text-gray-800 hover:bg-gray-50"
          >
            대화 업로드 하러 가기
          </Link>
        </div>
      </main>
    );
  }
  // 여기부터는 conversationId는 있는데, 분석 데이터는 비동기로 가져오는 상태
  // 연습 시작 버튼 클릭 핸들러 (1단계: UI 목업만)
  // 연습 시작 버튼 핸들러
  function handleStartPractice(mode: 'chat' | 'voice') {
    if (!conversationId || startPractice.isPending) return;

    clearError();

    startPractice.mutate(
      {
        conversationId,
        mode,
      },
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
    <main className="mx-auto max-w-2xl space-y-6 p-6">
      <h1 className="text-xl font-semibold">연습 준비하기</h1>

      {/* 서버 에러 알림 */}
      {serverError && (
        <ErrorAlert message={serverError} />
      )}

      {/* 분석 결과 상태 안내 */}
      {isLoading && (
        <p className="text-sm text-gray-500">
          이전 대화 분석 결과를 불러오는 중이에요…
        </p>
      )}

      {isError && (
        <p className="text-sm text-red-600">
          이전 대화 분석 결과를 불러오지 못했어요. 잠시 후 다시 시도해 주세요.
        </p>
      )}

      {/* 분석 데이터가 준비된 경우에만 요약/안내를 보여줌 */}
      {data && data.status === 'ready' && (
        <section className="space-y-4 rounded-lg border bg-white p-4 text-sm">
          <div>
            <h2 className="text-sm font-semibold">이전 대화 한 줄 요약</h2>
            <p className="mt-1 whitespace-pre-line text-gray-700">
              {data.summary}
            </p>
          </div>

          {typeof data.score === 'number' && (
            <div className="mt-3">
              <h3 className="text-xs font-medium text-gray-500">
                말하기 점수(연습 기준)
              </h3>
              <p className="mt-1 text-base font-semibold">
                {(data.score * 100).toFixed(0)}점 / 100점
              </p>
            </div>
          )}

          <div className="mt-4">
            <h2 className="text-sm font-semibold">이번 연습에서 집중해 볼 부분</h2>
            <p className="mt-1 text-gray-700">
              분석 결과를 기반으로, 실제 가족 대화 상황을 가정하고
              <br />
              말투, 감정 표현, 질문 방식 등을 연습해 볼 수 있어요.
            </p>
          </div>
        </section>
      )}

      {/* 연습 모드 선택 버튼 */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium">연습 방식 선택</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => handleStartPractice('chat')}
            disabled={startPractice.isPending}
            className="rounded-lg border border-gray-300 bg-white px-4 py-3 text-left text-sm font-medium hover:border-black hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <div className="text-base">실시간 채팅으로 연습하기</div>
            <p className="mt-1 text-xs text-gray-600">
              문장으로 천천히 연습하고 싶은 경우,
              <br />
              채팅 형태로 말하기를 연습해 보세요.
            </p>
          </button>

          <button
            type="button"
            onClick={() => handleStartPractice('voice')}
            disabled={startPractice.isPending}
            className="rounded-lg border border-gray-300 bg-white px-4 py-3 text-left text-sm font-medium hover:border-black hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            <div className="text-base">음성대화로 연습하기</div>
            <p className="mt-1 text-xs text-gray-600">
              실제 대화처럼 말하고 듣는 연습을 하고 싶다면,
              <br />
              음성 대화 모드로 연습해 보세요.
            </p>
          </button>
        </div>

        {startPractice.isPending && (
          <p className="text-xs text-gray-500">연습 세션을 준비하고 있어요…</p>
        )}
      </section>
    </main>
  );
}
