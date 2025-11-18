'use client';

import { useAnalysis } from "@/hooks/useAnalysis";
import { analysisHistoryStorage, type AnalysisHistoryItem } from "@/utils/analysisHistoryStorage";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function AnalysisIndexPage() {
  const router = useRouter();
  const [history, setHistory] = useState<AnalysisHistoryItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  
  const safeId = selectedId ?? '';
  const { data, isLoading } = useAnalysis(safeId);

  // 히스토리 로드
  useEffect(() => {
    const loadedHistory = analysisHistoryStorage.getAll();
    setHistory(loadedHistory);
    
    // 최근 분석이 있으면 자동 선택
    const latest = analysisHistoryStorage.getLatest();
    if (latest && latest.status === 'ready') {
      setSelectedId(latest.conversationId);
    }
  }, []);

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

  // 분석 삭제
  const handleDeleteAnalysis = (conversationId: string) => {
    if (confirm('이 분석 결과를 삭제하시겠습니까?')) {
      analysisHistoryStorage.remove(conversationId);
      setHistory(analysisHistoryStorage.getAll());
      
      // 현재 선택된 분석이 삭제된 경우 선택 해제
      if (selectedId === conversationId) {
        setSelectedId(null);
      }
    }
  };

  return (
    <main className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold">분석</h1>
        <p className="text-sm text-gray-600">이전 분석 결과를 확인하거나 새로운 분석을 시작하세요.</p>
      </header>

      {/* 새 분석 시작 */}
      <section className="rounded-lg border bg-gradient-to-r from-orange-50 to-red-50 p-4">
        <h2 className="font-medium mb-2">새 분석 시작</h2>
        <Link 
          href="/conversation" 
          className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-all"
        >
          대화 업로드하기
        </Link>
      </section>

      {/* 분석 히스토리 */}
      {history.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-lg font-medium">이전 분석 결과</h2>
          <div className="grid gap-3">
            {history.map((item) => (
              <div
                key={item.conversationId}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedId === item.conversationId 
                    ? 'border-orange-500 bg-orange-50' 
                    : 'border-gray-200 hover:border-gray-300 bg-white'
                }`}
                onClick={() => handleSelectAnalysis(item.conversationId)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">
                        {item.title || `분석 ${item.conversationId.slice(0, 8)}...`}
                      </span>
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        item.status === 'ready' ? 'bg-green-100 text-green-700' :
                        item.status === 'processing' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {item.status === 'ready' ? '완료' : 
                         item.status === 'processing' ? '처리중' : '실패'}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">
                      {new Date(item.createdAt).toLocaleString('ko-KR')}
                    </p>
                    {item.summary && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">
                        {item.summary}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {item.status === 'ready' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          router.push(`/analysis/${item.conversationId}/summary`);
                        }}
                        className="px-3 py-1 text-xs bg-orange-500 text-white rounded hover:bg-orange-600 transition-colors"
                      >
                        보기
                      </button>
                    )}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteAnalysis(item.conversationId);
                      }}
                      className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                      title="삭제"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 선택된 분석의 로딩 상태 */}
      {selectedId && isLoading && (
        <section className="rounded-lg border bg-white p-4">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-orange-500 rounded-full animate-spin"></div>
            <span className="text-sm text-gray-600">분석 결과를 불러오는 중...</span>
          </div>
        </section>
      )}

      {/* 히스토리가 없을 때 */}
      {history.length === 0 && (
        <section className="text-center py-12">
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-lg font-medium mb-2">아직 분석 결과가 없습니다</h3>
          <p className="text-sm text-gray-600 mb-4">
            첫 번째 대화를 업로드하고 분석을 시작해보세요.
          </p>
          <Link 
            href="/conversation" 
            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-all"
          >
            대화 업로드하기
          </Link>
        </section>
      )}
    </main>
  );
}