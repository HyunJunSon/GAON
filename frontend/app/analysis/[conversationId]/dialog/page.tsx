'use client';
import { useAnalysis } from "@/hooks/useAnalysis";
import { useParams } from "next/navigation";

export default function ResultsDialogPage() {
  const { conversationId } = useParams();
  const id = Array.isArray(conversationId) ? conversationId[0] : conversationId as string;
  const { data, isLoading, isError, error } = useAnalysis(id);

  if (isLoading) return <div>로딩…</div>;
  if (isError || !data) return <div>{(error as Error)?.message ?? '불러오기 실패'}</div>;
  if (data.status !== 'ready') return <div>현재 상태: {data.status}</div>;
  return (
    <main className="mx-auto max-w-3xl p-6">
      <section className="rounded-lg border bg-white p-4">
        <h2 className="text-lg font-medium mb-2">대화록</h2>
        <pre className="rounded bg-gray-50 p-3 text-sm whitespace-pre-wrap">
          {data.dialog?.raw}
        </pre>
      </section>
    </main>
  );
}