'use client';

import { AnalysisRes } from "@/apis/analysis";
import { useAnalysis } from "@/hooks/useAnalysis";
import { useParams } from "next/navigation";

export default function ResultsSummaryPage() {
  const { conversationId } = useParams();
  const id = Array.isArray(conversationId) ? conversationId[0] : conversationId as string;
  const { data, isLoading, isError, error } = useAnalysis(id);

  if (isLoading) return <div>로딩…</div>;
  if (isError || !data) return <div>{(error as Error)?.message ?? '불러오기 실패'}</div>;
  if (data.status !== 'ready' && data.status !== 'completed') return <div>현재 상태: {data.status}</div>;

  const { summary, style_analysis, score, confidence_score, feedback } = data
    // style_analysis는 화자ID를 키로 갖는 Record 형태이므로, 표시할 대상 화자의 항목만 선택
  const MY_SPEAKER_ID = '1'; // TODO: 실제 사용자/선택 화자 ID로 교체
  const myStyle = (style_analysis as AnalysisRes['style_analysis'] | undefined)?.[MY_SPEAKER_ID] ?? null;

  return (
    <main className="mx-auto max-w-3xl p-6">
      <div className="space-y-6">
        <header className="text-sm text-gray-600">
          {(score != null || confidence_score != null) && (
            <div className="mt-1">
              {score != null && <>말하기 점수: <strong>{(score * 100).toFixed(0)}</strong>/100</>}
              
            </div>
          )}
        </header>

        {/* 내 말투/성향 분석 */}
        {!!myStyle && (
          <section className="rounded border bg-white p-4">
            <h3 className="text-base font-semibold">말투/성향 분석</h3>
            <ul className="mt-2 space-y-2 text-sm text-gray-700">
              {myStyle['주요_관심사'] && <li><strong>주요 관심사:</strong> {myStyle['주요_관심사']}</li>}
              {myStyle['대화_비교_분석'] && <li><strong>대화 비교 분석:</strong> {myStyle['대화_비교_분석']}</li>}
              {myStyle['말투_특징_분석'] && <li><strong>말투 특징:</strong> {myStyle['말투_특징_분석']}</li>}
              {myStyle['대화_성향_및_감정_표현'] && <li><strong>성향/감정 표현:</strong> {myStyle['대화_성향_및_감정_표현']}</li>}
            </ul>
          </section>
        )}

        {/* 리포트 본문 (프리포맷팅) */}
        {!!summary && (
          <section className="rounded border bg-white p-4">
            <h3 className="text-base font-semibold">AI 리포트</h3>
            <pre className="mt-2 whitespace-pre-wrap break-words text-sm text-gray-800">
              {summary.trim()}
            </pre>
          </section>
        )}

        {/* 개선점 (피드백)) */}
        {!!feedback && (
          <section className="rounded border bg-white p-4">
            <h3 className="text-base font-semibold">개선점</h3>
            <pre className="mt-2 whitespace-pre-wrap break-words text-sm text-gray-800">
              {feedback.trim()}
            </pre>
          </section>
        )}
      </div>
    </main>
  );
}