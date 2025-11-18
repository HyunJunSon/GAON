'use client';

import FloatingPracticeCTA from '@/components/cta/FloatingPracticeCTA';
import ConfirmLink from '@/components/ui/ConfirmLink';
import { useAnalysis } from '@/hooks/useAnalysis';
import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';

/**
 * 탭 네비게이션 레이아웃
 * - 이 레이아웃은 (tabs) 그룹 하위 라우트(summary/emotion/dialog)에만 적용됨
 * - 현재 탭은 비활성(클릭 막기) 처리
 */
export default function AnalysisTabsLayout({ children }: { children: React.ReactNode }) {
  const params = useParams();
  const pathname = usePathname();

  const conversationId = Array.isArray(params.conversationId)
    ? params.conversationId[0]
    : (params.conversationId as string | undefined);
  // id가 null일 수 있으므로 빈 문자열로 대체하여 훅 호출 순서를 유지합니다.

  const safeId = conversationId ?? '';
  // ✅ 페이지에서 먼저 불러왔든, 여기서 처음이든 동일 queryKey로 캐시 재사용
  const { data, isLoading, isError, error } = useAnalysis(safeId);
  
  // 현재 경로와 비교하여 active 판별
  const base = `/analysis/${conversationId}`;
  const tabs = [
    { href: `${base}/summary`, label: '요약' },
    { href: `${base}/emotion`, label: '감정' },
    { href: `${base}/dialog`,  label: '대화록' },
  ];

  return (
    <main className="mx-auto max-w-6xl p-6">
      <div className="space-y-8">
        {/* 상단 헤더 */}
        <header className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
          <div className="flex items-start justify-between">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-red-100 rounded-xl flex items-center justify-center">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h1 className="text-3xl font-bold text-gray-800">분석 결과</h1>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center gap-4 text-sm">
                  {data?.confidence_score != null && (
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span className="text-gray-600">신뢰도:</span>
                      <span className="font-semibold text-green-600">{(data?.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {data?.updatedAt && (
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span className="text-gray-600">업데이트:</span>
                      <span className="font-medium text-gray-800">{new Date(data?.updatedAt).toLocaleString()}</span>
                    </div>
                  )}
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">대화 ID:</span>
                  <code className="bg-gray-100 text-gray-800 px-3 py-1 rounded-lg text-sm font-mono">{conversationId}</code>
                </div>
              </div>
            </div>

            {/* 로그아웃 버튼 */}
            <div className="flex gap-3">
              <ConfirmLink
                href="/conversation"
                className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-all duration-200 flex items-center gap-2"
                confirmTitle="다른 대화 분석하기"
                confirmDesc="이동하면 기존 대화 분석결과가 사라집니다. 계속하시겠습니까?"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                다른 대화 분석하기
              </ConfirmLink>
            </div>
          </div>
        </header>

        {/* 탭 네비게이션 */}
        <nav className="bg-white rounded-2xl shadow-lg border border-orange-100 overflow-hidden">
          <div className="flex">
            {tabs.map(({ href, label }, index) => {
              const active = pathname === href;
              const icons = [
                <svg key="summary" className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>,
                <svg key="emotion" className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>,
                <svg key="dialog" className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              ];

              return (
                <div key={href} className="flex-1">
                  {active ? (
                    <div className="px-6 py-4 bg-gradient-to-r from-orange-500 to-red-500 text-white">
                      <div className="flex items-center justify-center gap-2">
                        {icons[index]}
                        <span className="font-semibold">{label}</span>
                      </div>
                    </div>
                  ) : (
                    <Link
                      href={href}
                      className="block px-6 py-4 text-gray-600 hover:bg-gray-50 hover:text-gray-800 transition-all duration-200"
                      prefetch
                    >
                      <div className="flex items-center justify-center gap-2">
                        {icons[index]}
                        <span className="font-medium">{label}</span>
                      </div>
                    </Link>
                  )}
                </div>
              );
            })}
          </div>
        </nav>

        {/* 실제 탭 콘텐츠 */}
        <section>{children}</section>
        
        {/* 하단 CTA */}
        <FloatingPracticeCTA />
      </div>
    </main>
  );
}