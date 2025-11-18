'use client';
import { AnalysisRes } from "@/apis/analysis";
import { useAnalysis } from "@/hooks/useAnalysis";
import { useParams } from "next/navigation";

export default function ResultsEmotionPage() {
  const { conversationId } = useParams();
  const id = Array.isArray(conversationId) ? conversationId[0] : conversationId as string;
  const { data, isLoading, isError, error } = useAnalysis(id);
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">감정 분석 결과를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-red-600">{(error as Error)?.message ?? '감정 분석 결과를 불러올 수 없습니다'}</p>
        </div>
      </div>
    );
  }

  if (data.status !== 'ready' && data.status !== 'completed') {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">현재 상태: {data.status}</p>
        </div>
      </div>
    );
  }
  
  const { summary, statistics, style_analysis, score, confidence_score} = data;
  const MY_SPEAKER_ID = '1'; // TODO: 실제 사용자/선택 화자 ID로 교체
  const myStyle = (style_analysis as AnalysisRes['style_analysis'] | undefined)?.[MY_SPEAKER_ID] ?? null;
  
  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="space-y-8">
        {/* 헤더 */}
        <header className="text-center">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-pink-100 to-purple-100 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-800">감정 분석</h1>
          </div>
          <p className="text-gray-600 text-lg">대화 속 감정과 통계를 분석한 결과입니다</p>
        </header>

        {/* 통계 분석 */}
        <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-800">통계 분석</h3>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* 사용자 통계 */}
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-6 border border-green-100">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <h4 className="font-semibold text-green-800">사용자</h4>
              </div>
              <div className="space-y-4 text-sm">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-green-700">총 단어:</span>
                    <span className="font-medium text-green-800">{statistics?.user?.word_count ?? 0}</span>
                  </div>
                  <div className="w-full bg-green-100 rounded-full h-2">
                    <div 
                      className="bg-green-300 h-2 rounded-full transition-all duration-1000" 
                      style={{ 
                        width: `${Math.min(100, ((statistics?.user?.word_count ?? 0) / Math.max(statistics?.user?.word_count ?? 1, statistics?.others?.word_count ?? 1)) * 100)}%` 
                      }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-green-700">고유 단어:</span>
                    <span className="font-medium text-green-800">{statistics?.user?.unique_words ?? 0}</span>
                  </div>
                  <div className="w-full bg-green-100 rounded-full h-2">
                    <div 
                      className="bg-green-300 h-2 rounded-full transition-all duration-1000" 
                      style={{ 
                        width: `${Math.min(100, ((statistics?.user?.unique_words ?? 0) / Math.max(statistics?.user?.unique_words ?? 1, statistics?.others?.unique_words ?? 1)) * 100)}%` 
                      }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-green-700">평균 문장 길이:</span>
                    <span className="font-medium text-green-800">{statistics?.user?.avg_sentence_length ?? 0}</span>
                  </div>
                  <div className="w-full bg-green-100 rounded-full h-2">
                    <div 
                      className="bg-green-300 h-2 rounded-full transition-all duration-1000" 
                      style={{ 
                        width: `${Math.min(100, ((statistics?.user?.avg_sentence_length ?? 0) / Math.max(statistics?.user?.avg_sentence_length ?? 1, statistics?.others?.avg_sentence_length ?? 1)) * 100)}%` 
                      }}
                    ></div>
                  </div>
                </div>
                
                {!!(statistics?.user?.top_words?.length) && (
                  <div className="pt-2 border-t border-green-200">
                    <span className="text-green-700 text-xs">자주 사용하는 단어:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {statistics?.user?.top_words?.slice(0,5).map((word, idx) => (
                        <span key={idx} className="bg-green-200 text-green-800 px-2 py-1 rounded text-xs">
                          {word}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 상대방 통계 */}
            <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-100">
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <h4 className="font-semibold text-blue-800">상대방</h4>
              </div>
              <div className="space-y-4 text-sm">
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-blue-700">총 단어:</span>
                    <span className="font-medium text-blue-800">{statistics?.others?.word_count ?? 0}</span>
                  </div>
                  <div className="w-full bg-blue-100 rounded-full h-2">
                    <div 
                      className="bg-blue-300 h-2 rounded-full transition-all duration-1000" 
                      style={{ 
                        width: `${Math.min(100, ((statistics?.others?.word_count ?? 0) / Math.max(statistics?.user?.word_count ?? 1, statistics?.others?.word_count ?? 1)) * 100)}%` 
                      }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-blue-700">고유 단어:</span>
                    <span className="font-medium text-blue-800">{statistics?.others?.unique_words ?? 0}</span>
                  </div>
                  <div className="w-full bg-blue-100 rounded-full h-2">
                    <div 
                      className="bg-blue-300 h-2 rounded-full transition-all duration-1000" 
                      style={{ 
                        width: `${Math.min(100, ((statistics?.others?.unique_words ?? 0) / Math.max(statistics?.user?.unique_words ?? 1, statistics?.others?.unique_words ?? 1)) * 100)}%` 
                      }}
                    ></div>
                  </div>
                </div>
                
                <div>
                  <div className="flex justify-between mb-1">
                    <span className="text-blue-700">평균 문장 길이:</span>
                    <span className="font-medium text-blue-800">{statistics?.others?.avg_sentence_length ?? 0}</span>
                  </div>
                  <div className="w-full bg-blue-100 rounded-full h-2">
                    <div 
                      className="bg-blue-300 h-2 rounded-full transition-all duration-1000" 
                      style={{ 
                        width: `${Math.min(100, ((statistics?.others?.avg_sentence_length ?? 0) / Math.max(statistics?.user?.avg_sentence_length ?? 1, statistics?.others?.avg_sentence_length ?? 1)) * 100)}%` 
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 비교 차트 */}
          {statistics?.user && statistics?.others && (
            <div className="mt-8 bg-gray-50 rounded-xl p-6">
              <h4 className="font-semibold text-gray-800 mb-4 text-center">대화 참여도 비교</h4>
              <div className="flex items-center justify-center gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{statistics?.user?.word_count ?? 0}</div>
                  <div className="text-sm text-gray-600">사용자</div>
                </div>
                <div className="flex-1 max-w-xs">
                  <div className="flex h-8 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="bg-green-500 transition-all duration-1000"
                      style={{ 
                        width: `${((statistics?.user?.word_count ?? 0) / Math.max((statistics?.user?.word_count ?? 0) + (statistics?.others?.word_count ?? 0), 1)) * 100}%` 
                      }}
                    ></div>
                    <div 
                      className="bg-blue-500 transition-all duration-1000"
                      style={{ 
                        width: `${((statistics?.others?.word_count ?? 0) / Math.max((statistics?.user?.word_count ?? 0) + (statistics?.others?.word_count ?? 0), 1)) * 100}%` 
                      }}
                    ></div>
                  </div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{statistics?.others?.word_count ?? 0}</div>
                  <div className="text-sm text-gray-600">상대방</div>
                </div>
              </div>
            </div>
          )}

          {/* 비교 분석 */}
          {statistics?.comparison && (
            <div className="mt-6 bg-orange-50 rounded-xl p-6 border border-orange-200">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-6 h-6 bg-orange-100 rounded-lg flex items-center justify-center">
                  <svg className="w-3 h-3 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h4 className="font-semibold text-orange-800">비교 분석</h4>
              </div>
              <p className="text-orange-700 leading-relaxed">{statistics?.comparison}</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
