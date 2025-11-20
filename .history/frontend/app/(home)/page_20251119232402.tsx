'use client';

import Link from "next/link";
import { useLogout } from "@/hooks/useAuth";
import GaonLogo from "@/components/ui/GaonLogo";

export default function HomePage() {
  const { mutate, isPending } = useLogout();

  return (
    <main className="mx-auto w-full max-w-5xl space-y-8 px-4 pb-16 pt-8 md:space-y-10 md:px-0">
      {/* 헤더 섹션 - 브랜드 디자인 적용 */}
      <header className="rounded-3xl border border-orange-200 bg-gradient-to-br from-orange-50 via-white to-red-100 p-8 shadow-inner">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 text-white shadow-lg">
                <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-orange-600">Home</p>
                <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">대화에 온도를 더하다</h1>
              </div>
            </div>
            <p className="text-base leading-relaxed text-gray-600 md:text-lg">
              AI 기반 대화 분석으로 인간관계에 따뜻함을 더하는 서비스입니다. 
              음성 대화를 분석하여 관계의 온도를 측정하고 개선점을 찾아보세요.
            </p>
          </div>
          <div className="rounded-2xl border border-white/80 bg-white/70 px-6 py-5 shadow-lg backdrop-blur">
            <p className="text-sm font-medium text-gray-500">현재 관계 온도</p>
            <div className="mt-3 flex items-center gap-3">
              <span className="text-4xl font-bold text-gray-900">36.5°</span>
              <div className="text-sm text-gray-500">
                <p className="font-semibold text-orange-600">따뜻함</p>
                <p className="text-xs text-gray-400">최근 대화 기준</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 히어로 섹션 */}
      <div className="text-center py-12 bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl border border-orange-100">
        {/* SVG 로고 */}
        <div className="mb-8 flex justify-center">
          <svg viewBox="0 0 400 400" className="w-40 h-40" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="warmGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{stopColor:"#FF6B6B", stopOpacity:1}} />
                <stop offset="50%" style={{stopColor:"#FFA07A", stopOpacity:1}} />
                <stop offset="100%" style={{stopColor:"#FFD93D", stopOpacity:1}} />
              </linearGradient>
              
              <radialGradient id="bgGradient" cx="50%" cy="50%" r="50%">
                <stop offset="0%" style={{stopColor:"#FFF5F5", stopOpacity:1}} />
                <stop offset="100%" style={{stopColor:"#FFFFFF", stopOpacity:1}} />
              </radialGradient>
              
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            <rect width="400" height="400" fill="url(#bgGradient)"/>
            
            <g transform="translate(200, 160)">
              <path d="M 0,25 
                       C -50,0 -75,-5 -75,25
                       C -75,60 -40,90 0,115
                       C 40,90 75,60 75,25
                       C 75,-5 50,0 0,25 Z" 
                    fill="url(#warmGradient)" 
                    opacity="0.3"
                    filter="url(#glow)"/>
              
              <defs>
                <clipPath id="heartClip">
                  <path d="M 0,25 
                           C -50,0 -75,-5 -75,25
                           C -75,60 -40,90 0,115
                           C 40,90 75,60 75,25
                           C 75,-5 50,0 0,25 Z"/>
                </clipPath>
              </defs>
              
              <g clipPath="url(#heartClip)">
                <rect x="-75" y="115" width="150" height="0" fill="url(#warmGradient)" opacity="0.9">
                  <animate attributeName="y" 
                           values="115;-5;115" 
                           dur="4s" 
                           repeatCount="indefinite"/>
                  <animate attributeName="height" 
                           values="0;120;0" 
                           dur="4s" 
                           repeatCount="indefinite"/>
                </rect>
              </g>
              
              <g transform="translate(0, -10)">
                <rect x="-3" y="0" width="6" height="60" fill="#FFFFFF" opacity="0.5" rx="3"/>
                <circle cx="0" cy="65" r="6" fill="#FFFFFF" opacity="0.6"/>
                <circle cx="0" cy="65" r="4" fill="#FF6B6B" opacity="0.8"/>
              </g>
              
              <circle cx="0" cy="30" r="60" fill="none" stroke="#FFB6B6" strokeWidth="2" opacity="0.3">
                <animate attributeName="r" values="60;80;60" dur="4s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.3;0;0.3" dur="4s" repeatCount="indefinite"/>
              </circle>
              <circle cx="0" cy="30" r="60" fill="none" stroke="#FFC8C8" strokeWidth="2" opacity="0.2">
                <animate attributeName="r" values="60;90;60" dur="4s" begin="1s" repeatCount="indefinite"/>
                <animate attributeName="opacity" values="0.2;0;0.2" dur="4s" begin="1s" repeatCount="indefinite"/>
              </circle>
            </g>
            
            <g opacity="0.4">
              <line x1="120" y1="180" x2="180" y2="180" stroke="#FF8C8C" strokeWidth="1.5"/>
              <line x1="220" y1="180" x2="280" y2="180" stroke="#FF8C8C" strokeWidth="1.5"/>
              <circle cx="120" cy="180" r="3" fill="#FF8C8C"/>
              <circle cx="280" cy="180" r="3" fill="#FF8C8C"/>
            </g>
            
            {/* 브랜드명: GAON (3D 입체 효과) */}
            <defs>
              <linearGradient id="textGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style={{stopColor:"#FF8C8C", stopOpacity:1}} />
                <stop offset="50%" style={{stopColor:"#FF6B6B", stopOpacity:1}} />
                <stop offset="100%" style={{stopColor:"#E85858", stopOpacity:1}} />
              </linearGradient>
              
              <filter id="textShadow">
                <feGaussianBlur in="SourceAlpha" stdDeviation="2"/>
                <feOffset dx="2" dy="4" result="offsetblur"/>
                <feComponentTransfer>
                  <feFuncA type="linear" slope="0.3"/>
                </feComponentTransfer>
                <feMerge>
                  <feMergeNode/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>
            
            {/* 그림자 레이어들 (3D 깊이감) */}
            <text x="204" y="314" 
                  fontFamily="'Quicksand', 'Fredoka', 'Nunito', sans-serif" 
                  fontSize="48" 
                  fontWeight="700" 
                  fill="#D85555" 
                  textAnchor="middle"
                  letterSpacing="6"
                  opacity="0.3">GAON</text>
            
            <text x="202" y="312" 
                  fontFamily="'Quicksand', 'Fredoka', 'Nunito', sans-serif" 
                  fontSize="48" 
                  fontWeight="700" 
                  fill="#E85858" 
                  textAnchor="middle"
                  letterSpacing="6"
                  opacity="0.5">GAON</text>
            
            {/* 메인 텍스트 */}
            <text x="200" y="310" 
                  fontFamily="'Quicksand', 'Fredoka', 'Nunito', sans-serif" 
                  fontSize="48" 
                  fontWeight="700" 
                  fill="url(#textGradient)" 
                  textAnchor="middle"
                  letterSpacing="6"
                  filter="url(#textShadow)">GAON</text>
            
            {/* 하이라이트 효과 */}
            <text x="200" y="310" 
                  fontFamily="'Quicksand', 'Fredoka', 'Nunito', sans-serif" 
                  fontSize="48" 
                  fontWeight="700" 
                  fill="#FFAAAA" 
                  textAnchor="middle"
                  letterSpacing="6"
                  opacity="0.4"
                  transform="translate(0, -1)">GAON</text>
            
            {/* 한글명: 가온 */}
            <text x="200" y="340" 
                  fontFamily="'Noto Serif KR', serif" 
                  fontSize="22" 
                  fontWeight="400" 
                  fill="#FF8C8C" 
                  textAnchor="middle"
                  letterSpacing="2">加溫</text>
            
            {/* 서브 태그라인 */}
            <text x="200" y="365" 
                  fontFamily="'Noto Sans KR', sans-serif" 
                  fontSize="12" 
                  fontWeight="300" 
                  fill="#999999" 
                  textAnchor="middle"
                  letterSpacing="1">마음의 온도를 측정하여, 온기를 더합니다</text>
          </svg>
        </div>
        
      </div>

      {/* 주요 기능 카드 */}
      <div className="grid md:grid-cols-2 gap-6">
        <Link href="/conversation" className="group">
          <div className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg transition-all duration-300 hover:shadow-xl hover:border-orange-200 hover:-translate-y-1">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 flex items-center justify-center text-orange-600 group-hover:scale-110 transition-transform duration-300">
                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 group-hover:text-orange-600 transition-colors mb-2">대화 분석</h3>
                <p className="text-gray-600 leading-relaxed text-sm">음성 대화를 분석하여 관계의 온도를 측정해보세요</p>
              </div>
            </div>
            <div className="flex items-center text-orange-600 font-semibold group-hover:gap-3 transition-all duration-300">
              <span>시작하기</span>
              <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </Link>

        <Link href="/analysis" className="group">
          <div className="rounded-2xl border border-orange-100 bg-white p-8 shadow-lg transition-all duration-300 hover:shadow-xl hover:border-orange-200 hover:-translate-y-1">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-orange-500/20 to-red-500/20 flex items-center justify-center text-orange-600 group-hover:scale-110 transition-transform duration-300">
                <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-semibold text-gray-900 group-hover:text-orange-600 transition-colors mb-2">분석 결과</h3>
                <p className="text-gray-600 leading-relaxed text-sm">이전 대화 분석 결과를 확인하고 인사이트를 얻어보세요</p>
              </div>
            </div>
            <div className="flex items-center text-orange-600 font-semibold group-hover:gap-3 transition-all duration-300">
              <span>결과 보기</span>
              <svg className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </div>
        </Link>
      </div>

      {/* 로그아웃 버튼 */}
      <div className="text-center pt-8 border-t border-gray-200">
        <button
          onClick={() => mutate()}
          disabled={isPending}
          className="px-6 py-3 bg-gradient-to-r from-gray-100 to-gray-200 hover:from-gray-200 hover:to-gray-300 text-gray-700 rounded-xl transition-all duration-200 shadow-sm hover:shadow-md disabled:opacity-50 flex items-center gap-2 mx-auto"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          {isPending ? '로그아웃 중…' : '로그아웃'}
        </button>
      </div>
    </main>
  );
}
