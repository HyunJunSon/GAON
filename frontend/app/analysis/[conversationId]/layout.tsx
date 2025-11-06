'use client';

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

  // 현재 경로와 비교하여 active 판별
  const base = `/analysis/${conversationId}`;
  const tabs = [
    { href: `${base}/summary`, label: '요약' },
    { href: `${base}/emotion`, label: '감정' },
    { href: `${base}/dialog`,  label: '대화록' },
  ];

  return (
    <main className="space-y-6">
      {/* 상단 헤더(필요 시 간결히) */}
      <header>
        <h1 className="text-2xl font-semibold">분석 결과</h1>
        <p className="text-sm text-gray-600">
          대화 ID: <code className="rounded bg-gray-100 px-1 py-0.5">{conversationId}</code>
        </p>
      </header>

      {/* 탭 네비 */}
      <nav className="border-b mb-0">
        <ul className="flex gap-4">
          {tabs.map(({ href, label }) => {
            const active = pathname === href;
            // 같은 페이지로 이동 방지: active면 span으로 렌더
            return (
              <li key={href}>
                {active ? (
                  <span
                    aria-current="page"
                    className="inline-block px-2 pb-2 text-sm font-medium border-b-2 border-black"
                  >
                    {label}
                  </span>
                ) : (
                  <Link
                    href={href}
                    className="inline-block px-2 pb-2 text-sm text-gray-600 hover:text-black"
                    prefetch
                  >
                    {label}
                  </Link>
                )}
              </li>
            );
          })}
        </ul>
      </nav>

      {/* 실제 탭 콘텐츠 */}
      <section>{children}</section>
    </main>
  );
}