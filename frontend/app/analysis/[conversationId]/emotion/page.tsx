'use client';
import { AnalysisRes } from "@/apis/analysis";
import { useAnalysis } from "@/hooks/useAnalysis";
import { useParams } from "next/navigation";

export default function ResultsEmotionPage() {
  const { conversationId } = useParams();
  const id = Array.isArray(conversationId) ? conversationId[0] : conversationId as string;
  const { data, isLoading, isError, error } = useAnalysis(id);
  
  if (isLoading) return <div>로딩…</div>;
  if (isError || !data) return <div>{(error as Error)?.message ?? '불러오기 실패'}</div>;
  if (data.status !== 'ready') return <div>현재 상태: {data.status}</div>;
  
  
  const { summary, statistics, style_analysis, score, confidence_score} = data
    // style_analysis는 화자ID를 키로 갖는 Record 형태이므로, 표시할 대상 화자의 항목만 선택
  const MY_SPEAKER_ID = '1'; // TODO: 실제 사용자/선택 화자 ID로 교체
  const myStyle = (style_analysis as AnalysisRes['style_analysis'] | undefined)?.[MY_SPEAKER_ID] ?? null;
  
  return (
    <main className="mx-auto max-w-3xl p-6">
      {/* 통계 요약 */}
      <section className="rounded border bg-white p-4">
        <h3 className="text-base font-semibold">통계 분석</h3>
        <div className="mt-2 grid gap-3 sm:grid-cols-2">
          <div className="text-sm">
            <div className="font-medium">사용자</div>
            <div>총 단어: {statistics?.user?.word_count ?? '-'}</div>
            <div>고유 단어: {statistics?.user?.unique_words ?? '-'}</div>
            <div>평균 문장 길이: {statistics?.user?.avg_sentence_length ?? '-'}</div>
            {!!(statistics?.user?.top_words?.length) && (
              <div>자주 사용: {statistics?.user?.top_words?.slice(0,5).join(', ')}</div>
            )}
          </div>
          <div className="text-sm">
            <div className="font-medium">상대방</div>
            <div>총 단어: {statistics?.others?.word_count ?? '-'}</div>
            <div>고유 단어: {statistics?.others?.unique_words ?? '-'}</div>
            <div>평균 문장 길이: {statistics?.others?.avg_sentence_length ?? '-'}</div>
          </div>
        </div>
        {statistics?.comparison && (
          <p className="mt-2 text-sm text-gray-700">비교: {statistics?.comparison}</p>
        )}
      </section>
    </main>
  );
}