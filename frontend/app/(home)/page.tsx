'use client';

import Link from "next/link";
import { useLogout } from "@/hooks/useAuth";
import GaonLogo from "@/components/ui/GaonLogo";

export default function HomePage() {
  const { mutate, isPending } = useLogout();

  return (
    <main className="mx-auto max-w-4xl p-6 space-y-8">
      {/* 히어로 섹션 */}
      <div className="text-center py-12 bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl border border-orange-100">
        <GaonLogo size="lg" variant="full" className="justify-center mb-6" />
        <h1 className="text-3xl font-bold text-gray-800 mb-3">대화에 온도를 더하다</h1>
        <p className="text-gray-600 text-lg">AI 기반 대화 분석으로 인간관계에 따뜻함을 더하는 서비스</p>
      </div>

      {/* 주요 기능 카드 */}
      <div className="grid md:grid-cols-2 gap-6">
        <Link href="/conversation" className="group">
          <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all duration-200 hover:border-orange-200">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-red-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-800 group-hover:text-orange-600 transition-colors">대화 분석</h3>
                <p className="text-gray-600">음성 대화를 분석하여 관계의 온도를 측정해보세요</p>
              </div>
            </div>
            <div className="text-sm text-orange-600 font-medium">시작하기 →</div>
          </div>
        </Link>

        <Link href="/analysis" className="group">
          <div className="bg-white rounded-xl border border-gray-200 p-6 hover:shadow-lg transition-all duration-200 hover:border-orange-200">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-red-100 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-800 group-hover:text-orange-600 transition-colors">분석 결과</h3>
                <p className="text-gray-600">이전 대화 분석 결과를 확인하고 인사이트를 얻어보세요</p>
              </div>
            </div>
            <div className="text-sm text-orange-600 font-medium">결과 보기 →</div>
          </div>
        </Link>
      </div>

      {/* 온도 표시 위젯 (예시) */}
      <div className="bg-gradient-to-r from-orange-500 to-red-500 rounded-xl p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-2">현재 관계 온도</h3>
            <p className="text-orange-100">최근 대화를 바탕으로 측정된 관계의 따뜻함 정도입니다</p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold">36.5°</div>
            <div className="text-orange-200 text-sm">따뜻함</div>
          </div>
        </div>
      </div>

      {/* 로그아웃 버튼 */}
      <div className="text-center pt-8 border-t border-gray-200">
        <button
          onClick={() => mutate()}
          disabled={isPending}
          className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          {isPending ? '로그아웃 중…' : '로그아웃'}
        </button>
      </div>
    </main>
  );
}
