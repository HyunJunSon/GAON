// components/cta/FloatingPracticeCTA.tsx
'use client';

import { useEffect, useRef, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function FloatingPracticeCTA() {
  const router = useRouter();
  const params = useParams<{ conversationId: string }>();
  const conversationId = Array.isArray(params.conversationId)
    ? params.conversationId[0]
    : params.conversationId;

  const [docked, setDocked] = useState(false);
  const sentinelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el) return;

    const io = new IntersectionObserver(
      (entries) => setDocked(entries[0].isIntersecting),
      { root: null, threshold: 0.01 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const goPractice = () => {
    router.push(`/practice?conversationId=${encodeURIComponent(conversationId ?? '')}`);
  };

  return (
    <>
      {/* 페이지 끝에 배치되어 도킹 전환을 알리는 센티넬 */}
      <div ref={sentinelRef} id="analysis-bottom-sentinel" className="h-1 w-full" />

      {/* CTA 래퍼 */}
      <div
        className={[
          'pointer-events-auto',
          docked
            ? 'static mt-8' // 도킹: 문서 흐름으로, 내용 가리지 않음
            : [
                // 플로팅: 화면 하단 고정 + 모바일 네비 높이만큼 띄우기 + 안전영역
                'fixed inset-x-0 z-50',
                'bottom-[calc(56px+env(safe-area-inset-bottom))] md:bottom-0',
              ].join(' '),
        ].join(' ')}
      >
        <div
          className={[
            // 탭 본문 폭에 맞춤
            'mx-auto w-full max-w-4xl px-6 py-4',
            // 플로팅일 때만 버튼 인터랙션 허용
            docked ? '' : 'pointer-events-auto',
          ].join(' ')}
        >
          <button
            type="button"
            onClick={goPractice}
            className={[
              'group w-full rounded-2xl cursor-pointer flex items-center justify-center gap-3',
              // GAON 브랜드 그라데이션
              'bg-gradient-to-r from-orange-500 to-red-500 text-white',
              'hover:from-orange-600 hover:to-red-600',
              // 그림자 및 애니메이션
              'shadow-lg hover:shadow-xl',
              'py-4 text-lg font-semibold',
              'pb-[calc(1rem+env(safe-area-inset-bottom))]',
              // 인터랙션
              'transition-all duration-200 ease-out',
              'hover:-translate-y-1 active:translate-y-0',
              // 접근성 포커스
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-300',
            ].join(' ')}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            연습하러 가기
          </button>
        </div>
      </div>
    </>
  );
}