'use client';

import { useAnalysis } from "@/hooks/useAnalysis";
import { fetchAnalysisList, type AnalysisListItem } from "@/apis/analysis";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";

export default function AnalysisIndexPage() {
  const router = useRouter();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  // API에서 분석 목록 가져오기
  const { data: history = [], isLoading: isLoadingList } = useQuery({
    queryKey: ['analysisList'],
    queryFn: fetchAnalysisList,
    staleTime: 30_000,
  });

  const safeId = selectedId ?? "";
  const { data, isLoading } = useAnalysis(safeId);

  const readyCount = history.filter((item) => item.status === "ready").length;
  const processingCount = history.filter((item) => item.status === "processing").length;
  const failedCount = history.filter((item) => item.status === "failed").length;

  // 최근 분석이 있으면 자동 선택
  useEffect(() => {
    if (history.length > 0 && !selectedId) {
      const latest = history[0];
      if (latest.status === 'ready') {
        setSelectedId(latest.conversationId);
      }
    }
  }, [history, selectedId]);

  // 분석 완료 시 해당 페이지로 이동
  useEffect(() => {
    if (data?.status === 'ready' && selectedId) {
      router.replace(`/analysis/${selectedId}/summary`);
    }
  }, [data?.status, selectedId, router]);

  // 분석 선택
  const handleSelectAnalysis = (conversationId: string) => {
    setSelectedId(conversationId);
  };

  return (
    <main className="mx-auto w-full max-w-5xl space-y-8 px-4 pb-16 pt-8 md:space-y-10 md:px-0">
      {/* 헤더 섹션 - 브랜드 디자인 적용 */}
      <header className="rounded-3xl border border-orange-200 bg-gradient-to-br from-orange-50 via-white to-red-100 p-8 shadow-inner">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 text-white shadow-lg">
                <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-orange-600">Analysis Workspace</p>
                <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">분석 인덱스</h1>
              </div>
            </div>
            <p className="text-base leading-relaxed text-gray-600 md:text-lg">
              이전 분석 결과를 확인하거나 새로운 분석을 시작하세요. 최근 분석 히스토리를 기반으로
              완료율과 진행 상태를 한눈에 확인할 수 있습니다.
            </p>
          </div>

          <div className="rounded-2xl border border-white/80 bg-white/70 px-6 py-5 shadow-lg backdrop-blur">
            <p className="text-sm font-medium text-gray-500">최근 분석 상태</p>
            <div className="mt-3 flex items-center gap-3">
              <span className="text-4xl font-bold text-gray-900">{readyCount}</span>
              <div className="text-sm text-gray-500">
                <p className="font-semibold text-green-600">완료</p>
                <p className="font-semibold text-yellow-600">진행중 {processingCount}</p>
              </div>
            </div>
            <p className="mt-2 text-xs text-gray-400">
              실패 {failedCount}건 · 총 {history.length}건의 분석 기록
            </p>
          </div>
        </div>
      </header>

      {/* 새 분석 시작 카드 */}
      <section className="rounded-2xl border border-orange-100 bg-white p-6 shadow-lg md:p-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-800">새 분석 시작</h2>
        </div>
        <p className="text-gray-600 mb-4 leading-relaxed">
          대화 파일을 업로드하여 새로운 분석을 시작해보세요.
        </p>
        <Link 
          href="/conversation" 
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:from-orange-600 hover:to-red-600 transition-all shadow-lg hover:shadow-xl font-medium text-base min-h-[44px]"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          대화 업로드하기
        </Link>
      </section>

      {/* 로딩 상태 */}
      {isLoadingList && (
        <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 border-2 border-gray-300 border-t-orange-500 rounded-full animate-spin"></div>
            <span className="text-gray-600 font-medium">분석 목록을 불러오는 중...</span>
          </div>
        </section>
      )}

      {/* 분석 히스토리 */}
      {!isLoadingList && history.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-800">이전 분석 결과</h2>
          </div>
          
          <div className="grid gap-4">
            {history.map((item) => (
              <div
                key={item.conversationId}
                className={`bg-white rounded-2xl shadow-lg border transition-all cursor-pointer hover:shadow-xl ${
                  selectedId === item.conversationId 
                    ? 'border-orange-500 ring-2 ring-orange-200' 
                    : 'border-gray-200 hover:border-orange-300'
                }`}
                onClick={() => handleSelectAnalysis(item.conversationId)}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-3 flex-wrap">
                        <h3 className="text-lg font-bold text-gray-800 break-words">
                          {item.title || `분석 ${item.conversationId.slice(0, 8)}...`}
                        </h3>
                        <span className={`px-3 py-1 text-sm rounded-full font-medium flex-shrink-0 ${
                          item.status === 'ready' ? 'bg-green-100 text-green-700' :
                          item.status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {item.status === 'ready' ? '완료' : 
                           item.status === 'processing' ? '처리중' : '실패'}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2 mb-3 text-sm text-gray-500">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {new Date(item.createdAt).toLocaleString('ko-KR')}
                      </div>
                      
                      {item.summary && (
                        <p className="text-gray-600 line-clamp-2 leading-relaxed">
                          {item.summary}
                        </p>
                      )}
                    </div>
                    
                    <div className="flex flex-col gap-2 flex-shrink-0">
                      {item.status === 'ready' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/analysis/${item.conversationId}/summary`);
                          }}
                          className="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-all font-medium text-sm min-h-[44px] shadow-md"
                        >
                          보기
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 선택된 분석의 로딩 상태 */}
      {selectedId && isLoading && (
        <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 border-2 border-gray-300 border-t-orange-500 rounded-full animate-spin"></div>
            <span className="text-gray-600 font-medium">분석 결과를 불러오는 중...</span>
          </div>
        </section>
      )}

      {/* 히스토리가 없을 때 */}
      {!isLoadingList && history.length === 0 && (
        <section className="bg-white rounded-2xl shadow-lg border border-gray-200 p-12 text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-orange-100 to-red-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-gray-800 mb-3">아직 분석 결과가 없습니다</h3>
          <p className="text-gray-600 mb-6 leading-relaxed max-w-md mx-auto">
            첫 번째 대화를 업로드하고 AI 분석을 통해 관계의 온도를 측정해보세요.
          </p>
          <Link 
            href="/conversation" 
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:from-orange-600 hover:to-red-600 transition-all shadow-lg hover:shadow-xl font-medium min-h-[44px]"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            첫 분석 시작하기
          </Link>
        </section>
      )}
    </main>
  );
}

  return (
    <main className="mx-auto w-full max-w-5xl space-y-8 px-4 pb-16 pt-8 md:space-y-10 md:px-0">
      {/* 헤더 섹션 - 브랜드 디자인 적용 */}
      <header className="rounded-3xl border border-orange-200 bg-gradient-to-br from-orange-50 via-white to-red-100 p-8 shadow-inner">
        <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-red-500 text-white shadow-lg">
                <svg className="h-7 w-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-orange-600">Analysis Workspace</p>
                <h1 className="text-3xl font-bold text-gray-900 md:text-4xl">분석 인덱스</h1>
              </div>
            </div>
            <p className="text-base leading-relaxed text-gray-600 md:text-lg">
              이전 분석 결과를 확인하거나 새로운 분석을 시작하세요. 최근 분석 히스토리를 기반으로
              완료율과 진행 상태를 한눈에 확인할 수 있습니다.
            </p>
          </div>

          <div className="rounded-2xl border border-white/80 bg-white/70 px-6 py-5 shadow-lg backdrop-blur">
            <p className="text-sm font-medium text-gray-500">최근 분석 상태</p>
            <div className="mt-3 flex items-center gap-3">
              <span className="text-4xl font-bold text-gray-900">{readyCount}</span>
              <div className="text-sm text-gray-500">
                <p className="font-semibold text-green-600">완료</p>
                <p className="font-semibold text-yellow-600">진행중 {processingCount}</p>
              </div>
            </div>
            <p className="mt-2 text-xs text-gray-400">
              실패 {failedCount}건 · 총 {history.length}건의 분석 기록
            </p>
          </div>
        </div>
      </header>

      {/* 새 분석 시작 카드 */}
      <section className="rounded-2xl border border-orange-100 bg-white p-6 shadow-lg md:p-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-green-100 to-emerald-100 rounded-xl flex items-center justify-center">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-800">새 분석 시작</h2>
        </div>
        <p className="text-gray-600 mb-4 leading-relaxed">
          대화 파일을 업로드하여 새로운 분석을 시작해보세요.
        </p>
        <Link 
          href="/conversation" 
          className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:from-orange-600 hover:to-red-600 transition-all shadow-lg hover:shadow-xl font-medium text-base min-h-[44px]"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          대화 업로드하기
        </Link>
      </section>

      {/* 분석 히스토리 */}
      {history.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center">
              <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-800">이전 분석 결과</h2>
          </div>
          
          <div className="grid gap-4">
            {history.map((item) => (
              <div
                key={item.conversationId}
                className={`bg-white rounded-2xl shadow-lg border transition-all cursor-pointer hover:shadow-xl ${
                  selectedId === item.conversationId 
                    ? 'border-orange-500 ring-2 ring-orange-200' 
                    : 'border-gray-200 hover:border-orange-300'
                }`}
                onClick={() => handleSelectAnalysis(item.conversationId)}
              >
                <div className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-3 flex-wrap">
                        <h3 className="text-lg font-bold text-gray-800 break-words">
                          {item.title || `분석 ${item.conversationId.slice(0, 8)}...`}
                        </h3>
                        <span className={`px-3 py-1 text-sm rounded-full font-medium flex-shrink-0 ${
                          item.status === 'ready' ? 'bg-green-100 text-green-700' :
                          item.status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {item.status === 'ready' ? '완료' : 
                           item.status === 'processing' ? '처리중' : '실패'}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2 mb-3 text-sm text-gray-500">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {new Date(item.createdAt).toLocaleString('ko-KR')}
                      </div>
                      
                      {item.summary && (
                        <p className="text-gray-600 line-clamp-2 leading-relaxed">
                          {item.summary}
                        </p>
                      )}
                    </div>
                    
                    <div className="flex flex-col gap-2 flex-shrink-0">
                      {item.status === 'ready' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            router.push(`/analysis/${item.conversationId}/summary`);
                          }}
                          className="px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-all font-medium text-sm min-h-[44px] shadow-md"
                        >
                          보기
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteAnalysis(item.conversationId);
                        }}
                        className="px-3 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm min-h-[44px] shadow-md"
                        title="삭제"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 선택된 분석의 로딩 상태 */}
      {selectedId && isLoading && (
        <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 border-2 border-gray-300 border-t-orange-500 rounded-full animate-spin"></div>
            <span className="text-gray-600 font-medium">분석 결과를 불러오는 중...</span>
          </div>
        </section>
      )}

      {/* 히스토리가 없을 때 */}
      {history.length === 0 && (
        <section className="bg-white rounded-2xl shadow-lg border border-gray-200 p-12 text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-orange-100 to-red-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-gray-800 mb-3">아직 분석 결과가 없습니다</h3>
          <p className="text-gray-600 mb-6 leading-relaxed max-w-md mx-auto">
            첫 번째 대화를 업로드하고 AI 분석을 통해 관계의 온도를 측정해보세요.
          </p>
          <Link 
            href="/conversation" 
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-xl hover:from-orange-600 hover:to-red-600 transition-all shadow-lg hover:shadow-xl font-medium min-h-[44px]"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            첫 분석 시작하기
          </Link>
        </section>
      )}
    </main>
  );
}
