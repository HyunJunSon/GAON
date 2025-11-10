'use client';
import { useAnalysis } from "@/hooks/useAnalysis";
import { useParams } from "next/navigation";

export default function ResultsEmotionPage() {
  const { conversationId } = useParams();
  const id = Array.isArray(conversationId) ? conversationId[0] : conversationId as string;
  const { data, isLoading, isError, error } = useAnalysis(id);
  
  if (isLoading) return <div>로딩…</div>;
  if (isError || !data) return <div>{(error as Error)?.message ?? '불러오기 실패'}</div>;
  if (data.status !== 'ready') return <div>현재 상태: {data.status}</div>;
  
  
  return (
    <main className="mx-auto max-w-3xl p-6">
      <section className="rounded-lg border bg-white p-4">
        <h2 className="text-lg font-medium mb-2">감정(샘플)</h2>
        <div className="text-sm text-gray-700 space-y-2">
          {data.emotion?.series?.map((s) => (
            <div key={s.label} className="flex items-center gap-2">
              <span className="w-20 text-gray-500">{s.label}</span>
              <div className="h-2 bg-gray-200 rounded w-64">
                <div className="h-2 bg-gray-800 rounded" style={{ width: `${s.value}%` }} />
              </div>
              <span>{s.value}%</span>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}