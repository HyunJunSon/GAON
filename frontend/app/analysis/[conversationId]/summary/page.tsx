'use client';

import { AnalysisRes } from "@/apis/analysis";
import { useAnalysis } from "@/hooks/useAnalysis";
import { useParams } from "next/navigation";

export default function ResultsSummaryPage() {
  const { conversationId } = useParams();
  const id = Array.isArray(conversationId) ? conversationId[0] : conversationId as string;
  const { data, isLoading, isError, error } = useAnalysis(id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-orange-200 border-t-orange-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">분석 결과를 불러오는 중...</p>
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
          <p className="text-red-600">{(error as Error)?.message ?? '분석 결과를 불러올 수 없습니다'}</p>
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

  const { summary, style_analysis, score, confidence_score, feedback } = data;
  const MY_SPEAKER_ID = '1'; // TODO: 실제 사용자/선택 화자 ID로 교체
  const myStyle = (style_analysis as AnalysisRes['style_analysis'] | undefined)?.[MY_SPEAKER_ID] ?? null;

  return (
    <main className="mx-auto max-w-4xl p-6">
      <div className="space-y-8">
        {/* 헤더 */}
        <header className="text-center">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-red-100 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-800">분석 요약</h1>
          </div>
          
          {/* 점수 표시 */}
          {(score != null || confidence_score != null) && (
            <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-2xl p-6 mb-6">
              <div className="flex items-center justify-center gap-8">
                {score != null && (
                  <div className="text-center">
                    <div className="text-4xl font-bold">{(score * 100).toFixed(0)}</div>
                    <div className="text-orange-100">말하기 점수</div>
                  </div>
                )}
                {confidence_score != null && (
                  <div className="text-center">
                    <div className="text-4xl font-bold">{(confidence_score * 100).toFixed(0)}%</div>
                    <div className="text-orange-100">신뢰도</div>
                  </div>
                )}
              </div>
            </div>
          )}
        </header>

        {/* 내 말투/성향 분석 */}
        {!!myStyle && (
          <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-purple-100 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-800">말투/성향 분석</h3>
            </div>
            <div className="grid gap-4">
              {myStyle['주요_관심사'] && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-800 mb-2">주요 관심사</h4>
                  <p className="text-gray-700">{myStyle['주요_관심사']}</p>
                </div>
              )}
              {myStyle['대화_비교_분석'] && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-800 mb-2">대화 비교 분석</h4>
                  <p className="text-gray-700">{myStyle['대화_비교_분석']}</p>
                </div>
              )}
              {myStyle['말투_특징_분석'] && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-800 mb-2">말투 특징</h4>
                  <p className="text-gray-700">{myStyle['말투_특징_분석']}</p>
                </div>
              )}
              {myStyle['대화_성향_및_감정_표현'] && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h4 className="font-medium text-gray-800 mb-2">성향/감정 표현</h4>
                  <p className="text-gray-700">{myStyle['대화_성향_및_감정_표현']}</p>
                </div>
              )}
            </div>
          </section>
        )}

        {/* AI 리포트 */}
        {!!summary && (
          <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-green-100 to-emerald-100 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-800">AI 리포트</h3>
            </div>
            <div className="bg-gray-50 rounded-lg p-6">
              <pre className="whitespace-pre-wrap break-words text-gray-800 leading-relaxed">
                {summary.trim()}
              </pre>
            </div>
          </section>
        )}

        {/* 개선점 */}
        {!!feedback && (
          <section className="bg-white rounded-2xl shadow-lg border border-orange-100 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 bg-gradient-to-br from-yellow-100 to-orange-100 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-800">개선점</h3>
            </div>
            <div className="bg-yellow-50 rounded-lg p-6 border border-yellow-200">
              <pre className="whitespace-pre-wrap break-words text-gray-800 leading-relaxed">
                {feedback.trim()}
              </pre>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
