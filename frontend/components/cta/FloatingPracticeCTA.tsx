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
            ? 'static mt-4' // 도킹: 문서 흐름으로, 내용 가리지 않음
            : [
                // 플로팅: 화면 하단 고정 + 모바일 네비 높이만큼 띄우기 + 안전영역
                'fixed inset-x-0 z-50',
                'bottom-[calc(56px+env(safe-area-inset-bottom))] md:bottom-0', // <-- 핵심
              ].join(' '),
        ].join(' ')}
      >
        <div
          className={[
            // 탭 본문 폭에 맞춤 (프로젝트 기준으로 조정: max-w-2xl 사용)
            'mx-auto w-full max-w-2xl px-4 py-3',
            // 플로팅일 때만 버튼 인터랙션 허용
            docked ? '' : 'pointer-events-auto',
          ].join(' ')}
        >
          <button
            type="button"
            onClick={goPractice}
            className={[
              'group w-full rounded-xl cursor-pointer',
              // 글라스: 반투명 + 블러 + 약한 링/보더
              'bg-black/50 text-white border border-white/10 ring-1 ring-white/10',
              'backdrop-blur supports-[backdrop-filter]:backdrop-blur-md backdrop-saturate-150',
              // 기본 그림자
              'shadow-md',
              // 패딩(모바일 하단 안전영역 고려)
              'py-3 text-sm font-medium',
              'pb-[calc(0.75rem+env(safe-area-inset-bottom))]',
              // 인터랙션: 자연스러운 전환 + 호버/액티브 변형
              'transition-all duration-200 ease-out',
              'hover:bg-black/55 hover:shadow-lg hover:-translate-y-0.5',
              'active:translate-y-0',
              // 접근성 포커스
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40',
            ].join(' ')}
          >
            연습하러 가기
          </button>
        </div>
      </div>
    </>
  );
}